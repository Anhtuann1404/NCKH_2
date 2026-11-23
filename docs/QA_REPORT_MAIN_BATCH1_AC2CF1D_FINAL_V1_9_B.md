# BÁO CÁO QA ĐỘC LẬP CUỐI — MAIN ANNOTATION BATCH 1 (V4.2 REMEDIATION) — THÀNH VIÊN B (V1.9)

- **Mã tài liệu**: `QA_REPORT_MAIN_BATCH1_AC2CF1D_FINAL_V1_9_B`
- **Ngày ban hành**: `2026-11-23`
- **Người thực hiện QA độc lập**: **Phùng Tấn Minh** (**Thành viên B — Annotator B kiêm QA Lead & Nhóm trưởng**)
- **Người thực hiện mã nguồn & hồ sơ**: **Nguyễn Thắng** (**Thành viên C — Data Pipeline & Thư ký**)
- **Người kiểm chứng gói dữ liệu hạn chế thật & điều phối**: **Anh Tuấn** (**Thành viên D — Lead & Trọng tài**)
- **Repository**: `https://github.com/Anhtuann1404/NCKH_2`
- **Nhánh kiểm tra**: `origin/feat/c-main-annotation-batch1`
- **Commit HEAD được kiểm**: **`ac2cf1d82d9a742ec0f5e9af81e0ce116fdfbe3d`** (`chore: update isolation verification report for commit fb48754`)
- **Commit sửa lõi trực tiếp (parent)**: **`fb487540aa6c877553eeb9e0978437642a4173b1`** (`fix(sampling): enforce raw-byte authority in fingerprinting and add hydrated rehearsal v4.2`)
- **Mốc lỗi V4.1 trước khi sửa (giữ nguyên làm audit trail)**: `28462fcece5883a652779976e342d939f7a81e5a` (đã ghi nhận `FAIL / HOLD` tại `docs/QA_REPORT_MAIN_BATCH1_28462FC_HOLD_V1_8_B.md`)
- **Mốc mã nền tảng G1–G7**: `33e8bb6c29c7ee15209ae5847d48aae973a3f536` (đã ghi nhận `PASS` phạm vi mã/fixture `154 passed` tại `docs/QA_REPORT_MAIN_BATCH1_33E8BB6_CONSOLIDATED_V1_6_B.md`)
- **Trạng thái kết luận QA kỹ thuật mã/fixture tại `ac2cf1d82d9a742ec0f5e9af81e0ce116fdfbe3d`**: **`PASS` (ĐẠT TRONG PHẠM VI MÃ NGUỒN, VERIFIER, MIGRATION PROBE VÀ 165 KIỂM THỬ FIXTURE CHỌN LỌC)**
- **Trạng thái các cổng quản trị hiện hành**:
  - `main_annotation_status = "LOCKED"` (Main Annotation Pass 1 chưa mở; chờ quyết định phát hành riêng của Lead D)
  - `training_blocked = true`
  - `official_test_used = false`

> [!IMPORTANT]
> **Ranh giới kết luận QA của Thành viên B**:
> 1. Báo cáo V1.9 này xác nhận **QA kỹ thuật mã nguồn và kiểm thử trên fixture của bản sửa V4.2 tại commit `ac2cf1d82d9a742ec0f5e9af81e0ce116fdfbe3d` đạt (`PASS`)**.
> 2. Để bảo vệ tính mù của Annotator B trước Pass 1 theo Mục 3 `AGENTS.md`, Thành viên B **không nhận và không mở** gói dữ liệu hạn chế thật V4.2 (`MAIN_BATCH1_B5B7DB2_EVIDENCE_FOR_D_V4_2.zip`), không truy cập `data/restricted/`, không đọc mapping A100/B30 thật, sổ cái thật hay seed/salt thật. Các kết quả kiểm chứng trên gói dữ liệu hạn chế thật và diễn tập từ nguồn thô thật được dẫn chiếu rõ là **kết quả kiểm chứng của Lead D** tại gói `MAIN_BATCH1_V4_2_LEAD_D_REVIEW.zip`.
> 3. Kết luận `PASS` kỹ thuật mã/fixture này **không tự động áp dụng Block 2 vào sổ cái hạn chế thật**, **không tự chuyển `approval_status` của manifest thật sang `approved`**, và **không tự mở Main Annotation Pass 1**. Quyền phê duyệt áp dụng sổ cái thật và mở cổng phát hành Pass 1 thuộc quyết định riêng của Lead D.

---

## 1. Xác định nhiệm vụ QA (5 mục theo Mục 1 `AGENTS.md`)

1. **Mục tiêu**:
   - Kiểm chứng độc lập bản sửa V4.2 của Thành viên C trên nhánh `origin/feat/c-main-annotation-batch1` tại commit HEAD `ac2cf1d82d9a742ec0f5e9af81e0ce116fdfbe3d` (và commit sửa lõi `fb487540aa6c877553eeb9e0978437642a4173b1`), xác nhận hai lỗi hồi quy R1 và R2 tại `28462fcece5883a652779976e342d939f7a81e5a` đã được khắc phục trên clean checkout không có `data/restricted/`, không gây hồi quy các chốt chặn G1–G7 (`165 passed` trên 12 tệp test chọn lọc trong repository) và đạt phép kiểm cô lập Git (`verify_git_isolation.py`).
2. **Đầu vào được phép**:
   - Nhánh remote `origin/feat/c-main-annotation-batch1` tại commit `ac2cf1d82d9a742ec0f5e9af81e0ce116fdfbe3d` và parent `fb487540aa6c877553eeb9e0978437642a4173b1`.
   - Gói bằng chứng công khai/trung tính do Lead D bàn giao: `MAIN_BATCH1_V4_2_LEAD_D_REVIEW.zip` (`10.377 bytes`, SHA-256: `5626514cc1b61083879bf4516fdff126dd22946200e44eb9e4cf1b02ec8a03fb`).
   - Toàn bộ fixture tổng hợp trong repository; tuyệt đối không dùng dữ liệu hạn chế ngoài Git (`data/restricted/`).
3. **Đầu ra và tiêu chí đạt**:
   - Tệp báo cáo QA cuối của Thành viên B: `docs/QA_REPORT_MAIN_BATCH1_AC2CF1D_FINAL_V1_9_B.md` và tệp raw log thực thi: `docs/QA_RAW_LOG_MAIN_BATCH1_AC2CF1D_B.txt`.
   - Tiêu chí đạt:
     - Đối chiếu khớp byte và SHA-256 của gói `MAIN_BATCH1_V4_2_LEAD_D_REVIEW.zip` cùng 9 tệp thành phần.
     - Kiểm tra diff mã nguồn giữa `28462fcece5883a652779976e342d939f7a81e5a` và `ac2cf1d82d9a742ec0f5e9af81e0ce116fdfbe3d` xác nhận cơ chế sửa lỗi R1 và R2 đúng thiết kế fail-closed.
     - Chạy độc lập trên clean worktree (`Test-Path data/restricted == False`): 2 probe hồi quy V4.1 đạt (`2 passed`), 12 tệp test chọn lọc trong repository đạt (`165 passed, 0 failed, 0 skipped`), và `scripts/data/verify_git_isolation.py` đạt (`PASS`).
4. **Ranh giới**:
   - Thành viên B chỉ kiểm mã nguồn, script verifier, probe migration, manifest công khai và chạy test trên fixture tổng hợp.
   - Giữ nguyên byte toàn bộ báo cáo QA lịch sử (`V1.0` đến `V1.8`), trong đó `V1.8` giữ trạng thái `FAIL / HOLD` cho commit `28462fcece5883a652779976e342d939f7a81e5a`.
   - Không mở gói dữ liệu hạn chế thật; không ký thay quyết định phê duyệt sổ cái thật hoặc mở Pass 1 của Lead D.
5. **Điều chưa biết / Giới hạn ngoài phạm vi trực tiếp của B**:
   - Thành viên B không trực tiếp chạy `verify_population_fingerprint.py` hay `rehearse_v42_from_raw.py` trên 1.232 mẫu hạn chế thật trong `data/restricted/` vì rào chắn bảo vệ tính mù của Annotator B; phần kiểm chứng này do Lead D thực hiện độc lập và được ghi nhận theo đúng nguồn chứng cứ của Lead D.

---

## 2. Kiểm định gói bằng chứng của Lead D và định danh Commit Git

### 2.1. Kiểm chứng gói `MAIN_BATCH1_V4_2_LEAD_D_REVIEW.zip`

Em đã tính SHA-256 trực tiếp trên byte của gói `MAIN_BATCH1_V4_2_LEAD_D_REVIEW.zip` và đối chiếu toàn bộ 9 tệp thành phần với bảng `SHA256SUMS_D.txt`:

- **Kích thước gói ZIP**: `10.377 bytes`
- **SHA-256 gói ZIP**: `5626514cc1b61083879bf4516fdff126dd22946200e44eb9e4cf1b02ec8a03fb`

| STT | Tệp thành phần trong ZIP | Kích thước (bytes) | SHA-256 tính trực tiếp trên byte | Đối chiếu `SHA256SUMS_D.txt` |
| :-: | :--- | --: | :--- | :-: |
| 1 | `COMMANDS.md` | 1.437 | `7a963823b15f2a8547b4928a7b40b4126d9b2c0fc78aa3c399a163f8a8539561` | Khớp |
| 2 | `REVIEW_MAIN_BATCH1_V4_2_LEAD_D.md` | 6.101 | `0c925c1769fc8a648fc96834d8609b173e56ab25f06c432c0b027116fcdbeb0a` | Khớp |
| 3 | `SHA256SUMS_D.txt` | 737 | `930a43753aaf5e8e8681ca2baa7b9373102e07762bc34fb687d96c7f7413a0e5` | Khớp |
| 4 | `SOURCE_VERIFIED.json` | 455 | `788116daa985287dd7cb4a72e6b9796a64aecef7417ca73e8c0bbf0d07f098ec` | Khớp |
| 5 | `audit_main_v42_metadata.py` | 7.253 | `72b720703efa9236bf695e3320e5ffd2edf7fd1214c4ef5bd0a48a8e8c1b8d16` | Khớp |
| 6 | `main_v42_isolation.log` | 91 | `5703c86b8b3ff5c3f9d6763b6fbb607062bbda7a6ea608c2b35175a5ac2028cc` | Khớp |
| 7 | `main_v42_metadata_summary.json` | 2.618 | `fc622298a1ff45fe6943793bbacc898624cc533e97c663c3809778822f1d6016` | Khớp |
| 8 | `main_v42_selected.log` | 260 | `37043a65f53d2346d8b67818e61b33d7249927724ed5f0e8360d184ef6ae9999` | Khớp |
| 9 | `test_main_v41_fingerprint_integrity.py` | 1.942 | `c28107eb706d3a4a707653b3a7903d2331f51e058f135dd6b7262cf5b931425d` | Khớp |

Đồng thời, tệp `tests/test_main_v41_fingerprint_integrity.py` được commit trong repository tại `ac2cf1d82d9a742ec0f5e9af81e0ce116fdfbe3d` có kích thước `1.942 bytes` và SHA-256 `c28107eb706d3a4a707653b3a7903d2331f51e058f135dd6b7262cf5b931425d`, khớp nguyên byte với probe của Lead D.

### 2.2. Kiểm chứng chuỗi Commit trên nhánh `origin/feat/c-main-annotation-batch1`

- **`28462fcece5883a652779976e342d939f7a81e5a`** (Mốc V4.1 lỗi):
  - Tác giả: Nguyễn Thắng (`Thang1234566`) | Thời điểm: `2026-04-20T09:50:00+07:00`
  - Thông điệp: `feat(qa): integrate B V1.7 addendum, lead D V3/V4 reviews, and population fingerprint v4.1 support`
  - Trạng thái QA: **`FAIL / HOLD`** (bảo lưu tại `docs/QA_REPORT_MAIN_BATCH1_28462FC_HOLD_V1_8_B.md`; lưu ý chuỗi SHA `28462fc48f29bf4244f77c2aa5b214f4eb04c54e` do C từng dẫn chiếu trong tin nhắn cũ không tồn tại trong Git object database).
- **`fb487540aa6c877553eeb9e0978437642a4173b1`** (Commit sửa lõi V4.2):
  - Tác giả: Nguyễn Thắng (`Thang1234566`) | Thời điểm: `2026-04-20T11:37:01+07:00`
  - Thông điệp: `fix(sampling): enforce raw-byte authority in fingerprinting and add hydrated rehearsal v4.2`
  - Thay đổi 13 tệp so với `28462fcece5883a652779976e342d939f7a81e5a`, trong đó sửa lõi `src/phishing/data/main_sampling.py`, thêm `tests/test_main_v41_fingerprint_integrity.py`, thêm script diễn tập `scripts/data/rehearse_v42_from_raw.py`, lưu trữ gói review V4.1 của Lead D và cập nhật đầy đủ `20.658 bytes` cho tệp `docs/QA_ADDENDUM_MAIN_BATCH1_B5B7DB2_MIGRATION_VERIFIER_PENDING_V1_7_B.md` cùng báo cáo V1.8 của B.
- **`ac2cf1d82d9a742ec0f5e9af81e0ce116fdfbe3d`** (HEAD hiện hành được kiểm):
  - Tác giả: Nguyễn Thắng (`Thang1234566`) | Thời điểm: `2026-04-20T11:38:27+07:00`
  - Thông điệp: `chore: update isolation verification report for commit fb48754`
  - Diff giữa `fb487540aa6c877553eeb9e0978437642a4173b1` và `ac2cf1d82d9a742ec0f5e9af81e0ce116fdfbe3d`: chỉ cập nhật duy nhất 1 dòng `total_tracked_files_checked` (`163` $\rightarrow$ `164`) trong `artifacts/isolation_verification_report.json`.

---

## 3. Đánh giá chi tiết từng hạng mục kỹ thuật V4.2 (R1, R2, Rerun Payload & Manifest/Lineage)

### 3.1. Hạng mục R1 — Tính nhất quán giữa Raw HTML/URL và Hash cung cấp kèm (`PASS`)

- **Nguyên nhân lỗi tại V4.1 (`28462fcece5883a652779976e342d939f7a81e5a`)**:
  - Hàm `compute_population_fingerprint` trong `src/phishing/data/main_sampling.py` ưu tiên lấy `c.get("html_sha256")` và `c.get("url_sha256")` trước khi băm nội dung thô `c.get("html")` / `c.get("url")`. Nếu một bản ghi có nội dung raw HTML hoặc raw URL bị thay đổi nhưng vẫn mang trường `html_sha256` / `url_sha256` cũ (stale hash), hàm vẫn trả về cùng `population_fingerprint` cũ.
- **Cơ chế sửa tại V4.2 (`fb487540...` / `ac2cf1d8...`)**:
  - Đối với URL: luôn lấy raw URL (`c.get("url") or c.get("url_raw")`), tính trực tiếp `computed_url_hash = hashlib.sha256(url_raw.encode("utf-8")).hexdigest()` và `computed_norm = normalize_url(url_raw)`. Nếu bản ghi có truyền kèm `url_sha256` hoặc `url_normalized` mà lệch với giá trị tính từ raw URL, hàm lập tức ném `ValueError("Dữ liệu mâu thuẫn...")`.
  - Đối với HTML: khi bản ghi có trường `"html"` (khác `None`), luôn tính trực tiếp `computed_html_hash = hashlib.sha256(html_content.encode("utf-8")).hexdigest()`. Nếu bản ghi có truyền kèm `html_sha256` mà khác `computed_html_hash`, hàm lập tức ném `ValueError("Dữ liệu mâu thuẫn: sample ... có html_sha256 cung cấp sẵn khác với băm thực tế của raw HTML.")`.
- **Kết quả kiểm chứng độc lập trên fixture**:
  - Probe `tests/test_main_v41_fingerprint_integrity.py::test_changed_raw_html_cannot_hide_behind_stale_supplied_hash`: **`PASSED`**.

### 3.2. Hạng mục R2 — Chặn Rerun từ Metadata-Only làm rỗng Blind View (`PASS`)

- **Nguyên nhân lỗi tại V4.1 (`28462fcece5883a652779976e342d939f7a81e5a`)**:
  - Khi gọi `run_main_batch1_sampling` với đầu vào chỉ có metadata (`url`, `url_sha256`, `html_sha256` nhưng thiếu `"html"`), V4.1 dùng `html_sha256` để tính fingerprint nên vượt qua chốt `prior_pop_hash == pop_hash`, sau đó nhánh rerun truyền `c.get("html", "")` vào `project_blind_view()` khiến toàn bộ 100 mẫu A và 30 mẫu B bị ghi đè thành `page_text == ""` và `sample_content_hash` bị đổi.
- **Cơ chế sửa tại V4.2 (`fb487540...` / `ac2cf1d8...`)**:
  - Khi bản ghi không có trường `"html"` (hoặc `"html"` là `None`), `compute_population_fingerprint` không tin cậy trường `html_sha256` đi kèm mà băm chuỗi rỗng `hashlib.sha256(b"").hexdigest()`. Do đó, một tập đầu vào metadata-only sẽ có `pop_hash` khác hẳn `prior_pop_hash` của lot đã phát hành từ nguồn thô (`html` đầy đủ).
  - Khi chạy `run_main_batch1_sampling` trên lot đã tồn tại với đầu vào metadata-only, chốt kiểm tra `if prior_pop_hash != pop_hash:` kích hoạt ngay lập tức và ném `ValueError("TỪ CHỐI RERUN LOT ...: Quần thể đầu vào đã thay đổi...")` trước khi chạm tới bước tạo Blind View.
- **Kết quả kiểm chứng độc lập trên fixture**:
  - Probe `tests/test_main_v41_fingerprint_integrity.py::test_metadata_only_rerun_cannot_silently_replace_views_with_empty_text`: **`PASSED`**.

### 3.3. Hạng mục Bảo toàn Rerun Payload và Chống nhân đôi Ledger Block khi Rerun hợp lệ từ Raw-Hydrated Input (`PASS`)

- **Kiểm chứng trên fixture (`tests/test_main_annotation_batch1.py`)**:
  - Khi rerun cùng `lot_id` trên tập đầu vào có đầy đủ raw HTML/URL hợp lệ khớp `prior_pop_hash`, sampler khôi phục đúng 100 mẫu Lô A và 30 mẫu Tập B theo đúng thứ tự phát hành đã ghi trong sổ cái, giữ nguyên `page_text`, `structure_summary`, `sample_content_hash` của từng mẫu và giữ nguyên số block trong sổ cái (không append block trùng lặp).
- **Đối chiếu với kết quả diễn tập trên nguồn thô thật do Lead D kiểm chứng** (theo `REVIEW_MAIN_BATCH1_V4_2_LEAD_D.md` và `main_v42_metadata_summary.json` trong gói của Lead D):
  - Lead D đã kiểm chứng độc lập báo cáo diễn tập từ nguồn thô thật (`raw_rehearsal_v42_report.json`): nạp đủ 1.232 mẫu từ nguồn thô với `hydrated_html_count = 1232`, `empty_html_count = 0`, `first_run_nonempty_text_A = 100`, `first_run_nonempty_text_B = 30`, `rerun_identical_views_A = true`, `rerun_identical_views_B = true`, `ledger_blocks_after_first = 2`, `ledger_blocks_after_rerun = 2`, và `metadata_only_rerun_rejected = true`. (Ghi chú ranh giới: Đây là kết quả do Lead D kiểm chứng trên dữ liệu hạn chế thật; Thành viên B ghi nhận từ báo cáo của Lead D, không tự nhận đã mở gói hạn chế thật).

### 3.4. Hạng mục Manifest công khai, Lineage và script Verifier (`PASS`)

- Kiểm tra `artifacts/main_batch1_release_manifest.json` trên commit `ac2cf1d82d9a742ec0f5e9af81e0ce116fdfbe3d`:
  - `approval_status`: `"pending_lead_d"`
  - `main_annotation_status`: `"LOCKED"`
  - `training_blocked`: `true`
  - `official_test_used`: `false`
  - Không chứa đường dẫn tuyệt đối máy cá nhân, không lộ danh sách `sample_id` A100/B30, mapping hay seed/salt hạn chế.
- Kiểm tra `scripts/data/verify_population_fingerprint.py`:
  - Đã sử dụng trực tiếp hàm `compute_population_fingerprint` đã vá tại `src/phishing/data/main_sampling.py` (nghiêm cấm raw HTML/URL mâu thuẫn với hash đi kèm) và kiểm tra đối chiếu từng trường `url_sha256`, `html_sha256`, `url_normalized` trên toàn bộ bản ghi.

---

## 4. Kết quả thực thi kiểm thử độc lập trên Clean Worktree (`ac2cf1d82d9a742ec0f5e9af81e0ce116fdfbe3d`)

- **Môi trường thực thi của Thành viên B**:
  - Hệ điều hành: Windows (`win32`)
  - Python: `Python 3.14.2`
  - Pytest: `pytest-9.1.1`, `pluggy-1.6.0`, `anyio-4.14.2`
  - Clean Worktree tách biệt: `D:\UED\NCKH2\scratch\ac2cf1d_wt` tại commit `ac2cf1d82d9a742ec0f5e9af81e0ce116fdfbe3d`
  - Kiểm tra sự vắng mặt của dữ liệu hạn chế: `Test-Path data/restricted` $\rightarrow$ **`False`**
  - Tệp log kết quả nguyên bản: `docs/QA_RAW_LOG_MAIN_BATCH1_AC2CF1D_B.txt` (`5.823 bytes`, SHA-256: `bbfc3d991c000f2c99a56ba74968403b7ec536535e98a4799bf55f13ca74a2e4`).

### 4.1. Chạy riêng bộ Probe hồi quy V4.1 (`tests/test_main_v41_fingerprint_integrity.py`)

- **Lệnh thực thi**:
  ```powershell
  $env:PYTHONPATH=".;src"; python -m pytest tests/test_main_v41_fingerprint_integrity.py -v
  ```
- **Kết quả**: **`2 passed, 0 failed, 0 skipped, 0 deselected` trong `0.63s`**.
  - `tests/test_main_v41_fingerprint_integrity.py::test_changed_raw_html_cannot_hide_behind_stale_supplied_hash`: **`PASSED`**
  - `tests/test_main_v41_fingerprint_integrity.py::test_metadata_only_rerun_cannot_silently_replace_views_with_empty_text`: **`PASSED`**

### 4.2. Chạy toàn bộ 12 tệp kiểm thử chọn lọc trong Repository (G1–G7 + Migration + Isolation + Manifest Preflight + V4.1 Probes)

- **Lệnh thực thi**:
  ```powershell
  $env:PYTHONPATH=".;src"; python -m pytest tests/test_main_annotation_batch1.py tests/test_blind_view.py tests/test_annotate_cli_timer_pause.py tests/test_ledger_migration_proposal.py tests/test_isolation_scanner_regression.py tests/test_main_batch1_manifest_preflight.py tests/test_main_v41_fingerprint_integrity.py artifacts/lead_d_review_8fc845d/test_main_8fc_additional_guards.py artifacts/lead_d_review_6c26d74/test_main_6c26_release_boundaries.py artifacts/lead_d_review_599c7d9/test_main_599_followup.py artifacts/lead_d_review_da3a78d/test_main_da3_intake_history.py artifacts/lead_d_review_a12f90b/test_main_a12_approval_and_sop.py -q
  ```
- **Kết quả**: **`165 passed, 0 failed, 0 skipped, 0 deselected` trong `28.06s`**.
- **Giải trình đối chiếu số lượng test giữa B (`165 passed`) và Lead D (`167 passed`)**:
  - 12 tệp test chọn lọc nằm trong repository tại commit `ac2cf1d82d9a742ec0f5e9af81e0ce116fdfbe3d` gồm đúng **165 test** (11 tệp tại mốc `28462fc` = 163 test + tệp mới `tests/test_main_v41_fingerprint_integrity.py` = 2 test; lưu ý tệp `artifacts/lead_d_review_v4_1/test_main_v41_fingerprint_integrity.py` trong repo là bản sao trùng tên và trùng nội dung của `tests/test_main_v41_fingerprint_integrity.py`).
  - Trong `COMMANDS.md` của gói `MAIN_BATCH1_V4_2_LEAD_D_REVIEW.zip`, lệnh chạy của Lead D đạt `167 passed` vì có chạy kèm thêm 1 tệp ngoài repository trên máy Lead D là `/private/tmp/test_main_v3_pure_fixture_migration.py` (gồm 2 pure-fixture test). Sự chênh lệch đúng 2 test này khớp chính xác với lưu ý của Lead D trong yêu cầu giao việc.

### 4.3. Chạy kiểm tra cô lập Git (`scripts/data/verify_git_isolation.py`)

- **Lệnh thực thi**:
  ```powershell
  $env:PYTHONPATH=".;src"; python scripts/data/verify_git_isolation.py
  ```
- **Kết quả**: **`Git Isolation Status: PASS`** (`total_tracked_files_checked: 164`, `violations_count: 0`, `status: "PASS"`).

---

## 5. Bảng tổng hợp phân định phạm vi kiểm chứng (B trực tiếp kiểm / D đã kiểm / Việc quản trị còn mở)

| Hạng mục kiểm tra | Phân loại nguồn kiểm chứng | Trạng thái | Bằng chứng xác thực |
| :--- | :--- | :-: | :--- |
| **R1**: Chặn raw HTML/URL thay đổi ẩn sau `html_sha256`/`url_sha256` cũ | **Thành viên B trực tiếp kiểm** (trên mã & fixture) | **`PASS`** | `src/phishing/data/main_sampling.py`; `test_changed_raw_html_cannot_hide_behind_stale_supplied_hash` (`PASSED`) |
| **R2**: Chặn metadata-only rerun làm rỗng `page_text` của Blind View A100/B30 | **Thành viên B trực tiếp kiểm** (trên mã & fixture) | **`PASS`** | `src/phishing/data/main_sampling.py`; `test_metadata_only_rerun_cannot_silently_replace_views_with_empty_text` (`PASSED`) |
| **Hồi quy G1–G7, Migration Probe, Isolation Scanner & Manifest Preflight** (12 tệp test trong repo) | **Thành viên B trực tiếp kiểm** (trên clean worktree không có `data/restricted/`) | **`PASS`** | **`165 passed, 0 failed, 0 skipped`** trong `28.06s` (`docs/QA_RAW_LOG_MAIN_BATCH1_AC2CF1D_B.txt`) |
| **Cô lập Git (`verify_git_isolation.py`) & Cờ khóa Manifest công khai** | **Thành viên B trực tiếp kiểm** (trên commit `ac2cf1d8...`) | **`PASS`** | `Git Isolation Status: PASS` (164 tracked files, 0 vi phạm); `approval_status="pending_lead_d"` |
| **Kiểm chứng gói dữ liệu hạn chế thật V4.2 & Diễn tập từ nguồn thô thật (1.232 mẫu)** | **Lead D đã kiểm độc lập** (B không mở để bảo toàn tính mù Annotator B) | **Đã được Lead D xác nhận trong gói review** | `REVIEW_MAIN_BATCH1_V4_2_LEAD_D.md` & `main_v42_metadata_summary.json` trong `MAIN_BATCH1_V4_2_LEAD_D_REVIEW.zip` |
| **Áp dụng Block 2 vào sổ cái hạn chế thật (`allocation_ledger.jsonl`)** | **Quyết định quản trị của Lead D** | **`PENDING_LEAD_D`** | Chờ quyết định phê duyệt riêng của Lead D sau khi nhận báo cáo QA V1.9 này |
| **Chuyển `approval_status` sang `approved` và mở cổng Main Annotation Pass 1** | **Quyết định quản trị của Lead D** | **`LOCKED` / `PENDING_LEAD_D`** | `main_annotation_status="LOCKED"`, `training_blocked=true`, `official_test_used=false` |

---

## 6. Danh mục tệp hồ sơ QA của Thành viên B bàn giao để lưu trữ nguyên byte

Thành viên C đã khôi phục đầy đủ `20.658 bytes` cho tệp `docs/QA_ADDENDUM_MAIN_BATCH1_B5B7DB2_MIGRATION_VERIFIER_PENDING_V1_7_B.md` và lưu trữ nguyên byte báo cáo `V1.8` (`docs/QA_REPORT_MAIN_BATCH1_28462FC_HOLD_V1_8_B.md`) trên nhánh `origin/feat/c-main-annotation-batch1` tại commit `ac2cf1d82d9a742ec0f5e9af81e0ce116fdfbe3d`.

Sau lượt QA cuối V1.9 này, danh mục hồ sơ QA của Thành viên B (bao gồm 2 tệp mới của đợt V1.9 và các tệp lịch sử giữ nguyên byte) như sau:

| Tệp hồ sơ QA của Thành viên B | Vai trò / Phạm vi | Kích thước (bytes) | SHA-256 trực tiếp trên byte |
| :--- | :--- | --: | :--- |
| `docs/QA_REPORT_MAIN_BATCH1_AC2CF1D_FINAL_V1_9_B.md` | **Báo cáo QA cuối V1.9 (`PASS` kỹ thuật mã/fixture tại `ac2cf1d8...`)** | *(xem bảng bàn giao bên ngoài tệp)* | *(tính trực tiếp trên byte tệp sau khi ghi)* |
| `docs/QA_RAW_LOG_MAIN_BATCH1_AC2CF1D_B.txt` | **Raw log thực thi 165 test & Git isolation tại `ac2cf1d8...`** | `5.823` | `bbfc3d991c000f2c99a56ba74968403b7ec536535e98a4799bf55f13ca74a2e4` |
| `docs/QA_REPORT_MAIN_BATCH1_28462FC_HOLD_V1_8_B.md` | Báo cáo lịch sử V1.8 (`FAIL / HOLD` tại `28462fce...` — đã có trong repo) | `27.759` | `bbdb9d20e94e401375f786cc9d1443b575088390b225b9c9d0f7bcd4fda82192` |
| `docs/QA_ADDENDUM_MAIN_BATCH1_B5B7DB2_MIGRATION_VERIFIER_PENDING_V1_7_B.md` | Phụ lục lịch sử V1.7 (`b5b7db2` — đã khôi phục đủ byte trong repo) | `20.658` | `3fecd1ef8f7cffd4a537ea45d4285c823eb0f557c9bd36f213779c0794e15007` |
| `docs/QA_REPORT_MAIN_BATCH1_33E8BB6_CONSOLIDATED_V1_6_B.md` | Báo cáo QA gộp V1.6 (`PASS` 154 test tại `33e8bb6c...` — đã có trong repo) | `37.162` | `bfeb73d97db47fdb6741ce47849254d4f3a9483120bd533a3cb0f357f8a41e09` |
| `docs/QA_RAW_LOG_MAIN_BATCH1_33E8BB6_B.txt` | Raw log thực thi 154 test tại `33e8bb6c...` (đã có trong repo) | `10.920` | `29b452ff6b2debfd2826d3ac3f15678a7f07aff3b45012e53ff3462c17c30ee7` |

---

## 7. Văn bản chứng thực QA độc lập của Thành viên B (QA Lead)

Tôi, **Phùng Tấn Minh** (**Thành viên B — Annotator B kiêm QA Lead & Nhóm trưởng**), chứng thực:

1. Đã kiểm tra độc lập trên clean worktree tách biệt tại đúng commit HEAD **`ac2cf1d82d9a742ec0f5e9af81e0ce116fdfbe3d`** (và commit sửa lõi **`fb487540aa6c877553eeb9e0978437642a4173b1`**) trên nhánh `origin/feat/c-main-annotation-batch1`, hoàn toàn không sử dụng thư mục `data/restricted/` và không tiếp xúc với bất kỳ dữ liệu hạn chế thật nào của Main Batch 1.
2. Xác nhận **hai lỗi hồi quy R1 và R2 tại `28462fcece5883a652779976e342d939f7a81e5a` đã được sửa đạt yêu cầu kỹ thuật**:
   - `compute_population_fingerprint` băm trực tiếp từ raw HTML và raw URL khi hiện diện, từ chối mọi bản ghi có `html_sha256`, `url_sha256` hoặc `url_normalized` mâu thuẫn với dữ liệu thô (`R1: PASS`).
   - Đầu vào metadata-only (thiếu `"html"`) tạo fingerprint khác với lot đã phát hành từ nguồn thô và bị `run_main_batch1_sampling` từ chối ngay ở bước kiểm tra quần thể, ngăn chặn việc ghi đè Blind View thành `page_text` rỗng (`R2: PASS`).
   - Toàn bộ 12 tệp kiểm thử chọn lọc trong repository đạt **`165 passed, 0 failed, 0 skipped`** và phép kiểm cô lập Git `scripts/data/verify_git_isolation.py` đạt **`PASS`**.
3. Kết luận QA độc lập của Thành viên B: **`PASS` đối với phạm vi kỹ thuật mã nguồn, script verifier, probe migration và bộ 165 kiểm thử fixture tại commit `ac2cf1d82d9a742ec0f5e9af81e0ce116fdfbe3d`**.
4. Các cổng quản trị `main_annotation_status="LOCKED"`, `training_blocked=true`, `official_test_used=false` vẫn giữ nguyên trạng thái khóa, chờ quyết định phê duyệt áp dụng sổ cái thật và mở cổng phát hành Pass 1 từ **Lead D (Anh Tuấn)**.
