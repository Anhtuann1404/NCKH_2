# Current tasks

## Cập nhật A — 06/10/2026

- DONE — cập nhật hồ sơ A theo manifest C tại `d8020f4`: V1 invalidated, không dùng Kappa/PLAN-01; giữ 32 nhãn gốc và log để audit. Hash file A được kiểm lại trước cập nhật, không sửa nhãn.
- BLOCKED — A-PILOT V2: manifest `configs/pilot_manifest_v2.json` còn B/D pending và ready_for_annotation=false; chờ bàn giao/khóa và lệnh Lead, chưa mở mẫu mới.
- DONE phần rà câu chữ tĩnh — UI fixture của D tại develop `e175562`: phản hồi về checkbox consent và giới hạn tín hiệu ở [MEMBER_A](MEMBER_A.md). Chưa thử UI trực tiếp; không gọi là nghiệm thu chức năng.
- A-REPORT còn IN_PROGRESS: phương pháp đã soạn, phần kết quả phải chờ pilot hợp lệ. V1 chỉ là bằng chứng sự cố, không thay pilot hợp lệ.

Các bảng/trạng thái bên dưới là lịch sử khởi động và ngày 05/10; không dùng để mở lại V1 hoặc suy V2 đã duyệt.

Cập nhật phần A ngày 05/10/2026. Sprint khởi động dài hai tuần tính từ ngày nhóm bắt đầu; chưa có ngày bắt đầu chính thức. Các trạng thái công việc C/D bên dưới là khung khởi động; không dùng để suy rằng công việc trên nhánh C chưa triển khai. Trạng thái bàn giao A mới nhất nằm trong mục phần việc A và nhật ký.

## Trạng thái có bằng chứng

- DONE — hướng đề cương được GVHD duyệt: theo xác nhận người dùng.
- DONE — nhóm từ 4 người trở lên: theo xác nhận người dùng, chưa điền tên/ngân sách giờ.
- DONE — kiểm kê URL PhishVN: [kết quả](../data/source_audit/PhishVN_kiem_ke.json), [script](../data/source_audit/kiem_ke_phishvn.py).
- DONE — thử kỹ thuật 20 PhreshPhish: [summary](../data/source_audit/phreshphish/pilot_summary.json). Không phải tập thực nghiệm đã xác minh.
- DONE — bộ tài liệu khởi động và hợp đồng API v0.1.
- DONE — D là lead, nhận model và API–extension theo xác nhận trước; phân công owner A/B/C/D ở [TEAM](TEAM.md). A là Trần Hồng Khải theo xác nhận 04/10/2026; B/C chưa có họ tên.
- DONE — A-PREP: hồ sơ làm việc, biểu mẫu và bản thảo phương pháp của A ở [MEMBER_A](MEMBER_A.md). Chưa có nhãn mẫu thật hoặc giờ pilot.
- TODO — date toàn nguồn, freeze danh mục/codebook, pilot nhãn, dữ liệu chính, mô hình, API và extension.

`TODO` chưa làm; `IN_PROGRESS` đang có công việc thực; `BLOCKED` có phụ thuộc cụ thể; `DONE` có sản phẩm kiểm tra được. Không đánh dấu DONE chỉ vì đã có mô tả.

## Việc tiếp theo theo thứ tự

### START-01 — Chốt người và ngân sách giờ

Status: IN_PROGRESS. Owner: D — lead. Phụ thuộc: không. A đã xác nhận họ tên Trần Hồng Khải và 49 giờ/tuần; số tuần thực có của A, người/giờ B/C/D và nơi giữ dữ liệu chưa đủ để nghiệm thu.

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

## Phần việc A — Trần Hồng Khải

Các mục dưới cụ thể hóa nhiệm vụ nhãn của A; không đổi trạng thái DONE của DATA-02/LABEL-01 khi mới có biểu mẫu. Chi tiết và điều kiện nghiệm thu tại [MEMBER_A](MEMBER_A.md).

| Task | Status | Sản phẩm/bằng chứng và phụ thuộc |
| --- | --- | --- |
| A-PREP — chuẩn bị hồ sơ | DONE | Quy trình A, biểu mẫu annotation/time, phiếu bàn giao; JSON đọc được, liên kết kiểm tra được |
| A-RULE — rà codebook cho DATA-02 | IN_PROGRESS | [Góp ý cụ thể cho 9 điểm](annotation_templates/CODEBOOK_REVIEW_A.md); chờ A/B/C rà và C khóa version/hash |
| A-PILOT — lượt A của LABEL-01 | BLOCKED | Manifest C tại edc8887: B approved, D pending, ready_for_annotation=false; chờ Lead phát lệnh và nhận file view có hash khớp; 0 lượt thật, chưa đo giờ |
| A-LABEL — toàn bộ phishing giữ lại | BLOCKED | Chờ pilot, quy mô/sampling plan và view chính; không dùng source target để gán |
| A-BENIGN — kiểm hard benign | BLOCKED | Chờ tiêu chí/danh sách/view được chọn từ C |
| A-RESOLVE — phân xử và kiểm đầy đủ nhãn cuối | BLOCKED | Chờ lượt độc lập B, đồng thuận random trước phân xử và quyết định nhóm |
| A-REPORT — phần phương pháp/kết quả nhãn | IN_PROGRESS | [Phương pháp dự kiến đã viết](REPORT_LABELING_A.md); số liệu kết quả chờ dữ liệu thật |

Hồ sơ local `data/annotations/A/` có sổ nhãn thật trống, trạng thái và đầu ra tập dượt, được Git ignore. Hỗ trợ AI gồm rà tài liệu/soạn hồ sơ, dry-run kỹ thuật và 20 nhãn AI tham khảo trên tập mô phỏng; không tính là annotation độc lập hoặc giờ người pilot.

Phần A làm được trước bàn giao đã chuẩn bị thêm: [6 bài tập mô phỏng có giải thích](annotation_templates/PRACTICE_A.md), [tin nhắn đề nghị C bàn giao](annotation_templates/REQUEST_PILOT_C.md) (người dùng xác nhận đã gửi cho C) và [bảng ước lượng giờ theo giả định đề cương](annotation_templates/TIME_PLAN_A.md). Ngân sách A đã xác nhận 49 giờ/tuần. [Kiểm bàn giao mới nhất](PILOT_HANDOFF_REVIEW_A.md) tại edc8887 xác nhận real32 chưa mở; CLI mới đã chạy help trong snapshot riêng, chưa đọc/gán mẫu thật. Lượt A-PILOT vẫn BLOCKED.

## Đội nhóm cần điền

- A — họ tên: Trần Hồng Khải (người dùng xác nhận 04/10/2026); giờ/tuần: 49; số tuần thực có chưa chốt.
- B — họ tên: chưa điền; giờ/tuần: chưa điền.
- C — họ tên: chưa điền; giờ/tuần: chưa điền.
- D — lead + model + API–extension; họ tên chính thức/giờ tuần: chưa điền. Người dùng phiên hiện tại là A, không đổi vai trò D.
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

05/10/2026 — rà lại phần việc A và fetch nhánh C tại edc8887. Lead chưa duyệt, manifest đã trả D=pending và ready_for_annotation=false; hash codebook/dictionary khớp, view real32 không tracked trên Git. Chuẩn bị snapshot CLI mới và kiểm --help/--manifest; không mở mẫu thật. Cập nhật hồ sơ, phương pháp/disclosure AI và hướng dẫn nhận gói. Đã có riêng 20 nhãn AI tham khảo trên synthetic, kiểm schema/trích dẫn và loại khỏi kappa mặc định; 0 nhãn thật, chưa đo giờ người. Các cập nhật hồ sơ được lưu trên nhánh codex/member-a-preparation, không merge main.

03/10/2026 — tạo khung khởi động từ đề cương được duyệt; chưa khởi động pipeline, crawler hoặc mô hình. Đã kiểm liên kết nội bộ, JSON/config, schema refs và 4 ví dụ request/response bằng JSON Schema 2020-12; các request chứa target, thiếu HTML, revision âm hoặc file URL bị schema từ chối. Chưa kiểm toàn bộ OpenAPI meta-schema hoặc backend chạy thật. Cập nhật trạng thái cùng đường dẫn bằng chứng sau mỗi task, không tạo file current task theo ngày.

04/10/2026 — chốt ownership 4 vai trò: A nhãn, B kiểm độc lập/QA, C pipeline dữ liệu/view mù, D người dùng/lead + model + API–extension. Các task triển khai vẫn TODO; chưa huấn luyện hoặc chạy API.

04/10/2026 — đưa phân công TEAM vào mục 6.1, bảng tiến độ mục 8 và bảng thông tin bốn thành viên của đề cương theo yêu cầu. D nhận trực tiếp model/API–extension và lead; họ tên A/B/C và giờ tuần chưa chốt.

04/10/2026 — người dùng phiên hiện tại xác nhận là A, tên Trần Hồng Khải, giờ/tuần chưa xác nhận. Hoàn thành A-PREP: quy trình, biểu mẫu JSON, phiếu bàn giao và bản thảo phương pháp; khởi tạo sổ A local trống. A-RULE/A-REPORT còn chờ rà và số liệu; lượt nhãn thật chờ C bàn giao codebook khóa/view mù. Không đọc raw pilot có target/label, không tạo nhãn hoặc thời gian giả và không đổi nhiệm vụ D. Kiểm JSON, liên kết mới, Git ignore và whitespace; chưa có kiểm chứng nhãn/đồng thuận từ A/B.

04/10/2026 — theo yêu cầu làm tiếp của A, bổ sung phương án cụ thể R-A01–R-A09, 6 tình huống mô phỏng có cách ghi, bản đề nghị bàn giao pilot cho C chưa gửi và bảng giờ 1.200/2.000 mẫu theo giả định 3–5 phút. Không thay codebook chính thức, không ghi bài tập thành nhãn thật hoặc đo thời gian thay người dùng.

04/10/2026 — A xác nhận đã gửi đề nghị cho C và có ngân sách 49 giờ/tuần. Cập nhật hồ sơ hiện hành và trạng thái local; ngân sách điều kiện cho 6/7/8 tuần lần lượt 294/343/392 giờ, số tuần cụ thể chưa chốt. START-01 vẫn IN_PROGRESS, PLAN-01 chưa chốt: cần ngân sách B và pilot thực; gói C chưa được bàn giao trong phiên này. Lượt nhãn và thời gian pilot vẫn chưa có.

04/10/2026 — nhận thông báo bàn giao từ C; fetch feat/data-pipeline và kiểm snapshot ccdfdbb trong tmp, không merge main. Validator cấu trúc, ID độc nhất, hash dictionary và CLI help/dry-run đạt; 20 dry-run chỉ simulated_A, tách khỏi lượt người. Metadata xác nhận gói synthetic_practice_pilot, codebook pending_review, version mẫu chưa đồng bộ; ghi phản hồi exclusion/Kappa và lệnh tập dượt tại PILOT_HANDOFF_REVIEW_A. Chưa có nhãn người A hoặc pilot công sức thật; chưa gửi phản hồi này cho C.
