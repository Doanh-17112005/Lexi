import 'package:easy_localization/easy_localization.dart';
import 'package:flutter/material.dart';
import 'package:lexilingo_app/features/games/domain/entities/game_entities.dart';

class GameAnswerExplanationCard extends StatelessWidget {
  final bool isCorrect;
  final String selectedAnswer;
  final String correctAnswer;
  final GameExplanation explanation;
  final String fallbackRule;
  final String fallbackExample;

  const GameAnswerExplanationCard({
    super.key,
    required this.isCorrect,
    required this.selectedAnswer,
    required this.correctAnswer,
    required this.explanation,
    this.fallbackRule = '',
    this.fallbackExample = '',
  });

  @override
  Widget build(BuildContext context) {
    final colors = Theme.of(context).colorScheme;
    final accent = isCorrect ? Colors.green.shade700 : colors.error;
    final summary = explanation.summary.isNotEmpty
        ? explanation.summary
        : '${'games.correctAnswer'.tr()}: $correctAnswer';
    final rule = explanation.rule.isNotEmpty ? explanation.rule : fallbackRule;
    final example = explanation.example.isNotEmpty
        ? explanation.example
        : fallbackExample;

    return Semantics(
      liveRegion: true,
      label: isCorrect
          ? 'games.answerCorrect'.tr()
          : 'games.answerIncorrect'.tr(),
      child: Container(
        width: double.infinity,
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: accent.withValues(alpha: 0.08),
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: accent.withValues(alpha: 0.55)),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(
                  isCorrect ? Icons.check_circle_rounded : Icons.cancel_rounded,
                  color: accent,
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    isCorrect
                        ? 'games.answerCorrect'.tr()
                        : 'games.answerIncorrect'.tr(),
                    style: TextStyle(
                      color: accent,
                      fontWeight: FontWeight.w800,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 10),
            Text(summary, style: const TextStyle(height: 1.45)),
            if (selectedAnswer.isNotEmpty && !isCorrect) ...[
              const SizedBox(height: 8),
              Text(
                '${'games.yourAnswer'.tr()}: $selectedAnswer',
                style: TextStyle(color: colors.onSurfaceVariant),
              ),
            ],
            const SizedBox(height: 8),
            Text(
              '${'games.correctAnswer'.tr()}: $correctAnswer',
              style: const TextStyle(fontWeight: FontWeight.w700),
            ),
            if (rule.isNotEmpty) ...[
              const SizedBox(height: 12),
              _DetailSection(
                icon: Icons.menu_book_rounded,
                title: 'games.rule'.tr(),
                value: rule,
              ),
            ],
            if (example.isNotEmpty) ...[
              const SizedBox(height: 10),
              _DetailSection(
                icon: Icons.lightbulb_outline_rounded,
                title: 'games.example'.tr(),
                value: example,
              ),
            ],
            if (explanation.optionExplanations.isNotEmpty) ...[
              const SizedBox(height: 12),
              Text(
                'games.choiceAnalysis'.tr(),
                style: const TextStyle(fontWeight: FontWeight.w700),
              ),
              const SizedBox(height: 6),
              for (final entry in explanation.optionExplanations.entries)
                Padding(
                  padding: const EdgeInsets.only(bottom: 6),
                  child: Text(
                    '• ${entry.value}',
                    style: TextStyle(
                      color: colors.onSurfaceVariant,
                      height: 1.35,
                    ),
                  ),
                ),
            ],
          ],
        ),
      ),
    );
  }
}

class _DetailSection extends StatelessWidget {
  final IconData icon;
  final String title;
  final String value;

  const _DetailSection({
    required this.icon,
    required this.title,
    required this.value,
  });

  @override
  Widget build(BuildContext context) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Icon(icon, size: 18, color: Theme.of(context).colorScheme.primary),
        const SizedBox(width: 8),
        Expanded(
          child: Text.rich(
            TextSpan(
              children: [
                TextSpan(
                  text: '$title: ',
                  style: const TextStyle(fontWeight: FontWeight.w700),
                ),
                TextSpan(text: value),
              ],
            ),
            style: const TextStyle(height: 1.4),
          ),
        ),
      ],
    );
  }
}

class GameAnswerSaveStatus extends StatelessWidget {
  final bool isSaving;
  final String? error;
  final VoidCallback? onRetry;

  const GameAnswerSaveStatus({
    super.key,
    required this.isSaving,
    required this.error,
    this.onRetry,
  });

  @override
  Widget build(BuildContext context) {
    if (!isSaving && error == null) return const SizedBox.shrink();
    if (isSaving) {
      return Semantics(
        liveRegion: true,
        label: 'games.savingAnswer'.tr(),
        child: const Padding(
          padding: EdgeInsets.only(top: 12),
          child: LinearProgressIndicator(),
        ),
      );
    }
    return Padding(
      padding: const EdgeInsets.only(top: 12),
      child: Row(
        children: [
          Icon(
            Icons.cloud_off_rounded,
            color: Theme.of(context).colorScheme.error,
          ),
          const SizedBox(width: 8),
          Expanded(child: Text('games.answerSaveFailed'.tr())),
          TextButton(onPressed: onRetry, child: Text('games.retrySave'.tr())),
        ],
      ),
    );
  }
}
