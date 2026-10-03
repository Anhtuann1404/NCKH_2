# ĐỀ CƯƠNG ĐỀ TÀI NGHIÊN CỨU KHOA HỌC

**TÊN ĐỀ TÀI:** Phát hiện website phishing mạo danh tổ chức bằng học máy kết hợp URL và nội dung trang.

**Lĩnh vực nghiên cứu:** KHTN — Công nghệ thông tin, học máy và an toàn thông tin [đối chiếu phân loại của khoa].

**Loại hình đề tài:** Nghiên cứu ứng dụng, thực nghiệm định lượng.

**Thời gian thực hiện:** 6–7 tháng [bổ sung ngày bắt đầu và hạn nộp].

**Giảng viên hướng dẫn:** [Học hàm, học vị, họ tên, đơn vị công tác].

| Vai trò và phần việc phụ trách | Họ và tên | MSSV | Lớp | Khoa | Email | SĐT |
| --- | --- | --- | --- | --- | --- | --- |
| **Sinh viên chủ nhiệm (D)** — điều phối; xây dựng, huấn luyện và đánh giá mô hình; API và tiện ích trình duyệt | [Bổ sung họ tên chủ nhiệm] | [Bổ sung] | [Bổ sung] | [Bổ sung] | [Bổ sung] | [Bổ sung] |
| **Thành viên A** — gán nhãn tổ chức, bằng chứng nội dung và kiểm tra trang hợp lệ khó | [Bổ sung họ tên] | [Bổ sung] | [Bổ sung] | [Bổ sung] | [Bổ sung] | [Bổ sung] |
| **Thành viên B** — kiểm nhãn độc lập; kiểm chứng thực nghiệm, tái lập và kiểm thử hệ thống | [Bổ sung họ tên] | [Bổ sung] | [Bổ sung] | [Bổ sung] | [Bổ sung] | [Bổ sung] |
| **Thành viên C** — nguồn dữ liệu, danh mục tổ chức, công cụ gán nhãn mù, xử lý dữ liệu và chia tập | [Bổ sung họ tên] | [Bổ sung] | [Bổ sung] | [Bổ sung] | [Bổ sung] | [Bổ sung] |

Trách nhiệm, sản phẩm bàn giao và phối hợp của từng thành viên được trình bày tại mục 6.1; tiến độ thực hiện tại mục 8.

## NỘI DUNG THUYẾT MINH ĐỀ TÀI

## 1. Tóm tắt đề tài (Abstract)

Website phishing mạo danh tổ chức để đánh lừa người dùng cung cấp thông tin nhạy cảm. Đề tài xây dựng và đánh giá phương pháp phát hiện website phishing bằng học máy kết hợp URL, cấu trúc trang, văn bản và tín hiệu mạo danh tổ chức. Câu hỏi chính là liệu các tín hiệu này có cải thiện recall trên tên miền chưa gặp tại mức cảnh báo nhầm được kiểm soát hay không. Phương pháp sử dụng từ điển tên tổ chức, so khớp mờ, đối chiếu tên miền chính thức và dấu hiệu yêu cầu thông tin nhạy cảm. PhreshPhish URL–HTML làm tập thực nghiệm chính; dữ liệu Việt Nam là nhóm ứng dụng bổ sung. Nguồn chính đã thử truy cập; crawler và HTML PhishVN được khai thác theo điều kiện sử dụng để bổ sung mẫu. Phạm vi ưu tiên tiếng Anh, với danh mục khóa từ thống kê bên ngoài. Nhóm gán nhãn tổ chức độc lập, so sánh bốn cấu hình, đối chứng quy tắc và loại bỏ thành phần. Đánh giá dùng kiểm định chéo theo nhóm miền, phân tích phụ theo thời gian, kiểm soát trang gần trùng và chọn ngưỡng nội bộ. Recall và FPR thực đo được báo cáo tại ngưỡng mục tiêu 1% và 5%, kèm khoảng tin cậy. Mô hình được triển khai thành tiện ích trình duyệt, có cảnh báo kèm tín hiệu quan sát và đo độ trễ trên trang động. Sản phẩm gồm báo cáo, mã nguồn, mô hình, dữ liệu được phép chia sẻ và tiện ích demo. Đóng góp hướng tới bằng chứng thực nghiệm về bộ tín hiệu mạo danh có cấu trúc và phương án triển khai phù hợp nguồn lực.

**Từ khóa:** phishing; mạo danh tổ chức; học máy; URL; HTML; tiện ích trình duyệt.

## 2. Tính cấp thiết, ý nghĩa khoa học và thực tiễn của đề tài

### 2.1. Tính cấp thiết

Tại Việt Nam, thông tin công bố ngày 23/04/2024 trên cổng thông tin Bộ Thông tin và Truyền thông, hiện được lưu trên cổng Bộ Khoa học và Công nghệ, dẫn NCSC ghi nhận 124.579 địa chỉ website giả mạo cơ quan, tổ chức (Bộ Thông tin và Truyền thông, 2024). Số liệu phản ánh nhu cầu cảnh báo mạo danh trong nước; đơn vị là địa chỉ website được nguồn ghi nhận, không suy thành số miền độc lập hay số nạn nhân.

Website phishing khai thác tên tổ chức và nội dung đăng nhập/xác thực để thu thập thông tin người dùng. URL có thể ít dấu hiệu rõ ràng; trong khi tên tổ chức xuất hiện trên trang cũng có thể chỉ là tin tức, đại lý hoặc dịch vụ được ủy quyền. Vì vậy, cần xét đồng thời nội dung, quan hệ tên miền và ngữ cảnh yêu cầu thông tin.

PHILTER khảo sát 55 phương pháp và chỉ ra hạn chế trong kiểm chứng yêu cầu chức năng, an toàn và cảnh báo nhầm trên trang hợp lệ đa dạng (Alam et al., 2026). PhreshPhish nhấn mạnh rò rỉ dữ liệu và tỷ lệ lớp thiếu thực tế trong đánh giá (Dalton et al., 2026). Các công trình này định hướng đề tài kiểm chứng hiệu quả tại FPR kiểm soát, thay vì chỉ báo cáo accuracy.

Phạm vi tổ chức nói chung cho phép sử dụng dữ liệu quốc tế có URL–HTML và giảm phụ thuộc một nguồn nội dung có kiểm soát truy cập. Việt Nam được giữ như nhóm ứng dụng bổ sung, với kết quả phụ thuộc dữ liệu có bằng chứng thực tế.

### 2.2. Ý nghĩa khoa học

- Đo giá trị tăng thêm của tín hiệu tổ chức–tên miền–ý định so với URL, DOM và văn bản thông thường.
- Xác định đóng góp từng thành phần, phân biệt hiệu quả của mô hình học máy với quy tắc mạo danh đơn thuần.
- Cung cấp giao thức trên miền chưa gặp, có trang hợp lệ khó, kiểm soát rò rỉ và báo cáo độ bất định.

### 2.3. Ý nghĩa thực tiễn

Tiện ích hỗ trợ cảnh báo khi truy cập website có dấu hiệu phishing, giải thích bằng tín hiệu quan sát được. Dữ liệu, mã và cấu hình giúp tái lập thí nghiệm. Bộ phát hiện chung tiếp tục xử lý trường hợp ngoài danh mục tổ chức. Nhóm Việt Nam cung cấp thông tin về khả năng ứng dụng tại địa phương khi có đủ mẫu.

## 3. Tổng quan tình hình nghiên cứu và Tính mới của đề tài

### 3.1. Tổng quan các công trình liên quan

**Kết hợp URL–HTML:** D-PhishNet sử dụng kiến trúc hai nhánh GNN và BERT để khai thác URL và HTML (Jiang et al., 2025). Preprint của Vu (2026a) khảo sát kết hợp URL với TF-IDF/encoder văn bản tiếng Việt. Việc kết hợp hai nguồn đầu vào đã có tiền lệ.

**Nhận diện mạo danh:** Phishpedia đối sánh logo với thương hiệu tham chiếu và kiểm tra miền (Lin et al., 2021). PhishIntention bổ sung ý định thu thập thông tin và tương tác để xác nhận (Liu et al., 2022). PhishLLM khai thác quan hệ thương hiệu–miền và ý định bằng LLM, kết hợp xác minh qua tìm kiếm (Liu et al., 2024). KnowPhish sử dụng tri thức thương hiệu đa phương thức và khai thác thông tin trong HTML (Li et al., 2024). Mishra và Varshney (2025) còn đánh giá hiệu quả các đặc trưng xác định miền thương hiệu; đây là tiền lệ gần về đánh giá nhóm đặc trưng, được xác minh ở mức tóm tắt preprint. Các công trình là nền tảng cho biểu diễn danh tính–miền–ý định; đề tài chọn phương án quy tắc/từ điển có cấu trúc và mô hình nhẹ để kiểm chứng giá trị tăng thêm trong phạm vi cụ thể.

**Dữ liệu và đánh giá:** PhreshPhish cung cấp cặp URL–HTML, benchmark giảm rò rỉ và điều chỉnh tỷ lệ lớp (Dalton et al., 2026). PHILTER mở rộng đánh giá sang yêu cầu chức năng và an toàn (Alam et al., 2026). Đề tài tiếp thu kiểm tra nhóm miền, trang gần trùng, đa dạng mẫu hợp lệ và cảnh báo nhầm.

**Nghiên cứu và dữ liệu Việt Nam:** PhishVN cung cấp bảng URL công khai cùng phần HTML–ảnh theo yêu cầu (Vu, 2026b). Nhãn lĩnh vực suy từ token URL và chất lượng nhãn phân tầng đòi hỏi kiểm chứng nội dung. Phần Background dẫn một nghiên cứu email phishing tiếng Việt chưa công bố dữ liệu; điều này không được suy thành thiếu mọi dữ liệu website quốc tế. Nguyen và Nguyen (2027; online 15/08/2026) khảo sát LLM với URL/HTML website tiếng Việt. Các nguồn này phục vụ nhóm ứng dụng bổ sung; phạm vi tổ chức và hiệu năng cụ thể chỉ được kết luận theo phần đã xác minh.

**Triển khai trình duyệt:** Linh et al. (2025) tích hợp phát hiện URL, exact/fuzzy matching và danh sách miền trong extension Chrome. Content script và declarativeNetRequest cung cấp cơ chế xử lý DOM và chặn yêu cầu theo quy tắc (Google, n.d.-a, n.d.-b). Extension demo cài cục bộ bằng Load unpacked (Google, n.d.-c).

**Phạm vi rà soát:** tổng quan có chọn lọc đến 03/10/2026, gồm nhóm từ khóa reference-based phishing detection, URL–HTML fusion, Phishpedia, PhishIntention, phishing browser extension và Vietnamese phishing website detection. Nguồn ưu tiên là nhà xuất bản, USENIX và bản thảo tác giả; nhật ký và mức xác minh lưu trong ghi chú nghiên cứu. PhreshPhish/SSRN ghi đúng trạng thái preprint; tài liệu Chrome phục vụ kỹ thuật.

### 3.2. Khoảng trống nghiên cứu và Tính mới, sáng tạo

**Định hướng phương pháp và câu hỏi kiểm chứng:** xây dựng bộ phát hiện kết hợp URL–nội dung và kiểm chứng có kiểm soát giá trị tăng thêm của một bộ tín hiệu mạo danh có cấu trúc, nhẹ và có thể giải thích, khi bổ sung vào đối chứng URL–DOM–văn bản trên miền chưa gặp, tại các ngưỡng FPR mục tiêu. Khoảng trống được đặt ở phép kiểm chứng này; các thành phần tên tổ chức, quan hệ miền và ý định đã có trong nghiên cứu trước.

- **RQ1:** Bổ sung tín hiệu mạo danh vào đối chứng URL–DOM–văn bản có tăng recall trên phishing ở tên miền chưa gặp tại ngưỡng FPR mục tiêu 1% và 5% không?
- **RQ2:** Nhóm tín hiệu tổ chức, quan hệ miền và ý định đóng góp thế nào? Hiệu quả khác nhau ra sao khi URL có hoặc không có token tổ chức?
- **RQ3:** Kết quả và cảnh báo nhầm thay đổi thế nào giữa các mẫu có tổ chức nằm trong danh mục, ngoài danh mục/chưa xác định và trang hợp lệ khó?

**Giả thuyết:** tín hiệu kết hợp giúp tăng recall, đặc biệt khi URL thiếu token tổ chức, trong khi duy trì điểm vận hành cảnh báo nhầm đã chọn. Báo cáo cả kết quả không xác nhận giả thuyết.

**Đóng góp dự kiến:** quy trình phát hiện kết hợp URL–nội dung và đặc tả bộ tín hiệu; giao thức kiểm chứng M0–M3, đối chứng quy tắc và loại bỏ thành phần; dữ liệu xử lý có kiểm kê và bằng chứng triển khai. Tính mới của phương pháp/thuật toán được xác định qua đối chiếu nghiên cứu trước và kết quả thực nghiệm, không mặc định từ việc kết hợp đặc trưng hoặc triển khai extension. Việt Nam là phân tích ứng dụng bổ sung, không là điều kiện tạo đóng góp chính; lập trình extension và ad block là phần sản phẩm.

## 4. Mục tiêu và Nội dung nghiên cứu

### 4.1. Mục tiêu

**Mục tiêu tổng quát:** xây dựng và đánh giá phương pháp phát hiện website phishing mạo danh tổ chức bằng học máy kết hợp URL và nội dung trang, triển khai thành tiện ích trình duyệt cảnh báo. Thực nghiệm so sánh và loại bỏ thành phần được dùng để kiểm chứng hiệu quả và vai trò của tín hiệu mạo danh.

**Mục tiêu cụ thể:**

1. Xây dựng tập URL–HTML quốc tế có kiểm kê chất lượng, nguồn, phiên bản, nhãn và nhóm miền; bổ sung nhóm Việt Nam khi đủ bằng chứng.
2. Đặc tả danh mục chính thức và bộ tín hiệu mạo danh, có xử lý tên không xác định.
3. Xây dựng các cấu hình M0–M3 và đối chứng quy tắc; so sánh hiệu quả phát hiện, báo cáo recall/FPR, loại bỏ thành phần và khoảng tin cậy.
4. Tạo tiện ích demo; đo p50/p95 độ trễ và kiểm tra nội dung động.

Cỡ mẫu và độ trễ là mục tiêu tham chiếu; cam kết của đề tài là quy trình và sản phẩm tại mục 7.

### 4.2. Nội dung nghiên cứu

Rà soát công trình; lựa chọn phiên bản dữ liệu và codebook; làm sạch, kiểm nhãn và nhóm miền; lập danh mục chính thức; xây dựng đặc trưng/mô hình; đánh giá và phân tích lỗi; triển khai demo; hoàn thiện báo cáo và hướng dẫn tái lập.

Ưu tiên: **lõi** là dữ liệu quốc tế, danh mục, M0–M3 và loại bỏ thành phần; **tầng 2** là extension/độ trễ; **tầng 3** là encoder, ad block và phân tích Việt Nam nếu tiến độ/dữ liệu cho phép. OCR và khảo sát người dùng là hướng phát triển tiếp.

## 5. Đối tượng, phạm vi và Phương pháp nghiên cứu

### 5.1. Đối tượng và phạm vi

**Đối tượng:** website phishing mạo danh tổ chức và website hợp lệ, với đầu vào URL, HTML lưu trữ/DOM và văn bản. Dữ liệu quốc tế là tập chính; phương pháp không giới hạn tên miền hoặc tổ chức ở Việt Nam. “Tổ chức” gồm doanh nghiệp, thương hiệu dịch vụ và cơ quan/dịch vụ công có danh tính–miền được xác minh từ nguồn chính thức.

**Giới hạn thực nghiệm:** ưu tiên nội dung tiếng Anh trong tập chính để phù hợp nguồn lực; tiếng Việt và ngôn ngữ khác được gán thuộc tính và phân tích riêng khi đủ mẫu. Phạm vi quốc tế không đồng nghĩa với bao phủ mọi quốc gia, tổ chức hoặc ngôn ngữ. Kết luận gắn với dữ liệu, danh mục và ngôn ngữ đã đánh giá.

**Danh mục nhận diện và thời gian tham chiếu:** thay danh mục một quý bằng hợp các top 10 của Check Point Research cho Q4/2024 và Q1–Q4/2025 (Check Point Research, 2025a–2025d, 2026). Cửa sổ thực nghiệm dự kiến từ 01/10/2024 đến 31/12/2025, tương ứng năm quý này; chọn trước để giảm phụ thuộc dao động một quý, không theo số mẫu từng thương hiệu. Các báo cáo là thống kê bên ngoài, không bảo đảm tỷ lệ phủ trong PhreshPhish. Sau chuẩn hóa thương hiệu con theo codebook tại 5.2c, danh mục gồm 14 mã: Microsoft, Google, Apple, Amazon, Meta, LinkedIn, Adobe, Booking, PayPal, DHL, Spotify, Alibaba, Mastercard và X/Twitter. LinkedIn giữ mã riêng; Facebook/Instagram/WhatsApp quy về Meta. Mốc 10 thương hiệu Q4/2025 cũ được thay bằng danh mục này, không điều chỉnh theo kết quả.

Trước khi mở URL, nhãn, target hoặc HTML của tập chính, C chỉ kiểm kê cột `date` của revision nguồn: min/max, số bản ghi theo tháng và tỷ lệ thiếu/sai ngày; lưu log cho quyết định cửa sổ. Chỉ khoảng ngày của 20 mẫu kỹ thuật đã kiểm là 10/07/2024–02/09/2025, không phải toàn corpus. Cửa sổ trên là kế hoạch cần xác nhận bằng kiểm kê date; nếu revision không phủ, điều chỉnh một lần theo các quý thực có và lấy hợp top 10 của tất cả quý đó, ghi lý do và khóa trước mở nhãn/nội dung/gán nhãn. Không chọn quý để tối đa tỷ lệ phủ hoặc hiệu năng. Tên miền, bí danh và quan hệ ủy quyền lấy từ nguồn chính thức, kèm phạm vi URL và loại dịch vụ.

Danh mục và quy tắc chuẩn hóa được khóa bằng phiên bản/checksum sau kiểm kê date nhưng trước khi mở URL/nhãn/nội dung của tập mẫu dùng thực nghiệm, không thêm tổ chức do thấy nhiều mẫu hoặc kết quả tốt. 20 mẫu kỹ thuật đã mở không dùng để chọn danh mục và được loại khỏi tập đánh giá chính. Việc tăng danh mục chỉ thuộc nhánh mở rộng được ghi riêng, không thay danh mục của phân tích chính. Báo cáo tỷ lệ phủ theo nhãn độc lập: số mẫu và miền phishing có tổ chức trong danh mục chia cho toàn bộ phishing, đồng thời báo cáo tỷ lệ chưa xác định. Một tổ chức được báo cáo riêng khi có ít nhất 5 miền phishing độc lập trong toàn tập đã kiểm chứng nhãn, đếm trước khi xem kết quả; quy tắc này chỉ quyết định báo cáo nhóm, không xây danh mục hay chọn mô hình.

**Mục tiêu dữ liệu tham chiếu:** khoảng 2.000 mẫu phishing/ít nhất 500 miền và 10.000 trang hợp lệ/ít nhất 3.000 miền, sau xử lý trùng và chất lượng; trong đó hướng tới 300 trang hợp lệ khó/ít nhất 100 miền. Các mốc định hướng lấy một tập vừa sức từ dữ liệu công khai, không phải số mẫu đã có hay bảo đảm độ đủ thống kê. Báo cáo cả tập tổng thể và nhóm mạo danh được xác minh, kèm số trang/miền; độ đủ cho RQ1 và phân nhóm phụ thuộc thành phần thực tế sau kiểm kê.

Trong hai tuần đầu, kiểm tra chất lượng nội dung, nhãn, độ đa dạng và số mẫu theo tổ chức để khóa quy mô thực nghiệm. Nhóm Việt Nam có mốc khảo sát riêng khoảng 150 phishing/50 miền; nếu dưới mốc, chỉ báo cáo mô tả hoặc thăm dò, không ảnh hưởng phép kiểm chứng chính đã đăng ký trên dữ liệu quốc tế. Nếu thu được đủ dữ liệu, nhóm Việt Nam được đánh giá như nhánh bổ sung với danh mục mở rộng lập từ nguồn bên ngoài, được khóa trước khi gán nhãn và đánh giá; báo cáo riêng và không gộp vào kết quả chính. Phương án thay nguồn luôn giữ lõi URL–nội dung–tín hiệu mạo danh.

### 5.2. Phương pháp nghiên cứu

#### a. Nguồn, lựa chọn mẫu và quản lý dữ liệu

**Nguồn chính:** PhreshPhish có cặp URL–HTML và nhãn nguồn. Tập chính lấy từ split train chính thức trong cửa sổ đã khóa; split test chính thức được giữ ngoài huấn luyện/chọn cấu hình và chỉ dùng kiểm tra độc lập theo điều kiện tại 5.2e. Dataset card ghi CC BY 4.0 cùng điều kiện sử dụng cho nghiên cứu chống phishing. Schema API đã kiểm tra có `sha256`, `url`, `label`, `target`, `date`, `lang`, `lang_score`, `html`; viewer công khai cũng hiển thị `target`. Trong 8 mẫu phishing thử, cột này gồm facebook, meta, swiss post và 5 giá trị other. Cột nguồn có thể thiếu hoặc khác giữa phiên bản; không coi đây là nhãn tổ chức chuẩn đã được kiểm chứng. Kiểm tra truy cập ngày 03/10/2026 đã tải 20 bản ghi không đăng nhập: 8 nhãn phish, 12 benign; 20 HTML không rỗng và 19 trích được văn bản bằng parser. Đây là thử kỹ thuật, chưa kiểm chứng nhãn hoặc hiệu năng. Bản thử API lưu checksum; tập chính sẽ khóa revision/tệp nguồn thay vì mặc định API rows tương ứng commit metadata.

Lấy mẫu theo quy tắc định trước, cân nhắc nguồn, thời gian, nhãn, tổ chức và chất lượng. Kiểm kê trước/sau lọc; không chọn mẫu theo kết quả mô hình. Nhãn target/tên tổ chức của nguồn chỉ phục vụ kiểm kê/gán nhãn, không là đầu vào M3. Không bắt buộc tải toàn bộ corpus; lấy tập đủ dùng, ghi cách lấy mẫu và điều kiện tái lập.

**Nguồn bổ sung:** PhishVN URL công khai và HTML–ảnh xin được theo thỏa thuận nghiên cứu; crawler độc lập lấy trang từ nguồn/feed cho phép truy cập. Các việc này song song với xây tập chính, không chờ tác giả mới bắt đầu nghiên cứu. Mốc 300 trang hợp lệ khó/100 miền ưu tiên tuyển từ lớp benign của cùng corpus, rồi xác minh thủ công các trường hợp trang đăng nhập, tin tức nhắc tổ chức, đại lý và SSO/thanh toán. Nếu phải tự thu từ website chính thức, phần đó là tập thử thách bổ sung, không cộng mặc định vào thí nghiệm chính. Số miền không phải quota của các thương hiệu trong danh mục: có thể gồm miền tin tức và bên liên kết hợp lệ được xác minh. Ghi tiêu chí trang khó trước khi chạy mô hình; không chọn từ ca mô hình đã dự đoán sai.

HTML lưu trữ được phân tích bằng parser, không thực thi script hoặc tải tài nguyên bên ngoài khi trích đặc trưng offline. Với crawler, dùng máy ảo/sandbox và hồ sơ riêng, lưu HTML sau dựng trang, ảnh, URL đầu/cuối, chuyển hướng, thời điểm, trạng thái và hash. Giới hạn tốc độ, dung lượng và timeout; không nhập dữ liệu thật hay gửi biểu mẫu. Trang chết/bị chặn được ghi trạng thái để đánh giá thiên lệch thu thập.

Chỉ so sánh M0–M3 trên cùng tập có đủ URL–nội dung; ghi riêng các mẫu URL-only. Kiểm tra điều kiện sử dụng, trùng liên nguồn và artefact thu thập trước kết hợp dữ liệu.

**Kiểm soát nhiễu theo nguồn:** phân tích chính chỉ dùng PhreshPhish, giữ metadata nguồn, chế độ thu (HTML thô/rendered/không rõ), thời gian và pipeline xử lý để kiểm tra khác biệt giữa hai lớp ngay cả trong cùng corpus. Hai lớp dùng chung parser và quy tắc lọc; việc chuẩn hóa không được coi là xóa hết artefact. Trong nhánh gộp dữ liệu, một nguồn/chế độ thu chỉ được tham gia so sánh gộp khi có cả hai lớp ở mỗi fold ngoài và phép chia nội bộ; kiểm tra số trang và nhóm trước chạy, giảm fold hoặc loại khỏi nhánh gộp nếu không đạt. Nhánh này luôn kèm kết quả PhreshPhish-only trên cùng tập test nền để đo tác động bổ sung. Tập crawler chỉ có benign dùng riêng để đo FPR trên trang khó, không dùng làm nguồn benign duy nhất đối lập phishing từ corpus, không chọn ngưỡng từ tập thử thách. Theo dõi phân bố độ dài HTML, script/form, thời gian và tỷ lệ lớp theo nguồn/chế độ; báo cáo các khác biệt còn tồn tại.

#### b. Gán nhãn và kiểm soát chất lượng

Nhãn gồm phishing, hợp lệ và chưa đủ bằng chứng, phân biệt thu thập thông tin nhạy cảm với dạng lừa đảo khác. Nhãn phụ: tổ chức mục tiêu, danh mục/ngoài danh mục, ngôn ngữ, token tổ chức trong URL, trạng thái biểu mẫu và chất lượng nội dung. Nhãn tổ chức tham chiếu dựa trên nội dung và nguồn chính thức, độc lập với đầu ra quy tắc/mô hình.

**Gán nhãn tổ chức cho toàn bộ phần phishing:** thành viên phụ trách dữ liệu A đọc từng trang trong khoảng 2.000 mẫu phishing được chọn, ghi tên thương hiệu/dịch vụ tự do, bằng chứng nội dung, vai trò tên (tuyên bố danh tính/nhắc đến), nhiều mục tiêu nếu có, hoặc chưa xác định/không có mục tiêu tổ chức rõ. Sau bước nhận diện tự do mới chuẩn hóa mã tổ chức và đối chiếu danh mục đã khóa. Người gán nhãn không nhìn `target` nguồn, điểm số, tên do bộ so khớp gợi ý hay đầu ra M0–M3/B-rule. Thành viên C, khác A và B, quản lý giao diện mù chỉ hiện URL–nội dung và mã mẫu; kết quả nguồn chỉ đối chiếu sau khi khóa lượt nhãn độc lập. Thiếu nội dung để xác nhận tổ chức được giữ là chưa xác định, không tự gán ngoài danh mục.

Người kiểm nhãn B gán độc lập mẫu con 30% phishing ngẫu nhiên phân tầng theo nguồn/ngôn ngữ và các ca khó chuyển thêm; kappa tên tổ chức tính trên mẫu ngẫu nhiên, trước phân xử, với mã chuẩn hóa theo cùng codebook, không gộp ca khó thêm. Nhóm phân xử bất đồng bằng bằng chứng; lưu nhãn trước/sau phân xử. Các trang hợp lệ khó được A kiểm toàn bộ và B kiểm 30% ngẫu nhiên cùng ca khó. Nhãn phụ của benign dùng cho RQ3 phải được đọc tay hoặc để chưa xác định; không dùng cờ nhận diện của M3 làm nhãn tham chiếu.

**Ước lượng công sức:** trong T1, A/B đo thời gian gán nhãn trên 20 mẫu kỹ thuật đã tải (8 phishing, 12 benign), rồi bổ sung 12 phishing ngoài tập đánh giá để có pilot 20 phishing. Ghi thời gian đọc, tra cứu, chuẩn hóa và phân xử; dùng thời gian theo từng loại, không suy từ thời gian parser. Chưa đo thực tế: giả định lập kế hoạch 3–5 phút/phishing tương ứng khoảng 100–167 giờ người cho A và 30–50 giờ người cho B kiểm 600 mẫu, chưa gồm ca khó, benign và sửa codebook. Nhóm có từ 4 người theo xác nhận của sinh viên: A, B, C là ba người khác nhau; thành viên D là chủ nhiệm, phụ trách xây dựng–huấn luyện–đánh giá mô hình và API–tiện ích/đo hệ thống. Ở 7 tuần, riêng A cần khoảng 14–24 giờ/tuần cho 2.000 trang theo giả định này; số thành viên không tự bảo đảm đủ giờ. Bố trí công việc nhãn trong 6–8 tuần và khai báo ngân sách giờ của A/B. Quy tắc chốt sau pilot, trước chọn tập cuối: nếu thời gian trung bình tính cả tra cứu/chuẩn hóa vượt 5 phút/phishing hoặc ngân sách A/B không đủ cho 2.000 + kiểm chéo 30% + phần dự phòng benign/ca khó, giảm mục tiêu xuống khoảng 1.200 phishing (mốc miền tham chiếu khoảng 300). Với 1.200 và 3–5 phút/trang, A cần 60–100 giờ, B kiểm 360 mẫu cần 18–30 giờ, chưa gồm phần dự phòng. Nếu vẫn quá ngân sách, giảm tiếp theo thời gian pilot và giờ thực có, ghi quy mô trước xem kết quả; vẫn gán nhãn tổ chức cho toàn bộ phần phishing giữ lại và báo cáo độ phủ/cỡ mẫu, không thay bằng chỉ audit 200 mẫu.

Với tập quốc tế, kiểm tra toàn bộ mẫu được thêm thủ công và audit mẫu ngẫu nhiên phân tầng khoảng 200 bản ghi từ corpus nguồn, bao gồm mẫu hợp lệ và phishing. Một người kiểm nhãn audit; người thứ hai gán nhãn độc lập trên cùng mẫu để tính đồng thuận. Báo cáo nhãn nguồn và nhãn kiểm chứng riêng; không gọi toàn bộ corpus đã được nhóm kiểm tra thủ công. Nếu audit phát hiện vấn đề, tăng kiểm tra ở tầng liên quan hoặc loại tầng thiếu bằng chứng theo quy tắc ghi nhận trước đánh giá chính. Audit khoảng 200 mẫu này phục vụ nhãn phishing/benign, không thay việc gán nhãn tổ chức trên toàn bộ phishing; mẫu trùng giữa các quy trình không được tính là hai quan sát độc lập.

Với PhishVN, gold/silver là nhãn khởi đầu ưu tiên, vẫn xét bằng chứng nội dung. Bronze tập trung vào ứng viên mạo danh tổ chức Việt Nam; một người kiểm toàn bộ phần sử dụng, người thứ hai kiểm mẫu con 30% ngẫu nhiên phân tầng theo nguồn/nhãn sơ bộ và các ca khó chuyển kiểm tra. Sàng lọc ứng viên không chỉ dựa token URL. Bronze chưa kiểm chứng không vào huấn luyện/đánh giá chính.

Tỷ lệ đồng thuận và Cohen’s kappa tính từ lượt độc lập trước phân xử: trên mẫu audit quốc tế hoặc mẫu con ngẫu nhiên 30% của bronze, báo cáo riêng từng quy trình. Ca khó được chuyển thêm ngoài mẫu ngẫu nhiên chỉ phục vụ phân xử, không gộp vào kappa; ca khó vốn thuộc mẫu ngẫu nhiên vẫn được giữ. Chọn mẫu kiểm tra trước kết quả mô hình. Mẫu chưa đủ bằng chứng tách khỏi đánh giá xác nhận, báo cáo tỷ lệ loại và số lượng từng tầng.

#### c. Nhận diện tổ chức và tín hiệu mạo danh

**Danh mục:** mã tổ chức, tên chính thức, tên viết tắt/bí danh, tên miền và quan hệ ủy quyền, nguồn/ngày xác minh. Lập từ nguồn chính thức độc lập với tập nghiên cứu, khóa phiên bản và dùng chung mọi fold. Không bổ sung tổ chức/bí danh/miền từ toàn bộ dữ liệu kiểm thử. Nếu thử bổ sung theo dữ liệu, dựng lại riêng trong từng fold ngoài và phép chia nội bộ; đây là nhánh bổ sung.

**Codebook thương hiệu con:** nhãn lưu cả tên dịch vụ quan sát được và mã tổ chức chuẩn để không xóa thông tin. Khóa ánh xạ trước gán nhãn, dùng chung A/B; ví dụ:

| Tên quan sát trên trang | Mã chuẩn dùng tính đồng thuận/phân nhóm | Quy tắc |
| --- | --- | --- |
| Outlook, Office 365/Microsoft 365, OneDrive | Microsoft | Không suy chỉ từ hạ tầng Azure/SharePoint |
| Gmail, Google Drive | Google | Không coi tài liệu người dùng là Google tự tuyên bố danh tính |
| Facebook, Instagram, WhatsApp | Meta | Giữ tên dịch vụ ở cột riêng |
| AWS | Amazon | Tách thương hiệu dịch vụ khỏi chủ nội dung trên S3 |
| iCloud | Apple | Giữ iCloud là tên dịch vụ |
| LinkedIn | LinkedIn | Ngoại lệ cố định: mã riêng, dù thuộc Microsoft |
| Twitter, X | X/Twitter | Cùng một mã cho đổi tên |

Tên khác chỉ gộp khi có ánh xạ và bằng chứng chính thức đã khóa; chưa có thì giữ mã ngoài danh mục/chưa xác định, không đoán theo chủ sở hữu hạ tầng. Nhiều tổ chức trên trang được ghi nhiều nhãn; kappa mã tổ chức chính dùng quy tắc chọn mục tiêu của biểu mẫu/luồng lừa đảo trong codebook, còn ca không có mục tiêu chính rõ giữ mã đa mục tiêu và báo cáo riêng. Cả A/B sử dụng cùng quy tắc trước phân xử.

**Nhận diện tên:** chuẩn hóa Unicode, chữ thường và khoảng trắng; giữ văn bản gốc, thêm bản không dấu cho nhóm Việt Nam. Biến thể như o/0, i/1 được tạo bằng quy tắc cố định có kiểm soát. Khớp chính xác theo ranh giới từ trước, rồi khớp mờ. Ngưỡng khớp mờ và các tham số thích nghi với dữ liệu chỉ chọn trong chia nhóm nội bộ của fold đang chạy.

**Ngữ cảnh danh tính:** vị trí tên trong title, heading, vùng đăng nhập và nội dung chính; dấu hiệu “sign in”, “verify account”, “official portal” cùng tương đương tiếng Việt khi phân tích nhóm Việt Nam. Phân biệt tuyên bố đại diện với bài viết nhắc tổ chức; giữ nhiều ứng viên khi trang đề cập nhiều tên.

**Quan hệ miền và vai trò dịch vụ:** đối chiếu hostname, miền đăng ký và tên miền con theo ranh giới DNS; không coi tên trong path/query hoặc miền như `brand.example.net` là miền chính thức của brand. Danh mục tách (i) endpoint định danh/đăng nhập và nội dung do tổ chức trực tiếp quản lý, (ii) hạ tầng lưu trữ, biểu mẫu hoặc nội dung do khách hàng/người dùng tạo, (iii) dịch vụ được ủy quyền có bằng chứng và (iv) chưa xác minh. Loại miền có thể cần hostname + phạm vi path/endpoint, không wildcard toàn bộ tên miền của nhà cung cấp.

Ví dụ `sites.google.com`, tài liệu/biểu mẫu trên `docs.google.com`, `forms.office.com`, tenant/site trên `sharepoint.com` và tài nguyên dưới `blob.core.windows.net`/`web.core.windows.net` được coi là hạ tầng nội dung người dùng/khách hàng: quan hệ với tổ chức được trang tuyên bố là **chưa xác minh**, không là khớp danh tính chỉ vì chủ hạ tầng là Google/Microsoft. Trang hồ sơ/bài đăng trên nền tảng xã hội cũng xử lý như nội dung người dùng. Kiểm riêng endpoint đăng nhập chính thức và đích gửi biểu mẫu; tenant/tài khoản/tài liệu không được coi thuộc tổ chức mục tiêu khi chỉ suy từ tên hiển thị. Tài liệu nhà cung cấp về Sites và Azure Storage xác nhận khả năng người dùng xuất bản nội dung (Google, n.d.-d; Microsoft, n.d.).

Áp dụng cho cả M3 và B-rule: hạ tầng dùng chung không tạo tín hiệu “nhất quán đã xác minh” và không được đưa vào allowlist bỏ qua cảnh báo; giữ cờ hạ tầng dùng chung/chưa xác minh, kết hợp nội dung và ý định. Chưa xác minh không đồng nghĩa chắc chắn phishing hoặc chắc chắn bất nhất. Ngay cả endpoint first-party đã xác minh cũng không tự chứng nhận trang an toàn hay triệt tiêu tín hiệu khác. Báo cáo riêng recall/FPR trên hạ tầng dùng chung khi có mẫu, nhằm quan sát loại lỗi này.

**Ý định:** ngữ cảnh biểu mẫu đăng nhập, mật khẩu/OTP/định danh, lời yêu cầu xác thực và đích nhận dữ liệu. Biểu diễn thành tín hiệu kết hợp, tách khỏi các thống kê DOM cơ bản của M1. Tổ chức không xác định có cờ riêng; bộ phát hiện chung tiếp tục xử lý. Phương án lõi không cần NER, OCR hoặc mô hình nhận diện tổ chức riêng.

#### d. Đối chứng, mô hình và loại bỏ thành phần

| Cấu hình | Nhóm đầu vào | Mục đích |
| --- | --- | --- |
| M0 | URL | Mốc đối chứng |
| M1 | M0 + thống kê DOM | Đóng góp cấu trúc |
| M2 | M1 + văn bản thông thường | Đối chứng trực tiếp cho M3 |
| M3 | M2 + tín hiệu tổ chức–miền–ý định | Kiểm chứng RQ1 |
| B-rule | Quy tắc kết hợp danh tính–miền–ý định | Kiểm tra lợi ích của học máy so với quy tắc |

URL dùng đặc trưng từ vựng/cấu trúc; DOM dùng liên kết, biểu mẫu, iframe và quan hệ cùng/khác miền. Văn bản dùng TF-IDF từ/char n-gram; Logistic Regression là mô hình đầu tiên. Thử thêm LightGBM cho M2–M3, dùng biểu diễn văn bản phù hợp; SVD nếu có chỉ fit ở phần huấn luyện. Hai cấu hình trong cùng họ mô hình dùng cùng biểu diễn, phân chia và ngân sách tối ưu hóa. Chọn tham số/ngưỡng B-rule bằng phần nội bộ, không bằng test.

Loại khỏi đầu vào nhãn nguồn, target, tier, split, mã bản ghi, timestamp, hash và metadata phân nhóm. Với PhishVN, loại `is_https` được nguồn ghi là artefact thu thập; kiểm tra các dấu hiệu đặc thù nguồn trong tập quốc tế. Tín hiệu M3 chỉ tính từ URL–nội dung quan sát được và danh mục đã khóa, không đọc nhãn tham chiếu.

Loại bỏ lần lượt tổ chức, quan hệ miền và ý định khỏi M3; phân tích lợi ích của kết hợp tín hiệu. So khớp mờ/biến thể có ablation bổ sung nếu đủ thời gian. Encoder nhỏ hoặc đa ngữ chỉ thử sau khi TF-IDF hoàn tất, không bắt buộc cho lõi. Phishpedia/PhishIntention/PhishLLM là tiền lệ và đối chiếu phương pháp; không cam kết tái lập toàn bộ hệ thống nặng trong 6–7 tháng.

#### e. Giao thức đánh giá và thống kê

**Chống rò rỉ:** nhóm theo miền đăng ký (eTLD+1, xét nền tảng tên miền dùng chung); gộp/loại trang gần trùng về nội dung hoặc template theo quy trình định trước. Nếu nhóm gộp chứa nhiều miền, giữ toàn bộ nhóm cùng phía phân chia. Kiểm tra trùng liên nguồn, số nhóm, phân bố lớp, tổ chức và thời gian; nhãn tổ chức không được suy từ chính đầu ra mô hình để đánh giá mô hình.

**Hai phân tích chính đăng ký trước:** (A) recall/FPR và chênh M3–M2 trên toàn tập PhreshPhish đã chọn; (B) recall/chênh recall trên phishing có tổ chức trong danh mục theo nhãn độc lập. Phân tích B giữ cùng mô hình và ngưỡng đã chọn trên cùng tập benign nội bộ như A, không tối ưu lại trên tập con; báo cáo FPR trên tập benign chung và trên benign khó riêng. Ghi số trang/miền, tỷ lệ phủ, phần ngoài danh mục và chưa xác định; không dùng kết quả B thay cho kết quả toàn tập. Tỷ lệ phủ thấp vẫn được giữ và giải thích, không mở danh mục để tăng kết quả.

**Tập chính:** grouped 5-fold lặp 3 seed định trước (17, 42, 2026), cân bằng lớp khi khả thi; M0–M3/B-rule dùng cùng phân chia. Trong mỗi fold ngoài, chia nhóm nội bộ để chọn cấu hình và ngưỡng; TF-IDF, giảm chiều, tham số khớp mờ và mô hình chỉ fit/chọn từ phần huấn luyện tương ứng. Nội dung/miền trùng fold test không vào dữ liệu bổ sung của fold đó. Giảm số fold khi cấu trúc nhóm không cho phép và ghi lý do.

**Điểm vận hành:** chọn ngưỡng FPR mục tiêu 1% và 5% trên trang hợp lệ nội bộ, cố định khi đánh giá fold ngoài. Báo cáo FPR thực đo, số mẫu hợp lệ và số FP của từng tập/fold. Ngưỡng mục tiêu không bảo đảm FPR đúng trên dữ liệu mới; mức 5% là điểm so sánh nghiên cứu, không tự chọn làm ngưỡng sử dụng thực tế.

**Chỉ số:** recall, FPR, precision, F1 và PR-AUC; ưu tiên chênh recall M3–M2 và so sánh B-rule ở từng điểm vận hành. Kèm TP/FN/FP/TN, tỷ lệ lớp, kết quả từng fold/seed và dự đoán ngoài mẫu. Phân tích có/không có token URL, tổ chức trong danh mục, ngoài danh mục đã xác minh, chưa xác định, miền, lĩnh vực và trang hợp lệ khó; nhóm đủ mẫu báo cáo riêng, nhóm nhỏ báo cáo thăm dò.

**Khoảng tin cậy:** bootstrap ghép cặp theo nhóm miền/nhóm gộp, dùng cùng mẫu bootstrap cho các cấu hình. Tính chỉ số ngoài mẫu riêng mỗi seed rồi tổng hợp; không đếm dự đoán lặp của một trang thành mẫu độc lập. Khoảng tin cậy 95% phản ánh bất định mẫu với mô hình đã fit; báo cáo thêm dao động giữa fold/seed. FPR 1% và phân nhóm ít mẫu có thể vẫn bất định dù tổng tập lớn.

**Phân tích phụ theo thời gian đăng ký trước:** trên cùng tập chính có date hợp lệ, đặt hai mốc theo phân vị 60%/80% của ngày, chỉ dùng date; các trang cùng ngày không bị tách qua mốc. Phần sớm nhất huấn luyện, phần giữa chọn cấu hình/ngưỡng và phần cuối kiểm thử. Không fit TF-IDF/SVD, tối ưu tham số, chọn họ mô hình hay ngưỡng bằng phần tương lai hoặc kết quả CV chứa phần đó. Kiểm miền/nhóm gần trùng: loại bản ghi ở phần muộn trùng nhóm với phần sớm, không chuyển trang tương lai về huấn luyện; báo cáo số loại và phạm vi ngày. Điểm vận hành 1%/5% chọn trên benign giai đoạn giữa; giữ khi đo phần cuối. Nếu loại trùng làm thiếu một lớp hoặc quá ít nhóm, vẫn báo cáo cỡ mẫu/lý do không đủ để ước lượng, không chọn lại mốc bằng hiệu năng. Date được diễn giải theo metadata thời điểm thu, không khẳng định là ngày trang bắt đầu lừa đảo.

Danh mục dùng trong nhánh thời gian chỉ lấy thương hiệu từ các báo cáo đã công bố trước hoặc vào cuối giai đoạn huấn luyện; không dùng xếp hạng quý sau để cấp thông tin cho mô hình quá khứ. Các miền/bí danh/ủy quyền phải có bằng chứng có hiệu lực ở mốc đó; khi không tái dựng được phiên bản lịch sử, ghi rõ phần dùng tri thức hiện tại và giới hạn kết luận thành đánh giá hồi cứu, không tuyên bố dự báo triển khai tương lai. Nhánh này có danh mục/checksum riêng, khóa trước huấn luyện; codebook tham chiếu vẫn dùng để chấm nhãn thống nhất. Grouped k-fold chính chứng minh miền chưa gặp trong giao thức; kết quả thời gian đo chuyển sang giai đoạn thu sau, không đồng nhất hai kết luận.

**Split test chính thức:** kiểm tra độc lập thêm nếu có thể truy cập và đủ mẫu hai lớp. Khóa mô hình/ngưỡng từ split train nghiên cứu; loại test trùng miền/nhóm nội dung với dữ liệu fit, chọn ngưỡng, pilot hoặc phần đã xem để phát triển. Không dùng official test chọn danh mục/tham số. Báo cáo số trang/miền giữ lại, khoảng ngày, tỷ lệ lớp và số loại trùng; không mặc định official test là tương lai nếu date không chứng minh thứ tự. Phân tích này tách khỏi grouped k-fold và không thay phân tích phụ thời gian đã định trước.

Nhóm Việt Nam chỉ tạo phân tích riêng khi có dữ liệu đã kiểm chứng; không suy kết quả quốc tế thành hiệu quả Việt Nam. Tổ chức chưa gặp và ngôn ngữ khác là nhánh bổ sung nếu đủ dữ liệu; không suy từ grouped k-fold theo miền.

#### f. Tiện ích trình duyệt và đo hệ thống

Chrome Manifest V3 kiểm tra URL khi điều hướng, phân tích DOM khi đủ đầu vào và cập nhật khi nội dung thay đổi đáng kể, có giới hạn tần suất. Dùng mô hình nhẹ; máy chủ cục bộ là phương án demo nếu chưa chuyển mô hình sang trình duyệt. Báo cáo kiến trúc thực tế và dữ liệu truyền ra ngoài.

Cảnh báo hiển thị tín hiệu quan sát được, tránh kết luận chắc chắn tổ chức bị mạo danh từ một lần khớp tên. Trạng thái bình thường là “chưa phát hiện dấu hiệu phishing”. Đo p50/p95 từ điều hướng đến cảnh báo, từ DOM đầu vào đến kết quả, thời gian trích đặc trưng/suy luận, timeout và lỗi; ghi cấu hình máy/kết nối và số lượt đo.

Kiểm tra trang dựng phía khách, SPA, chuyển hướng và biểu mẫu xuất hiện trễ. HTML offline có thể khác DOM runtime; đo hiệu quả mô hình trên dữ liệu lưu trữ và đo chức năng/độ trễ demo được báo cáo riêng. Trang mô phỏng chỉ kiểm chức năng, không thay phishing thực để chứng minh hiệu quả. Ad block là công tắc tùy chọn, không tạo RQ hoặc thí nghiệm bật/tắt về hiệu năng phát hiện.

#### g. Rủi ro, giới hạn, đạo đức và khả năng tái lập

**Nguồn và quyền sử dụng:** tập chính dùng nguồn quốc tế đã thử truy cập. Nếu một nguồn bị hạn chế, thay bằng nguồn URL–HTML có điều kiện sử dụng phù hợp trong cùng lõi đã đăng ký. Khi chưa được cấp HTML PhishVN, nghiên cứu chính vẫn tiếp tục; crawler/nhóm Việt Nam bổ sung theo khả năng. Chưa có đầy đủ dữ liệu/nhãn kiểm chứng từ việc tải thử 20 mẫu. Nếu thiếu nội dung hợp lệ ngay cả ở nguồn thay thế, phải báo cáo hạn chế và trao đổi với giảng viên; không tự chuyển sang URL-only sau đăng ký.

**Nhãn và lấy mẫu:** audit corpus quốc tế chỉ ước lượng chất lượng nhãn phishing/benign của phần chưa được đọc tay. Nhãn tổ chức toàn bộ phishing do A gán có khoảng 70% không được B kiểm độc lập, trừ ca khó; nhiễu phần này chỉ ước lượng từ mẫu ngẫu nhiên 30%, không tự coi mọi nhãn tổ chức là ground truth tuyệt đối. Khoảng 70% bronze ngoài mẫu kiểm tra chéo chỉ có một người gán nhãn, trừ ca khó chuyển phân xử; nhiễu nhãn phần này được ước lượng gián tiếp qua mẫu ngẫu nhiên 30%, phụ thuộc tính đại diện và độ tin cậy phân xử. Đồng thuận cao không tự bảo đảm nhãn đúng. Trang chết, cloaking, cách lấy mẫu và sự tập trung theo tổ chức tạo giới hạn đại diện.

**Khái quát và triển khai:** danh mục cơ sở hợp nhiều quý, sau chuẩn hóa có 14 mã theo cửa sổ dự kiến, vẫn có thể có độ phủ thấp hoặc thiên về dịch vụ công nghệ; tiếng Anh là ngôn ngữ chính; tên lạ, chữ trong ảnh, miền bị xâm nhập và quan hệ ủy quyền chưa biết có thể gây sai. K-fold lặp không tăng số mẫu độc lập; nhóm nhỏ/FPR thấp có khoảng tin cậy rộng. Phân tích HTML lưu trữ và trạng thái trình duyệt khác nhau; kết luận phải gắn môi trường đo. Nhiễu giữa HTML thô/rendered và giữa quy trình thu hai lớp có thể tồn tại ngay trong cùng corpus; báo cáo kiểm tra nguồn/chế độ thu và kết quả tách nguồn. Tổng quan có chọn lọc và tính mới tiếp tục được đối chiếu.

Tuân thủ giấy phép/thỏa thuận; che thông tin cá nhân, token và tham số nhạy cảm trước chia sẻ. Chỉ công bố phần được phép; HTML nguy hiểm lưu tách biệt. Lưu phiên bản nguồn, codebook, danh mục, nhóm/split, seed, cấu hình, dự đoán và quy trình chống rò rỉ. Nhóm chịu trách nhiệm kiểm tra nguồn/nội dung và lưu vết hỗ trợ AI.

## 6. Năng lực nhóm thực hiện và Giảng viên hướng dẫn

### 6.1. Nhóm sinh viên

Nhóm có nền tảng Python/học máy và web/JavaScript, phát triển thêm kỹ năng NLP. Phân công nòng cốt cho bốn thành viên như sau; ký hiệu A/B/C/D được thay bằng họ tên trong hồ sơ. D là sinh viên chủ nhiệm, trực tiếp phụ trách mô hình và tích hợp hệ thống. Mỗi thành viên chịu trách nhiệm hoàn thành, lưu bằng chứng, bàn giao và viết phần báo cáo thuộc nhiệm vụ của mình.

| Thành viên | Nhiệm vụ và trách nhiệm chính | Sản phẩm phụ trách/bàn giao | Phối hợp và kiểm tra |
| --- | --- | --- | --- |
| **D — Sinh viên chủ nhiệm** | Điều phối tiến độ, tổng hợp báo cáo và trao đổi với GVHD; xây dựng đặc trưng, mô hình M0–M3 và B-rule; huấn luyện, chọn tham số/ngưỡng theo giao thức, đánh giá và phân tích kết quả; xây API, tiện ích trình duyệt và đo hệ thống | Mã/cấu hình huấn luyện–đánh giá, kết quả thực nghiệm và giới hạn; bundle mô hình; API–extension demo; báo cáo tổng hợp và hướng dẫn tái lập | C bàn giao dữ liệu/split/danh mục; B chạy lại cấu hình và kiểm thử; A hỗ trợ phân tích nội dung sau khóa nhãn; GVHD rà giao thức/diễn giải |
| **A — Gán nhãn và bằng chứng nội dung** | Gán nhãn tổ chức cho toàn bộ phishing giữ lại; ghi tên dịch vụ, mục tiêu, vai trò và bằng chứng; kiểm trang hợp lệ khó; ghi công sức và ca khó; phối hợp phân xử | Lượt nhãn A, hồ sơ bằng chứng, danh sách ca khó và thời gian pilot; bộ nhãn cuối đầy đủ sau phân xử; phần báo cáo dữ liệu/nhãn | B kiểm độc lập; C cung cấp view mù và lưu phiên bản. A không tự sửa nhãn B hoặc quyết định bất đồng một mình |
| **B — Kiểm nhãn độc lập và kiểm chứng** | Kiểm 30% mẫu ngẫu nhiên và ca khó theo codebook; giữ lượt độc lập trước phân xử. Sau khóa nhãn, kiểm kết quả đồng thuận, chạy lại cấu hình thực nghiệm đã chốt và kiểm thử API–extension | Lượt nhãn B; kiểm tra subset/đồng thuận; biên bản phân xử; báo cáo tái lập, lỗi và kịch bản kiểm thử; phần báo cáo kiểm chứng | C chuẩn bị công cụ/nhóm mẫu; A cùng phân xử; D bàn giao cấu hình, hướng dẫn và sửa lỗi. Không dùng prediction để sửa lượt nhãn độc lập hoặc chọn lại cấu hình bằng test |
| **C — Nguồn và pipeline dữ liệu** | Kiểm revision/checksum/quyền nguồn và riêng cột date; lập danh mục/codebook từ nguồn ngoài; tạo giao diện gán nhãn mù, kế hoạch lấy mẫu/kiểm chéo; làm sạch, QC, nhóm miền/trùng, tạo splits theo giao thức và quản lý phiên bản | Source/date manifests, dictionary/codebook đã khóa, view mù và công cụ đồng thuận; sample index, nhãn đã phân xử có phiên bản, group/split manifests, QC/coverage/exclusion report; phần báo cáo pipeline | A/B gán nhãn độc lập; D kiểm hợp đồng đầu vào và sử dụng dữ liệu cho model. C không tiết lộ target/nhãn nguồn/score/nhãn người kia cho A/B trong lượt độc lập |

**Nguyên tắc phối hợp:** A, B và C là ba người khác nhau; lượt gán nhãn độc lập được khóa trước khi tiếp cận đầu ra mô hình. C bàn giao dữ liệu/danh mục/groups/splits có checksum cho D; D trực tiếp xây dựng và huấn luyện mô hình, B hỗ trợ kiểm chứng/tái lập sau khóa nhãn. Bất đồng nhãn được phân xử theo bằng chứng, giữ lịch sử; không tự thay nhãn/danh mục/ngưỡng sau xem test để tăng kết quả. D tổng hợp báo cáo, còn từng thành viên viết và kiểm phần mình.

[Bổ sung họ tên, MSSV, kinh nghiệm và giờ/tuần của từng thành viên; nếu có người hỗ trợ thêm, ghi nhiệm vụ dưới người phụ trách tương ứng]. Phần phishing và kiểm chéo cần khoảng 130–217 giờ người ở mốc 2.000 hoặc 78–130 giờ người ở mốc 1.200 theo giả định 3–5 phút/trang, cộng công sức benign/phân xử; đo lại bằng pilot tại mục 5.2b trước chốt quy mô. Ngân sách giờ của D phải tính cả mô hình, API–extension và điều phối; B/C hỗ trợ kiểm thử/tái lập nhưng không thay trách nhiệm chính. Triển khai ưu tiên mô hình ở T2–T4, tích hợp thật ở T4–T5; khung demo mô phỏng có thể chuẩn bị sớm.

GPU không bắt buộc cho lõi TF-IDF; cần máy chạy trình duyệt và sandbox nếu thu trang sống. Encoder trên Colab/Kaggle là tùy chọn.

### 6.2. Giảng viên hướng dẫn

[Bổ sung chuyên môn, kinh nghiệm/công trình liên quan và hình thức hỗ trợ]. Rà codebook, danh mục, giao thức, kết quả audit và diễn giải kết quả tại các mốc chính.

## 7. Sản phẩm dự kiến và cam kết

### 7.1. Báo cáo tổng kết

Một báo cáo theo mẫu trường: tổng quan, dữ liệu, tín hiệu, giao thức, kết quả đối chứng/ablation, phân tích lỗi, demo và giới hạn; có phụ lục tái lập.

### 7.2. Sản phẩm khác

- Dữ liệu xử lý và tài liệu mô tả; chia sẻ phần được phép hoặc danh sách chỉ mục/quy trình tái tạo phù hợp điều kiện nguồn.
- Mã xử lý/thu thập, huấn luyện/đánh giá; cấu hình và mô hình.
- Extension demo, hướng dẫn cài cục bộ và kịch bản trình diễn.
- Bảng đo p50/p95 và kiểm tra nội dung động.

Encoder, công tắc ad block và phân tích Việt Nam là phần bổ sung theo nguồn lực. Không cam kết bài báo, mức recall hoặc độ trễ cố định; các giá trị được đo và báo cáo.

## 8. Kế hoạch và tiến độ thực hiện

T1–T7 tính từ ngày bắt đầu. A/B/C/D theo phân công tại mục 6.1; điền họ tên khi nhóm chốt thành viên. Người chủ trì chịu trách nhiệm sản phẩm của dòng công việc; người phối hợp hỗ trợ hoặc kiểm tra theo vai trò. Các phần dữ liệu/nhãn có thể song song sau khi hoàn tất điều kiện khóa trước đó.

| STT | Công việc | Người thực hiện | Sản phẩm | Thời gian |
| --- | --- | --- | --- | --- |
| 1 | Kiểm revision/quyền nguồn và riêng date; xác nhận cửa sổ/quý trước mở URL/nhãn/nội dung tập chính | **C chủ trì**; D rà nguồn và kế hoạch | Source manifest, date audit và quyết định cửa sổ | Tuần 1–2 T1 |
| 2 | Tổng quan, danh mục/codebook chính thức và giao thức; khóa trước gán nhãn/đánh giá | **C chủ trì danh mục/codebook**; D phụ trách giao thức thực nghiệm; A/B rà quy tắc; GVHD hỗ trợ | Danh mục/checksum, codebook, protocol và kế hoạch audit | T1 |
| 3 | Pilot có đo giờ, chốt quy mô theo ngân sách; A gán tổ chức toàn bộ phishing giữ lại, kiểm hard benign; B kiểm 30% và ca khó, audit lớp/phân xử | **A chủ trì nhãn**; B kiểm độc lập; C tạo view mù/lưu phiên bản; D điều phối quy mô | Pilot timing, quyết định cỡ mẫu, lượt nhãn độc lập/cuối và biên bản phân xử | T1–T2; pilot/chốt quy mô trong tuần 1–2 T1 |
| 4 | Làm sạch, QC, nhóm miền/trùng; kiểm đồng thuận, coverage và khóa splits | **C chủ trì**; B kiểm subset/đồng thuận; A bổ sung bằng chứng; D kiểm splits trước training | Tập chính, QC/exclusion report, group/split manifests và coverage | T1–T2 |
| 5 | Xây dựng–huấn luyện M0–M2, B-rule và pipeline chọn ngưỡng nội bộ | **D chủ trì**; C hỗ trợ dữ liệu; B chạy lại cấu hình đã chốt sau khóa nhãn | Mã/cấu hình baseline, run manifests và kết quả đối chứng | T2–T3 |
| 6 | Xây dựng–huấn luyện M3, đánh giá 1%/5%, ablation/thời gian và phân tích lỗi; official test riêng khi đủ điều kiện | **D chủ trì**; B kiểm chứng/tái lập; C kiểm provenance/splits; A hỗ trợ đọc lỗi sau khóa nhãn | Kết quả chính/thời gian, khoảng tin cậy và phân tích giới hạn | T3–T4 |
| 7 | Bundle mô hình, API–extension, DOM động và đo p50/p95 | **D chủ trì**; B kiểm thử; C kiểm dữ liệu/phiên bản | API–extension demo, bundle, hướng dẫn và số liệu hệ thống | T4–T5 |
| 8 | Nhánh Việt Nam/encoder/ad block khi phần lõi ổn định | **D điều phối**; C nguồn/danh mục riêng; A/B nhãn/kiểm chứng; D model/tích hợp | Kết quả bổ sung báo cáo riêng nếu thực hiện | T4–T6 |
| 9 | Hoàn thiện báo cáo, dữ liệu/mã được phép chia sẻ và bảo vệ | **D chủ trì tổng hợp**; A/B/C viết/kiểm phần phụ trách; cả nhóm + GVHD rà soát | Báo cáo, mô hình, tài liệu tái lập, hướng dẫn và demo | T6–T7 |

Nếu thực hiện trong 6 tháng, hoàn thiện báo cáo ở T6 và giảm phần tùy chọn. Mốc ngày 14 điều chỉnh quy mô/lịch thu thập trong phạm vi đã đăng ký; giữ ưu tiên cho dữ liệu chính, đối chứng và báo cáo.

## 9. Tài liệu tham khảo

Danh mục theo APA, dùng các nguồn đã rà tới 03/10/2026. PhreshPhish được ghi rõ là preprint; tài liệu Chrome là tài liệu kỹ thuật, không phải bằng chứng về hiệu quả phát hiện. Năm 2026 của PhreshPhish tương ứng bản v2 đang sử dụng, bản đầu công bố năm 2025. Chương của Nguyen và Nguyen mang năm 2027 theo trích dẫn chính thức của Springer, nhưng đã xuất bản online ngày 15/08/2026. SSRN được ghi rõ là preprint; metadata/tóm tắt đã đối chiếu Crossref, chưa đọc toàn văn. Ký hiệu 2026a/2026b phân biệt hai công trình của Vu.

Alam, M., Rahman, M. L., Paul, S. K., Hays, A. W., Hussain, A., Huq, M. I., & Saxena, N. (2026). SoK: PHILTER: Uncovering security and functional gaps in AI-based phishing website detection literature via an LLM-based reasoning framework. In *Proceedings of the 35th USENIX Security Symposium* (pp. 4981–5000). USENIX Association. [Trang công trình](https://www.usenix.org/conference/usenixsecurity26/presentation/alam).

Bộ Thông tin và Truyền thông. (2024, April 23). *Giả mạo website cơ quan chức năng, tổ chức tài chính để tấn công, lừa đảo*. Cổng thông tin, hiện lưu tại Bộ Khoa học và Công nghệ. [Bản tin chính thức](https://mst.gov.vn/gia-mao-website-co-quan-chuc-nang-to-chuc-tai-chinh-de-tan-cong-lua-dao-197240423101514809.htm).

Check Point Research. (2025a, January 22). *Exploring Q4 2024 brand phishing trends: Microsoft remains the top target as LinkedIn makes a comeback*. Check Point Blog. [Báo cáo Q4/2024](https://blog.checkpoint.com/research/exploring-q4-2024-brand-phishing-trends-microsoft-remains-the-top-target-as-linkedin-makes-a-comeback/).

Check Point Research. (2025b, April 21). *Microsoft dominates as top target for imitation, Mastercard makes a comeback*. Check Point Blog. [Báo cáo Q1/2025](https://blog.checkpoint.com/research/microsoft-dominates-as-top-target-for-imitation-mastercard-makes-a-comeback/).

Check Point Research. (2025c, October 16). *Microsoft dominates phishing impersonations in Q3 2025*. Check Point Blog. [Báo cáo Q3/2025](https://blog.checkpoint.com/research/microsoft-dominates-phishing-impersonations-in-q3-2025/).

Check Point Research. (2025d, July 22). *Phishing trends Q2 2025: Microsoft maintains top spot, Spotify reenters as a prime target*. Check Point Blog. [Báo cáo Q2/2025](https://blog.checkpoint.com/research/phishing-trends-q2-2025-microsoft-maintains-top-spot-spotify-reenters-as-a-prime-target/).

Check Point Research. (2026, January 15). *Microsoft remains the most imitated brand in phishing attacks in Q4 2025*. Check Point Blog. [Báo cáo thương hiệu](https://blog.checkpoint.com/research/microsoft-remains-the-most-imitated-brand-in-phishing-attacks-in-q4-2025/).

Dalton, T., Gowda, H., Rao, G., Pargi, S., Khodabakhshi, A. H., Rombs, J., Jou, S., & Marwah, M. (2026). *PhreshPhish: A real-world, high-quality, large-scale phishing website dataset and benchmark* (Version 2) [Preprint]. arXiv. [DOI: 10.48550/arXiv.2507.10854](https://doi.org/10.48550/arXiv.2507.10854). [Bản v2](https://arxiv.org/abs/2507.10854v2).

Google. (n.d.-a). *Content scripts*. Chrome for Developers. Retrieved October 3, 2026, from [tài liệu content scripts](https://developer.chrome.com/docs/extensions/develop/concepts/content-scripts).

Google. (n.d.-b). *DeclarativeNetRequest*. Chrome for Developers. Retrieved October 3, 2026, from [tài liệu API chặn yêu cầu](https://developer.chrome.com/docs/extensions/reference/api/declarativeNetRequest).

Google. (n.d.-c). *Hello World extension*. Chrome for Developers. Retrieved October 3, 2026, from [hướng dẫn cài extension cục bộ](https://developer.chrome.com/docs/extensions/get-started/tutorial/hello-world).

Google. (n.d.-d). *Publish & share your site*. Google Sites Help. Retrieved October 3, 2026, from [tài liệu Google Sites](https://support.google.com/sites/answer/6372880?hl=en).

Jiang, H., Chen, Y., Zhu, Y., Xu, X., Song, Y., & Chen, Q. (2025). D-PhishNet: A dual-branch network for URL and HTML feature fusion in phishing webpage detection. *Computer Networks, 271*, Article 111648. [DOI: 10.1016/j.comnet.2025.111648](https://doi.org/10.1016/j.comnet.2025.111648).

Li, Y., Huang, C., Deng, S., Lock, M. L., Cao, T., Oo, N., Lim, H. W., & Hooi, B. (2024). KnowPhish: Large language models meet multimodal knowledge graphs for enhancing reference-based phishing detection. In *Proceedings of the 33rd USENIX Security Symposium* (pp. 793–810). USENIX Association. [Trang công trình](https://www.usenix.org/conference/usenixsecurity24/presentation/li-yuexin).

Lin, Y., Liu, R., Divakaran, D. M., Ng, J. Y., Chan, Q. Z., Lu, Y., Si, Y., Zhang, F., & Dong, J. S. (2021). Phishpedia: A hybrid deep learning based approach to visually identify phishing webpages. In *Proceedings of the 30th USENIX Security Symposium* (pp. 3793–3810). USENIX Association. [Trang công trình](https://www.usenix.org/conference/usenixsecurity21/presentation/lin).

Linh, D. M., Chau, H. M., Thua, H. T., & Hung, T. C. (2025). Real-time browser-integrated phishing uniform resource locator detection via deep learning and fuzzy matching. *Bulletin of Electrical Engineering and Informatics, 14*(6), 4876–4889. [DOI: 10.11591/eei.v14i6.10099](https://doi.org/10.11591/eei.v14i6.10099).

Liu, R., Lin, Y., Yang, X., Ng, S. H., Divakaran, D. M., & Dong, J. S. (2022). Inferring phishing intention via webpage appearance and dynamics: A deep vision based approach. In *Proceedings of the 31st USENIX Security Symposium* (pp. 1633–1650). USENIX Association. [Trang công trình](https://www.usenix.org/conference/usenixsecurity22/presentation/liu-ruofan).

Liu, R., Lin, Y., Teoh, X., Liu, G., Huang, Z., & Dong, J. S. (2024). Less defined knowledge and more true alarms: Reference-based phishing detection without a pre-defined reference list. In *Proceedings of the 33rd USENIX Security Symposium* (pp. 523–540). USENIX Association. [Trang công trình PhishLLM](https://www.usenix.org/conference/usenixsecurity24/presentation/liu-ruofan).

Microsoft. (n.d.). *Static website hosting in Azure Storage*. Microsoft Learn. Retrieved October 3, 2026, from [tài liệu Azure Storage](https://learn.microsoft.com/en-us/azure/storage/blobs/storage-blob-static-website).

Mishra, R., & Varshney, G. (2025). *A study of effectiveness of brand domain identification features for phishing detection in 2025* [Preprint]. arXiv. [DOI: 10.48550/arXiv.2503.06487](https://doi.org/10.48550/arXiv.2503.06487).

Nguyen, A.-B., & Nguyen, A.-N. (2027). Leveraging large language models for automated online fraud detection: A case study in Vietnam. In S. Kumar, V. Singh, & M. Prasad (Eds.), *Proceedings of International Conference on Information Technology and Artificial Intelligence* (Lecture Notes in Networks and Systems, Vol. 2127, pp. 35–45). Springer. [DOI: 10.1007/978-3-032-34772-5_4](https://doi.org/10.1007/978-3-032-34772-5_4).

Vu, T. N. (2026a). *Content and URL fusion for Vietnamese phishing pages: Five encoders under a variance-corrected protocol and a strength-controlled paraphrase attack* [Preprint]. SSRN. [DOI: 10.2139/ssrn.7454637](https://doi.org/10.2139/ssrn.7454637).

Vu, T. N. (2026b). PhishVN: A time-stamped Vietnamese URL phishing dataset with impersonation-scenario labels and confidence tiers. *Data in Brief, 68*, Article 113195. [DOI: 10.1016/j.dib.2026.113195](https://doi.org/10.1016/j.dib.2026.113195).

**Ghi chú nguồn dữ liệu:** tập chính dùng PhreshPhish, lưu phiên bản, checksum và điều kiện nghiên cứu chống phishing theo dataset card. PhishVN là nguồn bổ sung; mã tái lập bài PhishVN dùng release tương ứng bài báo. [Dữ liệu PhishVN v4](https://data.mendeley.com/datasets/b97hxbxtpd/4), [mã PhishVN](https://github.com/vuthainguyen1602/phishvn), [dữ liệu PhreshPhish](https://huggingface.co/datasets/phreshphish/phreshphish).

---

**Đà Nẵng, ngày … tháng … năm 2026**

| Trưởng Khoa | Giảng viên hướng dẫn | Sinh viên chủ nhiệm |
| --- | --- | --- |
| (Ký và ghi rõ họ tên) | (Ký và ghi rõ họ tên) | (Ký và ghi rõ họ tên) |
