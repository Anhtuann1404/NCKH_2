# Ghi chú nghiên cứu

Tài liệu làm việc đi kèm [đề cương hiện hành](/Users/yingjunn_/Study_/NCKH_2/docs/De_cuong_NCKH_Phishing_Mau_2.md). Cập nhật ngày 03/10/2026.

## Phân công được đưa vào đề cương — 04/10/2026

Theo yêu cầu người dùng, đã cụ thể hóa bốn thành viên ở phần thông tin nhóm, mục 6.1 và bảng tiến độ mục 8: D là chủ nhiệm/owner mô hình, trực tiếp xây dựng–huấn luyện–đánh giá và API–extension; A nhãn/evidence; B kiểm độc lập và QA/tái lập sau khóa nhãn; C nguồn/pipeline/view mù/dictionary/groups/splits. Mỗi vai trò có output bàn giao và người phối hợp/kiểm tra. Cập nhật tương ứng một câu phân công trong 5.2b. Họ tên và ngân sách giờ chưa có, giữ placeholder. Không đổi RQ, phương pháp, nguồn, giao thức đánh giá hay sản phẩm đã duyệt; chia tách các dòng dữ liệu/nhãn/kiểm chứng trong tiến độ để rõ chủ trì, không thêm hạng mục nghiên cứu bắt buộc.

## Chốt tên và trọng tâm trình bày — 03/10/2026

Theo yêu cầu mới nhất của người dùng, tên hiện hành là **Phát hiện website phishing mạo danh tổ chức bằng học máy kết hợp URL và nội dung trang**. Trọng tâm trình bày là xây dựng và đánh giá phương pháp phát hiện, triển khai extension cảnh báo; phép so sánh M2–M3 và ablation là bằng chứng kiểm chứng đóng góp. Không dùng “đánh giá giá trị tăng thêm” làm tên chính và không khẳng định có thuật toán mới trước khi đối chiếu/thực nghiệm. Tên cũ trong các ghi chú rà soát bên dưới là lịch sử.

Đã chỉnh tên, mở đầu tóm tắt, mục tiêu tổng quát/cụ thể và cách dẫn mục 3.2. Giữ các câu hỏi nghiên cứu, M0–M3/B-rule, dữ liệu quốc tế, nhánh Việt Nam, danh mục, giao thức, quy tắc nhãn, tiến độ và sản phẩm đã thống nhất. Việc đổi trọng tâm trình bày không thay phép kiểm chứng hoặc nâng đóng góp dự kiến thành kết quả đã chứng minh.

## Cập nhật hạ tầng dùng chung, thời gian và nhân lực — 03/10/2026

Phần này là quyết định hiện hành, thay các mốc/danh mục cũ trong lịch sử phía dưới khi có khác biệt. Người dùng xác nhận nhóm **4 người trở lên**; chưa cung cấp họ tên và ngân sách giờ.

- **Vai trò độc lập:** A gán nhãn; B kiểm nhãn; C chuẩn bị dữ liệu/giao diện mù, khác A/B; D phụ trách extension/hệ thống. Mục tiêu 2.000 vẫn là tham chiếu. 3–5 phút/trang cho A tương ứng 100–167 giờ, khoảng 14–24 giờ/tuần trong 7 tuần. Pilot trung bình >5 phút hoặc ngân sách A/B không đủ → giảm mục tiêu xuống 1.200/300 miền, A 60–100 giờ, B kiểm 360 mẫu 18–30 giờ, chưa gồm benign/phân xử. Nếu còn quá tải thì giảm theo giờ thực có trước xem kết quả. Không suy đủ nhân lực chỉ từ số thành viên.
- **Quan hệ miền:** phân loại endpoint first-party, nội dung người dùng/tenant, dịch vụ ủy quyền có bằng chứng và chưa xác minh. Sites/Docs/Forms/SharePoint/Blob và hồ sơ xã hội không được tự gắn là nhất quán/allowlist vì chủ hạ tầng. Unknown không đồng nghĩa phishing. Cả M3 và B-rule tuân thủ; báo cáo nhóm shared hosting. [Google Sites](https://support.google.com/sites/answer/6372880?hl=en) xác nhận người dùng xuất bản site; [Azure Storage](https://learn.microsoft.com/en-us/azure/storage/blobs/storage-blob-static-website) mô tả nội dung HTML tĩnh của storage account, endpoint web và blob.
- **Danh mục theo thời gian:** thay 10 mã Q4/2025 bằng hợp top 10 Q4/2024, Q1–Q4/2025 cho cửa sổ dự kiến 01/10/2024–31/12/2025. Sau chuẩn hóa có 14 mã: Microsoft, Google, Apple, Amazon, Meta, LinkedIn, Adobe, Booking, PayPal, DHL, Spotify, Alibaba, Mastercard, X/Twitter. Trước mở tập chính C kiểm riêng date toàn revision; nếu không phủ cửa sổ dự kiến thì điều chỉnh một lần theo quý thực có, hợp tất cả báo cáo quý đó rồi khóa, không dùng nhãn/target/hiệu năng chọn quý. Tỷ lệ phủ vẫn có thể thấp.
- **Bằng chứng date có giới hạn:** chỉ đọc date của 20 mẫu kỹ thuật thấy 2024-07-10–2025-09-02. API statistics không trả thống kê cột date, nên chưa xác nhận min/max toàn corpus. Không dùng thống kê label/target của endpoint này để chọn thương hiệu hay quý. Hai mốc cửa sổ trên là kế hoạch được khóa sau date audit, không mô tả dữ liệu đã kiểm kê xong.
- **Codebook:** Outlook/Office365/Microsoft365/OneDrive→Microsoft; Gmail/Drive→Google; Facebook/Instagram/WhatsApp→Meta; AWS→Amazon; iCloud→Apple; LinkedIn mã riêng; X/Twitter một mã. Giữ dịch vụ quan sát ở cột riêng; không suy tổ chức bị mạo danh từ chủ cloud. Ánh xạ/ngoại lệ khóa trước gán nhãn; ca đa mục tiêu theo codebook thống nhất.
- **Thời gian là phân tích phụ định trước:** mốc 60%/80% từ date, không tách cùng ngày; trước train, giữa validation chọn ngưỡng, cuối test; bỏ bản ghi muộn trùng nhóm sớm. Không dùng CV chứa tương lai để chọn họ mô hình/siêu tham số nhánh này. Danh mục nhánh thời gian chỉ gồm báo cáo đã công bố trước mốc train và bằng chứng miền/bí danh có hiệu lực lúc đó. Không tái dựng được tri thức lịch sử thì ghi hồi cứu, không nói đã chứng minh dự báo tương lai.
- **Official test:** giữ ngoài tập chính (tập chính từ official train). Chỉ đo thêm sau khóa; loại trùng miền/nội dung với train/validation/pilot/phần phát triển. Date phải chứng minh thứ tự mới coi là tương lai. Không dùng official test cho chọn mô hình/danh mục.
- **Bối cảnh trong nước:** sửa “nhóm ứng dụng ưu tiên” thành “bổ sung”. Mở lại [bản tin Bộ ngày 23/04/2024](https://mst.gov.vn/gia-mao-website-co-quan-chuc-nang-to-chuc-tai-chinh-de-tan-cong-lua-dao-197240423101514809.htm) xác nhận 124.579 địa chỉ website giả mạo cơ quan/tổ chức; không quy thành số miền độc lập.

Báo cáo Check Point đã mở trực tiếp, chỉ dùng top 10 và ngày công bố của các báo cáo ngoài corpus:

| Quý | Ngày công bố | Nguồn |
| --- | --- | --- |
| Q4/2024 | 22/01/2025 | [Báo cáo chính thức](https://blog.checkpoint.com/research/exploring-q4-2024-brand-phishing-trends-microsoft-remains-the-top-target-as-linkedin-makes-a-comeback/) |
| Q1/2025 | 21/04/2025 | [Báo cáo chính thức](https://blog.checkpoint.com/research/microsoft-dominates-as-top-target-for-imitation-mastercard-makes-a-comeback/) |
| Q2/2025 | 22/07/2025 | [Báo cáo chính thức](https://blog.checkpoint.com/research/phishing-trends-q2-2025-microsoft-maintains-top-spot-spotify-reenters-as-a-prime-target/) |
| Q3/2025 | 16/10/2025 | [Báo cáo chính thức](https://blog.checkpoint.com/research/microsoft-dominates-phishing-impersonations-in-q3-2025/) |
| Q4/2025 | 15/01/2026 | [Báo cáo chính thức](https://blog.checkpoint.com/research/microsoft-remains-the-most-imitated-brand-in-phishing-attacks-in-q4-2025/) |

Chưa chạy gán nhãn có bấm giờ, huấn luyện, CV, chia thời gian hoặc kiểm official test. Chưa xác nhận revision đầy đủ và min/max date toàn corpus. Không nâng các quy tắc kế hoạch thành thao tác đã hoàn tất.

## Rà soát nhãn tổ chức, danh mục và nhiễu theo nguồn — 03/10/2026

Đã sửa trực tiếp bốn góp ý và câu bổ sung cho nhánh Việt Nam. Các quyết định tại đây thay mô tả lịch sử khác bên dưới khi có khác biệt.

1. **Tên và tính cấp thiết:** đổi tên sang đánh giá giá trị tăng thêm. [Bản tin chính thức ngày 23/04/2024](https://mst.gov.vn/gia-mao-website-co-quan-chuc-nang-to-chuc-tai-chinh-de-tan-cong-lua-dao-197240423101514809.htm) dẫn NCSC ghi nhận 124.579 địa chỉ website giả mạo cơ quan/tổ chức. Chỉ dùng đúng đơn vị địa chỉ, không suy số miền, nạn nhân hoặc quy mô hiện tại 2026.
2. **Schema:** [viewer hiện hành](https://huggingface.co/datasets/phreshphish/phreshphish) và JSON API đã lưu đều có target cùng url/label/html và metadata. Mẫu 20 gồm 12 target null ở benign; 8 phishing có facebook:1, meta:1, swiss post:1, other:5. Không coi target là ground truth hoặc dùng làm đặc trưng. Schema của tập chính vẫn phải xác minh lại sau khóa revision.
3. **Nhãn tổ chức:** A đọc toàn bộ phishing giữ lại (mục tiêu 2.000), ghi tên tự do và bằng chứng trước chuẩn hóa mã/tra danh mục. A/B không thấy target nguồn hoặc đầu ra quy tắc/mô hình; B kiểm 30% ngẫu nhiên và ca khó. Audit 200 mẫu lớp không thay gán nhãn tổ chức. Kappa riêng trên mẫu ngẫu nhiên trước phân xử. Khoảng 70% do một người gán có độ tin cậy giới hạn.
4. **Công sức chưa đo:** kế hoạch giả định 3–5 phút/phishing → A 100–167 giờ người, B kiểm 600 mẫu 30–50 giờ, chưa gồm benign/phân xử. Trong T1 đo 20 mẫu kỹ thuật, bổ sung 12 phishing để có pilot 20 phishing; các mẫu pilot loại khỏi đánh giá chính. Thời gian tính cả đọc/tra cứu/gán nhãn, không lấy thời gian parser. Chốt cỡ mẫu theo nhân lực trước chạy, gán nhãn toàn bộ phần giữ lại.
5. **Danh mục độc lập:** chọn 10 thương hiệu của [báo cáo Q4/2025, công bố 15/01/2026](https://blog.checkpoint.com/research/microsoft-remains-the-most-imitated-brand-in-phishing-attacks-in-q4-2025/): Microsoft, Google, Amazon, Apple, Facebook (Meta), PayPal, Adobe, Booking, DHL, LinkedIn. Quan hệ sở hữu tách khỏi đơn vị thương hiệu/dịch vụ. Không chọn theo corpus/pilot; khóa miền/bí danh từ nguồn chính thức trước mở tập chính. Thống kê hãng không đại diện mọi thương hiệu thế giới.
6. **Hai phân tích định trước:** toàn tập và phishing trong danh mục dùng cùng mô hình/ngưỡng; tập con không tối ưu ngưỡng riêng. Báo cáo coverage theo trang/miền, unknown riêng, FPR benign chung và hard benign. Tỷ lệ phủ thấp không là lý do đổi danh mục sau xem kết quả.
7. **Nhiễu nguồn:** kết quả chính PhreshPhish-only, kiểm khác biệt pipeline ngay trong corpus. Nhánh gộp phải có cả hai lớp của từng nguồn/chế độ ở mọi fold ngoài/nội bộ; luôn báo cáo PhreshPhish-only trên cùng test nền. Crawler chỉ benign là tập thử thách FPR riêng; không trộn như nguồn benign đối lập phishing corpus. Cùng parser không tự xóa artefact.
8. **Hard benign:** giảm mốc 500/200 xuống 300 trang/100 miền, ưu tiên lớp benign cùng corpus. Tin tức, đại lý và SSO cần xác minh, không quota 100 miền của 10 thương hiệu. Trang tự thu báo cáo riêng, không chọn sau xem lỗi mô hình.
9. **Nhánh Việt Nam:** danh mục mở rộng lập từ nguồn ngoài, khóa trước gán nhãn và đánh giá; kết quả riêng, không gộp vào hai phân tích chính.

Trong quá trình tìm nguồn phát hiện thêm [Mishra & Varshney (2025)](https://arxiv.org/abs/2503.06487), preprint về hiệu quả đặc trưng xác định miền thương hiệu. Đã xác minh tên/tác giả/ngày/tóm tắt trên arXiv; chưa đọc toàn văn. Bổ sung như tiền lệ gần và không dẫn số hiệu năng làm căn cứ kỳ vọng. Không khẳng định đề tài là phương pháp tín hiệu mạo danh đầu tiên.

Các truy vấn bổ sung: `site.ncsc.gov.vn 2024 2025 website giả mạo lừa đảo số lượng`; `site.khonggianmang.vn 2025 website lừa đảo giả mạo 2024`; `site.research.checkpoint.com 2025 Q4 brand phishing report Microsoft`. Kiểm trực tiếp trang Bộ, Check Point, arXiv và Hugging Face ngày 03/10/2026.

## Phạm vi hiện hành — đã chốt trước khi nộp

Người dùng đồng ý làm lại đề cương theo góp ý mở rộng của giảng viên. Tên hiện hành: **Phát hiện website phishing mạo danh tổ chức bằng học máy kết hợp URL và nội dung trang**. Dữ liệu quốc tế là tập thực nghiệm chính; Việt Nam là nhóm ứng dụng bổ sung, với danh mục mở rộng khóa trước gán nhãn/đánh giá, báo cáo riêng và không gộp kết quả chính. Các đoạn bên dưới ghi phạm vi Việt Nam hoặc đang chờ quyết định được giữ như lịch sử, không phải phương án hiện hành.

### Các quyết định sau brainstorm

- **Giữ lõi:** đo giá trị tăng thêm của tín hiệu tổ chức–miền–ý định vào mô hình URL–DOM–văn bản; triển khai tiện ích cảnh báo. Thay nguồn dữ liệu về sau vẫn phải giữ đầu vào và câu hỏi này.
- **Mở phạm vi có giới hạn:** ưu tiên tiếng Anh, danh mục hợp top 10 của Q4/2024 và Q1–Q4/2025, sau chuẩn hóa có 14 mã theo cửa sổ dự kiến; miền/bí danh và vai trò dịch vụ lấy từ nguồn chính thức, khóa sau kiểm kê date và trước mở nhãn/nội dung tập chính. Danh mục một quý và mốc 20–30 cũ đã được thay. Không nhận bao phủ mọi tổ chức/ngôn ngữ. Mẫu ngoài danh mục vẫn được đánh giá bằng bộ phát hiện chung.
- **Giảm phụ thuộc quyền truy cập:** PhreshPhish là nguồn khởi đầu có URL–HTML đã thử tải. PhishVN gated và crawler là nguồn bổ sung. 20 dòng thử chỉ chứng minh truy cập và trích nội dung, chưa chứng minh chất lượng toàn bộ dữ liệu hay hiệu năng mô hình.
- **Đặt cỡ mẫu theo tập chính mới:** hướng tới khoảng 2.000 phishing/500 miền và 10.000 hợp lệ/3.000 miền, gồm 300 trang hợp lệ khó/100 miền, ưu tiên cùng corpus; phần tự thu là tập thử thách riêng. Đây là mục tiêu tham chiếu, khóa lại quy mô sau kiểm kê hai tuần đầu. Tăng phần hợp lệ giúp có thêm bằng chứng ở FPR thấp, không tự bảo đảm khoảng tin cậy hẹp. Mốc 150 phishing/50 miền chỉ còn dùng cho nhóm Việt Nam bổ sung.
- **Đối chứng và câu hỏi:** giữ M0–M3, thêm B-rule để phân biệt lợi ích học máy với quy tắc. RQ1 về tăng recall tại FPR mục tiêu; RQ2 về từng nhóm tín hiệu; RQ3 về trong/ngoài danh mục và trang hợp lệ khó. Không có RQ ad block.
- **Kiểm nhãn vừa sức:** audit quốc tế khoảng 200 mẫu ngẫu nhiên phân tầng, hai người độc lập; kiểm toàn bộ mẫu thêm thủ công. Quy tắc bronze bên dưới áp dụng riêng nguồn PhishVN bổ sung. Kappa không gộp ca khó được chuyển thêm ngoài mẫu ngẫu nhiên.
- **Khả năng kiểm chứng:** grouped 5-fold lặp 3 seed, chọn ngưỡng nội bộ, kiểm soát miền/template gần trùng; báo cáo FPR thực đo tại mục tiêu 1%/5%, bootstrap ghép cặp theo nhóm và dao động giữa fold/seed.
- **Ưu tiên 6–7 tháng:** dữ liệu và đối chứng trước, extension/độ trễ sau; encoder, nhóm Việt Nam và ad block tùy nguồn lực. OCR và khảo sát người dùng để hướng mở rộng.

Bản phạm vi Việt Nam trước sửa đã lưu trong [archive](/Users/yingjunn_/Study_/NCKH_2/docs/archive/De_cuong_NCKH_Phishing_Mau_2_Pham_vi_Viet_Nam.md). Chưa chạy crawler, huấn luyện hoặc thực nghiệm hiệu năng; phần nội dung chính đã viết lại theo mẫu chín mục, còn thông tin hành chính do nhóm bổ sung.

**Quy tắc bronze hiện hành (nguồn Việt Nam bổ sung):** một người kiểm tra toàn bộ ứng viên mạo danh tổ chức Việt Nam được sử dụng; người thứ hai kiểm độc lập mẫu con ngẫu nhiên phân tầng 30% và các trường hợp khó. Độ đồng thuận tính trên mẫu con ngẫu nhiên. Những đoạn mô tả quy tắc cũ bên dưới được giữ để lưu lịch sử, đã được thay bằng quy tắc này.

- [Kiểm kê và ghi chú rà soát](#kiem-ke-va-ghi-chu-ra-soat)
- [Nhật ký tìm và xác minh tài liệu](#nhat-ky-tim-va-xac-minh-tai-lieu)

<a id="kiem-ke-va-ghi-chu-ra-soat"></a>
## Kiểm kê và ghi chú rà soát

## Ghi chú rà soát và chuẩn bị nghiên cứu

Ngày rà soát: 03/10/2026. Tệp này phục vụ làm việc, tách khỏi đề cương nộp.

### 1. Kiểm kê PhishVN thực tế

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

### 2. Xác minh các tài liệu được trích

| Nguồn sơ cấp | Nội dung đã kiểm tra và cách sử dụng |
| --- | --- |
| [PHILTER, USENIX Security 2026](https://www.usenix.org/conference/usenixsecurity26/presentation/alam) | Trang công trình và BibTeX xác nhận 55 phương pháp; 4 tiêu chí chức năng và 3 tiêu chí an toàn. Đề cương chỉ dùng kết luận định hướng đánh giá. |
| [PhreshPhish v2](https://arxiv.org/abs/2507.10854v2), [toàn văn HTML](https://arxiv.org/html/2507.10854v2) | Bản đầu 14/07/2025, v2 ngày 11/02/2026. Xác nhận vấn đề leakage, tỷ lệ lớp và thiết kế benchmark. Ghi là preprint v2; không gán trạng thái xuất bản tạp chí/hội nghị. |
| [D-PhishNet, nhà xuất bản](https://www.sciencedirect.com/science/article/pii/S1389128625006152) | Metadata/tóm tắt sơ cấp xác nhận mô hình hai nhánh GNN–BERT, Computer Networks 271, 111648, 2025. Đề cương không dẫn số hiệu năng; chưa coi phần trả phí là đã đọc toàn văn. |
| [PhishLLM, USENIX Security 2024](https://www.usenix.org/conference/usenixsecurity24/presentation/liu-ruofan) | Xác nhận quan hệ thương hiệu–miền, ý định thu thập thông tin và xác minh qua tìm kiếm; tác giả và trang 523–540. Đề cương không vay mượn mức cải thiện của mô hình này làm kỳ vọng hiệu năng. |
| [PhishVN v4](https://data.mendeley.com/datasets/b97hxbxtpd/4), [bài báo](https://doi.org/10.1016/j.dib.2026.113195) | Kiểm kê CSV trực tiếp; bộ HTML–ảnh mới xác minh ở mức báo cáo tác giả. Metadata nguồn còn câu “under revision”, trong khi bài báo đã có DOI/ấn phẩm: trích thông tin xuất bản từ bài báo. |
| [Kho mã PhishVN](https://github.com/vuthainguyen1602/phishvn) | README yêu cầu dùng release `dib-113195` để tái lập bài báo; nhánh hiện tại có thay đổi về sau. Lưu ý kiểm chứng nhãn feed, nhất là bronze. |

Tài liệu Chrome đã mở lại trên trang chính thức để kiểm tra DOM/content script, declarativeNetRequest và cách cài demo cục bộ. Đây là nguồn kỹ thuật, không chứng minh khả năng phát hiện của mô hình.

### 3. Những điều chỉnh trong đề cương

- Đổi tên sang mạo danh tổ chức Việt Nam; extension chuyển về sản phẩm.
- Giữ RQ1–RQ3, bỏ RQ4; ad block chỉ là công tắc demo tùy chọn.
- Dùng grouped k-fold theo miền, kiểm soát template gần trùng và trùng liên nguồn; chọn ngưỡng trong phần nội bộ, báo cáo FPR thực đo tại mục tiêu 1%/5%.
- Ngưỡng 150 mẫu/50 miền là mốc khả thi, không thay cho phân tích khoảng tin cậy. Các ngưỡng 5 miền/tổ chức dùng để chọn phân nhóm báo cáo từ toàn bộ nhãn tham chiếu trước khi xem kết quả mô hình; không xóa tổ chức ít mẫu khỏi danh mục.
- Cụ thể hóa từ điển, biến thể, chuẩn hóa không dấu, so khớp mờ, ngữ cảnh tuyên bố danh tính và quan hệ miền chính thức/ủy quyền.
- TF-IDF + char n-gram trước; LightGBM bổ sung cho M2/M3, encoder tùy chọn sau phần lõi.
- Cam kết báo cáo, dữ liệu được phép công bố, mã/mô hình, extension; đo p50/p95 thực tế.

### 4. Việc cần thực hiện trong hai tuần đầu

Đã hoàn tất: kiểm kê tệp URL công khai và checksum.

Còn cần thực hiện khi bắt đầu nghiên cứu: gửi yêu cầu HTML với thông tin nhóm/giảng viên; dựng môi trường sandbox và bộ thu thập; chụp trang sống từ nguồn truy cập được; đọc khoảng 50 mẫu; tổng hợp số mẫu/miền đủ bằng chứng. Chưa gửi thư, chưa chạy crawler trang phishing, chưa có dữ liệu HTML mới. Hai việc xin archive và thu thập mới được thực hiện song song.

Phương án thu thập tối thiểu: đọc feed hợp lệ → chuẩn hóa và loại URL đã chụp → đưa vào hàng đợi → mở trong trình duyệt sandbox → lưu rendered DOM, ảnh, chuyển hướng, thời điểm và trạng thái → kiểm tra nhãn. Không đưa biểu mẫu, cookies hay thông tin cá nhân thật vào môi trường thu thập. Chốt nguồn, nhịp cập nhật và giới hạn tài nguyên sau khảo sát quyền truy cập.

### 5. Thông tin cần bổ sung trước khi nộp

Tên trường/khoa, thông tin giảng viên và thành viên; lịch chính thức; người gán nhãn thứ hai; khả năng máy ảo/sandbox. Người dùng đã xác nhận trường thúc đẩy ứng dụng AI và việc hỗ trợ AI không vướng yêu cầu của trường. Ghi nhận thông tin này theo xác nhận của người dùng; tiếp tục lưu vết hỗ trợ, nguồn đã kiểm chứng và quyết định của nhóm.


### 6. Rà soát bổ sung sáu điểm

1. Đã chạy lại script kiểm kê CSV: 53.116 dòng dữ liệu (không tính header), lõi gold/silver 18.997; SHA-256 trùng MANIFEST. Tổng quan giữ cách dẫn số liệu theo tác giả để phân biệt văn liệu và thao tác kiểm kê. Số 868/209/659 có ở mục 3.6 bài báo và bản PMC lập chỉ mục; chưa đếm archive nội dung độc lập.
2. Danh mục cơ sở chỉ lấy từ nguồn chính thức, khóa trước thực nghiệm và dùng chung mọi fold. Nhánh bổ sung từ dữ liệu nếu làm phải dựng riêng cả fold ngoài và phép chia nội bộ tương ứng.
3. Quy tắc 5 miền đếm theo nhãn trên toàn tập trước khi xem kết quả; chỉ quyết định báo cáo nhóm, không điều chỉnh mô hình.
4. Thêm mốc tham chiếu 1.500 trang hợp lệ/500 miền, gồm 300 trang khó/100 miền. Điểm 1% có giới hạn do số FP ít và tập chọn ngưỡng nội bộ nhỏ; báo cáo FPR của tập hợp lệ gắn bối cảnh Việt Nam riêng. Các mục tiêu mẫu chưa phải dữ liệu thu được.
5. Bổ sung sáu nghiên cứu: Phishpedia (2021), PhishIntention (2022), KnowPhish (2024), Linh et al. về extension URL + fuzzy matching (2025), Nguyen và Nguyen về phishing website tiếng Việt (online 2026, năm trích dẫn Springer 2027), và preprint URL–text tiếng Việt của Vu (2026). Có tổng cộng 11 công trình nghiên cứu và 3 tài liệu Chrome. Khoảng trống đã thu hẹp theo tiền lệ mới tìm được.
6. Nhóm chính xác định theo tổ chức Việt Nam bị mạo danh, không theo ngôn ngữ. Trang tiếng Anh mạo danh ngân hàng Việt Nam được giữ; ngôn ngữ chỉ là thuộc tính phân nhóm. Nhãn tham chiếu độc lập với danh mục/đầu ra mô hình.

Bản trước sửa được lưu trong [De_cuong_NCKH_Phishing_Mau_2_Truoc_ra_soat_6_diem.md](/Users/yingjunn_/Study_/NCKH_2/docs/archive/De_cuong_NCKH_Phishing_Mau_2_Truoc_ra_soat_6_diem.md). Bản dùng tiếp là [đề cương hiện hành](/Users/yingjunn_/Study_/NCKH_2/docs/De_cuong_NCKH_Phishing_Mau_2.md).

### 7. Đợt rà soát nguồn và rủi ro bổ sung

Đã đối chiếu mục 3.6/868/209/659 từ toàn văn Europe PMC XML, DOI SSRN bằng Crossref, chương Springer và PDF BEEI. Chi tiết truy cập thành công/bị chặn, metadata và phạm vi nội dung đã đọc được cập nhật trong nhật ký tài liệu. Số nội dung PhishVN là tác giả báo cáo; chưa kiểm kê bộ gated.

Đề cương thêm quy tắc nhãn trước thực nghiệm: gold/silver ưu tiên làm nguồn khởi đầu, vẫn xác minh nội dung; bronze chưa kiểm chứng bị loại khỏi huấn luyện/đánh giá chính. Bronze được tiếp nhận sau hai người kiểm tra độc lập và phân xử có ghi nhận. Thêm rủi ro tập trung nguồn ở tác giả PhishVN/preprint và đường thu thập riêng khi chưa có quyền truy cập.

Grouped 5-fold lặp 3 seed định trước; kết quả lặp không được đếm như thêm mẫu độc lập. Mục 8 được rút gọn. Abstract bản hiện tại có 292 từ theo khoảng trắng; toàn bản khoảng 6.698 từ theo cách đếm đó, 42.437 byte. Số byte không quy đổi trực tiếp thành số trang. Chưa có tên trường/khoa hoặc quy định giới hạn trang để đối chiếu; đã hỏi người dùng. Thông tin giảng viên, thành viên, lịch và phân loại khoa còn cần người dùng điền, không tự tạo.


### 8. Đối chiếu lại hai câu và giảm tải kiểm chứng bronze

Đã kiểm tra lại bản XML toàn văn Europe PMC lưu tại `data/source_audit/PhishVN_EuropePMC_fulltext.xml`: article-id DOI khớp 10.1016/j.dib.2026.113195. Section `sec0008` có label **3.6**, title **Gated tier: captured pages**; đoạn đầu xác nhận 868 cặp gồm 209 phishing/659 hợp lệ. Tài liệu tham khảo có label **18**, nhan đề **A framework for vietnamese email phishing detection**, DOI **10.35940/ijitee.A4843.119119**, năm 2019. Do đó cả hai câu trong tổng quan có căn cứ từ toàn văn bài PhishVN; câu chưa công bố dữ liệu vẫn được dẫn là nhận định của tác giả PhishVN.

Quy tắc bronze hiện hành thay yêu cầu hai người kiểm từng mẫu: chỉ tập trung ứng viên mạo danh tổ chức Việt Nam, một người kiểm toàn bộ phần được sử dụng, người thứ hai kiểm độc lập mẫu con ngẫu nhiên phân tầng 30% và các trường hợp khó. Độ đồng thuận/kappa tính trên mẫu con ngẫu nhiên, báo cáo riêng trường hợp khó. Các bản ghi ứng viên không chỉ được chọn theo token URL; ghi lại nguồn/cách sàng lọc để nhận diện thiên lệch tuyển mẫu. Các quy tắc ở mục 7 và ghi chú cũ về hai người kiểm toàn bộ bronze được thay bằng mục 8 này.


<a id="nhat-ky-tim-va-xac-minh-tai-lieu"></a>
## Nhật ký tìm và xác minh tài liệu

## Nhật ký tìm và xác minh tài liệu — 03/10/2026

Mục đích: mở rộng tổng quan website phishing tiếng Việt, reference-based và triển khai trình duyệt. Đây là rà soát có chọn lọc; không phải tìm kiếm hệ thống hoặc kết luận không còn công trình khác. Các truy vấn được gửi tới công cụ tìm kiếm web; tên trường/đơn vị của tác giả không được dùng thay cho bằng chứng dữ liệu nghiên cứu thuộc Việt Nam.

### Truy vấn thực tế

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

### Nguồn bổ sung và mức xác minh

| Công trình | Nguồn sơ cấp và phần đã đọc | Điều được đưa vào đề cương |
| --- | --- | --- |
| Phishpedia | [USENIX 2021](https://www.usenix.org/conference/usenixsecurity21/presentation/lin), tóm tắt và BibTeX; phần mô tả phương pháp PDF được lập chỉ mục | Logo, đối sánh thương hiệu tham chiếu và miền; tên tác giả, năm, trang. Không trích mức hiệu năng. |
| PhishIntention | [USENIX 2022](https://www.usenix.org/conference/usenixsecurity22/presentation/liu-ruofan), tóm tắt và BibTeX | Ý định thương hiệu/thu thập thông tin và tương tác xác nhận; tên tác giả, năm, trang. Không coi nghiên cứu này là đánh giá tiếng Việt. |
| KnowPhish | [USENIX 2024](https://www.usenix.org/conference/usenixsecurity24/presentation/li-yuexin), tóm tắt và BibTeX | Tri thức thương hiệu đa phương thức, khai thác thông tin HTML; giới hạn bao phủ danh mục. Không tự thêm baseline chạy KnowPhish vào phạm vi 6–7 tháng. |
| Nguyen & Nguyen | [Springer](https://link.springer.com/chapter/10.1007/978-3-032-34772-5_4), tóm tắt, metadata và mục Cite this paper | Website tiếng Việt và pipeline URL–HTML với LLM. Chưa đọc toàn văn có trả phí; không suy đoán giao thức chia nhóm/FPR. Nhà xuất bản ghi trích dẫn năm 2027, published 15/08/2026, pp. 35–45. |
| Vu: Content and URL Fusion | [SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7454637), metadata/tóm tắt tác giả qua kết quả tìm kiếm được lập chỉ mục | URL + văn bản tiếng Việt, TF-IDF/encoder. Posted 13/09/2026, DOI 10.2139/ssrn.7454637. Mở trực tiếp trang gặp lỗi; chưa kiểm tra toàn văn/giao thức chi tiết. Ghi rõ preprint, không tuyên bố phản biện. |
| Linh et al. | [Trang tạp chí](https://beei.org/index.php/EEI/article/view/10099), tóm tắt; [PDF nhà xuất bản](https://beei.org/index.php/EEI/article/download/10099/4503) được lập chỉ mục | Extension Chrome, mô hình URL và fuzzy matching. Metadata 14(6), 4876–4889, 2025. PhiUSIIL không phải mặc định tập tiếng Việt dù tác giả làm việc tại Việt Nam. |

Nguồn về email tiếng Việt, spam hoặc lừa đảo nói chung được thấy trong tìm kiếm nhưng không đưa vào làm tiền lệ trực tiếp cho website phishing. Các bản sao Scribd/Studocu không được dùng làm nguồn xác minh.

### Cập nhật khoảng trống

Đã có công trình URL–text tiếng Việt và các phương pháp nhận diện thương hiệu–miền–ý định. Khoảng trống đề xuất được thu hẹp thành kiểm chứng giá trị tăng thêm của bộ tín hiệu mạo danh có cấu trúc, so với M2, trên nhóm mạo danh tổ chức Việt Nam ở miền chưa gặp, với ngưỡng FPR chọn nội bộ và khoảng tin cậy. Đây là câu hỏi thực nghiệm còn cần đối chiếu sâu, không phải tuyên bố phương pháp đầu tiên.

### PhishVN: tách hai loại bằng chứng

- CSV công khai: đã đếm lại trong phiên sửa này bằng `data/source_audit/kiem_ke_phishvn.py`; hash và kết quả ở `data/source_audit/PhishVN_kiem_ke.json`.
- HTML–ảnh: [mục 3.6 bài báo](https://doi.org/10.1016/j.dib.2026.113195) và [bản PMC được lập chỉ mục](https://pmc.ncbi.nlm.nih.gov/articles/PMC13572074/) xác nhận **tác giả báo cáo** 868 cặp, 209 phishing, 659 hợp lệ. Archive công khai đã tải không chứa HTML; chưa nhận archive gated để đếm độc lập.

### Đối chiếu trực tiếp bổ sung trước khi nộp

#### PhishVN

Trang PMC HTML gặp reCAPTCHA; đã đọc được toàn văn JATS/XML do **Europe PMC** phục vụ qua [API toàn văn công khai](https://www.ebi.ac.uk/europepmc/webservices/rest/PMC13572074/fullTextXML). Đã lưu tại `data/source_audit/PhishVN_EuropePMC_fulltext.xml`.

- Nhan đề và DOI trong bài trùng PhishVN đang trích.
- Section id `sec0008`, label **3.6**, title **Gated tier: captured pages**. Đoạn đầu nêu 868 records, 209 phishing và 659 benign, lưu DOM và ảnh theo mã bản ghi. Đã đối chiếu cả label XML và văn bản mục này; không chỉ dựa vào snippet tìm kiếm.
- Điều kiện: chỉ dùng nghiên cứu, mở HTML trong máy ảo cách ly, không phân phối lại. Chưa nhận archive gated nên đây vẫn là xác minh **số tác giả báo cáo**, không phải đếm tệp nội dung độc lập.
- Background nói nghiên cứu tiếng Việt trước chưa công bố dữ liệu. Kiểm tra tài liệu [18] cho thấy nhan đề **A framework for vietnamese email phishing detection** (Cho, Nguyen và Tisenko, 2019). Không diễn đạt thành một nghiên cứu website trước đó chưa công bố dữ liệu.
- Mô tả Mendeley v4 xác nhận kappa bốn lớp 0,609; nhiễu nhãn nhóm dương 12,1%, tập trung bronze. Các chỉ số thuộc audit mẫu của tác giả. Quy tắc đề cương: ưu tiên gold/silver có kiểm chứng; bronze chỉ vào thực nghiệm chính sau kiểm tra độc lập và phân xử.

#### SSRN

Đã mở DOI `10.2139/ssrn.7454637`; DOI chuyển đến SSRN nhưng trang đích hiện màn kiểm tra Cloudflare. Không vượt màn kiểm tra. **Crossref trả metadata/tóm tắt tác giả thành công** tại [API DOI](https://api.crossref.org/works/10.2139/ssrn.7454637), lưu `data/source_audit/SSRN_7454637_Crossref.json`.

Crossref xác nhận nhan đề Content and URL Fusion for Vietnamese Phishing Pages: Five Encoders under a Variance-Corrected Protocol and a Strength-Controlled Paraphrase Attack; tác giả metadata given Thai, family Nguyen Vu; năm 2026; loại bản thảo đăng tải. Tóm tắt xác nhận TF-IDF/encoder văn bản tiếng Việt kết hợp URL. Metadata không cung cấp page range; 23 trang là thông tin trang SSRN được lập chỉ mục, chưa kiểm tra PDF. Tài liệu tham khảo của đề cương không ghi số trang preprint. Không coi toàn văn hoặc đánh giá riêng mạo danh tổ chức Việt Nam là đã được kiểm tra.

#### Springer

DOI `10.1007/978-3-032-34772-5_4` mở được [trang nhà xuất bản](https://link.springer.com/chapter/10.1007/978-3-032-34772-5_4). Xác nhận Anh-Binh Nguyen và Anh-Nhat Nguyen, nhan đề Leveraging Large Language Models for Automated Online Fraud Detection: A Case Study in Vietnam, pp. 35–45, LNNS 2127. Mục Cite this paper ghi **2027**, mục Published ghi **15/08/2026**. Tóm tắt mô tả URL và 500 ký tự HTML đầu, kết quả giới hạn website tiếng Việt. Chưa đọc toàn văn trả phí; không suy từ tóm tắt rằng nhóm nghiên cứu là các tổ chức Việt Nam.

#### BEEI

Đã thử mở DOI `10.11591/eei.v14i6.10099` (web báo lỗi, curl hết thời gian chờ); nội dung được xác minh bằng cách đối chiếu trực tiếp [trang công trình](https://beei.org/index.php/EEI/article/view/10099) cùng [PDF nhà xuất bản](https://beei.org/index.php/EEI/article/download/10099/4503). PDF trang đầu xác nhận nhan đề, bốn tác giả, **14(6), tháng 12/2025, 4876–4889** và DOI. Tóm tắt và thuật toán nêu Chrome extension, exact/fuzzy matching, mô hình URL và danh sách trắng/đen. PhiUSIIL là dữ liệu dùng trong bài; không trình bày bài này như thực nghiệm nội dung website tiếng Việt.

#### Điều chỉnh tuyên bố tổng quan

Bỏ cụm “tiền lệ trực tiếp” cho hai nguồn tiếng Việt, thay bằng công trình liên quan gần về đầu vào. Phạm vi nhóm tổ chức và giao thức chi tiết không được suy từ tóm tắt. Khoảng trống về dữ liệu có kiểm chứng được nêu có nguồn và phân biệt email với website.


## Phương án dữ liệu giữ nguyên lõi sau đăng ký — 03/10/2026

### Nguồn đã thử truy cập thực tế

[PhreshPhish](https://huggingface.co/datasets/phreshphish/phreshphish) có URL, HTML, nhãn nguồn, target, ngày và metadata ngôn ngữ. Repository metadata báo `gated: false`, license CC BY 4.0; dataset card giới hạn sử dụng vào nghiên cứu chống phishing. Metadata revision tại thời điểm kiểm tra: `eabec4b7a66324b79cc8a0ad856d1731dc26fe1a`. Dataset card được lưu theo revision. Điều kiện công bố lại và nội dung bên thứ ba cần được kiểm tra trước khi chia sẻ; truy cập công khai không đồng nghĩa với tự do sử dụng mọi mục đích.

Đã tải 20 bản ghi qua API rows không đăng nhập: 8 nhãn phish, 12 benign, 20 HTML không rỗng, 19 trích được văn bản bằng HTMLParser, 12 có thẻ form. Không có ô bị API đánh dấu cắt ngắn. Đây là thử kỹ thuật, không đo hiệu năng hoặc kiểm chứng nhãn. Mẫu là 20 dòng đầu, không phải mẫu đại diện; parser không chạy JavaScript nên không bảo đảm giống DOM khi trang chạy. Trường target là nhãn nguồn, chỉ dùng để kiểm kê/gán nhãn, không đưa làm đặc trưng đầu vào mô hình.

Các tệp nằm ở `data/source_audit/phreshphish/`: `pilot_20_rows.json`, `pilot_summary.json`, `repository_metadata.json`, `README_at_revision.txt`. Bản rows API chưa khóa revision; lưu checksum để nhận diện chính xác nội dung thử tải. Khi xây tập chính cần lấy tệp theo revision, không mặc định snapshot API bằng commit metadata.

API filter tiếng Việt ở train trả 500, test hết thời gian chờ. Chưa xác nhận số lượng mẫu tiếng Việt hoặc tổ chức Việt Nam trong toàn bộ corpus. 20 mẫu thử không có metadata vi. Không suy rằng tập không có tiếng Việt từ mẫu nhỏ này.

### Lịch sử đề xuất phạm vi trước khi đăng ký

**Đã được thay thế:** người dùng đã đồng ý phạm vi tổ chức nói chung; đề cương hiện hành đã đổi tên và lấy dữ liệu quốc tế làm tập chính. Nội dung dưới đây lưu lại cân nhắc trước khi chốt. Khi tên còn giới hạn tổ chức Việt Nam, nguồn quốc tế chỉ là tập nền và chưa bảo đảm dữ liệu nhóm mục tiêu.

Phương án giảm phụ thuộc dữ liệu đề xuất: **Phát hiện website phishing mạo danh tổ chức bằng học máy kết hợp URL và tín hiệu trong nội dung trang**. Việt Nam được ghi là nhóm ứng dụng ưu tiên có phân tích riêng theo cỡ mẫu thực tế. Thực nghiệm chính vẫn giữ M0–M3, đặc trưng tổ chức–miền–ý định, ngưỡng FPR và extension. Đây là chốt phạm vi trước đăng ký, không chuyển lõi khi dữ liệu thiếu về sau.

Nếu người dùng giữ tên Việt Nam, phải tiếp tục xác minh nguồn nhóm mục tiêu trước khi xem hướng đã chắc chắn; không dùng PhreshPhish quốc tế để tuyên bố đã giải quyết toàn bộ rủi ro. Không thể bảo đảm tính khả thi riêng Việt Nam chỉ bằng 20 mẫu tải thử.

### Các phương án thay nguồn trong cùng lõi

1. Tập nền có sẵn: lấy mẫu PhreshPhish, kiểm nhãn và chất lượng URL–HTML; dựng danh mục tổ chức từ nguồn chính thức, khóa trước đánh giá. M0–M3 dùng cùng mẫu có đủ nội dung. Đây là đường truy cập đã thử.
2. Nhóm Việt Nam: PhishVN URL công khai làm nguồn ứng viên; bộ gated xin được là bổ sung. Thu thập HTML độc lập từ các nguồn cho phép, kiểm chứng tổ chức và nhãn. Không chờ thư tác giả mới bắt đầu thu thập.
3. Nếu một nguồn bị hạn chế: loại nguồn đó và thay bằng nguồn có nội dung và điều kiện sử dụng phù hợp. Nếu không được công bố lại, giữ dữ liệu nội bộ theo điều kiện nguồn, công bố mã/quy trình và metadata được phép.
4. Nếu crawler thu ít: dùng nội dung đã lưu của nguồn dự phòng để hoàn thành phép so sánh trong phạm vi tổ chức chung nếu đã đăng ký như vậy; mô tả phần Việt Nam đúng cỡ mẫu. Không chuyển sang URL-only hoặc giả vờ dữ liệu quốc tế là dữ liệu tổ chức Việt Nam.
5. Trang mô phỏng chỉ kiểm tra chức năng extension/nội dung động, không thay mẫu phishing thực để chứng minh hiệu quả mô hình.

Tên/phạm vi hiện đã chốt và nguồn dự phòng đã ghi trong hồ sơ. Hai tuần đầu khóa phiên bản, kiểm chất lượng tập chính và kiểm kê nhóm Việt Nam. Nguồn Phishpedia/KnowPhish được khảo sát trên kho chính thức nhưng chưa tải và kiểm toàn bộ điều kiện; không dùng làm nguồn đã bảo đảm.
