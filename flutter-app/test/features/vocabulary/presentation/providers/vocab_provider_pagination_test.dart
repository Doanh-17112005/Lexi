import 'dart:convert';

import 'package:dartz/dartz.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:lexilingo_app/core/error/failures.dart';
import 'package:lexilingo_app/core/network/api_client.dart';
import 'package:lexilingo_app/core/network/network_info.dart';
import 'package:lexilingo_app/features/vocabulary/domain/entities/vocab_word.dart';
import 'package:lexilingo_app/features/vocabulary/domain/repositories/vocab_repository.dart';
import 'package:lexilingo_app/features/vocabulary/domain/usecases/add_word_usecase.dart';
import 'package:lexilingo_app/features/vocabulary/domain/usecases/get_words_usecase.dart';
import 'package:lexilingo_app/features/vocabulary/presentation/providers/vocab_provider.dart';

class _AlwaysConnectedNetworkInfo implements NetworkInfo {
  @override
  Future<bool> get isConnected async => true;
}

class _EmptyVocabRepository implements VocabRepository {
  @override
  Future<Either<Failure, void>> addWord(VocabWord word) async =>
      const Right(null);

  @override
  Future<Either<Failure, List<VocabWord>>> getWords() async => const Right([]);
}

Map<String, dynamic> _itemJson(
  String word, {
  String level = 'A1',
  List<String> tags = const ['general'],
}) => {
  'id': 'id-$word',
  'word': word,
  'definition': 'Definition of $word',
  'part_of_speech': 'noun',
  'difficulty_level': level,
  'tags': tags,
};

Future<void> _waitUntil(bool Function() condition) async {
  final deadline = DateTime.now().add(const Duration(seconds: 3));
  while (!condition()) {
    if (DateTime.now().isAfter(deadline)) {
      fail('Timed out waiting for async VocabProvider state');
    }
    await Future<void>.delayed(const Duration(milliseconds: 10));
  }
}

void main() {
  test('paginates master catalog across multiple pages without duplicates', () async {
    final allCatalog = [
      _itemJson('alpha'),
      _itemJson('bravo'),
      _itemJson('charlie'),
      _itemJson('delta'),
      _itemJson('echo'),
    ];
    final requestedOffsets = <int>[];

    final apiClient = ApiClient(
      client: MockClient((request) async {
        if (request.url.path == '/vocabulary/items') {
          final limit = int.parse(request.url.queryParameters['limit']!);
          final offset = int.parse(request.url.queryParameters['offset']!);
          requestedOffsets.add(offset);
          final slice = allCatalog.skip(offset).take(limit).toList();
          return http.Response(
            jsonEncode(slice),
            200,
            headers: {'content-type': 'application/json'},
          );
        }
        if (request.url.path == '/vocabulary/collection') {
          return http.Response(
            jsonEncode({
              'items': [],
              'total': 0,
              'limit': 100,
              'offset': 0,
              'has_more': false,
            }),
            200,
            headers: {'content-type': 'application/json'},
          );
        }
        return http.Response('[]', 200);
      }),
      baseUrl: 'http://test.local',
      networkInfo: _AlwaysConnectedNetworkInfo(),
    );

    final repo = _EmptyVocabRepository();
    final provider = VocabProvider(
      getWordsUseCase: GetWordsUseCase(repo),
      addWordUseCase: AddWordUseCase(repo),
      apiClient: apiClient,
      catalogPageSize: 2,
    );

    await _waitUntil(() => !provider.isLoading);
    expect(provider.words.map((w) => w.word).toList(), ['alpha', 'bravo']);
    expect(provider.hasMoreWords, isTrue);

    await provider.loadMoreWords();
    expect(
      provider.words.map((w) => w.word).toList(),
      ['alpha', 'bravo', 'charlie', 'delta'],
    );
    expect(provider.hasMoreWords, isTrue);

    await provider.loadMoreWords();
    expect(
      provider.words.map((w) => w.word).toList(),
      ['alpha', 'bravo', 'charlie', 'delta', 'echo'],
    );
    expect(provider.hasMoreWords, isFalse);
    expect(requestedOffsets, [0, 2, 4]);

    // Calling loadMoreWords when hasMoreWords is false is a no-op.
    await provider.loadMoreWords();
    expect(requestedOffsets, [0, 2, 4]);

    provider.dispose();
  });

  test('forwards CEFR level and tag filters across paginated requests and handles load-more error retry', () async {
    final b1Items = [
      _itemJson('analyze', level: 'B1', tags: ['science']),
      _itemJson('benefit', level: 'B1', tags: ['business']),
      _itemJson('concept', level: 'B1', tags: ['science']),
    ];
    var failNextLoadMore = false;

    final apiClient = ApiClient(
      client: MockClient((request) async {
        if (request.url.path == '/vocabulary/items') {
          final level = request.url.queryParameters['difficulty_level'];
          final tag = request.url.queryParameters['tag'];
          final limit = int.parse(request.url.queryParameters['limit']!);
          final offset = int.parse(request.url.queryParameters['offset']!);

          if (failNextLoadMore && offset > 0) {
            return http.Response('{"detail":"temporary error"}', 500);
          }

          final filtered = b1Items.where((item) {
            if (level != null && item['difficulty_level'] != level) return false;
            if (tag != null && !(item['tags'] as List).contains(tag)) return false;
            return true;
          }).toList();

          return http.Response(
            jsonEncode(filtered.skip(offset).take(limit).toList()),
            200,
            headers: {'content-type': 'application/json'},
          );
        }
        if (request.url.path == '/vocabulary/collection') {
          return http.Response(
            jsonEncode({
              'items': [],
              'total': 0,
              'limit': 100,
              'offset': 0,
              'has_more': false,
            }),
            200,
            headers: {'content-type': 'application/json'},
          );
        }
        return http.Response('[]', 200);
      }),
      baseUrl: 'http://test.local',
      networkInfo: _AlwaysConnectedNetworkInfo(),
    );

    final repo = _EmptyVocabRepository();
    final provider = VocabProvider(
      getWordsUseCase: GetWordsUseCase(repo),
      addWordUseCase: AddWordUseCase(repo),
      apiClient: apiClient,
      catalogPageSize: 2,
    );
    await _waitUntil(() => !provider.isLoading);

    provider.setLevelFilter('B1');
    await _waitUntil(() => !provider.isLoading && provider.words.length == 2);
    expect(provider.hasMoreWords, isTrue);

    // Simulate failure on page 2 -> preserves existing words and exposes loadMoreError.
    failNextLoadMore = true;
    await provider.loadMoreWords();
    expect(provider.loadMoreError, isNotNull);
    expect(provider.words.map((w) => w.word).toList(), ['analyze', 'benefit']);

    // Retry succeeds cleanly.
    failNextLoadMore = false;
    await provider.loadMoreWords();
    expect(provider.loadMoreError, isNull);
    expect(
      provider.words.map((w) => w.word).toList(),
      ['analyze', 'benefit', 'concept'],
    );
    expect(provider.hasMoreWords, isFalse);

    // Filtering by tag preserves known tags in availableTags.
    provider.setTagFilter('science');
    await _waitUntil(
      () => !provider.isLoading && provider.filteredWords.length == 2,
    );
    expect(
      provider.filteredWords.map((w) => w.word).toList(),
      ['analyze', 'concept'],
    );
    expect(provider.availableTags, containsAll(['science', 'business']));

    provider.dispose();
  });

  test('paginates backend collection across multiple pages using has_more', () async {
    final collectionItems = [
      {
        'id': 'uv-1',
        'status': 'learning',
        'vocabulary': _itemJson('one'),
      },
      {
        'id': 'uv-2',
        'status': 'learning',
        'vocabulary': _itemJson('two'),
      },
      {
        'id': 'uv-3',
        'status': 'mastered',
        'vocabulary': _itemJson('three'),
      },
    ];

    final apiClient = ApiClient(
      client: MockClient((request) async {
        if (request.url.path == '/vocabulary/items') {
          return http.Response('[]', 200);
        }
        if (request.url.path == '/vocabulary/collection') {
          final limit = int.parse(request.url.queryParameters['limit']!);
          final offset =
              int.tryParse(request.url.queryParameters['offset'] ?? '0') ?? 0;
          final slice = collectionItems.skip(offset).take(limit).toList();
          return http.Response(
            jsonEncode({
              'items': slice,
              'total': collectionItems.length,
              'limit': limit,
              'offset': offset,
              'has_more': offset + slice.length < collectionItems.length,
            }),
            200,
            headers: {'content-type': 'application/json'},
          );
        }
        return http.Response('[]', 200);
      }),
      baseUrl: 'http://test.local',
      networkInfo: _AlwaysConnectedNetworkInfo(),
    );

    final repo = _EmptyVocabRepository();
    final provider = VocabProvider(
      getWordsUseCase: GetWordsUseCase(repo),
      addWordUseCase: AddWordUseCase(repo),
      apiClient: apiClient,
      catalogPageSize: 2,
      collectionPageSize: 2,
    );
    await _waitUntil(() => !provider.isLoading);

    expect(provider.words.map((w) => w.word).toList(), ['one', 'two', 'three']);
    expect(provider.words.last.isLearned, isTrue);

    provider.dispose();
  });
}
