# BÁO CÁO THẨM ĐỊNH QA ĐỘC LẬP: GÓI BỔ SUNG KIỂM SOÁT CÁCH LY DỮ LIỆU BẰNG MÃ THẬT TRÊN BASE b31a1b1 (LEAD D BÀN GIAO)

- **Mã tài liệu:** `QA-REPORT-LEAD-D-REAL-ISOLATION-B31A1B1-B`
- **Phiên bản:** 1.0 (Thẩm định độc lập riêng cho gói kiểm soát cách ly dữ liệu bằng mã thật do Lead D bàn giao; giữ nguyên toàn bộ các báo cáo QA trước làm dấu vết kiểm toán)
- **Ngày phát hành:** 2026-11-18
- **Người thực hiện thẩm định độc lập:** Phùng Tấn Minh (Thành viên B — Annotator B kiêm QA Lead & Nhóm trưởng)
- **Tệp gói nén đã thẩm định:** `lead_d_real_isolation_verification_b31a1b1.zip` (9.651 byte, SHA-256: `0a2d15ffa794c16b4e9bbcaea7b2b62a9c01f473ecd946244add294aa7d34e07`)
- **Base commit áp dụng patch:** `b31a1b1c35192a69e8acf8224f17523a4ff56f12`

---

## 1. MỤC TIÊU VÀ PHẠM VI
- Thẩm định độc lập 5 nội dung kỹ thuật của gói bản vá kiểm soát cách ly do Lead D bàn giao:
  1. Khóa đúng đối tượng QA: Gói nén `lead_d_real_isolation_verification_b31a1b1.zip`, base `b31a1b1`, patch `isolation_guard_b31a1b1.patch`.
  2. Thẩm tra nội dung bản vá: Xác nhận loại bỏ hoàn toàn `simulate_runplan_validate`, nạp ID vào `RunPlan.validate` thật, chặn cờ cách ly trong `readiness.py` và chặn mẫu ngoài fixture trong `experiment.py`.
  3. Chạy suite 95 bài test hồi quy của nhánh D trên clean checkout cô lập (`b31a1b1` + patch).
  4. Kiểm chứng 7 hành vi kỹ thuật bằng fixture tổng hợp độc lập.
  5. Đánh giá script `verify_real24.py`, phân định rõ ràng kết quả thực thi của Lead D với phạm vi tái lập độc lập của B; bảo toàn tính mù của Annotator B.

## 2. NGƯỜI THỰC HIỆN / NGƯỜI KIỂM ĐỘC LẬP
- **Người thực hiện bàn giao:** Lead D (Anh Tuấn).
- **Người thẩm định QA độc lập:** Phùng Tấn Minh (Thành viên B — Annotator B kiêm QA Lead & Nhóm trưởng).

## 3. AI ĐÃ DÙNG
- Sử dụng công cụ AI hỗ trợ phân tích diff, áp dụng patch trên clean checkout và đo lường mã băm SHA-256.
- **Phạm vi dữ liệu đưa vào AI:** Chỉ sử dụng các tệp mã nguồn và báo cáo công khai trong gói zip; tuyệt đối không đưa bất kỳ dữ liệu nhãn nguồn hay nội dung mẫu nào vào AI.

## 4. ĐẦU VÀO ĐÃ KHÓA VÀ ĐỐI SOÁT MÃ BĂM THỰC TẾ
- **Tệp gói nén bàn giao:** `lead_d_real_isolation_verification_b31a1b1.zip` (9.651 byte | SHA-256: `0a2d15ffa794c16b4e9bbcaea7b2b62a9c01f473ecd946244add294aa7d34e07`)
- **Các tệp thành phần bên trong gói (đối chiếu SHA256SUMS.txt):**
  - `ISOLATION_VERIFICATION_REPORT.md`: 5.330 byte | `b87a60090d0e06b068d900481126fb06320da471f10b541c30a9d334f7eb4861` (Khớp)
  - `isolation_guard_b31a1b1.patch`: 11.215 byte | `1149ed79addd106f5678388f9da93057198339bafe54e3774a20eb7911db19ac` (Khớp)
  - `pytest_full.log`: 179 byte | `008a287c1a26f68bb299333c696a3f72f4dcbecf39b7afa058b4744903643f94` (Khớp)
  - `real24_verification.json`: 421 byte | `526a1da866fc36751c13d09b5a7b5a70ab5d005610d934a24056df02ddf706d7` (Khớp)
  - `source_hashes.json`: 533 byte | `f8071d84410d08031c9e073be795d683d32dbc6deb6862a4b0e8aef11f801259` (Khớp)
  - `verify_real24.py`: 5.196 byte | `e4e1576b65389b863b2e8631453b4e95042de2af47e5ff5260396f9f8dc37815` (Khớp)
  - `SHA256SUMS.txt`: 536 byte | `4ec6b4b745426b389945a895b66d7adbc4b18c0df9ba0a6bc700445a60e0a544` (Khớp)
- **Base commit kiểm tra:** `b31a1b1c35192a69e8acf8224f17523a4ff56f12`.
- **Lưu ý quản trị:** Bản sửa hiện đã được tích hợp từ gói zip bàn giao lên nhánh `develop`.

## 5. THAY ĐỔI THỰC TẾ TRONG BẢN VÁ
- `src/phishing/training/readiness.py`:
  - Thêm `row_is_isolated(row)`: Kiểm tra 4 cờ cách ly, bắt buộc kiểu boolean JSON thuần túy (từ chối chuỗi "False", số 0, 1), trả về True nếu cờ True hoặc dataset_split không thuộc danh mục hợp lệ.
  - Thêm `load_isolated_ids(path, expected_sha256)`: Đọc tệp JSON/CSV đã khóa SHA-256, yêu cầu siêu dữ liệu cách ly cấp dòng đầy đủ, trả về `frozenset(excluded)`.
  - Thêm `check_run_plan_isolation(plan, group_by_sample, *, label_artifacts)`: Chuyển trực tiếp các ID bị cách ly vào phương thức `plan.validate` thật của RunPlan. Xác nhận: Hoàn toàn không còn dùng `simulate_runplan_validate`.
  - Sửa `check_training_inputs(manifest_path)`: Chặn nếu mẫu bị cách ly xuất hiện ở index hoặc labels.
- `src/phishing/training/experiment.py`:
  - Thêm `assert_fixture_cohort(samples)` ngay đầu hàm `fit_fold`, chặn mọi mẫu ngoài fixture trước khi phân tích variant và trước khi gọi `make_pipeline`.
- `tests/`:
  - Thêm `test_label_isolation.py`: Kiểm tra nạp ID từ JSON/CSV vào RunPlan thật, phát hiện tệp bị can thiệp và siêu dữ liệu không hợp lệ.
  - Mở rộng `test_training_pipeline.py` và `test_training_readiness.py`: Kiểm tra `fit_fold` chặn mẫu ngoài fixture và `check_training_inputs` chặn cờ cách ly.

## 6. TỰ KIỂM
- **Kiểm tra áp dụng bản vá:** Lệnh `git apply --check` trên base `b31a1b1` chạy thành công, không xung đột. Sau khi áp dụng, mã băm chuẩn LF của cả 5 tệp mã nguồn và test khớp tuyệt đối với `source_hashes.json`.
- **Kiểm chứng 7 hành vi với fixture tổng hợp độc lập:**
  1. JSON và CSV đều chuyển cờ cách ly thành `frozenset({'s2', 's3'})` chính xác.
  2. Mẫu cách ly đưa vào train, validation hay test đều bị `RunPlan.validate` thật từ chối với lý do *"Pilot/reserved samples entered the run plan"*.
  3. Sai hash (checksum mismatch), thiếu metadata cách ly, ID rỗng hoặc cờ boolean nhập nhằng ("False" dạng string trong JSON) đều bị chặn fail-closed.
  4. Dữ liệu kiểm soát hợp lệ đi qua RunPlan (`samples: [1, 1, 1]`) và `check_training_inputs`.
  5. `check_training_inputs` từ chối cờ cách ly xuất hiện ở cả `index.json` lẫn `labels.json` (*"Isolated sample entered input cohort"*).
  6. `fit_fold` ném ValueError (*"This handoff is restricted to invented fixture samples"*) ngay khi gặp mẫu ngoài fixture; `make_pipeline` hoàn toàn không được gọi (`assert_not_called` đạt).
  7. `check_training_inputs` chặn `scope="research"` (*"Research inputs blocked"*); kết quả fixture luôn có `research_training_allowed=False`.
- **Đánh giá script `verify_real24.py`:**
  - Script chỉ xuất các số đếm tổng hợp, không in nhãn nguồn hay HTML mẫu; phương pháp luận bảo vệ an toàn tính mù của Annotator B.

## 7. KIỂM THỬ
- **Môi trường:** Clean checkout, Python 3.14.2, pytest 9.1.1 / pytest 7.4.0 trên Windows.
- **Lệnh chạy:** `python -m pytest -o pythonpath=src tests/ -v`
- **Kết quả thực tế:** 95 passed, 0 failed, 0 skipped, 107 subtests passed in 7.97s.
- **Đối chiếu log Lead D (`pytest_full.log`):** Khớp chính xác số lượng 95 passed, 0 failed, 0 skipped.
- **Ranh giới suite test:** Đây là suite 95 bài test của nhánh D, hoàn toàn tách biệt và không ghép với suite 446 test của nhánh C.

## 8. QA ĐỘC LẬP
- **Người kiểm định:** Phùng Tấn Minh (QA Lead B).
- **Kết luận thẩm định:**
  - Tính toàn vẹn gói nén `lead_d_real_isolation_verification_b31a1b1.zip` và mã băm các tệp thành phần: **PASS**.
  - Thiết kế kỹ thuật bản vá `isolation_guard_b31a1b1.patch` (`RunPlan.validate` thật, `fit_fold` guard): **PASS**.
  - Bộ 95 bài test hồi quy của nhánh D trên clean checkout (`b31a1b1` + patch): **PASS**.
  - Bộ 7 phép kiểm chứng hành vi với fixture tổng hợp của B: **PASS**.
  - Phương pháp luận script `verify_real24.py` và bảo vệ tính mù: **PASS**.
  - Tích hợp vào nhánh vận hành chung của Thành viên C: **HOÀN TẤT TRÊN DEVELOP**.

## 9. GIỚI HẠN VÀ VIỆC CÒN MỞ
- **Phân định kết quả của D với phạm vi B tự tái lập:**
  - Con số 144 lần RunPlan từ chối thật, 72 lần check_training_inputs từ chối thật, 3 positive controls và 16 mẫu `binary_model_eligible=true` bị chặn là KẾT QUẢ DO LEAD D THỰC THI trên gói hiệu chuẩn thật `e0bb55e8...`.
  - Thành viên B ghi nhận các con số này dựa trên bằng chứng log bàn giao; B KHÔNG mở gói hiệu chuẩn `e0bb55e8...`, không mở nhãn hay HTML thật để giữ tính mù độc lập cho Annotator B. B chỉ tự tái lập trên test suite 95 test và các fixture tổng hợp.
- **Giới hạn liên nhánh:**
  - Bản vá này đã được tích hợp và xác thực trên `develop`. Việc gộp hoàn toàn với nhánh dữ liệu của C sẽ thực hiện qua quy trình PR tiêu chuẩn khi Lead D ban hành quyết định chọn mẫu Main.

## 10. TRẠNG THÁI QUẢN TRỊ
- Các chốt an toàn dữ liệu: `main_annotation_status="LOCKED"`, `training_blocked=true`, `official_test_used=false` tiếp tục duy trì hiệu lực nghiêm ngặt.
- Tuyệt đối không coi kết quả thẩm định này là việc cấp quyền huấn luyện nghiên cứu hay cấp quyền phát hành Blind View.
