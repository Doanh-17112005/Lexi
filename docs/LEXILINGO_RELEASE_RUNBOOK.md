# LexiLingo — Local RC Startup & Internet Deployment Runbook

- **Updated**: 2026-11-18 (+07)
- **Scope**: Runbook khởi động bản Release Candidate local (`Windows / Docker`) và chuẩn bị cấu hình triển khai Internet Web-first (**không tự ý deploy, tạo cloud resource hay bật billing**).

---

## 1. Local Release Candidate Startup & Health Check

### 1.1 Infrastructure (Docker)
Đảm bảo 4 container khỏe mạnh:
- `lexilingo-postgres` (`:5432`, DB `lexilingo`)
- `lexilingo-redis` (`:6379`)
- `lexilingo-mongodb` (`:27017`)
- `learnflow_postgres` (`:5433`, nếu chạy kèm service phụ)

Kiểm tra nhanh:
```powershell
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

### 1.2 Backend FastAPI (`:8000`)
```powershell
cd D:\LexiLingo\LexiLingo\backend-service
.\venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### 1.3 AI Service (`:8001`)
```powershell
cd D:\LexiLingo\LexiLingo\ai-service
.\.venv\Scripts\python.exe -m uvicorn api.main:app --host 127.0.0.1 --port 8001
```
*(Khi chạy pytest song song với process `:8001` đang bật, truyền `KUZU_DB_PATH` trỏ tới thư mục tạm cô lập để không đụng snapshot lock của Kuzu.)*

### 1.4 Flutter Web Learner (`:5174`)
```powershell
cd D:\LexiLingo\LexiLingo\flutter-app
flutter run -d web-server --web-hostname 127.0.0.1 --web-port 5174
```

### 1.5 React Admin Console (`:5173`)
```powershell
cd D:\LexiLingo\LexiLingo\admin-service
pnpm run dev -- --host 127.0.0.1 --port 5173
```

### 1.6 Endpoint Health Verification
- `http://127.0.0.1:8000/health` → `200`
- `http://127.0.0.1:8001/health` → `200`
- `http://127.0.0.1:5174/` → `200`
- `http://127.0.0.1:5173/` → `200`

---

## 2. Production Release Config & Build Verification

### 2.1 URL Routing & Dev/Release Parity
- **Flutter (`flutter-app/lib/core/network/api_config.dart`)**:
  - Trên loopback web (`127.0.0.1`/`localhost`) tự trỏ `AppConstants.localApiBaseUrl` (`:8000`) & `localAiServiceUrl` (`:8001`).
  - Trong bản release trên domain production (`_mustUseProductionBackend`), chặn loopback URL và trỏ mặc định về `https://api.lexilingo.me/api/v1` (hoặc giá trị cấu hình non-loopback `API_BASE_URL` / `AI_SERVICE_URL`).
  - Lệnh build release Web sau khi duyệt deploy:
    ```powershell
    cd D:\LexiLingo\LexiLingo\flutter-app
    flutter build web --release
    ```
- **React Admin (`admin-service/src/lib/env.ts` & `src/main.tsx`)**:
  - Default API URL là `https://api.lexilingo.me/api/v1`; dev dùng `.env` local.
  - `@vercel/analytics` chỉ kích hoạt trong `import.meta.env.PROD`, tránh lỗi CSP trên local dev.
  - Lệnh build kiểm tra TypeScript + CSS + bundle:
    ```powershell
    cd D:\LexiLingo\LexiLingo\admin-service
    pnpm run build:check
    ```

### 2.2 Backend & AI Service Production Checklist (Bắt buộc trước deploy Internet)
1. **Backend (`backend-service/.env.production`)**:
   - Đặt `APP_ENV=production`, `DEBUG=False`, `DEV_AUTO_VERIFY_EMAIL=False`.
   - Sinh `SECRET_KEY` ngẫu nhiên đủ entropy (`>= 32 bytes`), không dùng khóa dev.
   - Giới hạn `ALLOWED_ORIGINS` & `ALLOWED_HOSTS` đúng domain thực (`lexilingo.me`, `admin.lexilingo.me`, `api.lexilingo.me`) — đặt `GATEWAY_HANDLES_CORS=true` nếu Nginx/Kong đứng trước để tránh trùng header CORS.
   - Bật HTTPS termination & `HSTS`, kiểm tra Redis persistence & rate-limit fail-closed (`TokenBlacklist`).
2. **AI Service (`ai-service/.env`)**:
   - Điền ít nhất 1 provider key thật (`GEMINI_API_KEY` hoặc `GROQ_API_KEY`) hoặc endpoint Ollama bảo mật.
   - Đặt `KUZU_DB_PATH` ổn định theo volume persistence cho 1 worker hoặc tách đường dẫn theo worker.
3. **Dependency Security Upgrade (khuyến nghị trước Release)**:
   - Tại `admin-service`, `pnpm audit --prod` phát hiện `4` high advisories ở transitive/direct deps (`follow-redirects <= 1.16.1` cần `>= 1.16.2`, `zod < 4.6.6` cần `>= 4.6.6`). Chạy `pnpm update zod axios follow-redirects` rồi chạy lại `pnpm test && pnpm run build:check`.

---

## 3. Data Backup & User-Approved Seed Sequence

> **Không chạy tự động khi chưa có phê duyệt**. Thực hiện theo đúng thứ tự:

1. **Backup PostgreSQL**:
   ```powershell
   docker exec lexilingo-postgres pg_dump -U postgres -d lexilingo > D:\LexiLingo\LexiLingo\.tmp\lexilingo_backup.sql
   ```
2. **Backfill Achievements (`48` bản ghi, idempotent)**:
   ```powershell
   cd D:\LexiLingo\LexiLingo\backend-service
   .\venv\Scripts\python.exe -m scripts.backfill_achievements
   ```
3. **Seed 180 Từ vựng CEFR & Topic Taxonomy (`6` topics, giữ nguyên `15` từ hiện có)**:
   ```powershell
   cd D:\LexiLingo\LexiLingo\backend-service
   .\venv\Scripts\python.exe seed_and_test_cefr_a1_c2.py
   ```
4. **Xóa chọn lọc cache từ vựng trên Redis (không dùng `FLUSHALL`/`FLUSHDB`)**:
   ```powershell
   cd D:\LexiLingo\LexiLingo\backend-service
   .\venv\Scripts\python.exe -c "import asyncio; from app.core.redis import RedisClient; asyncio.run(RedisClient.delete_pattern('vocab_items:*'))"
   ```
