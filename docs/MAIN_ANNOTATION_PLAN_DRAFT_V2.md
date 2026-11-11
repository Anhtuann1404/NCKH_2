# KẾ HOẠCH VẬN HÀNH HỢP NHẤT CHIẾN DỊCH GÁN NHÃN CHÍNH (MASTER OPERATIONAL ANNOTATION PLAN - PROPOSAL V3.1)

**Dự án:** Nghiên cứu phát hiện website phishing mạo danh tổ chức bằng học máy kết hợp URL và nội dung trang (NCKH_2)  
**Mã văn bản:** `PLAN-MAIN-ANNOTATION-MASTER-V3.1`  
**Phiên bản:** `3.1.0-CONSOLIDATED-PROPOSAL`  
**Ngày lập:** 12/11/2026  
**Đơn vị lập:** Thành viên C (Nguyễn Thắng — Data Pipeline & Thư ký Kiểm toán)  
**Người thẩm định phương pháp độc lập:** Thành viên B (Phùng Tấn Minh — QA Lead & Nhóm trưởng)  
**Thẩm quyền phê duyệt tối hậu:** Lead D (Nguyễn Anh Tuấn)  
**Trạng thái quản trị:** `DRAFT_V3.1_PENDING_B_APPRAISAL_AND_LEAD_D_FINAL_DECISION` (Bản kế hoạch vận hành hợp nhất hoàn thiện — Tiếp thu đầy đủ danh sách sửa gộp 7 điểm của QA Lead B để Lead D xem xét và ban hành quyết định trong một lượt; duy trì nghiêm ngặt `training_blocked=true`, `official_test_used=false`, chưa trích xuất mẫu hay mở Pass 1)  

---

## BẢNG TỔNG HỢP BÀN GIAO KẾ HOẠCH HỢP NHẤT (CHUẨN ARS 5 CỘT)

| # | Yêu cầu của Lead D & QA Lead B | Mục tài liệu đáp ứng | Bằng chứng & Kiểm thử hiện có | Phần còn phải triển khai | Người chịu trách nhiệm |
|:---:|:---|:---|:---|:---|:---:|
| **1** | Khôi phục thiết kế Đợt 1 (Phương án A2: Lô đầu Main 100 mẫu; pre-locked seeds, tiêu chí chọn, dedupe 4 lớp, SimHash $\le 10$, Jaccard $\ge 0,85$; đăng ký tuần tự `TemplateSimilarityEngine`; ngân sách toàn nhóm Đợt 1; tiêu chí Đạt/Dừng). | **Mục 2** (Thiết kế chi tiết Đợt 1) | Mã nguồn `TemplateSimilarityEngine` tại `src/phishing/data/template_similarity.py` (dòng 96–97) đã có sẵn ngưỡng Hamming $\le 10$, Jaccard $\ge 0,85$. | Viết script tuyển chọn `scripts/data/sample_batch1.py` đăng ký tuần tự từng mẫu vào engine; nạp seed đã khóa; quét trùng lặp và xuất manifest. | Thành viên C (lập trình) & QA Lead B (kiểm định) |
| **2** | Chốt duy nhất tên trường `blind_contract_version = "1.2.0"`; giữ `codebook_version = "1.1.0"`; cơ chế tương thích ngược v1.1.0 và fail-closed khi thiếu/sai version; cấm `random_subset` trong view/record của B; chuẩn hóa đúng đủ các trường của `AnnotationRecord`. | **Mục 3** (Hợp đồng dữ liệu Blind View v1.2) | Bộ test hồi quy v1.1.0 hiện có (`tests/test_blind_view.py`) xác nhận schema v1.1.0 an toàn và không rò rỉ nhãn. | Cập nhật validator và parser trong `blind_view.py` và `annotate_cli.py` phân nhánh theo `blind_contract_version`, fail-closed khi thiếu trường; cập nhật `AnnotationRecord`. | Thành viên C (triển khai) & QA Lead B (thẩm định) |
| **3** | Khóa 30% ngẫu nhiên trước Pass 1, niêm phong seed trong hồ sơ hạn chế ngoài Git. Xử lý triệt để nguy cơ B suy ra ca khó: giải pháp trộn đệm ngẫu nhiên (*Blended Delivery Uniform Hash Shuffle*), thừa nhận trung thực giới hạn tính mù cuối kỳ. | **Mục 4** (Bảo vệ tính mù kép & Trộn đệm ngẫu nhiên) | Phép tính Cohen's Kappa trong `src/phishing/annotation/__init__.py` đã hỗ trợ lọc theo mảng boolean độc lập. | Lập trình module `blended_delivery.py` thực hiện Hash Shuffle và cập nhật `evaluate_kappa.py` thực hiện phép Join độc lập sau khi khóa Pass 1. | Thành viên C (thực hiện) & QA Lead B (kiểm tra mù) |
| **4** | Lô 1: Phân biệt điều đã xác minh với điều còn chờ; cách ly 2 shard đã biết `train-000`, `train-055`; ghi nhận `recovery_status.json` cho cả Lô 1 và Lô 2; lập phương án rủi ro tồn dư xin Lead D phê duyệt riêng. PhishVN là nguồn đề xuất thứ cấp. | **Mục 5** (Hiện trạng Lô 1 & Cách ly cấp Shard) | Sổ bộ `data/exclusion_registry.json` xác nhận Lô 2–10 có đủ hash; `recovery_status.json` ghi nhận trạng thái `pending_independent_review` cho Lô 1 và Lô 2. | Tổ chức phiên nghiệm thu độc lập mapping Lô 1; nếu chưa xong, trình Lead D ký duyệt văn bản chấp nhận rủi ro tồn dư trước khi trích xuất. | Thành viên C (hồ sơ) & Lead D (phê duyệt) |
| **5** | Quy trình vận hành khép kín (View $\rightarrow$ MarianMT `zh/ja/ru` $\rightarrow$ SHA256SUMS $\rightarrow$ QA B $\rightarrow$ Duyệt D); phân định rạch ròi 150 test hồi quy hiện có với test Main mới chưa viết; công bố đúng kết quả test độc lập của B (`137 passed, 13 skipped`). | **Mục 6** (Quy trình vận hành & Dịch ngoại tuyến) & **Mục 8** (Ranh giới kiểm thử) | Chạy kiểm thử độc lập của B trên clean checkout: `137 passed, 13 skipped in 2.22s` (13 skipped do không chứa tệp restricted ngoài Git). Máy C có đủ tệp đạt 150 passed. | Viết mới bộ kiểm thử cho Hợp đồng v1.2, cổng registry động và phép Join độc lập sau khi Lead D duyệt kế hoạch (hiện ở trạng thái CHƯA KIỂM CHỨNG). | Thành viên C (viết test) & QA Lead B (chạy kiểm chứng) |
| **6** | Đối chiếu ngân sách PLAN-01 (190,79h) vs Dự phóng V3.1 (192,32h; chênh +1,53h = +0,80% do đồng bộ 405 mẫu gán kép của B); khớp tổng tỷ trọng (100,01% do làm tròn); phân tích giờ của A (105,60h vs 105,67h) và lý do không cộng Model 4; chi tiết 15h QA B và 28h C; giữ tiến độ TBD. | **Mục 7** (Dự phóng định lượng & Bảng đối chiếu giờ công) | Dữ liệu đo đạc thực nghiệm Pass 1 của A (`intake_pass1_A_1c60d10a.jsonl`, mean 380,16s, median 335,62s) và B (mean 250,36s). | Trình Lead D xem xét phê duyệt điều chỉnh biên độ ngân sách +1,53 giờ trong một lượt quyết định. | Thành viên C (tính toán) & Lead D (phê duyệt) |

---

## 1. MỤC TIÊU, NGUYÊN TẮC VẬN HÀNH VÀ CAM KẾT CHỐNG RÒ RỈ

1. **Mục tiêu tối hậu:** Thiết lập quy trình vận hành gán nhãn khoa học, minh bạch và chặt chẽ nhằm xây dựng tập dữ liệu đánh giá 1.000 mẫu website phishing và benign có độ tin cậy cao, phục vụ công bố khoa học chuẩn quốc tế.
2. **Nguyên tắc học thuật bất biến (Academic Research Skills - ARS):**
   - *Tính mù kép (Double-Blind Annotation):* Cả hai chuyên viên gán nhãn (Annotator A và Annotator B) hoạt động độc lập, không nhìn thấy nhãn nguồn, không nhìn thấy locator và không nhìn thấy kết quả của nhau trong suốt Pass 1.
   - *Bảo vệ mẫu số Cohen's Kappa:* Chỉ số thỏa thuận liên đánh giá viên ($\kappa$) phải được tính toán trên một tập mẫu số ngẫu nhiên đại diện khách quan, độc lập với các ca khó bổ sung.
   - *Chống rò rỉ dữ liệu (Anti-Leakage Protocols):* Mọi mẫu hiệu chuẩn, pilot và sự cố lịch sử (246 mục trong `data/exclusion_registry.json`) được cách ly khỏi tập dữ liệu thực nghiệm chính thức.
3. **Các chốt chặn an toàn được duy trì nghiêm ngặt:**
   - `training_blocked = true` (Chặn nạp dữ liệu gán nhãn vào pipeline huấn luyện mô hình khi chưa hoàn tất phân xử Pass 2).
   - `official_test_used = false` (Cô lập nghiêm ngặt tập kiểm thử chính thức, không sử dụng cho bất kỳ đợt phát triển hay hiệu chuẩn nào).
   - `main_annotation_status = "LOCKED"` (Chiến dịch gán nhãn chính tiếp tục khóa chặt; chưa chọn mẫu, chưa tạo Blind View, chưa cấp phát tài nguyên cho đến khi Lead D ban hành quyết định phê duyệt chính thức).

---

## 2. THIẾT KẾ VẬN HÀNH CHI TIẾT ĐỢT 1 (BATCH 1 OPERATIONAL DESIGN)

### 2.1 Ma trận so sánh định lượng 4 kịch bản Đợt 1

Bảng phân tích so sánh toàn diện 4 phương án thiết kế Đợt 1 nhằm cung cấp đầy đủ căn cứ định lượng về nguồn lực để Lead D quyết định:

| Tiêu chí kỹ thuật & Quản trị | Phương án A1: Lô đầu Main (60 mẫu) | Phương án A2: Lô đầu Main (100 mẫu) | Phương án B1: Pilot Tách riêng (60 mẫu) | Phương án B2: Pilot Tách riêng (100 mẫu) |
|:---|:---:|:---:|:---:|:---:|
| **Bản chất dữ liệu** | Lô 1 chính thức của Main Corpus. | **Lô 1 chính thức của Main Corpus.** | Lô Pilot thử nghiệm công cụ tách riêng. | Lô Pilot thử nghiệm công cụ tách riêng. |
| **Hệ quả Loại trừ (Exclusion Registry)** | Giữ lại làm Train/Val/Test chính thức. | **Giữ lại làm Train/Val/Test chính thức.** | Bị loại trừ vĩnh viễn (thành Lô 11). | Bị loại trừ vĩnh viễn (thành Lô 11). |
| **Đóng góp vào mục tiêu 1.000 mẫu** | Đóng góp 60 mẫu (còn lại 940 mẫu). | **Đóng góp 100 mẫu (còn lại 900 mẫu).** | Đóng góp 0 mẫu (phải gán đủ 1.000 mẫu mới). | Đóng góp 0 mẫu (phải gán đủ 1.000 mẫu mới). |
| **Thời gian A gán Pass 1 (thực đo 6,34m)** | $60 \times 6,34\text{m} = \mathbf{6,34\text{ giờ}}$ | $100 \times 6,34\text{m} = \mathbf{10,57\text{ giờ}}$ | $60 \times 6,34\text{m} = \mathbf{6,34\text{ giờ}}$ | $100 \times 6,34\text{m} = \mathbf{10,57\text{ giờ}}$ |
| **Mẫu ngẫu nhiên gán kép của B (30%)** | 18 mẫu ($18 \times 4,17\text{m} = 1,25\text{h}$) | **30 mẫu ($30 \times 4,17\text{m} = 2,09\text{h}$)** | 18 mẫu ($18 \times 4,17\text{m} = 1,25\text{h}$) | 30 mẫu ($30 \times 4,17\text{m} = 2,09\text{h}$) |
| **Ca khó dự kiến phát sinh (~15%)** | ~9 mẫu ($9 \times 4,17\text{m} = 0,63\text{h}$) | **~15 mẫu ($15 \times 4,17\text{m} = 1,04\text{h}$)** | ~9 mẫu ($9 \times 4,17\text{m} = 0,63\text{h}$) | ~15 mẫu ($15 \times 4,17\text{m} = 1,04\text{h}$) |
| **Công sức kiểm định QA của B** | 2,50 giờ (schema, view, audit) | **3,00 giờ (schema, view, audit)** | 2,50 giờ | 3,00 giờ |
| **Công sức của Thành viên C** | 3,00 giờ (pipeline, MarianMT, Kappa) | **3,50 giờ (pipeline, MarianMT, Kappa)** | 3,00 giờ | 3,50 giờ |
| **Công sức của Lead D** | 1,00 giờ (phân xử Pass 2, duyệt cổng) | **1,50 giờ (phân xử Pass 2, duyệt cổng)** | 1,00 giờ | 1,50 giờ |
| **Tổng công số toàn nhóm cho Đợt 1** | **14,72 giờ** | **21,70 giờ** | **14,72 giờ** (lãng phí ngoài PLAN-01) | **21,70 giờ** (lãng phí ngoài PLAN-01) |
| **Ý nghĩa thống kê đo lường Kappa** | Cỡ mẫu $N=18$ có phương sai lớn. | **Cỡ mẫu $N=30$ đạt ngưỡng tiệm cận chuẩn.** | Cỡ mẫu $N=18$ có phương sai lớn. | Cỡ mẫu $N=30$ đạt ngưỡng tiệm cận chuẩn. |
| **Đánh giá tính khả thi trong 1 tuần** | Khả thi cao (~14,7h phân bổ 4 người). | **Khả thi cao (~21,7h phân bổ 4 người).** | Khả thi nhưng lãng phí nguồn lực. | Khả thi nhưng lãng phí nguồn lực. |

> [!TIP]
> **Khuyến nghị đề xuất của Thành viên C:** Thành viên C kính đề xuất Lead D lựa chọn **Phương án A2 (Lô đầu của Main Annotation — Quy mô 100 mẫu)**.  
> *Lý do:* Quy mô 100 mẫu cung cấp đúng $N_{\text{random}} = 30$ mẫu gán đôi cho B, đạt kích thước tối thiểu theo Định lý Giới hạn Trung tâm (CLT) để chỉ số Cohen's Kappa $\kappa_{A-B}$ có ý nghĩa thống kê tin cậy; đồng thời toàn bộ 100 mẫu này sau khi nghiệm thu sẽ đóng góp trực tiếp vào mục tiêu 1.000 mẫu, không làm lãng phí 21,7 giờ công của nhân sự vào việc tạo thêm một lô loại trừ mới.

### 2.2 Nguồn dữ liệu, Tiêu chí chọn mẫu & Bảo mật Hạt giống Phân tầng

1. **Nguồn dữ liệu hợp lệ duy nhất:** Trích xuất độc quyền từ nguồn `phreshphish` tại revision `eabec4b7a66324b79cc8a0ad856d1731dc26fe1a` (56 shards trong `configs/source_manifest.json`). Tuyệt đối không trích xuất từ PhishVN hoặc các nguồn chưa duyệt.
2. **Tiêu chí lọc thời gian (Temporal Window):** Chỉ lấy các bản ghi có ngày thu thập nằm trong dải đã kiểm toán: từ `2024-10-01` đến `2025-09-08`.
3. **Cơ chế Hạt giống ngẫu nhiên & Niêm phong Hồ sơ Hạn chế:**
   - *Hạt giống trích xuất ứng viên:* Sử dụng `random_seed_batch1_select = 20261101` đã xác định trong kế hoạch để rút tập ứng viên ngẫu nhiên từ các shard được phép khai thác.
   - *Bảo mật hạt giống phân tầng và xáo trộn:* Nhằm bảo vệ tính mù kép và ngăn ngừa việc Annotator B có thể tái lập trước danh sách 30% mẫu ngẫu nhiên hoặc thứ tự hiển thị, các hạt giống phân tầng (`random_seed_random30`) và xáo trộn (`random_seed_hash_shuffle`) **ĐƯỢC TẠO LẬP MẬT MÃ HỌC VÀ NIÊM PHONG TRONG HỒ SƠ HẠN CHẾ NGOÀI GIT** (`data/restricted/batch1_sampling_manifest.json`). Thành viên C chỉ công bố mã băm SHA-256 seal của tệp manifest này trước khi mở phiên Pass 1. Toàn bộ các giá trị hạt giống chỉ được mở niêm phong công khai sau khi cả A và B đã nộp và khóa mã băm bản ghi Pass 1.
4. **Tiêu chí phân bổ tổ chức & nhãn:**
   - Tỷ lệ nhãn nguồn cân bằng: 50% Phishing (50 mẫu) và 50% Benign (50 mẫu).
   - Phân bổ đại diện trên 14 tổ chức mục tiêu chuẩn hóa trong `configs/dictionary_v1.json` (`Microsoft, Google, Meta, Apple, Amazon, LinkedIn, X (Twitter), PayPal, Adobe, Booking.com, DHL, Spotify, Alibaba, Mastercard`) kết hợp nhóm tổ chức khác.

### 2.3 Quy trình kiểm tra trùng lặp 4 lớp & Lọc tương đồng Template

Trước khi đưa vào danh sách ứng viên chính thức, mọi mẫu trích xuất phải vượt qua các cổng kiểm soát kỹ thuật nghiêm ngặt:

1. **Cổng kiểm tra trùng lặp 4 lớp (4-Layer Cryptographic Deduplication Gate):**
   - *Lớp 1 (URL thô):* $\text{SHA-256}(\text{url}) \notin \text{ExclusionRegistry}$.
   - *Lớp 2 (URL chuẩn hóa):* $\text{SHA-256}(\text{normalize\_url}(\text{url})) \notin \text{ExclusionRegistry}$.
   - *Lớp 3 (HTML sạch):* $\text{SHA-256}(\text{clean\_html}(\text{raw\_html})) \notin \text{ExclusionRegistry}$.
   - *Lớp 4 (Domain Group):* $\text{SHA-256}(\text{eTLD+1}) \notin \text{ExclusionRegistry}$.
   - Đối soát đối chiếu với toàn bộ **246 mục ghi nhận loại trừ** trong `data/exclusion_registry.json`. Bất kỳ sự trùng khớp nào ở 1 trong 4 lớp đều bị loại bỏ ngay lập tức.
2. **Cổng kiểm tra tương đồng Template & Quy trình Đăng ký Tuần tự (`TemplateSimilarityEngine`):**
   - Áp dụng thuật toán SimHash 64-bit và DOM Tag Jaccard Similarity theo đúng mã nguồn `src/phishing/data/template_similarity.py` (dòng 96–97 và 164):
     * *Ngưỡng Hamming:* Loại bỏ ứng viên nếu khoảng cách Hamming $\le \mathbf{10\text{ bit}}$ (`max_allowed_simhash_distance = 10`) đối với bất kỳ template nào đã có trong corpus.
     * *Ngưỡng DOM Jaccard:* Loại bỏ ứng viên nếu độ tương đồng thẻ DOM Jaccard $\ge \mathbf{0,85}$ (`max_allowed_dom_jaccard = 0.85`) kết hợp khoảng cách SimHash $\le 12\text{ bit}$.
   - *Đặc tả bước đăng ký tuần tự (Sequential Registration):*
     Để ngăn chặn tình trạng nhiều mẫu trong cùng Lô 1 thuộc cùng một clone kit hoặc cùng một template sinh tự động, script `scripts/data/sample_batch1.py` duyệt tuần tự qua từng ứng viên rút từ shard:
     a) Ứng viên được kiểm tra qua `engine.check_candidate_similarity(candidate_text, candidate_html)`.
     b) Nếu `is_clone_template == True`, ứng viên bị loại bỏ ngay lập tức.
     c) Nếu `is_clone_template == False`, ứng viên được chấp nhận đưa vào danh sách tạm thời của Lô 1, và script **NGAY LẬP TỨC ĐĂNG KÝ ỨNG VIÊN NÀY VÀO ĐỘNG CƠ** thông qua:
        ```python
        engine.register_template(
            template_id=candidate["sample_id"],
            description=f"Batch1 accepted candidate {candidate['sample_id']}",
            sample_text=candidate_text,
            sample_html=candidate_html,
        )
        ```
     d) Nhờ bước đăng ký tuần tự này (`self.registered_templates.append(...)`), mọi ứng viên rút ra sau đó sẽ tự động được đối soát chống trùng clone với toàn bộ các ứng viên đã được chấp thuận trước đó trong cùng lô.
3. **Kiểm tra trùng lặp giữa các đợt (Cross-Batch Collision Check):**
   - Đảm bảo toàn bộ các mẫu của Đợt 1 không trùng lặp URL, HTML hoặc Domain Group với bất kỳ mẫu nào của các đợt hiệu chuẩn trước đó (Đợt B, Đợt C).

### 2.4 Tiêu chí ĐẠT & Tiêu chí DỪNG của Đợt 1 (Đồng bộ Blended Delivery)

Quy định thống nhất về cơ chế vận hành và nghiệm thu Đợt 1:

1. **Cơ chế phân phối và nghiệm thu Đợt 1:**
   - Trong Đợt 1 ($N=100$), Annotator A hoàn thành gán nhãn Pass 1 trên toàn bộ 100 mẫu.
   - Annotator B nhận gói dữ liệu Đợt 1 gồm đúng $N_{\text{random}} = 30$ mẫu ngẫu nhiên độc lập ($S_{\text{random30}}^{(1)}$) được phân tầng từ bảng niêm phong. Vì đây là đợt khởi đầu chiến dịch, bể ca khó tích lũy từ các đợt trước bằng rỗng ($S_{\text{hard\_accumulated}}^{(0)} = \emptyset$). Do đó, ở Đợt 1, gói giao cho B gồm đúng 30 mẫu ngẫu nhiên.
   - Các ca khó do Annotator A phát hiện trong 100 mẫu của Đợt 1 ($S_{\text{hard\_A1}}$, ước tính ~15 mẫu) được chuyển vào Bể ca khó tích lũy ($S_{\text{hard\_accumulated}}^{(1)}$) và sẽ được gộp phát cho B ở Đợt 2 thông qua cơ chế Blended Delivery cùng với $S_{\text{random30}}^{(2)}$.
2. **TIÊU CHÍ ĐẠT (PASS CRITERIA — ĐỦ ĐIỀU KIỆN MỞ RỘNG TOÀN CHIẾN DỊCH):**
   - *Tiến độ Pass 1:* Hoàn thành toàn bộ gán nhãn Pass 1 (A gán 100 mẫu, B gán 30 mẫu ngẫu nhiên).
   - *Hạ tầng CLI:* Không phát sinh lỗi kỹ thuật crash phần mềm hay lỗi schema validation trong suốt quá trình ghi nhận.
   - *Chất lượng đồng thuận:* Chỉ số Cohen's Kappa trước phân xử tính trên 30 mẫu ngẫu nhiên đạt $\kappa_{\text{random}} \ge \mathbf{0,75}$ (hoặc ngưỡng do Lead D chính thức chốt).
   - *Tỷ lệ nghi ngờ an toàn:* Tỷ lệ mẫu gắn cờ `insufficient_evidence` $\le \mathbf{5,0\%}$ (không quá 5 mẫu trên 100 mẫu).
   - *Nghiệm thu phân xử Pass 2:* Hoàn tất phiên họp phân xử Pass 2 do Lead D chủ trì cho các ca bất đồng nhãn phát sinh giữa A và B trong 30 mẫu ngẫu nhiên, ký biên bản QA độc lập.
   - *Bàn giao bể ca khó:* Nghiệm thu danh mục ca khó Đợt 1 của A để sẵn sàng nạp vào Đợt 2.
3. **TIÊU CHÍ DỪNG / CẢNH BÁO KHẨN CẤP (STOP GATES — DỪNG ĐỂ RÀ SOÁT NGUYÊN NHÂN GỐC):**
   - *Cổng cảnh báo chất lượng snapshot:* Nếu tỷ lệ `insufficient_evidence` $> \mathbf{5,0\%}$, hệ thống kích hoạt **Quy trình dừng an toàn để rà soát chất lượng snapshot HTML và tiêu chí crawl nguồn** (loại trừ lỗi mạng, bot-block, trang trắng). **TUYỆT ĐỐI NGHIÊM CẤM TẠO ÁP LỰC ÉP NGƯỜI GÁN PHẢI CHUYỂN ĐỔI NHÃN SANG PHISHING HOẶC BENIGN**.
   - *Cổng cảnh báo đồng thuận:* Nếu $\kappa_{\text{random}} < \mathbf{0,60}$, tạm dừng phát hành Đợt 2 để tổ chức phiên họp kỹ thuật rà soát lại độ rõ ràng của Codebook v1.1 và tiêu chí nhận diện của annotator.
   - *Cổng cảnh báo an toàn:* Nếu phát hiện bất kỳ sự cố rò rỉ nào về nhãn nguồn, locator hay cờ phân tầng đối với Annotator B, hủy bỏ đợt gán nhãn và cô lập dữ liệu.

---

## 3. HỢP ĐỒNG DỮ LIỆU GÁN NHÃN MÙ (BLIND CONTRACT V1.2) & CƠ CHẾ PHÂN NHÁNH PHIÊN BẢN

### 3.1 Chốt một tên trường duy nhất: `blind_contract_version`
- **Tên trường duy nhất được áp dụng:** **`blind_contract_version`** (loại bỏ hoàn toàn cách viết tùy chọn "hoặc view_schema_version").
- **Phiên bản Codebook giữ nguyên bất biến:** **`codebook_version = "1.1.0"`** (khớp toàn diện với `docs/CODEBOOK_V1_1.md`). Thành viên C tuyệt đối không tự nâng Codebook lên 1.2.0.
- **Giá trị của Hợp đồng dữ liệu Main:** **`"1.2.0"`**.

### 3.2 Đặc tả Hợp đồng Dữ liệu Main Annotation v1.2 (`blind_contract_version = "1.2.0"`)
1. **Schema tệp Blind View (`main_annotation_blind_view.json`):**
   - **HOÀN TOÀN KHÔNG CHỨA TRƯỜNG `random_subset`** (cấm cả giá trị thật lẫn giá trị boolean giả).
   - Danh mục 12 trường allowlist được phép xuất hiện trong mỗi `BlindSample`:
     `sample_id`, `url`, `page_text`, `structure_summary`, `codebook_version` (`"1.1.0"`), `blind_contract_version` (`"1.2.0"`), `translation_provided`, `translated_text`, `translation_source_language`, `translation_tool`, `translation_tool_version`, `translation_sha256`.
2. **Schema Bản ghi Gán nhãn Pass 1 (`AnnotationRecord`):**
   - Bản ghi xuất ra từ CLI (`intake_pass1_A.jsonl`, `intake_pass1_B.jsonl`) **LOẠI BỎ HOÀN TOÀN TRƯỜNG `random_subset`**.
   - Khớp đúng 100% các trường chuẩn hóa theo mã nguồn `src/phishing/annotation/blind_view.py` (dòng 540–601) và `src/phishing/annotation/__init__.py`:
     * *Định danh & tiến trình:* `annotator_id`, `sample_id`, `pass_id`, `seconds_spent`, `pause_count`, `paused_seconds`, `timestamp_utc`.
     * *Phán đoán phân loại (Codebook v1.1):* `class_label`, `primary_org_status`, `catalog_status`, `observed_service`, `org_targets`, `primary_org`, `identity_role`, `domain_role`, `evidence_note`, `difficult_case`, `confidence`, `primary_phishing_type`, `hard_benign_type`.
     * *Bằng chứng trích dẫn:* `org_evidence` (danh sách các đối tượng trích dẫn từ view).
     * *Kiểm soát phiên bản:* `codebook_version` (`"1.1.0"`), `blind_contract_version` (`"1.2.0"`).
     * *Nguồn gốc kiểm toán phục vụ `compute_cohens_kappa`:* `dataset_id`, `dataset_hash`, `codebook_hash`, `sampling_plan_version`, `sample_content_hash`, `is_dry_run`, `is_synthetic`.
   - Bảo toàn tính trung thực học thuật: Tuyệt đối không lưu trữ cờ `random_subset: true` giả vào kết quả của các ca khó bổ sung.

### 3.3 Cơ chế phân nhánh tương thích ngược & Từ chối an toàn (Fail-Closed Rejection)
Bộ nạp và kiểm tra tính hợp lệ (`Validator` và `annotate_cli.py`) được thiết kế phân nhánh xử lý tường minh, từ chối an toàn ngay khi thiếu hoặc sai phiên bản:

```python
# Logic phân nhánh và từ chối an toàn (Fail-Closed)
def validate_and_load_blind_sample(sample_dict: dict) -> BlindSample:
    # 1. Bắt buộc phải có khóa blind_contract_version tường minh
    if "blind_contract_version" not in sample_dict:
        raise ValueError("LỖI SCHEMA (FAIL-CLOSED): Thiếu trường bắt buộc 'blind_contract_version'!")
        
    contract_ver = sample_dict["blind_contract_version"]
    
    if contract_ver == "1.1.0":
        # CHẾ ĐỘ CALIBRATION CŨ: Tương thích ngược với dữ liệu Runway A lịch sử
        if "random_subset" not in sample_dict:
            raise ValueError("LỖI SCHEMA V1.1: Gói Calibration bắt buộc phải có random_subset: bool")
        return load_legacy_calibration_sample(sample_dict)
        
    elif contract_ver == "1.2.0":
        # CHẾ ĐỘ MAIN ANNOTATION: Hợp đồng v1.2 bảo vệ tính mù
        if "random_subset" in sample_dict:
            raise ValueError("LỖI BẢO MẬT HỢP ĐỒNG V1.2: Cấm đưa trường random_subset vào Blind View của Main!")
        if sample_dict.get("codebook_version") != "1.1.0":
            raise ValueError("LỖI CODEBOOK: Main Annotation bắt buộc dùng codebook_version='1.1.0' đã khóa!")
        return load_main_v12_sample(sample_dict)
        
    else:
        # TỪ CHỐI AN TOÀN KHI SAI PHIÊN BẢN HỢP ĐỒNG
        raise ValueError(f"TỪ CHỐI AN TOÀN (FAIL-CLOSED): Phiên bản hợp đồng '{contract_ver}' không hợp lệ!")
```

---

## 4. CƠ CHẾ BẢO VỆ TÍNH MÙ KÉP & GIẢI PHÁP PHÂN PHỐI TRỘN ĐỆM NGẪU NHIÊN (BLENDED DELIVERY)

### 4.1 Khóa tập ngẫu nhiên 30% & Lưu trữ Hồ sơ Phân tầng Hạn chế
1. **Khóa trước 30% mẫu ngẫu nhiên ($S_{\text{random}}$):**
   - Trước khi bất kỳ tệp Blind View nào được xuất xưởng cho Annotator A, Thành viên C thực hiện rút ngẫu nhiên độc lập 30% mẫu:
     $$N_{\text{random}} = \text{round}(0,30 \times N) \quad (N_{\text{random}} = 300\text{ mẫu cho toàn chiến dịch; } 30\text{ mẫu cho Đợt 1})$$
   - Hạt giống phân tầng được sinh ngẫu nhiên mật mã học và niêm phong trong hồ sơ hạn chế.
2. **Niêm phong Hồ sơ Phân tầng Hạn chế (Restricted Sampling Manifest):**
   - Danh sách phân định mẫu được lưu trữ duy nhất trong khu vực hạn chế ngoài Git:
     `data/restricted/main_annotation_sampling_manifest.json`
   - Cấu trúc tệp ghi nhận:
     ```json
     {
       "manifest_version": "1.2.0",
       "sampling_plan": "PLAN-MAIN-ANNOTATION-MASTER-V3.1",
       "total_samples": 1000,
       "random_subset_count": 300,
       "strata_mapping": {
         "MAIN-0001": {"stratum": "random_30", "is_random_subset": true},
         "MAIN-0002": {"stratum": "supplemental_candidate", "is_random_subset": false}
       }
     }
     ```
   - Tệp này được tạo và khóa SHA-256 trước khi phiên Pass 1 bắt đầu, lưu trữ tại khu vực restricted mà Annotator B không có quyền truy cập.

### 4.2 Giải pháp Phân phối Trộn đệm Ngẫu nhiên (Blended Delivery Uniform Hash Shuffle)

Nhằm giải quyết triệt để nguy cơ Annotator B suy đoán các mẫu được gửi bổ sung là "ca khó", nhóm nghiên cứu áp dụng mô hình phân phối trộn đệm cuốn chiếu qua các chặng (Sprint Chunks):

```
[Tiến trình của A]          [Đợt 1 của A: 100 mẫu] ────────────────► [Đợt 2 của A: 200 mẫu]
                                   │                                       │
                                   ├───────────────────────┐               │
                                   ▼                       ▼               ▼
                            (30% Rút ngẫu nhiên)     (Phát hiện ca khó)   (30% Rút ngẫu nhiên)
                                   │                       │               │
                                   │                       ▼               │
                                   │             [Bể Ca khó Đợt 1]         │
                                   │                       │               │
                                   │                       ├───────────────┤
                                   │                       ▼               ▼
[Gói phát hành cho B]     (Đợt 1 cho B: 30 mẫu)   (Đợt 2 cho B: 60 mẫu R_30% + Ca khó Đợt 1)
                                   │                               │
                                   ▼                               ▼
                         [Uniform Hash Shuffle]          [Uniform Hash Shuffle]
                                   │                               │
                                   ▼                               ▼
                         (B nhận 30 mẫu ngẫu nhiên)      (B nhận gói hỗn hợp xáo trộn)
                         (Chưa có ca khó tích lũy)       (Mù phân tầng, không biết ca khó)
```

1. **Nguyên tắc phân phối theo đợt gộp (Sprint Chunks):**
   - Tuyệt đối không phát hành các ca khó thành một tệp riêng lẻ.
   - Khi phát gói gán kép cho B ở Đợt $k+1$, tập dữ liệu giao cho B sẽ được tạo thành từ **Phép hợp toán học** giữa 30% ngẫu nhiên của đợt mới và ca khó tích lũy từ đợt trước:
     $$S_{B}^{(k+1)} = S_{\text{random30}}^{(k+1)} \cup S_{\text{hard\_accumulated}}^{(k)}$$
2. **Thuật toán Xáo trộn Băm Đồng nhất (Uniform Hash Shuffle):**
   - Trước khi xuất ra tệp Blind View phát cho B, toàn bộ các mẫu trong tập hợp trên được xáo trộn ngẫu nhiên dựa trên hàm băm mật mã học kết hợp hạt giống niêm phong:
     $$\text{sort\_key}(s) = \text{SHA-256}(\text{sample\_id} \parallel \text{seed\_shuffle})$$
   - Nhờ đó, các ca khó bổ sung được phân tán ngẫu nhiên xen kẽ giữa các mẫu ngẫu nhiên thông thường. Tệp giao cho B có định dạng đồng nhất, mã ID trung tính liên tục, không có bất kỳ cờ hay thứ tự nào để B có thể suy đoán nguồn gốc mẫu.
3. **Thừa nhận trung thực Giới hạn Tính mù Cuối kỳ (End-of-Campaign Residual Blinding Limitation):**
   - Tại đợt phát hành cuối cùng sau khi Annotator A hoàn thành toàn bộ 1.000 mẫu, không còn các mẫu ngẫu nhiên mới của đợt kế tiếp để làm lớp đệm xáo trộn cho nhóm ca khó tồn đọng cuối cùng. Kế hoạch thừa nhận trung thực giới hạn tính mù này thay vì khẳng định "mù tuyệt đối".
   - *Phương án quản trị rủi ro suy đoán cuối kỳ:* (a) Annotator B không được thông báo về số lượng ca khó hay ranh giới của đợt cuối; (b) Lead D có thể chỉ đạo trích xuất thêm một tập đệm ngẫu nhiên nhỏ ($N_{\text{buffer}} \approx 10\text{ mẫu}$) chỉ dùng làm vỏ bọc xáo trộn cho ca khó; hoặc (c) ghi nhận rõ tỷ lệ ca khó của đợt cuối trong báo cáo kiểm toán phương pháp.

### 4.3 Phép Join độc lập tính Cohen's Kappa chính thức trước phân xử
Sau khi A và B nộp và khóa mã băm Pass 1, module `evaluate_kappa.py` thực hiện phép kết (Join) độc lập:
$$\text{EvaluationSet} = \text{Record}_A[\text{sample\_id}] \bowtie \text{Record}_B[\text{sample\_id}] \bowtie \text{RestrictedStrataMap}[\text{sample\_id}]$$
- Chỉ số Cohen's Kappa chính thức trước phân xử ($\kappa_{\text{primary}}$) **CHỈ ĐƯỢC TÍNH TRÊN CÁC MẪU CÓ $\text{is\_random\_subset} == \text{True}$**.
- Các ca khó bổ sung được bóc tách để phân tích thăm dò riêng biệt (Subgroup Agreement), không đưa vào mẫu số Kappa đại diện toàn corpus.

---

## 5. HIỆN TRẠNG LÔ 1, DANH MỤC SHARD CÁCH LY & QUẢN TRỊ RỦI RO TỒN DƯ

### 5.1 Phân định rõ ràng: Điều đã xác minh vs Điều còn chờ kiểm toán

| Danh mục Lô loại trừ | Số mẫu | Trạng thái hiện tại trên `exclusion_registry.json` | Hiện trạng mã băm kiểm toán | Đánh giá an toàn kỹ thuật |
|:---|:---:|:---:|:---|:---|
| **Lô 1 (`EXCL-PILOT-01`)** | 20 | `unresolved_source_mapping` (Rows API chưa khóa revision) | **CHƯA CÓ** URL/HTML hash trên registry. Hồ sơ `raw20_mapping_check.json` trong `recovery_status.json` vẫn ở trạng thái `pending_independent_review`. | **ĐIỀU CÒN CHỜ:** Chưa thể đối soát hash tự động. Cần hoàn tất nghiệm thu độc lập hoặc khoanh vùng cách ly. |
| **Lô 2 (`EXCL-REAL-PILOT-32`)** | 32 | `unresolved_source_mapping` (chưa có locator shard) | **ĐÃ CÓ ĐỦ 32/32 bộ mã băm** `url_sha256`, `html_sha256`, `group_sha256` trên registry. Hồ sơ `v1_mapping_check.json` trong `recovery_status.json` cũng đang ở trạng thái `pending_independent_review`. | **ĐÃ XÁC MINH MÃ BĂM:** Đang hoạt động trực tiếp trong `is_excluded()` chặn trùng URL/HTML/Domain; định vị shard còn chờ nghiệm thu. |
| **Lô 3 & Lô 4 (`REAL-PILOT-32-V2`)** | 32 | Lô 4: `resolved` (Rows API pinned) | **ĐÃ CÓ ĐỦ 32/32 bộ mã băm** URL/HTML/Group và định vị shard (`train-000`, `train-055`). | **ĐÃ XÁC MINH TOÀN DIỆN:** Chặn bằng cả hash và locator vật lý. |
| **Lô 5 đến Lô 10 (Hiệu chuẩn & Sự cố)** | 162 | `resolved` / `mapped_to_shards` / `resolved_in_restricted_dossier` | **ĐÃ CÓ ĐỦ các bộ mã băm** URL/HTML/Group (công khai hoặc niêm phong ngoài Git). | **ĐÃ XÁC MINH MẬT MÃ HỌC:** Niêm phong bất biến với cam kết hash đã kiểm chứng. |

### 5.2 Danh mục Shard Cách ly đã biết & Định vị phần nguồn còn lại
1. **Hai shard đã biết cần cách ly:**
   - Căn cứ hồ sơ thực nghiệm, hai tệp Parquet sau đã được xác định chắc chắn từng được dùng cho các đợt V2 Rebuild và Hiệu chuẩn:
     * `data/train-000.parquet`
     * `data/train-055.parquet`
   - Hai tệp này được đưa vào **Danh mục Cách ly Cấm Khai thác (Quarantined Shards Blacklist)** đối với toàn bộ chiến dịch Main Annotation.
2. **Định vị chính xác phần nguồn còn lại:**
   - Thành viên C **loại bỏ cụm từ "Shard Nguồn Sạch Đã Được Xác Minh"**.
   - Do Lô 1 thu thập qua HuggingFace Rows API chưa khóa revision, nhóm nghiên cứu chưa thể chứng minh toán học rằng Rows API của Lô 1 chưa từng chạm tới các shard khác. Phần nguồn còn lại được định vị chính xác là: **"Các Shard Nguồn Chưa Xác Minh Được Phạm Vi Rows API của Lô 1 (Unverified Shards Pending Pilot 1 Scope)"**.
3. **Quy trình giải quyết & Điểm quyết định riêng của Lead D (Lead D Residual Risk Decision Gate):**
   - *Ưu tiên số 1:* Thành viên C phối hợp cùng QA Lead B tổ chức rà soát độc lập hồ sơ `raw20_mapping_check.json` để nghiệm thu chính thức 20 mã băm URL/HTML vào `exclusion_registry.json`.
   - *Điểm quyết định của Lead D:* Trường hợp chưa hoàn tất nghiệm thu Lô 1 trước ngày mở trích xuất Đợt 1, Thành viên C lập báo cáo kiểm kê rủi ro tồn dư để **Lead D ban hành Quyết định phê duyệt phạm vi nguồn và chấp nhận mức rủi ro tồn dư riêng bằng văn bản**. Tuyệt đối không tự ý suy diễn việc loại trừ khi chưa có căn cứ.
4. **Quy chế nguồn PhishVN:** PhishVN tiếp tục là **Nguồn đề xuất thứ cấp — CHƯA ĐƯỢC PHÉP TRÍCH XUẤT**.

---

## 6. QUY TRÌNH VẬN HÀNH KHÉP KÍN (END-TO-END PIPELINE) & CHUẨN HÓA DỊCH MARIANMT

### 6.1 Quy trình vận hành 6 bước chuẩn kiểm toán

```
[BƯỚC 1: TRÍCH XUẤT & LỌC TRÙNG]
  │ • Nạp các shard chưa thẩm định độc lập phạm vi Lô 1 (ngoài 2 shard đã cách ly train-000, train-055)
  │   sau khi Lead D phê duyệt Biên bản Cổng Quyết định Rủi ro Tồn dư.
  │ • Lọc trùng 4 lớp đối soát 246 mẫu registry + Đăng ký tuần tự TemplateSimilarityEngine.
  ▼
[BƯỚC 2: GẮN DỊCH NGOẠI TUYẾN MARIANMT TIẾNG ANH (R-A09)]
  │ • Quét phát hiện ngôn ngữ: zh, ja, ru -> Dịch sang TIẾNG ANH (Helsinki-NLP opus-mt ghim revision SHA).
  │ • Bảo toàn nguyên vẹn page_text gốc; lưu translated_text + 5 trường metadata + translation_sha256.
  ▼
[BƯỚC 3: KHÓA BẢNG PHÂN TẦNG & NIÊM PHONG HỒ SƠ HẠN CHẾ]
  │ • Khóa 30% ngẫu nhiên cho B vào data/restricted/main_annotation_sampling_manifest.json.
  │ • Xáo trộn Blended Delivery Uniform Hash Shuffle; tạo SHA256SUMS.txt và release manifest.
  ▼
[BƯỚC 4: THẨM ĐỊNH QA ĐỘC LẬP CỦA B & PHÊ DUYỆT MỞ PHIÊN CỦA LEAD D]
  │ • QA Lead B kiểm tra schema Hợp đồng v1.2, zero-leak check; ký biên bản QA độc lập.
  │ • Lead D kiểm tra hồ sơ, ký quyết định phê duyệt mở phiên Pass 1.
  ▼
[BƯỚC 5: GÁN NHÃN PASS 1 ĐỘC LẬP (A GÁN 100%, B GÁN GÓI BLENDED THEO ĐỢT)]
  │ • A và B gán nhãn độc lập qua annotate_cli.py v1.2; ghi nhật ký thời gian và bằng chứng org_evidence.
  │ • Kết thúc Pass 1: Đóng băng và khóa mã băm intake_pass1_A.jsonl và intake_pass1_B.jsonl.
  ▼
[BƯỚC 6: PHÂN XỬ PASS 2, KHÓA NHÃN VÀNG & BÀN GIAO DỮ LIỆU]
  │ • Tính Cohen's Kappa sơ bộ qua phép Join độc lập với bảng phân tầng hạn chế.
  │ • Lead D chủ trì phân xử Pass 2 cho các ca bất đồng; chốt consensus_label.
  │ • Cập nhật exclusion_registry.json nếu phát hiện mẫu lỗi/hỏng; bàn giao Gold Dataset cho Lead D.
```

### 6.2 Chuẩn hóa Quy trình Dịch ngoại tuyến MarianMT Tiếng Anh (Yêu cầu R-A09)
Nhằm hỗ trợ chuyên viên gán nhãn xử lý các website đa ngôn ngữ mà vẫn bảo toàn tính toàn vẹn khoa học:
- **Ngôn ngữ được dịch:** Tiếng Trung (`zh`), Tiếng Nhật (`ja`), Tiếng Nga (`ru`).
- **Mô hình dịch cục bộ ngoại tuyến (Offline MarianMT):**
  * Tiếng Trung: `Helsinki-NLP/opus-mt-zh-en` (Ghim revision commit SHA-256).
  * Tiếng Nhật: `Helsinki-NLP/opus-mt-ja-en` (Ghim revision commit SHA-256).
  * Tiếng Nga: `Helsinki-NLP/opus-mt-ru-en` (Ghim revision commit SHA-256).
- **Bảo toàn nguyên bản:** Văn bản gốc `page_text` được lưu trữ bất biến. Văn bản dịch được lưu vào `translated_text` kèm đầy đủ 5 trường siêu dữ liệu kiểm toán và mã băm `translation_sha256`. Tuyệt đối không gọi API dịch trực tuyến ra Internet trong quá trình suy luận.

---

## 7. DỰ PHÓNG NGÂN SÁCH ĐỊNH LƯỢNG & TIẾN ĐỘ THỰC NGHIỆM

### 7.1 Đánh giá Định lượng Tốc độ Thực tế của Annotator A
- **Dữ liệu thực nghiệm Pass 1 Runway A ($N=24$ mẫu đã khóa trong `intake_pass1_A_1c60d10a.jsonl`):**
  * Tổng thời gian gán: $9.123,72\text{ giây}$.
  * Thời gian trung bình: **$380,155\text{ giây/mẫu} \approx 6,34\text{ phút/mẫu}$**.
  * Thời gian trung vị: **$335,62\text{ giây/mẫu} \approx 5,59\text{ phút/mẫu}$** (khớp chuẩn `plan_01_calibration_effort_report.json`).
- **Tính toán năng suất cho 1.000 mẫu:**
  * Tại định mức đo thực tế $6,34\text{ phút/mẫu}$ (làm tròn từ 380,16s), chỉ riêng Annotator A cần:
    $$1.000 \times 6,3359\text{ phút} = 6.335,9\text{ phút} \approx \mathbf{105,60\text{ giờ}} \quad (\text{hoặc } 105,67\text{ giờ nếu tính theo } 6,34\text{m})$$
  * Nếu một tuần làm việc tiêu chuẩn là $40\text{ giờ/người}$, Annotator A cần tối thiểu **$2,64\text{ tuần làm việc toàn thời gian}$** chỉ để hoàn thành phần gán nhãn của mình.
  * Do đó, chuỗi phụ thuộc tuần tự khiến **toàn bộ chiến dịch 1.000 mẫu về mặt toán học và quy trình không thể hoàn thành trong 1 tuần (7 ngày dương lịch)**.
- **Đánh giá tiến độ có điều kiện:** Tiến độ 1 tuần chỉ khả thi đối với **Đợt 1 (Quy mô 100 mẫu Phương án A2, tổng công số toàn nhóm ~21,7 giờ)**. Tiến độ chính thức toàn chiến dịch tiếp tục là **CHƯA XÁC ĐỊNH (TBD)** chờ kết quả đo lường thực tế từ Đợt 1.

### 7.2 Bảng đối chiếu ngân sách: PLAN-01 (190,79h) vs Dự phóng V3.1 (192,32h)

| Thành viên / Vai trò | Phân bổ PLAN-01 được duyệt (Giờ) | Tỷ lệ PLAN-01 (%) | Kịch bản Dự phóng V3.1 đề xuất (Giờ) | Tỷ lệ V3.1 (%) | Độ lệch công số (Giờ) | Giải trình nguyên nhân dịch chuyển cơ cấu kỹ thuật |
|:---|:---:|:---:|:---:|:---:|:---:|:---|
| **Annotator A** | 114,08 | 59,80% | **105,67** | 54,95% | **-8,41** | Tính theo tốc độ thực đo $6,34\text{ phút/mẫu}$ ($105,67\text{h}$; nếu tính theo trung bình thô 380,155s là $105,60\text{h}$). Kịch bản V3.1 chủ động không áp dụng biên dự phòng Model 4 (+8% buffer = 114,08h của PLAN-01) để phản ánh đúng năng suất thực đo của chính A. |
| **QA Lead B** | 36,21 | 18,98% | **43,15** | 22,44% | **+6,94** | Gán nhãn kép 405 mẫu chuẩn PLAN-01 ($405 \times 4,17\text{m} = 28,15\text{h}$) cộng đệm công tác kiểm định QA độc lập, audit schema và verify SHA256SUMS qua 5 đợt gán ($5 \text{ đợt} \times 3,00\text{h} = 15,00\text{h}$). |
| **Thành viên C** | 25,00 | 13,10% | **28,00** | 14,56% | **+3,00** | Vận hành 5 đợt pipeline dữ liệu, dedupe 4 lớp, Template engine, MarianMT translation, khóa tệp phân tầng, độc lập join và tính Kappa ($5 \times 4,00\text{h} = 20,00\text{h}$); cộng 8,00h thiết lập Hợp đồng v1.2, quản trị registry và reconciliation tổng kết. |
| **Lead D** | 15,50 | 8,12% | **15,50** | 8,06% | **0,00** | Phân xử bất đồng Pass 2 cho các ca bất đồng phát sinh cộng thời gian thẩm duyệt mốc tối hậu (khớp chuẩn ngân sách PLAN-01). |
| **TỔNG CỘNG** | **190,79** | **100,00%** | **192,32** | **100,00%** | **+1,53** | **Kịch bản V3.1 đồng bộ 405 mẫu có tổng công số 192,32 giờ (chênh +1,53h = +0,80% so với khung PLAN-01), kính trình Lead D xem xét phê duyệt riêng.** |

*(Ghi chú số học: Tổng các tỷ lệ thành phần của V3.1 là $54,95\% + 22,44\% + 14,56\% + 8,06\% = 100,01\%$ do làm tròn số thập phân 2 chữ số; tổng giá trị chính xác là 100,00%).*

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
  * Commit V3.0: [`bc29582092c70b5d6c5793971fe7fa7482a8fbe5`](https://github.com/Anhtuann1404/NCKH_2/commit/bc29582092c70b5d6c5793971fe7fa7482a8fbe5)
  * Commit V3.1 (Bản Master hoàn thiện hiện hành): Được cập nhật và đẩy trực tiếp lên nhánh cùng văn bản này.

### 8.2 Báo cáo Trung thực Kết quả Kiểm thử & Phân định Ranh giới
1. **Kết quả kiểm thử độc lập của QA Lead B trên clean checkout commit `bc295820`:**
   - **Lệnh thực thi:**
     ```bash
     PYTHONPATH=src python -m pytest tests/test_blind_view.py tests/test_clean_calibration_blind_view.py tests/test_difficulty_strata.py tests/test_exclusion_registry.py -v -rs
     ```
   - **Kết quả quan sát được:** **`137 passed, 13 skipped in 2.22s`** (`0 failed, 0 deselected`, Python 3.14.2 / pytest 9.1.1):
     * `tests/test_blind_view.py`: **87 passed** (an toàn Blind View v1.1, allowlist trường, strip thẻ script/event, loại trừ rò rỉ nhãn).
     * `tests/test_difficulty_strata.py`: **9 passed** (tính toán độc lập 6 cờ chỉ báo mô tả bề mặt).
     * `tests/test_exclusion_registry.py`: **41 passed, 1 skipped** (`test_restricted_commitment_round_c_loaded_and_verified` bỏ qua do môi trường clean checkout không có tệp hạn chế ngoài Git `data/restricted/clean_calibration_exclusion_mapping_c_32.json`).
     * `tests/test_clean_calibration_blind_view.py`: **0 passed, 12 skipped** (bỏ qua do môi trường clean checkout không có tệp ngoài Git `data/annotations/clean_calibration_blind_view_24.json`).
   - *(Ghi chú đối soát: Trên môi trường của Thành viên C có sẵn hai tệp hạn chế nêu trên, test suite chạy đủ 150 passed).*
2. **Khẳng định ranh giới kiểm thử học thuật:**
   - Toàn bộ 150 hàm test nêu trên là **test hồi quy của mã v1.1.0 hiện hữu**.
   - Các cơ chế mới của Main Annotation (`sample_batch1.py`, Blended Delivery Uniform Hash Shuffle, MarianMT `zh/ja/ru`, validator phân nhánh Hợp đồng v1.2, phép Join độc lập tính Kappa) hiện **CHƯA ĐƯỢC LẬP TRÌNH VÀ CHƯA KIỂM CHỨNG**.
   - Các mã nguồn và bộ test mới này chỉ được phép lập trình sau khi Lead D chính thức ký duyệt kế hoạch vận hành.

---

## 9. DANH MỤC 6 QUYẾT ĐỊNH KÍNH TRÌNH LEAD D XEM XÉT TRONG MỘT LƯỢT

Thành viên C kính trình QA Lead B thẩm định độc lập và Lead D xem xét ban hành quyết định đối với 6 nội dung trọng tâm sau:

1. **Phê duyệt Phương án & Quy mô Đợt 1:** Lựa chọn Phương án A2 (Lô đầu Main — 100 mẫu, tổng công số toàn nhóm ~21,7 giờ); chốt tiêu chí Đạt/Dừng của Đợt 1.
2. **Phê duyệt Hợp đồng Dữ liệu Blind View v1.2:** Chấp thuận việc chốt duy nhất tên trường `blind_contract_version = "1.2.0"`, giữ nguyên `codebook_version = "1.1.0"`, cấm trường `random_subset` trong Blind View và bản ghi Pass 1 của Main, cơ chế fail-closed khi thiếu phiên bản.
3. **Phê duyệt Cơ chế Trộn đệm Ngẫu nhiên (Blended Delivery):** Thông qua phương án phân phối trộn đệm với Uniform Hash Shuffle để bảo vệ tính mù cho Annotator B, ghi nhận giới hạn tính mù cuối kỳ.
4. **Phê duyệt Quyết định Phạm vi Nguồn và Chấp nhận Rủi ro Tồn dư Lô 1:** Ban hành văn bản phê duyệt danh mục cách ly 2 shard đã biết (`train-000`, `train-055`) và quyết định phương án chấp nhận rủi ro tồn dư của Lô 1 trước khi rút mẫu.
5. **Phê duyệt Ngân sách Hiệu chỉnh V3.1 (192,32 giờ):** Chấp thuận độ lệch chênh +1,53 giờ so với khung PLAN-01 (190,79h) do đồng bộ theo 405 mẫu gán kép của B.
6. **Xác nhận Tiến độ Toàn chiến dịch là TBD:** Ghi nhận tiến độ chính thức theo tuần của toàn chiến dịch là TBD chờ kết quả thực nghiệm Đợt 1 và cam kết giờ làm việc của A và B.

---

**XÁC NHẬN CỦA THÀNH VIÊN C (DATA PIPELINE & THƯ KÝ KIỂM TOÁN)**  
*(Bản Kế hoạch Vận hành Hợp nhất V3.1 — Duy trì nghiêm ngặt: training_blocked=true, official_test_used=false, Main Annotation KHÓA)*  

**Nguyễn Thắng**
