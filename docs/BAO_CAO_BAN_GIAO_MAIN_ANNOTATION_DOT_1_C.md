# BÁO CÁO BÀN GIAO KỸ THUẬT: CHUẨN BỊ MAIN ANNOTATION ĐỢT 1 VÀ KIỂM SOÁT CÁCH LY DỮ LIỆU

- **Mã tài liệu**: `HANDOVER-MAIN-BATCH1-C-V1`
- **Phiên bản Hợp đồng Blind View**: `1.2.0`
- **Phiên bản Codebook**: `1.1.0` (tuân thủ `docs/CODEBOOK_V1.md`)
- **Ngày lập**: 19/11/2026
- **Người thực hiện**: Nguyễn Thắng (Thành viên C — Data Pipeline Owner kiêm Thư ký kiểm toán)
- **Người thẩm định**: Phùng Tấn Minh (Thành viên B — Annotator B kiêm QA Lead & Nhóm trưởng)
- **Người phê duyệt**: Anh Tuấn (Lead D — Chủ nhiệm đề tài)
- **Trạng thái cổng quản trị**: `main_annotation_status="LOCKED"`, `training_blocked=true`, `official_test_used=false`.
- **Ranh giới bắt buộc**: Chưa phát hành Blind View cho A/B, chưa mở Pass 1 trước khi có thẩm định QA phát hành từ B và lệnh riêng từ Lead D.

---

## 1. MỤC TIÊU VÀ PHẠM VI
- Tiếp thu và thực hiện trọn vẹn toàn bộ 6 nội dung chỉ đạo ban đầu và 4 nội dung làm rõ bổ sung của Lead D về việc chuẩn bị Main Annotation Đợt 1.
- Triển khai toàn diện chuỗi vận hành khép kín:
  Quần thể 1.232 ứng viên đã khóa $\rightarrow$ Lấy mẫu ngẫu nhiên không hoàn lại (SRS) 100 mẫu Main $\rightarrow$ Rút độc lập 30 mẫu cho B để tính Kappa chính $\rightarrow$ Thiết lập Hợp đồng Blind View v1.2.0 $\rightarrow$ Tích hợp CLI tự động bấm giờ $\rightarrow$ Kiểm soát Sổ cái quản lý lô (append-only ledger) $\rightarrow$ Kiểm tra cách ly Git thực tế (Git Isolation Verification).
- Phạm vi này chỉ chuẩn bị và niêm phong trong khu vực hạn chế (`data/restricted/`); tuyệt đối không mở training, không sử dụng official test, và không phát Blind View trước lệnh của Lead D.

---

## 2. NGƯỜI THỰC HIỆN VÀ NGƯỜI THẨM ĐỊNH
- **Người thực hiện kỹ thuật**: Nguyễn Thắng (Thành viên C).
- **Người kiểm định độc lập (QA Lead)**: Phùng Tấn Minh (Thành viên B).
- **Người chủ trì phân xử và phê duyệt phát hành**: Lead D (Anh Tuấn).

---

## 3. CÔNG CỤ AI ĐÃ DÙNG (MÔ HÌNH DUO)
- Tuân thủ nghiêm ngặt Quy chuẩn Agent (`AGENTS.md`): Sử dụng **Mô hình Duo (DeepSeek Bridge `deepseek-v4-pro` và `deepseek-flash`)** theo chỉ lệnh trực tiếp của người dùng (`suwr dungj mo hinh duo`).
- Vai trò của Duo:
  + Chế độ `reason`: Phân tích chuyên sâu kiến trúc 4 seed độc lập, thiết kế schema sổ cái append-only có liên kết chuỗi băm (hash-chaining) và lập bảng phân bổ lịch trình 4–5 giờ/ngày.
  + Chế độ `code`: Sinh mã nguồn chuẩn mực cho module lấy mẫu SRS, kiểm soát cách ly Git, và bộ kiểm thử hồi quy 9 test cases.
- Nguyên tắc an toàn: Không gửi dữ liệu hạn chế, nhãn nguồn hoặc nội dung mẫu lên AI; kiểm soát ngân sách token nghiêm ngặt qua `TokenGuard` (số dư hiện tại an toàn: 36.3%).

---

## 4. ĐẦU VÀO ĐÃ KHÓA VÀ BẢNG MÃ BĂM ĐỐI SOÁT
- Shard dữ liệu nguồn: `data/raw/phreshphish/data/train-001.parquet` (322.018.201 bytes | SHA-256: `260cb9c93299f6b244d48321fe115523159770f4e73446b382473628c6e81d74`).
- Git revision đã khóa: `eabec4b7a66324b79cc8a0ad856d1731dc26fe1a`.
- Quần thể ứng viên hợp lệ qua Gates 0–3: **1.232 mẫu** (tái lập 100% khớp chuỗi số đếm: 5.780 $\rightarrow$ 2.752 $\rightarrow$ 2.321 $\rightarrow$ 1.232).
- Khóa 4 Seed độc lập:
  + `seed_population`: **42** (giữ nguyên cấu hình kiểm nguồn đã được Lead D nghiệm thu tại commit `8643f55`).
  + `seed_lot_100`: **1017** (rút ngẫu nhiên không hoàn lại 100 mẫu Main cho A).
  + `seed_b_subset_30`: **2042** (rút ngẫu nhiên độc lập 30 mẫu từ lô 100 cho B tính Kappa chính).
  + `seed_release_shuffle`: **2026** (xáo trộn thứ tự hiển thị phát hành chống order bias).
- Mã băm cam kết bí mật (Seed Commitment SHA-256): Được công bố trước trong `main_batch1_release_manifest.json`, hạt giống và salt lưu tại `data/restricted/`.

---

## 5. THAY ĐỔI THỰC TẾ
1. **Module Lấy mẫu SRS (`src/phishing/data/main_sampling.py`)**:
   - Sinh ID trung tính định dạng `BLIND-xxxxxxxx` (8 ký tự hex), hoàn toàn không chứa số lô, nhãn, tổ chức hay phân tầng.
   - Ghép cặp nhất quán: Mẫu được A và B cùng gán dùng CHUNG một `blind_id`.
   - Thứ tự hiển thị của A (100 mẫu) và B (30 mẫu) được xáo trộn độc lập bằng `seed_release_shuffle`.
2. **Sổ cái Quản lý Lô (`src/phishing/data/lot_ledger.py`)**:
   - Lưu tại `data/restricted/main_annotation_lot_management_ledger.json` (nằm trong `.gitignore`).
   - Cấu trúc append-only với chuỗi băm SHA-256 (`event_hash` liên kết `prev_hash`).
   - Hỗ trợ các trạng thái vòng đời: `PREPARED`, `RESERVED`, `RELEASED`, `COMPLETED`, `REVOKED`.
   - Quản lý tập mẫu đã phân bổ để chống chọn trùng ở các đợt sau, **không đưa vào danh sách loại trừ vĩnh viễn** của pilot/hiệu chuẩn.
3. **Cập nhật Hợp đồng Blind View v1.2.0 (`src/phishing/annotation/blind_view.py`)**:
   - Thiết lập allowlist chặt chẽ `ALLOWED_BLIND_SAMPLE_KEYS_V1_2_0`: Giữ nguyên URL quan sát được để người gán đánh giá tương quan thương hiệu – tên miền.
   - Chặn tuyệt đối và báo lỗi fail-closed nếu xuất hiện: `random_subset`, `locator`, `source_row`, `parquet_file`, `parquet_metadata`, `source_label`, `model_score`, `matcher`.
4. **Công cụ Kiểm tra Cách ly Git (`scripts/data/verify_git_isolation.py`)**:
   - Kiểm tra `git check-ignore` trên các đường dẫn probe restricted.
   - Quét `git ls-files` đảm bảo 0 tệp restricted/binary nhạy cảm nào bị Git theo dõi.
   - Quét tài liệu công khai chống rò rỉ trường nhãn nguồn.

---

## 6. TỰ KIỂM: SỐ LIỆU ĐO LƯỜNG VÀ KIỂM CHUỖI VẬN HÀNH
- **Đo lường số lượng**:
  + Quần thể đầu vào: Đúng 1.232 ứng viên.
  + Lô A: Đúng 100 mẫu `BLIND-xxxxxxxx` duy nhất, không trùng lặp.
  + Lô B: Đúng 30 mẫu, 100% là tập con của Lô A, dùng chung `blind_id` tương ứng.
- **Tính xác định**:
  + Chạy lại sampling với cùng bộ seed sinh kết quả và mã băm giống hệt nhau 100%.
- **Phân định vai trò phân xử**:
  + Ghi rõ trong quy trình: A/B khóa tệp $\rightarrow$ C kiểm intake $\rightarrow$ D trực tiếp chủ trì và quyết định phân xử $\rightarrow$ C ghi biên bản $\rightarrow$ B kiểm QA.

---

## 7. KIỂM THỬ: BẰNG CHỨNG TEST SUITE & LOG KIỂM TOÁN
- Bộ kiểm thử hồi quy mới tại `tests/test_main_annotation_batch1.py`:
  + Chạy lệnh: `python -m pytest tests/test_main_annotation_batch1.py -v`
  + Kết quả: **9/9 test cases PASSED (100%) trong 1.99s**.
  + Bao quát: Định dạng blind ID, tính xác định, tập con B, xáo trộn thứ tự, schema v1.2.0, chặn trường cấm, bảo vệ toàn vẹn sổ cái và kiểm tra cách ly Git.
- Kiểm toán cách ly Git thực tế (`scripts/data/verify_git_isolation.py`):
  + Lệnh: `python scripts/data/verify_git_isolation.py`
  + Kết quả: **PASS (100%)**.
  + Báo cáo ghi nhận tại `artifacts/isolation_verification_report.json`.

---

## 8. KẾT LUẬN KIỂM TOÁN BÀN GIAO
- Thành viên C đã hoàn thành 100% công tác chuẩn bị kỹ thuật cho Main Annotation Đợt 1 theo đúng các chỉ đạo của Lead D.
- Toàn bộ hiện vật nhạy cảm (quần thể niêm phong, sổ cái quản lý lô, ánh xạ restricted, và gói mẫu A/B) đã được cô lập nghiêm ngặt trong `data/restricted/`.
- Phần công khai chỉ công bố mã nguồn, kiểm thử, hướng dẫn trung tính, quy trình intake và `main_batch1_release_manifest.json`.

---

## 9. GIỚI HẠN VÀ VIỆC CÒN MỞ
- **Giới hạn kiểm toán**:
  + Do lượt kiểm nguồn trước lưu số đếm (5.780 $\rightarrow$ 2.752 $\rightarrow$ 2.321 $\rightarrow$ 1.232) mà chưa lưu tệp danh sách từng ứng viên, C ghi rõ việc khớp số lượng không tự chứng minh thành viên hoàn toàn giống nhau; quần thể 1.232 ứng viên của đợt này đã được niêm phong và khóa băm độc lập trước khi rút mẫu.
  + Báo cáo cách ly Git kết luận trong đúng phạm vi các tệp và commit đã quét.
- **Việc còn mở**:
  + Chờ QA Lead B thực hiện thẩm định QA kỹ thuật đối với gói phát hành và bộ kiểm thử.
  + Chờ Lead D xem xét và ban hành Lệnh phát hành chính thức trước khi cấp phát Blind View cho Annotator A và B.
  + Tiếp nhận nguyên byte tệp `QA_ADDENDUM_INTEGRATION_DEVELOP_02FCA4F_B.md` khi B chuyển tệp gốc.

---

## 10. TRẠNG THÁI QUẢN TRỊ
- `main_annotation_status = "LOCKED"` (Chưa phát Blind View, chưa mở Pass 1).
- `training_blocked = true` (Tuyệt đối không mở huấn luyện mô hình).
- `official_test_used = false` (Tập test chính thức được bảo vệ cô lập 100%).
