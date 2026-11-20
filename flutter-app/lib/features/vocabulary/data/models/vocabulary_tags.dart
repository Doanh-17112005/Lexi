/// Canonical system vocabulary topics matching backend `CANONICAL_TOPICS`
/// and the Vocabulary Library topic cards.
const List<String> canonicalSystemTopics = <String>[
  'general',
  'travel',
  'business',
  'daily',
  'science',
  'technology',
];

const Map<String, String> _vocabularyTopicAliases = <String, String>{
  'daily_life': 'daily',
  'daily-life': 'daily',
  'daily life': 'daily',
};

/// Normalize a single topic/tag string using the canonical backend taxonomy.
String? normalizeVocabularyTopic(String? rawTag) {
  if (rawTag == null) return null;
  final lowered = rawTag.trim().toLowerCase();
  if (lowered.isEmpty) return null;
  return _vocabularyTopicAliases[lowered] ?? lowered;
}

/// Normalize stored/API vocabulary tag shapes to the public `List<String>`
/// contract. Object support is kept for cached and legacy API payloads.
List<String> normalizeVocabularyTags(Object? rawTags) {
  const metadataKeys = <String>[
    'source',
    'topic',
    'tags',
    'anki_tags',
    'source_reference',
    'qa_status',
  ];
  final normalized = <String>[];

  void addTag(String rawTag) {
    final tag = normalizeVocabularyTopic(rawTag);
    if (tag != null && !normalized.contains(tag)) {
      normalized.add(tag);
    }
  }

  void collect(Object? value) {
    if (value is String) {
      addTag(value);
      return;
    }
    if (value is Map) {
      for (final key in metadataKeys) {
        if (value.containsKey(key)) collect(value[key]);
      }
      for (final entry in value.entries) {
        if (metadataKeys.contains(entry.key) ||
            entry.value == null ||
            entry.value == false) {
          continue;
        }
        if (entry.value == true) {
          addTag(entry.key.toString());
        } else {
          collect(entry.value);
        }
      }
      return;
    }
    if (value is Iterable) {
      for (final item in value) {
        collect(item);
      }
    }
  }

  collect(rawTags);
  return normalized;
}

/// Publication state matching backend `content_publication_policy.py`.
enum ContentPublicationStatus { published, draft, quarantined }

const Set<String> _draftVocabularyTokens = <String>{
  'needs_review',
  'draft',
  'qa_status:needs_review',
  'qa_status:draft',
};

const Set<String> _quarantinedVocabularyTokens = <String>{
  'conflict',
  'blocked',
  'audit_status:conflict',
  'audit_status:blocked',
};

/// Classify vocabulary payload tags into `published`, `draft`, or `quarantined`.
ContentPublicationStatus classifyVocabularyPublication(Object? rawTags) {
  if (rawTags is Map) {
    final auditStatus =
        rawTags['audit_status']?.toString().trim().toUpperCase() ?? '';
    final qaStatus =
        rawTags['qa_status']?.toString().trim().toUpperCase() ?? '';
    final isPublished = rawTags['is_published'];

    if (auditStatus == 'CONFLICT' ||
        auditStatus == 'BLOCKED' ||
        qaStatus == 'CONFLICT' ||
        qaStatus == 'BLOCKED') {
      return ContentPublicationStatus.quarantined;
    }
    if (isPublished == false ||
        qaStatus == 'NEEDS_REVIEW' ||
        qaStatus == 'DRAFT') {
      return ContentPublicationStatus.draft;
    }
  }

  final tokens = normalizeVocabularyTags(rawTags);
  if (tokens.any(_quarantinedVocabularyTokens.contains)) {
    return ContentPublicationStatus.quarantined;
  }
  if (tokens.any(_draftVocabularyTokens.contains)) {
    return ContentPublicationStatus.draft;
  }
  return ContentPublicationStatus.published;
}

/// Whether a vocabulary item may be shown in Learner discovery views.
bool isVocabularyPublishedForLearner(Object? rawTags) {
  return classifyVocabularyPublication(rawTags) ==
      ContentPublicationStatus.published;
}
