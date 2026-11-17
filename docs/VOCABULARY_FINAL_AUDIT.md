# Vocabulary QA Final Audit

- Ngày tổng hợp: 2026-11-12.
- Phạm vi: tổng hợp 180/180 mục từ bằng chứng đã lưu trong `docs/VOCABULARY_QA.md`; không tra cứu lại từng từ, không sửa seed và không chạy full test.
- Cách phân loại: `CONFIRMED_SOURCE` nghĩa là bằng chứng đã lưu hỗ trợ đúng nghĩa/cách dùng và cấp mục tiêu; `CONFLICT` là nguồn Cambridge/Oxford (hoặc EVP được ghi rõ) cho cấp khác nhau; `BLOCKED` là chưa có nguồn trực tiếp đủ mạnh để xác nhận CEFR theo nghĩa. Cả ba nhóm vẫn là `NEEDS_REVIEW`, không đồng nghĩa `VERIFIED`.
- Khi Cambridge xác nhận nghĩa còn Oxford chỉ gắn cấp headword/từ loại, chênh lệch vẫn được giữ là `CONFLICT`; không dùng nhãn headword để tự quyết định cấp của mọi nghĩa.

## 1. Thống kê cuối

| CEFR | Đã đối chiếu | `CONFIRMED_SOURCE` | `CONFLICT` | `BLOCKED` | Sửa nội dung | Thay headword | Slot đã sửa/thay |
|---|---:|---:|---:|---:|---:|---:|---:|
| A1 | 30 | 30 | 0 | 0 | 1 | 0 | 1 |
| A2 | 30 | 14 | 16 | 0 | 1 | 6 | 7 |
| B1 | 30 | 9 | 21 | 0 | 5 | 6 | 11 |
| B2 | 30 | 15 | 15 | 0 | 3 | 3 | 6 |
| C1 | 30 | 12 | 14 | 4 | 6 | 7 | 13 |
| C2 | 30 | 1 | 0 | 29 | 9 | 1 | 10 |
| **Tổng** | **180** | **81** | **66** | **33** | **25** | **23** | **48** |

Ba cột `CONFIRMED_SOURCE`/`CONFLICT`/`BLOCKED` loại trừ lẫn nhau và cộng thành tổng mục của từng cấp. Cột sửa/thay là lịch sử thay đổi slot đã ghi trong QA, độc lập với phân loại bằng chứng hiện tại.

Các slot đã thay/sửa:

- A1: sửa `bad`.
- A2: thay `different` → `accident`, `difficult` → `adventure`, `message` → `advertisement`, `weather` → `airport`, `delicious` → `almost`, `choose` → `receive`; sửa `already`.
- B1: thay `advice` → `achievement`, `community` → `communication`, `confidence` → `confident`, `available` → `application`, `describe` → `afford`, `prefer` → `announce`; sửa `behaviour`, `relationship`, `independent`, `avoid`, `develop`.
- B2: thay `collaborate` → `beneficial`, `issue` → `crucial`, `reliable` → `adequate`; sửa `contribute`, `demonstrate`, `establish`.
- C1: thay `ambiguity` → `corruption`, `coherence` → `counterpart`, `discrepancy` → `comparable`, `intrinsic` → `allegation`, `arbitrary` → `reluctant`, `infer` → `enforce`, `substantiate` → `eligible`; sửa `articulate`, `implication`, `innovation`, `compelling`, `profound`, `reinforce`.
- C2: thay `fastidious` → `meticulous`; sửa `anachronism`, `equivocal`, `ineffable`, `obfuscate`, `parsimonious`, `pernicious`, `sycophant`, `vitriolic`, `perspicacious`.

## 2. Danh sách `CONFLICT` còn tồn đọng

Các URL dưới đây là URL đã lưu trong báo cáo QA. `[O3]` là [Oxford 3000 PDF](https://www.oxfordlearnersdictionaries.com/external/pdf/wordlists/oxford-3000-5000/The_Oxford_3000.pdf), `[O5]` là [Oxford 5000 PDF](https://www.oxfordlearnersdictionaries.com/external/pdf/wordlists/oxford-3000-5000/The_Oxford_5000.pdf). Nhãn Oxford là cấp headword/từ loại, còn nhãn Cambridge trong bảng là cấp nghĩa đã ghi nhận.

### A2 — 16 mục

| Headword | Lý do và nguồn đã lưu |
|---|---|
| [`journey`](https://dictionary.cambridge.org/dictionary/english/journey) | Cambridge nghĩa TRIP A2; [O3](https://www.oxfordlearnersdictionaries.com/external/pdf/wordlists/oxford-3000-5000/The_Oxford_3000.pdf) A1. |
| [`arrive`](https://dictionary.cambridge.org/dictionary/english/arrive) | Cambridge nghĩa REACH A2; [O3](https://www.oxfordlearnersdictionaries.com/external/pdf/wordlists/oxford-3000-5000/The_Oxford_3000.pdf) A1. |
| [`decide`](https://dictionary.cambridge.org/dictionary/english/decide) | Cambridge nghĩa chọn sau cân nhắc A2; [O3](https://www.oxfordlearnersdictionaries.com/external/pdf/wordlists/oxford-3000-5000/The_Oxford_3000.pdf) A1. |
| [`market`](https://dictionary.cambridge.org/dictionary/english/market) | Cambridge nghĩa PLACE A2; [O3](https://www.oxfordlearnersdictionaries.com/external/pdf/wordlists/oxford-3000-5000/The_Oxford_3000.pdf) A1. |
| [`neighbour`](https://dictionary.cambridge.org/dictionary/learner-english/neighbor) | Cambridge Learner nghĩa người sống gần A2; [O3](https://www.oxfordlearnersdictionaries.com/external/pdf/wordlists/oxford-3000-5000/The_Oxford_3000.pdf) A1. |
| [`prepare`](https://dictionary.cambridge.org/dictionary/learner-english/prepare) | Cambridge Learner nghĩa làm đồ/thức ăn sẵn sàng A2; [O3](https://www.oxfordlearnersdictionaries.com/external/pdf/wordlists/oxford-3000-5000/The_Oxford_3000.pdf) A1. |
| [`return`](https://dictionary.cambridge.org/dictionary/english/return) | Cambridge verb nghĩa quay lại nơi chốn A2; [O3](https://www.oxfordlearnersdictionaries.com/external/pdf/wordlists/oxford-3000-5000/The_Oxford_3000.pdf) A1. |
| [`suddenly`](https://dictionary.cambridge.org/dictionary/learner-english/suddenly) | Cambridge Learner B1; [O3](https://www.oxfordlearnersdictionaries.com/external/pdf/wordlists/oxford-3000-5000/The_Oxford_3000.pdf) và [EVP](https://www.englishprofile.org/) A2. |
| [`afraid`](https://dictionary.cambridge.org/dictionary/english/afraid) | Cambridge nghĩa cảm thấy sợ/lo A2; [O3](https://www.oxfordlearnersdictionaries.com/external/pdf/wordlists/oxford-3000-5000/The_Oxford_3000.pdf) A1. |
| [`friendly`](https://dictionary.cambridge.org/dictionary/english/friendly) | Cambridge nghĩa cư xử tử tế/dễ mến A2; [O3](https://www.oxfordlearnersdictionaries.com/external/pdf/wordlists/oxford-3000-5000/The_Oxford_3000.pdf) A1. |
| [`healthy`](https://dictionary.cambridge.org/dictionary/english/healthy) | Cambridge nghĩa tốt cho sức khỏe A2; [O3](https://www.oxfordlearnersdictionaries.com/external/pdf/wordlists/oxford-3000-5000/The_Oxford_3000.pdf) A1. |
| [`quickly`](https://dictionary.cambridge.org/dictionary/english/quickly) | Cambridge nghĩa tốc độ/thời gian ngắn A2; [O3](https://www.oxfordlearnersdictionaries.com/external/pdf/wordlists/oxford-3000-5000/The_Oxford_3000.pdf) A1. |
| [`during`](https://dictionary.cambridge.org/dictionary/english/during) | Cambridge hai nghĩa thời gian A2; [O3](https://www.oxfordlearnersdictionaries.com/external/pdf/wordlists/oxford-3000-5000/The_Oxford_3000.pdf) A1. |
| [`without`](https://dictionary.cambridge.org/dictionary/english/without) | Cambridge nghĩa không có/không làm A2; [O3](https://www.oxfordlearnersdictionaries.com/external/pdf/wordlists/oxford-3000-5000/The_Oxford_3000.pdf) A1. |
| [`explain`](https://dictionary.cambridge.org/dictionary/english/explain) | Cambridge nghĩa làm rõ/dễ hiểu A2; [O3](https://www.oxfordlearnersdictionaries.com/external/pdf/wordlists/oxford-3000-5000/The_Oxford_3000.pdf) A1. |
| [`promise`](https://dictionary.cambridge.org/dictionary/english/promise) | Cambridge nghĩa SAY CERTAINLY B1; [O3](https://www.oxfordlearnersdictionaries.com/external/pdf/wordlists/oxford-3000-5000/The_Oxford_3000.pdf) A2. |

### B1 — 21 mục

| Headword | Lý do và nguồn đã lưu |
|---|---|
| [`opportunity`](https://dictionary.cambridge.org/dictionary/english/opportunity) | Cambridge B1; [O3](https://www.oxfordlearnersdictionaries.com/external/pdf/wordlists/oxford-3000-5000/The_Oxford_3000.pdf) A2. |
| [`achieve`](https://dictionary.cambridge.org/dictionary/english/achieve) | Cambridge B1; [O3](https://www.oxfordlearnersdictionaries.com/external/pdf/wordlists/oxford-3000-5000/The_Oxford_3000.pdf) A2. |
| [`behaviour`](https://dictionary.cambridge.org/dictionary/english/behaviour) | Cambridge nghĩa cách một người cư xử B1; [O3](https://www.oxfordlearnersdictionaries.com/external/pdf/wordlists/oxford-3000-5000/The_Oxford_3000.pdf) A2. |
| [`decision`](https://dictionary.cambridge.org/dictionary/learner-english/decision) | Cambridge Learner B1; [O3](https://www.oxfordlearnersdictionaries.com/external/pdf/wordlists/oxford-3000-5000/The_Oxford_3000.pdf) A2. |
| [`experience`](https://dictionary.cambridge.org/dictionary/english/experience) | Cambridge nghĩa kiến thức/kỹ năng B1; [O3](https://www.oxfordlearnersdictionaries.com/external/pdf/wordlists/oxford-3000-5000/The_Oxford_3000.pdf) A2. |
| [`goal`](https://dictionary.cambridge.org/dictionary/english/goal) | Cambridge nghĩa AIM B1; [O3](https://www.oxfordlearnersdictionaries.com/external/pdf/wordlists/oxford-3000-5000/The_Oxford_3000.pdf) A2. |
| [`habit`](https://dictionary.cambridge.org/dictionary/english/habit) | Cambridge B1; [O3](https://www.oxfordlearnersdictionaries.com/external/pdf/wordlists/oxford-3000-5000/The_Oxford_3000.pdf) A2. |
| [`knowledge`](https://dictionary.cambridge.org/dictionary/english/knowledge) | Cambridge B1; [O3](https://www.oxfordlearnersdictionaries.com/external/pdf/wordlists/oxford-3000-5000/The_Oxford_3000.pdf) A2. |
| [`opinion`](https://dictionary.cambridge.org/dictionary/english/opinion) | Cambridge B1; [O3](https://www.oxfordlearnersdictionaries.com/external/pdf/wordlists/oxford-3000-5000/The_Oxford_3000.pdf) A1. |
| [`relationship`](https://dictionary.cambridge.org/dictionary/english/relationship) | Cambridge nghĩa quan hệ giữa người B1; [O3](https://www.oxfordlearnersdictionaries.com/external/pdf/wordlists/oxford-3000-5000/The_Oxford_3000.pdf) A2. |
| [`solution`](https://dictionary.cambridge.org/dictionary/english/solution) | Cambridge B1; [O3](https://www.oxfordlearnersdictionaries.com/external/pdf/wordlists/oxford-3000-5000/The_Oxford_3000.pdf) A2. |
| [`advantage`](https://dictionary.cambridge.org/dictionary/english/advantage) | Cambridge B1; [O3](https://www.oxfordlearnersdictionaries.com/external/pdf/wordlists/oxford-3000-5000/The_Oxford_3000.pdf) A2. |
| [`independent`](https://dictionary.cambridge.org/dictionary/english/independent) | Cambridge nghĩa tự lập/không nhận trợ giúp B1; [O3](https://www.oxfordlearnersdictionaries.com/external/pdf/wordlists/oxford-3000-5000/The_Oxford_3000.pdf) A2. |
| [`likely`](https://dictionary.cambridge.org/dictionary/english/likely) | Cambridge B1; [O3](https://www.oxfordlearnersdictionaries.com/external/pdf/wordlists/oxford-3000-5000/The_Oxford_3000.pdf) A2. |
| [`realise`](https://dictionary.cambridge.org/dictionary/english/realize) | Cambridge nghĩa bắt đầu hiểu/nhận biết B1; [O3](https://www.oxfordlearnersdictionaries.com/external/pdf/wordlists/oxford-3000-5000/The_Oxford_3000.pdf) A2. |
| [`recommend`](https://dictionary.cambridge.org/dictionary/learner-english/recommend) | Cambridge Learner nghĩa nói người/vật phù hợp B1; [O3](https://www.oxfordlearnersdictionaries.com/external/pdf/wordlists/oxford-3000-5000/The_Oxford_3000.pdf) A2; ví dụ còn sát ranh nghĩa B2. |
| [`avoid`](https://dictionary.cambridge.org/dictionary/english/avoid) | Cambridge nghĩa tránh xa B1; [O3](https://www.oxfordlearnersdictionaries.com/external/pdf/wordlists/oxford-3000-5000/The_Oxford_3000.pdf) A2. |
| [`compare`](https://dictionary.cambridge.org/dictionary/english/compare) | Cambridge nghĩa xét giống/khác B1; [O3](https://www.oxfordlearnersdictionaries.com/external/pdf/wordlists/oxford-3000-5000/The_Oxford_3000.pdf) A1. |
| [`consider`](https://dictionary.cambridge.org/dictionary/english/consider) | Cambridge nghĩa cân nhắc B1; [O3](https://www.oxfordlearnersdictionaries.com/external/pdf/wordlists/oxford-3000-5000/The_Oxford_3000.pdf) A2. |
| [`develop`](https://dictionary.cambridge.org/dictionary/english/develop) | Cambridge nghĩa GROW B1; [O3](https://www.oxfordlearnersdictionaries.com/external/pdf/wordlists/oxford-3000-5000/The_Oxford_3000.pdf) A2. |
| [`manage`](https://dictionary.cambridge.org/dictionary/english/manage?topic=succeeding-achieving-and-fulfilling) | Cambridge nghĩa thành công xử lý việc khó B1; [O3](https://www.oxfordlearnersdictionaries.com/external/pdf/wordlists/oxford-3000-5000/The_Oxford_3000.pdf) A2. |

### B2 — 15 mục

| Headword | Lý do và nguồn đã lưu |
|---|---|
| [`acknowledge`](https://dictionary.cambridge.org/dictionary/english/acknowledge) | Cambridge C1; [O3](https://www.oxfordlearnersdictionaries.com/external/pdf/wordlists/oxford-3000-5000/The_Oxford_3000.pdf) B2. |
| [`assumption`](https://dictionary.cambridge.org/dictionary/english/assumption) | Cambridge nghĩa BELIEF C1; [O5](https://www.oxfordlearnersdictionaries.com/external/pdf/wordlists/oxford-3000-5000/The_Oxford_5000.pdf) B2. |
| [`consequence`](https://dictionary.cambridge.org/dictionary/english/consequence) | Cambridge B2; [O3](https://www.oxfordlearnersdictionaries.com/external/pdf/wordlists/oxford-3000-5000/The_Oxford_3000.pdf) B1. |
| [`controversy`](https://dictionary.cambridge.org/dictionary/english/controversy) | Cambridge C1; [O5](https://www.oxfordlearnersdictionaries.com/external/pdf/wordlists/oxford-3000-5000/The_Oxford_5000.pdf) B2. |
| [`criterion`](https://dictionary.cambridge.org/dictionary/english/criterion) | Cambridge C1; [O3](https://www.oxfordlearnersdictionaries.com/external/pdf/wordlists/oxford-3000-5000/The_Oxford_3000.pdf) B2. |
| [`evidence`](https://dictionary.cambridge.org/dictionary/english/evidence) | Cambridge nghĩa FACTS B2; [O3](https://www.oxfordlearnersdictionaries.com/external/pdf/wordlists/oxford-3000-5000/The_Oxford_3000.pdf) A2. |
| [`factor`](https://dictionary.cambridge.org/dictionary/english/factor) | Cambridge B2; [O3](https://www.oxfordlearnersdictionaries.com/external/pdf/wordlists/oxford-3000-5000/The_Oxford_3000.pdf) A2. |
| [`impact`](https://dictionary.cambridge.org/dictionary/english/impact) | Cambridge nghĩa EFFECT B2; [O3](https://www.oxfordlearnersdictionaries.com/external/pdf/wordlists/oxford-3000-5000/The_Oxford_3000.pdf) B1. |
| [`perspective`](https://dictionary.cambridge.org/dictionary/english/perspective) | Cambridge nghĩa cách xem xét vấn đề C1; [O3](https://www.oxfordlearnersdictionaries.com/external/pdf/wordlists/oxford-3000-5000/The_Oxford_3000.pdf) B2. |
| [`policy`](https://dictionary.cambridge.org/dictionary/english/policy) | Cambridge B2; [O3](https://www.oxfordlearnersdictionaries.com/external/pdf/wordlists/oxford-3000-5000/The_Oxford_3000.pdf) B1. |
| [`principle`](https://dictionary.cambridge.org/dictionary/english/principle) | Cambridge Advanced: BASIC IDEA C1, moral RULE C2; Cambridge Learner: BASIC IDEA B2; [O3](https://www.oxfordlearnersdictionaries.com/external/pdf/wordlists/oxford-3000-5000/The_Oxford_3000.pdf) B2. Nghĩa seed nằm sát ranh belief–behaviour. |
| [`substantial`](https://dictionary.cambridge.org/dictionary/english/substantial) | Cambridge nghĩa LARGE B2; [O5](https://www.oxfordlearnersdictionaries.com/external/pdf/wordlists/oxford-3000-5000/The_Oxford_5000.pdf) C1. |
| [`tendency`](https://dictionary.cambridge.org/dictionary/english/tendency) | Cambridge mẫu `have a tendency to` C1; [O5](https://www.oxfordlearnersdictionaries.com/external/pdf/wordlists/oxford-3000-5000/The_Oxford_5000.pdf) B2. |
| [`clarify`](https://dictionary.cambridge.org/dictionary/english/clarify) | Cambridge C1; [O5](https://www.oxfordlearnersdictionaries.com/external/pdf/wordlists/oxford-3000-5000/The_Oxford_5000.pdf) B2. |
| [`negotiate`](https://dictionary.cambridge.org/dictionary/english/negotiate) | Cambridge nghĩa DISCUSS C1; [O5](https://www.oxfordlearnersdictionaries.com/external/pdf/wordlists/oxford-3000-5000/The_Oxford_5000.pdf) B2. |

### C1 — 14 mục

| Headword | Lý do và nguồn đã lưu |
|---|---|
| [`comprehensive`](https://dictionary.cambridge.org/dictionary/english/comprehensive) | Cambridge nghĩa COMPLETE C1; [O5](https://www.oxfordlearnersdictionaries.com/external/pdf/wordlists/oxford-3000-5000/The_Oxford_5000.pdf) B2. |
| [`constraint`](https://dictionary.cambridge.org/dictionary/english/constraint) | Cambridge C2; [O5](https://www.oxfordlearnersdictionaries.com/external/pdf/wordlists/oxford-3000-5000/The_Oxford_5000.pdf) C1. |
| [`implication`](https://dictionary.cambridge.org/dictionary/english/implication) | Cambridge nghĩa EFFECT C1; [O5](https://www.oxfordlearnersdictionaries.com/external/pdf/wordlists/oxford-3000-5000/The_Oxford_5000.pdf) B2. |
| [`innovation`](https://dictionary.cambridge.org/dictionary/english/innovation) | Cambridge danh từ đếm được C1; [O5](https://www.oxfordlearnersdictionaries.com/external/pdf/wordlists/oxford-3000-5000/The_Oxford_5000.pdf) B2. |
| [`integrity`](https://dictionary.cambridge.org/dictionary/english/integrity) | Cambridge nghĩa HONESTY C2; [O5](https://www.oxfordlearnersdictionaries.com/external/pdf/wordlists/oxford-3000-5000/The_Oxford_5000.pdf) C1. |
| [`phenomenon`](https://dictionary.cambridge.org/dictionary/english/phenomenon) | Cambridge nghĩa EXISTING THING C1; [O3](https://www.oxfordlearnersdictionaries.com/external/pdf/wordlists/oxford-3000-5000/The_Oxford_3000.pdf) B2. |
| [`resilience`](https://dictionary.cambridge.org/dictionary/english/resilience) | Cambridge nghĩa phục hồi sau khó khăn C2; [O5](https://www.oxfordlearnersdictionaries.com/external/pdf/wordlists/oxford-3000-5000/The_Oxford_5000.pdf) C1. |
| [`scrutiny`](https://dictionary.cambridge.org/dictionary/english/scrutiny) | Cambridge C2; [O5](https://www.oxfordlearnersdictionaries.com/external/pdf/wordlists/oxford-3000-5000/The_Oxford_5000.pdf) C1. |
| [`viable`](https://dictionary.cambridge.org/dictionary/english/viable) | Cambridge nghĩa có thể thành công C2; [O5](https://www.oxfordlearnersdictionaries.com/external/pdf/wordlists/oxford-3000-5000/The_Oxford_5000.pdf) C1. |
| [`profound`](https://dictionary.cambridge.org/dictionary/english/profound) | Cambridge nghĩa EXTREME C2; [O5](https://www.oxfordlearnersdictionaries.com/external/pdf/wordlists/oxford-3000-5000/The_Oxford_5000.pdf) C1. |
| [`formulate`](https://dictionary.cambridge.org/dictionary/english/formulate) | Cambridge nghĩa phát triển chi tiết kế hoạch C2; [O5](https://www.oxfordlearnersdictionaries.com/external/pdf/wordlists/oxford-3000-5000/The_Oxford_5000.pdf) C1. |
| [`reinforce`](https://dictionary.cambridge.org/dictionary/english/reinforce) | Cambridge nghĩa hỗ trợ ý tưởng/ý kiến C1; [O5](https://www.oxfordlearnersdictionaries.com/external/pdf/wordlists/oxford-3000-5000/The_Oxford_5000.pdf) B2. |
| [`undermine`](https://dictionary.cambridge.org/dictionary/english/undermine) | Cambridge C2; [O5](https://www.oxfordlearnersdictionaries.com/external/pdf/wordlists/oxford-3000-5000/The_Oxford_5000.pdf) C1. |
| [`advocate`](https://dictionary.cambridge.org/dictionary/english/advocate) | Cambridge verb C2; [O5](https://www.oxfordlearnersdictionaries.com/external/pdf/wordlists/oxford-3000-5000/The_Oxford_5000.pdf) C1. |

## 3. Danh sách `BLOCKED` còn tồn đọng

### C1 — 4 mục

| Headword | Lý do và URL đã lưu |
|---|---|
| [`articulate`](https://dictionary.cambridge.org/dictionary/english/articulate) | Cambridge xác nhận adjective và đúng nghĩa nhưng không hiện CEFR; Oxford 5000 không có headword/từ loại tương ứng. |
| [`rationale`](https://dictionary.cambridge.org/dictionary/english/rationale) | Cambridge xác nhận nghĩa/cách dùng nhưng không hiện CEFR; Oxford 3000/5000 không liệt kê. |
| [`synthesis`](https://dictionary.cambridge.org/dictionary/english/synthesis) | Cambridge xác nhận nghĩa formal MIX nhưng không hiện CEFR; Oxford 3000/5000 không liệt kê. |
| [`nuanced`](https://dictionary.cambridge.org/dictionary/english/nuanced) | Cambridge xác nhận adjective/ngữ cảnh nhưng không hiện CEFR; Oxford 3000/5000 không liệt kê. |

### C2 — 29 mục

Với toàn bộ các mục dưới đây, Cambridge xác nhận nghĩa/từ loại/ngữ cảnh nhưng không hiển thị CEFR; truy vấn chính xác trên [English Vocabulary Profile Online](https://englishprofile.org/?menu=evp-online) không trả bản ghi và giao diện không có permalink cho truy vấn. [Oxford 5000](https://www.oxfordlearnersdictionaries.com/external/pdf/wordlists/oxford-3000-5000/The_Oxford_5000.pdf) chỉ bao phủ B2–C1, nên việc không xuất hiện không phải bằng chứng C2.

| Headword | Lý do và URL Cambridge đã lưu |
|---|---|
| [`ubiquitous`](https://dictionary.cambridge.org/dictionary/english/ubiquitous?topic=somewhere-anywhere-nowhere-or-everywhere) | Không có nhãn CEFR theo nghĩa; EVP không trả bản ghi. |
| [`serendipity`](https://dictionary.cambridge.org/dictionary/english/serendipity) | Không có nhãn CEFR theo nghĩa; EVP không trả bản ghi. |
| [`acquiesce`](https://dictionary.cambridge.org/dictionary/english/acquiesce) | Không có nhãn CEFR theo nghĩa; EVP không trả bản ghi. |
| [`anachronism`](https://dictionary.cambridge.org/dictionary/english/anachronism?topic=relating-to-time) | Không có nhãn CEFR theo nghĩa; EVP không trả bản ghi. |
| [`apocryphal`](https://dictionary.cambridge.org/dictionary/english/apocryphal) | Không có nhãn CEFR theo nghĩa; EVP không trả bản ghi. |
| [`capricious`](https://dictionary.cambridge.org/dictionary/english/capricious) | Không có nhãn CEFR theo nghĩa; EVP không trả bản ghi. |
| [`conundrum`](https://dictionary.cambridge.org/dictionary/english/conundrum) | Không có nhãn CEFR theo nghĩa; EVP không trả bản ghi. |
| [`dichotomy`](https://dictionary.cambridge.org/dictionary/english/dichotomy) | Không có nhãn CEFR theo nghĩa; EVP không trả bản ghi. |
| [`equivocal`](https://dictionary.cambridge.org/dictionary/english/equivocal) | Không có nhãn CEFR theo nghĩa; EVP không trả bản ghi. |
| [`incongruous`](https://dictionary.cambridge.org/dictionary/english/incongruous) | Không có nhãn CEFR theo nghĩa; EVP không trả bản ghi. |
| [`ineffable`](https://dictionary.cambridge.org/dictionary/english/ineffable) | Không có nhãn CEFR theo nghĩa; EVP không trả bản ghi. |
| [`intransigent`](https://dictionary.cambridge.org/dictionary/english/intransigent) | Không có nhãn CEFR theo nghĩa; EVP không trả bản ghi. |
| [`laconic`](https://dictionary.cambridge.org/dictionary/english/laconic) | Không có nhãn CEFR theo nghĩa; EVP không trả bản ghi. |
| [`magnanimous`](https://dictionary.cambridge.org/dictionary/english/magnanimous) | Không có nhãn CEFR theo nghĩa; EVP không trả bản ghi. |
| [`obfuscate`](https://dictionary.cambridge.org/dictionary/english/obfuscate) | Không có nhãn CEFR theo nghĩa; EVP không trả bản ghi. |
| [`parsimonious`](https://dictionary.cambridge.org/dictionary/english/parsimonious?topic=small) | Không có nhãn CEFR theo nghĩa; EVP không trả bản ghi. |
| [`pernicious`](https://dictionary.cambridge.org/dictionary/english/pernicious) | Không có nhãn CEFR theo nghĩa; EVP không trả bản ghi. |
| [`quintessential`](https://dictionary.cambridge.org/dictionary/english/quintessential) | Không có nhãn CEFR theo nghĩa; EVP không trả bản ghi. |
| [`recalcitrant`](https://dictionary.cambridge.org/dictionary/english/recalcitrant) | Không có nhãn CEFR theo nghĩa; EVP không trả bản ghi. |
| [`sagacious`](https://dictionary.cambridge.org/dictionary/english/sagacious) | Không có nhãn CEFR theo nghĩa; EVP không trả bản ghi. |
| [`sycophant`](https://dictionary.cambridge.org/dictionary/english/sycophant) | Không có nhãn CEFR theo nghĩa; EVP không trả bản ghi. |
| [`tenuous`](https://dictionary.cambridge.org/dictionary/english/tenuous) | Không có nhãn CEFR theo nghĩa; EVP không trả bản ghi. |
| [`vitriolic`](https://dictionary.cambridge.org/dictionary/english/vitriolic) | Không có nhãn CEFR theo nghĩa; EVP không trả bản ghi. |
| [`zeitgeist`](https://dictionary.cambridge.org/dictionary/english/zeitgeist) | Không có nhãn CEFR theo nghĩa; EVP không trả bản ghi. |
| [`circumspect`](https://dictionary.cambridge.org/dictionary/english/circumspect) | Không có nhãn CEFR theo nghĩa; EVP không trả bản ghi. |
| [`deleterious`](https://dictionary.cambridge.org/dictionary/english/deleterious) | Không có nhãn CEFR theo nghĩa; EVP không trả bản ghi. |
| [`elucidate`](https://dictionary.cambridge.org/dictionary/english/elucidate) | Không có nhãn CEFR theo nghĩa; EVP không trả bản ghi. |
| [`idiosyncratic`](https://dictionary.cambridge.org/dictionary/english/idiosyncratic?topic=habitual-behaviour) | Không có nhãn CEFR theo nghĩa; EVP không trả bản ghi. |
| [`perspicacious`](https://dictionary.cambridge.org/dictionary/english/perspicacious) | Không có nhãn CEFR theo nghĩa; EVP không trả bản ghi. |

## 4. Giới hạn bằng chứng

- Nhiều trang Cambridge mở trực tiếp từng trả HTTP 403; báo cáo QA chỉ dùng phần nội dung/nhãn thực sự hiện qua chỉ mục và đã lưu URL, không tuyên bố đã đọc toàn trang bị chặn.
- Oxford 3000/5000 cung cấp cấp theo headword/từ loại, không tự động xác nhận từng nghĩa; Oxford 5000 chỉ tới C1.
- British Council truy cập được nhưng danh sách vocabulary gộp A1–A2 hoặc B1–B2; các trang C1/C2 chỉ mô tả năng lực chung, không cấp nhãn cho từng nghĩa.
- EVP là giao diện động không tạo permalink cho truy vấn; kết quả rỗng không chứng minh một từ là C2 hoặc không thuộc CEFR.
- Vì seed vẫn để `source_reference=None`, URL trong tài liệu này là hồ sơ QA, chưa phải metadata nguồn đã được biên tập viên phê duyệt.

## 5. PASS kỹ thuật và duyệt chất lượng

Kiểm tra metadata đọc trực tiếp ngày 2026-11-12 cho kết quả:

| Kiểm tra | Kết quả |
|---|---|
| Số lượng theo cấp | PASS — A1/A2/B1/B2/C1/C2 đều 30 |
| Tổng số mục | PASS — 180 |
| Headword duy nhất, không phân biệt hoa/thường | PASS — 180/180 |
| Provenance | PASS — 180/180 `AI_GENERATED` |
| QA status | PASS — 180/180 `NEEDS_REVIEW`; 0 `VERIFIED` |
| Source metadata | 180/180 `source_reference=None` |

PASS kỹ thuật chỉ xác nhận cấu trúc/catalog và policy trạng thái. Nó **không** xác nhận bản dịch, độ tự nhiên, CEFR theo nghĩa hoặc quyền đổi sang `VERIFIED`; 99 mục `CONFLICT`/`BLOCKED` vẫn chưa đạt nghiệm thu nội dung.

## 6. Phương án xử lý tồn đọng

1. Với `CONFLICT`, biên tập viên độc lập phải khóa đúng từ loại + nghĩa + ví dụ, sau đó lấy nguồn CEFR theo **nghĩa** thứ hai (ưu tiên dữ liệu EVP/Cambridge có nhãn trực tiếp); không dùng Oxford headword để tự xử thắng/thua.
2. Với bốn mục C1 `BLOCKED`, tìm nguồn có nhãn CEFR trực tiếp cho đúng từ loại/nghĩa; nếu không có, giữ nguyên `NEEDS_REVIEW` hoặc trình chính sách ngoại lệ có phê duyệt, không tự gán C1.
3. Với 29 mục C2 `BLOCKED`, yêu cầu nguồn trực tiếp ghi C2 cho đúng nghĩa. Không suy diễn từ độ hiếm, độ khó, Oxford vắng mặt hoặc EVP trả rỗng; không thay từ chỉ để đủ 30 mục.
4. Lưu ảnh/PDF/trích đoạn hợp lệ, URL, ngày truy cập và giới hạn truy cập cho quyết định cuối; sau đó mới cân nhắc điền `source_reference`.
5. Mọi thay đổi CEFR/headword hoặc chuyển `VERIFIED` phải là một lượt biên tập độc lập riêng, có regression test tương ứng; audit này không cấp quyền thực hiện thay đổi đó.

## 7. Tiêu chí nghiệm thu nội dung

Một mục chỉ đủ điều kiện đề nghị duyệt khi đồng thời có: (a) headword/chính tả/từ loại đúng; (b) definition, nghĩa Việt và ví dụ cùng một nghĩa; (c) nguồn truy cập được gắn CEFR trực tiếp cho nghĩa/cách dùng đó, hoặc quyết định biên tập được phê duyệt khi nguồn bất đồng; (d) URL, ngày truy cập và hạn chế được lưu; (e) kiểm tra không trùng và đủ 30 mục/cấp vẫn PASS; (f) một biên tập viên độc lập xác nhận. Cho tới khi đáp ứng đầy đủ, giữ `AI_GENERATED + NEEDS_REVIEW` và không gán `VERIFIED`.
