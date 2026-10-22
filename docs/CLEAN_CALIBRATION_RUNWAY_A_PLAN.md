# ĐỀ ÁN & KẾ HOẠCH TUYỂN CHỌN GÓI HIỆU CHUẨN SẠCH CHO THÀNH VIÊN A (CALIBRATION-CLEAN-A)

**Dự án:** NCKH_2 — Phát hiện website phishing mạo danh tổ chức bằng học máy  
**Mã đề án:** `CALIBRATION-CLEAN-A-PLAN-V1.1`  
**Phiên bản:** `1.1.0-PROPOSAL`  
**Ngày lập:** 21/10/2026 (Cập nhật tiếp thu chỉ đạo Lead D: 22/10/2026)  
**Trạng thái:** `draft_pending_lead_d_approval` (Chờ Lead D duyệt trước khi phát sinh lệnh trích xuất mẫu)  
**Người lập:** Thành viên C (Data Pipeline & Blind View)  
**Thẩm định phương pháp:** Mô hình Duo (`deepseek-v4-pro`)  
**Kỷ luật áp dụng:** Academic Research Skills (ARS) & Ponytail Engineering Discipline  

---

## 1. BỐI CẢNH & MỤC TIÊU KHOA HỌC

### 1.1 Bối cảnh kỹ thuật
- Hồ sơ phân xử **Calibration v1.1.4** đã được Lead D phê duyệt chính thức toàn bộ 24/24 nhãn (17 mẫu nhị phân, 2 mẫu `insufficient_evidence` và 5 mẫu QC `pending_evidence`).
- **Nguyên tắc loại trừ vĩnh viễn:** Toàn bộ 24 mẫu thuộc hồ sơ Calibration v1.1.4 (bao gồm cả 17 mẫu có `binary_model_eligible = true`) đều bị **loại trừ vĩnh viễn** khỏi toàn bộ các tập train, validation và test của các mô hình M0–M3. Thuộc tính `binary_model_eligible = true` chỉ mô tả cấu trúc nhãn lớp hợp lệ trong phân tích độ đồng thuận Calibration nội bộ, tuyệt đối không cấp quyền dùng cho huấn luyện.
- Ở lượt hiệu chuẩn trước, Thành viên A đã tiếp xúc với 24 mẫu có sự trợ giúp từ bên ngoài trước khi lưu Pass 1. Do đó, toàn bộ dữ liệu gán nhãn và thời gian của A ở lượt cũ bị **loại bỏ hoàn toàn** khỏi mọi phân tích thống kê và mô hình công số PLAN-01.
- Để đảm bảo tính độc lập và khách quan khoa học, dự án triển khai **Lượt hiệu chuẩn sạch mới (Clean Calibration Runway)** trên các mẫu hoàn toàn mới mà A chưa từng xem.

### 1.2 Mục tiêu kép
1. **Đo lường độ đồng thuận liên đánh giá viên thực chất ($\kappa_{A-B}$):** Thành viên A và B cùng thực hiện gán nhãn mù độc lập song song trên cùng một gói 24 mẫu chính để đo lường Cohen's Kappa trước và sau chuẩn hóa alias.
2. **Đo đạc tốc độ gán nhãn thực tế của A phục vụ PLAN-01:** Thu thập dữ liệu thời gian trung bình (Mean, Median) và độ biến động thời gian thuần túy của A trên các tầng độ khó khác nhau, làm căn cứ định lượng đáng tin cậy để chốt kế hoạch công số và tiến độ Main Annotation (>1.000 mẫu).

---

## 2. NỘI DUNG TIẾP THU & HIỆU CHỈNH 5 ĐIỂM CHỈ ĐẠO CỦA LEAD D

### 2.1 Điểm 1: Đếm trực tiếp Registry & Kiểm kê đầy đủ 116 mẫu loại trừ đã biết
Đếm trực tiếp từ `data/exclusion_registry.json`, giải quyết toàn diện cả 8 mẫu dự phòng Calibration đã đăng ký, phạm vi loại trừ đã biết gồm đủ 5 lô chính (**116 mẫu**):
1. **20 mẫu tập dượt ban đầu** (`EXCL-PILOT-01`): 8 phish, 12 benign (20 `summary_fingerprint_hash`).
2. **32 mẫu Pilot V1 thật** (`EXCL-REAL-PILOT-32`): 20 phish, 12 benign (32 URL, 32 HTML, 31 Group).
3. **32 mẫu Pilot V2 thật** (`EXCL-PILOT-02`): 20 phish, 12 benign (32 URL, 32 HTML, 32 Group).
4. **24 mẫu Calibration v1.1.4 chính đã xem** (`EXCL-CALIBRATION-PROPOSAL-V1.1-MAIN-24`): 24 mẫu hiệu chuẩn cũ (24 URL, 24 HTML, 24 Group).
5. **8 mẫu dự phòng Calibration đã tra cứu/đăng ký trong registry** (`EXCL-CALIBRATION-PROPOSAL-V1.1-RESERVE-08`): 8 mẫu dự phòng cũ (8 URL, 8 HTML, 8 Group).
*(Ghi nhận thêm lô lưu trữ mở rộng `EXCL-PILOT-02-REBUILD-e039c774ef5f` gồm 32 mẫu trong registry).*  
**Tổng số mẫu loại trừ chính xác đã đăng ký trong `data/exclusion_registry.json`:** **116 mẫu** (gồm 96 URL sha256 duy nhất, 96 HTML sha256 duy nhất, 95 Group sha256 duy nhất và 20 summary fingerprints).

### 2.2 Điểm 2: Sử dụng nhãn nguồn strictly bounded (Không nhìn trước nhãn)
- **Phạm vi cho phép:** Nhãn nguồn (`source_label` từ tập train) **CHỈ ĐƯỢC PHÉP SỬ DỤNG** duy nhất ở bước lấy mẫu phân tầng (Stratified Sampling) nhằm đảm bảo tỷ lệ lớp cân bằng:
  * 12 mẫu phishing / 12 mẫu benign (cho 24 mẫu chính).
  * 4 mẫu phishing / 4 mẫu benign (cho 8 mẫu dự phòng có thứ tự).
- **Phạm vi nghiêm cấm:** Tuyệt đối **KHÔNG SỬ DỤNG** nhãn nguồn để tính toán hay định hướng 6 cờ tầng độ khó bề mặt (`difficulty_strata`). Sáu cờ độ khó (`url_token_mismatch`, `shared_hosting_ugc`, `brand_mention_news`, `login_form_present`, `non_brand_personal_site`, `cart_or_payment_surface`) phải được tính toán hoàn toàn độc lập từ URL và snapshot HTML tĩnh.

### 2.3 Điểm 3: Phân định rạch ròi giữa Blind View đầu vào và Bản ghi gán nhãn đầu ra
- **Gói Blind View đầu vào (Input View):**
  * Chỉ chứa các trường quan sát tĩnh: `sample_id`, `url`, `page_text` an toàn (đã strip script/iframe), `structure_summary` (thống kê form, input, button), và `translated_text` ngoại tuyến (nếu có mẫu tiếng Nhật).
  * **TUYỆT ĐỐI KHÔNG CHỨA:** nhãn nguồn, matcher gợi ý, điểm số mô hình, và KHÔNG chứa các trường nhận định: `evidence_quote`, `evidence_note`, `confidence`, `hard_benign_type`, hay `primary_phishing_type`.
- **Bản ghi gán nhãn đầu ra (Output Annotation Record):**
  * Là tệp do chính annotator (A hoặc B) tự tay nhập liệu qua CLI v1.1 sau khi xem xét snapshot độc lập.
  * Các trường bắt buộc người gán phải nhập: `class_label`, `primary_org`, `evidence_basis`, `evidence_quote` (trích dẫn nguyên văn), `evidence_note`, `confidence` (đánh giá tin cậy chủ quan sau khi gán), và trường loại (`hard_benign_type` hoặc `primary_phishing_type`).

### 2.4 Điểm 4: Kiểm soát rò rỉ dữ liệu 3 chiều & Quy trình Rà soát Template Similarity
- **Bộ lọc Anti-Leakage 3 chiều:**
  1. *URL Disjoint:* So khớp chính xác `url_sha256` và `normalized_url_sha256` với 116 mẫu trong registry.
  2. *Content Disjoint:* So khớp mã băm nội dung HTML tĩnh (`html_sha256`) và cấu trúc hiển thị (`view_content_sha256`).
  3. *Domain Group Disjoint:* So khớp `group_sha256` dựa trên ranh giới `eTLD+1` và quy tắc tenant nền tảng dùng chung (GitHub Pages, Cloudflare Pages, Netlify, Vercel, Firebase...).
- **Rà soát gần trùng / Template (Template Similarity Scan):**
  * **Quy trình thực thi:** Là **bước kiểm tra bắt buộc sẽ thực hiện ngay sau khi thuật toán tuyển chọn ứng viên ngẫu nhiên sinh danh sách locators**. Thuật toán đo độ tương đồng SimHash và DOM Jaccard similarity sẽ quét chéo tập ứng viên với toàn bộ các template đã biết (ví dụ: các biến thể shop tiếng Nhật `.shop`, trang clone Google/Meta).
  * Kết quả đo lường thực tế sẽ được đưa vào Báo cáo Nghiệm thu Ứng viên để Lead D phê duyệt trước khi phát hành gói Blind View. Không đưa ra phát biểu "đã rà soát" trước khi có danh sách ứng viên thực tế.

### 2.5 Điểm 5: Đo đạc thời gian CLI & Đã Hoàn thành Nhiệm vụ Tiên quyết TASK-CLI-TIMER-PAUSE
- **Hiện trạng mã nguồn CLI:**
  * Tại `scripts/annotate_cli.py` (commit `e039c77` / `bfd4f6c`), CLI đã có trường `seconds_spent` đo thời gian làm việc trên từng snapshot bằng `time.perf_counter()`, và bắt `KeyboardInterrupt` để lưu an toàn khi thoát phiên.
- **Hoàn thành Nhiệm vụ Kỹ thuật Tiên quyết (`TASK-CLI-TIMER-PAUSE`):**
  * Thành viên C đã hoàn tất việc xây dựng lớp `PausableTimer` tại `src/phishing/annotation/timer.py` và tích hợp vào `scripts/annotate_cli.py`.
  * Hỗ trợ lệnh `:p` / `:pause` tại mọi bước nhập liệu (`prompt_choice`, `prompt_text_input`) và phím `p` tại màn hình đọc toàn văn `display_sample_and_allow_reading`.
  * Khi annotator tạm dừng nghỉ, đồng hồ sẽ dừng đếm; khi tiếp tục, toàn bộ thời gian nghỉ sẽ được tự động khấu trừ khỏi `seconds_spent`.
  * **Kiểm thử độc lập:** Đã bổ sung bộ kiểm thử 8 kịch bản `tests/test_annotate_cli_timer_pause.py` (toán học trừ thời gian nghỉ, tạm dừng lũy kế nhiều đợt, mock clock tất định) và đạt tỷ lệ vượt qua **100% (8/8 tests pass)**, nâng tổng số test suite an toàn lên **35/35 tests pass**.
- **Nguyên tắc phòng sạch (Clean Room Pass 1):**
  * A và B gán hoàn toàn độc lập, không trao đổi, không xem trước nhãn của nhau, không sử dụng chat AI (ChatGPT, Claude, DeepSeek...) để gợi ý nhãn, không nhờ bên thứ ba chọn nhãn trước khi lưu Pass 1.

---

## 3. THIẾT KẾ MẪU & CƠ CẤU GÓI HIỆU CHUẨN SẠCH (32 MẪU)

### 3.1 Nguồn dữ liệu & Quy mô
- **Thống nhất nguồn trích xuất:** Gói hiệu chuẩn sạch được tuyển chọn từ **2 verified boundary source shards** đã được đối chiếu checksum và khóa kiểm kê trong `configs/source_manifest.json`:
  1. `data/train-000.parquet` (Dung lượng: 49.639.686 bytes, LFS SHA-256: `9a9c693a95daeddb127c4446df4c5673b3f1a39e457ffe964b9849069bd739fe`).
  2. `data/train-055.parquet` (Dung lượng: 20.213.199 bytes, LFS SHA-256: `205a7e1cf4fb11032683e90fdbd1c13ddc9d9dd86109658d13e69929b53b31d0`).
- **Quy mô:**
  * **24 mẫu chính (Main Calibration Set):** 12 phishing, 12 benign. Đây là gói phát hành chính thức cho cả A và B.
  * **8 mẫu dự phòng có thứ tự (Ordered Reserve Set):** 4 phishing, 4 benign. Được lưu trữ hạn chế tại khu vực của C; chỉ kích hoạt thay thế theo đúng thứ tự seed khi có sự cố hiển thị kỹ thuật (R-A08), **chưa phát cho annotator**.

### 3.2 Phân bổ tầng độ khó bề mặt (Difficulty Strata)
Tuyển chọn ngẫu nhiên có kiểm soát (Random Seeded Sampling) để đảm bảo độ bao phủ các tầng độ khó:
1. `url_token_mismatch`: URL chứa tên thương hiệu nhưng tên miền thực tế khác biệt.
2. `shared_hosting_ugc`: Trang nằm trên nền tảng lưu trữ người dùng (Pages, Workers, Firebase, Netlify...).
3. `brand_mention_news`: Trang tin tức, bài báo nhắc đến thương hiệu nhưng không phải đối tượng mạo danh.
4. `login_form_present`: Trang có form nhập thông tin đăng nhập hoặc mật khẩu.
5. `non_brand_personal_site`: Trang cá nhân, blog, thực thể phi thương hiệu dễ gây nhầm lẫn.
6. `cart_or_payment_surface`: Trang có bề mặt giỏ hàng, thanh toán trực tuyến.

---

## 4. QUY TRÌNH NGHIỆM THU & 10 TIÊU CHÍ KỸ THUẬT (ACCEPTANCE CRITERIA)

Trước khi mở gói cho A và B, Member C phải trình Lead D duyệt hồ sơ đáp ứng đủ 10 tiêu chí:

| # | Tiêu chí | Phương pháp kiểm tra | Ngưỡng nghiệm thu |
| :--- | :--- | :--- | :--- |
| 1 | **Số lượng mẫu** | Kiểm đếm cấu trúc locators | Đủ 32 mẫu (24 chính + 8 dự phòng) |
| 2 | **Cân bằng lớp** | Kiểm tra nhãn nguồn phân tầng | 12 phish + 12 benign (chính); 4 phish + 4 benign (dự phòng) |
| 3 | **Anti-Leakage URL** | So khớp URL sha256 với 116 mẫu đã biết | Trùng lặp = 0 |
| 4 | **Anti-Leakage Content** | So khớp HTML sha256 & View content sha256 | Trùng lặp = 0 |
| 5 | **Anti-Leakage Domain** | So khớp eTLD+1 và tenant group sha256 | Trùng lặp = 0 |
| 6 | **Template Similarity** | Hậu kiểm SimHash/Jaccard trên tập ứng viên sinh ra | Báo cáo chi tiết; loại bỏ triệt để clone template |
| 7 | **Độ sạch Blind View** | Kiểm tra trường view đầu vào (fail-closed) | 0 nhãn nguồn, 0 matcher, 0 confidence, 0 quote/note |
| 8 | **An toàn HTML tĩnh** | Kiểm tra strip script/iframe/event handlers | 100% snapshot an toàn, không fetch Internet |
| 9 | **Dịch ngoại tuyến** | Kiểm tra bản dịch MarianMT (nếu có mẫu hiếm) | Pinned model revision, hash bản dịch cố định |
| 10 | **Trạng thái an toàn** | Kiểm tra cờ hệ thống | `training_blocked = true`, `official_test_used = false` |

---

## 5. KẾ HOẠCH BÀN GIAO & CÁC BƯỚC TIẾP THEO

1. **Bước 1:** Lead D ký duyệt văn bản Biên bản nghiệm thu Calibration v1.1.4 (đã lập tại `data/labels/calibration_v1_1_4/CALIBRATION_V1_1_4_SIGN_OFF_MINUTES.md`).
2. **Bước 2:** Lead D xem xét và phê duyệt Đề án Tuyển chọn Gói Hiệu chuẩn Sạch này (`docs/CLEAN_CALIBRATION_RUNWAY_A_PLAN.md`).
3. **Bước 3:** C hoàn thành nhiệm vụ `TASK-CLI-TIMER-PAUSE` (bổ sung pause/resume và unit test cho CLI).
4. **Bước 4:** Sau khi Lead D phê duyệt, Member C sẽ thực thi script tuyển chọn bằng seed cố định `20261022`, trích xuất 32 locators từ 2 shards đã xác minh, hậu kiểm template similarity và kiểm tra đối soát bằng chứng loại trừ với 116 mẫu trong registry, trình Lead D duyệt trước khi mở view.
5. **Bước 5:** Thành viên A và B tiến hành gán nhãn mù độc lập song song Pass 1 qua CLI v1.1.

