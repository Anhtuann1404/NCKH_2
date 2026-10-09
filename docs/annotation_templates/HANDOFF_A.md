# Phiếu nhận và bàn giao phần A

## Chuẩn bị calibration mới — 09/10/2026

Nguồn: CURRENT_TASKS/CODEBOOK_V1_1_DRAFT tại nhánh `codex/c-data-recovery`, commit `12e951f`. Chỉ dùng phần này sau lệnh Lead; không áp v1.1 hồi tố cho Pass 1 v1.0. Tài liệu nhóm đã chuyển sang chuẩn bị calibration sau bảng pilot B–E được duyệt; mục chờ mở phân xử V2 bên dưới giữ làm lịch sử.

### Điều kiện trước khi bắt đầu

- Lead xác nhận codebook/dictionary v1.1 đã khóa, đúng version/hash; không chỉ dựa tên file DRAFT hoặc thông báo B QA.
- Nhận cùng gói view mù mới 20–30 mẫu cho A/B, hash byte và manifest, exclusion đã ghi; không dùng lại mẫu V1/V2 hoặc Official Test.
- Có lệnh CLI/commit/output mới do Lead phát; không dùng lệnh V2 cũ hoặc ghi đè JSONL cũ.
- Nếu có bản dịch, nhận bản dịch đã chuẩn bị ngoại tuyến và kiểm provenance/hash; xem song song nguyên văn. Không dịch tương tác bằng AI khi gán.
- A tự xác nhận lịch giờ thực tế; thống nhất cách ghi nghỉ/gián đoạn, đọc codebook, ghi chú và thời gian phân xử riêng.

### Phiếu tự kiểm từng mẫu — A tự điền trong công cụ được duyệt

1. Ghi đúng đoạn văn/form/heading quan sát được; tách quan sát khỏi phỏng đoán hậu quả.
2. Quyết định lớp và tổ chức riêng; ghi quy tắc phù hợp của bản đã khóa. Không lấy tên thương hiệu/HTTPS/hosting/form/giá rẻ một mình làm kết luận.
3. Chỉ `identified` khi có căn cứ danh tính; có tên hợp lệ và `org_evidence` tương ứng. Thiếu căn cứ ghi đúng trạng thái, không để `identified` với `unknown`.
4. Phân biệt tổ chức tự nhận với thương hiệu chỉ nhắc tới, nhà cung cấp SSO hoặc tài khoản hosting; chuẩn hóa bằng dictionary khóa.
5. Snapshot quá thiếu và bằng chứng xung đột là hai tình huống khác; dùng quy trình QC `pending_evidence` đúng bản khóa, không tự tạo lớp thứ tư hoặc ép chọn.
6. Đọc đủ nội dung được cung cấp, đánh dấu ca khó/bản dịch mơ hồ; ghi confidence theo cảm nhận, không coi là xác suất.
7. Không mở nhãn B/chat AI/gợi ý nhãn trong lượt độc lập. Không sửa lượt gốc khi phân xử; lưu sự kiện và giờ phân xử riêng.

Phiếu giải thích trống: `sample_id` — quan sát/trích dẫn — quy tắc — lớp/tổ chức do A tự quyết định — điểm còn thiếu — confidence/ca khó — nguồn tra cứu được phép và thời điểm nếu có. Không điền trước các quyết định bằng AI.

## Bổ sung cho V2 — chuẩn bị 07/10/2026

Phần A: đã nhập 32/32 mẫu tại `aae91a7`; file `data/annotations/A/labels_v2_pass1.jsonl`, SHA-256 `8da2e16dcd40b280ac0e7c3e4f56ebe74c0ea31f00cb727f2b84dcec65112e4c`. Gói ZIP đã có local; người nhận và thời điểm nhận: **chưa được xác nhận trong hồ sơ này**. Không dùng phiếu này để chứng nhận Kappa, timing hoặc nghiệm thu nhóm.

### Lời xác nhận timing cần Khải điền qua kênh hạn chế

- Có nghỉ/bị gián đoạn khi đồng hồ còn chạy không: **chưa xác nhận**; phạm vi nhớ được: **chưa xác nhận**.
- Có tra cứu ngoài CLI khi đồng hồ chạy không: **chưa xác nhận**; nguồn/phạm vi và cách tính giờ: **chưa xác nhận**.
- Trong lượt V2 có mở lại chat AI hoặc dùng AI hỗ trợ quyết định nhãn không: **chưa xác nhận**.
- Trong lượt V2 có mở/sử dụng kết quả V1 hoặc nhãn B không: **chưa xác nhận**.
- Đồng hồ tính đủ thời gian đọc mẫu, xem codebook và ghi chú không: **chưa xác nhận**.
- Có mẫu thao tác quá nhanh do lỗi hiển thị/chưa đọc đủ không: **chưa xác nhận**.
- Thời điểm bắt đầu/kết thúc/tiếp tục nhớ được, mẫu bị ảnh hưởng nếu có: **chưa xác nhận**.
- Người xác nhận/ngày: **Khải tự điền**. Không nhớ rõ thì ghi “không chắc”; AI không suy lời xác nhận từ JSONL.

Log CLI ghi 1.666,64 giây toàn lượt A; không coi giá trị này là đã loại giờ nghỉ/được nghiệm thu. Không sửa seconds_spent trong file gốc; ghi bổ sung/đề xuất xử lý trong hồ sơ mới để Lead quyết định.

B đã hoàn thành Pass 1 theo thông báo Lead được A chuyển trong chat ngày 07/10/2026. Hiện chưa mở phiên phân xử; không xem nhãn B/hồ sơ bất đồng trước lệnh riêng của Lead.

### Nhận Pass 2 khi được Lead cho phép

1. Nhận lệnh riêng của Lead mở phân xử và xác nhận hồ sơ lượt gốc đã khóa, phạm vi/phiên bản/hash hồ sơ hạn chế; trước đó không mở nhãn B hoặc hồ sơ đối chiếu.
2. Kiểm hash hai lượt gốc và manifest gói dùng chung; không sửa hoặc ghi đè chúng. C/D giữ vai trò tính đồng thuận trước phân xử.
3. Khi phiên phân xử được mở, ghi sự kiện mới: refs lượt A/B gốc, bằng chứng, người tham gia, kết luận nhóm, lý do và phiên bản quy tắc. Không biến đáp án AI thành quyết định con người.
4. Thời gian phân xử đo riêng, không tự cộng vào giờ Pass 1 hoặc cộng trùng. C/Lead khóa kết quả cuối; A kiểm đủ hồ sơ được giao.

Phiếu cũ bên dưới giữ làm biểu mẫu khởi tạo, không phản ánh trạng thái hoàn thành V2 hiện hành.

Biểu mẫu trống, chuẩn bị 04/10/2026. Dùng bản local cho batch thực; không đánh dấu đạt nếu chưa có bằng chứng.

## C → A: điều kiện nhận

- Batch/export ID, checksum và ngày xuất: **chưa nhận**.
- Codebook/dictionary version, checksum, xác nhận khóa: **chưa nhận**.
- Source/date/cửa sổ được C xác nhận: **chưa nhận**.
- Danh sách `sample_id`, số lượng và tiêu chí chọn: **chưa nhận**.
- Nội dung view: chỉ ID–URL–nội dung an toàn; kiểm không có target/label nguồn, matcher/score/prediction/lượt B: **chưa kiểm**.
- Pilot exclusion registry và xác nhận không dùng official test: **chưa nhận**.
- Tiêu chí hard benign/nhãn phụ nếu batch có phần này: **chưa nhận**.
- C giữ sampling membership riêng, đường dẫn manifest hạn chế: **chưa nhận**.
- Góp ý cách ghi hỗ trợ AI và incident handling: **đã đề xuất, chờ C/B rà**; không coi bản đề xuất của A là yêu cầu khóa mới thay giao thức.
- Họ tên A: **Trần Hồng Khải**, người dùng xác nhận 04/10/2026; ngân sách **49 giờ/tuần**; số tuần và lịch khung giờ cụ thể: **chưa chốt**.

Kết luận nhận batch: **chưa đủ đầu vào**. Ghi người xác nhận và thời điểm khi điều kiện thực sự đạt.

## A → B/C: bàn giao sau khóa lượt A

| Sản phẩm | Đường dẫn/version/hash thực | Tình trạng hiện tại |
| --- | --- | --- |
| Lượt A độc lập | `data/annotations/A/annotations.jsonl` | Trống, 0 lượt |
| Log thời gian | `data/annotations/A/timing.jsonl` | Trống, chưa đo |
| Ca khó và yêu cầu nội dung | `data/annotations/A/difficult_cases.jsonl` | Trống, chưa quan sát |
| Sửa đổi và sự cố | `data/annotations/A/revision_events.jsonl` | Trống, chưa phát sinh |
| Phần phương pháp báo cáo | `docs/REPORT_LABELING_A.md` | Bản thảo dự kiến, chưa có số liệu |

Ca khó local ghi ít nhất: `case_id`, `sample_id`, `pass_id`, loại khó, snapshot/evidence refs, câu hỏi cần xử lý, ngày và trạng thái. B cần gán độc lập trước khi xem kết luận/evidence A; C chuyển chỉ ID/view và câu hỏi trung lập phù hợp quy tắc đã khóa.

Revision event ghi: `event_id`, `sample_id`, `previous_pass_id`, `new_pass_id` (nếu có), loại sửa/sự cố, lý do, người/thời điểm, ảnh hưởng blinding. Phân xử có `adjudication_event_id`, refs lượt A/B khóa, người tham gia, nhãn cuối và lý do; do nhóm/C lưu, không ghi đè sổ A.

Checklist khi bàn giao dữ liệu thật:

- [ ] Số ID được giao = số ID hoàn thành + số ID chưa hoàn thành có lý do; counts lấy từ manifest thực.
- [ ] Lượt độc lập A đã khóa có version/hash; không thiếu/trùng ID–pass; sửa đổi giữ lịch sử.
- [ ] Mẫu thiếu bằng chứng/unknown/outside-catalog/multi-target được phân biệt theo codebook khóa.
- [ ] Tên tự do, nhãn chuẩn, evidence và thời gian truy được về snapshot; không có bí mật trong phần chia sẻ.
- [ ] B đã khóa lượt độc lập trước khi xem nhãn/ghi chú A.
- [ ] C tính đồng thuận random trước phân xử; ca khó thêm tách riêng.
- [ ] Nhóm phân xử có lý do/refs; C xuất bộ nhãn cuối có version; A kiểm đủ mọi phishing giữ lại và hard benign được giao.
- [ ] Counts pilot/giờ/độ phủ/giới hạn và disclosure AI trong báo cáo khớp dữ liệu thật.

Người nhận/reviewer và thời điểm: **chưa có**. Checklist này chưa chứng nhận hoàn tất LABEL-01 hoặc khóa nhãn.
