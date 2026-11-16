# GÓI THÔNG SỐ KỸ THUẬT VÀ KIỂM ĐỊNH CỔNG CHỌN MẪU MAIN ĐỢT 1 (BÀN GIAO QA LEAD B - BẢN V4.1)

**Kính gửi:** QA Lead B (Minh)  
**Người lập:** Thành viên C (Data Pipeline & Thư ký Kiểm toán)  
**Ngày cập nhật:** 16/11/2026 (Bản sửa đổi V4.1 sau khi tiếp thu chỉ đạo của Lead D Vòng 16)  
**Mục đích:** Bàn giao thông số kỹ thuật, mã băm niêm phong, và bằng chứng kiểm thử tự động của Cổng chọn mẫu Main Đợt 1 phục vụ tái thẩm định QA độc lập trên Clean Checkout.  
**Ranh giới bảo mật mù (ARS Double-Blind Protocol):** Tuyệt đối không tiết lộ danh sách ứng viên, locator shard/offset, URL/HTML, nhãn nguồn, cơ cấu nhãn, hoặc giá trị seed ngẫu nhiên. Chữ ký QA của B cho V3 không tự động áp dụng cho V4/V4.1; B cần thực hiện kiểm định độc lập trên commit mới.

---

## 1. Thông số Kỹ thuật 5 Cổng Kiểm Soát (Selection Gate V4.1 Specifications)

Quy trình chọn mẫu Main Đợt 1 được tích hợp tại [`src/phishing/data/selection_gate.py`](file:///d:/nguyen%20thang/NCKH/NCKH_2/src/phishing/data/selection_gate.py) và runner CLI tại [`scripts/data/run_main_selection.py`](file:///d:/nguyen%20thang/NCKH/NCKH_2/scripts/data/run_main_selection.py):

* **Cổng 0 (Gate 0 - Shard & Source Integrity):**
  * Nguồn được phép: `phreshphish` (bắt buộc Git revision đã khóa `eabec4b7a66324b79cc8a0ad856d1731dc26fe1a`).
  * Shard cách ly (Strict Quarantine): `train-000.parquet`, `train-055.parquet` (chặn cả tên định danh lẫn đường dẫn tệp).
  * Nguồn bị chặn (Blocked Source): `PhishVN` (chờ quy trình phê duyệt nguồn độc lập).
  * **Tự đối chiếu mã băm thực tế:** Đọc trực tiếp luồng byte thực tế của tệp shard trên đĩa theo chunk 64KB để tính SHA-256 và đối chiếu với `configs/source_manifest.json` (mục `files`).

* **Cổng 1 (Gate 1 - Field Validity & Operational Window V3.5):**
  * URL: Bắt buộc giao thức HTTP hoặc HTTPS hợp lệ (kiểm tra qua `normalize_url`).
  * HTML: Bắt buộc không rỗng, độ dài từ `1` đến `2,000,000` ký tự.
  * **Ngày kiểm định nghiêm ngặt theo Kế hoạch V3.5:** Bắt buộc định dạng regex `^\d{4}-\d{2}-\d{2}$` (bỏ hoàn toàn việc cắt chuỗi `[:10]`), từ chối mọi chuỗi có hậu tố rác. Cửa sổ thời gian đã khóa: `2024-10-01 <= date <= 2025-09-08`.

* **Cổng 2 (Gate 2 - Cryptographic Anti-Leakage Gate 6 Lớp & Fail-Closed Remediation):**
  * Đã sửa module import: dùng đúng `from phishing.preprocessing.urls import normalize_url` và `from phishing.preprocessing.html import clean_html`.
  * Đã chuẩn hóa chữ ký gọi `clean_html(html, page_url=...)` với `page_url` bắt buộc, loại bỏ hoàn toàn `TypeError: missing required argument`.
  * **Loại bỏ hoàn toàn `except Exception: pass`**:
    1. Lỗi dữ liệu định dạng (`ValueError`, `TypeError` khi URL/HTML không hợp lệ): Gate 2 từ chối mẫu với lý do `reject_gate2_preprocessing_error`, `is_excluded()` loại trừ fail-closed. Tuyệt đối không biến lỗi xử lý thành `passed`!
    2. Ngoại lệ hệ thống nghiêm trọng (`RuntimeError`, bugs): Không bị nuốt, propagate trực tiếp làm dừng pipeline.
  * Đã liên kết `EXCL-PILOT-01` trong `data/exclusion_registry.json` với hồ sơ hạn chế V2 ngoài Git (`data/restricted/pilot_batch1_recovery_dossier_restricted_v2.json`) với mã băm cam kết vật lý chính xác:
    `adc0b90dddc0aea4c3347cc709fabe6dbc3ea391335965c0ba949503bfcdf1fa`.

* **Cổng 3 (Gate 3 - Deduplication, Row-Order Bias Elimination & Template Clones V3.5):**
  * **Triệt tiêu thiên lệch thứ tự hàng:** Sắp xếp ứng viên theo khóa chính tắc (URL chuẩn hóa + HTML hash), sau đó xáo trộn bằng seed niêm phong trước khi chọn đại diện cho mỗi miền/template. Kết quả chọn mẫu bất biến với bất kỳ thứ tự đầu vào nào của shard.
  * Giới hạn tối đa 1 mẫu trên mỗi tên miền (`eTLD+1`).
  * **Động cơ Template Similarity Engine (V3.5):** Áp dụng thuật toán SimHash 64-bit (`hamming_distance <= 10`) và DOM Tag Jaccard (`similarity >= 0.85`), tuần tự kiểm tra và đăng ký ứng viên đã nhận để loại trừ các trang clone sinh từ cùng phishing kit.

* **Cổng 4 (Gate 4 - Seeded Random Sampling & Quota Fail-Closed):**
  * Phân tầng mẫu / chọn mẫu ngẫu nhiên xác định theo seed niêm phong.
  * **Quota Fail-Closed:** Bắt buộc đủ quota mẫu (ví dụ 100 mẫu). Nếu số lượng ứng viên sạch sau Cổng 3 nhỏ hơn quota yêu cầu, pipeline ném lỗi `SelectionGateError` dừng toàn bộ quy trình, không xuất dữ liệu thiếu.

---

## 2. Kết quả Kiểm thử Tự động & Phân định Minh bạch

Bộ kiểm thử [`tests/test_pilot_batch1_exclusion.py`](file:///d:/nguyen%20thang/NCKH/NCKH_2/tests/test_pilot_batch1_exclusion.py) gồm 40 ca kiểm thử tự chứa (bao gồm 5 ca kiểm thử hồi quy mới):

1. **Phép tự kiểm thử mô phỏng Clean Checkout do C thực hiện (Self-test Simulation by C):**
   * Kết quả tự kiểm: **38 passed, 0 failed, 2 skipped** (trong 1.93s).
   * **Chi tiết 2 ca kiểm thử tự động skip có lý do kiểm toán minh bạch (không gộp vào passed thực tế):**
     1. `test_gate0_rejects_quarantined_real_shard_path`: Skipped vì không có shard thực tế `data/raw/phreshphish/data/train-000.parquet` trên clean checkout (lý do: *"Chưa có shard train-000 trên clean checkout"*).
     2. `test_gate2_integration_with_real_restricted_dossier_v2`: Skipped vì không có tệp `data/restricted/pilot_batch1_recovery_dossier_restricted_v2.json` trên clean checkout (lý do: *"Chưa có hồ sơ restricted V2 cục bộ trên clean checkout"*).
   * **Lưu ý kiểm toán:** B chưa phát hành báo cáo QA cho commit V4/V4.1; QA Lead B sẽ tự chạy kiểm định độc lập trên máy của B và phát hành báo cáo riêng.
2. **Kết quả chạy trên Môi trường Đầy đủ Dữ liệu Hạn chế (Môi trường của C):**
   * **Kết quả:** **40 passed, 0 failed, 0 skipped** (trong 2.44s).
3. **Kiểm thử 7 bộ test liên quan đến tuyến dữ liệu, phân tách và chống rò rỉ:**
   * **Kết quả:** **147 passed, 0 failed** (trong 8.62s).

---

## 3. Bảng Mã Băm Niêm Phong Phục vụ Thẩm định QA Độc lập (Bản V4.1)

| Tệp tin / Cấu phần | Kích thước (bytes) | Mã băm SHA-256 |
| :--- | :---: | :--- |
| `src/phishing/data/selection_gate.py` | 20,308 | `eb3f36a9db9a5dbba62bd1643b68cf4c678d99e9a553132354e792de8753a6a1` |
| `src/phishing/data/exclusion.py` | 19,448 | `5cc8a445b20bb251df523e258f957215134cb804859de3855dff49db856aa041` |
| `scripts/data/run_main_selection.py` | 4,381 | `cc1d45d0801d846454347b877ba95907a1bb1537ba33954876b53ddd87c44fb2` |
| `data/exclusion_registry.json` | 107,424 | `f00df7a63fb6659d78fe065ca4c87445ebe071fb448e1d1f337d740317dd57ea` |
| `tests/test_pilot_batch1_exclusion.py` | 43,114 | `a0dab832654bf6ab76614f0098b3b0e7affc710d8e69695d167dfffcff9e75f5` |
| `docs/INCIDENT_REPORT_GIT_EXPOSURE_AD445A7.md` | 6,204 | `79505d4a503c87a762d0476d71e0360c940af86c654b37e41558991756d18f51` |

---

## 4. Hướng dẫn Tái thẩm định QA cho B (Verification Steps)

1. `git pull origin feat/c-calibration-v1-1-4-adjudication`
2. Đối soát mã commit mới nhất của C và kiểm tra mã băm các tệp trong bảng Mục 3.
3. Chạy kiểm thử tự động trên clean checkout:
   ```bash
   python -m pytest tests/test_pilot_batch1_exclusion.py -v
   ```
   *Kỳ vọng:* **38 passed, 2 skipped, 0 failed**.
4. Chạy kiểm thử 7 bộ test liên quan đến dữ liệu:
   ```bash
   python -m pytest tests/test_clean_calibration_selection.py tests/test_clean_calibration_blind_view.py tests/test_calibration_release_guards.py tests/test_prepare_calibration_selection.py tests/test_clean_calibration_zero_git_leak_regression.py tests/test_exclusion_registry.py tests/test_pilot_batch1_exclusion.py -v
   ```
   *Kỳ vọng:* **147 passed, 0 failed**.
5. B phát hành báo cáo thẩm định độc lập theo ranh giới mù.
