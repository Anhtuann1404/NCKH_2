# BẢN ĐÍNH CHÍNH BẢNG KÊ & TỜ TRÌNH HAI QUYẾT ĐỊNH CỔNG CHỌN MẪU MAIN ĐỢT 1 (ERRATA V4.2)

**Kính gửi:** Lead D (Anh Tuấn - Chủ nhiệm Dự án NCKH_2)  
**Đồng kính gửi:** QA Lead B (Phùng Tấn Minh - Phụ trách Đảm bảo Chất lượng Độc lập)  
**Người thực hiện:** Thành viên C (Data Pipeline & Thư ký Kiểm toán)  
**Ngày phát hành:** 17/11/2026  
**Commit tham chiếu:** [`2eddf41b5fe9148f5b502cb82b101635f804d5b6`](https://github.com/Anhtuann1404/NCKH_2/commit/2eddf41b5fe9148f5b502cb82b101635f804d5b6) (nhánh `feat/c-calibration-v1-1-4-adjudication`)  
**Biên bản QA độc lập của B:** [`docs/QA_REPORT_SELECTION_GATE_2EDDF41_B.md`](file:///d:/nguyen%20thang/NCKH/NCKH_2/docs/QA_REPORT_SELECTION_GATE_2EDDF41_B.md) (`26,507 bytes` | SHA-256: `45dacb831c5f6ceb40570f3870bbe3245a3b2ef9d16c1e2b6c1af3a76f6fda4b`)  
**Trạng thái Quản trị:** `main_annotation_status="LOCKED"`, `training_blocked=true`, `official_test_used=false`

---

## I. MỤC ĐÍCH PHÁT HÀNH BẢN ĐÍNH CHÍNH ERRATA V4.2

Tiếp thu chỉ đạo trực tiếp của Lead D tại Vòng 17 và kết quả tham vấn kiến trúc chuyên sâu cùng DeepSeek Reason Mode (Phiên Duo R17), Thành viên C phát hành văn bản **Errata V4.2** độc lập này nhằm:
1. Đính chính chính thức sai lệch số liệu bảng kê tài liệu đặc tả QA `docs/SELECTION_GATE_QA_SPEC_PACK_B.md` tại thông báo trước, giữ nguyên nội dung tệp vật lý trên Git blob để bảo toàn giá trị thẩm định của QA Lead B.
2. Chuẩn hóa cách mô tả trạng thái phê duyệt và văn phong trung thực khoa học, loại bỏ các diễn đạt suy đoán hoặc tối ưu hóa quá sớm.
3. Kính trình Lead D **hai dự thảo quyết định riêng biệt** để xem xét và chỉ đạo bước tiếp theo.

---

## II. ĐÍNH CHÍNH BẢNG KÊ ĐẶC TẢ QA (`docs/SELECTION_GATE_QA_SPEC_PACK_B.md`)

### 1. Bảng đối chiếu số liệu sai lệch:

| Thông số kiểm toán | Số liệu ghi nhầm tại thông báo trước | Số liệu thực tế tại commit `2eddf41` | Tình trạng đối soát với QA của B |
| :--- | :---: | :---: | :---: |
| **Kích thước tệp** | `8.432 bytes` | **`8.496 bytes`** | Khớp 100% bản B đã kiểm và ký `PASS` |
| **Mã băm SHA-256** | `3c59a3fe2fffe86a3449339e088a8d601b0f7e1b5ea176987c2b3e8c953ae298` | **`ca9a5af3d8e0abadf26eb4a19374b0d97820cf2dffb30ca2d80d457be9067d09`** | Khớp 100% bản B đã kiểm và ký `PASS` |
| **Commit gắn liền** | `2eddf41b5fe9148f5b502cb82b101635f804d5b6` | `2eddf41b5fe9148f5b502cb82b101635f804d5b6` | Cùng một commit duy nhất |

### 2. Nguyên nhân sai lệch:
Tại thời điểm soạn thảo tin nhắn thông báo trước, Thành viên C đã đo đạc kích thước và mã băm trên bản nháp cục bộ (8.432 bytes) trước khi commit bổ sung dòng ghi chú kiểm toán cuối tệp. Tệp vật lý thực tế được commit và push lên remote tại `2eddf41` là **8.496 bytes**, SHA-256 **`ca9a5af3d8e0abadf26eb4a19374b0d97820cf2dffb30ca2d80d457be9067d09`**.

### 3. Nguyên tắc bảo toàn Audit Trail & Giảm tải cho QA:
* **Giữ nguyên 100% byte tệp đặc tả:** Tệp `docs/SELECTION_GATE_QA_SPEC_PACK_B.md` tại commit `2eddf41` không bị chỉnh sửa, thay thế hay viết đè.
* **Không yêu cầu B tái thẩm định spec:** Do tệp trên đĩa và git blob đã được QA Lead B trực tiếp kiểm tra và cho kết luận `PASS` tại văn bản `docs/QA_REPORT_SELECTION_GATE_2EDDF41_B.md`, việc phát hành Errata này chỉ nhằm chuẩn hóa số liệu bảng kê của C, không làm phát sinh thêm việc re-QA nội dung đối với B.

---

## III. CHUẨN HÓA MÔ TẢ TRẠNG THÁI PHÊ DUYỆT & TÍNH TRUNG THỰC KHOA HỌC

1. **Chuẩn hóa trạng thái Shard nguồn Đợt 1:**
   * Thay thế toàn bộ cụm từ *"phê duyệt shard sạch"* bằng **"đề nghị cho phép tải và kiểm nguồn `train-001.parquet`"**.
   * Minh định rõ ràng: Shard `train-001.parquet` hiện chỉ có metadata và mã băm Git-LFS dự kiến (`260cb9c9...`). Byte Parquet trên đĩa (`locally_verified_sha256: null`) và kết quả rà soát loại trừ Gate 0–4 vẫn đang chờ kiểm sau khi Lead D phê duyệt lệnh kiểm nguồn.
2. **Chuẩn hóa trạng thái mã nguồn và kiểm định:**
   * Thay thế diễn đạt *"đã được Lead D xác nhận"* bằng: **"các thay đổi đã được đối chiếu trong mã, B đã QA phần công khai tại commit `2eddf41`, đang chờ quyết định của Lead D về nguồn"**.
3. **Báo cáo kết quả cụ thể các ca hồi quy (thay thế khẳng định tuyệt đối "nhất quán 100%"):**
   * *Tuyến `is_excluded()`:* 5/5 ca hồi quy chuyên biệt (`test_gate2_regression_*`) xử lý fail-closed. URL bất thường/HTML chứa script được nhận diện qua hàm chuẩn hóa; URL chứa ký tự null/lỗi tiền xử lý (`ValueError`) trả về `True` (loại trừ an toàn); ngoại lệ hệ thống (`RuntimeError`) không bị nuốt bởi `except Exception: pass` mà ném thẳng dừng pipeline.
   * *Tuyến `filter_split()`:* Đưa toàn bộ các bản ghi khớp mã băm cam kết hoặc gặp lỗi định dạng vào phân vùng `excluded`; phân vùng `kept` rỗng (không giữ lại bất kỳ bản ghi lỗi nào).
   * *Tuyến `gate_2_anti_leakage()`:* Từ chối rõ ràng với lý do minh bạch `reject_gate2_preprocessing_error` hoặc `reject_exclusion_registry_match`; tuyệt đối không trả về `(True, "passed")` cho bất kỳ mẫu nào gặp lỗi hoặc khớp cam kết loại trừ.
4. **Duy trì trạng thái Pilot Lô 1:**
   * Duy trì nguyên vẹn trạng thái `"content_identity_verified": false`, `"mapping_status": "unresolved_source_mapping"` và `"rows_api_revision_pinned": false` trong `data/exclusion_registry.json`.
   * Hồ sơ hạn chế V2 (`pilot_batch1_recovery_dossier_restricted_v2.json` - `adc0b90d...`) khớp đúng mã băm bàn giao, nhưng danh tính byte của phản hồi Rows API lịch sử vẫn chưa được xác minh do thiếu raw HTTP body dump.

---

## IV. HAI DỰ THẢO QUYẾT ĐỊNH TRÌNH LEAD D XEM XÉT VÀ BAN HÀNH

Thành viên C kính trình Lead D hai quyết định riêng biệt:

```
========================================================================================
DỰ THẢO QUYẾT ĐỊNH 1 (BAN HÀNH LỆNH KIỂM NGUỒN SHARD TRAIN-001)
========================================================================================

Căn cứ Source Manifest (configs/source_manifest.json) và Báo cáo Kiểm toán V4.2:

Điều 1. Cho phép Thành viên C thực hiện bước kỹ thuật: Tải về và kiểm tra nguồn đối với shard `train-001.parquet`.
   - Nguồn: phreshphish
   - Git Revision khóa: eabec4b7a66324b79cc8a0ad856d1731dc26fe1a
   - Tên tệp: train-001.parquet
   - Dung lượng dự kiến: 322,018,201 bytes
   - Mã băm Git-LFS dự kiến: 260cb9c93299f6b244d48321fe115523159770f4e73446b382473628c6e81d74
   - Cửa sổ ngày được phép lấy mẫu (Temporal Split): 2024-10-01 đến 2025-09-08

Điều 2. Quy trình kiểm tra kỹ thuật bắt buộc:
   1. Đo trực tiếp mã băm SHA-256 trên byte thật của tệp Parquet sau khi tải về đĩa cục bộ, đối chiếu với mã băm Git-LFS pointer dự kiến.
   2. Chạy toàn bộ bản ghi qua Selection Gate (Gates 0–4) để kiểm tra: cách ly shard (Gate 0), regex 14 tổ chức (Gate 1), 6 lớp mã băm ExclusionRegistry chống rò rỉ 52 mẫu đã biết (Gate 2), lọc tương đồng SimHash/DOM Tag và đa dạng tên miền tối đa 1 mẫu/eTLD+1 (Gate 3), cân bằng phân loại (Gate 4).

Điều 3. Tiêu chí dừng an toàn Fail-Closed (Halt Criteria):
   - DỪNG NGAY LẬP TỨC nếu SHA-256 byte thực tế trên đĩa sai lệch so với Git-LFS pointer.
   - DỪNG NGAY LẬP TỨC nếu xuất hiện bất kỳ ngoại lệ dữ liệu định dạng hoặc ngoại lệ hệ thống nào trong quá trình chạy qua Gate 0–4.
   - DỪNG NGAY LẬP TỨC nếu số lượng ứng viên hợp lệ sau Gate 0–4 không đạt chỉ tiêu tối thiểu 100 mẫu.
   - Khi dừng, lập tức niêm phong log, báo cáo Lead D, không xuất danh sách rút mẫu.

Điều 4. Sản phẩm báo cáo:
   - Báo cáo số đếm tổng hợp (tổng số hàng, số mẫu qua từng cổng, số mẫu bị loại theo từng lý do, các sai lệch phát hiện và phần còn chưa xác minh).
   - Quyết định này CHỈ cho phép kiểm nguồn kỹ thuật, CHƯA cho phép rút 100 mẫu Main, CHƯA mở Main Annotation và CHƯA đưa dữ liệu vào đào tạo mô hình.
========================================================================================
```

```
========================================================================================
DỰ THẢO QUYẾT ĐỊNH 2 (XỬ LÝ SỰ CỐ GIT CỦA PILOT TẠI COMMIT AD445A7)
========================================================================================

Căn cứ Biên bản Sự cố docs/INCIDENT_REPORT_GIT_EXPOSURE_AD445A7.md và Hồ sơ hạn chế V2:

Điều 1. Phê duyệt áp dụng Phương án A (Forward-Fix & Administrative Retirement):
   - Giữ nguyên lịch sử commit trên Git nhằm bảo toàn audit trail minh bạch, phục vụ đánh giá khoa học và kiểm toán độc lập.
   - Không thực hiện force-push hoặc viết lại lịch sử Git (git-filter-repo) trên nhánh cộng tác.

Điều 2. Thực thi loại trừ các mẫu đã biết:
   - Đánh dấu vĩnh viễn 20 mẫu Pilot Lô 1 trong data/exclusion_registry.json với mã cam kết EXCL-PILOT-01 và mã băm hồ sơ hạn chế commitment_sha256 = "adc0b90dddc0aea4c3347cc709fabe6dbc3ea391335965c0ba949503bfcdf1fa".
   - Toàn bộ 20 mẫu này bị loại trừ vĩnh viễn (retired) khỏi mọi tập dữ liệu huấn luyện, thẩm định và đánh giá (M0–M3).

Điều 3. Phạm vi Shard cách ly:
   - Cách ly vĩnh viễn shard `train-000.parquet` (QUARANTINED), cấm mọi hành vi trích xuất từ shard này cho Main Annotation.

Điều 4. Thừa nhận giới hạn khoa học & Rủi ro tồn dư:
   - Thừa nhận trung thực trong các báo cáo khoa học: Do thiếu bản lưu byte gốc từ Rows API lịch sử, mối quan hệ giữa Pilot lịch sử và shard hiện tại duy trì trạng thái unresolved_source_mapping. 6 lớp mã băm và cơ chế lọc tương đồng template giúp giảm thiểu tối đa rủi ro đối với các dấu vết đã biết, nhưng không tuyên bố loại bỏ 100% rủi ro lý thuyết.
   - Toàn bộ bảng chi tiết cấp mẫu (ID, locator, nhãn nguồn, tên miền) tiếp tục được niêm phong an toàn tại khu vực hạn chế ngoài Git (data/restricted/).
========================================================================================
```

---

## V. BẢNG MÃ BĂM KIỂM TOÁN ĐỐI CHIẾU V4.2 (AUDITED HASHES V4.2)

Toàn bộ kích thước và mã băm SHA-256 đo đạc trực tiếp trên byte vật lý thực tế:

| Tệp tin / Cấu phần | Vị trí / Tình trạng | Kích thước (bytes) | Mã băm SHA-256 |
| :--- | :--- | :---: | :--- |
| **Bản đính chính Errata V4.2 (Tệp này)** | `docs/SELECTION_GATE_ERRATA_V4_2_LEAD_D.md` | Bản phát hành chính thức | Tham chiếu commit V4.2 |
| **Báo cáo kiểm toán tổng hợp V4.2** | `docs/PILOT_BATCH1_AUDIT_AND_SELECTION_GATE_REPORT_LEAD_D.md` | 32,568 | `ebc4549a6514cb6ee162d622115086f44154bbaa247162ccca4a0ff1dc239631` |
| **Tài liệu đặc tả QA công khai (Giữ nguyên byte đã QA)** | `docs/SELECTION_GATE_QA_SPEC_PACK_B.md` | 8,496 | `ca9a5af3d8e0abadf26eb4a19374b0d97820cf2dffb30ca2d80d457be9067d09` |
| **Biên bản QA độc lập của B (Commit `2eddf41`)** | `docs/QA_REPORT_SELECTION_GATE_2EDDF41_B.md` | 26,507 | `45dacb831c5f6ceb40570f3870bbe3245a3b2ef9d16c1e2b6c1af3a76f6fda4b` |
| **Gói nén kiểm toán V4.1 gửi D (Audit trail)** | `data/restricted/pilot_batch1_remediation_pack_lead_d_v4_1.zip` | 30,280 | `f06fb890be501eb71e51c21b52d017dbce7bff66beb91fc884546c0817980b21` |
| **Hồ sơ hạn chế V2 (Lineage V1)** | `data/restricted/pilot_batch1_recovery_dossier_restricted_v2.json` | 23,169 | `adc0b90dddc0aea4c3347cc709fabe6dbc3ea391335965c0ba949503bfcdf1fa` |
| **Bảng chi tiết cấp mẫu (ngoài Git)** | `data/restricted/pilot_batch1_sample_level_audit_table.json` | 20,574 | `6395781aeada3b73c72ee7215bd29a167ea5ab639ce48fe3507bde515bbf128f` |
| **Biên bản sự cố Git Exposure** | `docs/INCIDENT_REPORT_GIT_EXPOSURE_AD445A7.md` | 6,204 | `79505d4a503c87a762d0476d71e0360c940af86c654b37e41558991756d18f51` |
| **Exclusion Registry V1.1.0** | `data/exclusion_registry.json` | 107,424 | `f00df7a63fb6659d78fe065ca4c87445ebe071fb448e1d1f337d740317dd57ea` |
| **Module loại trừ (Đã sửa import & fail-closed)** | `src/phishing/data/exclusion.py` | 19,448 | `5cc8a445b20bb251df523e258f957215134cb804859de3855dff49db856aa041` |
| **Cổng chọn mẫu Selection Gate (Đã sửa)** | `src/phishing/data/selection_gate.py` | 20,308 | `eb3f36a9db9a5dbba62bd1643b68cf4c678d99e9a553132354e792de8753a6a1` |
| **Runner chọn mẫu thực tế** | `scripts/data/run_main_selection.py` | 4,381 | `cc1d45d0801d846454347b877ba95907a1bb1537ba33954876b53ddd87c44fb2` |
| **Bộ kiểm thử 40 ca** | `tests/test_pilot_batch1_exclusion.py` | 43,114 | `a0dab832654bf6ab76614f0098b3b0e7affc710d8e69695d167dfffcff9e75f5` |
| **Log 40 tests (Môi trường Cục bộ C)** | `test_report_pilot_batch1_exclusion_v4_1.log` | 5,917 | `2db9f8eab72940d66c197a155595d71de9540d3ada3e297c1f546ade6cf54ed4` |
| **Log 38 passed / 2 skipped (Tự kiểm mô phỏng)** | `test_report_clean_checkout_simulation_v4_1.log` | 5,919 | `ded94b99f1b1718eac6d9eaf01065db16b31ddbd3db87fd00185fa687622b022` |
| **Log 147 tests (7 test suites)** | `test_report_7_suites_v4_1.log` | 21,476 | `81b62c32da70745b983e5bffad5fc36d8a5557f1c7939a06dbd49b13132c3382` |

---

## VI. TRẠNG THÁI QUẢN TRỊ & RANH GIỚI TRÁCH NHIỆM

* **Trạng thái hệ thống tiếp tục khóa chặt:**
  * `main_annotation_status = "LOCKED"`
  * `training_blocked = true`
  * `official_test_used = false`
* **Ranh giới trách nhiệm:**
  * Thành viên C tuyệt đối chưa tải shard `train-001.parquet`, chưa chạy lệnh rút 100 mẫu Main, chưa tạo và chưa phát Blind View cho A/B khi Lead D chưa ký lệnh phê duyệt nguồn.
  * Mọi bước kỹ thuật tiếp theo chỉ được kích hoạt sau khi Lead D phê duyệt Quyết định 1 và Quyết định 2 nêu trên.
