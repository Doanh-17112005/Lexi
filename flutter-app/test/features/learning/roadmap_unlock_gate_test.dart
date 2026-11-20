import 'package:dartz/dartz.dart';
import 'package:easy_localization/easy_localization.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:lexilingo_app/core/error/failures.dart';
import 'package:lexilingo_app/features/learning/domain/entities/course_roadmap.dart';
import 'package:lexilingo_app/features/learning/domain/entities/lesson_attempt.dart';
import 'package:lexilingo_app/features/learning/domain/entities/lesson_entity.dart';
import 'package:lexilingo_app/features/learning/domain/repositories/learning_repository.dart';
import 'package:lexilingo_app/features/learning/domain/usecases/complete_lesson_usecase.dart';
import 'package:lexilingo_app/features/learning/domain/usecases/get_course_roadmap_usecase.dart';
import 'package:lexilingo_app/features/learning/domain/usecases/get_lesson_content_usecase.dart';
import 'package:lexilingo_app/features/learning/domain/usecases/start_lesson_usecase.dart';
import 'package:lexilingo_app/features/learning/domain/usecases/submit_answer_usecase.dart';
import 'package:lexilingo_app/features/learning/presentation/providers/learning_provider.dart';
import 'package:lexilingo_app/features/learning/presentation/screens/learning_roadmap_screen.dart';
import 'package:lexilingo_app/features/learning/presentation/screens/learning_session_screen.dart';
import 'package:lexilingo_app/features/voice/presentation/providers/tts_settings_provider.dart';
import 'package:provider/provider.dart';
import 'package:shared_preferences/shared_preferences.dart';

class _RoadmapTestAssetLoader extends AssetLoader {
  const _RoadmapTestAssetLoader();

  @override
  Future<Map<String, dynamic>> load(String path, Locale locale) async => {
    'common': {'retry': 'Retry'},
    'learning': {
      'lessonLockedHint': 'Complete previous lessons to unlock this lesson',
      'unitProgress': '{completed}/{total}',
    },
  };
}

class _FakeLearningRepository extends Fake implements LearningRepository {
  int roadmapLoads = 0;

  @override
  Future<Either<Failure, CourseRoadmap>> getCourseRoadmap(
    String courseId,
  ) async {
    roadmapLoads++;
    return Right(
      CourseRoadmap(
        courseId: courseId,
        courseTitle: 'A1 Foundations',
        level: 'A1',
        totalUnits: 1,
        completedUnits: 0,
        totalLessons: 2,
        completedLessons: 0,
        completionPercentage: 0,
        currentStreak: 1,
        totalXpEarned: 0,
        units: const [
          UnitRoadmap(
            unitId: 'u-1',
            unitNumber: 1,
            title: 'Unit 1',
            totalLessons: 2,
            completedLessons: 0,
            completionPercentage: 0,
            isCurrent: true,
            backgroundColor: '#2196F3',
            lessons: [
              LessonProgress(
                lessonId: 'l-1',
                lessonNumber: 1,
                title: 'First Unlocked Lesson',
                isLocked: false,
                isCurrent: true,
                isCompleted: false,
                starsEarned: 0,
                attemptsCount: 0,
                completionPercentage: 0,
                backgroundColor: '#2196F3',
              ),
              LessonProgress(
                lessonId: 'l-2',
                lessonNumber: 2,
                title: 'Locked Next Lesson',
                isLocked: true,
                isCurrent: false,
                isCompleted: false,
                starsEarned: 0,
                attemptsCount: 0,
                completionPercentage: 0,
                backgroundColor: '#9E9E9E',
              ),
            ],
          ),
        ],
      ),
    );
  }

  @override
  Future<Either<Failure, LessonEntity>> getLessonContent(
    String lessonId,
  ) async => Left(ServerFailure('Preview stop in test'));

  @override
  Future<Either<Failure, LessonAttempt>> startLesson(String lessonId) async =>
      Left(ServerFailure('Preview stop in test'));

  @override
  Future<Either<Failure, void>> markTheoryViewed(String lessonId) async =>
      const Right(null);
}

void main() {
  setUpAll(() async {
    TestWidgetsFlutterBinding.ensureInitialized();
    SharedPreferences.setMockInitialValues({});
    EasyLocalization.logger.enableLevels = [];
    await EasyLocalization.ensureInitialized();
  });

  testWidgets(
    'Locked node shows unlock condition without opening session; unlocked node refreshes roadmap on return',
    (tester) async {
      tester.view.physicalSize = const Size(1080, 1920);
      tester.view.devicePixelRatio = 1.0;
      addTearDown(tester.view.reset);

      final repo = _FakeLearningRepository();
      final provider = LearningProvider(
        startLessonUseCase: StartLessonUseCase(repository: repo),
        submitAnswerUseCase: SubmitAnswerUseCase(repository: repo),
        completeLessonUseCase: CompleteLessonUseCase(repository: repo),
        getCourseRoadmapUseCase: GetCourseRoadmapUseCase(repository: repo),
        getLessonContentUseCase: GetLessonContentUseCase(repository: repo),
      );

      await tester.pumpWidget(
        EasyLocalization(
          supportedLocales: const [Locale('en')],
          path: 'assets/i18n',
          fallbackLocale: const [Locale('en')].first,
          startLocale: const Locale('en'),
          useOnlyLangCode: true,
          assetLoader: const _RoadmapTestAssetLoader(),
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
                home: const LearningRoadmapScreen(
                  courseId: 'course-1',
                  courseTitle: 'A1 Foundations',
                ),
              ),
            ),
          ),
        ),
      );
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 200));

      expect(repo.roadmapLoads, 1);

      // 1. Tapping locked node shows guidance SnackBar and does not open session.
      await tester.tap(find.byIcon(Icons.lock_rounded));
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 100));
      expect(
        find.text('Complete previous lessons to unlock this lesson'),
        findsOneWidget,
      );
      expect(find.byType(LearningSessionScreen), findsNothing);

      // 2. Tapping unlocked current node opens LearningSessionScreen and
      // popping back triggers a roadmap refresh.
      await tester.tap(find.byIcon(Icons.play_arrow_rounded));
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 300));
      expect(find.byType(LearningSessionScreen), findsOneWidget);

      final navigator = tester.state<NavigatorState>(find.byType(Navigator));
      navigator.pop();
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 300));

      expect(repo.roadmapLoads, 2);
    },
  );
}
