# ĐỀ CƯƠNG ĐỀ TÀI NGHIÊN CỨU KHOA HỌC

**TÊN ĐỀ TÀI:** Phát hiện website phishing mạo danh tổ chức Việt Nam bằng học máy kết hợp URL và tín hiệu mạo danh trong nội dung trang.

**Lĩnh vực nghiên cứu:** KHTN — Công nghệ thông tin, học máy và an toàn thông tin [đối chiếu phân loại của khoa].

**Loại hình đề tài:** Nghiên cứu ứng dụng, thực nghiệm định lượng.

**Thời gian thực hiện:** 6–7 tháng [bổ sung ngày bắt đầu và hạn nộp].

**Giảng viên hướng dẫn:** [Học hàm, học vị, họ tên, đơn vị công tác].

| Vai trò | Họ và tên | MSSV | Lớp | Khoa | Email | SĐT |
| --- | --- | --- | --- | --- | --- | --- |
| Sinh viên chủ nhiệm | [Bổ sung] | [Bổ sung] | [Bổ sung] | [Bổ sung] | [Bổ sung] | [Bổ sung] |
| Thành viên | [Bổ sung theo thực tế] | [Bổ sung] | [Bổ sung] | [Bổ sung] | [Bổ sung] | [Bổ sung] |

## NỘI DUNG THUYẾT MINH ĐỀ TÀI

## 1. Tóm tắt đề tài (Abstract)

Website phishing mạo danh tổ chức để đánh lừa người dùng cung cấp thông tin nhạy cảm. Đề tài nghiên cứu giá trị tăng thêm của tín hiệu mạo danh tổ chức Việt Nam trong nội dung trang khi bổ sung vào mô hình phát hiện dựa trên URL, cấu trúc trang và văn bản. Câu hỏi chính là liệu các tín hiệu này có cải thiện khả năng phát hiện trên tên miền chưa gặp tại cùng mức cảnh báo nhầm hay không. Phương pháp sử dụng từ điển tên tổ chức và biến thể, so khớp mờ, đối chiếu tên miền chính thức và dấu hiệu yêu cầu thông tin nhạy cảm. Nhóm thu thập dữ liệu URL–nội dung từ các nguồn công khai, kiểm tra nhãn và ghi nhận thời điểm chụp. Thực nghiệm so sánh bốn cấu hình đặc trưng, kết hợp loại bỏ thành phần để xác định nguồn gốc cải thiện. Nhóm mạo danh tổ chức Việt Nam được đánh giá bằng kiểm định chéo theo nhóm tên miền, kiểm soát trang gần trùng và báo cáo khoảng tin cậy. Các chỉ số chính gồm recall và FPR thực đo tại ngưỡng cảnh báo nhầm mục tiêu 1% và 5%. Phạm vi tổ chức được quyết định theo dữ liệu thu thập. Mô hình được triển khai thành tiện ích trình duyệt, có cảnh báo giải thích bằng tín hiệu quan sát và đo độ trễ trên trang động. Sản phẩm gồm báo cáo, dữ liệu được phép công bố, mã nguồn, mô hình và tiện ích demo. Đóng góp dự kiến là bằng chứng thực nghiệm về tín hiệu mạo danh tổ chức Việt Nam trong điều kiện dữ liệu và triển khai được mô tả rõ.

**Từ khóa:** phishing; tổ chức Việt Nam; tín hiệu mạo danh; học máy; URL; nội dung trang.

## 2. Tính cấp thiết, ý nghĩa khoa học và thực tiễn của đề tài

### 2.1. Tính cấp thiết

Website phishing tận dụng tên tổ chức, nội dung đăng nhập và lời yêu cầu xác thực để thu thập thông tin người dùng. Khi tên miền ít dấu hiệu rõ ràng, việc kiểm tra URL cần được bổ sung bằng bằng chứng trong nội dung trang.

PHILTER khảo sát 55 phương pháp và chỉ ra hạn chế trong đánh giá tính thích ứng, quyền riêng tư và cảnh báo nhầm trên trang hợp lệ đa dạng (Alam et al., 2026). PhreshPhish nhấn mạnh rò rỉ dữ liệu và tỷ lệ phishing thiếu thực tế trong kiểm thử (Dalton et al., 2026). Hai công trình định hướng xây dựng phép so sánh có kiểm soát, thay vì chỉ báo cáo accuracy.

PhishVN cung cấp dữ liệu Việt Nam, nhưng nhãn lĩnh vực suy từ token thương hiệu trong URL và phần nội dung có điều kiện truy cập riêng (Vu, 2026b). Nhu cầu thực nghiệm của đề tài là kiểm tra tín hiệu trên trang, đặc biệt khi tên tổ chức vắng mặt trong URL.

### 2.2. Ý nghĩa khoa học

- Đo giá trị tăng thêm của tín hiệu tổ chức–tên miền–ý định so với URL, DOM và văn bản thông thường.
- Xác định tác dụng của từng thành phần qua thực nghiệm loại bỏ, tại mức cảnh báo nhầm có kiểm soát.
- Cung cấp giao thức đánh giá trên tên miền chưa gặp và các trang hợp lệ dễ gây nhầm, có cỡ mẫu và khoảng tin cậy.

### 2.3. Ý nghĩa thực tiễn

Tiện ích cảnh báo khi người dùng truy cập trang có dấu hiệu phishing, kèm lý do quan sát được. Bộ phát hiện chung vẫn xử lý trang thuộc các lĩnh vực ngoài danh mục tổ chức. Sản phẩm phục vụ demo, giảng dạy và phát triển tiếp; dữ liệu và mã được tổ chức để tái lập thực nghiệm.

## 3. Tổng quan tình hình nghiên cứu và Tính mới của đề tài

### 3.1. Tổng quan các công trình liên quan

**Kết hợp URL và HTML:** D-PhishNet sử dụng mô hình hai nhánh kết hợp GNN và BERT để khai thác URL và HTML (Jiang et al., 2025). Công trình cho thấy kết hợp hai nguồn này đã có tiền lệ.

**Phân tích mạo danh:** PhishLLM khai thác quan hệ thương hiệu–tên miền và ý định thu thập thông tin đăng nhập, kết hợp LLM với xác minh bằng công cụ tìm kiếm (Liu et al., 2024). Đề tài sử dụng các tín hiệu tương ứng dưới dạng quy tắc và đặc trưng có cấu trúc, phù hợp với nguồn lực triển khai nhỏ.

**Dữ liệu Việt Nam:** Theo mô tả PhishVN v4, dữ liệu gồm 53.116 bản ghi URL: lõi 18.997, trong đó 2.587 phishing từ NCSC, và phần mở rộng 34.119 từ ChongLuaDao/OpenPhish. Theo mục 3.6 của bài báo, bộ đồng hành có 868 cặp HTML–ảnh, gồm 209 phishing và 659 hợp lệ, được cung cấp theo yêu cầu (Vu, 2026b). Các số này là báo cáo của tác giả về bộ nội dung có kiểm soát truy cập. Số bản ghi URL không đồng nghĩa với số trang có nội dung còn sử dụng được. Nhãn lĩnh vực cần được kiểm chứng bằng nội dung.

**Reference-based cổ điển:** Phishpedia nhận diện logo trên ảnh chụp, đối sánh với thương hiệu tham chiếu và kiểm tra miền tương ứng (Lin et al., 2021). PhishIntention bổ sung ý định thu thập thông tin đăng nhập và tương tác với trang để xác nhận ý định (Liu et al., 2022). Hai công trình cho thấy tổ chức–miền–ý định đã tạo nền tảng cho hướng nghiên cứu; đề tài cần chứng minh giá trị của biểu diễn và giao thức cụ thể.

**Tri thức thương hiệu và văn bản:** KnowPhish khai thác cơ sở tri thức thương hiệu đa phương thức cùng LLM để nhận diện thông tin thương hiệu từ HTML, bao gồm trang không có logo (Li et al., 2024). Phương án từ điển có cấu trúc của đề tài cần được đánh giá về độ bao phủ và trường hợp không nhận diện được tổ chức.

**Nghiên cứu website tiếng Việt:** Nguyen và Nguyen (2027; công bố online 15/08/2026) đánh giá LLM có sẵn trên website tiếng Việt, sử dụng pipeline lấy URL và phần HTML làm đầu vào. Preprint của Vu (2026a) khảo sát kết hợp đặc trưng URL với biểu diễn văn bản trang tiếng Việt, gồm char n-gram TF-IDF và encoder. Các công trình này là tiền lệ trực tiếp; phạm vi đề xuất tập trung vào tín hiệu mạo danh có cấu trúc và recall tại FPR kiểm soát, thay vì chỉ kết hợp URL với văn bản.

**Tiện ích và so khớp mờ:** Linh et al. (2025) tích hợp mô hình phát hiện URL, so khớp chính xác/mờ và danh sách miền trong extension Chrome trên dữ liệu PhiUSIIL. Công trình liên quan đến triển khai trình duyệt; dữ liệu PhiUSIIL không được coi là bằng chứng riêng cho hiệu quả trên tổ chức Việt Nam.

**Giao thức đánh giá:** PhreshPhish đề xuất đánh giá giảm rò rỉ và điều chỉnh tỷ lệ lớp; PHILTER mở rộng góc nhìn sang yêu cầu chức năng và an toàn (Dalton et al., 2026; Alam et al., 2026). Đề tài tiếp thu các nguyên tắc phân tách dữ liệu, kiểm tra trang hợp lệ khó và báo cáo giới hạn thực nghiệm.

**Triển khai:** Content script hỗ trợ thu thập DOM, còn declarativeNetRequest hỗ trợ chặn yêu cầu theo quy tắc (Google, n.d.-a, n.d.-b). Tiện ích demo được cài cục bộ bằng chế độ Load unpacked (Google, n.d.-c).

**Phạm vi rà soát:** tìm nguồn Việt Nam và quốc tế đến 03/10/2026 với các nhóm từ khóa “Vietnamese phishing website detection”, “Vietnam phishing website detection URL”, “phát hiện phishing tiếng Việt”, “Phishpedia”, “PhishIntention”, “reference-based phishing detection” và “Content and URL Fusion for Vietnamese Phishing Pages”. Ưu tiên nhà xuất bản, USENIX và bản thảo tác giả. Với tài liệu chỉ tiếp cận được tóm tắt/metadata, nhận định giới hạn trong phần đó; nhật ký truy vấn và mức đọc được lưu riêng. Các nguồn Chrome phục vụ triển khai kỹ thuật, không tính thay cho công trình nghiên cứu.

### 3.2. Khoảng trống nghiên cứu và Tính mới, sáng tạo

**Khoảng trống đề xuất:** cần bằng chứng thực nghiệm về giá trị tăng thêm của bộ tín hiệu mạo danh có cấu trúc (tên tổ chức–quan hệ tên miền–ý định thu thập thông tin) khi bổ sung vào đối chứng URL–DOM–văn bản, trên website mạo danh tổ chức Việt Nam ở miền chưa gặp, tại cùng điểm vận hành FPR. Các công trình đã có về fusion tiếng Việt và reference-based là đối chứng về ý tưởng; phép kiểm chứng giá trị tăng thêm, loại bỏ thành phần và kiểm soát FPR là trọng tâm đề xuất. Tổng quan sẽ tiếp tục được cập nhật trong tháng đầu.

- **RQ1:** Bổ sung tín hiệu mạo danh vào mô hình URL–DOM–văn bản có cải thiện recall trên website phishing mạo danh tổ chức Việt Nam ở tên miền chưa gặp tại ngưỡng FPR mục tiêu 1% và 5% không?
- **RQ2:** Thành phần nhận diện tổ chức, bất nhất tên miền và ý định yêu cầu thông tin đóng góp thế nào? Hiệu quả khác nhau ra sao giữa URL có và không có token tổ chức?
- **RQ3:** Việc bổ sung tín hiệu mạo danh làm thay đổi kết quả ở nhóm tổ chức được nhận diện, nhóm còn lại và các trang hợp lệ khó như thế nào?

**Giả thuyết:** sự kết hợp các tín hiệu giúp tăng recall, đặc biệt ở nhóm URL thiếu tên tổ chức, tại mức cảnh báo nhầm đã chọn.

**Đóng góp dự kiến:** bộ tín hiệu mạo danh được đặc tả rõ; tập dữ liệu và quy trình kiểm chứng nhãn mạo danh tổ chức Việt Nam; bằng chứng so sánh M0–M3 và loại bỏ thành phần trên tên miền chưa gặp. Extension là sản phẩm chuyển giao phương pháp. Độ trễ và nội dung động được đánh giá như điều kiện triển khai.

## 4. Mục tiêu và Nội dung nghiên cứu

### 4.1. Mục tiêu

**Mục tiêu tổng quát:** xây dựng và đánh giá phương pháp phát hiện phishing mạo danh tổ chức Việt Nam bằng học máy kết hợp URL và tín hiệu trong nội dung, triển khai thành tiện ích trình duyệt.

**Mục tiêu cụ thể:**

1. Thu thập, kiểm kê và kiểm chứng dữ liệu URL–nội dung, kèm nguồn, thời điểm, tên miền và mức tin cậy của nhãn.
2. Xây dựng M0–M3 trên cùng dữ liệu và giao thức, kiểm tra giá trị tăng thêm của tín hiệu mạo danh.
3. Báo cáo recall, FPR và khoảng tin cậy; phân tích URL thiếu tên tổ chức và trang hợp lệ khó.
4. Tạo tiện ích demo; đo p50/p95 độ trễ, lỗi xử lý và khả năng cập nhật khi nội dung động thay đổi.

Cỡ mẫu và độ trễ là mục tiêu tham chiếu, được điều chỉnh sau kiểm kê. Cam kết của đề tài là quy trình thực nghiệm và sản phẩm tại mục 7.

### 4.2. Nội dung nghiên cứu

- Rà soát công trình và thiết kế giao thức đánh giá.
- Thu thập, làm sạch, gán nhãn và lập danh mục tổ chức–tên miền chính thức.
- Trích đặc trưng URL, DOM, văn bản và tín hiệu mạo danh.
- Huấn luyện M0–M3, thực nghiệm loại bỏ thành phần và phân tích sai sót.
- Tích hợp mô hình vào tiện ích, đo độ trễ và kiểm tra trang động.
- Hoàn thiện báo cáo, dữ liệu công bố và hướng dẫn tái lập.

Ưu tiên thực hiện: **lõi** là dữ liệu, M0–M3 và loại bỏ thành phần; **tầng 2** là extension demo và đo độ trễ; **tầng 3** là công tắc ad block và encoder. OCR và khảo sát người dùng được đặt ở hướng phát triển tiếp.

## 5. Đối tượng, phạm vi và Phương pháp nghiên cứu

### 5.1. Đối tượng và phạm vi

**Đối tượng:** website phishing và website hợp lệ, với đầu vào URL, DOM đã dựng và văn bản hiển thị. Nhóm phân tích chính là website phishing mạo danh tổ chức Việt Nam, xác định bằng nhãn tổ chức được kiểm chứng độc lập từ nội dung và nguồn chính thức, không phụ thuộc ngôn ngữ trang; vì vậy trang tiếng Anh mạo danh ngân hàng Việt Nam vẫn thuộc nhóm chính. “Tổ chức Việt Nam” gồm cơ quan/dịch vụ công Việt Nam và tổ chức có tư cách hoạt động tại Việt Nam được xác minh bằng nguồn chính thức. Ngôn ngữ (tiếng Việt, tiếng Anh, hỗn hợp, khác) là thuộc tính phân nhóm bổ sung; tập nền bao gồm phishing ở các lĩnh vực/tổ chức khác.

**Phạm vi tổ chức:** danh mục nhận diện được lập từ nguồn chính thức. Ưu tiên ngân hàng và cơ quan/dịch vụ công khi có mẫu thực tế. Một tổ chức được báo cáo riêng khi có từ 5 tên miền phishing độc lập trở lên trong toàn bộ tập nghiên cứu đã kiểm chứng nhãn. Việc đếm chỉ dựa trên nhãn tham chiếu, thực hiện trước khi xem bất kỳ kết quả mô hình nào; nhóm ít mẫu gộp vào “khác”. Đây là quy tắc chọn phân nhóm báo cáo, không dùng để lựa chọn đặc trưng, xây danh mục nhận diện, chọn ngưỡng hay tối ưu mô hình. Danh sách nhóm báo cáo được khóa và lưu phiên bản trước thực nghiệm chính.

**Mốc khảo sát sau 14 ngày:** ít nhất 150 mẫu phishing mạo danh tổ chức Việt Nam có nội dung sử dụng được từ ít nhất 50 tên miền đăng ký độc lập, đã loại trùng. Đây là mốc quyết định tính khả thi thu thập. Nếu dưới ngưỡng, nhóm mục tiêu chuyển thành phân tích thăm dò; ưu tiên thực nghiệm tập nền có URL–nội dung phù hợp và thống nhất điều chỉnh phạm vi/tên đề tài với giảng viên.

**Mốc tham chiếu trang hợp lệ cho thực nghiệm chính:** hướng tới ít nhất 1.500 trang có nội dung từ ít nhất 500 tên miền đăng ký, gồm ít nhất 300 trang hợp lệ khó từ ít nhất 100 tên miền. Trang khó gồm bài viết nhắc tổ chức, trang đăng nhập chính thức, đại lý và cổng thanh toán/SSO đã xác minh. Báo cáo riêng số trang và miền thuộc bối cảnh tổ chức Việt Nam; kết luận FPR cho bối cảnh này dựa trên tập hợp lệ tương ứng, thay vì suy trực tiếp từ tập hợp lệ tổng thể. Các mốc là mục tiêu thu thập, không phải số mẫu đã có hoặc cam kết đạt.

Với 1.500 trang hợp lệ, FPR thực sự 1% tương ứng kỳ vọng khoảng 15 cảnh báo nhầm trên toàn tập; số mẫu chọn ngưỡng trong mỗi fold nội bộ còn nhỏ hơn. Vì vậy mốc này chưa bảo đảm ước lượng chính xác tại 1%, đặc biệt trong từng nhóm. Nếu dữ liệu hoặc khoảng tin cậy không đủ hỗ trợ kết luận ở 1%, kết quả tại mức này được báo cáo thăm dò và dùng mức 5% để bổ sung so sánh.

### 5.2. Phương pháp nghiên cứu

#### a. Thu thập và quản lý dữ liệu

Trong 1–2 tuần đầu, nhóm thực hiện song song:

1. Chốt PhishVN v4 và phiên bản mã tương ứng bài báo; tải tệp công khai, đếm bản ghi theo nhãn, nguồn, mức tin cậy, tên miền và trạng thái nội dung; lưu checksum.
2. Liên hệ tác giả xin HTML–ảnh và điều kiện sử dụng.
3. Dựng bộ thu thập nhỏ trong máy ảo/sandbox, bắt đầu chụp trang mới từ các nguồn NCSC/Tín nhiệm mạng, ChongLuaDao và OpenPhish ngay khi có quyền truy cập phù hợp; lưu HTML đã dựng và ảnh chụp.
4. Đọc tay khoảng 50 mẫu để xác định ngôn ngữ, dạng phishing, tổ chức và chất lượng nội dung.

Mỗi lần chụp lưu URL đầu vào, URL cuối, chuỗi chuyển hướng, thời điểm UTC, tên miền đăng ký, trạng thái HTTP, trạng thái chụp và hash nội dung. Trang đã chết, bị chặn hoặc không đủ bằng chứng được lưu trạng thái riêng, phục vụ phân tích thiên lệch thu thập. Bộ thu thập giới hạn thời gian, dung lượng và tốc độ; dùng hồ sơ trình duyệt tách biệt, không nhập thông tin thật hay gửi biểu mẫu.

Mẫu hợp lệ gồm website chính thức, trang đăng nhập hợp lệ và trang khó: tin tức đề cập tổ chức, đại lý, cổng thanh toán/SSO được ủy quyền. Tập nền URL–nội dung có thể bổ sung từ PhreshPhish sau khi kiểm tra giấy phép và trùng lặp liên nguồn. So sánh M0–M3 chỉ dùng tập mẫu chung có đủ đầu vào; các mẫu URL đơn lẻ được báo cáo riêng.

#### b. Gán nhãn và kiểm soát chất lượng

Nhãn nghiên cứu gồm phishing, hợp lệ và chưa đủ bằng chứng; phân biệt phishing thu thập thông tin nhạy cảm với các dạng lừa đảo khác. Nhãn feed là nguồn tham khảo, được kiểm chứng qua nội dung và bằng chứng lưu trữ. Nhãn phụ gồm ngôn ngữ trang, tổ chức bị mạo danh, lĩnh vực, token tổ chức trong URL, trạng thái biểu mẫu và chất lượng chụp.

Hai người gán nhãn độc lập trên khoảng 200 mẫu phân tầng nếu nguồn lực cho phép, ghi nhận đồng thuận và Cohen’s kappa trước khi phân xử. Mẫu “chưa đủ bằng chứng” tách khỏi đánh giá xác nhận, đồng thời báo cáo tỷ lệ loại. Các nhãn tổ chức dùng cho đánh giá được đọc tay để tránh kiểm chứng quy tắc bằng chính đầu ra của quy tắc.

#### c. Nhận diện tổ chức và tín hiệu mạo danh

**Danh mục:** mỗi tổ chức có mã định danh, tên đầy đủ, tên viết tắt, bí danh đã xác minh, tên miền chính thức, quan hệ ủy quyền có bằng chứng, nguồn và ngày xác minh. Danh mục cơ sở chỉ lấy tên, bí danh và quan hệ miền từ nguồn chính thức độc lập với tập website nghiên cứu, được khóa phiên bản trước thực nghiệm chính và dùng giống nhau ở mọi fold. Biến thể không dấu/thay ký tự được tạo bằng quy tắc cố định. Thực nghiệm chính không bổ sung tổ chức, bí danh hay quan hệ miền từ các mẫu nghiên cứu. Nếu khảo sát bổ sung từ dữ liệu, danh mục bổ sung phải được xây lại riêng trong từng fold ngoài, và trong từng fold nội bộ khi chọn cấu hình; không tái sử dụng danh mục đã học từ fold khác. Nhánh này được báo cáo như phân tích bổ sung.

**Chuẩn hóa:** Unicode, chữ thường, khoảng trắng; giữ cả văn bản gốc và bản không dấu. Tạo biến thể không dấu và thay thế ký tự thường gặp như o/0, i/1 có kiểm soát. Áp dụng so khớp chính xác theo ranh giới từ trước, sau đó so khớp mờ bằng độ tương tự chuỗi. Ngưỡng so khớp mờ và quy tắc chọn ứng viên được chọn bằng chia nhóm nội bộ của từng fold ngoài; không điều chỉnh bằng dữ liệu fold kiểm thử hoặc bằng cách đọc toàn bộ tập nghiên cứu.

**Bằng chứng danh tính:** ghi vị trí tên trong tiêu đề, heading, khu vực đăng nhập, nội dung chính và liên kết. Dùng dấu hiệu ngữ cảnh như “cổng thông tin”, “đăng nhập”, “xác thực tài khoản”, cùng các tương đương tiếng Anh như “sign in”, “verify account” để phân biệt tuyên bố đại diện với bài viết chỉ nhắc tên. Trang có nhiều tổ chức giữ nhiều ứng viên và mức độ khớp.

**Đối chiếu tên miền:** kiểm tra hostname thực, tên miền đăng ký và quan hệ tên miền con theo ranh giới DNS; tránh nhầm chuỗi tên tổ chức trong đường dẫn hoặc miền như `to-chuc.example.net`. Ghi nhận bất nhất danh tính–tên miền và đích gửi biểu mẫu; xét quan hệ thanh toán/SSO hợp lệ đã xác minh. Danh mục chính thức là bằng chứng quan hệ, không tự động chứng nhận mọi nội dung trên miền đó an toàn.

**Ý định thu thập:** trường mật khẩu/OTP/thông tin định danh, lời yêu cầu xác thực, ngữ cảnh biểu mẫu và đích nhận dữ liệu. Các tín hiệu được kết hợp thành đặc trưng có cấu trúc. Trường hợp không nhận diện được tổ chức có cờ “không xác định” và tiếp tục dùng đặc trưng phát hiện chung. Phương án lõi dùng quy tắc, từ điển và so khớp mờ, không cần huấn luyện mô hình nhận diện tổ chức riêng.

#### d. Mô hình đối chứng và thực nghiệm loại bỏ

| Mô hình | Nhóm đầu vào | Mục đích |
| --- | --- | --- |
| M0 | Đặc trưng URL | Mốc đối chứng |
| M1 | M0 + cấu trúc DOM | Đo đóng góp cấu trúc trang |
| M2 | M1 + văn bản thông thường | Đối chứng trực tiếp cho tín hiệu mạo danh |
| M3 | M2 + tổ chức, quan hệ miền, ý định | Kiểm chứng giả thuyết chính |

URL gồm độ dài, cấu trúc hostname/path/query và đặc trưng từ vựng. DOM gồm liên kết, biểu mẫu, iframe và quan hệ cùng/khác miền. Với PhishVN, loại `is_https` vì nguồn công bố xác định đây là artefact thu thập; loại cả trường nhãn, nguồn feed, mã bản ghi, split và mức tin cậy khỏi đầu vào mô hình.

Văn bản dùng TF-IDF từ và char n-gram trên văn bản gốc/không dấu; Logistic Regression là mô hình nhẹ đầu tiên. Với M2–M3, thử LightGBM trên đặc trưng có cấu trúc và biểu diễn văn bản phù hợp; nếu dùng SVD thì chỉ fit trên phần huấn luyện. Hai cấu hình M2/M3 trong mỗi họ mô hình dùng cùng cách xử lý văn bản và ngân sách tối ưu hóa.

Thực nghiệm loại bỏ lần lượt nhóm tổ chức, quan hệ miền và ý định; kiểm tra thêm vai trò so khớp mờ/chuẩn hóa khi đủ nguồn lực. PhoBERT hoặc encoder đa ngữ nhỏ chỉ thử ở T4 sau khi đối chứng TF-IDF hoàn tất; GPU Colab/Kaggle là tùy chọn.

#### e. Giao thức đánh giá và thống kê

**Phân nhóm:** dùng tên miền đăng ký (eTLD+1, xử lý nền tảng tên miền dùng chung bằng Public Suffix List phù hợp). Mẫu gần trùng về nội dung/template được gộp nhóm hoặc loại trùng; nếu liên kết nhiều miền thành cùng nhóm, giữ toàn bộ nhóm ở một phía phân chia. Kiểm tra trùng liên nguồn và báo cáo số mẫu/nhóm trước, sau xử lý.

**Nhóm Việt Nam:** ưu tiên grouped 5-fold, cân bằng lớp khi khả thi. Trong mỗi fold ngoài, dùng chia nhóm nội bộ để chọn siêu tham số và ngưỡng FPR; toàn bộ TF-IDF, giảm chiều và quy tắc điều chỉnh theo dữ liệu chỉ fit trong phần huấn luyện. Danh mục cơ sở từ nguồn chính thức được giữ cố định theo mục 5.2c; mọi tham số thích nghi với dữ liệu chỉ được chọn ở các phép chia nội bộ của fold đang chạy. Mọi dữ liệu nền bổ sung trùng miền hoặc nhóm nội dung với fold kiểm thử đều bị loại khỏi huấn luyện. Số fold có thể giảm khi cấu trúc nhóm không cho phép, kèm lý do.

**Ngưỡng:** chọn trên dữ liệu hợp lệ nội bộ cho FPR mục tiêu 1% và 5%, sau đó cố định khi đánh giá fold ngoài. Báo cáo cả FPR thực đo vì ngưỡng mục tiêu không bảo đảm đạt đúng FPR trên dữ liệu mới. Mức 5% là điểm so sánh nghiên cứu khi dữ liệu nhỏ; lựa chọn ngưỡng demo dựa trên kết quả và mức cảnh báo nhầm chấp nhận được.

**Chỉ số:** recall, FPR, precision, F1 và PR-AUC; ưu tiên mức chênh recall M3–M2 tại từng điểm vận hành. Báo cáo số trang hợp lệ và số cảnh báo nhầm của từng tập chọn ngưỡng/fold ngoài, kết quả từng fold, dự đoán ngoài mẫu gộp và số TP/FN/FP/TN. Precision luôn đi kèm tỷ lệ phishing trong tập đánh giá.

**Độ bất định:** bootstrap ghép cặp theo nhóm tên miền/nhóm gộp để ước lượng khoảng tin cậy 95% của chênh lệch M3–M2 và các tỷ lệ. Khoảng tin cậy từ dự đoán ngoài mẫu phản ánh bất định mẫu với các mô hình đã fit; báo cáo biến động giữa fold để bổ sung. Phân nhóm gồm URL có/không có token tổ chức, từng tổ chức đủ mẫu, nhóm khác và trang hợp lệ khó; kèm số trang và số miền độc lập.

Nếu có đủ dữ liệu và dấu thời gian đáng tin cậy, bổ sung tập tương lai độc lập với huấn luyện để đánh giá thay đổi theo thời gian. Phân tách theo miền được kiểm tra riêng; kết quả k-fold theo miền được diễn giải là khái quát sang miền chưa gặp.

#### f. Triển khai tiện ích và đo hệ thống

Tiện ích Chrome Manifest V3 kiểm tra URL khi điều hướng, phân tích DOM khi có đầu vào và cập nhật khi nội dung thay đổi đáng kể, có giới hạn tần suất. Demo ưu tiên mô hình nhẹ; phương án máy chủ cục bộ được dùng nếu chưa chuyển mô hình sang trình duyệt. Kiến trúc thực tế và dữ liệu gửi ra ngoài được mô tả trong báo cáo.

Cảnh báo hiển thị tín hiệu quan sát như tên tổ chức và miền không tương ứng, biểu mẫu yêu cầu thông tin nhạy cảm; trạng thái thông thường dùng diễn đạt “chưa phát hiện dấu hiệu phishing”. Công tắc ad block là tính năng demo tùy chọn, sau khi phần phát hiện chạy ổn định. Bộ phát hiện đọc trạng thái DOM thực tế; ad block được kiểm tra chức năng cơ bản, không tạo nhánh thí nghiệm so sánh hiệu quả phát hiện.

Đo p50/p95 từ điều hướng đến cảnh báo, từ lúc có DOM đầu vào đến kết quả, thời gian trích đặc trưng/suy luận và tỷ lệ lỗi. Ghi cấu hình máy, kết nối, số trang/lượt đo và cách xử lý timeout. Kiểm thử trang dựng phía khách, SPA, chuyển hướng, biểu mẫu xuất hiện trễ và thay đổi DOM; báo cáo thời điểm phát hiện thực tế.

#### g. Giới hạn, đạo đức và khả năng tái lập

Tổng quan hiện tại có chọn lọc; tính mới cần tiếp tục đối chiếu. Nhóm Việt Nam phụ thuộc số trang còn sống và chất lượng nhãn. Grouped k-fold tận dụng mẫu nhưng không tăng số quan sát độc lập; nhóm nhỏ và FPR thấp có thể có khoảng tin cậy rộng. Quy tắc có thể bỏ sót tên lạ hoặc chữ trong ảnh; danh mục miền cần cập nhật. Trang chết, nội dung cloaking, quan hệ ủy quyền thiếu dữ liệu và thời điểm cảnh báo tạo giới hạn triển khai. Các giới hạn này được phân tích cùng kết quả, kể cả khi giả thuyết không được xác nhận.

Dữ liệu thu thập được quản lý theo điều kiện nguồn và thỏa thuận sử dụng. Che thông tin cá nhân, token và tham số nhạy cảm trước khi công bố. Chỉ chia sẻ phần được phép; tệp HTML nguy hiểm được lưu tách biệt. Công bố codebook, cấu hình, danh sách nhóm, seed, phiên bản dữ liệu/mã/mô hình và quy trình kiểm tra rò rỉ. Nhóm chịu trách nhiệm xác minh nội dung, nguồn và kết quả, lưu vết việc sử dụng công cụ AI hỗ trợ và các quyết định nghiên cứu do nhóm thực hiện.

## 6. Năng lực nhóm thực hiện và Giảng viên hướng dẫn

### 6.1. Nhóm sinh viên

Nhóm có nền tảng Python/học máy và web/JavaScript, dự kiến phát triển thêm kỹ năng NLP. Phân công theo bốn vai trò: dữ liệu–gán nhãn, mô hình–thống kê, tiện ích–đo hệ thống và tổng hợp–báo cáo; một người có thể đảm nhiệm nhiều vai trò.

[Bổ sung số thành viên thực tế, người phụ trách từng vai trò, kinh nghiệm và thời lượng làm việc mỗi tuần]. Bố trí người gán nhãn thứ hai cho khoảng 200 mẫu, ước lượng thời gian sau thử nghiệm 20 mẫu. GPU không bắt buộc cho phương án lõi; cần máy chạy sandbox thu thập và trình duyệt demo.

### 6.2. Giảng viên hướng dẫn

[Bổ sung chuyên môn, công trình/kinh nghiệm liên quan và hình thức hỗ trợ]. Dự kiến rà soát giao thức, codebook, mốc khả thi dữ liệu và cách diễn giải kết quả trước các mốc chính.

## 7. Sản phẩm dự kiến và cam kết

### 7.1. Báo cáo tổng kết

Một báo cáo theo mẫu trường, trình bày tổng quan, dữ liệu, phương pháp, giao thức, kết quả M0–M3, loại bỏ thành phần, triển khai và giới hạn. Báo cáo có phụ lục giúp tái lập thực nghiệm.

### 7.2. Sản phẩm khác

- Dữ liệu đã xử lý và tài liệu mô tả; công bố phần được phép theo giấy phép/thỏa thuận.
- Mã thu thập, xử lý, huấn luyện, đánh giá; cấu hình và mô hình thực nghiệm.
- Tiện ích demo phát hiện/cảnh báo và hướng dẫn cài đặt cục bộ.
- Kịch bản demo cùng bảng đo độ trễ p50/p95 và kiểm tra nội dung động.

Các sản phẩm tùy chọn gồm công tắc ad block và thử nghiệm encoder, triển khai sau phần lõi. Mức recall, cỡ mẫu cuối cùng và thời gian cảnh báo được đo, báo cáo theo kết quả thực nghiệm.

## 8. Kế hoạch và tiến độ thực hiện

T1–T7 là tháng kể từ ngày bắt đầu. Bảng phân công theo vai trò sẽ thay bằng tên thành viên trước khi nộp.

| STT | Nội dung công việc | Người thực hiện | Sản phẩm | Thời gian |
| --- | --- | --- | --- | --- |
| 1 | Đối chiếu kiểm kê PhishVN, xin nội dung, bắt đầu thu thập sandbox; đọc 50 mẫu | Dữ liệu + chủ nhiệm | Bảng kiểm kê, nhật ký thu thập, khảo sát mốc phishing 150 mẫu/50 miền, kế hoạch 1.500 mẫu hợp lệ | Tuần 1–2 T1 |
| 2 | Chốt tổng quan, giao thức và codebook; lập danh mục chính thức | Chủ nhiệm + dữ liệu + GVHD | Giao thức, codebook, danh mục có nguồn | T1 |
| 3 | Tiếp tục thu thập; gán nhãn, đồng thuận, xử lý trùng | Dữ liệu + người gán nhãn thứ hai | Dữ liệu phiên bản 1, báo cáo chất lượng và nhóm | T1–T2 |
| 4 | Xây dựng M0–M2, chia nhóm nội bộ và đánh giá ngoài mẫu | Mô hình | Đối chứng chạy được, bảng kết quả sơ bộ | T2–T3 |
| 5 | Hoàn thiện M3, so sánh tại FPR 1%/5%, loại bỏ thành phần | Mô hình + dữ liệu | Kết quả chính, khoảng tin cậy, phân tích lỗi | T3–T4 |
| 6 | Thử encoder nếu phần lõi đã hoàn tất | Mô hình | Kết quả bổ sung nếu thực hiện | T4 |
| 7 | Tích hợp tiện ích, kiểm tra nội dung động, đo p50/p95 | Tiện ích + mô hình | Extension và báo cáo đo hệ thống | T4–T5 |
| 8 | Hoàn thiện dữ liệu mới/thí nghiệm đã định trước; công tắc ad block nếu đủ thời gian | Cả nhóm | Bản demo ổn định, kết quả khóa | T5–T6 |
| 9 | Viết báo cáo, rà nguồn, công bố phần được phép, chuẩn bị bảo vệ | Chủ nhiệm + cả nhóm + GVHD | Báo cáo, mã, mô hình, hướng dẫn và demo | T6–T7 |

Nếu thời hạn là 6 tháng, gộp giai đoạn hoàn thiện báo cáo vào T6 và giảm phần tùy chọn. Ngưỡng và cấu hình thích nghi với dữ liệu được chọn trong các phép chia nội bộ tương ứng với từng fold ngoài. Phân nhóm báo cáo theo nhãn và danh mục chính thức được khóa trước thực nghiệm. Mọi chỉnh sửa dựa trên kết quả kiểm thử được ghi nhận như phân tích thăm dò.

## 9. Tài liệu tham khảo

Danh mục theo APA, dùng các nguồn đã rà tới 03/10/2026. PhreshPhish được ghi rõ là preprint; tài liệu Chrome là tài liệu kỹ thuật, không phải bằng chứng về hiệu quả phát hiện. Năm 2026 của PhreshPhish tương ứng bản v2 đang sử dụng, bản đầu công bố năm 2025. Chương của Nguyen và Nguyen mang năm 2027 theo trích dẫn chính thức của Springer, nhưng đã xuất bản online ngày 15/08/2026. SSRN được ghi rõ là preprint; ký hiệu 2026a/2026b phân biệt hai công trình của Vu.

Alam, M., Rahman, M. L., Paul, S. K., Hays, A. W., Hussain, A., Huq, M. I., & Saxena, N. (2026). SoK: PHILTER: Uncovering security and functional gaps in AI-based phishing website detection literature via an LLM-based reasoning framework. In *Proceedings of the 35th USENIX Security Symposium* (pp. 4981–5000). USENIX Association. [Trang công trình](https://www.usenix.org/conference/usenixsecurity26/presentation/alam).

Dalton, T., Gowda, H., Rao, G., Pargi, S., Khodabakhshi, A. H., Rombs, J., Jou, S., & Marwah, M. (2026). *PhreshPhish: A real-world, high-quality, large-scale phishing website dataset and benchmark* (Version 2) [Preprint]. arXiv. [DOI: 10.48550/arXiv.2507.10854](https://doi.org/10.48550/arXiv.2507.10854). [Bản v2](https://arxiv.org/abs/2507.10854v2).

Google. (n.d.-a). *Content scripts*. Chrome for Developers. Retrieved October 3, 2026, from [tài liệu content scripts](https://developer.chrome.com/docs/extensions/develop/concepts/content-scripts).

Google. (n.d.-b). *DeclarativeNetRequest*. Chrome for Developers. Retrieved October 3, 2026, from [tài liệu API chặn yêu cầu](https://developer.chrome.com/docs/extensions/reference/api/declarativeNetRequest).

Google. (n.d.-c). *Hello World extension*. Chrome for Developers. Retrieved October 3, 2026, from [hướng dẫn cài extension cục bộ](https://developer.chrome.com/docs/extensions/get-started/tutorial/hello-world).

Jiang, H., Chen, Y., Zhu, Y., Xu, X., Song, Y., & Chen, Q. (2025). D-PhishNet: A dual-branch network for URL and HTML feature fusion in phishing webpage detection. *Computer Networks, 271*, Article 111648. [DOI: 10.1016/j.comnet.2025.111648](https://doi.org/10.1016/j.comnet.2025.111648).

Li, Y., Huang, C., Deng, S., Lock, M. L., Cao, T., Oo, N., Lim, H. W., & Hooi, B. (2024). KnowPhish: Large language models meet multimodal knowledge graphs for enhancing reference-based phishing detection. In *Proceedings of the 33rd USENIX Security Symposium* (pp. 793–810). USENIX Association. [Trang công trình](https://www.usenix.org/conference/usenixsecurity24/presentation/li-yuexin).

Lin, Y., Liu, R., Divakaran, D. M., Ng, J. Y., Chan, Q. Z., Lu, Y., Si, Y., Zhang, F., & Dong, J. S. (2021). Phishpedia: A hybrid deep learning based approach to visually identify phishing webpages. In *Proceedings of the 30th USENIX Security Symposium* (pp. 3793–3810). USENIX Association. [Trang công trình](https://www.usenix.org/conference/usenixsecurity21/presentation/lin).

Linh, D. M., Chau, H. M., Thua, H. T., & Hung, T. C. (2025). Real-time browser-integrated phishing uniform resource locator detection via deep learning and fuzzy matching. *Bulletin of Electrical Engineering and Informatics, 14*(6), 4876–4889. [DOI: 10.11591/eei.v14i6.10099](https://doi.org/10.11591/eei.v14i6.10099).

Liu, R., Lin, Y., Teoh, X., Liu, G., Huang, Z., & Dong, J. S. (2024). Less defined knowledge and more true alarms: Reference-based phishing detection without a pre-defined reference list. In *Proceedings of the 33rd USENIX Security Symposium* (pp. 523–540). USENIX Association. [Trang công trình PhishLLM](https://www.usenix.org/conference/usenixsecurity24/presentation/liu-ruofan).

Liu, R., Lin, Y., Yang, X., Ng, S. H., Divakaran, D. M., & Dong, J. S. (2022). Inferring phishing intention via webpage appearance and dynamics: A deep vision based approach. In *Proceedings of the 31st USENIX Security Symposium* (pp. 1633–1650). USENIX Association. [Trang công trình](https://www.usenix.org/conference/usenixsecurity22/presentation/liu-ruofan).

Nguyen, A.-B., & Nguyen, A.-N. (2027). Leveraging large language models for automated online fraud detection: A case study in Vietnam. In S. Kumar, V. Singh, & M. Prasad (Eds.), *Proceedings of International Conference on Information Technology and Artificial Intelligence* (Lecture Notes in Networks and Systems, Vol. 2127, pp. 35–45). Springer. [DOI: 10.1007/978-3-032-34772-5_4](https://doi.org/10.1007/978-3-032-34772-5_4).

Vu, T. N. (2026a). *Content and URL fusion for Vietnamese phishing pages: Five encoders under a variance-corrected protocol and a strength-controlled paraphrase attack* [Preprint]. SSRN. [DOI: 10.2139/ssrn.7454637](https://doi.org/10.2139/ssrn.7454637).

Vu, T. N. (2026b). PhishVN: A time-stamped Vietnamese URL phishing dataset with impersonation-scenario labels and confidence tiers. *Data in Brief, 68*, Article 113195. [DOI: 10.1016/j.dib.2026.113195](https://doi.org/10.1016/j.dib.2026.113195).

**Ghi chú nguồn dữ liệu:** phiên bản dữ liệu và mã cần được chốt khi bắt đầu thí nghiệm, không mặc định dùng nhánh mã mới nhất thay cho phiên bản của bài báo. [Dữ liệu PhishVN v4](https://data.mendeley.com/datasets/b97hxbxtpd/4), [mã PhishVN](https://github.com/vuthainguyen1602/phishvn), [dữ liệu PhreshPhish](https://huggingface.co/datasets/phreshphish/phreshphish).

---

**Đà Nẵng, ngày … tháng … năm 2026**

| Trưởng Khoa | Giảng viên hướng dẫn | Sinh viên chủ nhiệm |
| --- | --- | --- |
| (Ký và ghi rõ họ tên) | (Ký và ghi rõ họ tên) | (Ký và ghi rõ họ tên) |

