# GÓI THÔNG SỐ KỸ THUẬT VÀ KIỂM ĐỊNH CỔNG CHỌN MẪU MAIN ĐỢT 1 (BÀN GIAO QA LEAD B)

**Kính gửi:** QA Lead B (Minh)  
**Người lập:** Thành viên C (Data Pipeline & Thư ký Kiểm toán)  
**Mục đích:** Bàn giao thông số kỹ thuật, mã băm niêm phong, và bằng chứng kiểm thử tự động của Cổng chọn mẫu Main Đợt 1 phục vụ thẩm định QA độc lập.  
**Ranh giới bảo mật:** Tuân thủ ARS Anti-Leakage Protocol — Không tiết lộ danh sách ứng viên, locator shard/offset, nhãn nguồn, cơ cấu tỷ lệ nhãn, hoặc giá trị seed phân tầng.

---

## 1. Thông số Kỹ thuật Cổng Chọn Mẫu (Selection Gate Specifications)

Quy trình chọn mẫu Main Đợt 1 được chuẩn hóa thành 5 cổng logic liên hoàn tại `src/phishing/data/selection_gate.py`:

* **Cổng 0 (Gate 0 - Shard & Source Integrity):**
  * Nguồn được phép: `phreshphish` (revision đã khóa `eabec4b7a66324b79cc8a0ad856d1731dc26fe1a`).
  * Shard cách ly (Strict Quarantine): `train-000.parquet`, `train-055.parquet`.
  * Nguồn bị chặn (Blocked Source): `PhishVN` (trạng thái: chờ quy trình thẩm định nguồn riêng).
  * Kiểm toán toàn vẹn: Đối chiếu mã băm Git-LFS SHA-256 từ `configs/source_manifest.json`.

* **Cổng 1 (Gate 1 - Field Validity & Operational Windows):**
  * URL: Chuẩn hóa theo RFC/WHATWG, bắt buộc giao thức HTTP hoặc HTTPS tuyệt đối.
  * HTML: Bắt buộc không rỗng, giới hạn ký tự từ `1` đến `2,000,000` ký tự (chặn cắt cụt chuỗi).
  * Cửa sổ thời gian: Hỗ trợ cấu hình `min_date` và `max_date` theo temporal contract.

* **Cổng 2 (Gate 2 - Cryptographic Anti-Leakage Filter):**
  * Cơ chế: Fail-closed (dừng khẩn cấp bằng `RuntimeError` nếu thiếu hồ sơ hoặc sai mã băm).
  * Phạm vi chặn: Toàn bộ mã băm `url_sha256`, `normalized_url_sha256`, `html_sha256`, `cleaned_html_sha256`, và `group_sha256` (eTLD+1) đã niêm phong trong `data/exclusion_registry.json` và hồ sơ hạn chế.

* **Cổng 3 (Gate 3 - Candidate Deduplication):**
  * Khử trùng lặp nội bộ đợt: Chặn URL trùng lặp, HTML trùng lặp.
  * Giới hạn mật độ miền (Domain Diversity): Giới hạn tối đa 1 mẫu cho mỗi nhóm miền (`group_id` eTLD+1) trong cùng đợt rút mẫu.

* **Cổng 4 (Gate 4 - Sealed Seed Stratified Sampling):**
  * Chọn mẫu ngẫu nhiên xác định với Seed được niêm phong độc lập.

---

## 2. Bảng Mã băm Kiểm toán và Niêm phong Tài liệu (Cryptographic Integrity Hashes)

| Tệp thành phần | Đường dẫn | SHA-256 Checksum | Tình trạng |
| :--- | :--- | :--- | :--- |
| **Mã nguồn Selection Gate** | `src/phishing/data/selection_gate.py` | `895ef506fa5eb94e5afbc77d653745e715b4f0f93021d40686b5dba41cc25bab` | Sẵn sàng thẩm định |
| **Bộ kiểm thử tự động** | `tests/test_pilot_batch1_exclusion.py` | `ac58e0de837013a2165890a2f41ff3e2b5ea32a968277620c684b7ff00a89097` | Sẵn sàng thẩm định |
| **Source Manifest đã khóa** | `configs/source_manifest.json` | `50fa39d58325e4645b76886e519dd5fbaca31db234d8c70eb95a4eeb608e8eb0` | Đã khóa revision |
| **Exclusion Registry** | `data/exclusion_registry.json` | `89e7c0240828f9257e654963b3276935e707a47d32133bae39bcb99284ca6a88` | Đã khóa v1.1.0 |
| **Hồ sơ hạn chế Pilot 20 ngoài Git** | `data/restricted/pilot_batch1_recovery_dossier_restricted.json` | `7ab0d5cb637eb351eb4de39f5f9635c0f22cfb9c3a477fa197df59da28ad4d27` | Niêm phong (D kiểm soát) |

---

## 3. Báo cáo Kết quả Kiểm thử Tự động (Automated Verification Log)

* **Lệnh thực thi:** `python -m pytest tests/test_pilot_batch1_exclusion.py -v`
* **Môi trường:** Python 3.13.14, pytest-7.4.0, Windows 10
* **Kết quả:** **16 passed, 0 failed, 0 skipped** (thời gian: 0.49s)
  * Kiểm thử cách ly shard `train-000` và `train-055`: ĐẠT (SelectionGateError khi nạp).
  * Kiểm thử chặn nguồn `PhishVN`: ĐẠT (SelectionGateError khi nạp).
  * Kiểm thử tính hợp lệ trường & giới hạn HTML: ĐẠT.
  * Kiểm thử cố ý tiêm mẫu Pilot vào đường chọn mẫu: ĐẠT (bị chặn 100% tại Cổng 2).
  * Kiểm thử cố ý tiêm mẫu trùng domain với Pilot: ĐẠT (bị chặn 100% tại Cổng 2).
  * Kiểm thử Fail-closed khi thiếu hồ sơ hạn chế: ĐẠT (dừng ném `RuntimeError`).
  * Kiểm thử Fail-closed khi sai mã băm cam kết: ĐẠT (dừng ném `RuntimeError`).
  * Kiểm thử khử trùng lặp và tính tái lập của phân tầng: ĐẠT.

---

## 4. Trạng thái Quản trị Hiện tại

* `main_annotation_status`: **LOCKED** (Chưa trích xuất 100 mẫu thật, chưa tạo Blind View, chưa mở Pass 1).
* `training_blocked`: **TRUE** (Toàn bộ tiến trình huấn luyện M0–M3 tiếp tục khóa).
* `official_test_used`: **FALSE** (Tập Official Test được bảo vệ cô lập 100%).
* **Khuyến nghị từ C:** B thực hiện kiểm toán độc lập trên mã nguồn, mã băm và các ca kiểm thử trên đúng phiên bản bàn giao này. C không tự ghi `QA APPROVED` hoặc `D APPROVED`.
