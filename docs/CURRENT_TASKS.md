# Current tasks

Cập nhật hiện hành 05/10/2026. Sprint khởi động dài hai tuần tính từ ngày nhóm bắt đầu; chưa có ngày bắt đầu chính thức.

## Bàn giao D hiện hành

[Hồ sơ bàn giao và phân công review](DEVELOPMENT.md): MODEL-API-EXT-01, MODEL-BUNDLE-01, PERF-DEMO-01 và PARITY-DOM-01 DONE cho demo fixture. 55 Python tests, 11 Node tests, 15 browser checks, 6 parity cases đạt; số đo latency lưu local; code phần D đã tích hợp vào develop từ nhánh codex/d-demo-integration. Bản gốc feat/local-dev-01 được giữ nguyên. B review chạy lại, C review capture parity, A thử UI fixture; chưa dùng corpus thật.

Lead đã nghiệm thu pilot C 0bf180c/view8be1c642…8d9a749; chưa nhận commit kích hoạt hoặc kết quả A/B. Training chính tiếp tục bị chặn. Các task/nhật ký khởi động phía dưới giữ để truy vết; trạng thái C mới nhất phải đối chiếu nhánh C, không suy từ bảng TODO ban đầu.

## Trạng thái có bằng chứng

- DONE — hướng đề cương được GVHD duyệt: theo xác nhận người dùng.
- DONE — nhóm từ 4 người trở lên: theo xác nhận người dùng, chưa điền tên/ngân sách giờ.
- DONE — kiểm kê URL PhishVN: [kết quả](../data/source_audit/PhishVN_kiem_ke.json), [script](../data/source_audit/kiem_ke_phishvn.py).
- DONE — thử kỹ thuật 20 PhreshPhish: [summary](../data/source_audit/phreshphish/pilot_summary.json). Không phải tập thực nghiệm đã xác minh.
- DONE — bộ tài liệu khởi động và hợp đồng API v0.1.
- DONE — D là người dùng/lead, nhận model và API–extension; phân công owner A/B/C/D ở [TEAM](TEAM.md). A/B/C chưa có họ tên.
- DONE — scaffold DEV-01 của D: preprocessing URL/HTML, URL/DOM/text draft, primitive domain/UGC, CLI fixture, môi trường và 17 unittest; chưa là pipeline đã khóa.
- DONE — EXT-01: FastAPI mock và MV3 demo đã build; 35 Python tests, 9 Node tests, 11 browser smoke checks đạt. Chỉ kiểm chức năng bằng fixture, không là kết quả mô hình.
- DONE — phần khung kiểm run plan/chỉ số/ngưỡng validation của D; chưa có trainer mô hình thật.
- TODO — date toàn nguồn, freeze danh mục/codebook, pilot nhãn, phần import/index của C, dữ liệu chính, huấn luyện/đánh giá mô hình, serving bundle thật và đo p50/p95.

`TODO` chưa làm; `IN_PROGRESS` đang có công việc thực; `BLOCKED` có phụ thuộc cụ thể; `DONE` có sản phẩm kiểm tra được. Không đánh dấu DONE chỉ vì đã có mô tả.

## Việc tiếp theo theo thứ tự

### START-01 — Chốt người và ngân sách giờ

Status: TODO. Owner: D — lead. Phụ thuộc: không.

Điền tên A/B/C/D, giờ mỗi tuần trong 6–8 tuần gán nhãn, xác nhận D phụ trách model/API–extension và nơi giữ dữ liệu. A/B/C là người khác nhau. Done khi cả nhóm xác nhận phân công và tổng giờ; cập nhật mục đội nhóm trong file này, không sửa đề cương để thay lõi.

### DATA-01 — Khóa nguồn và audit riêng date

Status: TODO. Owner: C. Phụ thuộc: START-01 để xác định người thực hiện.

Lấy revision và tệp có checksum; đọc riêng date từ nguồn pinned, min/max, counts tháng, thiếu/sai ngày và split. Không dựa API statistics hiện tại để nói đã có date toàn corpus. Giữ official test riêng. Done khi có manifest xác minh và audit date tái lập; lấy mẫu pilot đã mở phải nằm trong exclusion registry.

### DATA-02 — Khóa danh mục và codebook

Status: TODO. Owner: C + A/B rà quy tắc, GVHD hỗ trợ. Phụ thuộc: DATA-01.

Đối chiếu cửa sổ quý, nguồn ngoài, 14 mã dự kiến, ánh xạ thương hiệu con; xác minh endpoint/UGC/ủy quyền và nguồn hiệu lực. Done khi dictionary/codebook có version/hash và log ngày khóa, trước mở nhãn/nội dung tập chính. Nhánh thời gian có quy tắc tri thức as-of riêng.

### LABEL-01 — View mù và pilot có bấm giờ

Status: TODO. Owner: C tạo view; A/B đọc độc lập. Phụ thuộc: DATA-02.

Giao diện chỉ có sample_id, URL–nội dung; ẩn target/nhãn nguồn/điểm mô hình và nhãn người còn lại. Dùng 20 mẫu kỹ thuật, bổ sung 12 phishing ngoài tập đánh giá để pilot có 20 phishing. Done khi lưu nhãn độc lập, thời gian gồm tra cứu/phân xử và giờ dự kiến. Không chạy HTML nguồn trực tiếp.

### PLAN-01 — Khóa quy mô và kế hoạch audit

Status: TODO. Owner: D + A/B/C. Phụ thuộc: LABEL-01.

Áp dụng quy tắc 2.000→1.200 nếu trung bình >5 phút/phishing hoặc thiếu giờ; nếu vẫn quá tải thì ghi quy mô thấp hơn trước kết quả. Khóa mẫu 30% ngẫu nhiên, audit lớp ~200 và tiêu chí hard benign. Done khi có sampling plan, seed, giờ dự phòng và quyết định cỡ mẫu.

### DEV-01 — Scaffold parser/features và môi trường

Status: IN_PROGRESS — phần scaffold của D đã DONE, import/index của C còn TODO. Owner: D (preprocessing/features); C (import/index dữ liệu). Phụ thuộc: có thể chuẩn bị bằng fixture trước DATA-02.

Tạo môi trường, khóa dependency, module preprocessing và fixture domain/UGC/HTML không có nội dung thật. Done khi fixture chứng minh không thực thi HTML, không fetch mạng, không dùng labels/metadata làm features. Chưa huấn luyện tập chính ở bước này.

**Bằng chứng phần D (04/10/2026):** [preprocessing](../src/phishing/preprocessing/__init__.py), [features](../src/phishing/features/__init__.py), [domain rules](../src/phishing/features/domains.py), [CLI](../scripts/inspect_snapshot.py), [tests](../tests/test_preprocessing.py), [domain tests](../tests/test_domain_rules.py), [fixture](../tests/fixtures/synthetic_login.html), [environment](../configs/dev_environment.lock.json). 17 tests đạt và CLI chạy bằng CPython 3.14.6; lệnh ở DEVELOPMENT. Version dev-0, chưa fit TF-IDF/mô hình, chưa phân nhóm eTLD+1 và chưa kiểm parity DOM trình duyệt. C vẫn cần bàn giao import/index; B review fixture/code trước khi coi pipeline đủ điều kiện cho run chính.

### EXT-01 — Khung MV3 và mock API

Status: DONE — prototype mock nội bộ. Owner: D. Phụ thuộc: đọc API_SPEC; có thể làm song song.

Popup bật/tắt, snapshot sạch, navigation/revision và cảnh báo mock. Done khi chuyển trang không nhận kết quả cũ, service offline hiện chưa đánh giá được. Mock luôn có nhãn rõ; không ghi số đo mock thành hiệu năng mô hình.

**Bằng chứng (04/10/2026):** [API mock](../src/phishing/serving/mock_api.py), [runner](../scripts/run_mock_api.py), [background](../extension/src/background.ts), [content](../extension/src/content.ts), [popup](../extension/src/popup.ts), [snapshot](../extension/src/snapshot.ts), [API tests](../tests/test_mock_api.py), [Node tests](../extension/tests/core.test.mjs), [browser smoke](../extension/tests/browser-smoke.mjs), [demo page](../tests/fixtures/demo_pages/login.html). Chromium 153.0.8010.12/profile tạm kiểm 11 tình huống; báo cáo/ảnh sinh tại `artifacts/smoke/` (ignore). Lệnh và từng bước cài ở DEVELOPMENT. Chưa kiểm privacy trên trang thật, chưa load bundle/checksum mô hình thật, chưa đo hiệu năng nghiên cứu; B review khi bàn giao.

### MODEL-PREP-01 — Khung kiểm đầu vào và đánh giá bằng fixture

Status: DONE — primitives, không phải trainer hoàn chỉnh. Owner: D. Phụ thuộc: giao thức đã duyệt, không cần dữ liệu thật.

[RunPlan](../src/phishing/training/plan.py) kiểm sample/group overlap, missing group, pilot/reserved exclusion từ groups do C cung cấp; không tự đoán eTLD+1. [Metrics](../src/phishing/evaluation/metrics.py) tính TP/FN/FP/TN/recall/FPR/precision/F1, giữ None khi không xác định; chọn threshold **từ validation** theo score >= threshold, ràng buộc FPR và tie-break cao hơn. Không có điểm khả thi trả None, thiếu lớp báo lỗi. [7 tests](../tests/test_evaluation.py) đạt. Grouped CV, TF-IDF/LR, average precision, paired bootstrap và ablation đã triển khai bằng fixture ở MODEL-PREP-02; temporal còn chờ; không đánh dấu điều kiện huấn luyện chính là hoàn tất.

### MODEL-PREP-02 — Trainer và đánh giá mô phỏng

Status: DONE — tích hợp dữ liệu mô phỏng, chưa đủ điều kiện run chính. Owner: D. Không phụ thuộc việc B nhận nhiệm vụ.

[Pipeline](../src/phishing/training/pipeline.py), [synthetic dataset](../src/phishing/training/synthetic.py), [grouped splits](../src/phishing/evaluation/grouped.py), [paired bootstrap](../src/phishing/evaluation/bootstrap.py), [runner](../src/phishing/training/experiment.py), [CLI](../scripts/run_synthetic_experiment.py), [13 tests](../tests/test_training_pipeline.py). Đã chạy 160 trang/40 nhóm, outer 5 × 3 seed, M0–M3/B-rule + 3 ablation, chọn C và ngưỡng validation, paired group-bootstrap 2000 lượt riêng từng seed. 48 Python tests đạt. Artifacts có manifest/code hash và dấu synthetic-only; chi tiết/lệnh tại DEVELOPMENT. Chưa gọi dữ liệu thật, chưa hoàn thiện dictionary/fuzzy/B-rule nghiên cứu hoặc temporal, chưa xuất bundle thật. B audit khi đã nhận việc; D tiếp tục phần không phụ thuộc dữ liệu.

### ERROR-ANALYSIS-01 — Đọc lỗi M2–M3 trên fixture

Status: DONE phần công cụ mô phỏng, chờ nhóm review PR vào develop. Owner: D. Nhánh codex/synthetic-error-analysis từ develop; không phụ thuộc mã ingestion C hoặc PR báo cáo #4.

[CLI](../scripts/analyze_synthetic_errors.py) xuất error_cases.csv và error_summary.json từ run đã lưu: M3 sửa/sai thêm, cả hai sai, FP/FN riêng từng mô hình và ca thiếu ngưỡng, tách seed × FPR. Kiểm cohort/group/fold/threshold/decision và hash artifact nếu run có; ghi rõ recorded_only cho run cũ. Không fit, không chọn lại ngưỡng, không đọc raw URL/HTML và không nhận scope dữ liệu thật. 65 Python tests đạt; chạy phân tích run fixture 160 mẫu/40 nhóm với ba seed, hai FPR đạt. Artifacts nằm trong artifacts/runs (ignored). B kiểm lệnh PowerShell theo DEVELOPMENT; chưa xác minh trên Windows thực tế. Không thay giao thức hoặc mở training nghiên cứu.

## Đội nhóm cần điền

- A — họ tên: chưa điền; giờ/tuần: chưa điền.
- B — họ tên: chưa điền; giờ/tuần: chưa điền.
- C — họ tên: chưa điền; giờ/tuần: chưa điền.
- D — người dùng, lead + model + API–extension; họ tên chính thức/giờ tuần: chưa điền.
- Owner model: D; C bàn giao dữ liệu, B kiểm tái lập sau khóa nhãn.
- GVHD và thành viên thêm: chưa điền.

## Điều kiện trước huấn luyện chính

- [ ] Revision/checksum và quyền nguồn đã ghi.
- [ ] Audit date, cửa sổ, dictionary/codebook khóa.
- [ ] Pilot loại khỏi tập đánh giá; ngân sách giờ và cỡ mẫu chốt.
- [ ] Nhãn tổ chức hoàn chỉnh phần giữ lại, QC/audit và phân xử có log.
- [ ] Groups/splits và các loại trùng đã kiểm; official test không vào phát triển.
- [ ] Preprocessing/features version hóa; pipeline học chỉ fit phần huấn luyện.

## Nhật ký cập nhật

03/10/2026 — tạo khung khởi động từ đề cương được duyệt; chưa khởi động pipeline, crawler hoặc mô hình. Đã kiểm liên kết nội bộ, JSON/config, schema refs và 4 ví dụ request/response bằng JSON Schema 2020-12; các request chứa target, thiếu HTML, revision âm hoặc file URL bị schema từ chối. Chưa kiểm toàn bộ OpenAPI meta-schema hoặc backend chạy thật. Cập nhật trạng thái cùng đường dẫn bằng chứng sau mỗi task, không tạo file current task theo ngày.

04/10/2026 — chốt ownership 4 vai trò: A nhãn, B kiểm độc lập/QA, C pipeline dữ liệu/view mù, D người dùng/lead + model + API–extension. Các task triển khai vẫn TODO; chưa huấn luyện hoặc chạy API.

04/10/2026 — đưa phân công TEAM vào mục 6.1, bảng tiến độ mục 8 và bảng thông tin bốn thành viên của đề cương theo yêu cầu. D nhận trực tiếp model/API–extension và lead; họ tên A/B/C và giờ tuần chưa chốt.

04/10/2026 — triển khai DEV-01 phần D trên nhánh `feat/dev-01-preprocessing`; tạo venv, URL/HTML preparation và URL/DOM/text draft, domain/UGC primitives, CLI cùng fixture mô phỏng. 17 unittest đạt; inspect xuất features đúng, không có verdict. Không mở tập chính, không gọi DeepSeek, không thay đề cương/RQ/giao thức hoặc đóng băng dictionary. DEV-01 còn IN_PROGRESS vì phần import/index của C chưa làm; START-01/DATA-01/DATA-02 vẫn TODO. Việc tiếp theo của D có thể là EXT-01 mock, song song với C khóa nguồn.

04/10/2026 — điều chỉnh cách làm theo yêu cầu của D: đưa scaffold vào repo gốc `/Users/yingjunn_/Study_/NCKH_2`, trên nhánh cục bộ `feat/local-dev-01` tạo từ main mới nhất. Giữ cập nhật DeepSeek hiện có; 17 tests chạy tại repo gốc đều đạt. Code và docs hiện để dạng thay đổi chưa commit; các lần triển khai tiếp theo làm trực tiếp tại repo gốc, chỉ commit/push khi người dùng yêu cầu.

04/10/2026 — hoàn thành EXT-01 mock và MODEL-PREP-01 primitives tại repo gốc. FastAPI/TypeScript dependencies có version lock; 35 Python tests + 9 Node tests + 11 Chromium smoke checks đạt. Không lấy dữ liệu thật, không gọi DeepSeek, không fit mô hình hoặc thay RQ/protocol. Giữ code/docs chưa commit theo yêu cầu. Các bước cần A/B/C vẫn TODO; DEV-01 còn phần import/index của C, model thật/API bundle thật và runtime p50/p95 chưa làm.

04/10/2026 — theo yêu cầu D, hoàn thiện MODEL-PREP-02 bằng fixture trong repo gốc: TF-IDF/LR, grouped CV, ablation, validation threshold, average precision và paired group-bootstrap. Giữ hướng nghiên cứu đã duyệt, không yêu cầu B demo khi chưa nhận việc. Code/docs để chưa commit.


## Nghiệm thu bàn giao A/B/C — Lead review 04/10/2026

Đã đọc nhánh B `docs/member-b-start01` tại `53adc15`, A tại `c528ea3`, C `feat/data-pipeline` tại `ccdfdbb` (mã sửa LABEL-01 `7fe0239`). B đã nhận vai trò, xác nhận 5–10 giờ/tuần và có review tĩnh; không còn coi B là chưa nhận việc. Tài liệu B trên remote hiện có R-B01–R-B04, chưa có bảng L-B01–L-B06 như thông báo bàn giao; cần B đồng bộ bảng lỗi/commit để truy vết.

Kiểm tra độc lập trên bản C: 78 tests + 32 subtests đạt. Script probe riêng trên fixture tái hiện: kappa loại mẫu random nhưng difficult; kết quả người tập thao tác synthetic thiếu dấu synthetic/dataset provenance; thay gói/nội dung nhưng cùng sample_id bị resume coi hoàn tất. Chưa sửa code nhánh C, chưa gán nhãn thật hoặc dùng official test.

Kết luận:
- LABEL-01: IN_PROGRESS/PENDING_REVIEW. Đã có allowlist, dry-run tách file, kiểm người/pass, báo JSON lỗi và xem toàn văn. Chưa đủ cho pilot nghiên cứu.
- DATA-02: giữ pending_review, không freeze. Cần sửa subset kappa theo random membership (giữ ca khó nằm trong random subset), provenance/hash cho annotation/resume, bỏ fallback codebook/random mặc định ở lượt thật và sửa metadata nguồn thương hiệu.
- Gói 20 mẫu hiện tại là synthetic_practice_pilot; không dùng thời gian/kappa làm kết quả nhãn thật hoặc chốt PLAN-01. Pilot thật cần manifest nguồn/exclusion và thành phần theo DATA_PROTOCOL trước mở lượt.
- DATA-01: phần sửa kỹ thuật đã được nhận trước đó; mapping pilot vẫn unresolved, training chính tiếp tục bị chặn.
- Không phát lệnh pilot chính thức, không merge, không thay phạm vi/protocol đã duyệt. Các task DEV-01/EXT-01/MODEL-PREP-01/02 của D giữ nguyên bằng chứng/trạng thái hiện có.

Nguồn dictionary đã mở đối chiếu: các bài Check Point Q4/2024, Q1/2025, Q2/2025, Q3/2025, Q4/2025 tồn tại. Metadata top_brands trong dictionary chưa khớp danh sách gốc (ví dụ DHL bị đưa vào top Q4/2024 và Twitter vào top Q4/2025). C/B phải lập bảng kiểm nguồn và lý do chọn danh mục chính trước khóa, không đổi bằng hiệu năng mô hình. A review đang là draft có AI hỗ trợ, không đồng nghĩa người gán nhãn đã ký duyệt.


### Đối chiếu lệnh khóa và mở pilot — C 662835f / B ef9409f

Ngày 04/10/2026: đã đọc biên bản B tại ef9409f và bản C mới nhất 662835f. Biên bản B kết luận chưa đủ điều kiện pilot thật, chưa ký codebook/dictionary. Sáu lỗi L-B01–06 có bản sửa một phần; các yêu cầu provenance annotation, resume theo gói/hash, ghép kappa theo sample_id và khóa override random cho lượt thật vẫn chưa được thực hiện ở bản C hiện tại. Sau bổ sung tldextract 5.4.0 và PyArrow 25.0.1 vào môi trường review tạm, 86 tests và 32 subtests đều đạt; không đồng nghĩa các yêu cầu chưa có test đã được giải quyết.

REAL-PILOT-32-V1 có manifest ghi 32 mẫu/20 source-phish/12 source-benign, nhưng blind_view_pilot_real.json và mapping C-only chưa có trong workspace Lead hoặc checkout review. Chưa đối chiếu được byte hash/view thật; không khẳng định đã nghiệm thu dữ liệu. Không đưa raw/mapping có nhãn vào Git hoặc view A/B để khắc phục thiếu bàn giao.

Giữ dictionary/codebook pending_review, ready_for_annotation=false; không đổi dataset_type sang real_pilot_ready, không phát lệnh A/B, không merge hoặc mở training. C bàn giao bản vá, môi trường và view mù qua kênh hạn chế; B review lại đúng commit, sửa encoding và metadata nguồn còn sai trước đề nghị Lead khóa. Giữ điều kiện temporal/as-of và pilot exclusion đã duyệt.


### Đối chiếu biên bản B 3fdfdff — quyết định Lead D

Đã đọc CODEBOOK_REVIEW_B.md tại 3fdfdff. B đã duyệt mã nguồn C; nghiệm thu dữ liệu được B giới hạn ở thiết kế/manifest, chưa kiểm trực tiếp dữ liệu thô C-only. Bản C vẫn là c03306b (mã nguồn 6817d7e). Chạy lại độc lập: 86 tests và 32 subtests đạt.

Chưa ký acceptance.D=approved hoặc chuyển codebook/dictionary sang locked: bảng nguồn của B và top_brands trong dictionary còn sai (DHL ở Q4/2024, PayPal ở Q1/2025, Facebook ở Q3/2025, Twitter ở Q4/2025). File blind_view_pilot_real.json chưa có tại workspace Lead/checkout review, nên chưa xác minh hash 9859fa938ad849bae040d4d78af297bd2794c7d7ad4fdc401a757ef37d986041, cấu trúc và đủ 32 mẫu. Không diễn giải nghiệm thu mã nguồn thành nghiệm thu byte dữ liệu.

Việc tiếp theo: C sửa metadata nguồn theo danh sách chính thức; B cập nhật bảng đối chiếu và xác nhận bản sửa. C bàn giao riêng file view mù cho Lead (không đưa raw/mapping chứa nhãn lên Git hoặc gửi A/B). Lead kiểm hash và schema trước ký, sau đó cập nhật đồng bộ phiên bản/hash codebook, dictionary, manifest và metadata gói. Chốt chặn training do unresolved_source_mapping tiếp tục giữ nguyên. Chưa mở pilot, chưa commit/push/merge.


### Nghiệm thu bản sửa C 94b5d62 — Lead D

Đã lấy commit 94b5d62f4219b53a2a763ffe5d7512497d86446c và kiểm tra diff so với c03306b trong checkout tạm. Có sửa mã nguồn provenance/resume/ghép sample_id/khóa CLI override. Chạy pytest độc lập: 93 tests + 32 subtests đạt.

Probe trên fixture tái hiện ba lỗi còn lại: (1) resume vẫn trả s1 đã hoàn thành khi JSONL cũ thiếu dataset_hash/dataset_id dù phiên yêu cầu gói NEW/hash mới; (2) Kappa vẫn tính 2 mẫu synthetic không dry-run, trộn hai dataset_hash khi hai bên có cùng tập hash; (3) loại trừ miền login.example.co.uk trả True với PSL nhưng False khi thiếu tldextract vì fallback lấy co.uk. Không dùng nhãn thật trong probe.

C cần fail-closed cho provenance/resume thiếu hoặc sai, kiểm codebook_hash/sampling_plan_version; Kappa yêu cầu provenance thống nhất trên từng cặp/toàn bộ tập và tách synthetic khỏi thống kê nghiên cứu; bỏ fallback hai nhãn DNS, thiếu PSL thì báo lỗi. Metadata nguồn dictionary/codebook không được sửa trong commit này; view real32 vẫn chưa bàn giao cho Lead. Chưa khóa codebook/dictionary hoặc ký nghiệm thu real32; training tiếp tục bị chặn. Không sửa nhánh C, không commit/push/merge.


### MODEL-API-EXT-01 — 05/10/2026

DONE cho demo mô phỏng: M0/M3 từ fixture nối API localhost và MV3. Thêm serving/demo_model.py và scripts/run_demo_model_api.py; giữ mock launcher/scenarios, auth/origin/limits/navigation checks. Fit fixture train/validation nhóm tách riêng, seed17, không đọc corpus thật và không mở chốt training. Extension phân biệt mock/synthetic_model, giữ nhãn DEMO và từ chối bundle chưa hỗ trợ. 51 Python tests + 10 Node tests + 12 Chromium smoke checks đạt; chưa đo hiệu quả nghiên cứu. Code tại repo gốc, chưa commit/push. Chưa serialize bundle; bước sau là đóng gói predictor + preprocessing/threshold/metadata và đo runtime trước tích hợp model thật sau nghiệm thu dữ liệu.


### MODEL-BUNDLE-01 — 05/10/2026

DONE phần persistence demo: lưu M0/M3 pipeline và manifest tại artifacts/models/synthetic-demo-v1 (ignored), launcher tải lại không fit; builder chọn output mới, không ghi đè. Loader kiểm checksum/versions/source/threshold trước joblib và metadata predictor sau load. Không load model upload, không đọc corpus thật/mở training chính. 54 Python tests đạt và extension build đạt. Browser smoke cho lần thay đổi này bị chặn bởi cổng 8765 đang có API demo của người dùng; giữ nguyên dịch vụ. Các 12 checks browser trước persistence đã đạt. Code/docs chưa commit/push.


### PERF-DEMO-01 — 05/10/2026

DONE benchmark demo và kiểm lỗi: extension đo client_roundtrip, API timing từng stage, báo cáo 30 lần/pha + 2 warmup trong Chromium/profile/API cổng riêng. p50/p95 URL-only=3.25/3.965ms, content=9.50/10.50ms; loại debounce/render/banner khỏi định nghĩa. artifacts/smoke/latency-report.json có raw timing và metadata bundle; không là bằng chứng nghiên cứu. 55 Python + 11 Node + 14 browser checks đạt. Lượt đầu benchmark chạm rate limit90/phút; cấu hình API riêng300/phút và chạy lại đạt, API người dùng mặc định giữ90. Không ngắt phiên8765 của D, không dùng data thật hoặc mở training. Code chưa commit/push. Bước tiếp theo: parity preprocessing runtime/offline và thử snapshot lớn trên fixture; kết quả thực cần dữ liệu đã nghiệm thu, nhóm độc lập và giao thức đã khóa.


### PARITY-DOM-01 — 05/10/2026

DONE fixture checks: 15 browser smoke checks đạt, gồm DOM lớn~594KB/6000paragraph xử lý được và >1m ký tự bị chặn không gửi/cắt. test:parity đạt6/6 trên DOM rendered giống nguồn; stored_html vs rendered_dom khác ở table repair/nested form/dynamic content, ghi report để nhóm xem trước thực nghiệm thật, chưa tự thay capture protocol/corpus. artifacts/smoke/parity-report.json và browser-report.json bị ignore; input HTML tạm xóa sau test. Không thay pipeline/features/bundle; API user vẫn giữ chạy. Benchmark lần tới có16checks khi bao gồm latency. Code chưa commit/push.


### Bàn giao D để nhóm review — 05/10/2026

Đã gom phạm vi/file/commands/tests/metrics/limits và phân công A/B/C review trong DEVELOPMENT; cập nhật README/CURRENT_TASKS để phản ánh backend fixture và nghiệm thu pilot riêng. Không tạo thêm báo cáo MD, không gộp code/dữ liệu C, không thay đề cương/giao thức; chưa commit/push/merge. output/ của người dùng giữ nguyên ngoài phạm vi bàn giao.

05/10/2026 — D chuẩn bị nhánh review codex/d-demo-integration từ origin/main theo yêu cầu người dùng. Bàn giao scaffold và demo model/API/extension, bundle, parity và runtime tests; giữ repo gốc feat/local-dev-01, không đưa workflow DeepSeek/Claude, dữ liệu hạn chế hoặc artifacts sinh vào commit. Không push/merge main.

05/10/2026 — D bổ sung lựa chọn Python Windows/POSIX và PHISHING_PYTHON cho browser/parity tests, hướng dẫn PowerShell + checklist B trong DEVELOPMENT. Thêm checker input fixture: hash, ID/nhãn/groups/split/exclusion; luôn research_training_allowed=false, không fit. Chưa xác minh Windows thực tế, chưa gộp adapter C; DATA-03/ingestion C vẫn chờ sửa và nghiệm thu. 61 Python và 12 Node tests đạt; giữ nhánh codex/d-demo-integration, không merge main.

05/10/2026 — Theo yêu cầu Lead, tạo develop từ origin/main, merge phần D đã kiểm thử tại 1614d84, chuyển PR #3 sang develop và cập nhật workflow nhánh công việc → develop → main. Main giữ nguyên. DATA-03/ingestion/tool nghiệm thu C tiếp tục PENDING_REVIEW; không merge phần chưa nghiệm thu hoặc mở training thật.

05/10/2026 — SYNTHETIC-REPORT-01 (D): hoàn tất cấu hình fixture và xuất summary JSON/CSV/Markdown tự động trên nhánh codex/synthetic-experiment-report từ develop. Tổng hợp OOF riêng seed; báo counts/recall/FPR/AP, dao động fold/seed, paired group CI cho M3–M2/B-rule/ablation; giữ NA khi thiếu ngưỡng. Run tham chiếu 160 mẫu/40 nhóm, 5 fold × 3 seed, 8 variants và 2.000 bootstrap; 66 Python tests đạt. Artifacts ignored, research_evidence=false; chưa tích hợp dữ liệu C hoặc mở training thật. B kiểm chứng lệnh PowerShell trên Windows theo DEVELOPMENT; kiểm kỹ thuật này không phải gán nhãn hoặc PLAN-01. Gửi PR đích develop để review, không sửa main.
