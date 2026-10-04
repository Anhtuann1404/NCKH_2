# Phiếu nhận và bàn giao phần A

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
