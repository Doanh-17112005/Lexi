import 'dart:convert';

import 'package:dartz/dartz.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:lexilingo_app/core/error/failures.dart';
import 'package:lexilingo_app/core/network/api_client.dart';
import 'package:lexilingo_app/core/network/network_info.dart';
import 'package:lexilingo_app/features/vocabulary/domain/entities/review_session_entity.dart';
import 'package:lexilingo_app/features/vocabulary/domain/entities/vocab_word.dart';
import 'package:lexilingo_app/features/vocabulary/domain/repositories/vocab_repository.dart';
import 'package:lexilingo_app/features/vocabulary/domain/usecases/add_word_usecase.dart';
import 'package:lexilingo_app/features/vocabulary/domain/usecases/get_words_usecase.dart';
import 'package:lexilingo_app/features/vocabulary/presentation/providers/vocab_provider.dart';
import 'package:lexilingo_app/features/vocabulary/presentation/widgets/review_quality_buttons.dart';

class _OnlineNetworkInfo implements NetworkInfo {
  @override
  Future<bool> get isConnected async => true;
}

class _NoopVocabRepo implements VocabRepository {
  @override
  Future<Either<Failure, void>> addWord(VocabWord word) async =>
      const Right(null);

  @override
  Future<Either<Failure, List<VocabWord>>> getWords() async => const Right([]);
}

void main() {
  test(
    'VocabProvider populates vocabularyId from catalog and saveToCollection updates userVocabularyId',
    () async {
      String? postedUrl;
      final apiClient = ApiClient(
        client: MockClient((request) async {
          if (request.url.path == '/vocabulary/items') {
            return http.Response(
              jsonEncode([
                {
                  'id': 'vocab-uuid-123',
                  'word': 'serendipity',
                  'definition': 'Finding good things by chance.',
                  'difficulty_level': 'C2',
                  'part_of_speech': 'noun',
                  'tags': ['science', 'general'],
                },
              ]),
              200,
              headers: {'content-type': 'application/json'},
            );
          }
          if (request.url.path == '/vocabulary/collection' &&
              request.method == 'GET') {
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
          if (request.url.path == '/vocabulary/collection' &&
              request.method == 'POST') {
            postedUrl = request.url.toString();
            return http.Response(
              jsonEncode({
                'id': 'uv-uuid-456',
                'vocabulary_id': 'vocab-uuid-123',
              }),
              201,
              headers: {'content-type': 'application/json'},
            );
          }
          return http.Response('{}', 200);
        }),
        baseUrl: 'http://test.local',
        networkInfo: _OnlineNetworkInfo(),
        enableLogging: false,
      );

      final repo = _NoopVocabRepo();
      final provider = VocabProvider(
        getWordsUseCase: GetWordsUseCase(repo),
        addWordUseCase: AddWordUseCase(repo),
        apiClient: apiClient,
      );

      await Future<void>.delayed(const Duration(milliseconds: 50));
      expect(provider.words.length, 1);
      expect(provider.words.first.vocabularyId, 'vocab-uuid-123');
      expect(provider.words.first.userVocabularyId, isNull);

      final saved = await provider.saveToCollection(provider.words.first);
      expect(saved, isTrue);
      expect(
        postedUrl,
        contains('/vocabulary/collection?vocabulary_id=vocab-uuid-123'),
      );
      expect(provider.words.first.userVocabularyId, 'uv-uuid-456');

      // Subsequent save is idempotent without firing another POST.
      postedUrl = null;
      final secondSave = await provider.saveToCollection(provider.words.first);
      expect(secondSave, isTrue);
      expect(postedUrl, isNull);
    },
  );

  testWidgets('ReviewQualityButtons exposes Again, Hard, Good, Easy ratings', (
    tester,
  ) async {
    final selected = <ReviewQuality>[];
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: ReviewQualityButtons(onQualitySelected: selected.add),
        ),
      ),
    );

    await tester.tap(find.text('1'));
    await tester.tap(find.text('2'));
    await tester.tap(find.text('3'));
    await tester.tap(find.text('4'));
    await tester.pump();

    expect(selected, [
      ReviewQuality.incorrect,
      ReviewQuality.hard,
      ReviewQuality.good,
      ReviewQuality.easy,
    ]);
  });
}
