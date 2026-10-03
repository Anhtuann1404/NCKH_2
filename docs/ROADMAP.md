# Roadmap 6–7 tháng

T1 bắt đầu từ ngày nhóm thực sự khởi động, chưa ấn định ngày lịch. Mốc phản ánh điều kiện chuyển bước, không phải phần trăm hoàn thành. Theo đề cương mục 8.

## P0 — Khởi động và khóa kế hoạch dữ liệu: tuần 1–2 T1

Owner: C + D (lead), A/B tham gia pilot.

- Chốt họ tên A/B/C/D, giờ mỗi tuần, môi trường và nơi giữ dữ liệu hạn chế.
- Khóa revision nguồn và checksum tệp, kiểm kê chỉ date trước mở nhãn/nội dung tập chính.
- Xác nhận cửa sổ quý, danh mục tổ chức và codebook từ nguồn ngoài.
- Tạo view gán nhãn mù, đo pilot; loại pilot khỏi test và phát triển mô hình.
- Chốt quy mô 2.000 hoặc 1.200 phishing theo thời gian/giờ thực có; giữ mục tiêu benign tham chiếu 10.000, hard benign 300/100 miền.

**Qua mốc khi:** có manifest, date audit, danh mục/codebook khóa, pilot timing và quyết định cỡ mẫu. Nếu thiếu dữ liệu nội dung, xử lý nguồn trong cùng lõi; ghi tình trạng với giảng viên khi không giải quyết được.

## P1 — Tập chính và nhãn: T1–T2

Owner: A/B/C.

- A gán tổ chức cho toàn bộ phishing giữ lại; B kiểm 30% ngẫu nhiên và ca khó.
- Audit khoảng 200 mẫu nhãn lớp; kiểm hard benign và metadata nguồn/chế độ thu.
- Tính đồng thuận trước phân xử, loại mẫu chưa đủ bằng chứng, lưu quyết định.
- Nhóm miền/trang gần trùng, khóa grouped splits và mốc thời gian.

**Qua mốc khi:** sample index, nhãn độc lập/cuối, QC, coverage, groups/splits và exclusion log có checksum; kiểm tra giao nhau train/validation/test đạt yêu cầu. Official test vẫn được giữ ngoài phát triển.

## P2 — Baseline: T2–T3

Owner: D xây dựng/huấn luyện model; C bàn giao dữ liệu; B kiểm tái lập sau khóa nhãn.

- Hoàn thiện preprocessing/features từ fixture an toàn.
- M0–M2, B-rule, Logistic Regression/TF-IDF và pipeline chọn ngưỡng nội bộ.
- Chạy thử trên tập nhỏ để kiểm pipeline, không dùng kết quả để thay danh mục.

**Qua mốc khi:** cùng mẫu/splits cho các đối chứng; features không dùng metadata nhãn; có run manifest và OOF predictions tái lập được.

## P3 — M3 và kết quả nghiên cứu: T3–T4

Owner: D đánh giá model; B QA/tái lập, A hỗ trợ phân tích nội dung sau khóa nhãn, C kiểm provenance/splits.

- M3, ablation tổ chức/miền/ý định; LightGBM M2/M3 theo ngân sách giống nhau.
- Grouped 5-fold × 3 seed, hai phân tích chính, FPR 1%/5%, CI nhóm.
- Phân tích phụ thời gian, shared hosting, unknown và benign khó.
- Official test riêng khi đủ điều kiện, sau khóa cấu hình.

**Qua mốc khi:** chỉ số + confusion counts + FPR thực đo, paired delta/CI, lỗi/giới hạn và manifest hoàn chỉnh. Không yêu cầu kết quả giả thuyết phải dương.

## P4 — API và extension demo: T4–T5

Owner: D (model + API + extension); B kiểm thử, C hỗ trợ đầu vào/version. Có thể dựng UI/mock API sớm trên fixture, không cần chờ kết quả nghiên cứu để học kỹ thuật.

- Bundle mô hình thật, API theo hợp đồng, extension URL/DOM và cảnh báo.
- Kiểm SPA/chuyển hướng/nội dung trễ, timeout, phản hồi cũ và phân tích không đủ.
- Đo p50/p95 và thành phần độ trễ, ghi môi trường và dữ liệu truyền.

**Qua mốc khi:** demo cài cục bộ chạy lại được, phân biệt mock/real, lỗi không hiện an toàn, số liệu đo có provenance.

## P5 — Hoàn thiện: T6–T7

Owner: cả nhóm + GVHD.

- Báo cáo, code/config, tài liệu dữ liệu được phép, hướng dẫn demo và bảo vệ.
- Chuẩn bị bản thảo bài báo từ kết quả thực có; không là điều kiện nghiệm thu bắt buộc.
- Việt Nam/encoder/ad block chỉ làm khi lõi ổn định; nhánh Việt Nam khóa danh mục riêng và báo cáo riêng.

**Hoàn thành khi:** sản phẩm theo mục 7 đề cương, giới hạn rõ, tài nguyên bàn giao chạy được và phần chia sẻ đúng quyền. Lịch 6 tháng dồn hoàn thiện vào T6, giảm phần tùy chọn.

## Đường phụ thuộc

`date → danh mục/codebook → nhãn/cỡ mẫu → groups/splits → baselines → M3/đánh giá → bundle → demo → báo cáo`.

Công việc có thể làm song song trước khóa dữ liệu: đọc tài liệu, viết fixture sạch, chuẩn bị parser/giao diện mù, học MV3 và mock API. Không dùng nhãn/target tập chính để chọn quý/danh mục.
