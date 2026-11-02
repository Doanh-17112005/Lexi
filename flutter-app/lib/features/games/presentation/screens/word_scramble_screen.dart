import 'dart:async';
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

const _wordScramblePowerUps = [
  ShopItemEntity.effectTimeFreeze,
  ShopItemEntity.effectExtraTime,
  ShopItemEntity.effectSkipToken,
  ShopItemEntity.effectRevealHint,
  ShopItemEntity.effectTranslateHint,
  ShopItemEntity.effectScoreMultiplier,
];

/// Word Scramble game screen.
///
/// Players unscramble letters to form target English vocabulary words.
/// Features interactive letter slots, hints, step-by-step navigation,
/// and comprehensive vocabulary explanations.
class WordScrambleScreen extends StatefulWidget {
  const WordScrambleScreen({super.key});

  @override
  State<WordScrambleScreen> createState() => _WordScrambleScreenState();
}

class _WordScrambleScreenState extends State<WordScrambleScreen> {
  late ConfettiController _confettiController;
  Timer? _timer;
  int _currentWordIndex = 0;
  int _timeLeft = 60;
  int _correctCount = 0;
  bool _showHint = false;
  String? _translationReveal;
  bool _wordAnswered = false;
  bool _gameLoaded = false;
  bool _isFinishing = false;
  bool _isSavingAnswer = false;
  bool _restoredSession = false;
  String? _answerSaveError;
  String? _xpPopup;
  int _scoreMultiplier = 1;

  late List<String?> _answerSlots;
  late List<String> _poolLetters;
  late List<bool> _slotCorrect;
  late List<bool> _slotWrong;

  final Map<String, String> _submittedAnswers = {};
  final Set<int> _answeredIndices = {};
  final Map<int, bool> _wordSolved = {};
  final Map<int, GameExplanation> _explanations = {};

  @override
  void initState() {
    super.initState();
    _confettiController = ConfettiController(
      duration: const Duration(seconds: 2),
    );
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<GamesProvider>().loadWordScramble().then((_) {
        if (mounted) _loadCurrentWord();
      });
    });
  }

  @override
  void dispose() {
    _timer?.cancel();
    _confettiController.dispose();
    super.dispose();
  }

  void _loadCurrentWord() {
    final provider = context.read<GamesProvider>();
    final game = provider.wordScramble;
    if (game == null || game.words.isEmpty) return;
    _restoreSessionAnswers(provider, game);

    if (_answeredIndices.contains(_currentWordIndex)) {
      _timer?.cancel();
      final word = game.words[_currentWordIndex];
      final targetLetters = word.word.toUpperCase().split('');
      final solved = _wordSolved[_currentWordIndex] ?? false;
      setState(() {
        _gameLoaded = true;
        _wordAnswered = true;
        _showHint = true;
        _translationReveal = word.vietnameseTranslation;
        _answerSlots = targetLetters;
        _slotCorrect = List<bool>.filled(targetLetters.length, solved);
        _slotWrong = List<bool>.filled(targetLetters.length, !solved);
        _poolLetters = List<String>.filled(targetLetters.length, '');
      });
    } else {
      _initWord();
    }
  }

  void _restoreSessionAnswers(GamesProvider provider, WordScrambleGame game) {
    if (_restoredSession) return;
    _restoredSession = true;
    for (var index = 0; index < game.words.length; index++) {
      final word = game.words[index];
      final feedback = provider.sessionAnswers[word.wordId];
      if (feedback == null) continue;
      _submittedAnswers[word.wordId] = feedback.answer;
      _wordSolved[index] = feedback.isCorrect;
      _explanations[index] = feedback.explanation;
      _answeredIndices.add(index);
      if (feedback.isCorrect) _correctCount++;
    }
    if (_answeredIndices.isNotEmpty) {
      _currentWordIndex = List.generate(game.words.length, (index) => index)
          .firstWhere(
            (index) => !_answeredIndices.contains(index),
            orElse: () => game.words.length - 1,
          );
    }
  }

  void _initWord() {
    final game = context.read<GamesProvider>().wordScramble;
    if (game == null || _currentWordIndex >= game.words.length) return;
    final word = game.words[_currentWordIndex];
    setState(() {
      _gameLoaded = true;
      _wordAnswered = false;
      _showHint = false;
      _translationReveal = null;
      _xpPopup = null;
      _answerSlots = List<String?>.filled(word.word.length, null);
      _slotCorrect = List<bool>.filled(word.word.length, false);
      _slotWrong = List<bool>.filled(word.word.length, false);
      _poolLetters = List<String>.from(word.shuffledLetters);
    });
    _startTimer(game.timerSeconds);
  }

  void _onPowerUpUsed(String itemType, Map<String, dynamic> effects) {
    if (_wordAnswered) return;
    final game = context.read<GamesProvider>().wordScramble;
    if (game == null) return;
    final word = game.words[_currentWordIndex];
    switch (itemType) {
      case ShopItemEntity.effectTimeFreeze:
      case ShopItemEntity.effectExtraTime:
        final seconds = (effects['seconds'] as num?)?.toInt() ?? 10;
        setState(
          () => _timeLeft = (_timeLeft + seconds).clamp(0, game.timerSeconds),
        );
        break;
      case ShopItemEntity.effectSkipToken:
        _skipWord();
        break;
      case ShopItemEntity.effectRevealHint:
        _revealLetter(word);
        break;
      case ShopItemEntity.effectTranslateHint:
        setState(() => _translationReveal = word.vietnameseTranslation);
        break;
      case ShopItemEntity.effectScoreMultiplier:
        final multiplier = (effects['multiplier'] as num?)?.toInt() ?? 2;
        setState(() => _scoreMultiplier = multiplier);
        break;
    }
  }

  void _revealLetter(ScrambleWord word) {
    final correctLetters = word.word.toUpperCase().split('');
    final emptySlot = _answerSlots.indexWhere((s) => s == null);
    if (emptySlot == -1) return;
    final neededLetter = correctLetters[emptySlot];
    final poolIdx = _poolLetters.indexWhere((l) => l == neededLetter);
    if (poolIdx == -1) return;
    setState(() {
      _poolLetters[poolIdx] = '';
      _answerSlots[emptySlot] = neededLetter;
    });
    _checkAnswer();
  }

  void _startTimer(int seconds) {
    _timer?.cancel();
    _timeLeft = seconds;
    _timer = Timer.periodic(const Duration(seconds: 1), (t) {
      if (!mounted) {
        t.cancel();
        return;
      }
      setState(() => _timeLeft--);
      if (_timeLeft <= 0) {
        t.cancel();
        _skipWord();
      }
    });
  }

  void _tapPool(int index) {
    if (_wordAnswered || _answeredIndices.contains(_currentWordIndex)) return;
    final letter = _poolLetters[index];
    if (letter.isEmpty) return;
    final slotIdx = _answerSlots.indexWhere((s) => s == null);
    if (slotIdx == -1) return;
    setState(() {
      _poolLetters[index] = '';
      _answerSlots[slotIdx] = letter;
    });
    _checkAnswer();
  }

  void _tapSlot(int index) {
    if (_wordAnswered || _answeredIndices.contains(_currentWordIndex)) return;
    final letter = _answerSlots[index];
    if (letter == null || letter.isEmpty) return;
    final poolIdx = _poolLetters.indexWhere((l) => l.isEmpty);
    setState(() {
      _answerSlots[index] = null;
      if (poolIdx != -1) {
        _poolLetters[poolIdx] = letter;
      } else {
        _poolLetters.add(letter);
      }
    });
  }

  void _checkAnswer() {
    if (_answerSlots.any((s) => s == null)) return;
    final provider = context.read<GamesProvider>();
    final game = provider.wordScramble;
    if (game == null) return;
    final word = game.words[_currentWordIndex];
    final answer = _answerSlots.join().toLowerCase();
    final correct = word.word.toLowerCase();

    final isCorrect = answer == correct;
    _timer?.cancel();
    _submittedAnswers[word.wordId] = answer;
    _answeredIndices.add(_currentWordIndex);
    _wordSolved[_currentWordIndex] = isCorrect;
    if (isCorrect) _correctCount++;

    _explanations[_currentWordIndex] = GameExplanation(
      summary:
          '${'games.correctAnswer'.tr()}: ${word.word} (${word.ipaPronunciation ?? ''}) - ${word.vietnameseTranslation ?? word.definition}',
      rule: word.definition,
      example: word.exampleSentence ?? word.hint,
    );

    final targetLetters = word.word.toUpperCase().split('');
    setState(() {
      _answerSlots = targetLetters;
      _poolLetters = List<String>.filled(targetLetters.length, '');
      _slotCorrect = List<bool>.filled(targetLetters.length, isCorrect);
      _slotWrong = List<bool>.filled(targetLetters.length, !isCorrect);
      _wordAnswered = true;
      _xpPopup = isCorrect ? '+${word.xpValue * _scoreMultiplier} XP' : null;
    });
    if (isCorrect) _confettiController.play();
    _persistAnswer(game.sessionId, word.wordId, answer, _currentWordIndex);
  }

  void _previousWord() {
    if (_currentWordIndex <= 0 || _isFinishing) return;
    _timer?.cancel();
    setState(() => _currentWordIndex--);
    _loadCurrentWord();
  }

  void _nextWord() {
    if (!mounted || _isFinishing) return;
    final game = context.read<GamesProvider>().wordScramble;
    if (game == null) return;
    if (_currentWordIndex + 1 >= game.words.length) {
      _finishGame();
      return;
    }
    _timer?.cancel();
    setState(() => _currentWordIndex++);
    _loadCurrentWord();
  }

  void _skipWord() {
    if (_wordAnswered || _answeredIndices.contains(_currentWordIndex)) return;
    _timer?.cancel();
    final provider = context.read<GamesProvider>();
    final game = provider.wordScramble;
    if (game == null) return;
    final word = game.words[_currentWordIndex];

    _submittedAnswers[word.wordId] = '';
    _answeredIndices.add(_currentWordIndex);
    _wordSolved[_currentWordIndex] = false;

    final explanation = GameExplanation(
      summary:
          '${'games.correctAnswer'.tr()}: ${word.word} (${word.ipaPronunciation ?? ''}) - ${word.vietnameseTranslation ?? word.definition}',
      rule: word.definition,
      example: word.exampleSentence ?? word.hint,
    );
    _explanations[_currentWordIndex] = explanation;

    final targetLetters = word.word.toUpperCase().split('');
    setState(() {
      _wordAnswered = true;
      _answerSlots = targetLetters;
      _slotCorrect = List<bool>.filled(targetLetters.length, false);
      _slotWrong = List<bool>.filled(targetLetters.length, true);
    });

    _persistAnswer(game.sessionId, word.wordId, '', _currentWordIndex);
  }

  Future<void> _persistAnswer(
    String sessionId,
    String itemId,
    String answer,
    int wordIndex,
  ) async {
    if (sessionId.isEmpty || _isSavingAnswer) return;
    setState(() {
      _isSavingAnswer = true;
      _answerSaveError = null;
    });
    final feedback = await context.read<GamesProvider>().saveAnswer(
      sessionId: sessionId,
      itemId: itemId,
      answer: answer,
    );
    if (!mounted) return;
    setState(() {
      _isSavingAnswer = false;
      if (feedback == null) {
        _answerSaveError = 'save_failed';
        return;
      }
      final wasCorrect = _wordSolved[wordIndex] ?? false;
      if (wasCorrect != feedback.isCorrect) {
        _correctCount += feedback.isCorrect ? 1 : -1;
      }
      _wordSolved[wordIndex] = feedback.isCorrect;
      _explanations[wordIndex] = feedback.explanation;
      _answerSaveError = null;
    });
  }

  void _retryCurrentAnswerSave() {
    final game = context.read<GamesProvider>().wordScramble;
    if (game == null) return;
    final word = game.words[_currentWordIndex];
    _persistAnswer(
      game.sessionId,
      word.wordId,
      _submittedAnswers[word.wordId] ?? '',
      _currentWordIndex,
    );
  }

  Future<void> _abandonGame() async {
    if (_isFinishing) return;
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text('games.exitTitle'.tr()),
        content: Text('games.exitXpByWords'.tr()),
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
    final game = provider.wordScramble;
    await provider.completeGame(
      gameType: GameType.wordScramble,
      score: _correctCount,
      totalQuestions: game?.words.length ?? 0,
      correctAnswers: _correctCount,
      answers: [
        for (final word in game?.words ?? <ScrambleWord>[])
          {'id': word.wordId, 'answer': _submittedAnswers[word.wordId] ?? ''},
      ],
    );
    if (mounted) Navigator.of(context).pop();
  }

  void _finishGame() async {
    if (_isFinishing) return;
    _isFinishing = true;
    _timer?.cancel();
    final provider = context.read<GamesProvider>();
    final game = provider.wordScramble;
    final xpResult = await provider.completeGame(
      gameType: GameType.wordScramble,
      score: _correctCount,
      totalQuestions: game?.words.length ?? 0,
      correctAnswers: _correctCount,
      answers: [
        for (final word in game?.words ?? <ScrambleWord>[])
          {'id': word.wordId, 'answer': _submittedAnswers[word.wordId] ?? ''},
      ],
    );
    if (!mounted) return;
    final result = GameResult(
      gameType: GameType.wordScramble,
      cefrLevel: provider.selectedLevel,
      score: _correctCount,
      totalQuestions: game?.words.length ?? 0,
      correctAnswers: _correctCount,
      xpEarned: xpResult?.xpAwarded ?? 0,
      durationSeconds: 0,
      xpResult: xpResult,
    );
    Navigator.pushReplacement(
      context,
      MaterialPageRoute(
        builder: (_) => GameResultScreen(
          result: result,
          xpResult: xpResult,
          onPlayAgain: () {},
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
      child: Stack(
        alignment: Alignment.topCenter,
        children: [
          Consumer<GamesProvider>(
            builder: (context, provider, _) {
              if (provider.isLoading) {
                return const Scaffold(
                  body: Center(child: LottieLoadingWidget.medium()),
                );
              }
              final game = provider.wordScramble;
              if (provider.error != null) {
                return GameLoadState(
                  message: 'games.loadFailed'.tr(),
                  onRetry: () async {
                    await provider.loadWordScramble();
                    if (mounted) _loadCurrentWord();
                  },
                );
              }
              if (game == null || game.words.isEmpty) {
                return GameLoadState(
                  message: 'games.emptyGame'.tr(),
                  onRetry: () async {
                    await provider.loadWordScramble();
                    if (mounted) _loadCurrentWord();
                  },
                );
              }
              if (!_gameLoaded) {
                return const Scaffold(
                  body: Center(child: LottieLoadingWidget.medium()),
                );
              }
              final word = game.words[_currentWordIndex];
              final isWordAnswered = _answeredIndices.contains(
                _currentWordIndex,
              );
              final isCorrect = _wordSolved[_currentWordIndex] ?? false;
              final explanation =
                  _explanations[_currentWordIndex] ??
                  GameExplanation(
                    summary: '${'games.correctAnswer'.tr()}: ${word.word}',
                    rule: word.definition,
                    example: word.exampleSentence ?? word.hint,
                  );

              return Scaffold(
                appBar: AppBar(
                  backgroundColor: Theme.of(context).colorScheme.surface,
                  elevation: 0,
                  title: Text(
                    'wordScramble.wordProgress'.tr(
                      namedArgs: {
                        'current': '${_currentWordIndex + 1}',
                        'total': '${game.words.length}',
                      },
                    ),
                    style: TextStyle(
                      color: Theme.of(context).colorScheme.onSurface,
                    ),
                  ),
                  centerTitle: true,
                  actions: [
                    if (!isWordAnswered)
                      Padding(
                        padding: const EdgeInsets.only(right: 12),
                        child: Center(
                          child: _TimerDisplay(
                            timeLeft: _timeLeft,
                            total: game.timerSeconds,
                          ),
                        ),
                      ),
                  ],
                ),
                body: Column(
                  children: [
                    // Word progress dots
                    Padding(
                      padding: const EdgeInsets.only(top: 8, bottom: 6),
                      child: GameQuestionProgress(
                        currentIndex: _currentWordIndex,
                        total: game.words.length,
                        answeredIndices: _answeredIndices,
                      ),
                    ),
                    Expanded(
                      child: SingleChildScrollView(
                        padding: const EdgeInsets.symmetric(
                          horizontal: 20,
                          vertical: 12,
                        ),
                        child: Column(
                          children: [
                            GamePowerUpTray(
                              availableTypes: _wordScramblePowerUps,
                              enabled: !isWordAnswered,
                              onUse: _onPowerUpUsed,
                            ),
                            const SizedBox(height: 8),
                            if (_xpPopup != null) _XpPopup(text: _xpPopup!),
                            const SizedBox(height: 4),
                            // Hint card
                            _HintCard(word: word, showHint: _showHint),
                            if (_translationReveal != null)
                              Padding(
                                padding: const EdgeInsets.only(top: 8),
                                child: _TranslationBanner(
                                  text: _translationReveal!,
                                ),
                              ),
                            const SizedBox(height: 16),
                            // Answer slots
                            Text(
                              'wordScramble.yourAnswerLabel'.tr(),
                              style: TextStyle(
                                color: Theme.of(
                                  context,
                                ).colorScheme.onSurfaceVariant,
                                fontSize: 13,
                              ),
                            ),
                            const SizedBox(height: 6),
                            Wrap(
                              alignment: WrapAlignment.center,
                              children: List.generate(_answerSlots.length, (i) {
                                return GestureDetector(
                                  onTap: isWordAnswered
                                      ? null
                                      : () => _tapSlot(i),
                                  child: AnimatedContainer(
                                    duration: const Duration(milliseconds: 150),
                                    width: 42,
                                    height: 48,
                                    margin: const EdgeInsets.all(4),
                                    decoration: BoxDecoration(
                                      color: _slotCorrect[i]
                                          ? AppColors.greenSuccess
                                          : _slotWrong[i]
                                          ? AppColors.errorDark
                                          : Theme.of(
                                              context,
                                            ).colorScheme.surface,
                                      borderRadius: BorderRadius.circular(10),
                                      border: Border.all(
                                        color: _answerSlots[i] != null
                                            ? AppColors.primary
                                            : Theme.of(
                                                context,
                                              ).colorScheme.outlineVariant,
                                        width: 1.5,
                                      ),
                                    ),
                                    alignment: Alignment.center,
                                    child: Text(
                                      _answerSlots[i]?.toUpperCase() ?? '',
                                      style: TextStyle(
                                        fontWeight: FontWeight.bold,
                                        fontSize: 18,
                                        color:
                                            (_slotCorrect[i] || _slotWrong[i])
                                            ? Colors.white
                                            : Theme.of(
                                                context,
                                              ).colorScheme.onSurface,
                                      ),
                                    ),
                                  ),
                                );
                              }),
                            ),
                            const SizedBox(height: 16),
                            // Letter pool (only active if unanswered)
                            if (!isWordAnswered) ...[
                              Text(
                                'wordScramble.availableLettersLabel'.tr(),
                                style: TextStyle(
                                  color: Theme.of(
                                    context,
                                  ).colorScheme.onSurfaceVariant,
                                  fontSize: 13,
                                ),
                              ),
                              const SizedBox(height: 8),
                              Wrap(
                                alignment: WrapAlignment.center,
                                children: List.generate(_poolLetters.length, (
                                  i,
                                ) {
                                  final letter = _poolLetters[i];
                                  if (letter.isEmpty) {
                                    return const SizedBox(
                                      width: 50,
                                      height: 56,
                                    );
                                  }
                                  return LetterTile(
                                    key: ValueKey('pool_${i}_$letter'),
                                    letter: letter,
                                    onTap: () => _tapPool(i),
                                  );
                                }),
                              ),
                              const SizedBox(height: 12),
                              // Hint & Skip row
                              Row(
                                mainAxisAlignment: MainAxisAlignment.center,
                                children: [
                                  OutlinedButton.icon(
                                    onPressed: () =>
                                        setState(() => _showHint = !_showHint),
                                    icon: const Icon(
                                      Icons.lightbulb_outline,
                                      size: 16,
                                    ),
                                    label: Text('wordScramble.hintButton'.tr()),
                                    style: OutlinedButton.styleFrom(
                                      side: const BorderSide(
                                        color: AppColors.primary,
                                      ),
                                      foregroundColor: AppColors.primary,
                                    ),
                                  ),
                                  const SizedBox(width: 12),
                                  TextButton(
                                    onPressed: _skipWord,
                                    child: Text(
                                      'wordScramble.skipButton'.tr(),
                                      style: TextStyle(
                                        color: AppColors.primary,
                                      ),
                                    ),
                                  ),
                                ],
                              ),
                            ],
                            // Detailed vocabulary explanation card when answered
                            if (isWordAnswered) ...[
                              const SizedBox(height: 16),
                              GameAnswerExplanationCard(
                                isCorrect: isCorrect,
                                selectedAnswer:
                                    _submittedAnswers[word.wordId] ?? '',
                                correctAnswer: word.word,
                                explanation: explanation,
                                fallbackRule: word.definition,
                                fallbackExample:
                                    word.exampleSentence ?? word.hint,
                              ),
                              GameAnswerSaveStatus(
                                isSaving: _isSavingAnswer,
                                error: _answerSaveError,
                                onRetry: _retryCurrentAnswerSave,
                              ),
                            ],
                            const SizedBox(height: 20),
                            // Navigation Buttons (Previous & Next)
                            GameQuestionNavigation(
                              canGoPrevious: _currentWordIndex > 0,
                              canGoNext:
                                  isWordAnswered &&
                                  !_isSavingAnswer &&
                                  _answerSaveError == null,
                              isLastQuestion:
                                  _currentWordIndex == game.words.length - 1,
                              isBusy:
                                  _isFinishing ||
                                  _isSavingAnswer ||
                                  _answerSaveError != null,
                              onPrevious: _previousWord,
                              onNext: _nextWord,
                            ),
                            const SizedBox(height: 16),
                          ],
                        ),
                      ),
                    ),
                  ],
                ),
              );
            },
          ),
          ConfettiWidget(
            confettiController: _confettiController,
            blastDirectionality: BlastDirectionality.explosive,
            numberOfParticles: 20,
            gravity: 0.4,
            emissionFrequency: 0.05,
            colors: const [
              AppColors.primary,
              AppColors.accentYellow,
              AppColors.greenSuccess,
            ],
          ),
        ],
      ),
    );
  }
}

class _TimerDisplay extends StatelessWidget {
  final int timeLeft;
  final int total;
  const _TimerDisplay({required this.timeLeft, required this.total});

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

class _TranslationBanner extends StatelessWidget {
  final String text;
  const _TranslationBanner({required this.text});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
      decoration: BoxDecoration(
        color: AppColors.primary.withValues(alpha: 0.08),
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: AppColors.primary.withValues(alpha: 0.3)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          const Icon(Icons.translate, size: 16, color: AppColors.primary),
          const SizedBox(width: 8),
          Text(
            text,
            style: const TextStyle(
              fontSize: 14,
              fontWeight: FontWeight.w600,
              color: AppColors.primary,
            ),
          ),
        ],
      ),
    );
  }
}

class _HintCard extends StatelessWidget {
  final ScrambleWord word;
  final bool showHint;
  const _HintCard({required this.word, required this.showHint});

  @override
  Widget build(BuildContext context) {
    final hint = showHint ? word.definition : word.hint;
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: Theme.of(context).colorScheme.surface,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Theme.of(context).colorScheme.outlineVariant),
      ),
      child: Column(
        children: [
          Text(
            showHint
                ? 'wordScramble.fullDefinitionLabel'.tr()
                : 'wordScramble.hintCardLabel'.tr(),
            style: TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.bold,
              color: Theme.of(context).colorScheme.primary,
            ),
          ),
          const SizedBox(height: 4),
          Text(
            hint,
            style: TextStyle(
              fontSize: 14,
              color: Theme.of(context).colorScheme.onSurface,
            ),
            textAlign: TextAlign.center,
          ),
        ],
      ),
    );
  }
}

class _XpPopup extends StatelessWidget {
  final String text;
  const _XpPopup({required this.text});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
      decoration: BoxDecoration(
        color: AppColors.primary,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Text(
        text,
        style: const TextStyle(
          color: Colors.white,
          fontWeight: FontWeight.bold,
          fontSize: 13,
        ),
      ),
    );
  }
}

class LetterTile extends StatelessWidget {
  final String letter;
  final VoidCallback onTap;

  const LetterTile({super.key, required this.letter, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        width: 44,
        height: 50,
        margin: const EdgeInsets.all(4),
        decoration: BoxDecoration(
          color: Theme.of(context).colorScheme.primaryContainer,
          borderRadius: BorderRadius.circular(10),
          boxShadow: [
            BoxShadow(
              color: Theme.of(
                context,
              ).colorScheme.shadow.withValues(alpha: 0.1),
              blurRadius: 4,
              offset: const Offset(0, 2),
            ),
          ],
        ),
        alignment: Alignment.center,
        child: Text(
          letter,
          style: TextStyle(
            fontSize: 20,
            fontWeight: FontWeight.bold,
            color: Theme.of(context).colorScheme.onPrimaryContainer,
          ),
        ),
      ),
    );
  }
}
