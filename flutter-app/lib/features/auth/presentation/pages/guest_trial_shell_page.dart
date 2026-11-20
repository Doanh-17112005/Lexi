import 'package:flutter/material.dart';
import 'package:lexilingo_app/core/theme/app_theme.dart';
import 'package:lexilingo_app/features/auth/data/services/guest_session_service.dart';

/// Public trial learning workspace for guests without an authenticated account.
/// Uses only `/api/v1/guest/*` public endpoints and local isolated storage.
class GuestTrialShellPage extends StatefulWidget {
  final GuestSessionService? guestService;
  final VoidCallback onSignInRequested;
  final VoidCallback onRegisterRequested;

  const GuestTrialShellPage({
    super.key,
    this.guestService,
    required this.onSignInRequested,
    required this.onRegisterRequested,
  });

  @override
  State<GuestTrialShellPage> createState() => _GuestTrialShellPageState();
}

class _GuestTrialShellPageState extends State<GuestTrialShellPage> {
  late final GuestSessionService _service;

  bool _isLoadingPack = true;
  String? _packError;
  Map<String, dynamic>? _trialPack;
  GuestTrialProgress _progress = const GuestTrialProgress();

  bool _isLoadingCourses = true;
  String? _coursesError;
  List<Map<String, dynamic>> _publicCourses = const [];

  int _flashcardIndex = 0;
  bool _flashcardFlipped = false;

  bool _showQuizPractice = false;
  bool _isGrading = false;
  final Map<String, String> _selectedQuizAnswers = {};
  Map<String, dynamic>? _quizGradeResult;

  @override
  void initState() {
    super.initState();
    _service = widget.guestService ?? GuestSessionService();
    _loadAll();
  }

  Future<void> _loadAll() async {
    await Future.wait([_loadTrialPack(), _loadCourses()]);
  }

  Future<void> _loadTrialPack() async {
    setState(() {
      _isLoadingPack = true;
      _packError = null;
    });
    try {
      final pack = await _service.fetchTrialPack();
      final progress = await _service.loadProgress();
      if (!mounted) return;
      setState(() {
        _trialPack = pack;
        _progress = progress;
        _isLoadingPack = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _packError = e.toString();
        _isLoadingPack = false;
      });
    }
  }

  Future<void> _loadCourses() async {
    setState(() {
      _isLoadingCourses = true;
      _coursesError = null;
    });
    try {
      final courses = await _service.fetchPublicCourses();
      if (!mounted) return;
      setState(() {
        _publicCourses = courses;
        _isLoadingCourses = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _coursesError = e.toString();
        _isLoadingCourses = false;
      });
    }
  }

  Future<void> _markCurrentVocabLearned(String vocabId) async {
    final updated = await _service.markVocabLearned(vocabId);
    if (!mounted) return;
    setState(() => _progress = updated);
  }

  Future<void> _beginQuizPractice() async {
    final updated = await _service.markTheoryViewed();
    if (!mounted) return;
    setState(() {
      _progress = updated;
      _showQuizPractice = true;
    });
  }

  Future<void> _submitQuiz(List<Map<String, dynamic>> questions) async {
    setState(() => _isGrading = true);
    try {
      final result = await _service.evaluateTrialQuiz(
        questions: questions,
        selectedAnswers: _selectedQuizAnswers,
      );
      final rawItems = (result['results'] as List?) ?? const [];
      final wrongs = <Map<String, dynamic>>[];
      for (final item in rawItems.whereType<Map>()) {
        if (item['is_correct'] != true) {
          final qid = item['question_id']?.toString() ?? '';
          final qObj = questions.firstWhere(
            (q) => q['id'].toString() == qid,
            orElse: () => const {},
          );
          wrongs.add({
            'question_id': qid,
            'prompt': qObj['prompt'] ?? '',
            'selected_option': item['selected_option'] ?? '',
            'correct_option': item['correct_option'] ?? '',
            'explanation': item['explanation'] ?? '',
            'skill': qObj['skill'] ?? 'grammar',
          });
        }
      }
      final updated = await _service.recordQuizResult(
        correctCount: result['correct_count'] as int? ?? 0,
        totalCount: result['total_questions'] as int? ?? questions.length,
        wrongAnswers: wrongs,
      );
      if (!mounted) return;
      setState(() {
        _quizGradeResult = result;
        _progress = updated;
        _isGrading = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() => _isGrading = false);
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(SnackBar(content: Text('Không thể chấm bài: $e')));
    }
  }

  void _showAuthGateDialog(String featureName) {
    showDialog<void>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text('Tính năng cần tài khoản ($featureName)'),
        content: const Text(
          'Đăng nhập hoặc tạo tài khoản miễn phí để lưu XP, mở khóa bảng xếp hạng, AI Tutor và cộng đồng.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(),
            child: const Text('Học thử tiếp'),
          ),
          OutlinedButton(
            onPressed: () {
              Navigator.of(ctx).pop();
              widget.onSignInRequested();
            },
            child: const Text('Đăng nhập'),
          ),
          FilledButton(
            onPressed: () {
              Navigator.of(ctx).pop();
              widget.onRegisterRequested();
            },
            child: const Text('Đăng ký'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final vocabList =
        (_trialPack?['vocabulary_items'] as List?)
            ?.whereType<Map>()
            .map((e) => Map<String, dynamic>.from(e))
            .toList() ??
        const [];
    final theory = _trialPack?['grammar_theory'] is Map
        ? Map<String, dynamic>.from(_trialPack!['grammar_theory'] as Map)
        : null;
    final questions =
        (_trialPack?['quiz_questions'] as List?)
            ?.whereType<Map>()
            .map((e) => Map<String, dynamic>.from(e))
            .toList() ??
        const [];

    return DefaultTabController(
      length: 3,
      child: Scaffold(
        appBar: AppBar(
          title: const Text('LexiLingo • Học thử (Guest)'),
          actions: [
            Padding(
              padding: const EdgeInsets.symmetric(vertical: 8, horizontal: 8),
              child: FilledButton.icon(
                onPressed: widget.onSignInRequested,
                icon: const Icon(Icons.login_rounded, size: 18),
                label: const Text('Đăng nhập'),
              ),
            ),
          ],
          bottom: const TabBar(
            tabs: [
              Tab(icon: Icon(Icons.style_rounded), text: 'Flashcards'),
              Tab(icon: Icon(Icons.menu_book_rounded), text: 'Ngữ pháp'),
              Tab(icon: Icon(Icons.explore_rounded), text: 'Khóa học'),
            ],
          ),
        ),
        body: Column(
          children: [
            Container(
              width: double.infinity,
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
              color: isDark
                  ? AppColors.surfaceDarkMuted
                  : AppColors.primary.withValues(alpha: 0.08),
              child: Wrap(
                spacing: 12,
                runSpacing: 6,
                alignment: WrapAlignment.spaceBetween,
                crossAxisAlignment: WrapCrossAlignment.center,
                children: [
                  Text(
                    'Chế độ Học thử • XP tạm: ${_progress.guestXp} • Đã học: ${_progress.learnedVocabIds.length}/${vocabList.length} từ',
                    style: const TextStyle(fontWeight: FontWeight.w600),
                  ),
                  TextButton(
                    onPressed: widget.onRegisterRequested,
                    child: const Text('Tạo tài khoản để lưu tiến độ →'),
                  ),
                ],
              ),
            ),
            Expanded(
              child: _isLoadingPack
                  ? const Center(child: CircularProgressIndicator())
                  : _packError != null
                  ? Center(
                      child: Column(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Text('Không tải được bài học thử: $_packError'),
                          const SizedBox(height: 12),
                          FilledButton(
                            onPressed: _loadTrialPack,
                            child: const Text('Thử lại'),
                          ),
                        ],
                      ),
                    )
                  : TabBarView(
                      children: [
                        _buildFlashcardTab(vocabList),
                        _buildGrammarAndQuizTab(theory, questions),
                        _buildPublicCoursesTab(),
                      ],
                    ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildFlashcardTab(List<Map<String, dynamic>> vocabList) {
    if (vocabList.isEmpty) {
      return const Center(child: Text('Không có từ vựng học thử.'));
    }
    final card = vocabList[_flashcardIndex % vocabList.length];
    final id = card['id'].toString();
    final isLearned = _progress.learnedVocabIds.contains(id);

    return SingleChildScrollView(
      padding: const EdgeInsets.all(20),
      child: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 560),
          child: Column(
            children: [
              Text(
                'Thẻ ${_flashcardIndex + 1}/${vocabList.length}',
                style: Theme.of(context).textTheme.labelLarge,
              ),
              const SizedBox(height: 12),
              InkWell(
                onTap: () =>
                    setState(() => _flashcardFlipped = !_flashcardFlipped),
                borderRadius: BorderRadius.circular(18),
                child: Card(
                  elevation: 2,
                  child: Padding(
                    padding: const EdgeInsets.all(24),
                    child: Column(
                      children: [
                        Chip(label: Text('${card['cefr_level']} • ${card['part_of_speech']}')),
                        const SizedBox(height: 16),
                        Text(
                          '${card['word']}',
                          style: Theme.of(context).textTheme.headlineMedium
                              ?.copyWith(fontWeight: FontWeight.bold),
                        ),
                        const SizedBox(height: 6),
                        Text(
                          '${card['phonetic']}',
                          style: Theme.of(context).textTheme.titleMedium,
                        ),
                        const SizedBox(height: 16),
                        if (_flashcardFlipped) ...[
                          const Divider(),
                          const SizedBox(height: 12),
                          Text(
                            '${card['meaning']}',
                            textAlign: TextAlign.center,
                            style: Theme.of(context).textTheme.titleMedium,
                          ),
                          const SizedBox(height: 8),
                          Text(
                            'Ví dụ: ${card['example']}',
                            textAlign: TextAlign.center,
                            style: Theme.of(context).textTheme.bodyMedium,
                          ),
                        ] else
                          const Text('Nhấn vào thẻ để xem nghĩa và ví dụ'),
                      ],
                    ),
                  ),
                ),
              ),
              const SizedBox(height: 16),
              Wrap(
                spacing: 12,
                runSpacing: 8,
                alignment: WrapAlignment.center,
                children: [
                  OutlinedButton.icon(
                    onPressed: _flashcardIndex > 0
                        ? () => setState(() {
                            _flashcardIndex--;
                            _flashcardFlipped = false;
                          })
                        : null,
                    icon: const Icon(Icons.arrow_back),
                    label: const Text('Trước'),
                  ),
                  FilledButton.icon(
                    onPressed: isLearned
                        ? null
                        : () => _markCurrentVocabLearned(id),
                    icon: Icon(
                      isLearned ? Icons.check_circle : Icons.bookmark_added,
                    ),
                    label: Text(isLearned ? 'Đã thuộc (+10 XP)' : 'Đánh dấu đã thuộc'),
                  ),
                  OutlinedButton.icon(
                    onPressed: _flashcardIndex + 1 < vocabList.length
                        ? () => setState(() {
                            _flashcardIndex++;
                            _flashcardFlipped = false;
                          })
                        : null,
                    icon: const Icon(Icons.arrow_forward),
                    label: const Text('Tiếp'),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildGrammarAndQuizTab(
    Map<String, dynamic>? theory,
    List<Map<String, dynamic>> questions,
  ) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(20),
      child: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 640),
          child: !_showQuizPractice && theory != null
              ? Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Chip(label: Text('Ngữ pháp ${theory['level'] ?? 'A1'}')),
                    const SizedBox(height: 8),
                    Text(
                      '${theory['title']}',
                      style: Theme.of(context).textTheme.titleLarge?.copyWith(
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: 12),
                    Card(
                      child: Padding(
                        padding: const EdgeInsets.all(16),
                        child: Text('${theory['explanation']}'),
                      ),
                    ),
                    const SizedBox(height: 12),
                    for (final ex
                        in (theory['examples'] as List?) ?? const [])
                      Card(
                        margin: const EdgeInsets.only(bottom: 8),
                        child: ListTile(
                          title: Text('${ex['sentence'] ?? ex}'),
                          subtitle: ex is Map && ex['translation'] != null
                              ? Text('${ex['translation']}')
                              : null,
                        ),
                      ),
                    const SizedBox(height: 16),
                    SizedBox(
                      width: double.infinity,
                      child: FilledButton(
                        onPressed: _beginQuizPractice,
                        child: Text(
                          'Bắt đầu bài tập thử (${questions.length} câu)',
                        ),
                      ),
                    ),
                  ],
                )
              : Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Wrap(
                      spacing: 8,
                      runSpacing: 4,
                      alignment: WrapAlignment.spaceBetween,
                      crossAxisAlignment: WrapCrossAlignment.center,
                      children: [
                        Text(
                          'Bài tập thử (${questions.length} câu)',
                          style: Theme.of(context).textTheme.titleLarge,
                        ),
                        if (theory != null)
                          TextButton(
                            onPressed: () =>
                                setState(() => _showQuizPractice = false),
                            child: const Text('Xem lại lý thuyết'),
                          ),
                      ],
                    ),
                    const SizedBox(height: 12),
                    for (final q in questions)
                      Card(
                        margin: const EdgeInsets.only(bottom: 12),
                        child: Padding(
                          padding: const EdgeInsets.all(16),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                '${q['prompt']}',
                                style: const TextStyle(
                                  fontWeight: FontWeight.w600,
                                ),
                              ),
                              const SizedBox(height: 8),
                              Wrap(
                                spacing: 8,
                                runSpacing: 8,
                                children: [
                                  for (final opt
                                      in (q['options'] as List?) ?? const [])
                                    ChoiceChip(
                                      label: Text(opt.toString()),
                                      selected:
                                          _selectedQuizAnswers[q['id']
                                              .toString()] ==
                                          opt.toString(),
                                      onSelected: _quizGradeResult == null
                                          ? (_) => setState(() {
                                              _selectedQuizAnswers[q['id']
                                                      .toString()] =
                                                  opt.toString();
                                            })
                                          : null,
                                    ),
                                ],
                              ),
                            ],
                          ),
                        ),
                      ),
                    if (_quizGradeResult != null) ...[
                      Card(
                        color: AppColors.primary.withValues(alpha: 0.1),
                        child: Padding(
                          padding: const EdgeInsets.all(16),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                'Kết quả: ${_quizGradeResult!['correct_count']}/${_quizGradeResult!['total_questions']} (${_quizGradeResult!['score_percentage']}%)',
                                style: Theme.of(context).textTheme.titleMedium
                                    ?.copyWith(fontWeight: FontWeight.bold),
                              ),
                              const SizedBox(height: 8),
                              const Text(
                                'Đăng nhập hoặc tạo tài khoản để đồng bộ XP và ghi chú lỗi sai.',
                              ),
                            ],
                          ),
                        ),
                      ),
                      const SizedBox(height: 12),
                    ],
                    SizedBox(
                      width: double.infinity,
                      child: FilledButton(
                        onPressed: _isGrading
                            ? null
                            : _quizGradeResult == null
                            ? (_selectedQuizAnswers.length == questions.length
                                  ? () => _submitQuiz(questions)
                                  : null)
                            : widget.onSignInRequested,
                        child: Text(
                          _quizGradeResult == null
                              ? (_isGrading
                                    ? 'Đang chấm...'
                                    : 'Nộp bài (${_selectedQuizAnswers.length}/${questions.length})')
                              : 'Đăng nhập để lưu kết quả',
                        ),
                      ),
                    ),
                  ],
                ),
        ),
      ),
    );
  }

  Widget _buildPublicCoursesTab() {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(20),
      child: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 720),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Tính năng yêu cầu tài khoản',
                style: Theme.of(context).textTheme.titleMedium,
              ),
              const SizedBox(height: 8),
              Wrap(
                spacing: 8,
                runSpacing: 8,
                children: [
                  for (final gated in const [
                    'AI Tutor Chat',
                    'Bảng xếp hạng',
                    'Cộng đồng',
                    'Gói Premium',
                  ])
                    ActionChip(
                      avatar: const Icon(Icons.lock_outline, size: 16),
                      label: Text(gated),
                      onPressed: () => _showAuthGateDialog(gated),
                    ),
                ],
              ),
              const SizedBox(height: 20),
              Text(
                'Khóa học công khai (Xem trước)',
                style: Theme.of(context).textTheme.titleMedium,
              ),
              const SizedBox(height: 10),
              if (_isLoadingCourses)
                const Center(child: CircularProgressIndicator())
              else if (_coursesError != null)
                Card(
                  child: ListTile(
                    title: const Text('Không tải được danh sách khóa học công khai'),
                    subtitle: Text(_coursesError!),
                    trailing: TextButton(
                      onPressed: _loadCourses,
                      child: const Text('Thử lại'),
                    ),
                  ),
                )
              else if (_publicCourses.isEmpty)
                const Card(
                  child: Padding(
                    padding: EdgeInsets.all(16),
                    child: Text('Chưa có khóa học công khai.'),
                  ),
                )
              else
                for (final course in _publicCourses)
                  Card(
                    margin: const EdgeInsets.only(bottom: 10),
                    child: ListTile(
                      leading: CircleAvatar(
                        child: Text('${course['level'] ?? 'A1'}'),
                      ),
                      title: Text('${course['title']}'),
                      subtitle: Text(
                        '${course['description'] ?? ''} (${course['total_lessons'] ?? 0} bài)',
                        maxLines: 2,
                        overflow: TextOverflow.ellipsis,
                      ),
                      trailing: const Icon(Icons.lock_open_outlined),
                      onTap: () => _showAuthGateDialog('${course['title']}'),
                    ),
                  ),
            ],
          ),
        ),
      ),
    );
  }
}
