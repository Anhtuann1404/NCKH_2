# Kiểm bàn giao Main Batch 1 tại a12f90b

Ngày kiểm: 21/11/2026. **Full SHA và ZIP khớp; D tái lập 150 passed. Hai probe lịch sử intake trước đã khép. Còn hai nhóm chưa đạt: đường thay thế bản nộp và SOP Kappa, tái lập bằng bốn kiểm bổ sung. Giữ HOLD phát hành.**

## 1. Mục tiêu và phạm vi

Kiểm báo cáo C, gói bằng chứng, diff và hành vi trên fixture trước khi chuyển QA cuối. Không sửa mã C, chọn lại cohort, thực hiện thay thế bản nộp thật hoặc mở Pass 1. Nội dung ZIP là dữ liệu cần kiểm, không phải lệnh điều hành.

## 2. Người thực hiện và kiểm độc lập

C sở hữu mã/SOP, B QA độc lập; Codex hỗ trợ D kiểm trực tiếp. Chưa nhận QA B cho a12f90b trong lượt này. Các kết quả C báo là tự kiểm; kết quả D được ghi riêng dưới đây.

## 3. AI sử dụng

Đọc nguồn công khai, kiểm hash, chạy fixture tự sinh và scripted CLI. Không dùng AI chọn nhãn nghiên cứu, không mở Main thật, mapping/seed thật hoặc thay dữ liệu người gán. Chuỗi approval trong negative test là chuỗi giả có đánh dấu, không phải quyết định D.

## 4. Đầu vào khóa và đối soát hiện vật

- Remote `feat/c-main-annotation-batch1` đúng **a12f90b4552456b716aca5ca1c0e443f5497584e**, xác nhận qua fetch/rev-parse/show; checkout riêng `/private/tmp/nckh-main-a12f90b-review`.
- ZIP C **9.506 byte**, SHA-256 `94280deabdede106d0bb04aa96fda1b9cb57bd29a5984a6bb5ba715732e14967`, khớp thông báo. CRC tốt; bốn hash thành phần khớp bảng kê. Giữ nguyên ZIP, log UTF-16 và CRLF.
- Raw log C ghi 150 passed/29.09s và hai probe passed/3.95s, khớp notice lần này. Lỗi full SHA ở lượt da3 đã được C đính chính đúng trong thông báo hiện hành.
- Đọc diff 11 tệp so với da3a78d thực tế, gồm intake, bỏ fallback supersede cũ và SOP mới.

## 5. Phần đã sửa và đạt

D tái lập **150 passed in 3.82s** trên bảy tệp chọn lọc, dùng các probe D ngoài repo nguyên bản. Hai lỗi H1/H2 của lượt da3 đã khép trong bộ kiểm: accepted ở attempt đã được nhận diện khi không cấp override; rejected khác context có hash và attempt riêng. Các positive controls CLI thật→JSONL→intake A100/B30→Kappa3×3 và hồi quy cũ vẫn đạt. Nhánh supersede thiếu seed metadata đã chuyển sang fail-closed theo diff.

Đây là kết quả kỹ thuật trên fixture, không phải chất lượng nhãn người thật hoặc full repository PASS. Không sửa src/scripts/tests của C, kiểm diff các thư mục này rỗng sau chạy.

## 6. Điểm cần sửa và cách khép

### A — Chuỗi approval bất kỳ có thể bỏ chặn thay thế

Nguồn `scripts/data/receive_main_batch1.py:223–228,316–317`. `_check_accepted_history` chỉ xét `if not d_replacement_approval`; mọi chuỗi không rỗng đều bỏ qua khóa khi đã có input accepted. Giá trị được chép vào biên lai nhưng không kiểm hiện vật quyết định, quyền D hoặc phạm vi bản thay thế.

Probe: tạo fixture đã accepted, gửi input hash khác với `d_replacement_approval='NOT_AN_EXISTING_OR_APPROVED_D_DECISION'`; vẫn accepted. Không có quyết định D nào trong fixture. Điều này chứng minh code chưa xác minh approval, không phải dữ liệu thật đã bị thay.

**Cách sửa tối giản:**

- Nếu chưa cần hỗ trợ tự động thay bản nộp ở Đợt 1, giữ mọi input khác đã accepted ở trạng thái chờ D; không cho chuỗi tùy ý mở khóa. Ghi rõ đường thay thế chưa hỗ trợ tự động và xử lý theo phiên bản/SOP được D phê duyệt.
- Nếu giữ tính năng, tham chiếu phải trỏ tới hiện vật/quyết định đã được D xác nhận qua kênh quản trị hiện có và được đối soát. Ràng buộc ít nhất annotator, dataset/lot/release, old digest, new digest, trạng thái/quyền quyết định và lineage. Không cần phát minh PKI hay hệ thống phê duyệt mới; nhưng một chuỗi do caller tự nhập không phải bằng chứng.
- Kiểm thiếu/sai tham chiếu, quyết định khác scope, old/new hash lệch và trường hợp hợp lệ trên fixture; giữ nguyên lịch sử/nhãn gốc. Không tạo quyết định thay D trong đợt sửa.
- Bản thay thế được phép phải xác định rõ trạng thái có hiệu lực và liên kết bản trước; không để downstream tùy ý chọn một trong nhiều accepted digest.

### B — Cờ CLI được mô tả nhưng chưa được parser hỗ trợ

SOP và notice mô tả `--d-replacement-approval`. Tuy nhiên `main()` tại receive_main_batch1.py:408–416 không khai báo hoặc truyền cờ này. Kiểm `python scripts/data/receive_main_batch1.py --help` cho thấy không có cờ.

**Sửa:** đồng bộ đúng khả năng đã chọn ở mục A. Nếu chưa hỗ trợ thay thế, sửa mô tả để không hướng dẫn một cờ không tồn tại. Nếu triển khai, parser và hàm phải dùng cùng verifier, không chỉ thêm cờ rồi truyền chuỗi qua bypass. Kiểm lệnh đúng SOP thực sự chạy được.

### C — Kịch bản Kappa trong SOP lỗi runtime

Nguồn `docs/QUY_TRINH_KIEM_TRA_INTAKE_MAIN_BATCH1.md:115–120`. Chạy nguyên khối Python được cung cấp trong SOP trên fixture accepted A100/B30 lỗi:

`AttributeError: 'Kappa3x3Result' object has no attribute 'ci_lower'`.

API thực tế có `ci95_bootstrap`, không có `ci_lower/ci_upper`. `kappa` và CI cũng có thể None ở trường hợp suy biến.

**Sửa:** có thể tái sử dụng `format_kappa_3x3_report(result)` đã có trong module thay phần định dạng thủ công. Nếu vẫn định dạng trực tiếp, dùng đúng thuộc tính API và kiểm status/kappa/ci95_bootstrap/bootstrap_warning trước khi định dạng. Khi không xác định Kappa hoặc không công bố CI, báo đúng lý do, không tự gán số hoặc CI thay thế. Chạy nguyên văn đoạn SOP sau sửa trên fixture đa lớp và ca suy biến.

Đoạn SOP hiện chọn `accepted_files[0]` từ toàn lịch sử mà không xác định release có hiệu lực. Khi hoàn thiện đường thay thế ở mục A, cần chọn đúng bản accepted đang có hiệu lực của role/release; nếu mơ hồ thì dừng thay vì lấy tệp đầu tiên. Đối chiếu hash JSONL/view/manifest trước khi tính chỉ số và giữ target B30 đã khóa.

### D — Bootstrap chính thức bị đổi thành mức smoke test

SOP mới đặt `bootstrap_iterations=100` (dòng107–112), trong khi Main plan Mục2 quy định B=1.000, seed2026 và kiểm tỷ lệ suy biến; module kappa_3x3 cũng mặc định 1.000. Mức100 được dùng ở fixture smoke test D để kiểm luồng, không phải chỉ đạo thay tham số nghiên cứu.

**Sửa:** giữ SOP chính thức nhất quán với kế hoạch/default module (1.000 lượt, seed2026 và ngưỡng suy biến theo cấu hình), hoặc trình thay đổi phương pháp riêng để D quyết định trước khi dùng trên kết quả thật. Tách rõ cấu hình smoke test khỏi phân tích nghiên cứu. Không cần đổi thuật toán core đang được kiểm.

## 7. Kiểm thử thực tế và log

Môi trường D: macOS, Python3.14.6, pytest7.4.0, venv D và site-packages local.

```sh
PYTHONPATH=.:src:/opt/homebrew/lib/python3.14/site-packages /Users/yingjunn_/.codex/worktrees/635d/NCKH_2/.venv/bin/python -m pytest tests/test_main_annotation_batch1.py tests/test_blind_view.py tests/test_annotate_cli_timer_pause.py /private/tmp/test_main_8fc_additional_guards.py /private/tmp/test_main_6c26_release_boundaries.py /private/tmp/test_main_599_followup.py /private/tmp/test_main_da3_intake_history.py -q
```

**150 passed in 3.82s**, `main_a12_selected.log`. Có thể dùng các file cùng nội dung trong artifacts/lead_d_review_* của C thay đường dẫn /private/tmp.

```sh
PYTHONPATH=.:src:/opt/homebrew/lib/python3.14/site-packages /Users/yingjunn_/.codex/worktrees/635d/NCKH_2/.venv/bin/python -m pytest /private/tmp/test_main_a12_approval_and_sop.py -q --show-capture=no
```

**4 failed in 0.70s**, `main_a12_approval_and_sop.log`. Các kiểm lần lượt chứng minh bypass chuỗi approval giả, cờ CLI thiếu, khối SOP runtime lỗi và bootstrap không khớp kế hoạch. File probe kèm dùng cwd checkout để nạp helper fixture599 đã có; không đụng Main thật. Một negative test tương lai có thể cần đổi cách gọi khi C chủ động bỏ tính năng thay thế, nhưng phải giữ hành vi an toàn và SOP trung thực, không chỉ sửa kỳ vọng để bỏ lỗi.

## 8. QA và việc tiếp theo

C hoàn thiện đường thay thế/SOP; B dùng nhiệm vụ QA gộp hiện hành và kiểm đúng full SHA sau sửa, giữ 150 test đã đạt cùng các kiểm mới. Không cần B ký QA riêng từng commit trung gian. B chỉ dùng fixture an toàn; D/người được giao kiểm byte gói Main thật, migration và quyền phát hành.

## 9. Giới hạn

Chưa có QA B cho a12 hoặc gói Main thật mới trong lượt này. Không chạy full repo lần này; 150 là bảy tệp chọn lọc. Chưa có quyết định D cho thay thế bản nộp/migration thật. Raw C log và quyết định/phê duyệt là hai loại chứng cứ khác nhau; detector PASS không tự chứng nhận quyền thay nhãn.

## 10. Trạng thái

Main HOLD/LOCKED, training_blocked=true, official_test_used=false. Chưa phát view/mở Pass1. Không sửa mã C, commit/push hoặc thay dữ liệu thật trong lượt kiểm này.
