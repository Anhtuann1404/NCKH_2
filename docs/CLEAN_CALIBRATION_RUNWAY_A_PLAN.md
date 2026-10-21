# ĐỀ ÁN & KẾ HOẠCH TUYỂN CHỌN GÓI HIỆU CHUẨN SẠCH CHO THÀNH VIÊN A (CALIBRATION-CLEAN-A)

**Dự án:** NCKH_2 — Phát hiện website phishing mạo danh tổ chức bằng học máy  
**Mã đề án:** `CALIBRATION-CLEAN-A-PLAN-V1.0`  
**Phiên bản:** `1.0.0-PROPOSAL`  
**Ngày lập:** 21/10/2026  
**Trạng thái:** `draft_pending_lead_d_approval` (Chờ Lead D duyệt trước khi phát sinh lệnh trích xuất mẫu)  
**Người lập:** Thành viên C (Data Pipeline & Blind View)  
**Thẩm định phương pháp:** Mô hình Duo (`deepseek-v4-pro`)  
**Kỷ luật áp dụng:** Academic Research Skills (ARS) & Ponytail Engineering Discipline  

---

## 1. BỐI CẢNH & MỤC TIÊU KHOA HỌC

### 1.1 Bối cảnh kỹ thuật
- Hồ sơ phân xử **Calibration v1.1.4** đã được Lead D ký duyệt chính thức và Member B nghiệm thu QA với cơ cấu: 17 mẫu nhị phân (11 benign, 6 phishing), 2 mẫu `insufficient_evidence` và 5 mẫu QC `pending_evidence`.
- Ở lượt hiệu chuẩn trước, Thành viên A đã tiếp xúc với 24 mẫu có sự trợ giúp từ bên ngoài trước khi lưu Pass 1. Do đó, toàn bộ dữ liệu gán nhãn và thời gian của A ở lượt cũ bị **loại bỏ hoàn toàn** khỏi mọi phân tích thống kê và mô hình công số PLAN-01.
- Để đảm bảo tính độc lập và khách quan khoa học, dự án cần một **Lượt hiệu chuẩn sạch mới (Clean Calibration Runway)** trên các mẫu hoàn toàn mới mà A chưa từng xem.

### 1.2 Mục tiêu kép
1. **Đo lường độ đồng thuận liên đánh giá viên thực chất ($\kappa_{A-B}$):** Thành viên A và B cùng thực hiện gán nhãn mù độc lập song song trên cùng một gói 24 mẫu chính để đo lường Cohen's Kappa trước và sau chuẩn hóa alias.
2. **Đo đạc tốc độ gán nhãn thực tế của A phục vụ PLAN-01:** Thu thập dữ liệu thời gian trung bình (Mean, Median) và độ biến động thời gian thuần túy của A trên các tầng độ khó khác nhau, làm căn cứ định lượng đáng tin cậy để chốt kế hoạch công số và tiến độ Main Annotation (>1.000 mẫu).

---

## 2. NỘI DUNG TIẾP THU & HIỆU CHỈNH 5 ĐIỂM CHỈ ĐẠO CỦA LEAD D

### 2.1 Điểm 1: Kiểm kê chính xác 4 tập loại trừ đã biết (Tổng cộng 108 mẫu)
Không tính trùng 24 mẫu Calibration thành hai đợt riêng biệt. Danh mục các mẫu đã biết cần loại trừ vĩnh viễn khỏi Gói Sạch gồm đúng 4 tập:
1. **20 mẫu tập dượt ban đầu** (`EXCL-PILOT-01`): 8 phish, 12 benign.
2. **32 mẫu Pilot V1 thật** (`EXCL-REAL-PILOT-32`): 20 phish, 12 benign.
3. **32 mẫu Pilot V2 thật** (`EXCL-PILOT-02`): 20 phish, 12 benign.
4. **24 mẫu Calibration v1.1.4 đã được A/E/B xem** (`EXCL-CALIBRATION-PROPOSAL-V1.1-MAIN-24`): 24 mẫu hiệu chuẩn cũ.
*(Lưu ý: Cộng thêm 8 mẫu dự phòng cũ `EXCL-CALIBRATION-PROPOSAL-V1.1-RESERVE-08` nếu đã tra cứu là 116 mẫu).*  
**Tổng số mẫu loại trừ tối thiểu đã đăng ký trong `data/exclusion_registry.json`:** **108 mẫu**.

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

### 2.4 Điểm 4: Kiểm soát rò rỉ dữ liệu 3 chiều & Rà soát gần trùng / Template
- **Bộ lọc Anti-Leakage 3 chiều:**
  1. *URL Disjoint:* So khớp chính xác `url_sha256` và `normalized_url_sha256`.
  2. *Content Disjoint:* So khớp mã băm nội dung HTML tĩnh (`html_sha256`) và cấu trúc hiển thị (`view_content_sha256`).
  3. *Domain Group Disjoint:* So khớp `group_sha256` dựa trên ranh giới `eTLD+1` và quy tắc tenant nền tảng dùng chung (GitHub Pages, Cloudflare Pages, Netlify, Vercel, Firebase...).
- **Rà soát gần trùng / Template (Template Similarity Scan):**
  * Thực hiện thuật toán so khớp độ tương đồng văn bản/DOM (SimHash / Jaccard similarity) để phát hiện và loại bỏ các biến thể clone hoặc template sinh hàng loạt (ví dụ: các trang shop tiếng Nhật cùng template với SMP-002/015/020/023, hoặc các trang phishing Google/Meta clone cùng mã nguồn).
- **Văn phong khoa học trung thực (ARS):**
  * Báo cáo đầy đủ phạm vi kiểm tra: "Đã kiểm tra đối chiếu độc lập trên 108 mẫu đã biết trong registry; đã rà soát template similarity để loại bỏ các biến thể cùng nguồn sinh".
  * Không sử dụng các tuyên bố tuyệt đối hóa không thể chứng minh (như "loại trừ rò rỉ tuyệt đối 100%").

### 2.5 Điểm 5: Khóa quy trình Pass 1 & Đo đạc thời gian chuẩn xác
- **Nguyên tắc phòng sạch (Clean Room Pass 1):**
  * A và B gán hoàn toàn độc lập, không trao đổi, không xem trước nhãn của nhau, không sử dụng chat AI (ChatGPT, Claude, DeepSeek...) để gợi ý nhãn, không nhờ bên thứ ba chọn nhãn trước khi lưu Pass 1.
- **Đo thời gian lao động thuần túy:**
  * Đồng hồ bấm giờ trên CLI v1.1 tích hợp cơ chế ghi nhận thời gian tạm dừng / nghỉ (pause/resume timestamp) khi annotator rời khỏi màn hình.
  * Phép đo `seconds_spent` phản ánh thời gian tập trung gán nhãn thực tế, loại trừ thời gian chờ nhàn rỗi, giúp mô hình PLAN-01 ước tính chính xác năng lực thực tế.

---

## 3. THIẾT KẾ MẪU & CƠ CẤU GÓI HIỆU CHUẨN SẠCH (32 MẪU)

### 3.1 Nguồn dữ liệu & Quy mô
- **Nguồn trích xuất:** 56 shards train đã được kiểm kê độc lập của PhreshPhish (`data/train-000.parquet` đến `data/train-055.parquet`, tổng cộng 498.255 dòng, dải ngày 02/07/2024 đến 08/09/2025).
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
| 3 | **Anti-Leakage URL** | So khớp URL sha256 với 108 mẫu đã biết | Trùng lặp = 0 |
| 4 | **Anti-Leakage Content** | So khớp HTML sha256 & View content sha256 | Trùng lặp = 0 |
| 5 | **Anti-Leakage Domain** | So khớp eTLD+1 và tenant group sha256 | Trùng lặp = 0 |
| 6 | **Template Similarity** | Rà soát SimHash/Jaccard với các template cũ | Không có mẫu clone cùng nguồn sinh |
| 7 | **Độ sạch Blind View** | Kiểm tra trường view đầu vào (fail-closed) | 0 nhãn nguồn, 0 matcher, 0 confidence, 0 quote/note |
| 8 | **An toàn HTML tĩnh** | Kiểm tra strip script/iframe/event handlers | 100% snapshot an toàn, không fetch Internet |
| 9 | **Dịch ngoại tuyến** | Kiểm tra bản dịch MarianMT (nếu có mẫu hiếm) | Pinned model revision, hash bản dịch cố định |
| 10 | **Trạng thái an toàn** | Kiểm tra cờ hệ thống | `training_blocked = true`, `official_test_used = false` |

---

## 5. KẾ HOẠCH BÀN GIAO & CÁC BƯỚC TIẾP THEO

1. **Bước 1:** Lead D ký duyệt văn bản Biên bản nghiệm thu Calibration v1.1.4 (đã lập tại `data/labels/calibration_v1_1_4/CALIBRATION_V1_1_4_SIGN_OFF_MINUTES.md`).
2. **Bước 2:** Lead D xem xét và phê duyệt Đề án Tuyển chọn Gói Hiệu chuẩn Sạch này (`docs/CLEAN_CALIBRATION_RUNWAY_A_PLAN.md`).
3. **Bước 3:** Sau khi Lead D phê duyệt, Member C sẽ thực thi script tuyển chọn bằng seed, trích xuất 32 locators, kiểm tra đối soát bằng chứng loại trừ, đăng ký vào `data/exclusion_registry.json`, xuất bản Manifest dự thảo và báo cáo bằng chứng loại trừ để Lead D nghiệm thu trước khi mở view.
4. **Bước 4:** Thành viên A và B tiến hành gán nhãn mù độc lập Pass 1 qua CLI v1.1.
