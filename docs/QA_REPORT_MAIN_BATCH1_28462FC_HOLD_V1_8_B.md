# BÁO CÁO THẨM ĐỊNH QA ĐỘC LẬP TẠI COMMIT `28462fcece5883a652779976e342d939f7a81e5a` (TRẠNG THÁI `FAIL / HOLD` DO HỒI QUY SAMPLER V4.1) — PHIÊN BẢN V1.8: CHUẨN BỊ MAIN ANNOTATION ĐỢT 1

- **Mã tài liệu**: `QA-REPORT-MAIN-BATCH1-28462FC-HOLD-V1-8-B`
- **Phiên bản**: `1.8` — Báo cáo thẩm định QA độc lập đối với commit thực tế `28462fcece5883a652779976e342d939f7a81e5a` (nhánh `origin/feat/c-main-annotation-batch1`), đối chiếu với commit trước `9367288ea27e681eb1eff93de7ed5e8b2704bfde` và baseline `33e8bb6c29c7ee15209ae5847d48aae973a3f536`.
- **Bảo toàn lịch sử kiểm toán (Audit Trail)**: Giữ nguyên byte của toàn bộ các văn bản QA trước:
  - Phụ lục V1.7 (`b5b7db2`): `docs/QA_ADDENDUM_MAIN_BATCH1_B5B7DB2_MIGRATION_VERIFIER_PENDING_V1_7_B.md` (`20.658 bytes` | SHA-256: `3fecd1ef8f7cffd4a537ea45d4285c823eb0f557c9bd36f213779c0794e15007`)
  - Báo cáo QA gộp V1.6 (`33e8bb6`): `docs/QA_REPORT_MAIN_BATCH1_33E8BB6_CONSOLIDATED_V1_6_B.md` (`37.162 bytes` | SHA-256: `bfeb73d97db47fdb6741ce47849254d4f3a9483120bd533a3cb0f357f8a41e09`)
  - Raw log thực thi V1.6 (`33e8bb6`): `docs/QA_RAW_LOG_MAIN_BATCH1_33E8BB6_B.txt` (`10.920 bytes` | SHA-256: `29b452ff6b2debfd2826d3ac3f15678a7f07aff3b45012e53ff3462c17c30ee7`)
  - Bản V1.5 (`29.287 bytes` | `016b537a...`), V1.4 (`34.343 bytes` | `f1031f64...`), V1.3 (`30.791 bytes` | `06cc07fc...`), V1.2 (`16.337 bytes` | `660fe800...`), V1.1 (`17.587 bytes` | `a574026b...`), V1.0 (`13.100 bytes` | `de51db19...`), Phụ lục `02fca4f` (`16.721 bytes` | `42e5389e...`).
- **Ngày phát hành**: `2026-11-23`
- **Người thực hiện thẩm định độc lập**: Phùng Tấn Minh (**Thành viên B — Annotator B kiêm QA Lead & Nhóm trưởng**)
- **Người nhận báo cáo**: **Lead D** (Anh Tuấn) và **Thành viên C** (Nguyễn Thắng)
- **Định danh commit đã kiểm tra**:
  - **Full SHA thực tế trên remote `origin/feat/c-main-annotation-batch1`**: **`28462fcece5883a652779976e342d939f7a81e5a`**
  - **Ghi nhận lỗi định danh trong thông báo của C**: Chuỗi full SHA `28462fc48f29bf4244f77c2aa5b214f4eb04c54e` mà Thành viên C ghi trong thông báo bàn giao **không tồn tại** trong Git repository.
- **Kết luận QA tại commit `28462fcece5883a652779976e342d939f7a81e5a`**: **`FAIL / HOLD`**
  - **Fingerprint / raw-hash consistency**: **`FAIL`** (Đổi nội dung raw HTML nhưng giữ `html_sha256` cũ không làm fingerprint thay đổi và không bị từ chối).
  - **Metadata-only rejection**: **`FAIL`** (Rerun `run_main_batch1_sampling` bằng bản ghi chỉ có metadata không có trường `html` vẫn vượt qua chốt `population_hash` và sinh ra 100/30 mẫu Blind View có `page_text == ""`).
  - **Rerun giữ đầy đủ payload**: **`PASS` trên input raw hợp lệ** / **`FAIL` khi input thiếu raw HTML payload tại `28462fc`**.
  - **Manifest / lineage và hồi quy chọn lọc**: **`PASS` trên phạm vi 11 tệp kiểm thử chọn lọc trong repo (`163 passed in 30.81s`)**; riêng tệp `docs/QA_ADDENDUM_MAIN_BATCH1_B5B7DB2_MIGRATION_VERIFIER_PENDING_V1_7_B.md` C lưu trên Git bị rút gọn còn `8.434 bytes` (`c34cfb04...`) so với bản gốc `20.658 bytes` (`3fecd1ef...`) của B, cần C khôi phục nguyên byte.
- **Trạng thái cổng quản trị hiện hành**: `main_annotation_status="LOCKED"`, `training_blocked=true`, `official_test_used=false` (Tiếp tục giữ đóng).

---

## I. XÁC ĐỊNH NHIỆM VỤ TRƯỚC KHI LÀM (THEO MỤC 1 `AGENTS.md`)

1. **Mục tiêu**:
   - Xác minh full commit SHA thực tế trên nhánh `origin/feat/c-main-annotation-batch1` (`28462fcece5883a652779976e342d939f7a81e5a`), đọc `git diff` so với `9367288ea27e681eb1eff93de7ed5e8b2704bfde` và `33e8bb6c29c7ee15209ae5847d48aae973a3f536`.
   - Kiểm tra việc lưu trữ nguyên byte 3 tệp hồ sơ QA của B mà C đã cam kết tại commit `74bbf419e34abf38b7fd43087891de766592c2c5`.
   - Chạy độc lập trên clean Git worktree của commit `28462fcece5883a652779976e342d939f7a81e5a` bộ 11 tệp kiểm thử hồi quy chọn lọc trong repo (gồm 8 tệp 154 test tại `33e8bb6` và 3 tệp test synthetic mới `test_ledger_migration_proposal.py`, `test_isolation_scanner_regression.py`, `test_main_batch1_manifest_preflight.py`).
   - Tái lập thực nghiệm 2 probe kiểm tính toàn vẹn fingerprint và bảo toàn nội dung khi rerun (`test_main_v41_fingerprint_integrity.py`) trên cả commit `28462fcece5883a652779976e342d939f7a81e5a` và commit trước `9367288ea27e681eb1eff93de7ed5e8b2704bfde` để chứng minh chính xác điểm hồi quy trong `src/phishing/data/main_sampling.py`.
2. **Đầu vào được phép**:
   - Chỉ đạo của Lead D ngày 23/11/2026 và các thông báo bàn giao của Thành viên C (`74bbf41`, `9367288`, `28462fc`).
   - Git commit `28462fcece5883a652779976e342d939f7a81e5a` và `9367288ea27e681eb1eff93de7ed5e8b2704bfde` trên nhánh `origin/feat/c-main-annotation-batch1` (kiểm trên clean Git worktree tạm không có `data/restricted/`).
   - **Bảo vệ tính mù**: Không nhận và không mở gói dữ liệu thật V3/V4/V4.1, mapping thật, ledger thật, seed/salt thật hay nhãn nguồn.
3. **Đầu ra và tiêu chí đạt**:
   - Báo cáo QA độc lập `docs/QA_REPORT_MAIN_BATCH1_28462FC_HOLD_V1_8_B.md` ghi nhận full commit SHA thực tế, diff, mã nguồn tái lập 2 probe hồi quy tại `28462fc`, kết quả chạy thực tế và báo cáo bàn giao chuẩn 10 mục để Thành viên C sửa lỗi và bàn giao commit sửa cuối.
4. **Ranh giới**:
   - B không sửa mã của C rồi tự ký QA cho phần đó; không ký trước cho commit chưa bàn giao; các nhận định về gói dữ liệu hạn chế thật V3/V4/V4.1 do Lead D trực tiếp kiểm được dẫn đúng nguồn.
5. **Điều chưa biết**:
   - Full commit SHA của bản sửa tiếp theo từ Thành viên C sau khi khép 2 lỗi hồi quy trong `src/phishing/data/main_sampling.py` và khôi phục nguyên byte tệp phụ lục V1.7 (`20.658 bytes`).

---

## II. ĐỐI SOÁT ĐỊNH DANH COMMIT, HỒ SƠ LƯU TRỮ CỦA B VÀ `GIT DIFF` TẠI `28462fcece5883a652779976e342d939f7a81e5a`

### 1. Xác minh Full Commit SHA trên remote `origin/feat/c-main-annotation-batch1`
- Chuỗi lịch sử commit thực tế trên nhánh `origin/feat/c-main-annotation-batch1`:
  - `33e8bb6c29c7ee15209ae5847d48aae973a3f536`: Baseline mã nguồn đã đạt 154 phép kiểm chọn lọc (Báo cáo V1.6).
  - `b5b7db2900fefd142c211fb2045a3e2bf3272298`: Chỉ cập nhật `artifacts/main_batch1_release_manifest.json`.
  - `38998ca...`: Cập nhật release manifest và thêm các script kiểm tra độc lập cho đợt bàn giao V3.
  - `74bbf419e34abf38b7fd43087891de766592c2c5`: Lưu 3 tệp báo cáo QA của B và thêm `tests/test_ledger_migration_proposal.py`.
  - `9367288ea27e681eb1eff93de7ed5e8b2704bfde`: Chuyển `tests/test_ledger_migration_proposal.py` sang fixture tổng hợp và thêm `tests/test_isolation_scanner_regression.py`.
  - **`28462fcece5883a652779976e342d939f7a81e5a`**: Commit HEAD hiện tại trên `origin/feat/c-main-annotation-batch1` (chuỗi `28462fc48f29bf4244f77c2aa5b214f4eb04c54e` trong tin nhắn của C là chuỗi sai, không tồn tại trong Git repository).

### 2. Kiểm tra tính toàn vẹn 3 tệp hồ sơ QA của B mà C đã lưu vào `docs/`
QA Lead B đã đo trực tiếp byte và SHA-256 của 3 tệp trong Git tree `28462fcece5883a652779976e342d939f7a81e5a` so với bản gốc của B:

| Tệp hồ sơ QA của B | Bản gốc của B (LF) | Bản C lưu trên Git (`74bbf41` / `28462fc`) | Kết quả đối chiếu |
| :--- | :--- | :--- | :---: |
| `docs/QA_REPORT_MAIN_BATCH1_33E8BB6_CONSOLIDATED_V1_6_B.md` | `37.162 bytes` \| `bfeb73d97db47fdb6741ce47849254d4f3a9483120bd533a3cb0f357f8a41e09` | `37.162 bytes` \| `bfeb73d97db47fdb6741ce47849254d4f3a9483120bd533a3cb0f357f8a41e09` | **Khớp nguyên byte** |
| `docs/QA_RAW_LOG_MAIN_BATCH1_33E8BB6_B.txt` | `10.920 bytes` \| `29b452ff6b2debfd2826d3ac3f15678a7f07aff3b45012e53ff3462c17c30ee7` | `10.920 bytes` \| `29b452ff6b2debfd2826d3ac3f15678a7f07aff3b45012e53ff3462c17c30ee7` | **Khớp nguyên byte** |
| `docs/QA_ADDENDUM_MAIN_BATCH1_B5B7DB2_MIGRATION_VERIFIER_PENDING_V1_7_B.md` | `20.658 bytes` \| `3fecd1ef8f7cffd4a537ea45d4285c823eb0f557c9bd36f213779c0794e15007` | `8.434 bytes` \| `c34cfb042797bbf46bf1c702dfba43a2f9ea0e27ebb33c0cef34153f60fc39ed` | **LỆCH (C lưu bản tóm tắt 8.434 bytes thay vì bản gốc 20.658 bytes)** |

- **Yêu cầu C khắc phục**: Khôi phục nguyên byte tệp `docs/QA_ADDENDUM_MAIN_BATCH1_B5B7DB2_MIGRATION_VERIFIER_PENDING_V1_7_B.md` đúng bản gốc của B (`20.658 bytes`, SHA-256: `3fecd1ef8f7cffd4a537ea45d4285c823eb0f557c9bd36f213779c0794e15007`).

### 3. Phân tích `git diff` giữa `9367288ea27e681eb1eff93de7ed5e8b2704bfde` và `28462fcece5883a652779976e342d939f7a81e5a`
Tại `src/phishing/data/main_sampling.py:63–72,126–132`, commit `28462fcece5883a652779976e342d939f7a81e5a` đã thay đổi cách tính `compute_population_fingerprint` và khóa sắp xếp trong `run_main_batch1_sampling`:
```python
raw_url = str(c.get("url_raw") or c.get("url") or "")
norm_url = str(c.get("url_normalized") or normalize_url(raw_url))
url_hash = str(c.get("url_sha256") or hashlib.sha256(raw_url.encode("utf-8")).hexdigest())
html_content = c.get("html") or ""
html_hash = str(c.get("html_sha256") or hashlib.sha256(html_content.encode("utf-8")).hexdigest())
```
Thay đổi này gây ra **2 lỗi hồi quy nghiêm trọng trong sampler**:
1. **Bỏ qua nội dung raw HTML/URL khi bản ghi có sẵn trường `html_sha256` / `url_sha256` / `url_normalized`**: Biểu thức `c.get("html_sha256") or hashlib.sha256(...)` ưu tiên lấy chuỗi `html_sha256` có sẵn mà **không kiểm tra xem `html_sha256` có khớp với mã băm thực tế của `c["html"]` hay không** (tương tự với `url_sha256` và `url_normalized`). Do đó, khi nội dung `c["html"]` bị thay đổi nhưng `c["html_sha256"]` vẫn giữ giá trị cũ, `compute_population_fingerprint` trả về đúng mã băm cũ mà không phát hiện mâu thuẫn.
2. **Cho phép rerun `run_main_batch1_sampling` bằng bản ghi chỉ có metadata (thiếu trường `html`), sinh ra Blind View có `page_text` rỗng**: Khi truyền danh sách bản ghi chỉ có metadata (`url`, `url_raw`, `url_normalized`, `url_sha256`, `html_sha256`, `source_row`, `source_shard`, `source_revision` nhưng không có khóa `"html"`), `compute_population_fingerprint` tại `28462fc` vẫn trả về cùng `population_hash` với quần thể raw ban đầu. Nhờ đó, lượt rerun vượt qua chốt kiểm `prior_pop_hash != pop_hash` tại dòng 155, rồi đi tới dòng 232 (`html_content = sample.get("html", "")` $\rightarrow$ `""`) và xuất ra 100 mẫu Blind View A cùng 30 mẫu Blind View B có đủ ID nhưng **`page_text == ""` (rỗng hoàn toàn)** và làm thay đổi `sample_content_hash`!

---

## III. KẾT QUẢ KIỂM THỬ ĐỘC LẬP & TÁI LẬP HAI PROBE HỒI QUY V4.1

- **Môi trường kiểm thử của B**: Windows 11 (`win32`), Python 3.14.2, pytest-9.1.1, pluggy-1.6.0, trên clean Git worktree độc lập không có `data/restricted/`.

### 1. Lượt 1 — Chạy 11 tệp kiểm thử chọn lọc trong repository tại `28462fcece5883a652779976e342d939f7a81e5a`
- **Lệnh thực thi**:
  ```powershell
  $env:PYTHONPATH=".;src"
  python -m pytest tests/test_main_annotation_batch1.py tests/test_blind_view.py tests/test_annotate_cli_timer_pause.py tests/test_ledger_migration_proposal.py tests/test_isolation_scanner_regression.py tests/test_main_batch1_manifest_preflight.py artifacts/lead_d_review_8fc845d/test_main_8fc_additional_guards.py artifacts/lead_d_review_6c26d74/test_main_6c26_release_boundaries.py artifacts/lead_d_review_599c7d9/test_main_599_followup.py artifacts/lead_d_review_da3a78d/test_main_da3_intake_history.py artifacts/lead_d_review_a12f90b/test_main_a12_approval_and_sop.py -q
  ```
- **Kết quả**: **`163 passed in 30.81s`** (`passed=163`, `failed=0`, `skipped=0`, `deselected=0` — gồm 154 test của 8 tệp tại `33e8bb6` + 1 test trong `test_ledger_migration_proposal.py` + 3 test trong `test_isolation_scanner_regression.py` + 5 test trong `test_main_batch1_manifest_preflight.py`; khi cộng thêm 2 test kiểm riêng của Lead D thì tương ứng mốc 165 test hồi quy chọn lọc).

### 2. Lượt 2 — Tái lập 2 probe hồi quy `test_main_v41_fingerprint_integrity.py` trên `28462fcece5883a652779976e342d939f7a81e5a` và đối chứng trên `9367288ea27e681eb1eff93de7ed5e8b2704bfde`

- **Mã nguồn tái lập độc lập (`test_main_v41_fingerprint_integrity.py`)**:
  ```python
  """Independent synthetic probes for V4.1 sampler regression at 28462fcece5883a652779976e342d939f7a81e5a."""
  import copy
  import hashlib
  from pathlib import Path
  import pytest

  from phishing.annotation.blind_view import normalize_url
  from phishing.data.lot_ledger import LotManagementLedger
  from phishing.data.main_sampling import (
      compute_population_fingerprint,
      run_main_batch1_sampling,
  )


  def _raw_pool(n: int = 120):
      pool = []
      for i in range(n):
          url = f"https://fixture-{i:04d}.example.test/login"
          html = f"<html><head><title>Fixture {i}</title></head><body><p>Content {i}</p></body></html>"
          pool.append({
              "candidate_uid": f"fixture_uid_{i:04d}",
              "url": url,
              "url_raw": url,
              "url_normalized": normalize_url(url),
              "url_sha256": hashlib.sha256(url.encode("utf-8")).hexdigest(),
              "html": html,
              "html_sha256": hashlib.sha256(html.encode("utf-8")).hexdigest(),
              "source_row": i,
              "source_shard": "train-001.parquet",
              "source_revision": "fixture-revision-0000",
          })
      return pool


  def test_mutated_raw_html_with_stale_html_sha256_must_change_fingerprint_or_raise():
      pool = _raw_pool(10)
      fp_original = compute_population_fingerprint(pool)
      mutated = copy.deepcopy(pool)
      mutated[0]["html"] = "<html><body>MUTATED PAYLOAD THAT DOES NOT MATCH STALE HASH</body></html>"
      try:
          fp_mutated = compute_population_fingerprint(mutated)
      except ValueError:
          return
      assert fp_mutated != fp_original, (
          "Regression at 28462fc: compute_population_fingerprint ignored mutated raw HTML because stale html_sha256 was present!"
      )


  def test_metadata_only_rerun_must_not_produce_empty_page_text_views(tmp_path: Path):
      raw_candidates = _raw_pool(120)
      ledger = LotManagementLedger(tmp_path / "fixture_ledger.json")
      first = run_main_batch1_sampling(
          raw_candidates,
          seed_lot_100=101,
          seed_b_subset_30=202,
          seed_release_shuffle=303,
          blind_salt="synthetic_probe_salt_v41",
          ledger=ledger,
          lot_id="fixture_lot_v41",
      )
      assert all(s["page_text"] for s in first.blind_view_a)
      metadata_only = [{k: v for k, v in c.items() if k != "html"} for c in raw_candidates]
      try:
          rerun = run_main_batch1_sampling(
              metadata_only,
              seed_lot_100=101,
              seed_b_subset_30=202,
              seed_release_shuffle=303,
              blind_salt="synthetic_probe_salt_v41",
              ledger=ledger,
              lot_id="fixture_lot_v41",
          )
      except ValueError:
          return
      assert [s["page_text"] for s in rerun.blind_view_a] == [s["page_text"] for s in first.blind_view_a], (
          "Regression at 28462fc: metadata-only rerun bypassed population_hash guard and produced empty page_text views!"
      )
  ```
- **Kết quả chạy trên commit `28462fcece5883a652779976e342d939f7a81e5a`**:
  - Lệnh: `$env:PYTHONPATH=".;src"; python -m pytest ../test_main_v41_fingerprint_integrity.py -q`
  - Kết quả: **`2 failed in 0.93s`** (`passed=0`, `failed=2`, `skipped=0`, `deselected=0`):
    1. `test_mutated_raw_html_with_stale_html_sha256_must_change_fingerprint_or_raise`: **`FAILED`** (`AssertionError: assert '3b70eef5cd1a22df9e421d14870ae67baeb4e5681cba9b8ffb41452e57f38331' != '3b70eef5cd1a22df9e421d14870ae67baeb4e5681cba9b8ffb41452e57f38331'`).
    2. `test_metadata_only_rerun_must_not_produce_empty_page_text_views`: **`FAILED`** (`AssertionError: assert ['', '', '', ...] == ['Content 73', 'Content 107', ...]`).
- **Kết quả đối chứng trên commit `9367288ea27e681eb1eff93de7ed5e8b2704bfde`**:
  - Lệnh: `$env:PYTHONPATH=".;src"; python -m pytest ../test_main_v41_fingerprint_integrity.py -q`
  - Kết quả: **`2 passed in 0.54s`** (`passed=2`, `failed=0`, `skipped=0`, `deselected=0`).

---

## IV. YÊU CẦU KỸ THUẬT ĐỂ THÀNH VIÊN C KHẮC PHỤC TRƯỚC KHI BÀN GIAO COMMIT SỬA CUỐI

1. **Khôi phục tính toàn vẹn của `compute_population_fingerprint` (Mục 3 chỉ đạo D)**:
   - Khi bản ghi đầu vào có trường raw (`"html"` hoặc `"url"` / `"url_raw"`), hàm phải tính trực tiếp mã băm SHA-256 / chuẩn hóa từ dữ liệu raw đó; nếu bản ghi đồng thời cung cấp các trường dẫn xuất (`"html_sha256"`, `"url_sha256"`, `"url_normalized"`) mà không khớp với giá trị tính từ raw payload thì **phải từ chối ngay (`ValueError`)**, tuyệt đối không được dùng `c.get("html_sha256") or ...` để bỏ qua nội dung `"html"` đã bị thay đổi.
   - Nếu tách riêng hàm kiểm định canonical metadata (`verify_population_fingerprint.py`) khỏi đường sampler raw (`main_sampling.py`), hợp đồng của từng đường phải tường minh và fail-closed.
2. **Chặn rerun thiếu raw payload và bảo toàn toàn bộ nội dung Blind View (Mục 4 chỉ đạo D)**:
   - Đường `run_main_batch1_sampling` và `supersede_lot_sampling` có nhiệm vụ render Blind View (`page_text`, `structure_summary`, `sample_content_hash`), nên bắt buộc từng ứng viên trong `lot_100` phải có raw `"html"` hợp lệ (kiểu `str` không bị thiếu/`None`); nếu đầu vào chỉ là metadata-only (không có khóa `"html"` hoặc `"html"` là `None`) thì phải từ chối fail-closed (`ValueError`) trước khi render, không được phép trả về 100/30 mẫu có `page_text == ""`.
   - Với rerun hợp lệ (có đủ raw payload hợp lệ): phải giữ nguyên cohort A100, tập B30, thứ tự phát hành, nội dung `page_text`, `structure_summary`, `sample_content_hash`, giữ nguyên 2 sự kiện lịch sử, không append lặp khi chạy nhiều lần và chặn khi sai fingerprint/seed hoặc thiếu trạng thái.
3. **Giữ nguyên các phần đã khép và chuẩn hóa hồ sơ (Mục 1 & Mục 5 chỉ đạo D)**:
   - Giữ nguyên hợp đồng manifest 12 trường, chặn `pending` / `ready_for_annotation=false`, và giữ tách biệt `cohort_seed_commitment` lịch sử khỏi `seed_commitment` phát hành.
   - Khôi phục nguyên byte tệp `docs/QA_ADDENDUM_MAIN_BATCH1_B5B7DB2_MIGRATION_VERIFIER_PENDING_V1_7_B.md` đúng bản gốc `20.658 bytes` (`3fecd1ef8f7cffd4a537ea45d4285c823eb0f557c9bd36f213779c0794e15007`) của B.
   - Khi bàn giao bản sửa cuối, ghi đúng full commit SHA thực tế tồn tại trên remote.

---

## V. BÁO CÁO BÀN GIAO CHUẨN 10 MỤC (THEO MỤC 6 `AGENTS.md`)

- **Mục tiêu và phạm vi**:
  - Thẩm định độc lập commit `28462fcece5883a652779976e342d939f7a81e5a` trên nhánh `origin/feat/c-main-annotation-batch1` (ghi nhận chuỗi `28462fc48f29bf4244f77c2aa5b214f4eb04c54e` trong thông báo của C không tồn tại trên repo).
  - Xác nhận 11 tệp kiểm thử hồi quy chọn lọc trong repo đạt `163 passed in 30.81s`, đồng thời tái lập thực nghiệm 2 probe hồi quy mới (`test_main_v41_fingerprint_integrity.py`) chứng minh `2 failed` trên `28462fcece5883a652779976e342d939f7a81e5a` và `2 passed` trên `9367288ea27e681eb1eff93de7ed5e8b2704bfde`.
  - Bàn giao cách tái lập và yêu cầu khắc phục cho Thành viên C để B thực hiện QA trên commit sửa cuối.
- **Người thực hiện / người kiểm độc lập**:
  - Người phát hiện hồi quy V4.1 & chỉ đạo phạm vi kiểm: Lead D (Anh Tuấn).
  - Người kiểm định độc lập trên clean worktree, tái lập 2 probe & lập báo cáo QA V1.8: Phùng Tấn Minh (Thành viên B — Annotator B kiêm QA Lead & Nhóm trưởng).
  - Người tiếp nhận báo cáo lỗi để sửa mã nguồn và hồ sơ: Nguyễn Thắng (Thành viên C — Data Pipeline & Thư ký).
- **AI đã dùng**:
  - AI hỗ trợ đối chiếu `git rev-parse`, `git diff`, kiểm tra mã băm 3 tệp hồ sơ QA của B trên Git tree `28462fc`, chạy pytest trên clean Git worktree tạm tại `28462fc` và `9367288` (sau đó xóa worktree) và lập báo cáo QA V1.8.
  - Không dùng AI cho dữ liệu hạn chế, gói thật V3/V4/V4.1, mapping thật, ledger thật, seed/salt thật hay nhãn nguồn.
- **Đầu vào đã khóa**:
  - Commit thực tế được kiểm: `28462fcece5883a652779976e342d939f7a81e5a` (nhánh `origin/feat/c-main-annotation-batch1`).
  - Commit đối chứng trước hồi quy: `9367288ea27e681eb1eff93de7ed5e8b2704bfde` (nhánh `origin/feat/c-main-annotation-batch1`).
  - Commit lưu hồ sơ QA trước đó: `74bbf419e34abf38b7fd43087891de766592c2c5`.
  - Toàn bộ các văn bản QA lịch sử của B trên máy B được giữ nguyên byte: V1.7 (`20.658 bytes` | `3fecd1ef...`), V1.6 (`37.162 bytes` | `bfeb73d9...`), Raw log V1.6 (`10.920 bytes` | `29b452ff...`), V1.5 (`29.287 bytes` | `016b537a...`), V1.4 (`34.343 bytes` | `f1031f64...`), V1.3 (`30.791 bytes` | `06cc07fc...`), V1.2 (`16.337 bytes` | `660fe800...`), V1.1 (`17.587 bytes` | `a574026b...`), V1.0 (`13.100 bytes` | `de51db19...`), Phụ lục `02fca4f` (`16.721 bytes` | `42e5389e...`).
- **Thay đổi thực tế**:
  - Phát hành văn bản QA độc lập `docs/QA_REPORT_MAIN_BATCH1_28462FC_HOLD_V1_8_B.md`; không sửa bất kỳ tệp mã nguồn hay tài liệu nào thuộc phạm vi của C.
- **Tự kiểm**:
  - Đối chiếu trực tiếp byte và SHA-256 của 3 tệp hồ sơ QA của B trên Git commit `28462fcece5883a652779976e342d939f7a81e5a`: xác nhận `QA_REPORT_MAIN_BATCH1_33E8BB6_CONSOLIDATED_V1_6_B.md` (`37.162 bytes`, `bfeb73d9...`) và `QA_RAW_LOG_MAIN_BATCH1_33E8BB6_B.txt` (`10.920 bytes`, `29b452ff...`) khớp nguyên byte, nhưng `QA_ADDENDUM_MAIN_BATCH1_B5B7DB2_MIGRATION_VERIFIER_PENDING_V1_7_B.md` trên Git bị rút gọn còn `8.434 bytes` (`c34cfb04...`) so với bản gốc `20.658 bytes` (`3fecd1ef...`).
  - Đọc trực tiếp `git diff 9367288ea27e681eb1eff93de7ed5e8b2704bfde 28462fcece5883a652779976e342d939f7a81e5a -- src/phishing/data/main_sampling.py` để xác định nguyên nhân gốc của 2 lỗi hồi quy.
- **Kiểm thử (Thực thi độc lập trên clean worktree không có `data/restricted/`)**:
  - Môi trường: Windows 11, Python 3.14.2, pytest-9.1.1, pluggy-1.6.0.
  - Lượt 1 (11 tệp kiểm thử chọn lọc trong repo tại `28462fcece5883a652779976e342d939f7a81e5a`):
    - Lệnh: `$env:PYTHONPATH=".;src"; python -m pytest tests/test_main_annotation_batch1.py tests/test_blind_view.py tests/test_annotate_cli_timer_pause.py tests/test_ledger_migration_proposal.py tests/test_isolation_scanner_regression.py tests/test_main_batch1_manifest_preflight.py artifacts/lead_d_review_8fc845d/test_main_8fc_additional_guards.py artifacts/lead_d_review_6c26d74/test_main_6c26_release_boundaries.py artifacts/lead_d_review_599c7d9/test_main_599_followup.py artifacts/lead_d_review_da3a78d/test_main_da3_intake_history.py artifacts/lead_d_review_a12f90b/test_main_a12_approval_and_sop.py -q`
    - Kết quả: **`passed=163`**, **`failed=0`**, **`skipped=0`**, **`deselected=0`** trong **`30.81s`** (bộ chọn lọc 11 tệp trong repo; không gọi là toàn bộ repository).
  - Lượt 2 (2 probe kiểm tính toàn vẹn fingerprint và rerun metadata-only `test_main_v41_fingerprint_integrity.py` tại `28462fcece5883a652779976e342d939f7a81e5a`):
    - Lệnh: `$env:PYTHONPATH=".;src"; python -m pytest ../test_main_v41_fingerprint_integrity.py -q`
    - Kết quả: **`passed=0`**, **`failed=2`**, **`skipped=0`**, **`deselected=0`** trong **`0.93s`**.
  - Lượt 3 (Đối chứng cùng 2 probe `test_main_v41_fingerprint_integrity.py` tại `9367288ea27e681eb1eff93de7ed5e8b2704bfde`):
    - Lệnh: `$env:PYTHONPATH=".;src"; python -m pytest ../test_main_v41_fingerprint_integrity.py -q`
    - Kết quả: **`passed=2`**, **`failed=0`**, **`skipped=0`**, **`deselected=0`** trong **`0.54s`**.
- **QA độc lập (Theo 4 hạng mục bắt buộc tại commit `28462fcece5883a652779976e342d939f7a81e5a`)**:
  - **1. Fingerprint / raw-hash consistency**: **`FAIL`** (Đổi raw HTML nhưng giữ `html_sha256` cũ vẫn trả về cùng fingerprint cũ mà không đổi hash hoặc báo lỗi mâu thuẫn).
  - **2. Metadata-only rejection**: **`FAIL`** (Rerun `run_main_batch1_sampling` với bản ghi thiếu raw `"html"` không bị từ chối mà tạo ra Blind View có `page_text == ""`).
  - **3. Rerun giữ đầy đủ payload**: **`PASS` trên input raw hợp lệ** / **`FAIL` trên đường không chặn input thiếu raw HTML tại `28462fc`**.
  - **4. Manifest / lineage và hồi quy liên quan**: **`PASS` trên 11 tệp kiểm thử chọn lọc (`163 passed`)**; **`FAIL` về lưu trữ nguyên byte tệp phụ lục V1.7 trên Git và sai lệch chuỗi full commit SHA trong thông báo của C**.
  - **Kết luận tổng thể tại commit `28462fcece5883a652779976e342d939f7a81e5a`**: **`FAIL / HOLD`**.
- **Giới hạn và việc còn mở**:
  - Giới hạn: B giữ tính mù, chỉ kiểm trên mã công khai và fixture tổng hợp trên clean checkout không có `data/restricted/`; các kết quả kiểm gói dữ liệu thật V3/V4/V4.1 được dẫn theo kết quả kiểm trực tiếp của Lead D.
  - Việc còn mở:
    1. Thành viên C sửa hồi quy trong `src/phishing/data/main_sampling.py` (đảm bảo tính nhất quán giữa raw HTML/URL và các trường hash/normalized; từ chối metadata-only input thiếu raw HTML trên đường sampler cần render Blind View; bảo toàn đầy đủ payload khi rerun hợp lệ).
    2. Thành viên C khôi phục nguyên byte tệp `docs/QA_ADDENDUM_MAIN_BATCH1_B5B7DB2_MIGRATION_VERIFIER_PENDING_V1_7_B.md` (`20.658 bytes`, SHA-256 `3fecd1ef...`) và bàn giao đúng full commit SHA thực tế của bản sửa cuối.
    3. Ngay khi C bàn giao commit sửa cuối, B sẽ kiểm tra lại full commit SHA, diff, chạy toàn bộ bộ test hồi quy chọn lọc cùng 2 probe `test_main_v41_fingerprint_integrity.py` để phát hành báo cáo QA cuối.
- **Trạng thái quản trị**:
  - Gói chuẩn bị Main Annotation Đợt 1 tại commit `28462fcece5883a652779976e342d939f7a81e5a`: **`FAIL / HOLD`**.
  - Các cờ khóa quản trị hiện hành: `main_annotation_status="LOCKED"`, `training_blocked=true`, `official_test_used=false` (Chưa áp dụng ledger thật, chưa mở Pass 1; chờ quyết định riêng của Lead D).
