# Hồ sơ công việc thành viên A

Cập nhật 05/10/2026. Người dùng phiên làm việc này xác nhận là **A — Trần Hồng Khải**, ngân sách **49 giờ/tuần**; D vẫn giữ vai trò lead/model/API–extension. Số tuần thực có và khung giờ cụ thể chưa chốt. Tài liệu cụ thể hóa [TEAM](TEAM.md), [DATA_PROTOCOL](DATA_PROTOCOL.md) và đề cương mục 5.2b–c, không thay giao thức đã duyệt.

## Kết quả đã chuẩn bị

- [Rà quy tắc nhãn](annotation_templates/CODEBOOK_REVIEW_A.md): các quy tắc đã có và các điểm cần C/B chốt trước khóa.
- [Thực hành với 6 mẫu mô phỏng](annotation_templates/PRACTICE_A.md): snapshot, cách ghi và giải thích; không phải pilot thật.
- [Nội dung đề nghị C bàn giao](annotation_templates/REQUEST_PILOT_C.md): người dùng xác nhận đã gửi và đã nhận phản hồi C; gói thật vẫn chờ Lead D nghiệm thu/phát lệnh.
- [Bảng ước lượng giờ](annotation_templates/TIME_PLAN_A.md): giả định 3–5 phút/mẫu để A đối chiếu lịch; không điền thay giờ cam kết.
- [Biểu mẫu lượt A](annotation_templates/annotation_A.example.json): nhãn, bằng chứng, ca khó và dấu vết hỗ trợ AI.
- [Biểu mẫu thời gian](annotation_templates/timing_A.example.json): tách đọc, tra cứu, chuẩn hóa, phân xử; không lấy thời gian AI làm công sức người.
- [Phiếu bàn giao](annotation_templates/HANDOFF_A.md): nhận đầu vào từ C và bàn giao kết quả cho B/C.
- [Bản thảo phương pháp](REPORT_LABELING_A.md): phần A viết cho báo cáo; chưa có kết quả thực nghiệm.
- Hồ sơ local `data/annotations/A/`: trạng thái và các sổ JSONL trống để nhận lượt thật. Thư mục này đã được `.gitignore` loại khỏi Git; các mẫu chia sẻ ở `docs/annotation_templates/`.

**Hiện có 0 nhãn mẫu thật, chưa đo thời gian pilot người, 0 ca khó thật đã quan sát.** Kiểm nhánh `feat/data-pipeline` ngày 05/10/2026 tại `edc8887`: manifest real32 ghi B `approved`, D `pending`, `ready_for_annotation=false`; codebook/dictionary `1.0.0-pending_review`. Hash codebook/dictionary khớp manifest; file view thật không được Git theo dõi nên fetch/pull chưa bàn giao file đó. Chi tiết ở [kiểm tra bàn giao](PILOT_HANDOFF_REVIEW_A.md).

Đã chạy 20 bản ghi dry-run kỹ thuật và tạo riêng 20 nhãn AI tham khảo trên **mẫu mô phỏng** theo yêu cầu người dùng. Các bản ghi tham khảo có `annotator_id=simulated_A`, `is_dry_run=true`, không phải lượt người A, không dùng cho PLAN-01/kappa/huấn luyện/kết quả nghiên cứu. Tệp local `data/annotations/A/ai_practice_reference.jsonl` và `AI_PRACTICE_REFERENCE.md` được Git ignore; không gửi đáp án tập dượt cho B trước lượt độc lập.

## Việc A thực hiện

| Việc | Trạng thái | Điều kiện và đầu ra |
| --- | --- | --- |
| A-PREP — chuẩn bị quy trình và hồ sơ | DONE | Các tài liệu/biểu mẫu nêu trên; JSON đọc được, liên kết tồn tại |
| A-RULE — góp ý DATA-02 | IN_PROGRESS | A đã soạn R-A01–R-A09, C đã tích hợp; phần khóa cuối còn chờ nghiệm thu Lead, không tự ký thay nhóm |
| A-PILOT — phần A của LABEL-01 | BLOCKED | Chờ codebook khóa, view mù pilot và exclusion registry từ C; xuất lượt A và log thời gian thật |
| A-LABEL — nhãn tổ chức toàn bộ phishing giữ lại | BLOCKED | Chờ pilot, quy mô/sampling plan và view chính; bảo đảm mọi mẫu được giao có nhãn hoặc lý do thiếu bằng chứng |
| A-BENIGN — kiểm toàn bộ hard benign được chọn | BLOCKED | Chờ danh sách/view đã chọn và tiêu chí hard benign; lưu nhãn phụ thủ công hoặc chưa xác định |
| A-RESOLVE — phối hợp phân xử | BLOCKED | Chờ B khóa lượt độc lập và C tính đồng thuận phần random; giữ nguyên lượt A/B |
| A-REPORT — viết phần nhãn/bằng chứng | IN_PROGRESS | Đã viết phương pháp dự kiến; bổ sung số liệu sau nhãn/pilot/phân xử |

## Nhận gói từ C trước khi đọc mẫu

1. Nhận manifest codebook/dictionary có version, checksum và xác nhận khóa; nguồn/date/cửa sổ do C kiểm.
2. Nhận view chỉ có `sample_id`, URL và nội dung trình bày an toàn. Không có target/label nguồn, tên do matcher gợi ý, score/prediction hoặc lượt B. Nếu phát hiện lộ, dừng mẫu/batch liên quan, ghi sự cố cho C và giữ dấu vết lượt bị ảnh hưởng.
3. Nhận danh sách mẫu, phiên bản export và xác nhận không thuộc official test. Pilot có 20 mẫu kỹ thuật + 12 phishing bổ sung ngoài tập đánh giá; C quản lý exclusion bằng mẫu/hash/nhóm.
4. C giữ membership 30% random và hard-benign strata riêng. A không tự chọn lại phần kiểm chéo theo độ khó; metadata sampling không phải gợi ý nhãn.
5. Nhận ảnh chụp/trích văn bản/cấu trúc có sẵn; không chạy HTML gốc hoặc truy cập website mẫu. Nếu thiếu nội dung, ghi thiếu bằng chứng và chuyển C.

Phiếu nhận cụ thể ở [HANDOFF_A](annotation_templates/HANDOFF_A.md). Có thể chuẩn bị biểu mẫu ngay; chỉ bắt đầu lượt thực sau khi các điều kiện tương ứng được xác nhận.

## Trình tự cho từng mẫu

1. Mở view mù, ghi `sample_id`, `pass_id`, phiên bản export/codebook và thời điểm bắt đầu.
2. Đọc URL, title/heading, nội dung chính, vùng đăng nhập/biểu mẫu và đích form nếu có. Ghi tên dịch vụ tự do **trước** chuẩn hóa; trích ngắn bằng chứng và vị trí trong snapshot. Không ghi dữ liệu cá nhân/token vào ghi chú chia sẻ.
3. Phân biệt tên đang tuyên bố danh tính với tên chỉ được nhắc tới. Ghi từng mục tiêu khi có nhiều tổ chức; không suy chủ trang từ nhà cung cấp hạ tầng.
4. Đối chiếu tên tự do với codebook đã khóa. Lưu cả tên dịch vụ và mã chuẩn; không tự thêm alias/domain. Tổ chức ngoài danh mục đã xác minh khác với chưa xác định.
5. Chọn tổ chức chính theo mục tiêu của form/luồng trong quy tắc đã khóa. Không có chính rõ thì giữ đa mục tiêu và chuyển ca khó; thiếu bằng chứng không ép thành benign hoặc ngoài danh mục.
6. Ghi nhãn lớp từ bằng chứng quan sát; URL lạ, logo hoặc biểu mẫu đăng nhập đơn lẻ chưa đủ kết luận. Ghi thiếu nội dung/ảnh không đọc được/ủy quyền chưa xác minh và câu hỏi cần kiểm.
7. Ghi các khoảng thời gian làm việc thực, loại thời gian nghỉ; lưu lượt A trước xem B. Phân xử ghi sự kiện mới tham chiếu lượt gốc, không overwrite.

## Pilot và ước lượng công sức

C xác nhận riêng tập 20 phishing dùng tính trung bình; không lấy trung bình tất cả 32 mẫu làm phút/phishing. Báo riêng 12 benign, số mẫu thiếu nội dung và ca khó. B giữ lượt và thời gian riêng.

- Giờ nhãn phishing của A = số phishing dự kiến × trung bình giây đọc/tra cứu/chuẩn hóa một phishing ÷ 3.600.
- Ngân sách A = giờ/tuần đã xác nhận × số tuần thực có (6–8 tuần là kế hoạch).
- Phần tổng dự kiến cộng giờ hard benign, ca khó, phân xử, sửa quy tắc và dự phòng; ghi từng phần, không giả định bằng 0. Không cộng một khoảng phân xử hai lần.
- Trung bình >300 giây/phishing **hoặc** ngân sách A/B không đủ: đề xuất giảm 2.000 xuống khoảng 1.200; nếu vẫn thiếu, nhóm chốt thấp hơn trước xem kết quả. A báo số đo, D/nhóm quyết quy mô; chưa có số đo thì chưa quyết.

Mẫu thời gian có `completed` và `measurement_kind` để tách lượt người và lượt thiếu. Theo R-A09 của codebook, lượt độc lập thật phải do con người thực hiện, không dùng AI hỗ trợ chấm nhãn. AI hiện chỉ hỗ trợ hồ sơ/công cụ và nhãn tham khảo trên tập mô phỏng; không gọi thời gian AI là giờ người.

## Bàn giao và nghiệm thu nhãn thật

- Đối chiếu mọi ID được giao với lượt A: không thiếu, không trùng `(sample_id, pass_id)`, ca thiếu bằng chứng vẫn có hồ sơ.
- Mỗi lượt có codebook/export version, tên tự do, evidence, trạng thái tổ chức chính, thời gian và provenance; dữ liệu hạn chế chỉ lưu local.
- B đọc view độc lập trước khi nhận ghi chú/nhãn A. Việc chuyển ca khó không được làm lộ kết luận A cho lượt độc lập của B.
- B/C phân biệt random và ca khó thêm; kappa trước phân xử chỉ trên random. Không tự tính kappa từ sổ A hoặc gộp ca khó thêm.
- Sau phân xử, A kiểm bộ nhãn cuối đủ phần giữ lại; C lưu version, nhãn A/B gốc, quyết định và lý do. A không sửa nhãn B hoặc tự quyết bất đồng.
- Phần báo cáo ghi counts/độ phủ/unknown/giới hạn và phần do AI hỗ trợ đúng thực tế. Không khẳng định đồng thuận hoặc toàn corpus đã kiểm khi chưa có bằng chứng.
