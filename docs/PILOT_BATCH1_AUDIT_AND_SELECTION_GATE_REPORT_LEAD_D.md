# BÁO CÁO KIỂM TOÁN TỔNG HỢP 20 MẪU PILOT (EXCL-PILOT-01), CỔNG CHỌN MẪU MAIN ĐỢT 1 & ĐỀ XUẤT SHARD PHÊ DUYỆT (BẢN V4)

**Kính gửi:** Lead D (Anh Tuấn)  
**Người thực hiện:** Thành viên C (Data Pipeline & Thư ký Kiểm toán)  
**Ngày cập nhật:** 16/11/2026 (Bản sửa đổi V4 sau đợt phản biện của Lead D Round 15 và báo cáo tái thẩm định QA của B)  
**Chế độ thực thi:** Duo Mode (Antigravity & DeepSeek Reason / Code Architecture Review)  
**Trạng thái Quản trị:** `main_annotation_status="LOCKED"`, `training_blocked=true`, `official_test_used=false`

---

## 1. Báo cáo Quản trị Sự cố Tiếp xúc Dữ liệu Cấp Mẫu trên Lịch sử Git (Commit `ad445a7`)

Biên bản sự cố chi tiết đã được lập và ban hành độc lập tại [`docs/INCIDENT_REPORT_GIT_EXPOSURE_AD445A7.md`](file:///d:/nguyen%20thang/NCKH/NCKH_2/docs/INCIDENT_REPORT_GIT_EXPOSURE_AD445A7.md).

* **Tóm tắt sự cố:** Trong commit `ad445a7`, bảng đối soát chi tiết cấp mẫu (Entry ID, locator `train-000:0..19`, nhãn nguồn, ngày và tên miền) đã vô tình xuất hiện trên Git.
* **Phạm vi tiếp xúc:** **Chưa xác minh (Unverified exposure scope)**. Do không có access/traffic logs từ máy chủ GitHub, Thành viên C tuyệt đối không đưa ra tuyên bố "0 lượt tiếp xúc" hay "chưa có người xem". Dữ liệu trong commit `ad445a7` vẫn tồn tại trên lịch sử remote repository. C không tuyên bố đã xóa sạch lịch sử Git.
* **Biện pháp khắc phục đã thực hiện:**
  1. Toàn bộ bảng cấp mẫu 20 dòng đã được niêm phong an toàn tại khu vực hạn chế ngoài Git:  
     `data/restricted/pilot_batch1_sample_level_audit_table.json` (20,574 bytes | SHA-256: `6395781aeada3b73c72ee7215bd29a167ea5ab639ce48fe3507bde515bbf128f`).
  2. Báo cáo Git và gói QA cho B chỉ chứa số liệu tổng hợp; toàn bộ tài liệu công khai không còn bảng cấp mẫu hoặc chi tiết giúp tra ngược mẫu.
  3. C giữ nguyên kỷ luật kỹ thuật: **Không tự ý force-push hoặc viết lại lịch sử Git**, bảo toàn vết kiểm toán để Lead D xem xét.
* **Hai phương án quản trị lịch sử trình Lead D quyết định:**
  * **Phương án A (Forward-Fix & Administrative Retirement - Khuyến nghị):** Giữ nguyên cây commit lịch sử; đánh dấu 20 mẫu này là đã bị phơi nhiễm locator trong lịch sử nội bộ và **loại trừ vĩnh viễn (retired)** khỏi toàn bộ quá trình phát triển, huấn luyện và kiểm thử mô hình (M0–M3). Shard `train-000` được cách ly vĩnh viễn. Phương án này bảo toàn tính minh bạch và audit trail.
  * **Phương án B (Git History Rewrite via git-filter-repo):** Dùng `git-filter-repo` để xóa vĩnh viễn commit `ad445a7` khỏi GitHub và yêu cầu toàn bộ nhóm clone lại repository. Phương án này chỉ thực hiện khi có lệnh điều phối trực tiếp từ Lead D.

---

## 2. Chuỗi Bằng chứng 20 Mẫu Pilot Lô 1 & Định nghĩa Đếm Nhóm Miền

### A. Giữ đúng giới hạn khoa học về chuỗi bằng chứng Pilot gốc:
* C xác nhận trong kho lưu trữ không có tệp raw HTTP response body dump nguyên byte từ các cuộc gọi Rows API trước đây.
* Do đó, C chính thức giữ nguyên kết luận đính chính trong mọi báo cáo: **Chưa chứng minh được "20/20 Pilot lịch sử khớp byte"**.
  * Các mã băm tính từ `train-000.parquet` tại Git revision `eabec4b7a66324b79cc8a0ad856d1731dc26fe1a` là bằng chứng xác thực về các bản ghi thuộc revision đã khóa đó.
  * Các số liệu trong `pilot_summary.json` (5,344 bytes | SHA-256: `3889bf2f...`) chỉ là bằng chứng đối chiếu cấu trúc tóm tắt.
  * Không chuyển trạng thái ánh xạ sang `verified` nếu chưa có chứng cứ mới; bảo lưu trạng thái `unresolved_source_mapping` và `rows_api_revision_pinned=false` trong `data/exclusion_registry.json`.

### B. Bảo lưu Hồ sơ Hạn chế V2 (Lineage & Audit Trail):
* **Tệp V2 hiện hành:** `data/restricted/pilot_batch1_recovery_dossier_restricted_v2.json`
  * *Dung lượng:* `23,169 bytes`
  * *Mã băm SHA-256:* `adc0b90dddc0aea4c3347cc709fabe6dbc3ea391335965c0ba949503bfcdf1fa`
  * *Trạng thái định danh nội dung:* `"content_identity_verified": false`, `"content_identity_status": "reconstructed_at_pinned_revision_unverified_historical_byte"`.
* **Tệp V1 cũ (Bảo lưu làm audit trail):** `data/restricted/pilot_batch1_recovery_dossier_restricted.json` (20,731 bytes | SHA-256: `2e14d95729a06c2315e8f7587d447a3983e497b0adb90eb50c11508c08a16977`).

### C. Mối quan hệ giữa 20 mẫu Pilot Lô 1 với `EXCL-REAL-PILOT-32`:
* **Số mục registry:** 10 lô loại trừ đã đăng ký trong `data/exclusion_registry.json`.
* **Số URL/HTML duy nhất đã xác minh byte:** 214 mẫu công khai từ 9 lô sự cố/lịch sử + 32 mẫu `EXCL-CALIB-01` niêm phong hạn chế (Tổng: 246 mẫu được kiểm toán chặt chẽ ba bên).
* **Quan hệ Pilot lịch sử còn suy luận:** Lô `EXCL-REAL-PILOT-32` (32 mẫu) được chọn dựa trên dấu vân tay cấu trúc từ `train-000` (20 mẫu) và `train-055` (12 mẫu). 20 mẫu của `EXCL-PILOT-01` tương ứng với 20 hàng đầu tiên (`0..19`) của `train-000`. Do thiếu bản lưu byte gốc từ Rows API, mối quan hệ đồng nhất giữa Pilot lịch sử và các bản ghi trong shard hiện tại chỉ dừng ở mức suy luận cấu trúc, **không khẳng định "96 mẫu Pilot lịch sử duy nhất"**.

### D. Giải trình toán học về số đếm Nhóm miền (19 vs 20):
Báo cáo công khai và hồ sơ hạn chế có hai số đếm khác nhau xuất phát từ hai định nghĩa đo lường chuẩn xác:
1. **Phép đếm theo FQDN / Hostname (`group_id = f"domain:{hostname}"`):** Có **20 giá trị `group_id` duy nhất / 20 mẫu**.
2. **Phép đếm theo Tên miền cấp 2 đã đăng ký (`eTLD+1` theo Public Suffix List):** Có **19 tên miền duy nhất**, do có 2 mẫu là hai subdomain khác nhau cùng thuộc 1 shared tenant/object storage (`r2.dev`).
3. Dưới Cổng 3 (giới hạn 1 mẫu/eTLD+1), 2 mẫu này nếu cùng đi vào tuyển chọn thì mẫu thứ hai sẽ bị loại theo cơ chế chống trùng lặp tenant.

---

## 3. Khắc phục Triệt để Lỗi Tuyến Loại trừ & Loại bỏ `except Exception: pass` (Fail-Closed Remediation)

Tiếp thu phản biện kỹ thuật của Lead D tại Vòng 15 và kết quả tham vấn kiến trúc cùng DeepSeek Reason Mode (`scratch/deepseek_r15_recommendations.md`), Thành viên C đã sửa tận gốc các khuyết tật trong module loại trừ:

### A. Sửa Import và Chữ ký Gọi hàm Hợp lệ:
1. **Module Chuẩn hóa URL:** Đổi từ `from phishing.url.canonicalization import normalize_url` (gây lỗi `ModuleNotFoundError`) sang đúng module chuẩn của codebase:  
   `from phishing.preprocessing.urls import normalize_url` (được import tại cấp module của cả `exclusion.py` và `selection_gate.py`).
2. **Module Làm sạch HTML:** Chữ ký hàm bắt buộc có `page_url`: `clean_html(html: str, page_url: str, *, max_characters: int)`.  
   Đã cập nhật lời gọi trong `ExclusionRegistry.is_excluded()` để truyền `page_url`:
   ```python
   norm_url_page = (
       url if (isinstance(url, str) and url.startswith(("http://", "https://")))
       else (f"http://{url}" if (isinstance(url, str) and url.strip()) else "http://placeholder.local")
   )
   cl_h = clean_html(html, page_url=norm_url_page)
   ```

### B. Loại bỏ Hoàn toàn Silent Exception Swallowing (`except Exception: pass`):
Hệ thống phân biệt rạch ròi 2 nhóm ngoại lệ theo nguyên tắc Fail-Closed:
1. **Lỗi dữ liệu định dạng (`ValueError`, `TypeError` từ parser/normalizer):**
   * Xảy ra khi URL có ký tự điều khiển/khoảng trắng bất hợp pháp, HTML vượt quá giới hạn ký tự, hoặc kiểu dữ liệu không đúng.
   * *Hành vi:* Không thể xác minh chắc chắn mẫu có nằm trong registry hay không → **Loại trừ mẫu để bảo vệ an toàn chống rò rỉ**.
     * Trong `is_excluded()`: Trả về `True` (loại trừ fail-closed).
     * Trong `gate_2_anti_leakage()`: Trả về `(False, "reject_gate2_preprocessing_error")`. Tuyệt đối không biến lỗi thành `(True, "passed")`!
2. **Ngoại lệ hệ thống nghiêm trọng (`RuntimeError`, `ImportError`, bugs nội bộ):**
   * *Hành vi:* **Không bắt bằng `except Exception: pass`**, để ngoại lệ propagate tự nhiên làm dừng pipeline ngay lập tức (Fail-Closed System Halt).

### C. Đảm bảo Tính Nhất quán giữa `is_excluded()`, `filter_split()` và `gate_2_anti_leakage()`:
* `gate_2_anti_leakage()` thực thi kiểm tra đa tầng, đồng thời gọi trực tiếp `self.exclusion_registry.is_excluded(sample)`.
* Bất kỳ mẫu nào bị `is_excluded()` loại trừ (do khớp raw hash, normalized hash, clean HTML hash, domain group, summary fingerprint cấu trúc, hoặc do lỗi định dạng tiền xử lý) đều bị `filter_split()` đưa vào tập `excluded` (không lọt vào `kept`) và bị Cổng 2 từ chối.
* Cùng một bản ghi dữ liệu sẽ luôn nhận cùng một quyết định bị loại ở cả ba tuyến kiểm tra.

---

## 4. Bộ Kiểm thử Hồi quy Chuyên biệt Bắt lại Chính Xác Các Lỗi Đã Qua

Trong [`tests/test_pilot_batch1_exclusion.py`](file:///d:/nguyen%20thang/NCKH/NCKH_2/tests/test_pilot_batch1_exclusion.py), Thành viên C đã bổ sung 5 ca kiểm thử hồi quy tự chứa (Self-Contained Regression Tests), sử dụng dữ liệu giả định tổng hợp, không dùng URL/HTML thật:

1. **`test_gate2_regression_raw_url_differs_but_normalized_url_matches`:**
   * Raw URL khác biệt (viết hoa hostname, chỉ định cổng tường minh `:443`, gắn fragment `#fragment`) → Raw URL hash hoàn toàn không có trong registry.
   * URL sau chuẩn hóa khớp chính xác với `normalized_url_sha256` trong registry.
   * *Kết quả:* `is_excluded() == True`, `filter_split()` đưa vào `excluded` (tập `kept` rỗng), Cổng 2 trả về `(False, "reject_exclusion_registry_match")`.
2. **`test_gate2_regression_raw_html_differs_but_cleaned_html_matches`:**
   * Raw HTML khác biệt (chứa mã `<script>alert('exploit');</script>`) → Raw HTML hash không có trong registry.
   * HTML sau khi làm sạch qua `clean_html(page_url=...)` loại bỏ script và khớp chính xác với `cleaned_html_sha256` trong registry.
   * *Kết quả:* `is_excluded() == True`, `filter_split()` đưa vào `excluded`, Cổng 2 từ chối với `reject_exclusion_registry_match`.
3. **`test_gate2_regression_malformed_input_preprocessing_error_fails_closed`:**
   * Mẫu có URL chứa khoảng trắng và ký tự null `\x00` → `normalize_url` ném `ValueError`.
   * *Kết quả:* Cổng 2 từ chối rõ ràng với lý do `reject_gate2_preprocessing_error`, **TUYỆT ĐỐI không trả về `passed`**; `is_excluded() == True`; `filter_split()` đưa vào `excluded`, không đưa vào `kept`.
4. **`test_gate2_regression_system_runtime_error_propagates_unswallowed`:**
   * Giả lập ngoại lệ hệ thống đột ngột (`RuntimeError`) trong hàm tiền xử lý.
   * *Kết quả:* Cả `gate_2_anti_leakage()` và `is_excluded()` đều ném thẳng `RuntimeError`, không bị nuốt bởi `except Exception: pass`, dừng pipeline an toàn.
5. **`test_gate2_regression_missing_or_tampered_commitment_halts_before_export`:**
   * Thử nghiệm trường hợp hồ sơ hạn chế bị sai mã băm cam kết hoặc bị thiếu tệp trên đĩa.
   * *Kết quả:* `ExclusionRegistry` ném `RuntimeError` ngay từ constructor hoặc hàm `assert_restricted_commitments_verified()`. Các hàm `filter_split()` và `run_selection()` đều dừng ngay lập tức trước khi xuất bất kỳ danh sách hay artifact nào.

---

## 5. Bảng Shard Đề nghị Cho Phép Đợt 1 (Whitelisted Shards Candidate Table - Trình Lead D Phê Duyệt)

Căn cứ vào `configs/source_manifest.json` (nguồn `phreshphish` tại revision khóa `eabec4b7a66324b79cc8a0ad856d1731dc26fe1a`), Thành viên C lập bảng danh mục các shard ứng viên để **trình Lead D xem xét và ban hành quyết định cho phép**:

| Tên Shard | Shard Index | Git-LFS SHA-256 (Theo Manifest) | Dung lượng (bytes) | Audited Rows | Cửa sổ Ngày (Audited) | Tình trạng Vật lý Cục bộ | Đánh giá & Phân loại Kiểm toán của C |
| :--- | :---: | :--- | :---: | :---: | :---: | :---: | :--- |
| `train-000.parquet` | 0 | `9a9c693a95daeddb127c4446df4c5673b3f1a39e457ffe964b9849069bd739fe` | 49,639,686 | 1,000 | 2024-07-04 đến 2025-09-08 | Có tệp (49.6 MB, khớp byte) | ⛔ **CÁCH LY TUYỆT ĐỐI (QUARANTINED)**. Chứa vết tái dựng 20 mẫu Pilot Lô 1 và locator đã lộ trên commit `ad445a7`. |
| `train-001.parquet` | 1 | `260cb9c93299f6b244d48321fe115523159770f4e73446b382473628c6e81d74` | 322,018,201 | 5,780 | 2024-07-02 đến 2025-09-08 | Chưa tải (`null`) | 🟢 **ĐỀ XUẤT HÀNG ĐẦU (RECOMMENDED CANDIDATE)**. Shard sạch, độc lập 100%, chưa từng tiếp xúc. |
| `train-002.parquet` | 2 | `75d891908c1f921542ea9e4f94578f8442da05333621f1cb3ef386c9698935a7` | 354,725,131 | 6,506 | 2024-07-04 đến 2025-09-08 | Chưa tải (`null`) | 🟡 **ỨNG VIÊN DỰ PHÒNG 1 (BACKUP CANDIDATE 1)**. Shard sạch độc lập. |
| `train-003.parquet` | 3 | `0f6bd169f813a9446294597602d1b93457da62c753594d8d1ecb78d20d5dec40` | 433,568,855 | 7,127 | 2024-07-04 đến 2025-09-08 | Chưa tải (`null`) | 🟡 **ỨNG VIÊN DỰ PHÒNG 2 (BACKUP CANDIDATE 2)**. Shard sạch độc lập. |
| `train-004.parquet` | 4 | `82fa46160b9d7779994f7f7ec8cb612f942b8410a0a3325e26134bad72c708ab` | 403,296,550 | 7,425 | 2024-07-03 đến 2025-09-08 | Chưa tải (`null`) | 🟡 **ỨNG VIÊN DỰ PHÒNG 3 (BACKUP CANDIDATE 3)**. Shard sạch độc lập. |
| `train-005.parquet` | 5 | `d5dde3895c6a78daf59ef8c3ee3e67a72a30bc7a7e34782a9dfa503d998334fa` | 463,326,261 | 7,870 | 2024-07-03 đến 2025-09-08 | Chưa tải (`null`) | 🟡 **ỨNG VIÊN DỰ PHÒNG 4 (BACKUP CANDIDATE 4)**. Shard sạch độc lập. |
| `train-055.parquet` | 55 | `94553229b0076a5996f0ba97b2fae38e68cfb99db27e5c6bb094d2df4680aa42` | 418,914,846 | 7,842 | 2024-07-03 đến 2025-09-08 | Có tệp (418.9 MB, khớp byte) | ⛔ **CÁCH LY TUYỆT ĐỐI (QUARANTINED)**. Chứa vết 12 mẫu PhreshPhish đã gán nhãn trong đợt Hiệu chuẩn sạch A/B. |

### Đánh giá Rủi ro Tồn dư (Residual Risk Assessment):
1. **Bản chất rủi ro:** Do Hugging Face Rows API thời điểm pilot chưa khóa revision, chúng ta không có bản lưu byte gốc phản hồi API lịch sử. Vì vậy, lý thuyết tồn tại rủi ro cực nhỏ là một mẫu pilot lịch sử có thể nằm ngoài `train-000`.
2. **Cơ chế kiểm soát phòng vệ chiều sâu (Defense-in-depth):**
   * Nếu có bất kỳ mẫu nào trùng URL, trùng URL sau chuẩn hóa, trùng HTML, trùng HTML sau làm sạch, hoặc chia sẻ tên miền / tenant (`eTLD+1`) với 20 mẫu Pilot Lô 1 hoặc 32 mẫu Lô 2, Cổng 2 sẽ **chặn đứng 100%**.
   * Cổng 3 kiểm tra tương đồng template tuần tự (SimHash distance <= 10, DOM Tag Jaccard >= 0.85) và đa dạng miền (1 mẫu/eTLD+1) sẽ loại bỏ toàn bộ các trang clone có cấu trúc tương tự.
   * Vì vậy, rủi ro rò rỉ mẫu pilot vào tập Main Đợt 1 được chặn đa tầng và kiểm soát hoàn toàn ở mức an toàn cao nhất.

---

## 6. Kết quả Thực nghiệm & Kiểm thử Minh bạch (Test Suite Metrics)

Thực hiện chỉ đạo nghiêm ngặt của Lead D về việc **phân định rõ ràng số lượng tests passed, failed, skipped giữa môi trường Clean Checkout và Môi trường Cục bộ đầy đủ (không gộp các test bị skip thành đã kiểm thực tế)**:

### A. Môi trường Clean Checkout (Môi trường máy B / CI độc lập không có dữ liệu hạn chế):
* Lệnh chạy: `python -m pytest tests/test_pilot_batch1_exclusion.py -v`
* **Kết quả:** **38 passed, 0 failed, 2 skipped** (Tổng 40 ca kiểm thử).
* **Chi tiết 2 ca kiểm thử tự động skip có lý do kiểm toán minh bạch:**
  1. `test_gate0_rejects_quarantined_real_shard_path`: Skipped vì không có shard thực tế `data/raw/phreshphish/data/train-000.parquet` trên clean checkout (lý do: *"Chưa có shard train-000 trên clean checkout"*).
  2. `test_gate2_integration_with_real_restricted_dossier_v2`: Skipped vì không có tệp `data/restricted/pilot_batch1_recovery_dossier_restricted_v2.json` trên clean checkout (lý do: *"Chưa có hồ sơ restricted V2 cục bộ trên clean checkout"*).
* Toàn bộ 38 ca kiểm thử còn lại (gồm cả 5 ca kiểm thử hồi quy mới) đều chạy thành công 100% bằng các fixture tự chứa.

### B. Môi trường Đầy đủ Dữ liệu Hạn chế (Môi trường của C):
* Lệnh chạy: `python -m pytest tests/test_pilot_batch1_exclusion.py -v`
* **Kết quả:** **40 passed, 0 failed, 0 skipped** (100% passed trong 3.47s).
* Cả 2 ca kiểm thử tích hợp thực tế với shard `train-000` và hồ sơ restricted V2 đều chạy và đạt kết quả kiểm toán an toàn.

### C. Kiểm thử Hồi quy Toàn bộ Repo (7 test suites chính):
* Lệnh chạy:
  ```bash
  python -m pytest tests/test_clean_calibration_selection.py tests/test_clean_calibration_blind_view.py tests/test_calibration_release_guards.py tests/test_prepare_calibration_selection.py tests/test_clean_calibration_zero_git_leak_regression.py tests/test_exclusion_registry.py tests/test_pilot_batch1_exclusion.py -q
  ```
* **Kết quả:** **147 passed, 0 failed** (100% passed trong 17.41s).

---

## 7. Bảng Mã Băm Kiểm toán Toàn Diện V4 (Audited Hashes V4)

| Tệp tin / Cấu phần | Vị trí / Tình trạng | Kích thước (bytes) | Mã băm SHA-256 |
| :--- | :--- | :---: | :--- |
| **Gói nén kiểm toán V4 gửi D** | `data/restricted/pilot_batch1_remediation_pack_lead_d_v4.zip` | 24,196 | `782863009b86cf5c051a3c1d3389020e45664966f17d8c223737be89cac9e2ba` |
| **Hồ sơ hạn chế V2 (Lineage V1)** | `data/restricted/pilot_batch1_recovery_dossier_restricted_v2.json` | 23,169 | `adc0b90dddc0aea4c3347cc709fabe6dbc3ea391335965c0ba949503bfcdf1fa` |
| **Hồ sơ hạn chế V1 (Audit trail)** | `data/restricted/pilot_batch1_recovery_dossier_restricted.json` | 20,731 | `2e14d95729a06c2315e8f7587d447a3983e497b0adb90eb50c11508c08a16977` |
| **Bảng chi tiết cấp mẫu (ngoài Git)** | `data/restricted/pilot_batch1_sample_level_audit_table.json` | 20,574 | `6395781aeada3b73c72ee7215bd29a167ea5ab639ce48fe3507bde515bbf128f` |
| **Biên bản sự cố Git Exposure** | `docs/INCIDENT_REPORT_GIT_EXPOSURE_AD445A7.md` | 6,204 | `79505d4a503c87a762d0476d71e0360c940af86c654b37e41558991756d18f51` |
| **Exclusion Registry V1.1.0** | `data/exclusion_registry.json` | 107,424 | `f00df7a63fb6659d78fe065ca4c87445ebe071fb448e1d1f337d740317dd57ea` |
| **Module loại trừ (Đã sửa import & fail-closed)** | `src/phishing/data/exclusion.py` | 19,448 | `5cc8a445b20bb251df523e258f957215134cb804859de3855dff49db856aa041` |
| **Cổng chọn mẫu Selection Gate (Đã sửa)** | `src/phishing/data/selection_gate.py` | 20,308 | `eb3f36a9db9a5dbba62bd1643b68cf4c678d99e9a553132354e792de8753a6a1` |
| **Runner chọn mẫu thực tế** | `scripts/data/run_main_selection.py` | 4,381 | `cc1d45d0801d846454347b877ba95907a1bb1537ba33954876b53ddd87c44fb2` |
| **Bộ kiểm thử 40 ca** | `tests/test_pilot_batch1_exclusion.py` | 43,114 | `a0dab832654bf6ab76614f0098b3b0e7affc710d8e69695d167dfffcff9e75f5` |

---

## 8. Khuyến nghị Quản trị & Yêu cầu Quyết định từ Lead D

Thành viên C tiếp tục duy trì khuyến nghị: **`NO-GO` đối với việc rút mẫu và mở Main Annotation Đợt 1 ngay lúc này**.

**Kính đề nghị Lead D xem xét và chỉ đạo:**
1. **Phê duyệt Phương án xử lý lịch sử Git:** Lựa chọn **Phương án A** (Forward-fix & retire vĩnh viễn 20 mẫu pilot cùng shard `train-000`) hay **Phương án B** (Rewrite history qua `git-filter-repo`).
2. **Quyết định nguồn Shard được phép dùng cho Đợt 1:** Xem xét Bảng Shard đề nghị tại Mục 5 và phê duyệt shard sạch (C đề xuất `train-001.parquet`). Khi D phê duyệt, C mới tiến hành tải tệp và đối soát byte hash thực tế với manifest trước khi cấp cho pipeline.

**Cam kết của C:** Tiếp tục giữ nghiêm ngặt trạng thái:
* `main_annotation_status = "LOCKED"`
* `training_blocked = true`
* `official_test_used = false`
* **Tuyệt đối chưa rút 100 mẫu Main, chưa tạo và chưa phát Blind View cho bất kỳ ai.**
