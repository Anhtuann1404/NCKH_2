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
- DONE (phần C) — import/index dữ liệu cho DEV-01: CorpusRecord chuẩn hóa 11 trường DATA_PROTOCOL.md, to_prepared_snapshot chống rò rỉ nhãn, adapter PhreshPhish & PhishVN, tích hợp ExclusionRegistry, CLI index_corpus.py; 10/10 unittests đạt (181/181 toàn dự án).
- TODO — pilot nhãn (A và B đang thực hiện Pass 1), dữ liệu chính, mô hình, API và extension.

`TODO` chưa làm; `IN_PROGRESS` đang có công việc thực; `BLOCKED` có phụ thuộc cụ thể; `DONE` có sản phẩm kiểm tra được; `PENDING_REVIEW` đã hoàn thành kỹ thuật kèm bằng chứng, chờ nghiệm thu. Không đánh dấu DONE chỉ vì đã có mô tả.

## Việc tiếp theo theo thứ tự

### START-01 — Chốt người và ngân sách giờ

Status: TODO. Owner: D — lead. Phụ thuộc: không.

Điền tên A/B/C/D, giờ mỗi tuần trong 6–8 tuần gán nhãn, xác nhận D phụ trách model/API–extension và nơi giữ dữ liệu. A/B/C là người khác nhau. Done khi cả nhóm xác nhận phân công và tổng giờ; cập nhật mục đội nhóm trong file này, không sửa đề cương để thay lõi.

### DATA-01 — Khóa nguồn và audit riêng date

Status: PENDING_REVIEW. Owner: C. Phụ thuộc: START-01 để xác định người thực hiện.

Đã hoàn thành toàn diện theo 4 điểm review của Lead D:
1. **Source manifest 56 shards:** [`source_manifest.json`](../configs/source_manifest.json) ghi chi tiết kích thước byte, `source_metadata_lfs_sha256` từ Git-LFS pointer, `locally_verified_sha256: null` (do dùng column projection, minh bạch không tự tuyên bố đã tải raw byte), số dòng từng shard đủ 56 tệp tại pinned revision `eabec4b7a66324b79cc8a0ad856d1731dc26fe1a`. Tổng 498.255 dòng khớp 100% với báo cáo.
2. **Exclusion registry & Chốt chặn huấn luyện:** [`exclusion_registry.json`](../data/exclusion_registry.json) ghi nhận chi tiết 20 mẫu pilot kỹ thuật; do `rows_api_revision_pinned=false`, trạng thái được ghi nhận là `unresolved_source_mapping` (chưa ánh xạ vị trí shard/offset cụ thể trong git revision khi chưa so khớp byte 1-1). Định danh mẫu bằng `summary_fingerprint_hash` (mã băm dấu vân tay cấu trúc tóm tắt, không ngộ nhận là băm raw HTML/URL). Module [`exclusion.py`](../src/phishing/data/exclusion.py) triển khai cơ chế phòng vệ chiều sâu: kiểm tra trực tiếp trạng thái ánh xạ và bằng chứng của từng lô; ném lỗi `RuntimeError` chặn cứng huấn luyện chính (hard block trước khi `fit`) bất kể cờ `training_blocked` có bị can thiệp hay không. Kiểm thử tại [`test_exclusion_registry.py`](../tests/test_exclusion_registry.py) xác thực chốt chặn này cùng cơ chế nhận diện theo fingerprint tóm tắt.
3. **Strict date parser:** [`date_parser.py`](../src/phishing/data/date_parser.py) kiểm tra toàn chuỗi, từ chối mọi hậu tố rác (loại bỏ lỗi `d_str[:10]`), từ chối ngày lịch sai (2024-02-30). Đã kiểm thử qua 9 unittest tại [`test_date_parser.py`](../tests/test_date_parser.py). Quét lại 100% 498.255 dòng của 56 shards không phát hiện lỗi nào: min `2024-07-02`, max `2025-09-08`, 0 missing.
4. **Khóa môi trường tái lập & Phụ thuộc:** [`data_environment.lock.json`](../configs/data_environment.lock.json) khóa CPython 3.13.14 trên win32, ghi rõ phiên bản pyarrow, huggingface_hub, pytest. File [`requirements.lock`](../requirements.lock) được xuất chuẩn hóa UTF-8 với Unix LF line endings (không có BOM UTF-16 hay byte NUL), đã kiểm định tương thích qua `pip install --dry-run`. Phối hợp đồng bộ và không mâu thuẫn với `dev_environment.lock.json` của D.

Bằng chứng: [date_audit_report.json](../data/source_audit/phreshphish/date_audit_report.json), [source_manifest.json](../configs/source_manifest.json), [exclusion_registry.json](../data/exclusion_registry.json), [data_environment.lock.json](../configs/data_environment.lock.json).

### DATA-02 — Khóa danh mục và codebook

Status: PENDING_REVIEW. Owner: C + A/B rà quy tắc, GVHD hỗ trợ. Phụ thuộc: DATA-01.

Đã hoàn thành toàn diện theo 3 điểm review của Lead D:
1. **Domain matcher dùng chung & UGC precedence:** [`domains.py`](../src/phishing/features/domains.py) đảm bảo quy tắc `user_content_hosting` luôn được ưu tiên không phụ thuộc vào thứ tự khai báo trong danh sách; bổ sung xử lý `forms.office.com`, `forms.microsoft.com`, Amazon S3 (virtual-hosted và regional), Azure Blob/Web, Google Cloud Storage `storage.googleapis.com`. Kiểm thử trực tiếp matcher dùng chung với 18 unit tests tại [`test_dictionary_and_annotation.py`](../tests/test_dictionary_and_annotation.py) kiểm tra DNS boundary, chống tấn công giả mạo và chứng minh tính độc lập thứ tự. Khẳng định rõ: quan sát miền không phải là quyết định phân loại an toàn.
2. **Sửa compute_cohens_kappa:** [`annotation/__init__.py`](../src/phishing/annotation/__init__.py) xử lý trường hợp $P_e=1.0$ (hoặc 1 danh mục duy nhất) trả về `kappa = None`, `status = 'undefined_single_class'` và tỷ lệ đồng thuận quan sát $P_o$ riêng biệt, không trả về 1.0; hỗ trợ cờ `is_difficult` để loại bỏ các ca khó khỏi mẫu ngẫu nhiên đo đạc; kiểm tra phát hiện thiếu dữ liệu.
3. **Căn cứ từ điển & Codebook:** [`dictionary_v1.json`](../configs/dictionary_v1.json) (SHA-256: `61acff28ad48322ff7d4fc1ff5ef4a1a440cee70651192c0999bac94fea36d28`) và [`CODEBOOK_V1.md`](CODEBOOK_V1.md) chuyển trạng thái sang `pending_review` (do Thành viên B chưa nhận việc rà soát); làm rõ căn cứ 5 quý Check Point (tập train kết thúc 09/2025, Q4/2025 lấy từ đề cương thiết kế) và quy tắc Temporal as-of dictionary.

Bằng chứng: [dictionary_v1.json](../configs/dictionary_v1.json), [CODEBOOK_V1.md](CODEBOOK_V1.md), [test_dictionary_and_annotation.py](../tests/test_dictionary_and_annotation.py).

### LABEL-01 — View mù và pilot có bấm giờ

Status: PENDING_REVIEW (Đã xử lý sự cố pilot V1; V1 bị vô hiệu hóa và đóng băng nguyên trạng; đã xây dựng gói mới REAL-PILOT-32-V2 gồm 32 mẫu sạch kiểm định 3 tầng, manifest V2 ở trạng thái pending_lead_acceptance, exclusion registry cô lập 84 mẫu; sẵn sàng chờ Lead D nghiệm thu trước khi mở gán nhãn). Owner: C tạo view & rào chắn; A/B đọc độc lập 100% thủ công không dùng AI. Phụ thuộc: DATA-02.

Đã hoàn thành toàn diện phần việc của Thành viên C (bao gồm xử lý sự cố pilot V1 do A thừa nhận dùng AI và 20 mẫu trùng tập dượt):
1. **Đóng băng nguyên trạng và vô hiệu hóa REAL-PILOT-32-V1:**
   - Cập nhật [`configs/pilot_manifest.json`](../configs/pilot_manifest.json) sang `status: "invalidated"`, `ready_for_annotation: false`, bổ sung `invalidation_metadata`.
   - Giữ nguyên toàn bộ tệp nhãn của A/B, blind view và logs của V1 để phục vụ kiểm toán khoa học; loại bỏ vĩnh viễn khỏi việc tính Cohen's Kappa hoặc nghiệm thu PLAN-01.
2. **Xây dựng gói pilot mới REAL-PILOT-32-V2:**
   - 32 mẫu thực tế độc lập (20 phishing, 12 benign).
   - Kiểm định đối chiếu 3 tầng (URL, raw HTML byte SHA-256, domain group eTLD+1): 0 trùng URL, 0 trùng HTML, 0 trùng domain group với V1 và tập dượt; 32 domain groups độc lập hoàn toàn.
   - Script tạo gói: [`build_real_pilot_v2.py`](../scripts/data/build_real_pilot_v2.py).
3. **Mù hóa tuyệt đối và bảo mật nguồn gốc:**
   - Blind view [`data/annotations/blind_view_pilot_real_v2.json`](../data/annotations/blind_view_pilot_real_v2.json) (SHA-256: `b5249858c2dfe8531f5d4f8ccca5ef70d6f107f882d5853117ca1eec0e80c48b`) ẩn 100% nhãn nguồn, target tổ chức, domain group.
   - Restricted source mapping [`data/raw/pilot_v2/source_mapping.json`](../data/raw/pilot_v2/source_mapping.json) lưu trữ cục bộ bảo mật cho C và Lead D.
   - Manifest V2 [`configs/pilot_manifest_v2.json`](../configs/pilot_manifest_v2.json) khóa ở trạng thái `pending_lead_acceptance`, `ready_for_annotation: false`, `acceptance: {"D": "pending", "B": "pending"}`.
4. **Cô lập dữ liệu trong Exclusion Registry:**
   - Cập nhật [`data/exclusion_registry.json`](../data/exclusion_registry.json) bổ sung entry `EXCL-PILOT-02`, nâng tổng số mẫu cô lập lên 84 (20 kỹ thuật + 32 V1 + 32 V2), khóa cứng huấn luyện (`training_blocked: true`).
5. **Tài liệu và Kiểm thử:**
   - Báo cáo sự cố: [`docs/PILOT_INCIDENT_REPORT.md`](PILOT_INCIDENT_REPORT.md).
   - Báo cáo bàn giao V2: [`docs/BAO_CAO_SU_CO_VA_BAN_GIAO_PILOT_V2.md`](BAO_CAO_SU_CO_VA_BAN_GIAO_PILOT_V2.md).
   - Bộ kiểm thử hồi quy [`tests/test_pilot_v2.py`](../tests/test_pilot_v2.py): 6/6 tests passed. Toàn bộ dự án đạt 209/209 tests passed (100%).


### PLAN-01 — Khóa quy mô và kế hoạch audit

Status: TODO. Owner: D + A/B/C. Phụ thuộc: LABEL-01.

Áp dụng quy tắc 2.000→1.200 nếu trung bình >5 phút/phishing hoặc thiếu giờ; nếu vẫn quá tải thì ghi quy mô thấp hơn trước kết quả. Khóa mẫu 30% ngẫu nhiên, audit lớp ~200 và tiêu chí hard benign. Done khi có sampling plan, seed, giờ dự phòng và quyết định cỡ mẫu.

### DEV-01 — Scaffold parser/features và môi trường

Status: PENDING_REVIEW (C đã hoàn tất phần import/index; D đã hoàn tất phần scaffold và demo). Owner: D (preprocessing/features/serving); C (import/index dữ liệu). Phụ thuộc: có thể chuẩn bị bằng fixture trước DATA-02.

Tạo môi trường, khóa dependency, module preprocessing và fixture domain/UGC/HTML không có nội dung thật. Done khi fixture chứng minh không thực thi HTML, không fetch mạng, không dùng labels/metadata làm features. Chưa huấn luyện tập chính ở bước này.

**Bằng chứng phần D (04/10/2026):** [preprocessing](../src/phishing/preprocessing/__init__.py), [features](../src/phishing/features/__init__.py), [domain rules](../src/phishing/features/domains.py), [CLI](../scripts/inspect_snapshot.py), [tests](../tests/test_preprocessing.py), [domain tests](../tests/test_domain_rules.py), [fixture](../tests/fixtures/synthetic_login.html), [environment](../configs/dev_environment.lock.json). 17 tests đạt và CLI chạy bằng CPython 3.14.6; lệnh ở DEVELOPMENT. Version dev-0, chưa fit TF-IDF/mô hình, chưa phân nhóm eTLD+1 và chưa kiểm parity DOM trình duyệt.

**Bằng chứng phần C (05/10/2026):** [loader](../src/phishing/data/loader.py), [CLI index_corpus](../scripts/data/index_corpus.py), [tests](../tests/test_loader.py). Đạt 12/12 unittests (tổng dự án 194/194 passed):
1. **Chốt loại trừ pilot đóng kín:** Không cho phép nạp real data nếu thiếu `ExclusionRegistry` (chỉ cho phép khi có cờ tường minh `--allow-unverified-fixture` dành cho fixture kiểm thử). `to_prepared_snapshot()` ném `ValueError` ngay khi gặp mẫu bị đánh dấu loại trừ, chặn đứng 100% rò rỉ vào feature extractor của D. Cung cấp hàm `filter_eligible_records` và `join_verified_labels_and_filter_eligible` để sàng lọc mẫu hợp lệ trước split/fit. Khóa trạng thái trong manifest: `ready_for_training=False`, `training_readiness_status="audit_only_training_blocked"`.
2. **Ánh xạ nhãn chặt chẽ theo schema:** Nhãn rỗng/thiếu được gán `missing_source_label`, nhãn ngoài phạm vi phân loại (malware, defacement trong PhishVN) được gán `out_of_scope_label`, tuyệt đối không tự ý chuyển thành benign. Bảo toàn thông tin `source_tier` (gold/silver/bronze) và `source_sub_source` của PhishVN.
3. **ID ổn định theo shard/offset và an toàn đa shard:** ID ràng buộc định danh shard và row offset (`PP-{shard}-R{row:06d}`, `PVN-{file}-R{row:06d}`), không phụ thuộc thứ tự xử lý. Hỗ trợ chạy đa shard qua `--shards` và `--source-manifest`. CLI có cơ chế bảo vệ chống ghi đè: từ chối chạy vào thư mục output đã có artifacts trừ khi có cờ `--overwrite`. Xử lý streaming tuần tự theo batch, không giữ toàn bộ raw HTML trong RAM.
4. **Kiểm tra Checksum và nguồn gốc dữ liệu:** Tính toán SHA-256 từ nội dung HTML thực tế; phát hiện mismatch và tự động đánh dấu loại trừ (`html_sha256_mismatch`). Đối chiếu shards với `source_manifest.json`. Ghi nhận đầy đủ mã băm SHA-256 của các tệp nguồn, phiên bản adapter (`2.0.0`), exclusion registry SHA-256 trong manifest.
5. **Grouping tenant chuẩn xác từ unredacted URL:** Trích xuất `group_id` từ URL chuẩn tắc ban đầu trước khi che mờ query values với `_redacted_`, đảm bảo phân biệt chính xác tenant của forms.office.com (`tenant:forms.office.com:id=...`) giữa các tenant khác nhau, trong khi `normalized_url` ở snapshot vẫn che query values.
6. **Tách biệt rõ ràng Technical Index và Restricted Vault:** `corpus_index.jsonl` chỉ chứa `locator`, `normalized_url`, `group_id`, `html_sha256`... tuyệt đối không chứa `raw_url`, `source_label`, `target`. Kho `restricted_vault.jsonl` lưu riêng biệt raw URLs và nhãn mặt đất. Cung cấp hàm `reconstitute_html_from_locator` đọc lại HTML chính xác từ shard và kiểm tra mã băm.
7. **Bảo toàn Date metadata và Capture mode:** Phân định rõ 3 trạng thái ngày `valid` / `missing` / `invalid` (ngày sai lịch 2024-02-30 đánh dấu `invalid`). Bảo toàn `capture_mode` (`rendered_dom` không bị hạ cấp thành `stored_html`).

### DATA-03 — Engine phân chia Grouped 5-Fold & Temporal Split

Status: PENDING_REVIEW. Owner: C. Phụ thuộc: DATA-01, DATA-02.

Đã hoàn thành toàn diện và xử lý triệt để tất cả các điểm phản biện/probe của Lead D:
1. **Đối chiếu Pilot View Mù Chặt Chẽ & Chuẩn Hóa Cross-Platform:** [`evaluate_kappa.py`](../scripts/evaluate_kappa.py) bắt buộc tệp blind view tồn tại (ném `FileNotFoundError` nếu thiếu hoặc sai đường dẫn, không dùng `except: pass`). Xác thực mã băm byte SHA-256 thực tế của view mù với `blind_view_sha256` trong manifest. Kiểm tra cấu trúc view có đủ 32 ID duy nhất và tính `expected_sample_content_hashes` cho từng mẫu để đối chiếu 1-1 với bản ghi của rater A và B (lỗi bất kỳ mẫu nào dừng ngay lập tức). Chuẩn hóa đường dẫn tương đối dùng POSIX forward slash (`/`) đảm bảo tương thích tuyệt đối trên cả macOS, Linux và Windows.
2. **Khóa Cố Định Tập Mẫu Tính Kappa (Chống Sửa Đổi Random Subset):** [`evaluate_kappa.py`](../scripts/evaluate_kappa.py) đối chiếu cờ `random_subset` của từng bản ghi với view mù và kế hoạch đã khóa. Với pilot full-overlap (32 mẫu), bắt buộc tất cả 32 mẫu phải hợp lệ; chặn đứng hành vi sửa `random_subset=False` để giảm tập tính xuống 31/32 mẫu. Kiểm tra xác nhận `kappa_class.sample_count == 32` và `kappa_org.sample_count == 32`.
3. **Công Bố Atomic Có Backup & Rollback Toàn Diện Khi Gặp Lỗi:** [`generate_splits.py`](../scripts/data/generate_splits.py) sinh và kiểm định toàn bộ artifacts trong thư mục staging tạm (`.staging_<output_dir>_<uuid>`). Trước khi công bố sang `output_dir`, hệ thống tự động sao lưu toàn bộ run cũ sang `.backup_<output_dir>_<uuid>`. Nếu xảy ra lỗi ở bất kỳ bước nào trong lúc chuyển file (kể cả lỗi ngắt quãng ở file thứ 2 do filesystem hoặc probe), cơ chế rollback lập tức xóa các file dở dang và khôi phục nguyên vẹn 100% run cũ từ backup, ngăn chặn hoàn toàn việc mất mát hoặc trộn lẫn artifact.
4. **Kiểm Định Lớp Nhị Phân (Phishing vs Benign) Cho Cả Temporal Split:** [`splits.py`](../src/phishing/data/splits.py) khóa cứng mục tiêu bài toán nhị phân `target_classes = ["phishing", "benign"]`. Tập dữ liệu chỉ chứa nhãn ngoài phạm vi (như `malware`, `defacement`, `unknown`) sẽ bị đánh dấu `status = "not_evaluable"` trên toàn bộ train, validation, test và overall status (đồng bộ với grouped split).
5. **Bộ Kiểm Thử Tự Chứa (Hermetic) Trên Clean Checkout:**
   - [`tests/test_evaluate_kappa.py`](../tests/test_evaluate_kappa.py): Toàn bộ unit test pilot sử dụng fixture tự sinh độc lập và truyền trực tiếp `--pilot-manifest` của fixture vào câu lệnh CLI, loại bỏ hoàn toàn việc fallback về đường dẫn mặc định chứa dữ liệu hạn chế, bảo đảm 100% pass trên checkout sạch.
   - Thêm integration test có `@pytest.mark.skipif` cho kiểm định manifest mặc định khi có file thật.
   - Bổ sung cấu hình `addopts = --capture=sys` trong [`pytest.ini`](../pytest.ini) để bảo đảm stream capture an toàn trong bộ nhớ RAM, chống lỗi cạn dung lượng đĩa hệ thống.
6. **Bằng chứng kiểm thử:** Đạt 34/34 tests tại [`test_splits.py`](../tests/test_splits.py) (bao gồm test rollback khi lỗi chuyển file và test temporal với malware/defacement), 15/15 tests tại [`test_evaluate_kappa.py`](../tests/test_evaluate_kappa.py). Toàn bộ dự án đạt 203/203 tests pass (100%).

Bằng chứng: [grouping.py](../src/phishing/data/grouping.py), [splits.py](../src/phishing/data/splits.py), [generate_splits.py](../scripts/data/generate_splits.py), [evaluate_kappa.py](../scripts/evaluate_kappa.py), [test_splits.py](../tests/test_splits.py), [test_evaluate_kappa.py](../tests/test_evaluate_kappa.py).

### EXT-01 — Khung MV3 và mock API

Status: TODO. Owner: D. Phụ thuộc: đọc API_SPEC; có thể làm song song.

Popup bật/tắt, snapshot sạch, navigation/revision và cảnh báo mock. Done khi chuyển trang không nhận kết quả cũ, service offline hiện chưa đánh giá được. Mock luôn có nhãn rõ; không ghi số đo mock thành hiệu năng mô hình.

## Đội nhóm cần điền

- A — họ tên: Trần Hồng Khải (nhánh codex/member-a-preparation); giờ/tuần: 49 giờ/tuần (đã xác nhận trong docs/MEMBER_A.md).
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
- DATA-01: Triển khai strict date parser (kiểm toàn chuỗi, chống lỗi d_str[:10], từ chối ngày sai lịch), kiểm kê toàn bộ 56 shards (498.255 dòng train) bổ sung bảng shard-level manifest với source_metadata_lfs_sha256 và locally_verified_sha256: null, hoàn thiện exclusion registry 20 mẫu pilot với trạng thái unresolved_source_mapping kèm bộ lọc và test chứng minh loại trừ bằng summary fingerprint, khóa môi trường tái lập data_environment.lock.json trên CPython 3.13/win32.
- DATA-02: Hoàn thiện matcher domain dùng chung với ưu tiên tuyệt đối cho UGC/shared hosting không phụ thuộc thứ tự quy tắc, bổ sung forms.office.com và S3/Azure/GCS, sửa compute_cohens_kappa khi Pe=1 trả về undefined_single_class và tách biệt Po, cập nhật dictionary_v1.json (SHA-256: 61acff28ad48322ff7d4fc1ff5ef4a1a440cee70651192c0999bac94fea36d28) và CODEBOOK_V1.md sang trạng thái pending_review, làm rõ căn cứ 5 quý Check Point và nguyên tắc Temporal as-of dictionary.

04/10/2026 — C giải quyết triệt để 3 điểm phản biện bổ sung của Lead D trước khi nghiệm thu:
1. Đổi `sample_content_hash` -> `summary_fingerprint_hash` trong schema, code và tests để phản ánh đúng bản chất băm thống kê cấu trúc tóm tắt, không ngộ nhận là băm raw HTML/URL; giữ nguyên trạng thái `unresolved_source_mapping`; sửa các câu "chặn 100% mẫu thật" trong tài liệu; chuẩn bị quy tắc băm canonical cố định khi có bản pilot thô.
2. Phòng vệ chiều sâu cho chốt chặn huấn luyện: `assert_training_allowed()` kiểm tra trực tiếp trạng thái ánh xạ (`mapping_status == 'resolved'` và `rows_api_revision_pinned is True`) của từng lô loại trừ, bắt buộc chặn huấn luyện ngay cả khi cờ `training_blocked` bị sửa thành `False`; bổ sung test tình huống mâu thuẫn này.
3. Xuất chuẩn hóa `requirements.lock` sang UTF-8 thuần với Unix LF line endings (loại bỏ hoàn toàn BOM UTF-16 và byte NUL), đã kiểm định thành công qua `pip install --dry-run`. Toàn bộ 54 unit tests của dự án đạt 100% pass.

04/10/2026 — C hoàn thành triển khai công cụ và dữ liệu cho Task LABEL-01:
- Module `blind_view.py`: Bóc tách văn bản và cấu trúc an toàn, loại bỏ 100% script/iframe/inline events, hàm `assert_no_label_leak` kiểm tra đệ quy chống rò rỉ nhãn nguồn/target/score.
- Schema `AnnotationRecord`: Chuẩn hóa 100% taxonomy theo `CODEBOOK_V1.md`, xác thực enum nghiêm ngặt, tích hợp đo thời gian `seconds_spent`. Cung cấp file mẫu `annotation_record_template.json`.
- Gói dữ liệu `blind_view_pilot.json`: 20 mẫu pilot mù an toàn đại diện đa dạng các loại hình dịch vụ.
- Công cụ CLI `annotate_cli.py`: Hỗ trợ gán nhãn có bấm giờ tự động, tương thích đa nền tảng UTF-8, lưu JSONL tức thời và hỗ trợ resume. Đạt 65/65 unit tests (100% pass). Sẵn sàng bàn giao cho Thành viên A và B.

05/10/2026 — C hoàn thành triển khai Task DATA-03 (Grouped 5-Fold & Temporal Splitting Engine):
- Trích xuất `group_id` offline qua `tldextract` (eTLD+1 kèm PSL private domains) và tenant rules cho SharePoint, Google Sites, Office Forms, S3, Azure Blob, Firebase, GitHub Pages, Vercel, Netlify.
- Xây dựng thuật toán phân chia Grouped 5-Fold CV với 3 seeds (17, 42, 2026), bảo đảm 100% không rò rỉ group giữa các fold, tích hợp inner validation split bên trong outer train để phục vụ chọn operating threshold độc lập.
- Xây dựng thuật toán phân chia Temporal Split 60/20/20 theo ngày lịch nguyên vẹn, tự động loại trừ bản ghi muộn trùng nhóm sớm (`purge_overlapping_groups=True`).
- Viết công cụ CLI `generate_splits.py` và 15 unit tests tại `test_splits.py`. Toàn bộ 160/160 tests của dự án đạt 100% pass.

05/10/2026 — C hoàn thành triển khai thành phần Data Ingestion & Indexing Engine cho Task DEV-01:
- Module `src/phishing/data/loader.py`: Chuẩn hóa 11 trường bản ghi nghiên cứu theo `DATA_PROTOCOL.md`, tách biệt `to_index_dict()` không lưu raw HTML trong index; hàm `to_prepared_snapshot()` chuyển giao dữ liệu an toàn cho D với bảo đảm tuyệt đối không rò rỉ nhãn nguồn, mục tiêu hay metadata; tích hợp chốt chặn `ExclusionRegistry`.
- Hỗ trợ đa nguồn: Viết adapter cho cả PhreshPhish Parquet shards và PhishVN CSV/ZIP, kèm scheme fallback xác định cho URL và strict date parser.
- Viết CLI `scripts/data/index_corpus.py` hỗ trợ đa nền tảng UTF-8, xuất `corpus_index.jsonl` và `index_manifest.json` ghi nhận đầy đủ mã băm SHA-256.
- Bổ sung 10 unit tests tại `tests/test_loader.py`. Toàn bộ dự án đạt 181/181 unit tests pass (100%). Sẵn sàng bàn giao cho Lead D.
