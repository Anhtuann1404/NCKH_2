# DỰ THẢO KẾ HOẠCH CHIẾN DỊCH GÁN NHÃN CHÍNH (MAIN ANNOTATION PLAN - PROPOSAL V2.4)

**Dự án:** Nghiên cứu phát hiện website phishing mạo danh tổ chức bằng học máy kết hợp URL và nội dung trang (NCKH_2)  
**Mã văn bản:** `PLAN-MAIN-ANNOTATION-PROPOSAL-V2.4`  
**Phiên bản:** `2.4.0-REVISED-DRAFT`  
**Ngày lập:** 11/11/2026  
**Đơn vị lập:** Thành viên C (Nguyễn Thắng — Data Pipeline & Thư ký Kiểm toán)  
**Trạng thái quản trị:** `DRAFT_V2.4_PENDING_B_QA_RE_APPRAISAL_AND_LEAD_D_DECISION` (Dự thảo V2.4 — Tiếp thu toàn diện Báo cáo thẩm định phương pháp độc lập ngày 11/11/2026 của QA Lead B; bàn giao commit và hash mới để B tái thẩm định và trình Lead D xem xét; tuyệt đối duy trì training_blocked=true, official_test_used=false, chưa trích xuất mẫu hay mở Pass 1)  
**Căn cứ pháp lý & kỹ thuật:**  
- Báo cáo thẩm định phương pháp độc lập của Thành viên B (Phùng Tấn Minh — QA Lead) ngày 11/11/2026 đối với bản V2.3 tại commit `583c52e`.  
- Ý kiến chỉ đạo kiểm toán của Lead D (Nguyễn Anh Tuấn) ngày 11/11/2026.  
- Giao thức dữ liệu (`docs/DATA_PROTOCOL.md`), Giao thức thực nghiệm (`docs/EXPERIMENT_PROTOCOL.md`) và Codebook v1.1 (`docs/CODEBOOK_V1_1.md`).  
- Sổ bộ loại trừ `data/exclusion_registry.json`, báo cáo kiểm toán phục hồi nguồn `data/source_audit/phreshphish/recovery_status.json`, và hồ sơ hạn chế niêm phong `data/restricted/clean_calibration_exclusion_mapping_c_32.json`.  
- Báo cáo khung ngân sách dự phóng công sức PLAN-01 (`plan_01_calibration_effort_report.json`).  
- Kỷ luật Ponytail Engineering và Academic Research Skills (ARS).

---

## BẢNG ĐỐI CHIẾU TIẾP THU VÀ HIỆU CHỈNH CÁC ĐIỂM THẨM ĐỊNH CỦA QA LEAD B (ĐỢT 5)

| # | Nhận xét & Điểm thẩm định của QA Lead B | Căn cứ mã nguồn / Hồ sơ kiểm toán hiện hành | Phương án hiệu chỉnh trong Bản V2.4 | Trạng thái sau hiệu chỉnh |
|:---:|:---|:---|:---|:---:|
| **1b** | **FAIL**: V2.3 gán `codebook_version="1.2.0"` trong khi Codebook chính thức là 1.1.0. Đề nghị tách phiên bản schema/view khỏi phiên bản quy tắc gán nhãn; giữ nguyên `codebook_version="1.1.0"` và dùng trường định danh hợp đồng riêng (ví dụ `blind_contract_version: "1.2.0"`). | `docs/CODEBOOK_V1_1.md` (`codebook_version = "1.1.0"`), `src/phishing/annotation/blind_view.py`. | **Giữ nguyên 100% `codebook_version = "1.1.0"`** theo đúng bộ quy tắc đã khóa. Bổ sung trường định danh hợp đồng dữ liệu hiển thị mù riêng: `blind_contract_version: "1.2.0"` để CLI và validator phân nhánh kỹ thuật. Khẳng định: C không tự ý nâng cấp Codebook; mọi thay đổi quy tắc gán nhãn phải trình văn bản riêng xin Lead D duyệt. | **ĐÃ XỬ LÝ TRIỆT ĐỂ** |
| **1c** | **PENDING**: Rà soát sự không nhất quán số mẫu của B giữa Mục 4.2 và Mục 7.2 (PLAN-01 ước tính 405 mẫu: 300 random + 105 khó; Mục 7.2 lại ghi 350 mẫu: 300 random + 50 khó). | `plan_01_calibration_effort_report.json` (Bảng 1 & Bảng 4 ghi nhận B kiểm 405 mẫu = 300 random + 105 khó). | **Thống nhất lấy Kịch bản cơ sở PLAN-01 (405 mẫu) làm chuẩn:** Giải trình rõ ràng: 405 mẫu là kịch bản cơ sở của PLAN-01 (với tỷ lệ ca khó phát sinh 15% của 700 mẫu = 105 mẫu); con số 350 mẫu chỉ là kịch bản độ nhạy tối thiểu (khi ca khó phát sinh chỉ 7,14% = 50 mẫu). Bản V2.4 đồng bộ toàn bộ bảng tính và sơ đồ theo chuẩn 405 mẫu của PLAN-01. | **ĐÃ ĐỒNG BỘ 100%** |
| **2** | **FAIL**: Bóc tách chính xác hiện trạng từng lô (Lô 1 thiếu URL/HTML hash trên registry và dùng Rows API chưa khóa revision; Lô 2–3 có đủ 32/32 hash URL/HTML/Group). Chỉ rõ danh sách shard cách ly đã biết (`train-000`, `train-055`). **Không gọi** phần nguồn còn lại là "Shard Nguồn Sạch Đã Được Xác Minh" khi chưa chứng minh được phạm vi của Lô 1; lược bỏ các tuyên bố vượt quá phạm vi chứng minh. | `data/exclusion_registry.json`, `data/source_audit/phreshphish/recovery_status.json`, `src/phishing/data/exclusion.py`. | **Bóc tách chuẩn xác hiện trạng từng lô:** Xác nhận Lô 1 thiếu hash URL/HTML và dùng Rows API chưa khóa revision (hồ sơ `raw20_mapping_check.json` vẫn đang `pending_independent_review`). Xác nhận Lô 2 và Lô 3 có đủ 32/32 bộ mã băm URL/HTML/Group. Liệt kê cụ thể 2 shard cách ly đã biết: `data/train-000.parquet` và `data/train-055.parquet`. **Xóa bỏ hoàn toàn cụm từ "Shard Nguồn Sạch Đã Được Xác Minh"**, đổi thành **"Các Shard Nguồn Chưa Xác Minh Được Phạm Vi Rows API của Lô 1"**. Lược bỏ mọi tuyên bố khẳng định quá mức. | **ĐÃ BÓC TÁCH MINH BẠCH** |
| **3b** | **PENDING**: Ghi chú rõ ngay trên tiêu đề và chú thích của sơ đồ "Tuần 1–7" tại Mục 7.2 rằng đây chỉ là minh họa trình tự phụ thuộc giữa các cổng công việc, không phải lịch biểu đã chốt; tiến độ chính thức vẫn là TBD. | Báo cáo Pass 1 ($N=24$), phân tích độ trễ chuỗi phụ thuộc tuần tự. | **Bổ sung ghi chú trực diện trên sơ đồ Mục 7.2:** Đổi tiêu đề sơ đồ thành *"SƠ ĐỒ MINH HỌA TRÌNH TỰ PHỤ THUỘC TUẦN TỰ GIỮA CÁC CỔNG CÔNG VIỆC (ILLUSTRATIVE SEQUENTIAL DEPENDENCY SEQUENCE — KHÔNG PHẢI LỊCH CHỐT)"*. Khẳng định rõ tiến độ toàn chiến dịch 1.000 mẫu chính thức tiếp tục là `CHƯA XÁC ĐỊNH (TBD)`. | **ĐÃ GHI CHÚ RÕ RÀNG** |
| **4** | **LÀM RÕ TEST**: Phân định rạch ròi 150 bài test hồi quy hiện có ($87 + 12 + 9 + 42 = 150$) với các bài test mới cho cơ chế Main Annotation chưa viết. | Test suite hiện hành tại commit `583c52e` trên nhánh `feat/c-calibration-v1-1-4-adjudication`. | **Phân định rạch ròi 2 nhóm test:** Bảng kê chi tiết 150 bài test hiện có theo từng file kiểm thử ($87 + 12 + 9 + 42 = 150$). Tách riêng danh mục các bài test mới đề xuất sẽ được lập trình sau khi Lead D chính thức phê duyệt thiết kế kỹ thuật. | **ĐÃ MINH ĐỊNH RANH GIỚI** |

---

## 1. NGUYÊN TẮC CỐT LÕI & RANH GIỚI QUẢN TRỊ

1. **Bản chất văn bản:** Đây là văn bản **DỰ THẢO ĐỀ XUẤT PHIÊN BẢN 2.4 (PROPOSAL V2.4)** do Thành viên C lập để tiếp thu toàn diện các nhận xét trong Báo cáo thẩm định phương pháp độc lập ngày 11/11/2026 của QA Lead B. Mọi nội dung, phương án và bảng tính trong tài liệu này đều ở trạng thái chờ QA Lead B tái thẩm định và Lead D xem xét phê duyệt; tuyệt đối không tự động phát sinh hiệu lực thi hành và chưa trích xuất bất kỳ mẫu dữ liệu nào.
2. **Khẳng định tính chất con số 1.000 trong PLAN-01:**
   - Con số 1.000 mẫu trong Báo cáo PLAN-01 là **Khung ngân sách công sức dự phóng có điều kiện** (Conditional Projected Effort Budget — 190,79 giờ người) được Lead D phê duyệt về mặt kế toán tài nguyên dự án.
   - Con số 1.000 mẫu **KHÔNG PHẢI LÀ LỆNH TRÍCH XUẤT THỰC TẾ**. Quy mô trích xuất thực tế sẽ do Lead D quyết định theo từng giai đoạn căn cứ vào kết quả thực nghiệm Đợt 1 và cam kết thời gian khả dụng của nhân sự.
3. **Kỷ luật hệ thống bất biến:**
   - `training_blocked = true` (Chặn 100% nạp dữ liệu vào pipeline huấn luyện).
   - `official_test_used = false` (Cô lập tuyệt đối 100% tập kiểm thử chính thức).
   - `main_annotation_status = "LOCKED"` (Chiến dịch gán nhãn chính tiếp tục khóa hoàn toàn).

---

## 2. HIỆN TRẠNG TỪNG LÔ PILOT CHƯA ÁNH XẠ NGUỒN & CHIẾN LƯỢC KHOANH VÙNG CẤP SHARD

Tiếp thu triệt để nhận xét thẩm định của QA Lead B và chỉ đạo của Lead D về việc nhìn thẳng vào hiện trạng dữ liệu trên `data/exclusion_registry.json` và `data/source_audit/phreshphish/recovery_status.json`:

### 2.1 Bóc tách hiện trạng kỹ thuật từng lô loại trừ lịch sử (Lô 1, Lô 2, Lô 3)

1. **Lô 1 (`EXCL-PILOT-01`, 20 mẫu kỹ thuật pilot ban đầu):**
   - *Trạng thái trên registry:* `mapping_status = "unresolved_source_mapping"`, `rows_api_revision_pinned = false`.
   - *Hiện trạng mã băm:* Cả 20/20 mẫu trong `data/exclusion_registry.json` **hoàn toàn không có** `url_sha256`, `normalized_url_sha256`, `html_sha256`, `group_sha256`, và **không có** thông tin vị trí vật lý (`relative_path` hay `row_offset`). Tệp registry hiện chỉ lưu trữ các siêu dữ liệu cấu trúc tóm tắt (`pilot_row_idx`, `label`, `lang`, `html_chars`, `text_chars`, `forms`, `inputs`, `password_inputs`) và `summary_fingerprint_hash`.
   - *Hồ sơ kiểm toán liên quan:* Trong `data/source_audit/phreshphish/recovery_status.json` có ghi nhận tệp kiểm tra đối chiếu `raw20_mapping_check.json` (ghi nhận 20 trường hợp khớp URL/HTML), tuy nhiên tệp này hiện vẫn ở trạng thái `mapping_review_status: "pending_independent_review"`, **chưa được nghiệm thu độc lập và chưa được nạp chính thức vào `data/exclusion_registry.json`**.
   - *Giới hạn đối soát:* Hàm `compute_summary_fingerprint_hash` chỉ băm các trường phái sinh gắn với `pilot_row_idx` và `label`, nên **không thể đối chiếu trực tiếp với các ứng viên thô mới rút từ shard**. Do đó, đối với Lô 1, hệ thống chưa thể bảo đảm cơ chế fail-closed tự động bằng mã băm URL/HTML trên registry.

2. **Lô 2 (`EXCL-REAL-PILOT-32`, 32 mẫu pilot thật Đợt 1):**
   - *Trạng thái trên registry:* `mapping_status = "unresolved_source_mapping"`, `rows_api_revision_pinned = false`.
   - *Hiện trạng mã băm dùng được:* Khác với Lô 1, Lô 2 đã có **đủ 32/32 bộ mã băm** `url_sha256`, `html_sha256`, `group_sha256` trên `data/exclusion_registry.json`. Toàn bộ 32 bộ mã băm này đều đang hoạt động trực tiếp trong hàm `ExclusionRegistry.is_excluded()` để chặn 100% các ứng viên mới trùng URL, HTML hoặc nhóm domain.
   - *Giới hạn còn lại:* Trong registry chưa có trường `relative_path` (tên shard) và `row_offset`.

3. **Lô 3 (`EXCL-PILOT-02` và `EXCL-PILOT-02-REBUILD-e039c774ef5f`, 32 mẫu pilot thật Đợt 2):**
   - *Bản ghi gốc `EXCL-PILOT-02`:* Có đủ 32/32 bộ mã băm `url_sha256`, `html_sha256`, `group_sha256`.
   - *Bản ghi tái lập `EXCL-PILOT-02-REBUILD-e039c774ef5f` (Lô 4):* Đã đạt trạng thái `mapping_status = "resolved"`, `rows_api_revision_pinned = true`, có đầy đủ mã băm và vị trí vật lý được xác định rút từ 2 shard: `data/train-000.parquet` và `data/train-055.parquet`.

4. **Các lô hiệu chuẩn từ Lô 5 đến Lô 10:** Đều có đầy đủ mã băm mật mã chuẩn hóa và được xác định gắn liền với 2 shard `data/train-000.parquet` và `data/train-055.parquet`.

### 2.2 Danh mục Shard Cách ly đã xác định và Nhận diện Rủi ro Tồn dư

1. **Danh mục Shard Cách ly đã xác định cụ thể (Known Quarantined Shards):**
   - Căn cứ hồ sơ thực nghiệm và `recovery_status.json`, hai shard Parquet sau đây đã được xác định chắc chắn từng được dùng để lấy mẫu cho các đợt V2 Rebuild và Hiệu chuẩn:
     * `data/train-000.parquet`
     * `data/train-055.parquet`
   - Hai shard này được đưa vào **Danh mục Cách ly Cấm Khai thác (Quarantined Shards Blacklist)** đối với chiến dịch Main Annotation. Mọi script tuyển chọn ứng viên Main Annotation bị cấm đọc dữ liệu từ hai tệp này.
2. **Thừa nhận thẳng thắn về phần nguồn còn lại:**
   - Tiếp thu triệt để nhận xét của QA Lead B, Thành viên C **xóa bỏ hoàn toàn cụm từ "Các Shard Nguồn Sạch Đã Được Xác Minh (Clean Verified Shards)"** khi nói về phần nguồn còn lại.
   - Do Lô 1 (`EXCL-PILOT-01`) thu thập ban đầu qua HuggingFace Rows API với `rows_api_revision_pinned = false` và chưa được nghiệm thu mapping chính thức lên registry, nhóm nghiên cứu **chưa thể chứng minh bằng toán học rằng Rows API của Lô 1 chưa từng chạm tới các shard khác ngoài `train-000` và `train-055`**.
   - Do đó, phần nguồn còn lại được định vị chính xác là: **"Các Shard Nguồn Chưa Xác Minh Được Phạm Vi Rows API của Lô 1 (Unverified Shards Pending Pilot 1 Scope)"**.
3. **Quy trình giải quyết và Thẩm quyền của Lead D:**
   - *Giải pháp ưu tiên:* Thành viên C phối hợp cùng QA Lead B tổ chức nghiệm thu độc lập hồ sơ `raw20_mapping_check.json` / `v1_mapping_check.json` để cập nhật bổ sung 20 mã băm URL/HTML và locator của Lô 1 vào `data/exclusion_registry.json`.
   - *Trường hợp chưa hoàn tất nghiệm thu Lô 1:* Thành viên C lập báo cáo kiểm kê rủi ro tồn dư, trình Lead D ban hành **Quyết định phê duyệt phạm vi nguồn và chấp nhận mức rủi ro tồn dư pilot (Decision on Unresolved Pilot Scope & Residual Risk Acceptance)** trước khi mở cổng trích xuất mẫu. Tuyệt đối không tự ý khẳng định đã loại trừ 100%.

---

## 3. ĐẶC TẢ CỔNG KIỂM TRA ĐỘNG SỔ BỘ LOẠI TRỪ (YÊU CẦU ĐỀ XUẤT CẦN TRIỂN KHAI)

- **Trạng thái thực tế:** Cơ chế này là **YÊU CẦU KỸ THUẬT ĐỀ XUẤT CẦN TRIỂN KHAI**, hiện chưa có trong mã nguồn chạy.
- **Quy trình 3 bước kiểm tra động của hàm `verify_exclusion_registry_integrity()`:**
  1. *Kiểm tra nhất quán số lượng động (Dynamic Consistency):* Đọc `data/exclusion_registry.json`. Lấy $E_{\text{decl}} = \text{total\_excluded\_entries}$ và $S_{\text{decl}} = \text{total\_excluded\_samples}$. Tính toán động: $\text{len}(\text{exclusions}) == E_{\text{decl}}$ và $\sum b[\text{"n\_samples"}] == S_{\text{decl}}$. Sai lệch ném lỗi `ValueError`.
  2. *Kiểm tra cam kết hạn chế (Restricted Commitment Check):* Quét qua toàn bộ các lô có `status: "resolved_in_restricted_dossier"` (như Lô 10). Đối chiếu SHA-256 thực tế của tệp hạn chế với `commitment_sha256` trong registry. Sai lệch dù 1 ký tự hex ném `RuntimeError`.
  3. *Kiểm tra an toàn phân vùng Shard:* Đối chiếu danh sách shard dự kiến trích xuất với danh mục Shard bị cách ly (`train-000.parquet`, `train-055.parquet`). Cố gắng đọc từ shard bị cách ly sẽ kích hoạt cơ chế dừng an toàn (Fail-Closed Stop).

---

## 4. HỢP ĐỒNG DỮ LIỆU GÁN NHÃN MÙ (BLIND VIEW CONTRACT V1.2): BẢO VỆ TÍNH MÙ TUYỆT ĐỐI

Tiếp thu ý kiến thẩm định Điểm 1 của QA Lead B về việc tách bạch phiên bản hợp đồng dữ liệu khỏi phiên bản Codebook:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 1. BLIND VIEW PHÁT HÀNH CHO MAIN ANNOTATION (A VÀ B ĐỀU TRUNG TÍNH)          │
│ • Tệp: main_annotation_blind_view.json                                      │
│ • Định danh hợp đồng dữ liệu riêng: blind_contract_version: "1.2.0"         │
│ • Giữ nguyên quy tắc gán nhãn: codebook_version: "1.1.0"                    │
│ • HOÀN TOÀN KHÔNG CHỨA TRƯỜNG random_subset (DÙ THẬT HAY GIẢ)               │
│ • Chỉ gồm các trường quan sát an toàn: sample_id, url, page_text, summary...│
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼ (A và B chạy CLI gán nhãn độc lập)
┌─────────────────────────────────────────────────────────────────────────────┐
│ 2. BẢN GHI GÁN NHÃN PASS 1 (ANNOTATION RECORDS)                             │
│ • Tệp: intake_pass1_A.jsonl / intake_pass1_B.jsonl                          │
│ • KHÔNG CHỨA TRƯỜNG random_subset TRONG DỮ LIỆU GÁN NHÃN CỦA MAIN           │
│ • Bảo toàn tính trung thực học thuật: 0 lưu trữ giá trị boolean giả         │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼ (Sau khi Pass 1 đã nộp và khóa mã băm)
┌─────────────────────────────────────────────────────────────────────────────┐
│ 3. HỒ SƠ PHÂN TẦNG LẤY MẪU HẠN CHẾ CỦA C (SAMPLING STRATIFICATION MANIFEST) │
│ • Tệp: data/restricted/main_annotation_sampling_manifest.json               │
│ • Lưu trữ bảng phân tầng thực tế đã khóa:                                   │
│   { "MAIN-0001": {"stratum": "random_30", "is_random_subset": true}, ... }  │
│ • Niêm phong mật mã với SHA-256 công bố trong release manifest từ đầu đợt   │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼ (Khớp nối độc lập trong evaluate_kappa)
┌─────────────────────────────────────────────────────────────────────────────┐
│ 4. PHÉP JOIN ĐỘC LẬP TÍNH COHEN'S KAPPA CHÍNH THỨC                          │
│ • Script evaluate_kappa thực hiện Inner Join độc lập:                       │
│   Record_A[sample_id] ⨝ Record_B[sample_id] ⨝ StrataMap[sample_id]         │
│ • Chỉ lọc các mẫu có is_random_subset == True để tính kappa_primary         │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 4.1 Chi tiết Thay đổi Schema, Tách bạch Phiên bản và CLI

1. **Tách biệt Phiên bản Hợp đồng Dữ liệu khỏi Phiên bản Codebook:**
   - **Phiên bản Codebook giữ nguyên:** Toàn bộ dự án tiếp tục tuân thủ nghiêm ngặt **`codebook_version = "1.1.0"`** theo đúng `docs/CODEBOOK_V1_1.md` đã được Lead D phê duyệt. Thành viên C tuyệt đối không tự tiện nâng cấp Codebook lên 1.2.0. Mọi đề xuất thay đổi taxonomy hay quy tắc gán nhãn phải trình văn bản sửa đổi Codebook riêng.
   - **Bổ sung Định danh Hợp đồng Dữ liệu riêng:** Tệp Blind View và manifest của Main Annotation sử dụng trường định danh kỹ thuật: **`blind_contract_version = "1.2.0"`** (hoặc `view_schema_version = "1.2.0"`). Trường này thuần túy phục vụ cấu hình parser của CLI và Validator, không làm thay đổi ngữ nghĩa nhãn.
2. **Schema Blind View của Main (`main_annotation_blind_view.json`):**
   - Loại bỏ hoàn toàn trường `random_subset` khỏi danh sách `ALLOWED_BLIND_SAMPLE_KEYS` của Hợp đồng v1.2.
   - Mỗi `BlindSample` chỉ chứa: `sample_id` (trung tính `MAIN-XXXX`), `url`, `page_text`, `structure_summary`, `codebook_version` (`"1.1.0"`), `blind_contract_version` (`"1.2.0"`), và các trường bản dịch ngoại tuyến MarianMT theo R-A09.
3. **Schema Bản ghi Gán nhãn (`AnnotationRecord`):**
   - Trong chế độ Hợp đồng v1.2, bản ghi của người gán nhãn không chứa trường `random_subset`. Bản ghi chỉ lưu trữ trung thực phán đoán: `class_label`, `identity_role`, `primary_org`, `evidence_quote`, `evidence_note`, `difficult_case`, `seconds_spent`. Tuyệt đối không ghi cờ boolean giả vào kết quả của B.
4. **Tương thích ngược với Calibration cũ (Backward Compatibility):**
   - Các gói dữ liệu và bản ghi của Calibration Runway A (`blind_contract_version = "1.1.0"`) trong `data/restricted/` vẫn giữ nguyên trường `random_subset: bool` lịch sử.
   - CLI và Validator kiểm tra theo `blind_contract_version`:
     * Nếu `blind_contract_version == "1.1.0"`: Tiếp tục kiểm tra `random_subset: bool` như cũ.
     * Nếu `blind_contract_version == "1.2.0"`: Bỏ qua kiểm tra trường `random_subset` trong Blind View và không đòi hỏi cờ này trong bản ghi đầu ra.
5. **Phép Join sau khi khóa Pass 1 (Post-Pass-1 Independent Join):**
   - Sau khi cả A và B đã nộp bản ghi Pass 1 và đã được khóa mã băm SHA-256 bất biến:
   - Module `evaluate_kappa.py` nạp tệp nhãn của A, tệp nhãn của B, và tệp phân tầng hạn chế của C (`main_annotation_sampling_manifest.json`).
   - Thực hiện phép kết hợp:
     $$\text{JoinedSample}_i = \text{Label}_A(i) \bowtie \text{Label}_B(i) \bowtie \text{StrataMap}(i)$$
   - Chỉ số $\kappa_{\text{primary}}$ trước phân xử **chỉ tính trên các mẫu có $\text{StrataMap}(i)[\text{"is\_random\_subset"}] == \text{True}$**, bảo đảm mẫu số đúng $N_{\text{random}}$ đại diện tự nhiên mà bản ghi của B hoàn toàn không bị vấy bẩn bởi cờ giả.

---

## 5. NGUỒN DỮ LIỆU ĐÃ KHÓA & QUY TRÌNH PHÊ DUYỆT PHISHVN

1. **Nguồn dữ liệu hợp lệ duy nhất:** `phreshphish` tại revision `eabec4b7a66324b79cc8a0ad856d1731dc26fe1a` (56 shards, 498.255 bản ghi trong `configs/source_manifest.json`).
2. **Quy chế nguồn PhishVN:** PhishVN được xếp vào diện **Nguồn đề xuất thứ cấp — CHƯA ĐƯỢC PHÉP TRÍCH XUẤT**.
3. **Quy trình 4 bước bắt buộc trước khi dùng PhishVN:** Lập `phishvn_manifest.json` riêng $\rightarrow$ Kiểm toán SHA-256 checksums $\rightarrow$ Xác định scope $\rightarrow$ Trình Lead D phê duyệt nguồn bằng văn bản.

---

## 6. CHUẨN HÓA DỊCH NGOẠI TUYẾN MARIANMT: NGÔN NGỮ ĐÍCH TIẾNG ANH & REVISION ĐÃ KHÓA

1. **Ngôn ngữ đích:** Đính chính dứt khoát là **TIẾNG ANH (EN)**, không phải tiếng Việt.
2. **Danh mục mô hình và revision khóa cứng (căn cứ `clean_calibration_translations.json`):**
   - Tiếng Nhật (`ja`): `Helsinki-NLP/opus-mt-ja-en@0770961` $\rightarrow$ Đích `en`.
   - Tiếng Nga (`ru`): `Helsinki-NLP/opus-mt-ru-en@fbd6dc7` $\rightarrow$ Đích `en`.
   - Tiếng Trung (`zh`): `Helsinki-NLP/opus-mt-zh-en` (phải khóa revision trước khi dùng) $\rightarrow$ Đích `en`.
   - Tiếng Việt (`vi`), Tiếng Anh (`en`): Giữ nguyên, không dịch (`translation_provided = false`).
3. **Tuân thủ quy tắc R-A09:** Giữ nguyên 100% `page_text` gốc; bản dịch tiếng Anh ngoại tuyến đặt trong `translated_text` kèm 5 trường metadata; kiểm tra mã băm `translation_sha256` fail-closed nếu bị chỉnh sửa.

---

## 7. ĐỒNG BỘ CƠ CẤU MẪU CỦA B, ĐỊNH LƯỢNG TIẾN ĐỘ & ĐỐI CHIẾU CÔNG SỐ VỚI PLAN-01

### 7.1 Đồng bộ và Thống nhất Cơ cấu Mẫu của Annotator B
Tiếp thu ý kiến thẩm định Điểm 1c của QA Lead B về sự không nhất quán giữa con số 405 mẫu và 350 mẫu:
- **Kịch bản Cơ sở Chuẩn mực (PLAN-01 Baseline — Áp dụng chính thức trong V2.4):**
  * Rút ngẫu nhiên độc lập 30% toàn bộ corpus: $N_{\text{random}} = 300\text{ mẫu}$.
  * Ca khó phát sinh từ 700 mẫu còn lại do Annotator A gắn cờ `difficult_case=true`: Dự phóng theo tỷ lệ 15% của PLAN-01 là $700 \times 0,15 = 105\text{ mẫu}$.
  * **Tổng khối lượng gán nhãn kép của Annotator B:**
    $$N_{B} = 300\text{ mẫu (random)} + 105\text{ mẫu (khó)} = \mathbf{405\text{ mẫu}}$$
  * Khối lượng này khớp 100% với Bảng 1 và Bảng 4 của `plan_01_calibration_effort_report.json`.
- **Kịch bản Độ nhạy Tối thiểu (Low-Difficulty Sensitivity Scenario):**
  * Trong trường hợp chất lượng crawl của nguồn tốt hơn dự kiến và tỷ lệ ca khó phát sinh chỉ ở mức 7,14% (50 mẫu), tổng mẫu của B sẽ là $300 + 50 = 350\text{ mẫu}$.
  * Bản V2.4 chính thức lấy **Kịch bản Cơ sở 405 mẫu** làm căn cứ lập kế hoạch ngân sách và phân bổ thời gian.

### 7.2 Phép tính định lượng chứng minh tính bất khả thi của tiến độ 1 tuần cho 1.000 mẫu
- **Thời gian làm việc tối đa trong 1 tuần (Full-time Sprint 40h):** $T_{\text{max}} = 40\text{ giờ} = 2.400\text{ phút}$.
- **Tốc độ gán nhãn đòi hỏi để hoàn thành 1.000 mẫu trong 40h:**
  $$t_{\text{required}} \le \frac{2.400\text{ phút}}{1.000\text{ mẫu}} = \mathbf{2,40\text{ phút/mẫu}} = \mathbf{144\text{ giây/mẫu}}$$
- **Tốc độ trung bình thực đo của Annotator A (Calibration Runway A, $N=24$):**
  $$t_{\text{actual}} = \mathbf{380,16\text{ giây/mẫu}} = \mathbf{6,34\text{ phút/mẫu}}$$
- **Thời gian thực tế riêng Annotator A cần để hoàn thành 1.000 mẫu:**
  $$T_A = 1.000\text{ mẫu} \times 6,34\text{ phút/mẫu} = 6.340\text{ phút} = \mathbf{105,67\text{ giờ}}$$
- **Số tuần A cần làm việc liên tục ở cường độ full-time (40h/tuần):**
  $$\frac{105,67\text{ giờ}}{40\text{ giờ/tuần}} = \mathbf{2,64\text{ tuần}} \quad (\approx 19\text{ ngày làm việc liên tục})$$
  *(Tốc độ thực tế hiện đo chậm hơn định mức 40h tới 2,64 lần. Nếu A làm việc bán thời gian 15h/tuần, A cần tới ~7,0 tuần chỉ riêng Pass 1).*

### 7.3 Sơ đồ Minh họa Trình tự Phụ thuộc Tuần tự giữa các Cổng Công việc (Illustrative Dependency Sequence — Không phải Lịch chốt)

> [!IMPORTANT]
> **Ghi chú bắt buộc về tính chất sơ đồ:** Sơ đồ phân kỳ dưới đây thuần túy là **Bản vẽ kỹ thuật minh họa trình tự phụ thuộc nghiệp vụ tuần tự giữa các cổng công việc (Illustrative Sequential Dependency Sequence)** dựa trên giả định mỗi thành viên làm việc bán thời gian ~15 giờ/tuần. Sơ đồ này **KHÔNG PHẢI LÀ LỊCH BIỂU ĐÃ CHỐT**. Tiến độ chính thức của toàn bộ chiến dịch 1.000 mẫu tiếp tục ở trạng thái **CHƯA XÁC ĐỊNH (TBD)** cho đến khi có kết quả thực nghiệm Đợt 1 và văn bản cam kết giờ khả dụng của A và B.

```
[GIAI ĐOẠN 1: C CHUẨN BỊ BLIND VIEW & PHÁT HÀNH ĐỢT]
         │
         ▼ (Sau khi Blind View được QA Lead B duyệt và Lead D phê duyệt mở phiên)
[GIAI ĐOẠN 2: A GÁN TOÀN BỘ 1.000 MẪU & B GÁN 405 MẪU ĐỘC LẬP (PASS 1)]
         │
         ▼ (Sau khi cả A và B đã nộp toàn bộ tệp nhãn và khóa mã băm SHA-256)
[GIAI ĐOẠN 3: C ĐỐI SOÁT BẤT ĐỒNG & TÍNH KAPPA QUA BẢNG PHÂN TẦNG HẠN CHẾ]
         │
         ▼ (Sau khi C phát hành Hồ sơ Phân xử bất đồng độc lập)
[GIAI ĐOẠN 4: LEAD D CHỦ TRÌ PHÂN XỬ PASS 2 & BAN HÀNH BIÊN BẢN PHÂN XỬ]
         │
         ▼ (Sau khi Lead D ký ban hành biên bản phân xử)
[GIAI ĐOẠN 5: QA LEAD B THẨM ĐỊNH ĐỘC LẬP TOÀN BỘ HỒ SƠ & KÝ QA SIGN-OFF]
         │
         ▼ (Sau khi có văn bản QA Sign-off của B)
[GIAI ĐOẠN 6: LEAD D PHÊ DUYỆT ĐÓNG MỐC TOÀN DIỆN CHIẾN DỊCH MAIN ANNOTATION]
```

- **Phân tích độ trễ tuần tự (Pipeline Sequential Latency):** B không thể ký QA khi D chưa phân xử; D không thể phân xử khi A và B chưa nộp nhãn Pass 1. Chuỗi phụ thuộc tuần tự giữa các khâu khiến chiến dịch 1.000 mẫu về mặt toán học và quy trình **không thể nén vào trong 1 tuần (7 ngày dương lịch)**.
- **Tiến độ 1 tuần chỉ khả thi cho Đợt 1 (Quy mô đo lường 60 hoặc 100 mẫu)**.
- **Ngưỡng đồng thuận:** Mục tiêu $\kappa_{\text{primary}} \ge 0,75$ tiếp tục được ghi nhận là **Mục tiêu kỹ thuật đề xuất chờ Lead D chính thức xem xét và phê duyệt**.

### 7.4 Bảng đối chiếu chênh lệch công số so với PLAN-01 (Đồng bộ theo Kịch bản 405 mẫu)

| Thành viên / Vai trò | Phân bổ PLAN-01 được duyệt (Giờ) | Tỷ lệ PLAN-01 (%) | Kịch bản Dự phóng V2.4 đề xuất (Giờ) | Tỷ lệ V2.4 (%) | Độ lệch công số (Giờ) | Giải trình nguyên nhân dịch chuyển cơ cấu kỹ thuật |
|:---|:---:|:---:|:---:|:---:|:---:|:---|
| **Annotator A** | 114,08 | 59,80% | **105,67** | 54,95% | **-8,41** | Chuyển từ định mức thận trọng (410,70s/mẫu = 6,85m) sang thời gian trung bình thực đo Pass 1 ($380,16\text{s/mẫu} = 6,34\text{m}$). |
| **QA Lead B** | 36,21 | 18,98% | **43,15** | 22,44% | **+6,94** | Gán kép 405 mẫu chuẩn PLAN-01 ($405 \times 4,17\text{m} = 28,15\text{h}$) cộng đệm kiểm định QA tuyển chọn, schema và nghiệm thu qua 5 đợt ($15,00\text{h}$). |
| **Thành viên C** | 25,00 | 13,10% | **28,00** | 14,56% | **+3,00** | Quản trị hạ tầng Hợp đồng v1.2, phân đợt batch chống rò rỉ, quản lý tệp phân tầng hạn chế và đối soát reconciliation độc lập. |
| **Lead D** | 15,50 | 8,12% | **15,50** | 8,06% | **0,00** | Phân xử bất đồng Pass 2 cho các ca bất đồng phát sinh cộng thời gian thẩm duyệt mốc tối hậu (khớp chuẩn ngân sách PLAN-01). |
| **TỔNG CỘNG** | **190,79** | **100,00%** | **192,32** | **100,00%** | **+1,53** | **Kịch bản V2.4 đồng bộ 405 mẫu có tổng công số 192,32 giờ (tăng 1,53h = 0,80% so với PLAN-01 do tăng cường thời lượng QA của B), chờ Lead D phê duyệt.** |

---

## 8. BẰNG CHỨNG TRUY XUẤT GIT VÀ RANH GIỚI BỘ KIỂM THỬ

### 8.1 Lịch sử Commit và Bằng chứng Truy xuất Git trên GitHub
- **Kho lưu trữ:** `https://github.com/Anhtuann1404/NCKH_2.git`
- **Nhánh phát triển:** `feat/c-calibration-v1-1-4-adjudication`
- **Các commit đã đồng bộ thành công trên GitHub:**
  * Commit V2.1: [`13e24a0cbf042c486825a67c74ef9332e1935d05`](https://github.com/Anhtuann1404/NCKH_2/commit/13e24a0cbf042c486825a67c74ef9332e1935d05)
  * Commit V2.2: [`4ac51d6eaf7ad67c717075d913c54dee0aa85016`](https://github.com/Anhtuann1404/NCKH_2/commit/4ac51d6eaf7ad67c717075d913c54dee0aa85016)
  * Commit V2.3: [`583c52e63fa91ccd2c074113340820e1c663e010`](https://github.com/Anhtuann1404/NCKH_2/commit/583c52e63fa91ccd2c074113340820e1c663e010)
  * Commit V2.4 (Bản hiện hành): Được tạo và push trực tiếp cùng văn bản này.

### 8.2 Phân định rạch ròi giữa Test Hồi quy Hiện có và Test Đề xuất Mới
Tiếp thu triệt để nhận xét của QA Lead B về việc làm rõ ranh giới các bài kiểm thử:

1. **Bộ test hồi quy mã nguồn hiện có (Existing Codebase Regression Tests — 150/150 PASSED):**
   - **Lệnh thực thi:**
     ```bash
     python -m pytest tests/test_blind_view.py tests/test_clean_calibration_blind_view.py tests/test_difficulty_strata.py tests/test_exclusion_registry.py -v
     ```
   - **Cấu tạo chi tiết của 150 bài test hiện có (đã kiểm chứng qua phân tích AST):**
     * `tests/test_blind_view.py`: **87 hàm test** (kiểm chứng an toàn Blind View v1.1, allowlist trường, strip thẻ nguy hiểm, loại trừ rò rỉ nhãn và tính toàn vẹn bản dịch).
     * `tests/test_clean_calibration_blind_view.py`: **12 hàm test** (kiểm chứng tính hợp lệ của gói view sạch Đợt C).
     * `tests/test_difficulty_strata.py`: **9 hàm test** (kiểm chứng tính toán độc lập 6 cờ chỉ báo mô tả bề mặt).
     * `tests/test_exclusion_registry.py`: **42 hàm test** (kiểm chứng logic loại trừ của 10 lô hiện hành và cam kết Lô 10 ngoài Git).
     * **Tổng cộng: $87 + 12 + 9 + 42 = 150\text{ bài test hiện có}$** (kết quả: 150 passed, 0 failed, 0 skipped, 0 deselected).
2. **Bộ test đề xuất cho các cơ chế mới (Future Proposed Tests — Chưa lập trình & Chưa chạy):**
   - *Test Hợp đồng dữ liệu v1.2:* Kiểm tra tệp `main_annotation_blind_view.json` không chứa key `random_subset`; kiểm tra validator phân nhánh theo `blind_contract_version = "1.2.0"` mà vẫn giữ `codebook_version = "1.1.0"`.
   - *Test Join độc lập:* Kiểm tra `evaluate_kappa` nạp tệp phân tầng hạn chế của C và tính đúng $\kappa_{\text{primary}}$ trên $N_{\text{random}} = 300$ mẫu.
   - *Test cô lập Shard:* Kiểm tra hệ thống dừng an toàn khi phát hiện script cố gắng nạp ứng viên từ `train-000.parquet` và `train-055.parquet`.
   - Toàn bộ danh mục test mới này sẽ được lập trình và tích hợp vào test suite sau khi Lead D chính thức phê duyệt thiết kế kỹ thuật của Bản V2.4.

---

## 9. DANH MỤC NHỮNG ĐIỀU CÒN CHỜ LEAD D QUYẾT ĐỊNH

Thành viên C kính trình QA Lead B và Lead D xem xét các nội dung sau:
1. **QA Lead B tái thẩm định:** Đánh giá việc tiếp thu 4 điểm nhận xét trong Bản V2.4 và phát hành kết luận thẩm định QA chính thức.
2. **Lead D phê duyệt Thiết kế Hợp đồng Dữ liệu v1.2:** Chấp thuận việc giữ nguyên `codebook_version: "1.1.0"` và dùng `blind_contract_version: "1.2.0"` để bỏ hoàn toàn `random_subset` khỏi view và bản ghi Pass 1.
3. **Lead D phê duyệt Quyết định Phạm vi Nguồn và Chấp nhận Rủi ro Tồn dư Lô 1:** Ban hành văn bản phê duyệt cách ly 2 shard đã biết (`train-000`, `train-055`) và quyết định phương án xử lý rủi ro tồn dư của Lô 1.
4. **Lead D phê duyệt Kịch bản Dự phóng Công số V2.4 (192,32 giờ):** Chấp thuận khung ngân sách điều chỉnh đồng bộ theo 405 mẫu của B.
5. **Lead D quyết định Phương án Đợt 1:** Lựa chọn giữa Phương án A (Lô đầu Main) hay Phương án B (Pilot tách riêng); chốt quy mô 60 mẫu hay 100 mẫu.

---

**XÁC NHẬN CỦA THÀNH VIÊN C (DATA PIPELINE & THƯ KÝ KIỂM TOÁN)**  
*(Văn bản dự thảo kỹ thuật V2.4 — Duy trì nghiêm ngặt: training_blocked=true, official_test_used=false, Main Annotation KHÓA 100%)*  

**Nguyễn Thắng**
