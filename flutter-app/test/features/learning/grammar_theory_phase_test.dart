import 'package:dartz/dartz.dart';
import 'package:easy_localization/easy_localization.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:lexilingo_app/core/error/failures.dart';
import 'package:lexilingo_app/features/learning/domain/entities/answer_response.dart';
import 'package:lexilingo_app/features/learning/domain/entities/course_roadmap.dart';
import 'package:lexilingo_app/features/learning/domain/entities/lesson_attempt.dart';
import 'package:lexilingo_app/features/learning/domain/entities/lesson_complete.dart';
import 'package:lexilingo_app/features/learning/domain/entities/lesson_entity.dart';
import 'package:lexilingo_app/features/learning/domain/repositories/learning_repository.dart';
import 'package:lexilingo_app/features/learning/domain/usecases/complete_lesson_usecase.dart';
import 'package:lexilingo_app/features/learning/domain/usecases/get_course_roadmap_usecase.dart';
import 'package:lexilingo_app/features/learning/domain/usecases/get_lesson_content_usecase.dart';
import 'package:lexilingo_app/features/learning/domain/usecases/start_lesson_usecase.dart';
import 'package:lexilingo_app/features/learning/domain/usecases/submit_answer_usecase.dart';
import 'package:lexilingo_app/features/learning/presentation/providers/learning_provider.dart';
import 'package:lexilingo_app/features/learning/presentation/screens/learning_session_screen.dart';
import 'package:lexilingo_app/features/voice/presentation/providers/tts_settings_provider.dart';
import 'package:provider/provider.dart';
import 'package:shared_preferences/shared_preferences.dart';

class _TheoryTestAssetLoader extends AssetLoader {
  const _TheoryTestAssetLoader();

  @override
  Future<Map<String, dynamic>> load(String path, Locale locale) async => {
    'common': {'retry': 'Retry', 'skip': 'Skip', 'cancel': 'Cancel'},
    'lesson': {
      'sessionTitle': 'Lesson',
      'loadingLesson': 'Loading...',
      'noLessonData': 'No lesson',
      'phasePreTask': 'Practice',
      'checkAnswer': 'Check',
      'exercise': {'multipleChoiceLabel': 'Multiple Choice'},
    },
    'voice': {'ttsSpeedTooltip': 'Speed', 'listen': 'Listen'},
  };
}

class _FakeTheoryRepo implements LearningRepository {
  final LessonEntity lesson;
  int theoryViewedCalls = 0;

  _FakeTheoryRepo(this.lesson);

  @override
  Future<Either<Failure, LessonAttempt>> startLesson(String lessonId) async =>
      Right(
        LessonAttempt(
          attemptId: 'att-1',
          lessonId: lessonId,
          startedAt: DateTime(2026),
          totalQuestions: lesson.exercises.length,
          livesRemaining: 3,
          hintsAvailable: 3,
        ),
      );

  @override
  Future<Either<Failure, LessonEntity>> getLessonContent(
    String lessonId,
  ) async => Right(lesson);

  @override
  Future<Either<Failure, void>> markTheoryViewed(String lessonId) async {
    theoryViewedCalls++;
    return const Right(null);
  }

  @override
  Future<Either<Failure, AnswerResponse>> submitAnswer({
    required String attemptId,
    required String questionId,
    required String questionType,
    required dynamic userAnswer,
    required int timeSpentMs,
    bool hintUsed = false,
    double? confidenceScore,
  }) => throw UnimplementedError();

  @override
  Future<Either<Failure, LessonComplete>> completeLesson(String attemptId) =>
      throw UnimplementedError();

  @override
  Future<Either<Failure, CourseRoadmap>> getCourseRoadmap(String courseId) =>
      throw UnimplementedError();
}

void main() {
  setUpAll(() async {
    TestWidgetsFlutterBinding.ensureInitialized();
    SharedPreferences.setMockInitialValues({});
    await EasyLocalization.ensureInitialized();
  });

  testWidgets(
    'Grammar lesson starts in theory phase, marks viewed on Start Practice, and allows theory peek',
    (tester) async {
      final lesson = LessonEntity(
        id: 'les-grammar-1',
        title: 'Present Simple',
        orderIndex: 1,
        estimatedMinutes: 5,
        xpReward: 20,
        grammarTheory: const GrammarTheoryEntity(
          title: 'Present Simple Tense',
          level: 'A1',
          topic: 'tenses',
          summary: 'Habits and facts',
          explanation: 'Use base verb or verb + s/es for he/she/it.',
          examples: [
            {'sentence': 'She reads daily.', 'translation': 'Cô ấy đọc mỗi ngày.'},
          ],
          grammarPoints: ['Subject + V(s/es)'],
        ),
        exercises: [
          Exercise(
            id: 'ex-1',
            type: ExerciseType.multipleChoice,
            question: 'She ___ daily.',
            options: ['read', 'reads'],
            correctAnswer: 'reads',
          ),
        ],
      );

      final repo = _FakeTheoryRepo(lesson);
      final provider = LearningProvider(
        startLessonUseCase: StartLessonUseCase(repository: repo),
        submitAnswerUseCase: SubmitAnswerUseCase(repository: repo),
        completeLessonUseCase: CompleteLessonUseCase(repository: repo),
        getCourseRoadmapUseCase: GetCourseRoadmapUseCase(repository: repo),
        getLessonContentUseCase: GetLessonContentUseCase(repository: repo),
        onTheoryViewed: repo.markTheoryViewed,
      );

      await tester.pumpWidget(
        EasyLocalization(
          supportedLocales: const [Locale('en')],
          path: 'assets/translations',
          fallbackLocale: const Locale('en'),
          startLocale: const Locale('en'),
          useOnlyLangCode: true,
          assetLoader: const _TheoryTestAssetLoader(),
          child: MultiProvider(
            providers: [
              ChangeNotifierProvider<LearningProvider>.value(value: provider),
              ChangeNotifierProvider<TtsSettingsProvider>(
                create: (_) => TtsSettingsProvider(),
              ),
            ],
            child: Builder(
              builder: (context) => MaterialApp(
                locale: context.locale,
                supportedLocales: context.supportedLocales,
                localizationsDelegates: context.localizationDelegates,
                home: const LearningSessionScreen(
                  lessonId: 'les-grammar-1',
                  courseId: 'course-1',
                ),
              ),
            ),
          ),
        ),
      );
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 200));

      expect(provider.isTheoryPhase, isTrue);
      expect(find.text('Present Simple Tense'), findsOneWidget);
      expect(find.text('Start Practice (1)'), findsOneWidget);
      expect(repo.theoryViewedCalls, 0);

      await tester.tap(find.text('Start Practice (1)'));
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 200));

      expect(provider.isTheoryPhase, isFalse);
      expect(provider.theoryViewed, isTrue);
      expect(repo.theoryViewedCalls, 1);
      expect(find.text('She ___ daily.'), findsOneWidget);

      // Re-open theory review from AppBar without resetting practice
      await tester.tap(find.byTooltip('Grammar Theory'));
      await tester.pump();
      expect(provider.isTheoryPhase, isTrue);
      expect(find.text('Present Simple Tense'), findsOneWidget);
    },
  );
}
