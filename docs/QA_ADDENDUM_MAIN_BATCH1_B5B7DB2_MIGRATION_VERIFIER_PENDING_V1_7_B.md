# PHỤ LỤC THẨM ĐỊNH QA ĐỘC LẬP (PHIÊN BẢN V1.7): GHI NHẬN HIỆN TRẠNG COMMIT `b5b7db2`, BÀN GIAO HỒ SƠ GỐC V1.6 (`33e8bb6`) & KHÓA CỔNG KIỂM MIGRATION / VERIFIER FINGERPRINT (`PENDING`)

- **Mã tài liệu**: `QA-ADDENDUM-MAIN-BATCH1-B5B7DB2-MIGRATION-VERIFIER-PENDING-V1-7-B`
- **Phiên bản**: `1.7 (Addendum & Migration/Verifier Gate Specification)` — Ghi nhận kết quả đối chiếu commit `b5b7db2900fefd142c211fb2045a3e2bf3272298` (chỉ đổi `artifacts/main_batch1_release_manifest.json`, giữ nguyên mã và test từ `33e8bb6c29c7ee15209ae5847d48aae973a3f536`), bàn giao nguyên byte báo cáo QA V1.6 gốc cùng tệp raw log thực thi tại `33e8bb6` để Thành viên C lưu hồ sơ, và khóa danh mục kiểm thử trên fixture tổng hợp cho **Phương án Migration Ledger** cùng **Verifier Fingerprint** (hiện ở trạng thái **`PENDING`** chờ Thành viên C bàn giao commit mã mới).
- **Hồ sơ QA V1.6 gốc và Raw Log bàn giao nguyên byte để C lưu trữ**:
  1. Báo cáo QA gộp V1.6 gốc (`33e8bb6`): `docs/QA_REPORT_MAIN_BATCH1_33E8BB6_CONSOLIDATED_V1_6_B.md` (**`37.162 bytes`** LF | SHA-256: **`bfeb73d97db47fdb6741ce47849254d4f3a9483120bd533a3cb0f357f8a41e09`**)
  2. Raw log thực thi tại `33e8bb6` của B: `docs/QA_RAW_LOG_MAIN_BATCH1_33E8BB6_B.txt` (**`10.920 bytes`** LF | SHA-256: **`29b452ff6b2debfd2826d3ac3f15678a7f07aff3b45012e53ff3462c17c30ee7`**)
- **Bảo toàn lịch sử kiểm toán (Audit Trail)**: Giữ nguyên byte của toàn bộ các văn bản QA trước (V1.6: `37.162 bytes` | `bfeb73d9...`; V1.5: `29.287 bytes` | `016b537a...`; V1.4: `34.343 bytes` | `f1031f64...`; V1.3: `30.791 bytes` | `06cc07fc...`; V1.2: `16.337 bytes` | `660fe800...`; V1.1: `17.587 bytes` | `a574026b...`; V1.0: `13.100 bytes` | `de51db19...`; Phụ lục `02fca4f`: `16.721 bytes` | `42e5389e...`).
- **Ngày phát hành**: `2026-11-22`
- **Người thực hiện**: Phùng Tấn Minh (**Thành viên B — Annotator B kiêm QA Lead & Nhóm trưởng**)
- **Người nhận**: **Lead D** (Anh Tuấn) và **Thành viên C** (Nguyễn Thắng)
- **Trạng thái kết luận QA hiện hành theo từng phạm vi**:
  1. **QA kỹ thuật trên mã nguồn, SOP và fixture tổng hợp tại commit `33e8bb6c29c7ee15209ae5847d48aae973a3f536` (kế thừa nguyên trạng tại `b5b7db2900fefd142c211fb2045a3e2bf3272298`)**: **`PASS`** (`154 passed in 19.82s` trong 8 tệp kiểm thử chọn lọc; không cần chạy lại 154 test chỉ vì release manifest thay đổi).
  2. **QA phương án Migration Ledger và Verifier Fingerprint trên fixture tổng hợp**: **`PENDING`** (Chưa nhận commit mã migration/verifier mới từ Thành viên C; không ký trước).
  3. **Gói dữ liệu hạn chế thật V2 và áp dụng Migration lên Ledger thật**: **`HOLD / PENDING (Do Lead D kiểm chứng trực tiếp và phê duyệt)`**.
- **Trạng thái cổng quản trị hiện hành**: `main_annotation_status="LOCKED"`, `training_blocked=true`, `official_test_used=false` (Tiếp tục giữ đóng).

---

## I. XÁC ĐỊNH NHIỆM VỤ TRƯỚC KHI LÀM (THEO MỤC 1 `AGENTS.md`)

1. **Mục tiêu**:
   - Xác minh commit `b5b7db2900fefd142c211fb2045a3e2bf3272298` trên nhánh `origin/feat/c-main-annotation-batch1` so với commit đã QA `33e8bb6c29c7ee15209ae5847d48aae973a3f536`; bảo lưu nguyên trạng kết quả 154 phép kiểm đã đạt tại `33e8bb6` mà không chạy lại chỉ vì `main_batch1_release_manifest.json` thay đổi.
   - Bàn giao nguyên byte báo cáo QA V1.6 gốc (`docs/QA_REPORT_MAIN_BATCH1_33E8BB6_CONSOLIDATED_V1_6_B.md`) và tệp raw log thực thi (`docs/QA_RAW_LOG_MAIN_BATCH1_33E8BB6_B.txt`) để Thành viên C lưu hồ sơ.
   - Ghi nhận trạng thái **`PENDING`** đối với phần QA mã Migration Ledger và Verifier Fingerprint, đồng thời khóa bộ tiêu chí kiểm thử bằng fixture tổng hợp (tách rõ kiểm chẩn đoán tái lập lỗi cấu trúc block sparse hiện tại với kiểm nghiệm thu bản sửa) để thực thi ngay khi C bàn giao commit mã mới.
2. **Đầu vào được phép**:
   - Chỉ đạo của Lead D ngày 22/11/2026 về kết quả kiểm gói dữ liệu thật V2 và yêu cầu QA đối với migration/verifier.
   - Git commit `33e8bb6c29c7ee15209ae5847d48aae973a3f536` và `b5b7db2900fefd142c211fb2045a3e2bf3272298` trên nhánh `origin/feat/c-main-annotation-batch1`.
   - **Bảo vệ tính mù**: B không nhận quần thể thật, mapping thật, seed/salt thật, nhãn nguồn hoặc Blind View A để làm QA; các nhận định về hiện vật thật V2 được ghi rõ là kết quả do Lead D kiểm trực tiếp.
3. **Đầu ra và tiêu chí đạt**:
   - Phụ lục `docs/QA_ADDENDUM_MAIN_BATCH1_B5B7DB2_MIGRATION_VERIFIER_PENDING_V1_7_B.md` kèm tệp raw log `docs/QA_RAW_LOG_MAIN_BATCH1_33E8BB6_B.txt` và văn bản bàn giao chuẩn 10 mục.
4. **Ranh giới**:
   - B không sửa mã của C rồi tự ký QA cho phần mình sửa; không ký trước khi C bàn giao mã migration/verifier mới; không tự cấp quyền migration thật hoặc mở Pass 1 (chờ quyết định riêng của Lead D).
5. **Điều chưa biết**:
   - Full commit SHA của bản mã migration và verifier fingerprint mới từ Thành viên C (hiện trên remote `origin/feat/c-main-annotation-batch1` vẫn đang ở `b5b7db2900fefd142c211fb2045a3e2bf3272298`).

---

## II. ĐỐI SOÁT COMMIT `b5b7db2900fefd142c211fb2045a3e2bf3272298` & HIỆN TRẠNG GÓI THẬT V2 (DO LEAD D KIỂM)

### 1. Kiểm tra `git diff` giữa `33e8bb6` và `b5b7db2`
- Lệnh kiểm tra:
  ```powershell
  git diff --stat 33e8bb6c29c7ee15209ae5847d48aae973a3f536 b5b7db2900fefd142c211fb2045a3e2bf3272298
  ```
- Kết quả:
  - Chỉ có đúng **1 tệp thay đổi**: `artifacts/main_batch1_release_manifest.json` (`1 file changed, 8 insertions(+), 7 deletions(-)`).
  - Toàn bộ mã nguồn (`src/`, `scripts/`), tài liệu SOP (`docs/`) và 8 tệp kiểm thử (`tests/`, `artifacts/lead_d_review_*/`) **không thay đổi byte nào** so với commit `33e8bb6c29c7ee15209ae5847d48aae973a3f536`.
  - Theo đúng Mục 2 chỉ đạo của Lead D, QA Lead B giữ nguyên kết luận **`PASS` cho phạm vi QA kỹ thuật trên mã nguồn, SOP và fixture tại `33e8bb6c29c7ee15209ae5847d48aae973a3f536`** và không chạy lại 154 phép kiểm chỉ vì release manifest thay đổi.

### 2. Ghi nhận thông tin gói dữ liệu thật V2 (Theo kết quả kiểm trực tiếp của Lead D — B không trực tiếp kiểm)
Theo thông báo của Lead D sau khi kiểm trực tiếp gói dữ liệu hạn chế thật V2 của Thành viên C:
- Envelope của hai tệp Blind View thật đã được sửa, cohort và thứ tự A100 / B30 được giữ nguyên.
- Tuy nhiên, gói dữ liệu thật và hồ sơ đi kèm vẫn còn 3 điểm chưa hoàn tất:
  1. Hồ sơ quần thể (`population_1232_sealed.json`) vẫn thiếu danh sách `1.232` bản ghi metadata chuẩn hóa như báo cáo của C mô tả.
  2. Đầu vào và log kiểm loại trừ chưa đủ thông tin để Lead D tái lập độc lập.
  3. Phương án thêm block kế nhiệm dạng thưa (sparse successor block) chưa tương thích với cơ chế nạp `LotManagementLedger.get_active_lot_details()` hiện hành và chưa được Lead D phê duyệt áp dụng lên ledger thật.

---

## III. CHẨN ĐOÁN KỸ THUẬT TRÊN MÃ HIỆN HÀNH (`33e8bb6` / `b5b7db2`) & CỔNG KIỂM FIXTURE KHI C BÀN GIAO MÃ MỚI

Qua đọc mã nguồn hiện hành tại `src/phishing/data/lot_ledger.py` và `src/phishing/data/main_sampling.py` (commit `33e8bb6` / `b5b7db2`), QA Lead B ghi nhận nguyên nhân kỹ thuật ở tầng mã và khóa bộ tiêu chí kiểm thử bằng fixture tổng hợp cho lượt bàn giao mã migration/verifier sắp tới của C:

### 1. Cổng kiểm Phương án Migration Ledger bằng fixture tổng hợp (Mục 3 chỉ đạo D — Trạng thái hiện tại: `PENDING`)

- **Chẩn đoán trên mã hiện hành (`src/phishing/data/lot_ledger.py:229–234`)**:
  - Hàm `LotManagementLedger.get_active_lot_details(lot_id)` hiện chỉ duyệt ngược `reversed(self.events)` và trả về nguyên từ điển `ev.details` của sự kiện gần nhất có `status in ("RESERVED", "RELEASED", "COMPLETED")`.
  - Nếu một block kế nhiệm (migration/backfill event) chỉ ghi bổ sung các trường còn thiếu (cấu trúc *sparse*, ví dụ chỉ chứa `b_subset_candidate_ids` và `b_indices_in_lot100` mà không chứa hoặc không hợp nhất với `allocated_candidate_ids`, `population_hash`, `seed_commitment` từ block gốc), `get_active_lot_details(lot_id)` sẽ trả về từ điển thiếu `allocated_candidate_ids` / `seed_commitment`, làm hỏng đường rerun của `run_main_batch1_sampling` và `supersede_lot_sampling`.
- **7 tiêu chí bắt buộc B sẽ kiểm bằng fixture khi C bàn giao mã migration**:
  1. **Ca hồi quy chẩn đoán vs. Nghiệm thu bản sửa**: Tách rõ phép kiểm chẩn đoán (tái lập việc block sparse đơn thuần gây lỗi trên loader cũ) khỏi phép kiểm chứng minh phương án đã chỉnh của C hoạt động đúng; không sửa kỳ vọng của test để bỏ qua lỗi.
  2. **Hợp nhất/xác định đúng trạng thái hiệu lực**: Loader xác định đúng trạng thái hiệu lực của `lot_id` mà không làm mất bất kỳ dữ liệu nào đã niêm phong ở block gốc.
  3. **Đầy đủ trường bắt buộc cho sampler**: Trạng thái hiệu lực sau migration phải có đủ 100 `allocated_candidate_ids` duy nhất, đúng 30 mẫu `b_subset_candidate_ids` là tập con của 100 mẫu, `b_indices_in_lot100` và đầy đủ các cam kết (`population_hash`, `seed_commitment` / `cohort_seed_commitment`, `seed_lot_100`, `seed_b_subset_30`, `seed_release_shuffle`) mà sampler cần.
  4. **Bất biến lịch sử**: Hai block lịch sử đầu tiên (block `GENESIS` `seq=0` và block `RESERVED` gốc `seq=1`) phải giữ nguyên từng byte và mã băm (`event_hash`, `prev_hash`).
  5. **Bất biến khi Rerun**: Gọi lại `run_main_batch1_sampling` (rerun) sau khi migration phải trả về đúng cohort A100, đúng tập B30 và đúng thứ tự phát hành theo hợp đồng mà không rút lại mẫu mới.
  6. **Khớp thứ tự UID B và chỉ số B**: Kiểm tra bất biến `[allocated_candidate_ids[idx] for idx in b_indices_in_lot100] == b_subset_candidate_ids` theo đúng định nghĩa thứ tự.
  7. **Chống ghi lặp (Idempotency) & Fail-Closed khi dữ liệu lỗi**: Chạy lại bước migration trên ledger đã migrate không được append lặp block mới; nếu dữ liệu đầu vào thiếu, sai, không khớp hash hoặc mâu thuẫn (ví dụ B30 không thuộc A100, số lượng khác 100/30) thì phải dừng ngay (`ValueError` / `LedgerIntegrityError`), không tự chọn lại mẫu hoặc dùng fallback.

### 2. Cổng kiểm Verifier Fingerprint bằng fixture tổng hợp (Mục 4 chỉ đạo D — Trạng thái hiện tại: `PENDING`)

- **Chẩn đoán trên mã hiện hành (`src/phishing/data/main_sampling.py:52–91`)**:
  - Hàm `compute_population_fingerprint(candidates)` hiện tại đọc `raw_url = str(c.get("url", ""))` và `html_content = c.get("html") or ""`, sau đó tự tính `hashlib.sha256(html_content.encode("utf-8")).hexdigest()`.
  - Nếu truyền danh sách **canonical metadata records** (vốn lưu `url_raw`, `url_normalized`, `url_sha256`, `html_sha256` mà không lưu chuỗi `html` thô) vào hàm này, `c.get("html")` sẽ là `None` dẫn tới việc **băm chuỗi HTML rỗng `""`** và `c.get("url", "")` cũng rỗng!
- **6 tiêu chí bắt buộc B sẽ kiểm bằng fixture khi C bàn giao verifier fingerprint**:
  1. **Phân định rõ chế độ đầu vào**: Verifier phải xác định rõ ràng đang nhận `raw input` (bản ghi có `url`, `html`) hay `canonical metadata` (bản ghi 8 trường chuẩn hóa đã trích xuất hash).
  2. **Chặn lỗi băm HTML rỗng**: Khi đầu vào là `canonical metadata` chỉ cung cấp `html_sha256` (không có `html`), tuyệt đối không được băm chuỗi HTML rỗng `""` thay cho `html_sha256`.
  3. **Đồng nhất thuật toán 8 trường**: Đối chiếu đúng schema 8 trường (`candidate_uid`, `url_raw`, `url_normalized`, `url_sha256`, `html_sha256`, `source_shard`, `source_row`, `source_revision`), thứ tự sắp xếp canonical `key=lambda r: (r["url_normalized"], r["html_sha256"], r["candidate_uid"])`, tuần tự hóa `json.dumps(records, sort_keys=True, ensure_ascii=False)` và mã hóa UTF-8 để cùng một quần thể fixture khi tính từ `raw input` và khi tính từ `canonical metadata` phải cho ra **cùng một mã băm SHA-256 duy nhất**.
  4. **Độ nhạy và tính tất định**: Thay đổi bất kỳ trường nội dung hay xuất xứ nào trong 8 trường đều phải làm thay đổi fingerprint; cùng dữ liệu chuẩn hóa phải luôn cho kết quả tất định.
  5. **Fail-Closed khi thiếu trường hoặc hash không hợp lệ**: Thiếu bất kỳ trường bắt buộc nào trong 8 trường (như `source_row=None`, thiếu `html_sha256`, thiếu `url_normalized`), hoặc định dạng SHA-256 không hợp lệ (không phải 64 ký tự hex), hoặc `url_normalized` không khớp `normalize_url(url_raw)`, hoặc khi có cả `html` và `html_sha256` mà mã băm không khớp nhau đều phải ném lỗi rõ ràng (`ValueError`).
  6. **Tính độc lập của expected hash**: B tự tính mã băm kỳ vọng bằng công thức độc lập trên fixture để đối chiếu với kết quả của verifier; không lấy một chuỗi hash công bố sẵn của C làm expected duy nhất.

---

## IV. BÁO CÁO BÀN GIAO CHUẨN 10 MỤC (THEO MỤC 6 `AGENTS.md`)

- **Mục tiêu và phạm vi**:
  - Đối chiếu commit `b5b7db2900fefd142c211fb2045a3e2bf3272298` với commit đã QA `33e8bb6c29c7ee15209ae5847d48aae973a3f536` trên nhánh `origin/feat/c-main-annotation-batch1`; xác nhận chỉ thay đổi `artifacts/main_batch1_release_manifest.json` và giữ nguyên kết quả QA kỹ thuật trên mã/fixture tại `33e8bb6` (`154 passed`) mà không cần chạy lại test chỉ vì manifest thay đổi.
  - Bàn giao nguyên byte tệp báo cáo QA V1.6 gốc (`docs/QA_REPORT_MAIN_BATCH1_33E8BB6_CONSOLIDATED_V1_6_B.md`) và tệp raw log thực thi tại `33e8bb6` (`docs/QA_RAW_LOG_MAIN_BATCH1_33E8BB6_B.txt`) để Thành viên C lưu hồ sơ.
  - Ghi nhận trạng thái **`PENDING`** và khóa đặc tả kiểm thử trên fixture tổng hợp cho **Phương án Migration Ledger** và **Verifier Fingerprint** theo chỉ đạo của Lead D ngày 22/11/2026.
- **Người thực hiện / người kiểm độc lập**:
  - Người lập phụ lục QA V1.7 & bàn giao hồ sơ V1.6 gốc: Phùng Tấn Minh (Thành viên B — Annotator B kiêm QA Lead & Nhóm trưởng).
  - Người tiếp nhận lưu hồ sơ V1.6 & chuẩn bị mã migration/verifier mới: Nguyễn Thắng (Thành viên C — Data Pipeline & Thư ký).
  - Người kiểm định trực tiếp gói dữ liệu thật V2 & phê duyệt phương án migration/phát hành: Lead D (Anh Tuấn).
- **AI đã dùng**:
  - AI hỗ trợ kiểm tra `git diff` giữa `33e8bb6` và `b5b7db2`, đóng gói nguyên vẹn tệp raw log đã chạy tại `33e8bb6`, phân tích mã nguồn `lot_ledger.py` và `main_sampling.py` để lập đặc tả kiểm thử fixture cho migration/verifier trong phụ lục V1.7.
  - Không dùng AI cho dữ liệu hạn chế, quần thể thật, mapping thật, seed/salt thật, Blind View A hay nhãn nguồn.
- **Đầu vào đã khóa**:
  - Commit mã nguồn đã QA kỹ thuật: `33e8bb6c29c7ee15209ae5847d48aae973a3f536` (`origin/feat/c-main-annotation-batch1`).
  - Commit cập nhật manifest hiện hành: `b5b7db2900fefd142c211fb2045a3e2bf3272298` (`origin/feat/c-main-annotation-batch1`).
  - Hồ sơ QA V1.6 gốc bàn giao nguyên byte cho C lưu trữ:
    - `docs/QA_REPORT_MAIN_BATCH1_33E8BB6_CONSOLIDATED_V1_6_B.md` (`37.162 bytes` LF | SHA-256: `bfeb73d97db47fdb6741ce47849254d4f3a9483120bd533a3cb0f357f8a41e09`)
    - `docs/QA_RAW_LOG_MAIN_BATCH1_33E8BB6_B.txt` (`10.920 bytes` LF | SHA-256: `29b452ff6b2debfd2826d3ac3f15678a7f07aff3b45012e53ff3462c17c30ee7`)
  - Toàn bộ các văn bản QA lịch sử trước đó (V1.5, V1.4, V1.3, V1.2, V1.1, V1.0, Phụ lục `02fca4f`) được bảo toàn nguyên byte.
- **Thay đổi thực tế**:
  - Trích xuất nguyên byte raw log đã chạy ở lượt `33e8bb6` thành tệp `docs/QA_RAW_LOG_MAIN_BATCH1_33E8BB6_B.txt` (`10.920 bytes` | SHA-256: `29b452ff...`) để bàn giao cùng báo cáo V1.6 gốc cho C lưu trữ.
  - Phát hành phụ lục `docs/QA_ADDENDUM_MAIN_BATCH1_B5B7DB2_MIGRATION_VERIFIER_PENDING_V1_7_B.md`; không sửa bất kỳ tệp nào của C.
- **Tự kiểm**:
  - Đối chiếu `git diff --stat 33e8bb6c29c7ee15209ae5847d48aae973a3f536 b5b7db2900fefd142c211fb2045a3e2bf3272298`: xác nhận chỉ thay đổi 1 tệp `artifacts/main_batch1_release_manifest.json`.
  - Đo trực tiếp byte và SHA-256 của báo cáo V1.6 gốc (`37.162 bytes`, `bfeb73d9...`), tệp raw log (`10.920 bytes`, `29b452ff...`) và phụ lục V1.7.
- **Kiểm thử**:
  - **Phần giữ nguyên từ QA V1.6 tại `33e8bb6c29c7ee15209ae5847d48aae973a3f536`**: Không chạy lại 154 phép kiểm chọn lọc (`passed=154, failed=0, skipped=0, deselected=0 in 19.82s`) và lượt chạy rộng (`passed=421, failed=6, skipped=38, deselected=0, subtests passed=32 in 27.32s`) do mã nguồn và bộ test tại `b5b7db2` không đổi so với `33e8bb6`.
  - **Phần kiểm mới cho Migration Ledger & Verifier Fingerprint**: **`N/A (PENDING)`** tại thời điểm này do đang chờ Thành viên C bàn giao commit mã migration và verifier mới.
- **QA độc lập (Theo từng phạm vi hiện hành)**:
  - **Phạm vi 1 — Mã nguồn, SOP và fixture tổng hợp đã kiểm tại `33e8bb6` (giữ nguyên tại `b5b7db2`)**: **`PASS`** (`154 passed` trong 8 tệp chọn lọc).
  - **Phạm vi 2 — Phương án Migration Ledger trên fixture tổng hợp (Mục 3 chỉ đạo D)**: **`PENDING`** (Chờ C bàn giao mã migration đã chỉnh).
  - **Phạm vi 3 — Verifier Fingerprint trên fixture tổng hợp (Mục 4 chỉ đạo D)**: **`PENDING`** (Chờ C bàn giao mã verifier cho canonical metadata / raw input).
  - **Phạm vi 4 — Hiện vật hạn chế thật V2 & Áp dụng Migration lên Ledger thật**: **`HOLD / PENDING (Do Lead D kiểm chứng trực tiếp và phê duyệt)`**.
- **Giới hạn và việc còn mở**:
  - Giới hạn: B giữ tính mù, không nhận hoặc mở quần thể thật, mapping thật, seed/salt thật, nhãn nguồn hay Blind View A; các nhận định về gói thật V2 là kết quả kiểm trực tiếp của Lead D.
  - Việc còn mở:
    1. Thành viên C lưu nguyên byte tệp báo cáo QA V1.6 gốc (`docs/QA_REPORT_MAIN_BATCH1_33E8BB6_CONSOLIDATED_V1_6_B.md`) và tệp raw log (`docs/QA_RAW_LOG_MAIN_BATCH1_33E8BB6_B.txt`).
    2. Thành viên C hoàn thiện mã migration ledger và verifier fingerprint theo chỉ đạo của Lead D, đồng thời bổ sung đủ 1.232 metadata records và đầu vào/log kiểm loại trừ cho gói thật V2.
    3. Ngay khi C bàn giao commit mã migration/verifier mới, B xác nhận full commit SHA, đọc diff và chạy bộ kiểm thử fixture (tách rõ ca chẩn đoán lỗi block sparse khỏi ca chứng minh bản sửa đạt) để phát hành kết luận QA cho phần migration/verifier.
- **Trạng thái quản trị**:
  - Phạm vi mã nguồn, SOP và fixture tại `33e8bb6`: **`QA PASS`**.
  - Phạm vi mã Migration Ledger & Verifier Fingerprint: **`PENDING`**.
  - Gói dữ liệu Main Annotation Đợt 1: **`HOLD / LOCKED`**.
  - Các cờ khóa quản trị hiện hành: `main_annotation_status="LOCKED"`, `training_blocked=true`, `official_test_used=false` (Chưa cấp quyền migration thật, chưa mở Pass 1; chờ quyết định riêng của Lead D).
