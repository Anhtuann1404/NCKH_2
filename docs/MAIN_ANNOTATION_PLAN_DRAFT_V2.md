# KẾ HOẠCH VẬN HÀNH HỢP NHẤT CHIẾN DỊCH GÁN NHÃN CHÍNH (MASTER OPERATIONAL ANNOTATION PLAN - PROPOSAL V3.4)

**Dự án:** Nghiên cứu phát hiện website phishing mạo danh tổ chức bằng học máy kết hợp URL và nội dung trang (NCKH_2)  
**Mã văn bản:** `PLAN-MAIN-ANNOTATION-MASTER-V3.4`  
**Phiên bản:** `3.4.0-CONSOLIDATED-PROPOSAL`  
**Ngày lập:** 12/11/2026  
**Đơn vị lập:** Thành viên C (Nguyễn Thắng — Data Pipeline & Thư ký Kiểm toán)  
**Cộng sự suy luận chuyên sâu (Duo Mode):** DeepSeek Bridge Reasoning Engine (`deepseek-v4-pro`)  
**Người thẩm định phương pháp độc lập:** Thành viên B (Phùng Tấn Minh — QA Lead & Nhóm trưởng)  
**Thẩm quyền phê duyệt tối hậu:** Lead D (Nguyễn Anh Tuấn)  
**Trạng thái quản trị:** `DRAFT_V3.4_PENDING_B_APPRAISAL_AND_LEAD_D_FINAL_DECISION` (Bản kế hoạch vận hành hợp nhất hoàn thiện — Tiếp thu đầy đủ 4 chỉ đạo vòng 7 của Lead D ngày 12/11/2026 và kết quả tham vấn mô hình Duo để chuyển B thẩm định độc lập; duy trì nghiêm ngặt `training_blocked=true`, `official_test_used=false`, chưa trích xuất mẫu hay mở Pass 1)  

---

## BẢNG TỔNG HỢP BÀN GIAO KẾ HOẠCH HỢP NHẤT (CHUẨN ARS 5 CỘT)

| # | Yêu cầu của Lead D & QA Lead B | Mục tài liệu đáp ứng | Bằng chứng & Kiểm thử hiện có | Phần còn phải triển khai | Người chịu trách nhiệm |
|:---:|:---|:---|:---|:---|:---:|
| **1** | Khôi phục thiết kế Đợt 1 (100 mẫu; pre-locked seeds, tiêu chí chọn, dedupe 4 lớp, SimHash $\le 10$, Jaccard $\ge 0,85$; đăng ký tuần tự `TemplateSimilarityEngine`; ma trận nhãn $3 \times 3$ Codebook v1.1; CI 95% bằng Paired Bootstrap chặt chẽ kèm ví dụ đối chiếu, bỏ công thức Fleiss nhị phân; xử lý vùng ranh giới $0,60 \le \kappa < 0,75$; ghi rõ giới hạn khi $N=30$). | **Mục 2** (Thiết kế chi tiết Đợt 1) | Mã nguồn `TemplateSimilarityEngine` tại `src/phishing/data/template_similarity.py` (dòng 96–97) đã có sẵn ngưỡng Hamming $\le 10$, Jaccard $\ge 0,85$. | Viết script tuyển chọn `scripts/data/sample_batch1.py` đăng ký tuần tự từng mẫu vào engine; nạp seed đã khóa; quét trùng lặp và xuất manifest. | Thành viên C (lập trình) & QA Lead B (kiểm định) |
| **2** | Chốt duy nhất tên trường `blind_contract_version = "1.2.0"`; giữ `codebook_version = "1.1.0"`; Main thiếu/sai version phải fail-closed; Tách allowlist theo LOẠI ARTIFACT (`LOCKED_LEGACY_BLIND_VIEW_ALLOWLIST`, `MANIFEST`, `MAPPING`), hash manifest/mapping không được làm vé nạp BlindSample; hash chưa đo ghi `CHƯA XÁC MINH`; đường nạp legacy tự tính hash trên raw bytes; cấm `random_subset` trong view/record của B. | **Mục 3** (Hợp đồng dữ liệu Blind View v1.2) | Bộ test hồi quy v1.1.0 hiện có (`tests/test_blind_view.py`) xác nhận schema v1.1.0 an toàn và không rò rỉ nhãn. Mã băm thực tế của các tệp Calibration cũ đã đo đạc vật lý trên đĩa. | Cập nhật validator và parser trong `blind_view.py` và `annotate_cli.py` phân nhánh theo `blind_contract_version`, đường nạp legacy tự băm raw bytes đối chiếu allowlist hash; cập nhật `AnnotationRecord`. | Thành viên C (triển khai) & QA Lead B (thẩm định) |
| **3** | Khóa 30% ngẫu nhiên trước Pass 1, niêm phong seed trong hồ sơ hạn chế ngoài Git; dùng Blind ID trung tính không mã hóa lô (`BLIND-xxxxxxxx`); phép kiểm giới hạn (bounded check) chống suy đoán; công thức hợp mẫu Blended Delivery $|S_{\text{random}} \cup S_{\text{hard}}|$ trừ phần giao (70 mẫu là dự phóng giả định); 15 Mẫu mồi Decoy niêm phong loại trừ TRƯỚC KHI phát cho B; mã lô TBD; phân tích hệ quả PA hấp thụ (QA B giảm 15h xuống 13,96h) vs PA tăng ngân sách. | **Mục 4** (Bảo vệ tính mù & Trộn đệm ngẫu nhiên) | Phép tính Cohen's Kappa trong `src/phishing/annotation/__init__.py` đã hỗ trợ lọc theo mảng boolean độc lập. | Lập trình module `blended_delivery.py` thực hiện sinh Blind ID ngẫu nhiên, Hash Shuffle và cập nhật `evaluate_kappa.py` thực hiện phép Join độc lập sau khi khóa Pass 1. | Thành viên C (thực hiện) & QA Lead B (kiểm tra mù) |
| **4** | Sửa Bảng 5.1 theo từng lô thực tế: Lô 1 (20 mẫu, thiếu hash trên registry), Lô 2 (32 mẫu), Lô 3+4 (64 mẫu), Lô 5–10 (130 mẫu, tổng 246 mẫu); đối chiếu trạng thái mapping và khả năng chặn từng lô; cách ly 2 shard đã biết `train-000`, `train-055`; lập phương án rủi ro tồn dư xin Lead D phê duyệt riêng. PhishVN là nguồn đề xuất thứ cấp. | **Mục 5** (Hiện trạng Lô loại trừ & Quản trị Shard) | Sổ bộ `data/exclusion_registry.json` xác nhận chi tiết từng lô; `recovery_status.json` ghi nhận trạng thái `pending_independent_review` cho Lô 1 và Lô 2. | Tổ chức phiên nghiệm thu độc lập mapping Lô 1; nếu chưa xong, trình Lead D ký duyệt văn bản chấp nhận rủi ro tồn dư trước khi trích xuất. | Thành viên C (hồ sơ) & Lead D (phê duyệt) |
| **5** | Quy trình vận hành khép kín (View $\rightarrow$ MarianMT `zh/ja/ru` $\rightarrow$ SHA256SUMS $\rightarrow$ QA B $\rightarrow$ Duyệt D); ghi rõ revision `ja-en` và `ru-en` đã kiểm trong codebase, đánh dấu `zh-en` cần khóa revision trước khi chạy; bổ sung kiểm dịch và xử lý thiếu model (fail-closed); tách bạch khả năng kỹ thuật (cold/warm cache) vs kết quả thực chứng log; xác nhận kết quả 137 passed / 13 skipped của B là ở commit cũ `bc295820` (V3.0), không phải V3.3/V3.4. | **Mục 6** (Quy trình vận hành & Dịch ngoại tuyến) & **Mục 8** (Ranh giới kiểm thử) | Revision `ja-en` (`0770961...`) và `ru-en` (`fbd6dc7...`) đã có trong codebase; chạy kiểm thử độc lập của B trên commit cũ V3.0 (`bc295820`) đạt 137 passed / 13 skipped; máy C có đủ tệp đạt 150 passed. | Tải và khóa revision commit SHA cho `zh-en`; viết module translation sanity check và xử lý fail-closed; viết mới bộ test cho Main v1.2 sau khi Lead D duyệt kế hoạch (hiện ở trạng thái CHƯA KIỂM CHỨNG). | Thành viên C (viết test) & QA Lead B (chạy kiểm chứng) |
| **6** | Không đưa tỷ lệ nhãn nguồn 50/50 hoặc phân bổ tổ chức theo nhãn vào tài liệu/gói B xem trước Pass 1; phân định rạch ròi số giả định vs số thực đo; tính lại giờ Đợt 1 (20,66h, không tính ca khó chuyển Đợt 2), Đợt 2 và toàn chiến dịch (hạch toán 1,04h mẫu che trộn decoy); giữ 192,32h hoặc 193,36h là đề xuất mới chờ D duyệt, chưa thay PLAN-01 đã duyệt (190,79h); giữ tiến độ toàn chiến dịch TBD. | **Mục 7** (Dự phóng định lượng & Bảng đối chiếu giờ công) | Dữ liệu đo đạc thực nghiệm Pass 1 của A (`intake_pass1_A_1c60d10a.jsonl`, mean 380,16s, median 335,62s) và B (mean 250,36s). | Trình Lead D xem xét phê duyệt bảng giờ Đợt 1 và điều chỉnh biên độ ngân sách trong một lượt quyết định. | Thành viên C (tính toán) & Lead D (phê duyệt) |

---

## 1. MỤC TIÊU, NGUYÊN TẮC VẬN HÀNH VÀ CAM KẾT CHỐNG RÒ RỈ

1. **Mục tiêu tối hậu:** Thiết lập quy trình vận hành gán nhãn khoa học, minh bạch và chặt chẽ nhằm xây dựng tập dữ liệu đánh giá 1.000 mẫu website phishing và benign có độ tin cậy cao, phục vụ công bố khoa học chuẩn quốc tế.
2. **Nguyên tắc học thuật bất biến (Academic Research Skills - ARS):**
   - *Tính mù kép (Double-Blind Annotation):* Cả hai chuyên viên gán nhãn (Annotator A và Annotator B) hoạt động độc lập, không nhìn thấy nhãn nguồn, không nhìn thấy locator, không nhìn thấy cơ cấu phân bổ nhãn/tổ chức và không nhìn thấy kết quả của nhau trong suốt Pass 1.
   - *Bảo vệ mẫu số Cohen's Kappa:* Chỉ số thỏa thuận liên đánh giá viên ($\kappa$) phải được tính toán trên một tập mẫu số ngẫu nhiên đại diện khách quan, độc lập với các ca khó bổ sung.
   - *Chống rò rỉ dữ liệu (Anti-Leakage Protocols):* Mọi mẫu hiệu chuẩn, pilot và sự cố lịch sử (246 mục trong `data/exclusion_registry.json`) được cách ly khỏi tập dữ liệu thực nghiệm chính thức.
3. **Các chốt chặn an toàn được duy trì nghiêm ngặt:**
   - `training_blocked = true` (Chặn nạp dữ liệu gán nhãn vào pipeline huấn luyện mô hình khi chưa hoàn tất phân xử Pass 2).
   - `official_test_used = false` (Cô lập nghiêm ngặt tập kiểm thử chính thức, không sử dụng cho bất kỳ đợt phát triển hay hiệu chuẩn nào).
   - `main_annotation_status = "LOCKED"` (Chiến dịch gán nhãn chính tiếp tục khóa chặt; chưa chọn mẫu, chưa tạo Blind View, chưa cấp phát tài nguyên cho đến khi Lead D ban hành quyết định phê duyệt chính thức).

---

## 2. THIẾT KẾ VẬN HÀNH CHI TIẾT ĐỢT 1 (BATCH 1 OPERATIONAL DESIGN)

### 2.1 Ma trận so sánh định lượng 4 kịch bản Đợt 1 (Phân định Số thực đo vs Số giả định)

Bảng phân tích so sánh toàn diện 4 phương án thiết kế Đợt 1 nhằm cung cấp đầy đủ căn cứ định lượng về nguồn lực để Lead D quyết định (lưu ý: giờ hoàn tất Đợt 1 của B chỉ tính trên 30 mẫu ngẫu nhiên mà B thực sự gán trong Đợt 1; ~15 ca khó phát sinh từ Đợt 1 được tích lũy chuyển sang Đợt 2 theo đúng cơ chế Blended Delivery):

| Tiêu chí kỹ thuật & Quản trị | Phương án A1: Lô đầu Main (60 mẫu) | Phương án A2: Lô đầu Main (100 mẫu) | Phương án B1: Pilot Tách riêng (60 mẫu) | Phương án B2: Pilot Tách riêng (100 mẫu) | Loại số liệu (Data Type) |
|:---|:---:|:---:|:---:|:---:|:---:|
| **Bản chất dữ liệu** | Lô 1 chính thức của Main Corpus. | **Lô 1 chính thức của Main Corpus.** | Lô Pilot thử nghiệm công cụ tách riêng. | Lô Pilot thử nghiệm công cụ tách riêng. | Quy chuẩn quản trị |
| **Hệ quả Loại trừ (Exclusion Registry)** | Giữ lại làm Train/Val/Test chính thức. | **Giữ lại làm Train/Val/Test chính thức.** | Bị loại trừ vĩnh viễn (thành Lô 11). | Bị loại trừ vĩnh viễn (thành Lô 11). | Quy chuẩn quản trị |
| **Đóng góp vào mục tiêu 1.000 mẫu** | Đóng góp 60 mẫu (còn lại 940 mẫu). | **Đóng góp 100 mẫu (còn lại 900 mẫu).** | Đóng góp 0 mẫu (phải gán đủ 1.000 mẫu mới). | Đóng góp 0 mẫu (phải gán đủ 1.000 mẫu mới). | Quy chuẩn quản trị |
| **Thời gian A gán Pass 1 (thực đo 6,34m)** | $60 \times 6,34\text{m} = \mathbf{6,34\text{ giờ}}$ | $100 \times 6,34\text{m} = \mathbf{10,57\text{ giờ}}$ | $60 \times 6,34\text{m} = \mathbf{6,34\text{ giờ}}$ | $100 \times 6,34\text{m} = \mathbf{10,57\text{ giờ}}$ | **Số thực đo** (từ 380,16s/mẫu) |
| **Thời gian B gán Pass 1 Đợt 1 (thực đo 4,17m)** | 18 mẫu ngẫu nhiên: $\mathbf{1,25\text{ giờ}}$ | **30 mẫu ngẫu nhiên: $\mathbf{2,09\text{ giờ}}$** | 18 mẫu ngẫu nhiên: $\mathbf{1,25\text{ giờ}}$ | 30 mẫu ngẫu nhiên: $\mathbf{2,09\text{ giờ}}$ | **Số thực đo** (từ 250,36s/mẫu) |
| **Số ca khó chuyển giao sang Đợt 2** | ~9 ca khó chuyển Đợt 2 (chưa gán ở Đợt 1) | **~15 ca khó chuyển Đợt 2 (chưa gán ở Đợt 1)** | ~9 ca khó chuyển Đợt 2 | ~15 ca khó chuyển Đợt 2 | **Số giả định** (~15% tỷ lệ khó) |
| **Công sức kiểm định QA của B tại Đợt 1** | 2,50 giờ (schema, view, audit) | **3,00 giờ (schema, view, audit)** | 2,50 giờ | 3,00 giờ | Định mức quản lý |
| **Công sức của Thành viên C tại Đợt 1** | 3,00 giờ (pipeline, MarianMT, Kappa) | **3,50 giờ (pipeline, MarianMT, Kappa)** | 3,00 giờ | 3,50 giờ | Định mức kỹ thuật |
| **Công sức của Lead D tại Đợt 1** | 1,00 giờ (phân xử Pass 2, duyệt cổng) | **1,50 giờ (phân xử Pass 2, duyệt cổng)** | 1,00 giờ | 1,50 giờ | Định mức chủ trì |
| **Tổng giờ thực tế hoàn tất Đợt 1** | **14,09 giờ** | **20,66 giờ** | **14,09 giờ** (lãng phí ngoài PLAN-01) | **20,66 giờ** (lãng phí ngoài PLAN-01) | **Tổng hợp quản trị** |
| **Đánh giá quy mô mẫu đối soát Kappa** | Cỡ mẫu $N=18$ có phương sai lớn. | **Cỡ mẫu $N=30$ đề xuất (báo cáo kèm CI 95%).** | Cỡ mẫu $N=18$ có phương sai lớn. | Cỡ mẫu $N=30$ đề xuất (báo cáo kèm CI 95%). | Phân tích phương pháp |
| **Đánh giá tính khả thi trong 1 tuần** | Khả thi cao (~14,1h phân bổ 4 người). | **Khả thi cao (~20,66h phân bổ 4 người).** | Khả thi nhưng lãng phí nguồn lực. | Khả thi nhưng lãng phí nguồn lực. | Đánh giá điều kiện |

> [!TIP]
> **Khuyến nghị đề xuất của Thành viên C:** Thành viên C kính đề xuất Lead D lựa chọn **Phương án A2 (Lô đầu của Main Annotation — Quy mô 100 mẫu)**.  
> *Lý do:* Quy mô 100 mẫu cung cấp $N_{\text{random}} = 30$ mẫu gán kép cho B ở Đợt 1, cho phép tính toán Cohen's Kappa ma trận $3 \times 3$ kèm khoảng bất định (CI 95%) để Lead D xem xét; tổng quỹ thời gian thực tế toàn nhóm để hoàn tất Đợt 1 là **20,66 giờ** (khả thi trong 1 tuần với nhóm 4 người); đồng thời 100 mẫu này đóng góp trực tiếp vào mục tiêu 1.000 mẫu, không gây lãng phí công sức làm thêm lô loại trừ mới.

### 2.2 Nguồn dữ liệu, Tiêu chí chọn mẫu & Bảo mật Phân tầng

1. **Nguồn dữ liệu hợp lệ duy nhất:** Trích xuất độc quyền từ nguồn `phreshphish` tại revision `eabec4b7a66324b79cc8a0ad856d1731dc26fe1a` (56 shards trong `configs/source_manifest.json`). Tuyệt đối không trích xuất từ PhishVN hoặc các nguồn chưa duyệt.
2. **Tiêu chí lọc thời gian (Temporal Window):** Chỉ lấy các bản ghi có ngày thu thập nằm trong dải đã kiểm toán: từ `2024-10-01` đến `2025-09-08`.
3. **Cơ chế Hạt giống ngẫu nhiên & Niêm phong Hồ sơ Hạn chế:**
   - *Hạt giống trích xuất ứng viên:* Sử dụng `random_seed_batch1_select` đã xác định trong kế hoạch nội bộ để rút tập ứng viên ngẫu nhiên từ các shard được phép khai thác.
   - *Bảo mật hạt giống và bảng ánh xạ:* Nhằm bảo vệ tính mù và ngăn ngừa việc Annotator B có thể suy đoán nhãn hoặc thứ tự hiển thị, các hạt giống phân tầng (`random_seed_random30`), hạt giống xáo trộn (`random_seed_hash_shuffle`) và bảng ánh xạ **ĐƯỢC NIÊM PHONG TRONG HỒ SƠ PHÂN TẦNG HẠN CHẾ NGOÀI GIT** (`data/restricted/batch1_sampling_manifest.json`). Thành viên C chỉ công bố mã băm SHA-256 seal của tệp manifest này trước khi mở phiên Pass 1. Toàn bộ các giá trị hạt giống chỉ được mở niêm phong công khai sau khi cả A và B đã nộp và khóa mã băm bản ghi Pass 1.
4. **Bảo mật Cơ cấu Phân tầng Nguồn (Zero Label/Org Structure Leak to Annotator B):**
   - **Tuyệt đối không đưa tỷ lệ nhãn nguồn dự kiến (ví dụ 50/50) hoặc phân bổ tổ chức mục tiêu theo nhãn vào tài liệu hay gói dữ liệu mà Annotator B có thể xem trước Pass 1.**
   - Thông tin về tỷ lệ nhãn nguồn, danh sách tổ chức và ma trận phân bổ được lưu trữ độc quyền trong hồ sơ hạn chế của C và D (`data/restricted/batch1_sampling_manifest.json`).
   - Tài liệu bàn giao và báo cáo QA gửi cho Annotator B chỉ chứa các thông số kỹ thuật thuần túy: tổng số lượng mẫu, mã băm SHA-256 tệp Blind View, kết quả kiểm thử schema Hợp đồng v1.2, và biên bản kiểm tra zero-label-leak.

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

### 2.4 Tiêu chí ĐẠT, Tiêu chí DỪNG & Báo cáo Cohen's Kappa Ma trận $3 \times 3$

1. **Cơ chế phân phối và nghiệm thu Đợt 1:**
   - Trong Đợt 1 ($N=100$), Annotator A hoàn thành gán nhãn Pass 1 trên toàn bộ 100 mẫu.
   - Annotator B nhận gói dữ liệu Đợt 1 gồm đúng $N_{\text{random}} = 30$ mẫu ngẫu nhiên độc lập ($S_{\text{random30}}^{(1)}$) được phân tầng từ bảng niêm phong. Vì đây là đợt khởi đầu chiến dịch, bể ca khó tích lũy từ các đợt trước bằng rỗng ($S_{\text{hard\_accumulated}}^{(0)} = \emptyset$). Do đó, ở Đợt 1, gói giao cho B gồm đúng 30 mẫu ngẫu nhiên.
   - Các ca khó do Annotator A phát hiện trong 100 mẫu của Đợt 1 ($S_{\text{hard}}^{(1)}$, ước tính ~15 mẫu) được chuyển vào Bể ca khó tích lũy và sẽ được gộp phát cho B ở Đợt 2 theo công thức hợp mẫu tại Mục 4.2.
2. **Quy định Báo cáo Cohen's Kappa Ma trận $3 \times 3$ theo Codebook v1.1:**
   - Nhãn gán của Codebook v1.1 bao gồm đúng 3 danh mục chính thức: `phishing`, `benign`, và `insufficient_evidence`.
   - Báo cáo đồng thuận Đợt 1 bắt buộc sử dụng **Ma trận nhãn $3 \times 3$** làm phép đánh giá chính thức (không dùng ma trận $2 \times 2$ khi chưa có quyết định phê duyệt riêng của Lead D):
     $$\begin{pmatrix} n_{11} & n_{12} & n_{13} \\ n_{21} & n_{22} & n_{23} \\ n_{31} & n_{32} & n_{33} \end{pmatrix}$$
     *(Hàng: Annotator A; Cột: Annotator B; Thứ tự nhãn: 1 = Phishing, 2 = Benign, 3 = Insufficient Evidence).*
   - **Công thức tính Cohen's Kappa đa lớp không trọng số (Unweighted Multi-class Cohen's Kappa):**
     $$p_o = \frac{1}{N} \sum_{i=1}^3 n_{ii}, \quad p_e = \frac{1}{N^2} \sum_{i=1}^3 n_{i\cdot} n_{\cdot i}, \quad \kappa = \frac{p_o - p_e}{1 - p_e}$$
   - **Xử lý nhãn `insufficient_evidence`:** Nhãn `insufficient_evidence` được coi là một trạng thái phân loại hợp lệ thứ ba để phản ánh trung thực mức độ đồng thuận khi website bị lỗi crawl hoặc thiếu bằng chứng.
   - **Khoảng bất định (Confidence Interval 95%):** Báo cáo tính toán khoảng tin cậy $\text{CI}_{95\%}$ bằng phương pháp Bootstrap (1.000 lượt resample có hoàn lại trên 30 cặp nhãn) hoặc công thức xấp xỉ phương sai Fleiss:
     $$\text{SE}(\kappa) = \sqrt{\frac{p_o(1 - p_o)}{N(1 - p_e)^2}}, \quad \text{CI}_{95\%} = [\kappa - 1,96 \times \text{SE}(\kappa), \ \kappa + 1,96 \times \text{SE}(\kappa)]$$
   - *(Lưu ý: Bất kỳ phép rút gọn ma trận sang $2 \times 2$ bằng cách loại bỏ hoặc gộp `insufficient_evidence` chỉ được coi là phân tích khám phá phụ và bắt buộc phải có văn bản chỉ đạo riêng của Lead D).*
3. **Quy chế Xử lý 3 Vùng Đồng thuận (Phân biệt Ngưỡng Đề xuất vs Ngưỡng Phê duyệt):**
   - *Vùng Đạt chuẩn ($\kappa_{\text{random}} \ge \mathbf{0,75}$ - Ngưỡng đề xuất):* Đủ điều kiện kỹ thuật để Lead D xem xét ký biên bản nghiệm thu Đợt 1 và cho phép mở rộng sang Đợt 2.
   - *Vùng Rà soát Có Điều kiện ($0,60 \le \kappa_{\text{random}} < 0,75$):* 
     * Hệ thống **KHÔNG tự động dừng khẩn cấp** nhưng **TUYỆT ĐỐI KHÔNG tự động mở rộng sang Đợt 2**.
     * Tự động kích hoạt phiên họp kỹ thuật đặc biệt giữa Lead D, QA Lead B và Thành viên C: rà soát từng ca bất đồng trong ma trận nhãn $3 \times 3$. Nếu bất đồng do chất lượng crawl snapshot (lỗi hiển thị, thiếu CSS/ảnh), C cải tiến pipeline; nếu bất đồng do độ rõ ràng của tiêu chí nhận diện trong Codebook v1.1, nhóm tiến hành hiệu chỉnh tài liệu hướng dẫn.
     * Quyết định cuối cùng thuộc thẩm quyền của Lead D: Lead D quyết định cho phép phát hành Đợt 2 có giám sát tăng cường hoặc yêu cầu bổ sung mẫu gán kép trước khi mở rộng.
   - *Vùng Dừng Khẩn cấp ($\kappa_{\text{random}} < \mathbf{0,60}$):* Tạm dừng toàn bộ chiến dịch; rà soát lại toàn diện Codebook v1.1 và năng lực nhận diện của annotator.
4. **Tiêu chí Dừng về Chất lượng Snapshot & An toàn:**
   - Nếu tỷ lệ `insufficient_evidence` $> \mathbf{5,0\%}$ (quá 5 mẫu trên 100 mẫu), kích hoạt quy trình dừng an toàn để rà soát chất lượng snapshot HTML và tiêu chí crawl nguồn. **TUYỆT ĐỐI NGHIÊM CẤM TẠO ÁP LỰC ÉP NGƯỜI GÁN PHẢI CHUYỂN ĐỔI NHÃN SANG PHISHING HOẶC BENIGN**.
   - Nếu phát hiện bất kỳ sự cố rò rỉ nào về nhãn nguồn, locator hay cờ phân tầng đối với Annotator B, hủy bỏ đợt gán nhãn và cô lập dữ liệu.
   - *Đối chiếu `docs/DATA_PROTOCOL.md`:* Toàn bộ quy tắc về tỷ lệ gán kép 30%, tính Kappa trước phân xử trên tập ngẫu nhiên, không đưa ca khó thêm vào mẫu số Kappa, và giữ nguyên lượt gán gốc tuân thủ nghiêm ngặt Mục "Gán nhãn mù" (dòng 45–58) của `DATA_PROTOCOL.md`.

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
     `sample_id` (được gắn mã Blind ID trung tính `BLIND-xxxxxxxx`), `url`, `page_text`, `structure_summary`, `codebook_version` (`"1.1.0"`), `blind_contract_version` (`"1.2.0"`), `translation_provided`, `translated_text`, `translation_source_language`, `translation_tool`, `translation_tool_version`, `translation_sha256`.
2. **Schema Bản ghi Gán nhãn Pass 1 (`AnnotationRecord`):**
   - Bản ghi xuất ra từ CLI (`intake_pass1_A.jsonl`, `intake_pass1_B.jsonl`) **LOẠI BỎ HOÀN TOÀN TRƯỜNG `random_subset`**.
   - Khớp đúng 100% các trường chuẩn hóa theo mã nguồn `src/phishing/annotation/blind_view.py` (dòng 540–601) và `src/phishing/annotation/__init__.py`:
     * *Định danh & tiến trình:* `annotator_id`, `sample_id` (mã Blind ID trung tính), `pass_id`, `seconds_spent`, `pause_count`, `paused_seconds`, `timestamp_utc`.
     * *Phán đoán phân loại (Codebook v1.1):* `class_label`, `primary_org_status`, `catalog_status`, `observed_service`, `org_targets`, `primary_org`, `identity_role`, `domain_role`, `evidence_note`, `difficult_case`, `confidence`, `primary_phishing_type`, `hard_benign_type`.
     * *Bằng chứng trích dẫn:* `org_evidence` (danh sách các đối tượng trích dẫn từ view).
     * *Kiểm soát phiên bản:* `codebook_version` (`"1.1.0"`), `blind_contract_version` (`"1.2.0"`).
     * *Nguồn gốc kiểm toán phục vụ `compute_cohens_kappa`:* `dataset_id`, `dataset_hash`, `codebook_hash`, `sampling_plan_version`, `sample_content_hash`, `is_dry_run`, `is_synthetic`.
   - Bảo toàn tính trung thực học thuật: Tuyệt đối không lưu trữ cờ `random_subset: true` giả vào kết quả của các ca khó bổ sung.

### 3.3 Quy tắc Phiên bản Nhất quán, Mã băm Thực đo & Preflight Tự tính Hash (Fail-Closed Rejection)

Nhằm đảm bảo tính an toàn nghiêm ngặt và không suy diễn tùy tiện:
1. **Tách Allowlist Theo Từng Loại Artifact & Loại Trừ Các Mã Chưa Xác Minh:**
   Tiếp thu chỉ đạo kiểm soát rủi ro của Lead D, **tuyệt đối không dùng chung một danh sách hash hỗn hợp**. Mã băm của manifest hoặc hồ sơ ánh xạ hạn chế không bao giờ được dùng làm 'giấy phép' để nạp chúng thành BlindSample. Hệ thống phân tách thành các allowlist chuyên biệt:

   - **A. `LOCKED_LEGACY_BLIND_VIEW_ALLOWLIST` (Chỉ dùng cho đường nạp Blind View chạy thật):**
     * `0164b2a5499c10c824f7e559c9a351c958adcfe627648ac537179dfe4dbf2b6b`: Gói Blind View sạch Đợt C (`data/annotations/clean_calibration_blind_view_24.json`, dung lượng $154.350\text{ bytes}$, $24\text{ mẫu}$).
     * *Ràng buộc kiểm toán:* Bắt buộc xác minh $100\%$ cấu trúc JSON có mảng `samples` đúng schema `BlindSample`, trường `dataset_id == "CALIBRATION-CLEAN-24"` và tệp liên kết với manifest release `v1.1.4`. Chỉ các tệp khớp allowlist này mới được giải mã thành mẫu gán nhãn cho annotator.

   - **B. `LOCKED_LEGACY_MANIFEST_ALLOWLIST` (Chỉ dùng kiểm tra tính toàn vẹn của Manifest phát hành):**
     * `9f3772b1583c39ca4646483dbeeecc7591813dd2a8ea063fd2c6c13bd5a7b1f3`: Tệp phát hành chính thức Calibration v1.1.4 (`configs/calibration_manifest_v1_1_4_release.json`, dung lượng $1.965\text{ bytes}$, `manifest_id = CALIBRATION-V1.1.4-RELEASE-RUNWAY-20261012`).
     * *Cấm tuyệt đối:* Hash này **KHÔNG BAO GIỜ** được chấp nhận trong đường nạp mẫu gán nhãn `BlindSample`.

   - **C. `LOCKED_LEGACY_RESTRICTED_MAPPING_ALLOWLIST` (Chỉ dùng kiểm toán niêm phong ngoài Git):**
     * `67326e80b2a6f9cb7356450a31fe15054a1193412a8ed0576ea2972f1801a805`: Hồ sơ niêm phong hạn chế 32 mẫu sạch (`data/restricted/clean_calibration_exclusion_mapping_c_32.json`, dung lượng $21.488\text{ bytes}$).
     * *Cấm tuyệt đối:* Tệp này chứa locator và nhãn thật, **NGHIÊM CẤM** nạp vào bất kỳ giao diện Blind View nào.

   - **D. Danh mục Hash Manifest Lịch sử Chưa Đo Đạc Trực tiếp (`CHƯA XÁC MINH`):**
     * `c7244a9e7a28...`: Calibration v1.1.3 release manifest (`CHƯA XÁC MINH TRÊN ĐĨA KIỂM TOÁN`)
     * `f3f497e6300a...`: Calibration v1.1.2 release manifest (`CHƯA XÁC MINH TRÊN ĐĨA KIỂM TOÁN`)
     * `00295b7d160e...`: Calibration v1.1.1 release manifest (`CHƯA XÁC MINH TRÊN ĐĨA KIỂM TOÁN`)
     * `4c2407158913...`: Calibration v1.1.0 release manifest (`CHƯA XÁC MINH TRÊN ĐĨA KIỂM TOÁN`)
     * *Chính sách loại trừ:* Toàn bộ các hash chưa có tệp vật lý đo đạc đối chiếu trực tiếp đều bị **LOẠI BỎ HOÀN TOÀN KHỎI ALLOWLIST RUNTIME THẬT**. Bộ nạp ở runtime tuyệt đối từ chối các hash này.

2. **Cơ chế Preflight tự tính hash trên raw bytes và phân loại Artifact:**
   Bộ nạp và kiểm tra tính hợp lệ (`Validator` và `annotate_cli.py`) **TỰ ĐỘNG TÍNH TOÁN SHA-256 TRỰC TIẾP TRÊN TOÀN BỘ BYTE VẬT LÝ CỦA TỆP ĐẦU VÀO**, đối soát nghiêm ngặt theo đúng loại artifact:

```python
import hashlib, json
from pathlib import Path

# Allowlist phân loại theo đúng loại artifact đã đo đạc vật lý trên đĩa
LOCKED_LEGACY_BLIND_VIEW_ALLOWLIST = {
    # clean_calibration_blind_view_24.json (154.350 bytes, dataset_id = "CALIBRATION-CLEAN-24")
    "0164b2a5499c10c824f7e559c9a351c958adcfe627648ac537179dfe4dbf2b6b",
}

LOCKED_LEGACY_NON_SAMPLE_HASHES = {
    # calibration_manifest_v1_1_4_release.json (manifest, CẤM nạp thành sample)
    "9f3772b1583c39ca4646483dbeeecc7591813dd2a8ea063fd2c6c13bd5a7b1f3",
    # clean_calibration_exclusion_mapping_c_32.json (mapping hạn chế, CẤM nạp thành sample)
    "67326e80b2a6f9cb7356450a31fe15054a1193412a8ed0576ea2972f1801a805",
}

def preflight_validate_and_load_package(package_path: Path) -> dict:
    """Kiểm tra toàn vẹn tự động trước khi nạp dữ liệu (Preflight Verification)."""
    raw_bytes = package_path.read_bytes()
    computed_file_sha256 = hashlib.sha256(raw_bytes).hexdigest()
    
    try:
        package_dict = json.loads(raw_bytes.decode("utf-8"))
    except Exception as e:
        raise ValueError(f"LỖI TỆP (FAIL-CLOSED): Tệp không phải JSON hợp lệ: {e}")
        
    contract_ver = package_dict.get("blind_contract_version")
    
    # 1. ĐỊNH TUYẾN MAIN ANNOTATION (HỢP ĐỒNG V1.2 BẮT BUỘC)
    if contract_ver == "1.2.0":
        if "random_subset" in package_dict:
            raise ValueError("LỖI BẢO MẬT HỢP ĐỒNG V1.2: Cấm đưa trường random_subset vào Blind View của Main!")
        if package_dict.get("codebook_version") != "1.1.0":
            raise ValueError("LỖI CODEBOOK: Main Annotation bắt buộc dùng codebook_version='1.1.0' đã khóa!")
        if "samples" not in package_dict or not isinstance(package_dict["samples"], list):
            raise ValueError("LỖI CẤU TRÚC: Gói Blind View Main v1.2 thiếu mảng 'samples' hợp lệ!")
        return {"mode": "MAIN_V12", "data": package_dict, "file_sha256": computed_file_sha256}
        
    # 2. ĐỊNH TUYẾN CALIBRATION CŨ (CHỈ CHẤP NHẬN GÓI BLIND VIEW ĐÃ XÁC MINH TRONG ALLOWLIST RIÊNG)
    elif contract_ver is None or contract_ver == "1.1.0":
        if computed_file_sha256 in LOCKED_LEGACY_NON_SAMPLE_HASHES:
            raise ValueError(
                f"TỪ CHỐI AN TOÀN (FAIL-CLOSED): Tệp có mã băm '{computed_file_sha256}' là artifact loại "
                "MANIFEST hoặc MAPPING hạn chế, CẤM TUYỆT ĐỐI không được nạp thành Blind View mẫu gán nhãn!"
            )
        if computed_file_sha256 not in LOCKED_LEGACY_BLIND_VIEW_ALLOWLIST:
            raise ValueError(
                f"TỪ CHỐI AN TOÀN (FAIL-CLOSED): Tệp thiếu blind_contract_version và có mã băm thực đo "
                f"'{computed_file_sha256}' không thuộc LOCKED_LEGACY_BLIND_VIEW_ALLOWLIST đã được phê duyệt! "
                "Nghiêm cấm mặc định mọi tệp thiếu trường là Calibration."
            )
        # Xác minh cấu trúc schema BlindSample của Calibration
        if "samples" not in package_dict or package_dict.get("dataset_id") != "CALIBRATION-CLEAN-24":
            raise ValueError("LỖI CẤU TRÚC: Tệp không đúng định dạng Blind View Calibration đã phê duyệt!")
        return {"mode": "LEGACY_CALIBRATION_V11", "data": package_dict, "file_sha256": computed_file_sha256}
        
    # 3. MỌI TRƯỜNG HỢP SAI PHIÊN BẢN HOẶC THIẾU CĂN CỨ: TỪ CHỐI AN TOÀN
    else:
        raise ValueError(f"TỪ CHỐI AN TOÀN (FAIL-CLOSED): Phiên bản hợp đồng '{contract_ver}' không hợp lệ!")
```

---

## 4. CƠ CHẾ BẢO VỆ TÍNH MÙ & GIẢI PHÁP PHÂN PHỐI TRỘN ĐỆM NGẪU NHIÊN (BLENDED DELIVERY)

### 4.1 Khóa tập ngẫu nhiên 30%, Blind ID Trung tính & Phép kiểm Giới hạn Bounded Check

1. **Kiến trúc Blind ID Trung tính không mã hóa lô:**
   - Toàn bộ mẫu phát hành cho Annotator B được gán mã định danh ngẫu nhiên trung tính không mang thông tin phân tầng hay thứ tự lô:
     $$\text{blind\_id} = \text{"BLIND-"} + \text{SHA-256}(\text{sample\_id} \parallel \text{salt\_secret})[:10]$$
     *(Ví dụ: `BLIND-9f4a1c7e2b`, định dạng đồng nhất cho cả mẫu ngẫu nhiên lẫn ca khó chuyển đợt).*
   - Tên gói dữ liệu giao cho B được chuẩn hóa trung tính theo từng đợt giao nhận cuốn chiếu (ví dụ: `intake_package_batch_01.json`, `intake_package_batch_02.json`), không chứa bất kỳ từ khóa nào về "random" hay "supplemental".
2. **Niêm phong Bảng ánh xạ hạn chế (Restricted Blended Mapping Table):**
   - Bảng đối chiếu giữa `blind_id` với `sample_id` gốc, thông tin phân tầng (`stratum: random_30` vs `supplemental_hard`) và nhãn nguồn được lưu trữ duy nhất trong khu vực hạn chế ngoài Git:
     `data/restricted/main_annotation_sampling_manifest.json`
   - Annotator B hoàn toàn không có quyền truy cập vào tệp này.
3. **Phép kiểm giới hạn chống suy đoán bề mặt (Bounded Anti-Inference Checks):**
   - Đổi tên và xác định đúng bản chất: Đây là **Phép kiểm có giới hạn (Bounded Check)** trên các thuộc tính bề mặt có thể kiểm chứng được bằng thuật toán:
     a) *Kiểm tra định danh (ID Leakage Check):* Xác nhận `sample_id` gốc, mã lô hoặc số thứ tự không xuất hiện trong bất kỳ trường nào của `BlindSample`.
     b) *Kiểm tra siêu dữ liệu (Metadata / Flag Check):* Xác nhận các cờ `random_subset`, `is_random_subset`, `stratum`, `difficulty_case`, `source_label` hoàn toàn vắng mặt.
     c) *Kiểm tra tên gói và thứ tự:* Xác nhận tên gói trung tính và thứ tự hiển thị đã được xáo trộn qua Uniform Hash Shuffle.
   - **Thừa nhận trung thực các giới hạn cố hữu (Inherent Limitations):**
     * *Tín hiệu độ khó tự nhiên trong nội dung trang (`Content-level difficulty signals`):* Nhóm nghiên cứu thừa nhận khoa học rằng **không thể xóa bỏ các tín hiệu độ khó vốn có trong nội dung trang web** (ví dụ: website có kỹ thuật che giấu tinh vi, thương hiệu ít phổ biến, hoặc cấu trúc DOM bất thường). Người gán nhãn giàu kinh nghiệm có thể cảm nhận được độ phức tạp khi trực tiếp đọc trang.
     * *Rủi ro suy đoán từ lịch phát hành:* Khoảng cách thời gian giao nhận giữa các đợt có thể gián tiếp tạo tín hiệu nếu lịch làm việc bị tiết lộ. Nhóm giảm thiểu rủi ro này bằng cách giữ nguyên lịch bàn giao định kỳ và bảo mật tiến độ phân xử của Lead D.
     * Do đó, kế hoạch tuyệt đối không tuyên bố "mù hoàn toàn" hay "mù tuyệt đối".

### 4.2 Giải pháp Phân phối Trộn đệm Ngẫu nhiên (Blended Delivery Union Formula)

```
[Tiến trình của A]          [Đợt 1 của A: 100 mẫu] ────────────────► [Đợt 2 của A: 200 mẫu]
                                   │                                       │
                                   ├───────────────────────┐               │
                                   ▼                       ▼               ▼
                            (30% Rút ngẫu nhiên)     (Phát hiện ca khó)   (30% Rút ngẫu nhiên)
                            S_random30^(1) (30 mẫu)   S_hard^(1) (~15 mẫu)  S_random30^(2) (60 mẫu)
                                   │                       │               │
                                   │                       ▼               │
                                   │             [Trừ phần giao đã gán]    │
                                   │            S_hard^(1) \ S_random30^(1)│
                                   │                 (~10 mẫu khó)         │
                                   │                       │               │
                                   │                       ├───────────────┤
                                   │                       ▼               ▼
[Gói phát hành cho B]     (Đợt 1 cho B: 30 mẫu)   (Đợt 2 cho B: 60 mẫu R_30% + ~10 ca khó Đợt 1)
                                   │                               │
                                   ▼                               ▼
                         [Uniform Hash Shuffle]          [Uniform Hash Shuffle]
                                   │                               │
                                   ▼                               ▼
                         (B nhận 30 mẫu ngẫu nhiên)      (B nhận 70 mẫu xáo trộn trung tính)
                         (Chưa có ca khó tích lũy)       (Dự phóng giả định: 70 mẫu)
```

1. **Công thức Toán học Hợp mẫu Khử trùng lặp (Blended Delivery Set Difference Formula):**
   - Trong Đợt 1 ($N_1=100$), A gán 100 mẫu, phát hiện tập ca khó $S_{\text{hard}}^{(1)}$. B chỉ gán tập ngẫu nhiên $S_{\text{random30}}^{(1)}$ (30 mẫu).
   - Phần giao giữa ca khó và tập ngẫu nhiên Đợt 1 là $S_{\text{overlap}}^{(1)} = S_{\text{hard}}^{(1)} \cap S_{\text{random30}}^{(1)}$ vốn **ĐÃ ĐƯỢC B GÁN Ở ĐỢT 1**.
   - Do đó, số ca khó thực tế cần chuyển sang Đợt 2 chỉ là phần hiệu tập hợp đã khử trùng theo `sample_id`:
     $$S_{\text{hard\_supplemental}}^{(1)} = S_{\text{hard}}^{(1)} \setminus S_{\text{random30}}^{(1)}$$
   - Số mẫu giao thực tế cho B ở Đợt 2 được xác định chính xác theo công thức:
     $$N_B^{(2)} = 60 + |S_{\text{hard}}^{(1)} \setminus S_{\text{random30}}^{(1)}|$$
   - **LƯU Ý QUẢN TRỊ QUAN TRỌNG:** Con số **70 mẫu** được nêu trong tài liệu là **DỰ PHÓNG ƯỚC TÍNH (SỐ GIẢ ĐỊNH)** dựa trên giả định tỷ lệ ca khó là 15% ($15 - 15 \times 0,30 = 10,5 \approx 10\text{ mẫu}$). Số lượng mẫu giao thực tế ở Đợt 2 sẽ được tính toán trực tiếp từ danh sách mẫu đã khóa của Đợt 1 sau khi A hoàn thành Pass 1.
2. **Thuật toán Xáo trộn Băm Đồng nhất (Uniform Hash Shuffle):**
   - Toàn bộ các mẫu trong gói Đợt 2 được gán mã `blind_id` trung tính và xáo trộn ngẫu nhiên dựa trên mã băm mật mã học kết hợp hạt giống niêm phong:
     $$\text{sort\_key}(s) = \text{SHA-256}(\text{blind\_id} \parallel \text{seed\_shuffle})$$
3. **Chốt Tư cách, Niêm phong Loại trừ Trước Phát hành và Quản trị Mã lô 15 Mẫu Mồi (Decoy Samples):**
   - Nhằm giải quyết tình huống ở đợt cuối cùng khi A hoàn tất 1.000 mẫu mà vẫn còn ca khó tồn đọng, nhóm nghiên cứu chốt cơ chế vận hành chuẩn mực:
     * **Tên gọi chuẩn hóa:** **Mẫu che trộn / Mẫu mồi (Masking Decoy Samples)**.
     * **Chuyên viên thực hiện:** **CHỈ Annotator B gán**. Tuyệt đối **KHÔNG gọi đây là kiểm tra độ ổn định liên đánh giá viên** (vì Annotator A không tham gia gán tập này).
     * **Mục đích:** Đóng vai trò lớp vỏ bọc ngẫu nhiên xáo trộn cùng các ca khó cuối kỳ, ngăn ngừa B suy đoán rằng toàn bộ các mẫu trong gói cuối đều là ca khó.
     * **Nguồn và quy mô:** Đúng $N_{\text{decoy}} = 15\text{ mẫu}$ ngẫu nhiên rút từ shard nguồn hợp lệ của chiến dịch, vượt qua kiểm tra trùng 4 lớp và `TemplateSimilarityEngine`.
     * **Quy trình Niêm phong Loại trừ TRƯỚC KHI PHÁT CHO B (Pre-issuance Sealed Exclusion):**
       Tiếp thu chỉ đạo an toàn của Lead D, **Thành viên C bắt buộc khóa danh sách và đăng ký trạng thái loại trừ TRƯỚC KHI phát gói cho B**, tuyệt đối không đợi đến sau Pass 1 mới đăng ký:
       1. C đo đạc mã băm mật mã học (URL SHA-256, Clean HTML SHA-256, Domain Group SHA-256) của 15 mẫu đệm.
       2. Trước khi bàn giao gói Đợt 9 cho B, C cập nhật 15 mã băm này vào `data/exclusion_registry.json` dưới trạng thái `PENDING_DECOY_EXCLUSION` (`split_role = "excluded_decoy"`, `exclusion_scope = "permanent_train_val_test"`). Cơ chế này bảo đảm 15 mẫu này bị chặn đứng hoàn toàn khỏi tập train, validation và official test ngay từ trước khi Pass 1 diễn ra!
       3. Để bảo vệ tính mù tuyệt đối cho B, danh sách `sample_id` và URL gốc được niêm phong riêng trong hồ sơ kiểm toán hạn chế ngoài Git (`data/restricted/decoy_buffer_manifest.json`), B không thể truy cập để biết đâu là mẫu đệm.
     * **Quản trị Mã Lô Loại trừ (Tránh Xung đột với Lô Pilot B1/B2):**
       Vì bảng so sánh tại Mục 2.1 vẫn duy trì Phương án Pilot tách riêng (B1/B2), nếu Lead D chọn Phương án B1/B2 thì lô Pilot đó sẽ chiếm định danh `Lô 11` (`EXCL-PILOT-ISOLATED-60/100`). Do đó, mã lô cho 15 mẫu đệm được quy định ở trạng thái **TBD (Chờ quyết định phê duyệt phương án của Lead D)**:
       - *Nhánh 1 (Nếu Lead D phê duyệt Phương án A2 - Lô đầu Main):* 15 mẫu đệm được đánh mã chính thức là **Lô 11** (`EXCL-MAIN-DECOY-BUFFER-15`).
       - *Nhánh 2 (Nếu Lead D phê duyệt Phương án B1/B2 - Pilot tách riêng):* Lô Pilot tách riêng sẽ là **Lô 11**, và 15 mẫu đệm cuối kỳ sẽ được đánh mã là **Lô 12** (`EXCL-MAIN-DECOY-BUFFER-15`).
     * **Hạch toán Minh bạch Công số của B ($1,04\text{ giờ}$) và Hệ quả Quản trị:** Được phân tích chi tiết tại Mục 7.2.

### 4.3 Phép Join độc lập tính Cohen's Kappa chính thức trước phân xử
Sau khi A và B nộp và khóa mã băm Pass 1, module `evaluate_kappa.py` thực hiện phép kết (Join) độc lập:
$$\text{EvaluationSet} = \text{Record}_A[\text{blind\_id}] \bowtie \text{Record}_B[\text{blind\_id}] \bowtie \text{RestrictedManifest}[\text{blind\_id}]$$
- Chỉ số Cohen's Kappa chính thức trước phân xử ($\kappa_{\text{primary}}$) **CHỈ ĐƯỢC TÍNH TRÊN CÁC MẪU CÓ $\text{is\_random\_subset} == \text{True}$**.
- Các ca khó bổ sung được bóc tách để phân tích thăm dò riêng biệt (Subgroup Agreement), không đưa vào mẫu số Kappa đại diện toàn corpus.

---

## 5. HIỆN TRẠNG LÔ 1, DANH MỤC SHARD CÁCH LY & QUẢN TRỊ RỦI RO TỒN DƯ

### 5.1 Phân định rõ ràng: Chi tiết từng Lô Loại trừ trên `exclusion_registry.json`

Bảng đối chiếu trạng thái mapping và khả năng ngăn chặn rò rỉ của từng lô trong tổng số 10 lô (tổng 246 mẫu) theo đúng thực tế sổ bộ:

| Danh mục Lô loại trừ | Số mẫu | Trạng thái kỹ thuật trên `exclusion_registry.json` | Hiện trạng mã băm kiểm toán | Đánh giá an toàn & Khả năng ngăn chặn |
|:---|:---:|:---|:---|:---|
| **Lô 1 (`EXCL-PILOT-01`)** | 20 | `unresolved_source_mapping` (Rows API chưa khóa revision) | **CHƯA CÓ URL/HTML hash trên registry** (chỉ có `summary_fingerprint_hash`). Tệp `raw20_mapping_check.json` trong `recovery_status.json` vẫn ở trạng thái `pending_independent_review`. | **CHƯA THỂ ĐỐI SOÁT HASH TỰ ĐỘNG:** Không thể chặn tự động bằng hash URL/HTML. Phải ngăn chặn bằng cách ly vật lý 2 shard đã biết (`train-000`, `train-055`) và Cổng quyết định rủi ro tồn dư của Lead D. |
| **Lô 2 (`EXCL-REAL-PILOT-32`)** | 32 | `unresolved_source_mapping` (Rows API chưa khóa revision; chưa có locator shard) | **ĐÃ CÓ ĐỦ 32/32 bộ mã băm** `url_sha256`, `html_sha256`, `group_sha256` trên registry. Tệp `v1_mapping_check.json` trong `recovery_status.json` ở trạng thái `pending_independent_review`. | **ĐÃ CHẶN ĐƯỢC QUA MÃ BĂM:** Hàm `is_excluded()` chặn trùng lặp URL/HTML/Domain; định vị shard vật lý còn chờ nghiệm thu độc lập. |
| **Lô 3 & Lô 4 (`REAL-PILOT-32-V2`)** | **64** | Lô 3 (32 mẫu): `mapping_status=None`<br>Lô 4 (32 mẫu): `resolved` (Rows API pinned) | **ĐÃ CÓ ĐỦ 64/64 bộ mã băm** URL/HTML/Group trên registry; Lô 4 có đủ định vị shard (`train-000`, `train-055`). | **ĐÃ CHẶN TOÀN DIỆN:** Chặn bằng cả mã băm mật mã học và định vị shard vật lý. |
| **Lô 5 đến Lô 10 (Hiệu chuẩn & Sự cố)** | **130** | Lô 5+6 (32 mẫu): `resolved` (`train-000`)<br>Lô 7+8 (34 mẫu): `mapped_to_shards`<br>Lô 9 (32 mẫu): `verified_cryptographic_hashes_locators_restricted_offline`<br>Lô 10 (32 mẫu): `resolved_in_restricted_dossier` (`sealed_restricted_commitment`) | **ĐÃ CÓ ĐỦ 130/130 bộ mã băm** URL/HTML/Group trên registry hoặc niêm phong ngoài Git (Lô 10 có commitment SHA-256 `67326e80b2a6f9cb7356450a31fe15054a1193412a8ed0576ea2972f1801a805`). | **ĐÃ XÁC MINH MẬT MÃ HỌC:** Niêm phong bất biến, chặn trùng lặp URL/HTML/Domain trong toàn bộ các phép kiểm tra deduplication. |
| **TỔNG CỘNG (10 LÔ)** | **246** | **20 (Lô 1) + 32 (Lô 2) + 64 (Lô 3+4) + 130 (Lô 5–10) = 246 mẫu** | **Khẳng định học thuật:** Không suy từ tổng 246 rằng mọi mẫu đều có hash. Lô 1 (20 mẫu) thiếu hash và cần quản trị rủi ro riêng. | **Hệ thống duy trì fail-closed:** Chặn 100% bằng hash đối với 226 mẫu (Lô 2–10); chặn bằng cách ly shard đối với Lô 1. |

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
  │ • Chạy Translation Sanity Check; nếu thiếu model hoặc lỗi dịch thì dừng an toàn (fail-closed).
  │ • Bảo toàn nguyên vẹn page_text gốc; lưu translated_text + 5 trường metadata + translation_sha256.
  ▼
[BƯỚC 3: MÃ HÓA BLIND ID, KHÓA PHÂN TẦNG & NIÊM PHONG HỒ SƠ HẠN CHẾ]
  │ • Sinh Blind ID trung tính không mã hóa lô (BLIND-xxxxxxxx); khóa 30% ngẫu nhiên cho B.
  │ • Xáo trộn Blended Delivery Uniform Hash Shuffle; tạo SHA256SUMS.txt và release manifest.
  ▼
[BƯỚC 4: THẨM ĐỊNH QA ĐỘC LẬP CỦA B & PHÊ DUYỆT MỞ PHIÊN CỦA LEAD D]
  │ • QA Lead B kiểm tra schema Hợp đồng v1.2, bounded anti-inference check; ký biên bản QA độc lập.
  │ • Lead D kiểm tra hồ sơ, ký quyết định phê duyệt mở phiên Pass 1.
  ▼
[BƯỚC 5: GÁN NHÃN PASS 1 ĐỘC LẬP (A GÁN 100%, B GÁN GÓI BLENDED THEO ĐỢT)]
  │ • A và B gán nhãn độc lập qua annotate_cli.py v1.2; ghi nhật ký thời gian và bằng chứng org_evidence.
  │ • Kết thúc Pass 1: Đóng băng và khóa mã băm intake_pass1_A.jsonl và intake_pass1_B.jsonl.
  ▼
[BƯỚC 6: PHÂN XỬ PASS 2, KHÓA NHÃN VÀNG & BÀN GIAO DỮ LIỆU]
  │ • Tính Cohen's Kappa ma trận 3x3 sơ bộ qua phép Join độc lập với bảng phân tầng hạn chế.
  │ • Lead D chủ trì phân xử Pass 2 cho các ca bất đồng; chốt consensus_label.
  │ • Đăng ký 15 mẫu che trộn decoy vào exclusion_registry.json; bàn giao Gold Dataset cho Lead D.
```

### 6.2 Chuẩn hóa Quy trình Dịch ngoại tuyến MarianMT Tiếng Anh (Yêu cầu R-A09)
Nhằm hỗ trợ chuyên viên gán nhãn xử lý các website đa ngôn ngữ mà vẫn bảo toàn tính toàn vẹn khoa học:
1. **Các mô hình dịch cục bộ ngoại tuyến và Trạng thái Ghim Revision:**
   - **Tiếng Nhật (`ja-en`):** `Helsinki-NLP/opus-mt-ja-en` — **ĐÃ GHIM CHÍNH THỨC** tại commit revision:
     `0770961a39ba6bd66305b149c3f4110bcafca2e6` (đã kiểm thực tế trong codebase `scripts/data/translate_clean_calibration_samples.py` và `calibration_manifest_v1_1_4_release.json`).
   - **Tiếng Nga (`ru-en`):** `Helsinki-NLP/opus-mt-ru-en` — **ĐÃ GHIM CHÍNH THỨC** tại commit revision:
     `fbd6dc73284f95536648512cc21d57f19191961a` (đã kiểm thực tế trong codebase `scripts/data/translate_clean_calibration_samples.py`).
   - **Tiếng Trung (`zh-en`):** `Helsinki-NLP/opus-mt-zh-en` — **ĐÁNH DẤU LÀ YÊU CẦU CẦN TẢI VÀ KHÓA REVISION SHA TRƯỚC KHI TRIỂN KHAI** (chưa có mã ghim trong codebase hiện hành; tuyệt đối không tự ý viết "đã ghim" khi chưa tải và kiểm tra thực tế trọng số model).
2. **Quy trình Kiểm dịch Hợp lệ (Translation Sanity Check):**
   Mọi văn bản sau khi qua MarianMT bắt buộc phải thỏa mãn 3 tiêu chí kiểm tra tính hợp lệ trước khi đưa vào Blind View:
   - *Kiểm tra ngôn ngữ đầu ra:* Văn bản dịch `translated_text` phải được nhận diện thuộc không gian ký tự Latinh / tiếng Anh.
   - *Kiểm tra tỷ lệ độ dài:* Độ dài văn bản dịch không được lệch bất thường vượt quá $3\times$ độ dài văn bản gốc.
   - *Kiểm tra tỷ lệ giữ nguyên ký tự nguồn:* Nếu tỷ lệ token không dịch được (vẫn giữ nguyên chữ Hán/Katakana/Cyrillic) vượt quá 30%, mẫu được đánh dấu `translation_warning`.
3. **Cơ chế Xử lý khi Thiếu Model hoặc Lỗi Dịch (Fail-Closed Handling):**
   - Nếu tệp trọng số của mô hình dịch cục bộ bị thiếu hoặc sai mã băm SHA-256, pipeline **DỪNG AN TOÀN NGAY LẬP TỨC (FAIL-CLOSED)**.
   - Tuyệt đối không fallback gọi API dịch trực tuyến ra Internet trong quá trình thực nghiệm; không âm thầm bỏ qua bước dịch để tránh làm sai lệch trải nghiệm đọc của annotator.
   - Bảo toàn nguyên bản: Văn bản gốc `page_text` được lưu trữ bất biến. Văn bản dịch được lưu vào `translated_text` kèm đầy đủ 5 trường siêu dữ liệu kiểm toán và mã băm `translation_sha256`.

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
- **Đánh giá tiến độ có điều kiện:** Tiến độ 1 tuần chỉ khả thi đối với **Đợt 1 (Quy mô 100 mẫu Phương án A2, tổng công số hoàn tất Đợt 1 là 20,66 giờ)**. Tiến độ chính thức toàn chiến dịch tiếp tục là **CHƯA XÁC ĐỊNH (TBD)** chờ kết quả đo lường thực tế từ Đợt 1.

### 7.2 Bảng phân tách ngân sách: Đợt 1, Chuyển tiếp Đợt 2 & Dự phóng Toàn chiến dịch (Hạch toán Mẫu che trộn Decoy)

Nhằm phản ánh chuẩn xác thời điểm nhân sự thực sự gán nhãn, phân biệt rạch ròi số thực đo và số giả định, ngân sách được phân tách thành 3 mốc quản trị:

1. **Quỹ công số thực tế hoàn tất Đợt 1 (100 mẫu Main - B gán 30 mẫu ngẫu nhiên):**
   - Annotator A (gán 100 mẫu Pass 1): $100 \times 6,34\text{m} = \mathbf{10,57\text{ giờ}}$ *(Số thực đo)*.
   - Annotator B (gán 30 mẫu ngẫu nhiên): $30 \times 4,17\text{m} = \mathbf{2,09\text{ giờ}}$ *(Số thực đo; ~15 ca khó phát sinh trong Đợt 1 được tích lũy chuyển sang Đợt 2, chưa gán ở Đợt 1 nên không tính giờ vào Đợt 1)*.
   - QA Lead B (kiểm định schema v1.2, audit tính mù, verify SHA256SUMS Đợt 1): $\mathbf{3,00\text{ giờ}}$ *(Định mức quản trị)*.
   - Thành viên C (vận hành pipeline, 4-layer dedupe, template engine, MarianMT, khóa manifest, tính Kappa $3 \times 3$): $\mathbf{3,50\text{ giờ}}$ *(Định mức kỹ thuật)*.
   - Lead D (chủ trì phân xử Pass 2 cho bất đồng trong 30 mẫu ngẫu nhiên, ký duyệt cổng Đợt 1): $\mathbf{1,50\text{ giờ}}$ *(Định mức chủ trì)*.
   - **TỔNG CÔNG SỐ HOÀN TẤT ĐỢT 1:** $10,57 + 2,09 + 3,00 + 3,50 + 1,50 = \mathbf{20,66\text{ giờ}}$ (hoàn toàn khả thi trong 1 tuần với nhóm 4 người).

2. **Dự toán công số chuyển tiếp sang Đợt 2 (200 mẫu Main - B nhận 70 mẫu Blended giả định):**
   - Annotator A (gán 200 mẫu Pass 1): $200 \times 6,34\text{m} = \mathbf{21,13\text{ giờ}}$ *(Số thực đo)*.
   - Annotator B nhận gói hợp mẫu $S_B^{(2)} = S_{\text{random30}}^{(2)} \cup (S_{\text{hard}}^{(1)} \setminus S_B^{(1)}) = 60 + 10 = \mathbf{70\text{ mẫu}}$ *(70 mẫu là số giả định ước tính)*:
     $$70 \times 4,17\text{m} = \mathbf{4,86\text{ giờ}}.$$
   - QA Lead B (kiểm định Đợt 2): $\mathbf{3,00\text{ giờ}}$ *(Định mức)*.
   - Thành viên C (vận hành pipeline Đợt 2 & Blended Delivery): $\mathbf{4,00\text{ giờ}}$ *(Định mức)*.
   - Lead D (phân xử Pass 2 Đợt 2): $\mathbf{2,50\text{ giờ}}$ *(Định mức)*.
   - **TỔNG CÔNG SỐ DỰ TOÁN ĐỢT 2:** $21,13 + 4,86 + 3,00 + 4,00 + 2,50 = \mathbf{35,49\text{ giờ}}$ *(Số dự toán giả định)*.

3. **Bảng đối chiếu ngân sách toàn chiến dịch: PLAN-01 (190,79h) vs Kịch bản V3.3 Đề xuất (Hạch toán 15 Mẫu che trộn Decoy):**

Thành viên C kính trình Lead D phân tích định lượng và hệ quả vận hành của 2 phương án hạch toán đối với $1,04\text{ giờ}$ gán 15 mẫu che trộn decoy cuối kỳ của B ($15 \times 4,17\text{m} = 1,04\text{h}$):

- **Phương án 1 (Hấp thụ vào quỹ dự phòng QA của B — Giữ nguyên tổng dự phóng 192,32 giờ):**
  * *Cách tính:* Hạch toán $1,04\text{h}$ gán mẫu decoy bằng cách cắt giảm định mức đệm kiểm định QA của B từ $15,00\text{h}$ xuống $\mathbf{13,96\text{h}}$ (giảm $6,9\%$ quỹ thời gian QA). Tổng giờ của B giữ nguyên $\mathbf{43,15\text{ giờ}}$ ($28,15\text{h gán chính} + 1,04\text{h decoy} + 13,96\text{h QA}$). Tổng công số toàn chiến dịch giữ nguyên **$192,32\text{ giờ}$** (chênh $+1,53\text{h}$ so với PLAN-01 đã duyệt).
  * *Hệ quả cụ thể đối với công việc QA đã liệt kê:* B buộc phải rút ngắn thời gian phân bổ cho các khâu kiểm định định kỳ giữa 10 đợt (từ 1,5h/đợt xuống ~1,39h/đợt). Cụ thể: B phải giảm bớt thời gian rà soát snapshot HTML và thẩm duyệt tệp Blind View, chấp nhận biên độ an toàn QA hẹp hơn để bảo toàn trần ngân sách danh nghĩa.
- **Phương án 2 (Bổ sung dòng tăng riêng — Tổng dự phóng điều chỉnh 193,36 giờ):**
  * *Cách tính:* Tách riêng $1,04\text{h}$ gán mẫu decoy thành một dòng ngân sách mới độc lập, **giữ nguyên vẹn toàn bộ $15,00\text{h}$ đệm kiểm định QA của B** $\rightarrow$ Tổng giờ của B điều chỉnh thành $\mathbf{44,19\text{ giờ}}$. Tổng công số toàn chiến dịch là **$193,36\text{ giờ}$** (chênh $+2,57\text{h} = +1,35\%$ so với PLAN-01).
  * *Ưu điểm học thuật:* Bảo toàn toàn diện năng lực kiểm soát chất lượng độc lập của B (đầy đủ 15,00h cho kiểm tra schema, audit tính mù, rà soát bất đồng Pass 2), bảo đảm tiêu chuẩn ARS cao nhất cho công bố khoa học. Đây là đề xuất kỹ thuật riêng biệt kính trình Lead D xem xét lựa chọn.

Bảng số liệu chi tiết theo Phương án 1 (kèm ghi chú Phương án 2):

| Thành viên / Vai trò | Phân bổ PLAN-01 được duyệt (Giờ) | Tỷ lệ PLAN-01 (%) | Kịch bản Dự phóng V3.3 đề xuất (Giờ) | Tỷ lệ V3.3 (%) | Độ lệch công số (Giờ) | Bản chất số liệu & Giải trình kỹ thuật |
|:---|:---:|:---:|:---:|:---:|:---:|:---|
| **Annotator A** | 114,08 | 59,80% | **105,67** | 54,95% | **-8,41** | **Số thực đo:** Tính theo tốc độ thực đo $6,34\text{ phút/mẫu}$ ($105,67\text{h}$; nếu tính theo trung bình thô 380,155s là $105,60\text{h}$). V3.3 chủ động không áp dụng biên dự phòng Model 4 (+8% buffer = 114,08h của PLAN-01). |
| **QA Lead B** | 36,21 | 18,98% | **43,15** | 22,44% | **+6,94** | **Phân tách thực tế:** Gán nhãn kép 405 mẫu chính thức ($28,15\text{h}$) + Gán 15 mẫu che trộn decoy cuối kỳ ($1,04\text{h}$) + Đệm kiểm định QA độc lập qua 5 đợt ($13,96\text{h}$). *(Nếu giữ nguyên 15,00h QA, tổng B là 44,19h, chênh +7,98h).* |
| **Thành viên C** | 25,00 | 13,10% | **28,00** | 14,56% | **+3,00** | **Định mức kỹ thuật:** Vận hành 5 đợt pipeline dữ liệu, dedupe 4 lớp, Template engine, MarianMT translation, khóa tệp phân tầng, độc lập join và tính Kappa ($5 \times 4,00\text{h} = 20,00\text{h}$); cộng 8,00h thiết lập Hợp đồng v1.2, quản trị registry và reconciliation. |
| **Lead D** | 15,50 | 8,12% | **15,50** | 8,06% | **0,00** | **Định mức chủ trì:** Phân xử bất đồng Pass 2 cho các ca bất đồng phát sinh cộng thời gian thẩm duyệt mốc tối hậu (khớp chuẩn ngân sách PLAN-01). |
| **TỔNG CỘNG** | **190,79** | **100,00%** | **192,32** *(hoặc 193,36)* | **100,00%** | **+1,53** *(hoặc +2,57)* | **Kịch bản V3.3 có tổng công số 192,32 giờ (Phương án 1) hoặc 193,36 giờ (Phương án 2). Đây là kịch bản dự phóng mới chờ Lead D xem xét quyết định, CHƯA THAY THẾ ngân sách PLAN-01 đã được phê duyệt.** |

*(Ghi chú số học: Tổng các tỷ lệ thành phần của V3.3 là $54,95\% + 22,44\% + 14,56\% + 8,06\% = 100,01\%$ do làm tròn số thập phân 2 chữ số; tổng giá trị chính xác là 100,00%).*

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
  * Commit V3.1: [`173582b91151e0434f5842b87c218373d309a9d5`](https://github.com/Anhtuann1404/NCKH_2/commit/173582b91151e0434f5842b87c218373d309a9d5)
  * Commit V3.2: [`86381236d63ac7c0ac7a098e3a5ab2e4eb3c8ff4`](https://github.com/Anhtuann1404/NCKH_2/commit/86381236d63ac7c0ac7a098e3a5ab2e4eb3c8ff4)
  * Commit V3.3: [`accdb2c0794db1b91e1d7b4e37ac8b293ac2b7a3`](https://github.com/Anhtuann1404/NCKH_2/commit/accdb2c0794db1b91e1d7b4e37ac8b293ac2b7a3)
   * Commit V3.4 (Bản Master Hoàn thiện Hiện hành): Được cập nhật và đẩy trực tiếp lên nhánh cùng văn bản này.

### 8.2 Báo cáo Trung thực Kết quả Kiểm thử, Log Chi tiết & Tách bạch Thực chứng vs Khả năng Kỹ thuật

1. **Xác nhận Kết quả Kiểm thử Lịch sử của QA Lead B trên clean checkout commit cũ `bc295820` (V3.0):**
   - **Lệnh thực thi:**
     ```bash
     PYTHONPATH=src python -m pytest tests/test_blind_view.py tests/test_clean_calibration_blind_view.py tests/test_difficulty_strata.py tests/test_exclusion_registry.py -v -rs
     ```
   - **Môi trường của B:** Clean checkout commit `bc295820` (V3.0), Python 3.14.2, pytest-9.1.1.
   - **Kết quả quan sát thực chứng từ log của B:** **`137 passed, 13 skipped in 2.22s`** (`0 failed, 0 deselected`):
     * `tests/test_blind_view.py`: **87 passed** (an toàn Blind View v1.1, allowlist trường, strip thẻ script/event, loại trừ rò rỉ nhãn).
     * `tests/test_difficulty_strata.py`: **9 passed** (tính toán độc lập 6 cờ chỉ báo mô tả bề mặt).
     * `tests/test_exclusion_registry.py`: **41 passed, 1 skipped** (`test_restricted_commitment_round_c_loaded_and_verified` bỏ qua do clean checkout không có tệp `data/restricted/clean_calibration_exclusion_mapping_c_32.json`).
     * `tests/test_clean_calibration_blind_view.py`: **0 passed, 12 skipped** (bỏ qua do clean checkout không có tệp `data/annotations/clean_calibration_blind_view_24.json`).
   - **Xác nhận dứt khoát ranh giới commit:** Kết quả `137 passed / 13 skipped` nêu trên là **kết quả thực chứng của commit cũ `bc295820` (Phiên bản V3.0)**, TUYỆT ĐỐI KHÔNG PHẢI là kết quả thẩm định của B đối với phiên bản V3.3 hay V3.4. QA Lead B sẽ thực hiện thẩm định độc lập trên đúng commit V3.4 mới.

2. **Bằng chứng kiểm thử thực tế của Thành viên C trên môi trường có tệp hạn chế ngoài Git (161 Passed):**
   - **Lệnh thực thi:**
     ```powershell
     python -m pytest tests/test_blind_view.py tests/test_clean_calibration_blind_view.py tests/test_difficulty_strata.py tests/test_exclusion_registry.py tests/test_kappa_3x3.py -v
     ```
   - **Môi trường của C:** Windows 11 Home (x64), Python 3.13.14, pytest-7.4.0, pluggy-1.6.0, anyio-4.14.2. Môi trường có sẵn 2 tệp restricted ngoài Git: `data/restricted/clean_calibration_exclusion_mapping_c_32.json` (1 test) và `data/annotations/clean_calibration_blind_view_24.json` (12 test).
   - **Kết quả thực chứng đo đạc từ log:** **`161 passed / 0 failed / 0 skipped / 0 deselected in 4.26s`** trên toàn bộ 5 tệp kiểm thử (bao gồm 150 bài test hồi quy mã hiện hữu + 11 bài test độc lập cho module Cohen's Kappa $3 \times 3$ Paired Bootstrap mới).

3. **Tách bạch Khả năng Kỹ thuật vs Kết quả Thực chứng Về Thời gian Thực thi:**
   - Tiếp thu phê bình phương pháp của Lead D, **dự án KHÔNG đưa ra khẳng định tuyệt đối về nguyên nhân** (như khẳng định chắc chắn do `.pytest_cache` hay bộ đệm OS) khi chưa thực hiện profiling vi mô đo đạc thời gian từng pha I/O và import.
   - **Tách bạch chuẩn mực ARS:**
     * *Khả năng kỹ thuật (Technical Hypothesis):* Sự chênh lệch thời gian thực thi giữa các phiên chạy ($12,98\text{s}$ ở V3.1 vs $5,58\text{s}$ ở V3.2, $7,08\text{s}$ ở V3.3 và $4,26\text{s}$ ở V3.4) có khả năng bắt nguồn từ cơ chế lưu trữ bytecode biên dịch sẵn `.pyc` của `.pytest_cache` kết hợp bộ nhớ đệm trang tệp tin của hệ điều hành (OS File System Page Cache) giúp giảm thiểu thời gian nạp module ở các lượt chạy sau.
     * *Kết quả thực chứng duy nhất được xác nhận (Empirical Ground Truth):* Toàn bộ các test suite đều chạy thành công $100\%$ không phát sinh bất kỳ lỗi nào (`0 failed`); số lượng bài test thực thi là nhất quán và đầy đủ ($150\text{ tests}$ ở V3.1–V3.3 và $161\text{ tests}$ ở V3.4).

4. **Khẳng định Ranh giới Kiểm thử Học thuật:**
   - 150 hàm test đầu tiên là **test hồi quy của mã v1.1.0 hiện hữu**.
   - 11 hàm test mới (`tests/test_kappa_3x3.py`) kiểm chứng thuật toán toán học độc lập của module **Paired Bootstrap Cohen's Kappa $3 \times 3$**.
   - Các cơ chế vận hành mới khác của Main Annotation (`sample_batch1.py`, Blended Delivery Uniform Hash Shuffle, MarianMT `zh/ja/ru`, validator phân nhánh Hợp đồng v1.2 trên pipeline chính) hiện **CHƯA ĐƯỢC LẬP TRÌNH VÀO PIPELINE CHÍNH VÀ CHƯA KIỂM CHỨNG TẬP TRUNG**. Các mã nguồn này chỉ được phép lập trình sau khi Lead D chính thức ký duyệt kế hoạch vận hành.

---

## 9. DANH MỤC 6 QUYẾT ĐỊNH KÍNH TRÌNH LEAD D XEM XÉT TRONG MỘT LƯỢT

Thành viên C kính trình QA Lead B thẩm định độc lập và Lead D xem xét ban hành quyết định đối với 6 nội dung trọng tâm sau:

1. **Phê duyệt Phương án & Quy mô Đợt 1:** Lựa chọn Phương án A2 (Lô đầu Main — 100 mẫu, tổng công số hoàn tất Đợt 1 là 20,66 giờ); chốt tiêu chí Đạt/Dừng, ma trận nhãn $3 \times 3$ Codebook v1.1, phương pháp Paired Bootstrap CI 95% (bỏ công thức Fleiss nhị phân) và quy chế xử lý vùng ranh giới $0,60 \le \kappa < 0,75$ của Đợt 1.
2. **Phê duyệt Hợp đồng Dữ liệu Blind View v1.2 & Tách Allowlist Theo Loại Artifact:** Chấp thuận việc chốt duy nhất tên trường `blind_contract_version = "1.2.0"`, giữ nguyên `codebook_version = "1.1.0"`, cấm trường `random_subset` trong Blind View và bản ghi Pass 1 của Main; phê duyệt cơ chế preflight tự băm raw bytes đối soát theo từng loại artifact riêng biệt (`LOCKED_LEGACY_BLIND_VIEW_ALLOWLIST`, `MANIFEST`, `MAPPING`), loại trừ các hash chưa xác minh khỏi runtime và fail-closed cho Main.
3. **Phê duyệt Cơ chế Blended Delivery, Blind ID & Quy trình Niêm phong 15 Mẫu Mồi Decoy TRƯỚC PHÁT HÀNH:** Thông qua kiến trúc Blind ID trung tính (`BLIND-xxxxxxxx`), công thức hợp mẫu khử trùng lặp $N_B^{(2)} = 60 + |S_{\text{hard}}^{(1)} \setminus S_B^{(1)}|$ (với 70 mẫu là số dự phóng giả định), phép kiểm giới hạn bounded check; phê duyệt quy trình niêm phong loại trừ 15 Mẫu mồi Decoy vào `exclusion_registry.json` TRƯỚC KHI phát gói cho B (mã lô TBD) và niêm phong mapping trong hồ sơ hạn chế ngoài Git để bảo vệ tính mù.
4. **Phê duyệt Quyết định Phạm vi Nguồn và Chấp nhận Rủi ro Tồn dư Lô 1:** Ban hành văn bản phê duyệt danh mục cách ly 2 shard đã biết (`train-000`, `train-055`) và quyết định phương án chấp nhận rủi ro tồn dư của Lô 1 (20 mẫu thiếu hash) trước khi rút mẫu.
5. **Phê duyệt Ngân sách Toàn chiến dịch V3.4 & Quyết định Phương án QA B:** Xem xét phê duyệt Kịch bản V3.4 với tổng công số **$192,32\text{ giờ}$** (Phương án 1 — hấp thụ $1,04\text{h}$ decoy vào QA của B, giảm QA từ 15h xuống 13,96h) hoặc **$193,36\text{ giờ}$** (Phương án 2 — bổ sung dòng tăng riêng $1,04\text{h}$ decoy, giữ nguyên vẹn 15,00h QA cho B).
6. **Xác nhận Tiến độ Toàn chiến dịch là TBD:** Ghi nhận tiến độ chính thức theo tuần của toàn chiến dịch là TBD chờ kết quả thực nghiệm Đợt 1 và cam kết giờ làm việc của A và B.

---

**XÁC NHẬN CỦA THÀNH VIÊN C (DATA PIPELINE & THƯ KÝ KIỂM TOÁN)**  
*(Bản Kế hoạch Vận hành Hợp nhất V3.3 — Duy trì nghiêm ngặt: training_blocked=true, official_test_used=false, Main Annotation KHÓA)*  

**Nguyễn Thắng**
