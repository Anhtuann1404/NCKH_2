# Phiếu nhận và bàn giao phần A

## Bổ sung cho V2 — chuẩn bị 07/10/2026

Phần A: đã nhập 32/32 mẫu tại `aae91a7`; file `data/annotations/A/labels_v2_pass1.jsonl`, SHA-256 `8da2e16dcd40b280ac0e7c3e4f56ebe74c0ea31f00cb727f2b84dcec65112e4c`. Gói ZIP đã có local; người nhận và thời điểm nhận: **chưa được xác nhận trong hồ sơ này**. Không dùng phiếu này để chứng nhận Kappa, timing hoặc nghiệm thu nhóm.

### Lời xác nhận timing cần Khải điền qua kênh hạn chế

- Có nghỉ/bị gián đoạn khi đồng hồ còn chạy không: **chưa xác nhận**; phạm vi nhớ được: **chưa xác nhận**.
- Có tra cứu ngoài CLI khi đồng hồ chạy không: **chưa xác nhận**; nguồn/phạm vi và cách tính giờ: **chưa xác nhận**.
- Trong lượt V2 có mở lại chat AI hoặc dùng AI hỗ trợ quyết định nhãn không: **chưa xác nhận**.
- Trong lượt V2 có mở/sử dụng kết quả V1 hoặc nhãn B không: **chưa xác nhận**.
- Thời điểm bắt đầu/kết thúc/tiếp tục nhớ được, mẫu bị ảnh hưởng nếu có: **chưa xác nhận**.
- Người xác nhận/ngày: **Khải tự điền**. Không nhớ rõ thì ghi “không chắc”; AI không suy lời xác nhận từ JSONL.

Log CLI ghi 1.666,64 giây toàn lượt A; không coi giá trị này là đã loại giờ nghỉ/được nghiệm thu. Không sửa seconds_spent trong file gốc; ghi bổ sung/đề xuất xử lý trong hồ sơ mới để Lead quyết định.

### Nhận Pass 2 khi được Lead cho phép

1. Nhận xác nhận B đã khóa Pass 1 và lệnh mở phân xử, phạm vi/phiên bản/hash hồ sơ hạn chế; trước đó không mở nhãn B hoặc hồ sơ đối chiếu.
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
