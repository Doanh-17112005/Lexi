import 'package:easy_localization/easy_localization.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:lexilingo_app/core/network/api_client.dart';
import 'package:lexilingo_app/features/level/data/datasources/proficiency_data_source.dart';
import 'package:lexilingo_app/features/level/presentation/pages/placement_test_page.dart';
import 'package:lexilingo_app/features/level/presentation/providers/placement_test_provider.dart';
import 'package:lexilingo_app/features/level/presentation/providers/proficiency_provider.dart';
import 'package:provider/provider.dart';
import 'package:shared_preferences/shared_preferences.dart';

class _PlacementAssetLoader extends AssetLoader {
  const _PlacementAssetLoader();

  @override
  Future<Map<String, dynamic>> load(String path, Locale locale) async => {
    'common': {'retry': 'Retry', 'done': 'Done'},
    'assessment': {
      'placementTest': 'Placement Test',
      'questionCounter': 'Question {current}/{total}',
      'answeredCount': '{answered}/{total} answered',
      'points': '{points} pts',
      'previous': 'Previous',
      'next': 'Next',
      'submitTest': 'Submit Test',
      'answerAllQuestions': 'Answer all questions first',
      'testCompleted': 'Assessment Complete',
      'yourLevelIs': 'Estimated CEFR: {level}',
      'score': 'Score',
      'correct': 'Objective Correct',
      'retakeTest': 'Retake',
      'loadFailed': 'Load Failed',
      'noQuestions': 'No Questions',
      'noQuestionsSubtitle': 'Try again later',
    },
  };
}

class _FakeProficiencyDataSource extends ProficiencyDataSource {
  int startCalls = 0;
  int submitCalls = 0;
  final Map<String, Map<String, dynamic>> savedDrafts = {};

  _FakeProficiencyDataSource() : super(apiClient: ApiClient());

  @override
  Future<Map<String, dynamic>> startSixSkillPlacementTest() async {
    startCalls++;
    return {
      'attempt_id': 'att-6skill-1',
      'status': 'in_progress',
      'skills': [
        'listening',
        'speaking',
        'reading',
        'writing',
        'grammar',
        'vocabulary',
      ],
      'disclaimer': 'Internal LexiLingo placement estimate — not an official CEFR certification.',
      'questions': [
        {
          'id': 'q-listen',
          'skill': 'listening',
          'task_type': 'listening_mcq',
          'level': 'A2',
          'points': 10,
          'listening_script': 'Go to Platform 6.',
          'question': 'Which platform?',
          'options': ['Platform 6', 'Platform 3'],
        },
        {
          'id': 'q-speak',
          'skill': 'speaking',
          'task_type': 'speaking_rubric',
          'level': 'B1',
          'points': 20,
          'min_words': 10,
          'rubric_criteria': ['Fluency', 'Keywords'],
          'question': 'Describe your daily English habit.',
        },
        {
          'id': 'q-write',
          'skill': 'writing',
          'task_type': 'writing_rubric',
          'level': 'B1',
          'points': 20,
          'min_words': 15,
          'rubric_criteria': ['Structure', 'Connectors'],
          'question': 'Write your learning goal.',
        },
      ],
    };
  }

  @override
  Future<Map<String, dynamic>> saveSixSkillAnswer({
    required String attemptId,
    required String taskId,
    int? selectedOption,
    String? textResponse,
  }) async {
    savedDrafts[taskId] = {
      if (selectedOption != null) 'selected_option': selectedOption,
      if (textResponse != null) 'text_response': textResponse,
    };
    return {'saved_task_id': taskId};
  }

  @override
  Future<Map<String, dynamic>> submitSixSkillPlacementTest({
    required String attemptId,
    required List<Map<String, dynamic>> answers,
    required int timeTakenSeconds,
    String? idempotencyKey,
  }) async {
    submitCalls++;
    return {
      'attempt_id': attemptId,
      'assessed_level': 'B1',
      'score_percentage': 78.5,
      'correct_count': 1,
      'total_questions': 1,
      'disclaimer': 'Internal LexiLingo placement estimate — not an official CEFR certification.',
      'skill_scores': {
        'listening': 100.0,
        'speaking': 75.0,
        'reading': 70.0,
        'writing': 80.0,
        'grammar': 75.0,
        'vocabulary': 70.0,
      },
      'recommendations': [
        {'skill': 'reading', 'score': 70.0, 'advice': 'Read short articles daily.'},
      ],
      'recommended_courses': [
        {'id': 'c1', 'title': 'B1 Intermediate Path', 'level': 'B1', 'total_lessons': 10},
      ],
    };
  }
}

void main() {
  setUpAll(() async {
    TestWidgetsFlutterBinding.ensureInitialized();
    SharedPreferences.setMockInitialValues({});
    await EasyLocalization.ensureInitialized();
  });

  testWidgets('6-skill PlacementTestPage completes listening, speaking, and writing tasks and shows 6-skill breakdown + disclaimer', (tester) async {
    SharedPreferences.setMockInitialValues({});
    final ds = _FakeProficiencyDataSource();
    final provider = PlacementTestProvider(
      dataSource: ds,
      prefsFactory: SharedPreferences.getInstance,
    );
    final profProvider = ProficiencyProvider(dataSource: ds);

    await tester.pumpWidget(
      EasyLocalization(
        supportedLocales: const [Locale('en')],
        path: 'assets/translations',
        fallbackLocale: const Locale('en'),
        startLocale: const Locale('en'),
        useOnlyLangCode: true,
        assetLoader: const _PlacementAssetLoader(),
        child: MultiProvider(
          providers: [
            ChangeNotifierProvider<PlacementTestProvider>.value(value: provider),
            ChangeNotifierProvider<ProficiencyProvider>.value(value: profProvider),
          ],
          child: Builder(
            builder: (context) => MaterialApp(
              locale: context.locale,
              supportedLocales: context.supportedLocales,
              localizationsDelegates: context.localizationDelegates,
              home: const PlacementTestPage(),
            ),
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();

    expect(ds.startCalls, 1);
    expect(find.text('LISTENING'), findsOneWidget);
    await tester.tap(find.text('Xem lời thoại'));
    await tester.pumpAndSettle();
    expect(find.text('Go to Platform 6.'), findsOneWidget);

    await tester.tap(find.text('Platform 6'));
    await tester.pumpAndSettle();

    await tester.drag(find.byType(ListView), const Offset(0, -350));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Next'));
    await tester.pumpAndSettle();
    expect(find.text('SPEAKING'), findsOneWidget);
    await tester.enterText(
      find.byType(TextField),
      'I practice English listening and speaking every morning because it helps my fluency.',
    );
    await tester.pumpAndSettle();

    await tester.drag(find.byType(ListView), const Offset(0, -350));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Next'));
    await tester.pumpAndSettle();
    expect(find.text('WRITING'), findsOneWidget);
    await tester.enterText(
      find.byType(TextField),
      'My English learning goal is to improve my writing and grammar through weekly practice.',
    );
    await tester.pumpAndSettle();

    await tester.drag(find.byType(ListView), const Offset(0, -350));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Submit Test'));
    await tester.pumpAndSettle();

    expect(ds.submitCalls, 1);
    expect(find.text('Estimated CEFR: B1'), findsOneWidget);
    expect(find.text('Kết quả theo 6 kỹ năng'), findsOneWidget);
    expect(
      find.textContaining('not an official CEFR certification'),
      findsOneWidget,
    );
    expect(find.text('B1 Intermediate Path'), findsOneWidget);
  });
}
