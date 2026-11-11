# KẾ HOẠCH VẬN HÀNH HỢP NHẤT CHIẾN DỊCH GÁN NHÃN CHÍNH (MASTER OPERATIONAL ANNOTATION PLAN - PROPOSAL V3.0)

**Dự án:** Nghiên cứu phát hiện website phishing mạo danh tổ chức bằng học máy kết hợp URL và nội dung trang (NCKH_2)  
**Mã văn bản:** `PLAN-MAIN-ANNOTATION-MASTER-V3.0`  
**Phiên bản:** `3.0.0-CONSOLIDATED-PROPOSAL`  
**Ngày lập:** 12/11/2026  
**Đơn vị lập:** Thành viên C (Nguyễn Thắng — Data Pipeline & Thư ký Kiểm toán)  
**Người thẩm định phương pháp độc lập:** Thành viên B (Phùng Tấn Minh — QA Lead & Nhóm trưởng)  
**Thẩm quyền phê duyệt tối hậu:** Lead D (Nguyễn Anh Tuấn)  
**Trạng thái quản trị:** `DRAFT_V3.0_PENDING_B_APPRAISAL_AND_LEAD_D_FINAL_DECISION` (Bản kế hoạch vận hành hợp nhất — Tích hợp đầy đủ các đặc tả vận hành để Lead D xem xét và ban hành quyết định trong một lượt; tuyệt đối duy trì `training_blocked=true`, `official_test_used=false`, chưa trích xuất mẫu hay mở Pass 1)  

---

## BẢNG TỔNG HỢP BÀN GIAO KẾ HOẠCH HỢP NHẤT (CHUẨN ARS 5 CỘT)

| # | Yêu cầu của Lead D & QA Lead B | Mục tài liệu đáp ứng | Bằng chứng & Kiểm thử hiện có | Phần còn phải triển khai | Người chịu trách nhiệm |
|:---:|:---|:---|:---|:---|:---:|
| **1** | Khôi phục thiết kế Đợt 1 (60 vs 100 mẫu; Pilot vs Lô đầu Main; pre-locked seeds, tiêu chí chọn, dedupe 4 lớp, SimHash $\le 10$, Jaccard $\ge 0,85$; tiêu chí Đạt/Dừng). | **Mục 2** (Thiết kế chi tiết Đợt 1) | Mã nguồn `TemplateSimilarityEngine` tại `src/phishing/data/template_similarity.py` (dòng 96–97) đã có ngưỡng Hamming $\le 10$, Jaccard $\ge 0,85$. | Viết script tuyển chọn `scripts/data/sample_batch1.py` nạp seed đã khóa; chạy quét trùng lặp và xuất báo cáo. | Thành viên C (lập trình) & QA Lead B (kiểm định) |
| **2** | Chốt duy nhất một tên trường `blind_contract_version = "1.2.0"`; giữ `codebook_version = "1.1.0"`; cơ chế tương thích ngược v1.1.0 và fail-closed khi thiếu/sai version; cấm `random_subset` thật trong view/record của B. | **Mục 3** (Hợp đồng dữ liệu Blind View v1.2) | 150 bài test hồi quy hiện có (`tests/test_blind_view.py`) xác nhận schema v1.1.0 hoạt động an toàn và không rò rỉ nhãn. | Cập nhật validator và parser trong `blind_view.py` và `annotate_cli.py` phân nhánh theo `blind_contract_version`. | Thành viên C (triển khai) & QA Lead B (thẩm định) |
| **3** | Khóa 30% ngẫu nhiên trước Pass 1, bảng phân tầng hạn chế. Xử lý triệt để nguy cơ B suy ra ca khó: giải pháp trộn đệm ngẫu nhiên (*Blended Delivery Uniform Hash Shuffle*), nêu rõ giới hạn tồn tại. | **Mục 4** (Bảo vệ tính mù kép & Trộn đệm ngẫu nhiên) | Phép tính Cohen's Kappa trong `src/phishing/annotation/__init__.py` đã hỗ trợ lọc theo mảng boolean độc lập. | Lập trình module `blended_delivery.py` thực hiện Hash Shuffle và cập nhật `evaluate_kappa.py` thực hiện phép Join độc lập. | Thành viên C (thực hiện) & QA Lead B (kiểm tra mù) |
| **4** | Lô 1: Phân biệt điều đã xác minh với điều còn chờ; cách ly 2 shard đã biết `train-000`, `train-055` (chưa phải toàn bộ phạm vi Lô 1); lập phương án rủi ro tồn dư xin Lead D phê duyệt riêng. PhishVN là nguồn đề xuất. | **Mục 5** (Hiện trạng Lô 1 & Cách ly cấp Shard) | Sổ bộ `data/exclusion_registry.json` xác nhận Lô 2–10 có đủ hash; `recovery_status.json` ghi nhận tệp `raw20_mapping_check.json`. | Tổ chức phiên nghiệm thu độc lập mapping Lô 1; nếu chưa xong, trình Lead D ký duyệt văn bản chấp nhận rủi ro tồn dư. | Thành viên C (hồ sơ) & Lead D (phê duyệt) |
| **5** | Quy trình vận hành khép kín (View $\rightarrow$ MarianMT $\rightarrow$ SHA256SUMS $\rightarrow$ QA B $\rightarrow$ Duyệt D); MarianMT ja/ru sang tiếng Anh; phân định rạch ròi 150 test hồi quy hiện có với test mới cần viết. | **Mục 6** (Quy trình vận hành & Dịch ngoại tuyến) & **Mục 8** (Ranh giới kiểm thử) | 150 bài test hồi quy hiện có ($87 + 12 + 9 + 42 = 150$) đạt `150 passed`. Tệp dịch `clean_calibration_translations.json` đã kiểm chứng. | Viết mới bộ kiểm thử cho Hợp đồng v1.2, cổng registry động và phép Join độc lập sau khi Lead D duyệt kế hoạch. | Thành viên C (viết test) & QA Lead B (chạy kiểm chứng) |
| **6** | Đối chiếu ngân sách: 190,79h (PLAN-01) vs 192,32h (V3.0, chênh +1,53h theo chuẩn 405 mẫu của B). Định lượng tốc độ A (40h $\rightarrow$ 2,4m/mẫu vs thực đo 6,34m $\rightarrow$ 105,67h), độ trễ tuần tự. Tiến độ chính thức là TBD. | **Mục 7** (Bảng tính định lượng & Đối chiếu ngân sách) | Báo cáo thực nghiệm Pass 1 ($N=24$) đo đạc chính xác: A mean 6,34 phút/mẫu, B mean 4,17 phút/mẫu; Bảng 1 & 4 của PLAN-01. | Thu thập văn bản cam kết số giờ khả dụng thực tế của Annotator A và QA Lead B để tính tiến độ theo tuần. | Thành viên C (tính toán) & Toàn nhóm (cam kết giờ) |

---

## 1. NGUYÊN TẮC CỐT LÕI & CÁC CỔNG QUẢN TRỊ BẤT BIẾN

1. **Bản chất văn bản:** Đây là bản **KẾ HOẠCH VẬN HÀNH HỢP NHẤT (MASTER OPERATIONAL PLAN V3.0)** được thiết kế đầy đủ, chi tiết, đóng gói toàn bộ các chiều kích kỹ thuật để Lead D có thể ra quyết định phê duyệt phương án trong một lượt xem xét duy nhất.
2. **Khẳng định tính chất con số 1.000 trong PLAN-01:**
   - Con số 1.000 mẫu trong Báo cáo PLAN-01 là **Khung ngân sách công sức dự phóng có điều kiện** (Conditional Projected Effort Budget — 190,79 giờ người) được Lead D phê duyệt về mặt kế toán tài nguyên dự án.
   - Con số 1.000 mẫu **KHÔNG PHẢI LÀ LỆNH TRÍCH XUẤT THỰC TẾ**. Quy mô trích xuất thực tế sẽ do Lead D quyết định theo từng giai đoạn căn cứ vào kết quả thực nghiệm Đợt 1 và cam kết thời gian khả dụng của nhân sự.
3. **Phân định ranh giới trách nhiệm (RACI Matrix):**
   - **Thành viên C (Tác giả Pipeline Dữ liệu):** Trích xuất mẫu, kiểm tra trùng lặp 4 lớp, lọc template, gắn bản dịch ngoại tuyến MarianMT, niêm phong bảng phân tầng hạn chế, tạo gói Blind View an toàn, đối soát Kappa độc lập.
   - **QA Lead B (Kiểm định Phương pháp & Nghiệm thu Độc lập):** Thẩm định độc lập Blind View, schema, bộ test hồi quy; ký biên bản xác nhận QA độc lập; gán nhãn mù độc lập trên tập mẫu gán kép trung tính. Tuyệt đối không sửa thay tài liệu của C rồi tự ký QA.
   - **Lead D (Chỉ đạo & Phê duyệt Tối hậu):** Thẩm quyền duy nhất phê duyệt phạm vi trích xuất, giải quyết bất đồng Pass 2, phê duyệt mở phiên Pass 1 và nghiệm thu đóng mốc dữ liệu.
4. **Các cổng khóa an toàn đang có hiệu lực:**
   - `training_blocked = true` (Chặn 100% nạp dữ liệu vào pipeline huấn luyện).
   - `official_test_used = false` (Cô lập tuyệt đối 100% tập kiểm thử chính thức).
   - `main_annotation_status = "LOCKED"` (Chiến dịch gán nhãn chính tiếp tục khóa hoàn toàn; chưa chọn mẫu, chưa phát Blind View, chưa mở Pass 1).

---

## 2. THIẾT KẾ VẬN HÀNH CHI TIẾT ĐỢT 1 (BATCH 1 OPERATIONAL DESIGN)

### 2.1 Ma trận so sánh định lượng 4 kịch bản Đợt 1

| Tiêu chí kỹ thuật & Quản trị | Phương án A1: Lô đầu Main (60 mẫu) | Phương án A2: Lô đầu Main (100 mẫu) | Phương án B1: Pilot Tách riêng (60 mẫu) | Phương án B2: Pilot Tách riêng (100 mẫu) |
|:---|:---:|:---:|:---:|:---:|
| **Bản chất dữ liệu** | Lô 1 chính thức của Main Corpus. | Lô 1 chính thức của Main Corpus. | Lô Pilot thử nghiệm công cụ tách riêng. | Lô Pilot thử nghiệm công cụ tách riêng. |
| **Hệ quả Loại trừ (Exclusion Registry)** | Giữ lại làm Train/Val/Test chính thức. | Giữ lại làm Train/Val/Test chính thức. | **Bị loại trừ vĩnh viễn** (thành Lô 11). | **Bị loại trừ vĩnh viễn** (thành Lô 11). |
| **Đóng góp vào mục tiêu 1.000 mẫu** | Đóng góp 60 mẫu (còn lại 940 mẫu). | **Đóng góp 100 mẫu (còn lại 900 mẫu).** | Đóng góp 0 mẫu (phải gán đủ 1.000 mẫu mới). | Đóng góp 0 mẫu (phải gán đủ 1.000 mẫu mới). |
| **Tác động quỹ công số (PLAN-01)** | Nằm trong 190,79h của PLAN-01. | **Tối ưu ngân sách 190,79h của PLAN-01.** | Phát sinh thêm ~11,5h ngoài ngân sách. | Phát sinh thêm ~19,2h ngoài ngân sách. |
| **Thời gian A gán Pass 1 (thực đo 6,34m)** | $60 \times 6,34\text{m} = \mathbf{6,34\text{ giờ}}$ | $100 \times 6,34\text{m} = \mathbf{10,57\text{ giờ}}$ | $60 \times 6,34\text{m} = \mathbf{6,34\text{ giờ}}$ | $100 \times 6,34\text{m} = \mathbf{10,57\text{ giờ}}$ |
| **Mẫu ngẫu nhiên gán kép của B (30%)** | 18 mẫu ($18 \times 4,17\text{m} = 1,25\text{h}$) | **30 mẫu ($30 \times 4,17\text{m} = 2,09\text{h}$)** | 18 mẫu ($18 \times 4,17\text{m} = 1,25\text{h}$) | 30 mẫu ($30 \times 4,17\text{m} = 2,09\text{h}$) |
| **Ý nghĩa thống kê đo lường Kappa** | Cỡ mẫu $N=18$ có phương sai lớn. | **Cỡ mẫu $N=30$ đạt ngưỡng tiệm cận chuẩn.** | Cỡ mẫu $N=18$ có phương sai lớn. | Cỡ mẫu $N=30$ đạt ngưỡng tiệm cận chuẩn. |
| **Đánh giá tính khả thi trong 1 tuần** | Rất khả thi (A làm ~1h/ngày). | **Khả thi cao (A làm ~1,5h/ngày).** | Rất khả thi nhưng lãng phí công sức. | Khả thi nhưng lãng phí công sức. |

> [!TIP]
> **Khuyến nghị đề xuất của Thành viên C:** Thành viên C kính đề xuất Lead D lựa chọn **Phương án A2 (Lô đầu của Main Annotation — Quy mô 100 mẫu)**.  
> *Lý do:* Quy mô 100 mẫu cung cấp đúng $N_{\text{random}} = 30$ mẫu gán đôi cho B, đạt kích thước tối thiểu theo Định lý Giới hạn Trung tâm (CLT) để chỉ số Cohen's Kappa $\kappa_{A-B}$ có ý nghĩa thống kê tin cậy; đồng thời toàn bộ 100 mẫu này sau khi nghiệm thu sẽ đóng góp trực tiếp vào mục tiêu 1.000 mẫu, không làm lãng phí 19,2 giờ công của nhân sự vào việc tạo thêm một lô loại trừ mới.

### 2.2 Nguồn dữ liệu, Tiêu chí chọn mẫu & Bộ Hạt giống Khóa trước (Pre-locked Seeds)
1. **Nguồn dữ liệu hợp lệ duy nhất:** Trích xuất độc quyền từ nguồn `phreshphish` tại revision `eabec4b7a66324b79cc8a0ad856d1731dc26fe1a` (56 shards trong `configs/source_manifest.json`). Cấm tuyệt đối trích xuất từ PhishVN hoặc các nguồn chưa duyệt.
2. **Tiêu chí lọc thời gian (Temporal Window):** Chỉ lấy các bản ghi có ngày thu thập nằm trong dải đã kiểm toán: từ `2024-10-01` đến `2025-09-08`.
3. **Bộ hạt giống ngẫu nhiên khóa trước (Pre-locked Pseudo-random Seeds):**
   - Hạt giống rút trích mẫu Đợt 1 từ Shard nguồn: `random_seed_batch1_select = 20261101`
   - Hạt giống phân tầng rút 30% ngẫu nhiên cho B: `random_seed_random30 = 20261102`
   - Hạt giống xáo trộn thứ tự hiển thị Blind View: `random_seed_hash_shuffle = 20261103`
4. **Cơ cấu phân tầng (Sampling Strata):**
   - Tỷ lệ nhãn nguồn cân bằng: 50% Phishing (50 mẫu) và 50% Benign (50 mẫu).
   - Phân bổ đại diện trên 14 tổ chức mục tiêu trong từ điển chuẩn hóa `configs/dictionary_v1.json` (Google, Microsoft, Facebook, PayPal, Apple, Amazon, Netflix, Telegram, Vietcombank, Techcombank, BIDV, VietinBank, MBBank, ZaloPay) kết hợp nhóm tổ chức khác.

### 2.3 Quy trình kiểm tra trùng lặp 4 lớp & Lọc tương đồng Template
Trước khi đưa vào danh sách ứng viên chính thức, mọi mẫu trích xuất phải vượt qua 2 cổng kiểm soát kỹ thuật nghiêm ngặt:

1. **Cổng kiểm tra trùng lặp 4 lớp (4-Layer Cryptographic Deduplication Gate):**
   - *Lớp 1 (URL thô):* $\text{SHA-256}(\text{url}) \notin \text{ExclusionRegistry}$.
   - *Lớp 2 (URL chuẩn hóa):* $\text{SHA-256}(\text{normalize\_url}(\text{url})) \notin \text{ExclusionRegistry}$.
   - *Lớp 3 (HTML sạch):* $\text{SHA-256}(\text{clean\_html}(\text{raw\_html})) \notin \text{ExclusionRegistry}$.
   - *Lớp 4 (Domain Group):* $\text{SHA-256}(\text{eTLD+1}) \notin \text{ExclusionRegistry}$.
   - Đối soát đối chiếu với toàn bộ **246 mục ghi nhận loại trừ** trong `data/exclusion_registry.json`. Bất kỳ sự trùng khớp nào ở 1 trong 4 lớp đều bị loại bỏ ngay lập tức.
2. **Cổng kiểm tra tương đồng Template (`TemplateSimilarityEngine`):**
   - Áp dụng thuật toán SimHash 64-bit và DOM Tag Jaccard Similarity theo đúng mã nguồn `src/phishing/data/template_similarity.py` (dòng 96–97 và 164):
     * *Ngưỡng Hamming:* Loại bỏ ứng viên nếu khoảng cách Hamming $\le \mathbf{10\text{ bit}}$ (`max_allowed_simhash_distance = 10`) đối với bất kỳ template nào đã có trong corpus.
     * *Ngưỡng DOM Jaccard:* Loại bỏ ứng viên nếu độ tương đồng thẻ DOM Jaccard $\ge \mathbf{0,85}$ (`max_allowed_dom_jaccard = 0.85`) kết hợp khoảng cách SimHash $\le 12\text{ bit}$.
3. **Kiểm tra trùng lặp giữa các đợt (Cross-Batch Collision Check):**
   - Đảm bảo 100% mẫu của Đợt 1 không trùng lặp URL, HTML hoặc Domain Group với bất kỳ mẫu nào của các đợt hiệu chuẩn trước đó (Đợt B, Đợt C).

### 2.4 Tiêu chí ĐẠT (Acceptance Criteria) & Tiêu chí DỪNG (Stop Gate) của Đợt 1
Kết thúc Đợt 1, nhóm nghiên cứu căn cứ vào các chỉ số định lượng sau để quyết định:

- **TIÊU CHÍ ĐẠT (PASS CRITERIA — ĐỦ ĐIỀU KIỆN MỞ RỘNG TOÀN CHIẾN DỊCH):**
  1. *Tiến độ & Dữ liệu:* Hoàn thành 100% gán nhãn Pass 1 (A gán 100 mẫu, B gán 30 mẫu ngẫu nhiên + ca khó phát sinh).
  2. *Hạ tầng CLI:* Không phát sinh lỗi kỹ thuật crash phần mềm hay lỗi schema validation trong suốt quá trình ghi nhận.
  3. *Chất lượng đồng thuận:* Chỉ số Cohen's Kappa trước phân xử tính trên 30 mẫu ngẫu nhiên đạt $\kappa_{\text{random}} \ge \mathbf{0,75}$ (hoặc ngưỡng do Lead D chính thức chốt).
  4. *Tỷ lệ nghi ngờ an toàn:* Tỷ lệ mẫu gắn cờ `insufficient_evidence` $\le \mathbf{5,0\%}$ (không quá 5 mẫu trên 100 mẫu).
  5. *Nghiệm thu phân xử:* Hoàn tất phân xử Pass 2 cho các ca bất đồng và ký biên bản QA độc lập.

- **TIÊU CHÍ DỪNG / CẢNH BÁO KHẨN CẤP (STOP GATES — DỪNG ĐỂ RÀ SOÁT NGUYÊN NHÂN GỐC):**
  1. *Cổng cảnh báo chất lượng snapshot:* Nếu tỷ lệ `insufficient_evidence` $> \mathbf{5,0\%}$, hệ thống kích hoạt **Quy trình dừng an toàn để rà soát chất lượng snapshot HTML và tiêu chí crawl nguồn** (loại trừ lỗi mạng, bot-block, trang trắng). **TUYỆT ĐỐI NGHIÊM CẤM TẠO ÁP LỰC ÉP NGƯỜI GÁN PHẢI CHUYỂN ĐỔI NHÃN SANG PHISHING HOẶC BENIGN**.
  2. *Cổng cảnh báo đồng thuận:* Nếu $\kappa_{\text{random}} < \mathbf{0,60}$, tạm dừng phát hành Đợt 2 để tổ chức phiên họp kỹ thuật rà soát lại độ rõ ràng của Codebook v1.1 và tiêu chí nhận diện của annotator.
  3. *Cổng cảnh báo an toàn:* Nếu phát hiện bất kỳ sự cố rò rỉ nào về nhãn nguồn, locator hay cờ phân tầng đối với Annotator B, hủy bỏ đợt gán nhãn và cô lập dữ liệu.

---

## 3. HỢP ĐỒNG DỮ LIỆU GÁN NHÃN MÙ (BLIND CONTRACT V1.2) & CƠ CHẾ PHÂN NHÁNH PHIÊN BẢN

Tiếp thu triệt để ý kiến chỉ đạo của Lead D và nhận xét thẩm định của QA Lead B về việc thống nhất một chuẩn hợp đồng kỹ thuật duy nhất:

### 3.1 Chốt một tên trường duy nhất: `blind_contract_version`
- **Tên trường duy nhất được áp dụng:** **`blind_contract_version`** (xóa bỏ hoàn toàn cách viết tùy chọn "hoặc view_schema_version").
- **Phiên bản Codebook giữ nguyên bất biến:** **`codebook_version = "1.1.0"`** (khớp 100% với `docs/CODEBOOK_V1_1.md`). Thành viên C tuyệt đối không tự nâng Codebook lên 1.2.0.
- **Giá trị của Hợp đồng dữ liệu Main:** **`"1.2.0"`**.

### 3.2 Đặc tả Hợp đồng Dữ liệu Main Annotation v1.2 (`blind_contract_version = "1.2.0"`)
1. **Schema tệp Blind View (`main_annotation_blind_view.json`):**
   - **HOÀN TOÀN KHÔNG CHỨA TRƯỜNG `random_subset`** (cấm cả giá trị thật lẫn giá trị boolean giả).
   - Danh mục 12 trường allowlist được phép xuất hiện trong mỗi `BlindSample`:
     `sample_id`, `url`, `page_text`, `structure_summary`, `codebook_version` (`"1.1.0"`), `blind_contract_version` (`"1.2.0"`), `translation_provided`, `translated_text`, `translation_source_language`, `translation_tool`, `translation_tool_version`, `translation_sha256`.
2. **Schema Bản ghi Gán nhãn Pass 1 (`AnnotationRecord`):**
   - Bản ghi xuất ra từ CLI (`intake_pass1_A.jsonl`, `intake_pass1_B.jsonl`) **HOÀN TOÀN KHÔNG CHỨA TRƯỜNG `random_subset`**.
   - Bản ghi chỉ lưu trữ các phán đoán khoa học thực tế: `sample_id`, `rater_id`, `pass_phase`, `class_label`, `identity_role`, `primary_org`, `evidence_quote`, `evidence_note`, `difficult_case`, `seconds_spent`, `codebook_version` (`"1.1.0"`), `blind_contract_version` (`"1.2.0"`).
   - Bảo toàn tính trung thực học thuật 100%: Tuyệt đối không lưu trữ cờ `random_subset: true` giả vào kết quả của các ca khó bổ sung.

### 3.3 Cơ chế phân nhánh tương thích ngược & Từ chối an toàn (Fail-Closed Rejection)
Bộ nạp và kiểm tra tính hợp lệ (`Validator` và `annotate_cli.py`) được thiết kế phân nhánh xử lý tường minh:

```python
# Giả mã logic phân nhánh và từ chối an toàn
def validate_and_load_blind_sample(sample_dict: dict) -> BlindSample:
    contract_ver = sample_dict.get("blind_contract_version", "1.1.0")
    
    if contract_ver == "1.1.0":
        # CHẾ ĐỘ CALIBRATION CŨ: Tương thích ngược với dữ liệu Runway A lịch sử
        if "random_subset" not in sample_dict:
            raise ValueError("LỖI SCHEMA V1.1: Gói Calibration bắt buộc phải có random_subset: bool")
        return load_legacy_calibration_sample(sample_dict)
        
    elif contract_ver == "1.2.0":
        # CHẾ ĐỘ MAIN ANNOTATION: Hợp đồng v1.2 bảo vệ tính mù tuyệt đối
        if "random_subset" in sample_dict:
            raise ValueError("LỖI BẢO MẬT HỢP ĐỒNG V1.2: Cấm đưa trường random_subset vào Blind View của Main!")
        if sample_dict.get("codebook_version") != "1.1.0":
            raise ValueError("LỖI CODEBOOK: Main Annotation bắt buộc dùng codebook_version='1.1.0' đã khóa!")
        return load_main_v12_sample(sample_dict)
        
    else:
        # TỪ CHỐI AN TOÀN KHI SAI HOẶC THIẾU PHIÊN BẢN HỢP ĐỒNG
        raise ValueError(f"TỪ CHỐI AN TOÀN (FAIL-CLOSED): Phiên bản hợp đồng '{contract_ver}' không hợp lệ!")
```

---

## 4. CƠ CHẾ BẢO VỆ TÍNH MÙ KÉP & GIẢI PHÁP PHÂN PHỐI TRỘN ĐỆM NGẪU NHIÊN (BLENDED DELIVERY)

### 4.1 Khóa tập ngẫu nhiên 30% & Lưu trữ Hồ sơ Phân tầng Hạn chế
1. **Khóa trước 30% mẫu ngẫu nhiên ($S_{\text{random}}$):**
   - Trước khi bất kỳ tệp Blind View nào được xuất xưởng cho Annotator A, Thành viên C thực hiện rút ngẫu nhiên độc lập 30% mẫu:
     $$N_{\text{random}} = \text{round}(0,30 \times N) \quad (N_{\text{random}} = 300\text{ mẫu cho toàn chiến dịch; } 30\text{ mẫu cho Đợt 1})$$
   - Sử dụng `random_seed_random30 = 20261102` đã công bố công khai.
2. **Niêm phong Hồ sơ Phân tầng Hạn chế (Restricted Sampling Manifest):**
   - Danh sách phân định mẫu được lưu trữ duy nhất trong khu vực hạn chế ngoài Git:
     `data/restricted/main_annotation_sampling_manifest.json`
   - Cấu trúc tệp ghi nhận:
     ```json
     {
       "strata_mapping": {
         "MAIN-0001": {"stratum": "random_30", "is_random_subset": true},
         "MAIN-0002": {"stratum": "supplemental_hard", "is_random_subset": false}
       },
       "commitment_sha256": "..."
     }
     ```
   - Mã băm SHA-256 của tệp này được công bố trong release manifest của đợt để khóa cứng phân tầng trước khi A bắt đầu gán nhãn.

### 4.2 Giải quyết triệt để nguy cơ B suy ra "Ca khó" bằng Giải pháp Phân phối Trộn đệm Ngẫu nhiên (*Blended Delivery with Uniform Hash Shuffle*)
- **Phân tích rủi ro:** Nếu Annotator B nhận 30% mẫu ngẫu nhiên ở Lượt 1, sau đó đợi A gán xong gắn cờ `difficult_case=true`, rồi C gửi tiếp các mẫu khó này cho B ở một đợt riêng Lượt 2, thì Annotator B sẽ **ngay lập tức suy diễn được rằng đợt gửi thứ hai toàn là ca khó**. Điều này tạo ra thiên kiến tâm lý làm hỏng tính độc lập khoa học.
- **Giải pháp Vận hành Phân phối Trộn đệm (*Blended Delivery Strategy*):**

```
[Tiến độ Annotator A] ───────────────► Gán Batch 1 (100 mẫu) ───────────────► Gán Batch 2 (200 mẫu)
                                              │                                       │
                                     (Phát sinh ca khó B1)                   (Phát sinh ca khó B2)
                                              │                                       │
                                              ▼                                       ▼
[Bể Ca khó Tích lũy] ────────────────► [Pool Ca khó Đợt 1] ──────────────────► [Pool Ca khó Đợt 2]
                                              │                                       │
                                              ├───────────────────────┐               │
                                              ▼                       ▼               ▼
[Gói phát hành cho B]                (Đợt 1 cho B: 30 mẫu)   (Đợt 2 cho B: 60 mẫu R_30% + Ca khó Đợt 1)
                                              │                               │
                                              ▼                               ▼
                                    [Uniform Hash Shuffle]          [Uniform Hash Shuffle]
                                              │                               │
                                              ▼                               ▼
                                    (B nhận 100% mẫu ngẫu nhiên)    (B nhận gói hỗn hợp xáo trộn)
                                    (B không biết có ca khó hay không, hoàn toàn mù phân tầng)
```

1. **Nguyên tắc phân phối theo đợt gộp (Sprint Chunks):**
   - Không phát hành các ca khó thành một tệp riêng lẻ.
   - Khi phát gói gán kép cho B ở Đợt $k+1$, tập dữ liệu giao cho B sẽ được tạo thành từ **Phép hợp toán học** giữa:
     $$S_{B}^{(k+1)} = S_{\text{random30}}^{(k+1)} \cup S_{\text{hard\_accumulated}}^{(k)}$$
2. **Thuật toán Xáo trộn Băm Đồng nhất (Uniform Hash Shuffle):**
   - Trước khi ghi ra tệp Blind View phát cho B, toàn bộ các mẫu trong tập hợp trên được xáo trộn ngẫu nhiên dựa trên mã băm mật mã học kết hợp hạt giống:
     $$\text{sort\_key}(s) = \text{SHA-256}(\text{sample\_id} \parallel \text{seed\_shuffle})$$
   - Nhờ đó, các ca khó bổ sung được phân tán ngẫu nhiên hoàn toàn xen kẽ giữa các mẫu ngẫu nhiên thông thường. Tệp giao cho B có định dạng đồng nhất, mã ID trung tính liên tục, không có bất kỳ cờ hay thứ tự nào để B có thể suy đoán nguồn gốc mẫu.
3. **Thừa nhận Giới hạn Tính mù còn tồn tại (Residual Blinding Limitation):**
   - Ở đợt phát hành cuối cùng của chiến dịch, nếu số lượng ca khó còn dư phát sinh mà không còn đủ mẫu ngẫu nhiên để trộn đệm với tỷ lệ an toàn, một mức độ suy đoán nhỏ có thể xuất hiện. Kế hoạch ghi nhận rõ giới hạn này và quy định Thành viên C tuyệt đối không thêm bất kỳ siêu dữ liệu hay ghi chú nào vào gói dữ liệu giao cho B.

### 4.3 Phép Join độc lập tính Cohen's Kappa chính thức trước phân xử
Sau khi A và B nộp và khóa mã băm Pass 1, module `evaluate_kappa.py` thực hiện:
$$\text{EvaluationSet} = \text{Record}_A[\text{sample\_id}] \bowtie \text{Record}_B[\text{sample\_id}] \bowtie \text{RestrictedStrataMap}[\text{sample\_id}]$$
- Chỉ số Cohen's Kappa chính thức trước phân xử ($\kappa_{\text{primary}}$) **CHỈ ĐƯỢC TÍNH TRÊN CÁC MẪU CÓ $\text{is\_random\_subset} == \text{True}$**.
- Các ca khó bổ sung được bóc tách để phân tích thăm dò riêng biệt (Subgroup Agreement), không đưa vào mẫu số Kappa đại diện toàn corpus.

---

## 5. HIỆN TRẠNG LÔ 1, DANH MỤC SHARD CÁCH LY & QUẢN TRỊ RỦI RO TỒN DƯ

Tiếp thu triệt để ý kiến chỉ đạo của Lead D và báo cáo thẩm định của QA Lead B:

### 5.1 Phân định rõ ràng: Điều đã xác minh vs Điều còn chờ kiểm toán

| Danh mục Lô loại trừ | Số mẫu | Trạng thái hiện tại trên `exclusion_registry.json` | Hiện trạng mã băm kiểm toán | Đánh giá an toàn kỹ thuật |
|:---|:---:|:---:|:---|:---|
| **Lô 1 (`EXCL-PILOT-01`)** | 20 | `unresolved_source_mapping` (Rows API chưa khóa revision) | **CHƯA CÓ** URL/HTML hash trên registry. Hồ sơ `raw20_mapping_check.json` (khớp 20 mẫu) trong `recovery_status.json` vẫn đang ở trạng thái `pending_independent_review`. | **ĐIỀU CÒN CHỜ:** Chưa thể đối soát hash tự động. Cần hoàn tất nghiệm thu độc lập hoặc khoanh vùng cách ly. |
| **Lô 2 (`EXCL-REAL-PILOT-32`)** | 32 | `unresolved_source_mapping` (chưa có locator shard) | **ĐÃ CÓ ĐỦ 32/32 bộ mã băm** `url_sha256`, `html_sha256`, `group_sha256` trên registry. | **ĐÃ XÁC MINH MÃ BĂM:** Đang hoạt động trực tiếp trong `is_excluded()` chặn 100% trùng URL/HTML/Domain. |
| **Lô 3 & Lô 4 (`REAL-PILOT-32-V2`)** | 32 | Lô 4: `resolved` (Rows API pinned) | **ĐÃ CÓ ĐỦ 32/32 bộ mã băm** URL/HTML/Group và định vị shard (`train-000`, `train-055`). | **ĐÃ XÁC MINH TOÀN DIỆN:** Chặn 100% bằng cả hash và locator vật lý. |
| **Lô 5 đến Lô 10 (Hiệu chuẩn & Sự cố)** | 162 | `resolved` / `mapped_to_shards` / `resolved_in_restricted_dossier` | **ĐÃ CÓ ĐỦ 100% mã băm** URL/HTML/Group (công khai hoặc niêm phong ngoài Git). | **ĐÃ XÁC MINH MẬT MÃ HỌC:** Niêm phong bất biến với cam kết hash đã kiểm chứng. |

### 5.2 Danh mục Shard Cách ly đã biết & Định vị phần nguồn còn lại
1. **Hai shard đã biết cần cách ly tuyệt đối:**
   - Căn cứ hồ sơ thực nghiệm, hai tệp Parquet sau đã được xác định chắc chắn từng được dùng cho các đợt V2 Rebuild và Hiệu chuẩn:
     * `data/train-000.parquet`
     * `data/train-055.parquet`
   - Hai tệp này được đưa vào **Danh mục Cách ly Cấm Khai thác (Quarantined Shards Blacklist)** đối với toàn bộ chiến dịch Main Annotation.
2. **Định vị chính xác phần nguồn còn lại:**
   - Thành viên C **xóa bỏ hoàn toàn cụm từ "Shard Nguồn Sạch Đã Được Xác Minh"**.
   - Do Lô 1 thu thập qua HuggingFace Rows API chưa khóa revision, nhóm nghiên cứu **chưa thể chứng minh bằng toán học rằng Rows API của Lô 1 chưa từng chạm tới các shard khác**. Phần nguồn còn lại được định vị chính xác là: **"Các Shard Nguồn Chưa Xác Minh Được Phạm Vi Rows API của Lô 1 (Unverified Shards Pending Pilot 1 Scope)"**.
3. **Quy trình giải quyết & Điểm quyết định riêng của Lead D (Lead D Residual Risk Decision Gate):**
   - *Ưu tiên số 1:* Thành viên C phối hợp cùng QA Lead B tổ chức rà soát độc lập hồ sơ `raw20_mapping_check.json` để nghiệm thu chính thức 20 mã băm URL/HTML vào `exclusion_registry.json`.
   - *Điểm quyết định của Lead D:* Trường hợp chưa hoàn tất nghiệm thu Lô 1 trước ngày mở trích xuất Đợt 1, Thành viên C lập báo cáo kiểm kê rủi ro tồn dư để **Lead D ban hành Quyết định phê duyệt phạm vi nguồn và chấp nhận mức rủi ro tồn dư riêng bằng văn bản**. Tuyệt đối không tự ý khẳng định đã loại trừ 100%.
4. **Quy chế nguồn PhishVN:** PhishVN tiếp tục là **Nguồn đề xuất thứ cấp — CHƯA ĐƯỢC PHÉP TRÍCH XUẤT**.

---

## 6. QUY TRÌNH VẬN HÀNH KHÉP KÍN (END-TO-END PIPELINE) & CHUẨN HÓA DỊCH MARIANMT

### 6.1 Quy trình vận hành 6 bước chuẩn kiểm toán

```
[BƯỚC 1: TRÍCH XUẤT & LỌC TRÙNG]
  │ • Nạp shard sạch (ngoài train-000, train-055) với seed đã khóa.
  │ • Lọc trùng 4 lớp đối soát 246 mẫu registry + Lọc SimHash <= 10, Jaccard >= 0.85.
  ▼
[BƯỚC 2: GẮN DỊCH NGOẠI TUYẾN MARIANMT TIẾNG ANH (R-A09)]
  │ • Quét phát hiện ngôn ngữ: ja, ru -> Dịch sang TIẾNG ANH (Helsinki-NLP opus-mt).
  │ • Bảo toàn 100% page_text gốc; lưu translated_text + 5 trường metadata + translation_sha256.
  ▼
[BƯỚC 3: KHÓA BẢNG PHÂN TẦNG & NIÊM PHONG HỒ SƠ HẠN CHẾ]
  │ • Khóa 30% ngẫu nhiên cho B vào data/restricted/main_annotation_sampling_manifest.json.
  │ • Xáo trộn Blended Delivery Uniform Hash Shuffle; tạo SHA256SUMS.txt và release manifest.
  ▼
[BƯỚC 4: THẨM ĐỊNH QA ĐỘC LẬP CỦA B & PHÊ DUYỆT MỞ PHIÊN CỦA LEAD D]
  │ • QA Lead B kiểm tra schema Hợp đồng v1.2, zero-leak check; ký biên bản QA độc lập.
  │ • Lead D kiểm tra hồ sơ, ký quyết định phê duyệt mở phiên Pass 1.
  ▼
[BƯỚC 5: GÁN NHÃN PASS 1 ĐỘC LẬP (A GÁN 100%, B GÁN GÓI BLENDED 405 MẪU)]
  │ • A và B gán nhãn độc lập qua CLI; CLI ghi AnnotationRecord chuẩn không có random_subset.
  │ • Khóa mã băm SHA-256 các tệp nhãn Pass 1 ngay khi hoàn thành.
  ▼
[BƯỚC 6: PHÉP JOIN ĐỘC LẬP TÍNH KAPPA & PHÂN XỬ PASS 2]
    • C chạy evaluate_kappa Inner Join với Strata Manifest tính kappa_primary trên N_random.
    • Lập hồ sơ bất đồng; Lead D chủ trì phân xử Pass 2; B ký QA sign-off đóng mốc.
```

---

## 7. ĐỊNH LƯỢNG TIẾN ĐỘ & ĐỐI CHIẾU NGÂN SÁCH CÔNG SỐ

### 7.1 Phép tính định lượng chứng minh tính bất khả thi của tiến độ 1 tuần cho 1.000 mẫu
- **Định mức làm việc 1 tuần (Sprint 40h):** $T_{\text{avail}} = 40\text{ giờ} = 2.400\text{ phút}$.
- **Tốc độ gán nhãn đòi hỏi để 1 người hoàn thành 1.000 mẫu trong 40h:**
  $$t_{\text{required}} \le \frac{2.400\text{ phút}}{1.000\text{ mẫu}} = \mathbf{2,40\text{ phút/mẫu}} = \mathbf{144\text{ giây/mẫu}}$$
- **Tốc độ trung bình thực đo của Annotator A (Calibration Runway A, $N=24$):**
  $$t_{\text{actual}} = \mathbf{380,16\text{ giây/mẫu}} = \mathbf{6,34\text{ phút/mẫu}}$$
- **Thời gian làm việc thuần túy riêng Annotator A cần cho 1.000 mẫu:**
  $$T_A = 1.000\text{ mẫu} \times 6,34\text{ phút/mẫu} = 6.340\text{ phút} = \mathbf{105,67\text{ giờ}}$$
- **Thời gian cần thiết ở mức full-time 40h/tuần:**
  $$\frac{105,67\text{ giờ}}{40\text{ giờ/tuần}} = \mathbf{2,64\text{ tuần}} \quad (\approx 19\text{ ngày làm việc liên tục không nghỉ})$$
- **Phân tích độ trễ chuỗi phụ thuộc tuần tự (Pipeline Sequential Latency):**
  * Quy trình kiểm toán đòi hỏi các khâu diễn ra tuần tự: C chuẩn bị view $\rightarrow$ A/B gán Pass 1 $\rightarrow$ C đối soát bất đồng $\rightarrow$ D phân xử Pass 2 $\rightarrow$ B thẩm định QA $\rightarrow$ D duyệt đóng mốc.
  * B không thể ký QA khi D chưa phân xử; D không thể phân xử khi A/B chưa nộp nhãn Pass 1.
  * Do đó, ngay cả khi toàn bộ 4 thành viên đều cam kết làm việc 40 giờ/tuần, chuỗi phụ thuộc tuần tự khiến **toàn bộ chiến dịch 1.000 mẫu về mặt toán học và quy trình không thể hoàn thành trong 1 tuần (7 ngày dương lịch)**.
- **Đánh giá tiến độ có điều kiện:** Tiến độ 1 tuần chỉ khả thi đối với **Đợt 1 (Quy mô 60 hoặc 100 mẫu)**. Khả năng hoàn thành chiến dịch 1.000 mẫu chỉ được cân nhắc điều chỉnh nếu kết quả thực tế Đợt 1 chứng minh tốc độ tăng lên đáng kể, chất lượng $\kappa \ge 0,75$ giữ vững và nhân sự cam kết đủ giờ. Tiến độ chính thức toàn chiến dịch tiếp tục là **CHƯA XÁC ĐỊNH (TBD)**.

### 7.2 Bảng đối chiếu ngân sách: PLAN-01 (190,79h) vs Dự phóng V3.0 (192,32h)

| Thành viên / Vai trò | Phân bổ PLAN-01 được duyệt (Giờ) | Tỷ lệ PLAN-01 (%) | Kịch bản Dự phóng V3.0 đề xuất (Giờ) | Tỷ lệ V3.0 (%) | Độ lệch công số (Giờ) | Giải trình nguyên nhân dịch chuyển cơ cấu kỹ thuật |
|:---|:---:|:---:|:---:|:---:|:---:|:---|
| **Annotator A** | 114,08 | 59,80% | **105,67** | 54,95% | **-8,41** | Chuyển từ định mức thận trọng (410,70s/mẫu = 6,85m) sang thời gian trung bình thực đo Pass 1 ($380,16\text{s/mẫu} = 6,34\text{m}$). |
| **QA Lead B** | 36,21 | 18,98% | **43,15** | 22,44% | **+6,94** | Gán kép 405 mẫu chuẩn PLAN-01 ($405 \times 4,17\text{m} = 28,15\text{h}$) cộng đệm kiểm định QA tuyển chọn, schema và nghiệm thu qua 5 đợt ($15,00\text{h}$). |
| **Thành viên C** | 25,00 | 13,10% | **28,00** | 14,56% | **+3,00** | Quản trị hạ tầng Hợp đồng v1.2, phân đợt batch chống rò rỉ, quản lý tệp phân tầng hạn chế và đối soát reconciliation độc lập. |
| **Lead D** | 15,50 | 8,12% | **15,50** | 8,06% | **0,00** | Phân xử bất đồng Pass 2 cho các ca bất đồng phát sinh cộng thời gian thẩm duyệt mốc tối hậu (khớp chuẩn ngân sách PLAN-01). |
| **TỔNG CỘNG** | **190,79** | **100,00%** | **192,32** | **100,00%** | **+1,53** | **Kịch bản V3.0 đồng bộ 405 mẫu có tổng công số 192,32 giờ (chênh +1,53h = 0,80% so với khung PLAN-01), kính trình Lead D xem xét phê duyệt riêng.** |

---

## 8. BẰNG CHỨNG TRUY XUẤT GIT VÀ PHÂN ĐỊNH RANH GIỚI BỘ KIỂM THỬ

### 8.1 Lịch sử Commit và Bằng chứng Truy xuất Git trên GitHub
- **Kho lưu trữ:** `https://github.com/Anhtuann1404/NCKH_2.git`
- **Nhánh phát triển:** `feat/c-calibration-v1-1-4-adjudication`
- **Các commit kiểm toán đã đồng bộ thành công trên GitHub:**
  * Commit V2.1: [`13e24a0cbf042c486825a67c74ef9332e1935d05`](https://github.com/Anhtuann1404/NCKH_2/commit/13e24a0cbf042c486825a67c74ef9332e1935d05)
  * Commit V2.2: [`4ac51d6eaf7ad67c717075d913c54dee0aa85016`](https://github.com/Anhtuann1404/NCKH_2/commit/4ac51d6eaf7ad67c717075d913c54dee0aa85016)
  * Commit V2.3: [`583c52e63fa91ccd2c074113340820e1c663e010`](https://github.com/Anhtuann1404/NCKH_2/commit/583c52e63fa91ccd2c074113340820e1c663e010)
  * Commit V2.4: [`e90d6e14ff430f3c96818cf723331088daed520f`](https://github.com/Anhtuann1404/NCKH_2/commit/e90d6e14ff430f3c96818cf723331088daed520f)
  * Commit V3.0 (Bản Master hiện hành): Được tạo và push trực tiếp cùng văn bản này.

### 8.2 Phân định rạch ròi giữa Test Hồi quy Hiện có và Test Đề xuất Mới
1. **Bộ test hồi quy mã nguồn hiện có (Existing Codebase Regression Tests — 150/150 PASSED):**
   - **Lệnh thực thi:**
     ```bash
     python -m pytest tests/test_blind_view.py tests/test_clean_calibration_blind_view.py tests/test_difficulty_strata.py tests/test_exclusion_registry.py -v
     ```
   - **Cấu tạo chi tiết của 150 bài test hiện có (đã xác thực AST):**
     * `tests/test_blind_view.py`: **87 hàm test** (an toàn Blind View v1.1, allowlist trường, strip thẻ nguy hiểm, loại trừ rò rỉ nhãn và tính toàn vẹn bản dịch).
     * `tests/test_clean_calibration_blind_view.py`: **12 hàm test** (tính hợp lệ của gói view sạch Đợt C).
     * `tests/test_difficulty_strata.py`: **9 hàm test** (tính toán độc lập 6 cờ chỉ báo mô tả bề mặt).
     * `tests/test_exclusion_registry.py`: **42 hàm test** (logic loại trừ của 10 lô hiện hành và cam kết Lô 10 ngoài Git).
     * **Tổng cộng: $87 + 12 + 9 + 42 = 150\text{ bài test hiện có}$** (kết quả: 150 passed, 0 failed, 0 skipped, 0 deselected).
2. **Bộ test đề xuất cho các cơ chế mới (Future Proposed Tests — Chưa lập trình & Chưa chạy):**
   - *Test Hợp đồng dữ liệu v1.2:* Kiểm tra tệp `main_annotation_blind_view.json` không chứa key `random_subset`; kiểm tra validator phân nhánh theo `blind_contract_version = "1.2.0"` mà vẫn giữ `codebook_version = "1.1.0"`.
   - *Test Join độc lập:* Kiểm tra `evaluate_kappa` nạp tệp phân tầng hạn chế của C và tính đúng $\kappa_{\text{primary}}$ trên $N_{\text{random}} = 300$ mẫu.
   - *Test cách ly Shard:* Kiểm tra hệ thống dừng an toàn khi phát hiện script cố gắng nạp ứng viên từ `train-000.parquet` và `train-055.parquet`.
   - Toàn bộ danh mục test mới này sẽ được lập trình và tích hợp vào test suite sau khi Lead D chính thức phê duyệt bản Kế hoạch Hợp nhất V3.0.

---

## 9. DANH MỤC 6 QUYẾT ĐỊNH KÍNH TRÌNH LEAD D XEM XÉT TRONG MỘT LƯỢT

Thành viên C kính trình QA Lead B thẩm định độc lập và Lead D xem xét ban hành quyết định đối với 6 nội dung trọng tâm sau:

1. **Phê duyệt Phương án & Quy mô Đợt 1:** Lựa chọn Phương án A2 (Lô đầu Main — 100 mẫu) hay phương án khác; chốt tiêu chí Đạt/Dừng của Đợt 1.
2. **Phê duyệt Hợp đồng Dữ liệu Blind View v1.2:** Chấp thuận việc chốt duy nhất tên trường `blind_contract_version = "1.2.0"`, giữ nguyên `codebook_version = "1.1.0"`, và cấm trường `random_subset` trong Blind View của Main.
3. **Phê duyệt Cơ chế Trộn đệm Ngẫu nhiên (Blended Delivery):** Thông qua phương án phân phối trộn đệm với Uniform Hash Shuffle để bảo vệ tính mù kép cho Annotator B.
4. **Phê duyệt Quyết định Phạm vi Nguồn và Chấp nhận Rủi ro Tồn dư Lô 1:** Ban hành văn bản phê duyệt danh mục cách ly 2 shard đã biết (`train-000`, `train-055`) và quyết định phương án chấp nhận rủi ro tồn dư của Lô 1 trước khi rút mẫu.
5. **Phê duyệt Ngân sách Hiệu chỉnh V3.0 (192,32 giờ):** Chấp thuận độ lệch chênh +1,53 giờ so với khung PLAN-01 (190,79h) do đồng bộ theo 405 mẫu gán kép của B.
6. **Xác nhận Tiến độ Toàn chiến dịch là TBD:** Ghi nhận tiến độ chính thức theo tuần của toàn chiến dịch là TBD chờ kết quả thực nghiệm Đợt 1 và cam kết giờ của A và B.

---

**XÁC NHẬN CỦA THÀNH VIÊN C (DATA PIPELINE & THƯ KÝ KIỂM TOÁN)**  
*(Bản Kế hoạch Vận hành Hợp nhất V3.0 — Duy trì nghiêm ngặt: training_blocked=true, official_test_used=false, Main Annotation KHÓA 100%)*  

**Nguyễn Thắng**
