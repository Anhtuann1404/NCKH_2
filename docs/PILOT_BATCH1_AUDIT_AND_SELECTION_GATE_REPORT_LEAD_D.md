# BÁO CÁO KIỂM TOÁN TỔNG HỢP 20 MẪU PILOT (EXCL-PILOT-01), CỔNG CHỌN MẪU MAIN ĐỢT 1 & XỬ LÝ SỰ CỐ LỊCH SỬ COMMIT (BẢN V3)

**Kính gửi:** Lead D (Anh Tuấn)  
**Người thực hiện:** Thành viên C (Data Pipeline & Thư ký Kiểm toán)  
**Ngày cập nhật:** 15/11/2026 (Bản sửa đổi V3 sau phản biện Lead D và QA Errata v1.1 của B)  
**Chế độ thực thi:** Duo Mode (Antigravity & DeepSeek Reason Architecture Review)  
**Trạng thái Quản trị:** `main_annotation_status="LOCKED"`, `training_blocked=true`, `official_test_used=false`

---

## 1. Báo cáo Sự cố Tiếp xúc Dữ liệu Cấp Mẫu trên Lịch sử Git (Commit `ad445a7`)

Biên bản sự cố chi tiết đã được lập và ban hành độc lập tại [`docs/INCIDENT_REPORT_GIT_EXPOSURE_AD445A7.md`](file:///d:/nguyen%20thang/NCKH/NCKH_2/docs/INCIDENT_REPORT_GIT_EXPOSURE_AD445A7.md).

* **Tóm tắt sự cố:** Trong commit `ad445a7`, bảng đối soát chi tiết cấp mẫu (Entry ID, locator `train-000:0..19`, nhãn nguồn, ngày và tên miền) đã vô tình xuất hiện trên Git.
* **Phạm vi tiếp xúc:** **Chưa xác minh (Unverified exposure scope)**. Do không có access/traffic logs từ máy chủ GitHub, Thành viên C tuyệt đối không đưa ra tuyên bố "0 lượt tiếp xúc" hay "chưa có người xem". Dữ liệu trong commit `ad445a7` vẫn tồn tại trên lịch sử remote repository. C không tuyên bố đã xóa sạch lịch sử Git.
* **Biện pháp khắc phục đã thực hiện:**
  1. Toàn bộ bảng cấp mẫu 20 dòng đã được chuyển vào lưu trữ hạn chế ngoài Git:  
     `data/restricted/pilot_batch1_sample_level_audit_table.json` (21,023 bytes | SHA-256: `29d107535d185c3369e615f99a63d9190a485b47f01a3bc7743cf46c802701bc`).
  2. Báo cáo Git và gói QA cho B chỉ chứa số liệu tổng hợp; đã xóa toàn bộ tên miền fixture thật trong bài test `test_pilot_batch1_exclusion.py`.
  3. C giữ nguyên kỷ luật kỹ thuật: **Không tự ý force-push hoặc viết lại lịch sử Git**, bảo toàn vết kiểm toán để Lead D xem xét.
* **Hai phương án quản trị lịch sử trình Lead D:**
  * **Phương án A (Forward-Fix & Administrative Retirement - Khuyến nghị):** Giữ nguyên cây commit lịch sử; đánh dấu 20 mẫu này là đã bị phơi nhiễm locator trong lịch sử nội bộ và **loại trừ vĩnh viễn (retired)** khỏi toàn bộ quá trình phát triển, huấn luyện và kiểm thử mô hình (M0–M3). Shard `train-000` được cách ly vĩnh viễn. Phương án này bảo toàn tính minh bạch và audit trail.
  * **Phương án B (Git History Rewrite via git-filter-repo):** Dùng `git-filter-repo` để xóa vĩnh viễn commit `ad445a7` khỏi GitHub và yêu cầu toàn bộ nhóm clone lại repository. Phương án này chỉ thực hiện khi có lệnh điều phối trực tiếp từ Lead D.

---

## 2. Chuỗi Bằng chứng 20 Mẫu Pilot Lô 1 & Định nghĩa Đếm Nhóm Miền

### A. Hạ cấp khoa học trung thực về chuỗi bằng chứng Pilot gốc:
* C xác nhận trong kho lưu trữ không có tệp raw HTTP response body dump nguyên byte từ các cuộc gọi Rows API trước đây.
* Do đó, C chính thức giữ nguyên kết luận đính chính: **Chưa chứng minh được "20/20 Pilot lịch sử khớp byte"**.
  * Các mã băm tính từ `train-000.parquet` tại Git revision `eabec4b7a66324b79cc8a0ad856d1731dc26fe1a` là bằng chứng xác thực về các bản ghi thuộc revision đã khóa đó.
  * Các số liệu trong `pilot_summary.json` (5,344 bytes | SHA-256: `3889bf2f...`) chỉ là bằng chứng đối chiếu cấu trúc tóm tắt.

### B. Phát hành Hồ sơ Hạn chế V2 (Lineage & Audit Trail):
Để phản ánh chính xác giới hạn khoa học trên, C đã tạo và niêm phong phiên bản hồ sơ mới:
* **Tệp mới (V2):** `data/restricted/pilot_batch1_recovery_dossier_restricted_v2.json`
  * *Dung lượng:* `23,169 bytes`
  * *Mã băm SHA-256:* `adc0b90dddc0aea4c3347cc709fabe6dbc3ea391335965c0ba949503bfcdf1fa`
  * *Trạng thái định danh nội dung:* Đã chuyển thành `"content_identity_verified": false`, `"content_identity_status": "reconstructed_at_pinned_revision_unverified_historical_byte"`.
* **Tệp cũ (V1 - Bảo lưu làm audit trail):** `data/restricted/pilot_batch1_recovery_dossier_restricted.json` (21,191 bytes | SHA-256: `7ab0d5cb637eb351eb4de39f5f9635c0f22cfb9c3a477fa197df59da28ad4d27`).

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

## 3. Hoàn thiện Hệ thống 5 Cổng Chọn Mẫu (Selection Gates V3)

### Cổng 0: Tính toàn vẹn Shard & Nguồn (Source & Shard Integrity)
* Bắt buộc `source_id == "phreshphish"`, `revision == "eabec4b7a66324b79cc8a0ad856d1731dc26fe1a"`. Chặn đứng tuyệt đối `PhishVN`.
* Cách ly vĩnh viễn shard `train-000` và `train-055` trên cả chuỗi định danh và đường dẫn tệp thực tế.
* Đọc luồng byte thực tế theo chunk 64KB để tính toán SHA-256 và đối soát với `configs/source_manifest.json` (mục `files`). Tuyệt đối không nhận hash caller-provided.

### Cổng 1: Đồng bộ Cửa sổ Ngày V3.5 & Kiểm định Regex Nghiêm ngặt
* Đồng bộ cửa sổ chọn mẫu theo Kế hoạch V3.5: **`2024-10-01` đến `2025-09-08`**.
* **Bỏ hoàn toàn việc cắt chuỗi `[:10]`**: Sử dụng regex bắt buộc `^\d{4}-\d{2}-\d{2}$` và kiểm tra `datetime.strptime`. Từ chối mọi chuỗi có hậu tố rác (như `2024-10-01T00:00:00`, `2024-10-01-extra`), chuỗi ngày không hợp lệ hoặc thiếu ngày.
* Kiểm tra URL hợp lệ (`http://` hoặc `https://`), nội dung HTML có độ dài từ 1 đến 2,000,000 ký tự.

### Cổng 2: Cryptographic Anti-Leakage 6 Lớp
* Đã cập nhật `ExclusionRegistry._load_registry()` trong [`src/phishing/data/exclusion.py`](file:///d:/nguyen%20thang/NCKH/NCKH_2/src/phishing/data/exclusion.py) để nạp đầy đủ 6 lớp vào bộ nhớ:
  1. `raw_url_sha256` / `url_sha256`
  2. `normalized_url_sha256`
  3. `raw_html_sha256` / `html_sha256`
  4. `cleaned_html_sha256`
  5. `bare_group_sha256` (không tiền tố `domain:`)
  6. `prefixed_group_sha256` (có tiền tố `domain:`)
* Đồng bộ `data/exclusion_registry.json` với cam kết ngoài Git:
  * `"status": "sealed_restricted_commitment"`
  * `"restricted_dossier_reference": "data/restricted/pilot_batch1_recovery_dossier_restricted_v2.json"`
  * `"commitment_sha256": "adc0b90dddc0aea4c3347cc709fabe6dbc3ea391335965c0ba949503bfcdf1fa"`
  * Giữ nguyên: `"mapping_status": "unresolved_source_mapping"`, `"rows_api_revision_pinned": false`.
* **Đề xuất bổ sung:** Kiểm tra `view_content_sha256` hoặc kiểm soát locator được xếp vào danh mục đề xuất nâng cấp trình Lead D xem xét, không tính vào hợp đồng 6 lớp hiện hành.

### Cổng 3: Khử trùng lặp, Loại bỏ Thiên lệch Thứ tự Hàng & Template Clones V3.5
* **Loại bỏ Thiên lệch Thứ tự Hàng (Row-Order Bias Elimination):** Toàn bộ ứng viên sau Cổng 2 được sắp xếp theo khóa chính tắc (URL chuẩn hóa + HTML hash), sau đó xáo trộn bằng PRNG seed niêm phong **trước khi** chọn đại diện cho mỗi miền/template. Kết quả chọn mẫu hoàn toàn bất biến đối với bất kỳ hoán vị đầu vào nào của shard.
* Giới hạn tối đa 1 mẫu trên mỗi tên miền (`eTLD+1`).
* **Động cơ Template Similarity Engine (V3.5):** Thay thế so khớp hash skeleton bằng [`TemplateSimilarityEngine`](file:///d:/nguyen%20thang/NCKH/NCKH_2/src/phishing/data/template_similarity.py):
  * Ngưỡng khoảng cách SimHash 64-bit: `max_allowed_simhash_distance = 10`.
  * Ngưỡng tương đồng thẻ DOM Jaccard: `max_allowed_dom_jaccard = 0.85`.
  * Đăng ký tuần tự các ứng viên đã nhận và từ chối các trang clone/near-duplicate sinh từ cùng phishing kit.

### Cổng 4: Quota Fail-Closed & Lấy Mẫu Ngẫu Nhiên Xác Định
* Thực thi Quota cứng: Nếu số lượng ứng viên sau Cổng 3 nhỏ hơn `target_quota` (ví dụ < 100), pipeline **ném lỗi `SelectionGateError` và từ chối xuất dữ liệu**.
* Lấy mẫu ngẫu nhiên xác định (Seeded Random Sampling) theo seed niêm phong. Đề xuất phân tầng theo nhãn nguồn tiếp tục chờ Lead D phê duyệt riêng.
* Kết nối hoàn chỉnh với runner thực tế: [`scripts/data/run_main_selection.py`](file:///d:/nguyen%20thang/NCKH/NCKH_2/scripts/data/run_main_selection.py).

---

## 4. Kết quả Thực nghiệm & Kiểm thử Toàn diện

Bộ kiểm thử [`tests/test_pilot_batch1_exclusion.py`](file:///d:/nguyen%20thang/NCKH/NCKH_2/tests/test_pilot_batch1_exclusion.py) đã được thiết kế lại hoàn toàn với các fixture tự chứa:

1. **Môi trường Clean Checkout (Không có tệp restricted):**
   * Kết quả: **34 passed, 0 failed, 1 skipped** (thời gian: 2.27s).
   * Ca test duy nhất bị skipped là `test_gate2_integration_with_real_restricted_dossier_v2` với lý do kiểm toán rõ ràng: *"Chưa có hồ sơ restricted V2 cục bộ trên clean checkout"*. Không còn hiện tượng 6 tests failed như tại commit `aad2a90`.
2. **Môi trường Đầy đủ Dữ liệu Hạn chế (Môi trường của C):**
   * Kết quả: **35 passed, 0 failed, 0 skipped** (100% passed, thời gian: 2.21s).
3. **Kiểm thử Hồi quy Toàn bộ Repo (5 test suites):**
   * Lệnh: `python -m pytest tests/test_pilot_batch1_exclusion.py tests/test_exclusion_registry.py tests/test_domain_rules.py tests/test_evaluate_kappa.py tests/test_clean_calibration_selection.py`
   * Kết quả: **118 passed, 0 failed** (thời gian: 11.45s).

---

## 5. Bảng Mã Băm Kiểm toán Toàn Diện (Audited Hashes V3)

| Tệp tin | Vị trí / Tình trạng | Kích thước (bytes) | Mã băm SHA-256 |
| :--- | :--- | :--- | :--- |
| **Gói nén kiểm toán V3 gửi D** | `data/restricted/pilot_batch1_remediation_pack_lead_d_v3.zip` | 21,947 | `e0d8bbd29aa504d61333d33d5ca3433cb65cfb1c21527b94aa21945fe7647e97` |
| **Hồ sơ hạn chế V2 (Lineage V1)** | `data/restricted/pilot_batch1_recovery_dossier_restricted_v2.json` | 23,169 | `adc0b90dddc0aea4c3347cc709fabe6dbc3ea391335965c0ba949503bfcdf1fa` |
| **Hồ sơ hạn chế V1 (Audit trail)** | `data/restricted/pilot_batch1_recovery_dossier_restricted.json` | 20,731 | `2e14d95729a06c2315e8f7587d447a3983e497b0adb90eb50c11508c08a16977` |
| **Bảng chi tiết cấp mẫu (ngoài Git)** | `data/restricted/pilot_batch1_sample_level_audit_table.json` | 20,574 | `6395781aeada3b73c72ee7215bd29a167ea5ab639ce48fe3507bde515bbf128f` |
| **Biên bản sự cố Git Exposure** | `docs/INCIDENT_REPORT_GIT_EXPOSURE_AD445A7.md` | 6,204 | `79505d4a503c87a762d0476d71e0360c940af86c654b37e41558991756d18f51` |
| **Exclusion Registry V1.1.0** | `data/exclusion_registry.json` | 107,424 | `f00df7a63fb6659d78fe065ca4c87445ebe071fb448e1d1f337d740317dd57ea` |
| **Bộ nạp loại trừ (Đã nạp 6 lớp)** | `src/phishing/data/exclusion.py` | 18,886 | `23d21f687aaae3cf4adf25d926f98e1a7c6426c8130ea6ffe8cb81389ddbc8a5` |
| **Cổng chọn mẫu Selection Gate** | `src/phishing/data/selection_gate.py` | 19,768 | `73e8b3fe149279dd235f032f5681ae90ad1cbef4a7b30af93e8f5355b7918475` |
| **Runner chọn mẫu thực tế** | `scripts/data/run_main_selection.py` | 4,381 | `cc1d45d0801d846454347b877ba95907a1bb1537ba33954876b53ddd87c44fb2` |
| **Bộ kiểm thử 35 ca** | `tests/test_pilot_batch1_exclusion.py` | 32,889 | `2f609653fde8e07ce8de33256fb613a283b27b7afa6dfd2d130c18b5095a2978` |

---

## 6. Khuyến nghị Quản trị & Yêu cầu Quyết định từ Lead D

Thành viên C tiếp tục duy trì khuyến nghị: **`NO-GO` đối với việc rút mẫu và mở Main Annotation Đợt 1 ngay lúc này**.

**Kính đề nghị Lead D xem xét và chỉ đạo:**
1. **Phê duyệt Phương án xử lý lịch sử Git:** Lựa chọn **Phương án A** (Forward-fix & retire vĩnh viễn 20 mẫu pilot cùng shard `train-000`) hay **Phương án B** (Rewrite history qua `git-filter-repo`).
2. **Ban hành danh mục Shard được phép dùng (Whitelisted Shards):** Phê duyệt danh sách các shard sạch (ví dụ nhóm `train-001`..`train-005`) để C chuẩn bị đối soát byte hash thực tế trước khi đưa vào pipeline.

**Cam kết của C:** Tiếp tục giữ nghiêm ngặt trạng thái:
* `main_annotation_status = "LOCKED"`
* `training_blocked = true`
* `official_test_used = false`
* **Tuyệt đối chưa rút 100 mẫu Main, chưa tạo và chưa phát Blind View cho bất kỳ ai.**
