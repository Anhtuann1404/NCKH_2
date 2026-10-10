# TỔNG HỢP CÁC ĐIỂM CÒN MỞ VÀ DỰ THẢO CODEBOOK V1.1 TRƯỚC PHÊ DUYỆT (D/B)
*(Review of Open Methodological Points & Codebook v1.1 Draft for Lead D & Member B Sign-Off)*

- **Dự án:** Nghiên cứu phát hiện website phishing mạo danh tổ chức (NCKH_2)
- **Tác giả chuẩn bị:** Thành viên C (Data Pipeline & Blind View Engineer)
- **Đối tượng xem xét và phê duyệt:** Lead D (Anh Tuấn) và Thành viên B
- **Trạng thái Codebook hiện tại:** **DRAFT (Pending D & B Approval)**. Thành viên C không tự chuyển trạng thái thành approved.
- **Tệp dự thảo tham chiếu:** [`docs/CODEBOOK_V1_1_DRAFT.md`](../docs/CODEBOOK_V1_1_DRAFT.md) (SHA-256: `20b4c181ca1da195c8cd86848ce084035e202ca22b56673cc1aa2e6a911c2b3b`).

---

## 1. Bối cảnh & Ranh giới Trách nhiệm (ARS Guidelines)
Kế thừa [Codebook v1.0](CODEBOOK_V1.md) (SHA-256 `12de9c2f3b457938039b05c72c651d6650f403b620216516262134a3313a2ed1`), Codebook v1.1 mở rộng các quy chuẩn hướng dẫn cho đợt gán nhãn dữ liệu chính và phiên hiệu chuẩn (Calibration).

Theo nguyên tắc ARS:
1. Thành viên C có trách nhiệm chuẩn bị tài liệu, rà soát tính khả thi kỹ thuật của dữ liệu và tiền kiểm công cụ CLI.
2. Quyền phê duyệt nội dung Codebook và quyết định khóa (`locked`) hoàn toàn thuộc về **Lead D và Thành viên B**.
3. Tuyệt đối không thay đổi trạng thái Codebook hoặc mở phiên Calibration cho đến khi cả D và B hoàn tất nghiệm thu và ký xác nhận.

---

## 2. Tổng hợp 5 Điểm Phương pháp Luận Cần D và B Chốt Duyệt

### Điểm 1: Quy chuẩn Hỗ trợ Dịch thuật Ngoại tuyến (Quy tắc R-A09)
- **Cơ chế triển khai:**
  - Mô hình dịch ngoại tuyến: `Helsinki-NLP/opus-mt-ja-en` (Revision `0770961a39ba6bd66305b149c3f4110bcafca2e6`), chạy 100% nội bộ trên CPU không kết nối Internet.
  - Tinh chỉnh tham số chống lặp: `no_repeat_ngram_size=3`, `repetition_penalty=1.2` để loại bỏ dứt điểm hiện tượng thoái hóa lặp từ và ảo giác ngữ cảnh (đã được kiểm toán thủ công tại [`docs/TRANSLATION_MANUAL_QC_REPORT_V1_1.md`](../docs/TRANSLATION_MANUAL_QC_REPORT_V1_1.md)).
  - Tính bất biến: Bản dịch được sinh trước, gắn trực tiếp vào Blind View và ràng buộc mã băm `sample_content_hash` trước khi mở phiên.
- **Hướng dẫn cho Người gán nhãn A và B:**
  - Bản dịch tiếng Anh là **công cụ trợ đọc phụ trợ (auxiliary reading aid)**. Người gán nhãn luôn được cung cấp song song nguyên văn tiếng Nhật và bản dịch tiếng Anh.
  - Không được suy diễn các khiếm khuyết dịch máy (như từ ghép lạ do cắt thẻ DOM không có dấu câu) thành bằng chứng lừa đảo hoặc an toàn.
  - Trường hợp bản dịch gây khó hiểu trầm trọng, người gán nhãn ghi chú `ambiguous_translation` và đánh giá dựa trên các cấu trúc quan sát được khác (URL, form, eTLD+1).

### Điểm 2: Phân định Thuộc tính Bề mặt (Surface Indicators) vs. "Ca khó" (Hard Cases)
- **Thực tế định lượng:**
  - 6 cờ cấu trúc bề mặt: `shared_hosting_or_ugc`, `brand_in_subdomain_or_path`, `login_credential_form`, `external_action_or_links`, `suspicious_url_syntax`, `non_ascii_or_cjk`.
  - Trên tập 24 mẫu Calibration, có tới 21 mẫu xuất hiện đồng thời từ 2 cờ trở lên (chủ yếu do ký tự non-ASCII và liên kết ngoài).
- **Điều chỉnh diễn đạt:**
  - Không gọi việc thỏa mãn $\ge 2$ cờ là xác nhận "ca khó" (confirmed hard case).
  - Thuật ngữ chuẩn hóa trong code và báo cáo: **Sự đồng xuất hiện của các chỉ báo bề mặt (co-occurrence of surface indicators)**.
  - Các cờ này chỉ đóng vai trò phân tầng mô tả (descriptive profiling), không phải bằng chứng phishing và không dùng để gán nhãn thay người.

### Điểm 3: Nguyên tắc Đánh giá Cửa hàng Bán lẻ & Gian lận Thanh toán (`payment_deception`)
- **Vấn đề thực tế:** Nhiều website thương mại điện tử nhỏ, shop bán hàng giảm giá hoặc sử dụng tên miền lạ (`.shop`, `.top`) có thể có hình thức sơ sài nhưng chưa chắc là website lừa đảo mạo danh tổ chức.
- **Quy tắc Codebook v1.1:**
  - Shop giảm giá, tên miền lạ, hoặc biểu mẫu đăng ký thành viên **không tự đủ điều kiện** để kết luận là phishing.
  - Chỉ gán kiểu `payment_deception` khi thỏa mãn đồng thời:
    1. Đã có căn cứ rõ ràng để gán `class_label=phishing` (mạo danh thương hiệu cụ thể, bất nhất về danh tính và tên miền).
    2. Snapshot quan sát thấy rõ luồng thanh toán / yêu cầu nhập thông tin thẻ gắn với hành vi gian lận.
  - Trường hợp nghi ngờ nhưng chưa đủ bằng chứng quan sát hành vi gian dối: Gán trạng thái QC `pending_evidence`, không ép sang `phishing` hoặc `benign`.

### Điểm 4: Ranh giới Nền tảng Dùng chung (UGC / Multi-tenant Hosting)
- **Quy tắc ranh giới:**
  - Độc lập với danh mục 14 tổ chức. Nhận diện ranh giới tenant theo hostname/path: GitHub Pages (`<owner>.github.io`), Cloudflare Pages/Workers (`<project>.pages.dev`), Netlify (`<site>.netlify.app`), Vercel (`*.vercel.app`), Blogger (`*.blogspot.com`), Webflow (`*.webflow.io`), Azure App Service (`*.azurewebsites.net`), Google App Engine (`*.appspot.com`).
  - Ghi nhận `domain_role=user_content_hosting` khi trang nằm trên tenant người dùng, **không đồng nghĩa với việc tổ chức sở hữu nền tảng ủy quyền cho trang**.
  - Không biến hạ tầng của Microsoft hay Google thành first-party của trang người dùng tạo trên đó.

### Điểm 5: Cấu trúc Ghi nhận Bằng chứng Tổ chức (`org_evidence`)
- **Yêu cầu bổ sung cho v1.1:**
  - Mỗi tổ chức được nhận diện (`identified`) phải đi kèm cấu trúc `org_evidence`: `org_id`, `evidence_basis` (`form`, `heading`, `body`, `logo_with_text`), và `evidence_quote` ngắn từ blind view.
  - Trích dẫn bắt buộc phải xuất hiện thực tế trong văn bản nguyên văn hoặc bản dịch của gói mù (được CLI tiền kiểm tự động, không chấp nhận trích dẫn hư cấu).

---

## 3. Quy trình Đề xuất Chốt Khóa (Next Steps for D & B)
1. **D và B rà soát** 5 điểm phương pháp luận trên và nội dung chi tiết trong [`docs/CODEBOOK_V1_1_DRAFT.md`](../docs/CODEBOOK_V1_1_DRAFT.md).
2. **Khi D và B đồng thuận:**
   - Tạo bản sao chính thức `docs/CODEBOOK_V1_1.md`.
   - Cập nhật dòng trạng thái trong tệp thành: `**Trạng thái:** locked (chính thức)`.
   - Tính toán mã băm SHA-256 byte cuối cùng của `docs/CODEBOOK_V1_1.md`.
   - Cập nhật mã băm vào manifest điều hành phiên Calibration.
3. **Thành viên C cam kết:** Giữ nguyên trạng thái `draft` và `ready_for_annotation=false` cho tới khi nhận được quyết định chính thức từ Lead D.
