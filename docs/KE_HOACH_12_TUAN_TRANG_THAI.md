# Đối chiếu kế hoạch phát triển 12 tuần

> Cập nhật: 01/11/2026
> Phạm vi xác minh: mã nguồn trong worktree, Flutter Web, Admin Web, Backend, AI Service, MCP và các bài kiểm thử chạy được cục bộ. Không deploy hoặc thay đổi production.

## Kết luận ngắn

LexiLingo đã có mã nguồn cho toàn bộ nội dung chức năng trong kế hoạch 12 tuần và đã vượt phạm vi MVP. Tuần 1–10 đã hoàn thành ở mức mã nguồn; Tuần 11–12 đã hoàn thành phần kiểm thử tĩnh/unit/build và tài liệu, nhưng chưa thể xác nhận end-to-end với dịch vụ thật vì máy hiện tại không truy cập được Docker daemon, chưa có bộ secret cục bộ để khởi động stack và không có credential dùng để gọi provider AI thật.

Quy ước trạng thái:

- **Hoàn thành:** có luồng triển khai trong mã nguồn và có bằng chứng test/build phù hợp.
- **Hoàn thành có điều kiện:** mã nguồn đã có, nhưng việc chạy thật phụ thuộc service, model, feature flag hoặc credential bên ngoài.
- **Chưa xác nhận E2E:** chưa chạy được toàn bộ luồng trên stack PostgreSQL/Redis/MongoDB/AI thật tại máy này.

## Trạng thái theo từng tuần

| Tuần | Trạng thái | Những gì đã làm | Phần còn lại cần xác nhận |
|---|---|---|---|
| 1 | Hoàn thành có điều kiện | Có Docker Compose cho local/dev/validation, cấu hình Backend/AI, PostgreSQL/Redis/MongoDB và provider Gemini/Groq/Ollama; có `.env.example` và script khởi động | Điền secret thật và chạy health check/provider smoke test; không ghi secret vào repo |
| 2 | Hoàn thành | Monorepo đã tách `flutter-app`, `backend-service`, `ai-service`, `admin-service`, `mcp-server`, gateway và monitoring; có `docs/ARCHITECTURE.md` | Chỉ cần cập nhật sơ đồ khi kiến trúc thay đổi |
| 3 | Hoàn thành | Có model User/Course/Unit/Lesson/Progress, SQLAlchemy/Alembic, auth JWT/Firebase/OAuth, RBAC và API học tập | Chạy lại migration trên PostgreSQL mới hoàn toàn trước nghiệm thu |
| 4 | Hoàn thành | Flutter có đăng ký/đăng nhập, hồ sơ, cài đặt, onboarding/mục tiêu học tập và kết nối Backend | Browser E2E auth/profile vẫn cần stack thật |
| 5 | Hoàn thành | Course → Unit → Lesson → Exercise, CEFR A1–C2, placement/proficiency assessment và script kiểm tra/seed CEFR đã có | Xác nhận chất lượng và độ phủ dữ liệu học thật A1–C2 |
| 6 | Hoàn thành | Có hơn 20 dạng bài tập, vocabulary library, flashcard, SM-2/FSRS, lưu kết quả và tiến độ bài học | Smoke test bằng dữ liệu production-like |
| 7 | Hoàn thành | XP, streak, daily quest, achievement, leaderboard, shop, sổ lỗi sai và ôn tập đã có. Ngày 01/11 đã thay bốn badge Grammar/Culture/Writing/Listening từ giá trị giả `0` sang dữ liệu lesson pass thật | Badge theo giờ học, chat/help và comeback vẫn cần nguồn sự kiện/timezone đầy đủ |
| 8 | Hoàn thành có điều kiện | AI Chat, topic chat, TRACE-CAG, learner profile, CEFR personalization, Gemini/Groq/Ollama và streaming đã có | Inference thật phụ thuộc API key/model, Redis/KuzuDB và feature flag |
| 9 | Hoàn thành có điều kiện | Whisper STT, Piper/gTTS TTS, HuBERT pronunciation và IELTS Writing/Speaking đã có; test voice/security/quota đã có | Chạy model inference và WebSocket/duplex voice trên máy có model/runtime phù hợp |
| 10 | Hoàn thành | Admin React có dashboard, CRUD course/unit/lesson/exercise/vocabulary/user/RBAC, analytics, AI settings và AI Content Studio tạo lesson | AI Content Studio cần Gemini key để smoke test provider thật |
| 11 | Hoàn thành phần code/test; chưa xác nhận E2E | Admin test/build, Backend suite, AI suite, MCP tests và các test tập trung đã chạy; gateway, security header, rate limit, monitoring và backup có cấu hình | Chạy stack PostgreSQL/Redis/MongoDB qua Docker, migration, health check và browser smoke test |
| 12 | Hoàn thành tài liệu/build; chưa xác nhận E2E | Có seed/check CEFR, tài liệu kiến trúc/API/vận hành/báo cáo, Flutter Web release build và các runbook nghiệm thu | Chạy trọn luồng đăng nhập → khóa học → bài học → tiến độ → AI trên stack thật và lưu biên bản nghiệm thu |

## Phần vừa hoàn thiện trong lần rà soát này

- Achievement skill không còn hardcode bằng 0: đếm lesson đã pass theo `Lesson.skill`, `Course.skill` và category `cultural-english`, dùng `COUNT(DISTINCT)` để tránh đếm trùng.
- Sửa script tạo load-test identity để đặt quyền trên đường dẫn file tạm thay vì file descriptor không hợp lệ trên Windows.
- Bỏ API SQLAlchemy `Result.tuples()` và Firebase `MulticastMessage.tokens` đã deprecated; full Backend suite chạy lại không còn warning.
- Chuẩn hóa test đọc source bằng UTF-8; tách rõ test entrypoint Linux khỏi runner Windows và chỉ skip network smoke khi transport thật sự không khả dụng.
- Làm Content ETL crash-durable tương thích Windows: file fsync dùng writable handle trên Windows, vẫn giữ read-only handle và directory fsync trên POSIX/Linux.
- Load-test identity giữ kiểm tra mode `0600` trên POSIX; Windows dùng ACL nên không diễn giải synthetic POSIX mode bits.
- STT session metric dùng `perf_counter()` để tránh độ phân giải 15,625 ms của `GetTickCount64` trên Windows.
- Test concurrency của TRACE-CAG dùng budget phù hợp với synthetic delay, nên đo concurrency thay vì vô tình kích hoạt timeout policy.
- Khi `model-development/` gitignored không tồn tại, pytest bỏ đúng nhóm benchmark phụ thuộc corpus 4,3 GB thay vì lỗi lúc collect; test production còn lại vẫn chạy bình thường.

## Bằng chứng kiểm thử ngày 01/11/2026

| Khối | Kết quả |
|---|---|
| Admin React | 48/48 test pass; TypeScript + Vite production build pass |
| Backend | 1.734 pass, 3 skip; không còn cảnh báo deprecation trong lần chạy cuối |
| AI Service | 998/998 test khả dụng pass; benchmark gitignored không được tính |
| MCP Server | 19 pass, 1 skip |
| Flutter Web | `flutter analyze`: no issues; `flutter build web --release`: thành công. Có cảnh báo tương thích Wasm từ `flutter_secure_storage_web`, không ảnh hưởng build JavaScript hiện tại |

## Việc không thể tự hoàn tất nếu thiếu môi trường bên ngoài

1. Khởi động Docker validation stack: tài khoản hiện tại không truy cập được Docker API và compose production yêu cầu secret chưa được cung cấp.
2. Gọi Gemini/Groq thật: cần API key hợp lệ; không nên tạo, đoán hoặc ghi key vào repo.
3. Browser E2E xuyên dịch vụ: cần Backend, AI, PostgreSQL, Redis và MongoDB cùng hoạt động.
4. Benchmark TRACE-CAG đầy đủ: cần thư mục `ai-service/model-development/` và corpus/model artifact gitignored.
5. Voice inference thật: cần model Whisper/Piper/HuBERT và tài nguyên runtime tương ứng.

Các mục trên không nên được đánh dấu hoàn thành chỉ bằng mock/unit test. Khi đủ môi trường, chạy `docker-compose.dev.yml` cùng `docker-compose.validation.yml`, `scripts/validate_local_stack.sh`, migration check và smoke test auth/course/lesson/AI trước khi nghiệm thu.
