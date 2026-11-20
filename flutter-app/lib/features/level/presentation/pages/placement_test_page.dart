import 'dart:async';

import 'package:easy_localization/easy_localization.dart';
import 'package:flutter/material.dart';
import 'package:lexilingo_app/core/theme/app_theme.dart';
import 'package:lexilingo_app/core/widgets/cefr_badge.dart';
import 'package:lexilingo_app/features/level/presentation/providers/placement_test_provider.dart';
import 'package:lexilingo_app/features/level/presentation/providers/proficiency_provider.dart';
import 'package:lexilingo_app/features/voice/presentation/widgets/speak_button.dart';
import 'package:provider/provider.dart';

class PlacementTestPage extends StatefulWidget {
  const PlacementTestPage({super.key});

  @override
  State<PlacementTestPage> createState() => _PlacementTestPageState();
}

class _PlacementTestPageState extends State<PlacementTestPage> {
  final TextEditingController _textController = TextEditingController();
  Timer? _timer;
  int _currentIndex = 0;
  int _elapsedSeconds = 0;
  bool _showListeningTranscript = false;
  String? _syncedControllerTaskId;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _loadTest(forceNew: false);
    });
  }

  @override
  void dispose() {
    _timer?.cancel();
    _textController.dispose();
    super.dispose();
  }

  Future<void> _loadTest({bool forceNew = false}) async {
    final provider = context.read<PlacementTestProvider>();
    if (forceNew) {
      _timer?.cancel();
      _currentIndex = 0;
      _elapsedSeconds = 0;
      _syncedControllerTaskId = null;
      _textController.clear();
      provider.reset();
    }

    await provider.loadTest(forceNew: forceNew);
    if (!mounted) return;

    if (provider.questions.isNotEmpty) {
      _syncControllerForCurrentQuestion(provider);
      _startTimer();
    }
  }

  void _startTimer() {
    _timer?.cancel();
    _timer = Timer.periodic(const Duration(seconds: 1), (_) {
      if (!mounted) return;
      setState(() => _elapsedSeconds += 1);
    });
  }

  String _formatElapsedTime() {
    final minutes = (_elapsedSeconds ~/ 60).toString().padLeft(2, '0');
    final seconds = (_elapsedSeconds % 60).toString().padLeft(2, '0');
    return '$minutes:$seconds';
  }

  void _syncControllerForCurrentQuestion(PlacementTestProvider provider) {
    if (_currentIndex >= provider.questions.length) return;
    final task = provider.questions[_currentIndex];
    final taskId = '${task['id'] ?? _currentIndex + 1}';
    if (_syncedControllerTaskId == taskId) return;
    _syncedControllerTaskId = taskId;
    final savedText =
        provider.draftAnswers[taskId]?['text_response']?.toString() ?? '';
    _textController.value = TextEditingValue(
      text: savedText,
      selection: TextSelection.collapsed(offset: savedText.length),
    );
  }

  void _goToQuestion(int index, PlacementTestProvider provider) {
    final total = provider.questions.length;
    if (index < 0 || index >= total) return;
    setState(() {
      _currentIndex = index;
      _showListeningTranscript = false;
      _syncedControllerTaskId = null;
      _syncControllerForCurrentQuestion(provider);
    });
  }

  Future<void> _submit() async {
    final provider = context.read<PlacementTestProvider>();
    final total = provider.questions.length;
    if (provider.answeredCount < total) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('assessment.answerAllQuestions'.tr())),
      );
      return;
    }

    final submitted = await provider.submitSixSkillTest(_elapsedSeconds);
    if (!mounted) return;

    if (submitted) {
      _timer?.cancel();
      try {
        await context.read<ProficiencyProvider>().loadProfile();
      } catch (_) {}
    } else if (provider.errorMessage != null) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(provider.errorMessage!)),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final accent = AppColorRoles.primary(isDark);

    return Scaffold(
      backgroundColor: isDark
          ? AppColors.backgroundDark
          : AppColors.backgroundLight,
      appBar: AppBar(
        title: Text('assessment.placementTest'.tr()),
        actions: [
          Padding(
            padding: const EdgeInsetsDirectional.only(end: 16),
            child: Center(
              child: _MetaChip(
                icon: Icons.timer_rounded,
                label: _formatElapsedTime(),
                color: accent,
              ),
            ),
          ),
        ],
      ),
      body: SafeArea(
        child: Consumer<PlacementTestProvider>(
          builder: (context, provider, _) {
            if (provider.isLoading && provider.questions.isEmpty) {
              return const Center(child: CircularProgressIndicator());
            }

            if (provider.errorMessage != null && provider.questions.isEmpty) {
              return _ErrorState(
                message: provider.errorMessage!,
                onRetry: () => _loadTest(forceNew: false),
              );
            }

            if (provider.result != null) {
              return _ResultState(
                result: provider.result!,
                onRetake: () => _loadTest(forceNew: true),
              );
            }

            if (provider.questions.isEmpty) {
              return _EmptyState(onRetry: () => _loadTest(forceNew: true));
            }

            _syncControllerForCurrentQuestion(provider);

            return _QuestionState(
              questions: provider.questions,
              currentIndex: _currentIndex,
              draftAnswers: provider.draftAnswers,
              answeredCount: provider.answeredCount,
              isSubmitting: provider.isSubmitting,
              elapsedLabel: _formatElapsedTime(),
              disclaimer: provider.disclaimer,
              textController: _textController,
              showListeningTranscript: _showListeningTranscript,
              onToggleTranscript: () => setState(
                () => _showListeningTranscript = !_showListeningTranscript,
              ),
              onSelectOption: (taskId, optIndex) => provider.saveAnswer(
                taskId: taskId,
                selectedOption: optIndex,
              ),
              onTextChanged: (taskId, value) => provider.saveAnswer(
                taskId: taskId,
                textResponse: value,
              ),
              onPrevious: () => _goToQuestion(_currentIndex - 1, provider),
              onNext: () => _goToQuestion(_currentIndex + 1, provider),
              onSubmit: _submit,
            );
          },
        ),
      ),
    );
  }
}

class _QuestionState extends StatelessWidget {
  const _QuestionState({
    required this.questions,
    required this.currentIndex,
    required this.draftAnswers,
    required this.answeredCount,
    required this.isSubmitting,
    required this.elapsedLabel,
    required this.disclaimer,
    required this.textController,
    required this.showListeningTranscript,
    required this.onToggleTranscript,
    required this.onSelectOption,
    required this.onTextChanged,
    required this.onPrevious,
    required this.onNext,
    required this.onSubmit,
  });

  final List<Map<String, dynamic>> questions;
  final int currentIndex;
  final Map<String, Map<String, dynamic>> draftAnswers;
  final int answeredCount;
  final bool isSubmitting;
  final String elapsedLabel;
  final String? disclaimer;
  final TextEditingController textController;
  final bool showListeningTranscript;
  final VoidCallback onToggleTranscript;
  final void Function(String taskId, int optionIndex) onSelectOption;
  final void Function(String taskId, String value) onTextChanged;
  final VoidCallback onPrevious;
  final VoidCallback onNext;
  final VoidCallback onSubmit;

  @override
  Widget build(BuildContext context) {
    final question = questions[currentIndex];
    final taskId = '${question['id'] ?? currentIndex + 1}';
    final taskType = question['task_type']?.toString() ?? 'mcq';
    final isRubricTask =
        taskType == 'speaking_rubric' || taskType == 'writing_rubric';
    final options = List<String>.from(question['options'] ?? const <String>[]);
    final savedAnswer = draftAnswers[taskId];
    final selectedOption = savedAnswer?['selected_option'] as int?;
    final currentText = savedAnswer?['text_response']?.toString() ?? '';
    final wordCount = currentText
        .trim()
        .split(RegExp(r'\s+'))
        .where((w) => w.isNotEmpty)
        .length;
    final minWords = question['min_words'] as int? ?? 15;
    final rubricCriteria = List<String>.from(
      question['rubric_criteria'] ?? const <String>[],
    );
    final passage = question['passage']?.toString();
    final listeningScript = question['listening_script']?.toString();

    final isLast = currentIndex == questions.length - 1;
    final progress = (currentIndex + 1) / questions.length;
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final accent = AppColorRoles.primary(isDark);
    final surface = isDark ? AppColors.surfaceDarkMuted : Colors.white;
    final border = isDark ? AppColors.borderDarkSoft : AppColors.slate200;

    return ListView(
      padding: const EdgeInsets.fromLTRB(16, 12, 16, 24),
      children: [
        if (disclaimer != null && disclaimer!.isNotEmpty) ...[
          Container(
            padding: const EdgeInsets.all(10),
            decoration: BoxDecoration(
              color: accent.withValues(alpha: 0.08),
              borderRadius: BorderRadius.circular(10),
            ),
            child: Text(
              disclaimer!,
              style: Theme.of(context).textTheme.bodySmall,
            ),
          ),
          const SizedBox(height: 10),
        ],
        Row(
          children: [
            Expanded(
              child: Text(
                'assessment.questionCounter'.tr(
                  namedArgs: {
                    'current': '${currentIndex + 1}',
                    'total': '${questions.length}',
                  },
                ),
                style: Theme.of(
                  context,
                ).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700),
              ),
            ),
            _MetaChip(
              icon: Icons.fact_check_rounded,
              label: 'assessment.answeredCount'.tr(
                namedArgs: {
                  'answered': '$answeredCount',
                  'total': '${questions.length}',
                },
              ),
              color: accent,
            ),
          ],
        ),
        const SizedBox(height: 12),
        ClipRRect(
          borderRadius: BorderRadius.circular(999),
          child: LinearProgressIndicator(
            value: progress,
            minHeight: 8,
            backgroundColor: isDark
                ? Colors.white.withValues(alpha: 0.08)
                : AppColors.grey200,
            valueColor: AlwaysStoppedAnimation<Color>(accent),
          ),
        ),
        const SizedBox(height: 18),
        Container(
          padding: const EdgeInsets.all(18),
          decoration: BoxDecoration(
            color: surface,
            borderRadius: BorderRadius.circular(16),
            border: Border.all(color: border),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Wrap(
                spacing: 8,
                runSpacing: 8,
                children: [
                  CefrBadge(
                    level: '${question['level'] ?? 'A1'}',
                    size: CefrBadgeSize.large,
                  ),
                  _TextChip(
                    label: '${question['skill'] ?? 'general'}'.toUpperCase(),
                    icon: Icons.psychology_alt_rounded,
                  ),
                  _TextChip(
                    label: 'assessment.points'.tr(
                      namedArgs: {'points': '${question['points'] ?? 0}'},
                    ),
                    icon: Icons.stars_rounded,
                  ),
                  _TextChip(label: elapsedLabel, icon: Icons.timer_rounded),
                ],
              ),
              if (passage != null && passage.isNotEmpty) ...[
                const SizedBox(height: 14),
                Container(
                  width: double.infinity,
                  padding: const EdgeInsets.all(14),
                  decoration: BoxDecoration(
                    color: isDark
                        ? AppColors.surfaceDarkInput
                        : AppColors.grey50,
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(color: border),
                  ),
                  child: Text(
                    passage,
                    style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                      height: 1.45,
                      fontStyle: FontStyle.italic,
                    ),
                  ),
                ),
              ],
              if (listeningScript != null && listeningScript.isNotEmpty) ...[
                const SizedBox(height: 14),
                Container(
                  width: double.infinity,
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: accent.withValues(alpha: 0.08),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          SpeakIconButton(text: listeningScript, color: accent),
                          const SizedBox(width: 8),
                          const Expanded(
                            child: Text(
                              'Nhấn biểu tượng loa để nghe đoạn hội thoại / thông báo',
                              style: TextStyle(fontWeight: FontWeight.w600),
                            ),
                          ),
                          TextButton(
                            onPressed: onToggleTranscript,
                            child: Text(
                              showListeningTranscript
                                  ? 'Ẩn lời thoại'
                                  : 'Xem lời thoại',
                            ),
                          ),
                        ],
                      ),
                      if (showListeningTranscript) ...[
                        const Divider(),
                        Text(listeningScript),
                      ],
                    ],
                  ),
                ),
              ],
              const SizedBox(height: 18),
              Text(
                '${question['question'] ?? ''}',
                style: Theme.of(context).textTheme.titleLarge?.copyWith(
                  fontWeight: FontWeight.w800,
                  height: 1.25,
                ),
              ),
              const SizedBox(height: 16),
              if (isRubricTask) ...[
                if (question['prompt_hint'] != null) ...[
                  Text(
                    '${question['prompt_hint']}',
                    style: Theme.of(context).textTheme.bodySmall?.copyWith(
                      color: AppColorRoles.textSecondary(isDark),
                    ),
                  ),
                  const SizedBox(height: 10),
                ],
                if (rubricCriteria.isNotEmpty) ...[
                  Container(
                    width: double.infinity,
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: isDark
                          ? AppColors.surfaceDarkInput
                          : AppColors.grey50,
                      borderRadius: BorderRadius.circular(10),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text(
                          'Tiêu chí chấm điểm (Deterministic Rubric):',
                          style: TextStyle(fontWeight: FontWeight.bold),
                        ),
                        const SizedBox(height: 6),
                        for (final c in rubricCriteria) Text('• $c'),
                      ],
                    ),
                  ),
                  const SizedBox(height: 12),
                ],
                TextField(
                  controller: textController,
                  minLines: 4,
                  maxLines: 7,
                  onChanged: (val) => onTextChanged(taskId, val),
                  decoration: InputDecoration(
                    hintText: taskType == 'speaking_rubric'
                        ? 'Nhập hoặc ghi âm phần trả lời nói của bạn bằng tiếng Anh...'
                        : 'Viết đoạn văn ngắn bằng tiếng Anh của bạn tại đây...',
                    border: const OutlineInputBorder(),
                    helperText: 'Số từ hiện tại: $wordCount (khuyến nghị >= $minWords từ)',
                  ),
                ),
              ] else ...[
                for (var i = 0; i < options.length; i++) ...[
                  _AnswerOption(
                    index: i,
                    text: options[i],
                    selected: selectedOption == i,
                    onTap: () => onSelectOption(taskId, i),
                  ),
                  if (i != options.length - 1) const SizedBox(height: 10),
                ],
              ],
            ],
          ),
        ),
        const SizedBox(height: 18),
        Row(
          children: [
            Expanded(
              child: OutlinedButton.icon(
                onPressed: currentIndex == 0 ? null : onPrevious,
                icon: const Icon(Icons.arrow_back_rounded),
                label: Text('assessment.previous'.tr()),
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: ElevatedButton.icon(
                onPressed: isSubmitting
                    ? null
                    : isLast
                    ? onSubmit
                    : onNext,
                icon: isSubmitting
                    ? const SizedBox(
                        width: 16,
                        height: 16,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : Icon(
                        isLast
                            ? Icons.check_circle_rounded
                            : Icons.arrow_forward_rounded,
                      ),
                label: Text(
                  isLast
                      ? 'assessment.submitTest'.tr()
                      : 'assessment.next'.tr(),
                ),
                style: ElevatedButton.styleFrom(
                  backgroundColor: accent,
                  foregroundColor: Colors.white,
                ),
              ),
            ),
          ],
        ),
      ],
    );
  }
}

class _AnswerOption extends StatelessWidget {
  const _AnswerOption({
    required this.index,
    required this.text,
    required this.selected,
    required this.onTap,
  });

  final int index;
  final String text;
  final bool selected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final accent = AppColorRoles.primary(isDark);
    final border = selected
        ? accent
        : isDark
        ? AppColors.borderDarkSoft
        : AppColors.slate200;
    final background = selected
        ? accent.withValues(alpha: isDark ? 0.2 : 0.1)
        : isDark
        ? AppColors.surfaceDarkInput
        : AppColors.grey50;

    return Material(
      color: background,
      borderRadius: BorderRadius.circular(12),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(12),
        child: Container(
          width: double.infinity,
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: border, width: selected ? 1.5 : 1),
          ),
          child: Row(
            children: [
              Container(
                width: 28,
                height: 28,
                alignment: Alignment.center,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  color: selected ? accent : Colors.transparent,
                  border: Border.all(color: selected ? accent : border),
                ),
                child: Text(
                  String.fromCharCode(65 + index),
                  style: TextStyle(
                    color: selected
                        ? Colors.white
                        : AppColorRoles.textPrimary(isDark),
                    fontWeight: FontWeight.w800,
                  ),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Text(
                  text,
                  style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                    fontWeight: selected ? FontWeight.w700 : FontWeight.w500,
                    height: 1.25,
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _ResultState extends StatelessWidget {
  const _ResultState({required this.result, required this.onRetake});

  final Map<String, dynamic> result;
  final VoidCallback onRetake;

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final accent = AppColorRoles.primary(isDark);
    final level = '${result['assessed_level'] ?? 'A1'}';
    final score = result['score_percentage'] ?? 0;
    final correct = result['correct_count'] ?? 0;
    final total = result['total_questions'] ?? 0;
    final skillScores = result['skill_scores'] is Map
        ? Map<String, dynamic>.from(result['skill_scores'] as Map)
        : const <String, dynamic>{};
    final recommendations = (result['recommendations'] as List?) ?? const [];
    final recCourses = (result['recommended_courses'] as List?) ?? const [];
    final disclaimer = result['disclaimer']?.toString() ?? '';

    return ListView(
      padding: const EdgeInsets.fromLTRB(16, 18, 16, 24),
      children: [
        Container(
          padding: const EdgeInsets.all(22),
          decoration: BoxDecoration(
            color: isDark ? AppColors.surfaceDarkMuted : Colors.white,
            borderRadius: BorderRadius.circular(18),
            border: Border.all(
              color: isDark ? AppColors.borderDarkSoft : AppColors.slate200,
            ),
          ),
          child: Column(
            children: [
              Container(
                width: 68,
                height: 68,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  color: accent.withValues(alpha: 0.14),
                ),
                child: Icon(
                  Icons.emoji_events_rounded,
                  color: accent,
                  size: 34,
                ),
              ),
              const SizedBox(height: 16),
              Text(
                'assessment.testCompleted'.tr(),
                textAlign: TextAlign.center,
                style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                  fontWeight: FontWeight.w900,
                ),
              ),
              const SizedBox(height: 8),
              if (disclaimer.isNotEmpty)
                Container(
                  padding: const EdgeInsets.all(10),
                  decoration: BoxDecoration(
                    color: Colors.amber.withValues(alpha: 0.12),
                    borderRadius: BorderRadius.circular(10),
                  ),
                  child: Text(
                    disclaimer,
                    textAlign: TextAlign.center,
                    style: Theme.of(context).textTheme.bodySmall,
                  ),
                ),
              const SizedBox(height: 16),
              CefrBadge(
                level: level,
                size: CefrBadgeSize.large,
                outlined: true,
              ),
              const SizedBox(height: 10),
              Text(
                'assessment.yourLevelIs'.tr(namedArgs: {'level': level}),
                style: Theme.of(
                  context,
                ).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w900),
              ),
              const SizedBox(height: 20),
              Row(
                children: [
                  Expanded(
                    child: _ResultMetric(
                      label: 'assessment.score'.tr(),
                      value: '$score%',
                    ),
                  ),
                  const SizedBox(width: 10),
                  Expanded(
                    child: _ResultMetric(
                      label: 'assessment.correct'.tr(),
                      value: '$correct/$total',
                    ),
                  ),
                ],
              ),
              if (skillScores.isNotEmpty) ...[
                const SizedBox(height: 20),
                const Align(
                  alignment: Alignment.centerLeft,
                  child: Text(
                    'Kết quả theo 6 kỹ năng',
                    style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                  ),
                ),
                const SizedBox(height: 10),
                for (final entry in skillScores.entries) ...[
                  Padding(
                    padding: const EdgeInsets.only(bottom: 8),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            Text(entry.key.toUpperCase()),
                            Text('${entry.value}%'),
                          ],
                        ),
                        const SizedBox(height: 4),
                        LinearProgressIndicator(
                          value: ((num.tryParse('${entry.value}') ?? 0) / 100.0)
                              .clamp(0.0, 1.0),
                        ),
                      ],
                    ),
                  ),
                ],
              ],
              if (recommendations.isNotEmpty) ...[
                const SizedBox(height: 16),
                const Align(
                  alignment: Alignment.centerLeft,
                  child: Text(
                    'Đề xuất cải thiện',
                    style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                  ),
                ),
                const SizedBox(height: 8),
                for (final rec in recommendations.whereType<Map>())
                  ListTile(
                    dense: true,
                    contentPadding: EdgeInsets.zero,
                    leading: const Icon(Icons.lightbulb_outline),
                    title: Text('${rec['skill']}'.toUpperCase()),
                    subtitle: Text('${rec['advice'] ?? ''}'),
                  ),
              ],
              if (recCourses.isNotEmpty) ...[
                const SizedBox(height: 12),
                const Align(
                  alignment: Alignment.centerLeft,
                  child: Text(
                    'Khóa học phù hợp',
                    style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                  ),
                ),
                for (final c in recCourses.whereType<Map>())
                  ListTile(
                    dense: true,
                    contentPadding: EdgeInsets.zero,
                    leading: const Icon(Icons.school_outlined),
                    title: Text('${c['title']}'),
                    subtitle: Text('CEFR ${c['level']} • ${c['total_lessons']} bài'),
                  ),
              ],
              const SizedBox(height: 22),
              Row(
                children: [
                  Expanded(
                    child: OutlinedButton.icon(
                      onPressed: onRetake,
                      icon: const Icon(Icons.replay_rounded),
                      label: Text('assessment.retakeTest'.tr()),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: ElevatedButton.icon(
                      onPressed: () => Navigator.of(context).pop(),
                      icon: const Icon(Icons.check_rounded),
                      label: Text('common.done'.tr()),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: accent,
                        foregroundColor: Colors.white,
                      ),
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      ],
    );
  }
}

class _ResultMetric extends StatelessWidget {
  const _ResultMetric({required this.label, required this.value});

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 14),
      decoration: BoxDecoration(
        color: isDark ? AppColors.surfaceDarkInput : AppColors.grey50,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Column(
        children: [
          Text(
            value,
            textAlign: TextAlign.center,
            style: Theme.of(
              context,
            ).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w900),
          ),
          const SizedBox(height: 4),
          Text(
            label,
            textAlign: TextAlign.center,
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
              color: AppColorRoles.textSecondary(isDark),
            ),
          ),
        ],
      ),
    );
  }
}

class _ErrorState extends StatelessWidget {
  const _ErrorState({required this.message, required this.onRetry});

  final String message;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    return _CenteredState(
      icon: Icons.error_outline_rounded,
      title: 'assessment.loadFailed'.tr(),
      message: message,
      actionLabel: 'common.retry'.tr(),
      onAction: onRetry,
    );
  }
}

class _EmptyState extends StatelessWidget {
  const _EmptyState({required this.onRetry});

  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    return _CenteredState(
      icon: Icons.quiz_rounded,
      title: 'assessment.noQuestions'.tr(),
      message: 'assessment.noQuestionsSubtitle'.tr(),
      actionLabel: 'common.retry'.tr(),
      onAction: onRetry,
    );
  }
}

class _CenteredState extends StatelessWidget {
  const _CenteredState({
    required this.icon,
    required this.title,
    required this.message,
    required this.actionLabel,
    required this.onAction,
  });

  final IconData icon;
  final String title;
  final String message;
  final String actionLabel;
  final VoidCallback onAction;

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final accent = AppColorRoles.primary(isDark);

    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(icon, size: 44, color: accent),
            const SizedBox(height: 14),
            Text(
              title,
              textAlign: TextAlign.center,
              style: Theme.of(
                context,
              ).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w800),
            ),
            const SizedBox(height: 8),
            Text(
              message,
              textAlign: TextAlign.center,
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                color: AppColorRoles.textSecondary(isDark),
                height: 1.35,
              ),
            ),
            const SizedBox(height: 18),
            ElevatedButton.icon(
              onPressed: onAction,
              icon: const Icon(Icons.refresh_rounded),
              label: Text(actionLabel),
            ),
          ],
        ),
      ),
    );
  }
}

class _MetaChip extends StatelessWidget {
  const _MetaChip({
    required this.icon,
    required this.label,
    required this.color,
  });

  final IconData icon;
  final String label;
  final Color color;

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
      decoration: BoxDecoration(
        color: color.withValues(alpha: isDark ? 0.18 : 0.1),
        borderRadius: BorderRadius.circular(999),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 15, color: color),
          const SizedBox(width: 6),
          Text(
            label,
            style: TextStyle(
              color: color,
              fontWeight: FontWeight.w800,
              fontSize: 12,
            ),
          ),
        ],
      ),
    );
  }
}

class _TextChip extends StatelessWidget {
  const _TextChip({required this.label, required this.icon});

  final String label;
  final IconData icon;

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 5),
      decoration: BoxDecoration(
        color: isDark ? AppColors.surfaceDarkInput : AppColors.grey100,
        borderRadius: BorderRadius.circular(8),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 14, color: AppColorRoles.textSecondary(isDark)),
          const SizedBox(width: 5),
          Text(
            label,
            style: Theme.of(context).textTheme.labelSmall?.copyWith(
              fontWeight: FontWeight.w700,
              color: AppColorRoles.textSecondary(isDark),
            ),
          ),
        ],
      ),
    );
  }
}
