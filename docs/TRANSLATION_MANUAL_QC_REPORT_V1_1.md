# BÁO CÁO PHƯƠNG PHÁP & KẾT QUẢ TỔNG HỢP KIỂM TOÁN CHẤT LƯỢNG DỊCH MÁY HIỆU CHUẨN V1.1
*(Methodology & Synthesis Report: Quality Control of Offline Machine Translations)*

- **Dự án:** Nghiên cứu phát hiện website phishing mạo danh tổ chức (NCKH_2)
- **Tác giả:** Thành viên C (Data Pipeline & Blind View Engineer - Độc lập, không tham gia gán nhãn mù)
- **Mô hình dịch:** `Helsinki-NLP/opus-mt-ja-en` (Revision: `0770961a39ba6bd66305b149c3f4110bcafca2e6`, Offline MarianMT).
- **Phạm vi kiểm toán:** 4 mẫu ngoại ngữ tiếng Nhật trong tập Calibration 24 mẫu (`SMP-002`, `SMP-015`, `SMP-020`, `SMP-023`).

---

## 1. Nguyên tắc Bảo mật Blind View & Ranh giới Tài liệu (ARS Protocol)

Theo nguyên tắc nghiên cứu thực nghiệm định lượng chống rò rỉ dữ liệu (Anti-Leakage Protocols):
1. **Bảo vệ tính khách quan của Đánh giá viên A và B:** Thành viên A và B sẽ trực tiếp tham gia phiên gán nhãn mù độc lập (Blind Calibration). Do đó, **báo cáo lưu trữ trên Git tuyệt đối không chứa URL cụ thể, tên miền thực tế hoặc trích đoạn nội dung văn bản của các mẫu**.
2. **Khu vực dữ liệu hạn chế:** Toàn bộ hồ sơ kiểm toán đối chiếu chi tiết từng mẫu (kèm URL gốc, trích đoạn lỗi quan sát và trích đoạn bản dịch) được chuyển lưu trữ an toàn tại:
   `data/raw/recovery/translation_experiment/TRANSLATION_MANUAL_QC_DETAILS.md`
   (Thuộc phân vùng dữ liệu riêng tư, nằm trong `.gitignore`, không đưa lên Git công khai).
3. **Báo cáo này:** Đóng vai trò tài liệu phương pháp luận, phân tích bản chất lỗi kỹ thuật và công bố kết quả tổng hợp cùng tham số giải mã chuẩn hóa.

---

## 2. Bản chất Lỗi Kỹ thuật Quan sát được trên Dữ liệu Web Thô

Khi chạy mô hình MarianMT ngoại tuyến với cấu hình Beam Search cơ bản (`num_beams=4`) trên văn bản bóc tách từ DOM HTML của các trang web tiếng Nhật, hai hiện tượng lỗi chính đã được quan sát:

1. **Thoái hóa lặp từ ngữ tự hồi quy (Autoregressive Degeneration Loops):**
   - *Giả thuyết kỹ thuật:* Nhóm đặt giả thuyết rằng khi trình bóc tách DOM trích xuất các danh sách thẻ danh mục hàng hóa (`<li>`, `<span>`) thiếu dấu câu ngữ pháp hoặc liên từ tự nhiên trong tiếng Nhật, mô hình giải mã tự hồi quy khi gặp chuỗi danh từ liên tục có thể bị kẹt xác suất chuyển trạng thái, khiến token liền trước kích hoạt việc lặp lại chính nó hàng chục lần (ví dụ: lặp các từ chỉ danh mục hàng hóa, phương tiện, thời trang).
2. **Ảo giác ngữ cảnh từ dữ liệu tiền huấn luyện (Corpus-level Hallucination):**
   - *Giả thuyết kỹ thuật:* Nhóm đặt giả thuyết rằng khi gặp các chuỗi số liệu dày đặc (giá tiền, thông số kỹ thuật, ngày tháng) thiếu ngữ cảnh văn cảnh hoàn chỉnh, mô hình có thể kích hoạt các liên tưởng xác suất từ ngữ liệu báo chí tiếng Anh được học trong giai đoạn tiền huấn luyện (pretraining corpus), dẫn tới việc chèn các cụm từ trích dẫn tin tức ngoại lai hoàn toàn không có trong nội dung trang web gốc.

---

## 3. Phương pháp Tinh chỉnh Cơ chế Giải mã & Tham số Chuẩn hóa

Để xử lý các dạng lỗi quan sát được ở trên trong môi trường thực nghiệm ngoại tuyến mà vẫn duy trì tính ổn định giải mã, quy trình giải mã được tinh chỉnh với hai tham số điều khiển (áp dụng cho 4 mẫu kiểm toán trong điều kiện môi trường xác định):

1. **Chặn N-gram trùng lặp (`no_repeat_ngram_size=3`):**
   - Ngăn chặn việc mô hình lặp lại bất kỳ chuỗi 3 từ liên tiếp nào đã xuất hiện trước đó trong đoạn dịch.
   - Chặn đứng dứt điểm các vòng lặp từ vựng và chuỗi danh từ lặp vô tận.
2. **Phạt tần suất lặp lại (`repetition_penalty=1.2`):**
   - Giảm xác suất chọn lại các token đã được sinh ra, khuyến khích mô hình chuyển sang các token mang thông tin danh mục tiếp theo.
   - Ngưỡng `1.2` được chọn để đảm bảo vừa đủ phá vỡ vòng lặp suy thoái mà không làm sai lệch cấu trúc câu hoặc ép mô hình chọn các từ hiếm bất thường.

*Lệnh thực thi sinh bản dịch tinh chỉnh:*
```bash
.venv\Scripts\python.exe scripts/data/run_offline_translation_experiment.py \
    --no-repeat-ngram-size 3 \
    --repetition-penalty 1.2 \
    --single-run-payload data/raw/recovery/translation_experiment/translations_ja_en_v1.1_clean.jsonl
```

---

## 4. Kết quả Tổng hợp trên 4 Mẫu Kiểm toán

Sau khi áp dụng cơ chế giải mã tinh chỉnh và đối soát thủ công trên 4 mẫu tiếng Nhật (`SMP-002`, `SMP-015`, `SMP-020`, `SMP-023`):

* **Hiện tượng lặp từ thoái hóa:** Đã được loại bỏ trên cả 4 mẫu được rà soát; các danh mục chức năng, điều khoản thanh toán và thông tin giao dịch được thể hiện rõ ràng, mạch lạc.
* **Hiện tượng ảo giác báo chí:** Đã triệt tiêu hoàn toàn đoạn trích dẫn báo chí ngoại lai trên mẫu bị ảnh hưởng (`SMP-015`); bản dịch mới chỉ phản ánh đúng thông tin sản phẩm và chính sách của trang.
* **Giới hạn phạm vi tái lập (Reproducibility Boundary):** Khả năng tái lập nội dung và mã băm được giới hạn chặt chẽ trong môi trường thực nghiệm cụ thể (phiên bản `transformers 4.49.0`, checkpoint mô hình pinned `0770961a...`, tham số giải mã chuẩn hóa) đối với 4 mẫu kiểm toán này. Nhóm không đưa ra tuyên bố mang tính khái quát về "tính tất định 100%" cho mọi nền tảng phần cứng hoặc toàn bộ mô hình MarianMT nói chung.
* **Mức độ khẳng định khoa học:** C xác nhận các lỗi quan sát cụ thể **đã giảm hoặc không còn xuất hiện trên 4 mẫu đã kiểm trong môi trường thực nghiệm này**. Nhóm nghiên cứu tuyệt đối không khẳng định giải pháp này "loại bỏ 100% mọi ảo giác dịch máy trên toàn bộ không gian ngôn ngữ", vì dịch máy nơ-ron luôn tiềm ẩn xác suất ngoại lệ đối với văn bản web phi chuẩn.

---

## 5. Khuyến nghị Hướng dẫn Codebook v1.1 cho Người gán nhãn (A & B)

1. **Bản dịch là công cụ trợ đọc phụ trợ (`auxiliary reading aid`):**
   - Annotator luôn được cung cấp song song nguyên văn tiếng Nhật và bản dịch tiếng Anh.
   - Annotator tuyệt đối không suy diễn các cấu trúc ngữ pháp lạ hoặc từ ghép không tự nhiên của dịch máy thành bằng chứng lừa đảo hoặc an toàn.
2. **Quy tắc quan sát đa chiều:**
   - Việc xác định nhãn lớp và kiểu tấn công phải căn cứ trên: URL/eTLD+1, sự hiện diện của biểu mẫu thu thập thông tin xác thực/thanh toán, và bằng chứng mạo danh thương hiệu trong danh mục 14 tổ chức.
   - Nếu bản dịch gây khó hiểu, annotator ghi chú `ambiguous_translation` và đánh giá dựa trên cấu trúc quan sát được hoặc chuyển QC.

---

## 6. Danh mục Artifacts & Mã băm Đối soát

* **Bản dịch sạch v1.1:**
  - Tệp: `data/raw/recovery/translation_experiment/translations_ja_en_v1.1_clean.jsonl`
  - Dung lượng: 6,127 bytes
  - SHA-256: `4c6e87f594477d112a039a886c4db519c1f325f7cedacc32a749ffda2653aa18`
* **Hồ sơ chi tiết từng mẫu:**
  - Tệp: `data/raw/recovery/translation_experiment/TRANSLATION_MANUAL_QC_DETAILS.md` (khu vực hạn chế, không commit Git)
* **Gói nghiệm thu gốc:**
  - `calibration_v1.1_final_acceptance_20261010.zip` (SHA-256: `04ebdcc11993a460927b155152c121ffe8535df3a5249aa4a2c2820e0f6b289c`) được giữ nguyên vẹn 100% làm dấu vết kiểm toán.
