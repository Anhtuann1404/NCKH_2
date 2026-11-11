# DỰ THẢO KẾ HOẠCH CHIẾN DỊCH GÁN NHÃN CHÍNH (MAIN ANNOTATION PLAN - PROPOSAL V2.3)

**Dự án:** Nghiên cứu phát hiện website phishing mạo danh tổ chức bằng học máy kết hợp URL và nội dung trang (NCKH_2)  
**Mã văn bản:** `PLAN-MAIN-ANNOTATION-PROPOSAL-V2.3`  
**Phiên bản:** `2.3.0-REVISED-DRAFT`  
**Ngày lập:** 11/11/2026  
**Đơn vị lập:** Thành viên C (Nguyễn Thắng — Data Pipeline & Thư ký Kiểm toán)  
**Trạng thái quản trị:** `DRAFT_V2.3_PENDING_LEAD_D_REVIEW_AND_QA_APPRAISAL` (Dự thảo V2.3 — Tiếp thu toàn diện 3 yêu cầu kiểm toán ngày 11/11/2026 của Lead D; chờ Lead D xem xét và chuyển QA Lead B thẩm định độc lập; tuyệt đối duy trì training_blocked=true, official_test_used=false, chưa trích xuất mẫu hay mở Pass 1)  
**Căn cứ pháp lý & kỹ thuật:**  
- Ý kiến chỉ đạo kiểm toán của Lead D (Nguyễn Anh Tuấn) đối với bản dự thảo V2.2 ngày 11/11/2026 (3 yêu cầu cốt lõi về hợp đồng dữ liệu, pilot unresolved và định lượng tiến độ).  
- Giao thức dữ liệu (`docs/DATA_PROTOCOL.md`), Giao thức thực nghiệm (`docs/EXPERIMENT_PROTOCOL.md`) và Codebook v1.1 (`docs/CODEBOOK_V1_1.md`).  
- Báo cáo khung ngân sách dự phóng công sức PLAN-01 (`plan_01_calibration_effort_report.json`).  
- Sổ bộ loại trừ `data/exclusion_registry.json` và hồ sơ hạn chế niêm phong `data/restricted/clean_calibration_exclusion_mapping_c_32.json`.  
- Kỷ luật Ponytail Engineering và Academic Research Skills (ARS).

---

## BẢNG ĐỐI CHIẾU TIẾP THU VÀ HIỆU CHỈNH 3 YÊU CẦU KIỂM TOÁN CỦA LEAD D (ĐỢT 4)

| # | Yêu cầu kiểm toán của Lead D | Căn cứ mã nguồn / Tài liệu hiện hành | Phương án hiệu chỉnh trong Bản V2.3 | Phép kiểm & Bằng chứng thực tế |
|:---:|:---|:---|:---|:---|
| **1** | Không dùng `random_subset=true` giả cho bản ghi của B (sai bản chất ca khó). Đề xuất **một hợp đồng dữ liệu duy nhất**: thông tin phân tầng chỉ ở bảng hạn chế đã khóa; Blind View và bản ghi Pass 1 của Main không chứa `random_subset` giả. Nêu rõ thay đổi schema, CLI, tương thích Calibration cũ, phép join và test. | `src/phishing/annotation/blind_view.py`, `scripts/annotate_cli.py`, `src/phishing/annotation/__init__.py`. | **Thiết lập Hợp đồng Dữ liệu Duy nhất (Clean Blind Data Contract v1.2):** Trường `random_subset` bị LOẠI BỎ HOÀN TOÀN khỏi Blind View và bản ghi Pass 1 của Main Annotation. Tách biệt tuyệt đối thuộc tính phân tầng ra tệp cam kết hạn chế `main_annotation_sampling_manifest.json` của C. CLI Main Mode không ghi trường này. Giữ tương thích ngược với Calibration v1.1 qua phân nhánh phiên bản. Script `evaluate_kappa` thực hiện phép Join độc lập sau Pass 1 để lọc đúng $N_{\text{random}}$ mẫu. | Ranh giới mù tuyệt đối và dữ liệu trung thực 100%: Bản ghi Pass 1 không chứa bất kỳ giá trị boolean giả nào. Test chứng minh view 0 rò rỉ và phép join tái lập chính xác $N_{\text{random}}$. |
| **2** | Sửa đặc tả xử lý lô pilot chưa ánh xạ (Lô 1–3). `summary_fingerprint_hash` gồm số dòng/nhãn/thống kê cấu trúc, không đối chiếu chắc chắn với ứng viên mới; không gọi chỉ dừng khi phát hiện trùng fingerprint là fail-closed. Trình cách khôi phục ánh xạ hoặc khoanh vùng nguồn; thừa nhận rủi ro tồn dư xin D phê duyệt. | `src/phishing/data/exclusion.py` (hàm `compute_summary_fingerprint_hash`), `data/exclusion_registry.json`. | **Minh bạch hóa giới hạn kỹ thuật & Chiến lược 2 mũi nhọn:** Thừa nhận `summary_fingerprint_hash` không thể đối chiếu hash thô với ứng viên shard mới. Đề xuất: (1) Mũi nhọn khôi phục ánh xạ URL/HTML gốc qua truy vết kho lịch sử; (2) Mũi nhọn khoanh vùng (Quarantine/Blacklist) toàn bộ các shard nguồn đã từng khai thác pilot cũ, cấm rút mẫu Main từ đó. Ghi nhận rõ rủi ro tồn dư và xin Quyết định riêng của Lead D, không tuyên bố đã loại trừ 100%. | Phân tích an toàn: Cô lập cấp shard ngăn chặn rò rỉ ngay cả khi không có URL thô của pilot cũ. |
| **3** | Sửa điều kiện tiến độ một tuần thành phép tính định lượng: Với A có 40h, 1.000 mẫu đòi hỏi tốc độ $\le 2,4\text{ phút/mẫu}$; với tốc độ đo được 6,34 phút/mẫu, riêng A cần 105,67h. Tính tiếp giờ B, C, D và chuỗi phụ thuộc tuần tự. Không dùng điều kiện ">40h/tuần" như bằng chứng đủ. Ngưỡng $\kappa \ge 0,75$ là đề xuất chờ D duyệt. | Báo cáo Pass 1 ($N=24$): A mean 6,34 min/mẫu, B mean 4,17 min/mẫu. Khung PLAN-01 (190,79h). | **Chứng minh toán học về tính bất khả thi của tiến độ 1 tuần:** Trình bày phép tính định lượng chi tiết: 40h sprint $\rightarrow$ đòi hỏi $\le 2,40\text{ phút/mẫu}$, trong khi thực tế đo được 6,34 phút/mẫu $\rightarrow$ riêng A cần 105,67h ($\approx 2,64\text{ tuần}$). Phân tích độ trễ tuần tự (Pipeline Latency: C tạo view $\rightarrow$ A/B gán $\rightarrow$ C đối soát $\rightarrow$ D phân xử $\rightarrow$ B QA $\rightarrow$ D duyệt) chứng minh không thể nén vào 7 ngày. Ngưỡng $\kappa \ge 0,75$ ghi rõ là mục tiêu kỹ thuật đề xuất chờ D phê duyệt. | Bảng tính định lượng công số và độ trễ tuần tự tại Mục 7. |

---

## 1. NGUYÊN TẮC CỐT LÕI & RANH GIỚI QUẢN TRỊ

1. **Bản chất văn bản:** Đây là văn bản **DỰ THẢO ĐỀ XUẤT PHIÊN BẢN 2.3 (PROPOSAL V2.3)** do Thành viên C lập để tiếp thu toàn diện 3 yêu cầu kiểm toán ngày 11/11/2026 của Lead D. Mọi nội dung, phương án và bảng tính trong tài liệu này đều ở trạng thái chờ Lead D phê duyệt, tuyệt đối không tự động phát sinh hiệu lực thi hành và chưa trích xuất bất kỳ mẫu dữ liệu nào.
2. **Khẳng định tính chất con số 1.000 trong PLAN-01:**
   - Con số 1.000 mẫu trong Báo cáo PLAN-01 là **Khung ngân sách công sức dự phóng có điều kiện** (Conditional Projected Effort Budget — 190,79 giờ người) được Lead D phê duyệt về mặt kế toán tài nguyên dự án.
   - Con số 1.000 mẫu **KHÔNG PHẢI LÀ LỆNH TRÍCH XUẤT THỰC TẾ**. Quy mô trích xuất thực tế sẽ do Lead D quyết định theo từng giai đoạn căn cứ vào kết quả thực nghiệm Đợt 1 và cam kết thời gian khả dụng của nhân sự.
3. **Kỷ luật hệ thống bất biến:**
   - `training_blocked = true` (Chặn 100% nạp dữ liệu vào pipeline huấn luyện).
   - `official_test_used = false` (Cô lập tuyệt đối 100% tập kiểm thử chính thức).
   - `main_annotation_status = "LOCKED"` (Chiến dịch gán nhãn chính tiếp tục khóa hoàn toàn).

---

## 2. MINH BẠCH HÓA GIỚI HẠN CỦA CÁC LÔ PILOT CHƯA ÁNH XẠ NGUỒN & CHIẾN LƯỢC KHOANH VÙNG NGUỒN

Tiếp thu triệt để ý kiến chỉ đạo của Lead D về việc nhìn thẳng vào sự thật dữ liệu và không tạo ra cảm giác an toàn giả tạo (security theater):

### 2.1 Bản chất kỹ thuật của `summary_fingerprint_hash` và Giới hạn đối soát
Căn cứ vào mã nguồn thực thi tại `src/phishing/data/exclusion.py` (dòng 19–39):
```python
def compute_summary_fingerprint_hash(sample: Dict[str, Any]) -> str:
    canonical = json.dumps({
        "pilot_row_idx": sample.get("pilot_row_idx", sample.get("row_idx")),
        "label": sample.get("label"),
        "lang": sample.get("lang"),
        "html_chars": sample.get("html_chars"),
        "text_chars": sample.get("text_chars"),
        "forms": sample.get("forms"),
        "inputs": sample.get("inputs"),
        "password_inputs": sample.get("password_inputs"),
    }, sort_keys=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
```
- **Hạn chế cố hữu:** Hàm này băm các siêu dữ liệu cấu trúc phái sinh kết hợp chỉ số dòng pilot (`pilot_row_idx`) và nhãn (`label`). Khi trích xuất một ứng viên thô hoàn toàn mới từ shard Parquet, ứng viên đó **chưa hề có trường `pilot_row_idx` hay `label`**, và độ dài ký tự/số thẻ có thể có phương sai nhỏ tùy bộ parser.
- **Kết luận khoa học:** Việc chỉ so sánh `summary_fingerprint_hash` **KHÔNG THỂ BẢO ĐẢM 100% FAIL-CLOSED** đối với các mẫu thô mới trích xuất từ shard. Thành viên C xin đính chính, không tuyên bố rằng cơ chế này đã loại trừ hoàn toàn các lô pilot chưa ánh xạ nguồn.

### 2.2 Chiến lược xử lý 2 mũi nhọn đối với Lô 1, 2, 3 (`unresolved_source_mapping`)
Để bảo vệ tập dữ liệu thực nghiệm trước nguy cơ rò rỉ pilot lịch sử, Thành viên C đề xuất chiến lược kết hợp:

1. **Mũi nhọn 1: Khôi phục Ánh xạ Độc lập (Verifiable Provenance Recovery):**
   - Thành viên C thực hiện rà soát các bản sao lưu cục bộ, commit lịch sử ban đầu và log crawl để tìm lại danh sách URL/HTML thô của Lô 1 (`EXCL-PILOT-01`, 20 mẫu) và Lô 2 (`EXCL-REAL-PILOT-32`, 32 mẫu).
   - Khi tìm lại được, trích xuất đầy đủ 4 mã băm chuẩn hóa: `url_sha256`, `normalized_url_sha256`, `html_sha256`, `group_sha256` để nâng cấp trạng thái từ `unresolved_source_mapping` lên `resolved` (tương tự như Lô 4 đã tái lập thành công cho Lô 3).
2. **Mũi nhọn 2: Khoanh vùng Cách ly Cấp Shard (Shard-Level Quarantine / Blacklist):**
   - Trong thời gian chưa thể khôi phục 100% URL thô của Lô 1 và Lô 2:
   - Hệ thống xác định toàn bộ các file shard Parquet đã từng được nạp để lấy mẫu cho các đợt pilot sơ bộ (dựa theo commit lịch sử và date audit).
   - **Đưa toàn bộ các shard nghi vấn này vào Danh mục Cách ly Cấm Khai thác (Quarantined Shards Blacklist).**
   - Mọi ứng viên Main Annotation chỉ được phép trích xuất từ **Các Shard Nguồn Sạch Đã Được Xác Minh (Clean Verified Shards)** nằm ngoài danh mục cách ly. Cơ chế này loại bỏ nguy cơ trùng lặp từ gốc rễ phân vùng vật lý.

### 2.3 Thừa nhận Rủi ro Tồn dư & Thẩm quyền Phê duyệt của Lead D
- **Minh bạch rủi ro tồn dư:** Nếu một URL xuất hiện trong pilot cũ nhưng nằm trên một shard sạch chưa được khoanh vùng, nguy cơ trùng lặp vẫn tồn tại ở mức lý thuyết nếu không có URL hash 1-1.
- **Thẩm quyền quyết định:** Thành viên C sẽ lập báo cáo kiểm kê chi tiết các shard bị cách ly và rủi ro tồn dư, trình Lead D ban hành **Quyết định phê duyệt phạm vi nguồn và chấp nhận rủi ro tồn dư pilot (Decision on Unresolved Pilot Scope & Residual Risk Acceptance)** trước khi chạy trích xuất ứng viên Main Annotation.

---

## 3. ĐẶC TẢ CỔNG KIỂM TRA ĐỘNG SỔ BỘ LOẠI TRỪ (YÊU CẦU ĐỀ XUẤT CẦN TRIỂN KHAI)

Tiếp thu chỉ đạo của Lead D về việc loại bỏ các hằng số viết cứng (hardcoded 246/10) và xây dựng cơ chế kiểm soát động:
- **Trạng thái thực tế:** Cơ chế này là **YÊU CẦU KỸ THUẬT ĐỀ XUẤT CẦN TRIỂN KHAI**, hiện chưa có trong mã nguồn chạy.

### 3.1 Quy trình 3 bước kiểm tra động của hàm `verify_exclusion_registry_integrity()`
1. **Kiểm tra nhất quán số lượng động (Dynamic Consistency):**
   - Đọc `data/exclusion_registry.json`. Lấy $E_{\text{decl}} = \text{total\_excluded\_entries}$ và $S_{\text{decl}} = \text{total\_excluded\_samples}$.
   - Tính toán động trên danh sách lô:
     $$E_{\text{calc}} = \text{len}(\text{exclusions}) \quad \text{và} \quad S_{\text{calc}} = \sum_{b \in \text{exclusions}} b[\text{"n\_samples"}]$$
   - Yêu cầu bắt buộc: $E_{\text{calc}} == E_{\text{decl}}$ và $S_{\text{calc}} == S_{\text{decl}}$. Bất kỳ sự sai lệch nào đều ném ngoại lệ `ValueError`.
2. **Kiểm tra cam kết hạn chế (Restricted Commitment Check):**
   - Quét qua toàn bộ các lô có `status: "resolved_in_restricted_dossier"` (như Lô 10).
   - Kiểm tra sự tồn tại vật lý của tệp hồ sơ hạn chế tại `data/restricted/`.
   - Tính toán SHA-256 thực tế của tệp và đối chiếu với `commitment_sha256` trong registry. Sai lệch dù 1 ký tự hex ném `RuntimeError`.
3. **Kiểm tra an toàn phân vùng Shard:**
   - Đối chiếu danh sách shard dự kiến trích xuất với danh mục Shard bị cách ly (Quarantined Shards). Nếu phát hiện cố gắng đọc từ shard bị cách ly mà chưa có quyết định phê duyệt của D, hệ thống lập tức dừng an toàn (Fail-Closed Stop).

---

## 4. HỢP ĐỒNG DỮ LIỆU DUY NHẤT: BẢO VỆ TÍNH MÙ TUYỆT ĐỐI KHÔNG DÙNG GIÁ TRỊ GIẢ

Tiếp thu chỉ đạo của Lead D ("không dùng random_subset=true giả cho mọi bản ghi của B; đề xuất một hợp đồng dữ liệu duy nhất: thông tin phân tầng chỉ ở bảng hạn chế đã khóa; Blind View và bản ghi Pass 1 của Main không chứa một giá trị random_subset giả"):

Thành viên C xin đề xuất **Hợp đồng Dữ liệu Gán nhãn Mù Main Annotation v1.2 (Clean Blind Data Contract v1.2)**:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 1. BLIND VIEW PHÁT HÀNH CHO MAIN ANNOTATION (A VÀ B ĐỀU TRUNG TÍNH)          │
│ • Tệp: main_annotation_blind_view.json                                      │
│ • HOÀN TOÀN KHÔNG CHỨA TRƯỜNG random_subset (DÙ THẬT HAY GIẢ)               │
│ • Chỉ gồm các trường quan sát an toàn: sample_id, url, page_text, summary...│
│ • Ranh giới mù tuyệt đối: Người gán chỉ tập trung vào bằng chứng trang      │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼ (A và B chạy CLI gán nhãn độc lập)
┌─────────────────────────────────────────────────────────────────────────────┐
│ 2. BẢN GHI GÁN NHÃN PASS 1 (ANNOTATION RECORDS)                             │
│ • Tệp: intake_pass1_A.jsonl / intake_pass1_B.jsonl                          │
│ • KHÔNG CHỨA TRƯỜNG random_subset TRONG DỮ LIỆU GÁN NHÃN CỦA MAIN           │
│ • Bảo toàn tính trung thực học thuật: 0 lưu trữ giá trị giả trong kết quả   │
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

### 4.1 Chi tiết Thay đổi Schema và CLI
1. **Schema Blind View của Main (`main_annotation_blind_view.json`):**
   - Loại bỏ hoàn toàn trường `random_subset` khỏi danh sách `ALLOWED_BLIND_SAMPLE_KEYS` của Main Annotation.
   - Mỗi `BlindSample` chỉ chứa: `sample_id` (trung tính `MAIN-XXXX`), `url`, `page_text`, `structure_summary`, `codebook_version` (`"1.2.0"`), và các trường bản dịch ngoại tuyến MarianMT theo R-A09.
2. **Schema Bản ghi Gán nhãn (`AnnotationRecord`):**
   - Trong chế độ Main (`codebook_version: "1.2.0"`), trường `random_subset` được định nghĩa là tùy chọn hoặc không xuất hiện trong bản ghi xuất ra của người gán nhãn. Bản ghi gán nhãn chỉ phản ánh trung thực phán đoán của người gán: `class_label`, `identity_role`, `primary_org`, `evidence_quote`, `evidence_note`, `difficult_case`, `seconds_spent`.
   - Tuyệt đối không ghi trường `random_subset: true` giả vào bản ghi của các ca khó bổ sung.
3. **Tương thích ngược với Calibration cũ (Backward Compatibility):**
   - Các gói dữ liệu và bản ghi của Calibration Runway A (v1.1) đã khóa trong `data/restricted/` vẫn giữ nguyên trường `random_subset: bool` lịch sử (không sửa đổi lịch sử).
   - CLI và Validator phân nhánh kiểm tra:
     * Nếu `codebook_version == "1.1.0"`: Tiếp tục kiểm tra `random_subset: bool` như cũ.
     * Nếu `codebook_version == "1.2.0"`: Bỏ qua hoặc cấm trường `random_subset` trong Blind View và bản ghi người gán.
4. **Phép Join sau khi khóa Pass 1 (Post-Pass-1 Independent Join):**
   - Sau khi cả A và B đã nộp bản ghi Pass 1 và đã được khóa mã băm SHA-256 bất biến:
   - Module `evaluate_kappa.py` nạp tệp nhãn của A, tệp nhãn của B, và tệp phân tầng hạn chế của C (`main_annotation_sampling_manifest.json`).
   - Thực hiện phép kết hợp:
     $$\text{JoinedSample}_i = \text{Label}_A(i) \bowtie \text{Label}_B(i) \bowtie \text{StrataMap}(i)$$
   - Chỉ số $\kappa_{\text{primary}}$ trước phân xử **chỉ tính trên các mẫu có $\text{StrataMap}(i)[\text{"is\_random\_subset"}] == \text{True}$**, bảo đảm mẫu số đúng $N_{\text{random}}$ đại diện tự nhiên mà bản ghi của B không bao giờ chứa thông tin phân tầng giả.
5. **Kiểm thử đề xuất cần làm trước khi phát hành:**
   - *Test Blinding Integrity:* Quét toàn bộ tệp Blind View của B, khẳng định 100% mẫu không chứa từ khóa hay cờ `random_subset`.
   - *Test Join & Kappa Accuracy:* Giả lập dữ liệu A và B không có `random_subset`, chạy `evaluate_kappa` kết hợp với bảng phân tầng hạn chế, chứng minh chỉ số Kappa tính ra khớp chính xác với kết quả tính trên tập ngẫu nhiên gốc.

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

## 7. BẢNG TÍNH ĐỊNH LƯỢNG TIẾN ĐỘ & ĐỐI CHIẾU CÔNG SỐ SO VỚI PLAN-01

### 7.1 Phép tính định lượng chứng minh tính bất khả thi của tiến độ 1 tuần cho 1.000 mẫu
Để làm rõ bằng số liệu định lượng chính xác:
- **Thời gian làm việc tối đa trong 1 tuần (Full-time Sprint 40h):** $T_{\text{max}} = 40\text{ giờ} = 2.400\text{ phút}$.
- **Tốc độ gán nhãn đòi hỏi để hoàn thành 1.000 mẫu trong 40h:**
  $$t_{\text{required}} \le \frac{2.400\text{ phút}}{1.000\text{ mẫu}} = \mathbf{2,40\text{ phút/mẫu}} = \mathbf{144\text{ giây/mẫu}}$$
- **Tốc độ trung bình thực đo của Annotator A (Calibration Runway A, $N=24$):**
  $$t_{\text{actual}} = \mathbf{380,16\text{ giây/mẫu}} = \mathbf{6,34\text{ phút/mẫu}}$$
- **Thời gian thực tế riêng Annotator A cần để hoàn thành 1.000 mẫu:**
  $$T_A = 1.000\text{ mẫu} \times 6,34\text{ phút/mẫu} = 6.340\text{ phút} = \mathbf{105,67\text{ giờ}}$$
- **Số tuần A cần làm việc liên tục ở cường độ full-time (40h/tuần):**
  $$\frac{105,67\text{ giờ}}{40\text{ giờ/tuần}} = \mathbf{2,64\text{ tuần}} \quad (\approx 19\text{ ngày làm việc liên tục})$$
  *(Lưu ý: Tốc độ thực tế hiện đo chậm hơn định mức 40h tới 2,64 lần. Nếu A làm việc bán thời gian 15h/tuần, A cần tới ~7,0 tuần).*

### 7.2 Phân tích Độ trễ Chuỗi Phụ thuộc Tuần tự (Pipeline Sequential Latency)
Chiến dịch gán nhãn tuân theo quy trình kiểm toán khép kín, gồm các bước phụ thuộc tuần tự nghiêm ngặt, không thể thực hiện song song hoàn toàn:

```
[Tuần 1-3: C chuẩn bị View & A/B gán Pass 1] 
         │
         ▼ (Sau khi Pass 1 nộp và khóa hash)
[Tuần 4: C kiểm tra tính nhất quán & Lập hồ sơ bất đồng]
         │
         ▼ (Sau khi có hồ sơ đối soát)
[Tuần 5: Lead D chủ trì phân xử Pass 2]
         │
         ▼ (Sau khi có biên bản phân xử)
[Tuần 6: QA Lead B kiểm định độc lập & Ký QA sign-off]
         │
         ▼ (Sau khi có văn bản QA)
[Tuần 7: Lead D phê duyệt đóng mốc chính thức]
```

- **Annotator B:** Gán 350 mẫu $\times 4,17\text{ phút/mẫu} = 24,33\text{ giờ}$ gán nhãn độc lập.
- **QA Lead B:** Kiểm định tuyển chọn, schema, test hồi quy, xác minh chữ ký độc lập = $15,00\text{ giờ}$. (Tổng B = $39,33\text{ giờ}$).
- **Thành viên C:** Trích xuất, lọc trùng 4 lớp, tạo Blind View, MarianMT, quản trị bảng phân tầng hạn chế, đối soát Kappa = $30,00\text{ giờ}$.
- **Lead D:** Phân xử 53 ca bất đồng $\times 8\text{ phút/ca} = 7,07\text{ giờ} + 8,00\text{ giờ}$ thẩm định, phê duyệt = $15,07\text{ giờ}$.
- **Kết luận:** Ngay cả khi toàn bộ nhân sự làm việc 40 giờ/tuần, các rào cản phụ thuộc tuần tự giữa các khâu khiến **toàn bộ chiến dịch 1.000 mẫu về mặt toán học và quy trình không thể hoàn thành trong 1 tuần (7 ngày dương lịch)**.
- **Tiến độ một tuần chỉ khả thi đối với Đợt 1 (Quy mô đo lường 60 hoặc 100 mẫu)**. Tiến độ toàn chiến dịch 1.000 mẫu chính thức ở trạng thái **CHƯA XÁC ĐỊNH (TBD)** chờ kết quả thực nghiệm Đợt 1 và cam kết giờ của A và B.
- **Mục tiêu chất lượng:** Ngưỡng đồng thuận $\kappa_{\text{primary}} \ge 0,75$ tiếp tục được ghi nhận là **Mục tiêu kỹ thuật đề xuất chờ Lead D chính thức xem xét và phê duyệt**.

### 7.3 Bảng đối chiếu chênh lệch công số so với PLAN-01
Khung ngân sách PLAN-01 (`plan_01_calibration_effort_report.json`, Bảng 1 & 4) được phê duyệt là **190,79 giờ người**. Dưới đây là bảng đối chiếu chi tiết giữa PLAN-01 và Kịch bản dự phóng hiệu chỉnh V2.3:

| Thành viên / Vai trò | Phân bổ PLAN-01 được duyệt (Giờ) | Tỷ lệ PLAN-01 (%) | Kịch bản Dự phóng V2.3 đề xuất (Giờ) | Tỷ lệ V2.3 (%) | Độ lệch công số (Giờ) | Giải trình nguyên nhân dịch chuyển cơ cấu kỹ thuật |
|:---|:---:|:---:|:---:|:---:|:---:|:---|
| **Annotator A** | 114,08 | 59,80% | **105,67** | 55,59% | **-8,41** | Chuyển từ định mức thận trọng (410,70s/mẫu = 6,85m) sang thời gian trung bình thực đo Pass 1 ($380,16\text{s/mẫu} = 6,34\text{m}$). |
| **QA Lead B** | 36,21 | 18,98% | **39,33** | 20,69% | **+3,12** | Tăng đệm thời gian kiểm định QA tuyển chọn và nghiệm thu độc lập qua 5 đợt phát hành ($15,0\text{h}$) cộng gán đôi 350 mẫu ($24,33\text{h}$). |
| **Thành viên C** | 25,00 | 13,10% | **30,00** | 15,78% | **+5,00** | Bổ sung khối lượng quản trị hạ tầng tính mù 3 tầng, kiểm tra cam kết sổ bộ loại trừ động, quản lý tệp phân tầng hạn chế và đối soát reconciliation. |
| **Lead D** | 15,50 | 8,12% | **15,07** | 7,93% | **-0,43** | Tính toán lại chi tiết thời gian phân xử Pass 2 cho 53 ca bất đồng dự kiến ($7,07\text{h}$) cộng thời gian phê duyệt mốc quản trị ($8,0\text{h}$). |
| **TỔNG CỘNG** | **190,79** | **100,00%** | **190,07** | **100,00%** | **-0,72** | **Kịch bản dự phóng hiệu chỉnh V2.3 giảm 0,72 giờ so với PLAN-01, chờ Lead D xem xét phê duyệt.** |

---

## 8. BẰNG CHỨNG TRUY XUẤT GIT VÀ KẾT QUẢ KIỂM THỬ HỒI QUY

### 8.1 Lịch sử Commit và Bằng chứng Truy xuất Git trên GitHub
- **Kho lưu trữ:** `https://github.com/Anhtuann1404/NCKH_2.git`
- **Nhánh phát triển:** `feat/c-calibration-v1-1-4-adjudication`
- **Các commit đã đồng bộ thành công trên GitHub:**
  * Commit V2.1: [`13e24a0cbf042c486825a67c74ef9332e1935d05`](https://github.com/Anhtuann1404/NCKH_2/commit/13e24a0cbf042c486825a67c74ef9332e1935d05)
  * Commit V2.2: [`4ac51d6eaf7ad67c717075d913c54dee0aa85016`](https://github.com/Anhtuann1404/NCKH_2/commit/4ac51d6eaf7ad67c717075d913c54dee0aa85016)
  * Commit V2.3 (Bản hiện hành): Được tạo và push trực tiếp cùng văn bản này.

### 8.2 Phân định rạch ròi giữa Test Hồi quy Hiện có và Test Đề xuất Mới
1. **Bộ test hồi quy mã nguồn hiện có (Existing Codebase Regression Tests — 150/150 PASSED):**
   - **Lệnh thực thi:**
     ```bash
     python -m pytest tests/test_blind_view.py tests/test_clean_calibration_blind_view.py tests/test_difficulty_strata.py tests/test_exclusion_registry.py -v
     ```
   - **Kết quả đo lường thực tế:** **150 passed**, 0 failed, 0 skipped, 0 deselected (thời gian thực thi: 3.38s).
   - **Phạm vi kiểm thử:**
     * `tests/test_blind_view.py` (33 tests): Kiểm chứng an toàn Blind View v1.1, allowlist trường, strip thẻ nguy hiểm, loại trừ rò rỉ nhãn và tính toàn vẹn bản dịch.
     * `tests/test_clean_calibration_blind_view.py` (4 tests): Kiểm chứng tính hợp lệ của gói view sạch Đợt C.
     * `tests/test_difficulty_strata.py` (12 tests): Kiểm chứng tính toán độc lập 6 cờ chỉ báo mô tả bề mặt.
     * `tests/test_exclusion_registry.py` (101 tests): Kiểm chứng logic loại trừ của 10 lô hiện hành và cam kết Lô 10 ngoài Git.
2. **Bộ test đề xuất cho các cơ chế mới (Future Proposed Tests — Chưa triển khai):**
   - *Test hợp đồng dữ liệu Main v1.2:* Kiểm tra tệp `main_annotation_blind_view.json` không chứa key `random_subset`; kiểm tra CLI ghi nhận bản ghi không có `random_subset`.
   - *Test Join độc lập:* Kiểm tra `evaluate_kappa` nạp tệp phân tầng hạn chế của C và tính đúng $\kappa_{\text{primary}}$ trên $N_{\text{random}}$ mẫu.
   - *Test cách ly shard:* Kiểm tra hệ thống dừng khi phát hiện cố gắng nạp ứng viên từ các shard pilot bị cách ly.
   - Các bài test này sẽ được viết mới và tích hợp vào test suite sau khi Lead D chính thức phê duyệt thiết kế kỹ thuật của Bản V2.3.

---

## 9. DANH MỤC NHỮNG ĐIỀU CÒN CHỜ LEAD D QUYẾT ĐỊNH

Thành viên C kính trình Lead D xem xét và ban hành quyết định đối với các nội dung sau:
1. **Phê duyệt Hợp đồng Dữ liệu Duy nhất Main v1.2:** Thông qua việc loại bỏ hoàn toàn `random_subset` khỏi Blind View và bản ghi Pass 1 của Main, quản lý phân tầng qua tệp cam kết hạn chế của C.
2. **Phê duyệt Chiến lược Xử lý Pilot Unresolved & Danh mục Shard Cách ly:** Chấp thuận phương án khoanh vùng các shard nghi vấn và chấp nhận mức rủi ro tồn dư đã báo cáo.
3. **Phê duyệt Kịch bản Dự phóng Công số Hiệu chỉnh V2.3:** Chấp thuận độ lệch -0,72h và sự dịch chuyển cơ cấu A/B/C/D so với PLAN-01.
4. **Quyết định Quy mô & Bản chất Đợt 1:** Lựa chọn giữa Phương án A (Lô đầu Main) hay Phương án B (Pilot tách riêng); chốt quy mô 60 mẫu hay 100 mẫu.
5. **Thu thập Cam kết Giờ khả dụng:** Yêu cầu Annotator A và QA Lead B nộp văn bản cam kết số giờ khả dụng/tuần để chốt tiến độ chính thức.

---

**XÁC NHẬN CỦA THÀNH VIÊN C (DATA PIPELINE & THƯ KÝ KIỂM TOÁN)**  
*(Văn bản dự thảo kỹ thuật V2.3 — Duy trì nghiêm ngặt: training_blocked=true, official_test_used=false, Main Annotation KHÓA 100%)*  

**Nguyễn Thắng**
