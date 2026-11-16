# BÁO CÁO KIỂM TOÁN TỔNG HỢP 20 MẪU PILOT (EXCL-PILOT-01), CỔNG CHỌN MẪU MAIN ĐỢT 1 & HỒ SƠ NGUỒN TRÌNH DUYỆT (BẢN V4.2)

**Kính gửi:** Lead D (Anh Tuấn)  
**Người thực hiện:** Thành viên C (Data Pipeline & Thư ký Kiểm toán)  
**Ngày cập nhật:** 17/11/2026 (Bản sửa đổi V4.2 đính chính bảng kê và hoàn thiện theo chỉ đạo của Lead D Vòng 17)  
**Chế độ thực thi:** Duo Mode (Antigravity & DeepSeek Reason Architecture Review - Session R17)  
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

### A. Kết quả Xác minh Chuỗi Bằng chứng Pilot Gốc (Lead D & C Đối soát Độc lập):
* **Tìm lại bản phản hồi Rows API gốc:** Tệp Rows API gốc được lưu trữ tại `data/source_audit/phreshphish/pilot_20_rows.json` (bàn giao qua gói hạn chế `pilot20_provenance_handoff_for_C_RESTRICTED.zip`).
  * *Dung lượng:* `7,186,229 bytes`
  * *Mã băm SHA-256:* `738ea69b920cb3037d7e9da38590024d8faa5f34c2eca6c760cb34690f2f190f`
  * *Đối soát lịch sử:* Khớp 100% với `pilot_summary.json` tại commit `bc674e9` và `batch_sha256` của `EXCL-PILOT-01` tại commit `a62105a`.
  * *Kiểm tra dữ liệu:* Tệp có đủ 20 dòng, 20 cặp (URL hash, HTML hash) nguyên bản duy nhất, 0 dòng bị cắt (`partial: false`).
* **Đối chiếu Parquet tại revision khóa `eabec4b7a66324b79cc8a0ad856d1731dc26fe1a`:**
  * Cả Lead D và C đã kiểm tra dung lượng và SHA-256 của hai tệp Parquet trước khi đọc, băm riêng URL và HTML trên chuỗi UTF-8 nguyên gốc rồi so theo cặp:
    - `train-000.parquet` (49,639,686 bytes | SHA-256: `9a9c693a...`, 1,000 dòng): Khớp chính xác **20/20 cặp tại đúng 20 hàng đầu tiên (`row_offset: 0..19`)**, 0 đa vị trí (0 duplicates), 0 thiếu.
    - `train-055.parquet` (20,213,199 bytes | SHA-256: `205a7e1c...`, 361 dòng): Khớp **0/20 cặp** (hoàn toàn cách ly với 20 mẫu Pilot).
* **Đối chiếu hồ sơ cũ và V4.1:** Chỉ số Pilot, cặp hash URL/HTML và vị trí nguồn của cả 20 mẫu đều khớp `raw20_mapping_check.json` (SHA-256: `7c7ea17d...`), `pilot_mapping_reproducible.json` (SHA-256: `31aa501b...`) và Dossier V2 trong ZIP V4.1.
* **Kết luận chuẩn xác theo chỉ đạo của Lead D:**
  > **Bản phản hồi Rows API lưu từ lần thu thập đã được xác minh bằng hash lịch sử. Cả 20 cặp URL/HTML và locator đã được đối chiếu với Parquet ở revision khóa.**  
  > * Giữ `rows_api_revision_pinned=false` vì đó là cách nhóm đã gọi API lúc thu thập ban đầu.  
  > * Phạm vi kiểm vị trí duy nhất là **hai shard đã quét** (`train-000` và `train-055`). Shard `train-001` và các shard còn lại cần được kiểm theo phạm vi Lead D phê duyệt.

### B. Phát hành Dossier Hạn chế V3 & Bảo lưu Lineage Audit Trail:
* **Hồ sơ hạn chế V3 hiện hành:** `data/restricted/pilot_batch1_recovery_dossier_restricted_v3.json`
  * *Dung lượng:* `29,018 bytes`
  * *Mã băm SHA-256:* `0d817d0b1eca177f22794f21c305db542194d6e7c9f9dc418bd26e5d8a64c5a3`
  * *Trạng thái định danh:* `"content_identity_verified": true`, `"content_identity_status": "verified_from_historical_rows_api_and_pinned_parquet"`.
  * *Trạng thái ánh xạ:* `"mapping_status": "verified_at_pinned_revision_2_shards_audited"`, `"rows_api_revision_pinned": false`.
  * *Trạng thái phê duyệt:* `"approval_status": "pending_lead_d_signoff"`.
* **Hồ sơ V2 cũ (Bảo lưu audit trail):** `data/restricted/pilot_batch1_recovery_dossier_restricted_v2.json` (`23,169 bytes` | SHA-256: `adc0b90d...`).
* **Hồ sơ V1 cũ (Bảo lưu audit trail):** `data/restricted/pilot_batch1_recovery_dossier_restricted.json` (`20,731 bytes` | SHA-256: `2e14d957...`).

### C. Mối quan hệ giữa 20 mẫu Pilot Lô 1 với `EXCL-REAL-PILOT-32` & Giải trình Số đếm 246:
* **Giao với Lô Pilot 32 (`EXCL-REAL-PILOT-32`):** Cả 20 cặp URL/HTML của Pilot 20 đều có trong `EXCL-REAL-PILOT-32` (Giao = 20).
* **Số mẫu hợp (Union):** Khi báo cáo số mẫu duy nhất giữa hai lô, tính theo **hợp các cặp hash đã đối chiếu** thay vì cộng gộp 20 + 32; hợp của hai lô là **32 mẫu duy nhất**.
* **Giải trình con số 246 trong Registry:**
  - Con số **246** là **tổng mục khai báo theo lô (sum of declared batch items)** trên 10 lô loại trừ trong `data/exclusion_registry.json`.
  - Tổng số mẫu duy nhất toàn registry sau khi khử giao (union of distinct hash pairs) là **226 mẫu** (do 20 mẫu của `EXCL-PILOT-01` nằm hoàn toàn trong `EXCL-REAL-PILOT-32`).
  - Mọi thống kê mẫu duy nhất toàn registry đều được tính theo phép hợp các cặp hash đối chiếu, tránh hiểu nhầm về mặt định lượng khoa học.

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

### C. Đối chiếu Mã nguồn & Kết quả Cụ thể trên Ba Tuyến `is_excluded()`, `filter_split()` và `gate_2_anti_leakage()`:
* **Hiện trạng kiểm định:** Các thay đổi sửa lỗi import, hợp đồng `clean_html(page_url=...)` và loại bỏ `except Exception: pass` đã được đối chiếu trong mã nguồn; QA Lead B đã thực hiện thẩm định độc lập phần công khai tại commit `2eddf41b5fe9148f5b502cb82b101635f804d5b6` và ký `PASS`; hệ thống hiện đang chờ quyết định của Lead D về nguồn và các bước tiếp theo.
* **Kết quả cụ thể của các ca hồi quy đã chạy trên ba tuyến xử lý:**
  1. **Tuyến `is_excluded()`:** Cả 5 ca hồi quy chuyên biệt (`test_gate2_regression_*`) đều xử lý fail-closed. Mẫu có URL bất thường hoặc HTML chứa script được nhận diện qua hàm chuẩn hóa; mẫu có URL chứa ký tự null/lỗi tiền xử lý (`ValueError`) trả về `True` (loại trừ an toàn); ngoại lệ hệ thống (`RuntimeError`) không bị nuốt bởi `except Exception: pass` mà ném thẳng ra ngoài.
  2. **Tuyến `filter_split()`:** Đưa toàn bộ các bản ghi khớp mã băm cam kết hoặc gặp lỗi định dạng vào phân vùng `excluded`; phân vùng `kept` rỗng (không giữ lại bất kỳ bản ghi lỗi nào).
  3. **Tuyến `gate_2_anti_leakage()`:** Từ chối rõ ràng với lý do minh bạch `reject_gate2_preprocessing_error` hoặc `reject_exclusion_registry_match`; tuyệt đối không trả về `(True, "passed")` cho bất kỳ mẫu nào gặp lỗi hoặc khớp cam kết loại trừ.
* **Quy tắc phối hợp:** `gate_2_anti_leakage()` gọi trực tiếp `self.exclusion_registry.is_excluded(sample)` để bảo đảm rằng một bản ghi khi bị từ chối ở `is_excluded()` cũng sẽ bị loại ở `filter_split()` và Cổng 2.

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

## 5. Bảng Shard Đề xuất Đợt 1 & Đính chính Ba Mức Bằng chứng (Trình Lead D Xem xét)

Căn cứ vào `configs/source_manifest.json` (nguồn `phreshphish` tại revision khóa `eabec4b7a66324b79cc8a0ad856d1731dc26fe1a`), Thành viên C đính chính bảng kiểm kê shard theo đúng 3 mức bằng chứng thực tế:
- **Mức 1 (Metadata nguồn đã ghi nhận):** Mã băm Git-LFS pointer, dung lượng LFS, số dòng audited và cửa sổ ngày qua column projection.
- **Mức 2 (Byte Parquet đã tải & đối chiếu hash thực tế trên đĩa):** Trạng thái tệp vật lý và mã băm `locally_verified_sha256`. Nếu chưa tải, ghi nhận rõ ràng là `Chưa tải (null)`.
- **Mức 3 (Quét loại trừ, trùng lặp & tương đồng trên dữ liệu thật):** Kết quả chạy qua pipeline Gate 0–4 trên toàn bộ bản ghi của shard. Nếu chưa tải thì ghi nhận là `Chưa quét (Chưa xác minh)`.

| Tên Shard | Shard Index | Mức 1: Metadata Nguồn (Git-LFS SHA-256 / Dung lượng / Audited Rows / Ngày) | Mức 2: Byte Parquet Trên Đĩa (`locally_verified_sha256`) | Mức 3: Quét Tuyến Gate 0–4 Trên Dữ Liệu Thật | Hiện Trạng Kiểm Toán & Phân Loại Đề Xuất |
| :--- | :---: | :--- | :---: | :---: | :--- |
| `train-000.parquet` | 0 | `9a9c693a95daeddb127c4446df4c5673b3f1a39e457ffe964b9849069bd739fe`<br>49,639,686 bytes \| 1,000 rows \| 2024-07-04 đến 2025-09-08 | Đã tải<br>(Khớp byte SHA-256 metadata) | Đã quét đối soát khi tái dựng Pilot Lô 1 | ⛔ **CÁCH LY TUYỆT ĐỐI (QUARANTINED)**.<br>Chứa vết tái dựng 20 mẫu Pilot Lô 1 và locator đã lộ trên commit `ad445a7`. Bị loại trừ vĩnh viễn khỏi mọi đợt chọn mẫu thực nghiệm. |
| `train-055.parquet` | 55 | `205a7e1cf4fb11032683e90fdbd1c13ddc9d9dd86109658d13e69929b53b31d0`<br>20,213,199 bytes \| 361 rows \| 2024-07-03 đến 2025-09-08 | Đã tải<br>(Khớp byte SHA-256 thực tế trên đĩa) | Đã quét đối soát Pilot: Khớp 0/20 cặp | ⛔ **CÁCH LY TUYỆT ĐỐI (QUARANTINED)**.<br>Chứa vết 12 mẫu đã tiếp xúc trong đợt Hiệu chuẩn sạch (Clean Calibration). Đã đối soát độc lập cách ly với Pilot 20: khớp 0/20 cặp. Bị cách ly khỏi Đợt 1 Main Annotation.<br>*(Đính chính: Số cũ 418,914,846 bytes / 94553229... là số ước tính nháp chưa kiểm)* |
| `train-001.parquet` | 1 | `260cb9c93299f6b244d48321fe115523159770f4e73446b382473628c6e81d74`<br>322,018,201 bytes \| 5,780 rows \| 2024-07-02 đến 2025-09-08 | **Chưa tải (`null`)** | **Chưa quét (Chưa xác minh)** | 🟢 **ĐỀ NGHỊ CHO PHÉP TẢI VÀ KIỂM NGUỒN `train-001.parquet`**.<br>Shard tiềm năng trong manifest, không có tiền sử tiếp xúc với Pilot hay Hiệu chuẩn trong metadata. Hiện có metadata và hash Git-LFS dự kiến (`260cb9c9...`, 322,018,201 bytes, 5,780 hàng audited, cửa sổ ngày được phép lấy mẫu: `2024-10-01` đến `2025-09-08`). Byte Parquet trên đĩa (`locally_verified_sha256: null`) và kết quả rà soát loại trừ Gate 0–4 vẫn chờ kiểm sau khi Lead D phê duyệt lệnh kiểm nguồn. |
| `train-002.parquet` | 2 | `75d891908c1f921542ea9e4f94578f8442da05333621f1cb3ef386c9698935a7`<br>354,725,131 bytes \| 6,506 rows \| 2024-07-04 đến 2025-09-08 | **Chưa tải (`null`)** | **Chưa quét (Chưa xác minh)** | 🟡 **ỨNG VIÊN DỰ PHÒNG 1 (BACKUP CANDIDATE 1)**.<br>Shard độc lập chưa tải. |
| `train-003.parquet` | 3 | `0f6bd169f813a9446294597602d1b93457da62c753594d8d1ecb78d20d5dec40`<br>433,568,855 bytes \| 7,127 rows \| 2024-07-04 đến 2025-09-08 | **Chưa tải (`null`)** | **Chưa quét (Chưa xác minh)** | 🟡 **ỨNG VIÊN DỰ PHÒNG 2 (BACKUP CANDIDATE 2)**.<br>Shard độc lập chưa tải. |
| `train-004.parquet` | 4 | `82fa46160b9d7779994f7f7ec8cb612f942b8410a0a3325e26134bad72c708ab`<br>403,296,550 bytes \| 7,425 rows \| 2024-07-03 đến 2025-09-08 | **Chưa tải (`null`)** | **Chưa quét (Chưa xác minh)** | 🟡 **ỨNG VIÊN DỰ PHÒNG 3 (BACKUP CANDIDATE 3)**.<br>Shard độc lập chưa tải. |
| `train-005.parquet` | 5 | `d5dde3895c6a78daf59ef8c3ee3e67a72a30bc7a7e34782a9dfa503d998334fa`<br>463,326,261 bytes \| 7,870 rows \| 2024-07-03 đến 2025-09-08 | **Chưa tải (`null`)** | **Chưa quét (Chưa xác minh)** | 🟡 **ỨNG VIÊN DỰ PHÒNG 4 (BACKUP CANDIDATE 4)**.<br>Shard độc lập chưa tải. |

### Đánh giá Rủi ro Tồn dư (Residual Risk Assessment - Cập nhật sau khi xác minh chuỗi bằng chứng Rows API & Parquet):
1. **Kết quả xác minh chuỗi bằng chứng:**
   * Tệp Rows API gốc `pilot_20_rows.json` (7,186,229 bytes | SHA-256: `738ea69b920cb3037d7e9da38590024d8faa5f34c2eca6c760cb34690f2f190f`) đã được Lead D tìm lại và C đối soát độc lập: khớp 100% với hash lịch sử công bố tại `bc674e9` và `a62105a`.
   * Cả 20 cặp URL/HTML và locator đã được đối chiếu trực tiếp trên byte UTF-8 với Parquet ở revision khóa `eabec4b7a66324b79cc8a0ad856d1731dc26fe1a`: toàn bộ 20/20 khớp chính xác tại `train-000` (`row_offset: 0..19`), khớp 0/20 tại `train-055`.
   * Phạm vi kiểm vị trí duy nhất đã hoàn thành trên **hai shard đã quét** (`train-000` và `train-055`).
2. **Giới hạn khoa học và nguyên tắc quản trị rủi ro:**
   * Giữ nguyên `rows_api_revision_pinned = false` vì thời điểm thu thập lịch sử API chưa khóa revision.
   * Cập nhật Dossier V3 với `content_identity_verified = true`, `mapping_status = "verified_at_pinned_revision_2_shards_audited"` và `approval_status = "pending_lead_d_signoff"`.
   * Trong `data/exclusion_registry.json`, `EXCL-PILOT-01` trỏ tới Dossier V3, cập nhật `commitment_sha256 = "0d817d0b1eca177f22794f21c305db542194d6e7c9f9dc418bd26e5d8a64c5a3"`, tạm giữ `mapping_status = "unresolved_source_mapping"` để chờ Lead D ký nghiệm thu chính thức.
   * Shard `train-001` và các shard khác sẽ tiếp tục được quét toàn diện qua 6 lớp mã băm của Cổng 2 và lọc tương đồng của Cổng 3 ngay khi Lead D phê duyệt lệnh kiểm nguồn.

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
* **Ghi nhận QA độc lập của B:** QA Lead B đã hoàn thành thẩm định độc lập trên clean checkout tại commit `2eddf41` (văn bản `docs/QA_REPORT_SELECTION_GATE_2EDDF41_B.md`, SHA-256 `45dacb831c5f6ceb40570f3870bbe3245a3b2ef9d16c1e2b6c1af3a76f6fda4b`) với kết luận **`PASS`** đối với toàn bộ mã nguồn 5 Cổng, ExclusionRegistry, Runner, test suite 40 ca và tài liệu đặc tả công khai; ghi riêng **`PENDING`** đối với hồ sơ hạn chế V2 và quyết định mở cổng của Lead D.

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

## 7. Bảng Mã Băm Kiểm toán Toàn Diện V4.2 (Audited Hashes V4.2)

Toàn bộ kích thước và mã băm SHA-256 được đo đạc trực tiếp trên byte vật lý thực tế của từng tệp:

| Tệp tin / Cấu phần | Vị trí / Tình trạng | Kích thước (bytes) | Mã băm SHA-256 |
| :--- | :--- | :---: | :--- |
| **Gói nén kiểm toán V4.2 gửi D (Hiện hành)** | `data/restricted/pilot_batch1_remediation_pack_lead_d_v4_2.zip` | 1,713,628 | `043be4b4dff9201dc7ee4de0bd5b0545bcdb6de7d434299a570a4b4d89b8d744` |
| **Hồ sơ hạn chế V3 (Lineage V2)** | `data/restricted/pilot_batch1_recovery_dossier_restricted_v3.json` | 29,018 | `0d817d0b1eca177f22794f21c305db542194d6e7c9f9dc418bd26e5d8a64c5a3` |
| **Gói nén kiểm toán V4.1 cũ (Audit trail)** | `data/restricted/pilot_batch1_remediation_pack_lead_d_v4_1.zip` | 30,280 | `f06fb890be501eb71e51c21b52d017dbce7bff66beb91fc884546c0817980b21` |
| **Hồ sơ hạn chế V2 (Lineage V1 - Audit trail)** | `data/restricted/pilot_batch1_recovery_dossier_restricted_v2.json` | 23,169 | `adc0b90dddc0aea4c3347cc709fabe6dbc3ea391335965c0ba949503bfcdf1fa` |
| **Gói nén kiểm toán V4 cũ (Audit trail)** | `data/restricted/pilot_batch1_remediation_pack_lead_d_v4.zip` | 24,196 | `782863009b86cf5c051a3c1d3389020e45664966f17d8c223737be89cac9e2ba` |
| **Hồ sơ hạn chế V1 (Audit trail)** | `data/restricted/pilot_batch1_recovery_dossier_restricted.json` | 20,731 | `2e14d95729a06c2315e8f7587d447a3983e497b0adb90eb50c11508c08a16977` |
| **Bảng chi tiết cấp mẫu (ngoài Git)** | `data/restricted/pilot_batch1_sample_level_audit_table.json` | 20,574 | `6395781aeada3b73c72ee7215bd29a167ea5ab639ce48fe3507bde515bbf128f` |
| **Biên bản sự cố Git Exposure** | `docs/INCIDENT_REPORT_GIT_EXPOSURE_AD445A7.md` | 6,204 | `79505d4a503c87a762d0476d71e0360c940af86c654b37e41558991756d18f51` |
| **Tài liệu đặc tả QA công khai (Giữ nguyên byte đã QA)** | `docs/SELECTION_GATE_QA_SPEC_PACK_B.md` | 8,496 | `ca9a5af3d8e0abadf26eb4a19374b0d97820cf2dffb30ca2d80d457be9067d09` |
| **Bản đính chính Errata V4.2 & Tờ trình Quyết định** | `docs/SELECTION_GATE_ERRATA_V4_2_LEAD_D.md` | Văn bản công khai | Tham chiếu commit V4.2 |
| **Exclusion Registry V1.1.0** | `data/exclusion_registry.json` | 107,484 | `71c8d8735cdfb63d146b30002789004c490090c1280f6731390ed9527457806d` |
| **Báo cáo kiểm toán Exclusion Audit** | `data/source_audit/clean_calibration_exclusion_audit_report.json` | 7,652 | `a2f2d5bf157a2597cdd234c9d8162008e415615770a591b5034861277a343fe2` |
| **Clean Calibration Manifest** | `configs/calibration_clean_a_manifest.json` | 7,365 | `e89863c1f39fd19254bf792eb9c0688c6e885cf1981c96ae9e5318ab885a2474` |
| **Module loại trừ (Đã sửa import & fail-closed)** | `src/phishing/data/exclusion.py` | 19,448 | `5cc8a445b20bb251df523e258f957215134cb804859de3855dff49db856aa041` |
| **Cổng chọn mẫu Selection Gate (Đã sửa)** | `src/phishing/data/selection_gate.py` | 20,308 | `eb3f36a9db9a5dbba62bd1643b68cf4c678d99e9a553132354e792de8753a6a1` |
| **Runner chọn mẫu thực tế** | `scripts/data/run_main_selection.py` | 4,381 | `cc1d45d0801d846454347b877ba95907a1bb1537ba33954876b53ddd87c44fb2` |
| **Bộ kiểm thử 40 ca** | `tests/test_pilot_batch1_exclusion.py` | 43,114 | `a0dab832654bf6ab76614f0098b3b0e7affc710d8e69695d167dfffcff9e75f5` |
| **Log 40 tests (Môi trường Cục bộ C)** | `test_report_pilot_batch1_exclusion_v4_1.log` | 5,917 | `2db9f8eab72940d66c197a155595d71de9540d3ada3e297c1f546ade6cf54ed4` |
| **Log 38 passed / 2 skipped (Tự kiểm mô phỏng)** | `test_report_clean_checkout_simulation_v4_1.log` | 5,919 | `ded94b99f1b1718eac6d9eaf01065db16b31ddbd3db87fd00185fa687622b022` |
| **Log 147 tests (7 test suites)** | `test_report_7_suites_v4_1.log` | 21,476 | `81b62c32da70745b983e5bffad5fc36d8a5557f1c7939a06dbd49b13132c3382` |

* **Ghi chú đính chính bảng kê:** Tại bảng kê thông báo bàn giao trước, C ghi nhầm `docs/SELECTION_GATE_QA_SPEC_PACK_B.md` dài 8.432 byte / hash `3c59a3fe...` do đo đạc trên bản nháp trước khi commit bổ sung dòng ghi chú cuối. Tệp vật lý thực tế tại commit `2eddf41` là đúng **8.496 byte** với SHA-256 **`ca9a5af3d8e0abadf26eb4a19374b0d97820cf2dffb30ca2d80d457be9067d09`**, khớp hoàn toàn với bản QA Lead B đã kiểm định độc lập và ký `PASS`. Tệp đặc tả này được giữ nguyên byte và hash tại commit `2eddf41` để bảo toàn giá trị thẩm định của B.

---

## 8. Danh mục Các Vấn đề Còn Mở & Hai Dự thảo Quyết định Trình Lead D

Thành viên C tiếp tục duy trì khuyến nghị quản trị: **`NO-GO` đối với việc rút mẫu và mở Main Annotation Đợt 1 ngay lúc này**. Hệ thống giữ nguyên trạng thái khóa an toàn (`main_annotation_status="LOCKED"`, `training_blocked=true`, `official_test_used=false`).

Để từng bước tháo gỡ điểm nghẽn có kiểm soát, C kính trình Lead D xem xét và ban hành **hai quyết định riêng biệt**:

---

### DỰ THẢO QUYẾT ĐỊNH 1: CHO PHÉP TẢI VÀ KIỂM NGUỒN `train-001.parquet` (BƯỚC 1)

1. **Thông số kỹ thuật nguồn xác lập từ manifest (`configs/source_manifest.json`):**
   * **Nguồn dữ liệu:** `phreshphish`
   * **Git Revision khóa:** `eabec4b7a66324b79cc8a0ad856d1731dc26fe1a`
   * **Tên tệp shard:** `train-001.parquet`
   * **Dung lượng tệp dự kiến:** `322,018,201 bytes`
   * **Mã băm SHA-256 Git-LFS trong manifest:** `260cb9c93299f6b244d48321fe115523159770f4e73446b382473628c6e81d74`
   * **Cửa sổ ngày được phép lấy mẫu (Temporal Split):** `2024-10-01` đến `2025-09-08` (áp dụng theo ngưỡng temporal split; loại bỏ các mẫu ngoài cửa sổ này).

2. **Phạm vi kiểm tra kỹ thuật sau khi được Lead D cho phép:**
   * **Bước 1.1:** Tải tệp vật lý về đĩa cục bộ, đo trực tiếp mã băm SHA-256 trên byte thật của tệp Parquet và đối chiếu với giá trị Git-LFS pointer dự kiến (`260cb9c9...`). Cập nhật `locally_verified_sha256` trong manifest.
   * **Bước 1.2:** Chạy toàn bộ bản ghi của shard qua Cổng chọn mẫu Selection Gate (Gates 0–4):
     * *Gate 0 (Kiểm tra cách ly Shard):* Xác nhận shard không phải `train-000` hay `train-055`.
     * *Gate 1 (Domain/Brand Regex Matcher):* Nhận diện ứng viên thuộc 14 tổ chức mục tiêu.
     * *Gate 2 (ExclusionRegistry Anti-Leakage):* Đối soát 6 lớp mã băm đối với các cam kết `EXCL-PILOT-01` (20 mẫu) và `EXCL-CALIB-01` (32 mẫu).
     * *Gate 3 (Dedup & Template Diversity):* Lọc tương đồng SimHash / DOM Tag và đa dạng hóa tên miền (tối đa 1 mẫu/eTLD+1).
     * *Gate 4 (Cân bằng phân loại phụ):* Kiểm soát hạn ngạch tổ chức.

3. **Điều kiện dừng an toàn bắt buộc (Fail-Closed Halt Criteria):**
   * DỪNG NGAY LẬP TỨC nếu SHA-256 byte thực tế trên đĩa sai lệch so với giá trị Git-LFS pointer (`260cb9c9...`).
   * DỪNG NGAY LẬP TỨC nếu phát sinh bất kỳ ngoại lệ dữ liệu định dạng (`ValueError`) hoặc ngoại lệ hệ thống (`RuntimeError`) trong quá trình chạy qua Gate 0–4.
   * DỪNG NGAY LẬP TỨC nếu số lượng ứng viên hợp lệ sau Gate 0–4 không đạt chỉ tiêu tối thiểu 100 mẫu.
   * Khi dừng, C lập tức niêm phong tệp log, báo cáo Lead D, và không xuất bất kỳ danh sách rút mẫu nào.

4. **Sản phẩm bàn giao sau bước kiểm nguồn:** Báo cáo số đếm tổng hợp (tổng số hàng, số mẫu qua từng cổng, số mẫu bị loại theo từng lý do, các sai lệch phát hiện và phần còn chưa xác minh).

---

### DỰ THẢO QUYẾT ĐỊNH 2: XỬ LÝ SỰ CỐ GIT CỦA PILOT (COMMIT `ad445a7`) & NGHIỆM THU CHUỖI BẰNG CHỨNG PILOT 20

1. **Phương án C khuyến nghị:** **Phương án A (Forward-Fix & Administrative Retirement)**.
2. **Cơ sở lựa chọn:**
   * Giữ nguyên cây commit lịch sử để bảo toàn audit trail minh bạch, phục vụ đánh giá khoa học và kiểm toán độc lập.
   * Tuyệt đối không force-push hoặc viết lại lịch sử Git trên nhánh cộng tác khi chưa có lệnh điều phối khẩn cấp từ Lead D.
3. **Nghiệm thu chuỗi bằng chứng xác minh Pilot 20:**
   * Xác nhận bản phản hồi Rows API gốc tại `data/source_audit/phreshphish/pilot_20_rows.json` (7,186,229 bytes | SHA-256 `738ea69b920cb3037d7e9da38590024d8faa5f34c2eca6c760cb34690f2f190f`) khớp với hash lịch sử công bố tại `bc674e9` và `a62105a`.
   * Xác nhận kết quả đối chiếu Parquet tại revision khóa `eabec4b7a66324b79cc8a0ad856d1731dc26fe1a`: 20/20 cặp URL/HTML khớp chính xác tại `train-000` (`row_offset: 0..19`), khớp 0/20 tại `train-055`.
   * Xác nhận giữ nguyên `rows_api_revision_pinned = false` theo đúng phương thức thu thập lịch sử.
   * Phê duyệt hồ sơ hạn chế V3 (`data/restricted/pilot_batch1_recovery_dossier_restricted_v3.json` - SHA-256: `0d817d0b1eca177f22794f21c305db542194d6e7c9f9dc418bd26e5d8a64c5a3`).
4. **Cách thức ghi nhận và thực thi loại trừ các mẫu đã biết:**
   * Đánh dấu vĩnh viễn 20 mẫu Pilot Lô 1 trong `data/exclusion_registry.json` với mã cam kết `EXCL-PILOT-01`, trỏ tới Dossier V3 với `commitment_sha256 = "0d817d0b1eca177f22794f21c305db542194d6e7c9f9dc418bd26e5d8a64c5a3"`.
   * Toàn bộ 20 mẫu này bị loại trừ vĩnh viễn (retired) khỏi mọi tập dữ liệu huấn luyện, thẩm định và đánh giá (M0–M3).
   * Xác nhận giải trình số đếm: Con số 246 là tổng mục khai báo theo lô (declared batch items); tổng số mẫu duy nhất toàn registry theo phép hợp các cặp hash là **226 mẫu** (do 20 mẫu Pilot 20 nằm hoàn toàn trong Lô 32).
5. **Phạm vi Shard cách ly:** Cách ly vĩnh viễn shard `train-000.parquet` (`QUARANTINED`), cấm mọi hành vi trích xuất từ shard này.
6. **Thừa nhận Rủi ro tồn dư (Residual Risk) & Bảo mật dữ liệu:**
   * Phạm vi kiểm vị trí duy nhất đã hoàn thành trên 2 shard (`train-000` và `train-055`). Cổng 2 (6 lớp mã băm) và Cổng 3 (lọc tương đồng template) sẽ tiếp tục rà soát trên mọi shard mới được cấp phép.
   * Toàn bộ bảng chi tiết cấp mẫu (ID, locator, nhãn nguồn, tên miền) tiếp tục được niêm phong an toàn tại `data/restricted/pilot_batch1_sample_level_audit_table.json` và `data/restricted/pilot_batch1_recovery_dossier_restricted_v3.json`.

---

### B. Cam kết Bất biến của Thành viên C:
* `main_annotation_status = "LOCKED"`
* `training_blocked = true`
* `official_test_used = false`
* **Tuyệt đối chưa tải Parquet để kiểm nguồn, chưa rút 100 mẫu Main, chưa tạo và chưa phát Blind View cho bất kỳ ai trước khi Lead D phê duyệt bằng văn bản.**
