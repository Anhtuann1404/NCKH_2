# Bộ tài liệu khởi động dự án

Cập nhật: 05/10/2026. Hướng nghiên cứu đã được giảng viên duyệt theo xác nhận của nhóm. Đây là tài liệu triển khai, không thay thế hoặc sửa phạm vi đề cương.

**Đề tài:** Phát hiện website phishing mạo danh tổ chức bằng học máy kết hợp URL và nội dung trang.

## Bắt đầu cho thành viên nhóm

Clone nhánh tích hợp `develop` của repo:

```sh
git clone --branch develop https://github.com/Anhtuann1404/NCKH_2.git
cd NCKH_2
```

Đọc `docs/TEAM.md` để xác định vai trò, sau đó đọc `docs/CURRENT_TASKS.md` và `docs/DEVELOPMENT.md` để nhận việc và thống nhất cách bàn giao. Điền họ tên và thời gian có thể dành mỗi tuần trước khi chốt người nhận nhiệm vụ. Đã có preprocessing, API–extension mock và mô hình TF-IDF demo, lưu/tải bundle, benchmark và parity trên fixture trong repo cục bộ D; chưa huấn luyện mô hình nghiên cứu. Phần D đã kiểm thử được tích hợp vào `develop`; xem DEVELOPMENT để chạy và tiếp tục review. Main chỉ nhận giai đoạn đã nghiệm thu.

Khi bắt đầu viết mã, tạo nhánh riêng từ `develop` đã cập nhật và gửi pull request đích `develop` để nhóm rà soát trước khi gộp. Khi một giai đoạn ổn định, Lead mở PR `develop` → `main`; không push trực tiếp main. Không commit khóa API, dữ liệu bị hạn chế chia sẻ hoặc HTML thu thập vào repo.

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
- API và stack là thiết kế khởi đầu v0.1; đã có FastAPI/MV3 với mock và backend mô hình học từ fixture. Chưa có backend mô hình nghiên cứu. Ví dụ/score mock và số đo demo không là kết quả nghiên cứu.

## Phạm vi giữ nguyên

Lõi là URL + nội dung + tín hiệu tổ chức–miền–ý định; tập quốc tế chính từ PhreshPhish, ưu tiên tiếng Anh; so sánh M0–M3 và B-rule, kiểm tra rò rỉ, FPR mục tiêu 1%/5%, phân tích phụ theo thời gian. Extension cảnh báo và đo p50/p95 là sản phẩm. Việt Nam là nhánh bổ sung có danh mục riêng khóa trước gán nhãn/đánh giá. Encoder và ad block tùy nguồn lực; số bài báo không là điều kiện hoàn thành.

## Trạng thái và bàn giao hiện hành

Phần D đã tích hợp PR #4/#5/#6/#7 vào develop: model fixture → API → extension, báo cáo thực nghiệm, phân tích lỗi và selected-fit bundle. 77 Python tests, 13 Node tests và 18 selected-fit Chromium checks đạt; người dùng đã kiểm thủ công login/ordinary/lỗi API. Hướng dẫn ở [DEVELOPMENT](DEVELOPMENT.md); Windows chờ B kiểm độc lập.

V1 không dùng Kappa/PLAN-01 do lượt A có AI hỗ trợ chọn nhãn. V2 chờ duyệt; giữ bằng chứng V1, chưa mở gán nhãn V2 hoặc training thật. DATA-03/DEV-01 C được nghiệm thu riêng, không coi tests fixture là bằng chứng nguồn/nhãn thật.

D là lead/owner model/API–extension; A Trần Hồng Khải gán nhãn, B Phùng Tấn Minh kiểm độc lập/QA, C quản lý dữ liệu/view mù. Xem [CURRENT_TASKS](CURRENT_TASKS.md) cho trạng thái có bằng chứng và [checklist nghiệm thu](DATA_PROTOCOL.md#checklist-nghiệm-thu-và-mở-training) trước mọi lần bàn giao. Hướng nghiên cứu và giao thức đã duyệt giữ nguyên.

## Các file cấu hình mẫu

- [project.example.json](../configs/project.example.json): tham số kế hoạch, chưa phải cấu hình đã khóa.
- [source_manifest.example.json](../configs/source_manifest.example.json): biểu mẫu ghi nguồn, quyền và checksum; không coi giá trị trống là đã xác minh.

Đề cương, ghi chú và tài liệu triển khai hiện nằm trong `docs/`; lịch sử nằm trong `docs/archive/`. Giữ một bản đề cương hiện hành, không tạo thêm bản sao.

Hướng dẫn Windows/PowerShell, checklist review demo và checker đầu vào fixture nằm trong [DEVELOPMENT](DEVELOPMENT.md). Research training vẫn bị chặn; Windows cần thành viên kiểm thực tế.
