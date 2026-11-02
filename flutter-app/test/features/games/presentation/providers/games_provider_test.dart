import 'dart:async';

import 'package:flutter_test/flutter_test.dart';
import 'package:lexilingo_app/features/games/data/repositories/games_repository.dart';
import 'package:lexilingo_app/features/games/domain/entities/game_entities.dart';
import 'package:lexilingo_app/features/games/presentation/providers/games_provider.dart';

class _FakeGamesRepository extends GamesRepository {
  int completionCalls = 0;
  int clearSessionCalls = 0;
  int newSessionCalls = 0;
  String? savedSessionId;
  GameSessionProgress? progress;
  GameAnswerFeedback? answerFeedback;
  final List<Object> outcomes;
  Completer<XPAwardResult>? pendingCompletion;

  _FakeGamesRepository({List<Object> outcomes = const []})
    : outcomes = List<Object>.of(outcomes);

  @override
  Future<XPAwardResult> completeGameSession({
    required String sessionId,
    required List<Map<String, String>> answers,
    int? clientDurationSeconds,
    int hintsUsed = 0,
  }) async {
    completionCalls++;
    if (pendingCompletion != null) return pendingCompletion!.future;
    final outcome = outcomes.removeAt(0);
    if (outcome is Exception) throw outcome;
    return outcome as XPAwardResult;
  }

  @override
  Future<String?> getSavedSessionId({
    required GameType gameType,
    required String level,
  }) async => savedSessionId;

  @override
  Future<GameSessionProgress> getGameSessionProgress(String sessionId) async {
    return progress!;
  }

  @override
  Future<void> saveSessionId({
    required GameType gameType,
    required String level,
    required String sessionId,
  }) async {
    savedSessionId = sessionId;
  }

  @override
  Future<void> clearSavedSession({
    required GameType gameType,
    required String level,
  }) async {
    clearSessionCalls++;
    savedSessionId = null;
  }

  @override
  Future<WordScrambleGame> getWordScramble({
    String level = 'A2',
    int count = 10,
  }) async {
    newSessionCalls++;
    return WordScrambleGame.fromJson(<String, dynamic>{
      'session_id': 'new-session',
      'cefr_level': level,
      'timer_seconds': 60,
      'base_xp_per_word': 10,
      'streak_bonus_threshold': 3,
      'words': <dynamic>[],
    });
  }

  @override
  Future<GameAnswerFeedback> saveGameAnswer({
    required String sessionId,
    required String itemId,
    required String answer,
  }) async {
    return answerFeedback!;
  }
}

const _award = XPAwardResult(
  xpAwarded: 10,
  baseXp: 10,
  newTotalXp: 110,
  oldLevel: 1,
  newLevel: 1,
  currentXpInLevel: 10,
);

const _answers = [
  {'id': 'q1', 'answer': 'cat'},
];

void main() {
  test('successful completion applies server award', () async {
    final repository = _FakeGamesRepository(outcomes: [_award]);
    final provider = GamesProvider(repository: repository);

    final result = await provider.completeGame(
      gameType: GameType.wordScramble,
      score: 1,
      totalQuestions: 1,
      correctAnswers: 1,
      answers: _answers,
      sessionId: 'session-1',
    );

    expect(result?.xpAwarded, 10);
    expect(provider.lastGameResult?.xpEarned, 10);
    expect(provider.awardStatus, GameAwardStatus.awarded);
    expect(repository.completionCalls, 1);
  });

  test('failed completion preserves payload and can retry', () async {
    final repository = _FakeGamesRepository(
      outcomes: [Exception('offline'), _award],
    );
    final provider = GamesProvider(repository: repository);

    final first = await provider.completeGame(
      gameType: GameType.wordScramble,
      score: 1,
      totalQuestions: 1,
      correctAnswers: 1,
      answers: _answers,
      sessionId: 'session-1',
    );
    final retried = await provider.retryLastCompletion();

    expect(first, isNull);
    expect(retried?.xpAwarded, 10);
    expect(provider.awardStatus, GameAwardStatus.awarded);
    expect(repository.completionCalls, 2);
  });

  test('completion cannot be submitted twice while in flight', () async {
    final repository = _FakeGamesRepository()
      ..pendingCompletion = Completer<XPAwardResult>();
    final provider = GamesProvider(repository: repository);

    final first = provider.completeGame(
      gameType: GameType.wordScramble,
      score: 1,
      totalQuestions: 1,
      correctAnswers: 1,
      answers: _answers,
      sessionId: 'session-1',
    );
    final second = await provider.completeGame(
      gameType: GameType.wordScramble,
      score: 1,
      totalQuestions: 1,
      correctAnswers: 1,
      answers: _answers,
      sessionId: 'session-1',
    );

    expect(second, isNull);
    expect(repository.completionCalls, 1);
    repository.pendingCompletion!.complete(_award);
    expect((await first)?.xpAwarded, 10);
  });

  test('already awarded completion returns cached result', () async {
    final repository = _FakeGamesRepository(outcomes: [_award]);
    final provider = GamesProvider(repository: repository);

    await provider.completeGame(
      gameType: GameType.wordScramble,
      score: 1,
      totalQuestions: 1,
      correctAnswers: 1,
      answers: _answers,
      sessionId: 'session-1',
    );
    final repeated = await provider.completeGame(
      gameType: GameType.wordScramble,
      score: 1,
      totalQuestions: 1,
      correctAnswers: 1,
      answers: _answers,
      sessionId: 'session-1',
    );

    expect(repeated?.xpAwarded, 10);
    expect(provider.awardStatus, GameAwardStatus.alreadyAwarded);
    expect(repository.completionCalls, 1);
  });

  test('load resumes server snapshot and restored finalized answers', () async {
    final repository = _FakeGamesRepository()
      ..savedSessionId = 'session-resume'
      ..progress = GameSessionProgress.fromJson(<String, dynamic>{
        'session_id': 'session-resume',
        'game_type': 'word_scramble',
        'cefr_level': 'A1',
        'status': 'in_progress',
        'content': <String, dynamic>{
          'timer_seconds': 60,
          'base_xp_per_word': 10,
          'streak_bonus_threshold': 3,
          'words': <dynamic>[
            <String, dynamic>{
              'word_id': 'w1',
              'word': 'cat',
              'shuffled_letters': <dynamic>['t', 'a', 'c'],
            },
          ],
        },
        'answers': <dynamic>[
          <String, dynamic>{
            'session_id': 'session-resume',
            'item_id': 'w1',
            'answer': 'cat',
            'is_correct': true,
            'correct_answer': 'cat',
            'explanation': <String, dynamic>{'summary': 'A small pet.'},
            'already_submitted': true,
          },
        ],
      });
    final provider = GamesProvider(repository: repository);

    await provider.loadWordScramble();

    expect(provider.wordScramble?.sessionId, 'session-resume');
    expect(provider.wordScramble?.words.single.word, 'cat');
    expect(provider.sessionAnswers['w1']?.isCorrect, isTrue);
    expect(repository.newSessionCalls, 0);
  });

  test('expired saved session is cleared before creating a new one', () async {
    final repository = _FakeGamesRepository()
      ..savedSessionId = 'session-expired'
      ..progress = GameSessionProgress.fromJson(<String, dynamic>{
        'session_id': 'session-expired',
        'game_type': 'word_scramble',
        'cefr_level': 'A1',
        'status': 'expired',
        'content': <String, dynamic>{'words': <dynamic>[]},
        'answers': <dynamic>[],
      });
    final provider = GamesProvider(repository: repository);

    await provider.loadWordScramble();

    expect(provider.wordScramble?.sessionId, 'new-session');
    expect(repository.clearSessionCalls, 1);
    expect(repository.newSessionCalls, 1);
    expect(repository.savedSessionId, 'new-session');
  });

  test(
    'saveAnswer keeps authoritative feedback for refresh hydration',
    () async {
      const feedback = GameAnswerFeedback(
        sessionId: 'session-1',
        itemId: 'q1',
        answer: 'has',
        isCorrect: true,
        correctAnswer: 'has',
        explanation: GameExplanation(summary: 'Use has with she.'),
      );
      final repository = _FakeGamesRepository()..answerFeedback = feedback;
      final provider = GamesProvider(repository: repository);

      final result = await provider.saveAnswer(
        sessionId: 'session-1',
        itemId: 'q1',
        answer: 'has',
      );

      expect(result, same(feedback));
      expect(provider.sessionAnswers['q1'], same(feedback));
    },
  );
}
