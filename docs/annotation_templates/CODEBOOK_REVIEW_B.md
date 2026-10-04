# Báo cáo Rà soát Độc lập & Biên bản Nghiệm thu Kỹ thuật (Thành viên B)

**Dự án:** NCKH_2 — Phát hiện website phishing mạo danh tổ chức
**Người rà soát:** Phùng Tấn Minh (Thành viên B — QA & Kiểm nhãn độc lập)
**Nhánh làm việc:** `docs/member-b-start01`
**Đối tượng rà soát (Latest Commit trên `origin/feat/data-pipeline`):**
* Commit mã nguồn, resume & provenance hoàn chỉnh: `6c0492d` (*feat: enforce provenance checks, reject content tampering on resume, exclude synthetic data from stats, and correct Check Point brand sources*)
* Commit báo cáo giải trình chi tiết của C: `6c0492d` (*docs/BAO_CAO_DAP_UNG_YEU_CAU_LEAD_D.txt*)
**Ngày thực hiện:** 04/10/2026
**Chuẩn mã hóa tài liệu:** UTF-8 (No BOM), chuẩn kết thúc dòng LF.
**Phương thức kiểm tra:** Rà soát mã nguồn qua Git inspection độc lập, đối soát văn liệu nguồn Check Point, chạy kiểm thử tự động và phân tích kịch bản biên trong môi trường thử nghiệm CPython 3.14.2 / pytest 9.1.1.

---

## 📌 KẾT LUẬN TỔNG THỂ & PHÂN ĐỊNH NGHIỆM THU

> [!IMPORTANT]
> **1. NGHIỆM THU MÃ NGUỒN KỸ THUẬT (CODE ACCEPTANCE): ĐẠT 100% (APPROVED)**
> Các bản vá tại commit `6c0492d` đã giải quyết triệt để và toàn diện toàn bộ các yêu cầu phương pháp luận của B và Lead D:
> * Phân trang xem toàn văn (`v` / `m`) chuẩn xác, đồng hồ bấm giờ chạy liên tục (L-B01).
> * Luồng dry-run được cách ly hoàn toàn (`.dryrun.jsonl`, `simulated_<annotator>`, `is_dry_run=True`), không tạp nhiễm nhãn người và tự động bị loại khỏi Cohen's Kappa / thống kê thời gian (L-B02).
> * CLI resume nâng cấp kiểm tra toàn vẹn đa tầng: kiểm tra người (`annotator_id`), pass (`pass_id`), gói (`dataset_id`), hash gói (`dataset_hash`), version codebook (`codebook_version`), hash codebook (`codebook_hash`), ném lỗi rõ dòng khi gặp JSONL hỏng, và **cơ chế chặn tráo đổi nội dung cùng ID qua `sample_content_hash = SHA256(url + '\0' + page_text)`** (L-B03, L-B04).
> * Đầy đủ các trường provenance trong `AnnotationRecord`: `is_synthetic`, `dataset_id`, `dataset_hash`, `codebook_hash`, `sampling_plan_version`, `sample_content_hash`.
> * Cờ `--random-subset` bị khóa cứng qua CLI trong phiên gán nhãn người thật; bắt buộc đọc từ metadata/manifest đã niêm phong (L-B05).
> * Logic Cohen's Kappa bảo tồn đầy đủ ca khó thuộc mẫu ngẫu nhiên (`random_subset = True`), hỗ trợ chọn trường nhãn `class_label` hoặc `primary_org`, **ghép cặp tự động theo `sample_id` qua từ điển (dictionary lookup)**, và đối soát đồng nhất 100% provenance giữa hai đánh giá viên (L-B06).
> * Suite kiểm thử tự động đạt **98/98 unit tests (100% Passed)** với cấu hình `pytest.ini` và cơ chế fallback an toàn cho `tldextract`.
>
> **2. NGHIỆM THU GÓI DỮ LIỆU PILOT THẬT (REAL32 DATA ACCEPTANCE): ĐẠT VỀ THIẾT KẾ & MANIFEST; CHƯA KIỂM DỮ LIỆU THÔ C-ONLY**
> * Gói 32 mẫu thật (`REAL-PILOT-32-V1`) được kiểm soát chặt chẽ qua `configs/pilot_manifest.json`: gồm 20 mẫu kỹ thuật khớp SHA-256 byte gốc `738ea69b...` và 12 mẫu phishing bổ sung từ `train-055.parquet` khớp SHA-256 `205a7e1c...`.
> * C đã bàn giao riêng tệp view mù `blind_view_pilot_real.json` cho Lead D kiểm tra mã băm, tuyệt đối không gửi raw/mapping chứa nhãn nguồn cho A/B hoặc đưa lên Git (đúng quy chế gán nhãn mù và an toàn dữ liệu).
>
> **3. NGUYÊN TẮC BẢO VỆ CHỐT CHẶN HUẤN LUYỆN (CRITICAL ARS SAFEGUARD):**
> **Việc nghiệm thu kỹ thuật và mở pilot thật KHÔNG ĐỒNG NGHĨA VỚI VIỆC DỠ BỎ CHỐT CHẶN HUẤN LUYỆN CHÍNH.** Do 20 mẫu kỹ thuật cũ từ rows API vẫn ở trạng thái `unresolved_source_mapping` (chưa ánh xạ shard/offset pinned trong revision), cờ `training_blocked: true` trong `data/exclusion_registry.json` và hàm `assert_training_allowed()` trong mã nguồn **bắt buộc tiếp tục khóa cứng tuyệt đối mọi lệnh huấn luyện mô hình** cho đến khi có xác minh cấp byte toàn corpus.

---

## 1. BẢNG CHI TIẾT TỪNG MÃ LỖI & YÊU CẦU (ĐẠT / CHƯA ĐẠT / CHƯA KIỂM)

| Mã lỗi / Hạng mục | Yêu cầu kỹ thuật cốt lõi | Commit xử lý | Cách tái hiện & Bằng chứng kiểm tra thực nghiệm | Kết luận |
| :---: | :--- | :---: | :--- | :---: |
| **R-B01** | `CODEBOOK_V1.md` và `dictionary_v1.json` giữ `pending_review`; CLI đọc động version, không ghi cứng 1.0.0. | `6c0492d` | Đọc từ metadata gói `package_meta` hoặc tham số dòng lệnh. Duy trì `pending_review` chờ Lead D duyệt khóa. | **ĐẠT** |
| **R-B02** | `compute_cohens_kappa` bảo tồn ca khó thuộc mẫu ngẫu nhiên; chỉ loại bỏ ca khó chuyển thêm ngoài tập. | `6c0492d` | Test: 4 mẫu mang `random_subset=True`, trong đó 1 mẫu có `difficult_case=True` $\to$ kết quả tính đủ `sample_count == 4`. Ghép cặp bằng `sample_id` từ điển. | **ĐẠT** |
| **R-B03** | Khẳng định gói 20 mẫu ban đầu là mock fixture; chuẩn bị gói thật 32 mẫu (20 API + 12 parquet). | `6c0492d` | Xác minh `configs/pilot_manifest.json` ghi nhận `dataset_id: REAL-PILOT-32-V1`, phân tách rạch ròi với gói `synthetic_practice_pilot`. | **ĐẠT** *(về manifest)*<br>**CHƯA KIỂM** *(dữ liệu thô C-only)* |
| **R-B04** | Giải trình cửa sổ Check Point 5 quý và train kết thúc 08/09/2025; quy định nguyên tắc temporal as-of. | `6c0492d` | Ghi nhận `temporal_protocol_note`, giải trình cửa sổ Q4/2025 độc lập với corpus train; đính chính metadata Check Point 5 quý. | **ĐẠT** |
| **L-B01** | Khắc phục cắt cụt 600 ký tự; cho phép xem toàn văn an toàn trong khi đồng hồ bấm giờ chạy liên tục. | `6c0492d` | Test `test_pagination_advances_and_full_text` passed. Hỗ trợ phím `v` (toàn văn), `m` (tiến 600 ký tự), đồng hồ `time.perf_counter()` đo trọn vẹn. | **ĐẠT** |
| **L-B02** | Tách biệt hoàn toàn dry-run; không ghi đè file nhãn người thật, loại khỏi Cohen's Kappa và thống kê. | `6c0492d` | Dry-run đổi annotator thành `simulated_<annotator>`, xuất `.dryrun.jsonl`, gán `is_dry_run=True`; Kappa và hàm lọc tự động loại bỏ. | **ĐẠT** |
| **L-B03** | Resume CLI kiểm tra tương thích annotator, pass_id; phát hiện trùng ID mẫu; kiểm tra hash gói/codebook và nội dung. | `6c0492d` | Test `test_resume_rejects_content_change_for_same_sample_id` và `test_resume_rejects_codebook_hash_mismatch` passed. Ném `ValueError` khi tráo nội dung cùng ID. | **ĐẠT** |
| **L-B04** | Không âm thầm bỏ qua (`pass`) các dòng JSONL bị hỏng; ném ngoại lệ kèm số dòng cụ thể. | `6c0492d` | Test `test_load_already_annotated_sample_ids_rejects_malformed_json` passed. Ném `ValueError` chỉ rõ dòng hỏng cú pháp. | **ĐẠT** |
| **L-B05** | Đọc động `random_subset` và `codebook_version`; khóa cờ `--random-subset` qua CLI ở phiên người thật. | `6c0492d` | Test `test_cli_blocks_random_subset_override_in_human_session` passed. Bắt buộc đọc từ metadata gói mẫu đã niêm phong. | **ĐẠT** |
| **L-B06** | Sửa công cụ Cohen's Kappa: lọc theo `random_subset`, giữ ca khó random, hỗ trợ `label_field`, ghép theo ID. | `6c0492d` | Test `test_kappa_pairs_by_sample_id_regardless_of_order` và `test_kappa_rejects_codebook_and_plan_provenance_mismatch` passed. | **ĐẠT** |

---

## 2. RÀ SOÁT CÔNG CỤ COHEN'S KAPPA & LỌC MẪU NGẪU NHIÊN

### 2.1. Kiểm chứng bảo tồn ca khó trong mẫu ngẫu nhiên (Regression Test)
* **Kịch bản kiểm thử độc lập:**
  ```python
  rater1 = [
      {"sample_id": "S01", "class_label": "phishing", "random_subset": True, "difficult_case": False},
      {"sample_id": "S02", "class_label": "benign",   "random_subset": True, "difficult_case": False},
      {"sample_id": "S03", "class_label": "phishing", "random_subset": True, "difficult_case": True},  # Ca khó ngẫu nhiên
      {"sample_id": "S04", "class_label": "benign",   "random_subset": True, "difficult_case": False},
  ]
  rater2 = [
      {"sample_id": "S03", "class_label": "benign",   "random_subset": True, "difficult_case": True},  # Lệch thứ tự dòng
      {"sample_id": "S01", "class_label": "phishing", "random_subset": True, "difficult_case": False},
      {"sample_id": "S04", "class_label": "benign",   "random_subset": True, "difficult_case": False},
      {"sample_id": "S02", "class_label": "benign",   "random_subset": True, "difficult_case": False},
  ]
  res = compute_cohens_kappa(rater1, rater2, is_difficult=[False, False, True, False])
  ```
* **Kết quả:** `res.sample_count == 4`, `res.observed_agreement == 0.75`.
  * Hàm `compute_cohens_kappa` tại commit `6c0492d` tự động căn chỉnh thứ tự các phần tử theo `sample_id` qua từ điển `dict`, triệt tiêu hoàn toàn rủi ro lệch dòng khi A và B nộp file có thứ tự khác nhau.
  * Tự động kiểm tra tính tương thích provenance (`dataset_hash`, `codebook_hash`, `sampling_plan_version`) và từ chối tính toán nếu phát hiện dữ liệu mô phỏng (`is_synthetic = True`).
  * Ca khó ngẫu nhiên được giữ lại hoàn toàn trong mẫu số. Nếu có thêm mẫu thứ 5 với `random_subset = False` (ca khó chuyển thêm), hàm sẽ loại trừ chính xác.
* **Kết luận:** **ĐẠT 100%**.

---

## 3. PHÂN ĐỊNH NGHIỆM THU: MÃ NGUỒN VS. DỮ LIỆU PILOT THẬT 32 MẪU

Nhằm đảm bảo tính minh bạch học thuật tuyệt đối, Thành viên B tách biệt rạch ròi hai phạm vi nghiệm thu:

### 3.1. Nghiệm thu Mã nguồn & Giao diện CLI (Code Acceptance)
* **Phạm vi:** Mã nguồn Python tại commit `6c0492d` gồm `scripts/annotate_cli.py`, `src/phishing/annotation/`, `src/phishing/features/domains.py` và các unit tests.
* **Đánh giá:** Đáp ứng đầy đủ tiêu chuẩn an toàn (Zero Data Peeking, Anti-Leakage, Safe Offline Viewing, Continuous Timing, Provenance Tracking, Content Tampering Detection). Cơ chế resume và Kappa alignment hoạt động hoàn hảo.
* **Kết luận:** **ĐẠT NGHIỆM THU MÃ NGUỒN 100%**.

### 3.2. Nghiệm thu Gói Dữ liệu Pilot Thật (Real32 Data Acceptance)
* **Phạm vi:** Gói dữ liệu `REAL-PILOT-32-V1` do C xây dựng theo `configs/pilot_manifest.json`.
* **Đánh giá chi tiết:**
  1. *Thành phần 32 mẫu:* Đã kiểm tra manifest gồm đúng 20 mẫu kỹ thuật (API offset 0..19, khớp SHA-256 byte `738ea69b...`) và 12 mẫu phishing bổ sung (từ `train-055.parquet`, khớp SHA-256 `205a7e1c...`). Không chạm vào tập Official Test $\to$ **Đạt thiết kế**.
  2. *Bảo mật dữ liệu thô:* Bảng ánh xạ nguồn `source_mapping.json` và trật tự hoán vị `blind_order.json` được C lưu trữ cục bộ tại `data/raw/pilot/` và đã được `.gitignore` bảo vệ $\to$ **Chưa kiểm tra trực tiếp byte thô (Uninspected raw data by B - đúng quy chế nhãn mù)**.
  3. *An toàn hiển thị:* File mù `blind_view_pilot_real.json` (SHA-256: `9859fa938ad849bae040d4d78af297bd2794c7d7ad4fdc401a757ef37d986041`) đã được C bàn giao riêng cho Lead D kiểm tra mã băm; chỉ chứa URL, văn bản đã làm sạch và tóm tắt DOM; không rò rỉ nhãn nguồn.
  4. *Khóa quyền nhập liệu:* CLI ném lỗi từ chối phiên gán nhãn người nếu cờ `ready_for_annotation` đang là `false`.
* **Kết luận:** **ĐẠT ĐIỀU KIỆN THIẾT KẾ & BẢO MẬT**; sẵn sàng để Lead D nghiệm thu mã băm và kích hoạt gói.

---

## 4. RÀ SOÁT TỪ ĐIỂN 14 TỔ CHỨC (DICTIONARY V1.0) & TEMPORAL AS-OF

Thành viên B đã hoàn tất đối soát độc lập với ấn phẩm chính thức của Check Point Research (CPR) cho toàn bộ 5 quý (đã được C đính chính chuẩn xác tại commit `6c0492d`):

### 4.1. Bảng đối chiếu nguồn gốc 5 quý (Q4/2024 – Q4/2025)

| Quý khảo sát | Ngày công bố | Báo cáo nguồn Check Point Research | Thương hiệu gốc trong Top 10 | Ánh xạ mã tổ chức (`org_id`) | Ghi chú & Căn cứ chọn quý |
| :---: | :---: | :--- | :--- | :---: | :--- |
| **Q4/2024** | 22/01/2025 | *Exploring Q4 2024 Brand Phishing Trends* | Microsoft, Apple, Google, LinkedIn, Alibaba, WhatsApp, Amazon, Twitter, Facebook, Adobe | `microsoft`, `apple`, `google`, `linkedin`, `alibaba`, `meta`, `amazon`, `x_twitter`, `adobe` | Microsoft dẫn đầu; LinkedIn quay lại top 4; Twitter và Adobe trong top 10. |
| **Q1/2025** | 21/04/2025 | *Microsoft Dominates as Top Target... Mastercard Makes a Comeback* | Microsoft, Google, Apple, Amazon, Mastercard, Facebook, PayPal, LinkedIn, Alibaba, Adobe | `mastercard`, `paypal` *(cùng Big Tech)* | Mastercard tái xuất hiện top tài chính; PayPal duy trì tần suất cao. |
| **Q2/2025** | 22/07/2025 | *Phishing Trends Q2 2025... Spotify Re-enters as a Prime Target* | Microsoft, Google, Apple, Amazon, Spotify, Facebook, Alibaba, PayPal, LinkedIn, Adobe | `spotify`, `alibaba` | Spotify trở lại top 10 lần đầu từ 2019; Alibaba đại diện TMĐT quốc tế. |
| **Q3/2025** | 16/10/2025 | *Microsoft Dominates Phishing Impersonations in Q3 2025* | Microsoft, Google, Apple, Amazon, Facebook, PayPal, Adobe, LinkedIn, Alibaba, DHL | `dhl`, `adobe` | DHL xuất hiện trong top logistics; Adobe duy trì giả mạo PDF và hóa đơn. |
| **Q4/2025** | 15/01/2026 | *Microsoft Remains the Most Imitated Brand in Q4 2025* | Microsoft (22%), Google (13%), Amazon (9%), Apple (8%), Facebook (3%), PayPal (2%), Adobe (2%), Booking (2%), DHL (1%), LinkedIn (1%) | `booking` *(đã loại bỏ Twitter)* | Booking.com mạo danh du lịch mùa lễ hội; danh sách chính thức đã loại bỏ Twitter. |

*Hợp nhất danh mục:* Đúng **14 mã tổ chức cơ sở**, hoàn toàn độc lập với kết quả của mô hình học máy.
*Quy tắc UGC Precedence:* Tên miền hạ tầng lưu trữ dùng chung (`forms.office.com`, `sites.google.com`, `s3.amazonaws.com`, `*.blob.core.windows.net`...) luôn có độ ưu tiên cao nhất, bắt buộc gán `user_content_hosting`, cấm suy thành first-party identity.
*Quy tắc Temporal As-Of:* Dữ liệu train PhreshPhish kết thúc ngày 08/09/2025 (Q3/2025) $\to$ cấm dùng báo cáo Q4/2025 (công bố 15/01/2026) cho các mốc cắt thời gian as-of trước ngày 15/01/2026.
*Kết luận:* **ĐẠT**.

---

## 5. BẰNG CHỨNG THỰC NGHIỆM ĐÃ CHẠY

* **Môi trường thử nghiệm:** Windows 11, CPython 3.14.2, pytest 9.1.1.
* **Kết quả Test Suite:**
  Lệnh chạy: `python -m pytest`
  Kết quả: **98/98 test cases PASSED (100%)**, 0 lỗi, 32 subtests passed in 4.71s.
  - `tests/test_blind_view.py`: 39 passed (gồm các bài test mới: chặn đổi nội dung cùng ID, chặn lệch codebook hash, kiểm soát provenance đa tầng)
  - `tests/test_label_fixes.py`: 8 passed (chứng minh sửa dứt điểm L-B01–L-B06)
  - `tests/test_date_parser.py`: 9 passed
  - `tests/test_dictionary_and_annotation.py`: 18 passed
  - `tests/test_domain_rules.py`: 6 passed
  - `tests/test_exclusion_registry.py`: 11 passed
  - `tests/test_preprocessing.py`: 7 passed (32 subtests passed)
* **Kết luận:** Hệ thống kiểm thử hoàn toàn tự động, sạch sẽ và tái lập 100%.

---

## 6. QUY TRÌNH TIẾP THEO & ĐIỀU KIỆN MỞ PILOT THẬT

1. **Thành viên B:**
   - Ký xác nhận hoàn tất nghiệm thu kỹ thuật độc lập đối với toàn bộ mã nguồn của C tại commit `6c0492d`.
   - Cam kết: Chưa thực hiện gán nhãn pilot thật, giữ nguyên tắc nhãn mù độc lập, sẵn sàng nhận gói thật khi có lệnh.
2. **Quyền hạn và Trách nhiệm của Lead D:**
   - Lead D rà soát biên bản này của B và kiểm tra mã băm của tệp view mù `blind_view_pilot_real.json` do C bàn giao riêng.
   - Lead D thực hiện đóng khóa chính thức `docs/CODEBOOK_V1.md` và `configs/dictionary_v1.json` (chuyển trạng thái từ `pending_review` sang `locked`/`approved`).
   - Lead D cập nhật các mã hash phụ thuộc trong `configs/pilot_manifest.json` và phê duyệt `"acceptance": {"B": "approved", "D": "approved"}`.
   - Lead D chính thức phát lệnh mở đợt gán nhãn pilot thật và chỉ đạo C kích hoạt `ready_for_annotation: true`.
3. **Chốt chặn huấn luyện chính (Reiterated):**
   - Mở đợt pilot thật 32 mẫu **không đồng nghĩa với dỡ bỏ chốt chặn huấn luyện mô hình chính**. Trạng thái 20 mẫu kỹ thuật cũ vẫn là `unresolved_source_mapping`, cờ `training_blocked: true` tiếp tục có hiệu lực cho đến khi có xác minh toàn diện.
