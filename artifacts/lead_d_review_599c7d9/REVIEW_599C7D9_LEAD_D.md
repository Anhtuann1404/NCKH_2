# Kiểm Main Batch 1 tại 599c7d9 và báo cáo QA B V1.4

Ngày kiểm: 21/11/2026. **Đã tái lập 144 passed và chuỗi CLI thật tới intake/Kappa 3×3 trên fixture. Còn hai nhóm lỗi mã, tương ứng ba kiểm chưa đạt: retry hợp lệ sau supersede và bất biến lịch sử biên lai. Main vẫn HOLD.**

## 1. Mục tiêu và phạm vi

Đọc hai báo cáo mới của B/C, phân biệt phiên bản, đối chiếu sửa lỗi và chạy lại các kiểm liên quan. Không sửa mã C, rút lại cohort Main, thực hiện supersede thật, phát view hoặc mở Pass 1.

## 2. Người thực hiện và kiểm độc lập

C là owner mã nguồn, B QA độc lập; Codex hỗ trợ D kiểm mã/fixture. B V1.4 kiểm 6c26d74 và giữ HOLD. C bàn giao 599c7d9, vẫn chờ B QA phiên bản mới. Không dùng QA 6c làm chứng thực 599.

## 3. AI đã dùng

Codex đọc mã công khai, kiểm hash và tạo dữ liệu cùng câu trả lời CLI nhân tạo cho kiểm tích hợp. Không dùng AI gán nhãn dữ liệu nghiên cứu. Các approval và record trong fixture chỉ mô phỏng hợp đồng, không là quyết định/nhãn thật của dự án.

## 4. Đầu vào đã khóa

- NCKH_2, nhánh `feat/c-main-annotation-batch1`, commit `599c7d92a15ce3422d8eeecd7b290e2da3628d53`, đã fetch origin và checkout kiểm riêng `/private/tmp/nckh-main-599c7d9-review`.
- Đọc diff 13 tệp so với 6c26d74.
- Hai probe D do C đưa vào Git giữ nguyên byte: bộ 8fc SHA b7f5c37902032701f7aa009024a4c079c800c2321a964a29480fd6ae41e8410a; bộ 6c SHA 4f117730fe811401e2132c50458dbad576a14c9e8fad22988f50099882cbb63d.
- Thông báo B V1.4 và C 599 được lưu nguyên byte riêng trong gói bằng chứng. ZIP 6c 20.687 byte cùng hash của đủ tám thành phần B dẫn đều khớp tệp D. Chưa nhận file QA B V1.4 gốc 34.343 byte/raw log B để đối chiếu trực tiếp; kết quả trên máy B là B công bố, không gọi là D đo được.
- Chưa nhận gói Main thật mới hoặc xác minh migration trên cohort thật.

## 5. Đã sửa và kết quả đạt

Đã tái lập **144 passed in 2.73s** trên ba suite và hai bộ probe D nguyên bản. Vì vậy, 11 lỗi cụ thể của bộ ranh giới 6c đã được khép trong phạm vi probe, cùng hai positive controls và các hồi quy cũ.

Mã đã xét final isolation, bổ sung rollback các file, kiểm số lượng B30, siết quyền/pass/boolean/timestamp/hash của intake, chặn random_subset lồng và che literal secret trong report. Không tiếp tục ghi các probe đó là lỗi đang tái lập.

D bổ sung kiểm chuỗi **export → CLI thật (đầu vào scripted fixture) → JSONL → intake A100/B30 → đọc lại JSONL đã accepted → compute_kappa_3x3_from_records với target_sample_ids B30**: **PASS**. Không dựng JSONL thủ công cho kiểm này. Có ba lớp trong fixture, mẫu số 30 và Kappa=1.0 do câu trả lời A/B được lập trình đồng nhất. Giá trị này chỉ là positive control kỹ thuật, không phải độ đồng thuận nghiên cứu; thời gian CLI trong fixture không dùng cho PLAN-01. Bootstrap 100 lượt phục vụ smoke test, không thay cấu hình báo cáo thống kê chính thức.

## 6. Hai nhóm lỗi còn mở và cách sửa

### F1 — Retry hợp lệ sau supersede vẫn bị từ chối

Nguồn: `src/phishing/data/main_sampling.py:161–167,537–548`; hàm `compute_seed_commitment` ở cùng module.

Supersede ghi cam kết theo payload `supersede:<shuffle>|salt:<salt>`, còn rerun tính payload đủ lot seed/B seed/shuffle/salt qua compute_seed_commitment. Hai công thức khác nhau. Thêm cùng tên seed_commitment vào event đã chặn được seed sai, nhưng cũng chặn đường hợp lệ.

Probe: tạo lot với seed11/22/33 và salt fixture cũ; supersede với shuffle44/salt mới; retry giữ nguyên seed chọn lot và B, dùng đúng shuffle44/salt mới. Hàm ném ValueError vì cam kết không khớp, thay vì trả đúng A100/B30 và ID vừa niêm phong.

**Cách sửa:**

1. Tách rõ cam kết bất biến về cohort/B30 khỏi cam kết release/ID hiện hành; dùng cùng schema và cách canonical hóa khi ghi, đọc và kiểm một loại cam kết.
2. Rerun hợp lệ phải nạp đúng active release, không rút mẫu lại hoặc phát sinh ID khác. Tham số lệch phải bị từ chối trước khi ghi.
3. Nếu thiết kế không cho gọi sampler sau supersede, phải có đường nạp/xuất active release được tài liệu hóa và được exporter sử dụng; không để toàn bộ đường chạy lại gói supersede bị khóa.
4. Có cả positive control retry đúng sau supersede và negative controls seed/salt/pool sai; kiểm reload ledger và byte/UID A100/B30/ID không đổi.
5. Hoàn thiện bằng fixture trước. Migration/supersede cohort thật vẫn chờ quyết định riêng của D.

### F3b — Lịch sử biên lai chưa bất biến trên mọi lần kiểm lại

Nguồn: `scripts/data/receive_main_batch1.py:251–267`.

C đã bảo vệ accepted cũ khi lần sau rejected; probe cũ đạt. Nhưng hai nhánh còn ghi đè:

- **Accepted → accepted:** thêm metadata ngữ cảnh hợp lệ vào manifest, giữ input/view/nhãn. Intake vẫn accepted và ghi đè receipt gốc bằng manifest_sha256 mới. Byte biên lai lịch sử đã thay đổi.
- **Nhiều rejected sau accepted:** các lần kiểm bị từ chối đều dùng cùng tên `<digest>.recheck_rejected.json`. Lần sau có lý do khác ghi đè lần trước.

**Cách sửa:**

1. Giữ nguyên mọi biên lai đã phát hành, cả accepted và rejected; không chỉ nhánh accepted→rejected đầu tiên.
2. Lần kiểm cùng input và cùng ngữ cảnh có thể trả biên lai gốc theo chính sách idempotency. Khi có lần kiểm/ngữ cảnh mới, lưu attempt có ID duy nhất và tham chiếu attempt trước.
3. Mỗi attempt gắn input hash, manifest/view/release hash, version công cụ, timestamp kiểm và kết quả. Tách bản chỉ mục trạng thái hiện hành khỏi lịch sử.
4. Không bỏ qua âm thầm lỗi đọc receipt cũ rồi ghi đè. Khi không xác minh được hiện vật cũ phải dừng hoặc cách ly, bảo lưu nguyên byte.
5. Kiểm đủ accepted→accepted với manifest context mới, accepted→rejected, nhiều rejected có lý do khác, rejected→accepted và retry cùng context. Positive controls intake A/B vẫn phải đạt.

## 7. Kiểm thử và bằng chứng

Môi trường: macOS, Python3.14.6/pytest7.4.0, pyarrow24.0.0; interpreter venv D và site-packages local. Không sửa src/scripts/tests của C (`git diff HEAD` trên các thư mục này rỗng).

Lệnh tái lập 144 test dùng hai probe ngoài repo giữ nguyên byte:

```sh
PYTHONPATH=.:src:/opt/homebrew/lib/python3.14/site-packages /Users/yingjunn_/.codex/worktrees/635d/NCKH_2/.venv/bin/python -m pytest tests/test_main_annotation_batch1.py tests/test_blind_view.py tests/test_annotate_cli_timer_pause.py /private/tmp/test_main_8fc_additional_guards.py /private/tmp/test_main_6c26_release_boundaries.py -q
```

Kết quả **144 passed in 2.73s**, `main_599_selected.log`. Có thể thay hai đường dẫn /private/tmp bằng file cùng hash trong artifacts/lead_d_review_* của C.

```sh
PYTHONPATH=.:src:/opt/homebrew/lib/python3.14/site-packages /Users/yingjunn_/.codex/worktrees/635d/NCKH_2/.venv/bin/python -m pytest /private/tmp/test_main_599_followup.py -q --show-capture=no
```

Kết quả **3 failed, 1 passed in 0.82s**, `main_599_followup.log`; passed là chuỗi CLI thật tới Kappa3x3. Probe kèm có thể đặt ngoài repo và chạy từ cwd checkout. stdout fixture bị ẩn ở log lỗi bằng --show-capture=no, không chạy trên Main thật.

Lượt rộng `python -m pytest tests/ --ignore=tests/test_translation_experiment.py -q` với cùng PYTHONPATH: **421 passed, 38 skipped, 6 failed in 5.40s**, `main_599_broad.log`. Sáu fail do thiếu gói/nhãn/PLAN01 restricted ở test_real_calibration_split_isolation.py. Translation bị bỏ theo thiếu transformers đã biết; đây không phải full-suite PASS hoặc sáu lỗi runtime mới.

## 8. QA độc lập và việc cần B

B V1.4 đã tái lập đúng các lỗi 6c theo báo cáo nhận; không phát hiện sai lệch hash gói D B dẫn. B chuyển QA sang commit sửa tiếp theo sau 599, kiểm cả luồng được phép và luồng phải chặn. Có thể dùng positive E2E CLI của D để khép bằng chứng G7 trong phạm vi fixture, nhưng phải tái lập độc lập và đồng bộ lệnh vào SOP. Không dùng Kappa fixture để kết luận chất lượng nhãn người thật. B giữ tính mù, chỉ nhận fixture và bằng chứng kỹ thuật an toàn.

## 9. Giới hạn và hồ sơ

Chưa có QA B cho 599 trong hiện vật nhận; chưa kiểm byte gói Main thật hoặc migration. C dùng cụm “tái lập độc lập” cho tự kiểm của owner cần đổi thành “C tự kiểm/tái lập test D”; chờ B QA riêng. Không gọi rollback bằng RAM và os.replace từng file là chứng minh phục hồi sau mọi kiểu crash: kết luận trong phạm vi ngoại lệ và fault injection đã chạy. SOP cần có lệnh intake/ghép B30/Kappa thực tế, không chỉ tên module. Đây là hoàn thiện báo cáo và cách dùng, không yêu cầu tạo thêm nền tảng giao dịch hoặc thay phương pháp nghiên cứu.

## 10. Quản trị

Giữ Main HOLD/LOCKED, training_blocked=true, official_test_used=false. C sửa hai nhóm còn tái lập, B kiểm phiên bản cuối; D kiểm gói thật, quyết định lineage và phát hành riêng. Không sửa cohort, commit/push hoặc phát view trong lượt kiểm này.
