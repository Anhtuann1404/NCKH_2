# BÁO CÁO THẨM ĐỊNH QA ĐỘC LẬP GỘP (PHIÊN BẢN V1.6): NGHIỆM THU KỸ THUẬT MÃ NGUỒN, SOP & FIXTURE TẠI COMMIT `33e8bb6` VÀ PHÂN ĐỊNH RANH GIỚI GÓI HẠN CHẾ THẬT MAIN ANNOTATION ĐỢT 1

- **Mã tài liệu**: `QA-REPORT-MAIN-BATCH1-33E8BB6-CONSOLIDATED-V1-6-B`
- **Phiên bản**: `1.6 (Consolidated Technical QA Report)` — Báo cáo thẩm định QA độc lập gộp của Thành viên B trên phiên bản mã nguồn `33e8bb6c29c7ee15209ae5847d48aae973a3f536` (nhánh `origin/feat/c-main-annotation-batch1`). Hợp nhất toàn bộ yêu cầu kiểm định từ các lượt trước trên mã nguồn, SOP và fixture tổng hợp; đồng thời phân định rõ ranh giới với gói dữ liệu hạn chế thật đang chờ Thành viên C đồng bộ và Lead D đối soát.
- **Bảo toàn lịch sử kiểm toán (Audit Trail)**: Giữ nguyên byte và phạm vi lịch sử của toàn bộ các văn bản trước (không kế thừa chữ ký cũ sang hash mới):
  - Danh mục hợp nhất V1.5 (`a12f90b`): `docs/QA_CONSOLIDATED_CHECKLIST_MAIN_BATCH1_B_V1_5.md` (`29.287 bytes` | SHA-256: `016b537af1c124e0aa43c99d0898a0886d83701f1908aeb691ac7ef214af7e6e`)
  - Báo cáo V1.4 (`6c26d74`): `docs/QA_REPORT_MAIN_BATCH1_6C26D74_HOLD_V1_4_B.md` (`34.343 bytes` | SHA-256: `f1031f647513d0235345a856200162cf78b136ab2f0390b42847e8b31b30ca0b`)
  - Báo cáo V1.3 (`8fc845d`): `docs/QA_REPORT_MAIN_BATCH1_8FC845D_HOLD_V1_3_B.md` (`30.791 bytes` | SHA-256: `06cc07fc0f9c35126efb93ea8d1c44c2fe68424785a5ce446fe7ba1f36bad356`)
  - Báo cáo V1.2 (`b013ed7`): `docs/QA_PRE_RELEASE_CHECKLIST_MAIN_BATCH1_B_V1_2_HOLD_B013ED7.md` (`16.337 bytes` | SHA-256: `660fe8004bfe5b5c45d2754519e455d7942f72953f860dc331334878f4d2f2ef`)
  - Bản V1.1 (`17.587 bytes` | `a574026b...`), Bản V1.0 (`13.100 bytes` | `de51db19...`), Phụ lục `02fca4f` (`16.721 bytes` | `42e5389e...`).
- **Ngày phát hành**: `2026-11-21`
- **Người thực hiện thẩm định độc lập**: Phùng Tấn Minh (**Thành viên B — Annotator B kiêm QA Lead & Nhóm trưởng**)
- **Người bàn giao đối tượng mã nguồn**: Nguyễn Thắng (**Thành viên C — Data Pipeline & Thư ký**)
- **Người chỉ đạo, kiểm hiện vật hạn chế & quyết định mở phiên**: **Lead D** (Anh Tuấn)
- **Repository & Nhánh kiểm định**: `https://github.com/Anhtuann1404/NCKH_2` — nhánh `origin/feat/c-main-annotation-batch1`
- **Full Commit SHA đã kiểm định**: **`33e8bb6c29c7ee15209ae5847d48aae973a3f536`**
- **Kết luận QA theo đúng phạm vi**:
  - **Phạm vi mã nguồn, SOP và fixture tổng hợp tại commit `33e8bb6c29c7ee15209ae5847d48aae973a3f536`**: **`PASS`** (**“QA kỹ thuật trên mã và fixture tại commit 33e8bb6 đạt”** — 154/154 phép kiểm trong 8 tệp chọn lọc đạt, toàn bộ 7 cổng G1–G7 trên mã và fixture tổng hợp đạt).
  - **Phạm vi gói dữ liệu hạn chế thật (Real Restricted Package) và Migration hiện vật thật**: **`HOLD / PENDING`** (Theo kết quả kiểm trực tiếp của Lead D trên hiện vật hạn chế, gói dữ liệu thật C bàn giao chưa đồng bộ với hợp đồng mã nguồn tại `33e8bb6`: hai view thật còn là bare list, mapping thiếu `source_row` ở 100 dòng, cam kết quần thể dùng thuật toán UID-only cũ, và ledger thật thiếu dữ liệu tập B30 phục vụ rerun. B không mở hiện vật hạn chế để giữ tính mù; chưa nghiệm thu nội dung gói Main thật).
- **Trạng thái cổng quản trị hiện hành**: `main_annotation_status="LOCKED"`, `training_blocked=true`, `official_test_used=false` (Tiếp tục giữ đóng; chỉ Lead D quyết định mở phiên gán nhãn sau khi gói dữ liệu thật được đồng bộ và đối soát).

---

## I. XÁC ĐỊNH NHIỆM VỤ TRƯỚC KHI LÀM (THEO MỤC 1 `AGENTS.md`)

1. **Mục tiêu**:
   - Thực hiện đợt QA độc lập gộp cho Main Annotation Batch 1 trên commit mới nhất `33e8bb6c29c7ee15209ae5847d48aae973a3f536` (nhánh `origin/feat/c-main-annotation-batch1`).
   - Kiểm tra đầy đủ 7 cổng **G1–G7** (gồm sampling & ledger, hợp đồng Main `1.2.0` & tương thích legacy, xuất gói & khóa phát hành, intake & lịch sử biên lai/attempt, khóa quyền thay thế bản nộp, và thực thi nguyên văn kịch bản Kappa 3×3 trong SOP với `bootstrap_iterations=1000`, `random_seed=2026`).
   - Tái lập độc lập **8 tệp kiểm thử chọn lọc (154 phép kiểm)**, chạy `scripts/data/verify_git_isolation.py`, chạy các phép kiểm hành vi bổ sung bằng fixture tổng hợp (từ chối bare list, bảo toàn provenance qua mapping, độ nhạy fingerprint khi giữ nguyên UID nhưng đổi URL/HTML/source_row/shard/revision), và chạy riêng lượt kiểm rộng toàn repo để phân định rõ phạm vi.
   - Ghi nhận rõ ràng ranh giới giữa **phần B trực tiếp kiểm trên mã và fixture**, **phần đối chiếu báo cáo của Lead D/C** (gồm gói `MAIN_BATCH1_33E8BB6_EVIDENCE_FOR_B.zip` và 4 phát hiện của Lead D trên gói dữ liệu hạn chế thật), và **phần chưa kiểm được** (hiện vật hạn chế thật và cơ chế migration nếu C bổ sung sau).
2. **Đầu vào được phép**:
   - Quy tắc `AGENTS.md` và chỉ đạo nhiệm vụ QA gộp + thông tin bổ sung của Lead D ngày 21/11/2026.
   - Git commit `33e8bb6c29c7ee15209ae5847d48aae973a3f536` trên nhánh `origin/feat/c-main-annotation-batch1` (kiểm trên clean Git worktree độc lập).
   - Các tệp probe chuẩn của Lead D đã được đối chiếu mã băm SHA-256 (`test_main_8fc_additional_guards.py`, `test_main_6c26_release_boundaries.py`, `test_main_599_followup.py`, `test_main_da3_intake_history.py`, `test_main_a12_approval_and_sop.py`).
   - **Bảo vệ tính mù của Annotator B**: B chỉ dùng mã công khai, đặc tả kỹ thuật và fixture tổng hợp; không nhận và không mở quần thể thật, mapping thật, seed/salt thật, nhãn nguồn, Blind View A hoặc cơ cấu nhãn tuyển chọn.
3. **Đầu ra và tiêu chí đạt**:
   - Báo cáo QA gộp `docs/QA_REPORT_MAIN_BATCH1_33E8BB6_CONSOLIDATED_V1_6_B.md` đứng tên Thành viên B, tuân thủ mẫu 10 mục chuẩn kiểm chứng, phân tách rõ 7 cổng G1–G7 và 6 nhóm kết luận.
4. **Ranh giới**:
   - B không sửa mã hay tài liệu của C rồi tự ký QA.
   - B không ký xác nhận nội dung gói dữ liệu Main thật (do B chỉ kiểm trên mã và fixture tổng hợp để giữ tính mù; phần gói thật do Lead D kiểm chứng trực tiếp).
   - Kết luận `QA PASS` cho mã và fixture tại `33e8bb6` không tự động mở phát hành hay mở Pass 1.
5. **Điều chưa biết**:
   - Phương án và commit đồng bộ/migration gói dữ liệu hạn chế thật của Thành viên C theo phê duyệt của Lead D để khắc phục 4 điểm lệch giữa gói dữ liệu thật và hợp đồng mã nguồn `33e8bb6`.

---

## II. ĐỐI SOÁT COMMIT, DIFF VÀ MÃ BĂM HIỆN VẬT TẠI `33e8bb6c29c7ee15209ae5847d48aae973a3f536`

### 1. Xác minh Commit & Diff từ baseline `a12f90b4552456b716aca5ca1c0e443f5497584e`
- **Full Commit SHA trên `origin/feat/c-main-annotation-batch1`**: `33e8bb6c29c7ee15209ae5847d48aae973a3f536` (kế thừa qua `79a9478` từ `a12f90b4552456b716aca5ca1c0e443f5497584e`).
- **Tóm tắt `git diff --stat a12f90b4552456b716aca5ca1c0e443f5497584e 33e8bb6c29c7ee15209ae5847d48aae973a3f536`**:
  - Thay đổi 9 tệp (`344 insertions(+), 24 deletions(-)`), trong đó các thay đổi chức năng và SOP gồm:
    1. `scripts/data/receive_main_batch1.py`: Trong `_check_accepted_history`, khóa cứng bản nộp đã `accepted` đối với mọi input digest khác (không cho phép chuỗi `d_replacement_approval` tùy ý mở khóa; ghi rõ tính năng thay thế bản nộp chưa hỗ trợ tự động và cần quyết định riêng của Lead D); đồng thời bổ sung tham số `--d-replacement-approval` vào CLI `argparse` của `main()` và truyền vào `receive_main_batch1` để đồng bộ giao diện CLI/API.
    2. `docs/QUY_TRINH_KIEM_TRA_INTAKE_MAIN_BATCH1.md`: Cập nhật mô tả khóa vĩnh viễn bản nộp `accepted` đối với input digest khác; sửa khối mã Python tính Kappa 3×3: (i) quét cả `.receipt.json` và `.attempt_*.json` để tìm bản `accepted` duy nhất cho từng annotator và dừng với `RuntimeError` nếu tồn tại nhiều digest `accepted` chưa xác định hiệu lực; (ii) kiểm tra mã băm SHA-256 của `blind_view_b.json` so với `manifest_b.json` và mã băm tệp JSONL đã lưu so với `file_sha256` trong biên lai; (iii) kiểm tra tập B30 có đúng 30 `sample_id`; (iv) đặt `bootstrap_iterations=1000`, `random_seed=2026`; và (v) xuất báo cáo qua hàm chuẩn `format_kappa_3x3_report(result)`.
    3. `artifacts/lead_d_review_a12f90b/test_main_a12_approval_and_sop.py`: Lưu trữ nguyên byte tệp 4 probe kiểm quyền thay thế và SOP Kappa của Lead D.
    4. `artifacts/isolation_verification_report.json`: Cập nhật `total_tracked_files` từ `234` lên `240` (`violations_count: 0`, `status: "PASS"`).

### 2. Bảng mã băm SHA-256 của 22 tệp mã nguồn, tài liệu và bộ kiểm thử tại commit `33e8bb6`

*(Đo trực tiếp trên Git blob chuẩn LF tại commit `33e8bb6c29c7ee15209ae5847d48aae973a3f536`)*

| Đường dẫn tệp trong repository | Dung lượng (LF) | SHA-256 đo trực tiếp | Ghi chú đối chiếu |
| :--- | :---: | :--- | :--- |
| `src/phishing/annotation/blind_view.py` | `49.367 bytes` | `b32e4a585032550913249fee57819f421eff296132816e1e5995d54e031b705b` | Hợp đồng Blind View `1.2.0` & legacy |
| `src/phishing/data/lot_ledger.py` | `9.854 bytes` | `52c1d475a07ec624259ac8e2bc28437adcd0e465a4bd4c54b4dd8b0953029a6f` | Sổ phân bổ lô append-only |
| `src/phishing/data/main_sampling.py` | `27.153 bytes` | `aa142b63a8c657382cdf786c5468974ef1ecd9f76494598292aa27ec3fc09cda` | Sampling A100/B30, fingerprint & supersede |
| `scripts/annotate_cli.py` | `56.803 bytes` | `2d4f32657daa44a46073809d3249f766a3d3a7d48abb8999602dad170e49b710` | CLI gán nhãn, timer pause/resume |
| `scripts/data/export_and_seal_population.py` | `4.736 bytes` | `2746f8393e731dfd6c7d0234a66454ee58ade8297c58a50025cbf6654d16b1b0` | Gắn `source_row` trước Gates & niêm phong |
| `scripts/data/receive_main_batch1.py` | `19.728 bytes` | `6f790e1be14d6068fe40e839b3e52190f6037cf13f06c019b0fc5fd87e480358` | Intake Main Batch 1 & khóa lịch sử biên lai |
| `scripts/data/run_main_batch1_pipeline.py` | `14.960 bytes` | `68af824a9477bc81ee57a24d96133f689a9282d0aaa79a3f1dfda5ec66ea51ce` | Exporter, staging & rollback bảo toàn gói cũ |
| `scripts/data/verify_git_isolation.py` | `9.870 bytes` | `cdea7216f2e2204c8711726ebb6b76befaeb9622bf14b895a343b4df440f887d` | Quét cách ly Git & redact secret |
| `docs/HUONG_DAN_CLI_MAIN_BATCH1.md` | `3.404 bytes` | `b09af927c76a3905c6733b4f04209e8bab679a70de983f37b97998be16be3168` | Hướng dẫn thao tác CLI Main Batch 1 |
| `docs/QUY_TRINH_KIEM_TRA_INTAKE_MAIN_BATCH1.md` | `8.344 bytes` | `26cc86d27f4319d014d1abb7bfc00e7be15cc2f7f880220410d7c18ed03c3482` | SOP Intake & kịch bản Python Kappa 3×3 |
| `docs/BAO_CAO_BAN_GIAO_MAIN_ANNOTATION_DOT_1_C.md` | `9.447 bytes` | `0d12df02e89863b0b0846a6ecc581c67232220e3c1d75b0b82315f1ef69682fa` | Báo cáo kỹ thuật của Thành viên C |
| `artifacts/INCIDENT_LOG_20261119_MAIN_BATCH1_SALT_EXPOSURE.md` | `6.897 bytes` | `f0ac150ed22ab79d450669fcb8e400e3202818dc44474b05850467afc893c980` | Báo cáo sự cố lộ default salt/seed |
| `artifacts/main_batch1_release_manifest.json` | `1.377 bytes` | `7f40d94dcd7ff80500a3fcb16e5e1ab3fb8cde95f9f21d9b92df5291211945a8` | Release manifest công khai |
| `artifacts/isolation_verification_report.json` | `2.084 bytes` | `5c6e98f52ea7f9690bc8361b725a8e93d521649a651b05e3c02248b9ac7fe3a1` | Báo cáo quét cách ly (`240` tracked files) |
| `tests/test_main_annotation_batch1.py` | `42.039 bytes` | `b6ff5fdfd5327558a6833c1d12c19a4676dd52229790d9b2eabaff571a059486` | Tệp kiểm thử số 1 trong 8 tệp chọn lọc |
| `tests/test_blind_view.py` | `121.243 bytes` | `31f22b590b5d01ccc784a1468cd35a4d340d46522848a91c8373c11183505160` | Tệp kiểm thử số 2 trong 8 tệp chọn lọc |
| `tests/test_annotate_cli_timer_pause.py` | `23.329 bytes` | `9dd72dd792e05bfb91e3c8775d448b77952a371f33727b92a0379397e5bf8728` | Tệp kiểm thử số 3 trong 8 tệp chọn lọc |
| `artifacts/lead_d_review_8fc845d/test_main_8fc_additional_guards.py` | `4.949 bytes` | `b7f5c37902032701f7aa009024a4c079c800c2321a964a29480fd6ae41e8410a` | Tệp số 4 — **Khớp nguyên byte bản D gốc** |
| `artifacts/lead_d_review_6c26d74/test_main_6c26_release_boundaries.py` | `7.659 bytes` | `4f117730fe811401e2132c50458dbad576a14c9e8fad22988f50099882cbb63d` | Tệp số 5 — **Khớp nguyên byte bản D gốc** |
| `artifacts/lead_d_review_599c7d9/test_main_599_followup.py` | `6.210 bytes` | `da4b89eb038412f2860071311e3e8e18c67bca94c6aa214203f8d2a6369254a6` | Tệp số 6 — **Khớp nguyên byte bản D gốc** |
| `artifacts/lead_d_review_da3a78d/test_main_da3_intake_history.py` | `2.770 bytes` | `514f39e734e666d272a55473ed5fe41700683fa7e33f5ceca80283bcde320605` | Tệp số 7 — **Khớp nguyên byte bản D gốc** |
| `artifacts/lead_d_review_a12f90b/test_main_a12_approval_and_sop.py` | `2.715 bytes` | `200a273bb83d13835e08ee84c42072b618578d2bd1ab1dcf07b2ffcfc29e6e87` | Tệp số 8 — **Khớp nguyên byte bản D gốc** |

- **Ghi chú về gói `MAIN_BATCH1_33E8BB6_EVIDENCE_FOR_B.zip` (`9.397 bytes`, SHA-256: `f547b2447cca0190bc99fed63f533e6639e94cf10a28efce1fcddb50a16bc543`)**: Gói ZIP bằng chứng chạy máy C này đã được Lead D trực tiếp đối soát kích thước, mã băm và bảng kê (C ghi nhận `154 passed in 49.51s`, D tái lập `154 passed in 4.58s`). Do tệp ZIP rời này không đính kèm trực tiếp vào thư mục tải lên của máy B trong lượt này, B ghi nhận thông số gói ZIP này theo **bằng chứng đối chiếu của Lead D**, đồng thời B trực tiếp kiểm chứng toàn bộ 22 tệp thật trên Git commit `33e8bb6c29c7ee15209ae5847d48aae973a3f536` và tự chạy độc lập toàn bộ 8 tệp kiểm thử (154 phép kiểm) trên máy B.

---

## III. KẾT QUẢ KIỂM THỬ THỰC NGHIỆM ĐỘC LẬP CỦA B TẠI COMMIT `33e8bb6c29c7ee15209ae5847d48aae973a3f536`

- **Môi trường kiểm thử độc lập của B**:
  - Hệ điều hành: Windows 11 (`win32`)
  - Python: `3.14.2` (`pytest-9.1.1`, `pluggy-1.6.0`, `anyio-4.14.2`)
  - Checkout kiểm định: Git worktree tách biệt `scratch/33e8bb6_wt` tại đúng commit `33e8bb6c29c7ee15209ae5847d48aae973a3f536` (đã dọn sạch sau khi hoàn tất kiểm thử; không chạm `src/`, `scripts/`, `tests/`).

### 1. Tái lập 8 tệp kiểm thử chọn lọc (154 phép kiểm)
- **Lệnh thực thi**:
  ```powershell
  $env:PYTHONPATH=".;src"
  python -m pytest tests/test_main_annotation_batch1.py tests/test_blind_view.py tests/test_annotate_cli_timer_pause.py artifacts/lead_d_review_8fc845d/test_main_8fc_additional_guards.py artifacts/lead_d_review_6c26d74/test_main_6c26_release_boundaries.py artifacts/lead_d_review_599c7d9/test_main_599_followup.py artifacts/lead_d_review_da3a78d/test_main_da3_intake_history.py artifacts/lead_d_review_a12f90b/test_main_a12_approval_and_sop.py -q
  ```
- **Raw log kết quả trên máy B (`pytest -q --no-header --tb=no`)**:
  ```text
  154 passed in 19.82s
  ```
- **Chỉ số tách riêng**: **`passed=154`**, **`failed=0`**, **`skipped=0`**, **`deselected=0`**, thời gian **`19.82s`** (so với mốc đối chiếu trên máy Lead D: `154 passed in 4.58s` và máy Thành viên C: `154 passed in 49.51s`; 4 probe trong `test_main_a12_approval_and_sop.py` đã nằm trong tổng số 154 phép kiểm của 8 tệp chọn lọc này).

### 2. Chạy kiểm tra cách ly Git (`verify_git_isolation.py`)
- **Lệnh thực thi**:
  ```powershell
  $env:PYTHONPATH=".;src"
  python scripts/data/verify_git_isolation.py
  ```
- **Raw log kết quả trên máy B**:
  ```text
  Git Isolation Status: PASS
  Report written to: artifacts\isolation_verification_report.json
  ```
- **Giới hạn kết luận**: Kết quả `PASS` của công cụ quét xác nhận các quy tắc kiểm tra `.gitignore`, tệp theo dõi trên Git (`240` tracked files) và mẫu chuỗi bí mật trong phạm vi quét đều đạt; không suy rộng từ kết quả scanner `PASS` thành kết luận không có mọi loại rò rỉ ngoài phạm vi quét.

### 3. Phép kiểm hành vi bổ sung bằng fixture tổng hợp (Theo Mục 3 Thông tin bổ sung của Lead D)
QA Lead B đã chạy kịch bản kiểm tra hành vi trực tiếp trên fixture tổng hợp tại `33e8bb6c29c7ee15209ae5847d48aae973a3f536` để đối chiếu các yêu cầu kỹ thuật liên quan đến những điểm lệch mà Lead D phát hiện trên gói dữ liệu thật:
- **Từ chối rõ ràng gói Blind View dạng danh sách trần (`bare list`)**:
  - Khi truyền một tệp JSON dạng `list` (`[{'sample_id': 'BLIND-0123abcd', 'url': 'https://a.test/'}]`) vào `scripts/annotate_cli.py` (`annotate_interactive_session`), CLI từ chối ngay với ngoại lệ rõ ràng:
    ```text
    ValueError: LỖI GÓI VIEW: Tệp đầu vào tại '.../bare_list_view.json' phải là một JSON envelope (dict) chứa metadata và trường 'samples'. Nhận: list. Vui lòng kiểm tra lại quá trình xuất gói.
    ```
- **Độ nhạy của `compute_population_fingerprint` khi giữ nguyên `candidate_uid`**:
  - Trên quần thể fixture 130 mẫu, khi giữ nguyên `candidate_uid` nhưng thay đổi lần lượt từng trường `url`, `html`, `source_row`, `source_shard`, hoặc `source_revision` ở 1 mẫu, mã băm `compute_population_fingerprint` đều thay đổi tương ứng (`fp_mut != fp_base`).
- **Bảo toàn provenance xuyên suốt `Quần thể → Sampling → Mapping → Đóng gói Envelope v1.2.0`**:
  - Chạy `export_main_batch1` trên quần thể fixture 130 mẫu tạo ra `blind_view_a.json` (envelope `dict`, `blind_contract_version == "1.2.0"`, 100 mẫu), `blind_view_b.json` (envelope `dict`, `blind_contract_version == "1.2.0"`, 30 mẫu), và `mapping_restricted.json` (danh sách 100 mục) trong đó cả 100 mục đều giữ đầy đủ `source_row`, `source_shard`, `source_revision`, `url_sha256`, `html_sha256`, `sample_content_hash` và `canonical_pop_index`.

### 4. Lượt chạy rộng toàn bộ `tests/` (Báo cáo phạm vi riêng)
- **Lệnh thực thi**:
  ```powershell
  $env:PYTHONPATH=".;src"
  python -m pytest tests/ --ignore=tests/test_translation_experiment.py -q
  ```
- **Chỉ số tách riêng**:
  - `passed`: **421**
  - `failed`: **6** (cả 6 ca tại `tests/test_real_calibration_split_isolation.py` do clean worktree không có các tệp hạn chế ngoài Git của đợt Calibration trước)
  - `skipped`: **38** (các test phụ thuộc hiện vật lịch sử đã cô lập; không cộng gộp vào `passed`)
  - `deselected`: **0** (tệp `tests/test_translation_experiment.py` được loại trừ tường minh qua `--ignore` do môi trường máy B không cài thư viện `transformers`)
  - `subtests passed`: **32** (ghi nhận riêng, không cộng vào số bài test độc lập)
  - Thời gian thực thi: **27.32s**.

---

## IV. ĐÁNH GIÁ CHI TIẾT BẢY CỔNG THỰC THI G1–G7 VÀ SÁU KẾT LUẬN TÁCH BIỆT

### 1. Bảng kết quả từng cổng G1–G7 tại commit `33e8bb6c29c7ee15209ae5847d48aae973a3f536`

| Cổng | Nội dung kiểm định & Bằng chứng thực nghiệm | Kết luận trên Mã & Fixture (`33e8bb6`) | Trạng thái trên Hiện vật hạn chế thật (Do D kiểm) |
| :---: | :--- | :---: | :---: |
| **G1 — E2E, Intake & Lịch sử bản nộp** | • Chuỗi thật `Exporter → Envelope → CLI thật → JSONL → Intake` chạy thông suốt trên fixture A100/B30.<br>• Chặn manifest `pending`/`ready=false`, sai người, sai pass, sai tập ID, trùng/thiếu mẫu, cờ `is_dry_run`/`is_synthetic` sai kiểu hoặc bằng `True`, thiếu/sai provenance hoặc `timestamp_utc`.<br>• Quét cả `.receipt.json` và `.attempt_*.json` để khóa bản nộp đã `accepted`; mọi input digest khác cho cùng annotator/release đều bị từ chối kể cả khi truyền chuỗi bất kỳ vào `d_replacement_approval` (chưa hỗ trợ thay thế tự động).<br>• Context khác tạo attempt riêng, giữ nguyên byte biên lai cũ; bản `rejected` không làm mất dấu `accepted` ở attempt lịch sử. | **`PASS`** | **`PENDING`** (Chờ phát hành gói thật hợp lệ) |
| **G2 — Hợp đồng Main `1.2.0` & Tương thích Legacy** | • Bắt buộc đồng nhất `blind_contract_version="1.2.0"` và `codebook_version="1.1.0"` xuyên suốt envelope, sample và record.<br>• Chặn thiếu/sai/unknown/mixed version và chặn hạ cấp Main (`BLIND-xxxxxxxx`) xuống legacy; từ chối rõ ràng tệp view dạng `bare list`.<br>• Toàn bộ các bài test hồi quy cho gói legacy (`v1.0`/`v1.1`) đều đạt. | **`PASS`** | **`HOLD / FAIL (D phát hiện)`** (Hai view thật C xuất trước đó còn là `bare list`, cần C xuất lại theo đúng exporter `33e8bb6`) |
| **G3 — Tính mù (Blindness)** | • Gói Main `1.2.0` và bản ghi Main không chứa `random_subset`, cờ phân tầng hay metadata nguồn bị cấm ở cả cấp đầu lẫn cấu trúc lồng nhau.<br>• Chặn nhãn nguồn, locator, matcher và điểm mô hình trong gói người gán. | **`PASS`** | **`PENDING (D đối soát khi C xuất lại gói thật)`** |
| **G4 — Fingerprint & Provenance** | • `compute_population_fingerprint` thay đổi khi URL, HTML, `source_row`, `source_shard` hoặc `source_revision` thay đổi dù giữ nguyên `candidate_uid`.<br>• `export_and_seal_population.py` gắn `source_row` trước lọc Gates và giữ nguyên qua sampling/mapping/đóng gói; chặn khi thiếu `source_row`. | **`PASS` (trên mã & fixture)** | **`HOLD / FAIL (D phát hiện)`** (Mapping thật đang thiếu `source_row` ở 100 dòng; cam kết quần thể gói thật dùng thuật toán UID-only cũ) |
| **G5 — Sampling, Ledger & Supersede** | • Không chọn lại mẫu đã phân bổ cho lô khác; chạy lại cùng lô giữ nguyên cohort và B30 đã niêm phong; thiếu seed bắt buộc dừng fail-closed.<br>• Supersede kiểm đủ A100/B30 duy nhất và quan hệ tập con ($B_{30} \subset A_{100}$); dừng khi ledger thiếu dữ liệu B30 hoặc thiếu seed metadata; rerun sau supersede kiểm đúng cam kết active release và chặn khi đổi seed. | **`PASS` (trên mã & fixture)** | **`HOLD / FAIL (D phát hiện)`** (Ledger thật đang thiếu dữ liệu tập B30 phục vụ rerun; chờ phương án migration được D duyệt) |
| **G6 — Isolation & Khóa phát hành (Publish)** | • Phát hiện secret hardcoded mới, dừng khi thiếu private input hoặc lỗi đọc tệp, và che (redact) giá trị secret trong báo cáo JSON công khai.<br>• Mọi lần quét `verify_git_isolation` trả về `FAIL` (kể cả lần cuối) đều chặn `SUCCESS`.<br>• Khi lỗi trước publish, lỗi I/O giữa lúc thay tệp hoặc hậu kiểm `FAIL`, khôi phục nguyên byte toàn bộ gói hạn chế, manifest công khai và ledger cũ. | **`PASS`** | **`PENDING (D đối soát khi C đồng bộ gói thật)`** |
| **G7 — SOP, CLI & Kappa 3×3** | • Cờ `--d-replacement-approval` đã có trong parser `receive_main_batch1.py --help` và SOP ghi đúng trạng thái khóa thay thế tự động.<br>• Chạy nguyên văn đoạn mã Python trong `docs/QUY_TRINH_KIEM_TRA_INTAKE_MAIN_BATCH1.md` trên dữ liệu fixture `accepted`: kiểm hash JSONL và Blind View B, chặn khi có nhiều digest `accepted` chưa xác định hiệu lực, ghép đúng 30 mẫu B30 đã khóa, chạy `bootstrap_iterations=1000`, `random_seed=2026` và xuất báo cáo qua `format_kappa_3x3_report(result)`. | **`PASS`** | **`PENDING`** (Chỉ chạy trên kết quả thật sau khi kết thúc Pass 1) |

### 2. Sáu kết luận tách biệt (Theo Mục 5 & Mục 8 chỉ đạo của Lead D)

1. **Về chức năng (Functional Pipeline)**: Trên mã nguồn và fixture tổng hợp tại commit `33e8bb6c29c7ee15209ae5847d48aae973a3f536`, toàn bộ chuỗi chức năng từ niêm phong quần thể, rút mẫu A100/B30, ghi ledger, xuất gói envelope `1.2.0`, chạy CLI tương tác thật, tiếp nhận intake, khóa lịch sử biên lai/attempt đến chạy nguyên văn đoạn mã SOP tính Cohen's Kappa 3×3 (`B=1000`, `seed=2026`) đều hoạt động đúng đặc tả (**`154 passed`** trong 8 tệp kiểm thử chọn lọc).
2. **Về tương thích Legacy (Legacy Compatibility)**: Các luồng và gói dữ liệu legacy được phép (`v1.0`/`v1.1`, Pilot/Calibration) giữ nguyên tính tương thích hồi quy, đồng thời bị tách biệt nghiêm ngặt không cho phép dùng để hạ cấp hoặc vượt rào kiểm tra của hợp đồng Main `1.2.0`.
3. **Về tính mù (Blindness Preservation)**: Mã nguồn và hợp đồng Main `1.2.0` đã loại bỏ và chặn `random_subset` (kể cả lồng nhau), nhãn nguồn, điểm mô hình và locator trong gói phát cho người gán. Trong suốt quá trình QA, Thành viên B chỉ tiếp cận mã công khai, đặc tả và fixture tổng hợp; không mở hoặc nhận bất kỳ hiện vật hạn chế thật nào, bảo toàn tính mù của Annotator B.
4. **Về xuất xứ dữ liệu (Provenance)**: Ở tầng mã nguồn và fixture tại `33e8bb6`, các trường `source_row`, `source_shard`, `source_revision`, mã băm nội dung và provenance bản ghi đã được bắt buộc và bảo toàn xuyên suốt. Tuy nhiên, theo phát hiện kiểm trực tiếp của Lead D trên hiện vật hạn chế thật, gói dữ liệu thật C bàn giao trước đó còn thiếu `source_row` ở 100 dòng mapping và dùng fingerprint UID-only cũ, nên phần provenance trên hiện vật hạn chế thật đang ở trạng thái **`HOLD / CHỜ C ĐỒNG BỘ & D ĐỐI SOÁT`**.
5. **Về tính bất biến của Cohort và Hiện vật (Cohort & Artifact Immutability)**: Ở tầng mã nguồn và fixture tại `33e8bb6`, cơ chế giữ nguyên cohort khi rerun, chống ghi đè biên lai lịch sử và rollback bảo toàn byte hiện vật cũ khi lỗi I/O hoặc isolation `FAIL` đã đạt kiểm thử. Riêng trên hiện vật hạn chế thật, do ledger thật đang thiếu dữ liệu tập B30 phục vụ rerun và view thật còn ở dạng bare list (theo phát hiện của Lead D), Thành viên C cần thực hiện phương án đồng bộ/migration theo đúng chỉ đạo của Lead D mà không làm thay đổi ngầm danh tính nguồn của cohort đã rút nếu Lead D quyết định bảo lưu cohort.
6. **Về điều kiện phát hành (Release Readiness)**: **“QA kỹ thuật trên mã và fixture tại commit 33e8bb6 đạt”**. Tuy nhiên, đây là điều kiện đủ về mặt mã nguồn và SOP trên fixture, **chưa phải nghiệm thu nội dung gói dữ liệu Main thật**. Gói Main Annotation Đợt 1 tiếp tục giữ trạng thái **`HOLD / LOCKED`** cho đến khi Thành viên C đồng bộ gói dữ liệu hạn chế thật khớp với hợp đồng mã nguồn `33e8bb6`,(nếu có thêm mã migration cho ledger/gói cũ thì B sẽ kiểm bổ sung cơ chế migration đó bằng fixture), và được Lead D kiểm chứng byte/provenance gói thật cũng như ra lệnh mở phiên riêng.

---

## V. BÁO CÁO BÀN GIAO CHUẨN 10 MỤC (THEO MỤC 6 `AGENTS.md` / `AI_WORK_RULES.md`)

- **Mục tiêu và phạm vi**:
  - Thực hiện đợt QA độc lập gộp cho Main Annotation Batch 1 tại commit `33e8bb6c29c7ee15209ae5847d48aae973a3f536` (nhánh `origin/feat/c-main-annotation-batch1`).
  - Kiểm tra toàn bộ 7 cổng **G1–G7**, tái lập 8 tệp kiểm thử chọn lọc (`154 passed`), chạy `verify_git_isolation.py`, kiểm hành vi bổ sung trên fixture tổng hợp và chạy riêng lượt kiểm rộng toàn repo.
  - Phân định rõ kết luận **`PASS` cho mã nguồn, SOP và fixture tại commit `33e8bb6`** với trạng thái **`HOLD / PENDING` của gói dữ liệu hạn chế thật** (theo 4 phát hiện trực tiếp của Lead D trên hiện vật hạn chế).
- **Người thực hiện / người kiểm độc lập**:
  - Người thực hiện mã nguồn & SOP tại commit `33e8bb6`: Nguyễn Thắng (Thành viên C — Data Pipeline & Thư ký).
  - Người kiểm định độc lập mã nguồn, SOP & fixture tổng hợp: Phùng Tấn Minh (Thành viên B — Annotator B kiêm QA Lead & Nhóm trưởng).
  - Người kiểm định trực tiếp gói dữ liệu hạn chế thật & phê duyệt phát hành: Lead D (Anh Tuấn).
- **AI đã dùng**:
  - AI hỗ trợ xác minh commit và `git diff` trên remote, tính mã băm SHA-256 của 22 tệp trên Git tree `33e8bb6`, chạy pytest trên clean Git worktree tạm `scratch/33e8bb6_wt` (sau đó xóa worktree) và lập báo cáo QA gộp V1.6.
  - Không dùng AI cho dữ liệu hạn chế, quần thể thật, mapping thật, seed/salt thật, Blind View A hay nhãn nguồn.
- **Đầu vào đã khóa**:
  - Repository: `https://github.com/Anhtuann1404/NCKH_2`, nhánh `origin/feat/c-main-annotation-batch1`, full commit SHA: `33e8bb6c29c7ee15209ae5847d48aae973a3f536`.
  - 5 tệp probe chuẩn của Lead D trong repo tại `33e8bb6` khớp nguyên byte bản gốc của Lead D (`test_main_8fc_additional_guards.py`: `b7f5c379...`; `test_main_6c26_release_boundaries.py`: `4f117730...`; `test_main_599_followup.py`: `da4b89eb...`; `test_main_da3_intake_history.py`: `514f39e7...`; `test_main_a12_approval_and_sop.py`: `200a273b...`).
  - Thông số gói `MAIN_BATCH1_33E8BB6_EVIDENCE_FOR_B.zip` (`9.397 bytes` | SHA-256: `f547b2447cca0190bc99fed63f533e6639e94cf10a28efce1fcddb50a16bc543`) và 4 phát hiện trên gói dữ liệu hạn chế thật được ghi nhận theo văn bản đối chiếu của Lead D.
  - Các văn bản QA lịch sử của B được giữ nguyên byte: V1.5 (`29.287 bytes` | `016b537a...`), V1.4 (`34.343 bytes` | `f1031f64...`), V1.3 (`30.791 bytes` | `06cc07fc...`), V1.2 (`16.337 bytes` | `660fe800...`), V1.1 (`17.587 bytes` | `a574026b...`), V1.0 (`13.100 bytes` | `de51db19...`), Phụ lục `02fca4f` (`16.721 bytes` | `42e5389e...`).
- **Thay đổi thực tế**:
  - Phát hành văn bản QA gộp do B đứng tên: `docs/QA_REPORT_MAIN_BATCH1_33E8BB6_CONSOLIDATED_V1_6_B.md`.
  - Không sửa bất kỳ tệp mã nguồn, script, test hay tài liệu nào của Thành viên C.
- **Tự kiểm**:
  - Kiểm tra trực tiếp mã băm SHA-256 của 22 tệp mã nguồn, SOP, manifest công khai và tệp test tại commit `33e8bb6c29c7ee15209ae5847d48aae973a3f536`.
  - Kiểm tra bảo toàn nguyên byte toàn bộ các văn bản QA lịch sử của B.
- **Kiểm thử (Thực thi độc lập trên clean worktree `33e8bb6c29c7ee15209ae5847d48aae973a3f536`)**:
  - Môi trường: Windows 11, Python 3.14.2, pytest-9.1.1, pluggy-1.6.0.
  - Lượt 1 (8 tệp kiểm thử chọn lọc):
    - Lệnh: `$env:PYTHONPATH=".;src"; python -m pytest tests/test_main_annotation_batch1.py tests/test_blind_view.py tests/test_annotate_cli_timer_pause.py artifacts/lead_d_review_8fc845d/test_main_8fc_additional_guards.py artifacts/lead_d_review_6c26d74/test_main_6c26_release_boundaries.py artifacts/lead_d_review_599c7d9/test_main_599_followup.py artifacts/lead_d_review_da3a78d/test_main_da3_intake_history.py artifacts/lead_d_review_a12f90b/test_main_a12_approval_and_sop.py -q`
    - Kết quả: **`passed=154`**, **`failed=0`**, **`skipped=0`**, **`deselected=0`** trong **`19.82s`** (154 phép kiểm thuộc 8 tệp chọn lọc, không gọi là toàn bộ repository).
  - Lượt 2 (Kiểm tra cách ly Git):
    - Lệnh: `$env:PYTHONPATH=".;src"; python scripts/data/verify_git_isolation.py`
    - Kết quả: **`Git Isolation Status: PASS`** (`240` tracked files, `0` violations).
  - Lượt 3 (Kiểm hành vi bổ sung trên fixture tổng hợp):
    - Xác nhận CLI `annotate_interactive_session` từ chối `bare list` với `ValueError`; `compute_population_fingerprint` đổi hash khi giữ nguyên UID nhưng đổi `url`, `html`, `source_row`, `source_shard` hoặc `source_revision`; `export_main_batch1` xuất đúng envelope `1.2.0` (A=100, B=30) và giữ đủ `source_row`/`source_shard`/`source_revision`/`sample_content_hash` trên cả 100 mục mapping.
  - Lượt 4 (Lượt chạy rộng toàn bộ `tests/` bỏ qua `test_translation_experiment.py` do thiếu `transformers` — phạm vi riêng):
    - Lệnh: `$env:PYTHONPATH=".;src"; python -m pytest tests/ --ignore=tests/test_translation_experiment.py -q`
    - Kết quả tách riêng: **`passed=421`**, **`failed=6`** (tại `test_real_calibration_split_isolation.py` do thiếu tệp hạn chế ngoài Git), **`skipped=38`** (không cộng vào `passed`), **`deselected=0`**, **`subtests passed=32`** (ghi riêng) trong **`27.32s`**.
- **QA độc lập**:
  - **Trên mã nguồn, SOP và fixture tổng hợp tại commit `33e8bb6c29c7ee15209ae5847d48aae973a3f536`**:
    - **G1 (E2E, Intake & Lịch sử bản nộp)**: **`PASS`**
    - **G2 (Hợp đồng Main `1.2.0` & Tương thích Legacy)**: **`PASS`**
    - **G3 (Tính mù)**: **`PASS`**
    - **G4 (Fingerprint & Provenance trên mã/fixture)**: **`PASS`**
    - **G5 (Sampling, Ledger & Supersede trên mã/fixture)**: **`PASS`**
    - **G6 (Isolation & Khóa phát hành)**: **`PASS`**
    - **G7 (SOP, CLI & Kappa 3×3)**: **`PASS`**
    - **Kết luận phạm vi mã & fixture**: **“QA kỹ thuật trên mã và fixture tại commit 33e8bb6 đạt”**.
  - **Trên gói dữ liệu hạn chế thật (theo kết quả kiểm trực tiếp của Lead D)**: **`HOLD / PENDING`** (chưa nghiệm thu nội dung gói Main thật do gói dữ liệu thật C xuất trước đó chưa đồng bộ với hợp đồng mã nguồn tại `33e8bb6`).
- **Giới hạn và việc còn mở**:
  - Phân biệt rõ 3 mức chứng cứ:
    1. *Trực tiếp kiểm được bởi B*: Mã nguồn, diff, 22 tệp trên Git commit `33e8bb6`, 154 phép kiểm trong 8 tệp chọn lọc, `verify_git_isolation.py`, kịch bản Python Kappa trong SOP và các phép kiểm fixture tổng hợp.
    2. *Chỉ đối chiếu qua báo cáo của Lead D/C*: Thông số tệp rời `MAIN_BATCH1_33E8BB6_EVIDENCE_FOR_B.zip` (`9.397 bytes`, SHA-256 `f547b244...`) và 4 điểm lệch trên gói dữ liệu hạn chế thật do Lead D trực tiếp kiểm tra.
    3. *Chưa kiểm được bởi B*: Nội dung byte của gói dữ liệu hạn chế thật (`blind_view_a.json`, `blind_view_b.json`, `mapping_restricted.json`, `population_1232_sealed.json`, ledger thật) nhằm bảo vệ tính mù của Annotator B, cùng cơ chế migration cho ledger/gói thật (chờ C triển khai theo phương án được Lead D phê duyệt).
  - Việc còn mở:
    - Thành viên C thực hiện đồng bộ/migration gói dữ liệu hạn chế thật theo phương án được Lead D duyệt để khớp với hợp đồng mã nguồn `33e8bb6` (envelope `1.2.0`, đủ `source_row` trong mapping, fingerprint đầy đủ, đủ dữ liệu B30 trong ledger). Nếu C có thay đổi/bổ sung mã cho bước migration, B sẽ kiểm tra cơ chế migration đó bằng fixture tổng hợp trên commit mới.
    - Lead D đối soát trực tiếp gói dữ liệu hạn chế thật sau khi C đồng bộ và ban hành quyết định mở phiên.
- **Trạng thái quản trị**:
  - Mã nguồn, SOP và fixture tại commit `33e8bb6c29c7ee15209ae5847d48aae973a3f536`: **`QA PASS (Phạm vi kỹ thuật trên mã và fixture)`**.
  - Gói dữ liệu Main Annotation Đợt 1: **`HOLD / LOCKED`** (Chờ C đồng bộ gói thật và Lead D đối soát).
  - Các cờ khóa quản trị hiện hành: `main_annotation_status="LOCKED"`, `training_blocked=true`, `official_test_used=false` (A và B chỉ bắt đầu Pass 1 khi có lệnh riêng của Lead D).
