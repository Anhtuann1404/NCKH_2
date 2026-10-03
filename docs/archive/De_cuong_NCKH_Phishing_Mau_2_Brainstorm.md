# ĐỀ CƯƠNG ĐỀ TÀI NGHIÊN CỨU KHOA HỌC

**Bản brainstorm v0.1 — ngày 03/10/2026, để cùng tinh chỉnh**

> Bản nháp được xây dựng theo cấu trúc 9 mục của “Mẫu 2 — Đề cương chi tiết”. Đây là phương án nghiên cứu đề xuất, chưa phải hồ sơ nộp chính thức. Các giả thuyết, cỡ mẫu và mốc hiệu năng chưa được kiểm chứng. Thông tin hành chính để trống có chủ đích.

**TÊN ĐỀ TÀI ĐỀ XUẤT:** Phát hiện website phishing bằng học máy kết hợp URL và tín hiệu mạo danh trong nội dung trang, triển khai trên tiện ích trình duyệt.

**Trọng tâm nghiên cứu:** Website giả mạo ngân hàng và cơ quan nhà nước tại Việt Nam; bộ phát hiện chung vẫn được huấn luyện và đánh giá trên phishing thuộc các lĩnh vực khác.

**Lĩnh vực nghiên cứu:** KHTN — Công nghệ thông tin; hướng học máy, xử lý ngôn ngữ tự nhiên và an toàn thông tin. Cần xác nhận cách phân loại với khoa.

**Loại hình đề tài:** Nghiên cứu ứng dụng, sử dụng thiết kế thực nghiệm định lượng.

**Giảng viên hướng dẫn:** [Học hàm, học vị, họ tên, đơn vị công tác — cần bổ sung].

**Nhóm sinh viên thực hiện:**

| Vai trò | Họ và tên | MSSV | Lớp | Khoa | Email | SĐT |
| --- | --- | --- | --- | --- | --- | --- |
| Sinh viên chủ nhiệm | [Bổ sung] | [Bổ sung] | [Bổ sung] | [Bổ sung] | [Bổ sung] | [Bổ sung] |
| Thành viên, nếu có | [Bổ sung] | [Bổ sung] | [Bổ sung] | [Bổ sung] | [Bổ sung] | [Bổ sung] |

## NỘI DUNG THUYẾT MINH ĐỀ TÀI

## 1. Tóm tắt đề tài (Abstract)

Website phishing đánh lừa người dùng cung cấp thông tin nhạy cảm bằng cách mạo danh tổ chức đáng tin cậy. Đề tài nghiên cứu giá trị của tín hiệu mạo danh trong nội dung tiếng Việt khi bổ sung vào mô hình phát hiện dựa trên URL và cấu trúc trang, chú trọng ngân hàng và cơ quan nhà nước. Câu hỏi chính là liệu các tín hiệu này có tăng khả năng phát hiện trên tên miền chưa gặp tại cùng mức cảnh báo nhầm hay không. Phương pháp đề xuất kết hợp ba nhóm thông tin: tổ chức được thể hiện trong nội dung, mức độ phù hợp của tên miền với tổ chức và ý định yêu cầu dữ liệu nhạy cảm. Nhóm xây dựng dữ liệu URL–nội dung có nhãn, so sánh các cấu hình đặc trưng và thực hiện thí nghiệm loại bỏ thành phần. Dữ liệu được kiểm thử với phân tách tên miền, kiểm soát trang gần trùng và đánh giá theo thời gian khi có dấu thời gian đáng tin cậy. Mô hình được triển khai thành tiện ích Chrome có cảnh báo và chặn quảng cáo tùy chọn. Đánh giá bao gồm khả năng phát hiện, cảnh báo nhầm, độ trễ và ảnh hưởng của ad block. Sản phẩm dự kiến là mô hình, bộ dữ liệu đánh giá, mã nguồn, tiện ích và báo cáo. Đóng góp hướng tới bằng chứng thực nghiệm về tín hiệu mạo danh tiếng Việt trong điều kiện triển khai thực tế.

**Từ khóa:** phishing; mạo danh tổ chức; học máy; nội dung tiếng Việt; tiện ích trình duyệt; cảnh báo nhầm.

## 2. Tính cấp thiết, ý nghĩa khoa học và thực tiễn của đề tài

### 2.1. Tính cấp thiết

Phishing trên website khai thác sự tin tưởng của người dùng vào tên tổ chức và nội dung được trình bày. Đề tài xuất phát từ nhu cầu nhận diện những trang giả mạo nhưng có URL ít dấu hiệu rõ ràng, đặc biệt trong các tình huống yêu cầu thông tin đăng nhập, OTP hoặc thông tin định danh.

Đánh giá PHILTER trên 55 phương pháp cho thấy nhiều nghiên cứu còn thiếu bằng chứng về khả năng thích ứng, quyền riêng tư và cảnh báo nhầm trên trang hợp lệ đa dạng (Alam et al., 2026). PhreshPhish đặt vấn đề về rò rỉ dữ liệu và tỷ lệ phishing thiếu thực tế trong các bộ kiểm thử (Dalton et al., 2026). Những kết quả này định hướng đề tài chú trọng chất lượng đánh giá và khả năng sử dụng của cảnh báo.

Trong bối cảnh Việt Nam, PhishVN cung cấp dữ liệu có nhãn lĩnh vực và mức tin cậy; tuy nhiên, nhãn lĩnh vực được suy từ tên trong URL, còn phần HTML–ảnh chụp có phạm vi nhỏ hơn nhiều so với bảng URL (Vu, 2026). Điều này gợi mở nhu cầu kiểm chứng thông tin từ nội dung trang, nhất là với tên miền không chứa tên tổ chức.

### 2.2. Ý nghĩa khoa học

- Xác định giá trị tăng thêm của tín hiệu mạo danh so với URL, cấu trúc trang và văn bản thông thường.
- Phân tích vai trò riêng của tổ chức được thể hiện, quan hệ tổ chức–tên miền và ý định yêu cầu thông tin nhạy cảm.
- Đánh giá khả năng khái quát trên tên miền chưa gặp, các mẫu trang ít dấu hiệu ở URL và các trang hợp lệ dễ bị hiểu nhầm.
- Kiểm chứng ảnh hưởng của chặn quảng cáo tới đặc trưng đầu vào và kết quả phát hiện trong trình duyệt.
- Cung cấp cấu hình thực nghiệm, quy trình gán nhãn và kết quả có thể tái lập.

### 2.3. Ý nghĩa thực tiễn

- Tạo tiện ích cảnh báo khi truy cập website có dấu hiệu phishing, kèm lý do dựa trên tín hiệu quan sát được.
- Hỗ trợ phát hiện chung ở nhiều lĩnh vực, đồng thời bổ sung phân tích cho nhóm ngân hàng/cơ quan nhà nước Việt Nam.
- Cung cấp ad block tùy chọn, có công tắc theo website; tắt ad block vẫn giữ kiểm tra phishing.
- Tạo sản phẩm demo và tài liệu phục vụ giảng dạy, nghiên cứu hoặc phát triển tiếp.

Kết quả được diễn đạt theo khả năng phát hiện trong phạm vi dữ liệu và điều kiện thử nghiệm. Trạng thái “chưa phát hiện dấu hiệu phishing” không được trình bày như chứng nhận website an toàn.

## 3. Tổng quan tình hình nghiên cứu và Tính mới của đề tài

### 3.1. Tổng quan các công trình liên quan

**Hướng kết hợp URL và HTML.** D-PhishNet sử dụng kiến trúc hai nhánh GNN và Transformer/BERT để xử lý URL và HTML (Jiang et al., 2025). Công trình là tiền lệ cho kết hợp nhiều nguồn đặc trưng; việc ghép URL với nội dung không được xem là tính mới riêng của đề tài.

**Hướng nhận diện mạo danh tổ chức.** PhishLLM phân tích quan hệ thương hiệu–tên miền và ý định thu thập thông tin đăng nhập, sử dụng LLM cùng cơ chế xác minh qua tìm kiếm (Liu et al., 2024). Đề tài kế thừa cách nhìn về bất nhất danh tính, nhưng đề xuất khảo sát một bộ tín hiệu có cấu trúc, ưu tiên mô hình nhẹ và dữ liệu tiếng Việt. Các khác biệt này cần được kiểm chứng, không mặc định là ưu thế.

**Hướng dữ liệu Việt Nam.** PhishVN có 53.116 bản ghi URL, bao gồm lõi 18.997 bản ghi và phần mở rộng; tập đồng hành có 868 cặp HTML–ảnh chụp, gồm 209 mẫu phishing, truy cập theo yêu cầu. Công trình đã có nhãn lĩnh vực ngân hàng/chính phủ/thuế và phân tách theo nhóm tên miền; khoảng 91% mẫu phishing thuộc nhóm `other` do thiếu tên nhận diện trong URL (Vu, 2026). Đề tài cần kiểm kê dữ liệu có nội dung và kiểm tra nhãn tổ chức bằng bằng chứng trên trang.

**Hướng đánh giá khả năng sử dụng.** PhreshPhish kết hợp kiểm thử theo thời gian, lọc các trang tương tự và điều chỉnh tỷ lệ phishing; tài liệu này là nguồn tham khảo để xây dựng giao thức đánh giá (Dalton et al., 2026). PHILTER định hướng xem xét nhiều yêu cầu chức năng và an toàn ngoài accuracy (Alam et al., 2026).

**Hướng triển khai trình duyệt.** Chrome cung cấp content script để đọc/thay đổi DOM, service worker để xử lý sự kiện nền và `declarativeNetRequest` để chặn yêu cầu theo quy tắc (Google, n.d.-a, n.d.-b). Chặn mạng có thể xảy ra trước khi đủ nội dung để phân tích; vì vậy, hệ thống cần được thử nghiệm trên trạng thái trang thực tế khi ad block bật và tắt.

**Giới hạn của tổng quan hiện tại:** rà soát có chọn lọc, dựa trên trang nhà xuất bản/hội nghị, nội dung mở và tóm tắt công khai; chưa phải tổng quan hệ thống. Tháng đầu tiếp tục tìm công trình gần nhất về phát hiện mạo danh tiếng Việt, mô hình nhẹ và tiện ích trình duyệt. Không khẳng định đây là phương pháp đầu tiên cho Việt Nam.

### 3.2. Phân tích “khoảng trống” nghiên cứu và khẳng định Tính mới, sáng tạo của đề tài

**Khoảng trống chính đề xuất:** bằng chứng về giá trị tăng thêm của bộ tín hiệu mạo danh trong nội dung tiếng Việt đối với phát hiện phishing ở tên miền chưa gặp, đặc biệt khi URL không chứa tên tổ chức, tại cùng mức cảnh báo nhầm.

**Câu hỏi nghiên cứu chính — RQ1:** Tại cùng mức cảnh báo nhầm mục tiêu, việc bổ sung tín hiệu mạo danh tổ chức và ý định yêu cầu thông tin nhạy cảm có cải thiện recall trên website phishing tiếng Việt ở tên miền chưa gặp so với mô hình URL–DOM–văn bản thông thường không?

**Các câu hỏi hỗ trợ:**

- **RQ2:** Thành phần nào tạo giá trị tăng thêm: nhận diện tổ chức, quan hệ tên miền hay ý định yêu cầu thông tin? Hiệu quả khác nhau thế nào giữa URL có và không có tên tổ chức?
- **RQ3:** Mô hình phát hiện chung hoạt động thế nào ở nhóm ngoài ngân hàng/cơ quan nhà nước, và phần chuyên sâu có làm thay đổi khả năng phát hiện/cảnh báo nhầm ở nhóm đó không?
- **RQ4:** Khi triển khai trong trình duyệt, bật ad block và nội dung động ảnh hưởng thế nào tới kết quả và thời gian cảnh báo?

**Giả thuyết cần kiểm chứng:** bộ tín hiệu kết hợp giúp tăng recall ở nhóm mục tiêu và nhóm URL ít dấu hiệu, trong khi duy trì mức cảnh báo nhầm đã chọn; từng tín hiệu riêng lẻ có thể chưa đủ để đạt cải thiện đó.

**Đóng góp dự kiến:**

1. Bộ tín hiệu có cấu trúc về mạo danh tổ chức trong nội dung tiếng Việt, có quy tắc xử lý trường hợp không xác định được tổ chức.
2. Tập đánh giá và giao thức so sánh làm rõ giá trị tăng thêm của tín hiệu mạo danh, có các trang hợp lệ khó và phân nhóm lĩnh vực.
3. Bằng chứng thực nghiệm khi triển khai mô hình trong tiện ích, bao gồm trạng thái bật/tắt chặn quảng cáo.

Tính mới được đặt ở cách biểu diễn, dữ liệu và phép kiểm chứng cụ thể. Lập trình extension, tích hợp ad block hoặc dùng NLP tự thân chưa đủ là đóng góp mới. Kết quả không xác nhận giả thuyết vẫn phải được báo cáo và phân tích.

## 4. Mục tiêu và Nội dung nghiên cứu

### 4.1. Mục tiêu

**Mục tiêu tổng quát:** Xây dựng và đánh giá phương pháp phát hiện website phishing bằng học máy kết hợp URL, nội dung và tín hiệu mạo danh tổ chức; triển khai thành tiện ích trình duyệt, chú trọng ngân hàng/cơ quan nhà nước Việt Nam và duy trì đánh giá ở các lĩnh vực khác.

**Mục tiêu cụ thể, có thể kiểm chứng:**

1. Xây dựng tập dữ liệu ghép URL–nội dung, quy tắc gán nhãn và các phân nhóm đánh giá; ghi nhận nguồn, thời gian, mức tin cậy và số mẫu sử dụng được.
2. Xây dựng các mô hình đối chứng sử dụng cùng dữ liệu, cùng tập phân chia và cùng ngân sách tối ưu hóa.
3. Đo mức thay đổi recall tại mức FPR mục tiêu, kèm khoảng tin cậy; thực hiện loại bỏ thành phần để kiểm tra nguồn gốc cải thiện.
4. Báo cáo riêng nhóm ngân hàng, cơ quan nhà nước, lĩnh vực khác và các trang hợp lệ khó.
5. Triển khai tiện ích Chrome Manifest V3 với cảnh báo, mô tả tín hiệu, cài đặt và ad block tùy chọn.
6. Đo độ trễ, tài nguyên và lỗi chức năng trang khi bật/tắt ad block; công bố cấu hình máy và môi trường đo.

**Mốc đánh giá tạm thời, sẽ chốt sau khảo sát dữ liệu:** ưu tiên FPR mục tiêu 1%; khảo sát thêm 0,1% nếu đủ mẫu hợp lệ. Độ trễ mục tiêu ban đầu của pha nội dung là p95 không quá 2 giây tính từ khi có đầu vào DOM cần thiết đến cảnh báo, trên máy demo được ghi rõ cấu hình. Đồng thời đo thời gian từ điều hướng đến cảnh báo, kể cả thời gian chờ trang. Đây là mục tiêu kỹ thuật đề xuất, không phải kết quả đã đạt hay cam kết bảo vệ mọi lần truy cập.

### 4.2. Nội dung nghiên cứu

**Nội dung 1 — Tổng quan và đặc tả bài toán:** hoàn thiện tổng quan; định nghĩa phishing; lập danh mục trường hợp thuộc/ngoài phạm vi; chốt RQ và giao thức thí nghiệm.

**Nội dung 2 — Dữ liệu và nhãn:** kiểm kê dữ liệu công khai, xin truy cập nội dung nếu cần; xây dựng công cụ trích xuất và làm sạch; gán nhãn lĩnh vực, tổ chức được thể hiện và kiểu yêu cầu thông tin; kiểm soát trùng lặp và độ tin cậy.

**Nội dung 3 — Đặc trưng và mô hình:** xây dựng đặc trưng URL, DOM, văn bản; xây dựng tín hiệu mạo danh; huấn luyện mô hình cơ sở và mô hình đề xuất; thử một encoder văn bản nhỏ nếu nguồn lực cho phép.

**Nội dung 4 — Thực nghiệm:** đánh giá tách tên miền, theo thời gian khi có thể; phân nhóm mẫu; loại bỏ thành phần; phân tích cảnh báo nhầm và bỏ sót.

**Nội dung 5 — Tiện ích trình duyệt:** tích hợp mô hình, theo dõi điều hướng/nội dung động, cảnh báo và giải thích dựa trên tín hiệu; tích hợp ad block có công tắc độc lập.

**Nội dung 6 — Đánh giá triển khai và báo cáo:** đo hiệu quả và độ trễ trong trình duyệt; thử bật/tắt ad block; kiểm tra thao tác trang; hoàn thiện báo cáo, mã nguồn và demo.

## 5. Đối tượng, phạm vi và phương pháp nghiên cứu

### 5.1. Đối tượng và phạm vi nghiên cứu

**Đối tượng nghiên cứu:** quan hệ giữa đặc trưng URL–nội dung, tín hiệu mạo danh tổ chức và khả năng phân biệt website phishing với trang hợp lệ.

**Phạm vi nội dung:**

- Phishing qua trang web nhằm đánh lừa người dùng cung cấp thông tin đăng nhập hoặc thông tin nhạy cảm.
- Nhóm chuyên sâu: trang tiếng Việt mạo danh ngân hàng và cơ quan nhà nước; mẫu được chọn theo bằng chứng nội dung, không chỉ theo tên miền `.vn`.
- Nhóm chung: phishing thuộc email, mạng xã hội, thương mại điện tử và các dịch vụ khác, tùy dữ liệu thực có.
- Các dạng lừa đảo đầu tư, bán hàng gian dối hoặc hành vi ác ý khác được gán nhãn riêng nếu xuất hiện; không mặc định dùng chung nhãn phishing.
- Khởi đầu với URL, DOM và văn bản hiển thị. OCR/logo và mô hình thị giác lớn là phương án mở rộng nếu dữ liệu và tiến độ phù hợp.

**Phạm vi triển khai:** Chrome trên máy tính, Manifest V3; đánh giá trong môi trường thử nghiệm có kiểm soát. Phiên bản đầu có thể sử dụng API Python trên máy demo. Phiên bản suy luận hoàn toàn trong trình duyệt là lựa chọn sau khi xác định khả năng chuyển mô hình và ngân sách tài nguyên.

**Phạm vi thời gian:** 6–7 tháng kể từ mốc bắt đầu được khoa/nhóm thống nhất. Ngày thu thập, chốt dữ liệu và các khoảng huấn luyện–kiểm thử được ghi cụ thể trong báo cáo; chưa tự gán lịch hành chính.

### 5.2. Phương pháp nghiên cứu

#### a. Thiết kế nghiên cứu

Nghiên cứu thực nghiệm định lượng, kết hợp xây dựng sản phẩm và đánh giá có đối chứng. Quy trình gồm khảo sát dữ liệu, xây dựng đặc trưng, huấn luyện, đánh giá độc lập và kiểm thử triển khai.

**Đơn vị quan sát** là một bản ghi URL gắn với nội dung được chụp tại thời điểm xác định. Một tên miền có nhiều trang vẫn cần lưu URL đầy đủ. Trang đã đổi nội dung, lỗi tải hoặc không đủ bằng chứng không được tự động coi là trang hợp lệ.

#### b. Phương pháp thu thập số liệu và gán nhãn

**Nguồn dự kiến:** PhishVN cho bối cảnh Việt Nam; PhreshPhish hoặc nguồn URL–HTML công khai phù hợp cho bộ phát hiện chung; website chính thức và các trang hợp lệ khó làm đối chứng. Số lượng, điều kiện truy cập và giấy phép phải được kiểm tra trước khi sử dụng.

**Mục tiêu cỡ mẫu để khảo sát tính khả thi:** khoảng 1.000–2.000 bản chụp phishing và 3.000–5.000 bản chụp hợp lệ sau làm sạch, bằng cách kết hợp các nguồn phù hợp. Nhóm chuyên sâu hướng tới ít nhất 200 bản chụp phishing có bằng chứng nội dung, từ nhiều tên miền. Đây là mục tiêu kế hoạch, không khẳng định nguồn hiện có đáp ứng; số mẫu của tập kiểm thử còn nhỏ hơn sau phân chia. Số tên miền và mẫu giao diện độc lập được báo cáo cùng số trang.

**Các trường lưu trữ:** URL gốc, URL chuẩn hóa để so trùng, tên miền đăng ký, nguồn, thời điểm phát hiện nếu có, thời điểm chụp, ngôn ngữ, HTML/DOM, nhãn phishing, lĩnh vực, tổ chức được thể hiện, dạng yêu cầu thông tin, bằng chứng nhãn, mức tin cậy và nhóm trùng lặp. Thời điểm chụp không mặc định là thời điểm phát hiện đầu tiên.

**Gán nhãn và kiểm tra:**

- Xây dựng codebook phân biệt phishing, trang hợp lệ, lừa đảo khác và chưa đủ bằng chứng.
- Lĩnh vực/tổ chức được xác định từ bằng chứng trong nội dung; tên xuất hiện trong URL chỉ là gợi ý.
- Chọn một mẫu phân tầng dự kiến 200–300 trang để hai người đánh giá độc lập theo cùng hướng dẫn; đo mức đồng thuận và xử lý bất đồng. Việc này cần xác nhận có người hỗ trợ gán nhãn.
- Không dùng chính blacklist đang đánh giá làm bằng chứng duy nhất cho vòng kiểm tra nhãn.
- Tách các bản chụp thiếu/khác nội dung, lỗi tải và nhãn chưa chắc chắn; báo cáo tỷ lệ loại bỏ và thiên lệch do trang còn sống.

**Trang hợp lệ khó:** trang đăng nhập chính thức, bài báo nhắc tên ngân hàng/cơ quan, trang hướng dẫn thủ tục, dịch vụ xác thực bên thứ ba được xác minh, trang có biểu mẫu nhạy cảm hợp lệ và URL dài. Sự hiện diện của biểu mẫu, từ khóa OTP hoặc tên tổ chức không tự tạo nhãn phishing.

**Thu thập và xử lý:** ưu tiên bản chụp lưu trữ/sandbox và môi trường cô lập; không gửi thông tin thật vào biểu mẫu. Giảm dữ liệu cá nhân trong bản chụp; tuân thủ điều kiện sử dụng của nguồn. Nếu có khảo sát người dùng sau này, lập kế hoạch riêng với giảng viên trước khi thực hiện.

#### c. Phương pháp biểu diễn đặc trưng và mô hình

**Nhóm URL:** độ dài, thành phần tên miền/đường dẫn, số ký tự và tỷ lệ chữ số, cấu trúc tên miền phụ, biểu diễn ký tự/từ. HTTPS và đuôi tên miền được xem là tín hiệu ngữ cảnh, không phải căn cứ xác nhận an toàn.

**Nhóm DOM:** loại biểu mẫu/input, liên kết, iframe, đích gửi biểu mẫu quan sát được, tỷ lệ liên kết khác miền và vị trí văn bản liên quan. Trang dùng JavaScript gửi dữ liệu được ghi nhận như giới hạn của đặc trưng `form action`; không mặc định thiếu `action` là không thu thập thông tin.

**Nhóm văn bản:** tiêu đề, đoạn văn bản hiển thị, nhãn biểu mẫu và nút bấm. Khởi đầu bằng TF-IDF; sau đó thử một encoder văn bản có sẵn phù hợp tiếng Việt/đa ngữ. Không huấn luyện mô hình ngôn ngữ lớn từ đầu.

**Bộ tín hiệu mạo danh đề xuất:**

1. **Tổ chức được thể hiện và ngữ cảnh:** nhận diện tên/biến thể tên; phân biệt nhắc tới tổ chức với tự nhận là dịch vụ của tổ chức. Nhãn phụ và các ví dụ đối chứng giúp kiểm tra bước này.
2. **Quan hệ tổ chức–tên miền:** đối chiếu danh mục tên miền chính thức và dịch vụ được xác minh, có nguồn và ngày cập nhật. Các tên miền dịch vụ/SSO cần được xử lý; chưa xác minh được quan hệ được mã hóa là thiếu thông tin, không tự kết luận phishing.
3. **Ý định yêu cầu thông tin:** biểu diễn ngữ cảnh đăng nhập, xác thực, OTP và dữ liệu định danh, kết hợp kiểu biểu mẫu. Những từ khóa này không được dùng như quy tắc chặn độc lập.
4. **Quan hệ giữa các tín hiệu:** đưa mức phù hợp/bất nhất, ý định và mức chắc chắn nhận diện vào bộ phân loại cùng đặc trưng chung.

Danh mục tổ chức là nguồn tham chiếu được xác minh, không phải danh sách “miễn kiểm tra”. Trang thuộc tên miền quen vẫn được phân tích. Với tổ chức không xác định được, mô hình dùng đặc trưng chung và cờ thiếu thông tin.

Các đặc trưng đầu vào phải được sinh tự động từ URL, nội dung và danh mục tham chiếu tại thời điểm dự đoán. Nhãn tổ chức/ý định gán thủ công phục vụ huấn luyện bước nhận diện hoặc đánh giá sai số; không đưa nhãn thủ công của tập test vào đầu vào mô hình. Thành phần học nhận diện tổ chức/ý định cũng tuân thủ phân chia train/validation/test chung.

**Các cấu hình đối chứng:**

| Mã | Cấu hình | Vai trò |
| --- | --- | --- |
| M0 | URL | Mốc so sánh tối thiểu |
| M1 | URL + DOM | Đo giá trị cấu trúc trang |
| M2 | URL + DOM + văn bản thông thường | Đối chứng chính, kiểm soát lợi ích của việc thêm văn bản |
| M3 | M2 + bộ tín hiệu mạo danh đề xuất | Kiểm tra đóng góp cốt lõi |

M2 và M3 dùng cùng biểu diễn văn bản, thuật toán phân loại và ngân sách tối ưu hóa. Khởi đầu với Logistic Regression làm đối chứng thống nhất; so sánh thêm mô hình cây nếu phù hợp. Khi thử encoder, lặp lại cặp M2–M3 với cùng encoder để tránh gán lợi ích của deep learning cho tín hiệu mạo danh.

**Loại bỏ thành phần:** so sánh M3 đầy đủ với các cấu hình bỏ lần lượt ngữ cảnh tổ chức, quan hệ tên miền, ý định yêu cầu thông tin và đặc trưng kết hợp; giữ nguyên quy trình huấn luyện.

#### d. Phân chia dữ liệu và kiểm soát rò rỉ

- Phân chia dự kiến train/validation/test theo tỷ lệ 70/15/15, điều chỉnh sau khi biết số nhóm độc lập.
- Tách theo tên miền đăng ký; kiểm tra thêm mẫu trang/HTML gần trùng xuyên tên miền. Dùng cách xác định hậu tố công khai phù hợp với nền tảng hosting.
- Tập kiểm thử theo thời gian chỉ sử dụng các bản ghi có thời gian đáng tin cậy, đảm bảo dữ liệu kiểm thử sau dữ liệu huấn luyện. Mẫu không đủ dấu thời gian được đánh giá riêng bằng phân tách nhóm tên miền.
- So trùng giữa các nguồn, kiểm tra thiên lệch ngôn ngữ/nguồn dữ liệu và phân tích độ nhạy khi đổi nguồn trang hợp lệ.
- TF-IDF, chuẩn hóa, chọn đặc trưng và các bước học từ dữ liệu chỉ được fit trên train. Siêu tham số, hiệu chỉnh xác suất và ngưỡng quyết định được chọn bằng validation; test được giữ lại để đánh giá cuối.
- Chốt danh mục tham chiếu theo mốc thời gian và ghi rõ nguồn. Không sử dụng nhãn hoặc thông tin có được từ tập test để bổ sung danh mục trước khi đánh giá.
- Tách tình huống “tên miền chưa có trong train” với “chưa có trong blacklist tại thời điểm thu thập”; chỉ dùng tuyên bố sau nếu có bản ghi blacklist tại thời điểm đó.

#### e. Phương pháp phân tích số liệu

**Chỉ tiêu chính:** recall của M3 so với M2 tại các ngưỡng đã chọn trên validation để nhắm tới cùng FPR mục tiêu. Trên test, báo cáo cả FPR thực tế và recall; không điều chỉnh lại ngưỡng bằng test để tạo ra FPR bằng nhau.

**Chỉ tiêu bổ sung:** precision, F1, PR-AUC, ma trận nhầm lẫn, số cảnh báo nhầm trên 1.000 trang hợp lệ. Accuracy là chỉ tiêu mô tả, không phải căn cứ kết luận duy nhất. Khảo sát độ nhạy của precision với các tỷ lệ phishing giả định và ghi rõ đây không phải tỷ lệ truy cập thực của người dùng Việt Nam.

**Độ bất định:** dùng bootstrap ghép cặp theo nhóm tên miền/mẫu trang trên cùng tập kiểm thử để ước lượng khoảng tin cậy 95% của chênh lệch; kiểm tra độ ổn định qua các lần huấn luyện phù hợp. Báo cáo số mẫu mỗi nhóm. FPR nhỏ chỉ được kết luận trong giới hạn khoảng tin cậy và cỡ mẫu hợp lệ; vài trăm trang không đủ để chứng minh mức cảnh báo nhầm rất thấp.

**Phân nhóm:** ngân hàng, cơ quan nhà nước, lĩnh vực khác; URL có/không có tên tổ chức; trang hợp lệ khó; tổ chức xác định được/không xác định được. Phân tích lỗi bằng ví dụ và nguyên nhân có bằng chứng. Nếu thiếu số mẫu cơ quan nhà nước, báo cáo nhóm đó như phân tích thăm dò hoặc thu hẹp nhóm chuyên sâu sau khi trao đổi với giảng viên.

#### f. Triển khai tiện ích và đánh giá ad block

**Luồng đề xuất:** kiểm tra URL sớm; áp dụng ad block theo lựa chọn người dùng; phân tích DOM/văn bản khi có nội dung; cập nhật đánh giá khi xuất hiện biểu mẫu hoặc trạng thái mới; hiển thị cảnh báo theo kết quả. URL ít rủi ro vẫn được phân tích nội dung khi cần.

**Thành phần:** manifest; popup/cài đặt; content script; service worker; bộ trích đặc trưng; mô hình hoặc kết nối API nội bộ; quy tắc ad block. Phần chặn mạng dùng cơ chế quy tắc của trình duyệt, phần ẩn quảng cáo có thể dùng CSS. Không giả định có thể tải đầy đủ nội dung rồi chặn ngược lại các yêu cầu đã xảy ra (Google, n.d.-a, n.d.-b).

**Giao diện kết quả:** “có dấu hiệu phishing”, “chưa phát hiện dấu hiệu phishing” hoặc “chưa đủ thông tin”. Điểm số chưa hiệu chỉnh không được trình bày là xác suất chắc chắn. Giải thích gắn với các tín hiệu quan sát được; không tự suy ra tổ chức cụ thể khi không có bằng chứng.

**Đo thời gian:** ghi mốc điều hướng, có URL, có DOM cần thiết, bắt đầu trích đặc trưng, hoàn tất suy luận và hiển thị cảnh báo. Báo cáo p50/p95 từ điều hướng đến cảnh báo và từng pha; ghi riêng timeout, lỗi API và trang không phân tích được. Với trang mô phỏng, đo cảnh báo có xuất hiện trước thao tác nhập dữ liệu hay không; không tuyên bố bảo đảm mọi trang đều được cảnh báo trước khi người dùng nhập.

**Đánh giá bật/tắt ad block:** dùng cùng tập trang trong các phiên độc lập để giảm ảnh hưởng cache; cố định phiên bản quy tắc, trình duyệt và cấu hình máy. So sánh dự đoán, cảnh báo nhầm, độ trễ, tài nguyên và khả năng hoạt động của đăng nhập, biểu mẫu, nút bấm. Ghi riêng cảnh báo từ ML và tài nguyên bị chặn theo quy tắc để tránh nhầm đóng góp giữa hai phần. Đối với dữ liệu lưu trữ, các phép đo chặn mạng cần môi trường phát lại tái hiện tài nguyên; HTML đơn lẻ chỉ kiểm chứng được phần giao diện/DOM.

**Quyền riêng tư và demo:** không lưu giá trị người dùng nhập vào mật khẩu/OTP; ưu tiên xử lý cục bộ. Nếu dùng API trên máy demo, nêu rõ dữ liệu truyền, chế độ lưu và giới hạn triển khai. Demo trên trang mô phỏng có dữ liệu giả và bản chụp phù hợp, cài bằng Developer mode/Load unpacked (Google, n.d.-c). Demo minh họa luồng sản phẩm, tách khỏi bộ kiểm thử đo hiệu quả mô hình.

#### g. Rủi ro và phương án điều chỉnh

| Rủi ro | Dấu hiệu cần xử lý | Phương án |
| --- | --- | --- |
| Thiếu nội dung phishing tiếng Việt | Nhiều URL chết hoặc chỉ có tên miền | Kiểm kê sớm, xin nội dung theo điều kiện nguồn, bổ sung bản chụp có bằng chứng; điều chỉnh cỡ mẫu và phạm vi |
| Ít mẫu cơ quan nhà nước | Không đủ nhóm độc lập cho kiểm thử | Tăng thu thập hoặc giữ nhóm này ở mức thăm dò; chốt lại với giảng viên |
| Nhãn sai/không chắc chắn | Nội dung không hỗ trợ nhãn từ feed | Gán nhãn lại, tách mức tin cậy, làm phân tích độ nhạy |
| Thêm tín hiệu mạo danh không cải thiện | Chênh lệch nhỏ hoặc khoảng tin cậy rộng | Báo cáo kết quả âm, phân tích nguyên nhân và giới hạn |
| Encoder chậm hoặc không phù hợp | Tăng độ trễ/tài nguyên mà ít cải thiện | Giữ mô hình nhẹ làm bản chính; encoder là cấu hình thử nghiệm |
| Ad block làm hỏng trang/đổi dự đoán | Lỗi chức năng hoặc đặc trưng thay đổi | Chỉnh quy tắc, hỗ trợ tắt theo website, báo cáo ảnh hưởng |
| Lịch thực hiện bị dồn | Phần lõi chưa hoàn tất trước tháng 5 | Ưu tiên dữ liệu và thí nghiệm; giảm phần mở rộng như OCR hoặc nghiên cứu người dùng |

## 6. Năng lực của nhóm nghiên cứu và Giảng viên hướng dẫn

### 6.1. Nhóm sinh viên thực hiện

**Năng lực đã được trao đổi:** sinh viên có nền tảng Python, học máy cơ bản và lập trình web/JavaScript; mong muốn phát triển thêm kỹ năng deep learning/NLP. Các thành tích, chứng chỉ, kinh nghiệm dự án cụ thể chưa được cung cấp, cần bổ sung bằng thông tin thật.

**Kiến thức cần bồi dưỡng:** đánh giá mô hình trên dữ liệu mất cân bằng; chống rò rỉ dữ liệu; gán nhãn; biểu diễn văn bản tiếng Việt; kiểm thử extension và cơ chế Manifest V3.

**Phân công theo vai trò dự kiến:**

| Vai trò | Nhiệm vụ | Người phụ trách |
| --- | --- | --- |
| Chủ nhiệm/điều phối | Chốt giao thức, quản lý tiến độ, tổng hợp báo cáo | [Bổ sung] |
| Dữ liệu | Thu thập, làm sạch, codebook, kiểm tra nhãn | [Bổ sung] |
| Mô hình và NLP | Đặc trưng, huấn luyện, thí nghiệm loại bỏ thành phần | [Bổ sung] |
| Tiện ích và kiểm thử | Extension, API demo, ad block, đo độ trễ/lỗi trang | [Bổ sung] |
| Người đánh giá nhãn thứ hai | Gán nhãn độc lập mẫu kiểm tra | [Cần xác nhận người hỗ trợ] |

Một người có thể đảm nhiệm nhiều vai trò; chưa giả định số thành viên thực tế.

### 6.2. Thông tin giảng viên hướng dẫn

[Bổ sung họ tên, học hàm/học vị, đơn vị, hướng nghiên cứu và kinh nghiệm phù hợp]. Hướng phù hợp để tìm giảng viên là học máy/NLP, an toàn thông tin hoặc đánh giá hệ thống phần mềm. Chỉ ghi các công trình và năng lực đã được xác minh của giảng viên.

## 7. Sản phẩm cam kết của đề tài

### 7.1. Sản phẩm bắt buộc

01 báo cáo tổng kết toàn văn, bao gồm tổng quan, phương pháp, dữ liệu, thực nghiệm, sản phẩm triển khai, phân tích lỗi và giới hạn nghiên cứu.

### 7.2. Sản phẩm khác (dự kiến đưa vào cam kết sau khi chốt nguồn lực)

1. **01 bộ dữ liệu đánh giá đã xử lý**, kèm schema, nguồn, codebook, mức tin cậy và tập phân chia. Công bố phần được phép; nội dung hạn chế truy cập được mô tả điều kiện sử dụng.
2. **01 gói mô hình và mã thực nghiệm**, gồm đối chứng, mô hình đề xuất, cấu hình, môi trường chạy và mã tái tạo bảng kết quả.
3. **01 tiện ích Chrome bản demo**, có kiểm tra phishing, cảnh báo, cài đặt và ad block bật/tắt được.
4. **01 bộ kịch bản demo và tài liệu sử dụng**, cùng biên bản đo độ trễ và kiểm tra lỗi chức năng.

**Sản phẩm mở rộng:** bản thảo bài báo hoặc báo cáo hội nghị sinh viên nếu kết quả và tiến độ phù hợp. Chưa cam kết bài báo được chấp nhận, phát hành lên Chrome Web Store hoặc mô hình đạt một tỷ lệ chính xác cụ thể.

## 8. Kế hoạch thực hiện (Tiến độ chi tiết)

**Ký hiệu thời gian:** T1–T7 là tháng tương đối kể từ ngày bắt đầu được thống nhất. Nếu thời hạn là 6 tháng, ghép công việc hoàn thiện ở T7 vào cuối T6 và thu gọn phần mở rộng.

| STT | Nội dung công việc chi tiết | Người thực hiện | Sản phẩm dự kiến | Thời gian |
| --- | --- | --- | --- | --- |
| 1 | Đọc công trình gần nhất, chốt RQ, phạm vi và kế hoạch thực nghiệm | Chủ nhiệm và nhóm | Đề cương, danh mục tài liệu, giao thức sơ bộ | T1 |
| 2 | Kiểm kê quyền truy cập và chất lượng URL–HTML; xây dựng codebook; chạy thử thu thập/gán nhãn | Vai trò dữ liệu và mô hình | Báo cáo khả thi, tập pilot, quy tắc nhãn | T1–T2 |
| 3 | Thu thập/làm sạch, kiểm tra nhãn độc lập, phân nhóm và tách tập | Vai trò dữ liệu; người hỗ trợ nhãn | Dữ liệu phiên bản 1, tập train/validation/test, báo cáo nhãn | T2–T3 |
| 4 | Xây dựng M0–M2, kiểm tra thiên lệch và lỗi | Vai trò mô hình | Mô hình cơ sở, kết quả validation | T3 |
| 5 | Xây dựng tín hiệu mạo danh và M3; thử encoder; thí nghiệm loại bỏ thành phần | Vai trò mô hình/NLP | Mô hình đề xuất, bảng đối chứng và phân tích thành phần | T3–T4 |
| 6 | Xây dựng extension, API trên máy demo và ad block tùy chọn; tích hợp cảnh báo | Vai trò tiện ích | Extension phiên bản thử nghiệm, bộ trang demo | T4–T5 |
| 7 | Chốt cấu hình, đánh giá test độc lập, phân nhóm và khoảng tin cậy; đo bật/tắt ad block | Nhóm; chủ nhiệm tổng hợp | Kết quả cuối, phân tích lỗi, biên bản kiểm thử | T5–T6 |
| 8 | Viết báo cáo, hoàn thiện mã/tài liệu/demo; sửa theo góp ý của giảng viên | Chủ nhiệm và nhóm | Báo cáo toàn văn, gói tái lập, sản phẩm demo | T6–T7 |

**Các mốc quyết định:**

- **Cuối T1:** chốt khả năng lấy nội dung và điều chỉnh phạm vi; đây là mốc quyết định tính khả thi.
- **Cuối T3:** có dữ liệu chia tập và đối chứng chạy được; chốt mốc FPR/cỡ mẫu phù hợp.
- **Cuối T4:** xác định giá trị và chi phí của tín hiệu mạo danh/encoder để chọn bản triển khai.
- **Trước test cuối:** khóa cấu hình, ngưỡng và quy trình; mọi thay đổi sau khi xem test phải được ghi nhận, không coi lần đánh giá lại là kiểm thử độc lập ban đầu.

## 9. Tài liệu tham khảo

Danh mục theo APA, dùng các nguồn đã rà tới 03/10/2026. PhreshPhish được ghi rõ là preprint; tài liệu Chrome là tài liệu kỹ thuật, không phải bằng chứng về hiệu quả phát hiện. Năm 2026 của PhreshPhish tương ứng bản v2 đang sử dụng, bản đầu công bố năm 2025.

Alam, M., Rahman, M. L., Paul, S. K., Hays, A. W., Hussain, A., Huq, M. I., & Saxena, N. (2026). SoK: PHILTER: Uncovering security and functional gaps in AI-based phishing website detection literature via an LLM-based reasoning framework. In *Proceedings of the 35th USENIX Security Symposium* (pp. 4981–5000). USENIX Association. [Trang công trình](https://www.usenix.org/conference/usenixsecurity26/presentation/alam).

Dalton, T., Gowda, H., Rao, G., Pargi, S., Khodabakhshi, A. H., Rombs, J., Jou, S., & Marwah, M. (2026). *PhreshPhish: A real-world, high-quality, large-scale phishing website dataset and benchmark* (Version 2) [Preprint]. arXiv. [DOI: 10.48550/arXiv.2507.10854](https://doi.org/10.48550/arXiv.2507.10854). [Bản v2](https://arxiv.org/abs/2507.10854v2).

Google. (n.d.-a). *Content scripts*. Chrome for Developers. Retrieved October 3, 2026, from [tài liệu content scripts](https://developer.chrome.com/docs/extensions/develop/concepts/content-scripts).

Google. (n.d.-b). *DeclarativeNetRequest*. Chrome for Developers. Retrieved October 3, 2026, from [tài liệu API chặn yêu cầu](https://developer.chrome.com/docs/extensions/reference/api/declarativeNetRequest).

Google. (n.d.-c). *Hello World extension*. Chrome for Developers. Retrieved October 3, 2026, from [hướng dẫn cài extension cục bộ](https://developer.chrome.com/docs/extensions/get-started/tutorial/hello-world).

Jiang, H., Chen, Y., Zhu, Y., Xu, X., Song, Y., & Chen, Q. (2025). D-PhishNet: A dual-branch network for URL and HTML feature fusion in phishing webpage detection. *Computer Networks, 271*, Article 111648. [DOI: 10.1016/j.comnet.2025.111648](https://doi.org/10.1016/j.comnet.2025.111648).

Liu, R., Lin, Y., Teoh, X., Liu, G., Huang, Z., & Dong, J. S. (2024). Less defined knowledge and more true alarms: Reference-based phishing detection without a pre-defined reference list. In *Proceedings of the 33rd USENIX Security Symposium* (pp. 523–540). USENIX Association. [Trang công trình PhishLLM](https://www.usenix.org/conference/usenixsecurity24/presentation/liu-ruofan).

Vu, T. N. (2026). PhishVN: A time-stamped Vietnamese URL phishing dataset with impersonation-scenario labels and confidence tiers. *Data in Brief, 68*, Article 113195. [DOI: 10.1016/j.dib.2026.113195](https://doi.org/10.1016/j.dib.2026.113195).

**Ghi chú nguồn dữ liệu:** phiên bản dữ liệu và mã cần được chốt khi bắt đầu thí nghiệm, không mặc định dùng nhánh mã mới nhất thay cho phiên bản của bài báo. [Dữ liệu PhishVN v4](https://data.mendeley.com/datasets/b97hxbxtpd/4), [mã PhishVN](https://github.com/vuthainguyen1602/phishvn), [dữ liệu PhreshPhish](https://huggingface.co/datasets/phreshphish/phreshphish).

---

**Đà Nẵng, ngày … tháng … năm 2026**

| Trưởng Khoa | Giảng viên hướng dẫn | Sinh viên chủ nhiệm |
| --- | --- | --- |
| (Ký và ghi rõ họ tên) | (Ký và ghi rõ họ tên) | (Ký và ghi rõ họ tên) |

## Ghi chú brainstorm để tinh chỉnh cùng nhau

*Phần này phục vụ trao đổi, sẽ bỏ khỏi hồ sơ chính thức.*

1. **Tên đề tài:** giữ tên gọn như đầu bản nháp, hay nêu rõ ngân hàng/cơ quan nhà nước Việt Nam ngay trong tên? Ad block có thể giữ trong phần sản phẩm để tên phản ánh đúng lõi nghiên cứu.
2. **Dữ liệu:** khả năng xin phần HTML của PhishVN và số trang tiếng Việt đủ bằng chứng là việc cần kiểm tra đầu tiên; chưa thực hiện gửi thư/liên hệ tác giả trong bản nháp này.
3. **Phạm vi tổ chức:** chọn số ngân hàng/cơ quan sau kiểm kê mẫu; tránh chọn trước một danh sách dài mà mỗi tổ chức chỉ có vài trang.
4. **NLP:** ưu tiên cặp đối chứng TF-IDF trước, rồi thử một encoder nhỏ; quyết định dựa trên hiệu quả và tài nguyên.
5. **Mức cam kết:** các cỡ mẫu và mốc độ trễ là dự kiến. Cần thống nhất với giảng viên trước khi chuyển thành chỉ tiêu cam kết.
6. **Nguồn lực:** bổ sung số thành viên, khả năng có người gán nhãn độc lập, máy có GPU hay không và lịch của khoa.
7. **Ưu tiên:** dữ liệu và câu hỏi nghiên cứu là phần chính; ad block, OCR và khảo sát người dùng được điều chỉnh theo tiến độ, trong đó ad block đã được chọn là tính năng bổ sung của demo.

**Ghi nhận hỗ trợ AI:** bản brainstorm được soạn với công cụ AI hỗ trợ tổng hợp cấu trúc và tài liệu; nhóm sinh viên cần đọc, xác minh nguồn, lựa chọn phương án và chịu trách nhiệm nội dung trước khi nộp. Chưa có dữ liệu thực nghiệm hay kết quả phát hiện nào được tạo ra trong bản đề cương này.
