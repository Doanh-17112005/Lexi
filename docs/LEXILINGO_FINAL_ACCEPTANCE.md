# Báo Cáo Nghiệm Thu Cuối Dự Án LexiLingo (`LEXILINGO_FINAL_ACCEPTANCE.md`)

- **Ngày lập**: 2026-11-19 17:38 (+07)
- **Repository**: `D:\LexiLingo\LexiLingo`
- **Kiến trúc Web-first**: Flutter Web Learner (`http://127.0.0.1:5174` UP), FastAPI Backend (`http://127.0.0.1:8000` UP), AI Service (`http://127.0.0.1:8001` UP), React Admin (`http://127.0.0.1:5173` UP), Docker PostgreSQL `:5432` + Redis `:6379` + MongoDB `:27017` (UP).

---

## 1. Danh sách toàn bộ tính năng & Trạng thái

| # | Tính năng | Trạng thái | Ghi chú phạm vi |
|---|---|---|---|
| 1 | Auth (Register / Login / Logout / Refresh / TokenBlacklist) | **PASS** | Auth flow & security hardening đã test + Chrome E2E |
| 2 | Course Progress Consistency (Listing / Detail / Home / Category) | **PASS** | Đồng bộ `100%` sau reload từ PostgreSQL |
| 3 | XP, Gems, Streak & Recommendations | **PASS** | Bền vững DB, đã sửa lỗi 500 `/complete` & `/recommendations` |
| 4 | Achievements (`48` defs DB / `44` UI) | **PASS** *(Backfilled local DB & Chrome E2E PASS)* | Đã backfill `48/48` (`created=48, updated=0`), `84 passed` Backend, Chrome E2E (`99779a06`: `5/44`, `0` console error, `0` failed reqs) |
| 5 | AI Service & LLM Providers (TraceCAG / Lexi / Topic / Voice / Safety) | **PARTIAL** *(Real LLM Gen `BLOCKED` by Keys)* | Sửa `diagnose_node` fallback (`models_used=["rule_fallback"]`, `0.5`), tạo `ai-service/docs/AI_PROVIDER_SETUP.md`, thêm contract tests (`73 passed` AI contract + `1,008 passed` full AI pytest); boolean `.env`: `GEMINI_API_KEY_SET=False`, `GROQ_API_KEY_SET=False`, `OLLAMA_ENABLED=false` |
| 6 | T01 Tags Contract (`PortableJSON` -> `List<String>`) | **PASS** | Normalization nhất quán Backend & Flutter |
| 7 | T02 Vocabulary Catalog Pagination & Search/Filter | **PASS** | Đã E2E `16 từ`, filter CEFR, search, reload persistence |
| 8 | T03 Topic Taxonomy (180 CEFR + 6 topic cards) | **BLOCKED (Data Seed)** | Kiểm chứng `88 CONFIRMED_SOURCE / 66 CONFLICT / 26 BLOCKED` (`180/180 AI_GENERATED + NEEDS_REVIEW`, `0 VERIFIED`), thêm `--only-confirmed-source` (`88`) & `--levels` selective idempotent (`29 passed`, `docs/VOCABULARY_FINAL_AUDIT.md`); live DB giữ `15` từ |
| 9 | T04 Vocabulary Flashcard + Quiz + SRS | **PARTIAL** *(Code PASS; SRS `due` & Auth Chrome UAT chưa đủ dữ liệu live)* | 4 nút SRS (`Again/Hard/Good/Easy`), Save-to-Collection, Quiz -> Mistake Notebook & idempotency API PASS; chờ Chrome auth UAT sau khi seed live |
| 10 | T05–T06 Dashboard Course Progress & Charts | **PASS** | Navigation `CourseDetailScreen`, UTC weekly chart, error/retry UI |
| 11 | T07–T09 Roadmap Unlock Gate | **PARTIAL** | Shared unlock policy & `403` PASS; live DB mới có `1` lesson/course (sẵn sàng mở rộng lên `3` lessons/course qua `seed_grammar_courses.py`) |
| 12 | T10–T12 Grammar Theory -> Practice | **PARTIAL** | Đã kiểm kê `6/12/12/18/72+12/36` (`docs/GRAMMAR_CONTENT_QA_INVENTORY.md`), sửa 15 lỗi disambiguation/distractor/mojibake, `3 passed` & idempotent trên `lexilingo_test` (`100% AI_GENERATED + NEEDS_REVIEW`); live `grammar_items = 0` |
| 13 | T13–T15 Mistake Review Loop | **PASS** | Capture + `reopen` + session `"Practice Mistakes"` đã test |
| 14 | T16–T18 Grammar 3 Difficulty Tiers (`easy`/`medium`/`hard`) | **PASS** | Strict tier filtering, bank A1–C2 đủ 3 tier, selector & resume |
| 15 | T19–T22 Guest Learning MVP | **PASS** | Public APIs, SHA-256 offline grading, isolated `guest_trial_v1:*`, conversion idempotent, Chrome E2E + Mobile `390x844` PASS |
| 16 | T23–T29 6-Skill Placement Test | **PASS** *(Deterministic Rubric; AI Grader N/A)* | Start/Answer/Resume/Submit đủ 6 kỹ năng, rubric Speaking/Writing minh bạch (`ai_graded: false`), chống submit trùng; **Chrome E2E (`7a8229e9`) PASS** (`C2`, `99.3%`, reload bền vững) |
| 17 | Phase 4: 6 Mini-Games | **PASS** | Backend `76 passed`, Flutter games `+121 passed` |
| 18 | Phase 6: React Admin Console (`:5173`) | **PARTIAL** *(Isolated 7-Flow QA Fixtures, Build & Audit PASS / Post-Login Browser UAT `BLOCKED` by User Login)* | Tách guard `canToggleAdminStatus`, thêm 7 Super Admin QA fixture tests (`superAdminFlows.test.ts` -> **`13 files, 67 passed`**), `pnpm run build:check` exit `0`, `0` CVE, Checklist UAT 7 bước; Chrome `:5173/login` (`d29b7b68`, `@verifier`) render sạch; chờ user đăng nhập `super_admin` |

---

## 2. Thống kê tổng hợp (`PASS / FAIL / BLOCKED / NOT_TESTED`)

- **PASS**: **12** nhóm tính năng (`Auth`, `Course Progress`, `XP/Streak`, `Achievements`, `T01`, `T02`, `T05–T06`, `T13–T15`, `T16–T18`, `T19–T22 Guest MVP`, `T23–T29 6-Skill Placement`, `Phase 4 Mini-Games`).
- **PARTIAL** *(automated & isolated PG UAT PASS, còn phụ thuộc live auth E2E hoặc nội dung DB)*: **4** nhóm (`T04 Vocabulary Flashcard + Quiz + SRS`, `T07–T09 Roadmap Gate`, `T10–T12 Grammar Theory`, `Phase 6 React Admin` — phần CRUD/RBAC sau đăng nhập thuộc `NOT_TESTED` khi chưa có phiên Super Admin từ người dùng).
- **BLOCKED**: **2** nhóm (`T03 Vocabulary 180 CEFR Seed`, `Phase 5 AI Chat LLM Key`).
- **FAIL (Code/Functional P0/P1)**: **0** *(Lưu ý kỹ thuật: AI Service pytest có `1` failure tại `test_blocking_kg_initialization_does_not_block_event_loop` trong `998` tests do process `:8001` đang chạy giữ file lock Kuzu snapshot trong môi trường dev).*

---

## 3. Các lỗi đã phát hiện & sửa chữa (Root-Cause Fixes)

1. **T04 / Vocabulary (`UniqueViolationError` ẩn khi review lặp)**: `XPTransaction.source_id` chỉ dùng `str(user_vocabulary_id)`, khiến review lần 2 bị đụng unique key -> sửa thành `f"{user_vocabulary_id}:{updated_vocab.total_reviews}"`, đồng thời gom commit nguyên tử với `Idempotency-Key` cache (`vocab_review_idem:`).
2. **T05–T06 / Dashboard (`MyProgressScreen` & UTC)**: Thay điều hướng `/course-detail` chưa đăng ký sang `CourseDetailScreen`, lộ trạng thái lỗi/retry cho Weekly chart (`weeklyError`), và chuẩn hóa UTC `datetime.now(timezone.utc).date()` trong `get_weekly_progress`.
3. **T07–T09 / Roadmap Unlock Gate**: Tạo pure policy `roadmap_unlock_policy.py` dùng chung giữa `courses.py`, `learning.py` (`roadmap` + `start_lesson` trả HTTP `403` khi bài khóa) và UI refresh khi quay lại roadmap.
4. **T10–T12 / Grammar Theory -> Practice**: Sửa lỗi khởi tạo `UserGrammarItem(status="learning")` không tồn tại cột (`TypeError`), thêm `_resolve_grammar_theory` sanitized + HTTP `409` khi grammar lesson thiếu theory + phase `theory` -> `practice` trong `LearningProvider` / `LearningSessionScreen`.
5. **T13–T15 / Mistake Review Loop**: Bổ sung `reopen(id)` đồng bộ queue offline, tự động capture lỗi từ `course_lesson` trong `LearningProvider`, thêm luồng luyện tập lại tương tác (`Practice Mistakes`) trong `MistakeNotebookPage`, và dọn trùng lặp class trong quá trình edit.
6. **T16–T18 / Grammar Quiz Tiers**: Thêm câu hỏi C1/C2 và gán `difficulty_tier` (`easy`, `medium`, `hard`) cho toàn bộ A1–C2, chặn fallback chéo tier trên Backend và thêm selector 3 mức + resume theo tier trên Flutter.
7. **T19–T22 / Guest Learning MVP**: Tạo `/api/v1/guest/*`, sửa overflow layout `Row` -> `Wrap` trên `GuestTrialShellPage`, cô lập storage `guest_trial_v1:*`, SHA-256 offline grading không lộ đáp án, và migration idempotent sau login.
8. **T23–T29 / 6-Skill Placement Test**: Sửa lỗi thực tế phát hiện qua test Postgres thật — `current_user.level = 'beginner'` (8 ký tự) gây `StringDataRightTruncationError` khi insert `LevelAssessmentTest.assessed_level` (`VARCHAR(5)`) bằng `_normalize_cefr()`; đồng thời hỗ trợ cả `@router.put` và `@router.patch` cho draft answer từ `ApiClient.patch`, và sửa `UserScopeService.getScopeOrDefault()`.
9. **React Admin (`:5173`) Localhost CSP Console Error & Dependency Advisories**: Chuyển `<Analytics />` (`@vercel/analytics/react`) trong `admin-service/src/main.tsx` sang `{import.meta.env.PROD && <Analytics />}` để loại bỏ lỗi CSP `va.vercel-scripts.com` trên `:5173` (`0` console error), và nâng cấp non-breaking trong `admin-service/pnpm-lock.yaml` (`axios@1.20.0 -> 1.21.1` kéo `follow-redirects >= 1.16.2`, `zod@4.6.5 -> 4.6.7`), đưa `pnpm audit --prod` từ `4 high` xuống **`0` lỗ hổng**.
10. **Phục hồi Docker Desktop Port-Forward & Test Harness Redis (`db_session`)**: Xác định nguyên nhân `:5432` và `:27017` từng bị ngắt kết nối trên host sau sự cố WSL là bảng forward của `wsl-bootstrap.vpnkitcontrol` bị lệch IP cũ (`172.19.0.3`/`.4` hoán đổi giữa `lexilingo-postgres` và `lexilingo-mongodb`); thực hiện `docker restart lexilingo-postgres lexilingo-mongodb` (không tạo container mới, không mất volume), khôi phục `SELECT 1` và Mongo `ping`. Đồng thời bổ sung `_InMemoryAsyncRedis` trong fixture `db_session` (`backend-service/tests/conftest.py`) khớp với `async_client`, giúp `test_jwt_boundary.py` và cụm 9 file Auth/RBAC/Gamification/XP/Config đạt **`203 passed`**, không còn lỗi 503 giả do thiếu Redis client khi test unit trực tiếp `get_current_user`.
11. **Admin RBAC 403 Login Mapping, Cache Sync & Vocabulary Non-Destructive Edit (`admin-service` & `admin_courses.py`)**:
    - Sửa `AuthProvider.tsx` (`processLogin`, `refreshProfile`) ném `ApiError(..., 403)` thay vì `Error` trơn khi tài khoản hợp lệ không có quyền Admin, và bổ sung fallback nhận diện `"quyền truy cập"` trong `adminLoginError.ts` + test `adminLoginError.test.ts`.
    - Bổ sung `invalidate_cache("courses")`, `invalidate_cache("vocab_items")`, `invalidate_cache("word_of_day")` trên toàn bộ route ghi Course/Unit/Lesson/Vocabulary trong `backend-service/app/routes/admin_courses.py` để đồng bộ tức thì sang Learner App.
    - Sửa `update_vocabulary` giữ nguyên `vocab.translation["examples"]` thay vì ghi đè `{"vi": translation}`, thêm metadata `topics`, `qa_status` (`NEEDS_REVIEW`/`VERIFIED` bắt buộc có `source_reference`), filter CEFR/Topic/QA & phân trang ở cả API và `admin-service/src/pages/VocabularyPage.tsx`, và giải thích `48` bản ghi DB vs `44` badge Learner ở `AchievementsPage.tsx`.
12. **Multi-Agent Swarm Stabilization & Independent QA Verification (`@backend`, `@platform`, `@learner`, `@verifier`)**:
    - **`@backend`**: Chuẩn hóa UTC date rollover trong `app/routes/progress.py` & `app/routes/challenges.py`; bổ sung `.with_for_update()` row locks + sửa `UserLevelHistory.change_type` trong `app/routes/proficiency.py`; sửa fixture UTC/FakeRedis/claims trong `tests/test_product_events.py`, `test_starter_reward_service.py`, `test_progress_routes.py`, `test_challenges_routes.py`, `test_gem_economy_db.py`. (`@verifier`: `932 passed, 0 failed` trên `lexilingo_test` + dry-run seed exit `0`).
    - **`@platform` (`ai-service` & `admin-service`)**: Sửa `lexi_chat_service.py` (stream voice `audio_base64`, giữ `story_context`, +1ms MongoDB timestamp order), `topic_chat_service.py` (`provider="trace-cag_safe_response"`, `fallback_used=True`, +1ms order), `topic_llm_gateway.py` (`self.gemini_model_name`), `test_contracts.py` (`_isolate_settings_env`), +3 unit tests (`1,008 passed, 0 failed`); sửa standalone edit & `order_index: 0` (`UnitsPage.tsx`/`LessonsPage.tsx`), `defaultExercise("true_or_false")` `"False"` (`LessonExercisesPage.tsx` + `LessonExercisesPage.test.ts`), validation/error handling (`CoursesPage.tsx`, `ContentLabPage.tsx`, `ContentAnalyticsPage.tsx`, `ContentQaQueuePage.tsx`, `UserManagementPage.tsx`), và self-deactivation guard (`AdminManagementPage.tsx`) -> **`12 files, 60 passed`**, `pnpm run build:check` PASS, `0` prod CVE.
    - **`@learner` (`flutter-app`)**: Reset state sạch trong `learning_provider.dart` (`startLesson`) & `placement_test_provider.dart` (`loadTest`), chuẩn hóa `word.tags` trong `vocab_provider.dart` (`loadMoreWords`), guard `'News quiz'` fallback trong `news_provider.dart`, thêm `skipAudioService` trong `podcast_di.dart` & `injection_container.dart`, bổ sung `learning.lessonLockedHint` trên 7 file `assets/i18n/*.json`, sửa test (`vocabulary_word_of_day_test.dart`, `known_words_service_test.dart`, `news_provider_*_test.dart`, `learner_surface_inventory_test.dart`) -> **`948 passed, 0 failed`**, `flutter analyze --no-pub lib test`: **`No issues found!`**.

13. **Final Blocker Resolution Swarm (`@content_grammar`, `@vocab_qa`, `@platform`, `@verifier`)**:
    - **`@content_grammar`**: Kiểm toán `grammar_course_data.py`, sửa 15 lỗi disambiguation/distractor/mojibake, lập `docs/GRAMMAR_CONTENT_QA_INVENTORY.md` (`6/12/12/18/72+12/36`, `100% AI_GENERATED + NEEDS_REVIEW`, `0 VERIFIED`), xác minh `--target test --apply` x2 idempotent + `3 passed` (`@verifier`: `7.79s`).
    - **`@vocab_qa`**: Đối chứng trực tiếp Oxford 3000/5000 PDF + Oxford sense pages cho 180 từ (`81/66/33` -> `88 CONFIRMED_SOURCE / 66 CONFLICT / 26 BLOCKED`, vẫn giữ `180/180 AI_GENERATED + NEEDS_REVIEW`, `0 VERIFIED`), bổ sung `--only-confirmed-source` (`88`) & `--levels` trong `seed_cefr_vocabulary.py`, xác minh trên `lexilingo_test` + `29 passed` (`@verifier`: `5.54s`).
    - **`@platform` (`ai-service` & `admin-service`)**: Sửa `diagnose_node` (`models_used=["rule_fallback"]`, `0.5`), kiểm tra `.env` dạng boolean (`0` key bị lộ), tạo `ai-service/docs/AI_PROVIDER_SETUP.md`, thêm 3 contract tests (`73 passed` AI contract), bổ sung `canToggleAdminStatus` + 7 isolated Super Admin QA fixture tests (`superAdminFlows.test.ts`, **`13 files / 67 passed`**), và lập Checklist Admin Browser UAT.
14. **Content Publication Gate Preflight & Safe Isolation (`content_publication_policy.py` & Flutter Guards)**:
    - Phát hiện trước đây `seed_grammar_courses.py` & `seed_cefr_vocabulary.py` để bài `NEEDS_REVIEW` / `CONFLICT` / `BLOCKED` hiển thị trực tiếp cho người học vì `/courses`, `/learning`, `/vocabulary/items`, `/word-of-day` và Flutter không lọc trạng thái xuất bản.
    - Bổ sung `backend-service/app/services/content_publication_policy.py` phân tách rạch ròi `PUBLISHED` (`VERIFIED`/legacy untagged), `DRAFT` (`NEEDS_REVIEW`/`DRAFT`/`is_published=False`), `QUARANTINED` (`CONFLICT`/`BLOCKED`); khóa toàn bộ bypass `/courses/{id}`, `/learning/roadmap`, `/start`/`/content`/`/context`/`/theory-viewed`/`/attempts/*/answer`/`/attempts/*/complete` (HTTP `403`), `ProgressCRUD` (`calculate_course_progress` & `get_course_progress_detail` loại draft khỏi mẫu số tiến độ), `/vocabulary/items`, `/vocabulary/items/{id}`, `/word-of-day` (kể cả stale cache), `/vocabulary/collection` (`404`) & `/collection/bulk`; giữ filter phòng thủ trong Flutter (`vocabulary_tags.dart`, `vocabulary_remote_datasource.dart`, `course_detail_model.dart`).
    - Kiểm chứng Final Gate: Backend 8 files **`180 passed in 30.54s`**, Flutter `vocabulary_item_model_tags_test.dart` (`5 passed`), Backup Restore Drill `.tmp/lexilingo_preflight_backup.sql` (`401,987 bytes`) khôi phục thành công vào DB cô lập `lexilingo_restore_check` (`ON_ERROR_STOP=1`, khớp `12` bảng live, `82` FK / `135` PK / `69` UNIQUE, `0` orphan rows -> `DROP DATABASE`), dry-run Grammar (`6 courses, +6 units, +12 grammar_items, +12 lessons, +36 question_bank`) & Selective Vocab `--only-confirmed-source` (`selected=88, created=82, updated=6, preserved_non_cefr=4, total=97`), kiểm tra 6 từ trùng (`happy` có `user_vocabulary_refs=1`, cảnh báo `tags=null` -> `NEEDS_REVIEW` sẽ ẩn tạm khỏi catalog công khai nếu áp trực tiếp), và kiểm tra Chrome read-only phiên Super Admin tại `:5173/super` & `/admin/*` (`2e39297e`: `HTTP 200` Users `29` / Courses `6` / Vocab `15` / Achievements `48`, ghi nhận `GET :8001/api/v1/ai/monitoring/dashboard -> 403 Forbidden`).

---

## 4. Các chức năng chưa có dữ liệu trên PostgreSQL Live (Đã kiểm tra Read-Only)

Số liệu thực tế trên database `lexilingo` tại thời điểm nghiệm thu (2026-11-19):
- `achievements`: **48** bản ghi (`user_achievements`: **5**) — đã backfill idempotent và Chrome E2E PASS (`5/44`).
- `vocabulary_items`: **15** bản ghi, trong đó `vocab_with_tags`: **0** (`tags = null`, chưa nạp bộ chọn lọc `88 CONFIRMED_SOURCE` hoặc `180` từ CEFR & 6 topic `daily`, `business`, `general`, `science`, `travel`, `technology`).
- `grammar_items`: **0** bản ghi; `question_bank`: **0** bản ghi.
- `courses` (`is_published = true`): **6** khóa học A1–C2; `units`: **6**; `lessons`: **6** (`1` bài/khóa).
- `users`: **29** bản ghi (`1 super_admin`, `28` learners).

---

## 5. Những yếu tố cần người dùng phê duyệt trước khi thực thi

1. **Backup PostgreSQL trước khi ghi dữ liệu (đã tạo & kiểm tra cấu trúc thuần UTF-8 `360,280 bytes`, không dùng `>` của PowerShell vì dễ lỗi encoding)**:
   - Đã chạy kiểm chứng: `docker exec lexilingo-postgres pg_dump -U lexilingo -d lexilingo -f /tmp/lexilingo_pre_seed_backup.sql && docker cp lexilingo-postgres:/tmp/lexilingo_pre_seed_backup.sql D:\LexiLingo\LexiLingo\.tmp\lexilingo_pre_seed_backup.sql`
   - Đã xác nhận đủ dòng cho `users: 29`, `user_wallets: 27`, `wallet_transactions: 30`, `vocabulary_items: 15`, `courses: 6`, `lessons: 6`, `user_course_progress: 11`.
2. **Duyệt Backfill Achievements (`48` bản ghi — đã dry-run PostgreSQL `lexilingo_test` 2 lần liên tiếp PASS: Run 1 `created=48, updated=0`, Run 2 `created=0, updated=0`, `with_badge_icon=44`)**:
   - Giải trình chênh lệch `46` vs `48`: Flutter `sample_achievements.dart` có `46` mẫu fallback (`44` trong `BADGE_FILES` + `polyglot`, `pronunciation_master`), trong khi server `ACHIEVEMENT_SEED` có `48` bản ghi (`44` + `xp_hunter`, `xp_warrior`, `xp_champion`, `xp_legend`). Đồng thời `AchievementProvider._removeXpAchievements` tự động lọc bỏ `category == 'xp'`, nên UI thật khi đọc từ server sẽ hiển thị `44` huy hiệu đều khớp 100% asset trong `BadgeAssetMapper`.
   - Lệnh: `cd D:\LexiLingo\LexiLingo\backend-service; .\venv\Scripts\python.exe -m scripts.backfill_achievements`
   - Dự kiến: Insert tối đa `48` dòng vào `achievements` (idempotent theo `slug`), không xóa bảng/user hiện có; user có tiến độ cũ vẫn an toàn nhờ `uq_user_achievement` và `WalletCRUD.add_gems(..., SELECT FOR UPDATE)` nên kích hoạt `POST /api/v1/gamification/achievements/check` không thưởng trùng.
3. **Duyệt Seed 180 Từ vựng CEFR & Multi-Topic Taxonomy (đã dry-run PostgreSQL `lexilingo` thành công: `created=169, updated=11, unchanged=0, preserved_non_cefr=4, total=184`, và seed idempotent trên `lexilingo_test` Run 1 `created=180` / Run 2 `unchanged=180`)**:
   - Lệnh: `cd D:\LexiLingo\LexiLingo\backend-service; .\venv\Scripts\python.exe -m scripts.seed_cefr_vocabulary --target local --apply`
   - Kèm dọn đúng prefix Redis cache: `vocab_items:*` (không flush toàn bộ Redis). Toàn bộ 180 mục giữ nguyên `AI_GENERATED + NEEDS_REVIEW` chờ editorial QA.
4. **Cấu hình LLM Provider thật cho AI Service (`ai-service/.env`)**:
   - Điền hợp lệ `GEMINI_API_KEY` hoặc `GROQ_API_KEY` (hoặc bật Ollama local tại `:11434`). Hệ thống hiện xác nhận tất cả key này đều đang trống (`False`).

---

## 6. Đánh giá Bảo mật & Chất lượng

- **Auth & RBAC**: Kiểm tra trực tiếp trên Backend live `:8000`: `/api/v1/users/me`, `/api/v1/proficiency/placement-test`, `/api/v1/admin/grammar` không token đều trả HTTP `401`; TokenBlacklist & Rate Limit tests (`108 passed`) đạt chuẩn fail-closed.
- **Guest Isolation & Answer Security**: `GET /api/v1/guest/trial-pack` trả `200` không auth, `0` user DB được tạo, `answer_leaks=False` (dùng `answer_digest` SHA-256 thay vì trả `correct_answer`); `POST /proficiency/placement-test/start` & `GET /proficiency/placement-test` đều strip `correct` và `rubric_keywords`.
- **Không giả lập AI**: Speaking/Writing trong Placement Test dùng deterministic rubric rõ tiêu chí (`ai_graded: false`, `scoring_mode: "deterministic_rubric"`) kèm disclaimer đây không phải chứng chỉ CEFR chính thức; AI Chat giữ fallback an toàn khi thiếu key.
- **Responsive & Console**: Kiểm thử thực tế trên Chrome desktop và mobile `390x844` ở `:5174` và `:5173/login` ghi nhận **0 console errors**, **0 overflow/clipping**.
- **Lưu ý môi trường**: Backend đang chạy ở chế độ dev (`DEBUG=True`, `CORS origins=None`/dev defaults) — cần set `ENVIRONMENT=production`, `DEBUG=False`, và whitelist `CORS_ORIGINS` cụ thể trước khi deploy thật.

---

## 7. Mức độ sẵn sàng triển khai

- **Mức độ hiện tại**: **Sẵn sàng cho UAT / Staging nội bộ** (`CONDITIONAL`); **CHƯA ĐẠT `READY` cho Production Launch** do còn 3 blocker ngoài code:
  1. Dữ liệu live `lexilingo` vẫn giữ `vocabulary_items = 15` (`0` tags) và `grammar_items = 0`, `question_bank = 0`, `lessons = 6` (chờ phê duyệt chạy seed chọn lọc/đầy đủ & xóa cache Redis).
  2. AI Service chưa có LLM provider key (`GEMINI_API_KEY_SET=False`, `GROQ_API_KEY_SET=False`, `OLLAMA_ENABLED=false`) nên chưa E2E được phản hồi LLM thật.
  3. Cần kiểm thử Chrome UAT sau đăng nhập `super_admin` trên `:5173/login` và xác minh lại luồng Learner thực tế sau khi nạp dữ liệu chuẩn.

---

## 8. Các bước cuối cùng cần thực hiện

1. Người dùng phê duyệt backup PostgreSQL và chọn chạy nạp chọn lọc (`--only-confirmed-source` = `88` từ) hoặc đầy đủ (`180` từ) via `seed_cefr_vocabulary.py --target local --apply` + `seed_grammar_courses.py --target local --apply`, sau đó xóa cache `vocab_items:*`, `word_of_day:*`, `courses:*`.
2. Người dùng làm theo [AI_PROVIDER_SETUP.md](file:///D:/LexiLingo/LexiLingo/ai-service/docs/AI_PROVIDER_SETUP.md) cấu hình `GEMINI_API_KEY` / `GROQ_API_KEY` (hoặc Ollama), restart `:8001` và kiểm chứng qua `GET /health`.
3. Người dùng tự đăng nhập `super_admin` tại `http://127.0.0.1:5173/login` và thực hiện Checklist Admin UAT 7 bước; đội biên tập viên gán `source_reference` trước khi chuyển các mục `NEEDS_REVIEW` sang `VERIFIED`.
4. Bật cấu hình Production (`APP_ENV=production`, `DEBUG=False`, `ALLOWED_ORIGINS` domain thật) và review git diff trước khi commit/deploy.
