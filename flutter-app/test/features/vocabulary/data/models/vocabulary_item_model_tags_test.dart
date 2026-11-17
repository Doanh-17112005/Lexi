import 'package:flutter_test/flutter_test.dart';
import 'package:lexilingo_app/features/vocabulary/data/models/vocabulary_item_model.dart';

Map<String, dynamic> _itemJson(Object? tags) => {
  'id': '7f313ad4-2e6e-43f4-8231-27089da4cb64',
  'word': 'discover',
  'definition': 'to find something for the first time',
  'translation': {'vi': 'khám phá'},
  'pronunciation': '/dɪˈskʌvər/',
  'audio_url': null,
  'part_of_speech': 'verb',
  'difficulty_level': 'A2',
  'course_id': null,
  'lesson_id': null,
  'tags': tags,
  'usage_frequency': 10,
  'created_at': '2026-06-06T00:00:00Z',
};

void main() {
  group('VocabularyItemModel tags contract', () {
    test('normalizes null to an empty list', () {
      final item = VocabularyItemModel.fromJson(_itemJson(null));

      expect(item.tags, isEmpty);
    });

    test('normalizes and de-duplicates list tags', () {
      final item = VocabularyItemModel.fromJson(
        _itemJson([' Travel ', 'daily_life', 'travel']),
      );

      expect(item.tags, ['travel', 'daily']);
    });

    test('reads source, topic and QA metadata from legacy objects', () {
      final item = VocabularyItemModel.fromJson(
        _itemJson({
          'source': 'AI_GENERATED',
          'source_reference': null,
          'qa_status': 'NEEDS_REVIEW',
          'topic': ['daily_life', 'Travel'],
        }),
      );

      expect(item.tags, ['ai_generated', 'daily', 'travel', 'needs_review']);
    });
  });
}
