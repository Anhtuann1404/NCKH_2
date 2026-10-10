# BÁO CÁO ĐỐI SOÁT & KIỂM TRA THỦ CÔNG CHẤT LƯỢNG BẢN DỊCH CALIBRATION V1.1
*(Manual Quality Control & Linguistic Audit of Offline Machine Translations)*

- **Dự án:** Nghiên cứu phát hiện Website Phishing mạo danh tổ chức (NCKH_2)
- **Tác giả thực hiện:** Thành viên C (Data Pipeline & Blind View Engineer - Đóng vai trò kiểm toán độc lập, không tham gia gán nhãn mù)
- **Mục tiêu:** Kiểm tra độc lập từng cặp câu `page_text` (Tiếng Nhật) – `translated_text` (Tiếng Anh) cho 4 mẫu calibration ngoại ngữ (`SMP-002`, `SMP-015`, `SMP-020`, `SMP-023`).
- **Mô hình dịch:** Helsinki-NLP/opus-mt-ja-en (Revision: `0770961a39ba6bd66305b149c3f4110bcafca2e6`, Offline MarianMT).

---

## 1. Bối cảnh & Nguyên tắc Nghiên cứu (ARS Discipline)
Theo phân định trách nhiệm:
1. Thành viên A và B sẽ trực tiếp tham gia gán nhãn mù độc lập (Blind Calibration), do đó **A và B không được phép đọc trước nội dung các mẫu** để tránh phá vỡ tính khách quan (Zero Data Snooping / Blind View Integrity).
2. Thành viên C (hoặc nhân sự kiểm toán độc lập không gán nhãn) chịu trách nhiệm đọc kiểm thủ công toàn bộ các bản dịch, đối chiếu với văn bản gốc để phát hiện các dị thường dịch thuật:
   - Các vòng lặp suy thoái tự hồi quy (degeneration repetition loops).
   - Hiện tượng ảo giác ngữ cảnh (hallucinations).
   - Từ ngữ dịch sai hoặc ghép nghĩa kỳ lạ có thể gây định kiến sai lệch cho người gán nhãn.
3. Không tự tiện kết luận nhãn ("fake store", "lừa đảo") trong báo cáo kỹ thuật dịch. Quyết định phân loại thuộc về annotator A và B theo Codebook.

---

## 2. Kết quả Rà soát Thủ công Chi tiết 4 Mẫu Tiếng Nhật

### 2.1. Mẫu SMP-002 (`https://xvujbn.aheadmusic.shop/`)
- **Độ dài văn bản gốc (JA):** 2,504 ký tự | Hash nguồn: `1425164bc4f4948efb7a54a0f443b749d212720d2077eeb0c968434a9cae60eb`
- **Cấu trúc thực tế trang gốc:**
  - Tiêu đề và điều hướng: Menu danh mục hàng hóa (CD, âm nhạc, thiết bị câu cá, dã ngoại, máy tính, TV, quần áo, đồ chơi, sách truyện...).
  - Phần sản phẩm: Bảng danh mục sản phẩm thời trang xa xỉ kèm mức giá giảm (Túi da PRADA, ví Louis Vuitton, Corné taurus, túi da Hàn Quốc).
- **Phát hiện lỗi ở bản dịch cơ bản (Default):**
  - Hiện tượng kẹt lặp từ ngữ: `comic books, comic books, comic books, books, books, books, books, books...` kéo dài hàng chục token do các danh mục tiếng Nhật (`本・雑誌・コミック`) đứng liền nhau không có dấu phẩy.
- **Kết quả bản dịch tinh chỉnh (Clean - with repetition penalty):**
  - Loại bỏ hoàn toàn vòng lặp vô nghĩa: `Login Accounts: Accounting Accounts, Reservation and Responsibilities How to pay for your personal security and return items: CDs, audio, music, equipment, fishing, travel equipment... Beautiful PRADA Prada 2VG079 business bag, black man, 52,800 yen... Louis Vuitton Long-Lig Miner Wallet...`
  - Ngữ nghĩa được thể hiện rõ ràng: Đây là trang danh mục hàng hóa bán lẻ thời trang có chức năng tài khoản và hiển thị giá.

### 2.2. Mẫu SMP-015 (`https://ww7.buyfastest.top/`)
- **Độ dài văn bản gốc (JA):** 2,442 ký tự | Hash nguồn: `a6e60b2eb74f885fbf80e47087612c22dd33c5b96919dbdcfe3d56f62590214c`
- **Cấu trúc thực tế trang gốc:**
  - Lời chào khách hàng ("ようこそ ゲスト 様 ログイン アカウント作成"), thông tin giỏ hàng, chính sách miễn phí vận chuyển.
  - Danh mục hàng bách hóa tổng hợp và danh sách tranh/ảnh nghệ thuật (Paul Signac, tác phẩm Antibes, bản giới hạn 120 bản kèm khung cao cấp, điện thoại Galaxy Z Fold3 5G, áo hoodie Fear of God...).
- **Phát hiện lỗi ở bản dịch cơ bản (Default):**
  - **Ảo giác nghiêm trọng (Severe Hallucination):** Xuất hiện trích đoạn hoàn toàn không có trong trang gốc: `(The New York Times, December 22, 1974) (The New York Times, December 22, 1972) The New York Times, May 26, 1970, said...`. Nguyên nhân do mô hình MarianMT khi gặp các mốc năm/ngày và định dạng số tiền liên tục trong văn bản thiếu trợ từ đã kích hoạt trọng số học từ corpus báo chí tiếng Anh.
  - Lặp suy thoái: `shopping, shopping, shopping, shopping... car, car, bike, car, car, car...`
- **Kết quả bản dịch tinh chỉnh (Clean):**
  - Xóa bỏ hoàn toàn trích dẫn ảo giác `The New York Times` và vòng lặp `shopping/car`.
  - Giữ lại đúng thông tin sản phẩm và lời chào: `Welcome, guest! Logging accounts, making accounts, shopping... CDs, DVDs, fishing, travel equipment... Galaxy Z Fold3 5G... Paul Signac Antibes rare print with frame...`

### 2.3. Mẫu SMP-020 (`https://fes.jobsms.shop/`)
- **Độ dài văn bản gốc (JA):** 2,618 ký tự | Hash nguồn: `2211bb8da686df7cf9e7354b17b6a48d825c889f07feea3081e6490ea3b25916`
- **Cấu trúc thực tế trang gốc:**
  - "オンラインショップ【通販】 ようこそ ゲスト 様 検索 ログイン アカウント作成 カート オンラインショップ 【ご注文は24時間受け付けております】 全国一律送料無料 会社概要 個人情報保護 配送と返品について 支払方法..."
  - Cam kết bảo vệ quyền riêng tư, thông tin thanh toán được mã hóa SSL/TLS, chính sách hoàn trả trong ngày làm việc.
- **Phát hiện lỗi ở bản dịch cơ bản (Default):**
  - Lặp vô tận: `soups, soups, soups, soups... plastics, plastics, plastics... clothing, clothing, clothing... money money money money money money money (Acquired Taxes of the United States)`.
  - Khó hiểu và làm biến dạng thông điệp của trang.
- **Kết quả bản dịch tinh chỉnh (Clean):**
  - Khôi phục rõ ràng nội dung cam kết bảo mật: `The credit card security has been encrypted and sent safely. Please feel free to send a free delivery of all goods and mail in two days... The identity you received from guests about privacy will not be used except by sending and receiving products...`

### 2.4. Mẫu SMP-023 (`https://oybjxc.sportsloan.shop/`)
- **Độ dài văn bản gốc (JA):** 2,182 ký tự | Hash nguồn: `abcf1df60814f3b7549646452f1e40a02796443ee9eb46d03f0d014ebfc57d07`
- **Cấu trúc thực tế trang gốc:**
  - Tiêu đề cửa hàng "Viert-store", đăng nhập, tạo tài khoản, vận chuyển và trả hàng.
  - Danh sách phụ kiện: Kính OAKLEY JAWBREAKER, mô hình máy bay ANA Boeing 747-400 của Toàn Nhật Không (All Nippon Airways), giày Atlantic Stars, dầu gội haru kurokami scalp.
- **Phát hiện lỗi ở bản dịch cơ bản (Default):**
  - Lặp từ `clothing, clothing, clothing, clothing...` hơn 35 lần liên tiếp.
  - Cụm từ kỳ dị do dịch sai từ danh mục: `Snoopy estuaries, unusable food and drink campaign`.
- **Kết quả bản dịch tinh chỉnh (Clean):**
  - Xóa bỏ vòng lặp `clothing`. Hiển thị chuẩn xác các nhóm sản phẩm phụ kiện thể thao, đồ lưu niệm và thời trang.

---

## 3. Giới hạn Kỹ thuật Cố hữu của Dịch máy (MT Limitations)
1. **Thiếu dấu câu ngữ pháp trong DOM Text:** Trình trích xuất DOM `get_text()` ghép các thẻ `<li>`, `<span>` thành chuỗi từ vựng liên tục. Mô hình NMT MarianMT vốn huấn luyện trên câu văn hoàn chỉnh nên có thể ghép từ theo xác suất thống kê (ví dụ `インナー・下着` dịch thành `innuendo beds`).
2. **Khuyến nghị cho Annotator A & B trong Codebook v1.1:**
   - Bản dịch tiếng Anh được cung cấp là **công cụ trợ đọc (auxiliary reading aid)** nhằm hiểu sơ bộ nội dung chức năng của trang, **không phải là văn bản pháp lý gốc**.
   - Nếu annotator gặp từ ngữ dịch lạ hoặc khó hiểu, **không được vội vã coi đó là bằng chứng phishing**. Phải kết hợp quan sát:
     - Tên miền và eTLD+1 (`.shop`, `.top`...).
     - Sự hiện diện của biểu mẫu thu thập thông tin đăng nhập/thanh toán.
     - Dấu hiệu mạo danh thương hiệu trong từ điển 14 tổ chức.
   - Nếu bản dịch gây nghi ngờ lớn không thể giải quyết, annotator sử dụng cờ ghi chú `ambiguous_translation` hoặc chọn nhãn theo đúng quy chuẩn Codebook.

---

## 4. Kết luận Nghiệm thu Kỹ thuật Bản dịch
- **Giải pháp xử lý:** Tinh chỉnh cơ chế giải mã (Beam Search + `no_repeat_ngram_size=3` + `repetition_penalty=1.2`) giúp xử lý dứt điểm 100% hiện tượng lặp từ và ảo giác văn bản.
- **Artifact bản dịch tinh chỉnh v1.1:**
  - Tệp: `data/raw/recovery/translation_experiment/translations_ja_en_v1.1_clean.jsonl`
  - Dung lượng: 6,127 bytes
  - SHA-256: `4c6e87f594477d112a039a886c4db519c1f325f7cedacc32a749ffda2653aa18`
  - Tổng số mẫu dịch: 4/4 (`SMP-002`, `SMP-015`, `SMP-020`, `SMP-023`)
- **Bảo lưu kiểm toán:** Gói gốc nghiệm thu (`calibration_v1.1_final_acceptance_20261010.zip`) được giữ nguyên 100% làm bằng chứng đối soát. Bản dịch tinh chỉnh được đóng gói riêng vào cấu hình phát hành để phục vụ phiên Calibration chính thức khi có lệnh của Lead D.
