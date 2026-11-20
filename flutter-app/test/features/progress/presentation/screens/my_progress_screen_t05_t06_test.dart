import 'package:dartz/dartz.dart';
import 'package:easy_localization/easy_localization.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:lexilingo_app/core/error/failures.dart';
import 'package:lexilingo_app/features/course/domain/entities/course_category_entity.dart';
import 'package:lexilingo_app/features/course/domain/entities/course_detail_entity.dart';
import 'package:lexilingo_app/features/course/domain/entities/course_entity.dart';
import 'package:lexilingo_app/features/course/domain/repositories/course_repository.dart';
import 'package:lexilingo_app/features/course/domain/usecases/enroll_in_course_usecase.dart';
import 'package:lexilingo_app/features/course/domain/usecases/get_categories_usecase.dart';
import 'package:lexilingo_app/features/course/domain/usecases/get_course_detail_usecase.dart';
import 'package:lexilingo_app/features/course/domain/usecases/get_courses_by_category_usecase.dart';
import 'package:lexilingo_app/features/course/domain/usecases/get_courses_usecase.dart';
import 'package:lexilingo_app/features/course/domain/usecases/get_enrolled_courses_usecase.dart';
import 'package:lexilingo_app/features/course/presentation/providers/course_provider.dart';
import 'package:lexilingo_app/features/course/presentation/screens/course_detail_screen.dart';
import 'package:lexilingo_app/features/home/presentation/providers/home_provider.dart';
import 'package:lexilingo_app/features/progress/domain/entities/content_activity_entity.dart';
import 'package:lexilingo_app/features/progress/domain/entities/user_progress_entity.dart';
import 'package:lexilingo_app/features/progress/domain/entities/weekly_progress_entity.dart';
import 'package:lexilingo_app/features/progress/domain/repositories/progress_repository.dart';
import 'package:lexilingo_app/features/progress/domain/usecases/complete_lesson_usecase.dart';
import 'package:lexilingo_app/features/progress/domain/usecases/get_course_progress_usecase.dart';
import 'package:lexilingo_app/features/progress/domain/usecases/get_my_progress_usecase.dart';
import 'package:lexilingo_app/features/progress/domain/usecases/get_weekly_progress_usecase.dart';
import 'package:lexilingo_app/features/progress/presentation/providers/content_activity_provider.dart';
import 'package:lexilingo_app/features/progress/presentation/providers/progress_provider.dart';
import 'package:lexilingo_app/features/progress/presentation/screens/my_progress_screen.dart';
import 'package:lexilingo_app/features/progress/presentation/widgets/course_progress_card.dart';
import 'package:provider/provider.dart';
import 'package:shared_preferences/shared_preferences.dart';

class _DashboardTestAssetLoader extends AssetLoader {
  const _DashboardTestAssetLoader();

  @override
  Future<Map<String, dynamic>> load(String path, Locale locale) async => {
    'common': {'retry': 'Retry'},
    'course': {'userProgressPercent': '{percent}%'},
    'progress': {
      'title': 'My Progress',
      'loadingProgress': 'Loading progress...',
      'noProgressDataAvailable': 'No progress data available',
      'overallStatistics': 'Overall Statistics',
      'coursesEnrolledStat': 'Courses Enrolled',
      'coursesCompletedStat': 'Courses Completed',
      'lessonsCompletedStat': 'Lessons Completed',
      'weeklyOverview': 'Weekly Overview',
      'weeklySummary': '{xp} XP • {lessons} lessons • {days} days',
      'tabLessons': 'Lessons',
      'tabActivity': 'Activity',
      'tabContent': 'Content',
      'courseProgressTitle': 'Course Progress',
      'lessonsOfTotal': '{completed}/{total} lessons',
    },
    'profile': {
      'totalXp': 'Total XP',
      'currentStreak': 'Current Streak',
      'longestStreak': 'Longest Streak',
      'daysCount': '{count} days',
      'noEnrolledCoursesYet': 'No enrolled courses yet',
    },
  };
}

class _FakeProgressRepository extends Fake implements ProgressRepository {
  Either<Failure, ProgressStatsEntity> Function() onGetMyProgress;
  Either<Failure, WeeklyProgressEntity> Function() onGetWeeklyProgress;

  _FakeProgressRepository({
    required this.onGetMyProgress,
    required this.onGetWeeklyProgress,
  });

  @override
  Future<Either<Failure, ProgressStatsEntity>> getMyProgress() async =>
      onGetMyProgress();

  @override
  Future<Either<Failure, WeeklyProgressEntity>> getWeeklyProgress() async =>
      onGetWeeklyProgress();

  @override
  Future<Either<Failure, ContentActivityEntity>> getContentActivity({
    int days = 7,
  }) async => const Right(ContentActivityEntity.empty);
}

class _FakeCourseRepository extends Fake implements CourseRepository {
  @override
  Future<Either<Failure, (List<CourseEntity>, int)>> getCourses({
    int page = 1,
    int pageSize = 20,
    String? language,
    String? level,
  }) async => const Right(([], 0));

  @override
  Future<Either<Failure, (List<CourseEntity>, int)>> getEnrolledCourses({
    int page = 1,
    int pageSize = 20,
  }) async => const Right(([], 0));

  @override
  Future<Either<Failure, CourseDetailEntity>> getCourseDetail(
    String courseId,
  ) async => Left(ServerFailure('Course preview unavailable in test'));

  @override
  Future<Either<Failure, List<CourseCategoryEntity>>> getCategories({
    bool activeOnly = true,
  }) async => const Right([]);
}

ProgressStatsEntity _sampleStats({
  int xp = 120,
  int lessons = 3,
  double pct = 50.0,
}) => ProgressStatsEntity(
  summary: UserProgressSummary(
    totalXp: xp,
    coursesEnrolled: 1,
    coursesCompleted: 0,
    lessonsCompleted: lessons,
    currentStreak: 2,
    longestStreak: 5,
    achievementsUnlocked: 0,
  ),
  courseProgress: [
    CourseProgressDetail(
      courseId: 'course-123',
      courseTitle: 'A1 Foundations',
      progressPercentage: pct,
      lessonsCompleted: lessons,
      totalLessons: 6,
      totalXpEarned: xp,
      startedAt: DateTime.utc(2026, 11, 1),
      lastActivityAt: DateTime.utc(2026, 11, 18),
    ),
  ],
);

WeeklyProgressEntity _sampleWeekly({int xp = 120, int lessons = 3}) {
  final days = List<DailyProgressEntity>.generate(
    7,
    (index) => DailyProgressEntity(
      day: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'][index],
      date: DateTime.utc(2026, 11, 12 + index),
      xpEarned: index == 6 ? xp : 0,
      lessonsCompleted: index == 6 ? lessons : 0,
      studyTimeMinutes: index == 6 ? 15 : 0,
      vocabularyReviewed: 0,
      goalMet: index == 6 && xp > 0,
      isToday: index == 6,
    ),
  );
  return WeeklyProgressEntity(
    weekProgress: days,
    totalXP: xp,
    totalLessons: lessons,
    totalStudyTime: xp > 0 ? 15 : 0,
    daysActive: xp > 0 ? 1 : 0,
    currentStreak: 2,
    longestStreak: 5,
    weekGoalProgress: xp > 0 ? 0.2 : 0.0,
  );
}

Widget _wrapDashboard({
  required ProgressProvider progressProvider,
  required HomeProvider homeProvider,
  required CourseProvider courseProvider,
  required ProgressRepository progressRepository,
}) {
  return EasyLocalization(
    supportedLocales: const [Locale('en')],
    path: 'assets/i18n',
    fallbackLocale: const Locale('en'),
    startLocale: const Locale('en'),
    useOnlyLangCode: true,
    assetLoader: const _DashboardTestAssetLoader(),
    child: MultiProvider(
      providers: [
        ChangeNotifierProvider<ProgressProvider>.value(value: progressProvider),
        ChangeNotifierProvider<HomeProvider>.value(value: homeProvider),
        ChangeNotifierProvider<CourseProvider>.value(value: courseProvider),
        ChangeNotifierProvider<ContentActivityProvider>(
          create: (_) =>
              ContentActivityProvider(repository: progressRepository),
        ),
      ],
      child: Builder(
        builder: (context) => MaterialApp(
          locale: context.locale,
          supportedLocales: context.supportedLocales,
          localizationsDelegates: context.localizationDelegates,
          home: const MyProgressScreen(),
        ),
      ),
    ),
  );
}

void main() {
  setUpAll(() async {
    TestWidgetsFlutterBinding.ensureInitialized();
    SharedPreferences.setMockInitialValues({});
    EasyLocalization.logger.enableLevels = [];
    await EasyLocalization.ensureInitialized();
  });

  testWidgets(
    'MyProgressScreen handles initial error/retry, weekly error/retry, and CourseProgressCard navigation',
    (tester) async {
      tester.view.physicalSize = const Size(1080, 1920);
      tester.view.devicePixelRatio = 1.0;
      addTearDown(tester.view.reset);

      var failProgress = true;
      var failWeekly = true;
      var currentXp = 120;

      final progressRepo = _FakeProgressRepository(
        onGetMyProgress: () => failProgress
            ? Left(ServerFailure('Progress service unavailable'))
            : Right(_sampleStats(xp: currentXp)),
        onGetWeeklyProgress: () => failWeekly
            ? Left(ServerFailure('Weekly summary unavailable'))
            : Right(_sampleWeekly(xp: currentXp)),
      );
      final courseRepo = _FakeCourseRepository();

      final progressProvider = ProgressProvider(
        getMyProgressUseCase: GetMyProgressUseCase(progressRepo),
        getCourseProgressUseCase: GetCourseProgressUseCase(progressRepo),
        completeLessonUseCase: CompleteLessonUseCase(progressRepo),
      );
      final homeProvider = HomeProvider(
        getCoursesUseCase: GetCoursesUseCase(courseRepo),
        getEnrolledCoursesUseCase: GetEnrolledCoursesUseCase(courseRepo),
        getWeeklyProgressUseCase: GetWeeklyProgressUseCase(progressRepo),
      );
      final courseProvider = CourseProvider(
        getCoursesUseCase: GetCoursesUseCase(courseRepo),
        getCourseDetailUseCase: GetCourseDetailUseCase(courseRepo),
        enrollInCourseUseCase: EnrollInCourseUseCase(courseRepo),
        getCategoriesUseCase: GetCategoriesUseCase(courseRepo),
        getCoursesByCategoryUseCase: GetCoursesByCategoryUseCase(courseRepo),
        getEnrolledCoursesUseCase: GetEnrolledCoursesUseCase(courseRepo),
      );

      await tester.pumpWidget(
        _wrapDashboard(
          progressProvider: progressProvider,
          homeProvider: homeProvider,
          courseProvider: courseProvider,
          progressRepository: progressRepo,
        ),
      );
      await tester.pumpAndSettle();

      // 1. Initial error + retry recovers
      expect(find.text('Progress service unavailable'), findsOneWidget);
      failProgress = false;
      await tester.tap(find.text('Retry'));
      await tester.pumpAndSettle();

      // 2. Weekly error + retry recovers
      expect(find.text('Weekly summary unavailable'), findsOneWidget);
      failWeekly = false;
      await tester.tap(find.text('Retry'));
      await tester.pumpAndSettle();
      expect(find.text('Weekly summary unavailable'), findsNothing);
      expect(find.text('A1 Foundations'), findsOneWidget);

      // 3. Tapping CourseProgressCard navigates cleanly to CourseDetailScreen
      // and refreshes progress upon returning.
      currentXp = 170;
      await tester.ensureVisible(find.byType(CourseProgressCard));
      await tester.tap(find.byType(CourseProgressCard));
      await tester.pumpAndSettle();

      final detailScreen = tester.widget<CourseDetailScreen>(
        find.byType(CourseDetailScreen),
      );
      expect(detailScreen.courseId, 'course-123');

      final navigator = tester.state<NavigatorState>(find.byType(Navigator));
      navigator.pop();
      await tester.pumpAndSettle();

      expect(find.text('170'), findsOneWidget);
    },
  );
}
