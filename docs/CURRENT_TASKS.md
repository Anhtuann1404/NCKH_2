# Current tasks

Cập nhật 04/10/2026. Sprint khởi động dài hai tuần tính từ ngày nhóm bắt đầu; chưa có ngày bắt đầu chính thức.

## Trạng thái có bằng chứng

- DONE — hướng đề cương được GVHD duyệt: theo xác nhận người dùng.
- DONE — nhóm từ 4 người trở lên: theo xác nhận người dùng; B đã xác nhận 5–10 giờ/tuần, tên và ngân sách giờ các thành viên còn lại chưa điền.
- DONE — kiểm kê URL PhishVN: [kết quả](../data/source_audit/PhishVN_kiem_ke.json), [script](../data/source_audit/kiem_ke_phishvn.py).
- DONE — thử kỹ thuật 20 PhreshPhish: [summary](../data/source_audit/phreshphish/pilot_summary.json). Không phải tập thực nghiệm đã xác minh.
- DONE — bộ tài liệu khởi động và hợp đồng API v0.1.
- DONE — D là chủ nhiệm/lead, nhận model và API–extension; phân công owner A/B/C/D ở [TEAM](TEAM.md). B là Phùng Tấn Minh; A/C/D chưa điền họ tên chính thức.
- TODO — date toàn nguồn, freeze danh mục/codebook, pilot nhãn, dữ liệu chính, mô hình, API và extension.

`TODO` chưa làm; `IN_PROGRESS` đang có công việc thực; `BLOCKED` có phụ thuộc cụ thể; `DONE` có sản phẩm kiểm tra được. Không đánh dấu DONE chỉ vì đã có mô tả.

## Việc tiếp theo theo thứ tự

### START-01 — Chốt người và ngân sách giờ

Status: IN_PROGRESS. Owner: D — lead. Phụ thuộc: không.

Điền tên A/B/C/D, giờ mỗi tuần trong 6–8 tuần gán nhãn, xác nhận D phụ trách model/API–extension và nơi giữ dữ liệu. A/B/C là người khác nhau. Done khi cả nhóm xác nhận phân công và tổng giờ; cập nhật mục đội nhóm trong file này, không sửa đề cương để thay lõi.

Tiến độ 04/10/2026: B đã xác nhận vai trò, họ tên, thông tin hồ sơ và ngân sách 5–10 giờ/tuần. Hồ sơ đã điền trong [đề cương hiện hành](De_cuong_NCKH_Phishing_Mau_2.md), phần bảng thành viên và mục 6.1. Kinh nghiệm/kỹ năng B chưa cung cấp; còn chờ thông tin A/C/D, GVHD, nơi giữ dữ liệu và xác nhận của cả nhóm trước khi đánh dấu DONE.

### DATA-01 — Khóa nguồn và audit riêng date

Status: TODO. Owner: C. Phụ thuộc: START-01 để xác định người thực hiện.

Lấy revision và tệp có checksum; đọc riêng date từ nguồn pinned, min/max, counts tháng, thiếu/sai ngày và split. Không dựa API statistics hiện tại để nói đã có date toàn corpus. Giữ official test riêng. Done khi có manifest xác minh và audit date tái lập; lấy mẫu pilot đã mở phải nằm trong exclusion registry.

### DATA-02 — Khóa danh mục và codebook

Status: TODO. Owner: C + A/B rà quy tắc, GVHD hỗ trợ. Phụ thuộc: DATA-01.

Đối chiếu cửa sổ quý, nguồn ngoài, 14 mã dự kiến, ánh xạ thương hiệu con; xác minh endpoint/UGC/ủy quyền và nguồn hiệu lực. Done khi dictionary/codebook có version/hash và log ngày khóa, trước mở nhãn/nội dung tập chính. Nhánh thời gian có quy tắc tri thức as-of riêng.

Tiến độ B ngày 04/10/2026: đã fetch gói C ở `origin/feat/data-pipeline` (commit `c0b9d61`) và rà soát tĩnh; góp ý tại [CODEBOOK_REVIEW_B](annotation_templates/CODEBOOK_REVIEW_B.md). Bản bàn giao vẫn `pending_review`, còn cần xử lý subset tính Kappa, phiên bản codebook, xác nhận pilot và quyết định cửa sổ/quý. Chưa ký duyệt hoặc merge gói C; chưa chạy LABEL-01. Trạng thái C trên nhánh bàn giao là PENDING_REVIEW, chưa coi là nghiệm thu trên nhánh B.

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
- B — họ tên: Phùng Tấn Minh; giờ/tuần: 5–10 giờ.
- C — họ tên: chưa điền; giờ/tuần: chưa điền.
- D — chủ nhiệm/lead + model + API–extension; họ tên chính thức/giờ tuần: chưa điền.
- Owner model: D; C bàn giao dữ liệu, B kiểm tái lập sau khóa nhãn.
- GVHD và thành viên thêm: chưa điền.

## Các vị trí B cần điền và cập nhật

| File/vị trí | Thông tin thuộc B | Trạng thái |
| --- | --- | --- |
| [CURRENT_TASKS](CURRENT_TASKS.md), mục đội nhóm/START-01 | Họ tên, vai trò, giờ mỗi tuần | Đã xác nhận và điền; task chung còn IN_PROGRESS |
| [Đề cương](De_cuong_NCKH_Phishing_Mau_2.md), bảng thành viên | Họ tên, MSSV, lớp, khoa, email, SĐT | Đã điền theo thông tin B cung cấp |
| [Đề cương](De_cuong_NCKH_Phishing_Mau_2.md), mục 6.1 | Kinh nghiệm/kỹ năng và giờ/tuần | Đã điền giờ; kinh nghiệm/kỹ năng chưa cung cấp |
| [TEAM](TEAM.md), vai trò B | Xác nhận người nhận vai trò và ngân sách | Đã điền, tham chiếu hồ sơ ở đề cương |

Các file `configs/*.example.json` là mẫu cấu hình, chưa phải hồ sơ nhóm đã khóa: `B_name` và `annotation_hours_B` sẽ được đối chiếu từ thông tin trên khi nhóm tạo cấu hình thật; không coi giá trị null của mẫu là B chưa xác nhận. Source manifest thuộc C; cấu hình model/demo thuộc D. Các bản `docs/archive/` giữ lịch sử, không điền lại hồ sơ vào bản cũ.

Sau này B ghi nhãn và thời gian pilot khi nhận view mù/codebook từ C (LABEL-01), rồi biên bản bất đồng/đồng thuận và QA/tái lập khi có dữ liệu hoặc run thật. Chưa tạo nhãn, số đo hoặc báo cáo kết quả khi chưa thực hiện.

## Điều kiện trước huấn luyện chính

- [ ] Revision/checksum và quyền nguồn đã ghi.
- [ ] Audit date, cửa sổ, dictionary/codebook khóa.
- [ ] Pilot loại khỏi tập đánh giá; ngân sách giờ và cỡ mẫu chốt.
- [ ] Nhãn tổ chức hoàn chỉnh phần giữ lại, QC/audit và phân xử có log.
- [ ] Groups/splits và các loại trùng đã kiểm; official test không vào phát triển.
- [ ] Preprocessing/features version hóa; pipeline học chỉ fit phần huấn luyện.

## Nhật ký cập nhật

04/10/2026 — DATA-02/LABEL-01: C bàn giao các commits `6817d7e`, `c03306b` và `94b5d62` xử lý dứt điểm L-B01–L-B06, tích hợp đầy đủ provenance (`is_synthetic`, `dataset_id`, `dataset_hash`, `codebook_hash`), cơ chế resume kiểm hash và Kappa ghép cặp theo `sample_id` từ điển. Thành viên B rà soát độc lập và KÝ DUYỆT NGHIỆM THU KỸ THUẬT (Approved for code & manifest) trong [biên bản review B](annotation_templates/CODEBOOK_REVIEW_B.md). Bàn giao view mù cho Lead D kiểm hash, chờ Lead D khóa Codebook/Dictionary để kích hoạt mở gói pilot thật. Chốt chặn huấn luyện mô hình chính tiếp tục được khóa cứng.

04/10/2026 — DATA-02/LABEL-01: nhận thông báo bàn giao của C, fetch và rà codebook/CLI/schema/metadata tại commit `c0b9d61`; lưu [biên bản review B](annotation_templates/CODEBOOK_REVIEW_B.md). Chưa tạo nhãn hay số đo pilot; nhãn độc lập do người gán nhãn thực hiện theo R-A09. Kiểm tra tài liệu bằng `git diff --check`; các JSON metadata đọc được bằng `ConvertFrom-Json`. Góp ý chờ C/D xử lý, chưa chạy tests hoặc tự nghiệm thu công cụ.

04/10/2026 — START-01: B (Phùng Tấn Minh) cung cấp hồ sơ và xác nhận 5–10 giờ/tuần; điền bảng thành viên/mục 6.1 đề cương, CURRENT_TASKS và TEAM. Chuyển START-01 sang IN_PROGRESS vì đã có phần việc thực của B, còn thiếu thông tin/xác nhận nhóm. Rà toàn bộ docs, gồm OpenAPI và archive; dùng đề cương hiện hành làm chuẩn, giữ archive làm lịch sử. Nhánh làm việc: `docs/member-b-start01`, từ commit `0db1868`. Chuẩn hóa cách gọi D thành chủ nhiệm/lead trong hướng dẫn hiện hành để không nhầm với B; sửa liên kết tài liệu trỏ tới máy người soạn. Kiểm tra đạt: `git diff --check`; đọc JSON bằng PowerShell `ConvertFrom-Json` cho OpenAPI và hai cấu hình mẫu; kiểm đường dẫn đích của liên kết Markdown cục bộ bằng `Test-Path` trong docs hiện hành, không có đường dẫn thiếu. Schema/contract không đổi; chưa chạy kiểm thử backend hoặc mô hình.

04/10/2026 — thành viên B xác nhận ngân sách 5–10 giờ/tuần cho đợt gán nhãn. START-01 vẫn TODO vì chưa đủ họ tên/ngân sách giờ và xác nhận của cả nhóm; quy mô mẫu sẽ chốt sau pilot.

03/10/2026 — tạo khung khởi động từ đề cương được duyệt; chưa khởi động pipeline, crawler hoặc mô hình. Đã kiểm liên kết nội bộ, JSON/config, schema refs và 4 ví dụ request/response bằng JSON Schema 2020-12; các request chứa target, thiếu HTML, revision âm hoặc file URL bị schema từ chối. Chưa kiểm toàn bộ OpenAPI meta-schema hoặc backend chạy thật. Cập nhật trạng thái cùng đường dẫn bằng chứng sau mỗi task, không tạo file current task theo ngày.

04/10/2026 — chốt ownership 4 vai trò: A nhãn, B kiểm độc lập/QA, C pipeline dữ liệu/view mù, D người dùng/lead + model + API–extension. Các task triển khai vẫn TODO; chưa huấn luyện hoặc chạy API.

04/10/2026 — đưa phân công TEAM vào mục 6.1, bảng tiến độ mục 8 và bảng thông tin bốn thành viên của đề cương theo yêu cầu. D nhận trực tiếp model/API–extension và lead; họ tên A/B/C và giờ tuần chưa chốt.
