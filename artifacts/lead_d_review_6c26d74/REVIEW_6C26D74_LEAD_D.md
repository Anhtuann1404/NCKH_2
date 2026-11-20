# Kiểm bản sửa Main Batch 1 tại 6c26d74

Ngày kiểm: 20/11/2026. Kết luận: **130 test đã tái lập đạt, chín probe cũ được khép; vẫn HOLD vì các nhánh phát hành, supersede và intake còn thiếu bảo vệ.**

## 1. Mục tiêu và phạm vi

Kiểm báo cáo C ngày 19/11 trên mã bàn giao mới. Không chọn lại cohort thật, phát view, mở Pass 1 hoặc sửa mã C. Các probe mới kiểm tiếp những yêu cầu F1–F7 đã giao, không thay phương pháp nghiên cứu.

## 2. Người thực hiện và người kiểm độc lập

C sở hữu mã. Codex hỗ trợ D đọc diff và chạy fixture độc lập; đây không thay chữ ký QA của B hay quyết định phát hành của D. B chưa có QA cho commit này trong các hiện vật nhận ở lượt kiểm.

## 3. AI sử dụng

AI đọc mã công khai, tạo record/URL/HTML nhân tạo để kiểm. Không nạp Main thật, mapping/seed thật hoặc nhãn người gán. Các cờ approved trong probe chỉ là fixture kiểm hợp đồng, không phải phê duyệt dự án.

## 4. Đầu vào khóa

Repository https://github.com/Anhtuann1404/NCKH_2, nhánh `feat/c-main-annotation-batch1`, commit `6c26d7464ef6cfa7f1711bba4e27eda7195bd832`, đã fetch từ origin và checkout riêng tại `/private/tmp/nckh-main-6c26d74-review`. Đọc diff 13 tệp so với 8fc845d. Tệp chín probe C đưa vào Git khớp nguyên byte tệp D gốc: SHA-256 `b7f5c37902032701f7aa009024a4c079c800c2321a964a29480fd6ae41e8410a`.

## 5. Phần đã sửa và đã kiểm đạt

- Tái lập đúng lệnh ba suite và chín probe nguyên bản: **130 passed in 1.18s**.
- Các probe cũ về retry lot, mixed version, downgrade record, provenance bị thiếu, HTML fingerprint, source_row, phát hiện salt mới và chặn FAIL trước publish đã được khép trong phạm vi của chúng.
- Mã đã gắn source_row trước Gates, thêm intake Main, staging, ghi ledger qua file tạm và hạ kết luận Zero Label Leakage.
- Hai positive controls bổ sung: intake fixture A100 và B30 hợp lệ được nhận.
- Không sửa mã C; `git diff HEAD -- src scripts tests` rỗng sau kiểm.

## 6. Phát hiện còn chặn phát hành và cách sửa

### F6a — Bỏ qua kết quả isolation sau publish

`scripts/data/run_main_batch1_pipeline.py:275–281` gọi verifier lần cuối nhưng bỏ kết quả, trả SUCCESS bằng kết quả PASS trước đó. Probe cho hai lần đầu PASS, lần cuối FAIL: vẫn SUCCESS.

**Sửa:** mọi phép kiểm có thẩm quyền chặn đều phải được xét. Hoàn tất kiểm trước khi kích hoạt release; nếu còn kiểm sau kích hoạt thì có cơ chế thu hồi/rollback nhất quán và không báo SUCCESS khi FAIL.

### F6b — Replace từng tệp không phải giao dịch nguyên khối

`run_main_batch1_pipeline.py:263–291` thay từng file; khi lỗi chỉ phục hồi ledger, không phục hồi những file đã thay. Probe tiêm lỗi ở lần replace hiện vật thứ hai: file thứ nhất đã đổi, gói không còn nguyên byte cũ. Probe hậu kiểm FAIL cũ chỉ xảy ra trước publish nên không kiểm được nhánh này.

**Sửa:** xuất mỗi phiên bản vào thư mục mới bất biến, kiểm xong chuyển một tham chiếu phiên bản có hiệu lực bằng thao tác nguyên tử; hoặc rollback đầy đủ từng hiện vật khi lỗi. Đừng gọi các os.replace riêng lẻ là atomic cả gói. Ledger/release pointer phải nhất quán khi tiến trình lỗi. Giữ bằng chứng lỗi trong kênh hạn chế, không dọn mất dấu vết cần đối soát.

### F1a — Supersede có thể tạo A100/B0 khi thiếu thông tin B30

`src/phishing/data/main_sampling.py:412–416` mặc định tập B rỗng khi ledger thiếu b_subset_candidate_ids. Đây là tình huống cần giải quyết khi tiếp nhận ledger đời cũ, vốn chưa lưu các trường B mới. Hàm vẫn có thể ghi event supersede với view B rỗng.

**Sửa:** trước bất kỳ thay đổi nào, bắt buộc có đúng 100 UID duy nhất và đúng 30 UID B duy nhất là tập con; kiểm đủ nội dung/cam kết. Nếu hồ sơ cũ thiếu B30, dừng và khôi phục bằng mapping/B view cũ đã khóa có đối chiếu hash trong khu vực hạn chế; không chọn mới, không tự coi tập rỗng là hợp lệ. Đường migration phải có lineage và quyết định D.

### F1b — Cam kết sau supersede không còn được guard đúng

Event supersede ghi `new_seed_commitment`, nhưng đường rerun đọc `seed_commitment`. Khi không thấy trường, guard bỏ qua phép so sánh. Probe supersede xong rồi gọi sampler với seed khác: vẫn được nhận.

**Sửa:** một cấu trúc active release thống nhất cho sampling/supersede/rerun; bắt buộc cam kết hiện hành tồn tại. Phân biệt cam kết chọn cohort với cam kết phát hành/ID, giữ quan hệ phiên bản trước. Rerun phải trả đúng release đang niêm phong, không tự sinh lại ID từ tham số bất kỳ.

### F3a — Intake chưa thực thi quyền phát hành, pass và kiểu cờ

`scripts/data/receive_main_batch1.py` chưa kiểm acceptance/ready_for_annotation, không buộc pass_id=1 và chỉ loại cờ bằng phép so sánh `is True`. Ba probe cho thấy nhận được record khi manifest pending, nhận toàn bộ pass_id=2, và nhận is_dry_run dạng chuỗi `"true"`.

**Sửa:** kiểm manifest đã được duyệt đúng role/release, ready=true, bản Codebook/dictionary và hash đã khóa trước khi official ACCEPTED. Có thể lưu tệp chưa đủ quyền ở khu vực cách ly với trạng thái riêng, không coi là kết quả đã nghiệm thu. Bắt buộc pass đúng mục đích intake; is_dry_run/is_synthetic phải là boolean thật và bằng False ở đường kết quả chính thức. Đồng bộ định mức thời gian với SOP. Kiểm các lỗi trước khi báo thành công, có positive controls rõ trên fixture.

### F3b — Biên lai ACCEPTED có thể bị ghi đè khi kiểm lại

Tên biên lai chỉ phụ thuộc hash input; `receive_main_batch1.py:230–237` ghi lại cùng tên mỗi lần. Probe intake hợp lệ rồi thay manifest và kiểm lại cùng input: biên lai accepted cũ bị thay bằng rejected. File nhãn thô bất biến không đủ bảo toàn lịch sử quyết định kiểm.

**Sửa:** giữ nguyên biên lai đã phát hành, lưu từng lần kiểm bằng ID/context hash mới với tham chiếu biên lai trước. Tách trạng thái hiện hành khỏi lịch sử; không ghi đè âm thầm accepted/rejected. Mỗi lần phải gắn input hash, manifest/view/release hash, version công cụ và thời điểm kiểm.

### F3c — Timestamp chỉ kiểm không rỗng, chưa kiểm định dạng

Record với timestamp_utc=`definitely-not-a-timestamp` vẫn được validator nhận.

**Sửa:** parse và kiểm timezone/chuẩn timestamp, kiểm định dạng SHA-256 của trường hash; đối chiếu giá trị với hiện vật chuẩn ở intake. Không tự sửa giờ hoặc điền giờ hiện tại khi nguồn thiếu/sai. Probe hiện tại chứng minh lỗi timestamp; kiểm hash là yêu cầu cần hoàn thiện theo hợp đồng đã giao, không được báo đã test nếu chưa chạy.

### F2/G3 — random_subset lồng trong metadata Main vẫn lọt

Envelope Main có sample hợp lệ nhưng chứa `release_info.random_subset=true` vẫn qua assert_no_label_leak. Quy tắc mới chỉ kiểm ở vài tầng trực tiếp, chưa truyền chế độ Main qua đệ quy.

**Sửa:** kiểm schema/allowlist envelope và truyền ngữ cảnh Main qua toàn cây; cấm trường phân tầng ở metadata lồng nhau trong Main mà không làm hỏng legacy được phép. Test phải dùng sample hợp lệ để không nhận PASS do lỗi schema không liên quan.

### F5 — Scanner phát hiện secret rồi chép nguyên giá trị vào report

`scripts/data/verify_git_isolation.py:144–150` đưa line.strip() vào term. Probe xác nhận JSON report có nguyên secret fixture. Report mặc định được ghi dưới artifacts công khai, nên chính báo cáo có thể phát tán giá trị vừa phát hiện.

**Sửa:** report chỉ chứa file/dòng, mã quy tắc và định danh bằng chứng đã che; không xuất literal hay cả dòng. Nếu cần lưu bản gốc, niêm phong kênh hạn chế có quyền truy cập riêng. Kiểm cả stdout/stderr và report không chứa secret.

### Hồ sơ và mức kết luận

Incident đã hạ câu Zero Label Leakage nhưng vẫn ghi A là “Nguyễn Văn A” và khẳng định hoàn toàn chưa tiếp cận mã. Dự án đang dùng Annotator A (Khải); C phải đối chiếu đúng định danh, không tự gán họ tên hoặc kết luận mức tiếp xúc ngoài bằng chứng. Ghi “theo log bàn giao...” hoặc “theo xác nhận...” đúng nguồn; phần chưa xác minh giữ mở. Không yêu cầu A tham gia công việc QA để sửa lỗi thư ký.

Đổi “đạt bảy cổng của B” thành “C tự kiểm theo checklist, chờ B tái lập”. Test intake mới dựng record thủ công; test CLI hiện có và test intake tách rời chưa tự chứng minh một lượt CLI→JSONL→intake→ghép B30/Kappa hoàn chỉnh. C/B cần chạy chuỗi đó bằng fixture và đưa đúng lệnh vào SOP; chỉ có tên script không chứng minh SOP/CLI đã đồng bộ.

## 7. Lệnh kiểm, kết quả và log

Môi trường: macOS, Python3.14.6, pytest7.4.0, pyarrow24.0.0; venv D và site-packages local.

```sh
PYTHONPATH=.:src:/opt/homebrew/lib/python3.14/site-packages /Users/yingjunn_/.codex/worktrees/635d/NCKH_2/.venv/bin/python -m pytest tests/test_main_annotation_batch1.py tests/test_blind_view.py tests/test_annotate_cli_timer_pause.py /private/tmp/test_main_8fc_additional_guards.py -q
```

**130 passed in 1.18s**, `main_6c26_selected.log`.

```sh
PYTHONPATH=.:src:/opt/homebrew/lib/python3.14/site-packages /Users/yingjunn_/.codex/worktrees/635d/NCKH_2/.venv/bin/python -m pytest /private/tmp/test_main_6c26_release_boundaries.py -q
```

**11 failed, 2 passed in 1.60s**, `main_6c26_boundaries.log`. Hai passed là positive controls intake A/B. Tệp probe kèm theo có thể đặt ngoài repo khi chạy; thay đường dẫn bằng vị trí giải nén, giữ cwd là checkout đúng commit. Đây là bộ kiểm bổ sung, không sửa hoặc thay chín probe D trước đó.

Chạy rộng `python -m pytest tests/ --ignore=tests/test_translation_experiment.py -q` với cùng PYTHONPATH: **420 passed, 38 skipped, 6 failed in 5.58s** (`main_6c26_broad.log`). Sáu fail do thiếu gói/nhãn/PLAN01 restricted ở test_real_calibration_split_isolation.py; không coi chúng là sáu lỗi mã mới. Translation test bị loại có chủ đích vì môi trường thiếu transformers đã xác nhận ở lượt trước; không gọi đây là full-suite PASS.

## 8. QA độc lập

B cần kiểm commit sửa tiếp theo trên fixture, giữ mù với dữ liệu thật; không ký PASS dựa riêng 130 test. D/người được D giao kiểm gói Main thật và migration cohort. Các kết quả của C ở báo cáo là tự kiểm, chưa phải chữ ký B.

## 9. Giới hạn và bàn giao

Chưa nhận gói Main thật, chưa thực hiện supersede trên cohort thật, chưa kiểm exposure toàn lịch sử Git. Các lỗi được chứng minh bằng fixture; không suy thành đã mất dữ liệu thật hoặc nhãn thật đã bị sửa. Graph vẫn chụp b013ed7; dùng AI_HANDOFF và báo cáo commit này cho hiện trạng.

## 10. Quản trị

Giữ Main **HOLD/LOCKED**, training_blocked=true, official_test_used=false. C tiếp tục sửa các nhánh còn hở, B QA phiên bản cuối, D quyết định lineage và phát hành riêng. Không commit/push hoặc sửa mã C trong lượt này.
