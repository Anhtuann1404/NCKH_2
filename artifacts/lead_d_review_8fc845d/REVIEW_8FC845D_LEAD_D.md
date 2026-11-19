# Kiểm độc lập bản sửa Main Batch 1 — 8fc845d

Ngày kiểm: 19/11/2026. Kết luận: **đã sửa một số lỗi cũ, còn HOLD phát hành**. Đây là hỗ trợ kiểm chứng cho Lead D, không thay văn bản QA của B hoặc quyết định của D.

## 1. Mục tiêu và phạm vi

Đối chiếu báo cáo C với mã thực tế, tái lập ba suite từng có 35 lỗi legacy, và kiểm hành vi ở các ranh giới còn hở. Không rút mẫu thật, không dùng AI gán nhãn, không phát view và không sửa mã C.

## 2. Người thực hiện / người kiểm độc lập

C là owner mã nguồn. Codex hỗ trợ D đọc mã và chạy fixture độc lập. B vẫn phải QA phiên bản sửa và gói phát hành theo phân quyền; chưa có QA mới của B trong lần bàn giao này.

## 3. AI đã dùng

Codex đọc mã công khai, báo cáo và tạo fixture nhân tạo để kiểm hành vi. Không nạp cohort Main thật hoặc nhãn của A/B. Chỉ đọc tên các cột trong schema shard đã kiểm để xác nhận trường nguồn, không xuất dòng dữ liệu.

## 4. Đầu vào đã khóa

- Repository: https://github.com/Anhtuann1404/NCKH_2.
- Nhánh `feat/c-main-annotation-batch1`, fetch từ origin và xác nhận commit `8fc845dfbade60a880cf62fdcb3ccda47474207b`, kế thừa `b013ed726b8d694679ca7447adbd3d64f0f97bca`.
- Checkout kiểm riêng: `/private/tmp/nckh-main-8fc845d-review`.
- Chưa nhận gói view/mapping/ledger Main thật mới của C để kiểm byte hoặc khẳng định cohort đã được bảo toàn.

## 5. Thay đổi thực tế và phần C đã sửa được

Đã đọc diff 11 tệp. Có sửa thực chất: bỏ cấm `random_subset` toàn cục để giữ legacy; Main sample BLIND thiếu version bị chặn; exporter xuất envelope và CLI đọc được; bản ghi Main do CLI sinh không có `random_subset`; fingerprint thay đổi khi HTML thay đổi; có chặn cấp trùng giữa hai lot khác nhau trong ca test của C; kiểm isolation trước xuất có thể chặn sớm; role manifests có pending/ready=false.

Chưa có thay đổi mã do D/Codex thực hiện trong checkout này. `git diff HEAD -- src scripts tests` rỗng sau kiểm.

## 6. Tự kiểm: phát hiện còn mở và cách sửa

### F1 — Ledger chưa bảo toàn cohort khi chạy lại cùng lot

Nguồn: `src/phishing/data/main_sampling.py:136–162,286–316`.

- Cùng `lot_id` nhưng đổi seed vẫn được rút lại và thêm một RESERVED mới, không yêu cầu quyết định supersede.
- Lô 1 đã rút, lô 2 được cấp tiếp; chạy lại lô 1 cùng tham số thì cohort đổi, do sampler rút lại trên pool đã trừ lô 2 thay vì nạp danh sách lô 1 đã niêm phong. Biến `is_idempotent_rerun` chỉ ngăn ghi event, không giữ kết quả.
- Hai probe đầu trong tệp kiểm kèm đều thất bại theo kỳ vọng an toàn.

**Sửa:** Khi lot đã tồn tại, nạp đúng tập `allocated_candidate_ids`/mapping đã niêm phong và kiểm fingerprint; không gọi lại bước random sample. Nếu tham số/nguồn/nội dung khác cam kết, từ chối trước khi sửa bất kỳ tệp/event nào. Việc đổi ID/salt chỉ thực hiện theo sự kiện supersede được D cho phép và phải giữ danh tính nguồn của A100 và B30; không xem đó là một lượt rút lại tự động. Chỉ lot mới mới lấy từ pool chưa cấp. Kiểm cả retry sau khi đã tạo lot khác, reload ledger từ đĩa và thay đổi tham số. Chỉ số `canonical_pop_index` phải thực sự chỉ vào quần thể gốc, không nhầm với chỉ số pool đã lọc.

### F2 — Hợp đồng Main chưa được kiểm xuyên envelope/sample/record

Nguồn: `src/phishing/annotation/blind_view.py:219–268,675–695`.

- Envelope Main 1.2.0 vẫn nhận sample legacy có `random_subset` nếu sample có đủ trường legacy.
- Envelope version không biết vẫn nhận sample Main 1.2.0 hợp lệ.
- Bản ghi có ID Main BLIND-8hex bỏ contract version và thêm `random_subset` lại được validator nhận theo nhánh legacy.

**Sửa:** Xác định chế độ Main từ ngữ cảnh gói đã khóa, rồi bắt buộc cùng version 1.2.0 trên envelope, từng sample và từng record; sai/thiếu/mixed phải dừng trước hiển thị hoặc ghi nhãn. Kiểm unknown version tại mọi tầng. Legacy đi qua đường legacy được phép, không được dùng để hạ phiên bản Main; giữ hồi quy legacy đang đạt. Giữ Codebook 1.1.0, không tự đổi Codebook.

### F3 — Validator chấp nhận bản ghi Main thiếu xuất xứ

Nguồn: `src/phishing/annotation/blind_view.py:683–687,826–834`.

Một bản ghi Main bị xóa đồng thời `dataset_id`, `dataset_hash`, `codebook_hash`, `sample_content_hash`, `timestamp_utc` vẫn được nhận. Hàm dùng chuỗi rỗng hoặc tự tạo timestamp thay vì từ chối. CLI bình thường có ghi các trường này không đồng nghĩa intake đã kiểm chúng.

**Sửa:** Yêu cầu đủ trường provenance, đúng kiểu/định dạng và không rỗng cho Main thật; không tự điền thời điểm gán nhãn thiếu. Intake đối chiếu với view, role manifest, Codebook và mapping đã khóa; kiểm đủ A100/B30, ID duy nhất, đúng người/lượt, không dry-run, hash nội dung khớp. Hoàn thiện đường intake Main có test đầu-cuối; không dùng nguyên `receive_pass1_v2.py` vốn còn yêu cầu `random_subset` của pilot.

### F4 — Fingerprint đã khóa HTML, nhưng locator nguồn còn có thể rỗng

Nguồn: `scripts/data/export_and_seal_population.py:61–95`; `src/phishing/data/main_sampling.py:60–77,213–227`.

Schema Parquet thật có các cột `sha256,url,label,target,date,lang,lang_score,html`, không có `source_row`. Runner chuyển sang records và gán UID sau lọc nhưng không gắn vị trí dòng gốc trước lọc; Selection Gate cũng không bổ sung trường đó. Mapping nhận `source_row=None`, fingerprint vẫn được tính. Probe pool thiếu source_row vẫn được rút mẫu thành công. Đây là khoảng hở provenance, không phải bằng chứng mất snapshot hoặc sai nhãn.

**Sửa:** Gắn vị trí dòng gốc, shard và revision từ đầu vào đã xác minh trước Gates, giữ chúng qua mọi bước lọc/xáo trộn. Không dùng chỉ số sau lọc làm locator gốc. Main thật thiếu/sai provenance phải bị chặn; không dùng default shard/revision để che việc thiếu nguồn. Đối soát lại từng dòng mapping bằng URL/HTML hash trong khu vực hạn chế. Giữ cohort cũ, bổ sung provenance bằng phép join có kiểm chứng, không tự đổi mẫu. Niêm phong các cấu hình ảnh hưởng tuyển chọn và thứ tự canonical để tái lập.

### F5 — Isolation PASS chưa chứng minh phát hiện seed/salt hardcode mới

Nguồn: `scripts/data/verify_git_isolation.py:103–137`.

Scanner đã mở rộng thư mục, nhưng chỉ dò một giá trị salt cũ trong `PROHIBITED_SECRET_PATTERNS`; không có kiểm tổng quát đối với literal seed/salt đang dùng. Fixture `DEFAULT_BLIND_SALT = "synthetic-new-operating-secret"` vẫn nhận PASS. Scanner cũng bỏ qua lỗi đọc tệp bằng `except ...: continue` và không quét nội dung artifacts trong danh sách mặc định.

**Sửa:** Kiểm các điểm cấu hình vận hành thực sự: cấm default/literal seed/salt trong runner, yêu cầu private input; có negative test với một giá trị mới chưa từng biết. Quét đúng danh sách tracked/staged/public output trong phạm vi phát hành; không âm thầm bỏ qua tệp không đọc được. Tách fixture synthetic và mô tả sự cố lịch sử bằng ngoại lệ có phạm vi được review, không nới quy tắc cho source vận hành. Log không in secret. PASS chỉ xác nhận phép kiểm cụ thể đã chạy, không phải chứng minh không có mọi loại rò rỉ.

### F6 — Hậu kiểm FAIL vẫn có thể ghi đè gói trước

Nguồn: `scripts/data/run_main_batch1_pipeline.py:106–148,227–233`.

Preflight FAIL đã chặn đúng. Tuy nhiên nếu preflight PASS và hậu kiểm FAIL, mapping/view/manifest/ledger đã được ghi. Probe đặt một gói fixture cũ, cho verifier PASS lần đầu và FAIL lần sau: hàm ném RuntimeError nhưng file gói cũ đã bị ghi đè. Vì vậy chưa thể khẳng định “không ghi đè” trên mọi đường lỗi.

**Sửa:** Dựng phiên bản kế tiếp trong staging riêng, kiểm hash/contract/isolation đầy đủ rồi mới công bố bằng thao tác chuyển có kiểm soát; không sửa gói đã niêm phong. Chỉ ghi sự kiện ledger thể hiện trạng thái thực sau khi bước tương ứng thành công; khi lỗi giữ log và staging lỗi riêng, không trả SUCCESS, không thay artifact đang có hiệu lực. Có test preflight FAIL, lỗi giữa chừng, hậu kiểm FAIL và kiểm byte gói/ledger cũ không đổi ngoài event lỗi được quy định.

### F7 — Báo cáo sự cố kết luận vượt phạm vi bằng chứng

Nguồn: `artifacts/INCIDENT_LOG_20261119_MAIN_BATCH1_SALT_EXPOSURE.md:20–29`.

“Tuyệt đối KHÔNG rò rỉ nhãn/Zero Label Leakage” không được chứng minh bằng việc không có khóa label trong Blind View. Seed/salt công khai có rủi ro khôi phục ánh xạ trên nguồn công khai, từ đó biết nhãn nguồn. Tuyên bố “chưa gửi A/B” hiện là C khai báo; D chưa kiểm log bàn giao và gói thật mới trong lượt này.

**Sửa:** Dùng “chưa phát hiện trường nhãn trực tiếp trong các artifact/phạm vi đã kiểm”, mô tả rủi ro suy diễn và giới hạn kiểm người tiếp xúc; phân biệt giá trị seed/salt đã lộ với hash cam kết. Giữ hồ sơ cũ và các bản chưa phát hành làm lineage. Phương án giữ A100/B30 và tái cấp salt/shuffle mới là đề xuất hợp lý để D xem xét, chưa phải quyết định đã ban hành. B chỉ nhận fixture và báo cáo kỹ thuật an toàn trước khi gán mù, không nhận seed/mapping thật để tự kiểm.

## 7. Kiểm thử và bằng chứng

Môi trường D: macOS, Python 3.14.6, pytest 7.4.0, pyarrow 24.0.0. Interpreter venv D, thêm site-packages local như các lượt trước.

```sh
PYTHONPATH=src:/opt/homebrew/lib/python3.14/site-packages /Users/yingjunn_/.codex/worktrees/635d/NCKH_2/.venv/bin/python -m pytest tests/test_main_annotation_batch1.py tests/test_blind_view.py tests/test_annotate_cli_timer_pause.py -q
```

Kết quả: **114 passed in 0.49s**, log `main_8fc_three_suites.log`. Đây là suite hiện có, có 5 probe C bổ sung; không phải toàn bộ repo.

```sh
PYTHONPATH=.:src:/opt/homebrew/lib/python3.14/site-packages /Users/yingjunn_/.codex/worktrees/635d/NCKH_2/.venv/bin/python -m pytest /private/tmp/test_main_8fc_additional_guards.py -q
```

Kết quả: **9 failed in 0.19s**. Tệp kiểm và log kèm theo chứa fixture, không chứa Main thật. Các kiểm này mô tả hành vi an toàn còn thiếu; không được cộng vào số suite C đã báo. Khi tái lập từ ZIP, thay đường dẫn test bằng vị trí file vừa giải nén.

Chạy toàn repo: dừng collection do thiếu `transformers` trong `test_translation_experiment.py` (`main_8fc_full_suite.log`). Sau khi bỏ qua đúng tệp đó: **413 passed, 38 skipped, 6 failed in 4.85s** (`main_8fc_without_translation.log`). Sáu fail đều thiếu gói/nhãn/PLAN01 restricted ngoài Git ở `test_real_calibration_split_isolation.py`, không dùng chúng để quy thành sáu lỗi runtime mới. Kết quả **460 passed/2 skipped** là C báo trên môi trường C, D chưa tái lập đầy đủ. Không cài thêm dependency hoặc tạo dữ liệu thay thế để làm đẹp kết quả.

## 8. QA độc lập

Đề nghị B kiểm commit sửa kế tiếp và tái lập negative tests, không chỉ kiểm lại 114 test đang đạt. Chứng thực đúng commit/hash và nêu môi trường, restricted dependencies, skipped/failed; không tự nhận D đã phê duyệt. C sửa artifact của C, B không sửa rồi tự ký cho phần mình vừa viết.

## 9. Giới hạn và bàn giao tiếp

Chưa kiểm byte cohort gói thật mới; chưa đo exposure Git toàn lịch sử; không tuyên bố người gán chưa từng xem mẫu dựa trên scanner. Graph mới dựng ở phiên trước vẫn chụp b013ed7; đọc báo cáo này/AI_HANDOFF để biết lượt sửa 8fc845d, không coi graph là latest runtime. Gói bằng chứng này chỉ chứa report, probe và log fixture.

## 10. Trạng thái quản trị

**HOLD phát hành** cho đến khi khép các lỗi ảnh hưởng cohort, hợp đồng, provenance và bất biến artifact; QA của B và quyết định của D là các bước riêng. Giữ `main_annotation_status=LOCKED`, `training_blocked=true`, `official_test_used=false`. Không thay cohort thật hoặc tự cấp quyền phát A/B. Phiên này không sửa mã C và không commit/push.
