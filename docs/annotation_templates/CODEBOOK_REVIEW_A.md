# Rà quy tắc nhãn — góp ý của A

Ngày 04/10/2026. Trạng thái: **draft để C/B rà**, không phải codebook đã khóa. Nguồn: DATA_PROTOCOL và đề cương 5.2b–c; chưa đọc nội dung tập chính hoặc lượt B. Không xác minh mới miền/alias/ủy quyền trong tài liệu này.

## Quy tắc có trong giao thức, cần giữ nguyên

| Tình huống | Cách ghi của A |
| --- | --- |
| Outlook/Office 365/Microsoft 365/OneDrive; Gmail/Drive; Facebook/Instagram/WhatsApp; AWS; iCloud | Giữ tên dịch vụ; chuẩn hóa lần lượt Microsoft, Google, Meta, Amazon, Apple theo codebook khóa |
| LinkedIn; Twitter/X | LinkedIn mã riêng; Twitter/X cùng mã chuẩn |
| Tên trong bài viết, footer hoặc danh sách đối tác | Ghi vai trò nhắc đến; không tự coi là mục tiêu mạo danh |
| Google Sites/Docs/Forms, SharePoint, Blob/S3 hoặc hồ sơ xã hội | Hạ tầng chung không chứng minh danh tính/ủy quyền; giữ chưa xác minh khi không có bằng chứng |
| Tên thương hiệu trong path/query hoặc subdomain của miền khác | Không suy miền chính thức bằng substring |
| Nhiều tổ chức | Giữ tất cả mục tiêu có bằng chứng; chọn chính theo form/luồng; không rõ thì đa mục tiêu |
| Tổ chức ngoài danh mục có bằng chứng | Ghi tên và trạng thái ngoài danh mục; không biến thành unknown vì thiếu mã trong 14 tổ chức |
| Không đủ nội dung để xác nhận tổ chức | Chưa xác định, ghi lý do và ca khó nếu cần; không tự gán outside-catalog |
| Benign khó có tên tổ chức/form đăng nhập | Kiểm bằng chứng nội dung và miền/endpoint theo quy tắc; không dùng đầu ra M3 làm nhãn phụ |

Danh mục 14 mã và ánh xạ ở đề cương là dự kiến trước khóa; A không tự chuẩn hóa thành một bộ mã máy chính thức khi C chưa chốt.

## Điểm cần C/B chốt trước lượt thực

| ID | Điểm mở | Đề xuất/đầu ra cần khóa |
| --- | --- | --- |
| R-A01 | Mã máy và trạng thái tổ chức | C cung cấp mã chuẩn, cách biểu diễn unknown/no-clear-target/outside-catalog/multi-target. Mã ngoài danh mục không được tự thêm vào dictionary mô hình |
| R-A02 | Vai trò danh tính và vai trò miền | Tách tên đang tự nhận danh tính/nhắc đến khỏi `first_party_identity`, `first_party_content`, `user_content_hosting`, `authorized_service`, `unverified`; tránh dùng một enum cho hai khái niệm |
| R-A03 | Chọn mục tiêu chính khi nhiều form/tên | Khóa quy tắc theo luồng thu thập thông tin, xử lý ngang hàng/không rõ và biểu diễn multi-target trong báo cáo đồng thuận |
| R-A04 | Phân loại insufficient_evidence | Chốt nội dung tối thiểu và cách lưu lớp với trạng thái tổ chức riêng: có thể lớp xác định được nhưng tổ chức chưa xác định; thiếu tổ chức không tự làm lớp unknown |
| R-A05 | Hard benign và nhãn phụ RQ3 | C/D khóa tiêu chí lựa chọn trước kết quả; A/B thống nhất nhãn phụ, trường hợp unknown và bằng chứng, không lấy cờ M3 làm tham chiếu |
| R-A06 | Tra cứu ngoài view | C chốt nguồn chính thức/version được phép dùng, cách ghi ngày/hiệu lực; không mở URL mẫu để thu mới. Thiếu tài liệu ủy quyền ghi chưa xác minh |
| R-A07 | Ảnh/logo và nội dung thiếu | Chốt cách sử dụng ảnh có sẵn, yêu cầu bản trích bổ sung và khi nào giữ thiếu bằng chứng; không suy chắc từ logo đơn lẻ |
| R-A08 | Sự cố lộ target/nhãn B/prediction | C chốt cách cách ly lượt/batch, lưu lịch sử và quy tắc thay annotator/mẫu khi cần; không gọi lượt đã lộ là mù độc lập |
| R-A09 | Hỗ trợ AI | Nhóm chốt có dùng trong lượt thật không, cách disclosure và human verification; hỗ trợ AI không được tính thành hai người kiểm độc lập hoặc giờ người pilot |

## Góp ý cụ thể để C/B đưa vào bản khóa

Các phương án dưới là góp ý do Codex soạn hỗ trợ A, chưa được A/B/C duyệt. Có thể dùng để thảo luận trực tiếp thay vì chỉ nêu câu hỏi. Chúng không tự sửa dictionary hoặc nhãn nguồn.

### R-A01 — Tách mục tiêu chính khỏi tình trạng danh mục

Đề xuất giữ `primary_org_status` cho khả năng xác định mục tiêu chính (`identified`, `unknown`, `no_clear_target`, `multi_target`) và `catalog_status` riêng cho từng mục tiêu (`in_catalog`, `outside_catalog`, `unresolved`). Ví dụ một tổ chức ngoài danh mục vẫn có thể là mục tiêu chính đã nhận diện; không nên ép chọn giữa “identified” và “outside_catalog”.

`unknown`: nội dung không đủ xác định tên/vai trò. `no_clear_target`: đủ nội dung để quan sát nhưng không thấy mục tiêu tổ chức rõ. `multi_target`: có từ hai mục tiêu có bằng chứng mà không chọn được chính theo luồng. Không dùng `null` như một nhãn hoàn thành; `null` trong biểu mẫu nghĩa là chưa điền.

C chốt mã máy, ánh xạ sang cách biểu diễn kappa và quy tắc nhãn ngoài danh mục. Không tự thêm tổ chức ngoài danh mục vào dictionary mô hình chỉ vì A quan sát thấy.

### R-A02 — Ghi vai trò theo từng tên, không chỉ toàn trang

Một trang có thể tự nhận là dịch vụ A và chỉ nhắc B trong bài viết/footer. Đề xuất ghi `identity_role` trong từng phần tử `org_targets` hoặc hồ sơ tên quan sát: `identity_claim`, `mention_only`, `unclear`; vai trò cấp trang nếu cần chỉ là tổng hợp. Chỉ tên đang đóng vai mục tiêu có bằng chứng mới vào tập mục tiêu; tên nhắc tới vẫn được giữ trong ghi chú/tên quan sát để giải thích.

`domain_role` là quan hệ hostname/endpoint với tổ chức theo nguồn khóa, không là vai trò tên trong văn bản. Không suy một trong hai trường từ trường còn lại.

### R-A03 — Quy tắc chọn chính theo bằng chứng của luồng

Đề xuất thứ tự đọc: (1) tổ chức/dịch vụ mà vùng nhập thông tin đang tự nhận đại diện; (2) lời dẫn và heading gắn trực tiếp với vùng đó; (3) các tuyên bố khác. Tên prominent hoặc xuất hiện nhiều nhất không tự thắng. Không suy chính chỉ từ hostname đích form: đích đó có thể là bên thu thập, không phải tổ chức bị mạo danh.

Nếu có nhiều lựa chọn ngang hàng và không có luồng mặc định rõ trong snapshot, giữ mọi mục tiêu và `multi_target`; không tự click để tạo luồng mới. Khi tên/luồng mâu thuẫn, chuyển ca khó kèm trích dẫn hai phía. C/B chốt cách đưa mã đa mục tiêu vào báo cáo đồng thuận trước phân xử.

### R-A04 — Nhãn lớp và nhãn tổ chức là hai quyết định riêng

Có thể nhận diện rõ tên tổ chức nhưng chưa đủ kết luận phishing/benign; cũng có thể nhận diện hành vi lừa đảo rõ mà chưa biết tổ chức. Đề xuất ghi lớp `insufficient_evidence` khi không đủ bằng chứng về lớp, kèm lý do cụ thể; giữ nhận diện tổ chức có bằng chứng ở trường riêng. Với trang rỗng/lỗi/ảnh không đọc được, ghi phần quan sát được và phần thiếu, không ép benign.

URL khác lạ, logo hay password field đơn lẻ không quyết lớp. C/B cần chốt loại bằng chứng đủ để kết luận lớp và cách xử lý mẫu thiếu trước chọn tập cuối; nhãn nguồn không được dùng bù cho thiếu bằng chứng trong lượt độc lập.

### R-A05 — Nhãn phụ hard benign dựa trên quan sát

Đề xuất C/D chốt tiêu chí lấy mẫu độc lập với kết quả mô hình. Trong hồ sơ A ghi riêng: có tên tổ chức, có tuyên bố danh tính, có yêu cầu thông tin nhạy cảm, vai trò hạ tầng/ủy quyền và lý do lớp. Các trường không quan sát được để `unknown` theo mã C chốt, không coi là “không có”. Một mẫu được chọn vào strata hard benign chưa chứng nhận lớp benign khi A chưa đọc.

Trang hợp lệ nhắc thương hiệu hoặc sử dụng dịch vụ đăng nhập có thể là ca khó; chỉ kết luận theo nội dung và bằng chứng khóa tương ứng. Không dùng tỷ lệ cảnh báo M3 để chọn lại hoặc sửa nhãn phụ.

### R-A06 — Ghi bằng chứng tra cứu và hiệu lực

Đề xuất dùng tài liệu chính thức/dictionary đã khóa mà C bàn giao. Nếu cần thêm tài liệu, A ghi yêu cầu trung lập cho C, không mở website mẫu. Khi tra nguồn tham chiếu được phép, ghi tiêu đề/URL nguồn, ngày kiểm, phạm vi hostname/endpoint, mốc hiệu lực và đoạn hỗ trợ ngắn. Tài liệu hiện tại chưa chứng minh quan hệ ở quá khứ; thiếu bằng chứng lịch sử để chưa xác minh và báo giới hạn.

### R-A07 — Không đoán từ ảnh hoặc nội dung thiếu

Đề xuất dùng ảnh chụp đã có trong gói C. Logo đọc rõ chỉ hỗ trợ tên quan sát, không chứng nhận danh tính, quyền sở hữu hoặc lớp. Không đọc được chữ trong ảnh thì ghi đúng giới hạn, yêu cầu C bổ sung snapshot/trích nội dung. OCR hoặc thu mới nếu có là quy trình riêng cần ghi dấu vết; không tự bổ sung vào lượt gốc như thể đã quan sát ngay từ đầu.

### R-A08 — Bảo toàn lịch sử khi bị lộ

Đề xuất ghi incident ID, sample/batch, trường lộ và thời điểm; ngừng lượt liên quan, báo C qua kênh nhóm và giữ hồ sơ đã có. C/B/D quyết phạm vi ảnh hưởng và phương án lấy mẫu/người kiểm khác. Không xóa dấu vết rồi gọi lượt gán lại của cùng người là mù: người đó đã biết thông tin lộ. Không tự loại mẫu để tăng đồng thuận.

### R-A09 — Giữ hai lượt người độc lập

Đề xuất lượt A/B thật bắt đầu bằng quyết định riêng của người đọc; nếu dùng AI, ghi công cụ/version, phạm vi, thông tin đầu vào và người kiểm, theo lựa chọn nhóm. Không cung cấp kết luận A hay gợi ý chung từ lượt A cho B trước khóa lượt B. Hai kết quả AI không được gọi là hai người gán độc lập. Pilot công sức đo giờ người đọc/kiểm; ghi hỗ trợ AI để giải thích điều kiện đo. Phần hỗ trợ hiện tại chỉ là soạn tài liệu chuẩn bị.

## Nhật ký quyết định cần nhóm điền

| ID | Quyết định và lý do | Người xác nhận | Version/hash codebook | Ngày hiệu lực |
| --- | --- | --- | --- | --- |
| R-A01–R-A09 | Chưa chốt | Chưa xác nhận | Chưa có | Chưa có |

C là owner xuất/khóa codebook; A/B cùng rà. Bảng này không thay bản khóa của C và chưa đủ để bắt đầu LABEL-01.
