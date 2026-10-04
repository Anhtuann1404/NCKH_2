# Current tasks

Cập nhật 04/10/2026. Sprint khởi động dài hai tuần tính từ ngày nhóm bắt đầu; chưa có ngày bắt đầu chính thức.

## Trạng thái có bằng chứng

- DONE — hướng đề cương được GVHD duyệt: theo xác nhận người dùng.
- DONE — nhóm từ 4 người trở lên: theo xác nhận người dùng, chưa điền tên/ngân sách giờ.
- DONE — kiểm kê URL PhishVN: [kết quả](../data/source_audit/PhishVN_kiem_ke.json), [script](../data/source_audit/kiem_ke_phishvn.py).
- DONE — thử kỹ thuật 20 PhreshPhish: [summary](../data/source_audit/phreshphish/pilot_summary.json). Không phải tập thực nghiệm đã xác minh.
- DONE — bộ tài liệu khởi động và hợp đồng API v0.1.
- DONE — D là người dùng/lead, nhận model và API–extension; phân công owner A/B/C/D ở [TEAM](TEAM.md). A/B/C chưa có họ tên.
- DONE — scaffold DEV-01 của D: preprocessing URL/HTML, URL/DOM/text draft, primitive domain/UGC, CLI fixture, môi trường và 17 unittest; chưa là pipeline đã khóa.
- PENDING_REVIEW — DATA-01: C đã hoàn tất audit date 56 shards (498.255 dòng), strict date parser, exclusion registry (20 pilot samples với trạng thái unresolved mapping), khóa môi trường dữ liệu win32/CPython 3.13; chờ Lead D nghiệm thu.
- PENDING_REVIEW — DATA-02: C đã hoàn tất cập nhật domain matcher dùng chung (ưu tiên UGC không phụ thuộc thứ tự), xử lý forms.office.com và S3/Azure/GCS, sửa Kappa khi Pe=1, cập nhật dictionary_v1.json (SHA-256: `61acff28ad48322ff7d4fc1ff5ef4a1a440cee70651192c0999bac94fea36d28`) và CODEBOOK_V1.md sang trạng thái pending_review; chờ B rà soát và D nghiệm thu.
- TODO — pilot nhãn, phần import/index của C cho DEV-01, dữ liệu chính, mô hình, API và extension.

`TODO` chưa làm; `IN_PROGRESS` đang có công việc thực; `BLOCKED` có phụ thuộc cụ thể; `DONE` có sản phẩm kiểm tra được; `PENDING_REVIEW` đã hoàn thành kỹ thuật kèm bằng chứng, chờ nghiệm thu. Không đánh dấu DONE chỉ vì đã có mô tả.

## Việc tiếp theo theo thứ tự

### START-01 — Chốt người và ngân sách giờ

Status: TODO. Owner: D — lead. Phụ thuộc: không.

Điền tên A/B/C/D, giờ mỗi tuần trong 6–8 tuần gán nhãn, xác nhận D phụ trách model/API–extension và nơi giữ dữ liệu. A/B/C là người khác nhau. Done khi cả nhóm xác nhận phân công và tổng giờ; cập nhật mục đội nhóm trong file này, không sửa đề cương để thay lõi.

### DATA-01 — Khóa nguồn và audit riêng date

Status: PENDING_REVIEW. Owner: C. Phụ thuộc: START-01 để xác định người thực hiện.

Đã hoàn thành toàn diện theo 4 điểm review của Lead D:
1. **Source manifest 56 shards:** [`source_manifest.json`](../configs/source_manifest.json) ghi chi tiết kích thước byte, `source_metadata_lfs_sha256` từ Git-LFS pointer, `locally_verified_sha256: null` (do dùng column projection, minh bạch không tự tuyên bố đã tải raw byte), số dòng từng shard đủ 56 tệp tại pinned revision `eabec4b7a66324b79cc8a0ad856d1731dc26fe1a`. Tổng 498.255 dòng khớp 100% với báo cáo.
2. **Exclusion registry:** [`exclusion_registry.json`](../data/exclusion_registry.json) ghi nhận chi tiết 20 mẫu pilot kỹ thuật; do `rows_api_revision_pinned=false`, trạng thái được ghi nhận là `unresolved_source_mapping` (chưa ánh xạ vị trí shard/offset cụ thể trong git revision khi chưa so khớp byte 1-1). Module [`exclusion.py`](../src/phishing/data/exclusion.py) và bộ kiểm thử [`test_exclusion_registry.py`](../tests/test_exclusion_registry.py) chứng minh 20 mẫu pilot bị chặn 100% khỏi train/val/test.
3. **Strict date parser:** [`date_parser.py`](../src/phishing/data/date_parser.py) kiểm tra toàn chuỗi, từ chối mọi hậu tố rác (loại bỏ lỗi `d_str[:10]`), từ chối ngày lịch sai (2024-02-30). Đã kiểm thử qua 9 unittest tại [`test_date_parser.py`](../tests/test_date_parser.py). Quét lại 100% 498.255 dòng của 56 shards không phát hiện lỗi nào: min `2024-07-02`, max `2025-09-08`, 0 missing.
4. **Khóa môi trường tái lập:** [`data_environment.lock.json`](../configs/data_environment.lock.json) khóa CPython 3.13.14 trên win32, ghi rõ phiên bản pyarrow, huggingface_hub, pytest; phối hợp đồng bộ và không mâu thuẫn với `dev_environment.lock.json` của D.

Bằng chứng: [date_audit_report.json](../data/source_audit/phreshphish/date_audit_report.json), [source_manifest.json](../configs/source_manifest.json), [exclusion_registry.json](../data/exclusion_registry.json), [data_environment.lock.json](../configs/data_environment.lock.json).

### DATA-02 — Khóa danh mục và codebook

Status: PENDING_REVIEW. Owner: C + A/B rà quy tắc, GVHD hỗ trợ. Phụ thuộc: DATA-01.

Đã hoàn thành toàn diện theo 3 điểm review của Lead D:
1. **Domain matcher dùng chung & UGC precedence:** [`domains.py`](../src/phishing/features/domains.py) đảm bảo quy tắc `user_content_hosting` luôn được ưu tiên không phụ thuộc vào thứ tự khai báo trong danh sách; bổ sung xử lý `forms.office.com`, `forms.microsoft.com`, Amazon S3 (virtual-hosted và regional), Azure Blob/Web, Google Cloud Storage `storage.googleapis.com`. Kiểm thử trực tiếp matcher dùng chung với 18 unit tests tại [`test_dictionary_and_annotation.py`](../tests/test_dictionary_and_annotation.py) kiểm tra DNS boundary, chống tấn công giả mạo và chứng minh tính độc lập thứ tự. Khẳng định rõ: quan sát miền không phải là quyết định phân loại an toàn.
2. **Sửa compute_cohens_kappa:** [`annotation/__init__.py`](../src/phishing/annotation/__init__.py) xử lý trường hợp $P_e=1.0$ (hoặc 1 danh mục duy nhất) trả về `kappa = None`, `status = 'undefined_single_class'` và tỷ lệ đồng thuận quan sát $P_o$ riêng biệt, không trả về 1.0; hỗ trợ cờ `is_difficult` để loại bỏ các ca khó khỏi mẫu ngẫu nhiên đo đạc; kiểm tra phát hiện thiếu dữ liệu.
3. **Căn cứ từ điển & Codebook:** [`dictionary_v1.json`](../configs/dictionary_v1.json) (SHA-256: `61acff28ad48322ff7d4fc1ff5ef4a1a440cee70651192c0999bac94fea36d28`) và [`CODEBOOK_V1.md`](CODEBOOK_V1.md) chuyển trạng thái sang `pending_review` (do Thành viên B chưa nhận việc rà soát); làm rõ căn cứ 5 quý Check Point (tập train kết thúc 09/2025, Q4/2025 lấy từ đề cương thiết kế) và quy tắc Temporal as-of dictionary.

Bằng chứng: [dictionary_v1.json](../configs/dictionary_v1.json), [CODEBOOK_V1.md](CODEBOOK_V1.md), [test_dictionary_and_annotation.py](../tests/test_dictionary_and_annotation.py).

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

Status: TODO. Owner: D. Phụ thuộc: đọc API_SPEC; có thể làm song song.

Popup bật/tắt, snapshot sạch, navigation/revision và cảnh báo mock. Done khi chuyển trang không nhận kết quả cũ, service offline hiện chưa đánh giá được. Mock luôn có nhãn rõ; không ghi số đo mock thành hiệu năng mô hình.

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

04/10/2026 — C tiếp thu toàn diện 10 điểm phản biện của Lead D cho DATA-01 và DATA-02:
- DATA-01: Triển khai strict date parser (kiểm toàn chuỗi, chống lỗi d_str[:10], từ chối ngày sai lịch), kiểm kê toàn bộ 56 shards (498.255 dòng train) bổ sung bảng shard-level manifest với source_metadata_lfs_sha256 và locally_verified_sha256: null, hoàn thiện exclusion registry 20 mẫu pilot với trạng thái unresolved_source_mapping kèm bộ lọc và test chứng minh loại trừ 100%, khóa môi trường tái lập data_environment.lock.json trên CPython 3.13/win32.
- DATA-02: Hoàn thiện matcher domain dùng chung với ưu tiên tuyệt đối cho UGC/shared hosting không phụ thuộc thứ tự quy tắc, bổ sung forms.office.com và S3/Azure/GCS, sửa compute_cohens_kappa khi Pe=1 trả về undefined_single_class và tách biệt Po, cập nhật dictionary_v1.json (SHA-256: 61acff28ad48322ff7d4fc1ff5ef4a1a440cee70651192c0999bac94fea36d28) và CODEBOOK_V1.md sang trạng thái pending_review, làm rõ căn cứ 5 quý Check Point và nguyên tắc Temporal as-of dictionary. Toàn bộ 49 unit tests của dự án đạt 100%.
