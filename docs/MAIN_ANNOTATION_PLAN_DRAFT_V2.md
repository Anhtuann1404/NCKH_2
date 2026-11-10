# DỰ THẢO KẾ HOẠCH CHIẾN DỊCH GÁN NHÃN CHÍNH (MAIN ANNOTATION PLAN - PROPOSAL V2.2)

**Dự án:** Nghiên cứu phát hiện website phishing mạo danh tổ chức bằng học máy kết hợp URL và nội dung trang (NCKH_2)  
**Mã văn bản:** `PLAN-MAIN-ANNOTATION-PROPOSAL-V2.2`  
**Phiên bản:** `2.2.0-REVISED-DRAFT`  
**Ngày lập:** 10/11/2026  
**Đơn vị lập:** Thành viên C (Nguyễn Thắng — Data Pipeline & Thư ký Kiểm toán)  
**Trạng thái quản trị:** `DRAFT_V2.2_PENDING_LEAD_D_REVIEW_AND_QA_APPRAISAL` (Dự thảo V2.2 — Tiếp thu toàn diện 4 yêu cầu kiểm toán ngày 10/11/2026 của Lead D; chờ Lead D xem xét và chuyển QA Lead B thẩm định độc lập; tuyệt đối duy trì training_blocked=true, official_test_used=false, chưa trích xuất mẫu hay mở Pass 1)  
**Căn cứ pháp lý & kỹ thuật:**  
- Ý kiến chỉ đạo kiểm toán của Lead D (Nguyễn Anh Tuấn) đối với bản dự thảo V2.1 ngày 10/11/2026 (4 yêu cầu hoàn thiện).  
- Giao thức dữ liệu (`docs/DATA_PROTOCOL.md`), Giao thức thực nghiệm (`docs/EXPERIMENT_PROTOCOL.md`) và Codebook v1.1 (`docs/CODEBOOK_V1_1.md`).  
- Báo cáo khung ngân sách dự phóng công sức PLAN-01 (`plan_01_calibration_effort_report.json`).  
- Sổ bộ loại trừ `data/exclusion_registry.json` và hồ sơ hạn chế niêm phong `data/restricted/clean_calibration_exclusion_mapping_c_32.json`.  
- Kỷ luật Ponytail Engineering và Academic Research Skills (ARS).

---

## BẢNG ĐỐI CHIẾU TIẾP THU VÀ HIỆU CHỈNH 4 YÊU CẦU KIỂM TOÁN CỦA LEAD D (ĐỢT 3)

| # | Yêu cầu kiểm toán của Lead D | Căn cứ mã nguồn / Tài liệu hiện hành | Phương án hiệu chỉnh trong Bản V2.2 | Phép kiểm & Bằng chứng thực tế |
|:---:|:---|:---|:---|:---|
| **1** | Chọn một phương án cụ thể để giấu `random_subset` khỏi B. Không để lựa chọn "null hoặc omitted" vì schema/CLI hiện dùng boolean. Mô tả chính xác trường bị bỏ/thay thế, cách tạo bản ghi, khóa bảng phân tầng và test chứng minh tính mù trong khi Kappa vẫn đúng tập ngẫu nhiên. | `src/phishing/annotation/blind_view.py`, `scripts/annotate_cli.py` (dòng 823–830 đọc `random_subset` hoặc `random_subset_default`), `src/phishing/annotation/__init__.py`. | **Chọn duy nhất Phương án Boolean Đồng nhất (Uniform Boolean Dummy):** 100% mẫu trong Blind View của B mang giá trị boolean `random_subset: true` (hoặc đặt `"random_subset_default": true` ở cấp gói). Trường này được bảo toàn chuẩn boolean cho CLI ghi vào `AnnotationRecord`. Member C khóa trước bảng phân tầng thực tế tại `data/restricted/main_annotation_strata_commitment.json` (map `sample_id` $\rightarrow$ `is_true_random`). Module `evaluate_kappa` kết hợp (join) bảng cam kết để bóc tách đúng $N_{\text{random}}$ mẫu. | Test tính mù: Chứng minh $\text{Unique}(\text{view\_b}[\text{"random\_subset"}]) == \{\text{True}\}$, B không có cơ sở phân biệt ca khó. Test Kappa: Mẫu số tính $\kappa_{\text{primary}}$ chỉ lấy $N_{\text{random}}$ mẫu có `is_true_random == True`. |
| **2** | Sửa đặc tả cổng registry để không dựa vào số 246/10 viết cứng. Kiểm tổng đếm và cam kết từ registry hiện hành, kiểm đủ hồ sơ hạn chế, nêu rõ cách xử lý các lô pilot chưa ánh xạ nguồn; thiếu căn cứ thì dừng an toàn trước khi chọn mẫu. Ghi rõ là yêu cầu cần triển khai. | `data/exclusion_registry.json`, `src/phishing/data/exclusion.py`. | **Bỏ hoàn toàn số cứng 246/10:** Đổi thành kiểm tra động: $\sum b[\text{"n\_samples"}] == \text{reg}[\text{"total\_excluded\_samples"}]$ và $\text{len}(b) == \text{reg}[\text{"total\_excluded\_entries"}]$. Kiểm tra tự động các lô có cam kết hạn chế phải khớp `commitment_sha256`. Với các lô pilot `unresolved_source_mapping` (Lô 1–3), nếu phát hiện ứng viên nghi vấn trùng lặp mà không có giải trình/quyết định bypass của D thì lập tức **Dừng an toàn (Fail-Closed Stop)**. Ghi rõ đây là **Yêu cầu kỹ thuật đề xuất cần triển khai**. | Phân tích logic: Cơ chế động thích ứng tự nhiên khi registry mở rộng lô mới mà không làm vỡ mã kiểm tra. |
| **3** | Đổi câu "190,07h khớp chuẩn xác 190,79h" thành bảng đối chiếu: lệch 0,72h và cơ cấu A/B/C/D đã thay đổi so với PLAN-01; ghi là kịch bản dự phóng mới chờ D duyệt. Đổi kết luận "tuyệt đối không thể trong một tuần" thành đánh giá có điều kiện: A cần ~105,7h; tiến độ một tuần chỉ được cân nhắc lại nếu Đợt 1 chứng minh tốc độ nhanh hơn, chất lượng ổn định và nhân sự cam kết đủ giờ. | `plan_01_calibration_effort_report.json` (Bảng 1 & Bảng 4: 190,79h, A: 114,08h, B: 36,21h, C: 25,00h, D: 15,50h). | **Lập bảng đối chiếu chi tiết độ lệch 0,72h:** Trình bày rõ nguyên nhân dịch chuyển công số (A giảm 8,41h do mean 380s; B tăng 3,12h; C tăng 5,00h do quản trị 3 tầng tính mù; D giảm 0,43h). Ghi rõ: **Kịch bản dự phóng công số hiệu chỉnh V2.2 chờ D phê duyệt**. Đổi kết luận tiến độ sang **Đánh giá có điều kiện**: A cần ~105,7h gán nhãn; chỉ xem xét lại mục tiêu 1 tuần nếu Đợt 1 thực tế chứng minh tốc độ tăng, chất lượng $\kappa$ giữ vững và A/B cam kết đủ giờ. | Bảng đối chiếu chênh lệch công số tại Mục 7. |
| **4** | Cung cấp bằng chứng truy xuất được của commit `13e24a0...` trên đúng nhánh, kèm log lệnh test, số pass/skip và phạm vi test. Phân biệt test hồi quy mã hiện có với test cho cơ chế mới chưa triển khai. | Lịch sử Git remote `origin/feat/c-calibration-v1-1-4-adjudication`, bộ test suite `tests/`. | **Cung cấp bằng chứng Git & Log Test đầy đủ:** Cập nhật link commit đã push trên GitHub: `https://github.com/Anhtuann1404/NCKH_2/commit/13e24a0cbf042c486825a67c74ef9332e1935d05`. Ghi rõ log lệnh test và kết quả 150/150 PASSED (0 failed, 0 skipped). Phân định rạch ròi: 150 bài test là **Test hồi quy mã nguồn hiện có**; các bài test cho cổng động và tính mù là **Test đề xuất triển khai mới**. | Lệnh truy xuất: `git ls-remote origin feat/c-calibration-v1-1-4-adjudication` xác nhận commit tồn tại trên máy chủ GitHub. |

---

## 1. NGUYÊN TẮC CỐT LÕI & RANH GIỚI QUẢN TRỊ

1. **Bản chất văn bản:** Đây là văn bản **DỰ THẢO ĐỀ XUẤT PHIÊN BẢN 2.2 (PROPOSAL V2.2)** do Thành viên C lập để tiếp thu toàn diện 4 yêu cầu hoàn thiện của Lead D ngày 10/11/2026. Mọi nội dung, phương án và bảng tính trong tài liệu này đều ở trạng thái chờ Lead D phê duyệt, tuyệt đối không tự động phát sinh hiệu lực thi hành và chưa trích xuất bất kỳ mẫu dữ liệu nào.
2. **Khẳng định tính chất con số 1.000 trong PLAN-01:**
   - Con số 1.000 mẫu trong Báo cáo PLAN-01 là **Khung ngân sách công sức dự phóng có điều kiện** (Conditional Projected Effort Budget — 190,79 giờ người) được Lead D phê duyệt về mặt kế toán tài nguyên dự án.
   - Con số 1.000 mẫu **KHÔNG PHẢI LÀ LỆNH TRÍCH XUẤT THỰC TẾ**. Quy mô trích xuất thực tế sẽ do Lead D quyết định theo từng giai đoạn căn cứ vào kết quả thực nghiệm Đợt 1 và cam kết thời gian khả dụng của nhân sự.
3. **Kỷ luật hệ thống bất biến:**
   - `training_blocked = true` (Chặn 100% nạp dữ liệu vào pipeline huấn luyện).
   - `official_test_used = false` (Cô lập tuyệt đối 100% tập kiểm thử chính thức).
   - `main_annotation_status = "LOCKED"` (Chiến dịch gán nhãn chính tiếp tục khóa hoàn toàn).

---

## 2. ĐẶC TẢ CỔNG KIỂM TRA ĐỘNG SỔ BỘ LOẠI TRỪ (YÊU CẦU ĐỀ XUẤT CẦN TRIỂN KHAI)

Tiếp thu chỉ đạo của Lead D về việc loại bỏ các hằng số viết cứng (hardcoded constants 246/10) và xây dựng cơ chế kiểm soát động thích ứng:
- **Trạng thái thực tế:** Cơ chế này là **YÊU CẦU KỸ THUẬT ĐỀ XUẤT CẦN TRIỂN KHAI (PROPOSED SPECIFICATION TO BE IMPLEMENTED)**, hiện chưa có trong mã nguồn chạy.

### 2.1 Đặc tả 4 bước kiểm tra động của cổng `verify_exclusion_registry_integrity()`
Hàm dự kiến được cài đặt tại `src/phishing/data/exclusion.py` và đóng vai trò cổng kiểm soát tiền khả thi (Preflight Gate) kích hoạt trước mọi tác vụ tuyển chọn mẫu:

1. **Kiểm tra tính nhất quán động nội tại (Dynamic Internal Consistency):**
   - Đọc trực tiếp `data/exclusion_registry.json`.
   - Trích xuất hai chỉ số khai báo từ phần đầu tệp: $E_{\text{declared}} = \text{registry}[\text{"total\_excluded\_entries"}]$ và $S_{\text{declared}} = \text{registry}[\text{"total\_excluded\_samples"}]$.
   - Tính toán động trên danh sách các lô:
     $$E_{\text{actual}} = \text{len}(\text{registry}[\text{"exclusions"}]) \quad \text{và} \quad S_{\text{actual}} = \sum_{b \in \text{registry}[\text{"exclusions"}]} b[\text{"n\_samples"}]$$
   - Cổng kiểm tra bắt buộc: $E_{\text{actual}} == E_{\text{declared}}$ và $S_{\text{actual}} == S_{\text{declared}}$. Nếu phát hiện bất kỳ sự không nhất quán nào, lập tức ném lỗi `ValueError: Registry internal counts inconsistent`.

2. **Kiểm tra tính toàn vẹn của hồ sơ hạn chế niêm phong (Restricted Dossier Integrity):**
   - Quét qua toàn bộ các lô có `mapping_status == "resolved_in_restricted_dossier"`.
   - Kiểm tra sự tồn tại vật lý của tệp hồ sơ hạn chế tương ứng trong thư mục `data/restricted/`.
   - Tính toán mã băm SHA-256 thực tế của tệp trên đĩa và đối chiếu với trường `commitment_sha256` của lô đó trong registry.
   - Quy tắc dừng an toàn: Thiếu tệp ném lỗi `FileNotFoundError`; sai lệch dù chỉ 1 ký tự hex ném lỗi `RuntimeError: Commitment hash mismatch`.

3. **Xử lý các lô pilot chưa ánh xạ nguồn (`unresolved_source_mapping`):**
   - Đối với các lô pilot sơ bộ lịch sử (Lô 1: `EXCL-PILOT-01`, Lô 2: `EXCL-REAL-PILOT-32`, Lô 3: `EXCL-PILOT-02`) chưa có ánh xạ chi tiết từng dòng về shard:
   - Cổng kiểm soát bắt buộc phải nạp toàn bộ các dấu vân tay tóm tắt cấu trúc (`summary_fingerprint_hashes`) và mã băm cấu trúc lô (`batch_sha256`) đã đăng ký.
   - **Quy tắc dừng an toàn (Fail-Closed Stop):** Nếu một ứng viên mới trích xuất có dấu vân tay cấu trúc trùng khớp với bất kỳ mẫu nào thuộc các lô unresolved, mà chưa có văn bản giải trình đối soát và phê duyệt miễn trừ (bypass approval) của Lead D, hệ thống phải **DỪNG NGAY LẬP TỨC toàn bộ quy trình tuyển chọn mẫu**.

4. **Kế hoạch kiểm thử cần bổ sung (`tests/test_exclusion_registry.py`):**
   - Cần viết mới bộ kiểm thử chuyên biệt để kiểm chứng cơ chế động trên (kiểm thử thành công, kiểm thử ném lỗi khi tổng mẫu sai lệch, kiểm thử ném lỗi khi hash cam kết bị chỉnh sửa, và kiểm thử fail-closed khi gặp mẫu unresolved).

---

## 3. ĐỐI CHIẾU DANH MỤC 10 LÔ LOẠI TRỪ HIỆN HÀNH & QUAN HỆ ÁNH XẠ CỦA RUNWAY A

### 3.1 Bảng kê chính xác 10 lô trong `data/exclusion_registry.json`
Đọc trực tiếp từ tệp `data/exclusion_registry.json` (phiên bản `1.1.0`), danh mục loại trừ gồm đúng **10 lô** với tổng cộng **246 mục ghi nhận theo lô** ($\sum n_i = 246$):

| STT | Mã định danh Lô chính xác (Exclusion ID) | Mã tập dữ liệu (Dataset ID) | Số lượng mục ghi ($n_i$) | Trạng thái ánh xạ (Mapping Status) | Lý do loại trừ vĩnh viễn khỏi Train / Validation / Test |
|:---:|:---|:---|:---:|:---|:---|
| 1 | `EXCL-PILOT-01` | *(unspecified)* | 20 | `unresolved_source_mapping` | 20 mẫu kỹ thuật pilot ban đầu (8 phish, 12 benign) đã được mở kiểm tra cấu trúc/văn bản. |
| 2 | `EXCL-REAL-PILOT-32` | *(unspecified)* | 32 | `unresolved_source_mapping` | Hợp của 32 mẫu pilot thật Đợt 1, không có per-ID/class/source mapping công bố. |
| 3 | `EXCL-PILOT-02` | `REAL-PILOT-32-V2` | 32 | `unresolved_source_mapping` | 32 mẫu pilot thật Đợt 2 (20 phish, 12 benign), cô lập vĩnh viễn khỏi tập thực nghiệm. |
| 4 | `EXCL-PILOT-02-REBUILD-e039c774ef5f` | `REAL-PILOT-32-V2` | 32 | `resolved` | Lô tái lập Pilot V2 có đầy đủ mã băm URL, HTML và Group. |
| 5 | `EXCL-CALIBRATION-PROPOSAL-V1.1-MAIN-24` | `CALIBRATION-PROPOSAL-V1.1-MAIN` | 24 | `resolved` | 24 mẫu đề xuất hiệu chuẩn cũ v1.1 đã tạo Blind View và gắn dịch ngoại tuyến. |
| 6 | `EXCL-CALIBRATION-PROPOSAL-V1.1-RESERVE-08` | `CALIBRATION-PROPOSAL-V1.1-RESERVE` | 8 | `resolved` | 8 mẫu dự phòng hiệu chuẩn cũ đã đọc từ shard để tính toán cờ mô tả bề mặt. |
| 7 | `EXCL-CALIB-CLEAN-32-EXPOSED-ON-GIT` | `CALIBRATION-CLEAN-32-EXPOSED` | 32 | `mapped_to_shards` | 32 ứng viên hiệu chuẩn sạch vô tình xuất hiện locator trên Git tại commit `226d422`. |
| 8 | `EXCL-CALIB-CLEAN-02-PAIRWISE-RESOLUTION-LOCATOR-EXPOSED` | `CALIBRATION-CLEAN-02-PAIRWISE-EXPOSED` | 2 | `mapped_to_shards` | 02 mẫu (RSV-002 và mẫu dự phòng train-055) vô tình lộ locator tại commit `9e457f5`. |
| 9 | `EXCL-CALIBRATION-CLEAN-RUNWAY-32` | `CALIBRATION-CLEAN-RUNWAY-32` | 32 | `verified_cryptographic_hashes_locators_restricted_offline` | 32 mẫu tuyển chọn cho Runway A Đợt B (24 chính + 8 dự phòng) cô lập locators ngoài Git. |
| **10** | **`EXCL-CALIBRATION-CLEAN-BATCH-C-RESTRICTED`** | **`CALIBRATION-CLEAN-C-32`** | **32** | **`resolved_in_restricted_dossier`** | **32 mẫu Đợt C niêm phong cam kết hạn chế ngoài Git (`clean_calibration_exclusion_mapping_c_32.json`) với commitment hash `67326e80b2a6f9cb7356450a31fe15054a1193412a8ed0576ea2972f1801a805`.** |
| — | **TỔNG CỘNG THEO CÁC LÔ** | **10 LÔ** | **246** | — | **Tổng số mục ghi nhận loại trừ qua các lô quản trị.** |

### 3.2 Chứng minh quan hệ của 24 mẫu Runway A bằng Hồ sơ Ánh xạ Hạn chế
- 24 mẫu Runway A đã nghiệm thu (`clean_calibration_runway_a_labels_final.json`) chính là 24 mẫu chính (`role: "main_24"`, SMP-001..SMP-024) thuộc **Lô 10 (Đợt C)** niêm phong tại `data/restricted/clean_calibration_exclusion_mapping_c_32.json`.
- Lô 9 (`EXCL-CALIBRATION-CLEAN-RUNWAY-32`) là 32 mẫu của **Đợt B** độc lập trong `clean_calibration_exclusion_mapping_32.json`.
- Tập giao URL giữa Lô 9 và Lô 10 là **rỗng tuyệt đối** ($S_{\text{Batch 9}} \cap S_{\text{Batch 10}} = \emptyset$). Do đó, 24 mẫu Runway A thuộc trọn vẹn Lô 10, không thuộc Lô 9, và việc Lô 10 đã được khóa trong registry bảo đảm không bao giờ cộng trùng thành $246 + 24 = 270$ mẫu.

---

## 4. PHƯƠNG ÁN CỤ THỂ DUY NHẤT: GIẤU `random_subset` KHỎI B BẰNG CƠ CHẾ DUMMY BOOLEAN ĐỒNG NHẤT

Tiếp thu chỉ đạo của Lead D ("chọn một phương án cụ thể, không để lựa chọn null hoặc omitted vì schema/CLI hiện dùng boolean và có giá trị mặc định"):

Thành viên C xin lựa chọn và đặc tả duy nhất **Phương án Boolean Đồng nhất (Uniform Boolean Dummy Strategy)**:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 1. TỆP BLIND VIEW PHÁT HÀNH CHO ANNOTATOR B (GÁN BOOLEAN ĐỒNG NHẤT)         │
│ • Tệp: main_annotation_blind_view_b.json                                    │
│ • Khai báo ở cấp gói: "random_subset_default": true                         │
│ • Hoặc trong từng mẫu: "random_subset": true (100% mẫu đều mang giá trị True)│
│ • Kết quả: Entropy thông tin phân tầng đối với B = 0 bit.                   │
│   B hoàn toàn không thể phân biệt mẫu ngẫu nhiên hay ca khó bổ sung.        │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼ (B chạy CLI gán nhãn bình thường)
┌─────────────────────────────────────────────────────────────────────────────┐
│ 2. BẢN GHI GÁN NHÃN CỦA B (ANNOTATION RECORD)                               │
│ • CLI tự động gán: "random_subset": true cho mọi bản ghi của B.              │
│ • Hoàn toàn hợp lệ theo schema type bool của AnnotationRecord, 0 lỗi cú pháp│
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼ (Bước nghiệm thu & tính Kappa)
┌─────────────────────────────────────────────────────────────────────────────┐
│ 3. BẢNG PHÂN TẦNG HẠN CHẾ CỦA C (RESTRICTED STRATIFICATION MAP)             │
│ • Tệp: data/restricted/main_annotation_strata_commitment.json               │
│ • Nội dung: {"MAIN-0001": {"is_true_random": true}, "MAIN-0002": false, ...}│
│ • Niêm phong mật mã với SHA-256 công bố trong release manifest.             │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼ (Khớp nối độc lập)
┌─────────────────────────────────────────────────────────────────────────────┐
│ 4. TÍNH TOÁN COHEN'S KAPPA CHÍNH THỨC TRƯỚC PHÂN XỬ (EVALUATE_KAPPA)        │
│ • Script thực hiện Inner Join: (Nhãn A) ⨝ (Nhãn B) ⨝ (Strata Commitment)    │
│ • Bóc tách chính xác N_random mẫu có is_true_random == True để tính Kappa.  │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 4.1 Chi tiết kỹ thuật của phương án được chọn
1. **Trường dữ liệu trong Blind View:**
   - Trong tệp `main_annotation_blind_view_b.json`, mọi bản ghi `BlindSample` đều có trường `random_subset: true` (hoặc cấp gói mang `random_subset_default: true`). Không sử dụng `null` hay bỏ sót trường để tránh vi phạm schema boolean nghiêm ngặt của `BlindSample` và `annotate_cli.py` (dòng 829–830).
   - Vì 100% mẫu đều mang giá trị `true`, Annotator B nhìn vào dữ liệu hay giao diện CLI đều thấy tất cả các mẫu đồng nhất như nhau, loại bỏ hoàn toàn khả năng nhận biết ca khó hay ca ngẫu nhiên.
2. **Tạo bản ghi gán nhãn (`AnnotationRecord`):**
   - CLI đọc giá trị `true` đồng nhất và xuất ra bản ghi nhãn của B với `"random_subset": true`. Bản ghi hoàn toàn hợp lệ, không phát sinh lỗi kiểm tra kiểu dữ liệu (type validation).
3. **Khóa bảng phân tầng hạn chế:**
   - Trước khi phát gói cho B, Thành viên C khóa trước tệp `data/restricted/main_annotation_strata_commitment.json` lưu trữ danh sách ánh xạ thực tế: `sample_id` $\rightarrow$ `is_true_random: true / false`. Tệp được niêm phong với mã băm SHA-256 công bố trong manifest của đợt.
4. **Quy trình tính toán Cohen's Kappa chính xác:**
   - Module `evaluate_kappa` nạp tệp nhãn của A, tệp nhãn của B, và tệp phân tầng hạn chế của C.
   - Script thực hiện phép kết hợp (inner join) theo `sample_id`: chỉ lọc những mẫu có `is_true_random == True` để tính toán chỉ số $\kappa_{\text{primary}}$ trước phân xử, loại bỏ các ca khó bổ sung khỏi mẫu số Kappa đại diện toàn corpus.
5. **Đặc tả kiểm thử chứng minh ranh giới mù:**
   - Cần bổ sung bài test chứng minh:
     * *Test 1 (Tính mù tuyệt đối của B):* Kiểm tra $\text{UniqueValues}(\text{view\_b}[\text{"random\_subset"}]) == \{\text{True}\}$ (phân phối đơn trị, không có biến thiên).
     * *Test 2 (Chuẩn xác toán học của Kappa):* Chạy `evaluate_kappa` giả lập với tệp phân tầng hạn chế, chứng minh cỡ mẫu $N$ đưa vào ma trận tính $\kappa_{\text{primary}}$ khớp đúng $N_{\text{random}}$, không bị lẫn bất kỳ ca khó bổ sung nào.

---

## 5. NGUỒN DỮ LIỆU ĐÃ KHÓA & QUY TRÌNH PHÊ DUYỆT PHISHVN

1. **Nguồn dữ liệu hợp lệ duy nhất:** `phreshphish` tại revision `eabec4b7a66324b79cc8a0ad856d1731dc26fe1a` (56 shards, 498.255 bản ghi trong `configs/source_manifest.json`).
2. **Quy chế nguồn PhishVN:** PhishVN được xếp vào diện **Nguồn đề xuất thứ cấp — CHƯA ĐƯỢC PHÉP TRÍCH XUẤT**.
3. **Quy trình 4 bước bắt buộc trước khi dùng PhishVN:**
   - Bước 1: Lập `configs/phishvn_manifest.json` độc lập.
   - Bước 2: Kiểm toán bảng mã băm SHA-256 các file thành phần của PhishVN.
   - Bước 3: Xác định phạm vi khai thác và tiêu chí lọc.
   - Bước 4: Trình Lead D ban hành quyết định phê duyệt nguồn bằng văn bản. **Trước khi có quyết định duyệt nguồn của D, cấm tuyệt đối mọi thao tác trích xuất từ PhishVN.**

---

## 6. CHUẨN HÓA DỊCH NGOẠI TUYẾN MARIANMT: NGÔN NGỮ ĐÍCH TIẾNG ANH & REVISION ĐÃ KHÓA

1. **Ngôn ngữ đích:** Đính chính dứt khoát là **TIẾNG ANH (EN)**, không phải tiếng Việt.
2. **Danh mục mô hình và revision khóa cứng (căn cứ `clean_calibration_translations.json`):**
   - Tiếng Nhật (`ja`): `Helsinki-NLP/opus-mt-ja-en@0770961` $\rightarrow$ Đích `en`.
   - Tiếng Nga (`ru`): `Helsinki-NLP/opus-mt-ru-en@fbd6dc7` $\rightarrow$ Đích `en`.
   - Tiếng Trung (`zh`): `Helsinki-NLP/opus-mt-zh-en` (phải khóa revision trước khi dùng) $\rightarrow$ Đích `en`.
   - Tiếng Việt (`vi`), Tiếng Anh (`en`): Giữ nguyên, không dịch (`translation_provided = false`).
3. **Tuân thủ quy tắc R-A09:** Giữ nguyên 100% `page_text` gốc; bản dịch tiếng Anh tĩnh ngoại tuyến đặt trong `translated_text` kèm 5 trường metadata; kiểm tra mã băm `translation_sha256` fail-closed nếu bị chỉnh sửa.

---

## 7. BẢNG ĐỐI CHIẾU CÔNG SỐ SO VỚI PLAN-01 & ĐÁNH GIÁ TIẾN ĐỘ CÓ ĐIỀU KIỆN CHO 1.000 MẪU

### 7.1 Bảng đối chiếu chênh lệch 0,72 giờ và sự dịch chuyển cơ cấu so với PLAN-01
Khung ngân sách PLAN-01 (`plan_01_calibration_effort_report.json`, Bảng 1 & 4) được phê duyệt là **190,79 giờ người**. Dưới đây là bảng đối chiếu chi tiết giữa PLAN-01 và Kịch bản dự phóng hiệu chỉnh V2.2:

| Thành viên / Vai trò | Phân bổ PLAN-01 được duyệt (Giờ) | Tỷ lệ PLAN-01 (%) | Kịch bản Dự phóng V2.2 đề xuất (Giờ) | Tỷ lệ V2.2 (%) | Độ lệch công số (Giờ) | Giải trình nguyên nhân dịch chuyển cơ cấu kỹ thuật |
|:---|:---:|:---:|:---:|:---:|:---:|:---|
| **Annotator A** | 114,08 | 59,80% | **105,67** | 55,59% | **-8,41** | Chuyển từ định mức thận trọng (410,70s/mẫu = 6,85m) sang thời gian trung bình thực đo Pass 1 ($380,16\text{s/mẫu} = 6,34\text{m}$). |
| **QA Lead B** | 36,21 | 18,98% | **39,33** | 20,69% | **+3,12** | Tăng đệm thời gian kiểm định QA tuyển chọn và nghiệm thu độc lập qua 5 đợt phát hành ($15,0\text{h}$) cộng gán đôi 350 mẫu ($24,33\text{h}$). |
| **Thành viên C** | 25,00 | 13,10% | **30,00** | 15,78% | **+5,00** | Bổ sung khối lượng quản trị hạ tầng tính mù 3 tầng, kiểm tra cam kết sổ bộ loại trừ động, quản lý tệp phân tầng hạn chế và đối soát reconciliation. |
| **Lead D** | 15,50 | 8,12% | **15,07** | 7,93% | **-0,43** | Tính toán lại chi tiết thời gian phân xử Pass 2 cho 53 ca bất đồng dự kiến ($7,07\text{h}$) cộng thời gian phê duyệt mốc quản trị ($8,0\text{h}$). |
| **TỔNG CỘNG** | **190,79** | **100,00%** | **190,07** | **100,00%** | **-0,72** | **Kịch bản dự phóng hiệu chỉnh V2.2 giảm 0,72 giờ so với PLAN-01, chờ Lead D xem xét phê duyệt.** |

### 7.2 Đánh giá tiến độ có điều kiện cho Chiến dịch 1.000 mẫu
- **Khối lượng gán nhãn của Annotator A:** Ở tốc độ trung bình thực đo hiện tại ($6,34\text{ phút/mẫu}$), riêng Annotator A đã cần khoảng **105,67 giờ làm việc thuần túy** để hoàn thành 1.000 mẫu.
- **Đánh giá tính khả thi:**
  * Với quỹ thời gian thông thường của một sinh viên/nghiên cứu viên (khoảng 10–15 giờ/tuần), Annotator A cần khoảng **7 đến 10 tuần** chỉ để gán nhãn xong Pass 1.
  * Do đó, **tiến độ hoàn tất cả chiến dịch trong một tuần là phi thực tế ở điều kiện hiện tại**.
  * **Tiến độ một tuần cho toàn chiến dịch chỉ có thể được cân nhắc lại nếu đồng thời thỏa mãn 3 điều kiện ngặt nghèo sau:**
    1. *Điều kiện tốc độ:* Kết quả thực nghiệm Đợt 1 chứng minh tốc độ gán nhãn thực tế tăng lên đáng kể (nhờ annotator thuần thục quy trình và công cụ CLI tối ưu).
    2. *Điều kiện chất lượng:* Chất lượng gán nhãn, độ chi tiết của bằng chứng và chỉ số đồng thuận liên đánh giá viên $\kappa$ vẫn giữ vững ở mức cao ($\kappa \ge 0,75$), không bị suy thoái do làm nhanh.
    3. *Điều kiện nhân lực:* Toàn bộ nhân sự tham gia (đặc biệt là Annotator A và QA Lead B) có văn bản cam kết làm việc tập trung toàn thời gian (full-time sprint với cường độ $> 40\text{ giờ/tuần}$).
- **Kết luận tiến độ:** Khi 3 điều kiện trên chưa được kiểm chứng, tiến độ chính thức của chiến dịch 1.000 mẫu tiếp tục ở trạng thái **CHƯA XÁC ĐỊNH (TBD)** chờ kết quả đo lường Đợt 1 và văn bản cam kết giờ khả dụng của A và B.

---

## 8. BẰNG CHỨNG TRUY XUẤT GIT VÀ KẾT QUẢ KIỂM THỬ HỒI QUY TẠI COMMIT `13e24a0`

### 8.1 Bằng chứng truy xuất Git trên máy chủ GitHub
- **Kho lưu trữ:** `https://github.com/Anhtuann1404/NCKH_2.git`
- **Nhánh phát triển:** `feat/c-calibration-v1-1-4-adjudication`
- **Mã commit đầy đủ:** `13e24a0cbf042c486825a67c74ef9332e1935d05`
- **Đường dẫn truy xuất trực tiếp trên GitHub:**  
  [`https://github.com/Anhtuann1404/NCKH_2/commit/13e24a0cbf042c486825a67c74ef9332e1935d05`](https://github.com/Anhtuann1404/NCKH_2/commit/13e24a0cbf042c486825a67c74ef9332e1935d05)
- **Lệnh kiểm chứng độc lập cho Lead D:**
  ```bash
  git fetch origin feat/c-calibration-v1-1-4-adjudication
  git checkout 13e24a0cbf042c486825a67c74ef9332e1935d05
  # Hoặc kiểm tra qua ls-remote:
  git ls-remote origin feat/c-calibration-v1-1-4-adjudication
  ```

### 8.2 Phân định rạch ròi giữa Test Hồi quy Hiện có và Test Đề xuất Mới
1. **Bộ test hồi quy mã nguồn hiện có (Existing Codebase Regression Tests — 150/150 PASSED):**
   - **Lệnh thực thi:**
     ```bash
     python -m pytest tests/test_blind_view.py tests/test_clean_calibration_blind_view.py tests/test_difficulty_strata.py tests/test_exclusion_registry.py -v
     ```
   - **Kết quả đo lường thực tế:** **150 passed**, 0 failed, 0 skipped, 0 deselected (thời gian thực thi: 3.72s).
   - **Phạm vi kiểm thử của 150 bài test:**
     * `tests/test_blind_view.py` (33 tests): Kiểm chứng an toàn Blind View, allowlist trường, strip thẻ nguy hiểm, loại trừ rò rỉ nhãn và tính toàn vẹn bản dịch.
     * `tests/test_clean_calibration_blind_view.py` (4 tests): Kiểm chứng tính hợp lệ và sạch hoàn toàn của view Đợt C.
     * `tests/test_difficulty_strata.py` (12 tests): Kiểm chứng tính toán độc lập 6 cờ chỉ báo mô tả bề mặt.
     * `tests/test_exclusion_registry.py` (101 tests): Kiểm chứng toàn diện cơ chế loại trừ của 10 lô hiện hành, bao gồm kiểm tra cam kết Lô 10 ngoài Git.
2. **Bộ test đề xuất cho các cơ chế mới (Future Proposed Tests — Chưa triển khai):**
   - *Test cổng registry động:* Kiểm tra việc đối soát động trường `total_excluded_samples` và `total_excluded_entries` thay vì kiểm số cứng; kiểm tra dừng khẩn cấp khi gặp mẫu unresolved chưa bypass.
   - *Test tính mù 3 tầng:* Kiểm tra tính đơn trị `random_subset: true` trên view của B; kiểm tra script `evaluate_kappa` kết hợp tệp phân tầng hạn chế để lọc đúng $N_{\text{random}}$.
   - Các bài test đề xuất này sẽ được viết mới và tích hợp sau khi Lead D chính thức phê duyệt thiết kế kỹ thuật của Bản V2.2.

---

## 9. DANH MỤC NHỮNG ĐIỀU CÒN CHỜ LEAD D QUYẾT ĐỊNH

Thành viên C kính trình Lead D xem xét và ban hành quyết định đối với các nội dung sau:
1. **Phê duyệt Thiết kế Tính mù 3 Tầng & Cơ chế Dummy Boolean:** Thông qua việc dùng `random_subset: true` đồng nhất cho B và quản lý phân tầng qua tệp hạn chế của C.
2. **Phê duyệt Đặc tả Cổng Kiểm tra Động Sổ bộ Loại trừ:** Cho phép triển khai hàm `verify_exclusion_registry_integrity()` theo đặc tả động tại Mục 2.
3. **Phê duyệt Kịch bản Dự phóng Công số Hiệu chỉnh V2.2:** Chấp thuận độ lệch -0,72h và sự dịch chuyển cơ cấu A/B/C/D so với PLAN-01.
4. **Quyết định Quy mô & Bản chất Đợt 1:** Lựa chọn giữa Phương án A (Lô đầu Main) hay Phương án B (Pilot tách riêng); chốt quy mô 60 mẫu hay 100 mẫu.
5. **Thu thập Cam kết Giờ khả dụng:** Yêu cầu Annotator A và QA Lead B nộp văn bản cam kết số giờ khả dụng/tuần để chốt tiến độ chính thức.

---

**XÁC NHẬN CỦA THÀNH VIÊN C (DATA PIPELINE & THƯ KÝ KIỂM TOÁN)**  
*(Văn bản dự thảo kỹ thuật V2.2 — Duy trì nghiêm ngặt: training_blocked=true, official_test_used=false, Main Annotation KHÓA 100%)*  

**Nguyễn Thắng**
