import 'dart:async';
import 'package:easy_localization/easy_localization.dart';
import 'package:flutter/material.dart';
import 'package:lexilingo_app/core/widgets/lottie_loading_widget.dart';
import 'package:provider/provider.dart';
import 'package:lexilingo_app/core/di/service_locator.dart';
import 'package:lexilingo_app/core/theme/app_theme.dart';
import 'package:lexilingo_app/features/gamification/domain/entities/shop_item.dart';
import 'package:lexilingo_app/features/games/data/services/game_pronunciation_service.dart';
import 'package:lexilingo_app/features/games/domain/entities/game_entities.dart';
import 'package:lexilingo_app/features/games/presentation/providers/games_provider.dart';
import 'package:lexilingo_app/features/games/presentation/screens/game_result_screen.dart';
import 'package:lexilingo_app/features/games/presentation/widgets/game_answer_explanation.dart';
import 'package:lexilingo_app/features/games/presentation/widgets/game_load_state.dart';
import 'package:lexilingo_app/features/games/presentation/widgets/game_powerup_tray.dart';
import 'package:lexilingo_app/features/games/presentation/widgets/game_question_navigation.dart';

const _spellingBeePowerUps = [
  ShopItemEntity.effectMistakeShield,
  ShopItemEntity.effectTranslateHint,
  ShopItemEntity.effectSkipToken,
  ShopItemEntity.effectScoreMultiplier,
];

/// Spelling Bee game screen.
///
/// Player listens to TTS audio and types the word they heard.
/// Supports previous/next navigation, locked answer review,
/// and detailed vocabulary explanations.
class SpellingBeeScreen extends StatefulWidget {
  const SpellingBeeScreen({super.key});

  @override
  State<SpellingBeeScreen> createState() => _SpellingBeeScreenState();
}

class _SpellingBeeScreenState extends State<SpellingBeeScreen> {
  final TextEditingController _inputController = TextEditingController();
  late GamePronunciationService _pronunciationService;

  int _wordIndex = 0;
  int _playsLeft = 3;
  int _correctCount = 0;
  bool _gameLoaded = false;
  bool _answered = false;
  bool _isCorrect = false;
  bool _isFinishing = false;
  bool _isSavingAnswer = false;
  bool _restoredSession = false;
  String? _answerSaveError;
  String? _audioErrorMessage;
  String? _translationReveal;
  int _scoreMultiplier = 1;
  final Map<String, String> _submittedAnswers = {};

  final Set<int> _answeredIndices = {};
  final Map<int, String> _userAnswers = {};
  final Map<int, bool> _answerCorrectness = {};
  final Map<int, GameExplanation> _explanations = {};

  @override
  void initState() {
    super.initState();
    _pronunciationService = sl<GamePronunciationService>();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<GamesProvider>().loadSpellingBee().then((_) {
        if (mounted) _loadCurrentWord();
      });
    });
  }

  @override
  void dispose() {
    _pronunciationService.dispose();
    _inputController.dispose();
    super.dispose();
  }

  void _loadCurrentWord() {
    final provider = context.read<GamesProvider>();
    final game = provider.spellingBee;
    if (game == null || game.words.isEmpty) return;
    _restoreSessionAnswers(provider, game);

    if (_answeredIndices.contains(_wordIndex)) {
      final word = game.words[_wordIndex];
      setState(() {
        _gameLoaded = true;
        _answered = true;
        _isCorrect = _answerCorrectness[_wordIndex] ?? false;
        _inputController.text = _userAnswers[_wordIndex] ?? '';
        _translationReveal = word.vietnameseTranslation;
        _audioErrorMessage = null;
      });
    } else {
      _initWord();
    }
  }

  void _restoreSessionAnswers(GamesProvider provider, SpellingBeeGame game) {
    if (_restoredSession) return;
    _restoredSession = true;
    for (var index = 0; index < game.words.length; index++) {
      final word = game.words[index];
      final feedback = provider.sessionAnswers[word.wordId];
      if (feedback == null) continue;
      _submittedAnswers[word.wordId] = feedback.answer;
      _userAnswers[index] = feedback.answer;
      _answerCorrectness[index] = feedback.isCorrect;
      _explanations[index] = feedback.explanation;
      _answeredIndices.add(index);
      if (feedback.isCorrect) _correctCount++;
    }
    if (_answeredIndices.isNotEmpty) {
      _wordIndex = List.generate(game.words.length, (index) => index)
          .firstWhere(
            (index) => !_answeredIndices.contains(index),
            orElse: () => game.words.length - 1,
          );
    }
  }

  void _initWord() {
    final game = context.read<GamesProvider>().spellingBee;
    if (game == null || _wordIndex >= game.words.length) return;
    setState(() {
      _gameLoaded = true;
      _playsLeft = game.words[_wordIndex].maxReplays;
      _answered = false;
      _isCorrect = false;
      _audioErrorMessage = null;
      _translationReveal = null;
      _inputController.clear();
    });
  }

  void _onPowerUpUsed(String itemType, Map<String, dynamic> effects) {
    if (_answered) return;
    final game = context.read<GamesProvider>().spellingBee;
    if (game == null) return;
    final word = game.words[_wordIndex];
    switch (itemType) {
      case ShopItemEntity.effectMistakeShield:
        setState(() => _playsLeft += 1);
        break;
      case ShopItemEntity.effectTranslateHint:
        setState(() => _translationReveal = word.vietnameseTranslation);
        break;
      case ShopItemEntity.effectSkipToken:
        _skipCurrentWord();
        break;
      case ShopItemEntity.effectScoreMultiplier:
        final multiplier = (effects['multiplier'] as num?)?.toInt() ?? 2;
        setState(() => _scoreMultiplier = multiplier);
        break;
    }
  }

  Future<void> _playAudio() async {
    if (_playsLeft <= 0 || _pronunciationService.isPlaying) return;
    final game = context.read<GamesProvider>().spellingBee;
    if (game == null) return;
    final word = game.words[_wordIndex];

    final newPlaysLeft = await _pronunciationService.play(
      text: word.word,
      playsLeft: _playsLeft,
      audioUrl: word.audioUrl,
      onPlayingChanged: () {
        if (mounted) setState(() {});
      },
    );

    if (!mounted) return;
    final error = _pronunciationService.lastError;
    setState(() {
      _playsLeft = newPlaysLeft;
      _audioErrorMessage = error?.retryable == true ? error?.message : null;
    });
  }

  void _submitAnswer() {
    if (_answered || _answeredIndices.contains(_wordIndex)) return;
    final provider = context.read<GamesProvider>();
    final game = provider.spellingBee!;
    final word = game.words[_wordIndex];
    final input = _inputController.text.trim();
    final isCorrect = input.toLowerCase() == word.word.toLowerCase();

    _submittedAnswers[word.wordId] = input;
    _userAnswers[_wordIndex] = input;
    _answerCorrectness[_wordIndex] = isCorrect;
    _answeredIndices.add(_wordIndex);

    if (isCorrect) {
      _correctCount++;
    }

    final explanation = GameExplanation(
      summary:
          '${'games.correctAnswer'.tr()}: ${word.word} (${word.ipaPronunciation ?? ''}) - ${word.vietnameseTranslation ?? word.definition}',
      rule: word.definition,
      example: word.exampleSentence ?? word.definition,
    );
    _explanations[_wordIndex] = explanation;

    setState(() {
      _answered = true;
      _isCorrect = isCorrect;
    });

    _persistAnswer(game.sessionId, word.wordId, input, _wordIndex);
  }

  void _skipCurrentWord() {
    if (_answered || _answeredIndices.contains(_wordIndex)) return;
    final provider = context.read<GamesProvider>();
    final game = provider.spellingBee;
    if (game == null) return;
    final word = game.words[_wordIndex];

    _submittedAnswers[word.wordId] = '';
    _userAnswers[_wordIndex] = '';
    _answerCorrectness[_wordIndex] = false;
    _answeredIndices.add(_wordIndex);

    final explanation = GameExplanation(
      summary:
          '${'games.correctAnswer'.tr()}: ${word.word} (${word.ipaPronunciation ?? ''}) - ${word.vietnameseTranslation ?? word.definition}',
      rule: word.definition,
      example: word.exampleSentence ?? word.definition,
    );
    _explanations[_wordIndex] = explanation;

    setState(() {
      _answered = true;
      _isCorrect = false;
    });

    _persistAnswer(game.sessionId, word.wordId, '', _wordIndex);
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
      final wasCorrect = _answerCorrectness[wordIndex] ?? false;
      if (wasCorrect != feedback.isCorrect) {
        _correctCount += feedback.isCorrect ? 1 : -1;
      }
      _answerCorrectness[wordIndex] = feedback.isCorrect;
      _explanations[wordIndex] = feedback.explanation;
      if (_wordIndex == wordIndex) _isCorrect = feedback.isCorrect;
      _answerSaveError = null;
    });
  }

  void _retryCurrentAnswerSave() {
    final game = context.read<GamesProvider>().spellingBee;
    if (game == null) return;
    final word = game.words[_wordIndex];
    _persistAnswer(
      game.sessionId,
      word.wordId,
      _submittedAnswers[word.wordId] ?? '',
      _wordIndex,
    );
  }

  void _previousWord() {
    if (_wordIndex <= 0 || _isFinishing) return;
    setState(() => _wordIndex--);
    _loadCurrentWord();
  }

  void _nextWord() {
    if (!mounted || _isFinishing) return;
    final game = context.read<GamesProvider>().spellingBee;
    if (game == null) return;
    if (_wordIndex + 1 >= game.words.length) {
      _finishGame();
      return;
    }
    setState(() => _wordIndex++);
    _loadCurrentWord();
  }

  Future<void> _abandonGame() async {
    if (_isFinishing) return;
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text('spellingBee.abandonTitle'.tr()),
        content: Text('spellingBee.abandonBody'.tr()),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: Text('spellingBee.keepPlaying'.tr()),
          ),
          TextButton(
            onPressed: () => Navigator.pop(ctx, true),
            child: Text('spellingBee.quit'.tr()),
          ),
        ],
      ),
    );
    if (confirmed != true || !mounted || _isFinishing) return;
    _isFinishing = true;
    final provider = context.read<GamesProvider>();
    final game = provider.spellingBee;
    if (game != null) {
      await provider.completeGame(
        gameType: GameType.spellingBee,
        score: _correctCount,
        totalQuestions: game.words.length,
        correctAnswers: _correctCount,
        answers: [
          for (final word in game.words)
            {'id': word.wordId, 'answer': _submittedAnswers[word.wordId] ?? ''},
        ],
      );
    }
    if (mounted) Navigator.of(context).pop();
  }

  void _finishGame() async {
    if (_isFinishing) return;
    _isFinishing = true;
    final provider = context.read<GamesProvider>();
    final game = provider.spellingBee!;
    final xpResult = await provider.completeGame(
      gameType: GameType.spellingBee,
      score: _correctCount * _scoreMultiplier,
      totalQuestions: game.words.length,
      correctAnswers: _correctCount,
      answers: [
        for (final word in game.words)
          {'id': word.wordId, 'answer': _submittedAnswers[word.wordId] ?? ''},
      ],
    );
    if (!mounted) return;
    Navigator.pushReplacement(
      context,
      MaterialPageRoute(
        builder: (_) => GameResultScreen(
          result: GameResult(
            gameType: GameType.spellingBee,
            cefrLevel: provider.selectedLevel,
            score: _correctCount * _scoreMultiplier,
            totalQuestions: game.words.length,
            correctAnswers: _correctCount,
            xpEarned: xpResult?.xpAwarded ?? 0,
            durationSeconds: 0,
            xpResult: xpResult,
          ),
          xpResult: xpResult,
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
          final game = provider.spellingBee;
          if (provider.error != null) {
            return GameLoadState(
              message: 'games.loadFailed'.tr(),
              onRetry: () async {
                await provider.loadSpellingBee();
                if (mounted) _loadCurrentWord();
              },
            );
          }
          if (game == null || game.words.isEmpty) {
            return GameLoadState(
              message: 'games.emptyGame'.tr(),
              onRetry: () async {
                await provider.loadSpellingBee();
                if (mounted) _loadCurrentWord();
              },
            );
          }
          if (!_gameLoaded) {
            return const Scaffold(
              body: Center(child: LottieLoadingWidget.medium()),
            );
          }
          final word = game.words[_wordIndex];
          final isWordAnswered = _answeredIndices.contains(_wordIndex);
          final explanation =
              _explanations[_wordIndex] ??
              GameExplanation(
                summary: '${'games.correctAnswer'.tr()}: ${word.word}',
                rule: word.definition,
                example: word.vietnameseTranslation ?? word.definition,
              );

          return Scaffold(
            appBar: AppBar(
              backgroundColor: Theme.of(context).colorScheme.surface,
              elevation: 0,
              title: Text(
                'spellingBee.wordProgress'.tr(
                  namedArgs: {
                    'current': '${_wordIndex + 1}',
                    'total': '${game.words.length}',
                  },
                ),
                style: TextStyle(
                  color: Theme.of(context).colorScheme.onSurface,
                ),
              ),
              centerTitle: true,
            ),
            body: Column(
              children: [
                // Question progress dots
                Padding(
                  padding: const EdgeInsets.only(top: 8, bottom: 6),
                  child: GameQuestionProgress(
                    currentIndex: _wordIndex,
                    total: game.words.length,
                    answeredIndices: _answeredIndices,
                  ),
                ),
                Expanded(
                  child: SingleChildScrollView(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 24,
                      vertical: 12,
                    ),
                    child: Column(
                      children: [
                        GamePowerUpTray(
                          availableTypes: _spellingBeePowerUps,
                          enabled: !isWordAnswered,
                          onUse: _onPowerUpUsed,
                        ),
                        const SizedBox(height: 12),
                        // Listen button
                        GestureDetector(
                          onTap: _playAudio,
                          child: AnimatedContainer(
                            duration: const Duration(milliseconds: 200),
                            width: 88,
                            height: 88,
                            decoration: BoxDecoration(
                              shape: BoxShape.circle,
                              color: _pronunciationService.isPlaying
                                  ? AppColors.primary
                                  : AppColors.primary.withValues(alpha: 0.12),
                              border: Border.all(
                                color: AppColors.primary,
                                width: 2,
                              ),
                            ),
                            child: Icon(
                              _pronunciationService.isPlaying
                                  ? Icons.volume_up
                                  : Icons.volume_up_outlined,
                              size: 40,
                              color: _pronunciationService.isPlaying
                                  ? Colors.white
                                  : AppColors.primary,
                            ),
                          ),
                        ),
                        const SizedBox(height: 8),
                        Text(
                          'spellingBee.tapToListen'.tr(),
                          style: TextStyle(
                            fontSize: 13,
                            color: Theme.of(
                              context,
                            ).colorScheme.onSurfaceVariant,
                          ),
                        ),
                        if (_audioErrorMessage != null) ...[
                          const SizedBox(height: 6),
                          Text(
                            _audioErrorMessage!,
                            style: const TextStyle(
                              color: AppColors.errorBright,
                              fontSize: 12,
                            ),
                            textAlign: TextAlign.center,
                          ),
                        ],
                        const SizedBox(height: 16),
                        if (_translationReveal != null)
                          Container(
                            margin: const EdgeInsets.only(bottom: 12),
                            padding: const EdgeInsets.symmetric(
                              horizontal: 14,
                              vertical: 8,
                            ),
                            decoration: BoxDecoration(
                              color: AppColors.primary.withValues(alpha: 0.08),
                              borderRadius: BorderRadius.circular(10),
                              border: Border.all(
                                color: AppColors.primary.withValues(alpha: 0.3),
                              ),
                            ),
                            child: Row(
                              mainAxisSize: MainAxisSize.min,
                              children: [
                                const Icon(
                                  Icons.translate,
                                  size: 16,
                                  color: AppColors.primary,
                                ),
                                const SizedBox(width: 8),
                                Text(
                                  _translationReveal!,
                                  style: const TextStyle(
                                    fontSize: 14,
                                    fontWeight: FontWeight.w600,
                                    color: AppColors.primary,
                                  ),
                                ),
                              ],
                            ),
                          ),
                        // Input field
                        TextField(
                          controller: _inputController,
                          enabled: !isWordAnswered,
                          autocorrect: false,
                          enableSuggestions: false,
                          textCapitalization: TextCapitalization.none,
                          textAlign: TextAlign.center,
                          style: const TextStyle(
                            fontSize: 22,
                            fontWeight: FontWeight.bold,
                            letterSpacing: 2,
                          ),
                          decoration: InputDecoration(
                            hintText: 'spellingBee.inputHint'.tr(),
                            hintStyle: const TextStyle(
                              fontSize: 16,
                              letterSpacing: 0,
                              fontWeight: FontWeight.normal,
                            ),
                            filled: true,
                            fillColor: Theme.of(context).colorScheme.surface,
                            contentPadding: const EdgeInsets.symmetric(
                              vertical: 16,
                              horizontal: 20,
                            ),
                            border: OutlineInputBorder(
                              borderRadius: BorderRadius.circular(14),
                              borderSide: BorderSide(
                                color: Theme.of(
                                  context,
                                ).colorScheme.outlineVariant,
                              ),
                            ),
                            focusedBorder: OutlineInputBorder(
                              borderRadius: BorderRadius.circular(14),
                              borderSide: const BorderSide(
                                color: AppColors.primary,
                                width: 2,
                              ),
                            ),
                          ),
                          onSubmitted: (_) =>
                              isWordAnswered ? null : _submitAnswer(),
                        ),
                        const SizedBox(height: 16),
                        if (!isWordAnswered) ...[
                          SizedBox(
                            width: double.infinity,
                            child: ElevatedButton(
                              onPressed: _submitAnswer,
                              style: ElevatedButton.styleFrom(
                                backgroundColor: AppColors.primary,
                                foregroundColor: Colors.white,
                                padding: const EdgeInsets.symmetric(
                                  vertical: 14,
                                ),
                                shape: RoundedRectangleBorder(
                                  borderRadius: BorderRadius.circular(12),
                                ),
                              ),
                              child: Text(
                                'spellingBee.submitButton'.tr(),
                                style: const TextStyle(
                                  fontWeight: FontWeight.bold,
                                  fontSize: 16,
                                ),
                              ),
                            ),
                          ),
                        ] else ...[
                          // Detailed explanation card
                          GameAnswerExplanationCard(
                            isCorrect: _isCorrect,
                            selectedAnswer: _userAnswers[_wordIndex] ?? '',
                            correctAnswer: word.word,
                            explanation: explanation,
                            fallbackRule: word.definition,
                            fallbackExample: word.ipaPronunciation != null
                                ? 'Phát âm: ${word.ipaPronunciation}'
                                : '',
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
                          canGoPrevious: _wordIndex > 0,
                          canGoNext:
                              isWordAnswered &&
                              !_isSavingAnswer &&
                              _answerSaveError == null,
                          isLastQuestion: _wordIndex == game.words.length - 1,
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
    );
  }
}
