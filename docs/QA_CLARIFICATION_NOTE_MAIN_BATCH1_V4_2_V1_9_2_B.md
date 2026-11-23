# GHI CHÚ ĐÍNH CHÍNH NGẮN (CLARIFICATION NOTE V1.9.2) — BỔ SUNG CHO BÁO CÁO QA & ERRATA V1.9.1 (MAIN ANNOTATION BATCH 1 — V4.2)

- **Mã tài liệu**: `QA_CLARIFICATION_NOTE_MAIN_BATCH1_V4_2_V1_9_2_B`
- **Ngày ban hành**: `2026-11-23`
- **Người đứng tên phát hành**: **Phùng Tấn Minh** (**Thành viên B — Annotator B kiêm QA Lead & Nhóm trưởng**)
- **Tài liệu được bổ sung và giữ nguyên byte**:
  - Báo cáo Đính chính & QA V1.9.1: `docs/QA_REPORT_MAIN_BATCH1_V4_2_ERRATA_V1_9_1_B.md` (`52.912 bytes` | SHA-256: `a51ab9457c8de973ebcfd1c92de8fbf7983d381a1223f6542c620ccf31436b24`)
  - Báo cáo QA V1.9 lịch sử: `docs/QA_REPORT_MAIN_BATCH1_AC2CF1D_FINAL_V1_9_B.md` (`26.080 bytes` | SHA-256: `baf0e5c39b97f0a1a12a1f17ce6d1f3f42b21dded1e0f68f74c3157e7b061f4c`)
  - Tệp wrapper log V1.9 lịch sử: `docs/QA_RAW_LOG_MAIN_BATCH1_AC2CF1D_B.txt` (`5.823 bytes` | SHA-256: `bbfc3d991c000f2c99a56ba74968403b7ec536535e98a4799bf55f13ca74a2e4`)
  - Tệp raw task log nguyên byte của hệ thống (bàn giao tách biệt): `docs/QA_RAW_TASK_LOG_MAIN_BATCH1_AC2CF1D_TASK4524_B.log` (bản sao nguyên byte từ `task-4524.log` | `1.502 bytes` | SHA-256: `eb04b1bb1013c3010e57857ec3bb446f8524b5174b12fc6d1290db164e0c90e1`)
- **Commit được kiểm**: `ac2cf1d82d9a742ec0f5e9af81e0ce116fdfbe3d` (cùng commit sửa lõi `fb487540aa6c877553eeb9e0978437642a4173b1` và commit đồng bộ hồ sơ `d8b44849895bdb0a8a48432286b7d609ba01c635`) trên nhánh `origin/feat/c-main-annotation-batch1`.
- **Phạm vi tác động**: Chỉ chuẩn hóa cách phân loại bản trích log và bỏ tên hàm helper không có trong mã nguồn; **không thay đổi kết quả kiểm chứng R1/R2 (`2 passed`), bộ 12 tệp kiểm thử chọn lọc (`165 passed`), phép kiểm cô lập Git (`PASS`) hoặc phạm vi QA kỹ thuật đã chứng thực tại V1.9.1**.

---

## 1. Phân loại đúng bản trích log tại Mục 5.2 của V1.9.1 và bàn giao tệp Raw Task Log nguyên byte

1. **Phân loại lại khối văn bản tại Mục 5.2 của `docs/QA_REPORT_MAIN_BATCH1_V4_2_ERRATA_V1_9_1_B.md`**:
   - Tại Mục 5.2 của báo cáo V1.9.1 (`a51ab9457c8de973ebcfd1c92de8fbf7983d381a1223f6542c620ccf31436b24`), do Thành viên B đã thay ký hiệu phần trăm trên thanh tiến độ (progress bar) của pytest thành chữ `pct`, khối văn bản đó được phân loại chính xác là **“bản trích hiển thị đã chuyển đổi ký hiệu”**, **không phải** là bản nguyên byte của stdout/task log.
2. **Làm rõ quy tắc ngôn từ trong `AGENTS.md`**:
   - Quy tắc làm việc với AI của nhóm (Mục 5 `AGENTS.md`) chỉ yêu cầu không dùng từ tuyệt đối hóa trong nhận định/kết luận văn bản khi phép kiểm không chứng minh được phạm vi đó; **quy tắc không cấm ký hiệu phần trăm trong output kiểm thử nguyên bản của công cụ và không yêu cầu sửa thanh progress bar của pytest**.
3. **Phân tách rõ 3 hiện vật log khi bàn giao (không trộn lẫn và không tái tạo log)**:
   - **Hiện vật 1 — Tệp Raw Task Log nguyên byte từ hệ thống (`task-4524.log`)**: Được giữ nguyên byte và bàn giao riêng tại `docs/QA_RAW_TASK_LOG_MAIN_BATCH1_AC2CF1D_TASK4524_B.log` (**`1.502 bytes`** | SHA-256: **`eb04b1bb1013c3010e57857ec3bb446f8524b5174b12fc6d1290db164e0c90e1`**).
   - **Hiện vật 2 — Tệp Wrapper tổng hợp lịch sử**: `docs/QA_RAW_LOG_MAIN_BATCH1_AC2CF1D_B.txt` (**`5.823 bytes`** | SHA-256: **`bbfc3d991c000f2c99a56ba74968403b7ec536535e98a4799bf55f13ca74a2e4`**), giữ nguyên byte làm hồ sơ lịch sử kèm V1.9.
   - **Hiện vật 3 — Bản trích hiển thị đã chuyển đổi ký hiệu**: Nằm tại Mục 5.2 bên trong báo cáo V1.9.1 (`a51ab945...`), giữ nguyên byte trong tệp V1.9.1 và được định danh đúng theo mục 1 ở trên.

---

## 2. Đính chính mô tả mã nguồn tại hạng mục R2: Bỏ tên helper `_build_blind_record` không có trong `src/phishing/data/main_sampling.py`

1. **Nội dung cần đính chính trong V1.9.1 (`a51ab9457c8de973ebcfd1c92de8fbf7983d381a1223f6542c620ccf31436b24`)**:
   - Tại Mục 2 (dòng `E-07`) và Mục 4.1 của V1.9.1, khi mô tả cơ chế tạo Blind View trong `src/phishing/data/main_sampling.py`, văn bản có nhắc tới tên hàm helper `_build_blind_record`.
2. **Bằng chứng thực tế trong mã nguồn tại commit `ac2cf1d82d9a742ec0f5e9af81e0ce116fdfbe3d` (và `fb487540...` / `d8b44849...`)**:
   - Trong `src/phishing/data/main_sampling.py` **không có** hàm helper nào tên là `_build_blind_record`.
   - Cả hai nhánh trong hàm `run_main_batch1_sampling` (nhánh rerun khi lot đã tồn tại trong sổ cái và nhánh chọn mẫu lần đầu) đều đọc trực tiếp `html_content = sample.get("html", "")` và gọi trực tiếp hàm **`extract_safe_view_content(html_content, page_url=sample.get("url", ""))`** (được import từ `phishing.annotation.blind_view`) để lấy `cleaned_text, struct_summary` và tạo dictionary `blind_sample`.
3. **Nội dung đính chính chính thức**:
   - **Bỏ hoàn toàn tên helper `_build_blind_record`** khỏi mô tả R2.
   - Mô tả đúng theo mã nguồn thực tế: Trước khi sửa (tại V4.1 `28462fce...`), khi chạy `run_main_batch1_sampling` với đầu vào metadata-only (thiếu trường `"html"`), nhánh rerun trong `run_main_batch1_sampling` lấy `html_content = sample.get("html", "")` (chuỗi rỗng) và gọi trực tiếp `extract_safe_view_content(html_content, page_url=sample.get("url", ""))` để tạo nội dung Blind View, dẫn tới trả về các bản ghi Blind View có `page_text` rỗng trong **fixture hoặc bản sao rerun** (gói dữ liệu hạn chế thật đã niêm phong không bị ghi đè). Sau khi sửa tại V4.2 (`fb487540...` / `ac2cf1d8...`), `compute_population_fingerprint` băm chuỗi rỗng `b""` khi thiếu `"html"`, làm `pop_hash != prior_pop_hash` và `run_main_batch1_sampling` ném `ValueError` từ chối rerun ngay trước khi đi vào vòng lặp gọi `extract_safe_view_content`.

---

## 3. Xác nhận Bảo toàn Kết luận QA Kỹ thuật và Ranh giới Quản trị

Tôi, **Phùng Tấn Minh** (**Thành viên B — Annotator B kiêm QA Lead & Nhóm trưởng**), xác nhận:

1. Ghi chú đính chính ngắn **V1.9.2** này bổ sung trực tiếp cho Báo cáo Đính chính & QA **V1.9.1** (`docs/QA_REPORT_MAIN_BATCH1_V4_2_ERRATA_V1_9_1_B.md`, `52.912 bytes`, SHA-256: `a51ab9457c8de973ebcfd1c92de8fbf7983d381a1223f6542c620ccf31436b24`) mà không ghi đè hay thay đổi byte của V1.9.1, V1.9 (`baf0e5c3...`) và wrapper log V1.9 (`bbfc3d99...`).
2. Hai điểm làm rõ trên **không làm thay đổi** kết quả kiểm chứng kỹ thuật đã đạt:
   - Hai probe hồi quy R1 và R2 (`tests/test_main_v41_fingerprint_integrity.py`): **`2 passed in 0.63s`**.
   - Bộ 12 tệp kiểm thử chọn lọc trong repository (đã bao gồm 2 probe R1/R2): **`165 passed, 0 failed, 0 skipped in 28.06s`**.
   - Phép kiểm cô lập Git (`scripts/data/verify_git_isolation.py`): **`PASS`**.
   - Kết luận QA kỹ thuật mã nguồn và fixture của bản sửa V4.2 tại commit `ac2cf1d82d9a742ec0f5e9af81e0ce116fdfbe3d` (cùng core fix `fb487540aa6c877553eeb9e0978437642a4173b1` và commit đồng bộ hồ sơ `d8b44849895bdb0a8a48432286b7d609ba01c635`) được giữ nguyên là **`PASS` trong phạm vi mã nguồn và fixture đã kiểm**.
3. Các cổng quản trị hiện hành tiếp tục giữ nguyên trạng thái khóa: `main_annotation_status = "LOCKED"` (`main_batch1_status = "HOLD"`), `training_blocked = true`, `official_test_used = false`. Việc áp dụng Block 2 vào sổ cái hạn chế thật `data/restricted/main_annotation_lot_management_ledger.json` và mở Main Annotation Pass 1 vẫn chờ quyết định riêng của **Lead D (Anh Tuấn)**.
