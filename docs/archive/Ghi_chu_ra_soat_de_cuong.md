# Ghi chú rà soát và chuẩn bị nghiên cứu

Ngày rà soát: 03/10/2026. Tệp này phục vụ làm việc, tách khỏi đề cương nộp.

## 1. Kiểm kê PhishVN thực tế

Đã tải [PhishVN v4](https://data.mendeley.com/datasets/b97hxbxtpd/4), tệp `PhishVN_v3.1.0_open.zip`, và đếm `data/dataset_url.csv` bằng script `data/source_audit/kiem_ke_phishvn.py`. Chỉ đọc dữ liệu trong ZIP; không thực thi mã trong nguồn hay truy cập URL phishing. Kết quả đầy đủ tại `data/source_audit/PhishVN_kiem_ke.json`.

| Hạng mục | Bản ghi đếm được |
| --- | ---: |
| Tổng | 53.116 |
| Phishing | 36.706 |
| Hợp lệ | 16.410 |
| Phishing NCSC/Tín nhiệm mạng | 2.587 |
| Phishing ChongLuaDao | 33.823 |
| Phishing OpenPhish | 296 |
| Lõi gold/silver | 18.997 |
| Mở rộng bronze | 34.119 |

SHA-256 CSV: `8e1c6325a82177014ac892a9aaf8c4d3cbbc986b47fd1ecac8899c865fb6eade`, khớp dòng trong MANIFEST.txt. Archive công khai có **0 tệp HTML**; bảng CSV này không phải bộ URL–nội dung để chạy M0–M3 ngay.

Trong **riêng lớp phishing**, nhãn scenario suy từ URL gồm bank 1.402, gov 38, tax 9, other 33.342 và các nhóm còn lại. Đây là bản ghi theo quy tắc nguồn, không phải số trang sống, số miền độc lập hay nhãn mạo danh đã kiểm chứng. Đặc biệt, cộng nhãn gov trên cả hai lớp sẽ có 7.146 và dễ dẫn tới hiểu sai số phishing cơ quan nhà nước. Phát hiện này ủng hộ tên đề tài dùng “tổ chức Việt Nam” và quyết định nhóm báo cáo sau khảo sát nội dung.

Trường domain có 53.042 giá trị phân biệt theo đúng dữ liệu nguồn; chưa dùng con số đó thay cho số miền đăng ký độc lập trong thiết kế nghiên cứu. Lang cũng là metadata nguồn, cần đọc nội dung để xác nhận tiếng Việt. Các giá trị text trong bảng chưa được coi là DOM/văn bản hiển thị đã chụp.

Bài báo [PhishVN, mục bộ dữ liệu đồng hành](https://doi.org/10.1016/j.dib.2026.113195) nêu **868 bản ghi có HTML–ảnh, gồm 209 phishing và 659 hợp lệ**. Có xác nhận trong nội dung bài báo được lập chỉ mục công khai; chưa có quyền truy cập archive này để kiểm kê độc lập. Vì vậy đề cương dùng “bài báo báo cáo”, không dùng “nhóm đã thu thập”.

## 2. Xác minh các tài liệu được trích

| Nguồn sơ cấp | Nội dung đã kiểm tra và cách sử dụng |
| --- | --- |
| [PHILTER, USENIX Security 2026](https://www.usenix.org/conference/usenixsecurity26/presentation/alam) | Trang công trình và BibTeX xác nhận 55 phương pháp; 4 tiêu chí chức năng và 3 tiêu chí an toàn. Đề cương chỉ dùng kết luận định hướng đánh giá. |
| [PhreshPhish v2](https://arxiv.org/abs/2507.10854v2), [toàn văn HTML](https://arxiv.org/html/2507.10854v2) | Bản đầu 14/07/2025, v2 ngày 11/02/2026. Xác nhận vấn đề leakage, tỷ lệ lớp và thiết kế benchmark. Ghi là preprint v2; không gán trạng thái xuất bản tạp chí/hội nghị. |
| [D-PhishNet, nhà xuất bản](https://www.sciencedirect.com/science/article/pii/S1389128625006152) | Metadata/tóm tắt sơ cấp xác nhận mô hình hai nhánh GNN–BERT, Computer Networks 271, 111648, 2025. Đề cương không dẫn số hiệu năng; chưa coi phần trả phí là đã đọc toàn văn. |
| [PhishLLM, USENIX Security 2024](https://www.usenix.org/conference/usenixsecurity24/presentation/liu-ruofan) | Xác nhận quan hệ thương hiệu–miền, ý định thu thập thông tin và xác minh qua tìm kiếm; tác giả và trang 523–540. Đề cương không vay mượn mức cải thiện của mô hình này làm kỳ vọng hiệu năng. |
| [PhishVN v4](https://data.mendeley.com/datasets/b97hxbxtpd/4), [bài báo](https://doi.org/10.1016/j.dib.2026.113195) | Kiểm kê CSV trực tiếp; bộ HTML–ảnh mới xác minh ở mức báo cáo tác giả. Metadata nguồn còn câu “under revision”, trong khi bài báo đã có DOI/ấn phẩm: trích thông tin xuất bản từ bài báo. |
| [Kho mã PhishVN](https://github.com/vuthainguyen1602/phishvn) | README yêu cầu dùng release `dib-113195` để tái lập bài báo; nhánh hiện tại có thay đổi về sau. Lưu ý kiểm chứng nhãn feed, nhất là bronze. |

Tài liệu Chrome đã mở lại trên trang chính thức để kiểm tra DOM/content script, declarativeNetRequest và cách cài demo cục bộ. Đây là nguồn kỹ thuật, không chứng minh khả năng phát hiện của mô hình.

## 3. Những điều chỉnh trong đề cương

- Đổi tên sang mạo danh tổ chức Việt Nam; extension chuyển về sản phẩm.
- Giữ RQ1–RQ3, bỏ RQ4; ad block chỉ là công tắc demo tùy chọn.
- Dùng grouped k-fold theo miền, kiểm soát template gần trùng và trùng liên nguồn; chọn ngưỡng trong phần nội bộ, báo cáo FPR thực đo tại mục tiêu 1%/5%.
- Ngưỡng 150 mẫu/50 miền là mốc khả thi, không thay cho phân tích khoảng tin cậy. Các ngưỡng 5 miền/tổ chức dùng để chọn phân nhóm báo cáo từ toàn bộ nhãn tham chiếu trước khi xem kết quả mô hình; không xóa tổ chức ít mẫu khỏi danh mục.
- Cụ thể hóa từ điển, biến thể, chuẩn hóa không dấu, so khớp mờ, ngữ cảnh tuyên bố danh tính và quan hệ miền chính thức/ủy quyền.
- TF-IDF + char n-gram trước; LightGBM bổ sung cho M2/M3, encoder tùy chọn sau phần lõi.
- Cam kết báo cáo, dữ liệu được phép công bố, mã/mô hình, extension; đo p50/p95 thực tế.

## 4. Việc cần thực hiện trong hai tuần đầu

Đã hoàn tất: kiểm kê tệp URL công khai và checksum.

Còn cần thực hiện khi bắt đầu nghiên cứu: gửi yêu cầu HTML với thông tin nhóm/giảng viên; dựng môi trường sandbox và bộ thu thập; chụp trang sống từ nguồn truy cập được; đọc khoảng 50 mẫu; tổng hợp số mẫu/miền đủ bằng chứng. Chưa gửi thư, chưa chạy crawler trang phishing, chưa có dữ liệu HTML mới. Hai việc xin archive và thu thập mới được thực hiện song song.

Phương án thu thập tối thiểu: đọc feed hợp lệ → chuẩn hóa và loại URL đã chụp → đưa vào hàng đợi → mở trong trình duyệt sandbox → lưu rendered DOM, ảnh, chuyển hướng, thời điểm và trạng thái → kiểm tra nhãn. Không đưa biểu mẫu, cookies hay thông tin cá nhân thật vào môi trường thu thập. Chốt nguồn, nhịp cập nhật và giới hạn tài nguyên sau khảo sát quyền truy cập.

## 5. Thông tin cần bổ sung trước khi nộp

Tên trường/khoa, thông tin giảng viên và thành viên; lịch chính thức; người gán nhãn thứ hai; khả năng máy ảo/sandbox. Người dùng đã xác nhận trường thúc đẩy ứng dụng AI và việc hỗ trợ AI không vướng yêu cầu của trường. Ghi nhận thông tin này theo xác nhận của người dùng; tiếp tục lưu vết hỗ trợ, nguồn đã kiểm chứng và quyết định của nhóm.


## 6. Rà soát bổ sung sáu điểm

1. Đã chạy lại script kiểm kê CSV: 53.116 dòng dữ liệu (không tính header), lõi gold/silver 18.997; SHA-256 trùng MANIFEST. Tổng quan giữ cách dẫn số liệu theo tác giả để phân biệt văn liệu và thao tác kiểm kê. Số 868/209/659 có ở mục 3.6 bài báo và bản PMC lập chỉ mục; chưa đếm archive nội dung độc lập.
2. Danh mục cơ sở chỉ lấy từ nguồn chính thức, khóa trước thực nghiệm và dùng chung mọi fold. Nhánh bổ sung từ dữ liệu nếu làm phải dựng riêng cả fold ngoài và phép chia nội bộ tương ứng.
3. Quy tắc 5 miền đếm theo nhãn trên toàn tập trước khi xem kết quả; chỉ quyết định báo cáo nhóm, không điều chỉnh mô hình.
4. Thêm mốc tham chiếu 1.500 trang hợp lệ/500 miền, gồm 300 trang khó/100 miền. Điểm 1% có giới hạn do số FP ít và tập chọn ngưỡng nội bộ nhỏ; báo cáo FPR của tập hợp lệ gắn bối cảnh Việt Nam riêng. Các mục tiêu mẫu chưa phải dữ liệu thu được.
5. Bổ sung sáu nghiên cứu: Phishpedia (2021), PhishIntention (2022), KnowPhish (2024), Linh et al. về extension URL + fuzzy matching (2025), Nguyen và Nguyen về phishing website tiếng Việt (online 2026, năm trích dẫn Springer 2027), và preprint URL–text tiếng Việt của Vu (2026). Có tổng cộng 11 công trình nghiên cứu và 3 tài liệu Chrome. Khoảng trống đã thu hẹp theo tiền lệ mới tìm được.
6. Nhóm chính xác định theo tổ chức Việt Nam bị mạo danh, không theo ngôn ngữ. Trang tiếng Anh mạo danh ngân hàng Việt Nam được giữ; ngôn ngữ chỉ là thuộc tính phân nhóm. Nhãn tham chiếu độc lập với danh mục/đầu ra mô hình.

Bản trước sửa được lưu trong `De_cuong_NCKH_Phishing_Mau_2_Truoc_ra_soat_6_diem.md`. Bản dùng tiếp là `De_cuong_NCKH_Phishing_Mau_2.md`.

## 7. Đợt rà soát nguồn và rủi ro bổ sung

Đã đối chiếu mục 3.6/868/209/659 từ toàn văn Europe PMC XML, DOI SSRN bằng Crossref, chương Springer và PDF BEEI. Chi tiết truy cập thành công/bị chặn, metadata và phạm vi nội dung đã đọc được cập nhật trong nhật ký tài liệu. Số nội dung PhishVN là tác giả báo cáo; chưa kiểm kê bộ gated.

Đề cương thêm quy tắc nhãn trước thực nghiệm: gold/silver ưu tiên làm nguồn khởi đầu, vẫn xác minh nội dung; bronze chưa kiểm chứng bị loại khỏi huấn luyện/đánh giá chính. Bronze được tiếp nhận sau hai người kiểm tra độc lập và phân xử có ghi nhận. Thêm rủi ro tập trung nguồn ở tác giả PhishVN/preprint và đường thu thập riêng khi chưa có quyền truy cập.

Grouped 5-fold lặp 3 seed định trước; kết quả lặp không được đếm như thêm mẫu độc lập. Mục 8 được rút gọn. Abstract bản hiện tại có 292 từ theo khoảng trắng; toàn bản khoảng 6.698 từ theo cách đếm đó, 42.437 byte. Số byte không quy đổi trực tiếp thành số trang. Chưa có tên trường/khoa hoặc quy định giới hạn trang để đối chiếu; đã hỏi người dùng. Thông tin giảng viên, thành viên, lịch và phân loại khoa còn cần người dùng điền, không tự tạo.


## 8. Đối chiếu lại hai câu và giảm tải kiểm chứng bronze

Đã kiểm tra lại bản XML toàn văn Europe PMC lưu tại `data/source_audit/PhishVN_EuropePMC_fulltext.xml`: article-id DOI khớp 10.1016/j.dib.2026.113195. Section `sec0008` có label **3.6**, title **Gated tier: captured pages**; đoạn đầu xác nhận 868 cặp gồm 209 phishing/659 hợp lệ. Tài liệu tham khảo có label **18**, nhan đề **A framework for vietnamese email phishing detection**, DOI **10.35940/ijitee.A4843.119119**, năm 2019. Do đó cả hai câu trong tổng quan có căn cứ từ toàn văn bài PhishVN; câu chưa công bố dữ liệu vẫn được dẫn là nhận định của tác giả PhishVN.

Quy tắc bronze hiện hành thay yêu cầu hai người kiểm từng mẫu: chỉ tập trung ứng viên mạo danh tổ chức Việt Nam, một người kiểm toàn bộ phần được sử dụng, người thứ hai kiểm độc lập mẫu con ngẫu nhiên phân tầng 30% và các trường hợp khó. Độ đồng thuận/kappa tính trên mẫu con ngẫu nhiên, báo cáo riêng trường hợp khó. Các bản ghi ứng viên không chỉ được chọn theo token URL; ghi lại nguồn/cách sàng lọc để nhận diện thiên lệch tuyển mẫu. Các quy tắc ở mục 7 và ghi chú cũ về hai người kiểm toàn bộ bronze được thay bằng mục 8 này.
