import 'package:dartz/dartz.dart';
import 'package:easy_localization/easy_localization.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:lexilingo_app/core/error/failures.dart';
import 'package:lexilingo_app/features/learning/data/models/lesson_content_model.dart';
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
import 'package:lexilingo_app/features/learning/presentation/widgets/premium_exercise_widgets.dart';
import 'package:lexilingo_app/features/mistakes/data/mistake_notebook_repository.dart';
import 'package:lexilingo_app/features/mistakes/domain/mistake_notebook_entry.dart';
import 'package:lexilingo_app/features/voice/presentation/providers/tts_settings_provider.dart';
import 'package:provider/provider.dart';
import 'package:shared_preferences/shared_preferences.dart';

class _SanitizedTestAssetLoader extends AssetLoader {
  const _SanitizedTestAssetLoader();

  @override
  Future<Map<String, dynamic>> load(String path, Locale locale) async => {
        'common': {
          'retry': 'Retry',
          'skip': 'Skip',
          'cancel': 'Cancel',
          'error': 'Error',
          'back': 'Back',
        },
        'lesson': {
          'sessionTitle': 'Lesson',
          'loadingLesson': 'Loading...',
          'noLessonData': 'No lesson',
          'phaseTaskCycle': 'Practice',
          'checkAnswer': 'Check',
          'continueButton': 'Continue',
          'exercise': {
            'multipleChoiceLabel': 'MULTIPLE CHOICE',
            'fillBlankTitle': 'Fill in the blank',
            'fillBlankHint': 'Type your answer',
            'explanationLabel': 'Explanation',
          },
        },
        'voice': {'ttsSpeedTooltip': 'Speed', 'listen': 'Listen'},
      };
}

class _FakeSanitizedLearningRepo implements LearningRepository {
  final LessonEntity lesson;
  int theoryViewedCalls = 0;

  _FakeSanitizedLearningRepo(this.lesson);

  @override
  Future<Either<Failure, LessonAttempt>> startLesson(String lessonId) async =>
      Right(
        LessonAttempt(
          attemptId: 'att-sanitized-1',
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
  ) async =>
      Right(lesson);

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
  }) async {
    if (questionId == 'ex-mc-1') {
      final isRight = userAnswer.toString() == 'are';
      return Right(
        AnswerResponse(
          questionAttemptId: 'qa-1',
          isCorrect: isRight,
          correctAnswer: 'are',
          explanation: "Subject 'My parents' is plural so use 'are'.",
          xpEarned: isRight ? 12 : 0,
          livesRemaining: isRight ? 3 : 2,
          hintsRemaining: 3,
          currentScore: isRight ? 50.0 : 0.0,
        ),
      );
    }
    return const Right(
      AnswerResponse(
        questionAttemptId: 'qa-2',
        isCorrect: true,
        correctAnswer: 'studies',
        explanation: "He/she/it takes 'studies' in Present Simple.",
        xpEarned: 12,
        livesRemaining: 2,
        hintsRemaining: 3,
        currentScore: 50.0,
      ),
    );
  }

  @override
  Future<Either<Failure, LessonComplete>> completeLesson(String attemptId) async =>
      Right(
        LessonComplete(
          attemptId: attemptId,
          passed: true,
          finalScore: 50,
          totalXpEarned: 35,
          timeSpentSeconds: 10,
          accuracy: 50.0,
          starsEarned: 1,
          achievementsUnlocked: const [],
          totalQuestions: 2,
          correctAnswers: 1,
          wrongAnswers: 1,
          hintsUsed: 0,
        ),
      );

  @override
  Future<Either<Failure, CourseRoadmap>> getCourseRoadmap(String courseId) =>
      throw UnimplementedError();
}

class _InMemoryMistakeRepo extends MistakeNotebookRepository {
  final List<MistakeNotebookEntry> saved = [];

  @override
  Future<void> saveMistake(MistakeNotebookEntry entry) async {
    saved.add(entry);
  }
}

void main() {
  setUpAll(() async {
    TestWidgetsFlutterBinding.ensureInitialized();
    SharedPreferences.setMockInitialValues({});
    await EasyLocalization.ensureInitialized();
  });

  test('LessonContentModel parses sanitized API payload without answer keys', () {
    final model = LessonContentModel.fromJson({
      'id': 'lesson-1',
      'title': 'Grammar 1: To Be & Present Simple',
      'lesson_type': 'grammar',
      'order_index': 1,
      'xp_reward': 35,
      'pass_threshold': 70,
      'estimated_minutes': 10,
      'total_exercises': 2,
      'theory_viewed': false,
      'grammar_theory': {
        'grammar_item_id': '00000000-0000-0000-0000-000000000001',
        'title': "Verb 'To Be' & Present Simple Habits",
        'level': 'A1',
        'topic': 'tenses_and_verbs',
        'explanation': 'Rule explanation',
        'examples': [
          {'sentence': 'She works here.', 'translation': 'Cô ấy làm việc ở đây.'},
        ],
        'grammar_points': ['I am | He/She/It is | You/We/They are'],
        'linked_exercise_ids': ['ex-mc-1', 'ex-fill-2'],
      },
      'exercises': [
        {
          'id': 'ex-mc-1',
          'type': 'multiple_choice',
          'ui_type': 'multiple_choice',
          'phase': 'task_cycle',
          'question': 'My parents ___ at home.',
          'options': [
            {'id': '0', 'text': 'is', 'is_correct': null},
            {'id': '1', 'text': 'are', 'is_correct': null},
          ],
          'correct_answer': null,
          'explanation': null,
        },
        {
          'id': 'ex-fill-2',
          'type': 'fill_blank',
          'ui_type': 'fill_in_the_blank',
          'phase': 'task_cycle',
          'question': 'Minh {blank} every morning.',
          'correct_answer': null,
          'explanation': null,
        },
      ],
    });

    final entity = model.toEntity();
    expect(entity.exercises[0].correctAnswer, '');
    expect(entity.exercises[0].explanation, isNull);
    expect(entity.grammarTheory?.title, "Verb 'To Be' & Present Simple Habits");
    expect(formatFillBlankPrompt('Minh {blank} every morning.', ''), 'Minh _____ every morning.');
  });

  testWidgets(
    'Sanitized grammar lesson hides answers before submit, reveals explanation after submit, and records mistakes cleanly',
    (tester) async {
      final sanitizedLesson = LessonContentModel.fromJson({
        'id': 'lesson-grammar-a1',
        'title': 'Grammar 1: To Be & Present Simple',
        'lesson_type': 'grammar',
        'order_index': 1,
        'xp_reward': 35,
        'pass_threshold': 70,
        'estimated_minutes': 10,
        'total_exercises': 2,
        'theory_viewed': false,
        'grammar_theory': {
          'title': "Verb 'To Be' & Present Simple Habits",
          'level': 'A1',
          'topic': 'tenses_and_verbs',
          'explanation': 'Plural subjects take are.',
          'examples': [
            {'sentence': 'My parents are at home.'},
          ],
          'grammar_points': ['You/We/They are'],
          'linked_exercise_ids': ['ex-mc-1', 'ex-fill-2'],
        },
        'exercises': [
          {
            'id': 'ex-mc-1',
            'type': 'multiple_choice',
            'ui_type': 'multiple_choice',
            'phase': 'task_cycle',
            'question': 'My parents ___ at home.',
            'options': [
              {'id': '0', 'text': 'is'},
              {'id': '1', 'text': 'are'},
            ],
          },
          {
            'id': 'ex-fill-2',
            'type': 'fill_blank',
            'ui_type': 'fill_in_the_blank',
            'phase': 'task_cycle',
            'question': 'Minh {blank} every morning.',
          },
        ],
      }).toEntity();

      final repo = _FakeSanitizedLearningRepo(sanitizedLesson);
      final mistakeRepo = _InMemoryMistakeRepo();
      final provider = LearningProvider(
        startLessonUseCase: StartLessonUseCase(repository: repo),
        submitAnswerUseCase: SubmitAnswerUseCase(repository: repo),
        completeLessonUseCase: CompleteLessonUseCase(repository: repo),
        getCourseRoadmapUseCase: GetCourseRoadmapUseCase(repository: repo),
        getLessonContentUseCase: GetLessonContentUseCase(repository: repo),
        onTheoryViewed: repo.markTheoryViewed,
        mistakeRepository: mistakeRepo,
      );

      await tester.pumpWidget(
        EasyLocalization(
          supportedLocales: const [Locale('en')],
          path: 'assets/translations',
          fallbackLocale: const Locale('en'),
          startLocale: const Locale('en'),
          useOnlyLangCode: true,
          assetLoader: const _SanitizedTestAssetLoader(),
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
                  lessonId: 'lesson-grammar-a1',
                  courseId: 'course-a1',
                ),
              ),
            ),
          ),
        ),
      );
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 200));

      // Phase 1: Theory shown first
      expect(provider.isTheoryPhase, isTrue);
      expect(find.text("Verb 'To Be' & Present Simple Habits"), findsOneWidget);

      await tester.tap(find.text('Start Practice (2)'));
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 200));

      // Before submitting: no explanation rendered, correctAnswer still empty
      expect(provider.isTheoryPhase, isFalse);
      expect(provider.currentExercise?.correctAnswer, '');
      expect(find.text("Subject 'My parents' is plural so use 'are'."), findsNothing);

      // Submit wrong option 'is' -> server response resolves real correctAnswer & explanation
      await tester.tap(find.text('is'));
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 200));

      expect(provider.isCurrentCorrect, isFalse);
      expect(provider.currentExercise?.correctAnswer, 'are');
      expect(find.text("Subject 'My parents' is plural so use 'are'."), findsOneWidget);
      expect(mistakeRepo.saved, hasLength(1));
      expect(mistakeRepo.saved.single.correctAnswer, 'are');
    },
  );
}
