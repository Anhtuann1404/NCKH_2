# BÁO CÁO KIỂM TOÁN TỔNG HỢP 20 MẪU PILOT (EXCL-PILOT-01), CỔNG CHỌN MẪU MAIN ĐỢT 1 & HỒ SƠ NGUỒN TRÌNH DUYỆT (BẢN V4.1)

**Kính gửi:** Lead D (Anh Tuấn)  
**Người thực hiện:** Thành viên C (Data Pipeline & Thư ký Kiểm toán)  
**Ngày cập nhật:** 16/11/2026 (Bản sửa đổi V4.1 đính chính và hoàn thiện theo chỉ đạo của Lead D Vòng 16)  
**Chế độ thực thi:** Duo Mode (Antigravity & DeepSeek Reason / Code Architecture Review)  
**Trạng thái Quản trị:** `main_annotation_status="LOCKED"`, `training_blocked=true`, `official_test_used=false`

---

## 1. Báo cáo Quản trị Sự cố Tiếp xúc Dữ liệu Cấp Mẫu trên Lịch sử Git (Commit `ad445a7`)

Biên bản sự cố chi tiết đã được lập và ban hành độc lập tại [`docs/INCIDENT_REPORT_GIT_EXPOSURE_AD445A7.md`](file:///d:/nguyen%20thang/NCKH/NCKH_2/docs/INCIDENT_REPORT_GIT_EXPOSURE_AD445A7.md).

* **Tóm tắt sự cố:** Trong commit `ad445a7`, bảng đối soát chi tiết cấp mẫu (Entry ID, locator `train-000:0..19`, nhãn nguồn, ngày và tên miền) đã vô tình xuất hiện trên Git.
* **Phạm vi tiếp xúc:** **Chưa xác minh (Unverified exposure scope)**. Do không có access/traffic logs từ máy chủ GitHub, Thành viên C không đưa ra tuyên bố "0 lượt tiếp xúc" hay "chưa có người xem". Dữ liệu trong commit `ad445a7` vẫn tồn tại trên lịch sử remote repository. C không tuyên bố đã xóa sạch lịch sử Git.
* **Biện pháp khắc phục đã thực hiện:**
  1. Toàn bộ bảng cấp mẫu 20 dòng đã được niêm phong an toàn tại khu vực hạn chế ngoài Git:  
     `data/restricted/pilot_batch1_sample_level_audit_table.json` (20,574 bytes | SHA-256: `6395781aeada3b73c72ee7215bd29a167ea5ab639ce48fe3507bde515bbf128f`).
  2. Báo cáo Git và gói QA cho B chỉ chứa số liệu tổng hợp; toàn bộ tài liệu công khai không còn bảng cấp mẫu hoặc chi tiết giúp tra ngược mẫu.
  3. C giữ nguyên kỷ luật kỹ thuật: **Không tự ý force-push hoặc viết lại lịch sử Git**, bảo toàn vết kiểm toán để Lead D xem xét.
* **Hai phương án quản trị lịch sử trình Lead D quyết định:**
  * **Phương án A (Forward-Fix & Administrative Retirement - Khuyến nghị của C):** Giữ nguyên cây commit lịch sử; đánh dấu 20 mẫu này là đã bị phơi nhiễm locator trong lịch sử nội bộ và **loại trừ vĩnh viễn (retired)** khỏi toàn bộ quá trình phát triển, huấn luyện và kiểm thử mô hình (M0–M3). Shard `train-000` được cách ly vĩnh viễn. Phương án này bảo toàn tính minh bạch và audit trail.
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
Báo cáo công khai và hồ sơ hạn chế có hai số đếm khác nhau xuất phát từ hai định nghĩa đo lường:
1. **Phép đếm theo FQDN / Hostname (`group_id = f"domain:{hostname}"`):** Có **20 giá trị `group_id` duy nhất / 20 mẫu**.
2. **Phép đếm theo Tên miền cấp 2 đã đăng ký (`eTLD+1` theo Public Suffix List):** Có **19 tên miền duy nhất**, do có 2 mẫu là hai subdomain khác nhau cùng thuộc 1 shared tenant/object storage (`r2.dev`).
3. Dưới Cổng 3 (giới hạn 1 mẫu/eTLD+1), 2 mẫu này nếu cùng đi vào tuyển chọn thì mẫu thứ hai sẽ bị loại theo cơ chế chống trùng lặp tenant.

---

## 3. Khắc phục Triệt để Lỗi Tuyến Loại trừ & Khử Hoàn toàn `except Exception: pass` (Fail-Closed Remediation)

Tiếp thu phản biện kỹ thuật của Lead D tại Vòng 15 và kết quả tham vấn kiến trúc cùng DeepSeek Reason Mode (`scratch/deepseek_r15_recommendations.md`), Thành viên C đã sửa tận gốc các khuyết tật:

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
     * Trong `gate_2_anti_leakage()`: Trả về `(False, "reject_gate2_preprocessing_error")`. Tuyệt đối không biến lỗi xử lý thành `(True, "passed")`!
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
   * *Kết quả:* Cổng 2 từ chối rõ ràng với lý do `reject_gate2_preprocessing_error`, không trả về `passed`; `is_excluded() == True`; `filter_split()` đưa vào `excluded`, không đưa vào `kept`.
4. **`test_gate2_regression_system_runtime_error_propagates_unswallowed`:**
   * Giả lập ngoại lệ hệ thống đột ngột (`RuntimeError`) trong hàm tiền xử lý.
   * *Kết quả:* Cả `gate_2_anti_leakage()` và `is_excluded()` đều ném thẳng `RuntimeError`, không bị nuốt bởi `except Exception: pass`, dừng pipeline an toàn.
5. **`test_gate2_regression_missing_or_tampered_commitment_halts_before_export`:**
   * Thử nghiệm trường hợp hồ sơ hạn chế bị sai mã băm cam kết hoặc bị thiếu tệp trên đĩa.
   * *Kết quả:* `ExclusionRegistry` ném `RuntimeError` ngay từ constructor hoặc hàm `assert_restricted_commitments_verified()`. Các hàm `filter_split()` và `run_selection()` đều dừng ngay lập tức trước khi xuất bất kỳ danh sách hay artifact nào.

---

## 5. Bảng Shard Đề nghị Cho Phép Đợt 1 & Đính chính Ba Mức Bằng chứng (Trình Lead D Phê Duyệt)

Căn cứ vào `configs/source_manifest.json` (nguồn `phreshphish` tại revision khóa `eabec4b7a66324b79cc8a0ad856d1731dc26fe1a`), Thành viên C đính chính bảng kiểm kê shard theo đúng 3 mức bằng chứng thực tế:
- **Mức 1 (Metadata nguồn đã ghi nhận):** Mã băm Git-LFS pointer, dung lượng LFS, số dòng audited và cửa sổ ngày qua column projection.
- **Mức 2 (Byte Parquet đã tải & đối chiếu hash thực tế trên đĩa):** Trạng thái tệp vật lý và mã băm `locally_verified_sha256`. Nếu chưa tải, ghi nhận rõ ràng là `Chưa tải (null)`.
- **Mức 3 (Quét loại trừ, trùng lặp & tương đồng trên dữ liệu thật):** Kết quả chạy qua pipeline Gate 0–4 trên toàn bộ bản ghi của shard. Nếu chưa tải thì ghi nhận là `Chưa quét (Chưa xác minh)`.

| Tên Shard | Shard Index | Mức 1: Metadata Nguồn (Git-LFS SHA-256 / Dung lượng / Audited Rows / Ngày) | Mức 2: Byte Parquet Trên Đĩa (`locally_verified_sha256`) | Mức 3: Quét Tuyến Gate 0–4 Trên Dữ Liệu Thật | Hiện Trạng Kiểm Toán & Phân Loại Đề Xuất |
| :--- | :---: | :--- | :---: | :---: | :--- |
| `train-000.parquet` | 0 | `9a9c693a95daeddb127c4446df4c5673b3f1a39e457ffe964b9849069bd739fe`<br>49,639,686 bytes \| 1,000 rows \| 2024-07-04 đến 2025-09-08 | Đã tải<br>(Khớp byte SHA-256 metadata) | Đã quét đối soát khi tái dựng Pilot Lô 1 | ⛔ **CÁCH LY TUYỆT ĐỐI (QUARANTINED)**.<br>Chứa vết tái dựng 20 mẫu Pilot Lô 1 và locator đã lộ trên commit `ad445a7`. Bị loại trừ vĩnh viễn khỏi mọi đợt chọn mẫu thực nghiệm. |
| `train-055.parquet` | 55 | `94553229b0076a5996f0ba97b2fae38e68cfb99db27e5c6bb094d2df4680aa42`<br>418,914,846 bytes \| 7,842 rows \| 2024-07-03 đến 2025-09-08 | Đã tải<br>(Khớp byte SHA-256 metadata) | Đã quét chọn 12 mẫu PhreshPhish Hiệu chuẩn A/B | ⛔ **CÁCH LY TUYỆT ĐỐI (QUARANTINED)**.<br>Chứa vết 12 mẫu đã tiếp xúc trong đợt Hiệu chuẩn sạch. Bị cách ly khỏi Đợt 1 Main Annotation. |
| `train-001.parquet` | 1 | `260cb9c93299f6b244d48321fe115523159770f4e73446b382473628c6e81d74`<br>322,018,201 bytes \| 5,780 rows \| 2024-07-02 đến 2025-09-08 | **Chưa tải (`null`)** | **Chưa quét (Chưa xác minh)** | 🟢 **ỨNG VIÊN ĐỀ NGHỊ SỬ DỤNG (PROPOSED CANDIDATE)**.<br>Shard tiềm năng, không có tiền sử tiếp xúc với Pilot hay Hiệu chuẩn trong metadata. Chưa phải shard đã xác minh byte hay đã chứng minh sạch. Chờ D phê duyệt lệnh tải để C đối soát byte hash thực tế. |
| `train-002.parquet` | 2 | `75d891908c1f921542ea9e4f94578f8442da05333621f1cb3ef386c9698935a7`<br>354,725,131 bytes \| 6,506 rows \| 2024-07-04 đến 2025-09-08 | **Chưa tải (`null`)** | **Chưa quét (Chưa xác minh)** | 🟡 **ỨNG VIÊN DỰ PHÒNG 1 (BACKUP CANDIDATE 1)**.<br>Shard độc lập chưa tải. |
| `train-003.parquet` | 3 | `0f6bd169f813a9446294597602d1b93457da62c753594d8d1ecb78d20d5dec40`<br>433,568,855 bytes \| 7,127 rows \| 2024-07-04 đến 2025-09-08 | **Chưa tải (`null`)** | **Chưa quét (Chưa xác minh)** | 🟡 **ỨNG VIÊN DỰ PHÒNG 2 (BACKUP CANDIDATE 2)**.<br>Shard độc lập chưa tải. |
| `train-004.parquet` | 4 | `82fa46160b9d7779994f7f7ec8cb612f942b8410a0a3325e26134bad72c708ab`<br>403,296,550 bytes \| 7,425 rows \| 2024-07-03 đến 2025-09-08 | **Chưa tải (`null`)** | **Chưa quét (Chưa xác minh)** | 🟡 **ỨNG VIÊN DỰ PHÒNG 3 (BACKUP CANDIDATE 3)**.<br>Shard độc lập chưa tải. |
| `train-005.parquet` | 5 | `d5dde3895c6a78daf59ef8c3ee3e67a72a30bc7a7e34782a9dfa503d998334fa`<br>463,326,261 bytes \| 7,870 rows \| 2024-07-03 đến 2025-09-08 | **Chưa tải (`null`)** | **Chưa quét (Chưa xác minh)** | 🟡 **ỨNG VIÊN DỰ PHÒNG 4 (BACKUP CANDIDATE 4)**.<br>Shard độc lập chưa tải. |

### Đánh giá Rủi ro Tồn dư (Residual Risk Assessment - Đã loại bỏ khẳng định tuyệt đối):
1. **Bản chất rủi ro:** Do Hugging Face Rows API thời điểm pilot chưa khóa revision, chúng ta không có bản lưu nguyên byte của phản hồi API lịch sử. Vì vậy, lý thuyết tồn tại rủi ro là một mẫu pilot lịch sử có thể nằm ngoài `train-000`. C duy trì `content_identity_verified=false` và `mapping_status="unresolved_source_mapping"` trong `data/exclusion_registry.json`.
2. **Cơ chế giảm thiểu rủi ro đối với những dấu vết đã biết:**
   * Sáu lớp mã băm đối soát trong `ExclusionRegistry` đối chiếu với các bản ghi đã biết của Lô 1 (20 mẫu) và Lô 2 (32 mẫu) giúp phát hiện và loại bỏ các mẫu trùng URL thô, URL chuẩn hóa, HTML thô, HTML làm sạch hoặc chia sẻ nhóm miền / tenant (`eTLD+1`).
   * Cổng 3 kiểm tra tương đồng template tuần tự (SimHash distance <= 10, DOM Tag Jaccard >= 0.85) và đa dạng miền (tối đa 1 mẫu/eTLD+1) giúp giảm thiểu các trang clone sinh từ cùng phishing kit.
   * **Giới hạn khoa học thừa nhận:** Các biện pháp trên giúp **giảm thiểu đáng kể rủi ro đối với các dấu vết đã biết**, nhưng **chưa chứng minh được việc loại bỏ hoàn toàn rủi ro tồn dư** đối với các mẫu lịch sử chưa xác định được byte gốc hay vị trí phân phối thực tế của Rows API thời điểm trước khóa revision.

---

## 6. Kết quả Thực nghiệm & Đối Soát Log Kiểm thử Đúng Tệp Vật Lý

Đối soát chính xác từng số liệu với tệp log vật lý thực tế trên đĩa:

### A. Môi trường Cục bộ Đầy đủ Dữ liệu Hạn chế (Môi trường của C):
* Lệnh chạy: `python -m pytest tests/test_pilot_batch1_exclusion.py -v`
* **Kết quả:** **`40 passed in 2.44s`** (40/40 passed, 0 failed, 0 skipped).
* **Tệp log vật lý kèm theo:** [`test_report_pilot_batch1_exclusion_v4_1.log`](file:///d:/nguyen%20thang/NCKH/NCKH_2/test_report_pilot_batch1_exclusion_v4_1.log)
  * *Dung lượng:* `5,917 bytes`
  * *Mã băm SHA-256:* `2db9f8eab72940d66c197a155595d71de9540d3ada3e297c1f546ade6cf54ed4`
  * *Dòng kết thúc log:* `============================= 40 passed in 2.44s ==============================`

### B. Phép Tự Kiểm thử Mô phỏng Clean Checkout do C Thực hiện (Self-test Simulation by C):
* Mô phỏng môi trường không có shard `train-000` và tệp restricted ngoài Git để xác minh tính tự chứa của test suite.
* **Kết quả:** **`38 passed, 2 skipped in 1.93s`** (38 passed, 0 failed, 2 skipped).
* **Chi tiết 2 ca test tự động skip có lý do kiểm toán minh bạch:**
  1. `test_gate0_rejects_quarantined_real_shard_path`: Skipped vì không có shard `train-000` thật trên clean checkout (lý do: *"Chưa có shard train-000 trên clean checkout"*).
  2. `test_gate2_integration_with_real_restricted_dossier_v2`: Skipped vì không có tệp restricted V2 thật trên clean checkout (lý do: *"Chưa có hồ sơ restricted V2 cục bộ trên clean checkout"*).
* **Tệp log vật lý kèm theo:** [`test_report_clean_checkout_simulation_v4_1.log`](file:///d:/nguyen%20thang/NCKH/NCKH_2/test_report_clean_checkout_simulation_v4_1.log)
  * *Dung lượng:* `5,919 bytes`
  * *Mã băm SHA-256:* `ded94b99f1b1718eac6d9eaf01065db16b31ddbd3db87fd00185fa687622b022`
  * *Dòng kết thúc log:* `======================== 38 passed, 2 skipped in 1.93s ========================`
* **Lưu ý kiểm toán:** Đây là phép tự kiểm mô phỏng của C; **QA Lead B chưa phát hành báo cáo QA cho commit V4/V4.1**. B sẽ tự chạy kiểm định độc lập trên máy của B và phát hành báo cáo riêng.

### C. Kiểm thử 7 Bộ Test Liên Quan đến Tuyến Dữ Liệu và Chống Rò Rỉ:
* Lệnh chạy:
  ```bash
  python -m pytest tests/test_clean_calibration_selection.py tests/test_clean_calibration_blind_view.py tests/test_calibration_release_guards.py tests/test_prepare_calibration_selection.py tests/test_clean_calibration_zero_git_leak_regression.py tests/test_exclusion_registry.py tests/test_pilot_batch1_exclusion.py -v
  ```
* **Kết quả:** **`147 passed in 8.62s`** (Phạm vi 7 bộ test liên quan đến dữ liệu, phân tách và chống rò rỉ; không phải toàn bộ repo).
* **Tệp log vật lý kèm theo:** [`test_report_7_suites_v4_1.log`](file:///d:/nguyen%20thang/NCKH/NCKH_2/test_report_7_suites_v4_1.log)
  * *Dung lượng:* `21,476 bytes`
  * *Mã băm SHA-256:* `81b62c32da70745b983e5bffad5fc36d8a5557f1c7939a06dbd49b13132c3382`
  * *Dòng kết thúc log:* `============================= 147 passed in 8.62s =============================`

---

## 7. Bảng Mã Băm Kiểm toán Toàn Diện V4.1 (Audited Hashes V4.1)

Toàn bộ kích thước và mã băm SHA-256 được đo đạc trực tiếp trên byte vật lý thực tế của từng tệp:

| Tệp tin / Cấu phần | Vị trí / Tình trạng | Kích thước (bytes) | Mã băm SHA-256 |
| :--- | :--- | :---: | :--- |
| **Gói nén kiểm toán V4.1 gửi D** | `data/restricted/pilot_batch1_remediation_pack_lead_d_v4_1.zip` | Ngoài Git (Niêm phong) | Mã băm SHA-256 công bố tại biên bản bàn giao |
| **Gói nén kiểm toán V4 cũ (Audit trail)** | `data/restricted/pilot_batch1_remediation_pack_lead_d_v4.zip` | 24,196 | `782863009b86cf5c051a3c1d3389020e45664966f17d8c223737be89cac9e2ba` |
| **Hồ sơ hạn chế V2 (Lineage V1)** | `data/restricted/pilot_batch1_recovery_dossier_restricted_v2.json` | 23,169 | `adc0b90dddc0aea4c3347cc709fabe6dbc3ea391335965c0ba949503bfcdf1fa` |
| **Hồ sơ hạn chế V1 (Audit trail)** | `data/restricted/pilot_batch1_recovery_dossier_restricted.json` | 20,731 | `2e14d95729a06c2315e8f7587d447a3983e497b0adb90eb50c11508c08a16977` |
| **Bảng chi tiết cấp mẫu (ngoài Git)** | `data/restricted/pilot_batch1_sample_level_audit_table.json` | 20,574 | `6395781aeada3b73c72ee7215bd29a167ea5ab639ce48fe3507bde515bbf128f` |
| **Biên bản sự cố Git Exposure** | `docs/INCIDENT_REPORT_GIT_EXPOSURE_AD445A7.md` | 6,204 | `79505d4a503c87a762d0476d71e0360c940af86c654b37e41558991756d18f51` |
| **Exclusion Registry V1.1.0** | `data/exclusion_registry.json` | 107,424 | `f00df7a63fb6659d78fe065ca4c87445ebe071fb448e1d1f337d740317dd57ea` |
| **Module loại trừ (Đã sửa import & fail-closed)** | `src/phishing/data/exclusion.py` | 19,448 | `5cc8a445b20bb251df523e258f957215134cb804859de3855dff49db856aa041` |
| **Cổng chọn mẫu Selection Gate (Đã sửa)** | `src/phishing/data/selection_gate.py` | 20,308 | `eb3f36a9db9a5dbba62bd1643b68cf4c678d99e9a553132354e792de8753a6a1` |
| **Runner chọn mẫu thực tế** | `scripts/data/run_main_selection.py` | 4,381 | `cc1d45d0801d846454347b877ba95907a1bb1537ba33954876b53ddd87c44fb2` |
| **Bộ kiểm thử 40 ca** | `tests/test_pilot_batch1_exclusion.py` | 43,114 | `a0dab832654bf6ab76614f0098b3b0e7affc710d8e69695d167dfffcff9e75f5` |
| **Log 40 tests (Môi trường Cục bộ C)** | `test_report_pilot_batch1_exclusion_v4_1.log` | 5,917 | `2db9f8eab72940d66c197a155595d71de9540d3ada3e297c1f546ade6cf54ed4` |
| **Log 38 passed / 2 skipped (Tự kiểm mô phỏng)** | `test_report_clean_checkout_simulation_v4_1.log` | 5,919 | `ded94b99f1b1718eac6d9eaf01065db16b31ddbd3db87fd00185fa687622b022` |
| **Log 147 tests (7 test suites)** | `test_report_7_suites_v4_1.log` | 21,476 | `81b62c32da70745b983e5bffad5fc36d8a5557f1c7939a06dbd49b13132c3382` |

---

## 8. Danh mục Các Vấn đề Còn Mở & Yêu cầu Quyết định từ Lead D

Thành viên C tiếp tục duy trì khuyến nghị: **`NO-GO` đối với việc rút mẫu và mở Main Annotation Đợt 1 ngay lúc này**.

### A. Danh mục các điểm còn mở (Open Items):
1. **QA Lead B tái thẩm định độc lập:** Chờ B thực hiện kiểm định độc lập trên clean checkout và ký báo cáo QA riêng cho commit V4.1 (chữ ký V3 không áp dụng tự động cho V4/V4.1).
2. **Quyết định phương án xử lý lịch sử Git:** Chờ Lead D phê duyệt chính thức Phương án A (Forward-fix & retire vĩnh viễn 20 mẫu pilot cùng shard `train-000`) hay Phương án B.
3. **Quyết định nguồn Shard được phép dùng cho Đợt 1:** Chờ Lead D xem xét bảng tại Mục 5 và phê duyệt shard sạch (C đề xuất `train-001.parquet`).
4. **Đối soát byte Parquet thực tế sau khi được phê duyệt tải:** Khi Lead D ban hành lệnh tải `train-001.parquet`, C sẽ tải tệp, tự đối soát SHA-256 byte thực tế trên đĩa so với `source_manifest.json` (`locally_verified_sha256`) và báo cáo D trước khi nạp vào pipeline.

### B. Cam kết Bất biến của C:
* `main_annotation_status = "LOCKED"`
* `training_blocked = true`
* `official_test_used = false`
* **Tuyệt đối chưa rút 100 mẫu Main, chưa tạo và chưa phát Blind View cho bất kỳ ai.**
