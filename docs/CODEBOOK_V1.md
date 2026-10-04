# SỔ TAY QUY TẮC GÁN NHÃN (CODEBOOK V1.0 - DỰ THẢO CHỜ DUYỆT)

**Dự án:** NCKH_2 — Phát hiện website phishing mạo danh tổ chức  
**Phiên bản:** `v1.0.0-pending_review`  
**Ngày cập nhật:** 04/10/2026  
**Trạng thái:** `pending_review` (Chờ Thành viên B nhận việc và hoàn tất đối soát độc lập trước khi đóng băng chính thức)  
**Mã băm từ điển đối chiếu (`configs/dictionary_v1.json`):**  
`SHA-256: 61acff28ad48322ff7d4fc1ff5ef4a1a440cee70651192c0999bac94fea36d28`  
**Dải ngày corpus train đã kiểm kê:** `02/07/2024` đến `08/09/2025` (Task DATA-01, 56 shards, 498.255 dòng)  
**Người biên soạn & quản lý:** Thành viên C (Data Pipeline & Blind View)  
**Hiện trạng rà soát:**
- **Thành viên A (Annotator chính):** Đã rà soát và đóng góp 9 khuyến nghị R-A01–R-A09 ([`CODEBOOK_REVIEW_A.md`](annotation_templates/CODEBOOK_REVIEW_A.md)).
- **Thành viên B (QA & Kiểm độc lập):** Đang chờ nhận việc (`pending_review`). Chưa đóng băng chính thức khi B chưa ký duyệt.
- **Thành viên D (Lead):** Đã hoàn tất code review tại commit `f218166` và yêu cầu bổ sung các tiêu chí kỹ thuật.

---

## 1. Căn cứ Lựa chọn Quý & Nguyên tắc Temporal Split (ARS Anti-Leakage)

1. **Căn cứ 5 quý Check Point Brand Phishing (Q4/2024 đến Q4/2025):**
   - Dữ liệu tập train PhreshPhish đã kiểm kê thực tế kết thúc vào ngày **08/09/2025** (thuộc Q3/2025).
   - Quý **Q4/2025** được đưa vào từ đề cương nghiên cứu ban đầu nhằm bao quát cửa sổ dự kiến (đến hết 2025); điều này **không đồng nhất** với việc corpus thực nghiệm phủ trọn vẹn toàn bộ Q4/2025.
2. **Nguyên tắc Từ điển Thời gian (Temporal As-Of Dictionary Protocol):**
   - Trong phân tích Temporal Split (RQ3), để chống triệt để rò rỉ kiến thức tương lai (lookahead data snooping), mô hình tại thời điểm cắt $T$ chỉ được phép sử dụng danh mục thương hiệu và quy tắc tên miền được công bố **trước hoặc tại** thời điểm $T$. Không dùng từ điển tổng hợp của tương lai để hồi cứu dữ liệu quá khứ.

---

## 2. Nguyên tắc cốt lõi & Tiếp thu phản hồi R-A01 đến R-A09

Sổ tay này chuẩn hóa toàn bộ quy tắc gán nhãn, tích hợp đầy đủ 9 góp ý từ [CODEBOOK_REVIEW_A.md] của Thành viên A:

1. **R-A01 — Tách biệt khả năng nhận diện với tình trạng danh mục:**
   - Một tổ chức ngoài danh mục vẫn được coi là `identified` nếu có bằng chứng rõ ràng (ví dụ: mạo danh ngân hàng Việt Nam hoặc bưu chính Thụy Sĩ). Không ép người gán nhãn phải chọn giữa `identified` và `outside_catalog`.
2. **R-A02 — Tách bạch vai trò danh tính trên trang và vai trò tên miền:**
   - `identity_role` (trên trang) và `domain_role` (quan hệ hostname) là hai trường độc lập, không dùng chung một enum.
3. **R-A03 — Quy tắc xác định mục tiêu chính theo luồng thu thập thông tin:**
   - Ưu tiên: Vùng form nhập dữ liệu nhạy cảm đại diện cho ai thì tổ chức đó là mục tiêu chính. Tên xuất hiện nhiều nhất không tự thắng. Form destination không dùng để suy tổ chức bị mạo danh.
4. **R-A04 — Tách nhãn lớp (class label) và nhãn tổ chức:**
   - Một trang có thể xác định chắc chắn là `phishing` nhưng tổ chức là `unknown` hoặc `no_clear_target`.
5. **R-A05 — Tiêu chí Hard Benign:**
   - Phải có form xác thực hoặc từ khóa thương hiệu trên tên miền hợp lệ; không dùng điểm mô hình để chọn.
6. **R-A06 — Tra cứu ngoài view:**
   - Chỉ tra cứu whois/DNS và trang chủ chính thức; **tuyệt đối không truy cập URL phishing sống**.
7. **R-A07 — Xử lý hình ảnh/logo:**
   - Logo đơn lẻ không đi kèm ngữ cảnh văn bản được ghi chú nhưng không tự suy chắc chắn danh tính.
8. **R-A08 — Xử lý sự cố lộ nhãn mù:**
   - Nếu vô tình lộ target hoặc nhãn người kia, hủy bỏ lượt gán đó và thay thế bằng mẫu ngẫu nhiên dự phòng.
9. **R-A09 — Tính thuần túy con người (Human-only Labeling):**
   - 100% lượt gán nhãn độc lập phải do con người thực hiện, không dùng AI hỗ trợ trong quá trình chấm nhãn để đảm bảo độ tin cậy của chỉ số Cohen's Kappa.

---

## 3. Hệ thống phân loại (Taxonomy & Enums)

Mỗi bản ghi gán nhãn gồm các trường chuẩn hóa sau:

### A. Nhãn lớp (`class_label`)
- `phishing`: Trang có dấu hiệu lừa đảo, giả mạo hoặc thu thập thông tin trái phép.
- `benign`: Trang web hợp lệ, an toàn.
- `insufficient_evidence`: Nội dung bị lỗi, trang trắng, không đủ dữ liệu văn bản/DOM để kết luận.

### B. Trạng thái nhận diện mục tiêu chính (`primary_org_status`)
- `identified`: Mục tiêu tổ chức chính được xác định rõ ràng, có bằng chứng văn bản/form.
- `unknown`: Không đủ nội dung để xác định tổ chức bị mạo danh.
- `no_clear_target`: Trang lừa đảo chung (quay thưởng, khảo sát nhận quà, form thu thẻ tín dụng generic) không nhắm vào tổ chức cụ thể nào.
- `multi_target`: Có từ hai tổ chức trở lên xuất hiện ngang hàng, không phân định được mục tiêu chính theo luồng tương tác.

### C. Tình trạng đối với danh mục (`catalog_status`)
- `in_catalog`: Tổ chức thuộc 14 mã chính thức trong `configs/dictionary_v1.json`.
- `outside_catalog`: Tổ chức có bằng chứng xác thực nhưng không nằm trong 14 mã quy định. *(Lưu ý: Không tự ý thêm tổ chức này vào dictionary mô hình).*
- `unresolved`: Không xác định được tổ chức (`unknown` hoặc `no_clear_target`).

### D. Vai trò danh tính trên trang (`identity_role`)
- `identity_claim`: Form đăng nhập, tiêu đề chính hoặc logo tuyên bố trang này là của tổ chức.
- `mention_only`: Chỉ được nhắc tới trong bài báo, điều khoản, footer, danh sách liên kết.
- `unclear`: Không rõ ràng.

### E. Vai trò tên miền (`domain_role`) — Đối chiếu với Dictionary
- `first_party_identity`: Tên miền chính thức của tổ chức (trang chủ, login, account).
- `first_party_content`: CDN / tài nguyên phụ trợ thuộc tổ chức.
- `user_content_hosting`: Nền tảng dùng chung / UGC (Google Sites, SharePoint, Azure Blob, S3, Firebase, Microsoft Forms `forms.office.com`). **Luôn được ưu tiên trong matcher bất kể thứ tự khai báo. Không bao giờ suy thành quan hệ danh tính hợp pháp.**
- `authorized_service`: Đối tác được ủy quyền chính thức.
- `unverified`: Chưa xác minh được quan hệ hoặc tên miền giả mạo.

---

## 4. Danh mục 14 tổ chức chính thức (`in_catalog`)

| Mã máy (`org_id`) | Tên hiển thị | Các thương hiệu con / Dịch vụ ánh xạ về mã chuẩn | UGC / Dịch vụ lưu trữ cần cách ly (`user_content_hosting`) |
| :--- | :--- | :--- | :--- |
| `microsoft` | Microsoft | Outlook, Office 365, Microsoft 365, OneDrive, SharePoint, Azure, Teams | `forms.office.com`, `forms.microsoft.com`, `*.blob.core.windows.net`, `*.web.core.windows.net`, `*.sharepoint.com`, `1drv.ms` |
| `google` | Google | Gmail, Google Drive, Google Docs/Sheets/Forms, YouTube, Google Workspace | `sites.google.com`, `docs.google.com`, `forms.google.com`, `drive.google.com`, `storage.googleapis.com`, `*.firebaseapp.com`, `*.web.app` |
| `meta` | Meta | Facebook, Instagram, WhatsApp, Messenger, Threads | (Không có dịch vụ UGC hosting công cộng) |
| `apple` | Apple | iCloud, Apple ID, App Store, Apple Pay | (Không có dịch vụ UGC hosting công cộng) |
| `amazon` | Amazon | Amazon Store, AWS, Amazon Web Services, Prime Video | `s3.amazonaws.com`, `*.s3.amazonaws.com`, `*.s3.*.amazonaws.com`, `*.s3-*.amazonaws.com` |
| `linkedin` | LinkedIn | LinkedIn, LinkedIn Learning | (CDN: `licdn.com`) |
| `x_twitter` | X (Twitter) | X, Twitter | (Shortlink: `t.co`) |
| `paypal` | PayPal | PayPal | (CDN: `paypalobjects.com`) |
| `adobe` | Adobe | Adobe Creative Cloud, Acrobat, Photoshop, Document Cloud | (Tài nguyên tĩnh Adobe) |
| `booking` | Booking.com | Booking.com, Agoda, Priceline, Kayak | (Dịch vụ đặt phòng) |
| `dhl` | DHL | DHL Express, DHL Tracking, DHL Global Forwarding | (Theo dõi đơn hàng) |
| `spotify` | Spotify | Spotify Music, Spotify Premium | (Phát nhạc trực tuyến) |
| `alibaba` | Alibaba | Alibaba.com, AliExpress, Taobao, Alipay | (Thương mại điện tử) |
| `mastercard` | Mastercard | Mastercard, Mastercard Identity Check | (Dịch vụ thanh toán thẻ) |

---

## 5. Quy trình phân xử bất đồng giữa A và B

1. **Đo đạc độc lập:**
   - Thành viên C chạy công cụ tính Cohen's Kappa (`compute_cohens_kappa`) **chỉ trên tập 30% mẫu ngẫu nhiên** được chọn trước.
   - **Tuyệt đối không tính Kappa trên các ca khó** (`difficult_case = true`) được chuyển riêng.
   - Khi $P_e = 1.0$ (toàn bộ mẫu thuộc 1 lớp duy nhất), hệ số Kappa không xác định ($0/0$); hệ thống báo `status: undefined_single_class` và xuất riêng tỷ lệ đồng thuận quan sát ($P_o$), không báo $1.0$.
2. **Phiên phân xử (Adjudication):**
   - Chỉ phân xử các mẫu có bất đồng ý kiến hoặc ca khó.
   - Căn cứ phân xử dựa trên bằng chứng chụp màn hình / trích dẫn văn bản trực tiếp.
   - Ghi nhận `final_class_label` và `final_org_id` vào `labels_final.json`, đồng thời **bảo tồn nguyên vẹn 100% lịch sử lượt gán ban đầu của A và B**.
