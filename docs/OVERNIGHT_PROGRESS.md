# LexiLingo Overnight Autonomous Engineering Progress

- **Checkpoint Time**: 2026-11-18 08:47 (+07)
- **Current Task / Session Status**: Phase D Stabilization (Workstream A + B) & Workstream C (T02 PASS; T03 code fixes, CEFR topic mapping & unit/CRUD/widget tests PASS; live DB seed/tag backfill BLOCKED pending user approval)

## Passed Tasks
- **A1 — Regression Test (`test_endpoint_degrades_instead_of_failing`)**: **PASS**
  - Root cause: `tests/conftest.py` `async_client` used `ASGITransport(app=app)` without running FastAPI lifespan (`RedisClient.connect()`), while `TokenBlacklist` intentionally fails closed (`503`).
  - Fix: Added `_InMemoryAsyncRedis` to `async_client` in `backend-service/tests/conftest.py` (restoring prior state in `finally`, preserving explicit Redis-down `503` tests). Verified pre-existing changes in `backend-service/app/routes/courses.py` and `backend-service/app/schemas/course.py`.
- **A3 — Course Progress Consistency**: **PASS**
  - Fixed `backend-service/app/routes/course_categories.py` (`GET /categories/{id}/courses` now includes `user_progress`), `flutter-app/lib/features/course/presentation/providers/course_provider.dart` (sync `_enrolledCourses`), `flutter-app/lib/features/course/presentation/screens/course_detail_screen.dart` (refresh `HomeProvider.loadEnrolledCourses()` on completion), and added route regression test in `backend-service/tests/test_courses_routes.py`.
  - Verified consistent `100%` progress across Home, Course Listing, Course Detail, and Category Courses before and after reload.
- **A4 — Flashcard Persistence**: **PASS** (`SRS review: NOT_TESTED` because `due_for_review = 0`)
  - Fixed `flutter-app/lib/features/vocabulary/presentation/pages/vocab_library_page.dart` (`initState` refresh) and `flutter-app/lib/features/vocabulary/presentation/providers/vocab_provider.dart` (coalesce concurrent `loadWords`, parse `example` in `_fetchBackendCollection`).
  - Chrome + API + PostgreSQL verified `quick-save` persistence across full browser reload.
- **Workstream B — Chrome E2E Smoke Test**: **PASS**
  - Verified Auth, Dashboard, Courses, Lessons/Exercises, Games, Vocabulary, XP/Progress, Profile on `http://127.0.0.1:5174` (`0` console errors, `0` HTTP `>= 400`).
- **T02 — Vocabulary Catalog Pagination**: **PASS**
  - Backend: `backend-service/app/crud/vocabulary.py` and `backend-service/app/routes/vocabulary.py` support deterministic alphabetical `offset` pagination, active filter forwarding (`difficulty_level`, `tag`, `course_id`, `lesson_id`, `search`), accurate `has_more`, and `"na"` / `"na yet"` placeholder filtering; added 3 multi-page DB tests in `backend-service/tests/test_vocabulary_routes.py`.
  - Flutter: `vocab_provider.dart` and `vocab_library_page.dart` replaced hardcoded `limit=100` with `catalogPageSize = 30`, infinite scroll + `loadMoreWords()` + Retry/loading footer, server-side filters, `_loadEpoch` staleness guard, debounced search, and multi-page `_fetchBackendCollection()`; added `vocab_provider_pagination_test.dart`.
  - Live Chrome E2E verified `16 từ`, CEFR `B1` (`2 từ`), search `lucid` (`1 từ`), post-reload `16 từ`, `0` console errors, `0` HTTP `>= 400`.
- **T03 — Topic Taxonomy (Code, Seed Mapping & Tests)**: **PASS (Live DB Seed BLOCKED)**
  - Fixed in code: exported `CANONICAL_TOPICS` & expanded `TOPIC_ALIASES` (`daily_life`, `daily-life`, `daily life` -> `daily`) in `backend-service/app/services/vocabulary_catalog_policy.py`; fixed lowercase/invalid `difficulty_level` HTTP `500` PostgreSQL enum crash (normalizes `.strip().upper()` and returns HTTP `422` `HTTP_422_UNPROCESSABLE_CONTENT` on unknown level) and canonicalized `tag` before Redis cache keys in `routes/vocabulary.py` & `crud/vocabulary.py`; exported `canonicalSystemTopics` + `normalizeVocabularyTopic` in `vocabulary_tags.dart` and wired across `VocabProvider`, `FlashcardProvider`, and `QuizProvider`.
  - Prepared catalog seed code (NOT executed): added canonical topics to all 180 `CEFR_VOCABULARY` entries (`daily: 31`, `business: 39`, `general: 47`, `science: 25`, `travel: 20`, `technology: 18`), `build_cefr_seed_tags()`, and validation rules in `backend-service/app/core/cefr_vocabulary_data.py`, and updated `backend-service/seed_and_test_cefr_a1_c2.py`.
  - Added tests across `test_vocabulary_routes.py`, `test_cefr_vocabulary_seed.py`, `test_vocabulary_crud_quality.py`, `vocabulary_item_model_tags_test.dart`, `vocab_provider_topic_taxonomy_test.dart`, and widget test `vocab_library_topic_cards_test.dart`.

## FAIL / BLOCKED / NOT_TESTED
- **A2 — Achievements (`0/46`)**: **PARTIAL / BLOCKED (Data Seed)**
  - Fixed missing `await db.commit()` + cache invalidation in `backend-service/app/routes/gamification.py`, `progress.py`, `challenges.py`; aligned `condition_type`s in `backend-service/app/core/sample_data_catalog.py`; added regression tests in `backend-service/tests/test_achievement_system.py`.
  - Blocker: Live PostgreSQL `achievements` table has `0` rows (`user_achievements = 0`); running `scripts.backfill_achievements` requires user approval.
- **A4 — SRS Due Review**: **NOT_TESTED** (`due_for_review = 0` on active learner account; persistence verified via `quick-save`).
- **A5 — AI Chat Diagnostics**: **BLOCKED (Provider Config)**
  - Checked `ai-service/.env`, OS env, and local Ollama (`:11434`): `GEMINI_API_KEY` and `GROQ_API_KEY` empty, `GROQ_API_KEYS` unset, `OLLAMA_ENABLED=false`, `USE_OLLAMA=false`, port `11434` closed. Live `POST /api/v1/lexi/chat` returns `safe_tutor_fallback`.
- **T03 — Live DB Seed & Topic Tag Backfill**: **BLOCKED (User Approval Required)**
  - Live PostgreSQL `vocabulary_items` has `15` rows with `0` non-null JSON tag payloads (`tags::text = 'null'`). Executing `seed_and_test_cefr_a1_c2.py` or DB backfill requires user approval.

## Modified & New Files (Uncommitted Working Tree)
- **Modified (41 files total, including 18 prior checkpoint files retained intact)**:
  - Backend:
    - `backend-service/app/core/cefr_vocabulary_data.py`
    - `backend-service/app/core/sample_data_catalog.py`
    - `backend-service/app/crud/course.py`
    - `backend-service/app/crud/progress.py`
    - `backend-service/app/crud/vocabulary.py`
    - `backend-service/app/routes/challenges.py`
    - `backend-service/app/routes/course_categories.py`
    - `backend-service/app/routes/courses.py`
    - `backend-service/app/routes/gamification.py`
    - `backend-service/app/routes/learning.py`
    - `backend-service/app/routes/progress.py`
    - `backend-service/app/routes/vocabulary.py`
    - `backend-service/app/schemas/course.py`
    - `backend-service/app/services/recommendation_service.py`
    - `backend-service/app/services/streak_service.py`
    - `backend-service/app/services/vocabulary_catalog_policy.py`
    - `backend-service/seed_and_test_cefr_a1_c2.py`
    - `backend-service/tests/conftest.py`
    - `backend-service/tests/services/test_recommendation_service.py`
    - `backend-service/tests/test_achievement_system.py`
    - `backend-service/tests/test_cefr_vocabulary_seed.py`
    - `backend-service/tests/test_courses_routes.py`
    - `backend-service/tests/test_streak_service.py`
    - `backend-service/tests/test_vocabulary_crud_quality.py`
    - `backend-service/tests/test_vocabulary_routes.py`
  - Flutter:
    - `flutter-app/lib/features/auth/presentation/pages/login_page.dart`
    - `flutter-app/lib/features/auth/presentation/pages/register_page.dart`
    - `flutter-app/lib/features/course/presentation/providers/course_provider.dart`
    - `flutter-app/lib/features/course/presentation/screens/course_detail_screen.dart`
    - `flutter-app/lib/features/games/presentation/screens/games_hub_screen.dart`
    - `flutter-app/lib/features/learning/presentation/providers/learning_provider.dart`
    - `flutter-app/lib/features/learning/presentation/screens/learning_session_screen.dart`
    - `flutter-app/lib/features/user/presentation/pages/settings_page.dart`
    - `flutter-app/lib/features/vocabulary/data/models/vocabulary_tags.dart`
    - `flutter-app/lib/features/vocabulary/presentation/pages/vocab_library_page.dart`
    - `flutter-app/lib/features/vocabulary/presentation/providers/flashcard_provider.dart`
    - `flutter-app/lib/features/vocabulary/presentation/providers/quiz_provider.dart`
    - `flutter-app/lib/features/vocabulary/presentation/providers/vocab_provider.dart`
    - `flutter-app/lib/features/vocabulary/presentation/screens/flashcard_review_screen.dart`
    - `flutter-app/lib/main.dart`
    - `flutter-app/test/features/vocabulary/data/models/vocabulary_item_model_tags_test.dart`
- **Untracked / New Files (5)**:
  - `docs/OVERNIGHT_PROGRESS.md`
  - `docs/T03_TOPIC_TAXONOMY_PLAN.md`
  - `flutter-app/test/features/vocabulary/presentation/pages/vocab_library_topic_cards_test.dart`
  - `flutter-app/test/features/vocabulary/presentation/providers/vocab_provider_pagination_test.dart`
  - `flutter-app/test/features/vocabulary/presentation/providers/vocab_provider_topic_taxonomy_test.dart`

## Tests Run & Results (After Final Edits)
- **Backend targeted pytest (17 files)**: **374 passed in 24.77s** (`0` failures, `0` warnings).
  - Files: `test_courses_routes.py`, `test_streak_service.py`, `tests/services/test_recommendation_service.py`, `test_learning_routes.py`, `test_progress_routes.py`, `test_gamification_routes.py`, `test_achievement_system.py`, `test_vocabulary_routes.py`, `test_vocabulary_catalog_policy.py`, `test_vocabulary_crud_quality.py`, `test_vocabulary_catalog.py`, `test_vocabulary_catalog_normalize.py`, `test_cefr_vocabulary_seed.py`, `test_challenges_routes.py`, `test_token_blacklist.py`, `test_rate_limit_fail_closed.py`, `test_security_hardening.py`.
- **Flutter vocabulary unit & widget tests (8 files)**: **21 passed** (`+21: All tests passed!`).
  - Files: `vocabulary_item_model_tags_test.dart`, `vocabulary_remote_datasource_test.dart`, `vocab_provider_quick_save_test.dart`, `vocab_provider_pagination_test.dart`, `vocab_provider_topic_taxonomy_test.dart`, `vocab_library_topic_cards_test.dart`, `flashcard_provider_test.dart`, `quiz_provider_test.dart`.
- **Flutter analyze (`lib/features/vocabulary lib/features/course`)**: **No issues found!** (`ran in 156.3s`).
- **Live endpoints check**:
  - `http://127.0.0.1:5174` -> HTTP `200`
  - `http://127.0.0.1:8000/health` -> HTTP `200`
  - `http://127.0.0.1:8001/health` -> HTTP `200`
  - `GET /api/v1/vocabulary/items?difficulty_level=b1` -> HTTP `200` (`2` items)
  - `GET /api/v1/vocabulary/items?difficulty_level=invalid` -> HTTP `422`

## Unresolved Blockers (Requiring User Intervention)
1. **A2 Achievements Seed**: Run approved achievement seed (`scripts.backfill_achievements`) on `lexilingo`.
2. **A5 LLM Provider Config**: Configure valid `GROQ_API_KEY` / `GEMINI_API_KEY` in `ai-service/.env` or enable local Ollama (`:11434`).
3. **T03 Vocabulary Seed / Backfill**: Review and approve running the updated seed/tag backfill (`seed_and_test_cefr_a1_c2.py`) + clearing `vocab_items:*` Redis cache keys.

## Next Steps (Recommended Phase E Order)
1. Run user-approved seeds (`backfill_achievements`, `seed_and_test_cefr_a1_c2.py`) and configure an LLM provider in `ai-service/.env`.
2. Re-test Chrome E2E for Achievements unlock, 6 live system topic cards, AI Chat live response, and **T04** SRS flashcard + quiz review flow with due cards.
3. Proceed cleanly to **T05–T06 (Dashboard)** and **T07–T09 (Roadmap Gate)**.
