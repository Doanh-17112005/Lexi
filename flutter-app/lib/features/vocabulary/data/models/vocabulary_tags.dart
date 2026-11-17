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
  const aliases = <String, String>{'daily_life': 'daily'};
  final normalized = <String>[];

  void addTag(String rawTag) {
    final lowered = rawTag.trim().toLowerCase();
    final tag = aliases[lowered] ?? lowered;
    if (tag.isNotEmpty && !normalized.contains(tag)) {
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
