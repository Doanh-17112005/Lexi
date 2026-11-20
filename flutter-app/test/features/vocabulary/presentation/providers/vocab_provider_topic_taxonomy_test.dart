import 'dart:convert';

import 'package:dartz/dartz.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:lexilingo_app/core/error/failures.dart';
import 'package:lexilingo_app/core/network/api_client.dart';
import 'package:lexilingo_app/core/network/network_info.dart';
import 'package:lexilingo_app/features/vocabulary/data/models/vocabulary_tags.dart';
import 'package:lexilingo_app/features/vocabulary/domain/entities/user_vocabulary_entity.dart';
import 'package:lexilingo_app/features/vocabulary/domain/entities/vocab_word.dart';
import 'package:lexilingo_app/features/vocabulary/domain/entities/vocabulary_item_entity.dart';
import 'package:lexilingo_app/features/vocabulary/domain/repositories/vocab_repository.dart';
import 'package:lexilingo_app/features/vocabulary/domain/repositories/vocabulary_repository.dart';
import 'package:lexilingo_app/features/vocabulary/domain/usecases/add_word_usecase.dart';
import 'package:lexilingo_app/features/vocabulary/domain/usecases/get_due_vocabulary_usecase.dart';
import 'package:lexilingo_app/features/vocabulary/domain/usecases/get_words_usecase.dart';
import 'package:lexilingo_app/features/vocabulary/domain/usecases/submit_review_usecase.dart';
import 'package:lexilingo_app/features/vocabulary/presentation/providers/flashcard_provider.dart';
import 'package:lexilingo_app/features/vocabulary/presentation/providers/quiz_provider.dart';
import 'package:lexilingo_app/features/vocabulary/presentation/providers/vocab_provider.dart';

class _AlwaysConnectedNetworkInfo implements NetworkInfo {
  @override
  Future<bool> get isConnected async => true;
}

class _StubLocalVocabRepository implements VocabRepository {
  final List<VocabWord> localWords;
  _StubLocalVocabRepository(this.localWords);

  @override
  Future<Either<Failure, void>> addWord(VocabWord word) async =>
      const Right(null);

  @override
  Future<Either<Failure, List<VocabWord>>> getWords() async =>
      Right(localWords);
}

class _TopicFakeVocabularyRepository extends Fake
    implements VocabularyRepository {
  final List<VocabularyItemEntity> catalog;
  final List<String?> capturedTags = [];

  _TopicFakeVocabularyRepository(this.catalog);

  @override
  Future<Either<Failure, List<VocabularyItemEntity>>> getVocabularyItems({
    String? courseId,
    String? lessonId,
    String? difficultyLevel,
    String? tag,
    String? search,
    int limit = 50,
    int offset = 0,
  }) async {
    capturedTags.add(tag);
    final normalized = normalizeVocabularyTopic(tag);
    final filtered = catalog
        .where(
          (item) =>
              normalized == null ||
              normalizeVocabularyTags(item.tags).contains(normalized),
        )
        .take(limit)
        .toList();
    return Right(filtered);
  }

  @override
  Future<Either<Failure, List<UserVocabularyEntity>>> getUserCollection({
    VocabularyStatus? status,
    int limit = 50,
    int offset = 0,
  }) async =>
      const Right([]);

  @override
  Future<Either<Failure, UserVocabularyEntity>> addToCollection(
    String vocabularyId,
  ) async =>
      Right(
        UserVocabularyEntity(
          id: 'uv-$vocabularyId',
          userId: 'user-1',
          vocabularyId: vocabularyId,
          status: VocabularyStatus.learning,
          nextReviewDate: DateTime.utc(2026, 11, 18),
          addedAt: DateTime.utc(2026, 11, 18),
        ),
      );
}

List<Map<String, dynamic>> _seedLikeMasterItems() => [
      {
        'id': 'id-1',
        'word': 'hello',
        'definition': 'A greeting.',
        'difficulty_level': 'A1',
        'tags': ['general'],
      },
      {
        'id': 'id-2',
        'word': 'airport',
        'definition': 'Place for planes.',
        'difficulty_level': 'A2',
        'tags': {'topic': 'travel'},
      },
      {
        'id': 'id-3',
        'word': 'invoice',
        'definition': 'Bill for goods.',
        'difficulty_level': 'B1',
        'tags': ['business'],
      },
      {
        'id': 'id-4',
        'word': 'breakfast',
        'definition': 'Morning meal.',
        'difficulty_level': 'A1',
        'tags': {'topic': 'daily_life'},
      },
      {
        'id': 'id-5',
        'word': 'commute',
        'definition': 'Daily travel to work.',
        'difficulty_level': 'B1',
        'tags': ['daily-life'],
      },
      {
        'id': 'id-6',
        'word': 'hypothesis',
        'definition': 'Testable scientific idea.',
        'difficulty_level': 'B2',
        'tags': ['science'],
      },
      {
        'id': 'id-7',
        'word': 'algorithm',
        'definition': 'Step-by-step computation procedure.',
        'difficulty_level': 'C1',
        'tags': ['technology'],
      },
    ];

void main() {
  test(
    'VocabProvider normalizes canonical topics and level/tag filter requests',
    () async {
      final requestedUris = <Uri>[];
      final masterItems = _seedLikeMasterItems();

      final apiClient = ApiClient(
        client: MockClient((request) async {
          requestedUris.add(request.url);
          if (request.url.path == '/vocabulary/collection') {
            return http.Response(
              jsonEncode({'items': [], 'total': 0, 'has_more': false}),
              200,
              headers: {'content-type': 'application/json'},
            );
          }
          if (request.url.path == '/vocabulary/decks') {
            return http.Response(
              jsonEncode([]),
              200,
              headers: {'content-type': 'application/json'},
            );
          }
          if (request.url.path == '/vocabulary/items') {
            final level = request.url.queryParameters['difficulty_level'];
            final tag = request.url.queryParameters['tag'];
            final filtered = masterItems.where((raw) {
              if (level != null && raw['difficulty_level'] != level) {
                return false;
              }
              if (tag != null &&
                  !normalizeVocabularyTags(raw['tags']).contains(tag)) {
                return false;
              }
              return true;
            }).toList();
            return http.Response(
              jsonEncode(filtered),
              200,
              headers: {'content-type': 'application/json'},
            );
          }
          return http.Response('Not Found', 404);
        }),
        baseUrl: 'http://test.local',
        networkInfo: _AlwaysConnectedNetworkInfo(),
        enableLogging: false,
      );

      final localRepo = _StubLocalVocabRepository([
        VocabWord(
          word: 'errand',
          definition: 'Short trip to do something.',
          difficultyLevel: 'b1',
          tags: const ['Daily_Life'],
        ),
      ]);
      final provider = VocabProvider(
        getWordsUseCase: GetWordsUseCase(localRepo),
        addWordUseCase: AddWordUseCase(localRepo),
        apiClient: apiClient,
      );

      await Future<void>.delayed(const Duration(milliseconds: 20));
      expect(provider.availableTags, containsAll(canonicalSystemTopics));
      expect(provider.availableTags, isNot(contains('daily_life')));

      // Topic-only using alias 'daily_life'
      provider.setTagFilter('daily_life');
      expect(provider.selectedTag, 'daily');
      await Future<void>.delayed(const Duration(milliseconds: 20));
      expect(
        provider.filteredWords.map((w) => w.word).toSet(),
        containsAll({'breakfast', 'commute', 'errand'}),
      );

      // Combined level + topic ('b1' + 'daily')
      provider.setLevelFilter('b1');
      expect(provider.selectedLevel, 'B1');
      await Future<void>.delayed(const Duration(milliseconds: 20));
      expect(
        provider.filteredWords.map((w) => w.word).toSet(),
        {'commute', 'errand'},
      );

      final lastItemsCall = requestedUris.lastWhere(
        (uri) => uri.path == '/vocabulary/items',
      );
      expect(lastItemsCall.queryParameters['difficulty_level'], 'B1');
      expect(lastItemsCall.queryParameters['tag'], 'daily');
    },
  );

  test(
    'FlashcardProvider and QuizProvider canonicalize topic aliases for all 6 topics',
    () async {
      final catalog = [
        for (final topic in canonicalSystemTopics)
          VocabularyItemEntity(
            id: 'v-$topic-1',
            word: '${topic}one',
            definition: 'First word for $topic.',
            partOfSpeech: 'noun',
            difficultyLevel: 'B1',
            tags: topic == 'daily' ? const ['daily_life'] : [topic],
            createdAt: DateTime.utc(2026, 11, 18),
          ),
        VocabularyItemEntity(
          id: 'v-extra-2',
          word: 'distractortwo',
          definition: 'Second word.',
          partOfSpeech: 'noun',
          difficultyLevel: 'B1',
          tags: const ['general'],
          createdAt: DateTime.utc(2026, 11, 18),
        ),
        VocabularyItemEntity(
          id: 'v-extra-3',
          word: 'distractorthree',
          definition: 'Third word.',
          partOfSpeech: 'noun',
          difficultyLevel: 'B1',
          tags: const ['general'],
          createdAt: DateTime.utc(2026, 11, 18),
        ),
        VocabularyItemEntity(
          id: 'v-extra-4',
          word: 'distractorfour',
          definition: 'Fourth word.',
          partOfSpeech: 'noun',
          difficultyLevel: 'B1',
          tags: const ['general'],
          createdAt: DateTime.utc(2026, 11, 18),
        ),
      ];

      final repo = _TopicFakeVocabularyRepository(catalog);
      final flashcardProvider = FlashcardProvider(
        getDueVocabularyUseCase: GetDueVocabularyUseCase(repo),
        submitReviewUseCase: SubmitReviewUseCase(repo),
        vocabularyRepository: repo,
      );
      final quizProvider = QuizProvider(
        getDueVocabularyUseCase: GetDueVocabularyUseCase(repo),
        submitReviewUseCase: SubmitReviewUseCase(repo),
        vocabularyRepository: repo,
      );

      await flashcardProvider.startTopicSession(tag: 'daily_life');
      expect(repo.capturedTags.last, 'daily');
      expect(flashcardProvider.errorMessage, isNull);
      expect(flashcardProvider.currentSession?.cards.length, 1);

      await quizProvider.startTopicSession(tag: 'daily-life');
      expect(repo.capturedTags, ['daily', 'daily', null]);
      expect(quizProvider.errorMessage, isNull);
      expect(quizProvider.hasSession, isTrue);
      expect(quizProvider.totalQuestions, greaterThan(0));
    },
  );
}
