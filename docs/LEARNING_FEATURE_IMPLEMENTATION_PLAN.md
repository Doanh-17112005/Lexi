# Learning Feature Implementation Plan

- Ngày lập kế hoạch: 2026-11-13.
- Nguồn: `docs/LEARNING_FEATURE_AUDIT.md`. Không tìm thấy `docs/STABILIZATION_CHECKLIST.md` tại thời điểm lập kế hoạch.
- Trạng thái gốc được giữ nguyên: **0 DONE · 7 PARTIAL · 2 MISSING**. Tài liệu này chỉ định nghĩa công việc và cổng nghiệm thu, không tự đổi trạng thái tính năng.
- Ngoài phạm vi: AI Learning Brain, Learn From Anything, English RPG, Boss Fight; không mở rộng sang refactor toàn hệ thống, redesign thương hiệu hay thay thuật toán học không cần thiết cho 9 tính năng.

## 1. Hiện trạng và cổng để đủ điều kiện đánh giá DONE

| # | Tính năng / trạng thái hiện tại | Phần đã có | Phần còn thiếu | Cổng nghiệm thu để có thể đánh giá DONE |
|---:|---|---|---|---|
| 1 | Grammar: học lý thuyết rồi luyện ngay — `PARTIAL` | `GrammarItem` và API quản trị; lesson exercises; endpoint lesson context có `grammar_points`; learning session và completion/progress đã có. | Learner API theory; liên kết theory với lesson/exercises; bước UI theory trước practice; persistence trạng thái đã xem; test chuỗi đầy đủ. | Một grammar lesson tải đúng theory, bắt đầu ở theory, chuyển ngay sang exercises, hoàn tất và ghi progress; refresh/resume không làm mất trạng thái; contract/widget/integration tests đạt. |
| 2 | Vocabulary Flashcard + luyện tương tác — `PARTIAL` | Flashcard, quiz hai chiều, speaking practice; due queue; submit review; FSRS/XP/persistence và test đơn vị liên quan. | Contract `tags` object/list đang lệch; test chưa dùng shape seed thật; chưa có bằng chứng E2E seed → card/quiz → persisted review. | Seed item thật được tải qua API/client; hoàn tất flashcard và quiz cập nhật next review, activity và XP đúng một lần; reload thấy trạng thái mới; error/retry không nhân đôi review. |
| 3 | Dashboard tiến độ — `PARTIAL` | Summary, course cards, weekly chart/bar/heatmap; backend đọc progress, completion, activity, streak. | Route `/course-detail` không được đăng ký; chưa có kiểm thử tích hợp lesson completion → dashboard. | Hoàn thành lesson làm đổi summary/weekly/course progress; chart render dữ liệu mới; course card mở đúng course; empty/error/retry được kiểm thử. |
| 4 | Guest Learning — `MISSING` | Welcome/auth shell; một số nội dung public; local cache và user scope `anonymous` có thể tái sử dụng. | Entry guest, trial catalog, guest identity/policy, local progress, hạn chế tính năng, chuyển đổi khi đăng ký. | Người chưa đăng nhập vào được trial pack, học ít nhất một lesson và một vocabulary session, đóng/mở lại vẫn có local progress; không truy cập dữ liệu user khác/premium; đăng ký xử lý tiến độ guest theo policy đã chọn. |
| 5 | Lưu lỗi và ôn lại — `PARTIAL` | Local/offline notebook, backend sync/dedup; capture ở games/news/books/chat; filter và mark-reviewed. | Capture chưa phủ course/vocabulary/placement; “review” chỉ là đánh dấu thủ công; chưa có retry/chấm lại/scheduling. | Sai ở mọi assessment trong phạm vi được lưu idempotent; từ notebook có thể làm lại; hệ thống chấm kết quả và chỉ đóng/re-schedule theo rule; sync/retry không tạo bản sao. |
| 6 | Vocabulary A1–C2 + chủ đề — `PARTIAL` | 180 mục, 30/cấp; level filter; topic cards; API level/tag; topic flashcard/quiz. | Seed CEFR chưa có canonical topic; tags contract lệch; client chỉ lấy 100 item; chưa kiểm thử level+topic trên dữ liệu thật. | Catalog tải đủ 180+ mục có phân trang; mỗi item phát hành có level và topic hợp lệ; filter level/topic/kết hợp trả đúng; mọi topic card mở được session có dữ liệu. |
| 7 | Grammar ba độ khó — `MISSING` | Grammar quiz theo CEFR/topic; question bank; lesson exercise có metadata difficulty 1–5. | Domain ba tier, mapping với CEFR, metadata dữ liệu, API filter, UI selector, persistence/result theo tier. | Người học chọn đúng Dễ/Trung bình/Khó; API chỉ trả câu đúng tier và CEFR phù hợp; session/result giữ tier; test chứng minh ba pool khác nhau và fallback không lẫn tier. |
| 8 | Lộ trình dạng chặng — `PARTIAL` | Roadmap unit/lesson zigzag; locked/current/completed; completion và course progress. | Lock chỉ xét trong unit; start API không enforce; `Lesson.prerequisites` chưa dùng chung; có thể bypass UI. | Roadmap và start API dùng cùng policy; unit sau khóa đúng; bypass bị từ chối; hoàn thành điều kiện mở đúng node kế tiếp sau refresh; test liên unit và prerequisite đặc biệt đạt. |
| 9 | Placement Test sáu kỹ năng — `PARTIAL` | UI 20 MCQ, timer, submit/result CEFR; bank có Vocabulary/Grammar/Reading; proficiency schemas đã định nghĩa sáu skill. | Listening/Speaking/Writing; item types media/free response; per-skill scoring; `skill_scores` persistence/UI; time/validation/security. | Một attempt hợp lệ đánh giá đủ sáu skill, lưu và hiển thị sáu điểm cùng assessed CEFR; media/upload/retry hoạt động; submit thiếu/giả mạo bị chặn; evaluator và E2E tests đạt. |

## 2. Phạm vi tối thiểu cho hai tính năng MISSING

### Guest Learning

MVP chỉ gồm:

1. Nút **Học thử** từ welcome; không tạo tài khoản ngầm và không yêu cầu token người dùng.
2. Trial pack versioned, read-only: tối thiểu một lesson Grammar có theory + practice và một bộ Vocabulary có flashcard + quiz; không mở toàn catalog/premium/social/leaderboard.
3. Guest scope cục bộ riêng cho progress, answers và mistakes; dữ liệu không gửi vào user endpoint khi chưa xác thực.
4. Banner/CTA đăng ký rõ ràng; khi đăng ký, áp dụng một policy duy nhất: migrate idempotent hoặc giữ trial chỉ cục bộ rồi xóa có xác nhận.
5. Offline/relaunch giữ được trial state; logout/account switch không làm rò dữ liệu giữa guest và user.

Không nằm trong MVP: đồng bộ guest đa thiết bị, thanh toán guest, ranking guest, recommendation cá nhân hóa hoặc AI tutor.

### Grammar ba độ khó

MVP chỉ gồm:

1. Enum ổn định `easy | medium | hard` với nhãn Dễ/Trung bình/Khó; tier độc lập với CEFR nhưng mỗi câu vẫn mang CEFR.
2. Quy tắc ánh xạ được version hóa và document: dùng metadata câu hỏi làm nguồn quyết định; không suy ra chỉ từ CEFR ở runtime.
3. Question bank có đủ số câu tối thiểu cho mỗi tier được hỗ trợ; API nhận/validate `difficulty`, không fallback âm thầm sang tier khác.
4. Selector ba mức trong Grammar Quiz, giữ tier trong session snapshot/result và analytics; không đổi nhãn CEFR thành “difficulty”.

Không nằm trong MVP: adaptive difficulty, AI sinh câu hỏi, boss levels hoặc RPG progression.

## 3. Thứ tự triển khai

Thứ tự dưới đây tối ưu dependency và khả năng tái sử dụng; không phải thứ tự giá trị kinh doanh thuần túy.

| Thứ tự | Tính năng | Ưu tiên | Phụ thuộc / lý do |
|---:|---|---|---|
| 1 | #6 Vocabulary A1–C2 + chủ đề | P0 | Sửa contract tags, pagination và taxonomy là nền dữ liệu cho cả thư viện, flashcard, quiz và guest trial. |
| 2 | #2 Vocabulary Flashcard + luyện tương tác | P0 | Tái sử dụng catalog đã chuẩn hóa; tạo một vertical slice học tập hoàn chỉnh sớm. |
| 3 | #3 Dashboard tiến độ | P0 | Quick win, ảnh hưởng trực tiếp khả năng nhìn thấy thành quả; ít phụ thuộc và giúp quan sát các luồng sau. |
| 4 | #8 Lộ trình dạng chặng | P0 | Là correctness/security gate cho lesson; phải ổn định trước Grammar flow và Guest trial. |
| 5 | #1 Grammar theory → practice | P1 | Dùng learning session, lesson progress và unlock policy đã ổn định. |
| 6 | #5 Lưu lỗi và ôn lại | P1 | Cần các answer contracts của Vocabulary/Grammar ổn định; sau đó cung cấp capture/retry dùng lại cho Placement. |
| 7 | #7 Grammar ba độ khó | P1 | Tái sử dụng grammar content/quiz contract vừa hoàn thiện; phạm vi nhỏ hơn Guest/Placement. |
| 8 | #4 Guest Learning | P1 | Ảnh hưởng acquisition cao nhưng cross-cutting auth/data isolation; triển khai sau khi trial content thực sự hoàn chỉnh. |
| 9 | #9 Placement Test sáu kỹ năng | P2 | Phạm vi lớn và rủi ro nhất; tái sử dụng voice UI, scoring, mistake capture và progress/profile đã ổn định. |

## 4. Backlog theo task

### Phase A — Vocabulary foundation và learning loop (#6, #2)

| ID | Task nhỏ | Tiêu chí nghiệm thu | Test cần thực hiện |
|---|---|---|---|
| T01 — `IMPLEMENTED` (2026-11-13; không đổi trạng thái feature) | Chuẩn hóa contract `tags` giữa DB → Pydantic → Flutter: giữ nguyên `PortableJSON`, API xuất canonical `List<String>`, client vẫn đọc object/list/null legacy. Bằng chứng: `backend-service/app/{models/vocabulary.py,services/vocabulary_catalog_policy.py,schemas/vocabulary.py,routes/vocabulary.py}` và `flutter-app/lib/features/vocabulary/{data/models/vocabulary_tags.dart,data/models/vocabulary_item_model.dart,presentation/providers/vocab_provider.dart}`. | Seed object và item list/null đều serialize an toàn; giữ giá trị source/topic/QA; không migration hay ghi lại dữ liệu. | Backend Vocabulary: 86 passed; Flutter model/data-source: 5 passed; Flutter analyze 5 file: PASS; Ruff critical rules: PASS. Configured Ruff scoped run còn 225 lỗi baseline có sẵn trong các file legacy, không sửa ngoài T01. |
| T02 | Phân trang master catalog trong Flutter thay vì cố định 100 item; giữ merge/dedup ổn định. | Thư viện tải đủ 180 seed, không lặp headword, refresh không nhân bản; lỗi page giữa chừng có retry rõ ràng. | Provider/repository tests cho 2+ pages, page cuối, duplicate và failure; backend offset/limit route test. |
| T03 | Định nghĩa canonical topic taxonomy và gắn topic cho catalog phát hành; sửa filter level/tag dùng cùng normalizer. | Mỗi item dùng trong system topic có ít nhất một topic hợp lệ; sáu topic UI đều có dữ liệu; level-only, topic-only và kết hợp trả đúng. | Catalog policy/seed regression; CRUD filter tests; Flutter topic-card/provider tests với dữ liệu thật tương đương seed. |
| T04 | Khóa vertical slice flashcard + quiz trên seed thật, gồm idempotent review/XP/next-review và retry. | Một item được học qua hai mode; mỗi mode submit đúng một review/word theo rule; reload phản ánh schedule mới; network retry không nhân đôi XP/review. | Backend vocabulary integration/isolation tests; Flutter flashcard/quiz provider + screen tests; một integration test API seed → due → review → stats. |

### Phase B — Dashboard (#3)

| ID | Task nhỏ | Tiêu chí nghiệm thu | Test cần thực hiện |
|---|---|---|---|
| T05 | Sửa course progress card navigation bằng route/type-safe navigation hiện có. | Tap card mở đúng `CourseDetailScreen` và đúng course ID; back navigation giữ dashboard state. | Widget navigation test cho có/không có course; Flutter analyze phần route/screen. |
| T06 | Khóa pipeline lesson completion → summary/weekly/course chart và các state tải lỗi/rỗng. | Một completion hợp lệ đổi đúng XP, lessons, course %, daily activity một lần; refresh UI hiển thị dữ liệu mới. | Backend progress/learning integration tests; Flutter progress model/provider/chart widget tests; test retry và zero-data. |

### Phase C — Roadmap gate (#8)

| ID | Task nhỏ | Tiêu chí nghiệm thu | Test cần thực hiện |
|---|---|---|---|
| T07 | Tạo một unlock-policy service thuần dùng order, previous unit và `Lesson.prerequisites`. | Cùng input cho cùng kết quả; có rule rõ cho first lesson, previous lesson, previous unit, explicit prerequisites và replay completed lesson. | Unit tests ma trận khóa/mở, course rỗng, lesson không playable và prerequisite thiếu. |
| T08 | Dùng policy chung trong roadmap và `start_lesson`; trả lỗi domain nhất quán khi bị khóa. | UI/API không bất đồng; gọi trực tiếp lesson khóa bị từ chối; completed lesson vẫn replay theo policy. | Route tests roadmap + start; concurrency/idempotency test completion mở bài kế; security test cross-user progress. |
| T09 | Hoàn thiện UI locked/current/unlock refresh và thông báo điều kiện mở. | Node khóa không mở session; sau completion quay lại roadmap thấy đúng node mới mà không restart app; người học biết điều kiện còn thiếu. | Roadmap model/provider/widget navigation tests; golden/widget test các trạng thái chính. |

### Phase D — Grammar theory → practice (#1)

| ID | Task nhỏ | Tiêu chí nghiệm thu | Test cần thực hiện |
|---|---|---|---|
| T10 | Thiết kế learner grammar contract và liên kết lesson → grammar item/version; không tái sử dụng admin response trực tiếp. | API lesson trả theory đã sanitize, examples và linked exercise IDs; không lộ answer trước practice; thiếu theory trả lỗi nội dung có thể chẩn đoán. | Schema/route/sanitization tests; migration/seed integrity test cho link và version. |
| T11 | Thêm learning-session phase `theory` trước `practice`, hỗ trợ resume và accessibility/loading/error. | Grammar lesson luôn bắt đầu theory; CTA chuyển sang bài tập cùng lesson; quay lại/resume đúng phase; lesson không phải grammar không bị đổi hành vi. | Provider state-machine unit tests; widget tests theory → practice, resume, error, back/exit. |
| T12 | Ghi theory-view/practice completion và nối progress/roadmap mà không nhân đôi XP. | Chỉ lesson practice đạt pass threshold mới complete; theory viewed được lưu riêng; retry/replay không cấp thưởng lặp. | Backend completion/idempotency tests; Flutter integration flow; regression learning/progress/roadmap. |

### Phase E — Mistake review loop (#5)

| ID | Task nhỏ | Tiêu chí nghiệm thu | Test cần thực hiện |
|---|---|---|---|
| T13 | Chuẩn hóa `MistakeCapture` contract/service dùng chung: source, skill, prompt, selected/correct answer, explanation, stable idempotency key. | Các nguồn cùng tạo payload hợp lệ; cùng attempt retry không tạo duplicate; attempt mới tăng counter/reopen theo rule. | Domain serialization/unit tests; backend upsert/dedup/isolation tests; offline queue tests. |
| T14 | Nối capture vào course lesson, vocabulary quiz và các game còn thiếu; Placement nối sau trong Phase H. | Mọi câu chấm sai trong phạm vi tạo entry; câu đúng không tạo; lỗi sync không làm fail phiên học. | Provider/widget tests từng nguồn; backend route tests; regression news/books/chat recorder. |
| T15 | Thêm review session từ notebook và rule chấm/đóng/re-schedule thay cho mark-reviewed thủ công. | Người học làm lại câu; đúng thì reviewed theo rule, sai thì giữ/reopen và tăng attempt; reload/sync giữ trạng thái. | State-machine/widget tests; backend review/reopen tests; E2E sai → notebook → retry → sync. |

### Phase F — Grammar ba độ khó (#7)

| ID | Task nhỏ | Tiêu chí nghiệm thu | Test cần thực hiện |
|---|---|---|---|
| T16 | Thêm domain enum/versioned metadata `easy|medium|hard`; document quan hệ với CEFR. | Schema validate đúng ba giá trị; dữ liệu cũ có migration/default được phê duyệt; tier không thay thế CEFR. | Schema/model/migration tests; invalid value tests; data audit đếm câu theo tier và CEFR. |
| T17 | Annotate/bổ sung grammar question bank và filter API không fallback chéo tier. | Mỗi tier được hỗ trợ có đủ pool tối thiểu; response/session snapshot chứa tier yêu cầu; pool thiếu trả lỗi rõ. | Selection tests theo tier/topic/CEFR/count; randomness invariant; no-cross-tier regression. |
| T18 | Thêm selector ba mức vào Grammar Quiz và lưu tier qua resume/result. | Nhãn đúng Dễ/Trung bình/Khó; chọn tier quyết định request; resume giữ tier; result hiển thị tier. | Provider/repository/widget tests; localization tests; game session resume/integration tests. |

### Phase G — Guest Learning MVP (#4)

| ID | Task nhỏ | Tiêu chí nghiệm thu | Test cần thực hiện |
|---|---|---|---|
| T19 | Chốt guest policy và trial-pack manifest versioned dùng nội dung đã nghiệm thu từ Vocabulary/Grammar. | Manifest không chứa premium/answer leak; version và content IDs ổn định; không phụ thuộc user DB. | Manifest/schema tests; content integrity và answer-sanitization tests. |
| T20 | Thêm entry “Học thử”, guest session/scope và local persistence tách user. | Không token vẫn vào trial; relaunch khôi phục; login/logout/account switch không đọc nhầm guest data. | Auth-wrapper/widget tests; storage scope/isolation tests; deep-link/back navigation tests. |
| T21 | Cho guest chạy lesson, flashcard, quiz và local mistake/progress với feature gates. | Trial hoàn tất offline/local; endpoint yêu cầu auth không bị gọi; premium/social/leaderboard bị chặn có CTA. | Guest flow integration tests online/offline; network spy assertions; feature-gate tests. |
| T22 | Thực hiện conversion policy guest → account và cleanup/retry idempotent. | Migration/decline chỉ chạy một lần, không nhân XP/review; lỗi giữa chừng có thể retry; người dùng được thông báo. | Conversion unit/integration tests, duplicate/retry/account-isolation/security tests. |

### Phase H — Placement Test sáu kỹ năng (#9)

| ID | Task nhỏ | Tiêu chí nghiệm thu | Test cần thực hiện |
|---|---|---|---|
| T23 | Định nghĩa assessment blueprint/version: sáu section, item types, weights, timing, completion rules và per-skill score schema. | Server cấp attempt/version; không gửi answer/rubric bí mật; submission gắn attempt và item IDs; profile/test record lưu đủ sáu skill. | Schema/scoring unit tests; attempt lifecycle, expired/replay/tamper tests; migration tests. |
| T24 | Chuyển ba section hiện có Vocabulary/Grammar/Reading sang attempt blueprint và item IDs phía server. | Ba section giữ hành vi hiện tại nhưng dùng attempt/version mới; client không nhận correct answer; resume không đổi bộ câu. | Migration/route/provider tests; answer-leak và resume-order regression. |
| T25 | Xây Listening section bằng item bank và media đã kiểm duyệt. | Audio tải/phát lại theo policy; câu hỏi chấm phía server; timeout, media lỗi và accessibility có trạng thái rõ. | Item/media validation; signed/public URL tests; Flutter audio widget, permission, timeout và error tests. |
| T26 | Xây Speaking section bằng recorder hiện có và evaluator interface giới hạn cho placement. | Thu/upload/retry được; evaluator trả score/rubric/version; không dùng transcript client để tự chấm; failure không mất attempt. | Recorder/upload tests; evaluator contract tests; permission/timeout/invalid media/security tests. |
| T27 | Xây Writing section với free response, rubric/version và evaluator xác định; không mở rộng thành AI Learning Brain. | Lưu response nguyên bản; trả score theo rubric có audit metadata; giới hạn độ dài/ngôn ngữ; retry policy rõ. | Validation/rubric tests; evaluator contract/golden fixtures; injection/oversize/timeout tests. |
| T28 | Tổng hợp weighted per-skill scores, CEFR và result breakdown UI; ghi profile/history idempotent. | Result có sáu điểm, overall và assessed level; UI hiển thị từng skill; submit lại không tạo assessment/level change trùng. | Scoring boundary tests; persistence/idempotency tests; result/provider/widget tests. |
| T29 | Nối mistake capture phù hợp, telemetry tối thiểu và E2E toàn bộ placement. | Sai MCQ có thể vào notebook theo policy; free-response không lưu dữ liệu nhạy cảm ngoài phạm vi; attempt đủ/thiếu/tamper xử lý đúng. | End-to-end sáu section; authorization/isolation/rate-limit tests; targeted backend suite + Flutter analyze/test cho module. |

## 5. Quy tắc thực thi và nghiệm thu chung

1. Mỗi task là một thay đổi độc lập, có migration tương thích ngược nếu đổi schema; không gộp task kế tiếp khi task trước chưa đạt test mục tiêu.
2. Không dùng UI mock hoặc demo fallback làm bằng chứng nghiệm thu production; test phải dùng contract và shape dữ liệu seed/DB thực tế tương đương.
3. Mọi API ghi dữ liệu cần authorization, ownership, idempotency và error contract; mọi client flow cần loading/empty/error/retry.
4. Chỉ chạy targeted tests/lint trong từng task khi triển khai; full regression là cổng release riêng, không thuộc phiên lập kế hoạch này.
5. Sau khi hoàn thành toàn bộ task của một tính năng, thực hiện audit độc lập lại chuỗi frontend → backend → dữ liệu → persistence → UI trước khi cân nhắc đổi trạng thái; không tự động gán `DONE`.

