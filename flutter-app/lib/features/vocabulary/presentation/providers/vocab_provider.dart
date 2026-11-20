import 'dart:convert';
import 'dart:async';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:lexilingo_app/core/error/failures.dart';
import 'package:lexilingo_app/core/network/api_client.dart';
import 'package:lexilingo_app/core/services/quick_save_vocabulary_service.dart';
import 'package:lexilingo_app/core/usecase/usecase.dart';
import 'package:lexilingo_app/features/vocabulary/data/models/vocabulary_tags.dart';
import 'package:lexilingo_app/features/vocabulary/domain/entities/vocab_word.dart';
import 'package:lexilingo_app/features/vocabulary/domain/usecases/add_word_usecase.dart';
import 'package:lexilingo_app/features/vocabulary/domain/usecases/get_words_usecase.dart';

/// Result from the free Dictionary API lookup.
class DictionaryLookupResult {
  final String word;
  final String? pronunciation; // IPA
  final String? audioUrl;
  final String? definition;
  final String? example;
  final String? partOfSpeech;
  final bool found;

  const DictionaryLookupResult({
    required this.word,
    this.pronunciation,
    this.audioUrl,
    this.definition,
    this.example,
    this.partOfSpeech,
    required this.found,
  });
}

class VocabProvider extends ChangeNotifier {
  static const int defaultCatalogPageSize = 30;
  static const int defaultCollectionPageSize = 100;

  final GetWordsUseCase getWordsUseCase;
  final AddWordUseCase addWordUseCase;
  final ApiClient? _apiClient;
  final QuickSaveVocabularyService? _quickSaveService;
  final int _catalogPageSize;
  final int _collectionPageSize;
  StreamSubscription<QuickSaveVocabularyResult>? _savedWordsSubscription;
  bool _suppressNextQuickSaveReload = false;
  Future<void>? _inFlightLoadWords;
  Timer? _searchDebounce;
  int _loadEpoch = 0;

  List<VocabWord> _words = [];
  final Set<String> _knownTags = <String>{};
  String? _errorMessage;
  String? _loadMoreError;
  bool _isLoading = false;
  bool _isLoadingMore = false;
  bool _isLoadingDecks = false;
  bool _hasMoreWords = false;
  int _catalogOffset = 0;
  String? _selectedTag;
  String? _selectedLevel;
  String _searchQuery = '';

  // Dictionary lookup state
  DictionaryLookupResult? _lookupResult;
  bool _isLookingUp = false;

  VocabProvider({
    required this.getWordsUseCase,
    required this.addWordUseCase,
    ApiClient? apiClient,
    QuickSaveVocabularyService? quickSaveService,
    int catalogPageSize = defaultCatalogPageSize,
    int collectionPageSize = defaultCollectionPageSize,
  }) : _apiClient = apiClient,
       _quickSaveService = quickSaveService,
       _catalogPageSize = catalogPageSize,
       _collectionPageSize = collectionPageSize {
    _savedWordsSubscription = _quickSaveService?.savedWords.listen((_) {
      if (_suppressNextQuickSaveReload) {
        _suppressNextQuickSaveReload = false;
        return;
      }
      unawaited(loadWords(force: true));
    });
    unawaited(loadWords());
    unawaited(loadDecks());
  }

  List<VocabWord> get words => _words;
  String? get errorMessage => _errorMessage;
  String? get loadMoreError => _loadMoreError;
  bool get isLoading => _isLoading;
  bool get isLoadingMore => _isLoadingMore;
  bool get isLoadingDecks => _isLoadingDecks;
  bool get hasMoreWords => _hasMoreWords;
  String? get selectedTag => _selectedTag;
  String? get selectedLevel => _selectedLevel;
  String get searchQuery => _searchQuery;

  List<String> get availableTags {
    final tags = <String>{...normalizeVocabularyTags(_knownTags)};
    for (final w in _words) {
      if (w.tags != null) tags.addAll(normalizeVocabularyTags(w.tags));
    }
    final sorted = tags.toList()..sort();
    return sorted;
  }

  List<VocabWord> get filteredWords {
    final query = _searchQuery.trim().toLowerCase();
    return _words.where((word) {
      if (_selectedTag != null &&
          !normalizeVocabularyTags(word.tags).contains(_selectedTag)) {
        return false;
      }
      if (_selectedLevel != null &&
          word.difficultyLevel?.trim().toUpperCase() != _selectedLevel) {
        return false;
      }
      if (query.isNotEmpty &&
          !word.word.toLowerCase().contains(query) &&
          !word.definition.toLowerCase().contains(query)) {
        return false;
      }
      return true;
    }).toList();
  }

  void setTagFilter(String? tag) {
    final normalized = normalizeVocabularyTopic(tag);
    if (_selectedTag == normalized) return;
    _selectedTag = normalized;
    notifyListeners();
    if (_apiClient != null) {
      unawaited(loadWords(force: true));
    }
  }

  void setLevelFilter(String? level) {
    final normalized = (level == null || level.trim().isEmpty)
        ? null
        : level.trim().toUpperCase();
    if (_selectedLevel == normalized) return;
    _selectedLevel = normalized;
    notifyListeners();
    if (_apiClient != null) {
      unawaited(loadWords(force: true));
    }
  }

  void setSearchQuery(String query) {
    if (_searchQuery == query) return;
    _searchQuery = query;
    notifyListeners();
    if (_apiClient != null) {
      _searchDebounce?.cancel();
      _searchDebounce = Timer(const Duration(milliseconds: 300), () {
        unawaited(loadWords(force: true));
      });
    }
  }

  DictionaryLookupResult? get lookupResult => _lookupResult;
  bool get isLookingUp => _isLookingUp;

  Future<void> loadWords({bool force = false}) {
    if (!force) {
      final existing = _inFlightLoadWords;
      if (existing != null) return existing;
    }

    final future = _performLoadWords();
    _inFlightLoadWords = future;
    future.whenComplete(() {
      if (identical(_inFlightLoadWords, future)) {
        _inFlightLoadWords = null;
      }
    });
    return future;
  }

  Future<void> _performLoadWords() async {
    final epoch = ++_loadEpoch;
    final activeLevel = _selectedLevel;
    final activeTag = _selectedTag;
    final activeSearch = _searchQuery.trim();

    _isLoading = true;
    _isLoadingMore = false;
    _loadMoreError = null;
    _catalogOffset = 0;
    _hasMoreWords = false;
    notifyListeners();

    final localWords = <VocabWord>[];
    String? loadError;
    final result = await getWordsUseCase(NoParams());
    result.fold(
      (failure) {
        loadError = _getFailureMessage(failure);
      },
      (words) {
        localWords.addAll(words);
      },
    );

    final backendMaster = <VocabWord>[];
    final backendCollection = <VocabWord>[];
    var masterPageCount = 0;
    if (_apiClient != null) {
      try {
        final page = await _fetchBackendMasterPage(
          offset: 0,
          difficultyLevel: activeLevel,
          tag: activeTag,
          search: activeSearch,
        );
        masterPageCount = page.length;
        backendMaster.addAll(page);
      } catch (error) {
        loadError ??= 'Failed to load the vocabulary library: $error';
      }
      try {
        backendCollection.addAll(await _fetchBackendCollection());
      } catch (_) {
        // Collection requires a valid session; the public master list remains usable.
      }
    }

    if (epoch != _loadEpoch) return;

    final mergedByWord = <String, VocabWord>{};
    for (final word in [
      ...backendCollection,
      ...localWords,
      ...backendMaster,
    ]) {
      final key = word.word.toLowerCase();
      final existing = mergedByWord[key];
      mergedByWord[key] = existing == null ? word : _mergeWord(existing, word);
      if (word.tags != null) {
        _knownTags.addAll(normalizeVocabularyTags(word.tags));
      }
    }
    _words = mergedByWord.values.toList();
    _catalogOffset = masterPageCount;
    _hasMoreWords = _apiClient != null && masterPageCount >= _catalogPageSize;
    _errorMessage = _words.isEmpty ? loadError : null;

    _isLoading = false;
    notifyListeners();
  }

  Future<void> loadMoreWords() async {
    if (_apiClient == null || _isLoading || _isLoadingMore || !_hasMoreWords) {
      return;
    }

    final epoch = _loadEpoch;
    final activeLevel = _selectedLevel;
    final activeTag = _selectedTag;
    final activeSearch = _searchQuery.trim();

    _isLoadingMore = true;
    _loadMoreError = null;
    notifyListeners();

    try {
      final page = await _fetchBackendMasterPage(
        offset: _catalogOffset,
        difficultyLevel: activeLevel,
        tag: activeTag,
        search: activeSearch,
      );
      if (epoch != _loadEpoch) return;

      final mergedByWord = <String, VocabWord>{
        for (final word in _words) word.word.toLowerCase(): word,
      };
      for (final word in page) {
        final key = word.word.toLowerCase();
        final existing = mergedByWord[key];
        mergedByWord[key] =
            existing == null ? word : _mergeWord(existing, word);
        if (word.tags != null) {
          _knownTags.addAll(normalizeVocabularyTags(word.tags));
        }
      }

      _words = mergedByWord.values.toList();
      _catalogOffset += page.length;
      _hasMoreWords = page.length >= _catalogPageSize;
      _loadMoreError = null;
    } catch (error) {
      if (epoch != _loadEpoch) return;
      _loadMoreError = 'Failed to load more words: $error';
    } finally {
      if (epoch == _loadEpoch) {
        _isLoadingMore = false;
        notifyListeners();
      }
    }
  }

  VocabWord _mergeWord(VocabWord base, VocabWord incoming) {
    final mergedTags = <String>{
      ...normalizeVocabularyTags(base.tags),
      ...normalizeVocabularyTags(incoming.tags),
    }.toList();
    return VocabWord(
      id: incoming.id ?? base.id,
      vocabularyId: incoming.vocabularyId ?? base.vocabularyId,
      userVocabularyId: incoming.userVocabularyId ?? base.userVocabularyId,
      word: incoming.word,
      definition: incoming.definition.isNotEmpty
          ? incoming.definition
          : base.definition,
      isLearned: incoming.isLearned || base.isLearned,
      pronunciation: incoming.pronunciation ?? base.pronunciation,
      audioUrl: incoming.audioUrl ?? base.audioUrl,
      example: incoming.example ?? base.example,
      partOfSpeech: incoming.partOfSpeech ?? base.partOfSpeech,
      difficultyLevel: incoming.difficultyLevel ?? base.difficultyLevel,
      tags: mergedTags.isEmpty ? null : mergedTags,
    );
  }

  Future<List<VocabWord>> _fetchBackendMasterPage({
    required int offset,
    String? difficultyLevel,
    String? tag,
    String? search,
  }) async {
    final queryParams = <String, String>{
      'limit': '$_catalogPageSize',
      'offset': '$offset',
      if (difficultyLevel != null && difficultyLevel.isNotEmpty)
        'difficulty_level': difficultyLevel,
      if (tag != null && tag.isNotEmpty) 'tag': tag,
      if (search != null && search.isNotEmpty) 'search': search,
    };
    final uri = Uri(path: '/vocabulary/items', queryParameters: queryParams);
    final response = await _apiClient!.get(uri.toString());
    final items = response['data'] as List<dynamic>? ?? [];
    return items
        .map((raw) {
          final item = raw as Map<String, dynamic>;
          final translation = item['translation'] as Map<String, dynamic>?;
          final examples = translation?['examples'] as List<dynamic>?;
          return VocabWord(
            vocabularyId: item['id'] as String?,
            word: item['word'] as String? ?? '',
            definition: _cleanDefinition(item['definition'] as String? ?? ''),
            pronunciation: item['pronunciation'] as String?,
            audioUrl: item['audio_url'] as String?,
            example: examples?.whereType<String>().firstOrNull,
            partOfSpeech: item['part_of_speech'] as String?,
            difficultyLevel: item['difficulty_level'] as String?,
            tags: normalizeVocabularyTags(item['tags']),
          );
        })
        .where((word) => word.word.isNotEmpty)
        .toList();
  }

  @override
  void dispose() {
    _searchDebounce?.cancel();
    _savedWordsSubscription?.cancel();
    super.dispose();
  }

  Future<List<VocabWord>> _fetchBackendCollection() async {
    final collected = <VocabWord>[];
    var offset = 0;

    while (true) {
      final path = offset == 0
          ? '/vocabulary/collection?limit=$_collectionPageSize'
          : '/vocabulary/collection?limit=$_collectionPageSize&offset=$offset';
      final response = await _apiClient!.get(path);
      final items = (response['items'] as List<dynamic>? ?? []);
      for (final item in items) {
        final vocab = item['vocabulary'] as Map<String, dynamic>?;
        if (vocab == null) continue;
        final word = vocab['word'] as String? ?? '';
        if (word.isEmpty) continue;
        final translation = vocab['translation'] as Map<String, dynamic>?;
        final examples = translation?['examples'] as List<dynamic>?;
        collected.add(
          VocabWord(
            vocabularyId: vocab['id'] as String?,
            userVocabularyId: item['id'] as String?,
            word: word,
            definition: _cleanDefinition(vocab['definition'] as String? ?? ''),
            pronunciation: vocab['pronunciation'] as String?,
            audioUrl: vocab['audio_url'] as String?,
            example: examples?.whereType<String>().firstOrNull,
            partOfSpeech: vocab['part_of_speech'] as String?,
            difficultyLevel: vocab['difficulty_level'] as String?,
            isLearned: (item['status'] as String?) == 'mastered',
            tags: normalizeVocabularyTags(vocab['tags']),
          ),
        );
      }

      final hasMore = response['has_more'] == true;
      if (!hasMore || items.isEmpty) break;
      offset += items.length;
    }
    return collected;
  }

  /// Strips auto-generated seeded/placeholder definitions that were inserted
  /// by data-import scripts and should not be surfaced to the user.
  static String _cleanDefinition(String raw) {
    const seededPrefixes = ['Seeded from crawled', '#N/A'];
    for (final prefix in seededPrefixes) {
      if (raw.startsWith(prefix)) return '';
    }
    return raw;
  }

  /// Look up a word in the free Dictionary API.
  /// Fills [lookupResult] with pronunciation, definition, example, partOfSpeech.
  Future<DictionaryLookupResult> lookupWord(String word) async {
    _isLookingUp = true;
    _lookupResult = null;
    notifyListeners();

    final trimmed = word.trim().toLowerCase();
    DictionaryLookupResult result;
    try {
      final uri = Uri.parse(
        'https://api.dictionaryapi.dev/api/v2/entries/en/$trimmed',
      );
      final response = await http.get(uri).timeout(const Duration(seconds: 8));
      if (response.statusCode == 200) {
        final List<dynamic> data = jsonDecode(response.body) as List<dynamic>;
        final entry = data[0] as Map<String, dynamic>;

        // Phonetics
        String? ipa;
        String? audio;
        final phonetics = entry['phonetics'] as List<dynamic>? ?? [];
        for (final p in phonetics) {
          final pm = p as Map<String, dynamic>;
          ipa ??= pm['text'] as String?;
          if (audio == null) {
            final a = pm['audio'] as String?;
            if (a != null && a.isNotEmpty) audio = a;
          }
          if (ipa != null && audio != null) break;
        }

        // Meanings
        String? definition;
        String? example;
        String? pos;
        final meanings = entry['meanings'] as List<dynamic>? ?? [];
        if (meanings.isNotEmpty) {
          final meaning = meanings[0] as Map<String, dynamic>;
          pos = meaning['partOfSpeech'] as String?;
          final defs = meaning['definitions'] as List<dynamic>? ?? [];
          if (defs.isNotEmpty) {
            final def = defs[0] as Map<String, dynamic>;
            definition = def['definition'] as String?;
            example = def['example'] as String?;
          }
        }

        result = DictionaryLookupResult(
          word: word,
          pronunciation: ipa,
          audioUrl: audio,
          definition: definition,
          example: example,
          partOfSpeech: pos,
          found: true,
        );
      } else {
        result = DictionaryLookupResult(word: word, found: false);
      }
    } catch (_) {
      result = DictionaryLookupResult(word: word, found: false);
    }

    _lookupResult = result;
    _isLookingUp = false;
    notifyListeners();
    return result;
  }

  void clearLookup() {
    _lookupResult = null;
    notifyListeners();
  }

  Future<bool> addWord(
    String word,
    String definition, {
    String? pronunciation,
    String? audioUrl,
    String? example,
    String? partOfSpeech,
  }) async {
    _errorMessage = null;

    if (_quickSaveService != null) {
      _suppressNextQuickSaveReload = true;
      try {
        await _quickSaveService.quickSaveWord(
          word: word,
          sourceType: 'manual',
          contextSentence: example,
          definition: definition,
          partOfSpeech: partOfSpeech,
        );
      } catch (e) {
        _suppressNextQuickSaveReload = false;
        _errorMessage = 'Failed to save word: $e';
        notifyListeners();
        return false;
      }
    }

    final result = await addWordUseCase(
      AddWordParams(
        word: word,
        definition: definition,
        pronunciation: pronunciation,
        audioUrl: audioUrl,
        example: example,
        partOfSpeech: partOfSpeech,
      ),
    );
    bool success = _quickSaveService != null;
    result.fold(
      (failure) {
        if (_quickSaveService == null) {
          _errorMessage = _getFailureMessage(failure);
        }
      },
      (_) {
        _errorMessage = null;
        success = true;
      },
    );
    await loadWords(force: true);
    return success;
  }

  String _getFailureMessage(Failure failure) {
    if (failure is ServerFailure) {
      return failure.message;
    } else if (failure is NetworkFailure) {
      return 'Network error. Please check your internet connection.';
    } else if (failure is CacheFailure) {
      return 'Local storage error.';
    } else {
      return 'An error occurred. Please try again.';
    }
  }

  // ===== Vocabulary Decks =====
  List<VocabularyDeck> _decks = [];
  List<VocabularyDeck> get decks => _decks;

  Future<void> loadDecks() async {
    if (_apiClient == null) return;
    _isLoadingDecks = true;
    notifyListeners();

    try {
      final response = await _apiClient.get('/vocabulary/decks');
      final items = response['data'] ?? response;
      if (items is List) {
        _decks = items
            .map((d) => VocabularyDeck.fromJson(d as Map<String, dynamic>))
            .toList();
      } else {
        _decks = [];
      }
      _errorMessage = null;
    } catch (e) {
      _errorMessage = 'Failed to load decks: $e';
    } finally {
      _isLoadingDecks = false;
      notifyListeners();
    }
  }

  Future<bool> createDeck(
    String name,
    String? description,
    String color,
  ) async {
    if (_apiClient == null) return false;
    _isLoading = true;
    notifyListeners();

    try {
      final descParam = description != null
          ? '&description=${Uri.encodeComponent(description)}'
          : '';
      final colorParam = '&color=${Uri.encodeComponent(color)}';
      await _apiClient.post(
        '/vocabulary/decks?name=${Uri.encodeComponent(name)}'
        '$descParam$colorParam',
      );
      _errorMessage = null;
      await loadDecks();
      return true;
    } catch (e) {
      _errorMessage = 'Failed to create deck: $e';
      return false;
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<bool> addWordToDeck(String deckId, String userVocabularyId) async {
    if (_apiClient == null) return false;
    try {
      await _apiClient.post(
        '/vocabulary/decks/$deckId/items',
        body: {'user_vocabulary_id': userVocabularyId},
      );
      await loadDecks();
      return true;
    } catch (e) {
      _errorMessage = 'Failed to add word to deck: $e';
      return false;
    }
  }

  Future<bool> removeWordFromDeck(
    String deckId,
    String userVocabularyId,
  ) async {
    if (_apiClient == null) return false;
    try {
      await _apiClient.delete(
        '/vocabulary/decks/$deckId/items/$userVocabularyId',
      );
      await loadDecks();
      return true;
    } catch (e) {
      _errorMessage = 'Failed to remove word from deck: $e';
      return false;
    }
  }

  Future<bool> deleteDeck(String deckId) async {
    if (_apiClient == null) return false;
    _isLoading = true;
    notifyListeners();
    try {
      await _apiClient.delete('/vocabulary/decks/$deckId');
      await loadDecks();
      return true;
    } catch (e) {
      _errorMessage = 'Failed to delete deck: $e';
      return false;
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  /// Saves a master catalog word into the user's backend collection idempotently.
  Future<bool> saveToCollection(VocabWord word) async {
    if (word.userVocabularyId != null && word.userVocabularyId!.isNotEmpty) {
      return true;
    }
    if (word.vocabularyId != null &&
        word.vocabularyId!.isNotEmpty &&
        _apiClient != null) {
      try {
        final response = await _apiClient.post(
          '/vocabulary/collection?vocabulary_id=${Uri.encodeComponent(word.vocabularyId!)}',
        );
        final userVocabId = response['id']?.toString();
        final normalized = word.word.trim().toLowerCase();
        _words = _words.map((existing) {
          if (existing.word.trim().toLowerCase() != normalized) {
            return existing;
          }
          return VocabWord(
            id: existing.id,
            vocabularyId: existing.vocabularyId ?? word.vocabularyId,
            userVocabularyId: userVocabId ?? existing.userVocabularyId,
            word: existing.word,
            definition: existing.definition,
            isLearned: existing.isLearned,
            pronunciation: existing.pronunciation,
            audioUrl: existing.audioUrl,
            example: existing.example,
            partOfSpeech: existing.partOfSpeech,
            difficultyLevel: existing.difficultyLevel,
            tags: existing.tags,
          );
        }).toList();
        _errorMessage = null;
        notifyListeners();
        return true;
      } catch (e) {
        _errorMessage = 'Failed to save word to collection: $e';
        notifyListeners();
        return false;
      }
    }

    return addWord(
      word.word,
      word.definition,
      pronunciation: word.pronunciation,
      example: word.example,
      partOfSpeech: word.partOfSpeech,
    );
  }
}

class VocabularyDeck {
  final String id;
  final String name;
  final String? description;
  final String color;
  final bool isPublic;
  final int itemCount;

  const VocabularyDeck({
    required this.id,
    required this.name,
    this.description,
    required this.color,
    this.isPublic = false,
    this.itemCount = 0,
  });

  factory VocabularyDeck.fromJson(Map<String, dynamic> json) {
    return VocabularyDeck(
      id: json['id'] as String,
      name: json['name'] as String,
      description: json['description'] as String?,
      color: json['color'] as String? ?? "#2196F3",
      isPublic: json['is_public'] as bool? ?? false,
      itemCount: json['item_count'] as int? ?? 0,
    );
  }
}
