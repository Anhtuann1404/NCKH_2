# Current tasks

Cập nhật 04/10/2026. Sprint khởi động dài hai tuần tính từ ngày nhóm bắt đầu; chưa có ngày bắt đầu chính thức.

## Trạng thái có bằng chứng

- DONE — hướng đề cương được GVHD duyệt: theo xác nhận người dùng.
- DONE — nhóm từ 4 người trở lên: theo xác nhận người dùng, chưa điền tên/ngân sách giờ.
- DONE — kiểm kê URL PhishVN: [kết quả](../data/source_audit/PhishVN_kiem_ke.json), [script](../data/source_audit/kiem_ke_phishvn.py).
- DONE — thử kỹ thuật 20 PhreshPhish: [summary](../data/source_audit/phreshphish/pilot_summary.json). Không phải tập thực nghiệm đã xác minh.
- DONE — bộ tài liệu khởi động và hợp đồng API v0.1.
- DONE — D là người dùng/lead, nhận model và API–extension; phân công owner A/B/C/D ở [TEAM](TEAM.md). A/B/C chưa có họ tên.
- TODO — date toàn nguồn, freeze danh mục/codebook, pilot nhãn, dữ liệu chính, mô hình, API và extension.

`TODO` chưa làm; `IN_PROGRESS` đang có công việc thực; `BLOCKED` có phụ thuộc cụ thể; `DONE` có sản phẩm kiểm tra được. Không đánh dấu DONE chỉ vì đã có mô tả.

## Việc tiếp theo theo thứ tự

### START-01 — Chốt người và ngân sách giờ

Status: TODO. Owner: D — lead. Phụ thuộc: không.

Điền tên A/B/C/D, giờ mỗi tuần trong 6–8 tuần gán nhãn, xác nhận D phụ trách model/API–extension và nơi giữ dữ liệu. A/B/C là người khác nhau. Done khi cả nhóm xác nhận phân công và tổng giờ; cập nhật mục đội nhóm trong file này, không sửa đề cương để thay lõi.

### DATA-01 — Khóa nguồn và audit riêng date

Status: TODO. Owner: C. Phụ thuộc: START-01 để xác định người thực hiện.

Lấy revision và tệp có checksum; đọc riêng date từ nguồn pinned, min/max, counts tháng, thiếu/sai ngày và split. Không dựa API statistics hiện tại để nói đã có date toàn corpus. Giữ official test riêng. Done khi có manifest xác minh và audit date tái lập; lấy mẫu pilot đã mở phải nằm trong exclusion registry.

### DATA-02 — Khóa danh mục và codebook

Status: TODO. Owner: C + A/B rà quy tắc, GVHD hỗ trợ. Phụ thuộc: DATA-01.

Đối chiếu cửa sổ quý, nguồn ngoài, 14 mã dự kiến, ánh xạ thương hiệu con; xác minh endpoint/UGC/ủy quyền và nguồn hiệu lực. Done khi dictionary/codebook có version/hash và log ngày khóa, trước mở nhãn/nội dung tập chính. Nhánh thời gian có quy tắc tri thức as-of riêng.

### LABEL-01 — View mù và pilot có bấm giờ

Status: TODO. Owner: C tạo view; A/B đọc độc lập. Phụ thuộc: DATA-02.

Giao diện chỉ có sample_id, URL–nội dung; ẩn target/nhãn nguồn/điểm mô hình và nhãn người còn lại. Dùng 20 mẫu kỹ thuật, bổ sung 12 phishing ngoài tập đánh giá để pilot có 20 phishing. Done khi lưu nhãn độc lập, thời gian gồm tra cứu/phân xử và giờ dự kiến. Không chạy HTML nguồn trực tiếp.

### PLAN-01 — Khóa quy mô và kế hoạch audit

Status: TODO. Owner: D + A/B/C. Phụ thuộc: LABEL-01.

Áp dụng quy tắc 2.000→1.200 nếu trung bình >5 phút/phishing hoặc thiếu giờ; nếu vẫn quá tải thì ghi quy mô thấp hơn trước kết quả. Khóa mẫu 30% ngẫu nhiên, audit lớp ~200 và tiêu chí hard benign. Done khi có sampling plan, seed, giờ dự phòng và quyết định cỡ mẫu.

### DEV-01 — Scaffold parser/features và môi trường

Status: TODO. Owner: D (preprocessing/features); C (import/index dữ liệu). Phụ thuộc: có thể chuẩn bị bằng fixture trước DATA-02.

Tạo môi trường, khóa dependency, module preprocessing và fixture domain/UGC/HTML không có nội dung thật. Done khi fixture chứng minh không thực thi HTML, không fetch mạng, không dùng labels/metadata làm features. Chưa huấn luyện tập chính ở bước này.

### EXT-01 — Khung MV3 và mock API

Status: TODO. Owner: D. Phụ thuộc: đọc API_SPEC; có thể làm song song.

Popup bật/tắt, snapshot sạch, navigation/revision và cảnh báo mock. Done khi chuyển trang không nhận kết quả cũ, service offline hiện chưa đánh giá được. Mock luôn có nhãn rõ; không ghi số đo mock thành hiệu năng mô hình.

## Đội nhóm cần điền

- A — họ tên: chưa điền; giờ/tuần: chưa điền.
- B — họ tên: chưa điền; giờ/tuần: chưa điền.
- C — họ tên: chưa điền; giờ/tuần: chưa điền.
- D — người dùng, lead + model + API–extension; họ tên chính thức/giờ tuần: chưa điền.
- Owner model: D; C bàn giao dữ liệu, B kiểm tái lập sau khóa nhãn.
- GVHD và thành viên thêm: chưa điền.

## Điều kiện trước huấn luyện chính

- [ ] Revision/checksum và quyền nguồn đã ghi.
- [ ] Audit date, cửa sổ, dictionary/codebook khóa.
- [ ] Pilot loại khỏi tập đánh giá; ngân sách giờ và cỡ mẫu chốt.
- [ ] Nhãn tổ chức hoàn chỉnh phần giữ lại, QC/audit và phân xử có log.
- [ ] Groups/splits và các loại trùng đã kiểm; official test không vào phát triển.
- [ ] Preprocessing/features version hóa; pipeline học chỉ fit phần huấn luyện.

## Nhật ký cập nhật

03/10/2026 — tạo khung khởi động từ đề cương được duyệt; chưa khởi động pipeline, crawler hoặc mô hình. Đã kiểm liên kết nội bộ, JSON/config, schema refs và 4 ví dụ request/response bằng JSON Schema 2020-12; các request chứa target, thiếu HTML, revision âm hoặc file URL bị schema từ chối. Chưa kiểm toàn bộ OpenAPI meta-schema hoặc backend chạy thật. Cập nhật trạng thái cùng đường dẫn bằng chứng sau mỗi task, không tạo file current task theo ngày.

04/10/2026 — chốt ownership 4 vai trò: A nhãn, B kiểm độc lập/QA, C pipeline dữ liệu/view mù, D người dùng/lead + model + API–extension. Các task triển khai vẫn TODO; chưa huấn luyện hoặc chạy API.

04/10/2026 — đưa phân công TEAM vào mục 6.1, bảng tiến độ mục 8 và bảng thông tin bốn thành viên của đề cương theo yêu cầu. D nhận trực tiếp model/API–extension và lead; họ tên A/B/C và giờ tuần chưa chốt.
