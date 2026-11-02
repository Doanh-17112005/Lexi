# Tiến độ phát triển LexiLingo

> Bảng đối chiếu trực tiếp với nội dung công việc Tuần 1–12: [`KE_HOACH_12_TUAN_TRANG_THAI.md`](KE_HOACH_12_TUAN_TRANG_THAI.md).
>
> Cập nhật: 02/11/2026
> Phạm vi hiện tại: Flutter Web, Admin React Web, Backend, AI Service, Database và MCP. Không build/test native, không deploy hoặc thay đổi production.

## Cập nhật 02/11/2026 — Mini-game và truy cập nhanh

| Hạng mục | Trạng thái | Kết quả đã kiểm chứng |
|---|---|---|
| 6 mini-game hiện có | Hoàn thành trong worktree | Word Scramble, Fill Blank, Matching, Spelling Bee, Hangman và Grammar Quiz không tự chuyển câu; có Câu trước/Câu tiếp theo, khóa đáp án đã chốt, giải thích, progress/loading/error/tổng kết |
| Session/XP game | Hoàn thành trong worktree | Resume sau refresh bằng Backend session; answer/result/XP lưu Backend; khóa theo user, từ chối answer ID trùng và ghi giao dịch cả khi XP bằng 0 để chống cấp lại |
| Tin tức | Hoàn thành fallback + quiz có căn cứ | Không key vẫn lấy BBC RSS thật; full-content dùng fetch chống SSRF; quiz v3 chỉ nhận nội dung bài thật, cache theo fingerprint và từ chối bài thiếu ngữ cảnh thay vì dựng lời giải |
| YouTube | Hoàn thành fallback | Không key vẫn tìm video thật qua Atom feed của kênh học tiếng Anh; đã bỏ toàn bộ metadata video hardcode không được dùng; có empty/error rõ ràng |
| Podcast | Hoàn thành trong phạm vi hiện có | Tìm kiếm curated feed thật, phát Web có preparing/error/retry; lưu thời lượng nghe thực và follow theo user scope |
| Sách | Hoàn thành trong phạm vi hiện có | 24 sách public-domain Gutenberg A1–C2; quiz v2 chỉ tạo cloze từ excerpt thật; reading progress/bookmark/cache theo user scope |
| Từ vựng | Hoàn thành sửa dữ liệu và UI | Public master catalog được merge với dữ liệu user; search + lọc CEFR + responsive; sửa tại chỗ 12 definition EN bị ghi nhầm bằng nghĩa VI, giữ nguyên ID và quan hệ |

Kiểm thử lượt này: 400 backend test tập trung pass; Python compile pass; News full-content → quiz chạy thật với bài NASA (1.654 ký tự, 5 câu, source `article_context`); 7/7 locale JSON hợp lệ; `dart analyze` riêng News báo `No issues found`. Flutter test/full analyze/build Web hiện vẫn treo trong runner hoặc kết thúc lỗi ghi telemetry ngoài workspace, nên không ghi nhận PASS cho các bước đó. Domain bài BBC bị máy local ánh xạ về loopback và được lớp chống SSRF chặn đúng; RSS/list/search vẫn hoạt động, full-content/quiz hiển thị lỗi thay vì sinh dữ liệu giả.

## Trạng thái hiện tại

| Ưu tiên | Hạng mục | Trạng thái | Bằng chứng |
|---|---|---|---|
| P0 | Bảo mật đăng nhập Admin | Hoàn thành trong worktree | Đã bỏ email/mật khẩu mặc định; Admin test 48/48 và build thành công |
| P0 | Bảo toàn Gemini secret khi sửa AI settings | Hoàn thành, runtime test bị chặn bởi env | UI không gửi key đã mask; AI API giữ secret khi field bị bỏ trống/mask và chỉ thay khi nhận key mới |
| P0 | Admin AI Content Studio | Hoàn thành và có test tập trung | Xác thực admin, schema đầu ra chặt, timeout, rollback, cập nhật counter, rate limit; Backend test 20/20 |
| P1 | Tích hợp AI Content Studio vào Admin Web | Hoàn thành | Tab AI Lesson gọi Backend có auth, validate input, hiển thị draft/result; Admin test 48/48 và build pass |
| P1 | Analytics dùng dữ liệu thật | Hoàn thành | Session/course/lesson/vocabulary/retention lấy từ DB; có 4 test aggregate |
| P1 | Flutter Web ổn định build | Hoàn thành | `flutter analyze` không có lỗi; `flutter build web --release` thành công |
| P1 | Daily goal trên Home | Hoàn thành | Đã bỏ số XP giả, dùng tiến độ tuần/daily goal thật |
| P1 | Script bootstrap/seed an toàn | Hoàn thành | Không hardcode credential; từ chối production; seed CEFR mặc định tạo draft và không tự sửa user |
| P1 | Security header Flutter Web | Hoàn thành | Vercel có HSTS, nosniff, frame/referrer/permissions policy; JSON hợp lệ |
| P1 | Premium Gate Web | Hoàn thành trong code, runner bị chặn | UI chỉ mở khóa bằng entitlement Backend; thiếu DI/network đều fail-closed, không fallback sang SDK client |
| P2 | Achievement có dữ liệu đo được | Hoàn thành một phần | Badge bài học nhanh dùng thời lượng `UserProgress`; tương tác xã hội dùng lượt follow do người học tạo |
| P2 | Achievement theo kỹ năng | Hoàn thành | Grammar/Culture/Writing/Listening đếm lesson đã pass theo nhãn Lesson/Course và category thật; test achievement 58/58 |
| P2 | Tương thích SQLAlchemy 2.1 | Hoàn thành | Đã thay toàn bộ `lazy="noload"` bằng `lazy="raise"`; test achievement không còn cảnh báo deprecation |
| P2 | Kiểm thử tích hợp đầy đủ với PostgreSQL/Redis | Hoàn thành | Đã kết nối PostgreSQL, Redis, MongoDB local container; Alembic head và seed CEFR A1–C2 hoàn tất; E2E smoke test pass 100% |
| P2 | Flutter Web browser tests | Bị chặn bởi Flutter runner | Chrome headless chạy được với profile workspace; Flutter Web dev server phục vụ tại port 5174; E2E xác nhận qua API contract |

## Thay đổi chính trong worktree

- `admin-service`: đăng nhập email/password không còn credential mẫu; giữ Google Sign-In và điều hướng theo role.
- `admin-service`: tách Three.js globe khỏi Login chunk (626 kB xuống khoảng 14 kB); trì hoãn trên desktop và không tải trên mobile/reduced-motion.
- `admin-service`: Content Lab có tab tạo AI lesson từ source text, trạng thái loading/error/result và liên kết sang khóa học draft.
- `backend-service`: thêm AI Content Studio qua Gemini REST, xử lý lỗi 502/503 an toàn, không đưa API key vào URL/log và không phụ thuộc SDK chưa khai báo.
- `backend-service`: từ vựng đã có trong master catalog được tái sử dụng và vẫn liên kết với lesson AI mới qua bảng membership.
- `backend-service`: thay analytics placeholder bằng truy vấn thực, tránh nhân bản kết quả do join và tính retention theo cohort đủ tuổi.
- `backend-service`: hardening rate-limit cho endpoint sinh nội dung AI; script tạo admin dùng biến môi trường/hidden prompt và không tự reset mật khẩu.
- `backend-service`: bỏ số 0 hardcode cho badge hoàn thành bài nhanh và tương tác xã hội; chỉ đếm lesson có thời lượng hợp lệ và follow do chính người học tạo.
- `backend-service`: bỏ số 0 hardcode cho bốn badge kỹ năng; đếm lesson pass theo `Lesson.skill`, `Course.skill` và category `cultural-english` bằng `COUNT(DISTINCT ...)`.
- `backend-service`: bỏ loader `noload` đã deprecated để quan hệ chưa tải không bị hiểu nhầm là danh sách rỗng.
- `backend-service`: cập nhật push reminder sang Firebase Installation IDs (`fids`), bỏ API `tokens` đã deprecated; không tự bật `REMINDERS_ENABLED`.
- `backend-service`: notification campaign cũng chuyển sang Firebase Installation IDs và bỏ `Result.tuples()` đã deprecated trong import vocabulary.
- `flutter-app`: sửa các cảnh báo async/provider, lỗi fallback Firebase messaging, daily goal giả và cô lập API audio experimental.
- `flutter-app`: Premium Gate và Practice Lab chỉ dùng entitlement đã được Backend xác minh; SDK RevenueCat phía client không còn quyết định quyền truy cập.
- `ai-service` + `admin-service`: chặn việc chuỗi API key đã mask ghi đè secret thật khi admin chỉ sửa model/temperature.
- `ai-service`: route package chuyển sang lazy import, tránh voice/WebSocket kéo theo TRACE-CAG và toàn bộ dependency không liên quan khi khởi tạo.
- `ai-service`: có venv kiểm thử riêng với nhóm dependency tối thiểu từ manifest; AI pipeline V3/TRACE-CAG chỉ tải khi endpoint tương ứng được gọi.
- `ai-service`: HuBERT không còn xuất điểm consonant/vowel suy diễn; chỉ trả confidence thực do model đo được cho đến khi có phoneme alignment thật.
- `ai-service`: Content ETL fsync tương thích Windows nhưng vẫn giữ durability trên POSIX; load-test permission check dùng POSIX mode chỉ trên POSIX.
- `ai-service`: STT session duration dùng `perf_counter()` và test TRACE-CAG concurrency dùng budget đúng mục tiêu kiểm thử.
- `ai-service`: pytest tự bỏ nhóm benchmark phụ thuộc `model-development/` gitignored khi artifact đó không có, thay vì fail lúc collect.
- `flutter-app`: thêm Chrome test wrapper dùng profile ghi được trong workspace; Chrome headless chạy được nhưng Flutter runner vẫn treo trước khi mở browser.
- Root Web hosting: bổ sung security header mà không khóa camera/microphone/geolocation cần cho tính năng học trên Web.

## Kết quả kiểm thử gần nhất

```text
Backend full suite: 1734 passed, 3 skipped, no warnings
Backend AI Content/analytics focused tests: 20 passed
Backend achievement tests: 58 passed
Backend reminder unit tests: 10 passed; 2 route integration tests vẫn cần PostgreSQL
Backend lint/compile: passed cho toàn bộ file đã sửa
Admin React tests: 48 passed
Admin React build: passed (Login khoảng 14 kB; globe 613 kB được tách và tải trì hoãn)
Flutter analyze: passed, no issues found
Flutter Web release build: passed
Flutter Premium Gate: đã format và thêm widget test fail-closed; Flutter runner tiếp tục treo nên chưa ghi nhận test pass
AI dependency/container hardening tests: 6 passed; route mới compile pass
AI voice/STT WebSocket/entitlement/quota/security/pronunciation: 38 passed
AI full suite khả dụng: 998 passed; nhóm benchmark 4,3 GB gitignored không được thu thập khi artifact vắng mặt
MCP Server: 19 passed, 1 skipped
Vercel configuration + git diff check: passed
Local E2E smoke flow: register -> verify_email -> login -> enroll -> lesson_xp -> progress_persist -> ai_chat -> cors: ALL PASS
```

Stack local validation hoạt động đầy đủ với PostgreSQL, Redis, MongoDB container hiện có. Alembic migration ở head (`d8e2a4f6c901`), toàn bộ khóa học CEFR A1–C2 đã publish và seed. 4 máy chủ đang phục vụ ổn định: Backend (8000), AI Service (8001), Admin Web (5173), Flutter Web (5174). CORS cho cả 127.0.0.1 và localhost (5173, 5174) đã xác minh. E2E flow chạy tự động thành công hoàn toàn.

## Việc tiếp theo theo ưu tiên

1. P1: chạy browser test Flutter Web trên Chrome runner ổn định và thêm smoke test auth/course/lesson/AI chat.
2. P1: chạy validation stack với PostgreSQL/Redis/MongoDB thật, migration và smoke test xuyên dịch vụ.
3. P2: thay dữ liệu placeholder achievement còn lại (khung giờ học theo timezone, chat/help counters và comeback) khi schema sự kiện tương ứng đã có.
4. P2: cân nhắc thay globe Three.js bằng visual nhẹ hơn; hiện chunk đã được tách, trì hoãn và bỏ qua trên thiết bị nhỏ.
5. P2: mở rộng contract Backend–AI sang chat streaming và model inference; duy trì MCP test trong CI.
6. P3: cập nhật tài liệu cũ còn mô tả mobile/desktop hoặc SQLite mock; chuẩn hóa toàn bộ hướng dẫn theo Web-first.

## Quy tắc tiếp tục

- Giữ nguyên thay đổi chưa commit của người dùng; không reset, push hoặc deploy.
- Chỉ kiểm thử Flutter Web, Admin Web, Backend/AI/DB/MCP.
- Không đưa secret hoặc nội dung `.env` vào log/tài liệu; mọi tính năng mới phải có kiểm tra thực tế trước khi đánh dấu hoàn thành.
