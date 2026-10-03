# Nhật ký tìm và xác minh tài liệu — 03/10/2026

Mục đích: mở rộng tổng quan website phishing tiếng Việt, reference-based và triển khai trình duyệt. Đây là rà soát có chọn lọc; không phải tìm kiếm hệ thống hoặc kết luận không còn công trình khác. Các truy vấn được gửi tới công cụ tìm kiếm web; tên trường/đơn vị của tác giả không được dùng thay cho bằng chứng dữ liệu nghiên cứu thuộc Việt Nam.

## Truy vấn thực tế

- `site.usenix.org Phishpedia PhishIntention phishing`
- `Vietnamese phishing website detection machine learning Vietnam research paper`
- `Vietnam phishing website detection URL Vietnamese study`
- `site.usenix.org/conference "Phishpedia"`
- `site.usenix.org/conference "PhishIntention"`
- `"Leveraging Large Language Models" "Vietnam" phishing authors`
- `"Vietnamese" "phishing" detection machine learning paper -site:reddit.com -site:researchgate.net`
- `site.usenix.org/conference/usenixsecurity24/presentation "KnowPhish"`
- `"Content and URL Fusion for Vietnamese Phishing Pages" "10.2139"`
- `"Content and URL Fusion for Vietnamese Phishing Pages" "domain"`
- `"phát hiện" "phishing" "tiếng Việt" nghiên cứu website`
- `"Real-time browser-integrated phishing" fuzzy matching`
- `"Real-time browser-integrated" "2025" DOI`
- `"PhishVN" "868" "659" "209"`

## Nguồn bổ sung và mức xác minh

| Công trình | Nguồn sơ cấp và phần đã đọc | Điều được đưa vào đề cương |
| --- | --- | --- |
| Phishpedia | [USENIX 2021](https://www.usenix.org/conference/usenixsecurity21/presentation/lin), tóm tắt và BibTeX; phần mô tả phương pháp PDF được lập chỉ mục | Logo, đối sánh thương hiệu tham chiếu và miền; tên tác giả, năm, trang. Không trích mức hiệu năng. |
| PhishIntention | [USENIX 2022](https://www.usenix.org/conference/usenixsecurity22/presentation/liu-ruofan), tóm tắt và BibTeX | Ý định thương hiệu/thu thập thông tin và tương tác xác nhận; tên tác giả, năm, trang. Không coi nghiên cứu này là đánh giá tiếng Việt. |
| KnowPhish | [USENIX 2024](https://www.usenix.org/conference/usenixsecurity24/presentation/li-yuexin), tóm tắt và BibTeX | Tri thức thương hiệu đa phương thức, khai thác thông tin HTML; giới hạn bao phủ danh mục. Không tự thêm baseline chạy KnowPhish vào phạm vi 6–7 tháng. |
| Nguyen & Nguyen | [Springer](https://link.springer.com/chapter/10.1007/978-3-032-34772-5_4), tóm tắt, metadata và mục Cite this paper | Website tiếng Việt và pipeline URL–HTML với LLM. Chưa đọc toàn văn có trả phí; không suy đoán giao thức chia nhóm/FPR. Nhà xuất bản ghi trích dẫn năm 2027, published 15/08/2026, pp. 35–45. |
| Vu: Content and URL Fusion | [SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7454637), metadata/tóm tắt tác giả qua kết quả tìm kiếm được lập chỉ mục | URL + văn bản tiếng Việt, TF-IDF/encoder. Posted 13/09/2026, DOI 10.2139/ssrn.7454637. Mở trực tiếp trang gặp lỗi; chưa kiểm tra toàn văn/giao thức chi tiết. Ghi rõ preprint, không tuyên bố phản biện. |
| Linh et al. | [Trang tạp chí](https://beei.org/index.php/EEI/article/view/10099), tóm tắt; [PDF nhà xuất bản](https://beei.org/index.php/EEI/article/download/10099/4503) được lập chỉ mục | Extension Chrome, mô hình URL và fuzzy matching. Metadata 14(6), 4876–4889, 2025. PhiUSIIL không phải mặc định tập tiếng Việt dù tác giả làm việc tại Việt Nam. |

Nguồn về email tiếng Việt, spam hoặc lừa đảo nói chung được thấy trong tìm kiếm nhưng không đưa vào làm tiền lệ trực tiếp cho website phishing. Các bản sao Scribd/Studocu không được dùng làm nguồn xác minh.

## Cập nhật khoảng trống

Đã có công trình URL–text tiếng Việt và các phương pháp nhận diện thương hiệu–miền–ý định. Khoảng trống đề xuất được thu hẹp thành kiểm chứng giá trị tăng thêm của bộ tín hiệu mạo danh có cấu trúc, so với M2, trên nhóm mạo danh tổ chức Việt Nam ở miền chưa gặp, với ngưỡng FPR chọn nội bộ và khoảng tin cậy. Đây là câu hỏi thực nghiệm còn cần đối chiếu sâu, không phải tuyên bố phương pháp đầu tiên.

## PhishVN: tách hai loại bằng chứng

- CSV công khai: đã đếm lại trong phiên sửa này bằng `data/source_audit/kiem_ke_phishvn.py`; hash và kết quả ở `data/source_audit/PhishVN_kiem_ke.json`.
- HTML–ảnh: [mục 3.6 bài báo](https://doi.org/10.1016/j.dib.2026.113195) và [bản PMC được lập chỉ mục](https://pmc.ncbi.nlm.nih.gov/articles/PMC13572074/) xác nhận **tác giả báo cáo** 868 cặp, 209 phishing, 659 hợp lệ. Archive công khai đã tải không chứa HTML; chưa nhận archive gated để đếm độc lập.

## Đối chiếu trực tiếp bổ sung trước khi nộp

### PhishVN

Trang PMC HTML gặp reCAPTCHA; đã đọc được toàn văn JATS/XML do **Europe PMC** phục vụ qua [API toàn văn công khai](https://www.ebi.ac.uk/europepmc/webservices/rest/PMC13572074/fullTextXML). Đã lưu tại `data/source_audit/PhishVN_EuropePMC_fulltext.xml`.

- Nhan đề và DOI trong bài trùng PhishVN đang trích.
- Section id `sec0008`, label **3.6**, title **Gated tier: captured pages**. Đoạn đầu nêu 868 records, 209 phishing và 659 benign, lưu DOM và ảnh theo mã bản ghi. Đã đối chiếu cả label XML và văn bản mục này; không chỉ dựa vào snippet tìm kiếm.
- Điều kiện: chỉ dùng nghiên cứu, mở HTML trong máy ảo cách ly, không phân phối lại. Chưa nhận archive gated nên đây vẫn là xác minh **số tác giả báo cáo**, không phải đếm tệp nội dung độc lập.
- Background nói nghiên cứu tiếng Việt trước chưa công bố dữ liệu. Kiểm tra tài liệu [18] cho thấy nhan đề **A framework for vietnamese email phishing detection** (Cho, Nguyen và Tisenko, 2019). Không diễn đạt thành một nghiên cứu website trước đó chưa công bố dữ liệu.
- Mô tả Mendeley v4 xác nhận kappa bốn lớp 0,609; nhiễu nhãn nhóm dương 12,1%, tập trung bronze. Các chỉ số thuộc audit mẫu của tác giả. Quy tắc đề cương: ưu tiên gold/silver có kiểm chứng; bronze chỉ vào thực nghiệm chính sau kiểm tra độc lập và phân xử.

### SSRN

Đã mở DOI `10.2139/ssrn.7454637`; DOI chuyển đến SSRN nhưng trang đích hiện màn kiểm tra Cloudflare. Không vượt màn kiểm tra. **Crossref trả metadata/tóm tắt tác giả thành công** tại [API DOI](https://api.crossref.org/works/10.2139/ssrn.7454637), lưu `data/source_audit/SSRN_7454637_Crossref.json`.

Crossref xác nhận nhan đề Content and URL Fusion for Vietnamese Phishing Pages: Five Encoders under a Variance-Corrected Protocol and a Strength-Controlled Paraphrase Attack; tác giả metadata given Thai, family Nguyen Vu; năm 2026; loại bản thảo đăng tải. Tóm tắt xác nhận TF-IDF/encoder văn bản tiếng Việt kết hợp URL. Metadata không cung cấp page range; 23 trang là thông tin trang SSRN được lập chỉ mục, chưa kiểm tra PDF. Tài liệu tham khảo của đề cương không ghi số trang preprint. Không coi toàn văn hoặc đánh giá riêng mạo danh tổ chức Việt Nam là đã được kiểm tra.

### Springer

DOI `10.1007/978-3-032-34772-5_4` mở được [trang nhà xuất bản](https://link.springer.com/chapter/10.1007/978-3-032-34772-5_4). Xác nhận Anh-Binh Nguyen và Anh-Nhat Nguyen, nhan đề Leveraging Large Language Models for Automated Online Fraud Detection: A Case Study in Vietnam, pp. 35–45, LNNS 2127. Mục Cite this paper ghi **2027**, mục Published ghi **15/08/2026**. Tóm tắt mô tả URL và 500 ký tự HTML đầu, kết quả giới hạn website tiếng Việt. Chưa đọc toàn văn trả phí; không suy từ tóm tắt rằng nhóm nghiên cứu là các tổ chức Việt Nam.

### BEEI

Đã thử mở DOI `10.11591/eei.v14i6.10099` (web báo lỗi, curl hết thời gian chờ); nội dung được xác minh bằng cách đối chiếu trực tiếp [trang công trình](https://beei.org/index.php/EEI/article/view/10099) cùng [PDF nhà xuất bản](https://beei.org/index.php/EEI/article/download/10099/4503). PDF trang đầu xác nhận nhan đề, bốn tác giả, **14(6), tháng 12/2025, 4876–4889** và DOI. Tóm tắt và thuật toán nêu Chrome extension, exact/fuzzy matching, mô hình URL và danh sách trắng/đen. PhiUSIIL là dữ liệu dùng trong bài; không trình bày bài này như thực nghiệm nội dung website tiếng Việt.

### Điều chỉnh tuyên bố tổng quan

Bỏ cụm “tiền lệ trực tiếp” cho hai nguồn tiếng Việt, thay bằng công trình liên quan gần về đầu vào. Phạm vi nhóm tổ chức và giao thức chi tiết không được suy từ tóm tắt. Khoảng trống về dữ liệu có kiểm chứng được nêu có nguồn và phân biệt email với website.
