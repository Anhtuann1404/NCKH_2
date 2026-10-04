# Rà soát bàn giao cho B — DATA-02 / LABEL-01

Ngày: 04/10/2026. Người nhận: Phùng Tấn Minh. Đây là rà soát kỹ thuật/tài liệu có AI hỗ trợ, chưa phải lượt gán nhãn độc lập hoặc chữ ký duyệt của người gán nhãn.

Nguồn đã fetch: `origin/feat/data-pipeline`, commit `c0b9d6156145a582e97d63b631d463ad6ed3b522`. Đọc bằng `git show`; chưa merge nhánh C vào nhánh B, chưa chạy CLI, chưa tạo `pilot_pass1.jsonl`, chưa đọc nhãn A hoặc nhãn nguồn.

## Các điểm cần C/D xử lý trước bàn giao lượt thật

| Mã | Bằng chứng | Yêu cầu |
| --- | --- | --- |
| R-B01 | `CODEBOOK_V1.md` và `dictionary_v1.json` vẫn `pending_review`; CLI ghi cứng `codebook_version = 1.0.0` | Hoàn tất rà soát, xử lý góp ý và D nghiệm thu/khóa version/hash trước lượt thật; bản ghi phải chỉ đúng phiên bản dùng để chấm |
| R-B02 | `compute_cohens_kappa(..., is_difficult=...)` bỏ mọi mẫu có cờ khó; codebook mục 5 cũng chưa phân biệt ca khó ngẫu nhiên với ca khó chuyển thêm | Theo DATA_PROTOCOL, giữ mọi mẫu thuộc subset ngẫu nhiên, kể cả ca khó; chỉ loại ca khó chuyển thêm. CLI đang ghi cứng `random_subset = True` nên cần lấy membership từ kế hoạch lấy mẫu, không từ lựa chọn của người chấm |
| R-B03 | Gói mù có 20 mẫu; protocol yêu cầu 20 mẫu kỹ thuật (8 phishing/12 benign) cộng 12 phishing ngoài đánh giá để đo 20 phishing | C xác nhận nguồn và tính đầy đủ của pilot qua manifest riêng không lộ nhãn cho A/B. Nếu gói hiện chỉ dùng tập thao tác thì ghi rõ; chưa dùng thời gian của gói đó để khẳng định đã đo đủ pilot nghiên cứu |
| R-B04 | Codebook giữ danh mục Q4/2024–Q4/2025 trong khi audit train kết thúc 08/09/2025 | C/D ghi quyết định cửa sổ/quý theo quy tắc điều chỉnh một lần của đề cương trước khóa; lưu căn cứ nếu giữ danh mục cũ. Ghi chú temporal as-of chưa thay quyết định danh mục của phân tích chính |

Codebook còn dẫn `docs/annotation_templates/CODEBOOK_REVIEW_A.md`, nhưng tệp này không có trong cây Git của commit được bàn giao; cần bổ sung hoặc trỏ đúng phiên bản để kiểm chứng 9 góp ý đã tiếp thu.

## Kiểm tra đã làm và giới hạn

- `git fetch origin feat/data-pipeline` thành công; xác định commit bằng `git rev-parse`.
- Đọc metadata JSON bằng PowerShell `ConvertFrom-Json`: `total_samples = 20`, mảng `samples` có 20 phần tử; các trường mẫu là `page_text`, `sample_id`, `structure_summary`, `url`.
- Rà mã CLI: dùng input bàn phím và append JSONL; có resume, không có lệnh fetch mạng/render HTML trong script. Không chạy chế độ `--dry-run` trên output gán nhãn thật vì chế độ này sinh nhãn tự động.
- Chưa chạy unit tests hoặc chứng nhận toàn bộ sanitizer. Kiểm tra khóa JSON không chứng minh không có gợi ý trong nội dung; chưa chứng nhận provenance/thành phần lớp của pilot.

## Bước tiếp theo

C xử lý/bàn giao bản đã khóa; D nghiệm thu và đưa thay đổi vào nhánh tích hợp. Workflow mới trong `rules.md` dùng base PR `develop`, khác hướng dẫn `main` ban đầu; cần đồng bộ nhánh tích hợp thực tế trước merge. Sau khi nhận gói hợp lệ, người gán nhãn tự chạy CLI và nhập đánh giá/thời gian thực theo codebook. Quy tắc R-A09 yêu cầu human-only: AI hỗ trợ chuẩn bị/QA công cụ, không đề xuất nhãn từng mẫu hoặc chấm thay.
