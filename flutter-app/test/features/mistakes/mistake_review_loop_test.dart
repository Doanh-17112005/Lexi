import 'package:easy_localization/easy_localization.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:lexilingo_app/features/mistakes/data/mistake_notebook_remote_datasource.dart';
import 'package:lexilingo_app/features/mistakes/data/mistake_notebook_repository.dart';
import 'package:lexilingo_app/features/mistakes/domain/mistake_notebook_entry.dart';
import 'package:lexilingo_app/features/mistakes/presentation/pages/mistake_notebook_page.dart';
import 'package:shared_preferences/shared_preferences.dart';

class _MistakeAssetLoader extends AssetLoader {
  const _MistakeAssetLoader();

  @override
  Future<Map<String, dynamic>> load(String path, Locale locale) async => {
    'common': {'cancel': 'Cancel'},
    'mistakeNotebook': {
      'title': 'Mistake Notebook',
      'totalMistakes': 'Total',
      'unreviewed': 'Unreviewed',
      'reviewed': 'Reviewed',
      'reviewedTimes': 'Reviewed {count}x',
      'filterAll': 'All',
      'filterUnreviewed': 'Unreviewed',
      'filterReviewed': 'Reviewed',
      'markReviewed': 'Mark Reviewed',
      'delete': 'Delete',
      'deleteTitle': 'Delete',
      'deleteMessage': 'Delete?',
      'emptyTitle': 'Empty',
      'emptySubtitle': 'No mistakes',
      'emptyFilteredTitle': 'Empty',
      'emptyFilteredSubtitle': 'None in filter',
      'yourAnswer': 'Your answer',
      'correctAnswer': 'Correct answer',
      'explanation': 'Explanation',
    },
  };
}

class _FakeRemoteDataSource implements MistakeNotebookRemoteDataSource {
  final Map<String, MistakeNotebookEntry> store = {};
  int reviewCalls = 0;
  int reopenCalls = 0;

  @override
  Future<void> delete(String id) async {
    store.remove(id);
  }

  @override
  Future<List<MistakeNotebookEntry>> getEntries({String status = 'all'}) async {
    return store.values.toList();
  }

  @override
  Future<MistakeNotebookEntry> markReviewed(String id) async {
    reviewCalls++;
    final current = store[id]!;
    final updated = current.copyWith(
      reviewedAt: DateTime.now(),
      reviewCount: current.reviewCount + 1,
    );
    store[id] = updated;
    return updated;
  }

  @override
  Future<MistakeNotebookEntry> reopen(String id) async {
    reopenCalls++;
    final current = store[id]!;
    final updated = current.copyWith(clearReviewedAt: true);
    store[id] = updated;
    return updated;
  }

  @override
  Future<MistakeNotebookEntry> saveMistake(MistakeNotebookEntry entry) async {
    store[entry.id] = entry;
    return entry;
  }
}

void main() {
  setUpAll(() async {
    TestWidgetsFlutterBinding.ensureInitialized();
    SharedPreferences.setMockInitialValues({});
    await EasyLocalization.ensureInitialized();
  });

  testWidgets(
    'Mistake review session reopens on wrong retry and marks reviewed on correct retry',
    (tester) async {
      SharedPreferences.setMockInitialValues({});
      final remote = _FakeRemoteDataSource();
      final repo = MistakeNotebookRepository(
        prefsFactory: SharedPreferences.getInstance,
        remoteDataSource: remote,
        syncEnabled: true,
      );

      final entry = MistakeNotebookEntry(
        id: 'm-1',
        sourceType: 'course_lesson',
        sourceId: 'les-1:ex-1',
        sourceTitle: 'Present Simple',
        question: 'She ___ to school.',
        selectedAnswer: 'go',
        correctAnswer: 'walks',
        explanation: 'Use -s for 3rd person singular.',
        skill: 'grammar',
        createdAt: DateTime(2026, 1, 1),
      );
      await repo.saveMistake(entry);

      await tester.pumpWidget(
        EasyLocalization(
          supportedLocales: const [Locale('en')],
          path: 'assets/translations',
          fallbackLocale: const Locale('en'),
          startLocale: const Locale('en'),
          useOnlyLangCode: true,
          assetLoader: const _MistakeAssetLoader(),
          child: Builder(
            builder: (context) => MaterialApp(
              locale: context.locale,
              supportedLocales: context.supportedLocales,
              localizationsDelegates: context.localizationDelegates,
              home: MistakeNotebookPage(repository: repo),
            ),
          ),
        ),
      );
      await tester.pumpAndSettle();

      expect(find.text('Practice Mistakes (1)'), findsOneWidget);

      // 1. Open review session & submit wrong answer -> calls reopen
      await tester.tap(find.text('Practice Mistakes (1)'));
      await tester.pumpAndSettle();

      await tester.enterText(find.byType(TextField), 'walk');
      await tester.tap(find.text('Check'));
      await tester.pumpAndSettle();

      expect(
        find.text('Incorrect. Correct answer: walks'),
        findsOneWidget,
      );
      expect(remote.reopenCalls, 1);

      await tester.tap(find.text('Finish'));
      await tester.pumpAndSettle();

      // Still 1 unreviewed
      expect(find.text('Practice Mistakes (1)'), findsOneWidget);

      // 2. Open review session again & submit correct answer -> calls markReviewed
      await tester.tap(find.text('Practice Mistakes (1)'));
      await tester.pumpAndSettle();

      await tester.enterText(find.byType(TextField), 'walks');
      await tester.tap(find.text('Check'));
      await tester.pumpAndSettle();

      expect(find.text('Correct! Marked as reviewed.'), findsOneWidget);
      expect(remote.reviewCalls, 1);

      await tester.tap(find.text('Finish'));
      await tester.pumpAndSettle();

      expect(find.text('Practice Mistakes (1)'), findsNothing);
    },
  );
}
