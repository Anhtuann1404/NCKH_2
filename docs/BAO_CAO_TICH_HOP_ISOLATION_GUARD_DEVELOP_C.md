# BÁO CÁO TÍCH HỢP VÀ TỰ KIỂM BẢN VÁ CÁCH LY DỮ LIỆU TRÊN NHÁNH DEVELOP (BẢN ĐÍNH CHÍNH HOÀN THIỆN)

**Căn cứ thực hiện:** Yêu cầu tích hợp của Lead D từ gói `lead_d_real_isolation_verification_b31a1b1.zip` và ý kiến chỉ đạo rà soát hồ sơ kiểm toán của Lead D (19/11/2026)  
**Người thực hiện:** Nguyễn Thắng (Thành viên C — Data Pipeline Owner kiêm Integrator)  
**Người thẩm định kỹ thuật:** Lead D (Anh Tuấn — Model & Training Pipeline Lead)  
**Người thẩm định QA độc lập:** Phùng Tấn Minh (Thành viên B — Annotator B kiêm QA Lead & Nhóm trưởng)  
**Công cụ hỗ trợ:** Mô hình Duo (DeepSeek Bridge `deepseek-v4-pro` — chế độ `reason`)  
**Nhánh Git thực hiện:** `develop`  
**Base commit:** `b31a1b1c35192a69e8acf8224f17523a4ff56f12`  
**Commit chạy tự kiểm thực tế:** `4a6b021783f485ca425e4114b529a4a4b288e915`  
**Trạng thái quản trị:** `training_blocked = true`, `official_test_used = false`, `main_annotation_status = "LOCKED"`  

---

## 1. MỤC TIÊU VÀ PHẠM VI
1. Ghi nhận toàn bộ quy trình tích hợp bản vá kiểm soát cách ly `isolation_guard_b31a1b1.patch` (do Lead D bàn giao và QA Lead B đã thẩm định) vào nhánh `develop`.
2. Khắc phục triệt để các sai lệch hồ sơ theo kết luận chỉ đạo của Lead D:
   - Khôi phục bản gốc Báo cáo thẩm định QA của Thành viên B nguyên byte (`19.397 bytes` | SHA-256: `cae11d41074774d5daf2a2dcae47d48b8e6ff04f9349853205585ab9654990f3`).
   - Tách biệt bản tóm tắt do C biên tập vào thư mục lưu trữ lịch sử riêng (`docs/archive/`), ghi rõ bản chất không thay thế văn bản QA của B.
   - Bổ sung nguyên vẹn bản vá `isolation_guard_b31a1b1.patch` và `pytest_full.log` vào `artifacts/lead_d_isolation_verification/`, bảo đảm bảng kê `SHA256SUMS.txt` khớp 100% từng dòng.
   - Đính chính mã băm chuẩn của tệp `SHA256SUMS.txt`: Đúng chuẩn LF là `86842d826f2dd0ba57273e796d3b2a591d7b1048404c8e6d2ae275d946997b47` (thay thế số `4ec6b4b7...` do lỗi trích dẫn từ hồ sơ cũ).
   - Phân định rõ ràng hai định dạng log thực thi của Thành viên C: Bản Git LF (1.421 bytes | `dc161140...`) và bản Windows CRLF (1.443 bytes | `926a82d7...`).
3. Xác định chính xác phạm vi tích hợp: Việc áp dụng patch lên nhánh `develop` chỉ giải quyết cổng cách ly trên mã training của base D; hoàn toàn tách biệt với nhánh dữ liệu `feat/c-calibration-v1-1-4-adjudication` (commit `8643f55`).

## 2. NGƯỜI THỰC HIỆN VÀ PHÂN ĐỊNH TRÁCH NHIỆM
- **Thành viên C (Nguyễn Thắng):** Đứng tên Báo cáo tích hợp này; chịu trách nhiệm giải nén gói ZIP, áp dụng bản vá, chạy kiểm thử tự động, lưu vết hiện vật và bàn giao log thực thi. Tuyệt đối không thay đổi hay ký nhận thay văn bản QA của Thành viên B.
- **Lead D (Anh Tuấn):** Tác giả bản vá, chủ trì nghiệm thu kỹ thuật và đối chiếu mã nguồn.
- **Thành viên B (Phùng Tấn Minh):** Giữ quyền thẩm định QA độc lập; sẽ thẩm định lại và ban hành phụ lục QA trên commit sửa đổi chính thức.

## 3. CÔNG CỤ AI ĐÃ DÙNG (MÔ HÌNH DUO)
- Kích hoạt Mô hình Duo qua công cụ nội bộ `deepseek_bridge/cli.py` với model `deepseek-v4-pro` (mode `reason`).
- Phạm vi sử dụng: Phân tích chỉ đạo của Lead D, tính toán đối soát mã băm LF/CRLF và thiết kế cấu trúc bảng kê hiện hành chuẩn mực ARS và Ponytail.
- Bảo mật dữ liệu: Không nạp dữ liệu nhãn nguồn hay HTML vào AI.

## 4. ĐẦU VÀO ĐÃ KHÓA VÀ ĐỐI SOÁT MÃ BĂM
- Gói nén Lead D bàn giao: `lead_d_real_isolation_verification_b31a1b1.zip` (9.651 bytes | SHA-256: `0a2d15ffa794c16b4e9bbcaea7b2b62a9c01f473ecd946244add294aa7d34e07`).
- Bảng kê gốc `SHA256SUMS.txt` (536 bytes chuẩn LF | SHA-256: `86842d826f2dd0ba57273e796d3b2a591d7b1048404c8e6d2ae275d946997b47` — Đã đính chính từ số `4ec6b4b7...` do lỗi bảng thông số trước đó):
  1. `ISOLATION_VERIFICATION_REPORT.md`: 5.330 bytes | `b87a60090d0e06b068d900481126fb06320da471f10b541c30a9d334f7eb4861` (Khớp).
  2. `isolation_guard_b31a1b1.patch`: 11.215 bytes | `1149ed79addd106f5678388f9da93057198339bafe54e3774a20eb7911db19ac` (Khớp).
  3. `pytest_full.log`: 179 bytes | `008a287c1a26f68bb299333c696a3f72f4dcbecf39b7afa058b4744903643f94` (Khớp).
  4. `real24_verification.json`: 421 bytes | `526a1da866fc36751c13d09b5a7b5a70ab5d005610d934a24056df02ddf706d7` (Khớp).
  5. `source_hashes.json`: 533 bytes | `f8071d84410d08031c9e073be795d683d32dbc6deb6862a4b0e8aef11f801259` (Khớp).
  6. `verify_real24.py`: 5.196 bytes | `e4e1576b65389b863b2e8631453b4e95042de2af47e5ff5260396f9f8dc37815` (Khớp).
- Bản QA gốc của B: `docs/QA_REPORT_LEAD_D_REAL_ISOLATION_B31A1B1_B.md` (19.397 bytes | SHA-256: `cae11d41074774d5daf2a2dcae47d48b8e6ff04f9349853205585ab9654990f3`).

## 5. THAY ĐỔI THỰC TẾ TRÊN MÃ NGUỒN VÀ HỒ SƠ
- **Mã nguồn (khớp 100% bản vá của D và đã được D/B xác nhận):**
  - `src/phishing/training/readiness.py`: thêm `load_isolated_ids`, `row_is_isolated`, `check_run_plan_isolation` gọi `plan.validate` thật; sửa `check_training_inputs` chặn cờ cách ly.
  - `src/phishing/training/experiment.py`: chặn mẫu ngoài fixture tại đầu hàm `fit_fold`.
  - `tests/`: thêm `test_label_isolation.py`; mở rộng `test_training_pipeline.py`, `test_training_readiness.py`.
- **Hồ sơ lưu trữ:**
  - Khôi phục nguyên vẹn 6 tệp gốc và bảng kê `SHA256SUMS.txt` tại `artifacts/lead_d_isolation_verification/`.
  - Đính chính bảng kê hiện hành: `artifacts/lead_d_isolation_verification/MANIFEST_MEMBER_C_INTEGRATION.json`.
  - Lưu bản C tóm tắt trước đây vào `docs/archive/QA_REPORT_LEAD_D_REAL_ISOLATION_B31A1B1_B_c_summary_draft.md`.

## 6. TỰ KIỂM TRA CỦA THÀNH VIÊN C
- Đo đạc mã băm 5 tệp mã nguồn và test sau khi áp dụng patch:
  1. `src/phishing/training/readiness.py`: `1b5d89f9...` (Khớp 100%).
  2. `src/phishing/training/experiment.py`: `c17f082a...` (Khớp 100%).
  3. `tests/test_training_readiness.py`: `53d2917c...` (Khớp 100%).
  4. `tests/test_training_pipeline.py`: `71bd1f76...` (Khớp 100%).
  5. `tests/test_label_isolation.py`: `fa3afade...` (Khớp 100%).

## 7. BẰNG CHỨNG KIỂM THỬ THỰC TẾ
- **Phiên bản mã nguồn chạy tự kiểm:** Commit `4a6b021783f485ca425e4114b529a4a4b288e915` trên nhánh `develop`.
- **Môi trường:** Windows 11, Python 3.13.14, pytest 7.4.0, pluggy 1.6.0, anyio 4.14.2.
- **Lệnh chạy:** `PYTHONUTF8=1 PYTHONPATH=src .venv/Scripts/python.exe -m pytest tests/`
- **Kết quả thực tế:** **95 passed in 34.85s** (0 failed, 0 skipped, 0 deselected).
- **Hiện vật log bàn giao:**
  - `pytest_full.log` (179 bytes | SHA-256: `008a287c...`): Log 1.87s do Lead D bàn giao (lưu giữ làm bằng chứng lịch sử tại workspace D).
  - `pytest_member_c_develop_4a6b021_run.txt` (Log do Thành viên C tự kiểm trên máy Windows):
    + **Bản Git LF (lưu trữ trên repository):** 1.421 bytes | SHA-256: `dc161140d9add0fc5be356821dba80929990d7ee115c50400ae4587a4ce17b9a`.
    + **Bản Windows CRLF (ghi nhận trực tiếp từ console):** 1.443 bytes | SHA-256: `926a82d72167c7f3404d01b0b319cd5c13bd56ceb4a39912b5502ce9b4d2a931`.
    + *Giải trình chuyển đổi:* Bản Windows chứa 22 ký tự `\r` (CR) tại 22 dấu xuống dòng `\r\n` (thêm đúng 22 bytes). Khi chuyển 22 dấu xuống dòng LF sang CRLF tái lập hoàn toàn khớp 100% bản Windows; nội dung kết quả `95 passed in 34.85s` không thay đổi.
- Phân định rõ: 95 test này là test suite của nhánh D trên `develop`, hoàn toàn không ghép với suite 446 test trên nhánh dữ liệu C.

## 8. THẨM ĐỊNH QA ĐỘC LẬP
- **Trạng thái:** PENDING (Chờ Thành viên B thẩm định lại và phát hành phụ lục QA trên đúng commit hiệu chỉnh này).
- C bàn giao bản QA gốc của B tại `docs/QA_REPORT_LEAD_D_REAL_ISOLATION_B31A1B1_B.md` và không can thiệp vào bất kỳ kết luận nào của B.

## 9. GIỚI HẠN VÀ PHÂN ĐỊNH PHẠM VI LIÊN NHÁNH
- **Phạm vi trên nhánh `develop`:** Bản vá kiểm soát cách ly đã được áp dụng và tự kiểm đạt 95/95 test.
- **Phạm vi trên nhánh dữ liệu của C:** Nhánh `feat/c-calibration-v1-1-4-adjudication` đang ở commit `8643f55` (đã hoàn thành kiểm nguồn shard `train-001`).
- **Phân định rõ ràng:** Hai nhánh hiện tại hoạt động độc lập; chưa có việc gộp toàn diện thành một pipeline đầu-cuối duy nhất. Việc tích hợp toàn diện sẽ thực hiện sau khi Lead D nghiệm thu kiểm nguồn và ban hành Quyết định chính thức về chọn mẫu Main.

## 10. TRẠNG THÁI QUẢN TRỊ
- `main_annotation_status = "LOCKED"`
- `training_blocked = true`
- `official_test_used = false`
- Không phát Blind View, không rút mẫu Main, không huấn luyện mô hình.
