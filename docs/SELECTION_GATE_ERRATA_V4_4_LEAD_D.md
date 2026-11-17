# BẢN ĐÍNH CHÍNH BẢNG KÊ & TỜ TRÌNH HAI QUYẾT ĐỊNH CỔNG CHỌN MẪU MAIN ĐỢT 1 (ERRATA V4.4)

**Kính gửi:** Lead D (Anh Tuấn - Chủ nhiệm Dự án NCKH_2)  
**Đồng kính gửi:** QA Lead B (Phùng Tấn Minh - Phụ trách Đảm bảo Chất lượng Độc lập)  
**Người thực hiện:** Thành viên C (Data Pipeline & Thư ký Kiểm toán)  
**Ngày phát hành:** 17/11/2026  
**Chế độ thực thi:** Solo Antigravity (Tuân thủ nghiêm cẩn Ponytail Discipline & ARS)  
**Trạng thái Quản trị:** `main_annotation_status="LOCKED"`, `training_blocked=true`, `official_test_used=false`  
**Gói nén kiểm toán đính kèm (cho Lead D):** `data/restricted/pilot_batch1_remediation_pack_lead_d_v4_4.zip` (`1,736,373 bytes` | SHA-256: `91ccfa65078f1676695ccff91026cd37b38e0e63dde6f79a7b63bf9d1beec107`)

---

## I. MỤC ĐÍCH PHÁT HÀNH BẢN ĐÍNH CHÍNH ERRATA V4.4

Thực hiện nghiêm túc 4 chỉ đạo trọng tâm của Lead D tại Vòng 19 đối với gói V4.3, Thành viên C phát hành văn bản **Errata V4.4** độc lập này nhằm:

1. **Bàn giao đầy đủ bằng chứng kỹ thuật để Lead D tái lập độc lập con số 226:**
   - Chuyển bản nguyên byte tệp mapping Lô 10: `clean_calibration_exclusion_mapping_c_32.json` (`21,488 bytes` | SHA-256: `67326e80b2a6f9cb7356450a31fe15054a1193412a8ed0576ea2972f1801a805`).
   - Cung cấp script kiểm toán độc lập `scripts/data/audit_exclusion_registry_union.py` để Lead D tự tái lập phép hợp 10 lô với kết quả: **194 cặp duy nhất ở 9 lô đầu**, **32 cặp duy nhất ở Lô 10**, và **0 cặp giao nhau**.
   - Trong lúc chờ Lead D đối chiếu, công bố quy chuẩn: **246 mục khai báo theo lô** và **226 cặp duy nhất theo kiểm toán của C**.
2. **Khử triệt để chuỗi vị trí dòng cụ thể khỏi tài liệu Git bản hiện hành:**
   - Loại bỏ hoàn toàn các chuỗi chỉ vị trí dòng cụ thể khỏi bản hiện hành của `PILOT_BATCH1_AUDIT_AND_SELECTION_GATE_REPORT_LEAD_D.md` và `SELECTION_GATE_ERRATA_V4_4_LEAD_D.md`.
   - Chuẩn hóa câu công khai duy nhất: **“20/20 khớp tại `train-000`, 0/20 khớp tại `train-055`, trong phạm vi hai shard đã kiểm.”**
   - Xác định rõ phạm vi tự kiểm tài liệu là **bản hiện hành**, do lịch sử Git thuộc thẩm quyền quyết định riêng của Lead D.
3. **Giới hạn đầu ra `--vetting-only` ở số liệu tổng hợp & Hiệu chỉnh Cổng 1:**
   - Sửa hàm `run_selection()`: Loại bỏ hoàn toàn danh sách bản ghi `candidates_before_gate_4` khỏi kết quả trả về của nhánh kiểm nguồn. Kết quả chỉ trả về `selected_samples: []` và `audit_log`.
   - Cập nhật bộ kiểm thử hồi quy chứng minh: Chế độ kiểm nguồn dừng trước Gate 4 và đầu ra không có danh sách ứng viên hay nội dung bản ghi; dưới 100 ứng viên vẫn ghi nhận số đếm, `meets_quota_target=False` và trạng thái `vetted_insufficient_quota` (đã kiểm nguồn nhưng chưa đủ quota); chế độ tuyển chọn bình thường vẫn fail-closed khi thiếu quota.
   - Sửa mô tả Gate 1 thành **giới hạn ký tự HTML** (`len(html)` trên chuỗi, `[1, 2.000.000]` ký tự), và cửa sổ ngày `2024-10-01` đến `2025-09-08` là **điều kiện ngày ở bước kiểm nguồn**.
4. **Kiểm tích hợp động đúng dossier registry đang cam kết:**
   - Sửa ca test `test_gate2_integration_with_committed_restricted_dossier` để lấy động đường dẫn `restricted_dossier_reference` và mã băm `commitment_sha256` từ mục `EXCL-PILOT-01` của `data/exclusion_registry.json`.
   - Xác nhận byte thật của dossier khớp chính xác cam kết, rồi kiểm một bản ghi lấy từ chính dossier đó bị Gate 2 từ chối đúng lý do `reject_exclusion_registry_match`.
   - Trên clean checkout: ca test tự động bỏ qua (skip) có lý do rõ ràng.
5. **Kính trình Lead D hai dự thảo quyết định riêng biệt.**

---

## II. BẰNG CHỨNG TÁI LẬP CON SỐ 226 MẪU DUY NHẤT (LÔ 10 & SCRIPT KIỂM TOÁN)

### 1. Bàn giao tệp mapping Lô 10 nguyên byte:
- Tệp: `data/restricted/clean_calibration_exclusion_mapping_c_32.json`
- Kích thước: **`21,488 bytes`**
- Mã băm SHA-256: **`67326e80b2a6f9cb7356450a31fe15054a1193412a8ed0576ea2972f1801a805`**
- Đối chiếu cam kết: Khớp 100% với trường `commitment_sha256` của cam kết `EXCL-CALIBRATION-CLEAN-BATCH-C-RESTRICTED` trong `data/exclusion_registry.json`.
- Tệp đã được đóng gói trực tiếp vào gói nén `data/restricted/pilot_batch1_remediation_pack_lead_d_v4_4.zip`.

### 2. Script kiểm toán độc lập tái lập số liệu:
- Tệp script: `scripts/data/audit_exclusion_registry_union.py` (`5,092 bytes` | SHA-256: `70dea2b358256d928f8863ccf8ee73a28153a83f775ec0ffe74e8396646e14b5`).
- Lệnh thực thi:
  ```bash
  python scripts/data/audit_exclusion_registry_union.py
  ```
- **Đầu vào kiểm toán:**
  * Registry commit hiện hành: `e9ab8e9` / `HEAD`.
  * Dossier V4 (`EXCL-PILOT-01`): `data/restricted/pilot_batch1_recovery_dossier_restricted_v4.json` (`29,147 bytes` | SHA-256: `17f71f23...`).
  * Mapping Lô 10 (`EXCL-CALIBRATION-CLEAN-BATCH-C-RESTRICTED`): `data/restricted/clean_calibration_exclusion_mapping_c_32.json` (`21,488 bytes` | SHA-256: `67326e80...`).
- **Đầu ra tái lập độc lập:**

```
================================================================================
EXCLUSION REGISTRY 10-BATCH PAIRWISE UNION & CARDINALITY AUDIT
================================================================================
Batch  1 | EXCL-PILOT-01                                      | declared=20 | valid=20 | unique=20 | dups=0
Batch  2 | EXCL-REAL-PILOT-32                                 | declared=32 | valid=32 | unique=32 | dups=0
Batch  3 | EXCL-PILOT-02                                      | declared=32 | valid=32 | unique=32 | dups=0
Batch  4 | EXCL-PILOT-02-REBUILD-e039c774ef5f                 | declared=32 | valid=32 | unique=32 | dups=0
Batch  5 | EXCL-CALIBRATION-PROPOSAL-V1.1-MAIN-24             | declared=24 | valid=24 | unique=24 | dups=0
Batch  6 | EXCL-CALIBRATION-PROPOSAL-V1.1-RESERVE-08          | declared= 8 | valid= 8 | unique= 8 | dups=0
Batch  7 | EXCL-CALIB-CLEAN-32-EXPOSED-ON-GIT                 | declared=32 | valid=32 | unique=32 | dups=0
Batch  8 | EXCL-CALIB-CLEAN-02-PAIRWISE-RESOLUTION-LOCATOR-EXPOSED | declared= 2 | valid= 2 | unique= 2 | dups=0
Batch  9 | EXCL-CALIBRATION-CLEAN-RUNWAY-32                   | declared=32 | valid=32 | unique=32 | dups=0
Batch 10 | EXCL-CALIBRATION-CLEAN-BATCH-C-RESTRICTED          | declared=32 | valid=32 | unique=32 | dups=0
--------------------------------------------------------------------------------
Tổng mục khai báo theo lô (Declared):      246 mục
Tổng số cặp mã băm hợp lệ:                246 cặp
Số cặp duy nhất trong 9 lô đầu (Batches 1-9): 194 cặp
Số cặp duy nhất trong Lô 10 (Batch 10):        32 cặp
Số giao giữa Lô 10 và 9 lô đầu (Intersection): 0 cặp
Tổng cặp duy nhất toàn registry (10 lô):      226 cặp duy nhất
================================================================================
```

- **Quy chuẩn công bố trong lúc chờ Lead D đối chiếu:**
  C trình bày thống nhất: **246 mục khai báo theo lô** và **226 cặp duy nhất theo kiểm toán của C**. Toàn bộ mapping, hash cấp mẫu và locator tiếp tục được lưu trữ an toàn trong kho hạn chế ngoài Git.

---

## III. KHỬ TRIỆT ĐỂ CHUỖI VỊ TRÍ DÒNG KHỎI TÀI LIỆU GIT BẢN HIỆN HÀNH

- Toàn bộ các chuỗi chỉ vị trí dòng cụ thể đã được gỡ bỏ khỏi bản hiện hành của `docs/PILOT_BATCH1_AUDIT_AND_SELECTION_GATE_REPORT_LEAD_D.md` và `docs/SELECTION_GATE_ERRATA_V4_4_LEAD_D.md`.
- Câu công khai chuẩn mực duy nhất được sử dụng trong toàn bộ tài liệu:
  > **“20/20 khớp tại `train-000`, 0/20 khớp tại `train-055`, trong phạm vi hai shard đã kiểm.”**
- Mô tả sự cố Git được diễn đạt trung thực: *"Trong commit `ad445a7`, bảng đối soát chi tiết cấp mẫu (Entry ID, locator shard, nhãn nguồn, ngày và tên miền) đã vô tình xuất hiện trên Git"*.
- Vị trí cụ thể, shard locator và ánh xạ cấp mẫu tiếp tục được bảo vệ tuyệt đối trong kho hạn chế ngoài Git (`data/restricted/pilot_batch1_sample_level_audit_table.json` và `data/restricted/pilot_batch1_recovery_dossier_restricted_v4.json`).
- Khi tự kiểm tài liệu, Thành viên C xác định rõ phạm vi kiểm tra là **bản hiện hành**, do lịch sử Git thuộc quyết định xử lý riêng của Lead D.

---

## IV. GIỚI HẠN ĐẦU RA `--vetting-only` VÀ HIỆU CHỈNH CỔNG 1

### 1. Giới hạn đầu ra ở số liệu tổng hợp:
- Đã sửa đổi `run_selection()` trong `src/phishing/data/selection_gate.py`: Nhánh `vetting_only=True` chỉ trả về:
  ```python
  return {
      "selected_samples": [],
      "audit_log": audit_log,
  }
  ```
  Tuyệt đối không trả về trường `candidates_before_gate_4` chứa danh sách bản ghi hay nội dung thô của các ứng viên.
- `audit_log` chỉ chứa số liệu tổng hợp:
  * `"candidates_before_gate_4": len(g3_passed)` (số lượng ứng viên dạng số nguyên).
  * `"quota_target": target_quota`.
  * `"meets_quota_target": len(g3_passed) >= target_quota`.
  * `"vetting_status": "vetted_meets_quota" if len(g3_passed) >= target_quota else "vetted_insufficient_quota"`.

### 2. Cập nhật kiểm thử hồi quy:
- Ca test `test_pipeline_vetting_only_mode_halts_before_gate_4_quota_sampling` trong `tests/test_pilot_batch1_exclusion.py` đã chứng minh:
  1. Chế độ kiểm nguồn dừng trước Gate 4 và đầu ra không có danh sách ứng viên (`assert "candidates_before_gate_4" not in res`).
  2. Trường hợp dưới 100 ứng viên vẫn ghi nhận số đếm, `meets_quota_target=False` và trạng thái `vetted_insufficient_quota` (đã kiểm nguồn nhưng chưa đủ quota), không ném lỗi.
  3. Chế độ tuyển chọn bình thường (`vetting_only=False`) với cùng dữ liệu ném `SelectionGateError` fail-closed an toàn.
  4. Trường hợp đạt đủ quota ở chế độ kiểm nguồn ghi nhận `meets_quota_target=True`, `vetted_meets_quota`, và `selected_samples == []`.

### 3. Hiệu chỉnh mô tả Cổng 1:
- Cổng 1 được chuẩn hóa: **giới hạn ký tự HTML** (`len(html)` trên chuỗi, khoảng `[1, 2.000.000]` ký tự).
- Cửa sổ ngày `2024-10-01` đến `2025-09-08` được mô tả là **điều kiện ngày ở bước kiểm nguồn**.
- Tuyên bố kiểm toán minh bạch: Cổng 1 hoàn toàn không chứa regex matcher hay nhận diện thương hiệu 14 tổ chức.

---

## V. KIỂM TÍCH HỢP ĐỘNG ĐÚNG DOSSIER REGISTRY ĐANG CAM KẾT

- Đã sửa đổi ca kiểm thử tích hợp trong `tests/test_pilot_batch1_exclusion.py` thành `test_gate2_integration_with_committed_restricted_dossier`:
  * Đọc động tệp `data/exclusion_registry.json`.
  * Tìm mục `EXCL-PILOT-01`, trích xuất `restricted_dossier_reference` và `commitment_sha256`.
  * Nếu tệp hạn chế không tồn tại (trên clean checkout): Ca test tự động bỏ qua (skip) với thông báo rõ ràng: `Chưa có hồ sơ restricted 'data/restricted/pilot_batch1_recovery_dossier_restricted_v4.json' trên clean checkout`.
  * Nếu tệp hạn chế tồn tại (môi trường có dữ liệu hạn chế):
    1. Xác nhận mã băm byte thực tế của tệp khớp chính xác mã băm cam kết trong registry (`assert actual_sha == expected_sha`).
    2. Nạp dữ liệu dossier, lấy một bản ghi từ chính dossier đó, và kiểm tra Gate 2 từ chối đúng lý do `reject_exclusion_registry_match`.
- Loại bỏ hoàn toàn biến cứng `REAL_DOSSIER_V2_PATH` khỏi bộ test.

---

## VI. BÀN GIAO GÓI NÉN KIỂM TOÁN V4.4 & 4 TỆP LOG VẬT LÝ

### 1. Gói nén kiểm toán bàn giao cho Lead D:
- Đường dẫn: `data/restricted/pilot_batch1_remediation_pack_lead_d_v4_4.zip`
- Kích thước: **`1,736,373 bytes`**
- Mã băm SHA-256: **`91ccfa65078f1676695ccff91026cd37b38e0e63dde6f79a7b63bf9d1beec107`**
- Gói chứa đầy đủ 14 hiện vật kỹ thuật kèm `SHA256SUMS.txt`, bao gồm: mapping Lô 10 nguyên byte, Dossier V4, V3, V2, bảng đối soát 10 lô, script kiểm toán tái lập, bảng cấp mẫu 20 mục, Rows API gốc `pilot_20_rows.json`, và 4 tệp log kiểm thử V4.4.

### 2. 4 Tệp Log Kiểm thử Vật lý Chuẩn UTF-8 (Đo đạc thực tế trên đĩa):
1. **`test_report_pilot_batch1_exclusion_v4_4.log`** (`6,019 bytes` | SHA-256: `cca5b08f3b21cd16faad8e2bfbcb3d389da31bf0b00ef9becb3e863018f93081`):
   - Lệnh: `python -m pytest tests/test_pilot_batch1_exclusion.py -v`
   - Kết quả: **`41 passed in 2.66s`** (Môi trường cục bộ của C có dữ liệu hạn chế).
2. **`test_report_clean_checkout_simulation_v4_4.log`** (`6,021 bytes` | SHA-256: `72ca4de6f9d0bdd41a004961373f8206d7e591017319aadc1777b0787d99f596`):
   - Lệnh: `python -m pytest tests/test_pilot_batch1_exclusion.py -v` (mô phỏng không có tệp restricted và shard 000).
   - Kết quả: **`39 passed, 2 skipped in 2.39s`** (Tự kiểm mô phỏng clean checkout do C thực hiện).
3. **`test_report_7_suites_v4_4.log`** (`21,471 bytes` | SHA-256: `c47c2dbaad1f6a56ed9a9c31ac8d92b8fb37ecf12abc86942bcf400f9c69c4aa`):
   - Lệnh: 7 bộ test dữ liệu, phân tách và chống rò rỉ.
   - Kết quả: **`148 passed in 10.75s`**.
4. **`test_report_git_leak_v4_4.log`** (`1,707 bytes` | SHA-256: `785b7781f119f1c24a8c0a354b2e89aa774836b351ab23696fc8947b4a2e8762`):
   - Lệnh: `python -m pytest tests/test_clean_calibration_zero_git_leak_regression.py -v`
   - Kết quả: **`7 passed in 0.36s`** (Xác nhận 100% không rò rỉ Git).

---

## VII. HAI DỰ THẢO QUYẾT ĐỊNH TRÌNH LEAD D XEM XÉT VÀ KÝ BAN HÀNH

```
========================================================================================
DỰ THẢO QUYẾT ĐỊNH 1: CHO PHÉP TẢI VÀ KIỂM NGUỒN SHARD TRAIN-001.PARQUET (BƯỚC 1)
========================================================================================

Căn cứ Source Manifest (configs/source_manifest.json) và Báo cáo Kiểm toán V4.4:

Điều 1. Cho phép Thành viên C thực hiện bước kỹ thuật: Tải về và kiểm tra nguồn đối với shard `train-001.parquet`.
   - Nguồn: phreshphish
   - Git Revision khóa: eabec4b7a66324b79cc8a0ad856d1731dc26fe1a
   - Tên tệp: train-001.parquet
   - Dung lượng dự kiến: 322,018,201 bytes
   - Mã băm SHA-256 Git-LFS pointer dự kiến: 260cb9c93299f6b244d48321fe115523159770f4e73446b382473628c6e81d74
   - Cửa sổ ngày được phép lấy mẫu (Temporal Split): 2024-10-01 đến 2025-09-08 (điều kiện ngày ở bước kiểm nguồn).

Điều 2. Quy trình kiểm tra kỹ thuật bắt buộc với chế độ `--vetting-only`:
   1. Đo trực tiếp mã băm SHA-256 trên byte thật của tệp Parquet sau khi tải về đĩa cục bộ, đối chiếu với mã băm Git-LFS pointer dự kiến. Cập nhật locally_verified_sha256 trong manifest. Dừng ngay nếu sai lệch.
   2. Chạy toàn bộ bản ghi qua Selection Gate ở chế độ chỉ kiểm định (--vetting-only):
      - Gate 0 (Kiểm tra cách ly Shard): Xác nhận shard không phải train-000 hay train-055.
      - Gate 1 (Tính hợp lệ trường dữ liệu): Kiểm tra tính hợp lệ cơ bản của URL, giới hạn ký tự HTML trong khoảng [1, 2,000,000] ký tự, và ngày trong cửa sổ [2024-10-01, 2025-09-08] (điều kiện ngày ở bước kiểm nguồn). Tuyệt đối không có regex matcher 14 tổ chức trong Cổng 1.
      - Gate 2 (ExclusionRegistry Anti-Leakage): Đối soát 6 lớp mã băm đối với toàn bộ các cam kết loại trừ trong registry (226 cặp duy nhất trên 10 lô).
      - Gate 3 (Dedup & Template Diversity): Lọc tương đồng SimHash / DOM Tag và đa dạng hóa tên miền (tối đa 1 mẫu/eTLD+1).
      - Dừng trước Gate 4: Chế độ --vetting-only dừng ngay sau Gate 3, KHÔNG thực hiện quota sampling hay phân tầng hạn ngạch của Gate 4; đầu ra không có danh sách ứng viên hay nội dung bản ghi thô.
   3. Báo cáo số ứng viên hợp lệ trước Gate 4 so với chỉ tiêu 100 mẫu. Trường hợp dưới 100 ứng viên vẫn ghi nhận số đếm, meets_quota_target=False và trạng thái 'vetted_insufficient_quota' (đã kiểm nguồn nhưng chưa đủ quota).

Điều 3. Tiêu chí dừng an toàn Fail-Closed (Halt Criteria):
   - DỪNG NGAY LẬP TỨC nếu SHA-256 byte thực tế trên đĩa sai lệch so với Git-LFS pointer dự kiến (260cb9c9...).
   - DỪNG NGAY LẬP TỨC nếu xuất hiện bất kỳ ngoại lệ dữ liệu định dạng (ValueError) hoặc ngoại lệ hệ thống (RuntimeError) trong quá trình chạy qua Gate 0–3.
   - DỪNG NGAY LẬP TỨC nếu số lượng ứng viên hợp lệ sau Gate 3 không đạt chỉ tiêu tối thiểu 100 mẫu khi chạy ở chế độ tuyển chọn thực nghiệm.
   - Khi dừng, lập tức niêm phong log, báo cáo Lead D, không xuất danh sách rút mẫu.

Điều 4. Sản phẩm báo cáo sau bước kiểm nguồn:
   - Báo cáo kiểm nguồn tổng hợp (tổng số hàng, số mẫu qua từng cổng, số mẫu bị loại theo từng lý do, các sai lệch phát hiện và phần còn chưa xác minh).
   - Quyết định này CHỈ cho phép kiểm nguồn kỹ thuật, CHƯA cho phép rút 100 mẫu Main, CHƯA mở Main Annotation và CHƯA phát Blind View cho A và B. Quyết định rút 100 mẫu và phát Blind View sẽ được trình riêng sau khi có báo cáo kiểm nguồn đạt yêu cầu.
========================================================================================
```

```
========================================================================================
DỰ THẢO QUYẾT ĐỊNH 2: XỬ LÝ SỰ CỐ GIT CỦA PILOT TẠI COMMIT AD445A7 & NGHIỆM THU CHUỖI BẰNG CHỨNG PILOT 20
========================================================================================

Căn cứ Biên bản Sự cố docs/INCIDENT_REPORT_GIT_EXPOSURE_AD445A7.md, Gói xác minh data/restricted/pilot20_provenance_handoff_for_C_RESTRICTED.zip và Hồ sơ hạn chế V4:

Điều 1. Phê duyệt áp dụng Phương án A (Forward-Fix & Administrative Retirement):
   - Giữ nguyên lịch sử commit trên Git nhằm bảo toàn audit trail minh bạch, phục vụ đánh giá khoa học và kiểm toán độc lập.
   - Không thực hiện force-push hoặc viết lại lịch sử Git (git-filter-repo) trên nhánh cộng tác.

Điều 2. Nghiệm thu chuỗi bằng chứng xác minh Pilot 20:
   - Nghiệm thu bản phản hồi Rows API gốc data/source_audit/phreshphish/pilot_20_rows.json (7,186,229 bytes | SHA-256 738ea69b920cb3037d7e9da38590024d8faa5f34c2eca6c760cb34690f2f190f), khớp 100% hash lịch sử công bố tại bc674e9 và a62105a.
   - Nghiệm thu kết quả đối chiếu Parquet tại revision khóa eabec4b7a66324b79cc8a0ad856d1731dc26fe1a: 20/20 khớp tại train-000, 0/20 khớp tại train-055, trong phạm vi hai shard đã kiểm.
   - Xác nhận giữ rows_api_revision_pinned = false theo đúng phương thức thu thập lịch sử.
   - Phê duyệt hồ sơ hạn chế V4 (pilot_batch1_recovery_dossier_restricted_v4.json - SHA-256: 17f71f23c2314ebf9c36a0a07f9fe21fe56aa18efec682b75f7ec06baf196171), giữ nguyên lang = null nguyên bản.

Điều 3. Thực thi loại trừ các mẫu đã biết:
   - Đánh dấu vĩnh viễn 20 mẫu Pilot Lô 1 trong data/exclusion_registry.json với mã cam kết EXCL-PILOT-01 trỏ tới Dossier V4, mã băm commitment_sha256 = "17f71f23c2314ebf9c36a0a07f9fe21fe56aa18efec682b75f7ec06baf196171".
   - Toàn bộ 20 mẫu này bị loại trừ vĩnh viễn (retired) khỏi mọi tập dữ liệu huấn luyện, thẩm định và đánh giá (M0–M3).
   - Xác nhận quy chuẩn công bố số đếm: 246 mục khai báo theo lô (declared batch items) và 226 cặp duy nhất theo kiểm toán của C (tương ứng đúng 226 cặp (url_sha256, html_sha256) duy nhất toàn registry sau khi khử giao cắt).

Điều 4. Phạm vi Shard cách ly:
   - Cách ly vĩnh viễn shard `train-000.parquet` (QUARANTINED), cấm mọi hành vi trích xuất từ shard này cho Main Annotation.

Điều 5. Thừa nhận giới hạn khoa học & Rủi ro tồn dư:
   - Thừa nhận trung thực trong các báo cáo khoa học: Phạm vi kiểm vị trí duy nhất đã hoàn thành trên 2 shard đã quét (train-000 và train-055). 6 lớp mã băm của Cổng 2 và cơ chế lọc tương đồng của Cổng 3 sẽ tiếp tục bảo vệ các đợt trích xuất mới.
   - Toàn bộ bảng chi tiết cấp mẫu (ID, locator, nhãn nguồn, tên miền) tiếp tục được niêm phong an toàn tại khu vực hạn chế ngoài Git (data/restricted/).
========================================================================================
```

---

## VIII. TRẠNG THÁI QUẢN TRỊ & RANH GIỚI TRÁCH NHIỆM

* **Trạng thái hệ thống tiếp tục khóa chặt:**
  * `main_annotation_status = "LOCKED"`
  * `training_blocked = true`
  * `official_test_used = false`
* **Ranh giới trách nhiệm:**
  * Thành viên C tuyệt đối chưa tải shard `train-001.parquet`, chưa chạy lệnh rút 100 mẫu Main, chưa tạo và chưa phát Blind View cho A/B khi Lead D chưa ký lệnh phê duyệt nguồn.
  * Mọi bước kỹ thuật tiếp theo chỉ được kích hoạt sau khi Lead D phê duyệt Quyết định 1 và Quyết định 2 nêu trên.
