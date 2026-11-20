import 'dart:convert';
import 'dart:typed_data';

import 'package:lexilingo_app/core/di/service_locator.dart';
import 'package:lexilingo_app/core/network/api_client.dart';
import 'package:lexilingo_app/features/mistakes/data/mistake_notebook_repository.dart';
import 'package:lexilingo_app/features/mistakes/domain/mistake_notebook_entry.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// Isolated guest trial progress stored exclusively under `guest_trial_v1:*`
/// keys so authenticated user scopes remain completely separated.
class GuestTrialProgress {
  final String manifestVersion;
  final List<String> learnedVocabIds;
  final bool theoryViewed;
  final int? quizCorrectCount;
  final int? quizTotalCount;
  final int guestXp;
  final List<Map<String, dynamic>> guestMistakes;

  const GuestTrialProgress({
    this.manifestVersion = GuestSessionService.manifestVersion,
    this.learnedVocabIds = const [],
    this.theoryViewed = false,
    this.quizCorrectCount,
    this.quizTotalCount,
    this.guestXp = 0,
    this.guestMistakes = const [],
  });

  bool get hasAnyProgress =>
      learnedVocabIds.isNotEmpty ||
      theoryViewed ||
      quizCorrectCount != null ||
      guestXp > 0 ||
      guestMistakes.isNotEmpty;

  GuestTrialProgress copyWith({
    String? manifestVersion,
    List<String>? learnedVocabIds,
    bool? theoryViewed,
    int? quizCorrectCount,
    int? quizTotalCount,
    int? guestXp,
    List<Map<String, dynamic>>? guestMistakes,
  }) {
    return GuestTrialProgress(
      manifestVersion: manifestVersion ?? this.manifestVersion,
      learnedVocabIds: learnedVocabIds ?? this.learnedVocabIds,
      theoryViewed: theoryViewed ?? this.theoryViewed,
      quizCorrectCount: quizCorrectCount ?? this.quizCorrectCount,
      quizTotalCount: quizTotalCount ?? this.quizTotalCount,
      guestXp: guestXp ?? this.guestXp,
      guestMistakes: guestMistakes ?? this.guestMistakes,
    );
  }

  Map<String, dynamic> toJson() => {
    'manifest_version': manifestVersion,
    'learned_vocab_ids': learnedVocabIds,
    'theory_viewed': theoryViewed,
    'quiz_correct_count': quizCorrectCount,
    'quiz_total_count': quizTotalCount,
    'guest_xp': guestXp,
    'guest_mistakes': guestMistakes,
  };

  factory GuestTrialProgress.fromJson(Map<String, dynamic> json) {
    return GuestTrialProgress(
      manifestVersion:
          json['manifest_version'] as String? ??
          GuestSessionService.manifestVersion,
      learnedVocabIds:
          (json['learned_vocab_ids'] as List?)
              ?.map((e) => e.toString())
              .toList() ??
          const [],
      theoryViewed: json['theory_viewed'] as bool? ?? false,
      quizCorrectCount: json['quiz_correct_count'] as int?,
      quizTotalCount: json['quiz_total_count'] as int?,
      guestXp: json['guest_xp'] as int? ?? 0,
      guestMistakes:
          (json['guest_mistakes'] as List?)
              ?.whereType<Map>()
              .map((e) => Map<String, dynamic>.from(e))
              .toList() ??
          const [],
    );
  }
}

class GuestConversionResult {
  final bool migrated;
  final bool alreadyHandled;
  final int migratedMistakesCount;
  final int migratedXpEstimate;

  const GuestConversionResult({
    required this.migrated,
    required this.alreadyHandled,
    this.migratedMistakesCount = 0,
    this.migratedXpEstimate = 0,
  });
}

class GuestSessionService {
  static const String manifestVersion = '2026.1.0';
  static const String _activeKey = 'guest_trial_v1:active';
  static const String _progressKey = 'guest_trial_v1:progress';
  static const String _convertedUsersKey = 'guest_trial_v1:converted_users';
  static const String _declinedUsersKey = 'guest_trial_v1:declined_users';

  final Future<SharedPreferences> Function() _prefsFactory;
  final ApiClient? _apiClient;

  GuestSessionService({
    Future<SharedPreferences> Function()? prefsFactory,
    ApiClient? apiClient,
  }) : _prefsFactory = prefsFactory ?? SharedPreferences.getInstance,
       _apiClient = apiClient;

  ApiClient? get _client {
    if (_apiClient != null) return _apiClient;
    if (sl.isRegistered<ApiClient>()) return sl<ApiClient>();
    return null;
  }

  Future<bool> isGuestActive() async {
    final prefs = await _prefsFactory();
    return prefs.getBool(_activeKey) ?? false;
  }

  Future<void> setGuestActive(bool active) async {
    final prefs = await _prefsFactory();
    await prefs.setBool(_activeKey, active);
  }

  Future<GuestTrialProgress> loadProgress() async {
    final prefs = await _prefsFactory();
    final raw = prefs.getString(_progressKey);
    if (raw == null || raw.isEmpty) {
      return const GuestTrialProgress();
    }
    try {
      final decoded = jsonDecode(raw);
      if (decoded is Map<String, dynamic>) {
        return GuestTrialProgress.fromJson(decoded);
      }
    } catch (_) {}
    return const GuestTrialProgress();
  }

  Future<void> _saveProgress(GuestTrialProgress progress) async {
    final prefs = await _prefsFactory();
    await prefs.setString(_progressKey, jsonEncode(progress.toJson()));
  }

  Future<GuestTrialProgress> markVocabLearned(String vocabId) async {
    final current = await loadProgress();
    if (current.learnedVocabIds.contains(vocabId)) {
      return current;
    }
    final nextIds = [...current.learnedVocabIds, vocabId];
    final next = current.copyWith(
      learnedVocabIds: nextIds,
      guestXp: _computeGuestXp(
        learnedCount: nextIds.length,
        theoryViewed: current.theoryViewed,
        correctCount: current.quizCorrectCount ?? 0,
      ),
    );
    await _saveProgress(next);
    return next;
  }

  Future<GuestTrialProgress> markTheoryViewed() async {
    final current = await loadProgress();
    if (current.theoryViewed) return current;
    final next = current.copyWith(
      theoryViewed: true,
      guestXp: _computeGuestXp(
        learnedCount: current.learnedVocabIds.length,
        theoryViewed: true,
        correctCount: current.quizCorrectCount ?? 0,
      ),
    );
    await _saveProgress(next);
    return next;
  }

  Future<GuestTrialProgress> recordQuizResult({
    required int correctCount,
    required int totalCount,
    required List<Map<String, dynamic>> wrongAnswers,
  }) async {
    final current = await loadProgress();
    final bestCorrect = (current.quizCorrectCount ?? 0) > correctCount
        ? (current.quizCorrectCount ?? 0)
        : correctCount;
    final next = current.copyWith(
      quizCorrectCount: correctCount,
      quizTotalCount: totalCount,
      guestMistakes: wrongAnswers,
      guestXp: _computeGuestXp(
        learnedCount: current.learnedVocabIds.length,
        theoryViewed: current.theoryViewed,
        correctCount: bestCorrect,
      ),
    );
    await _saveProgress(next);
    return next;
  }

  int _computeGuestXp({
    required int learnedCount,
    required bool theoryViewed,
    required int correctCount,
  }) {
    return (learnedCount * 10) + (theoryViewed ? 5 : 0) + (correctCount * 10);
  }

  /// Fetch public versioned trial manifest from `/guest/trial-pack`.
  /// Falls back cleanly to bundled offline manifest when offline.
  Future<Map<String, dynamic>> fetchTrialPack() async {
    final client = _client;
    if (client != null) {
      try {
        final res = await client.get('/guest/trial-pack');
        final data = res['data'];
        if (data is Map<String, dynamic>) {
          return data;
        }
      } catch (_) {}
    }
    return bundledOfflineTrialPack();
  }

  /// Fetch public published courses preview (`GET /guest/courses`).
  Future<List<Map<String, dynamic>>> fetchPublicCourses() async {
    final client = _client;
    if (client == null) {
      throw Exception('API client unavailable');
    }
    final res = await client.get('/guest/courses?limit=10');
    final data = res['data'];
    if (data is List) {
      return data
          .whereType<Map>()
          .map((e) => Map<String, dynamic>.from(e))
          .toList();
    }
    return const [];
  }

  /// Grade quiz answers via `/guest/trial-pack/grade` when online,
  /// otherwise grade deterministically using SHA-256 digests (`answer_digest`).
  Future<Map<String, dynamic>> evaluateTrialQuiz({
    required List<Map<String, dynamic>> questions,
    required Map<String, String> selectedAnswers,
  }) async {
    final client = _client;
    if (client != null) {
      try {
        final payload = questions
            .map(
              (q) => {
                'question_id': q['id'].toString(),
                'selected_option': selectedAnswers[q['id'].toString()] ?? '',
              },
            )
            .toList();
        final res = await client.post(
          '/guest/trial-pack/grade',
          body: {'answers': payload},
        );
        final data = res['data'];
        if (data is Map<String, dynamic>) {
          return data;
        }
      } catch (_) {}
    }

    // Offline deterministic SHA-256 verification against `answer_digest`.
    final results = <Map<String, dynamic>>[];
    var correctCount = 0;
    for (final q in questions) {
      final qid = q['id'].toString();
      final selected = (selectedAnswers[qid] ?? '').trim();
      final digest = q['answer_digest']?.toString() ?? '';
      final computed = sha256Hex('$qid:${selected.toLowerCase()}');
      final isCorrect =
          selected.isNotEmpty && digest.isNotEmpty && computed == digest;
      if (isCorrect) correctCount++;

      // Find matching option whose digest matches when offline
      var matchedOption = '';
      if (digest.isNotEmpty && q['options'] is List) {
        for (final opt in q['options'] as List) {
          final optText = opt.toString().trim();
          if (sha256Hex('$qid:${optText.toLowerCase()}') == digest) {
            matchedOption = optText;
            break;
          }
        }
      }

      results.add({
        'question_id': qid,
        'selected_option': selected,
        'correct_option': matchedOption,
        'is_correct': isCorrect,
        'explanation': '',
      });
    }
    final total = questions.length;
    final pct = total == 0 ? 0.0 : (correctCount / total) * 100.0;
    return {
      'manifest_version': manifestVersion,
      'correct_count': correctCount,
      'total_questions': total,
      'score_percentage': double.parse(pct.toStringAsFixed(1)),
      'results': results,
      'offline': true,
    };
  }

  /// Conversion guard: only offer conversion if guest has progress AND this user
  /// has neither already converted nor declined it.
  Future<bool> canOfferConversionFor(String userId) async {
    if (userId.isEmpty) return false;
    final progress = await loadProgress();
    if (!progress.hasAnyProgress) return false;
    final prefs = await _prefsFactory();
    final converted = prefs.getStringList(_convertedUsersKey) ?? const [];
    final declined = prefs.getStringList(_declinedUsersKey) ?? const [];
    return !converted.contains(userId) && !declined.contains(userId);
  }

  Future<void> declineConversion(String userId) async {
    if (userId.isEmpty) return;
    final prefs = await _prefsFactory();
    final declined = List<String>.from(
      prefs.getStringList(_declinedUsersKey) ?? const [],
    );
    if (!declined.contains(userId)) {
      declined.add(userId);
      await prefs.setStringList(_declinedUsersKey, declined);
    }
  }

  /// Idempotently converts local guest trial mistakes/progress into the newly
  /// signed-in user's scope and clears the temporary guest progress afterward.
  Future<GuestConversionResult> migrateToAuthenticatedAccount({
    required String userId,
    MistakeNotebookRepository mistakeRepository =
        const MistakeNotebookRepository(),
  }) async {
    final prefs = await _prefsFactory();
    final converted = List<String>.from(
      prefs.getStringList(_convertedUsersKey) ?? const [],
    );
    if (converted.contains(userId)) {
      return const GuestConversionResult(migrated: false, alreadyHandled: true);
    }

    final progress = await loadProgress();
    if (!progress.hasAnyProgress) {
      return const GuestConversionResult(migrated: false, alreadyHandled: true);
    }

    var migratedMistakes = 0;
    for (final m in progress.guestMistakes) {
      final qid = m['question_id']?.toString() ?? '';
      if (qid.isEmpty) continue;
      await mistakeRepository.saveMistake(
        MistakeNotebookEntry(
          id: 'guest_trial_$qid',
          sourceType: 'guest_trial',
          sourceId: '${progress.manifestVersion}:$qid',
          sourceTitle: 'Guest Trial Quiz',
          question: m['prompt']?.toString() ?? m['question']?.toString() ?? '',
          selectedAnswer: m['selected_option']?.toString() ?? '',
          correctAnswer: m['correct_option']?.toString() ?? '',
          explanation: m['explanation']?.toString() ?? '',
          skill: m['skill']?.toString() ?? 'grammar',
          createdAt: DateTime.now(),
        ),
      );
      migratedMistakes++;
    }

    converted.add(userId);
    await prefs.setStringList(_convertedUsersKey, converted);
    await prefs.remove(_progressKey);
    await prefs.setBool(_activeKey, false);

    return GuestConversionResult(
      migrated: true,
      alreadyHandled: false,
      migratedMistakesCount: migratedMistakes,
      migratedXpEstimate: progress.guestXp,
    );
  }

  static Map<String, dynamic> bundledOfflineTrialPack() => {
    'manifest_version': manifestVersion,
    'policy': {
      'requires_auth': false,
      'creates_user': false,
      'offline_capable': true,
      'premium_included': false,
      'gated_features': ['leaderboard', 'social', 'ai_chat', 'premium'],
    },
    'vocabulary_items': const [
      {
        'id': 'guest-vocab-1',
        'word': 'commute',
        'phonetic': '/kəˈmjuːt/',
        'part_of_speech': 'verb',
        'meaning': 'To travel regularly between home and work or school.',
        'cefr_level': 'A2',
        'topic': 'work',
        'example': 'I commute by train every morning.',
      },
      {
        'id': 'guest-vocab-2',
        'word': 'schedule',
        'phonetic': '/ˈskedʒuːl/',
        'part_of_speech': 'noun',
        'meaning': 'A plan of activities and when they will happen.',
        'cefr_level': 'A2',
        'topic': 'daily_life',
        'example': 'Let me check my schedule for tomorrow.',
      },
      {
        'id': 'guest-vocab-3',
        'word': 'confirm',
        'phonetic': '/kənˈfɜːrm/',
        'part_of_speech': 'verb',
        'meaning':
            'To state or show that something is definitely true or arranged.',
        'cefr_level': 'A2',
        'topic': 'communication',
        'example': 'Please confirm your reservation before Friday.',
      },
      {
        'id': 'guest-vocab-4',
        'word': 'neighborhood',
        'phonetic': '/ˈneɪbərhʊd/',
        'part_of_speech': 'noun',
        'meaning': 'The area of a town or city around where someone lives.',
        'cefr_level': 'A2',
        'topic': 'community',
        'example': 'There is a quiet park in my neighborhood.',
      },
      {
        'id': 'guest-vocab-5',
        'word': 'prepare',
        'phonetic': '/prɪˈper/',
        'part_of_speech': 'verb',
        'meaning': 'To get ready for an event or task.',
        'cefr_level': 'A1',
        'topic': 'daily_life',
        'example': 'She prepares breakfast at seven.',
      },
      {
        'id': 'guest-vocab-6',
        'word': 'polite',
        'phonetic': '/pəˈlaɪt/',
        'part_of_speech': 'adjective',
        'meaning': 'Behaving in a respectful and considerate way.',
        'cefr_level': 'A2',
        'topic': 'communication',
        'example': "Using 'could you' is a polite way to ask.",
      },
    ],
    'grammar_theory': const {
      'id': 'guest-grammar-1',
      'version': manifestVersion,
      'title': 'Present Simple for Routines & Prepositions (at / on / in)',
      'level': 'A1',
      'topic': 'tenses_and_time',
      'summary':
          'Express daily habits cleanly and pair them with accurate time prepositions.',
      'explanation':
          "Use the base verb with I/you/we/they and add -s/-es with he/she/it for daily routines. Pair clock times with 'at' (at 8:00), days with 'on' (on Monday), and months/parts of the day with 'in' (in the morning).",
      'grammar_points': [
        "Subject (he/she/it) + Verb-s/-es: 'She commutes by bus.'",
        'Time prepositions: at + clock time, on + day, in + morning/month.',
      ],
      'examples': [
        {
          'sentence': 'She prepares breakfast at 7:00 every morning.',
          'translation': 'Cô ấy chuẩn bị bữa sáng lúc 7 giờ mỗi sáng.',
        },
        {
          'sentence': 'Our team meets on Monday to confirm the schedule.',
          'translation':
              'Nhóm của chúng tôi họp vào thứ Hai để xác nhận lịch trình.',
        },
      ],
    },
    'quiz_questions': [
      {
        'id': 'gq-1',
        'skill': 'grammar',
        'topic': 'present_simple',
        'prompt': 'She ___ to work by train every morning.',
        'options': ['commute', 'commutes', 'commuting', 'commuted'],
        'answer_digest': sha256Hex('gq-1:commutes'),
      },
      {
        'id': 'gq-2',
        'skill': 'grammar',
        'topic': 'time_prepositions',
        'prompt': 'The English club meets ___ Friday evening.',
        'options': ['in', 'at', 'on', 'to'],
        'answer_digest': sha256Hex('gq-2:on'),
      },
      {
        'id': 'gq-3',
        'skill': 'vocabulary',
        'topic': 'daily_life',
        'prompt':
            'Before buying train tickets, please ___ the departure time.',
        'options': ['confirm', 'neighborhood', 'polite', 'ignore'],
        'answer_digest': sha256Hex('gq-3:confirm'),
      },
      {
        'id': 'gq-4',
        'skill': 'vocabulary',
        'topic': 'communication',
        'prompt': "Saying 'Could you help me, please?' sounds ___.",
        'options': ['polite', 'schedule', 'ancient', 'rare'],
        'answer_digest': sha256Hex('gq-4:polite'),
      },
    ],
  };

  /// Pure-Dart SHA-256 hex digest (matches Python `hashlib.sha256`).
  static String sha256Hex(String input) {
    final bytes = utf8.encode(input);
    const k = <int>[
      0x428a2f98,
      0x71374491,
      0xb5c0fbcf,
      0xe9b5dba5,
      0x3956c25b,
      0x59f111f1,
      0x923f82a4,
      0xab1c5ed5,
      0xd807aa98,
      0x12835b01,
      0x243185be,
      0x550c7dc3,
      0x72be5d74,
      0x80deb1fe,
      0x9bdc06a7,
      0xc19bf174,
      0xe49b69c1,
      0xefbe4786,
      0x0fc19dc6,
      0x240ca1cc,
      0x2de92c6f,
      0x4a7484aa,
      0x5cb0a9dc,
      0x76f988da,
      0x983e5152,
      0xa831c66d,
      0xb00327c8,
      0xbf597fc7,
      0xc6e00bf3,
      0xd5a79147,
      0x06ca6351,
      0x14292967,
      0x27b70a85,
      0x2e1b2138,
      0x4d2c6dfc,
      0x53380d13,
      0x650a7354,
      0x766a0abb,
      0x81c2c92e,
      0x92722c85,
      0xa2bfe8a1,
      0xa81a664b,
      0xc24b8b70,
      0xc76c51a3,
      0xd192e819,
      0xd6990624,
      0xf40e3585,
      0x106aa070,
      0x19a4c116,
      0x1e376c08,
      0x2748774c,
      0x34b0bcb5,
      0x391c0cb3,
      0x4ed8aa4a,
      0x5b9cca4f,
      0x682e6ff3,
      0x748f82ee,
      0x78a5636f,
      0x84c87814,
      0x8cc70208,
      0x90befffa,
      0xa4506ceb,
      0xbef9a3f7,
      0xc67178f2,
    ];
    final h = <int>[
      0x6a09e667,
      0xbb67ae85,
      0x3c6ef372,
      0xa54ff53a,
      0x510e527f,
      0x9b05688c,
      0x1f83d9ab,
      0x5be0cd19,
    ];

    int rotr(int x, int n) => ((x & 0xffffffff) >> n) | ((x << (32 - n)) & 0xffffffff);

    final bitLen = bytes.length * 8;
    final padLen = ((56 - (bytes.length + 1) % 64) + 64) % 64;
    final padded = Uint8List(bytes.length + 1 + padLen + 8);
    padded.setAll(0, bytes);
    padded[bytes.length] = 0x80;
    final bd = ByteData.sublistView(padded);
    bd.setUint32(padded.length - 8, (bitLen >> 32) & 0xffffffff, Endian.big);
    bd.setUint32(padded.length - 4, bitLen & 0xffffffff, Endian.big);

    final w = List<int>.filled(64, 0);
    for (var i = 0; i < padded.length; i += 64) {
      for (var t = 0; t < 16; t++) {
        w[t] = bd.getUint32(i + t * 4, Endian.big);
      }
      for (var t = 16; t < 64; t++) {
        final s0 = rotr(w[t - 15], 7) ^ rotr(w[t - 15], 18) ^ ((w[t - 15] & 0xffffffff) >> 3);
        final s1 = rotr(w[t - 2], 17) ^ rotr(w[t - 2], 19) ^ ((w[t - 2] & 0xffffffff) >> 10);
        w[t] = (w[t - 16] + s0 + w[t - 7] + s1) & 0xffffffff;
      }

      var a = h[0], b = h[1], c = h[2], d = h[3];
      var e = h[4], f = h[5], g = h[6], hh = h[7];

      for (var t = 0; t < 64; t++) {
        final s1 = rotr(e, 6) ^ rotr(e, 11) ^ rotr(e, 25);
        final ch = (e & f) ^ ((~e) & g);
        final temp1 = (hh + s1 + ch + k[t] + w[t]) & 0xffffffff;
        final s0 = rotr(a, 2) ^ rotr(a, 13) ^ rotr(a, 22);
        final maj = (a & b) ^ (a & c) ^ (b & c);
        final temp2 = (s0 + maj) & 0xffffffff;

        hh = g;
        g = f;
        f = e;
        e = (d + temp1) & 0xffffffff;
        d = c;
        c = b;
        b = a;
        a = (temp1 + temp2) & 0xffffffff;
      }

      h[0] = (h[0] + a) & 0xffffffff;
      h[1] = (h[1] + b) & 0xffffffff;
      h[2] = (h[2] + c) & 0xffffffff;
      h[3] = (h[3] + d) & 0xffffffff;
      h[4] = (h[4] + e) & 0xffffffff;
      h[5] = (h[5] + f) & 0xffffffff;
      h[6] = (h[6] + g) & 0xffffffff;
      h[7] = (h[7] + hh) & 0xffffffff;
    }

    return h.map((v) => v.toRadixString(16).padLeft(8, '0')).join();
  }
}
