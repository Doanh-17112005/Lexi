# T03 — Topic Taxonomy Audit & Remediation Plan

- **Audit Date**: 2026-11-18
- **Status**: Code-level normalization, catalog topic mapping & regression tests **COMPLETED**; Live DB seed / bulk tag assignment **BLOCKED (Requires User Approval — No DB Writes/Seeds Performed)**

## 1. Existing Model & API Contract Audit

1. **Canonical Topic Taxonomy (`backend-service/app/services/vocabulary_catalog_policy.py` & `flutter-app/lib/features/vocabulary/presentation/pages/vocab_library_page.dart`)**:
   - Six system topics are defined consistently on both sides:
     - `general`, `travel`, `business`, `daily`, `science`, `technology`.
   - Backend `VocabularyItem.tags` (`PortableJSON`) stores either legacy dicts (`{"source": ..., "topic": ...}`) or canonical lists (`["travel"]`), while `VocabularyItemResponse.tags` outputs `List[str]` via `normalize_all_tags(...)`.
   - `GET /api/v1/vocabulary/items` accepts `difficulty_level`, `tag`, `search`, `course_id`, `lesson_id`, `limit`, `offset`.

2. **Verified Code Bugs & Catalog Code Fixed (No Schema/DB Mutation)**:
   - **Lowercase/Invalid `difficulty_level` HTTP 500**: Calling `GET /api/v1/vocabulary/items?difficulty_level=b1` raised a PostgreSQL `DBAPIError` (`invalid input value for enum difficulty_level_enum: "b1"` -> HTTP 500). Fixed by normalizing `difficulty_level` (`strip().upper()`) and returning HTTP `422` (`HTTP_422_UNPROCESSABLE_CONTENT`) for unknown levels in `backend-service/app/routes/vocabulary.py`, plus defensive enum checks in `backend-service/app/crud/vocabulary.py`.
   - **Topic Alias & Cache Normalization**: Exported `CANONICAL_TOPICS` and expanded `TOPIC_ALIASES` (`daily_life`, `daily-life`, `daily life` -> `daily`) in `backend-service/app/services/vocabulary_catalog_policy.py`, exported `canonicalSystemTopics` + `normalizeVocabularyTopic` in `flutter-app/lib/features/vocabulary/data/models/vocabulary_tags.dart`, and canonicalized `tag` before Redis cache key construction in `routes/vocabulary.py`.
   - **Flutter Provider Consistency**: Updated `VocabProvider`, `FlashcardProvider`, and `QuizProvider` to apply `normalizeVocabularyTopic` and `normalizeVocabularyTags` consistently across `setTagFilter`, `setLevelFilter`, `availableTags`, `filteredWords`, `_mergeWord`, and `startTopicSession`.
   - **Published CEFR Catalog Topic Assignment (`backend-service/app/core/cefr_vocabulary_data.py` & `backend-service/seed_and_test_cefr_a1_c2.py`)**:
     - Added `CANONICAL_TOPICS`, per-word `_WORD_TOPICS` coverage across all 180 `CEFR_VOCABULARY` entries (`daily: 31`, `business: 39`, `general: 47`, `science: 25`, `travel: 20`, `technology: 18`), `build_cefr_seed_tags()`, and topic validation inside `validate_cefr_vocabulary()`.
     - Updated `seed_and_test_cefr_a1_c2.py` to persist `build_cefr_seed_tags()` and idempotently backfill missing topics on existing rows **without** running the seed script.
   - **Regression Tests Added**:
     - Backend: `tests/test_cefr_vocabulary_seed.py`, `tests/test_vocabulary_crud_quality.py`, `tests/test_vocabulary_routes.py`.
     - Flutter: `vocabulary_item_model_tags_test.dart`, `vocab_provider_topic_taxonomy_test.dart`, and widget test `vocab_library_topic_cards_test.dart` covering all 6 topic filter chips + system topic cards + Quiz session launch.

3. **Verified Live Database Gap (Why Live System Topic Cards Return Empty)**:
   - Live PostgreSQL `lexilingo.vocabulary_items` currently contains **15 rows**, and **15/15 have `tags = null`** (`0` items mapped to `general`, `travel`, `business`, `daily`, `science`, or `technology`).

## 2. User-Approved Execution Steps (Pending Approval)

1. Run the prepared CEFR seed/backfill script against `lexilingo` (e.g., `seed_and_test_cefr_a1_c2.py` + `scripts/tag_basic_words.py` or equivalent curated backfill) to populate all 180 CEFR entries and their canonical topic tags without overwriting curated user data.
2. Clear `vocab_items:*` Redis cache keys so `/api/v1/vocabulary/items?tag=<topic>` serves updated topic tags immediately.
3. Verify in Chrome that Tab 1 renders topic filter chips and all 6 system topic cards in Tab 2 launch study sessions cleanly with real DB data.
