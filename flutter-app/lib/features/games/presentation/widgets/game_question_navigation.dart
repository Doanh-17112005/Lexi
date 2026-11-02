import 'package:easy_localization/easy_localization.dart';
import 'package:flutter/material.dart';

class GameQuestionProgress extends StatelessWidget {
  final int currentIndex;
  final int total;
  final Set<int> answeredIndices;

  const GameQuestionProgress({
    super.key,
    required this.currentIndex,
    required this.total,
    required this.answeredIndices,
  });

  @override
  Widget build(BuildContext context) {
    final colors = Theme.of(context).colorScheme;
    return Wrap(
      alignment: WrapAlignment.center,
      spacing: 6,
      runSpacing: 6,
      children: List.generate(total, (index) {
        final isCurrent = index == currentIndex;
        final isAnswered = answeredIndices.contains(index);
        return Semantics(
          label: 'games.questionState'.tr(
            namedArgs: {
              'current': '${index + 1}',
              'state': isCurrent
                  ? 'games.current'.tr()
                  : isAnswered
                  ? 'games.answered'.tr()
                  : 'games.unanswered'.tr(),
            },
          ),
          child: AnimatedContainer(
            duration: const Duration(milliseconds: 160),
            width: isCurrent ? 28 : 12,
            height: 12,
            decoration: BoxDecoration(
              color: isCurrent
                  ? colors.primary
                  : isAnswered
                  ? Colors.green.shade600
                  : colors.surfaceContainerHighest,
              borderRadius: BorderRadius.circular(8),
            ),
          ),
        );
      }),
    );
  }
}

class GameQuestionNavigation extends StatelessWidget {
  final bool canGoPrevious;
  final bool canGoNext;
  final bool isLastQuestion;
  final bool isBusy;
  final VoidCallback? onPrevious;
  final VoidCallback? onNext;

  const GameQuestionNavigation({
    super.key,
    required this.canGoPrevious,
    required this.canGoNext,
    required this.isLastQuestion,
    required this.isBusy,
    this.onPrevious,
    this.onNext,
  });

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        final compact = constraints.maxWidth < 420;
        final previous = OutlinedButton.icon(
          onPressed: canGoPrevious && !isBusy ? onPrevious : null,
          icon: const Icon(Icons.arrow_back_rounded),
          label: Text('games.previousQuestion'.tr()),
        );
        final next = FilledButton.icon(
          onPressed: canGoNext && !isBusy ? onNext : null,
          icon: isBusy
              ? const SizedBox(
                  width: 18,
                  height: 18,
                  child: CircularProgressIndicator(strokeWidth: 2),
                )
              : Icon(
                  isLastQuestion
                      ? Icons.flag_rounded
                      : Icons.arrow_forward_rounded,
                ),
          label: Text(
            isLastQuestion
                ? 'games.finishGame'.tr()
                : 'games.nextQuestion'.tr(),
          ),
        );
        if (compact) {
          return Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [previous, const SizedBox(height: 10), next],
          );
        }
        return Row(
          children: [
            Expanded(child: previous),
            const SizedBox(width: 12),
            Expanded(child: next),
          ],
        );
      },
    );
  }
}
