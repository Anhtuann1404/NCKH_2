# GÓI THÔNG SỐ KỸ THUẬT VÀ KIỂM ĐỊNH CỔNG CHỌN MẪU MAIN ĐỢT 1 (BÀN GIAO QA LEAD B - V2)

**Kính gửi:** QA Lead B (Minh)  
**Người lập:** Thành viên C (Data Pipeline & Thư ký Kiểm toán)  
**Mục đích:** Bàn giao thông số kỹ thuật, mã băm niêm phong, và bằng chứng kiểm thử tự động của Cổng chọn mẫu Main Đợt 1 phục vụ thẩm định QA độc lập.  
**Ranh giới bảo mật (ARS Protocol):** Tuyệt đối không tiết lộ danh sách ứng viên, locator shard/offset, nhãn nguồn, cơ cấu nhãn, hoặc giá trị seed phân tầng.

---

## 1. Thông số Kỹ thuật Cổng Chọn Mẫu (Selection Gate Specifications)

Quy trình chọn mẫu Main Đợt 1 được chuẩn hóa thành 5 cổng logic liên hoàn tại `src/phishing/data/selection_gate.py` và runner thực thi tại `scripts/data/run_main_selection.py`:

* **Cổng 0 (Gate 0 - Shard & Source Integrity):**
  * Nguồn được phép: `phreshphish` (bắt buộc revision đã khóa `eabec4b7a66324b79cc8a0ad856d1731dc26fe1a`).
  * Shard cách ly (Strict Quarantine): `train-000.parquet`, `train-055.parquet`.
  * Nguồn bị chặn (Blocked Source): `PhishVN` (trạng thái: chờ quy trình thẩm định nguồn riêng).
  * **Tự đối chiếu mã băm thực tế:** Đọc luồng byte thực tế của tệp shard trên đĩa để tính SHA-256 và đối chiếu trực tiếp với `source_manifest.json`.

* **Cổng 1 (Gate 1 - Field Validity & Operational Windows):**
  * URL: Chuẩn hóa theo RFC/WHATWG, bắt buộc giao thức HTTP hoặc HTTPS tuyệt đối.
  * HTML: Bắt buộc không rỗng, giới hạn ký tự từ `1` đến `2,000,000` ký tự (chặn cắt cụt chuỗi).
  * **Ngày bắt buộc (Mandatory Date):** Trường ngày bắt buộc có mặt, đúng định dạng `YYYY-MM-DD` và nằm trong cửa sổ thời gian đã duyệt `[2024-07-04, 2025-09-08]`.

* **Cổng 2 (Gate 2 - Cryptographic Anti-Leakage Filter):**
  * Cơ chế: Fail-closed (dừng khẩn cấp bằng `RuntimeError` nếu thiếu hồ sơ hoặc sai mã băm).
  * Phạm vi chặn: Toàn bộ mã băm `url_sha256`, `normalized_url_sha256`, `html_sha256`, `cleaned_html_sha256`, nhóm miền bare domain và prefixed domain group hash (eTLD+1) đã niêm phong trong `data/exclusion_registry.json` và hồ sơ hạn chế.

* **Cổng 3 (Gate 3 - Candidate Deduplication & Sequential Template Clustering):**
  * Khử trùng lặp URL và HTML.
  * Giới hạn mật độ miền (Domain Diversity): Giới hạn tối đa 1 mẫu cho mỗi nhóm miền (`group_id` eTLD+1).
  * **Kiểm tra template tuần tự:** Trích xuất khung sườn cấu trúc thẻ HTML (tag skeleton hash) để phát hiện và chặn các mẫu clone sinh từ cùng phishing kit.

* **Cổng 4 (Gate 4 - Sealed Seed Stratified Sampling & Quota Enforcement):**
  * Chọn mẫu ngẫu nhiên xác định với Seed được niêm phong độc lập.
  * **Thực thi Quota nghiêm ngặt:** Dừng fail-closed ném `SelectionGateError` nếu số lượng ứng viên sạch không đạt chỉ tiêu quota yêu cầu.

---

## 2. Bảng Mã băm Kiểm toán và Niêm phong Tài liệu (Cryptographic Integrity Hashes)

| Tệp thành phần | Đường dẫn | SHA-256 Checksum | Tình trạng |
| :--- | :--- | :--- | :--- |
| **Mã nguồn Selection Gate** | `src/phishing/data/selection_gate.py` | `ec258d1275d0756f6622862c3f0235803df0beeb55b027f6350599ec9b9a6902` | Sẵn sàng thẩm định |
| **Runner Main Selection** | `scripts/data/run_main_selection.py` | `4b549fe9a227e62cf2f3c5e6cb80ae16468db754cdee4e43b4e345dd2bba8c45` | Sẵn sàng thẩm định |
| **Bộ kiểm thử tự động (32 tests)** | `tests/test_pilot_batch1_exclusion.py` | `75d6fa5eac8e10dc1270918bbfdb76fff1a7f6ba780844c7678a23703449013f` | Sẵn sàng thẩm định |
| **Source Manifest đã khóa** | `configs/source_manifest.json` | `50fa39d58325e4645b76886e519dd5fbaca31db234d8c70eb95a4eeb608e8eb0` | Đã khóa revision |
| **Exclusion Registry** | `data/exclusion_registry.json` | `89e7c0240828f9257e654963b3276935e707a47d32133bae39bcb99284ca6a88` | Đã khóa v1.1.0 |
| **Hồ sơ cam kết hạn chế ngoài Git** | `data/restricted/pilot_batch1_recovery_dossier_restricted.json` | `7ab0d5cb637eb351eb4de39f5f9635c0f22cfb9c3a477fa197df59da28ad4d27` | Niêm phong (D kiểm soát) |
| **Bảng kê cấp mẫu hạn chế ngoài Git** | `data/restricted/pilot_batch1_sample_level_audit_table.json` | `29d107535d185c3369e615f99a63d9190a485b47f01a3bc7743cf46c802701bc` | Niêm phong (D kiểm soát) |

---

## 3. Báo cáo Kết quả Kiểm thử Tự động (Automated Verification Log)

* **Lệnh thực thi:** `python -m pytest tests/test_pilot_batch1_exclusion.py -v`
* **Môi trường:** Python 3.13.14, pytest-7.4.0, Windows 10
* **Kết quả:** **32 passed, 0 failed, 0 skipped** (thời gian: 5.20s):
  * Gate 0: 9 passed (chặn shard cách ly trên đường dẫn thật và tên chuỗi; chặn PhishVN; chặn sai revision/source; chặn file không tồn tại; chặn sai mã băm byte thực tế; chấp nhận file khớp byte).
  * Gate 1: 9 passed (chặn URL rỗng/sai format; chặn HTML rỗng/quá 2MB; chặn thiếu ngày, sai định dạng ngày, ngày trước min, ngày sau max; chấp nhận mẫu hợp lệ).
  * Gate 2: 5 passed (chặn URL thô từ shard thật; chặn HTML thô từ shard thật; chặn mẫu cùng tên miền; fail-closed khi thiếu hồ sơ hạn chế; fail-closed khi sai SHA-256 cam kết).
  * Gate 3: 3 passed (khử trùng URL/HTML; giới hạn 1 mẫu/domain; chặn template clone kit tuần tự).
  * Gate 4: 2 passed (thiếu quota ném `SelectionGateError` dừng an toàn; tính tái lập của PRNG seed).
  * End-to-End & Runner: 4 passed (chặn đứng `train-000` thật; chặn đứng `train-055` thật; chạy toàn bộ pipeline với mẫu pilot thật lẫn vào; runner CLI thực tế trả về exit code 1 và dừng fail-closed khi nạp shard cách ly).

---

## 4. Trạng thái Quản trị Hiện tại

* `main_annotation_status`: **LOCKED** (Chưa rút 100 mẫu thật, chưa tạo Blind View, chưa mở Pass 1).
* `training_blocked`: **TRUE** (Toàn bộ tiến trình huấn luyện M0–M3 tiếp tục khóa).
* `official_test_used`: **FALSE** (Tập Official Test được bảo vệ cô lập 100%).
* **Khuyến nghị từ C:** B thực hiện kiểm toán độc lập trên mã nguồn, mã băm và các ca kiểm thử trên đúng phiên bản bàn giao này. C không tự ghi `QA APPROVED` hoặc `D APPROVED`.
