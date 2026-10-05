# Kiểm tra bàn giao của C cho A

## Trạng thái hiện hành — 05/10/2026

Đã fetch `feat/data-pipeline`, HEAD `edc88877a9d866896fc6afdaca5996a83b75dc77`. Thông báo C mở pilot tại 3a8528a đã bị Lead yêu cầu thu hồi; manifest mới nhất ghi B `approved`, D `pending`, `ready_for_annotation=false`. A chưa bắt đầu và chưa có nhãn/thời gian thật. Không dùng tuyên bố mở pilot cũ làm lệnh bắt đầu.

- Codebook/dictionary: `1.0.0-pending_review`, chưa khóa; hash byte tệp khớp manifest.
- Codebook SHA-256: `fc89f7704fd8fcc2ebe26f135a780dcd2d5464958150abe9b5888aeeecd92c2e`.
- Dictionary SHA-256: `a7403a79531b0e5f13884fa4e4d431876f34e3277a3112577a3ff2275703ff2d`.
- Manifest REAL-PILOT-32-V1 ghi 32 mẫu, view hash `08dc47c45e7ff254389ac46b1068d505bea13ed4f05f56cf5416a5c516a78176`. Đây là hash **được khai báo**, chưa xác minh file nhận trên máy A; file view không tracked trên nhánh nên pull không đủ bàn giao.
- Snapshot công cụ mới ở `tmp/c-pilot-edc8887/`; CLI `--help` chạy được, có `--manifest`. Không copy/view nội dung real32. Kiểm help không thay nghiệm thu end-to-end trên gói đã khóa.
- L-B01–L-B06 đã có bản sửa; nghiệm thu cuối theo kết luận Lead. Các phát hiện lỗi CLI/Kappa bên dưới là lịch sử của ccdfdbb; không suy rằng toàn bộ công cụ đã được duyệt từ việc có bản sửa.
- Đã có 20 dry-run kỹ thuật và 20 nhãn AI tham khảo trên synthetic, lưu riêng local; chưa có lượt người A. Mọi nhãn AI bị loại khỏi kappa mặc định, không dùng cho PLAN-01 hoặc nghiên cứu.

Bằng chứng local: `data/annotations/A/real_pilot_handoff_status.json`, `latest_cli_environment_check.json`, `ai_practice_reference_report.json`. Những tệp này được Git ignore.

Việc còn chờ: C bàn giao file view thực cùng manifest/codebook/dictionary đã khóa nhất quán; B/D nghiệm thu cuối và Lead phát lệnh rõ ràng. Nhận lại phiên bản/hash mới nếu C sửa gói; không dùng hash pending ở trên làm bản khóa. Không gửi nhãn/ghi chú A cho B trước khóa lượt độc lập.

Lead đã rà hồ sơ A tại `868ab91` và ghi nhận phần chuẩn bị đạt; đây không phải phê duyệt mở pilot. A tiếp tục chờ, chưa mở mẫu thật. Khi nhận gói đã nghiệm thu, trước Pass 1 phải kiểm lại hash tệp nhận và ghi commit công cụ, phiên bản/hash gói, codebook, dictionary cùng sampling plan. Không dùng lệnh trong mục lịch sử để chạy phiên mới.

## Nhật ký kiểm tra cũ — ccdfdbb (04/10/2026)

Phần bên dưới giữ làm dấu vết lịch sử; các lệnh/path và nhận định lỗi thuộc snapshot cũ, không dùng để chạy pilot thật hoặc xác định trạng thái hiện hành.

Ngày 04/10/2026. A: Trần Hồng Khải, ngân sách 49 giờ/tuần. Kiểm nhánh `origin/feat/data-pipeline` tại commit `ccdfdbbc38422e804abfd2b44cdcc472155606c6`; không merge hoặc đổi `main`. Đây là kiểm tra kỹ thuật do Codex hỗ trợ, không phải lượt nhãn người A hoặc review độc lập của B.

## Kết quả kiểm được

| Mục | Bằng chứng từ snapshot | Kết luận |
| --- | --- | --- |
| Gói mù | `dataset_id=SYNTHETIC-PILOT-PRACTICE-V1`, `dataset_type=synthetic_practice_pilot`, `is_synthetic=true` | 20 mẫu mô phỏng để tập dượt, chưa phải pilot thực đo giờ cho PLAN-01 |
| Quy định sử dụng giờ | Metadata purpose ghi không dùng số liệu bấm giờ tập này ước lượng công sức thực | Giờ thực trên tập mô phỏng cũng không thay pilot dữ liệu thật |
| Codebook/dictionary | `pending_review`, `1.0.0-pending_review` | Chưa khóa chính thức, còn chờ B rà |
| Hash dictionary | `61acff28ad48322ff7d4fc1ff5ef4a1a440cee70651192c0999bac94fea36d28` | Hash byte tệp khớp hash ghi trong codebook |
| Hash gói mù | `aa1d923ffd4d043e34968568ddebdb0d198513d356380f4e63dc133c79fc860a` | Ghi dấu vết snapshot đã kiểm |
| Mẫu/ID | 20 mẫu, 20 ID khác nhau; validator `assert_no_label_leak` chạy qua | Đạt kiểm cấu trúc/allowlist; chưa chứng nhận mọi nội dung không lộ ngữ nghĩa hay toàn bộ quy trình thu an toàn |
| Version trên mẫu | Mọi mẫu ghi `1.0.0` | Không khớp trạng thái phiên bản codebook `1.0.0-pending_review`; cần C đồng bộ trước lượt thật |
| CLI | `--help` và `--dry-run` chạy thành công | Sẵn sàng kiểm thao tác kỹ thuật; dry-run không phải lượt người |
| Đầu ra kiểm | 20 bản ghi `annotator_id=simulated_A`, `is_dry_run=true`, nằm riêng trong `tmp/` | Không tạo `pilot_pass1.jsonl` của A, không đo giờ người |

Codebook mục R-A09 ghi: “100% lượt gán nhãn độc lập phải do con người thực hiện, không dùng AI hỗ trợ”. Vì vậy Codex chỉ kiểm công cụ/cấu trúc và chuẩn bị lệnh, không đưa đáp án mẫu hoặc nhập thay người vào lượt độc lập.

## Các điểm C cần xác nhận hoặc sửa trước pilot thực

1. **Phân biệt thực hành và pilot thực.** Nhãn/timing trên 20 mẫu mô phỏng chỉ phục vụ làm quen. Theo DATA_PROTOCOL hiện tại, pilot thực dự kiến 20 mẫu kỹ thuật + 12 phishing bổ sung để có 20 phishing; chưa thấy gói bàn giao đáp ứng phần dữ liệu thật đó. C quản lý membership riêng và không làm lộ lớp nguồn cho A/B.
2. **Khóa và đồng bộ phiên bản.** B rà xong trước khi C ghi phiên bản/hash khóa; version codebook trong từng mẫu/CLI phải trùng bản thực dùng. `--codebook-version` chỉ ghi dấu vết bản nháp khi tập dượt, không biến bản nháp thành đã khóa.
3. **Exclusion chưa giải quyết toàn bộ.** Registry trên nhánh C ghi `in_progress_unresolved`, pilot gốc là `unresolved_source_mapping`; cần xác nhận mapping/ID/hash/nhóm của pilot thật và loại khỏi đánh giá. Không coi registry tồn tại là đã hoàn tất exclusion.
4. **Kappa phải rõ loại nhãn và subset.** Hàm `compute_cohens_kappa` hiện trích `class_label` từ record, chưa tính trực tiếp nhãn tổ chức chính. Nó bỏ mọi cặp có `is_difficult=true` khi tham số này được truyền. DATA_PROTOCOL yêu cầu giữ ca khó vốn nằm trong random; chỉ tách ca khó thêm. C/B cần chuẩn bị đúng đầu vào tổ chức và random membership, không truyền cờ ca khó để loại cả mẫu random.
5. **Không mặc định 20 mẫu là subset random 30%.** Gói thực hành hiện có `random_subset=true` ở cả 20 mẫu. Có thể kiểm thao tác trên toàn bộ tập mô phỏng, nhưng không gọi đó là kiểm chứng 30% của tập thực hoặc kappa nhãn thật.

Các điểm này là phản hồi kiểm kỹ thuật, chưa gửi cho C/B trong phiên này. Không sửa codebook hoặc code C trực tiếp để tránh đổi hợp đồng của nhóm trong lượt A.

## Tập dượt trên bản công cụ đã chuẩn bị riêng

Snapshot local nằm trong `tmp/c-pilot-ccdfdbb/`, được Git ignore; gồm đúng CLI, module cần import, codebook/dictionary và gói thực hành từ commit đã ghi. Không cần chuyển nhánh hoặc sửa `main`.

Đọc bản codebook trước khi chạy. Từ terminal tại thư mục dự án:

```powershell
python tmp/c-pilot-ccdfdbb/scripts/annotate_cli.py --annotator A --input tmp/c-pilot-ccdfdbb/data/annotations/blind_view_pilot.json --output data/annotations/A/practice_pass1.jsonl --codebook-version 1.0.0-pending_review
```

Đây là lệnh **A tự nhập để thực hành**. Không đặt tên đầu ra là `pilot_pass1.jsonl`, không dùng giờ/kappa thực hành chốt PLAN-01. Đầu ra tương tác của CLI vẫn có `is_dry_run=false` dù đầu vào mô phỏng, nên phải giữ tệp thực hành riêng và kèm dataset provenance khi bàn giao; không ghép vào nhãn thật.

CLI hiện chỉ lấy giờ từ lúc hiện mẫu tới hết nhập, không tách pha/loại thời gian nghỉ. Khi cần nghỉ, dừng phiên và ghi trường hợp ảnh hưởng thời gian; chạy lại cùng lệnh để tiếp tục mẫu đã lưu. Với văn bản dài dùng `v` để xem toàn bộ: tùy chọn `m` hiện chỉ hiện đoạn 600–1.200 lặp lại, chưa tiến trang tiếp theo. Không dùng mặc định evidence chung thay cho bằng chứng cụ thể của người đọc.

## Dấu vết local

- `tmp/c-pilot-ccdfdbb/review_checks.json`: hash, metadata, kết quả kiểm kỹ thuật.
- `tmp/c-pilot-ccdfdbb/checks/cli.dryrun.jsonl`: 20 bản ghi mô phỏng tự động, giờ 0,5 giây hardcode của dry-run, không phải phép đo.
- Lượt người A thật: **0**, thời gian pilot người: **chưa đo**.

Chưa chạy phiên nhập thực hành tương tác thay A. Khi C bàn giao gói thực và bản khóa phù hợp, cập nhật phiếu nhận và dùng output riêng cho pilot thật.
