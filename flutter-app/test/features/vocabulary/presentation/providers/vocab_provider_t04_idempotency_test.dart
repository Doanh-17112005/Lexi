import 'package:dartz/dartz.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:lexilingo_app/core/error/failures.dart';
import 'package:lexilingo_app/features/vocabulary/domain/entities/review_session_entity.dart';
import 'package:lexilingo_app/features/vocabulary/domain/entities/user_vocabulary_entity.dart';
import 'package:lexilingo_app/features/vocabulary/domain/entities/vocabulary_item_entity.dart';
import 'package:lexilingo_app/features/vocabulary/domain/repositories/vocabulary_repository.dart';
import 'package:lexilingo_app/features/vocabulary/domain/usecases/get_due_vocabulary_usecase.dart';
import 'package:lexilingo_app/features/vocabulary/domain/usecases/submit_review_usecase.dart';
import 'package:lexilingo_app/features/vocabulary/presentation/providers/flashcard_provider.dart';
import 'package:lexilingo_app/features/vocabulary/presentation/providers/quiz_provider.dart';

class _RetryFakeVocabularyRepository extends Fake
    implements VocabularyRepository {
  final List<UserVocabularyEntity> dueItems;
  final Map<String, VocabularyItemEntity> itemsById;
  final List<String?> capturedKeys = [];
  bool shouldFailNextSubmit = false;

  _RetryFakeVocabularyRepository({
    required this.dueItems,
    required this.itemsById,
  });

  @override
  Future<Either<Failure, List<UserVocabularyEntity>>> getDueVocabulary({
    int limit = 20,
  }) async => Right(dueItems);

  @override
  Future<Either<Failure, VocabularyItemEntity>> getVocabularyItem(
    String vocabularyId,
  ) async {
    final item = itemsById[vocabularyId];
    return item == null ? const Left(NotFoundFailure()) : Right(item);
  }

  @override
  Future<Either<Failure, List<VocabularyItemEntity>>> getVocabularyItems({
    String? courseId,
    String? lessonId,
    String? difficultyLevel,
    String? tag,
    String? search,
    int limit = 50,
    int offset = 0,
  }) async => Right(itemsById.values.toList());

  @override
  Future<Either<Failure, ReviewResultEntity>> submitReview(
    String userVocabularyId,
    ReviewQuality quality, {
    int? timeSpentMs,
    String? idempotencyKey,
  }) async {
    capturedKeys.add(idempotencyKey);
    if (shouldFailNextSubmit) {
      shouldFailNextSubmit = false;
      return const Left(NetworkFailure('Simulated transient network error'));
    }
    return Right(
      ReviewResultEntity(
        userVocabularyId: userVocabularyId,
        quality: quality,
        xpEarned: 15,
        newEaseFactor: 2.5,
        newInterval: 1,
        newRepetitions: 1,
        nextReviewDate: DateTime.utc(2026, 11, 19),
        reviewedAt: DateTime.utc(2026, 11, 18),
      ),
    );
  }
}

void main() {
  late _RetryFakeVocabularyRepository repo;

  setUp(() {
    final now = DateTime.utc(2026, 11, 18);
    repo = _RetryFakeVocabularyRepository(
      dueItems: [
        UserVocabularyEntity(
          id: 'uv-1',
          userId: 'user-1',
          vocabularyId: 'v-1',
          status: VocabularyStatus.learning,
          nextReviewDate: now,
          addedAt: now,
        ),
      ],
      itemsById: {
        'v-1': VocabularyItemEntity(
          id: 'v-1',
          word: 'resilient',
          definition: 'Able to recover quickly.',
          partOfSpeech: 'adjective',
          difficultyLevel: 'B2',
          createdAt: now,
        ),
        'v-2': VocabularyItemEntity(
          id: 'v-2',
          word: 'airport',
          definition: 'Place for aircraft.',
          partOfSpeech: 'noun',
          difficultyLevel: 'A2',
          createdAt: now,
        ),
        'v-3': VocabularyItemEntity(
          id: 'v-3',
          word: 'habit',
          definition: 'Regular practice.',
          partOfSpeech: 'noun',
          difficultyLevel: 'B1',
          createdAt: now,
        ),
        'v-4': VocabularyItemEntity(
          id: 'v-4',
          word: 'evidence',
          definition: 'Facts supporting a claim.',
          partOfSpeech: 'noun',
          difficultyLevel: 'B2',
          createdAt: now,
        ),
      },
    );
  });

  test('FlashcardProvider reuses idempotencyKey on retry after transient failure', () async {
    final provider = FlashcardProvider(
      getDueVocabularyUseCase: GetDueVocabularyUseCase(repo),
      submitReviewUseCase: SubmitReviewUseCase(repo),
      vocabularyRepository: repo,
    );

    await provider.startReviewSession(limit: 5);
    expect(provider.hasSession, isTrue);

    repo.shouldFailNextSubmit = true;
    await provider.submitReview(ReviewQuality.good);
    expect(provider.errorMessage, isNotNull);
    expect(provider.currentSession!.reviewedCards, 0);

    await provider.submitReview(ReviewQuality.good);
    expect(provider.errorMessage, isNull);
    expect(provider.currentSession!.reviewedCards, 1);
    expect(provider.currentSession!.totalXpEarned, 15);
    expect(repo.capturedKeys, hasLength(2));
    expect(repo.capturedKeys[0], isNotNull);
    expect(repo.capturedKeys[0], repo.capturedKeys[1]);
  });

  test('QuizProvider tracks failed submissions and retries with original idempotencyKey', () async {
    final provider = QuizProvider(
      getDueVocabularyUseCase: GetDueVocabularyUseCase(repo),
      submitReviewUseCase: SubmitReviewUseCase(repo),
      vocabularyRepository: repo,
    );

    await provider.startQuizSession(wordTarget: 1);
    expect(provider.hasSession, isTrue);
    expect(provider.totalQuestions, 2);

    repo.shouldFailNextSubmit = true;

    for (var i = 0; i < provider.totalQuestions; i++) {
      final q = provider.currentQuestion!;
      final correctIdx = q.options.indexWhere((o) => o.isCorrect);
      provider.answer(correctIdx);
      if (i < provider.totalQuestions - 1) provider.next();
    }
    await provider.finishPending();

    expect(provider.failedSubmissionCount, 1);
    expect(provider.totalXpEarned, 0);

    await provider.retryFailedSubmissions();
    expect(provider.failedSubmissionCount, 0);
    expect(provider.totalXpEarned, 15);
    expect(repo.capturedKeys, hasLength(2));
    expect(repo.capturedKeys[0], isNotNull);
    expect(repo.capturedKeys[0], repo.capturedKeys[1]);
  });
}
