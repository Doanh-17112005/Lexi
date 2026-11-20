/// Sanitized grammar theory attached to a grammar lesson.
class GrammarTheoryEntity {
  final String? grammarItemId;
  final String? version;
  final String title;
  final String? level;
  final String? topic;
  final String? summary;
  final String explanation;
  final List<dynamic> examples;
  final List<dynamic> grammarPoints;
  final List<String> linkedExerciseIds;

  const GrammarTheoryEntity({
    this.grammarItemId,
    this.version,
    required this.title,
    this.level,
    this.topic,
    this.summary,
    required this.explanation,
    this.examples = const [],
    this.grammarPoints = const [],
    this.linkedExerciseIds = const [],
  });

  factory GrammarTheoryEntity.fromJson(Map<String, dynamic> json) {
    return GrammarTheoryEntity(
      grammarItemId: json['grammar_item_id']?.toString(),
      version: json['version']?.toString(),
      title: json['title'] as String? ?? '',
      level: json['level'] as String?,
      topic: json['topic'] as String?,
      summary: json['summary'] as String?,
      explanation: json['explanation'] as String? ?? '',
      examples: (json['examples'] as List?) ?? const [],
      grammarPoints: (json['grammar_points'] as List?) ?? const [],
      linkedExerciseIds:
          (json['linked_exercise_ids'] as List?)
              ?.map((e) => e.toString())
              .toList() ??
          const [],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'grammar_item_id': grammarItemId,
      'version': version,
      'title': title,
      'level': level,
      'topic': topic,
      'summary': summary,
      'explanation': explanation,
      'examples': examples,
      'grammar_points': grammarPoints,
      'linked_exercise_ids': linkedExerciseIds,
    };
  }
}

/// Lesson Entity
/// Represents a lesson with its exercises
class LessonEntity {
  final String id;
  final String title;
  final String? description;
  final String? outcome;
  final int orderIndex;
  final List<Exercise> exercises;
  final int estimatedMinutes;
  final int xpReward;
  final GrammarTheoryEntity? grammarTheory;
  final bool theoryViewed;

  LessonEntity({
    required this.id,
    required this.title,
    this.description,
    this.outcome,
    required this.orderIndex,
    required this.exercises,
    required this.estimatedMinutes,
    required this.xpReward,
    this.grammarTheory,
    this.theoryViewed = false,
  });

  LessonEntity copyWith({
    String? id,
    String? title,
    String? description,
    String? outcome,
    int? orderIndex,
    List<Exercise>? exercises,
    int? estimatedMinutes,
    int? xpReward,
    GrammarTheoryEntity? grammarTheory,
    bool? theoryViewed,
  }) {
    return LessonEntity(
      id: id ?? this.id,
      title: title ?? this.title,
      description: description ?? this.description,
      outcome: outcome ?? this.outcome,
      orderIndex: orderIndex ?? this.orderIndex,
      exercises: exercises ?? this.exercises,
      estimatedMinutes: estimatedMinutes ?? this.estimatedMinutes,
      xpReward: xpReward ?? this.xpReward,
      grammarTheory: grammarTheory ?? this.grammarTheory,
      theoryViewed: theoryViewed ?? this.theoryViewed,
    );
  }

  factory LessonEntity.fromJson(Map<String, dynamic> json) {
    return LessonEntity(
      id: json['id'] as String,
      title: json['title'] as String,
      description: json['description'] as String?,
      outcome: json['outcome'] as String?,
      orderIndex: json['order_index'] as int,
      exercises:
          (json['exercises'] as List?)
              ?.map((e) => Exercise.fromJson(e as Map<String, dynamic>))
              .toList() ??
          [],
      estimatedMinutes: json['estimated_minutes'] as int? ?? 10,
      xpReward: json['xp_reward'] as int? ?? 50,
      grammarTheory: json['grammar_theory'] is Map<String, dynamic>
          ? GrammarTheoryEntity.fromJson(
              json['grammar_theory'] as Map<String, dynamic>,
            )
          : null,
      theoryViewed: json['theory_viewed'] as bool? ?? false,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'title': title,
      'description': description,
      'outcome': outcome,
      'order_index': orderIndex,
      'exercises': exercises.map((e) => e.toJson()).toList(),
      'estimated_minutes': estimatedMinutes,
      'xp_reward': xpReward,
      if (grammarTheory != null) 'grammar_theory': grammarTheory!.toJson(),
      'theory_viewed': theoryViewed,
    };
  }
}

/// Exercise Types
enum ExerciseType {
  multipleChoice,
  trueFalse,
  fillInBlank,
  translate,
  matching,
  reorder,
  listening,
  speaking,
}

/// Exercise Entity
/// Represents an individual exercise within a lesson
class Exercise {
  final String id;
  final ExerciseType type;
  final String? uiType;
  final String? phase;
  final String question;
  final List<String>? options; // For multiple choice
  final String correctAnswer;
  final String? explanation;
  final String? hint;
  final String? audioUrl; // For listening exercises
  final Map<String, dynamic>? metadata;

  Exercise({
    required this.id,
    required this.type,
    this.uiType,
    this.phase,
    required this.question,
    this.options,
    required this.correctAnswer,
    this.explanation,
    this.hint,
    this.audioUrl,
    this.metadata,
  });

  Exercise copyWith({
    String? id,
    ExerciseType? type,
    String? uiType,
    String? phase,
    String? question,
    List<String>? options,
    String? correctAnswer,
    String? explanation,
    String? hint,
    String? audioUrl,
    Map<String, dynamic>? metadata,
  }) {
    return Exercise(
      id: id ?? this.id,
      type: type ?? this.type,
      uiType: uiType ?? this.uiType,
      phase: phase ?? this.phase,
      question: question ?? this.question,
      options: options ?? this.options,
      correctAnswer: correctAnswer ?? this.correctAnswer,
      explanation: explanation ?? this.explanation,
      hint: hint ?? this.hint,
      audioUrl: audioUrl ?? this.audioUrl,
      metadata: metadata ?? this.metadata,
    );
  }

  factory Exercise.fromJson(Map<String, dynamic> json) {
    return Exercise(
      id: json['id'] as String,
      type: _parseExerciseType(json['type'] as String),
      uiType: json['ui_type'] as String?,
      phase: json['phase'] as String?,
      question: json['question'] as String,
      options: (json['options'] as List?)?.map((e) => e as String).toList(),
      correctAnswer: json['correct_answer']?.toString() ?? '',
      explanation: json['explanation'] as String?,
      hint: json['hint'] as String?,
      audioUrl: json['audio_url'] as String?,
      metadata: json['metadata'] as Map<String, dynamic>?,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'type': type.name,
      'ui_type': uiType,
      'phase': phase,
      'question': question,
      'options': options,
      'correct_answer': correctAnswer,
      'explanation': explanation,
      'hint': hint,
      'audio_url': audioUrl,
      'metadata': metadata,
    };
  }

  static ExerciseType _parseExerciseType(String type) {
    switch (type.toLowerCase()) {
      case 'multiple_choice':
      case 'multiplechoice':
        return ExerciseType.multipleChoice;
      case 'true_false':
      case 'truefalse':
        return ExerciseType.trueFalse;
      case 'fill_in_blank':
      case 'fillinblank':
        return ExerciseType.fillInBlank;
      case 'translate':
      case 'translation':
        return ExerciseType.translate;
      case 'matching':
        return ExerciseType.matching;
      case 'reorder':
        return ExerciseType.reorder;
      case 'listening':
        return ExerciseType.listening;
      case 'speaking':
        return ExerciseType.speaking;
      default:
        return ExerciseType.multipleChoice;
    }
  }
}
