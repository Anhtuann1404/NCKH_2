# Bộ tài liệu khởi động dự án

Cập nhật: 04/10/2026. Hướng nghiên cứu đã được giảng viên duyệt theo xác nhận của nhóm. Đây là tài liệu triển khai, không thay thế hoặc sửa phạm vi đề cương.

**Đề tài:** Phát hiện website phishing mạo danh tổ chức bằng học máy kết hợp URL và nội dung trang.

## Bắt đầu cho thành viên nhóm

Clone nhánh `main` của repo:

```sh
git clone --branch main https://github.com/Anhtuann1404/NCKH_2.git
cd NCKH_2
```

Đọc `docs/TEAM.md` để xác định vai trò, sau đó đọc `docs/CURRENT_TASKS.md` và `docs/DEVELOPMENT.md` để nhận việc và thống nhất cách bàn giao. Thành viên A — Trần Hồng Khải bắt đầu từ [hồ sơ MEMBER_A](MEMBER_A.md). Điền họ tên và thời gian có thể dành mỗi tuần trước khi chốt người nhận nhiệm vụ. Tài liệu hiện là khung triển khai; mô hình, API và extension chưa được xây dựng.

Khi bắt đầu viết mã, tạo nhánh riêng từ `main` đã cập nhật và gửi pull request để nhóm rà soát trước khi gộp. Không commit khóa API, dữ liệu bị hạn chế chia sẻ hoặc HTML thu thập vào repo.

## Đọc theo thứ tự

0. [TEAM](TEAM.md): phân công 4 người, trách nhiệm và sản phẩm từng owner.
1. [CURRENT_TASKS](CURRENT_TASKS.md): việc cần làm ngay, người phụ trách và điều kiện hoàn thành.
2. [ROADMAP](ROADMAP.md): các giai đoạn trong 6–7 tháng, phụ thuộc và sản phẩm từng mốc.
3. [TECH_SPEC](TECH_SPEC.md): kiến trúc, stack đề xuất, ranh giới module và quyết định kỹ thuật.
4. [DATA_PROTOCOL](DATA_PROTOCOL.md): nguồn, gán nhãn mù, danh mục và phiên bản dữ liệu.
5. [EXPERIMENT_PROTOCOL](EXPERIMENT_PROTOCOL.md): M0–M3/B-rule, chia tập, ngưỡng và cách lưu kết quả.
6. [API_SPEC](API_SPEC.md): hợp đồng extension–API; [openapi.json](openapi.json) là bản máy đọc được.
7. [DEVELOPMENT](DEVELOPMENT.md): cách làm việc, kiểm tra, cập nhật trạng thái và bàn giao.

## Nguồn quyết định

- [Đề cương được dùng làm chuẩn](De_cuong_NCKH_Phishing_Mau_2.md).
- [Ghi chú và lịch sử xác minh](Ghi_chu_nghien_cuu.md).
- Đề cương quyết định mục tiêu, phạm vi và giao thức nghiên cứu. Tài liệu này cụ thể hóa triển khai; khi phát hiện mâu thuẫn, ghi lại và xử lý trước bước phụ thuộc, không âm thầm đổi lõi.
- API và stack là thiết kế khởi đầu v0.1, chưa có backend/extension chạy được. Ví dụ API là dữ liệu mô phỏng, không phải kết quả mô hình.

## Phạm vi giữ nguyên

Lõi là URL + nội dung + tín hiệu tổ chức–miền–ý định; tập quốc tế chính từ PhreshPhish, ưu tiên tiếng Anh; so sánh M0–M3 và B-rule, kiểm tra rò rỉ, FPR mục tiêu 1%/5%, phân tích phụ theo thời gian. Extension cảnh báo và đo p50/p95 là sản phẩm. Việt Nam là nhánh bổ sung có danh mục riêng khóa trước gán nhãn/đánh giá. Encoder và ad block tùy nguồn lực; số bài báo không là điều kiện hoàn thành.

## Trạng thái ban đầu

Đã có đề cương, ghi chú, kiểm kê URL PhishVN và thử tải 20 dòng PhreshPhish. Đã xác nhận nhóm từ 4 người trở lên. Chưa kiểm kê date toàn revision, chưa khóa tập thực nghiệm/danh mục cuối, chưa đo pilot nhãn, chưa huấn luyện, chưa có API hoặc extension.

Vai trò A gán nhãn, B kiểm độc lập và QA, C quản lý dữ liệu/giao diện mù. D là lead, owner xây dựng–huấn luyện–đánh giá model và API–extension. A/B/C phải là ba người khác nhau; A đã xác nhận tên Trần Hồng Khải và 49 giờ/tuần; họ tên B/C và ngân sách giờ nhóm chưa chốt. B hỗ trợ tái lập sau khóa nhãn, C bàn giao pipeline dữ liệu; D chịu trách nhiệm model. Chi tiết ở TEAM.

## Các file cấu hình mẫu

- [project.example.json](../configs/project.example.json): tham số kế hoạch, chưa phải cấu hình đã khóa.
- [source_manifest.example.json](../configs/source_manifest.example.json): biểu mẫu ghi nguồn, quyền và checksum; không coi giá trị trống là đã xác minh.

Đề cương, ghi chú và tài liệu triển khai hiện nằm trong `docs/`; lịch sử nằm trong `docs/archive/`. Giữ một bản đề cương hiện hành, không tạo thêm bản sao.
