# BẢN ĐÍNH CHÍNH BẢNG KÊ & TỜ TRÌNH HAI QUYẾT ĐỊNH CỔNG CHỌN MẪU MAIN ĐỢT 1 (ERRATA V4.3)

**Kính gửi:** Lead D (Anh Tuấn - Chủ nhiệm Dự án NCKH_2)  
**Đồng kính gửi:** QA Lead B (Phùng Tấn Minh - Phụ trách Đảm bảo Chất lượng Độc lập)  
**Người thực hiện:** Thành viên C (Data Pipeline & Thư ký Kiểm toán)  
**Ngày phát hành:** 17/11/2026  
**Chế độ thực thi:** Duo Mode (Antigravity & DeepSeek Reason Architecture Review - Session R18)  
**Trạng thái Quản trị:** `main_annotation_status="LOCKED"`, `training_blocked=true`, `official_test_used=false`  
**Gói nén kiểm toán đính kèm (cho Lead D):** `data/restricted/pilot_batch1_remediation_pack_lead_d_v4_3.zip` (`1,728,514 bytes` | SHA-256: `f6c9823f4d86299918ad0af07fa7e78fb8c4ead72fc11b3d5abc91eb87a3cc33`)

---

## I. MỤC ĐÍCH PHÁT HÀNH BẢN ĐÍNH CHÍNH ERRATA V4.3

Thực hiện nghiêm túc 4 chỉ đạo trọng tâm của Lead D đối với gói V4.2 và tiếp thu kết quả tham vấn kiến trúc chuyên sâu cùng DeepSeek Reason Mode (Phiên Duo R18), Thành viên C phát hành văn bản **Errata V4.3** độc lập này nhằm:

1. **Chốt chuẩn xác cách công bố số mẫu loại trừ toàn registry:** Giải trình phân tách rõ ràng giữa con số **246** (tổng mục khai báo theo 10 lô) và con số **226** (tổng số cặp mã băm `(raw_url_sha256, raw_html_sha256)` duy nhất toàn registry sau khi kiểm tra mã băm cam kết Lô 10).
2. **Sửa đổi báo cáo Git công khai & Ghi nguồn trung thực trường `lang`:**
   - Loại bỏ hoàn toàn thông tin định vị hàng cụ thể và locator cấp mẫu khỏi tài liệu Git công khai; chỉ ghi nhận chuẩn mực: *"20/20 khớp tại `train-000`, 0/20 khớp tại `train-055` trong phạm vi hai shard đã kiểm"*.
   - Phát hành **Dossier Hạn chế V4**, khôi phục trung thực giá trị `lang = null` nguyên bản từ Rows API gốc (`pilot_20_rows.json`), khắc phục triệt để artifact `NaN` do chuyển đổi kiểu dữ liệu bảng trong Dossier V3.
3. **Viết lại Dự thảo Quyết định 1 (Cho phép tải và kiểm nguồn `train-001.parquet`):**
   - Mô tả chính xác hành vi của Gate 1: chỉ kiểm định tính hợp lệ URL/HTML/cửa sổ ngày, tuyệt đối không có regex matcher 14 tổ chức trong Cổng 1.
   - Bổ sung kiến trúc chế độ `--vetting-only` dừng ngay sau Gate 3, không thực hiện chọn mẫu phân tầng theo hạn ngạch của Gate 4.
   - Báo cáo số ứng viên trước Gate 4 so với chỉ tiêu 100 mẫu; đầu ra là báo cáo kiểm nguồn tổng hợp; quyết định rút 100 mẫu và phát Blind View trình riêng sau.
4. **Bàn giao bằng chứng kiểm thử vật lý & Minh định ranh giới QA của B:**
   - Bàn giao 4 tệp log vật lý chuẩn UTF-8 khớp 100% kết quả công bố: 41 passed (môi trường C), 39 passed / 2 skipped (mô phỏng clean checkout của C), 148 passed (7 test suites), 7 passed (zero git leak regression).
   - Minh định rõ ràng: QA Lead B mới phát hành QA độc lập cho commit `2eddf41` (V4.1, 40 ca test). B chưa phát hành QA cho V4.3. Khi Lead D phê duyệt, C sẽ bàn giao phạm vi công khai để B thẩm định độc lập riêng.
5. **Kính trình Lead D xem xét hai dự thảo quyết định riêng biệt.**

---

## II. ĐỐI SOÁT & CHỐT CÁCH CÔNG BỐ SỐ MẪU LOẠI TRỪ (246 vs 226)

### 1. Cơ sở pháp lý và kỹ thuật:
- Đã kiểm tra SHA-256 tệp cam kết Lô 10: `data/restricted/clean_calibration_exclusion_mapping_c_32.json` (`21,488 bytes` | SHA-256: `67326e80b2a6f9cb7356450a31fe15054a1193412a8ed0576ea2972f1801a805`), khớp 100% với `commitment_sha256` của cam kết `EXCL-CALIBRATION-CLEAN-BATCH-C-RESTRICTED` trong `data/exclusion_registry.json`.
- Đã trích xuất và tính toán hợp cặp `(raw_url_sha256, raw_html_sha256)` trên toàn bộ 10 lô loại trừ bằng script kiểm toán độc lập.

### 2. Kết quả đối soát chi tiết (Lưu tại `data/restricted/registry_10_batches_pairwise_union_audit.json`):

| Cấp độ Thống kê | Số lượng đo đạc | Giải trình bản chất dữ liệu khoa học |
| :--- | :---: | :--- |
| **Tổng mục khai báo theo lô (Declared Items)** | **246 mục** | Tổng cơ học số mục của 10 lô loại trừ trong `data/exclusion_registry.json`. |
| **Số cặp mã băm hợp lệ** | **246 / 246 cặp** | 100% mục khai báo đều có đầy đủ mã băm URL và HTML hợp lệ. |
| **Số trùng lặp nội bộ từng lô** | **0 cặp** | Cả 10 lô đều không có trùng lặp URL/HTML trong nội bộ lô đó. |
| **Số cặp duy nhất trong 9 lô đầu** | **194 cặp** | Do 20 mẫu Pilot Lô 1 (`EXCL-PILOT-01`) nằm hoàn toàn trong Lô Pilot 32 (`EXCL-REAL-PILOT-32`): $20 + 32 - 20 = 32$. Hợp 9 lô đầu: 194 cặp duy nhất. |
| **Số cặp duy nhất trong Lô 10 hạn chế** | **32 cặp** | Toàn bộ 32 mục của `EXCL-CALIBRATION-CLEAN-BATCH-C-RESTRICTED` đều hợp lệ và duy nhất. |
| **Số giao giữa Lô 10 và 9 lô đầu** | **0 cặp** | Lô 10 được đối soát cách ly hoàn toàn, không có bất kỳ mẫu nào trùng với 9 lô trước. |
| **Tổng cặp URL/HTML duy nhất toàn registry (10 lô)** | **226 cặp duy nhất** | $194 + 32 - 0 = \mathbf{226\text{ cặp duy nhất}}$. Con số 226 là số thực đo chính xác, không còn là cận trên lý thuyết. |

* **Quy chuẩn công bố:** Trong mọi văn bản, C sẽ trình bày song song: *"246 mục khai báo trên 10 lô, tương ứng đúng 226 cặp (URL hash, HTML hash) duy nhất toàn registry sau khi khử giao cắt"*.

---

## III. HIỆU CHỈNH BÁO CÁO GIT & PHÁT HÀNH DOSSIER HẠN CHẾ V4

### 1. Khử hoàn toàn vị trí dòng trên tài liệu Git công khai:
- Trong toàn bộ tài liệu Git (`docs/PILOT_BATCH1_AUDIT_AND_SELECTION_GATE_REPORT_LEAD_D.md`, `docs/SELECTION_GATE_ERRATA_V4_3_LEAD_D.md`, `data/exclusion_registry.json`), thông tin định vị hàng cụ thể và locator đã được gỡ bỏ hoàn toàn.
- Chỉ ghi nhận đúng chuẩn mực khoa học: **"20/20 khớp tại `train-000`, 0/20 khớp tại `train-055` trong phạm vi hai shard đã kiểm"**.
- Chi tiết vị trí dòng, shard locator và ánh xạ cấp mẫu tiếp tục được lưu trữ an toàn trong kho hạn chế ngoài Git: `data/restricted/pilot_batch1_sample_level_audit_table.json` và `data/restricted/pilot_batch1_recovery_dossier_restricted_v4.json`.

### 2. Phát hành Dossier Hạn chế V4 phục hồi trường `lang = null`:
- **Nguyên nhân phát sinh lỗi ở V3:** Khi xuất dữ liệu từ bảng biểu trung gian, giá trị `None` (null) của trường `lang` ở bản ghi index 14 bị thư viện pandas ép kiểu thành giá trị thực số học `NaN` (`"lang": NaN`), gây sai lệch so với bản Rows API gốc.
- **Biện pháp xử lý ở V4:**
  - Khôi phục chính xác kiểu dữ liệu JSON gốc: `"lang": null` tại bản ghi index 14, khớp 100% với `pilot_20_rows.json`.
  - Ban hành tệp vật lý: `data/restricted/pilot_batch1_recovery_dossier_restricted_v4.json` (`29,147 bytes` | SHA-256: `17f71f23c2314ebf9c36a0a07f9fe21fe56aa18efec682b75f7ec06baf196171`).
  - Cập nhật mã cam kết `EXCL-PILOT-01` trong `data/exclusion_registry.json` trỏ tới Dossier V4 với `commitment_sha256 = "17f71f23c2314ebf9c36a0a07f9fe21fe56aa18efec682b75f7ec06baf196171"`.
  - Bảo lưu nguyên vẹn Dossier V3, V2, V1 trong lịch sử kiểm toán làm bằng chứng chuỗi phiên bản (Lineage Audit Trail).

---

## IV. NÂNG CẤP KIẾN TRÚC `--vetting-only` VÀ SỬA ĐÚNG HÀNH VI CỔNG 1

### 1. Đính chính hành vi Cổng 1 (Gate 1):
- `gate_1_field_validity` trong `selection_gate.py` chỉ thực hiện kiểm tra tính hợp lệ cơ bản của URL (`http`/`https`, hostname hợp lệ), độ dài HTML trong khoảng `[1, 2,000,000]` bytes, và ngày thu thập nằm trong cửa sổ temporal split `[2024-10-01, 2025-09-08]`.
- Tuyệt đối **không có bộ nhận diện thương hiệu hay regex matcher 14 tổ chức trong Cổng 1**. Mọi mô tả trước đây ghi Cổng 1 có regex 14 tổ chức đều đã được đính chính.

### 2. Bổ sung chế độ chỉ kiểm định `--vetting-only` (Dừng trước Gate 4):
- Đã bổ sung tham số `vetting_only: bool = False` vào `run_selection()` trong `src/phishing/data/selection_gate.py`.
- Khi `vetting_only=True`:
  - Pipeline chạy tuần tự Gate 0, Gate 1, Gate 2, Gate 3.
  - Ngay sau Gate 3, pipeline **DỪNG LẠI**, trả về:
    * `selected_samples = []` (không chọn mẫu nào).
    * `candidates_before_gate_4 = g3_passed` (toàn bộ ứng viên vượt qua Gate 3).
    * `audit_log["vetting_only"] = True`.
  - Tuyệt đối không can thiệp hạn ngạch hay chạy thuật toán quota sampling của Gate 4.
- Đã bổ sung cờ dòng lệnh `--vetting-only` vào `scripts/data/run_main_selection.py`, ghi nhận kết quả ra tệp `source_vetting_audit_manifest.json`.
- Đã thêm kiểm thử hồi quy `test_pipeline_vetting_only_mode_halts_before_gate_4_quota_sampling` vào `tests/test_pilot_batch1_exclusion.py`.

---

## V. ĐỐI SOÁT LOG KIỂM THỬ VẬT LÝ V4.3 & BÀN GIAO GÓI HẠN CHẾ

Thành viên C bàn giao 4 tệp log vật lý chuẩn UTF-8, đo đạc trực tiếp trên đĩa:

1. **`test_report_pilot_batch1_exclusion_v4_3.log`** (`6,119 bytes` | SHA-256: `c85072ebe962e669d38e77e088a24d0d3cfa94e3da1bfff70591a934789ba9cc`):
   - Lệnh chạy: `python -m pytest tests/test_pilot_batch1_exclusion.py -v`
   - Kết quả: **`41 passed in 3.54s`** (Môi trường cục bộ của C có dữ liệu hạn chế).
2. **`test_report_clean_checkout_simulation_v4_3.log`** (`6,070 bytes` | SHA-256: `ac11f924de26477e23a1c8dd356c989914be25316ccd6a67c1c67a6a67ac3cb6`):
   - Lệnh chạy: `python -m pytest tests/test_pilot_batch1_exclusion.py -v` (mô phỏng không có tệp restricted và shard 000).
   - Kết quả: **`39 passed, 2 skipped in 3.15s`** (Tự kiểm mô phỏng clean checkout do C thực hiện).
3. **`test_report_7_suites_v4_3.log`** (`21,785 bytes` | SHA-256: `1a33a6a3105b533956798764742519828a22f0276ac05c141e17557c45b0b014`):
   - Lệnh chạy: 7 bộ test liên quan đến dữ liệu, phân tách và chống rò rỉ.
   - Kết quả: **`148 passed in 10.27s`**.
4. **`test_report_git_leak_v4_3.log`** (`1,741 bytes` | SHA-256: `6cf270d4d694022be927434ae6a9b0a90411d3970b3f196d0fff6d6d0e5fcf91`):
   - Lệnh chạy: `python -m pytest tests/test_clean_calibration_zero_git_leak_regression.py -v`
   - Kết quả: **`7 passed in 0.39s`**.

* **Gói nén bàn giao cho Lead D:** `data/restricted/pilot_batch1_remediation_pack_lead_d_v4_3.zip` (`1,728,514 bytes` | SHA-256: `f6c9823f4d86299918ad0af07fa7e78fb8c4ead72fc11b3d5abc91eb87a3cc33`). Gói chứa đầy đủ Dossier V4, V3, V2, bảng đối soát 10 lô, bảng chi tiết 20 mẫu, Rows API gốc `pilot_20_rows.json`, 4 tệp log kiểm thử và `SHA256SUMS.txt`.

---

## VI. HAI DỰ THẢO QUYẾT ĐỊNH TRÌNH LEAD D XEM XÉT VÀ KÝ BAN HÀNH

```
========================================================================================
DỰ THẢO QUYẾT ĐỊNH 1: CHO PHÉP TẢI VÀ KIỂM NGUỒN SHARD TRAIN-001.PARQUET (BƯỚC 1)
========================================================================================

Căn cứ Source Manifest (configs/source_manifest.json) và Báo cáo Kiểm toán V4.3:

Điều 1. Cho phép Thành viên C thực hiện bước kỹ thuật: Tải về và kiểm tra nguồn đối với shard `train-001.parquet`.
   - Nguồn: phreshphish
   - Git Revision khóa: eabec4b7a66324b79cc8a0ad856d1731dc26fe1a
   - Tên tệp: train-001.parquet
   - Dung lượng dự kiến: 322,018,201 bytes
   - Mã băm SHA-256 Git-LFS pointer dự kiến: 260cb9c93299f6b244d48321fe115523159770f4e73446b382473628c6e81d74
   - Cửa sổ ngày được phép lấy mẫu (Temporal Split): 2024-10-01 đến 2025-09-08

Điều 2. Quy trình kiểm tra kỹ thuật bắt buộc với chế độ `--vetting-only`:
   1. Đo trực tiếp mã băm SHA-256 trên byte thật của tệp Parquet sau khi tải về đĩa cục bộ, đối chiếu với mã băm Git-LFS pointer dự kiến. Cập nhật locally_verified_sha256 trong manifest. Dừng ngay nếu sai lệch.
   2. Chạy toàn bộ bản ghi qua Selection Gate ở chế độ chỉ kiểm định (--vetting-only):
      - Gate 0 (Kiểm tra cách ly Shard): Xác nhận shard không phải train-000 hay train-055.
      - Gate 1 (Tính hợp lệ trường dữ liệu): Kiểm tra tính hợp lệ của URL, độ dài HTML trong khoảng [1, 2,000,000] bytes, và ngày trong cửa sổ [2024-10-01, 2025-09-08]. (Không có regex matcher 14 tổ chức trong Cổng 1).
      - Gate 2 (ExclusionRegistry Anti-Leakage): Đối soát 6 lớp mã băm đối với toàn bộ các cam kết loại trừ trong registry (226 cặp duy nhất trên 10 lô).
      - Gate 3 (Dedup & Template Diversity): Lọc tương đồng SimHash / DOM Tag và đa dạng hóa tên miền (tối đa 1 mẫu/eTLD+1).
      - Dừng trước Gate 4: Chế độ --vetting-only dừng ngay sau Gate 3, KHÔNG thực hiện quota sampling hay phân tầng hạn ngạch của Gate 4.
   3. Báo cáo số ứng viên hợp lệ trước Gate 4 so với chỉ tiêu 100 mẫu.

Điều 3. Tiêu chí dừng an toàn Fail-Closed (Halt Criteria):
   - DỪNG NGAY LẬP TỨC nếu SHA-256 byte thực tế trên đĩa sai lệch so với Git-LFS pointer dự kiến (260cb9c9...).
   - DỪNG NGAY LẬP TỨC nếu xuất hiện bất kỳ ngoại lệ dữ liệu định dạng (ValueError) hoặc ngoại lệ hệ thống (RuntimeError) trong quá trình chạy qua Gate 0–3.
   - DỪNG NGAY LẬP TỨC nếu số lượng ứng viên hợp lệ sau Gate 3 không đạt chỉ tiêu tối thiểu 100 mẫu.
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
   - Nghiệm thu kết quả đối chiếu Parquet tại revision khóa eabec4b7a66324b79cc8a0ad856d1731dc26fe1a: 20/20 cặp URL/HTML khớp tại train-000, khớp 0/20 tại train-055 trong phạm vi hai shard đã kiểm.
   - Xác nhận giữ rows_api_revision_pinned = false theo đúng phương thức thu thập lịch sử.
   - Phê duyệt hồ sơ hạn chế V4 (pilot_batch1_recovery_dossier_restricted_v4.json - SHA-256: 17f71f23c2314ebf9c36a0a07f9fe21fe56aa18efec682b75f7ec06baf196171), giữ nguyên lang = null nguyên bản.

Điều 3. Thực thi loại trừ các mẫu đã biết:
   - Đánh dấu vĩnh viễn 20 mẫu Pilot Lô 1 trong data/exclusion_registry.json với mã cam kết EXCL-PILOT-01 trỏ tới Dossier V4, mã băm commitment_sha256 = "17f71f23c2314ebf9c36a0a07f9fe21fe56aa18efec682b75f7ec06baf196171".
   - Toàn bộ 20 mẫu này bị loại trừ vĩnh viễn (retired) khỏi mọi tập dữ liệu huấn luyện, thẩm định và đánh giá (M0–M3).
   - Xác nhận giải trình số đếm: Con số 246 là tổng mục khai báo theo lô (declared batch items); tổng số cặp (url_sha256, html_sha256) duy nhất toàn registry (10 lô) theo phép hợp thực tế đã đối soát là đúng 226 cặp duy nhất (chi tiết tại bảng kê data/restricted/registry_10_batches_pairwise_union_audit.json).

Điều 4. Phạm vi Shard cách ly:
   - Cách ly vĩnh viễn shard `train-000.parquet` (QUARANTINED), cấm mọi hành vi trích xuất từ shard này cho Main Annotation.

Điều 5. Thừa nhận giới hạn khoa học & Rủi ro tồn dư:
   - Thừa nhận trung thực trong các báo cáo khoa học: Phạm vi kiểm vị trí duy nhất đã hoàn thành trên 2 shard đã quét (train-000 và train-055). 6 lớp mã băm của Cổng 2 và cơ chế lọc tương đồng của Cổng 3 sẽ tiếp tục bảo vệ các đợt trích xuất mới.
   - Toàn bộ bảng chi tiết cấp mẫu (ID, locator, nhãn nguồn, tên miền) tiếp tục được niêm phong an toàn tại khu vực hạn chế ngoài Git (data/restricted/).
========================================================================================
```

---

## VII. BẢNG MÃ BĂM KIỂM TOÁN ĐỐI CHIẾU V4.3 (AUDITED HASHES V4.3)

Toàn bộ kích thước và mã băm SHA-256 đo đạc trực tiếp trên byte vật lý thực tế:

| Tệp tin / Cấu phần | Vị trí / Tình trạng | Kích thước (bytes) | Mã băm SHA-256 |
| :--- | :--- | :---: | :--- |
| **Gói nén kiểm toán V4.3 gửi D (Hiện hành)** | `data/restricted/pilot_batch1_remediation_pack_lead_d_v4_3.zip` | 1,728,514 | `f6c9823f4d86299918ad0af07fa7e78fb8c4ead72fc11b3d5abc91eb87a3cc33` |
| **Hồ sơ hạn chế V4 (Lineage V3 - Hiện hành)** | `data/restricted/pilot_batch1_recovery_dossier_restricted_v4.json` | 29,147 | `17f71f23c2314ebf9c36a0a07f9fe21fe56aa18efec682b75f7ec06baf196171` |
| **Bảng đối soát hợp 10 lô loại trừ (ngoài Git)** | `data/restricted/registry_10_batches_pairwise_union_audit.json` | 3,052 | `057c5ea1433cfe4559db5c135e0a8f207459fa0fa77cec2073595d18d9ffa0b7` |
| **Bản đính chính Errata V4.3 (Tệp này)** | `docs/SELECTION_GATE_ERRATA_V4_3_LEAD_D.md` | Bản phát hành chính thức | Tham chiếu commit V4.3 |
| **Báo cáo kiểm toán tổng hợp V4.3** | `docs/PILOT_BATCH1_AUDIT_AND_SELECTION_GATE_REPORT_LEAD_D.md` | Báo cáo chính thức | Tham chiếu commit V4.3 |
| **Tài liệu đặc tả QA công khai (Giữ nguyên byte đã QA)** | `docs/SELECTION_GATE_QA_SPEC_PACK_B.md` | 8,496 | `ca9a5af3d8e0abadf26eb4a19374b0d97820cf2dffb30ca2d80d457be9067d09` |
| **Biên bản QA độc lập của B (Commit `2eddf41`)** | `docs/QA_REPORT_SELECTION_GATE_2EDDF41_B.md` | 26,507 | `45dacb831c5f6ceb40570f3870bbe3245a3b2ef9d16c1e2b6c1af3a76f6fda4b` |
| **Exclusion Registry V1.1.0** | `data/exclusion_registry.json` | 107,712 | `aee8c4f398e5b74240501d67e373434e80cca2f1395c6dcab22ad8d3507ce9bc` |
| **Báo cáo kiểm toán Exclusion Audit** | `data/source_audit/clean_calibration_exclusion_audit_report.json` | 7,652 | `3ea039ff3060ddc9218a041381de3946c7b575d3b82bed41b72ed14e346c4700` |
| **Clean Calibration Manifest** | `configs/calibration_clean_a_manifest.json` | 7,365 | `6c7de2e6b55b1c872c53c4a9fb90c9491bdaabe70b50c382484e4cd397490e70` |
| **Module loại trừ (Đã sửa import & fail-closed)** | `src/phishing/data/exclusion.py` | 19,448 | `5cc8a445b20bb251df523e258f957215134cb804859de3855dff49db856aa041` |
| **Cổng chọn mẫu Selection Gate (Hỗ trợ vetting-only)** | `src/phishing/data/selection_gate.py` | 20,966 | `efdfee043ed911e646fddea446c673ee131bc248aa72990150642579c470cd0c` |
| **Runner chọn mẫu thực tế (Thêm --vetting-only)** | `scripts/data/run_main_selection.py` | 5,226 | `d6ed1639742c5cedb328d1b382f6382fff21880d36155088c1858727253498d3` |
| **Bộ kiểm thử 41 ca (Bổ sung test vetting-only)** | `tests/test_pilot_batch1_exclusion.py` | 44,615 | `9be6dc954c76f386535a229446c4ee69cde2f9a4f74eb71b6a762893b52d4cea` |
| **Log 41 tests (Môi trường Cục bộ C)** | `test_report_pilot_batch1_exclusion_v4_3.log` | 6,119 | `c85072ebe962e669d38e77e088a24d0d3cfa94e3da1bfff70591a934789ba9cc` |
| **Log 39 passed / 2 skipped (Tự kiểm mô phỏng)** | `test_report_clean_checkout_simulation_v4_3.log` | 6,070 | `ac11f924de26477e23a1c8dd356c989914be25316ccd6a67c1c67a6a67ac3cb6` |
| **Log 148 tests (7 test suites)** | `test_report_7_suites_v4_3.log` | 21,785 | `1a33a6a3105b533956798764742519828a22f0276ac05c141e17557c45b0b014` |
| **Log 7 tests (Zero Git leak regression)** | `test_report_git_leak_v4_3.log` | 1,741 | `6cf270d4d694022be927434ae6a9b0a90411d3970b3f196d0fff6d6d0e5fcf91` |

---

## VIII. TRẠNG THÁI QUẢN TRỊ & RANH GIỚI TRÁCH NHIỆM

* **Trạng thái hệ thống tiếp tục khóa chặt:**
  * `main_annotation_status = "LOCKED"`
  * `training_blocked = true`
  * `official_test_used = false`
* **Ranh giới trách nhiệm:**
  * Thành viên C tuyệt đối chưa tải shard `train-001.parquet`, chưa chạy lệnh rút 100 mẫu Main, chưa tạo và chưa phát Blind View cho A/B khi Lead D chưa ký lệnh phê duyệt nguồn.
  * Mọi bước kỹ thuật tiếp theo chỉ được kích hoạt sau khi Lead D phê duyệt Quyết định 1 và Quyết định 2 nêu trên.