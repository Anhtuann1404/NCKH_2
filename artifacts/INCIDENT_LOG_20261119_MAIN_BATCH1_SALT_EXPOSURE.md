# BÁO CÁO SỰ CỐ AN TOÀN DỮ LIỆU & KIỂM TOÁN DÒNG DÕI (INCIDENT REPORT)
**Mã sự cố:** `INC-20261119-MAIN-BATCH1-SALT-EXPOSURE`  
**Ngày phát hiện:** 19/11/2026  
**Người phát hiện:** Lead D (Anh Tuấn)  
**Người xử lý & Báo cáo:** Thành viên C (Nguyễn Thắng - Data Pipeline & Thư ký Kiểm toán)  
**Tình trạng quản trị hiện tại:** `main_annotation_status = "LOCKED"`, `training_blocked = true`, `official_test_used = false`.

---

## 1. Tóm tắt sự cố (Executive Summary)
Trong đợt nghiệm thu độc lập commit `b013ed7` ngày 19/11/2026, Lead D phát hiện giá trị chuỗi muối che mù mặc định (`DEFAULT_BLIND_SALT = "nckh2_main_batch1_blind_salt_secure_2026"`) cùng bộ seed lựa chọn (`1017, 2042, 2026`) đã bị đưa dưới dạng giá trị mặc định (default values) trong mã nguồn công khai `scripts/data/run_main_batch1_pipeline.py`.

Từ các giá trị mặc định công khai này, bất kỳ ai có quyền truy cập mã nguồn đều có thể tính toán lại chính xác cam kết băm `seed_commitment_sha256` công bố trong `artifacts/main_batch1_release_manifest.json`, làm mất tính bảo mật của cam kết niêm phong trước phát hành.

---

## 2. Đánh giá ranh giới và phạm vi ảnh hưởng (Scope & Impact Boundary Assessment)
Căn cứ theo Kỷ luật Nghiên cứu Hàn lâm (ARS) và nguyên tắc trung thực khoa học, C xác nhận rõ ranh giới kỹ thuật và phạm vi tiếp cận của sự cố:

1. **Kết luận về nhãn trong phạm vi đã kiểm:**
   - Trong phạm vi các artifact và file Blind View v1.2.0 đã kiểm tra đối chiếu, **chưa phát hiện trường nhãn trực tiếp** (`source_label`, `is_phish`, `label`, `target`, `primary_org`, `model_score`) xuất hiện trong Blind View gửi cho người gán.
   - Các trường trong Blind View v1.2.0 vẫn tuân thủ allowlist trung tính của Codebook.

2. **Rủi ro suy luận nhận diện (De-anonymization Risk):**
   - **Mức độ rủi ro:** Đáng kể đối với người nắm được mã nguồn công khai tại commit `b013ed7`.
   - **Cơ chế suy luận:** Do `DEFAULT_BLIND_SALT` và các seed lựa chọn bị đưa vào mã nguồn, cá nhân có quyền truy cập Git repository và shard dữ liệu nguồn `train-001.parquet` có thể tái lập lại toàn bộ quá trình rút mẫu, tính toán `generate_blind_id()`, từ đó suy luận ngược ánh xạ giữa `BLIND-xxxxxxxx` và danh tính gốc (`url`, `candidate_uid`, `source_row`), làm suy giảm nghiêm ngặt tính mù đôi (double-blind).

3. **Tình trạng tiếp cận thực tế của các bên (Access & Exposure Status):**
   - **Lead D (Anh Tuấn):** Đã kiểm toán trực tiếp tại commit `b013ed7`, phát hiện lỗ hổng và phát hành báo cáo kiểm toán HOLD.
   - **Annotator B kiêm QA Lead (Phùng Tấn Minh):** Đã phát hành báo cáo QA độc lập `docs/QA_PRE_RELEASE_CHECKLIST_MAIN_BATCH1_B_V1_2_HOLD_B013ED7.md`, xác nhận trạng thái HOLD/PENDING và ghi nhận chưa từng mở mã nguồn công khai tại commit `b013ed7` để kiểm tra seed/salt, bảo toàn tính mù đánh giá viên.
   - **Annotator A (Khải):** Theo log bàn giao và hiện trạng kiểm toán, chưa từng được cấp phát view hay tệp kết quả nào của Main Batch 1; phần tiếp xúc ngoài kênh bàn giao chính thức giữ mở, chờ xác nhận độc lập khi có yêu cầu từ Lead D.
   - **Dữ liệu thật:** Toàn bộ gói hạn chế vẫn lưu trữ trong `data/restricted/` (không bị Git theo dõi); quyền gán nhãn Pass 1 chưa từng được mở.

---

## 3. Các biện pháp khắc phục triệt để đã triển khai (Remediation Actions)
C đã tiến hành rà soát và khắc phục tận gốc ở tầng mã nguồn:

1. **Gỡ bỏ hoàn toàn giá trị bí mật mặc định khỏi mã nguồn công khai:**
   - Đã loại bỏ hoàn toàn `DEFAULT_BLIND_SALT` và các seed mặc định khỏi `scripts/data/run_main_batch1_pipeline.py` và `scripts/data/export_and_seal_population.py`.
   - Bắt buộc tham số bảo mật phải được nạp động từ:
     - Biến môi trường hệ thống (`MAIN_BLIND_SALT`, `MAIN_SEED_LOT_100`, v.v.).
     - Hoặc tệp cấu hình hạn chế được cô lập: `data/restricted/seeds_and_salts.json` (được `.gitignore` bảo vệ 100%).
     - Nếu thiếu tham số, pipeline sẽ ném ngoại lệ dừng ngay lập tức (fail-closed).

2. **Nâng cấp công cụ kiểm tra cách ly Git (`verify_git_isolation.py`):**
   - Mở rộng phạm vi quét kiểm toán sang toàn bộ thư mục `src/` và `scripts/` (thay vì chỉ `docs/` và `configs/`).
   - Tự động quét và phát hiện các chuỗi muối/seed bị hardcode trong mã nguồn; báo cáo trạng thái `FAIL` nếu phát hiện bất kỳ chuỗi nhạy cảm nào.

3. **Cơ chế khóa cổng phát hành nghiêm ngặt (Export Fail-Closed Gate):**
   - Script xuất gói `export_main_batch1` bắt buộc phải chạy `verify_git_isolation()` trước khi xuất tệp. Nếu kiểm toán cách ly trả về `FAIL`, lệnh xuất sẽ bị chặn đứng (raise `RuntimeError`), tuyệt đối không tạo tệp hay trả về trạng thái `SUCCESS`.

---

## 4. Phương án dòng dõi (Lineage Options) trình Lead D phê duyệt
Để xử lý lô mẫu Main Batch 1 đã được chuẩn bị, C đề xuất 2 phương án dòng dõi:

- **Phương án 1 (Khuyến nghị - Bảo lưu Cohort, Tái cấp Salt mới):**
  - **Lý do khoa học:** Giữ nguyên danh sách 100 ứng viên đã rút ngẫu nhiên ban đầu để tránh thiên kiến lựa chọn (selection bias / cherry-picking) khi biết trước danh sách.
  - **Thao tác:** Sử dụng một chuỗi muối bí mật hoàn toàn mới (`BLIND_SALT_SECRET_V2`) và seed xáo trộn phát hành mới để sinh lại toàn bộ ID trung tính `BLIND-xxxxxxxx` mới và thứ tự trình bày mới.
  - **Dòng dõi Ledger:** Ghi nhận sự kiện `SUPERSEDE_MAIN_BATCH1_BLIND_IDS` liên kết chặt chẽ với sự kiện trước qua hash-chain.

- **Phương án 2 (Rút lại toàn bộ lô mới):**
  - Ghi nhận trạng thái `REVOKED` cho lô cũ trong Ledger.
  - Cấp bộ seed hoàn toàn mới và rút một lô 100 mẫu khác từ 1.232 ứng viên theo chỉ đạo trực tiếp của Lead D.

---

## 5. Cam kết kiểm toán
Thành viên C cam kết duy trì tính bảo mật, trung thực khoa học, và không phát hành bất kỳ gói dữ liệu nào cho Annotator A hoặc B khi chưa có quyết định dòng dõi và lệnh phát hành chính thức bằng văn bản từ Lead D.
