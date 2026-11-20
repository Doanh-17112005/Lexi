# LexiLingo — Release Candidate Report (`LEXILINGO_RELEASE_CANDIDATE_REPORT.md`)

- **Ngày lập**: 2026-11-19 15:40 (+07)
- **Repository**: `D:\LexiLingo\LexiLingo`
- **Trạng thái phát hành đề xuất**: **`CONDITIONAL`** *(Hạ tầng Docker PG/Redis/Mongo và 4 dịch vụ `:8000`, `:8001`, `:5173`, `:5174` đang UP — HTTP 200; **Blocker Resolution Swarm QA (`@verifier`, `#18`) xác nhận PASS**: Grammar QA (`3 passed` + 15 disambiguations/fixes + `lexilingo_test` idempotent + `docs/GRAMMAR_CONTENT_QA_INVENTORY.md`), Vocabulary QA (`29 passed` + tái đối chứng nguồn nâng `81 -> 88 CONFIRMED_SOURCE` + `--only-confirmed-source` idempotent, giữ `180/180 AI_GENERATED + NEEDS_REVIEW`), AI Service (`73 passed` contract tests, `diagnose_node` `rule_fallback`, `AI_PROVIDER_SETUP.md` non-secret), React Admin (**`13 files / 67 passed`** với 7 Super Admin fixture flows + `build:check` + `0` CVE), và các bộ nền trước đó Backend `932 passed`, AI full `1,008 passed`, Flutter `948 passed`; **chưa đạt `READY`** vì còn blocker phê duyệt seed DB live, LLM key thật và UAT sau đăng nhập `super_admin`).*

---

## 1. Danh sách Module & Trạng thái

- **PASS (Code + Tests + Chrome/Integration Evidence)**:
  - `Auth (Register/Login/Logout/Refresh/TokenBlacklist)`
  - `Course Progress Consistency`
  - `XP, Gems, Streak & Recommendations`
  - `T01 Tags Contract`
  - `T02 Vocabulary Catalog Pagination`
  - `T04 Vocabulary Flashcard + Quiz + SRS` *(code/API/idempotency PASS; SRS live `due = 0`)*
  - `T05–T06 Dashboard Progress & Charts`
  - `T13–T15 Mistake Review Loop`
  - `T16–T18 Grammar 3 Difficulty Tiers`
  - `T19–T22 Guest Learning MVP` *(Chrome E2E desktop + mobile `390x844` PASS)*
  - `Phase 4: 6 Mini-Games` *(Backend `76 passed`, Flutter `+121 passed`)*
  - `Achievements (48 defs DB / 44 UI)` *(Đã backfill local DB `created=48, updated=0`; `84 passed`; Chrome E2E `99779a06` PASS `5/44`, `0` console error, `0` failed requests, `28` tài khoản khác không đổi)*
  - `T23–T29 6-Skill Placement Test` *(Chrome E2E `7a8229e9` PASS: 6 kỹ năng, `99.3%`, `C2`, rubric minh bạch `ai_graded: false`, chống submit trùng, reload bền vững, `0` console error)*
  - `Full E2E Backend Journey & Isolated Task 2/3 UAT` (`test_release_candidate_e2e_journey.py` + `test_isolated_vocab_topics_srs_and_grammar_uat.py`: `PASS` trên PostgreSQL `lexilingo_test`)
- **PARTIAL**:
  - `T07–T09 Roadmap Unlock Gate` (Isolated PG `PASS` + Flutter/Backend tests `PASS`; live DB mới có `1` lesson/course nên chưa bật trên dữ liệu thật)
  - `T10–T12 Grammar Theory -> Practice` (Isolated PG `PASS` + Backend/Flutter tests `PASS`; live DB giữ nguyên `grammar_items = 0`, `lessons` type `grammar = 0`)
  - `Phase 6: React Admin (:5173)` (`58` Vitest + `tsc -b && vite build` + `0` CVE prod PASS; Backend Admin RBAC/CRUD/Cache-Sync **`259 passed`** gồm `test_admin_rbac_crud_and_learner_sync.py`; Chrome `:5173/login` `0ee8891e` PASS `401` + `390x844` `0` overflow + `0` console error; RBAC/CRUD sau đăng nhập chờ người dùng tự đăng nhập Super Admin)
- **BLOCKED**:
  - `T03 Vocabulary 180 CEFR + 6 Topics` — `BLOCKED (Data Seed)`
  - `Phase 5: AI Chat & Streaming LLM` — `BLOCKED (Provider API Key / Ollama)`

---

## 2. Release Blocker Matrix

| Mức độ | Hạng mục | Trạng thái | Nguyên nhân gốc | File liên quan | Acceptance Criteria | Test cần chạy | Cần duyệt User |
|---|---|---|---|---|---|---|---|
| **P1** | Achievements Live DB (`48/48` DB / `44` UI) | **RESOLVED (PASS)** | Đã backfill `48` defs (`44` non-XP + `4 xp_*`) lên local `lexilingo`; Chrome E2E `99779a06` PASS (`5/44`), sửa overflow & Web CDN 404/CORS | `backfill_achievements.py`, `achievements_screen.dart`, `recent_badges_section.dart` | DB có `48` thành tựu; unlock không thưởng trùng; UI `0` console error | `84 passed` (`test_achievement_system.py` + `test_gamification_routes.py` + `test_isolated...`) + Chrome `99779a06` | Đã hoàn tất *(được user phê duyệt)* |
| **P1** | Vocabulary 180 CEFR Seed & 6 Topic Cards | **BLOCKED (Live Seed Approval)** | Live `vocabulary_items` chỉ có `15` bản ghi (`0` tags). Đã tái đối chứng nguồn (`Oxford 3000/5000 PDF` + Oxford sense pages): **`88 CONFIRMED_SOURCE / 66 CONFLICT / 26 BLOCKED`** (`0 VERIFIED`, `180/180 AI_GENERATED + NEEDS_REVIEW`) và thêm `--only-confirmed-source` / `--levels` | `cefr_vocabulary_data.py`, `scripts/seed_cefr_vocabulary.py`, `test_cefr_vocabulary_safe_seed_and_srs_uat.py`, `docs/VOCABULARY_FINAL_AUDIT.md` | Bảo toàn dòng cũ & `user_vocabulary`; cho phép seed chọn lọc `88` mục `CONFIRMED_SOURCE` hoặc đủ `180` mục `NEEDS_REVIEW`, không ép `VERIFIED` | **`29 passed in 5.54s`**, Ruff clean, CLI `--only-confirmed-source` (`88`) & full (`180`) idempotent trên `lexilingo_test` | **Có** (duyệt backup + seed + xóa `vocab_items:*`) |
| **P1** | AI Chat Live LLM Provider & Voice/Safety Fixes | **PARTIAL** *(Code/Fallback/Contracts PASS; Real LLM `BLOCKED` by Keys)* | Đã hoàn thiện `diagnose_node` `rule_fallback`, `AI_PROVIDER_SETUP.md`, streaming/history/timeout/503 fail-closed; boolean `.env`: `GEMINI_API_KEY_SET=False`, `GROQ_API_KEY_SET=False`, `OLLAMA_ENABLED=false`, `VOICE_DUPLEX_ENABLED=false` | `nodes_v2.py`, `lexi_chat_service.py`, `topic_chat_service.py`, `topic_llm_gateway.py`, `ai-service/docs/AI_PROVIDER_SETUP.md` | Phản hồi thật + streaming + giải thích học thuật không fallback giả | **`73 passed in 4.54s`** AI contract pytest (hậu sửa cuối), `1,008` AI full suite, Ruff `All checks passed!`, `:8001/health` `200` | **Có** (nhập `GEMINI_API_KEY` / `GROQ_API_KEY` theo `AI_PROVIDER_SETUP.md`) |
| **P1** | Authorship & QA Grammar 6 Courses / 18 Lessons / 36 QB | **PARTIAL (Live Seed Pending)** | Live `lexilingo` giữ `grammar_items = 0`, `question_bank = 0`, `lessons = 6`; đã kiểm toán & sửa 15 lỗi disambiguation/distractor/mojibake trên `6/12/12/18/72+12/36`, lập `docs/GRAMMAR_CONTENT_QA_INVENTORY.md` (`100% AI_GENERATED + NEEDS_REVIEW`) | `app/core/grammar_course_data.py`, `scripts/seed_grammar_courses.py`, `tests/test_grammar_course_seed_and_uat.py`, `docs/GRAMMAR_CONTENT_QA_INVENTORY.md` | Seed idempotent `6/12/12/18/36` không đụng Lesson 1, trải nghiệm Roadmap Unlock & Grammar Theory thật | **`3 passed in 7.79s`**, `--target test --apply` x2 idempotent (`unchanged=6/6/12/12/36`), Ruff `All checks passed!` | **Có** (duyệt `--target local --apply` + xóa `courses:*`) |
| **P1** | React Admin Post-Login RBAC & CRUD UAT | **PARTIAL / BLOCKED_BY_USER_LOGIN** | Đã thêm `canToggleAdminStatus` guard & `superAdminFlows.test.ts` (7 Super Admin QA fixtures cô lập), cùng Checklist Admin Browser UAT 7 bước; Google OAuth button không render do thiếu `VITE_GOOGLE_CLIENT_ID`; chờ user tự đăng nhập `super_admin` | `admin-service/src/pages/*`, `admin-service/src/lib/superAdminFlows.test.ts`, `backend-service/app/routes/admin_courses.py` | Super Admin đăng nhập được, RBAC tách quyền, CRUD Users/Courses/Vocab/QA hoạt động theo Checklist | **`13 files, 67 passed`**, `build:check` exit 0, `pnpm audit --prod` = `0` CVE, Chrome `:5173/login` (`d29b7b68`, `0ee8891e`) | **Có** (user đăng nhập phiên `super_admin` thật) |
| **P2** | `admin-service` Dependency Advisories (`0 high`) | **RESOLVED** | Đã cập nhật `axios@1.21.1` (kéo `follow-redirects >= 1.16.2`) và `zod@4.6.7` trong `pnpm-lock.yaml` | `admin-service/pnpm-lock.yaml` | `pnpm audit --prod` = `0`, `pnpm test` (`58 passed`) & build PASS | Đã chạy: `pnpm audit --prod` (`No known vulnerabilities found`), `pnpm test` (`58 passed`), `pnpm run build:check` | Đã xong (non-breaking) |
| **P2** | 6-Skill Placement Test Live Chrome UAT | **PASS** *(Deterministic Rubric)* | Chrome E2E (`7a8229e9`) hoàn thành 10 câu 6 kỹ năng (`Listening`, `Speaking`, `Reading`, `Writing`, `Grammar`, `Vocabulary`), `99.3%` -> `C2`, reload giữ nguyên trạng thái | `app/routes/proficiency.py`, `app/services/six_skill_placement.py`, `placement_test_page.dart` | Hoàn thành 10 câu 6 kỹ năng trên Chrome `:5174`, reload & không submit trùng | `test_six_skill_placement.py` + `test_proficiency_routes.py` (`49 passed`) + Chrome E2E (`7a8229e9`) PASS | Đã xong *(AI grader vẫn off do chưa có LLM key)* |
| **P3** | Backend Dev Config Defaults (`DEBUG=True`, `CORS_ORIGINS`) | **ENVIRONMENT** | Đang bật `APP_ENV=development` cho local test; deploy Internet cần đổi `.env.production` | `backend-service/app/core/config.py`, `docs/LEXILINGO_RELEASE_RUNBOOK.md` | `APP_ENV=production`, `DEBUG=False`, `SECRET_KEY` mạnh, `ALLOWED_ORIGINS` đúng domain | Kiểm tra boot `APP_ENV=production` trước deploy | **Có** (khi deploy) |

---

## 3. Lỗi đã sửa trong đợt Stabilization → Release Candidate

- `UniqueViolationError` trên `XPTransaction.source_id` khi review lại cùng 1 `user_vocabulary_id` (`routes/vocabulary.py`, `crud/vocabulary.py`).
- Lỗi điều hướng `/course-detail` chưa đăng ký & thiếu trạng thái lỗi/retry cho biểu đồ tuần + lệch ngày UTC (`my_progress_screen.dart`, `home_provider.dart`, `routes/progress.py`).
- Bất nhất khóa mở bài trên Roadmap vs `start_lesson` (`roadmap_unlock_policy.py`, `courses.py`, `learning.py`, `learning_roadmap_screen.dart`).
- `TypeError` `UserGrammarItem(status="learning")` và thiếu hợp đồng Grammar Theory -> Practice (`routes/learning.py`, `schemas/course.py`, `learning_provider.dart`, `learning_session_screen.dart`).
- Thiếu `reopen` sync/luyện tập lại trong Sổ tay lỗi sai (`mistake_notebook_repository.dart`, `mistake_notebook_page.dart`) và capture từ bài học (`learning_provider.dart`).
- Thiếu phân tầng độ khó `easy`/`medium`/`hard` (cùng câu C1/C2) trong Grammar Quiz (`routes/games.py`, `games_provider.dart`, `grammar_quiz_screen.dart`).
- Thiếu Guest Trial mode cô lập (`routes/guest.py`, `guest_session_service.dart`, `guest_trial_shell_page.dart`, `auth_wrapper.dart`, `welcome_page.dart`, `login_page.dart`), kèm sửa layout overflow `Row` -> `Wrap`.
- Lỗi `StringDataRightTruncationError` khi user có `level='beginner'` (8 ký tự) bắt đầu 6-Skill Placement Test lưu vào `VARCHAR(5)`, mismatch `ApiClient.patch` vs `@router.put`, và gọi nhầm `UserScopeService.getScopedKey` (`six_skill_placement.py`, `routes/proficiency.py`, `proficiency_data_source.dart`, `placement_test_provider.dart`, `placement_test_page.dart`).
- Lỗi CSP console trong dev của React Admin từ `@vercel/analytics` gọi `va.vercel-scripts.com` (`admin-service/src/main.tsx` chuyển sang `{import.meta.env.PROD && <Analytics />}`).

---

## 4. File thay đổi chính trong phiên hiện tại (`git status`)

Xem danh sách đầy đủ trong [LEXILINGO_FINAL_ACCEPTANCE.md](file:///D:/LexiLingo/LexiLingo/docs/LEXILINGO_FINAL_ACCEPTANCE.md) và `git status -s`. Nhóm file mới thêm cho RC:
- Backend: `app/routes/guest.py`, `app/services/roadmap_unlock_policy.py`, `app/services/six_skill_placement.py`, `tests/test_guest_routes.py`, `tests/test_six_skill_placement.py`, `tests/test_grammar_theory_flow.py`, `tests/test_grammar_tiers_routes.py`, `tests/test_roadmap_unlock_policy.py`, `tests/test_release_candidate_e2e_journey.py`.
- Flutter: `lib/features/auth/data/services/guest_session_service.dart`, `lib/features/auth/presentation/pages/guest_trial_shell_page.dart`, cùng các test `guest_trial_flow_test.dart`, `six_skill_placement_test.dart`, `grammar_theory_phase_test.dart`, `roadmap_unlock_gate_test.dart`, `mistake_review_loop_test.dart`, `my_progress_screen_t05_t06_test.dart`, `vocab_provider_t04_idempotency_test.dart`.
- Admin: `admin-service/src/main.tsx`.
- Docs: `docs/LEXILINGO_COMPLETION_TRACKER.md`, `docs/LEXILINGO_FINAL_ACCEPTANCE.md`, `docs/LEXILINGO_RELEASE_RUNBOOK.md`, `docs/LEXILINGO_RELEASE_CANDIDATE_REPORT.md`.

---

## 5. Kết quả Test tổng hợp

- **Final Blocker Resolution Swarm QA (`@verifier`, `#18`, hậu mọi chỉnh sửa cuối)**:
  - **Grammar Content (`@content_grammar` + `@verifier`)**: `pytest -p no:cacheprovider tests/test_grammar_course_seed_and_uat.py -q`: **`3 passed in 7.79s`**; `seed_grammar_courses --target test --apply` x2 idempotent (`6/12/12/18/36 -> unchanged=6/6/12/12/36`); `ruff check`: `All checks passed!`.
  - **Vocabulary QA (`@vocab_qa` + `@verifier`)**: `pytest -p no:cacheprovider tests/test_cefr_vocabulary_safe_seed_and_srs_uat.py tests/test_cefr_vocabulary_seed.py -q`: **`29 passed in 5.54s`**; selective `--only-confirmed-source` (`88`) & `--levels C2` (`6`) & full (`180`) idempotent trên `lexilingo_test` (`verified_count=0`, `source_ref_set=0`); `ruff check`: `All checks passed!`.
  - **AI Service (`@platform` + `@verifier`)**: Contract pytest cô lập (`KUZU_DB_PATH` + `--basetemp`): **`73 passed in 4.54s`**; `ruff check --select F,E9`: `All checks passed!`. *(Đợt trước đó: `1,008 passed in 32.46s`).* Real LLM giữ **`BLOCKED`** (`groq_configured:false, gemini_configured:false, ollama_enabled:false`).
  - **React Admin (`@platform` + `@verifier`)**: `pnpm test -- --run`: **`13` files, `67 passed`** (`superAdminFlows.test.ts` +7); `pnpm run build:check` (`tsc -b && vite build`): exit `0`; `pnpm audit --prod`: **`No known vulnerabilities found`**. Post-login Admin UI giữ `NOT_TESTED` / `BLOCKED` chờ user đăng nhập `super_admin`.
- **Các bộ nền Swarm 1 đã PASS (`@verifier`, `#9`)**:
  - Backend Publication Gate & Seed Preflight (10 files gồm `test_content_publication_gate.py`, `test_grammar_course_seed_and_uat.py`, `test_cefr_vocabulary_safe_seed_and_srs_uat.py`): **`164 passed in 20.19s`**; Flutter Vocabulary & Course: **`53 passed`** + `flutter analyze` `No issues found!`; `pg_dump` preflight backup `.tmp/lexilingo_preflight_backup.sql` (`401,987 bytes`) hợp lệ; live DB `lexilingo` giữ nguyên vẹn.
  - **Flutter App**: `948 passed, 0 failed` (`153 + 186 + 290 + 319`); `flutter analyze --no-pub lib test`: **`No issues found!`**.
- **Live HTTP Smoke Checks & Chrome E2E**:
  - Live HTTP (`@verifier` + post-restart): `:8000/health`, `/api/v1/courses`, `/api/v1/guest/courses`, `/api/v1/guest/trial-pack`, `/api/v1/vocabulary/items`, `/api/v1/vocabulary/word-of-day` (`200`); `/api/v1/games/grammar-quiz` (`401`); `:8001/health`, `/api/v1/topics/stories`, `/api/v1/topics/llm/health`, `/api/v1/lexi/health` (`200`); `:5173/login`, `:5174/` (`200`).
  - Chrome E2E (`d29b7b68` post-swarm + `0ee8891e`, `7a8229e9`, `cd49ec51`, `99779a06`): `:5174/` Guest Trial (`Flashcards` lật `"commute"` + `6` khóa public `/api/v1/guest/courses?limit=10 -> 200`, `0` failed reqs, `0` console error) + `:5173/login` (`1440x900` & `390x844`: `401` + `"Email hoặc mật khẩu không đúng."`, `0` overflow, `0` console error; ảnh `final_step_29.png`).
- **`git diff --check`**: Exit code `0` trên toàn repository.

---

## 6. Chrome E2E Evidence

- **`cd49ec51` (`http://127.0.0.1:5174/`)**: Sign out → Login UI → `"Học thử ngay (Không cần đăng nhập)"` → Flashcard `"commute"` lật & đánh dấu thuộc (`XP tạm: 10`) → Ngữ pháp Theory → Practice `4/4` (`100%`, `XP tạm: 55`) → Khóa học (`6` public courses + gated dialog `"AI Tutor Chat"`) → reload giữ nguyên `XP tạm: 55` & `"commute"`. Responsive mobile **`390x844`**: **0 overflow, 0 clipping, 0 console errors**. *(Ảnh mới nhất: `final_step_53.png`.)*
- **`cd49ec51` (`http://127.0.0.1:5173/login`)**: Reload sau bản vá CSP → HTTP `200`, Admin Console Login UI đầy đủ, **0 failed network requests, 0 console errors**.
- **Các phiên Chrome E2E trước (`3f0c6cf5`, `a0a092e9`)**: Đã PASS Auth Login/Reload, Course Progress `100%` đồng bộ mọi màn hình, XP lưu thật sau reload, T02 Vocabulary Pagination (`16 từ`, lọc `B1`, search `lucid`).

---

## 7. Security Findings

- **Đã xử lý & xác nhận an toàn**:
  - Endpoint riêng tư (`/users/me`, `/proficiency/placement-test`, `/admin/grammar`, `/admin/users`, `/admin/vocabulary`, `/admin/courses`, `/admin/analytics/dashboard/kpis`) không token đều trả HTTP `401` và learner JWT trả HTTP `403`.
  - `/guest/trial-pack` không tạo user DB, không lộ `correct_answer`/`correct_option`, dùng SHA-256 `answer_digest`.
  - `/proficiency/placement-test/start` không lộ `correct` hay `rubric_keywords`; submit có `idempotency_key` replay + HTTP `409` chống submit trùng.
  - `@vercel/analytics` được giới hạn theo `import.meta.env.PROD`, xóa sạch CSP violation ở localhost `:5173`; `admin-service` `pnpm audit --prod` đạt **`No known vulnerabilities found`** (`axios@1.21.1`, `zod@4.6.7`).
  - Admin Vocabulary API chặn nâng trạng thái `VERIFIED` nếu thiếu `source_reference` và bảo toàn `translation["examples"]`.
- **Cần xử lý trước Go-Live Internet**:
  - Chuyển cấu hình `backend-service` sang `APP_ENV=production`, `DEBUG=False`, `SECRET_KEY` production, `ALLOWED_ORIGINS` chuẩn domain.
  - Bổ sung `VITE_GOOGLE_CLIENT_ID` cho `admin-service` nếu muốn bật nút đăng nhập Google OAuth trên `:5173/login`.

---

## 8. Content Quality Findings (`VERIFIED` / `NEEDS_REVIEW` / `BLOCKED_SOURCE` / `MISSING_CONTENT`)

| Nhóm nội dung | Phân loại hiện tại | Hiện trạng thực tế |
|---|---|---|
| `6` Khóa học A1–C2 & `6` Lesson hiện có trên DB | **`VERIFIED` *(phạm vi 12 bài tập hiện tại)*** | Cả `12/12` exercises có `correct_answer` và `explanation` đầy đủ (`missing_ans=0`, `missing_exp=0`). |
| `180` Từ vựng CEFR & `6` Topic tags trong code | **`88 CONFIRMED_SOURCE / 66 CONFLICT / 26 BLOCKED`** *(Toàn bộ `NEEDS_REVIEW`)* | Đã tái đối chứng Oxford 3000/5000 PDF + sense pages (`docs/VOCABULARY_FINAL_AUDIT.md`); sẵn sàng seed chọn lọc `88` mục hoặc đủ `180` mục `AI_GENERATED + NEEDS_REVIEW` (`0 VERIFIED`). |
| `48` Achievements definitions trong DB `lexilingo` | **`VERIFIED / PASS`** | Đã backfill `48/48` (`with_badge_icon=44`), Backend `84 passed`, Chrome E2E `99779a06` PASS (`5/44`, `0` console errors, `0` failed reqs). |
| `GrammarItem` & `QuestionBank` & Lesson `type=grammar` | **`AUDITED_NEEDS_REVIEW` / Chờ duyệt seed DB live** | Đã kiểm toán & sửa 15 lỗi disambiguation/distractor trên `6/12/12/18/72+12/36` (`docs/GRAMMAR_CONTENT_QA_INVENTORY.md`), 100% giữ `AI_GENERATED + NEEDS_REVIEW`; live DB hiện giữ `grammar_items = 0`, `question_bank = 0`. |
| Placement Test Speaking/Writing AI Grader & AI Chat | **`BLOCKED_SOURCE` (Thiếu LLM Key)** | Hoạt động minh bạch với deterministic rubric (`ai_graded=False`) và `safe_tutor_fallback`; không giả lập AI. |

---

## 9. Những blocker còn lại

1. **Phê duyệt Data Seed Vocabulary 180 CEFR lên PostgreSQL Live**: Seed `180` từ `NEEDS_REVIEW` (`seed_and_test_cefr_a1_c2.py`, bảo toàn `15` dòng cũ) + xóa prefix `vocab_items:*` nếu phát sinh. *(Achievements `48` defs đã hoàn tất backfill & xác minh E2E).*
2. **Cấu hình LLM Provider cho AI Service (`ai-service/.env`)**: Điền `GEMINI_API_KEY` / `GROQ_API_KEY` hợp lệ (hoặc bật Ollama `:11434`).
3. **Authorship dữ liệu Grammar & Multi-lesson Courses**: Nạp tối thiểu >=1 bài `lesson_type=grammar` (kèm `grammar_items`) và >=2 lessons/course để UAT trực tiếp Roadmap Unlock Gate & Grammar Theory trên Chrome.
4. **Post-Login Admin UAT**: Bạn tự đăng nhập Super Admin tại `http://127.0.0.1:5173/login` để UAT `/auth/me`, RBAC, Dashboard và User/Course/Vocabulary Management.

---

## 10. Kết luận Release Readiness: **`CONDITIONAL`**

- **Kết luận**: Đã phục hồi hoàn toàn hạ tầng Docker (`lexilingo-postgres`, `lexilingo-redis`, `lexilingo-mongodb`), toàn bộ Backend Security/Auth/Vocab/Gamification tests (`203` + `150` passed trên PostgreSQL thật) và `admin-service` security audit (`0` vulnerabilities, `58` tests + build PASS) cùng Chrome smoke check (`:5174` & `:5173`, `0` console error). Hệ thống **sẵn sàng cho UAT nội bộ**, nhưng vẫn giữ mức **`CONDITIONAL`** (chưa `READY` cho Production Public Launch) chừng nào 4 blocker dữ liệu/key/UAT ở Mục 9 chưa được người dùng phê duyệt và hoàn tất.
