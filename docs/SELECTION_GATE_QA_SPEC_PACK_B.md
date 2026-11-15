# GÓI THÔNG SỐ KỸ THUẬT VÀ KIỂM ĐỊNH CỔNG CHỌN MẪU MAIN ĐỢT 1 (BÀN GIAO QA LEAD B - BẢN V3)

**Kính gửi:** QA Lead B (Minh)  
**Người lập:** Thành viên C (Data Pipeline & Thư ký Kiểm toán)  
**Ngày cập nhật:** 15/11/2026 (Bản sửa đổi V3 sau khi tiếp thu Báo cáo Errata v1.1 của B và chỉ đạo Lead D)  
**Mục đích:** Bàn giao thông số kỹ thuật, mã băm niêm phong, và bằng chứng kiểm thử tự động của Cổng chọn mẫu Main Đợt 1 phục vụ tái thẩm định QA độc lập.  
**Ranh giới bảo mật mù (ARS Double-Blind Protocol):** Tuyệt đối không tiết lộ danh sách ứng viên, locator shard/offset, URL/HTML, nhãn nguồn, cơ cấu nhãn, hoặc giá trị seed ngẫu nhiên.

---

## 1. Thông số Kỹ thuật 5 Cổng Kiểm Soát (Selection Gate V3 Specifications)

Quy trình chọn mẫu Main Đợt 1 được tích hợp tại [`src/phishing/data/selection_gate.py`](file:///d:/nguyen%20thang/NCKH/NCKH_2/src/phishing/data/selection_gate.py) và runner CLI tại [`scripts/data/run_main_selection.py`](file:///d:/nguyen%20thang/NCKH/NCKH_2/scripts/data/run_main_selection.py):

* **Cổng 0 (Gate 0 - Shard & Source Integrity):**
  * Nguồn được phép: `phreshphish` (bắt buộc Git revision đã khóa `eabec4b7a66324b79cc8a0ad856d1731dc26fe1a`).
  * Shard cách ly (Strict Quarantine): `train-000.parquet`, `train-055.parquet` (chặn cả tên định danh lẫn đường dẫn tệp).
  * Nguồn bị chặn (Blocked Source): `PhishVN` (chờ quy trình phê duyệt nguồn độc lập).
  * **Tự đối chiếu mã băm thực tế:** Đọc trực tiếp luồng byte thực tế của tệp shard trên đĩa theo chunk 64KB để tính SHA-256 và đối chiếu với `configs/source_manifest.json` (mục `files`).

* **Cổng 1 (Gate 1 - Field Validity & Operational Window V3.5):**
  * URL: Bắt buộc giao thức HTTP hoặc HTTPS hợp lệ.
  * HTML: Bắt buộc không rỗng, độ dài từ `1` đến `2,000,000` ký tự.
  * **Ngày kiểm định nghiêm ngặt theo Kế hoạch V3.5:** Bắt buộc định dạng regex `^\d{4}-\d{2}-\d{2}$` (bỏ hoàn toàn việc cắt chuỗi `[:10]`), từ chối mọi chuỗi có hậu tố rác. Cửa sổ thời gian đã khóa: `2024-10-01 <= date <= 2025-09-08`.

* **Cổng 2 (Gate 2 - Cryptographic Anti-Leakage Gate 6 Lớp):**
  * Đã sửa lỗi bộ nạp `ExclusionRegistry._load_registry()` để nạp đầy đủ cả 6 lớp mã băm đối soát vào bộ nhớ:
    1. `url_sha256` (URL thô)
    2. `normalized_url_sha256` (URL chuẩn hóa)
    3. `html_sha256` (HTML thô)
    4. `cleaned_html_sha256` (HTML làm sạch)
    5. `bare domain group hash` (nhóm miền không tiền tố)
    6. `prefixed domain group hash` (nhóm miền có tiền tố `domain:`)
  * Đã liên kết `EXCL-PILOT-01` trong `data/exclusion_registry.json` với hồ sơ hạn chế V2 ngoài Git (`data/restricted/pilot_batch1_recovery_dossier_restricted_v2.json`) với mã băm cam kết vật lý chính xác:
    `adc0b90dddc0aea4c3347cc709fabe6dbc3ea391335965c0ba949503bfcdf1fa`.

* **Cổng 3 (Gate 3 - Deduplication, Row-Order Bias Elimination & Template Clones V3.5):**
  * **Triệt tiêu thiên lệch thứ tự hàng:** Sắp xếp ứng viên theo khóa chính tắc (URL chuẩn hóa + HTML hash), sau đó xáo trộn bằng seed niêm phong trước khi chọn đại diện cho mỗi miền/template. Kết quả chọn mẫu bất biến với bất kỳ thứ tự đầu vào nào của shard.
  * Giới hạn tối đa 1 mẫu trên mỗi tên miền (`eTLD+1`).
  * **Động cơ Template Similarity Engine (V3.5):** Áp dụng thuật toán SimHash 64-bit (`hamming_distance <= 10`) và DOM Tag Jaccard (`similarity >= 0.85`), tuần tự kiểm tra và đăng ký ứng viên đã nhận để loại trừ các trang clone/near-duplicate sinh từ cùng phishing kit.

* **Cổng 4 (Gate 4 - Seeded Random Sampling & Quota Fail-Closed):**
  * Phân tầng mẫu / chọn mẫu ngẫu nhiên xác định theo seed niêm phong.
  * **Quota Fail-Closed:** Bắt buộc đủ quota mẫu (ví dụ 100 mẫu). Nếu số lượng ứng viên sạch sau Cổng 3 nhỏ hơn quota yêu cầu, pipeline ném lỗi `SelectionGateError` dừng toàn bộ quy trình, không xuất dữ liệu thiếu.

---

## 2. Kết quả Kiểm thử Tự động (Môi trường Clean Checkout & Cục bộ)

Bộ kiểm thử [`tests/test_pilot_batch1_exclusion.py`](file:///d:/nguyen%20thang/NCKH/NCKH_2/tests/test_pilot_batch1_exclusion.py) đã được tái cấu trúc thành 35 ca kiểm thử tự chứa:

1. **Kết quả chạy trên Clean Git Checkout (Môi trường của QA Lead B - Không có tệp restricted):**
   * Lệnh chạy: `python -m pytest tests/test_pilot_batch1_exclusion.py -v`
   * **Kết quả:** **34 passed, 0 failed, 1 skipped** (100% pass, không còn 6 tests fail).
   * Ghi chú: 01 ca test duy nhất bị `skipped` là `test_gate2_integration_with_real_restricted_dossier_v2` do kiểm tra sự hiện diện của tệp restricted ngoài Git (đáp ứng đúng chuẩn mực tính mù của B).
2. **Kết quả chạy trên Môi trường Đầy đủ Dữ liệu Hạn chế (Môi trường của C):**
   * **Kết quả:** **35 passed, 0 failed, 0 skipped** (100% passed).
3. **Kiểm thử hồi quy 5 test suites toàn repo:**
   * **Kết quả:** **118 passed, 0 failed** (100% passed).

---

## 3. Bảng Mã Băm Niêm Phong Phục vụ Thẩm định QA Độc lập

| Tệp tin / Cấu phần | Kích thước (bytes) | Mã băm SHA-256 |
| :--- | :--- | :--- |
| `src/phishing/data/selection_gate.py` | 19,768 | `73e8b3fe149279dd235f032f5681ae90ad1cbef4a7b30af93e8f5355b7918475` |
| `src/phishing/data/exclusion.py` | 18,886 | `23d21f687aaae3cf4adf25d926f98e1a7c6426c8130ea6ffe8cb81389ddbc8a5` |
| `scripts/data/run_main_selection.py` | 4,381 | `cc1d45d0801d846454347b877ba95907a1bb1537ba33954876b53ddd87c44fb2` |
| `data/exclusion_registry.json` | 107,424 | `f00df7a63fb6659d78fe065ca4c87445ebe071fb448e1d1f337d740317dd57ea` |
| `tests/test_pilot_batch1_exclusion.py` | 32,889 | `2f609653fde8e07ce8de33256fb613a283b27b7afa6dfd2d130c18b5095a2978` |
| Cam kết hồ sơ Lô 1 V2 (`commitment_sha256`) | — | `adc0b90dddc0aea4c3347cc709fabe6dbc3ea391335965c0ba949503bfcdf1fa` |

---

## 4. Trạng thái Quản trị Tiếp tục Duy trì
* `main_annotation_status = "LOCKED"`
* `training_blocked = true`
* `official_test_used = false`
* C cam kết **chưa rút 100 mẫu Main và chưa phát Blind View** cho đến khi Lead D ban hành quyết định nghiệm thu chính thức.
