# DỰ THẢO KẾ HOẠCH CHIẾN DỊCH GÁN NHÃN CHÍNH (MAIN ANNOTATION PLAN - DRAFT PROPOSAL V1)

**Dự án:** Nghiên cứu phát hiện website phishing mạo danh tổ chức bằng học máy kết hợp URL và nội dung trang (NCKH_2)  
**Mã văn bản:** `PLAN-MAIN-ANNOTATION-PROPOSAL-V1.0`  
**Phiên bản:** `1.0.0-DRAFT`  
**Ngày lập:** 10/11/2026  
**Đơn vị lập:** Thành viên C (Nguyễn Thắng — Data Pipeline & Thư ký Kiểm toán)  
**Trạng thái quản trị:** `DRAFT_PENDING_LEAD_D_REVIEW_AND_APPROVAL` (Dự thảo đề xuất — Chưa trích xuất mẫu, chưa phát Blind View, chưa mở Pass 1)  
**Căn cứ pháp lý & kỹ thuật:**  
- Quy tắc làm việc với AI của nhóm NCKH_2 (Ban hành ngày 09/11/2026).  
- Giao thức dữ liệu (`docs/DATA_PROTOCOL.md`) và Giao thức thực nghiệm (`docs/EXPERIMENT_PROTOCOL.md`).  
- Quyết định đóng mốc Calibration Runway A (`DECISION-LEAD-D-CLOSURE-CALIBRATION-CLEAN-RUNWAY-A-OFFICIAL`).  
- Khung ngân sách công sức dự phóng có điều kiện PLAN-01 (190,79 giờ người).  
- Kỷ luật Academic Research Skills (ARS) và Ponytail Engineering Discipline.

---

## 1. NGUYÊN TẮC CỐT LÕI & RANH GIỚI QUẢN TRỊ

1. **Tính chất văn bản:** Đây là văn bản **DỰ THẢO ĐỀ XUẤT** do Thành viên C chuẩn bị theo yêu cầu của Lead D. Mọi con số, tỷ lệ và phương án trong tài liệu này đều ở trạng thái đề xuất, tuyệt đối không tự động phát sinh hiệu lực thi hành khi Lead D chưa ban hành Quyết định phê duyệt.
2. **Phân biệt rõ con số 1.000 mẫu trong PLAN-01:**
   - Con số 1.000 mẫu trong Báo cáo PLAN-01 là **Khung ngân sách công sức dự phóng có điều kiện** (Conditional Projected Effort Budget — 190,79 giờ người) được Lead D phê duyệt về mặt kế toán tài nguyên.
   - Con số 1.000 mẫu **CHƯA PHẢI LÀ LỆNH TRÍCH XUẤT THỰC TẾ**. Quy mô trích xuất và triển khai thực tế sẽ được Lead D ra lệnh theo từng giai đoạn (Staged Execution) căn cứ vào kết quả đo lường thực nghiệm đợt đầu và cam kết giờ công khả dụng của nhân sự.
3. **Kỷ luật hệ thống bất biến:**
   - `training_blocked = true` (Chặn 100% nạp dữ liệu vào pipeline huấn luyện).
   - `official_test_used = false` (Cô lập tuyệt đối 100% tập kiểm thử chính thức).
   - `main_annotation_status = "LOCKED"` (Chiến dịch gán nhãn chính tiếp tục khóa).

---

## 2. ĐỀ XUẤT QUY MÔ, NGUỒN VÀ CHIẾN LƯỢC CHỌN MẪU

### 2.1 Quy mô trích xuất theo giai đoạn (Staged Rollout)
Để kiểm soát rủi ro công sức và đảm bảo chất lượng khoa học, đề xuất chia chiến dịch thành 3 đợt:
- **Đợt 1 (Batch 1 — Pilot Runway / Thử nghiệm đo đạc):** Quy mô **60 đến 100 mẫu**. Mục tiêu là kiểm chứng công cụ, đo lường tốc độ gán nhãn thực tế của người và đánh giá độ đồng thuận sơ bộ $\kappa_{A-B}$.
- **Đợt 2 (Batch 2 — Mở rộng quy mô chính):** Quy mô **400 đến 500 mẫu**. Triển khai sau khi Lead D đánh giá kết quả Đợt 1 và phê duyệt lịch trình chính thức.
- **Đợt 3 (Batch 3 — Hoàn tất chiến dịch):** Quy mô phần còn lại (đạt ngưỡng tối ưu theo trần ngân sách mà Lead D phê duyệt).

### 2.2 Nguồn dữ liệu & Tiêu chí tuyển chọn ứng viên
- **Nguồn dữ liệu gốc:** Trích xuất từ kho ngữ liệu đã khóa mã băm SHA-256 trong `configs/source_manifest.json`:
  + Corpus PhreshPhish (tập crawl sạch độc lập).
  + Corpus PhishVN (tập phishing mục tiêu Việt Nam và quốc tế).
- **Cân bằng nhãn nguồn (Source Label Stratification):**
  + Duy trì tỷ lệ cân bằng mục tiêu: **50% Phishing / 50% Benign** trong tập ứng viên trích xuất nhằm phục vụ đánh giá công bằng mô hình học máy.
  + *Ranh giới ARS:* Nhãn nguồn (`source_label`) **CHỈ ĐƯỢC DÙNG** ở bước phân tầng lấy mẫu (Sampling Stratification); tuyệt đối **ẨN HOÀN TOÀN** trong toàn bộ quá trình gán nhãn của A và B.
- **Độ đại diện theo 14 tổ chức mục tiêu (`configs/dictionary_v1.json`):**
  + Đảm bảo phân bổ mẫu bao phủ 14 tổ chức đã định nghĩa (Microsoft, Google, Meta, Apple, Amazon, PayPal, Adobe, Booking, DHL, Spotify, Alibaba, Mastercard, v.v.).
  + Duy trì tỷ lệ mẫu ngoài danh mục (Outside-Catalog / Non-brand) tối thiểu 20–30% để kiểm tra năng lực phát hiện ca không mạo danh tổ chức trong danh mục.

---

## 3. CƠ CHẾ LOẠI TRỪ & CHỐNG RÒ RỈ DỮ LIỆU 4 LỚP (4-LAYER ANTI-LEAKAGE)

Để bảo đảm tính toàn vẹn tuyệt đối của dữ liệu nghiên cứu, mọi mẫu ứng viên trước khi đưa vào danh sách tuyển chọn bắt buộc phải vượt qua bộ lọc khử trùng 4 lớp:

```
[Ứng viên nguồn mới]
         │
         ▼
┌────────────────────────────────────────────────────────┐
│ Lớp 1: Khử trùng URL Chuẩn hóa (Normalized URL Hash)  │ ── Trùng ──► [LOẠI BỎ]
└────────────────────────────────────────────────────────┘
         │ Không trùng
         ▼
┌────────────────────────────────────────────────────────┐
│ Lớp 2: Khử trùng Nội dung HTML thô (Raw HTML SHA-256) │ ── Trùng ──► [LOẠI BỎ]
└────────────────────────────────────────────────────────┘
         │ Không trùng
         ▼
┌────────────────────────────────────────────────────────┐
│ Lớp 3: Cô lập Nhóm miền & Tenant (Domain / eTLD+1)     │ ── Trùng ──► [LOẠI BỎ]
└────────────────────────────────────────────────────────┘
         │ Không trùng
         ▼
┌────────────────────────────────────────────────────────┐
│ Lớp 4: Lọc gần trùng Template (SimHash 64-bit / DOM)   │ ── Trùng ──► [LOẠI BỎ]
└────────────────────────────────────────────────────────┘
         │ Đạt 4 lớp
         ▼
[Ứng viên Sạch Hợp lệ đưa vào Phân tầng Main Annotation]
```

### 3.1 Danh mục Loại trừ Bắt buộc (Exclusion Registry Enforcement)
Tự động quét và loại trừ 100% các mẫu trùng khớp với:
1. **24 mẫu hiệu chuẩn Clean Runway A:** Theo bảng nhãn đã khóa tại gói ZIP `e0bb55e8...` (`clean_calibration_runway_a_labels_final.json`).
2. **116 mẫu trong `data/exclusion_registry.json`:** Gồm 20 mẫu Pilot 01, 32 mẫu Pilot V1 thật, 32 mẫu Pilot V2 thật, 24 mẫu Calibration cũ và 8 mẫu dự phòng cũ.
3. **Mọi mẫu đã lộ hoặc đã mở:** Bất kỳ mẫu nào đã từng xuất hiện trong các biên bản phân xử, kiểm toán hoặc kiểm thử trước đây.
4. **Tập Official Test:** Tuyệt đối cô lập 100%, không sử dụng cho bất kỳ bước phát triển hay gán nhãn nào.

### 3.2 Đặc tả kỹ thuật 4 lớp khử trùng
1. **Lớp 1 (URL Match):** So khớp mã băm SHA-256 của URL sau khi chuẩn hóa (bỏ fragment `#`, sắp xếp query string, lowercase host, strip trailing slash).
2. **Lớp 2 (HTML Match):** So khớp mã băm SHA-256 của nội dung HTML tĩnh thô (`raw_html_sha256`) và cấu trúc hiển thị an toàn (`view_content_sha256`).
3. **Lớp 3 (Domain / Group Isolation):** Sử dụng hàm `extract_group_id` (`src/phishing/data/grouping.py`) phân tách theo `eTLD+1` và tenant hosting dùng chung (GitHub Pages, Cloudflare Pages, Vercel, Netlify, Firebase, Google Sites, Wix, WordPress, v.v.). Bất kỳ nhóm miền nào đã có mẫu trong danh mục loại trừ đều bị chặn hoàn toàn.
4. **Lớp 4 (Template Near-Duplicate Filter):** Sử dụng công cụ `phishing.data.template_similarity` đo độ tương đồng SimHash 64-bit (khoảng cách Hamming $\le 3$) và DOM Tag Jaccard similarity ($> 0.85$) để loại bỏ các biến thể clone giao diện hàng loạt (ví dụ: các mẫu shop `.shop` trùng cấu trúc, trang login mẫu dựng sẵn).

---

## 4. THIẾT KẾ BLIND VIEW, MANIFEST & PHÂN QUYỀN DỮ LIỆU HẠN CHẾ

### 4.1 Cấu trúc Blind View An toàn (Zero-Leakage Input View)
Gói dữ liệu phát cho Annotator (A và B) tuân thủ nghiêm ngặt module `src/phishing/annotation/blind_view.py`:
- **Các trường được phép xuất hiện:**
  + `sample_id`: Định danh ẩn danh duy nhất dạng `MAIN-XXXX` (được xáo trộn ngẫu nhiên, không để lộ nguồn gốc hay thứ tự crawl).
  + `url`: URL an toàn đã chuẩn hóa.
  + `page_text`: Văn bản trang đã được lọc bỏ toàn bộ mã độc, script, iframe, inline event handlers và form action URL.
  + `structure_summary`: Thống kê số lượng form, trường nhập liệu (input, password), button, external links (phục vụ đánh giá bề mặt).
  + `offline_translation`: Bản dịch tiếng Việt hỗ trợ ngoại tuyến (nếu gặp trang tiếng nước ngoài, tuân thủ quy chế dịch máy tĩnh).
- **Các trường TUYỆT ĐỐI BỊ GIẤU KÍN (Strictly Stripped):**
  + ❌ `source_label` (nhãn gốc từ tập crawl).
  + ❌ `target` / thương hiệu mục tiêu dự đoán.
  + ❌ Điểm số gợi ý matcher hoặc kết quả phân loại của bất kỳ mô hình nào.
  + ❌ Nhãn, ghi chú, bằng chứng hoặc danh tính của Annotator kia.
  + ❌ Định danh hàng gốc (raw locator) trỏ về tệp nguồn.

### 4.2 Kiến trúc Phân quyền Dữ liệu 3 Tầng
Để bảo vệ an toàn dữ liệu theo Quy tắc nhóm NCKH_2:
- **Tầng 1 (Public / Git-tracked):** Chỉ chứa mã nguồn công cụ (`src/`, `tests/`), schemas, codebook và tài liệu. Tuyệt đối không đẩy URL, HTML hay nhãn nghiên cứu lên Git.
- **Tầng 2 (Restricted Governance — `data/restricted/`):** Chỉ Thư ký C và Lead D có quyền truy cập. Chứa:
  + Tệp mapping bí mật (ánh xạ giữa `sample_id` $\leftrightarrow$ vị trí dòng trong corpus gốc).
  + Danh sách nhãn nguồn gốc phục vụ đối soát hậu phân xử.
  + Danh sách mẫu dự phòng có thứ tự (Reserve pool).
- **Tầng 3 (Annotator Workspace):** Kênh riêng biệt cấp phát cho từng thành viên:
  + `data/annotations/blind_view_main_batch1_A.json` (chỉ cấp cho A).
  + `data/annotations/blind_view_main_batch1_B.json` (chỉ cấp cho B trên phần mẫu gán đôi).

### 4.3 Khóa Mã băm Toàn vẹn (Cryptographic Manifest)
Mỗi đợt phát hành gói Blind View đều đi kèm một `manifest.json` và bảng `SHA256SUMS.txt` khóa cứng mã băm của từng tệp thành phần. Mọi sự thay đổi dù chỉ 1 byte đều hủy bỏ hiệu lực của gói dữ liệu.

---

## 5. PHƯƠNG PHÁP CHỌN PHẦN GÁN ĐỘC LẬP ĐÔI CHO B (DOUBLE ANNOTATION)

### 5.1 Mục tiêu & Tỷ lệ gán đôi
- **Mục tiêu:** Tính toán chỉ số thỏa thuận liên đánh giá viên **Cohen’s Kappa ($\kappa_{A-B}$)** để chứng minh độ tin cậy khoa học của tập nhãn chuẩn vàng (Gold Standard).
- **Tỷ lệ đề xuất:** **25% đến 30%** tổng số mẫu của đợt gán nhãn.
  + Ví dụ với Đợt 1 quy mô 100 mẫu: A gán 100 mẫu; B gán độc lập **30 mẫu** gán đôi.

### 5.2 Cơ cấu chọn mẫu gán đôi cho B (50% Ngẫu nhiên + 50% Ca khó)
Để vừa đảm bảo tính đại diện thống kê toàn diện, vừa kiểm tra sức bền của Codebook ở các trường hợp biên, 30 mẫu của B được phân bổ chính xác:
1. **50% Mẫu ngẫu nhiên đồng đều (Uniform Random Sampling — 15 mẫu):**
   - Chọn hoàn toàn ngẫu nhiên bằng bộ sinh số giả ngẫu nhiên có `random_seed` cố định và được công bố trước trong manifest.
   - Phản ánh trung thực phân phối tự nhiên của corpus.
2. **50% Ca khó phân tầng (Hard Cases Strata — 15 mẫu):**
   - Tuyển chọn có hệ thống dựa trên 6 cờ chỉ báo bề mặt đã chuẩn hóa trong `src/phishing/data/difficulty_strata.py`:
     * `brand_in_subdomain_or_path` (Tên thương hiệu xuất hiện ở subdomain hoặc đường dẫn).
     * `shared_hosting_or_ugc` (Website nằm trên nền tảng lưu trữ chia sẻ / UGC).
     * `login_credential_form` (Có form đăng nhập / mật khẩu).
     * `external_action_or_links` (Form submit trỏ ra tên miền ngoài hoặc phần lớn liên kết ngoài).
     * `suspicious_url_syntax` (URL có cú pháp bất thường, nhiều dấu gạch nối, subdomain sâu, cổng lạ).
     * `non_ascii_or_cjk` (Ký tự phi Latinh / CJK / IDN punycode).

### 5.3 Thuật toán Chọn Rời rạc Tránh Đếm trùng (Strict Disjoint Algorithm)
Để loại bỏ triệt để nguy cơ đếm trùng giữa nhóm mẫu ngẫu nhiên và nhóm ca khó:
1. **Bước 1 (Lọc ca khó):** Quét toàn bộ tập ứng viên, lọc ra các mẫu thỏa mãn $\ge 1$ cờ độ khó $\rightarrow$ Bốc ngẫu nhiên $k$ mẫu vào danh sách `selected_hard_ids`.
2. **Bước 2 (Loại trừ phần bù):** Tạo tập ứng viên cho phần ngẫu nhiên bằng phép trừ tập hợp:
   $$\text{Candidates}_{\text{random}} = \text{All\_Candidates} \setminus \text{selected\_hard\_ids}$$
3. **Bước 3 (Bốc ngẫu nhiên):** Bốc tiếp $m$ mẫu ngẫu nhiên từ $\text{Candidates}_{\text{random}}$ vào danh sách `selected_random_ids`.
4. **Khẳng định tính rời rạc:**
   $$\text{selected\_hard\_ids} \cap \text{selected\_random\_ids} = \emptyset \quad (100\% \text{ không đếm trùng})$$
- Trường siêu dữ liệu `sampling_stratum` (`"uniform_random"` vs `"hard_stratum"`) được lưu trữ tại kênh hạn chế của C để phục vụ phân rã chỉ số Kappa theo từng phân tầng.

---

## 6. KẾ HOẠCH PHÁT HÀNH ĐỢT ĐẦU (BATCH 1: 50–100 MẪU) & BỘ TIÊU CHÍ ĐÁNH GIÁ

### 6.1 Quy mô & Mục tiêu đo đạc Đợt 1
- **Quy mô đề xuất:** **60 mẫu** (A gán 60 mẫu, B gán 20 mẫu gán đôi) hoặc **100 mẫu** (A gán 100 mẫu, B gán 30 mẫu gán đôi).
- **Mục tiêu thực nghiệm:**
  + Đo đạc chính xác thời gian thao tác trung bình của người ($T_{\text{human}}$) trên từng mẫu qua bộ đếm thời gian `phishing.annotation.timer`.
  + Ghi chép nhật ký thời gian thực tế (Timesheet Log) của từng phiên gán nhãn; tách biệt 100% thời gian AI chạy nền ($0,00$ giờ công người).
  + Đo độ đồng thuận sơ bộ $\kappa_{A-B}$ ban đầu trước khi phân xử.
  + Thử tải và kiểm tra độ ổn định của công cụ `annotate_cli`.

### 6.2 Bộ Tiêu chí Định lượng để Lead D Quyết định Kế hoạch Tiếp theo (Go / No-Go Gate)
Sau khi hoàn tất Đợt 1, Thành viên C và QA Lead B sẽ lập báo cáo định lượng để Lead D quyết định có giữ tiến độ 1 tuần hay điều chỉnh:

| Tiêu chí | Ngưỡng ĐẠT (Tiếp tục kế hoạch) | Ngưỡng CẢNH BÁO (Cần điều chỉnh / Giãn tiến độ) |
|:---|:---|:---|
| **1. Độ đồng thuận liên đánh giá viên ($\kappa_{A-B}$)** | $\kappa \ge 0,75$ (Thỏa thuận tốt theo Landis & Koch) | $\kappa < 0,70$ $\rightarrow$ Tạm dừng trích xuất, tổ chức họp phân xử và làm rõ Codebook trước khi mở đợt tiếp theo. |
| **2. Tốc độ gán nhãn thực tế của Annotator A** | $\text{Median} \le 4,5$ phút/mẫu; $\text{P90} \le 8,0$ phút/mẫu | $\text{Median} > 5,5$ phút/mẫu $\rightarrow$ Nguy cơ vỡ tiến độ 1 tuần; đề xuất Lead D giãn tiến độ hoặc giảm quy mô đợt 2. |
| **3. Tốc độ gán nhãn thực tế của QA Lead B** | $\text{Median} \le 4,0$ phút/mẫu | $\text{Median} > 5,0$ phút/mẫu $\rightarrow$ Cần điều chỉnh phân bổ quỹ giờ của B. |
| **4. Tỷ lệ ca nghi ngờ (`insufficient_evidence`)** | $\le 5,0\%$ tổng số mẫu | $> 10,0\%$ $\rightarrow$ Báo hiệu chất lượng snapshot hoặc đường link nguồn suy giảm; cần rà soát lại tiêu chí crawl. |
| **5. Tính toàn vẹn kỹ thuật của CLI** | $0$ lỗi crash, $0$ lỗi ghi đè dữ liệu, 100% bản ghi hợp lệ format JSON | Có lỗi phát sinh $\rightarrow$ Khắc phục triệt để công cụ trước khi phát tiếp. |

---

## 7. MA TRẬN PHÂN CÔNG TRÁCH NHIỆM, TIỀN KIỂM & ĐIỀU CHỜ LEAD D QUYẾT ĐỊNH

### 7.1 Ma trận Phân công Trách nhiệm (RACI Matrix)

| Hạng mục công việc | Người thực hiện (R) | Người kiểm độc lập (A/C) | Thẩm quyền phê duyệt (D) |
|:---|:---:|:---:|:---:|
| Chuẩn bị danh mục loại trừ & lọc trùng 4 lớp | **C** | **B** (QA độc lập) | **D** |
| Trích xuất ứng viên & tạo gói Blind View an toàn | **C** | **B** (QA độc lập) | **D** |
| Kiểm định tính mù và mã băm gói dữ liệu | **B** | **C** (Đối soát) | **D** |
| Phê duyệt gói phát hành & phát lệnh mở Pass 1 | — | — | **D** (Toàn quyền) |
| Thực hiện gán nhãn mù độc lập Pass 1 A | **A** | — | — |
| Thực hiện gán nhãn mù độc lập Pass 1 B (phần gán đôi) | **B** | — | — |
| Thu thập nhật ký timesheet & đo đạc tốc độ | **C** | **B** (Kiểm chứng) | **D** |
| Lập báo cáo phân tích Kappa & đề xuất nhịp độ đợt 2 | **C** | **B** (Đồng ký) | **D** |

### 7.2 Các phép Tiền kiểm Bắt buộc Trước khi Phát gói (Pre-flight Checklist)
Trước khi bất kỳ tệp Blind View nào được gửi cho A hoặc B, C và B bắt buộc phải thực thi và ghi nhận:
1. `PRE-CHECK-01`: Script tự động quét toàn bộ trường của Blind View JSON, xác nhận 0% tồn tại `source_label`, `target`, `matcher_score`, `model_score`.
2. `PRE-CHECK-02`: Script đối chiếu chéo URL và HTML hash với `exclusion_registry.json` và bộ 24 mẫu Runway A, xác nhận 0% trùng lặp.
3. `PRE-CHECK-03`: Xác nhận toàn bộ nội dung HTML an toàn đã được strip toàn bộ thẻ `<script>`, `<iframe>`, inline event handler (`onload`, `onclick`), và giá trị trường mật khẩu/form.
4. `PRE-CHECK-04`: Lập bảng `SHA256SUMS.txt` và gói nén ZIP được bảo toàn nguyên byte.

### 7.3 Bằng chứng Bàn giao Lưu hồ sơ
- Tệp gói nén Blind View hoàn chỉnh kèm mã băm SHA-256.
- Biên bản nghiệm thu QA độc lập của B xác nhận kết quả 4 phép tiền kiểm trên.
- Bản lưu bí mật tệp mapping locator lưu trữ tại `data/restricted/`.

### 7.4 Những điều CÒN CHỜ LEAD D QUYẾT ĐỊNH (Pending Governance Decisions)
Thành viên C xin kính trình Lead D xem xét và cho ý kiến chỉ đạo đối với các điểm mấu chốt sau:
1. **Chốt quy mô chính thức của Đợt 1:** Lựa chọn phương án **60 mẫu** (A: 60, B: 20) hay **100 mẫu** (A: 100, B: 30)?
2. **Phê duyệt tiêu chí phân bổ ca khó:** Thống nhất danh mục 6 cờ độ khó trong `difficulty_strata.py` làm tiêu chuẩn chọn 50% ca khó cho B?
3. **Phê duyệt thời điểm phát lệnh mở gán nhãn:** Sau khi nhận cam kết văn bản về số giờ khả dụng mỗi tuần của Annotator A và QA Lead B.

---

**XÁC NHẬN CỦA ĐƠN VỊ LẬP DỰ THẢO**  
*(Dự thảo đề xuất kỹ thuật — Tiếp tục giữ training_blocked=true, official_test_used=false, Main Annotation KHÓA)*  

**Thành viên C (Nguyễn Thắng)**  
*Data Pipeline & Thư ký Kiểm toán Dự án NCKH_2*
