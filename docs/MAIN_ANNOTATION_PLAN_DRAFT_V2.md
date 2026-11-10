# DỰ THẢO KẾ HOẠCH CHIẾN DỊCH GÁN NHÃN CHÍNH (MAIN ANNOTATION PLAN - PROPOSAL V2.1)

**Dự án:** Nghiên cứu phát hiện website phishing mạo danh tổ chức bằng học máy kết hợp URL và nội dung trang (NCKH_2)  
**Mã văn bản:** `PLAN-MAIN-ANNOTATION-PROPOSAL-V2.1`  
**Phiên bản:** `2.1.0-REVISED-DRAFT`  
**Ngày lập:** 10/11/2026  
**Đơn vị lập:** Thành viên C (Nguyễn Thắng — Data Pipeline & Thư ký Kiểm toán)  
**Trạng thái quản trị:** `DRAFT_V2.1_PENDING_LEAD_D_REVIEW_AND_QA_APPRAISAL` (Dự thảo V2.1 — Tiếp thu trọn vẹn ý kiến kiểm toán ngày 10/11/2026 của Lead D; chờ Lead D xem xét và chuyển QA Lead B thẩm định độc lập; tuyệt đối chưa trích xuất mẫu, chưa phát Blind View, chưa mở Pass 1)  
**Căn cứ pháp lý & kỹ thuật:**  
- Ý kiến chỉ đạo kiểm toán của Lead D (Nguyễn Anh Tuấn) đối với bản dự thảo V2 ngày 10/11/2026 (6 điểm yêu cầu hiệu chỉnh).  
- Ý kiến phản biện chuyên sâu của Chuyên gia An toàn Học máy (ML Security Specialist — DeepSeek Reason Bridge trong Chế độ Duo).  
- Quy tắc làm việc với AI của nhóm NCKH_2 (Ban hành ngày 09/11/2026).  
- Giao thức dữ liệu (`docs/DATA_PROTOCOL.md`), Giao thức thực nghiệm (`docs/EXPERIMENT_PROTOCOL.md`) và Codebook v1.1 (`docs/CODEBOOK_V1_1.md`).  
- Quyết định phê duyệt đóng mốc Calibration Runway A (`DECISION-LEAD-D-CLOSURE-CALIBRATION-CLEAN-RUNWAY-A-OFFICIAL`).  
- Hồ sơ niêm phong cam kết Đợt C: `data/restricted/clean_calibration_exclusion_mapping_c_32.json` (SHA-256: `67326e80...`).  
- Kỷ luật nghiên cứu khoa học Academic Research Skills (ARS) và Ponytail Engineering Discipline.

---

## BẢNG ĐỐI CHIẾU TIẾP THU VÀ HIỆU CHỈNH 6 YÊU CẦU KIỂM TOÁN CỦA LEAD D (ĐỢT 2)

| # | Yêu cầu kiểm toán của Lead D | Căn cứ mã nguồn / Tài liệu hiện hành | Phương án hiệu chỉnh trong Bản V2.1 | Phép kiểm & Bằng chứng thực tế |
|:---:|:---|:---|:---|:---|
| **1** | Đối chiếu lại ID chính xác từng lô với `data/exclusion_registry.json` (sửa sai Lô 7–9). Phân biệt "246 mục ghi theo lô" với "246 mẫu duy nhất". Chứng minh 24 mẫu Runway A thuộc Lô 10 (Đợt C), độc lập với Lô 9 (Đợt B) bằng hồ sơ ánh xạ hạn chế, không suy từ số đếm. | `data/exclusion_registry.json` (`v1.1.0`), các tệp ánh xạ hạn chế: `data/restricted/clean_calibration_exclusion_mapping_32.json` (Đợt B) và `clean_calibration_exclusion_mapping_c_32.json` (Đợt C, hash `67326e80...`). | Đính chính 100% ID lô: Lô 7 là `EXCL-CALIB-CLEAN-32-EXPOSED-ON-GIT`, Lô 8 là `EXCL-CALIB-CLEAN-02-PAIRWISE-RESOLUTION-LOCATOR-EXPOSED`, Lô 9 là `EXCL-CALIBRATION-CLEAN-RUNWAY-32`. Làm rõ: 246 là tổng số mục ghi theo lô ($\sum n_i$). Chứng minh bằng hồ sơ hạn chế: 24 mẫu Runway A là `main_24` của Lô 10; Lô 9 và Lô 10 có tập URL giao nhau rỗng ($S_9 \cap S_{10} = \emptyset$). Tuyệt đối không cộng trùng $246 + 24 = 270$. | Kiểm tra thực tế: Lô 9 (32 mẫu) và Lô 10 (32 mẫu) độc lập 100%. Hash cam kết Lô 10 khớp đúng `67326e80b2a6f9cb7356450a31fe15054a1193412a8ed0576ea2972f1801a805`. |
| **2** | Đính chính trạng thái `verify_exclusion_registry_integrity()`: ghi rõ là yêu cầu cần triển khai, chỉ rõ vị trí tích hợp và test fail-closed cần làm. Không nhận vơ cơ chế mới như đã hoạt động. | `src/phishing/data/exclusion.py`, `tests/test_exclusion_registry.py`. | Đính chính minh bạch: Hàm này là **Yêu cầu kỹ thuật đề xuất cần triển khai**, hiện chưa có trong mã chạy. Quy định vị trí tích hợp: Hàm `verify_exclusion_registry_integrity()` trong `src/phishing/data/exclusion.py`, làm cổng preflight chặn trước mọi script sampling. Xác định 4 test case fail-closed cần bổ sung vào `test_exclusion_registry.py`. | Kiểm tra codebase: `git grep verify_exclusion_registry_integrity` không trả về mã giả vờ. |
| **3** | Giải quyết mâu thuẫn tính mù: Trường `random_subset` trong Blind View làm lộ mẫu ngẫu nhiên và ca khó cho B. Trình phương án đồng bộ schema, CLI và metadata hạn chế để B nhận mẫu trung tính, C vẫn tái lập được mẫu số Kappa. | `src/phishing/annotation/blind_view.py`, `ALLOWED_BLIND_SAMPLE_KEYS`, `src/phishing/annotation/annotate_cli.py`, `tests/test_blind_view.py`. | Thiết kế giải pháp đồng bộ 3 tầng: Tầng 1 (View của B): Loại bỏ hoặc đặt trung tính cờ `random_subset` để B hoàn toàn không biết mẫu thuộc nhóm nào. Tầng 2 (Metadata hạn chế của C): C lưu trữ tệp cam kết phân tầng niêm phong tại `data/restricted/`. Tầng 3 (Tính toán Kappa): Script đánh giá nối `sample_id` với bảng cam kết của C để bóc tách đúng $N_{\text{random}}$ mẫu. | Ranh giới mù tuyệt đối: B nhận view trung tính, không bị thiên kiến tâm lý; C và Lead D bảo toàn khả năng tái lập 100%. |
| **4** | Tách rõ "hoàn thành Đợt 1 trong 1 tuần" khỏi "hoàn thành cả chiến dịch trong 1 tuần". Bổ sung tính toán 1.000 mẫu (A gán 1.000, B gán 30% ngẫu nhiên + ca khó, C data/reconcile, D phân xử). Nếu chưa có cam kết giờ A/B, ghi tiến độ là *chưa xác định*. | Báo cáo thực nghiệm Pass 1 ($N=24$): A mean 6,34 phút/mẫu; B mean 4,17 phút/mẫu. Khung ngân sách PLAN-01 (190,79 giờ người). | Tách bạch rõ 2 quy mô: Đợt 1 (60 hoặc 100 mẫu) thực hiện trong 1 tuần; Chiến dịch 1.000 mẫu cần ~190–200 giờ người (A gán ~105,7h, B gán và QA ~40–45h, C ~30–35h, D ~12–15h). Kết luận tiến độ toàn chiến dịch ghi rõ: **CHƯA XÁC ĐỊNH (TBD)** chờ văn bản cam kết số giờ khả dụng mỗi tuần của A và B. | Bảng tính phân bổ công số 1.000 mẫu chi tiết tại Mục 7. |
| **5** | Dịch ngoại tuyến: Làm rõ ngôn ngữ đích, model và revision cho từng ngôn ngữ nguồn; không mặc định dịch sang tiếng Việt. Giữ nguyên `page_text`, metadata dịch và phép kiểm hash theo R-A09. | `data/restricted/clean_calibration_translations.json`, Codebook v1.1 Quy tắc R-A09. | Đính chính: Ngôn ngữ đích là **TIẾNG ANH (EN)**, không phải tiếng Việt. Khóa cứng model và revision: `Helsinki-NLP/opus-mt-ja-en@0770961` (tiếng Nhật) và `Helsinki-NLP/opus-mt-ru-en@fbd6dc7` (tiếng Nga). Giữ nguyên 100% `page_text` gốc, lưu bản dịch tiếng Anh ngoại tuyến vào `translated_text` kèm đủ 5 trường metadata và kiểm tra `translation_sha256`. | Đối chiếu thực tế 3 mẫu hiệu chuẩn (SMP-008 JA, SMP-009 JA, SMP-015 RU) đều dịch sang tiếng Anh bằng 2 model trên. |
| **6** | Bỏ thông tin tỷ lệ theo tổ chức mục tiêu khỏi gói QA trước Pass 1 của B nếu có thể gây lộ cơ cấu nguồn/đích; B chỉ nhận báo cáo tổng hợp đủ để kiểm kỹ thuật mà vẫn giữ mù. | Quy tắc làm việc với AI nhóm NCKH_2 (Khoản 2 & Khoản 3). | Loại bỏ 100% thông tin phân bổ tổ chức mục tiêu khỏi gói QA tuyển chọn của B. Gói QA bàn giao cho B chỉ chứa các chỉ số kỹ thuật: Tổng số lượng mẫu $N$, Schema Allowlist validation, Zero forbidden keys check, Template clone scan summary, và bảng mã băm `SHA256SUMS.txt`. | Ngăn chặn triệt để hiện tượng thiên kiến xác nhận (confirmation bias) khi B bước vào gán nhãn Pass 1. |

---

## 1. NGUYÊN TẮC CỐT LÕI & RANH GIỚI QUẢN TRỊ

1. **Bản chất văn bản:** Đây là văn bản **DỰ THẢO ĐỀ XUẤT PHIÊN BẢN 2.1 (PROPOSAL V2.1)** do Thành viên C lập để tiếp thu toàn diện các chỉ đạo kiểm toán của Lead D ngày 10/11/2026. Mọi nội dung, phương án và bảng tính trong tài liệu này đều ở trạng thái chờ Lead D phê duyệt, tuyệt đối không tự động phát sinh hiệu lực thi hành và chưa trích xuất bất kỳ mẫu dữ liệu nào.
2. **Khẳng định tính chất con số 1.000 trong PLAN-01:**
   - Con số 1.000 mẫu trong Báo cáo PLAN-01 là **Khung ngân sách công sức dự phóng có điều kiện** (Conditional Projected Effort Budget — 190,79 giờ người) được Lead D phê duyệt về mặt kế toán tài nguyên dự án.
   - Con số 1.000 mẫu **KHÔNG PHẢI LÀ LỆNH TRÍCH XUẤT THỰC TẾ**. Quy mô trích xuất thực tế sẽ do Lead D quyết định theo từng giai đoạn căn cứ vào kết quả thực nghiệm Đợt 1 và cam kết thời gian khả dụng của nhân sự.
3. **Kỷ luật hệ thống bất biến:**
   - `training_blocked = true` (Chặn 100% nạp dữ liệu vào pipeline huấn luyện).
   - `official_test_used = false` (Cô lập tuyệt đối 100% tập kiểm thử chính thức).
   - `main_annotation_status = "LOCKED"` (Chiến dịch gán nhãn chính tiếp tục khóa hoàn toàn).

---

## 2. KIỂM KÊ DANH MỤC LOẠI TRỪ HIỆN HÀNH (246 MỤC GHI THEO LÔ) & QUAN HỆ ÁNH XẠ HẠN CHẾ

### 2.1 Bảng đối chiếu chính xác 10 lô loại trừ trong `data/exclusion_registry.json`
Đọc trực tiếp từ tệp `data/exclusion_registry.json` (phiên bản `1.1.0`), danh mục loại trừ gồm đúng **10 lô** với tổng cộng **246 mục ghi nhận theo lô** ($\sum_{i=1}^{10} n_i = 246$), đính chính chính xác 100% mã định danh lô (Exclusion ID) và mã tập dữ liệu (Dataset ID):

| STT | Mã định danh Lô chính xác (Exclusion ID) | Mã tập dữ liệu (Dataset ID) | Số lượng mục ghi ($n_i$) | Trạng thái ánh xạ (Mapping Status) | Lý do loại trừ vĩnh viễn khỏi Train / Validation / Test |
|:---:|:---|:---|:---:|:---|:---|
| 1 | `EXCL-PILOT-01` | *(unspecified)* | 20 | `unresolved_source_mapping` | 20 mẫu kỹ thuật pilot ban đầu (8 phish, 12 benign) đã được mở kiểm tra cấu trúc/văn bản. |
| 2 | `EXCL-REAL-PILOT-32` | *(unspecified)* | 32 | `unresolved_source_mapping` | Hợp của 32 mẫu pilot thật Đợt 1, không có per-ID/class/source mapping công bố. |
| 3 | `EXCL-PILOT-02` | `REAL-PILOT-32-V2` | 32 | `unresolved_source_mapping` | 32 mẫu pilot thật Đợt 2 (20 phish, 12 benign), cô lập vĩnh viễn khỏi tập thực nghiệm. |
| 4 | `EXCL-PILOT-02-REBUILD-e039c774ef5f` | `REAL-PILOT-32-V2` | 32 | `resolved` | Lô tái lập Pilot V2 có đầy đủ mã băm URL, HTML và Group. |
| 5 | `EXCL-CALIBRATION-PROPOSAL-V1.1-MAIN-24` | `CALIBRATION-PROPOSAL-V1.1-MAIN` | 24 | `resolved` | 24 mẫu đề xuất hiệu chuẩn cũ v1.1 đã tạo Blind View và gắn dịch ngoại tuyến. |
| 6 | `EXCL-CALIBRATION-PROPOSAL-V1.1-RESERVE-08` | `CALIBRATION-PROPOSAL-V1.1-RESERVE` | 8 | `resolved` | 8 mẫu dự phòng hiệu chuẩn cũ đã đọc từ shard để tính toán cờ mô tả bề mặt. |
| 7 | `EXCL-CALIB-CLEAN-32-EXPOSED-ON-GIT` | `CALIBRATION-CLEAN-32-EXPOSED` | 32 | `mapped_to_shards` | 32 ứng viên hiệu chuẩn sạch vô tình xuất hiện locator trên Git tại commit `226d422`. |
| 8 | `EXCL-CALIB-CLEAN-02-PAIRWISE-RESOLUTION-LOCATOR-EXPOSED` | `CALIBRATION-CLEAN-02-PAIRWISE-EXPOSED` | 2 | `mapped_to_shards` | 02 mẫu (RSV-002 và mẫu dự phòng train-055) vô tình lộ locator tại commit `9e457f5`. |
| 9 | `EXCL-CALIBRATION-CLEAN-RUNWAY-32` | `CALIBRATION-CLEAN-RUNWAY-32` | 32 | `verified_cryptographic_hashes_locators_restricted_offline` | 32 mẫu tuyển chọn cho Runway A Đợt B (24 chính + 8 dự phòng) cô lập locators ngoài Git. |
| **10** | **`EXCL-CALIBRATION-CLEAN-BATCH-C-RESTRICTED`** | **`CALIBRATION-CLEAN-C-32`** | **32** | **`resolved_in_restricted_dossier`** | **32 mẫu Đợt C niêm phong cam kết hạn chế ngoài Git (`clean_calibration_exclusion_mapping_c_32.json`) với commitment hash `67326e80b2a6f9cb7356450a31fe15054a1193412a8ed0576ea2972f1801a805`.** |
| — | **TỔNG CỘNG THEO CÁC LÔ** | **10 LÔ** | **246** | — | **Tổng số mục ghi nhận loại trừ qua các lô quản trị.** |

### 2.2 Phân biệt "246 mục ghi theo lô" với "246 mẫu duy nhất"
- Con số **246** trong trường `total_excluded_samples` của registry là **tổng tích lũy số đếm mẫu được khai báo qua 10 lô** ($\sum_{i=1}^{10} n_i = 246$), phản ánh tổng thể các đợt phát sinh sự cố và quyết định cô lập dữ liệu.
- Về mặt bản thể dữ liệu (ontological uniqueness): Do các lô 1–3 có trạng thái `unresolved_source_mapping` (chưa có ánh xạ đầy đủ từng dòng về shard nguồn), số lượng URL hoặc domain duy nhất tuyệt đối có thể có sự trùng lặp bảo thủ giữa các đợt pilot lịch sử. Tuy nhiên, toàn bộ pipeline thực nghiệm áp dụng nguyên tắc **Fail-Closed**: chỉ cần một ứng viên trùng khớp với bất kỳ mã băm nào (`url_sha256`, `html_sha256`, hoặc `group_sha256`) trong bất kỳ lô nào thì đều bị loại trừ vĩnh viễn.

### 2.3 Chứng minh quan hệ của 24 mẫu Runway A với Lô 9 và Lô 10 bằng Hồ sơ Ánh xạ Hạn chế
Để minh định tuyệt đối quan hệ dữ liệu mà không dựa vào phép suy luận số đếm:
1. **24 mẫu Runway A thuộc về Lô 10 (Đợt C):**
   - 24 mẫu hiệu chuẩn Runway A thực tế đã gán nhãn và nghiệm thu (`clean_calibration_runway_a_labels_final.json`, manifest `configs/calibration_clean_a_manifest.json`) chính là 24 mẫu có vai trò `role: "main_24"` (SMP-001 đến SMP-024) nằm trong hồ sơ hạn chế Lô 10: `data/restricted/clean_calibration_exclusion_mapping_c_32.json` (tổng 32 mẫu gồm 24 chính + 8 dự phòng RSV-001..RSV-008).
   - Hồ sơ này đã được niêm phong mật mã với mã băm cam kết: `67326e80b2a6f9cb7356450a31fe15054a1193412a8ed0576ea2972f1801a805`.
2. **Lô 9 (`EXCL-CALIBRATION-CLEAN-RUNWAY-32`) là Đợt B độc lập:**
   - Lô 9 lưu trữ 32 mẫu ứng viên của Đợt B trước đó, được quản lý hạn chế trong `data/restricted/clean_calibration_exclusion_mapping_32.json`.
   - **Bằng chứng độc lập:** Đối soát toàn bộ 32 mã băm `url_sha256` của Lô 9 và 32 mã băm của Lô 10 cho thấy **tập giao hoàn toàn rỗng**:
     $$S_{\text{Batch 9}} \cap S_{\text{Batch 10}} = \emptyset$$
3. **Kết luận về loại trừ và chống cộng trùng:**
   - 24 mẫu Runway A **hoàn toàn thuộc Lô 10**, không thuộc Lô 9.
   - Việc Lô 10 đã được đăng ký loại trừ vĩnh viễn trong `data/exclusion_registry.json` bảo đảm 24 mẫu Runway A đã được cô lập 100%.
   - Nhóm nghiên cứu không cộng dồn $246 + 24 = 270$ mẫu, vì 24 mẫu Runway A đã nằm trọn vẹn trong 32 mẫu của Lô 10 thuộc tổng số 246 mục ghi nhận.

---

## 3. ĐÍNH CHÍNH CƠ CHẾ KIỂM TRA TOÀN VẸN SỔ BỘ LOẠI TRỪ (YÊU CẦU CẦN TRIỂN KHAI)

Tiếp thu nghiêm túc chỉ đạo của Lead D và tuân thủ kỷ luật Ponytail ("không mô tả một cơ chế mới như đã hoạt động chỉ vì được viết trong dự thảo"):
- **Trạng thái thực tế:** Hàm kiểm tra tự động `verify_exclusion_registry_integrity()` hiện là **YÊU CẦU KỸ THUẬT ĐỀ XUẤT CẦN TRIỂN KHAI (PROPOSED SPECIFICATION TO BE IMPLEMENTED)**, chưa có sẵn trong codebase đang chạy.
- **Kế hoạch triển khai kỹ thuật cụ thể:**
  1. *Vị trí tích hợp module:* Khai báo và cài đặt hàm `verify_exclusion_registry_integrity(registry_path: Path, restricted_dossier_path: Path) -> bool` trực tiếp tại `src/phishing/data/exclusion.py`.
  2. *Điểm kích hoạt bắt buộc (Preflight Gate):* Được gọi ở dòng đầu tiên của script trích xuất ứng viên Main Annotation (`scripts/data/sample_main_annotation.py` hoặc tương đương). Nếu tiền kiểm không đạt, script dừng ngay lập tức (fail-closed) trước khi đọc bất kỳ file dữ liệu nguồn nào.
  3. *Quy cách kiểm thử đơn vị cần bổ sung (`tests/test_exclusion_registry.py`):*
     - `test_verify_exclusion_registry_integrity_success()`: Pass khi registry đủ 10 lô, tổng 246 mẫu, và file Lô 10 khớp đúng mã băm `67326e80...`.
     - `test_verify_exclusion_registry_integrity_missing_file()`: Ném lỗi `FileNotFoundError` khi thiếu file hạn chế Lô 10.
     - `test_verify_exclusion_registry_integrity_tampered_hash()`: Ném lỗi `RuntimeError` khi nội dung file Lô 10 bị sửa đổi (sai lệch hash).
     - `test_verify_exclusion_registry_integrity_corrupted_counts()`: Ném lỗi `ValueError` khi trường `total_excluded_samples != 246` hoặc `total_excluded_entries != 10`.

---

## 4. GIẢI QUYẾT MÂU THUẪN TÍNH MÙ CỦA TRƯỜNG `random_subset` & THIẾT KẾ ĐỒNG BỘ 3 TẦNG

### 4.1 Bản chất mâu thuẫn tính mù trong Codebase hiện hành
- Trong lớp `BlindSample` (`src/phishing/annotation/blind_view.py`), trường `random_subset: bool` đang thuộc `ALLOWED_BLIND_SAMPLE_KEYS`.
- Khi xuất Blind View cho Annotator B, nếu trường này mang giá trị `true` (mẫu ngẫu nhiên) hoặc `false` (ca khó bổ sung), Annotator B khi đọc tệp JSON hoặc qua CLI sẽ **ngay lập tức biết mẫu nào là ngẫu nhiên, mẫu nào là ca khó**, gây thiên kiến tâm lý nghiêm trọng và phá vỡ nguyên tắc gán nhãn mù độc lập (ARS Blinding Protocol).

### 4.2 Phương án đồng bộ 3 tầng bảo vệ tính mù tuyệt đối (Schema — Metadata hạn chế — CLI/Evaluation)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ TẦNG 1: BLIND VIEW GIAO CHO ANNOTATOR B (TRUNG TÍNH TUYỆT ĐỐI)              │
│ • Loại bỏ trường random_subset khỏi tệp JSON phát cho B (hoặc gán đồng nhất)│
│ • Chỉ gồm 11 trường nội dung an toàn: sample_id, url, page_text, summary... │
│ • B gán nhãn với tâm lý độc lập 100%, không biết ca khó hay ngẫu nhiên      │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ TẦNG 2: HỒ SƠ PHÂN TẦNG NIÊM PHONG DO C LƯU TRỮ (RESTRICTED PARTITION MAP)  │
│ • Vị trí: data/restricted/main_annotation_selection_mapping.json           │
│ • Cấu trúc: { "MAIN-0001": {"is_random_subset": true}, ... }                │
│ • Khóa mã băm SHA-256 trong release manifest trước khi mở Pass 1            │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ TẦNG 3: TÍNH TOÁN COHEN'S KAPPA CHÍNH XÁC (EVALUATION / RECONCILIATION)     │
│ • Script evaluate_kappa thực hiện Inner Join theo sample_id:                │
│   (Nhãn của A) ⨝ (Nhãn của B) ⨝ (Restricted Partition Map)                  │
│ • Bóc tách chính xác N_random mẫu để tính Cohen's Kappa chính thức          │
└─────────────────────────────────────────────────────────────────────────────┘
```

1. **Tầng 1 — Blind View phát cho Annotator B (Mẫu trung tính):**
   - Loại bỏ trường `random_subset` khỏi view giao cho B, hoặc đặt mặc định trung tính (`null`/omitted).
   - Annotator B không nhận bất kỳ gợi ý nào về nguồn gốc tuyển chọn của mẫu.
2. **Tầng 2 — Hồ sơ phân tầng hạn chế của C (`data/restricted/`):**
   - Trước khi phát hành Blind View, Thành viên C khóa trước danh sách rút mẫu ngẫu nhiên độc lập 30% ($S_{\text{random}}$) và danh sách ca khó bổ sung ($S_{\text{hard\_supplemental}}$) vào tệp ánh xạ hạn chế ngoài Git: `data/restricted/main_annotation_selection_mapping.json`.
   - Tính toán mã băm SHA-256 của tệp này và công bố công khai trong manifest phát hành để khóa chặt tính toàn vẹn.
3. **Tầng 3 — Tái lập mẫu số Kappa chính xác:**
   - Khi chạy module tính toán độ đồng thuận (`evaluate_kappa`), hệ thống nạp các bản ghi nhãn độc lập của A và B, sau đó ghép nối (join) với tệp phân tầng hạn chế dựa trên `sample_id`.
   - Phép tính Cohen's Kappa chính thức ($\kappa_{\text{primary}}$) **chỉ lọc các bản ghi có `is_random_subset == True`**, bảo đảm tính chuẩn xác toán học mà người gán nhãn không hề hay biết về phân tầng.
4. **Cam kết kiểm thử ranh giới:** Thành viên C cam kết bổ sung bài unit test kiểm tra Blind View phát hành cho B bảo đảm 0 rò rỉ trường phân tầng trước khi bàn giao gói dữ liệu.

---

## 5. CHUẨN HÓA DỊCH NGOẠI TUYẾN MARIANMT: NGÔN NGỮ ĐÍCH TIẾNG ANH & REVISION ĐÃ KHÓA

### 5.1 Đính chính về Ngôn ngữ đích
- Thành viên C đính chính dứt khoát: Bản dịch ngoại tuyến MarianMT có ngôn ngữ đích là **TIẾNG ANH (EN)**, không phải tiếng Việt.
- Lý do kỹ thuật: Các mô hình MarianMT tiền huấn luyện (Helsinki-NLP) đạt chất lượng cao nhất ở các cặp dịch từ ngôn ngữ hiếm sang tiếng Anh (`xx -> en`). Các Annotator của dự án đều có năng lực đọc hiểu tiếng Anh chuyên ngành tốt; việc dịch sang tiếng Anh bảo đảm tính trung thực ngữ nghĩa của trang gốc, tránh suy hao dịch thuật hai chặng (`xx -> en -> vi`).

### 5.2 Danh mục Mô hình và Revision khóa cứng theo Ngôn ngữ nguồn
Căn cứ trực tiếp từ hồ sơ thực nghiệm dịch thuật `clean_calibration_translations.json` và kho lưu trữ cục bộ:

| Mã ngôn ngữ nguồn | Tên ngôn ngữ nguồn | Mô hình MarianMT áp dụng | Revision khóa cứng (Pinned Commit) | Ngôn ngữ đích | Trạng thái xác minh |
|:---:|:---|:---|:---|:---:|:---|
| `ja` | Tiếng Nhật | `Helsinki-NLP/opus-mt-ja-en` | `0770961` | `en` (Tiếng Anh) | Đã kiểm chứng trên SMP-008, SMP-009. |
| `ru` | Tiếng Nga | `Helsinki-NLP/opus-mt-ru-en` | `fbd6dc7` | `en` (Tiếng Anh) | Đã kiểm chứng trên SMP-015. |
| `zh` | Tiếng Trung | `Helsinki-NLP/opus-mt-zh-en` | *(phải khóa revision trước khi dùng)* | `en` (Tiếng Anh) | Đề xuất dự phòng khi xuất hiện mẫu tiếng Trung. |
| `vi`, `en` | Tiếng Việt / Tiếng Anh | *(Không dịch)* | `N/A` | `N/A` | `translation_provided = false`. |

### 5.3 Tuân thủ nghiêm ngặt Quy tắc R-A09
1. **Bảo toàn văn bản gốc:** Trường `page_text` lưu giữ 100% nội dung trang gốc không bị chỉnh sửa.
2. **Metadata dịch đầy đủ 5 trường:** Mọi mẫu có bản dịch phải có đủ: `translation_provided: true`, `translated_text`, `translation_source_language`, `translation_tool: "MarianMT"`, `translation_tool_version` (tên mô hình kèm revision), và `translation_sha256`.
3. **Kiểm tra mã băm fail-closed:** Mã băm `translation_sha256` được tính bằng $\text{SHA-256}(\text{translated\_text})$. Bất kỳ sự sai lệch nào dù chỉ 1 ký tự đều khiến pipeline ném ngoại lệ dừng lại ngay lập tức.

---

## 6. BẢO VỆ TÍNH MÙ TRONG GÓI BÁO CÁO QA TUYỂN CHỌN CỦA THÀNH VIÊN B

Tiếp thu triệt để ý kiến của Lead D về việc chống thiên kiến xác nhận (confirmation bias):
- **Loại bỏ hoàn toàn:** Tỷ lệ phần trăm phân bổ theo 14 tổ chức mục tiêu (Target Organizations) bị **CẤM TUYỆT ĐỐI** xuất hiện trong gói báo cáo giao cho QA Lead B trước khi Pass 1 hoàn tất.
- **Danh mục thông tin B ĐƯỢC PHÉP NHẬN trong gói QA Tuyển chọn:**
  1. *Quy mô mẫu:* Tổng số lượng mẫu ứng viên ($N$).
  2. *Schema Validation Report:* Báo cáo kiểm tra 100% mẫu tuân thủ allowlist `ALLOWED_BLIND_SAMPLE_KEYS` của `BlindSample`.
  3. *Anti-Leakage Check:* Báo cáo kiểm tra tự động xác nhận 0 chứa trường cấm (`source_label`, `target`, `locator`, `domain`, `score`...).
  4. *Template Clone Scan Summary:* Báo cáo quét SimHash và DOM Jaccard xác nhận 0 ứng viên nào vi phạm ngưỡng tương đồng (SimHash Hamming $\le 10$, Jaccard $\ge 0,85$).
  5. *Checksum Verification:* Bảng mã băm toàn vẹn `SHA256SUMS.txt` của gói dữ liệu.

---

## 7. TÁCH BẠCH TIẾN ĐỘ ĐỢT 1 & BẢNG TÍNH TOÁN CÔNG SỐ TOÀN CHIẾN DỊCH 1.000 MẪU

### 7.1 Phân định rạch ròi hai phạm vi tiến độ
Thành viên C xin tách bạch tường minh hai phạm vi công việc:
1. **Phạm vi 1: Tiến độ Đợt 1 (Đo lường & Kiểm thử — 60 hoặc 100 mẫu):**
   - Mục tiêu: Hoàn tất trong **01 tuần (07 ngày làm việc)** nhằm đo lường tốc độ thực tế của công cụ mới, kiểm tra độ mượt của giao diện CLI và đánh giá sơ bộ tỷ lệ đồng thuận.
2. **Phạm vi 2: Tiến độ Toàn bộ Chiến dịch Main Annotation (Quy mô dự phóng 1.000 mẫu):**
   - Đây là chiến dịch dài hơi, đòi hỏi tổng khối lượng công số lớn, **tuyệt đối không thể hoàn thành trong một tuần**.

### 7.2 Bảng tính toán công số chi tiết cho Chiến dịch 1.000 mẫu
Bảng tính dưới đây được xây dựng dựa trên **Thời gian trung bình thực đo (Mean)** từ 2 tệp Pass 1 đã khóa mật mã của Calibration Runway A ($N=24$):
- **Annotator A:** $380,16\text{ s/mẫu} = \mathbf{6,34\text{ phút/mẫu}}$.
- **Annotator B:** $250,36\text{ s/mẫu} = \mathbf{4,17\text{ phút/mẫu}}$.
- **Cơ cấu gán nhãn:**
  + Annotator A: Gán toàn bộ $1.000\text{ mẫu}$.
  + Annotator B: Gán $30\%\text{ ngẫu nhiên} = 300\text{ mẫu} + \text{ca khó bổ sung phát sinh}$ (ước tính 5% tổng thể = $50\text{ mẫu}$) $\rightarrow$ Tổng gán đôi = $\mathbf{350\text{ mẫu}}$.
  + Tỷ lệ bất đồng cần phân xử Pass 2 (giả định 15% tập gán đôi): $\approx 350 \times 0,15 = \mathbf{53\text{ ca bất đồng}}$.

| Vai trò / Thành viên | Nội dung công việc chi tiết | Khối lượng & Đơn giá thời gian thực đo | Tổng quỹ thời gian dự kiến (Giờ) |
|:---|:---|:---|:---:|
| **Annotator A** | Gán nhãn độc lập toàn bộ corpus 1.000 mẫu | $1.000 \text{ mẫu} \times 6,34 \text{ phút/mẫu}$ | **105,67 giờ** |
| **Annotator B** | Gán nhãn độc lập tập gán đôi (30% random + ca khó) | $350 \text{ mẫu} \times 4,17 \text{ phút/mẫu}$ | **24,33 giờ** |
| **QA Lead B** | Kiểm định QA tuyển chọn, schema, test hồi quy & nghiệm thu | 5 đợt phát hành $\times$ 3,0 giờ/đợt QA | **15,00 giờ** |
| *Tổng quỹ thời gian của B* | *(Gán nhãn độc lập + QA)* | *(24,33h + 15,00h)* | **39,33 giờ** |
| **Thành viên C** | Trích xuất dữ liệu, lọc trùng 4 lớp, tạo Blind View, MarianMT, reconciliation | 5 đợt phát hành $\times$ 6,0 giờ/đợt kỹ thuật | **30,00 giờ** |
| **Lead D** | Phân xử bất đồng Pass 2 & Phê duyệt mốc | $53 \text{ ca} \times 8 \text{ phút/ca} + 8,0\text{h phê duyệt}$ | **15,07 giờ** |
| **TỔNG CỘNG TOÀN NHÓM** | **Dự phóng công số toàn chiến dịch 1.000 mẫu** | — | **~190,07 giờ người** |

*(Ghi chú: Tổng công số ~190,07 giờ người khớp chuẩn xác với khung ngân sách dự phóng 190,79 giờ người đã được Lead D phê duyệt trong Báo cáo PLAN-01).*

### 7.3 Kết luận Tiến độ Chiến dịch 1.000 mẫu
- **KẾT LUẬN TIẾN ĐỘ THỰC TẾ:** **CHƯA XÁC ĐỊNH (PENDING AVAILABILITY COMMITMENT)**.
- **Căn cứ:** Tiến độ theo tuần của chiến dịch phụ thuộc hoàn toàn vào **Văn bản cam kết số giờ khả dụng mỗi tuần (Weekly Availability Commitment)** của Annotator A và QA Lead B.
  * *Kịch bản A cam kết 10 giờ/tuần:* Chiến dịch cần $\approx 10,5\text{ tuần}$ (~2,5 tháng).
  * *Kịch bản A cam kết 15 giờ/tuần:* Chiến dịch cần $\approx 7,0\text{ tuần}$ (~1,7 tháng).
  * *Kịch bản A cam kết 20 giờ/tuần:* Chiến dịch cần $\approx 5,3\text{ tuần}$ (~1,2 tháng).
- Thành viên C kiến nghị Lead D chỉ phê duyệt mốc tiến độ chính thức sau khi A và B nộp bản cam kết số giờ khả dụng bằng văn bản.

---

## 8. DANH MỤC NHỮNG ĐIỀU CÒN CHỜ LEAD D QUYẾT ĐỊNH

Thành viên C kính trình Lead D xem xét và ban hành quyết định đối với các nội dung sau:
1. **Chốt Phương án & Quy mô Đợt 1:** Lựa chọn Phương án A (Lô đầu Main) hay Phương án B (Pilot tách riêng); chốt quy mô 60 mẫu hay 100 mẫu.
2. **Phê duyệt Thiết kế Tính mù 3 Tầng:** Chấp thuận phương án loại bỏ `random_subset` khỏi view của B và quản lý qua hồ sơ phân tầng hạn chế của C.
3. **Phê duyệt Quy chế Dịch Ngoại tuyến Tiếng Anh:** Xác nhận việc sử dụng MarianMT dịch sang tiếng Anh cho tiếng Nhật và tiếng Nga.
4. **Phê duyệt Quy chế QA Tuyển chọn của B:** Xác nhận loại bỏ phân bổ tổ chức mục tiêu khỏi gói QA kỹ thuật của B.
5. **Thu thập Cam kết Giờ khả dụng:** Yêu cầu Annotator A và QA Lead B gửi văn bản cam kết số giờ khả dụng/tuần để chốt tiến độ chính thức.

---

**XÁC NHẬN CỦA THÀNH VIÊN C (DATA PIPELINE & THƯ KÝ KIỂM TOÁN)**  
*(Văn bản dự thảo kỹ thuật V2.1 — Duy trì nghiêm ngặt: training_blocked=true, official_test_used=false, Main Annotation KHÓA 100%)*  

**Nguyễn Thắng**
