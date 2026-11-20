import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:lexilingo_app/features/auth/data/services/guest_session_service.dart';
import 'package:lexilingo_app/features/auth/presentation/pages/guest_trial_shell_page.dart';
import 'package:lexilingo_app/features/mistakes/data/mistake_notebook_repository.dart';
import 'package:shared_preferences/shared_preferences.dart';

void main() {
  setUpAll(() {
    TestWidgetsFlutterBinding.ensureInitialized();
  });

  group('GuestSessionService (T19-T22)', () {
    test('bundled offline manifest grades deterministically via SHA-256 without raw answer keys', () async {
      SharedPreferences.setMockInitialValues({});
      final service = GuestSessionService(
        prefsFactory: SharedPreferences.getInstance,
      );

      final pack = GuestSessionService.bundledOfflineTrialPack();
      final questions = List<Map<String, dynamic>>.from(
        pack['quiz_questions'] as List,
      );
      for (final q in questions) {
        expect(q.containsKey('correct_answer'), isFalse);
        expect(q.containsKey('correct_option'), isFalse);
        expect(q['answer_digest'].toString().length, 64);
      }

      final grade = await service.evaluateTrialQuiz(
        questions: questions,
        selectedAnswers: {
          'gq-1': 'commutes',
          'gq-2': 'in', // wrong (correct is 'on')
          'gq-3': 'confirm',
          'gq-4': 'polite',
        },
      );

      expect(grade['correct_count'], 3);
      expect(grade['total_questions'], 4);
      expect(grade['score_percentage'], 75.0);
    });

    test('persists local guest progress and converts idempotently without cross-user leakage', () async {
      SharedPreferences.setMockInitialValues({});
      final service = GuestSessionService(
        prefsFactory: SharedPreferences.getInstance,
      );
      final mistakesRepo = MistakeNotebookRepository(
        prefsFactory: SharedPreferences.getInstance,
        syncEnabled: false,
      );

      await service.markVocabLearned('guest-vocab-1');
      await service.markTheoryViewed();
      await service.recordQuizResult(
        correctCount: 3,
        totalCount: 4,
        wrongAnswers: [
          {
            'question_id': 'gq-2',
            'prompt': 'The English club meets ___ Friday evening.',
            'selected_option': 'in',
            'correct_option': 'on',
            'explanation': 'Use on for days.',
            'skill': 'grammar',
          },
        ],
      );

      final loaded = await service.loadProgress();
      expect(loaded.guestXp, 45); // 10 + 5 + 30
      expect(loaded.learnedVocabIds, ['guest-vocab-1']);
      expect(await service.canOfferConversionFor('user-1'), isTrue);

      final res1 = await service.migrateToAuthenticatedAccount(
        userId: 'user-1',
        mistakeRepository: mistakesRepo,
      );
      expect(res1.migrated, isTrue);
      expect(res1.alreadyHandled, isFalse);
      expect(res1.migratedMistakesCount, 1);

      // Idempotent second call must not migrate again
      final res2 = await service.migrateToAuthenticatedAccount(
        userId: 'user-1',
        mistakeRepository: mistakesRepo,
      );
      expect(res2.migrated, isFalse);
      expect(res2.alreadyHandled, isTrue);
      expect(await service.canOfferConversionFor('user-1'), isFalse);

      final entries = await mistakesRepo.getEntries();
      expect(entries.length, 1);
      expect(entries.first.sourceType, 'guest_trial');
    });
  });

  group('GuestTrialShellPage widget flow', () {
    testWidgets('allows offline vocab flip, theory -> practice quiz, and gates protected tabs', (tester) async {
      SharedPreferences.setMockInitialValues({});
      final service = GuestSessionService(
        prefsFactory: SharedPreferences.getInstance,
      );
      var signInTriggered = false;

      await tester.pumpWidget(
        MaterialApp(
          home: GuestTrialShellPage(
            guestService: service,
            onSignInRequested: () => signInTriggered = true,
            onRegisterRequested: () {},
          ),
        ),
      );
      await tester.pumpAndSettle();

      // Learn first flashcard
      expect(find.text('commute'), findsOneWidget);
      await tester.tap(find.text('Đánh dấu đã thuộc'));
      await tester.pumpAndSettle();
      expect(find.textContaining('XP tạm: 10'), findsOneWidget);

      // Navigate to Grammar tab -> Theory before Practice
      await tester.tap(find.text('Ngữ pháp'));
      await tester.pumpAndSettle();
      expect(find.textContaining('Present Simple for Routines'), findsOneWidget);

      final startQuizBtn = find.text('Bắt đầu bài tập thử (4 câu)');
      await tester.ensureVisible(startQuizBtn);
      await tester.tap(startQuizBtn);
      await tester.pumpAndSettle();
      expect(find.text('Nộp bài (0/4)'), findsOneWidget);

      // Answer all 4 questions & submit
      for (final target in [
        find.widgetWithText(ChoiceChip, 'commutes').first,
        find.widgetWithText(ChoiceChip, 'on').first,
        find.widgetWithText(ChoiceChip, 'confirm').first,
        find.widgetWithText(ChoiceChip, 'polite').last,
      ]) {
        await tester.ensureVisible(target);
        await tester.tap(target);
        await tester.pump();
      }
      await tester.pumpAndSettle();

      await tester.ensureVisible(find.text('Nộp bài (4/4)'));
      await tester.tap(find.text('Nộp bài (4/4)'));
      await tester.pumpAndSettle();

      expect(find.text('Kết quả: 4/4 (100.0%)'), findsOneWidget);

      // Check gated tab CTA
      await tester.tap(find.text('Khóa học'));
      await tester.pumpAndSettle();
      await tester.tap(find.text('AI Tutor Chat'));
      await tester.pumpAndSettle();
      expect(find.text('Tính năng cần tài khoản (AI Tutor Chat)'), findsOneWidget);
      await tester.tap(find.text('Đăng nhập').last);
      await tester.pumpAndSettle();
      expect(signInTriggered, isTrue);
    });
  });
}
