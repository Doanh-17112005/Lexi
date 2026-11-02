# Tổng quan dự án LexiLingo

> Đối chiếu kế hoạch Tuần 1–12 và danh sách phần còn lại: [`KE_HOACH_12_TUAN_TRANG_THAI.md`](KE_HOACH_12_TUAN_TRANG_THAI.md).

> Tiến độ triển khai và kết quả kiểm thử mới nhất: [`DEVELOPMENT_PROGRESS.md`](DEVELOPMENT_PROGRESS.md). Phạm vi phát triển hiện tại đã chuyển sang Web-first; các mô tả mobile/desktop bên dưới chỉ phản ánh khả năng có sẵn trong mã nguồn, không phải mục tiêu build/test hiện tại.

> Cập nhật: 01/11/2026
> Phạm vi: đối chiếu mã nguồn, tài liệu dự án và trạng thái Git tại thời điểm cập nhật.
> Lưu ý: trạng thái “đã có” nghĩa là đã tìm thấy luồng triển khai trong mã nguồn; không đồng nghĩa mọi chức năng đã được kiểm thử end-to-end trên môi trường production.

## 1. Tổng quan

LexiLingo là nền tảng học tiếng Anh đa nền tảng, kết hợp lộ trình học theo CEFR, trợ giảng AI, luyện hội thoại và phát âm, nội dung thực tế, theo dõi tiến độ và gamification.

Dự án được tổ chức theo monorepo với năm thành phần có thể vận hành độc lập:

| Thành phần | Vai trò | Công nghệ chính |
|---|---|---|
| `flutter-app/` | Ứng dụng cho người học trên mobile/web/desktop | Flutter, Dart, Provider, GetIt, sqflite |
| `backend-service/` | API nghiệp vụ, xác thực, dữ liệu học tập và gamification | FastAPI, SQLAlchemy async, PostgreSQL, Redis, Celery |
| `ai-service/` | Trợ giảng AI, TRACE-CAG, voice, chấm phát âm và IELTS | FastAPI, LangGraph, KuzuDB, Gemini/Groq/Ollama, Whisper, Piper, HuBERT |
| `admin-service/` | Trang quản trị nội dung, người dùng và vận hành | React, TypeScript, Vite, TanStack Query, Recharts |
| `mcp-server/` | Công cụ hỗ trợ IDE/AI agent trong lúc phát triển | Python, Model Context Protocol |

Hạ tầng bổ trợ gồm Docker Compose, Kong/NGINX gateway, Prometheus, Grafana, systemd, backup/restore và các workflow GitHub Actions.

## 2. Kiến trúc và luồng chính

```text
Người học ──> Flutter App ──> Gateway ──> Backend API ──> PostgreSQL/Redis
                                  │              │
                                  └──────────────┴──> AI Service
                                                        ├─ TRACE-CAG + KuzuDB
                                                        ├─ LLM cloud/local
                                                        └─ STT/TTS/Pronunciation

Quản trị viên ──> Admin React ──> Gateway/Backend/AI Service
Nhà phát triển ──> MCP Server ──> công cụ i18n, schema và ngữ cảnh học tập
```

Luồng học điển hình: đăng nhập → chọn khóa học/bài học → làm bài → nhận XP và cập nhật tiến độ → lưu lỗi/từ vựng → ôn tập → nhận gợi ý hoặc phản hồi cá nhân hóa từ AI.

## 3. Những phần đã hoàn thành

### 3.1 Ứng dụng người học

- Xác thực bằng email và các nhà cung cấp xã hội, quên/đặt lại mật khẩu, xác minh email.
- Hồ sơ, thiết lập ngôn ngữ/giao diện/mục tiêu ngày và quản lý tài khoản.
- Lộ trình Course → Unit → Lesson, đăng ký khóa học, phiên học và hơn 20 dạng bài tập giao diện.
- Thư viện từ vựng, flashcard, hàng đợi ôn tập, word of the day và lưu nhanh từ mới.
- Placement test và đánh giá CEFR theo nhiều kỹ năng; có cơ chế xét nâng cấp trình độ.
- Sổ tay lỗi sai từ bài học, quiz và hội thoại.
- IELTS: danh sách đề, phiên thi, kết quả và hỗ trợ AI chấm Writing/Speaking.
- Sáu mini-game có phiên chơi phía server và kiểm tra thời lượng nhằm hạn chế gian lận.
- Khu nội dung gồm tin tức, sách, podcast và YouTube; hỗ trợ quiz, phụ đề/dịch và ghi nhận thời gian học.
- Offline cache và hàng đợi đồng bộ lại khi có mạng.
- Giao diện đa ngôn ngữ; dự án hiện hướng tới iOS, Android, Web và desktop.

### 3.2 AI và luyện giao tiếp

- Lexi Chat dùng pipeline TRACE-CAG với knowledge graph KuzuDB, Redis cache và LangGraph.
- Cá nhân hóa phản hồi theo CEFR, learner card, lịch sử lỗi và mức độ thành thạo khái niệm.
- Topic Chat cho luyện hội thoại theo chủ đề và hỗ trợ phản hồi dạng streaming.
- Speech-to-Text bằng Whisper, Text-to-Speech bằng Piper/gTTS.
- Chấm phát âm ở mức phoneme bằng HuBERT và đưa kết quả vào kỹ năng speaking.
- Dịch từ/câu có cache.
- AI chấm IELTS, gợi ý nội dung, ranking insight và sinh nội dung thông báo.
- Có bộ benchmark và test riêng cho TRACE-CAG, retrieval, cache, knowledge graph, voice và provider routing.

### 3.3 Gamification và duy trì thói quen

- Cấp XP tập trung, giới hạn theo nguồn/ngày và chống ghi nhận trùng.
- Daily quest, streak, streak freeze, gem, ví, shop và inventory.
- Leaderboard theo tuần/league, thành tích và badge tự động.
- Theo dõi hoạt động học từ nội dung: số phiên, số phút, XP và lần hoạt động gần nhất.
- Follow/unfollow, feed, gợi ý bạn bè, người dùng gần đây và referral/deep link.

### 3.4 Backend và dữ liệu

- Hệ thống route bao phủ auth, user, course, learning, vocabulary, progress, proficiency, IELTS, games, XP, gamification, content, notifications, analytics, RBAC và monitoring.
- SQLAlchemy async, Alembic migration, PostgreSQL; Redis cho cache/session/rate limit và Celery cho tác vụ nền.
- API health/monitoring, AI audit, entitlement và các endpoint nội bộ giữa Backend với AI Service.
- Có dữ liệu seed, script tạo bảng/admin, kiểm tra CEFR và công cụ nhập/xuất nội dung.

### 3.5 Trang quản trị

- Dashboard tổng quan, biểu đồ tăng trưởng, tương tác, độ phổ biến khóa học và funnel hoàn thành.
- CRUD khóa học, unit, lesson, bài tập, từ vựng, topic và IELTS.
- Quản lý người dùng, admin, role/quyền truy cập và điều hướng theo vai trò.
- Quản lý achievements, shop, notification campaign và ranking agent.
- Content Lab, QA queue, content analytics, AI models, AI chat settings và AI quality dashboard.
- Monitoring, logs, database/system settings và xuất CSV.

### 3.6 Hạ tầng, vận hành và chất lượng

- Docker Compose cho local, development, validation và triển khai tách service.
- Kong/NGINX gateway, SSL, CORS, rate limit, cấu hình WAF/Cloudflare và fail2ban.
- Prometheus/Grafana, health check, smoke test và sentinel giám sát.
- Backup, restore, kiểm tra backup, cảnh báo và systemd timer.
- CI/CD, kiểm tra bảo mật, Dependabot, tự động đồng bộ bản dịch Crowdin.
- Số file test được tìm thấy: Backend 149, AI 152, Flutter 142, Admin 8 và MCP 5. Đây là số file, không phải kết quả pass/fail.

## 4. Hoàn thành một phần hoặc chưa bật mặc định

Các thành phần sau đã có mã nguồn nhưng chưa nên xem là sẵn sàng đầy đủ trên production nếu chưa xác nhận cấu hình triển khai:

| Hạng mục | Trạng thái hiện tại | Phần còn thiếu/cần xác nhận |
|---|---|---|
| Learner State + lịch ôn FSRS/delta-rule | Một phần | Luồng observation từ chat phụ thuộc `LEARNER_STATE_ENABLED`, mặc định đang tắt theo tài liệu kiểm kê |
| Practice Lab | Một phần | Luồng luyện kỹ năng đã có; một số thẻ như Writing còn đi qua Premium Gate |
| Premium/Entitlements | Một phần | UI Web fail-closed theo entitlement Backend và có `require_premium`; vẫn cần áp dụng dependency vào từng API premium khi chốt danh mục sản phẩm |
| Content Agent | Một phần | Có pipeline sinh course/unit/lesson bằng LLM; phụ thuộc `CONTENT_AGENT_ENABLED` |
| Content ETL | Một phần | Có pipeline từ các nguồn mở cho từ vựng/phát âm; phụ thuộc `CONTENT_ETL_ENABLED` và chưa tạo trọn bài học |
| Duplex Voice | Một phần | Ticket, readiness và quota đã có; phụ thuộc `VOICE_DUPLEX_ENABLED` |
| Reminders | Chưa hoạt động mặc định | API và Celery task đã có nhưng `REMINDERS_ENABLED` đang tắt |
| TRACE-CAG external/Ollama | Theo cấu hình | Phụ thuộc provider, model và các flag `TRACE_CAG_EXTERNAL_ENABLED`, `OLLAMA_ENABLED` |
| Banner/quảng cáo | Chưa hoàn chỉnh | Chưa có backend hoàn chỉnh; trang WIP đã được gỡ khỏi navigation admin theo báo cáo hiện có |

Giá trị feature flag cần được kiểm tra trên đúng môi trường chạy. File `.env.example` chỉ là mẫu và không chứng minh tính năng đang được bật thực tế.

## 5. Đang phát triển trong worktree hiện tại

Tại thời điểm lập tài liệu, Git đang có các thay đổi chưa commit sau:

### 5.1 AI Content Studio cho Admin

- Thêm endpoint admin sinh lesson từ `topic + CEFR + source text` bằng Gemini.
- Kết quả dự kiến gồm tiêu đề, mô tả, learning outcome, 5–10 từ vựng và 3 câu quiz.
- Nội dung được lưu theo cấu trúc Course → Unit → Lesson và VocabularyItem.
- Admin Content Lab có tab AI Lesson để nhập chủ đề, CEFR và source text, sau đó xem tóm tắt bản draft vừa tạo.
- Bổ sung cấu hình model/timeout, đăng ký router, kiểm tra schema đầu ra, rollback transaction và cập nhật counter danh mục.
- Trạng thái: đã harden trong worktree; nhóm test tập trung cho auth, provider, schema, rollback và persistence đã pass.

### 5.2 Đăng nhập Admin bằng email/mật khẩu

- Bổ sung form email/password bên cạnh Google Sign-In.
- Điều hướng theo role `super_admin` hoặc `admin` sau đăng nhập.
- Bỏ lỗi bắt buộc Google Client ID trong môi trường development.
- Trạng thái: đã bỏ credential mặc định, bổ sung autocomplete phù hợp; test và build Admin Web đã pass.

### 5.3 Hỗ trợ local development

- Điều chỉnh rate-limit middleware để sensitive route không fail-closed khi Redis lỗi trong development.
- Có thêm script tạo admin mặc định và script seed/kiểm tra dữ liệu CEFR chưa được Git theo dõi.
- Trạng thái: script từ chối production, không hardcode/hiển thị mật khẩu và không tự sửa tài khoản nếu người dùng không truyền rõ qua CLI.

## 6. Các khoảng trống và nợ kỹ thuật đáng chú ý

- Analytics session/course/lesson/vocabulary/retention đã dùng dữ liệu DB; vẫn cần kiểm chứng tải lớn và dữ liệu production-like.
- Badge hoàn thành nhanh và tương tác xã hội đã dùng dữ liệu thật từ thời lượng lesson và lượt follow. Các điều kiện còn thiếu nguồn dữ liệu là học sáng/đêm theo timezone, skill, chat và giúp người khác.
- Backend có fallback sinh bài tập placeholder khi lesson chưa có nội dung; cần bảo đảm dữ liệu production đầy đủ.
- Một số hiệu ứng item trong shop chưa có handler triển khai.
- Điểm chi tiết consonant/vowel trong HuBERT hiện còn phép ước lượng placeholder.
- Daily goal Home đã dùng tiến độ thật; cần tiếp tục kiểm thử browser với timezone và dữ liệu tuần biên.
- Cần tiếp tục dọn dead path/phiên bản cũ trong TRACE-CAG và đồng bộ tên model, tài liệu với runtime.
- Cần kiểm tra secret hygiene, xoay vòng khóa đã từng xuất hiện trong repo và dùng secret manager/env injection.
- Admin có ít file test hơn đáng kể so với ba khối chính; nên ưu tiên test cho auth, RBAC, Content Studio và các thao tác ghi dữ liệu.

## 7. Đánh giá mức độ sẵn sàng

| Khối | Đánh giá | Nhận xét |
|---|---|---|
| Learning core | Tốt | Đã vượt MVP, có đầy đủ luồng học, bài tập, tiến độ và CEFR |
| AI tutor | Tốt nhưng phụ thuộc hạ tầng | Nhiều năng lực đã có; cần model/provider, Redis/KuzuDB và feature flag đúng |
| Voice | Khá | STT/TTS/phát âm đã có; duplex realtime chưa bật mặc định |
| Gamification | Tốt | XP, quest, streak, shop, leaderboard và achievements đã được nối luồng |
| Content hub | Tốt | News, books, podcast, YouTube đã có đường dùng thật |
| Admin | Khá tốt | Phạm vi quản trị rộng; cần tăng test và hoàn thiện luồng mới |
| Production operations | Khá | Có gateway, monitoring, backup và runbook; vẫn cần xác minh thực tế theo môi trường |
| Security/readiness | Cần ưu tiên | Secret hygiene, cấu hình production và review thay đổi auth là các điểm quan trọng |

Kết luận: LexiLingo đã vượt mức MVP về độ rộng chức năng. Trọng tâm phù hợp tiếp theo là ổn định production, hoàn thiện các tính năng đang bị feature flag chặn, tăng kiểm thử tích hợp và xử lý nợ kỹ thuật thay vì tiếp tục mở rộng chức năng thiếu kiểm soát.

## 8. Ưu tiên phát triển đề xuất

1. Chạy browser test Flutter Web trên Chrome runner ổn định và smoke test các luồng auth/course/lesson/AI chat.
2. Chạy toàn bộ Backend suite với PostgreSQL/Redis test; xác nhận transaction Content Studio trên database thật.
3. Giảm bundle Admin Login và mở rộng test cho auth, RBAC cùng các thao tác ghi dữ liệu.
4. Hoàn thiện dữ liệu achievement còn placeholder và độ chính xác pronunciation metrics.
5. Chốt cấu hình production cho learner state, content agent, reminders và duplex voice; chỉ bật từng phần sau smoke test.
6. Hoàn thiện Premium Gate và entitlement trên các route cần thu phí.
7. Tiếp tục secret hygiene, rotate credential đã từng lộ và chuẩn hóa secret injection.
8. Benchmark AI, kiểm tra WebSocket voice/chat và backup/restore trước release tiếp theo.

## 9. Tài liệu liên quan

- `README.md`: giới thiệu và cách chạy toàn hệ thống.
- `docs/ARCHITECTURE.md`: kiến trúc chi tiết.
- `docs/Report/RPT-017_PROJECT_MASTER_REPORT.md`: báo cáo tổng thể theo từng service.
- `docs/Report/RPT-018_FEATURE_ANALYSIS.md`: bảng trạng thái tính năng chi tiết.
- `backend-service/FEATURES.md`: danh mục chức năng backend.
- `docs/operations/`: runbook deployment, security, backup và learner-state.
- `docs/qa/game-system-acceptance.md`: tiêu chí nghiệm thu games.

## 10. Quy ước cập nhật tài liệu này

Khi hoàn thành một tính năng, cần cập nhật đồng thời trạng thái, endpoint/client liên quan, feature flag và bằng chứng kiểm thử. Không đưa API key, token, mật khẩu, connection string hoặc nội dung thật từ `.env` vào tài liệu.
