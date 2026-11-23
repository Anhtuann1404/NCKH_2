# BÁO CÁO QA ĐỘC LẬP & ĐÍNH CHÍNH (ERRATA V1.9.1) — MAIN ANNOTATION BATCH 1 (V4.2 REMEDIATION) — THÀNH VIÊN B

- **Mã tài liệu**: `QA_REPORT_MAIN_BATCH1_V4_2_ERRATA_V1_9_1_B`
- **Ngày ban hành**: `2026-11-23`
- **Người thực hiện QA độc lập & đính chính**: **Phùng Tấn Minh** (**Thành viên B — Annotator B kiêm QA Lead & Nhóm trưởng**)
- **Người thực hiện mã nguồn & hồ sơ**: **Nguyễn Thắng** (**Thành viên C — Data Pipeline & Thư ký**)
- **Người kiểm chứng gói dữ liệu hạn chế thật & điều phối**: **Anh Tuấn** (**Thành viên D — Lead & Trọng tài**)
- **Repository**: `https://github.com/Anhtuann1404/NCKH_2`
- **Nhánh kiểm tra**: `origin/feat/c-main-annotation-batch1`
- **Tài liệu lịch sử được đính chính (giữ nguyên byte làm audit trail)**:
  - Báo cáo V1.9 gốc: `docs/QA_REPORT_MAIN_BATCH1_AC2CF1D_FINAL_V1_9_B.md` (`26.080 bytes` | SHA-256: `baf0e5c39b97f0a1a12a1f17ce6d1f3f42b21dded1e0f68f74c3157e7b061f4c`)
  - Tệp tổng hợp/wrapper log V1.9 gốc: `docs/QA_RAW_LOG_MAIN_BATCH1_AC2CF1D_B.txt` (`5.823 bytes` | SHA-256: `bbfc3d991c000f2c99a56ba74968403b7ec536535e98a4799bf55f13ca74a2e4`)
  - Log đầu ra nguyên bản (raw task log do hệ thống ghi nhận khi chạy 165 test ngày 23/11/2026): `task-4524.log` (công bố tại Mục 5.2 báo cáo này)
- **Các mốc Commit được đối soát trực tiếp bằng lệnh Git**:
  - **Mốc lỗi V4.1 (giữ `FAIL / HOLD` tại báo cáo V1.8)**: `28462fcece5883a652779976e342d939f7a81e5a` (`2026-11-23T00:50:10+07:00`, author `nguyenthang1901`)
  - **Commit sửa lõi V4.2**: `fb487540aa6c877553eeb9e0978437642a4173b1` (`2026-11-23T11:30:57+07:00`, author `nguyenthang1901`)
  - **Commit kiểm thử kỹ thuật V4.2**: `ac2cf1d82d9a742ec0f5e9af81e0ce116fdfbe3d` (`2026-11-23T11:32:54+07:00`, author `nguyenthang1901`)
  - **Commit đồng bộ hồ sơ hiện hành (không đổi mã/test so với `ac2cf1d8...`)**: `d8b44849895bdb0a8a48432286b7d609ba01c635` (`2026-11-23T12:21:09+07:00`, author `nguyenthang1901`)
- **Trạng thái kết luận QA kỹ thuật mã/fixture (tại `ac2cf1d8...` và `d8b44849...` với `git diff src/ scripts/ tests/ configs/` rỗng)**: **`PASS` (ĐẠT TRONG PHẠM VI MÃ NGUỒN SAMPLER V4.2, HAI PROBE R1/R2, 165 KIỂM THỬ FIXTURE CHỌN LỌC VÀ KIỂM TRA CÔ LẬP GIT)**
- **Trạng thái các cổng quản trị hiện hành**:
  - `main_annotation_status = "LOCKED"` / `main_batch1_status = "HOLD"` (Main Annotation Pass 1 chưa mở; chờ quyết định riêng của Lead D)
  - `training_blocked = true`
  - `official_test_used = false`

> [!IMPORTANT]
> **Tóm tắt phạm vi Đính chính (Errata V1.9.1) và Ranh giới QA**:
> 1. **Bảo toàn lịch sử**: Hai tệp `docs/QA_REPORT_MAIN_BATCH1_AC2CF1D_FINAL_V1_9_B.md` (`26.080 bytes`, SHA-256: `baf0e5c39b97f0a1a12a1f17ce6d1f3f42b21dded1e0f68f74c3157e7b061f4c`) và `docs/QA_RAW_LOG_MAIN_BATCH1_AC2CF1D_B.txt` (`5.823 bytes`, SHA-256: `bbfc3d991c000f2c99a56ba74968403b7ec536535e98a4799bf55f13ca74a2e4`) được giữ nguyên byte làm hồ sơ lịch sử. Bản V1.9.1 này đính chính toàn bộ các nhận định về metadata Git, tình trạng lưu trữ hồ sơ QA lịch sử tại mốc `ac2cf1d8...`, số đếm tracked files của scanner, nội dung dẫn chiếu từ gói review của Lead D, cũng như mô tả hàm/script và tên hiện vật hạn chế.
> 2. **Giữ nguyên kết quả thực thi kỹ thuật đã có bằng chứng trực tiếp**: Kết quả chạy **2 probe R1/R2 (`2 passed in 0.63s`)** và **12 tệp test chọn lọc trong repository (`165 passed in 28.06s`)** trên clean worktree tại commit `ac2cf1d82d9a742ec0f5e9af81e0ce116fdfbe3d` (không có `data/restricted/`) là kết quả thực thi thật từ `task-4524.log`, phù hợp với kết quả `167 passed` của Lead D (chênh đúng 2 test ngoài repo). Vì `git diff ac2cf1d82d9a742ec0f5e9af81e0ce116fdfbe3d d8b44849895bdb0a8a48432286b7d609ba01c635 -- src/ scripts/ tests/ configs/` hoàn toàn rỗng (0 dòng thay đổi mã nguồn và test), không cần chạy lại 165 test.
> 3. **Rút nhận định sai về số `164 tracked files` và bổ sung phép kiểm scanner mới tách biệt**: Trong lượt chạy `task-4524`, stdout của `verify_git_isolation.py` chỉ in 2 dòng (`Git Isolation Status: PASS` và `Report written to: artifacts\isolation_verification_report.json`); con số `164` trong văn bản V1.9 là lỗi do người viết báo cáo tự suy diễn không đúng, không phải output thực tế của scanner. Thành viên B chính thức **rút nhận định `total_tracked_files_checked: 164`** và công bố kết quả chạy mới độc lập `verify_git_isolation.py` ngày `23/11/2026` trên cả hai snapshot `ac2cf1d8...` (`total_tracked_files = 261`, `scanned_files_count = 215`) và `d8b44849...` (`total_tracked_files = 269`, `scanned_files_count = 223`), ghi rõ trạng thái `git status` trước và sau khi chạy.

---

## 1. Xác định nhiệm vụ QA và Đính chính (5 mục theo Mục 1 `AGENTS.md`)

1. **Mục tiêu**:
   - Phát hành văn bản Đính chính & Báo cáo QA kế tiếp (**V1.9.1**) nhằm sửa toàn bộ các dữ kiện sai lệch về provenance Git, trạng thái lưu trữ hồ sơ QA lịch sử, số liệu scanner, trích dẫn báo cáo của Lead D và mô tả mã/tên hiện vật trong báo cáo V1.9 (`baf0e5c3...`), đồng thời kiểm định mốc commit đồng bộ hồ sơ mới nhất `d8b44849895bdb0a8a48432286b7d609ba01c635` trên nhánh `origin/feat/c-main-annotation-batch1`.
2. **Đầu vào được phép**:
   - Các commit trên nhánh `origin/feat/c-main-annotation-batch1`: `28462fcece5883a652779976e342d939f7a81e5a`, `fb487540aa6c877553eeb9e0978437642a4173b1`, `ac2cf1d82d9a742ec0f5e9af81e0ce116fdfbe3d`, và `d8b44849895bdb0a8a48432286b7d609ba01c635`.
   - Gói bằng chứng công khai của Lead D: `MAIN_BATCH1_V4_2_LEAD_D_REVIEW.zip` (`10.377 bytes`, SHA-256: `5626514cc1b61083879bf4516fdff126dd22946200e44eb9e4cf1b02ec8a03fb`) và bản đối chiếu `Đối chiếu QA B V1.9 — 23/11/2026` của Lead D.
   - Bản lưu nguyên byte báo cáo V1.9 (`baf0e5c3...`), tệp wrapper log V1.9 (`bbfc3d99...`) và raw task log hệ thống `task-4524.log`.
3. **Đầu ra và tiêu chí đạt**:
   - Tệp báo cáo Errata & QA V1.9.1: `docs/QA_REPORT_MAIN_BATCH1_V4_2_ERRATA_V1_9_1_B.md` kèm bảng ánh xạ đầy đủ **“Claim cũ trong V1.9 $\rightarrow$ Bằng chứng thực tế $\rightarrow$ Nội dung đính chính trong V1.9.1”**.
   - Bàn giao kèm tệp gốc `docs/QA_REPORT_MAIN_BATCH1_28462FC_HOLD_V1_8_B.md` (`27.759 bytes`, SHA-256: `bbdb9d20e94e401375f786cc9d1443b575088390b225b9c9d0f7bcd4fda82192`) và giữ nguyên byte V1.9 (`26.080 bytes`) cùng log V1.9 (`5.823 bytes`) để Thành viên C lưu trữ vào repository.
4. **Ranh giới**:
   - Thành viên B không sửa mã nguồn của Thành viên C, không mở gói dữ liệu hạn chế thật (`MAIN_BATCH1_RESTRICTED_DATA_PACK_FOR_LEAD_D_V4_2_STAGING.zip`), không đọc sổ cái thật (`data/restricted/main_annotation_lot_management_ledger.json`) hay mapping/seed/salt thật.
   - Không chạy lại bộ 165 test khi mã nguồn và test không thay đổi giữa `ac2cf1d8...` và `d8b44849...` và raw log gốc `task-4524.log` vẫn còn nguyên vẹn; chỉ chạy lượt kiểm chứng mới đối với `verify_git_isolation.py` để làm rõ số lượng tracked files và trạng thái working tree trước/sau khi chạy.
5. **Điều chưa biết / Giới hạn**:
   - Thành viên B không trực tiếp kiểm tra byte bên trong gói dữ liệu hạn chế thật `MAIN_BATCH1_RESTRICTED_DATA_PACK_FOR_LEAD_D_V4_2_STAGING.zip` và không trực tiếp chạy `scripts/data/verify_population_fingerprint.py` trên tệp hạn chế `data/restricted/main_batch1/population_1232_canonical_records_v1.json`. Các thông tin về hiện vật hạn chế thật được trích dẫn nghiêm ngặt theo kết quả Lead D đã xác minh tại `REVIEW_MAIN_BATCH1_V4_2_LEAD_D.md` và `main_v42_metadata_summary.json`.

---

## 2. Bảng tổng hợp Đính chính: Claim cũ trong V1.9 $\rightarrow$ Bằng chứng thực tế $\rightarrow$ Nội dung đính chính V1.9.1

| Mã mục | Nhận định cũ trong V1.9 (`baf0e5c3...`) | Bằng chứng thực tế kiểm trực tiếp (Git / Gói Lead D / Mã nguồn) | Nội dung đính chính chính thức tại V1.9.1 |
| :-: | :--- | :--- | :--- |
| **E-01** | Tại `ac2cf1d8...`, C đã khôi phục đầy đủ `20.658 bytes` cho `docs/QA_ADDENDUM_MAIN_BATCH1_B5B7DB2_MIGRATION_VERIFIER_PENDING_V1_7_B.md` và đã lưu trữ `docs/QA_REPORT_MAIN_BATCH1_28462FC_HOLD_V1_8_B.md` (`27.759 bytes`) trong repo. | Kiểm tra `git ls-tree ac2cf1d82d9a742ec0f5e9af81e0ce116fdfbe3d docs/`: <br>- Tệp `docs/QA_ADDENDUM_MAIN_BATCH1_B5B7DB2_MIGRATION_VERIFIER_PENDING_V1_7_B.md` tại `ac2cf1d8...` có git blob `51d56860...`, kích thước **`8.434 bytes`**, SHA-256: `c34cfb042797bbf46bf1c702dfba43a2f9ea0e27ebb33c0cef34153f60fc39ed` (chỉ là bản handoff notice, chưa phải bản gốc `20.658 bytes`).<br>- Tệp `docs/QA_REPORT_MAIN_BATCH1_28462FC_HOLD_V1_8_B.md` **không tồn tại** trong Git tree tại `ac2cf1d8...` (chỉ tồn tại trên máy local của B).<br>- Tới commit mới **`d8b44849895bdb0a8a48432286b7d609ba01c635`**, C mới phục hồi bản gốc V1.7 (`20.658 bytes`, SHA-256: `3fecd1ef8f7cffd4a537ea45d4285c823eb0f557c9bd36f213779c0794e15007`) vào `docs/QA_ADDENDUM_MAIN_BATCH1_B5B7DB2_MIGRATION_VERIFIER_PENDING_V1_7_B.md` và tách notice cũ sang `docs/QA_ADDENDUM_MAIN_BATCH1_B5B7DB2_HANDOFF_NOTICE_V1_7_B.md` (`8.434 bytes`, SHA-256: `c34cfb04...`). Riêng tệp V1.8 (`27.759 bytes`) vẫn chưa có trong Git tree tại `d8b44849...`. | **Đính chính**: Tại snapshot `ac2cf1d8...`, tệp V1.7 trong Git vẫn là bản notice `8.434 bytes` (`c34cfb04...`) và tệp V1.8 chưa được commit vào repo. Việc khôi phục tệp V1.7 gốc `20.658 bytes` (`3fecd1ef...`) chỉ mới hoàn tất tại commit `d8b44849895bdb0a8a48432286b7d609ba01c635` (không hồi tố về `ac2cf1d8...`). Tệp V1.8 gốc (`27.759 bytes`, SHA-256: `bbdb9d20e94e401375f786cc9d1443b575088390b225b9c9d0f7bcd4fda82192`) được B bàn giao lại nguyên byte cùng đợt V1.9.1 này để C commit vào `docs/`. |
| **E-02** | Ghi metadata commit: author `Thang1234566`, các mốc thời gian ngày `2026-04-20` (`09:50:00+07:00`, `11:37:01+07:00`, `11:38:27+07:00`). | Kết quả `git show -s --format="%H | %an | %ae | %aI | %s"`:<br>- `28462fce...`: author `nguyenthang1901` (`thanghoangnguyen19012007@gmail.com`), author date `2026-11-23T00:50:10+07:00`.<br>- `fb487540...`: author `nguyenthang1901`, author date `2026-11-23T11:30:57+07:00`.<br>- `ac2cf1d8...`: author `nguyenthang1901`, author date `2026-11-23T11:32:54+07:00`.<br>- `d8b44849...`: author `nguyenthang1901`, author date `2026-11-23T12:21:09+07:00`. | **Đính chính**: Ghi đúng author metadata trong Git là `nguyenthang1901` và các mốc timestamp thuộc ngày `2026-11-23` (lưu ý Git timestamp chỉ là metadata của commit object, không tự xác thực thời điểm thao tác hay phê duyệt). |
| **E-03** | Ghi diff `28462fce...` $\rightarrow$ `fb487540...` thay đổi `13 tệp` và có thêm script `scripts/data/rehearse_v42_from_raw.py`. | Kết quả `git diff --name-status 28462fcece5883a652779976e342d939f7a81e5a fb487540aa6c877553eeb9e0978437642a4173b1` có đúng **10 tệp** (2 tệp `M` là `artifacts/isolation_verification_report.json`, `src/phishing/data/main_sampling.py`; 8 tệp `A` gồm 6 tệp trong `artifacts/lead_d_review_v4_1/`, `scripts/data/prepare_main_batch1_successor_v4_2.py`, và `tests/test_main_v41_fingerprint_integrity.py`). Không tồn tại tệp `scripts/data/rehearse_v42_from_raw.py` tại `fb487540...` hay `ac2cf1d8...`; script staging/rehearsal thực tế trong repo là `scripts/data/prepare_main_batch1_successor_v4_2.py`. | **Đính chính**: Diff `28462fce...` $\rightarrow$ `fb487540...` có đúng **10 tệp**; script staging và rehearsal thực tế trong repository là `scripts/data/prepare_main_batch1_successor_v4_2.py` (không có `scripts/data/rehearse_v42_from_raw.py`). |
| **E-04** | Ghi diff `fb487540...` $\rightarrow$ `ac2cf1d8...` đổi `total_tracked_files_checked` từ `163` lên `164`; và ghi kết quả chạy `verify_git_isolation.py` tại `ac2cf1d8...` có `total_tracked_files_checked: 164`. | 1. `git diff fb487540aa6c877553eeb9e0978437642a4173b1 ac2cf1d82d9a742ec0f5e9af81e0ce116fdfbe3d` trên `artifacts/isolation_verification_report.json` đổi trường **`"total_tracked_files": 253` $\rightarrow$ `"total_tracked_files": 261`** (không có trường nào tên là `total_tracked_files_checked`, và không phải `163` $\rightarrow$ `164`).<br>2. Trong `task-4524.log` (lượt chạy ban đầu của B), stdout của `python scripts/data/verify_git_isolation.py` chỉ in 2 dòng:<br>`Git Isolation Status: PASS`<br>`Report written to: artifacts\isolation_verification_report.json`<br>Lượt chạy đó không in nội dung JSON ra stdout trước khi xóa worktree; con số `164` trong V1.9 là do người lập báo cáo tự suy diễn nhầm từ số lượng test (`163`/`165`), hoàn toàn không có trong log thật. | **Rút nhận định cũ và Đính chính**: Thành viên B **rút hoàn toàn con số `164`** và tên trường `total_tracked_files_checked`. Tại snapshot `ac2cf1d8...`, số đường dẫn tracked thực tế (`git ls-tree -r` / `git ls-files`) là **261** (và tại `d8b44849...` là **269**). B đã chạy lượt kiểm tra scanner mới độc lập (ghi rõ là lượt chạy mới tại Mục 3.3), ghi nhận đầy đủ trạng thái working tree trước và sau khi chạy (do scanner ghi lại `artifacts/isolation_verification_report.json` với `scanned_files_count = 215` tại `ac2cf1d8...` và `223` tại `d8b44849...` trên clean checkout không có các tệp untracked ngoài Git). |
| **E-05** | Dẫn kết quả của Lead D từ tệp `raw_rehearsal_v42_report.json` với các trường `hydrated_html_count = 1232`, `empty_html_count = 0`, `first_run_nonempty_text_A = 100`, `first_run_nonempty_text_B = 30`, `ledger_blocks_after_first = 2`, `ledger_blocks_after_rerun = 2`. | Trong gói `MAIN_BATCH1_V4_2_LEAD_D_REVIEW.zip` của Lead D **không có** tệp `raw_rehearsal_v42_report.json` và không có các tên trường nói trên. Nguồn chứng cứ thực tế của Lead D là `main_v42_metadata_summary.json` và `REVIEW_MAIN_BATCH1_V4_2_LEAD_D.md` với các trường và giá trị chính xác như sau:<br>- `text_counts`: `a_total = 100`, **`a_nonempty = 97`**, **`a_empty = 3`** (3 mẫu rỗng nguyên bản theo `.strip()`, giữ nguyên từ gói đã niêm phong), `b_total = 30`, **`b_nonempty = 30`**.<br>- `raw_source_exact_proposal_rehearsal` (chạy trên **bản sao ledger** sau khi append proposal block 2): `old_events_unchanged = true`, **`events_after_two_reruns = 3`**, `ledger_copy_unchanged_by_reruns = true`, `a_view_matches_package = true`, `b_view_matches_package = true`, `two_reruns_equal = true`, **`applied_to_real_ledger = false`**.<br>- `metadata_only_rejection`: `rejected = true`, `error_type = "ValueError"`, `ledger_copy_still_unchanged = true`.<br>- `governance.ledger_migration_status`: `"RESERVED_PROPOSAL_ONLY_2_BLOCKS_ON_DISK"` (sổ cái thật trên đĩa vẫn giữ nguyên 2 block lịch sử, chưa áp dụng block 2). | **Đính chính**: Bỏ toàn bộ dẫn chiếu tới `raw_rehearsal_v42_report.json` và các tên trường không có trong gói của Lead D. Trích dẫn đúng theo `main_v42_metadata_summary.json` và `REVIEW_MAIN_BATCH1_V4_2_LEAD_D.md`: Lô A có **97 mẫu `page_text` không rỗng và 3 mẫu `page_text` rỗng nguyên bản**; Tập B có **30/30 mẫu `page_text` không rỗng**; bản sao ledger dùng để rehearsal có **3 events** sau khi thêm block 2 (hai lượt rerun không append thêm event); sổ cái thật vẫn giữ nguyên **2 block lịch sử** (`applied_to_real_ledger = false`). |
| **E-06** | Mô tả `scripts/data/verify_population_fingerprint.py` tại `ac2cf1d8...` “đã sử dụng trực tiếp hàm `compute_population_fingerprint` đã vá tại `src/phishing/data/main_sampling.py`”. | Kiểm tra trực tiếp mã nguồn `scripts/data/verify_population_fingerprint.py` tại `ac2cf1d8...` (`4.558 bytes`, git blob `fff2cc3f17bd77ce10aaa3edb4453e90ca671d0f`): script này chỉ import `normalize_url` từ `phishing.preprocessing.urls`, kiểm tra sự hiện diện của 8 trường bắt buộc trên 1.232 bản ghi trong tệp JSON canonical metadata, kiểm tra `uid_hash` khớp `EXPECTED_HISTORICAL_UID_HASH`, và **tự sắp xếp + serialize JSON canonical (`json.dumps(sorted_records, sort_keys=True, ensure_ascii=False)`) để băm SHA-256** đối chiếu với `EXPECTED_MULTIDIMENSIONAL_FINGERPRINT`. Script này **không import và không gọi** hàm `compute_population_fingerprint` của `src/phishing/data/main_sampling.py`, cũng không nạp raw HTML để băm lại. | **Đính chính**: Ghi đúng thiết kế thực tế của `scripts/data/verify_population_fingerprint.py` (`4.558 bytes`): script tự thực hiện canonical serialization trên 8 trường metadata của tệp hồ sơ chuẩn hóa, không gọi `compute_population_fingerprint`. Việc kiểm tra raw HTML/URL nhất quán với hash cung cấp kèm thuộc về hàm `compute_population_fingerprint` trong `src/phishing/data/main_sampling.py` và quy trình nạp raw Parquet trong `scripts/data/prepare_main_batch1_successor_v4_2.py` (cùng `audit_main_v42_metadata.py` của Lead D). |
| **E-07** | Mô tả lỗi R2 trong `src/phishing/data/main_sampling.py` gọi hàm `project_blind_view()` khiến toàn bộ 100 mẫu A và 30 mẫu B bị ghi đè thành `page_text == ""`. | Trong `src/phishing/data/main_sampling.py` không có hàm `project_blind_view()`; hàm chiếu nội dung an toàn sang Blind View trong `main_sampling.py` là **`extract_safe_view_content(html_content)`** (được gọi bên trong `_build_blind_record`). Ngoài ra, lỗi R2 trước khi sửa là hành vi trả về view có `page_text` rỗng khi chạy rerun với đầu vào metadata-only trên **fixture hoặc bản sao diễn tập**, trong khi các tệp Blind View A/B của gói dữ liệu hạn chế thật đã niêm phong không hề bị ghi đè (như Lead D đã xác nhận `unchanged_from_v4_1.blind_view_a.json = true`, `blind_view_b.json = true`). | **Đính chính**: Sửa tên hàm thành `extract_safe_view_content(html_content)` (trong `_build_blind_record` của `src/phishing/data/main_sampling.py`) và ghi rõ lỗi R2 tại V4.1 là làm trả về view có `page_text` rỗng trong **fixture/bản sao rerun khi truyền đầu vào metadata-only**, không suy diễn thành gói dữ liệu hạn chế thật đã bị ghi đè. |
| **E-08** | Mô tả `artifacts/main_batch1_release_manifest.json` tại `ac2cf1d8...` có trường `approval_status: "pending_lead_d"`. | Kiểm tra trực tiếp `git show ac2cf1d82d9a742ec0f5e9af81e0ce116fdfbe3d:artifacts/main_batch1_release_manifest.json`: tệp manifest công khai trong repo có khối **`"governance_flags": {"main_annotation_status": "LOCKED", "training_blocked": true, "official_test_used": false}`**, hoàn toàn **không có** trường `approval_status`. (Còn các trường `acceptance: {"B": "pending", "D": "pending"}` và `ready_for_annotation: false` nằm trong role manifests / staging `release_manifest.json` thuộc gói staging theo `main_v42_metadata_summary.json`). | **Đính chính**: Ghi đúng cấu trúc `artifacts/main_batch1_release_manifest.json` trong repo chỉ có khối `governance_flags` (`main_annotation_status: "LOCKED"`, `training_blocked: true`, `official_test_used: false`), không gán trường `approval_status` vào tệp này. |
| **E-09** | Ghi tên gói hạn chế thật là `MAIN_BATCH1_B5B7DB2_EVIDENCE_FOR_D_V4_2.zip` và tên tệp sổ cái thật là `allocation_ledger.jsonl`. | Theo `REVIEW_MAIN_BATCH1_V4_2_LEAD_D.md`, `main_v42_metadata_summary.json`, `scripts/data/prepare_main_batch1_successor_v4_2.py` và `scripts/data/verify_git_isolation.py`, tên gói dữ liệu hạn chế thật đang được Lead D xem xét là **`MAIN_BATCH1_RESTRICTED_DATA_PACK_FOR_LEAD_D_V4_2_STAGING.zip`** (`646.230 bytes`, SHA-256: `99defd93b7e7f616a71818b79349ac2d6ee12dc78f540eb6c3d853cbda67a1b4`), và đường dẫn sổ cái hạn chế thật là **`data/restricted/main_annotation_lot_management_ledger.json`**. | **Đính chính**: Sử dụng đúng tên gói hạn chế thật `MAIN_BATCH1_RESTRICTED_DATA_PACK_FOR_LEAD_D_V4_2_STAGING.zip` và đường dẫn sổ cái hạn chế thật `data/restricted/main_annotation_lot_management_ledger.json` trong toàn bộ báo cáo và văn bản chứng thực. |

---

## 3. Đối soát trực tiếp Git tại các Commit `28462fce...`, `fb487540...`, `ac2cf1d8...` và `d8b44849...`

### 3.1. Metadata của 4 Commit liên quan trên nhánh `origin/feat/c-main-annotation-batch1`

Lệnh kiểm tra trực tiếp của Thành viên B:
```powershell
git show -s --format="%H | %an | %ae | %aI | %s" 28462fcece5883a652779976e342d939f7a81e5a fb487540aa6c877553eeb9e0978437642a4173b1 ac2cf1d82d9a742ec0f5e9af81e0ce116fdfbe3d d8b44849895bdb0a8a48432286b7d609ba01c635
```

Kết quả nguyên bản từ Git object database:
1. **`28462fcece5883a652779976e342d939f7a81e5a`** (Mốc V4.1 còn 2 lỗi R1/R2 — giữ trạng thái `FAIL / HOLD` tại V1.8):
   - Author: `nguyenthang1901` (`thanghoangnguyen19012007@gmail.com`)
   - Author Date (metadata commit): `2026-11-23T00:50:10+07:00`
   - Subject: `fix(contract): restore full manifest schema, separate cohort commitment, and standardize scanner scope`
2. **`fb487540aa6c877553eeb9e0978437642a4173b1`** (Commit sửa lõi V4.2):
   - Author: `nguyenthang1901` (`thanghoangnguyen19012007@gmail.com`)
   - Author Date (metadata commit): `2026-11-23T11:30:57+07:00`
   - Subject: `fix(sampling): enforce raw-byte authority in fingerprinting and add hydrated rehearsal v4.2`
3. **`ac2cf1d82d9a742ec0f5e9af81e0ce116fdfbe3d`** (Commit cập nhật báo cáo scanner cho `fb487540...` — mốc chạy 165 test):
   - Author: `nguyenthang1901` (`thanghoangnguyen19012007@gmail.com`)
   - Author Date (metadata commit): `2026-11-23T11:32:54+07:00`
   - Subject: `chore: update isolation verification report for commit fb48754`
4. **`d8b44849895bdb0a8a48432286b7d609ba01c635`** (Commit đồng bộ hồ sơ QA V1.7 và lưu gói review V4.2 của Lead D):
   - Author: `nguyenthang1901` (`thanghoangnguyen19012007@gmail.com`)
   - Author Date (metadata commit): `2026-11-23T12:21:09+07:00`
   - Subject: `docs(audit): restore original QA V1.7 addendum, archive handoff notice, and ingest Lead D V4.2 review`

### 3.2. Kiểm tra Diff giữa các mốc Commit

1. **Diff từ `28462fcece5883a652779976e342d939f7a81e5a` sang `fb487540aa6c877553eeb9e0978437642a4173b1`** (`git diff --name-status 28462fce... fb487540...`):
   - Thay đổi đúng **10 tệp**:
     - `M  artifacts/isolation_verification_report.json`
     - `A  artifacts/lead_d_review_v4_1/COMMANDS.md`
     - `A  artifacts/lead_d_review_v4_1/REVIEW_MAIN_BATCH1_V4_1_LEAD_D.md`
     - `A  artifacts/lead_d_review_v4_1/SHA256SUMS_D.txt`
     - `A  artifacts/lead_d_review_v4_1/audit_main_v41_metadata.py`
     - `A  artifacts/lead_d_review_v4_1/main_v41_metadata_summary.json`
     - `A  artifacts/lead_d_review_v4_1/test_main_v41_fingerprint_integrity.py`
     - `A  scripts/data/prepare_main_batch1_successor_v4_2.py`
     - `M  src/phishing/data/main_sampling.py`
     - `A  tests/test_main_v41_fingerprint_integrity.py`
2. **Diff từ `fb487540aa6c877553eeb9e0978437642a4173b1` sang `ac2cf1d82d9a742ec0f5e9af81e0ce116fdfbe3d`**:
   - Chỉ thay đổi đúng **1 dòng** trong `artifacts/isolation_verification_report.json`:
     - Trường `checks.tracked_files_inspection.total_tracked_files`: từ `253` $\rightarrow$ `261`.
3. **Diff từ `ac2cf1d82d9a742ec0f5e9af81e0ce116fdfbe3d` sang `d8b44849895bdb0a8a48432286b7d609ba01c635`**:
   - Kiểm tra sự bất biến của mã nguồn, script, test và cấu hình:
     ```powershell
     git diff ac2cf1d82d9a742ec0f5e9af81e0ce116fdfbe3d d8b44849895bdb0a8a48432286b7d609ba01c635 -- src/ scripts/ tests/ configs/
     ```
     $\rightarrow$ **Đầu ra hoàn toàn rỗng (0 byte thay đổi)**. Mã nguồn và bộ kiểm thử tại `d8b44849895bdb0a8a48432286b7d609ba01c635` giống nguyên vẹn với `ac2cf1d82d9a742ec0f5e9af81e0ce116fdfbe3d` và `fb487540aa6c877553eeb9e0978437642a4173b1`.
   - 11 tệp thay đổi tại `d8b44849...` chỉ bao gồm tài liệu, artifacts review của Lead D và cấu hình `.gitattributes`:
     - `M  .gitattributes`
     - `M  artifacts/isolation_verification_report.json` (`total_tracked_files`: `261` $\rightarrow$ `269`, `scanned_files_count`: `221` $\rightarrow$ `229`)
     - `A  artifacts/lead_d_review_v4_2/COMMANDS.md`
     - `A  artifacts/lead_d_review_v4_2/REVIEW_MAIN_BATCH1_V4_2_LEAD_D.md`
     - `A  artifacts/lead_d_review_v4_2/SHA256SUMS_D.txt`
     - `A  artifacts/lead_d_review_v4_2/SOURCE_VERIFIED.json`
     - `A  artifacts/lead_d_review_v4_2/audit_main_v42_metadata.py`
     - `A  artifacts/lead_d_review_v4_2/main_v42_metadata_summary.json`
     - `A  artifacts/lead_d_review_v4_2/test_main_v41_fingerprint_integrity.py`
     - `A  docs/QA_ADDENDUM_MAIN_BATCH1_B5B7DB2_HANDOFF_NOTICE_V1_7_B.md` (`8.434 bytes` | SHA-256: `c34cfb042797bbf46bf1c702dfba43a2f9ea0e27ebb33c0cef34153f60fc39ed`)
     - `M  docs/QA_ADDENDUM_MAIN_BATCH1_B5B7DB2_MIGRATION_VERIFIER_PENDING_V1_7_B.md` (`20.658 bytes` | SHA-256: `3fecd1ef8f7cffd4a537ea45d4285c823eb0f557c9bd36f213779c0794e15007`)

### 3.3. Xác minh lại `verify_git_isolation.py` trên Clean Worktree tại `ac2cf1d8...` và `d8b44849...` (Lượt chạy mới ngày `2026-11-23T17:25+07:00`)

Để giải trình minh bạch về số lượng tracked files và hành vi của scanner (không gắn output mới vào lượt chạy cũ `task-4524`), Thành viên B đã thực hiện lượt chạy mới độc lập trên hai clean worktree tách biệt:

1. **Trên clean worktree tại commit `ac2cf1d82d9a742ec0f5e9af81e0ce116fdfbe3d`** (`D:\UED\NCKH2\scratch\ac2cf1d_scanner_check`):
   - **Trước khi chạy scanner**:
     - `git rev-parse HEAD` $\rightarrow$ `ac2cf1d82d9a742ec0f5e9af81e0ce116fdfbe3d`
     - `(git ls-files | Measure-Object).Count` $\rightarrow$ **`261`**
     - `(git ls-tree -r --name-only HEAD | Measure-Object).Count` $\rightarrow$ **`261`**
     - `git status --short` $\rightarrow$ rỗng (working tree sạch trước khi chạy).
     - Trong tệp `artifacts/isolation_verification_report.json` đã commit sẵn tại `ac2cf1d8...`: `total_tracked_files = 261`, `scanned_files_count = 221` (do khi C chạy trên máy C có thêm 6 tệp untracked trong các thư mục quét).
   - **Chạy lệnh**: `python scripts/data/verify_git_isolation.py`
     - Stdout:
       ```text
       Git Isolation Status: PASS
       Report written to: artifacts\isolation_verification_report.json
       ```
   - **Sau khi chạy scanner**:
     - `git status --short` $\rightarrow$ `M artifacts/isolation_verification_report.json` (working tree có 1 tệp bị sửa sau khi chạy vì scanner ghi lại `scanned_files_count = 215` tương ứng đúng 215 tệp tracked thuộc 6 thư mục `docs`, `configs`, `src`, `scripts`, `tests`, `artifacts` trên clean checkout).
     - Giá trị trong `artifacts/isolation_verification_report.json` vừa sinh:
       - `overall_status`: `"PASS"`
       - `checks.check_ignore_probes.status`: `"PASS"` (`all_probes_ignored: true`)
       - `checks.tracked_files_inspection.total_tracked_files`: **`261`** (`violations_count: 0`)
       - `checks.public_content_leak_inspection.scanned_files_count`: **`215`** (`leaks_count: 0`, `read_errors_count: 0`)

2. **Trên clean worktree tại commit `d8b44849895bdb0a8a48432286b7d609ba01c635`** (`D:\UED\NCKH2\scratch\d8b4484_scanner_check`):
   - **Trước khi chạy scanner**:
     - `git rev-parse HEAD` $\rightarrow$ `d8b44849895bdb0a8a48432286b7d609ba01c635`
     - `(git ls-files | Measure-Object).Count` $\rightarrow$ **`269`**
     - `(git ls-tree -r --name-only HEAD | Measure-Object).Count` $\rightarrow$ **`269`**
     - `git status --short` $\rightarrow$ rỗng (working tree sạch trước khi chạy).
     - Trong tệp `artifacts/isolation_verification_report.json` đã commit sẵn tại `d8b44849...`: `total_tracked_files = 269`, `scanned_files_count = 229`.
   - **Chạy lệnh**: `python scripts/data/verify_git_isolation.py`
     - Stdout:
       ```text
       Git Isolation Status: PASS
       Report written to: artifacts\isolation_verification_report.json
       ```
   - **Sau khi chạy scanner**:
     - `git status --short` $\rightarrow$ `M artifacts/isolation_verification_report.json` (do scanner cập nhật `scanned_files_count` từ `229` thành `223` tệp tracked thuộc 6 thư mục mục tiêu trên clean checkout).
     - Giá trị trong `artifacts/isolation_verification_report.json` vừa sinh:
       - `overall_status`: `"PASS"`
       - `checks.check_ignore_probes.status`: `"PASS"` (`all_probes_ignored: true`)
       - `checks.tracked_files_inspection.total_tracked_files`: **`269`** (`violations_count: 0`)
       - `checks.public_content_leak_inspection.scanned_files_count`: **`223`** (`leaks_count: 0`, `read_errors_count: 0`)

---

## 4. Đính chính phần đánh giá kỹ thuật Mã nguồn, Manifest, Verifier và Kết quả kiểm chứng của Lead D

### 4.1. Hạng mục R1 & R2 trong `src/phishing/data/main_sampling.py` (`PASS`)

- **R1 — Tính nhất quán giữa Raw HTML/URL và Hash đi kèm (`PASS`)**:
  - Trong `compute_population_fingerprint(candidates)` tại `src/phishing/data/main_sampling.py`:
    - Raw URL (`c.get("url") or c.get("url_raw")`) là bắt buộc; hàm tự tính `computed_url_hash = hashlib.sha256(url_raw.encode("utf-8")).hexdigest()` và `computed_norm = normalize_url(url_raw)`. Nếu bản ghi có truyền kèm `url_sha256` hoặc `url_normalized` khác với kết quả tính từ raw URL, hàm ném `ValueError("Dữ liệu mâu thuẫn...")`.
    - Khi bản ghi có trường `"html"` (khác `None`), hàm tự tính `computed_html_hash = hashlib.sha256(html_content.encode("utf-8")).hexdigest()`. Nếu bản ghi có truyền kèm `html_sha256` khác với `computed_html_hash`, hàm ném `ValueError("Dữ liệu mâu thuẫn: sample ... có html_sha256 cung cấp sẵn khác với băm thực tế của raw HTML.")`.
  - Probe kiểm chứng: `tests/test_main_v41_fingerprint_integrity.py::test_changed_raw_html_cannot_hide_behind_stale_supplied_hash` (`PASSED`).
- **R2 — Chặn Rerun từ Metadata-Only làm trả về Blind View có `page_text` rỗng trong Fixture/Bản sao (`PASS`)**:
  - Trước khi sửa (tại V4.1 `28462fce...`): khi truyền đầu vào metadata-only (có `html_sha256` nhưng thiếu trường `"html"`), `compute_population_fingerprint` dùng `html_sha256` nên vẫn khớp `prior_pop_hash`, sau đó nhánh rerun trong `run_main_batch1_sampling` gọi `_build_blind_record` $\rightarrow$ **`extract_safe_view_content(html_content)`** với `html_content = ""` làm trả về các bản ghi Blind View có `page_text == ""` trong **fixture hoặc bản sao rerun** (lưu ý: gói dữ liệu hạn chế thật đã niêm phong không bị ghi đè).
  - Sau khi sửa (tại V4.2 `fb487540...` / `ac2cf1d8...` / `d8b44849...`): khi bản ghi không có trường `"html"` (hoặc `"html"` là `None`), `compute_population_fingerprint` băm chuỗi rỗng `hashlib.sha256(b"").hexdigest()` thay vì tin cậy `html_sha256`. Nhờ đó, `pop_hash` của tập metadata-only khác với `prior_pop_hash` của lot đã phát hành từ dữ liệu thô, và `run_main_batch1_sampling` lập tức ném `ValueError("TỪ CHỐI RERUN LOT ...: Quần thể đầu vào đã thay đổi...")` trước khi tạo Blind View.
  - Probe kiểm chứng: `tests/test_main_v41_fingerprint_integrity.py::test_metadata_only_rerun_cannot_silently_replace_views_with_empty_text` (`PASSED`).

### 4.2. Mô tả đúng `scripts/data/verify_population_fingerprint.py`, `scripts/data/prepare_main_batch1_successor_v4_2.py` và `artifacts/main_batch1_release_manifest.json`

1. **`scripts/data/verify_population_fingerprint.py`** (`4.558 bytes`, git blob `fff2cc3f17bd77ce10aaa3edb4453e90ca671d0f` tại cả `ac2cf1d8...` và `d8b44849...`):
   - Script này là công cụ kiểm tra tệp hồ sơ metadata chuẩn hóa 1.232 ứng viên (`data/restricted/main_batch1/population_1232_canonical_records_v1.json`).
   - Script kiểm tra sự hiện diện của 8 trường bắt buộc (`candidate_uid`, `url_raw`, `url_normalized`, `url_sha256`, `html_sha256`, `source_shard`, `source_row`, `source_revision`), đối chiếu mã băm danh sách UID với `EXPECTED_HISTORICAL_UID_HASH` (`40ad5d600e93b10d3fe5910e7454ce4a7a94fe2384b5625d8e6af8983525f9a8`), và **tự sắp xếp + serialize canonical JSON (`json.dumps(sorted_records, sort_keys=True, ensure_ascii=False)`)** để tính SHA-256 đối chiếu với `EXPECTED_MULTIDIMENSIONAL_FINGERPRINT` (`77773871ab50c361cb5df0ca4f9e5604a251a20f933d1bc22ee7d9f016814919`).
   - Script này **không gọi** `compute_population_fingerprint` của `src/phishing/data/main_sampling.py` và không nạp raw HTML từ Parquet.
2. **`scripts/data/prepare_main_batch1_successor_v4_2.py`** (git blob `88081243e6ea4b07e4dae7a6f96c54c83935c014`):
   - Đây là script staging và diễn tập thực tế được thêm tại commit `fb487540...` (không tồn tại script nào tên là `scripts/data/rehearse_v42_from_raw.py`).
   - Script này nạp raw HTML/URL từ `data/raw/phreshphish/data/train-001.parquet` theo `source_row`, kiểm tra khớp `url_sha256` và `html_sha256` của cả 1.232 ứng viên với bản ghi canonical, gọi `compute_population_fingerprint(hydrated_candidates)`, tạo bản sao sổ cái trong thư mục tạm để diễn tập `run_main_batch1_sampling` 2 lần cùng `lot_id="main_lot_batch_001"`, và đóng gói hiện vật hạn chế `MAIN_BATCH1_RESTRICTED_DATA_PACK_FOR_LEAD_D_V4_2_STAGING.zip`.
3. **`artifacts/main_batch1_release_manifest.json`** (manifest công khai trong repository):
   - Có `manifest_version: "1.1.0"`, `lot_id: "main_lot_batch_001"`, và khối cờ quản trị:
     ```json
     "governance_flags": {
       "main_annotation_status": "LOCKED",
       "training_blocked": true,
       "official_test_used": false
     }
     ```
   - Tệp này **không có** trường `approval_status`.

### 4.3. Dẫn chiếu đúng kết quả kiểm chứng của Lead D trên gói dữ liệu hạn chế thật V4.2

Theo đúng hai tệp chứng cứ của Lead D trong gói `MAIN_BATCH1_V4_2_LEAD_D_REVIEW.zip` (`REVIEW_MAIN_BATCH1_V4_2_LEAD_D.md` và `main_v42_metadata_summary.json`), các kết quả do **Lead D đã trực tiếp kiểm chứng** trên hiện vật hạn chế thật bao gồm:

- **Hiện vật hạn chế thật được Lead D kiểm**:
  - Gói ZIP hạn chế thật: **`MAIN_BATCH1_RESTRICTED_DATA_PACK_FOR_LEAD_D_V4_2_STAGING.zip`** (`646.230 bytes`, SHA-256: `99defd93b7e7f616a71818b79349ac2d6ee12dc78f540eb6c3d853cbda67a1b4`, `crc_ok = true`, gồm 26 tệp tổng cộng = 25 hiện vật đối chiếu hash khớp `25/25` + 1 bảng kê `SHA256SUMS.txt`).
  - Sổ cái hạn chế thật: **`data/restricted/main_annotation_lot_management_ledger.json`** (giữ nguyên byte so với V4.1, trên đĩa vẫn chỉ có **2 block lịch sử**, trạng thái `ledger_migration_status = "RESERVED_PROPOSAL_ONLY_2_BLOCKS_ON_DISK"`).
  - Các tệp `blind_view_a.json`, `blind_view_b.json`, `mapping_restricted.json`, `population_1232_canonical_records_v1.json`, `population_1232_sealed.json`, `exclusion_registry.json`, `pilot_batch1_recovery_dossier_restricted_v4.json`, `clean_calibration_exclusion_mapping_c_32.json`, `provenance_recovery_audit_log.json` đều giữ nguyên byte so với V4.1 (`unchanged_from_v4_1 = true`), `salt_and_selection_seeds_unchanged = true`.
- **Thống kê `page_text` thực tế trên Blind View A100 và B30 (`text_counts` trong `main_v42_metadata_summary.json`)**:
  - **Lô A (`a_total = 100`)**: **`a_nonempty = 97`** mẫu có `page_text` không rỗng, và **`a_empty = 3`** mẫu có `page_text` rỗng nguyên bản theo `.strip()` (giữ nguyên từ bản niêm phong trước đó, không phải phát sinh do lỗi metadata-only/rerun).
  - **Tập B (`b_total = 30`)**: **`b_nonempty = 30`** mẫu có `page_text` không rỗng.
- **Kết quả diễn tập từ nguồn thô thật trên bản sao sổ cái (`raw_source_exact_proposal_rehearsal` và `metadata_only_rejection` trong `main_v42_metadata_summary.json`)**:
  - Lead D tải lại shard công khai `train-001.parquet` (`322.018.201 bytes`, SHA-256: `260cb9c93299f6b244d48321fe115523159770f4e73446b382473628c6e81d74`), hydrate raw candidates theo `source_row`, ghi proposal V4.2 vào **bản sao ledger** và gọi sampler thật 2 lần:
    - `old_events_unchanged = true` (2 sự kiện lịch sử giữ nguyên).
    - `events_after_two_reruns = 3` (bản sao ledger có 3 events sau khi thêm block 2; hai lượt rerun không ghi thêm event và không sửa byte: `ledger_copy_unchanged_by_reruns = true`).
    - `a_view_matches_package = true`, `b_view_matches_package = true`, `two_reruns_equal = true` (payload Blind View A100/B30 khi rerun từ nguồn thô khớp với gói đã niêm phong).
    - `applied_to_real_ledger = false` (chưa áp dụng migration vào sổ cái thật `data/restricted/main_annotation_lot_management_ledger.json`).
  - Khi thử rerun bằng đầu vào metadata-only trên bản sao đã niêm phong (`metadata_only_rejection`):
    - `rejected = true`, `error_type = "ValueError"`, `ledger_copy_still_unchanged = true`.
- **Trạng thái role manifests & quản trị trong gói staging (`role_manifests` và `governance` trong `main_v42_metadata_summary.json`)**:
  - Cả hai role manifest `a` và `b` đều có `acceptance: {"B": "pending", "D": "pending"}`, `ready: false`, `blocked_for_pending: true`, `output_created: false` (CLI thật dừng đúng với thông báo `"CHƯA NGHIỆM THU"`, không tạo tệp JSONL đầu ra).
  - Khối `governance`: `main_batch1_status = "HOLD"`, `ready_for_annotation = false`, `acceptance = {"B": "pending", "D": "pending"}`, `training_blocked = true`, `official_test_used = false`, `ledger_migration_status = "RESERVED_PROPOSAL_ONLY_2_BLOCKS_ON_DISK"`.

---

## 5. Chuẩn hóa Bằng chứng Log: Phân biệt Output nguyên bản (`task-4524.log`) và Tệp tổng hợp/Wrapper (`QA_RAW_LOG_MAIN_BATCH1_AC2CF1D_B.txt`)

### 5.1. Giải trình Provenance của tệp `docs/QA_RAW_LOG_MAIN_BATCH1_AC2CF1D_B.txt` (`5.823 bytes`)

- Tệp `docs/QA_RAW_LOG_MAIN_BATCH1_AC2CF1D_B.txt` (`5.823 bytes`, SHA-256: `bbfc3d991c000f2c99a56ba74968403b7ec536535e98a4799bf55f13ca74a2e4`; khi dán vào khung văn bản không có ký tự `LF` cuối là `5.822 bytes`) là **tệp biên bản tổng hợp (formatted wrapper summary)** do Thành viên B lập sau khi tiến trình chạy test hoàn tất, nhằm lược bỏ các ký hiệu phần trăm tiến độ trên thanh progress bar của pytest theo quy tắc từ ngữ tại Mục 5 `AGENTS.md`.
- Để phân biệt rõ ràng giữa **output nguyên bản của hệ thống** và **phần tổng hợp do B lập**, Mục 5.2 dưới đây trích xuất nguyên văn nội dung từ tệp log hệ thống `task-4524.log` (đã thay ký hiệu `%` trên thanh tiến độ bằng chữ `pct` để tuân thủ quy tắc không chứa chuỗi ký tự cấm trong báo cáo Markdown).

### 5.2. Output nguyên bản của lệnh chạy 2 Probe, 165 Test và Git Isolation trên Clean Worktree `ac2cf1d82d9a742ec0f5e9af81e0ce116fdfbe3d` (Từ `task-4524.log`)

- **Thời điểm hoàn tất task hệ thống**: `2026-11-23T04:52:19Z` (`2026-11-23T11:52:19+07:00`)
- **Mã thoát (Exit code)**: `0`
- **Nội dung stdout nguyên bản (chỉ thay ký tự `%` trong ngoặc vuông tiến độ pytest thành `pct`)**:

```text
Preparing worktree (detached HEAD ac2cf1d)
HEAD is now at ac2cf1d chore: update isolation verification report for commit fb48754
=== WORKTREE HEAD & ENVIRONMENT ===
ac2cf1d82d9a742ec0f5e9af81e0ce116fdfbe3d
fb487540aa6c877553eeb9e0978437642a4173b1
Python 3.14.2
pytest 9.1.1
=== TEST DATA/RESTRICTED ABSENCE ===
False
=== PROBE SUITE (2 TESTS) ===
============================= test session starts =============================
platform win32 -- Python 3.14.2, pytest-9.1.1, pluggy-1.6.0 -- C:\Users\LAPTOP MSI\AppData\Local\Python\pythoncore-3.14-64\python.exe
cachedir: .pytest_cache
rootdir: D:\UED\NCKH2\scratch\ac2cf1d_wt
configfile: pytest.ini
plugins: anyio-4.14.2
collecting ... collected 2 items

tests/test_main_v41_fingerprint_integrity.py::test_changed_raw_html_cannot_hide_behind_stale_supplied_hash PASSED [ 50pct]
tests/test_main_v41_fingerprint_integrity.py::test_metadata_only_rerun_cannot_silently_replace_views_with_empty_text PASSED [100pct]

============================== 2 passed in 0.63s ==============================
=== 12 SELECTED REPOSITORY TEST SUITES (165 TESTS) ===
........................................................................ [ 43pct]
........................................................................ [ 87pct]
.....................                                                    [100pct]
165 passed in 28.06s
=== GIT ISOLATION VERIFIER ===
Git Isolation Status: PASS
Report written to: artifacts\isolation_verification_report.json
```

- **Lưu ý đối chiếu số lượng test (`165` vs `167`)**:
  - Bộ 12 tệp test chọn lọc trong repository tại `ac2cf1d82d9a742ec0f5e9af81e0ce116fdfbe3d` (và `d8b44849895bdb0a8a48432286b7d609ba01c635`) có tổng cộng **165 test**, đã **bao gồm** 2 probe trong `tests/test_main_v41_fingerprint_integrity.py` (163 test từ 11 tệp trước đó + 2 probe V4.1 = 165 test; không cộng trùng hai lần).
  - Bộ `167 passed` của Lead D trong `COMMANDS.md` gồm đúng 165 test trong repository nói trên cộng thêm 2 pure-fixture test nằm ở tệp ngoài repository trên máy Lead D (`/private/tmp/test_main_v3_pure_fixture_migration.py`).

---

## 6. Trạng thái Lưu trữ Hồ sơ QA Lịch sử và Bàn giao Tệp Nguyên Byte

### 6.1. Đối chiếu trạng thái các tệp hồ sơ QA của Thành viên B trên Git (`ac2cf1d8...` vs `d8b44849...`) và bản gốc của B

| Tệp hồ sơ QA của Thành viên B | Trạng thái thực tế tại commit `ac2cf1d82d9a742ec0f5e9af81e0ce116fdfbe3d` | Trạng thái thực tế tại commit `d8b44849895bdb0a8a48432286b7d609ba01c635` | Bản gốc trên máy Thành viên B (bàn giao để C lưu nguyên byte) |
| :--- | :--- | :--- | :--- |
| `docs/QA_REPORT_MAIN_BATCH1_33E8BB6_CONSOLIDATED_V1_6_B.md` | Đã có trong Git (`37.162 bytes` \| SHA-256: `bfeb73d97db47fdb6741ce47849254d4f3a9483120bd533a3cb0f357f8a41e09`) | Đã có trong Git (`37.162 bytes` \| SHA-256: `bfeb73d9...`) | Khớp nguyên byte (`37.162 bytes` \| `bfeb73d9...`) |
| `docs/QA_RAW_LOG_MAIN_BATCH1_33E8BB6_B.txt` | Đã có trong Git (`10.920 bytes` \| SHA-256: `29b452ff6b2debfd2826d3ac3f15678a7f07aff3b45012e53ff3462c17c30ee7`) | Đã có trong Git (`10.920 bytes` \| SHA-256: `29b452ff...`) | Khớp nguyên byte (`10.920 bytes` \| `29b452ff...`) |
| `docs/QA_ADDENDUM_MAIN_BATCH1_B5B7DB2_MIGRATION_VERIFIER_PENDING_V1_7_B.md` | **Chưa phải bản gốc**: tại `ac2cf1d8...` tệp này vẫn là bản handoff notice (`8.434 bytes` \| SHA-256: `c34cfb042797bbf46bf1c702dfba43a2f9ea0e27ebb33c0cef34153f60fc39ed`) | **Đã khôi phục bản gốc**: tại `d8b44849...` đã là bản gốc (`20.658 bytes` \| SHA-256: `3fecd1ef8f7cffd4a537ea45d4285c823eb0f557c9bd36f213779c0794e15007`); bản notice cũ được lưu riêng tại `docs/QA_ADDENDUM_MAIN_BATCH1_B5B7DB2_HANDOFF_NOTICE_V1_7_B.md` (`8.434 bytes` \| `c34cfb04...`) | Khớp nguyên byte với bản đã khôi phục tại `d8b44849...` (`20.658 bytes` \| `3fecd1ef...`) |
| `docs/QA_REPORT_MAIN_BATCH1_28462FC_HOLD_V1_8_B.md` | **Không tồn tại trong Git tree** tại `ac2cf1d8...` | **Chưa tồn tại trong Git tree** tại `d8b44849...` | Có sẵn bản gốc trên máy B: **`27.759 bytes`** \| SHA-256: **`bbdb9d20e94e401375f786cc9d1443b575088390b225b9c9d0f7bcd4fda82192`** (B bàn giao kèm đợt này để C commit nguyên byte) |
| `docs/QA_REPORT_MAIN_BATCH1_AC2CF1D_FINAL_V1_9_B.md` | Chưa phát hành tại thời điểm tạo commit `ac2cf1d8...` | Chưa được commit vào `d8b44849...` | Bản lịch sử V1.9 giữ nguyên byte trên máy B: **`26.080 bytes`** \| SHA-256: **`baf0e5c39b97f0a1a12a1f17ce6d1f3f42b21dded1e0f68f74c3157e7b061f4c`** (C lưu kèm bản Errata V1.9.1) |
| `docs/QA_RAW_LOG_MAIN_BATCH1_AC2CF1D_B.txt` | Chưa phát hành tại thời điểm tạo commit `ac2cf1d8...` | Chưa được commit vào `d8b44849...` | Bản wrapper log V1.9 giữ nguyên byte trên máy B: **`5.823 bytes`** \| SHA-256: **`bbfc3d991c000f2c99a56ba74968403b7ec536535e98a4799bf55f13ca74a2e4`** |
| `docs/QA_REPORT_MAIN_BATCH1_V4_2_ERRATA_V1_9_1_B.md` | Không áp dụng | Phát hành sau commit `d8b44849...` | **Bản Đính chính & Báo cáo QA V1.9.1 này** (xem kích thước & SHA-256 trong bảng bàn giao bên ngoài tệp) |

---

## 7. Bảng phân định Phạm vi Kết luận QA sau Đính chính V1.9.1

| Hạng mục / Phạm vi | Nguồn kiểm chứng | Trạng thái sau V1.9.1 | Ghi chú phạm vi & bằng chứng |
| :--- | :--- | :-: | :--- |
| **1. Sửa lỗi R1 (Raw HTML/URL vs Stale Hash)** trong `src/phishing/data/main_sampling.py` | **Thành viên B trực tiếp kiểm** (mã nguồn & probe fixture) | **`PASS` (Giữ nguyên)** | `test_changed_raw_html_cannot_hide_behind_stale_supplied_hash` đạt (`PASSED` trong `0.63s`). |
| **2. Sửa lỗi R2 (Chặn Metadata-Only Rerun trả về view rỗng trong fixture/bản sao)** trong `src/phishing/data/main_sampling.py` | **Thành viên B trực tiếp kiểm** (mã nguồn & probe fixture) | **`PASS` (Giữ nguyên, đính chính mô tả hàm `extract_safe_view_content`)** | `test_metadata_only_rerun_cannot_silently_replace_views_with_empty_text` đạt (`PASSED` trong `0.63s`). |
| **3. Bộ 12 tệp kiểm thử chọn lọc trong repository (165 tests, đã bao gồm 2 probe R1/R2)** | **Thành viên B trực tiếp kiểm** trên clean worktree `ac2cf1d8...` (không có `data/restricted/`) | **`PASS` (Giữ nguyên)** | `165 passed, 0 failed, 0 skipped` trong `28.06s` (`task-4524.log`); mã nguồn và test không đổi tại `d8b44849...`. |
| **4. Kiểm tra cô lập Git (`scripts/data/verify_git_isolation.py`)** | **Thành viên B chạy lại lượt kiểm mới độc lập** ngày `23/11/2026` tại `ac2cf1d8...` và `d8b44849...` | **`PASS` (Đã rút con số `164` sai ở V1.9; thay bằng số thực đo `261` tại `ac2cf1d8...` và `269` tại `d8b44849...`)** | `Git Isolation Status: PASS` (`violations_count = 0`, `leaks_count = 0`; ghi rõ scanner sửa `scanned_files_count` trong `artifacts/isolation_verification_report.json` thành `215` tại `ac2cf1d8...` và `223` tại `d8b44849...` sau khi chạy trên clean checkout). |
| **5. Khôi phục tệp V1.7 gốc (`20.658 bytes`, `3fecd1ef...`) trong Git** | **Thành viên B trực tiếp kiểm** bằng `git cat-file blob` | **`CHƯA KHÔI PHỤC` tại `ac2cf1d8...` $\rightarrow$ `ĐÃ KHÔI PHỤC` tại `d8b44849...`** | Tại `ac2cf1d8...` vẫn là notice `8.434 bytes` (`c34cfb04...`); đã được C khôi phục đúng `20.658 bytes` (`3fecd1ef...`) tại commit `d8b44849895bdb0a8a48432286b7d609ba01c635`. |
| **6. Lưu trữ tệp V1.8 gốc (`27.759 bytes`, `bbdb9d20...`), V1.9 (`26.080 bytes`, `baf0e5c3...`), log V1.9 (`5.823 bytes`, `bbfc3d99...`) và V1.9.1 vào Git** | **Thành viên B trực tiếp kiểm** trên Git tree `d8b44849...` | **`PENDING` (Chờ C commit nguyên byte các tệp B bàn giao)** | Chưa có trong Git tree tại `d8b44849...`; B bàn giao đầy đủ các tệp nguyên byte để C commit vào `docs/`. |
| **7. Kiểm chứng gói hạn chế thật `MAIN_BATCH1_RESTRICTED_DATA_PACK_FOR_LEAD_D_V4_2_STAGING.zip` và diễn tập nguồn thô thật trên bản sao sổ cái** | **Lead D đã kiểm độc lập** (`REVIEW_MAIN_BATCH1_V4_2_LEAD_D.md` & `main_v42_metadata_summary.json`) | **Dẫn chiếu đúng kết quả của Lead D (B không mở gói hạn chế thật)** | A100: 97 `page_text` không rỗng + 3 rỗng nguyên bản; B30: 30 không rỗng; bản sao ledger rehearsal có 3 events; sổ cái thật `data/restricted/main_annotation_lot_management_ledger.json` giữ nguyên 2 block (`applied_to_real_ledger = false`). |
| **8. Áp dụng Block 2 vào sổ cái hạn chế thật và mở cổng Main Annotation Pass 1** | **Quyết định quản trị riêng của Lead D** | **`HOLD` / `LOCKED` (`PENDING_LEAD_D`)** | `main_annotation_status="LOCKED"`, `main_batch1_status="HOLD"`, `training_blocked=true`, `official_test_used=false`. |

---

## 8. Văn bản Chứng thực QA Độc lập & Đính chính của Thành viên B (V1.9.1)

Tôi, **Phùng Tấn Minh** (**Thành viên B — Annotator B kiêm QA Lead & Nhóm trưởng**), chứng thực:

1. **Về việc đính chính hồ sơ V1.9**:
   - Giữ nguyên byte báo cáo `docs/QA_REPORT_MAIN_BATCH1_AC2CF1D_FINAL_V1_9_B.md` (`26.080 bytes`, SHA-256: `baf0e5c39b97f0a1a12a1f17ce6d1f3f42b21dded1e0f68f74c3157e7b061f4c`) và tệp wrapper log `docs/QA_RAW_LOG_MAIN_BATCH1_AC2CF1D_B.txt` (`5.823 bytes`, SHA-256: `bbfc3d991c000f2c99a56ba74968403b7ec536535e98a4799bf55f13ca74a2e4`) làm dấu vết lịch sử.
   - Phát hành bản Đính chính & Báo cáo QA **V1.9.1** (`docs/QA_REPORT_MAIN_BATCH1_V4_2_ERRATA_V1_9_1_B.md`) để sửa toàn bộ các sai sót về metadata commit, số lượng tệp diff, trạng thái lưu trữ V1.7/V1.8 tại `ac2cf1d8...`, rút con số `164 tracked files` không có trong output scanner, sửa trích dẫn kết quả của Lead D theo đúng `main_v42_metadata_summary.json` / `REVIEW_MAIN_BATCH1_V4_2_LEAD_D.md`, và sửa mô tả mã nguồn (`verify_population_fingerprint.py`, `prepare_main_batch1_successor_v4_2.py`, `extract_safe_view_content`, `artifacts/main_batch1_release_manifest.json`) cùng tên hiện vật hạn chế thật (`MAIN_BATCH1_RESTRICTED_DATA_PACK_FOR_LEAD_D_V4_2_STAGING.zip` và `data/restricted/main_annotation_lot_management_ledger.json`).
2. **Về kết luận QA kỹ thuật mã nguồn và bộ kiểm thử fixture V4.2**:
   - Xác nhận mã nguồn, script, test và cấu hình tại commit `d8b44849895bdb0a8a48432286b7d609ba01c635` hoàn toàn bất biến so với commit `ac2cf1d82d9a742ec0f5e9af81e0ce116fdfbe3d` (và commit sửa lõi `fb487540aa6c877553eeb9e0978437642a4173b1`).
   - Giữ nguyên kết luận **`PASS` kỹ thuật trong phạm vi mã nguồn sampler V4.2, hai probe hồi quy R1/R2 (`2 passed in 0.63s`), bộ 12 tệp kiểm thử chọn lọc trong repository (`165 passed, 0 failed, 0 skipped in 28.06s`) và phép kiểm cô lập Git (`verify_git_isolation.py` đạt `PASS` với `261` tracked files tại `ac2cf1d8...` và `269` tracked files tại `d8b44849...`)** trên clean worktree không có `data/restricted/`.
3. **Về ranh giới quản trị**:
   - Việc lưu trữ các tệp báo cáo QA của B (`V1.8`, `V1.9`, log `V1.9`, và `V1.9.1`) vào nhánh Git đang ở trạng thái chờ Thành viên C commit nguyên byte.
   - Các cổng quản trị `main_annotation_status="LOCKED"`, `main_batch1_status="HOLD"`, `training_blocked=true`, `official_test_used=false` tiếp tục giữ nguyên trạng thái đóng; chưa áp dụng Block 2 vào sổ cái hạn chế thật `data/restricted/main_annotation_lot_management_ledger.json` và chưa mở Main Annotation Pass 1 cho đến khi có quyết định riêng của **Lead D (Anh Tuấn)**.
