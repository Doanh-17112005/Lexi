import 'dart:async';
import 'dart:math';
import 'package:confetti/confetti.dart';
import 'package:easy_localization/easy_localization.dart';
import 'package:flutter/material.dart';
import 'package:lexilingo_app/core/widgets/lottie_loading_widget.dart';
import 'package:provider/provider.dart';
import 'package:lexilingo_app/core/theme/app_theme.dart';
import 'package:lexilingo_app/features/gamification/domain/entities/shop_item.dart';
import 'package:lexilingo_app/features/games/domain/entities/game_entities.dart';
import 'package:lexilingo_app/features/games/presentation/providers/games_provider.dart';
import 'package:lexilingo_app/features/games/presentation/screens/game_result_screen.dart';
import 'package:lexilingo_app/features/games/presentation/widgets/game_answer_explanation.dart';
import 'package:lexilingo_app/features/games/presentation/widgets/game_load_state.dart';
import 'package:lexilingo_app/features/games/presentation/widgets/game_powerup_tray.dart';
import 'package:lexilingo_app/features/games/presentation/widgets/game_question_navigation.dart';

const _matchingPowerUps = [
  ShopItemEntity.effectTimeFreeze,
  ShopItemEntity.effectExtraTime,
  ShopItemEntity.effectPairSwap,
  ShopItemEntity.effectLuckyClover,
  ShopItemEntity.effectScoreMultiplier,
];

/// Matching Game screen.
///
/// Two columns: words (left) and definitions/matches (right).
/// Player taps a word then taps its match. Correct pairs disappear with green
/// flash; wrong pairs shake red and apply a penalty.
class MatchingGameScreen extends StatefulWidget {
  const MatchingGameScreen({super.key});

  @override
  State<MatchingGameScreen> createState() => _MatchingGameScreenState();
}

class _MatchingGameScreenState extends State<MatchingGameScreen> {
  late ConfettiController _confettiController;
  Timer? _timer;
  int _timeLeft = 45;
  bool _gameLoaded = false;
  String? _selectedWord; // Word column selection (pair id)
  String? _selectedMatch; // Match column selection
  Set<String> _matchedIds = {};
  final Set<String> _answeredIds = {};
  final Map<String, String> _submittedAnswers = {};
  final Map<String, GameAnswerFeedback> _feedbackById = {};
  final List<String> _answerOrder = [];
  Map<String, _PairState> _matchState = {};
  int _correctCount = 0;
  bool _isFinishing = false;
  bool _isSavingAnswer = false;
  String? _answerSaveError;
  String? _reviewedPairId;
  bool _timeExpired = false;

  bool _isReviewMode = false;
  bool _luckyCloverActive = false;
  int _scoreMultiplier = 1;
  final _random = Random();

  @override
  void initState() {
    super.initState();
    _confettiController = ConfettiController(
      duration: const Duration(seconds: 2),
    );
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<GamesProvider>().loadMatchingGame().then((_) {
        if (mounted) _initGame();
      });
    });
  }

  @override
  void dispose() {
    _timer?.cancel();
    _confettiController.dispose();
    super.dispose();
  }

  void _initGame() {
    final provider = context.read<GamesProvider>();
    final game = provider.matching;
    if (game == null) return;
    _answeredIds.clear();
    _submittedAnswers.clear();
    _feedbackById.clear();
    _answerOrder.clear();
    _matchedIds = {};
    _matchState = {};
    _correctCount = 0;
    _timeExpired = false;
    for (final pair in game.pairs) {
      final feedback = provider.sessionAnswers[pair.wordId];
      if (feedback == null) continue;
      _answeredIds.add(pair.wordId);
      _submittedAnswers[pair.wordId] = feedback.answer;
      _feedbackById[pair.wordId] = feedback;
      _answerOrder.add(pair.wordId);
      _matchState[pair.wordId] = feedback.isCorrect
          ? _PairState.correct
          : _PairState.wrong;
      if (feedback.isCorrect) {
        _matchedIds.add(pair.wordId);
        _correctCount++;
      }
    }
    MatchingPair? firstUnanswered;
    for (final pair in game.pairs) {
      if (!_answeredIds.contains(pair.wordId)) {
        firstUnanswered = pair;
        break;
      }
    }
    setState(() {
      _gameLoaded = true;
      _isReviewMode = firstUnanswered == null;
      _timeLeft = game.timerSeconds;
      _selectedWord = firstUnanswered?.wordId;
      _selectedMatch = null;
      _reviewedPairId = _isReviewMode && _answerOrder.isNotEmpty
          ? _answerOrder.last
          : null;
    });
    if (!_isReviewMode) _startTimer(game.timerSeconds);
  }

  void _startTimer(int seconds) {
    _timer?.cancel();
    _timer = Timer.periodic(const Duration(seconds: 1), (t) {
      if (!mounted) {
        t.cancel();
        return;
      }
      setState(() => _timeLeft--);
      if (_timeLeft <= 0) {
        t.cancel();
        _expireGame();
      }
    });
  }

  void _selectWord(String pairId) {
    if (_answeredIds.contains(pairId) ||
        _isSavingAnswer ||
        _reviewedPairId != null) {
      return;
    }
    setState(() {
      _selectedWord = pairId;
      _selectedMatch = null;
    });
  }

  void _selectMatchItem(String matchText) {
    if (_selectedWord == null ||
        _answeredIds.contains(_selectedWord) ||
        _isSavingAnswer) {
      return;
    }
    final game = context.read<GamesProvider>().matching!;
    final pair = game.pairs.firstWhere((p) => p.wordId == _selectedWord);
    final correctMatch = pair.matchText;

    var matched = matchText == correctMatch;
    var submittedMatch = matchText;
    if (!matched && _luckyCloverActive && _random.nextDouble() < 0.3) {
      matched = true;
      submittedMatch = correctMatch;
      _luckyCloverActive = false;
    }

    if (matched) {
      _finalizePair(pair, submittedMatch, true);
    } else {
      _finalizePair(pair, submittedMatch, false);
    }
  }

  void _finalizePair(MatchingPair pair, String answer, bool isCorrect) {
    if (_answeredIds.contains(pair.wordId)) return;
    _answeredIds.add(pair.wordId);
    _answerOrder.add(pair.wordId);
    _submittedAnswers[pair.wordId] = answer;
    _matchState[pair.wordId] = isCorrect
        ? _PairState.correct
        : _PairState.wrong;
    if (isCorrect) {
      _matchedIds.add(pair.wordId);
      _correctCount++;
    }
    _feedbackById[pair.wordId] = GameAnswerFeedback(
      sessionId: '',
      itemId: pair.wordId,
      answer: answer,
      isCorrect: isCorrect,
      correctAnswer: pair.matchText,
      explanation: GameExplanation(
        summary: "'${pair.word}' matches '${pair.matchText}'.",
        rule: 'matchingGame.${pair.variant}'.tr(),
      ),
    );
    setState(() {
      _selectedWord = pair.wordId;
      _selectedMatch = answer;
      _reviewedPairId = pair.wordId;
    });
    _persistPair(pair);
  }

  Future<void> _persistPair(MatchingPair pair) async {
    final game = context.read<GamesProvider>().matching;
    if (game == null || _isSavingAnswer) return;
    setState(() {
      _isSavingAnswer = true;
      _answerSaveError = null;
    });
    final feedback = await context.read<GamesProvider>().saveAnswer(
      sessionId: game.sessionId,
      itemId: pair.wordId,
      answer: _submittedAnswers[pair.wordId] ?? '',
    );
    if (!mounted) return;
    setState(() {
      _isSavingAnswer = false;
      if (feedback == null) {
        _answerSaveError = 'save_failed';
        return;
      }
      final wasCorrect = _matchState[pair.wordId] == _PairState.correct;
      if (wasCorrect != feedback.isCorrect) {
        _correctCount += feedback.isCorrect ? 1 : -1;
        if (feedback.isCorrect) {
          _matchedIds.add(pair.wordId);
        } else {
          _matchedIds.remove(pair.wordId);
        }
      }
      _matchState[pair.wordId] = feedback.isCorrect
          ? _PairState.correct
          : _PairState.wrong;
      _feedbackById[pair.wordId] = feedback;
      _answerSaveError = null;
    });
  }

  void _onPowerUpUsed(String itemType, Map<String, dynamic> effects) {
    final game = context.read<GamesProvider>().matching;
    if (game == null) return;
    switch (itemType) {
      case ShopItemEntity.effectTimeFreeze:
      case ShopItemEntity.effectExtraTime:
        final seconds = (effects['seconds'] as num?)?.toInt() ?? 10;
        setState(
          () => _timeLeft = (_timeLeft + seconds).clamp(0, game.timerSeconds),
        );
        break;
      case ShopItemEntity.effectPairSwap:
        final remaining = game.pairs
            .where((p) => !_answeredIds.contains(p.wordId))
            .toList();
        if (remaining.isEmpty) return;
        final pair = remaining[_random.nextInt(remaining.length)];
        _finalizePair(pair, pair.matchText, true);
        break;
      case ShopItemEntity.effectLuckyClover:
        setState(() => _luckyCloverActive = true);
        break;
      case ShopItemEntity.effectScoreMultiplier:
        final multiplier = (effects['multiplier'] as num?)?.toInt() ?? 2;
        setState(() => _scoreMultiplier = multiplier);
        break;
    }
  }

  void _previousPair() {
    if (_reviewedPairId == null || _isSavingAnswer || _isFinishing) return;
    final current = _answerOrder.indexOf(_reviewedPairId!);
    if (current <= 0) return;
    final previousId = _answerOrder[current - 1];
    setState(() {
      _reviewedPairId = previousId;
      _selectedWord = previousId;
      _selectedMatch = _submittedAnswers[previousId];
    });
  }

  void _nextPair() {
    if (_isSavingAnswer || _answerSaveError != null || _isFinishing) return;
    final game = context.read<GamesProvider>().matching;
    if (game == null) return;
    final current = _reviewedPairId == null
        ? -1
        : _answerOrder.indexOf(_reviewedPairId!);
    if (current >= 0 && current + 1 < _answerOrder.length) {
      final nextId = _answerOrder[current + 1];
      setState(() {
        _reviewedPairId = nextId;
        _selectedWord = nextId;
        _selectedMatch = _submittedAnswers[nextId];
      });
      return;
    }
    MatchingPair? nextPair;
    for (final pair in game.pairs) {
      if (!_answeredIds.contains(pair.wordId)) {
        nextPair = pair;
        break;
      }
    }
    if (nextPair != null) {
      setState(() {
        _reviewedPairId = null;
        _selectedWord = nextPair!.wordId;
        _selectedMatch = null;
      });
      return;
    }
    _timer?.cancel();
    if (_correctCount == game.pairs.length) _confettiController.play();
    setState(() => _isReviewMode = true);
  }

  Future<void> _retryCurrentPairSave() async {
    final game = context.read<GamesProvider>().matching;
    if (game == null || _reviewedPairId == null) return;
    final pair = game.pairs.firstWhere(
      (candidate) => candidate.wordId == _reviewedPairId,
    );
    await _persistPair(pair);
    if (_timeExpired && _answerSaveError == null && mounted) {
      await _expireGame();
    }
  }

  Future<void> _expireGame() async {
    if (_isSavingAnswer || _isFinishing) return;
    final provider = context.read<GamesProvider>();
    final game = provider.matching;
    if (game == null) return;
    final unanswered = game.pairs
        .where((pair) => !_answeredIds.contains(pair.wordId))
        .toList();
    setState(() {
      _timeExpired = true;
      _isSavingAnswer = true;
      _answerSaveError = null;
      _isReviewMode = true;
    });
    for (final pair in unanswered) {
      _answeredIds.add(pair.wordId);
      _answerOrder.add(pair.wordId);
      _submittedAnswers[pair.wordId] = '';
      _matchState[pair.wordId] = _PairState.wrong;
      _reviewedPairId = pair.wordId;
      _feedbackById[pair.wordId] = GameAnswerFeedback(
        sessionId: game.sessionId,
        itemId: pair.wordId,
        answer: '',
        isCorrect: false,
        correctAnswer: pair.matchText,
        explanation: GameExplanation(
          summary: "'${pair.word}' matches '${pair.matchText}'.",
          rule: 'matchingGame.${pair.variant}'.tr(),
        ),
      );
      final feedback = await provider.saveAnswer(
        sessionId: game.sessionId,
        itemId: pair.wordId,
        answer: '',
      );
      if (feedback == null) {
        if (!mounted) return;
        setState(() {
          _isSavingAnswer = false;
          _answerSaveError = 'save_failed';
        });
        return;
      }
      _feedbackById[pair.wordId] = feedback;
    }
    if (!mounted) return;
    setState(() => _isSavingAnswer = false);
  }

  Future<void> _abandonGame() async {
    if (_isFinishing) return;
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text('games.exitTitle'.tr()),
        content: Text('games.exitXpByPairs'.tr()),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: Text('games.keepPlaying'.tr()),
          ),
          TextButton(
            onPressed: () => Navigator.pop(ctx, true),
            child: Text('games.exit'.tr()),
          ),
        ],
      ),
    );
    if (confirmed != true || !mounted || _isFinishing) return;
    _isFinishing = true;
    _timer?.cancel();
    final provider = context.read<GamesProvider>();
    final game = provider.matching;
    if (game != null) {
      await provider.completeGame(
        gameType: GameType.matching,
        score: _correctCount,
        totalQuestions: game.pairs.length,
        correctAnswers: _correctCount,
        answers: [
          for (final pair in game.pairs)
            {'id': pair.wordId, 'answer': _submittedAnswers[pair.wordId] ?? ''},
        ],
      );
    }
    if (mounted) Navigator.of(context).pop();
  }

  void _finishGame() async {
    if (_isFinishing) return;
    _isFinishing = true;
    _timer?.cancel();
    final provider = context.read<GamesProvider>();
    final game = provider.matching!;
    final total = game.pairs.length;

    final elapsed = game.timerSeconds - _timeLeft;
    final xpResult = await provider.completeGame(
      gameType: GameType.matching,
      score: _correctCount * _scoreMultiplier,
      totalQuestions: total,
      correctAnswers: _correctCount,
      answers: [
        for (final pair in game.pairs)
          {'id': pair.wordId, 'answer': _submittedAnswers[pair.wordId] ?? ''},
      ],
    );
    if (!mounted) return;
    Navigator.pushReplacement(
      context,
      MaterialPageRoute(
        builder: (_) => GameResultScreen(
          result: GameResult(
            gameType: GameType.matching,
            cefrLevel: provider.selectedLevel,
            score: _correctCount * _scoreMultiplier,
            totalQuestions: total,
            correctAnswers: _correctCount,
            xpEarned: xpResult?.xpAwarded ?? 0,
            durationSeconds: elapsed,
            xpResult: xpResult,
          ),
          xpResult: xpResult,
        ),
      ),
    );
  }

  Widget _buildPairFeedback(MatchingGame game) {
    final pairId = _reviewedPairId;
    if (pairId == null) return const SizedBox.shrink();
    final pair = game.pairs.firstWhere(
      (candidate) => candidate.wordId == pairId,
    );
    final feedback = _feedbackById[pairId];
    if (feedback == null) return const SizedBox.shrink();
    return ConstrainedBox(
      constraints: const BoxConstraints(maxHeight: 260),
      child: SingleChildScrollView(
        padding: const EdgeInsets.fromLTRB(12, 10, 12, 0),
        child: Column(
          children: [
            GameAnswerExplanationCard(
              isCorrect: feedback.isCorrect,
              selectedAnswer: feedback.answer,
              correctAnswer: pair.matchText,
              explanation: feedback.explanation,
            ),
            GameAnswerSaveStatus(
              isSaving: _isSavingAnswer,
              error: _answerSaveError,
              onRetry: _retryCurrentPairSave,
            ),
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return PopScope(
      canPop: false,
      onPopInvokedWithResult: (didPop, _) {
        if (!didPop) _abandonGame();
      },
      child: Consumer<GamesProvider>(
        builder: (context, provider, _) {
          if (provider.isLoading) {
            return const Scaffold(
              body: Center(child: LottieLoadingWidget.medium()),
            );
          }
          final game = provider.matching;
          if (provider.error != null) {
            return GameLoadState(
              message: 'games.loadFailed'.tr(),
              onRetry: () async {
                await provider.loadMatchingGame();
                if (mounted) _initGame();
              },
            );
          }
          if (game == null || game.pairs.isEmpty) {
            return GameLoadState(
              message: 'games.emptyGame'.tr(),
              onRetry: () async {
                await provider.loadMatchingGame();
                if (mounted) _initGame();
              },
            );
          }
          if (!_gameLoaded) {
            return const Scaffold(
              body: Center(child: LottieLoadingWidget.medium()),
            );
          }
          final remaining = game.pairs
              .where((p) => !_answeredIds.contains(p.wordId))
              .toList();

          return Scaffold(
            appBar: AppBar(
              backgroundColor: Theme.of(context).colorScheme.surface,
              elevation: 0,
              title: Text(
                'matchingGame.title'.tr(),
                style: TextStyle(
                  color: Theme.of(context).colorScheme.onSurface,
                ),
              ),
              actions: [
                Padding(
                  padding: const EdgeInsets.only(right: 12),
                  child: _TimerChip(
                    timeLeft: _timeLeft,
                    total: game.timerSeconds,
                  ),
                ),
              ],
            ),
            body: Stack(
              children: [
                Column(
                  children: [
                    LinearProgressIndicator(
                      value: _answeredIds.length / game.pairs.length,
                      backgroundColor: AppColors.grey200,
                      color: AppColors.greenSuccess,
                      minHeight: 4,
                    ),
                    Padding(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 12,
                        vertical: 8,
                      ),
                      child: GamePowerUpTray(
                        availableTypes: _matchingPowerUps,
                        onUse: _onPowerUpUsed,
                      ),
                    ),
                    if (_luckyCloverActive)
                      Padding(
                        padding: EdgeInsets.only(bottom: 6),
                        child: ActivePowerUpBadge(
                          itemType: ShopItemEntity.effectLuckyClover,
                          label: 'games.luckyCloverActive'.tr(),
                        ),
                      ),
                    Padding(
                      padding: const EdgeInsets.all(12),
                      child: Text(
                        'matchingGame.matchedProgress'.tr(
                          namedArgs: {
                            'matched': '${_answeredIds.length}',
                            'total': '${game.pairs.length}',
                          },
                        ),
                        style: TextStyle(
                          color: Theme.of(context).colorScheme.onSurfaceVariant,
                          fontSize: 13,
                        ),
                      ),
                    ),
                    if (_isReviewMode)
                      Expanded(
                        child: SingleChildScrollView(
                          padding: const EdgeInsets.all(16),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.stretch,
                            children: [
                              Container(
                                padding: const EdgeInsets.all(16),
                                decoration: BoxDecoration(
                                  color: AppColors.greenSuccess.withValues(
                                    alpha: 0.1,
                                  ),
                                  borderRadius: BorderRadius.circular(14),
                                  border: Border.all(
                                    color: AppColors.greenSuccess,
                                  ),
                                ),
                                child: Row(
                                  children: [
                                    const Icon(
                                      Icons.check_circle,
                                      color: AppColors.greenSuccess,
                                    ),
                                    const SizedBox(width: 12),
                                    Expanded(
                                      child: Text(
                                        '${'games.answerCorrect'.tr()}: '
                                        '$_correctCount / ${game.pairs.length}',
                                        style: const TextStyle(
                                          fontWeight: FontWeight.bold,
                                          fontSize: 16,
                                        ),
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                              const SizedBox(height: 16),
                              Text(
                                'games.choiceAnalysis'.tr(),
                                style: const TextStyle(
                                  fontWeight: FontWeight.bold,
                                  fontSize: 15,
                                ),
                              ),
                              const SizedBox(height: 10),
                              for (final p in game.pairs)
                                Container(
                                  margin: const EdgeInsets.only(bottom: 8),
                                  padding: const EdgeInsets.all(12),
                                  decoration: BoxDecoration(
                                    color: Theme.of(
                                      context,
                                    ).colorScheme.surface,
                                    borderRadius: BorderRadius.circular(10),
                                    border: Border.all(
                                      color:
                                          _matchState[p.wordId] ==
                                              _PairState.correct
                                          ? AppColors.greenSuccess
                                          : Theme.of(
                                              context,
                                            ).colorScheme.outlineVariant,
                                    ),
                                  ),
                                  child: Row(
                                    children: [
                                      Icon(
                                        _matchState[p.wordId] ==
                                                _PairState.correct
                                            ? Icons.check_circle
                                            : Icons.cancel_outlined,
                                        color:
                                            _matchState[p.wordId] ==
                                                _PairState.correct
                                            ? AppColors.greenSuccess
                                            : AppColors.errorBright,
                                        size: 18,
                                      ),
                                      const SizedBox(width: 10),
                                      Text(
                                        p.word,
                                        style: const TextStyle(
                                          fontWeight: FontWeight.bold,
                                        ),
                                      ),
                                      const SizedBox(width: 8),
                                      const Text('—'),
                                      const SizedBox(width: 8),
                                      Expanded(
                                        child: Text(
                                          p.matchText,
                                          style: TextStyle(
                                            color: Theme.of(
                                              context,
                                            ).colorScheme.onSurfaceVariant,
                                          ),
                                        ),
                                      ),
                                    ],
                                  ),
                                ),
                              const SizedBox(height: 20),
                              GameAnswerSaveStatus(
                                isSaving: _isSavingAnswer,
                                error: _answerSaveError,
                                onRetry: _retryCurrentPairSave,
                              ),
                              FilledButton.icon(
                                onPressed:
                                    _isFinishing ||
                                        _isSavingAnswer ||
                                        _answerSaveError != null ||
                                        _answeredIds.length != game.pairs.length
                                    ? null
                                    : _finishGame,
                                icon: const Icon(Icons.flag_rounded),
                                label: Text('games.finishGame'.tr()),
                              ),
                            ],
                          ),
                        ),
                      )
                    else
                      Expanded(
                        child: Column(
                          children: [
                            Expanded(
                              child: Padding(
                                padding: const EdgeInsets.symmetric(
                                  horizontal: 12,
                                ),
                                child: Row(
                                  children: [
                                    // Words column
                                    Expanded(
                                      child: _ColumnList(
                                        items: remaining
                                            .map((p) => p.word)
                                            .toList(),
                                        selectedItem: _selectedWord != null
                                            ? game.pairs
                                                  .firstWhere(
                                                    (p) =>
                                                        p.wordId ==
                                                        _selectedWord,
                                                  )
                                                  .word
                                            : null,
                                        pairStates: Map.fromEntries(
                                          remaining.map(
                                            (p) => MapEntry(
                                              p.word,
                                              _matchState[p.wordId],
                                            ),
                                          ),
                                        ),
                                        onTap: (word) {
                                          final p = game.pairs.firstWhere(
                                            (p) => p.word == word,
                                          );
                                          _selectWord(p.wordId);
                                        },
                                        label: 'matchingGame.wordsColumnLabel'
                                            .tr(),
                                      ),
                                    ),
                                    const SizedBox(width: 10),
                                    // Matches column
                                    Expanded(
                                      child: _ColumnList(
                                        items: game.definitionsColumn
                                            .where(
                                              (m) => !_answeredIds.any((id) {
                                                try {
                                                  return game.pairs
                                                          .firstWhere(
                                                            (p) =>
                                                                p.wordId == id,
                                                          )
                                                          .matchText ==
                                                      m;
                                                } catch (_) {
                                                  return false;
                                                }
                                              }),
                                            )
                                            .toList(),
                                        selectedItem: _selectedMatch,
                                        pairStates: const {},
                                        onTap: _selectMatchItem,
                                        label: game.variant == 'definition'
                                            ? 'matchingGame.definitionsLabel'
                                                  .tr()
                                            : 'matchingGame.matchesLabel'.tr(),
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                            ),
                            if (_reviewedPairId != null) ...[
                              _buildPairFeedback(game),
                              Padding(
                                padding: const EdgeInsets.fromLTRB(
                                  12,
                                  8,
                                  12,
                                  12,
                                ),
                                child: GameQuestionNavigation(
                                  canGoPrevious:
                                      _answerOrder.indexOf(_reviewedPairId!) >
                                      0,
                                  canGoNext:
                                      !_isSavingAnswer &&
                                      _answerSaveError == null,
                                  isLastQuestion:
                                      _answeredIds.length == game.pairs.length,
                                  isBusy:
                                      _isSavingAnswer ||
                                      _answerSaveError != null ||
                                      _isFinishing,
                                  onPrevious: _previousPair,
                                  onNext: _nextPair,
                                ),
                              ),
                            ],
                          ],
                        ),
                      ),
                  ],
                ),
                // Confetti overlay (skill: gamification-confetti-win)
                Align(
                  alignment: Alignment.topCenter,
                  child: ConfettiWidget(
                    confettiController: _confettiController,
                    blastDirectionality: BlastDirectionality.explosive,
                    numberOfParticles: 20,
                    gravity: 0.4,
                    colors: const [
                      AppColors.primary,
                      Colors.yellow,
                      AppColors.greenSuccessBright,
                      AppColors.orange,
                    ],
                  ),
                ),
              ],
            ),
          );
        },
      ),
    );
  }
}

enum _PairState { correct, wrong }

class _ColumnList extends StatelessWidget {
  final List<String> items;
  final String? selectedItem;
  final Map<String, _PairState?> pairStates;
  final ValueChanged<String> onTap;
  final String label;

  const _ColumnList({
    required this.items,
    required this.selectedItem,
    required this.pairStates,
    required this.onTap,
    required this.label,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          label,
          style: TextStyle(
            fontWeight: FontWeight.bold,
            fontSize: 13,
            color: Theme.of(context).colorScheme.onSurfaceVariant,
          ),
        ),
        const SizedBox(height: 6),
        Expanded(
          child: ListView.builder(
            itemCount: items.length,
            itemBuilder: (_, i) {
              final item = items[i];
              final selected = selectedItem == item;
              final state = pairStates[item];
              Color bg = Theme.of(context).colorScheme.surface;
              Color border = Theme.of(context).colorScheme.outlineVariant;
              if (selected) {
                bg = AppColors.primary.withValues(alpha: 0.1);
                border = AppColors.primary;
              }
              if (state == _PairState.correct) {
                bg = AppColors.greenSuccess.withValues(alpha: 0.15);
                border = AppColors.greenSuccess;
              }
              if (state == _PairState.wrong) {
                bg = Colors.red.withValues(alpha: 0.1);
                border = AppColors.errorBright;
              }
              return GestureDetector(
                onTap: () => onTap(item),
                child: AnimatedContainer(
                  duration: const Duration(milliseconds: 180),
                  margin: const EdgeInsets.only(bottom: 8),
                  padding: const EdgeInsets.symmetric(
                    horizontal: 12,
                    vertical: 12,
                  ),
                  decoration: BoxDecoration(
                    color: bg,
                    borderRadius: BorderRadius.circular(10),
                    border: Border.all(color: border, width: 1.5),
                  ),
                  child: Text(
                    item,
                    style: TextStyle(
                      fontSize: 13,
                      color: Theme.of(context).colorScheme.onSurface,
                    ),
                    maxLines: 3,
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
              );
            },
          ),
        ),
      ],
    );
  }
}

class _TimerChip extends StatelessWidget {
  final int timeLeft;
  final int total;
  const _TimerChip({required this.timeLeft, required this.total});

  @override
  Widget build(BuildContext context) {
    final ratio = total > 0 ? timeLeft / total : 0.0;
    final color = ratio > 0.5
        ? AppColors.greenSuccess
        : ratio > 0.25
        ? AppColors.orange
        : AppColors.errorBright;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.1),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: color),
      ),
      child: Text(
        '${timeLeft}s',
        style: TextStyle(
          fontWeight: FontWeight.bold,
          color: color,
          fontSize: 14,
        ),
      ),
    );
  }
}
