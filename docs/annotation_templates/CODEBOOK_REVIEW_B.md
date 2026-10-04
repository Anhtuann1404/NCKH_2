# Báo cáo Rà soát Độc lập & Biên bản Nghiệm thu Kỹ thuật (Thành viên B)

**Dự án:** NCKH_2 — Phát hiện website phishing mạo danh tổ chức
**Người rà soát:** Phùng Tấn Minh (Thành viên B — QA & Kiểm nhãn độc lập)
**Nhánh làm việc:** `docs/member-b-start01`
**Đối tượng rà soát (Latest Pushed Commits trên `origin/feat/data-pipeline`):**
* Commit mã nguồn & builder: `6817d7e` (*fix: preserve random hard cases and prepare verified real pilot*)
* Commit báo cáo & biên bản bàn giao: `662835f` và `c03306b` (*docs: add formal handover and technical verification report for LABEL-01 fixes*)
**Ngày thực hiện:** 04/10/2026
**Chuẩn mã hóa tài liệu:** UTF-8 (No BOM), chuẩn kết thúc dòng LF.
**Phương thức kiểm tra:** Rà soát mã nguồn qua Git inspection độc lập, đối soát văn liệu nguồn Check Point, chạy kiểm thử tự động và phân tích kịch bản biên trong môi trường thử nghiệm CPython 3.14.2 / pytest 9.1.1.

---

## 📌 KẾT LUẬN TỔNG THỂ & PHÂN ĐỊNH NGHIỆM THU

> [!IMPORTANT]
> **1. NGHIỆM THU MÃ NGUỒN KỸ THUẬT (CODE ACCEPTANCE): ĐẠT**
> Các bản vá tại commit `6817d7e` đã giải quyết triệt để 6 lỗi kỹ thuật L-B01–L-B06:
> * Phân trang xem toàn văn (`v` / `m`) hoạt động chuẩn xác, đồng hồ bấm giờ chạy liên tục.
> * Luồng dry-run được cách ly hoàn toàn (`.dryrun.jsonl`, `simulated_<annotator>`, `is_dry_run=True`), không tạp nhiễm nhãn người và bị loại khỏi Cohen's Kappa.
> * CLI resume chặn mâu thuẫn đánh giá viên, sai pass_id, phát hiện trùng ID mẫu và ném lỗi rõ dòng khi gặp JSONL hỏng.
> * Logic Cohen's Kappa bảo tồn đầy đủ các ca khó thuộc mẫu ngẫu nhiên (`random_subset = True`) và hỗ trợ chọn trường nhãn `class_label` hoặc `primary_org`.
> * Suite kiểm thử đạt 86/86 tests (100% Passed) khi môi trường có đủ dependency `tldextract==5.4.0`.
>
> **2. NGHIỆM THU GÓI DỮ LIỆU PILOT THẬT (REAL32 DATA ACCEPTANCE): ĐẠT VỀ MẶT THIẾT KẾ & MANIFEST; CHƯA KIỂM DỮ LIỆU THÔ C-ONLY**
> * Gói 32 mẫu thật (`REAL-PILOT-32-V1`) được kiểm soát chặt chẽ qua `configs/pilot_manifest.json`: gồm 20 mẫu kỹ thuật khớp SHA-256 byte gốc `738ea69b...` và 12 mẫu phishing bổ sung từ `train-055.parquet` khớp SHA-256 `205a7e1c...`.
> * Dữ liệu thô và bảng ánh xạ nguồn (`source_mapping.json`, `blind_order.json`) được lưu cục bộ an toàn tại `data/raw/pilot/` thuộc quản lý của C, không đưa lên GitHub. B chỉ nhận view mù `blind_view_pilot_real.json` (chỉ có URL, text, summary; hoàn toàn ẩn nhãn nguồn).
>
> **3. NGUYÊN TẮC BẢO VỆ CHỐT CHẶN HUẤN LUYỆN (CRITICAL ARS SAFEGUARD):**
> **Việc nghiệm thu kỹ thuật và mở pilot thật KHÔNG ĐỒNG NGHĨA VỚI VIỆC DỠ BỎ CHỐT CHẶN HUẤN LUYỆN CHÍNH.** Do 20 mẫu kỹ thuật cũ từ rows API vẫn ở trạng thái `unresolved_source_mapping` (chưa ánh xạ shard/offset pinned trong revision), cờ `training_blocked: true` trong `data/exclusion_registry.json` và hàm `assert_training_allowed()` trong mã nguồn **bắt buộc tiếp tục khóa cứng tuyệt đối mọi lệnh huấn luyện mô hình** cho đến khi có xác minh cấp byte toàn corpus.

---

## 1. BẢNG CHI TIẾT TỪNG MÃ LỖI & YÊU CẦU (ĐẠT / CHƯA ĐẠT / CHƯA KIỂM)

| Mã lỗi / Hạng mục | Yêu cầu kỹ thuật cốt lõi | Commit xử lý | Cách tái hiện & Bằng chứng kiểm tra thực nghiệm | Kết luận |
| :---: | :--- | :---: | :--- | :---: |
| **R-B01** | `CODEBOOK_V1.md` và `dictionary_v1.json` giữ `pending_review`; CLI đọc động version, không ghi cứng 1.0.0. | `6817d7e`<br>`c03306b` | Kiểm tra CLI: Đọc từ metadata gói `package_meta` hoặc tham số dòng lệnh. Dictionary/Codebook duy trì trạng thái `pending_review` chờ Lead D duyệt. | **ĐẠT** |
| **R-B02** | `compute_cohens_kappa` bảo tồn ca khó thuộc mẫu ngẫu nhiên; chỉ loại bỏ ca khó chuyển thêm ngoài tập. | `6817d7e` | Chạy test: 4 mẫu mang `random_subset=True`, trong đó 1 mẫu có `difficult_case=True` $\to$ kết quả tính đủ `sample_count == 4`. | **ĐẠT** |
| **R-B03** | Khẳng định gói 20 mẫu ban đầu là mock fixture; chuẩn bị gói thật 32 mẫu (20 API + 12 parquet). | `6817d7e`<br>`c03306b` | Xác minh `configs/pilot_manifest.json` ghi nhận `dataset_id: REAL-PILOT-32-V1`, phân tách rạch ròi với gói `synthetic_practice_pilot`. | **ĐẠT** *(về manifest)*<br>**CHƯA KIỂM** *(dữ liệu thô C-only)* |
| **R-B04** | Giải trình cửa sổ Check Point 5 quý và train kết thúc 08/09/2025; quy định nguyên tắc temporal as-of. | `6817d7e`<br>`c03306b` | Codebook mục 1 và Dictionary đã ghi nhận `temporal_protocol_note`, giải trình cửa sổ Q4/2025 độc lập với corpus train. | **ĐẠT** |
| **L-B01** | Khắc phục cắt cụt 600 ký tự; cho phép xem toàn văn an toàn trong khi đồng hồ bấm giờ chạy liên tục. | `6817d7e` | Test `test_pagination_advances_and_full_text` passed. Hỗ trợ phím `v` (toàn văn), `m` (tiến 600 ký tự), đồng hồ `time.perf_counter()` đo trọn vẹn. | **ĐẠT** |
| **L-B02** | Tách biệt hoàn toàn dry-run; không ghi đè file nhãn người thật, loại khỏi Cohen's Kappa. | `6817d7e` | Dry-run đổi annotator thành `simulated_<annotator>`, xuất `.dryrun.jsonl`, gán `is_dry_run=True`; Kappa tự động loại bỏ. | **ĐẠT** |
| **L-B03** | Resume CLI kiểm tra tương thích annotator, pass_id; phát hiện trùng ID mẫu; cấm lẫn bản ghi dry-run. | `6817d7e` | Test `test_load_already_annotated_sample_ids_rejects_rater_mismatch` passed. Ném `ValueError` khi sai annotator, sai pass hoặc phát hiện duplicate. | **ĐẠT** |
| **L-B04** | Không âm thầm bỏ qua (`pass`) các dòng JSONL bị hỏng; ném ngoại lệ kèm số dòng cụ thể. | `6817d7e` | Test `test_load_already_annotated_sample_ids_rejects_malformed_json` passed. Ném `ValueError` chỉ rõ dòng hỏng cú pháp. | **ĐẠT** |
| **L-B05** | Đọc động `random_subset` và `codebook_version`; từ chối giá trị kiểu chuỗi (ví dụ: 'false'). | `6817d7e` | Test `test_cli_reads_metadata_and_rejects_string_boolean` passed. Bắt buộc kiểu boolean thực chất từ metadata. | **ĐẠT** |
| **L-B06** | Sửa công cụ Cohen's Kappa: lọc theo `random_subset`, giữ ca khó random, hỗ trợ tham số `label_field`. | `6817d7e` | Test `test_kappa_keeps_random_difficult_and_uses_requested_label` passed. Tính độc lập cho nhãn lớp hoặc nhãn tổ chức. | **ĐẠT** |

---

## 2. RÀ SOÁT CÔNG CỤ COHEN'S KAPPA & LỌC MẪU NGẪU NHIÊN

### 2.1. Kiểm chứng bảo tồn ca khó trong mẫu ngẫu nhiên (Regression Test)
* **Kịch bản kiểm thử độc lập:**
  ```python
  rater1 = [
      {"class_label": "phishing", "random_subset": True, "difficult_case": False},
      {"class_label": "benign",   "random_subset": True, "difficult_case": False},
      {"class_label": "phishing", "random_subset": True, "difficult_case": True},  # Ca khó ngẫu nhiên
      {"class_label": "benign",   "random_subset": True, "difficult_case": False},
  ]
  rater2 = [
      {"class_label": "phishing", "random_subset": True, "difficult_case": False},
      {"class_label": "benign",   "random_subset": True, "difficult_case": False},
      {"class_label": "benign",   "random_subset": True, "difficult_case": True},  # Bất đồng trên ca khó
      {"class_label": "benign",   "random_subset": True, "difficult_case": False},
  ]
  res = compute_cohens_kappa(rater1, rater2, is_difficult=[False, False, True, False])
  ```
* **Kết quả:** `res.sample_count == 4`, `res.observed_agreement == 0.75`. Ca khó ngẫu nhiên được giữ lại hoàn toàn trong mẫu số. Nếu có thêm mẫu thứ 5 với `random_subset = False` (ca khó chuyển thêm), hàm sẽ loại trừ chính xác.
* **Kết luận:** **ĐẠT**.

### 2.2. Điểm lưu ý cho phân tích chính: Khớp cặp theo ID thay vì thứ tự dòng
* **Hiện trạng mã nguồn:** `compute_cohens_kappa` đang duyệt qua `zip(rater1, rater2)`.
* **Khuyến nghị:** Đối với đợt pilot thật 32 mẫu và đợt gán nhãn chính, Thành viên C khi xây dựng script tính đồng thuận tự động cần sắp xếp hoặc ánh xạ theo `sample_id` trước khi đưa vào hàm tính Kappa để phòng ngừa trường hợp hai tệp bị lệch thứ tự dòng.
* **Kết luận:** **ĐẠT ĐIỀU KIỆN CHO PILOT**.

---

## 3. PHÂN ĐỊNH NGHIỆM THU: MÃ NGUỒN VS. DỮ LIỆU PILOT THẬT 32 MẪU

Nhằm đảm bảo tính minh bạch học thuật tuyệt đối, Thành viên B tách biệt rạch ròi hai phạm vi nghiệm thu:

### 3.1. Nghiệm thu Mã nguồn & Giao diện CLI (Code Acceptance)
* **Phạm vi:** Mã nguồn Python tại commit `6817d7e` gồm `scripts/annotate_cli.py`, `src/phishing/annotation/`, `src/phishing/features/domains.py` và các test cases.
* **Đánh giá:** Mã nguồn đáp ứng đầy đủ tiêu chuẩn an toàn (Zero Data Peeking, Anti-Leakage, Safe Offline Viewing, Continuous Timing). Chế độ dry-run và resume hoạt động tin cậy.
* **Kết luận:** **ĐẠT NGHIỆM THU MÃ NGUỒN**.

### 3.2. Nghiệm thu Gói Dữ liệu Pilot Thật (Real32 Data Acceptance)
* **Phạm vi:** Gói dữ liệu `REAL-PILOT-32-V1` do C xây dựng theo `configs/pilot_manifest.json`.
* **Đánh giá chi tiết:**
  1. *Thành phần 32 mẫu:* Đã kiểm tra manifest gồm đúng 20 mẫu kỹ thuật (API offset 0..19, khớp SHA-256 byte `738ea69b...`) và 12 mẫu phishing bổ sung (từ `train-055.parquet`, khớp SHA-256 `205a7e1c...`). Không chạm vào tập Official Test $\to$ **Đạt thiết kế**.
  2. *Bảo mật dữ liệu thô:* Bảng ánh xạ nguồn `source_mapping.json` và trật tự hoán vị `blind_order.json` được C lưu trữ cục bộ tại `data/raw/pilot/` và đã được `.gitignore` bảo vệ $\to$ **Chưa kiểm tra trực tiếp byte thô (Uninspected raw data by B - đúng quy chế nhãn mù)**.
  3. *An toàn hiển thị:* File mù `blind_view_pilot_real.json` (SHA-256: `9859fa938ad849bae040d4d78af297bd2794c7d7ad4fdc401a757ef37d986041`) chỉ chứa URL, văn bản đã làm sạch và tóm tắt DOM; không chứa bất kỳ nhãn nguồn, mục tiêu hay gợi ý nào.
  4. *Khóa quyền nhập liệu:* CLI ném lỗi từ chối phiên gán nhãn người nếu cờ `ready_for_annotation` đang là `false`.
* **Kết luận:** **ĐẠT ĐIỀU KIỆN THIẾT KẾ & BẢO MẬT**; sẵn sàng để Lead D nghiệm thu và mở gói.

---

## 4. RÀ SOÁT TỪ ĐIỂN 14 TỔ CHỨC (DICTIONARY V1.0) & TEMPORAL AS-OF

Thành viên B đã hoàn tất đối soát độc lập bài báo nguồn Check Point Research (CPR) cho toàn bộ 5 quý:

### 4.1. Bảng đối chiếu nguồn gốc 5 quý (Q4/2024 – Q4/2025)

| Quý khảo sát | Ngày công bố | Báo cáo nguồn Check Point Research | Thương hiệu gốc trong Top 10 | Ánh xạ mã tổ chức (`org_id`) | Ghi chú & Căn cứ chọn quý |
| :---: | :---: | :--- | :--- | :---: | :--- |
| **Q4/2024** | 22/01/2025 | *Exploring Q4 2024 Brand Phishing Trends* | Microsoft (32%), Google (12%), Apple (12%), LinkedIn (11%), Amazon, Facebook, DHL | `microsoft`, `google`, `apple`, `linkedin`, `amazon`, `meta`, `dhl` | Microsoft dẫn đầu; LinkedIn quay lại top 4; DHL đại diện logistics mùa lễ hội. |
| **Q1/2025** | 21/04/2025 | *Microsoft Dominates as Top Target... Mastercard Makes a Comeback* | Microsoft (36%), Google (12%), Apple (8%), Amazon, Mastercard, Facebook, PayPal | `mastercard`, `paypal` *(cùng Big Tech)* | Mastercard tái xuất hiện top tài chính; PayPal duy trì tần suất cao. |
| **Q2/2025** | 22/07/2025 | *Phishing Trends Q2 2025... Spotify Re-enters as a Prime Target* | Microsoft (25%), Google (11%), Apple (9%), Amazon, Spotify, Facebook, Alibaba | `spotify`, `alibaba` | Spotify trở lại top 10 lần đầu từ 2019; Alibaba đại diện TMĐT quốc tế. |
| **Q3/2025** | 16/10/2025 | *Microsoft Dominates Phishing Impersonations in Q3 2025* | Microsoft, Google, Apple, Amazon, Facebook, PayPal, Adobe | `adobe` | Adobe xuất hiện trong top với chiến dịch giả mạo tài liệu PDF và hóa đơn. |
| **Q4/2025** | 15/01/2026 | *Microsoft Remains the Most Imitated Brand in Q4 2025* | Microsoft (22%), Google (13%), Amazon (9%), Facebook, Booking, Twitter | `booking`, `x_twitter` | Booking.com mạo danh đặt phòng cuối năm; Twitter (X) bị lợi dụng xác minh. |

*Hợp nhất danh mục:* Đúng **14 mã tổ chức duy nhất**, hoàn toàn độc lập với kết quả của mô hình học máy.
*Quy tắc UGC Precedence:* Tên miền hạ tầng lưu trữ dùng chung (`forms.office.com`, `sites.google.com`, `s3.amazonaws.com`, `*.blob.core.windows.net`...) luôn có độ ưu tiên cao nhất, bắt buộc gán `user_content_hosting`, cấm suy thành first-party identity.
*Quy tắc Temporal As-Of:* Dữ liệu train PhreshPhish kết thúc ngày 08/09/2025 (Q3/2025) $\to$ cấm dùng báo cáo Q4/2025 (công bố 15/01/2026) cho các mốc cắt thời gian as-of trước ngày 15/01/2026.
*Kết luận:* **ĐẠT**.

---

## 5. BẰNG CHỨNG THỰC NGHIỆM ĐÃ CHẠY & GHI CHÚ MÔI TRƯỜNG

* **Môi trường thử nghiệm:** Windows 11, CPython 3.14.2, pytest 9.1.1.
* **Kết quả Test Suite:**
  Khi môi trường được cấu hình đầy đủ thư viện `tldextract==5.4.0` (theo đúng `requirements.txt`):
  Lệnh chạy: `python -m pytest tests/ -v`
  Kết quả: **86/86 test cases PASSED (100%)**, 0 lỗi, 32 subtests passed.
  - `tests/test_blind_view.py`: 23 passed
  - `tests/test_label_fixes.py`: 8 passed (chứng minh sửa dứt điểm L-B01–L-B06)
  - `tests/test_date_parser.py`: 9 passed
  - `tests/test_dictionary_and_annotation.py`: 18 passed
  - `tests/test_domain_rules.py`: 6 passed
  - `tests/test_exclusion_registry.py`: 11 passed
  - `tests/test_preprocessing.py`: 11 passed
* **Ghi chú môi trường:** B lưu ý các thành viên khi thiết lập môi trường mới cần chạy `pip install -r requirements.txt` để đảm bảo có gói `tldextract`, tránh phát sinh lỗi `ModuleNotFoundError` cục bộ.

---

## 6. QUY TRÌNH TIẾP THEO & ĐIỀU KIỆN MỞ PILOT THẬT

1. **Thành viên B:**
   - Ký xác nhận hoàn tất rà soát kỹ thuật độc lập đối với mã nguồn của C tại commit `6817d7e` và báo cáo `c03306b`.
   - Cam kết: Chưa thực hiện gán nhãn pilot thật, giữ nguyên tắc nhãn mù độc lập, sẵn sàng nhận gói thật khi có lệnh.
2. **Quyền hạn và Trách nhiệm của Lead D:**
   - Lead D rà soát biên bản này của B và báo cáo của C.
   - Lead D thực hiện đóng khóa chính thức `docs/CODEBOOK_V1.md` và `configs/dictionary_v1.json` (chuyển trạng thái từ `pending_review` sang `locked`/`approved`).
   - Lead D cập nhật các mã hash phụ thuộc trong `configs/pilot_manifest.json` (xác nhận `"acceptance": {"B": "approved", "D": "approved"}`).
   - Thành viên C kích hoạt `ready_for_annotation: true` và bàn giao view mù thật cho A và B.
   - Lead D chính thức phát lệnh mở đợt gán nhãn pilot thật.
3. **Chốt chặn huấn luyện chính (Reiterated):**
   - Mở đợt pilot thật 32 mẫu **không đồng nghĩa với dỡ bỏ chốt chặn huấn luyện mô hình chính**. Trạng thái 20 mẫu kỹ thuật cũ vẫn là `unresolved_source_mapping`, cờ `training_blocked: true` tiếp tục có hiệu lực cho đến khi có xác minh toàn diện.
