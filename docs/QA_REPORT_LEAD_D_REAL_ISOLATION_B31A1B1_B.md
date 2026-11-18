# BÁO CÁO THẨM ĐỊNH QA ĐỘC LẬP: GÓI BỔ SUNG KIỂM SOÁT CÁCH LY DỮ LIỆU BẰNG MÃ THẬT TRÊN BASE `b31a1b1` (LEAD D)

- **Mã tài liệu**: `QA-REPORT-LEAD-D-REAL-ISOLATION-B31A1B1-B`
- **Phiên bản**: `1.0` (Thẩm định độc lập riêng cho gói kiểm soát cách ly dữ liệu bằng mã thật do Lead D bàn giao; giữ nguyên toàn bộ các báo cáo QA trước làm dấu vết kiểm toán)
- **Ngày phát hành**: `2026-11-18`
- **Người thực hiện thẩm định độc lập**: Phùng Tấn Minh (**Thành viên B — Annotator B kiêm QA Lead & Nhóm trưởng**)
- **Người bàn giao đối tượng thẩm định**: **Lead D** (Anh Tuấn)
- **Người nhận báo cáo**: **Lead D** và **Thành viên C**
- **Đối tượng bàn giao đã thẩm định**:
  - Tệp gói nén: `lead_d_real_isolation_verification_b31a1b1.zip`
  - Dung lượng gói: `9.651 bytes`
  - Mã băm SHA-256 đo trực tiếp: `0a2d15ffa794c16b4e9bbcaea7b2b62a9c01f473ecd946244add294aa7d34e07` (Khớp tuyệt đối với mã băm Lead D công bố).
  - Base commit áp dụng patch: `b31a1b1c35192a69e8acf8224f17523a4ff56f12` (nhánh `develop` / `origin/codex/extension-banner-toggle`).
  - Tệp bản vá: `isolation_guard_b31a1b1.patch` (`11.215 bytes`, SHA-256: `1149ed79addd106f5678388f9da93057198339bafe54e3774a20eb7911db19ac`).
- **Trạng thái kết luận QA**:
  - **Toàn vẹn tệp gói nén và bảng mã băm các thành phần**: **`PASS`**.
  - **Mã nguồn bản vá (`readiness.py`, `experiment.py`) & loại bỏ `simulate_runplan_validate`**: **`PASS`** (Đã chuyển cờ cách ly thành ID và gọi `RunPlan.validate` thật; chặn mẫu ngoài fixture ngay đầu `fit_fold`).
  - **Bộ kiểm thử hồi quy của nhánh D trên clean checkout (`b31a1b1` + patch)**: **`PASS`** (`95 passed, 0 failed, 0 skipped, 107 subtests passed in 7.97s`).
  - **Kiểm chứng 7 hành vi với fixture tổng hợp độc lập**: **`PASS`**.
  - **Đánh giá phương pháp script `verify_real24.py` & phân định kết quả thực thi của D**: **`PASS`** (Phương pháp hợp thức; B không mở tệp hạn chế và không tự nhận đã chạy trên gói thật để bảo vệ tính mù).
  - **Tích hợp vào nhánh chung của Thành viên C**: **`PENDING`** (Chờ C hợp nhất vào nhánh vận hành chung; kết luận QA tại base D không tự kế thừa cho nhánh C).
- **Trạng thái cổng quản trị hiện hành**: `main_annotation_status="LOCKED"`, `training_blocked=true`, `official_test_used=false` (Tiếp tục duy trì nghiêm ngặt).

---

## I. XÁC ĐỊNH NHIỆM VỤ TRƯỚC KHI LÀM (THEO MỤC 1 `AGENTS.md`)

1. **Mục tiêu**:
   - Thực hiện đúng phần việc của Thành viên B (QA Lead) theo yêu cầu thẩm định độc lập của Lead D:
     1. Khóa đúng đối tượng QA: Kiểm tra tệp `lead_d_real_isolation_verification_b31a1b1.zip`, đối soát dung lượng và SHA-256; kiểm tra tính toàn vẹn và mã băm các tệp thành phần.
     2. Đọc diff của bản vá `isolation_guard_b31a1b1.patch`, xác nhận đã thay thế hoàn toàn `simulate_runplan_validate` bằng `RunPlan.validate` thật, bổ sung kiểm tra cờ cách ly trong `readiness.py` và chặn mẫu ngoài fixture trong `experiment.py`.
     3. Trích xuất clean checkout của đúng base `b31a1b1c35192a69e8acf8224f17523a4ff56f12`, áp dụng patch và chạy toàn bộ suite test của nhánh D (kỳ vọng 95 passed, tách biệt với 446 test nhánh C).
     4. Thiết lập fixture tổng hợp độc lập để kiểm chứng 7 hành vi kỹ thuật then chốt.
     5. Đánh giá script `verify_real24.py`, phân định rõ ràng giữa kết quả thực thi của Lead D trên gói hiệu chuẩn thật và phạm vi kiểm chứng của B; bảo toàn tính mù độc lập của Annotator B.
2. **Đầu vào được phép**:
   - Tệp gói nén: `lead_d_real_isolation_verification_b31a1b1.zip` tại đường dẫn đính kèm.
   - Clean checkout trích xuất từ commit `b31a1b1c35192a69e8acf8224f17523a4ff56f12` tại `scratch/b31a1b1_eval`.
   - Các tệp trong gói: `ISOLATION_VERIFICATION_REPORT.md`, `SHA256SUMS.txt`, `isolation_guard_b31a1b1.patch`, `pytest_full.log`, `real24_verification.json`, `source_hashes.json`, `verify_real24.py`.
   - **Tệp tuyệt đối KHÔNG mở/đọc để bảo vệ tính mù của Annotator B**: Toàn bộ dữ liệu cấp mẫu, nhãn nguồn, HTML thật trong `data/restricted/` hoặc trong gói `e0bb55e8...`.
3. **Đầu ra và tiêu chí đạt**:
   - Biên bản thẩm định QA độc lập `docs/QA_REPORT_LEAD_D_REAL_ISOLATION_B31A1B1_B.md` kèm dung lượng byte, mã băm SHA-256 đo trực tiếp và báo cáo bàn giao 10 mục theo Mục 6 `AGENTS.md`.
4. **Ranh giới**:
   - Chỉ thực hiện phần việc của **Thành viên B (QA Lead)**; không sửa mã của D hay C rồi tự ký QA; không cấp quyền huấn luyện hay mở Main Annotation.
5. **Điều chưa biết**:
   - Bản sửa hiện là working-tree diff trên workspace của Lead D, chưa commit/push lên nhánh Git từ xa; B thẩm định trên môi trường clean checkout cô lập của base `b31a1b1` cộng patch.

---

## II. ĐỐI SOÁT TÍNH TOÀN VẸN GÓI BÀN GIAO VÀ BẢNG MÃ BĂM SHA-256

### 1. Đối soát tệp gói nén:
- Tệp bàn giao: `lead_d_real_isolation_verification_b31a1b1.zip`
- Dung lượng thực tế: `9.651 bytes`
- SHA-256 đo trực tiếp: `0a2d15ffa794c16b4e9bbcaea7b2b62a9c01f473ecd946244add294aa7d34e07`
- Kết luận: **Khớp tuyệt đối 100% với thông báo của Lead D**.

### 2. Đối soát các tệp thành phần bên trong gói (so với `SHA256SUMS.txt`):

| Tệp thành phần trong gói | Dung lượng | SHA-256 đo trực tiếp | Đối soát `SHA256SUMS.txt` |
| :--- | ---: | :--- | :---: |
| `ISOLATION_VERIFICATION_REPORT.md` | `5.330 bytes` | `b87a60090d0e06b068d900481126fb06320da471f10b541c30a9d334f7eb4861` | Khớp |
| `isolation_guard_b31a1b1.patch` | `11.215 bytes` | `1149ed79addd106f5678388f9da93057198339bafe54e3774a20eb7911db19ac` | Khớp |
| `pytest_full.log` | `179 bytes` | `008a287c1a26f68bb299333c696a3f72f4dcbecf39b7afa058b4744903643f94` | Khớp |
| `real24_verification.json` | `421 bytes` | `526a1da866fc36751c13d09b5a7b5a70ab5d005610d934a24056df02ddf706d7` | Khớp |
| `source_hashes.json` | `533 bytes` | `f8071d84410d08031c9e073be795d683d32dbc6deb6862a4b0e8aef11f801259` | Khớp |
| `verify_real24.py` | `5.196 bytes` | `e4e1576b65389b863b2e8631453b4e95042de2af47e5ff5260396f9f8dc37815` | Khớp |
| `SHA256SUMS.txt` | `536 bytes` | `4ec6b4b745426b389945a895b66d7adbc4b18c0df9ba0a6bc700445a60e0a544` | Khớp |

### 3. Đối soát mã băm các tệp sau khi áp dụng patch (chuẩn ngắt dòng Unix LF):
Thành viên B đã trích xuất clean checkout tại commit `b31a1b1c35192a69e8acf8224f17523a4ff56f12`, áp dụng bản vá `isolation_guard_b31a1b1.patch` bằng `git apply`, và đối chiếu với `source_hashes.json`:
- `src/phishing/training/readiness.py`: `1b5d89f985cbbb1a0a691fb38008c7abebb9729251f63d7115d1d42d77df1933` (Khớp LF)
- `src/phishing/training/experiment.py`: `c17f082a7a9554daf24ccfbf5bd2326ad28a0733c379b77c83b9ba8d66cb4f31` (Khớp LF)
- `tests/test_training_readiness.py`: `53d2917c0b80b60d8e967612022a86b0048d129e32196d1b393d742baf7b2450` (Khớp LF)
- `tests/test_training_pipeline.py`: `71bd1f7644b1e80c57e4fea0115e3efc476a8495158200f758a81d8d35bae06e` (Khớp LF)
- `tests/test_label_isolation.py`: `fa3afade69b340a78edf1d7f9e57c33d16414b6859d0ae0ce946753dfa7ad653` (Khớp LF)

---

## III. KẾT QUẢ ĐỐI SOÁT VÀ THẨM ĐỊNH ĐỘC LẬP THEO 5 TRỌNG TÂM

### 1. Thẩm tra nội dung bản vá mã nguồn (`PASS`)

Thành viên B đã đọc chi tiết từng dòng thay đổi trong `isolation_guard_b31a1b1.patch`:

1. **Hàm `row_is_isolated(row)` trong `readiness.py`**:
   - Kiểm tra chặt chẽ 4 cờ cách ly: `excluded_from_model_training`, `excluded_from_model_validation`, `excluded_from_validation`, `excluded_from_official_test`.
   - Nếu cờ xuất hiện, bắt buộc phải có kiểu dữ liệu là boolean thuần túy (`type(row[key]) is not bool` ném `ValueError('Isolation flags must be JSON booleans')`). Ngăn chặn triệt để việc lọt lưới do dùng chuỗi `"False"` hay số nguyên `0, 1`.
   - Nếu `dataset_split` không nằm trong tập hợp hợp lệ `{'train', 'validation', 'test', 'synthetic_fixture_only'}` (ví dụ: `calibration_offline_excluded`), hàm trả về `True`.
   - Trả về `True` nếu bất kỳ cờ cách ly nào có giá trị `True`.
2. **Hàm `load_isolated_ids(path, expected_sha256)` trong `readiness.py`**:
   - Khóa cứng tệp nhãn bằng mã băm `expected_sha256` (64 ký tự hex). Bất kỳ sự sai lệch nào về byte tệp đều bị chặn ngay với thông báo `checksum mismatch`.
   - Hỗ trợ cả hai định dạng `.json` (kiểm tra `object_pairs_hook=unique_keys`) và `.csv` (yêu cầu tiêu đề cột duy nhất, cờ boolean CSV rõ ràng `{'True', 'False', 'true', 'false'}`).
   - Kiểm tra `sample_id` không rỗng, không chứa khoảng trắng thừa, không trùng lặp (`seen.add(sid)`).
   - Yêu cầu bắt buộc phải có đầy đủ siêu dữ liệu cách ly cấp dòng (`dataset_split`, `excluded_from_model_training`, `excluded_from_official_test` và ít nhất một cờ validation).
   - Trả về tập hợp bất biến `frozenset(excluded)` chứa toàn bộ các ID bị cách ly.
3. **Hàm `check_run_plan_isolation(plan, group_by_sample, *, label_artifacts)` trong `readiness.py`**:
   - Yêu cầu truyền danh sách hiện vật nhãn đã khóa `label_artifacts`.
   - Hợp nhất các ID cách ly đọc được từ các tệp và truyền trực tiếp vào phương thức **`plan.validate(group_by_sample, excluded)` thật** của `RunPlan`.
   - **Xác nhận**: Trong toàn bộ gói bản vá này, **hoàn toàn không còn xuất hiện `simulate_runplan_validate`**. Logic kiểm tra được thực hiện bằng chính mã nguồn thật của hệ sinh thái `RunPlan`.
4. **Hàm `check_training_inputs(manifest_path)` trong `readiness.py`**:
   - Bổ sung chốt chặn: `if row_is_isolated(row) or row_is_isolated(labels[sid]): raise ValueError('Isolated sample entered input cohort')`.
   - Đảm bảo mẫu bị cách ly bị chặn nếu xuất hiện ở `index` hoặc `labels`.
5. **Hàm `fit_fold` trong `experiment.py`**:
   - Gọi ngay `assert_fixture_cohort(samples)` tại dòng đầu tiên của hàm.
   - Bất kỳ mẫu nào không thuộc miền `synthetic-domain-` hoặc URL không có đuôi `.fixture.test` đều bị từ chối ngay lập tức trước khi phân tích biến thể mô hình (`variant`) và trước khi gọi `make_pipeline`.

---

### 2. Chạy bộ kiểm thử hồi quy của nhánh D trên clean checkout (`PASS`)

- **Môi trường thực thi**: Clean checkout tại thư mục tạm `scratch/b31a1b1_eval`, Python 3.14.2, pytest 9.1.1 trên Windows.
- **Lệnh chạy**: `python -m pytest -o pythonpath=src tests/ -v`
- **Kết quả thực tế**: **`95 passed, 0 failed, 0 skipped, 107 subtests passed in 7.97s`**.
- **Đối soát với log bàn giao của Lead D (`pytest_full.log`)**:
  - Log của Lead D ghi nhận: `95 passed in 1.87s` (trên Linux/macOS trong môi trường `.venv`).
  - Kết quả B chạy lại độc lập trên Windows đạt chính xác **95 passed, 0 failed, 0 skipped**.
- **Phân định ranh giới bộ test**:
  - Đây là suite 95 bài test của nhánh phát triển D (chuyên trách kiểm tra pipeline huấn luyện, serving demo, đánh giá lỗi và kiểm soát cách ly).
  - **Tuyệt đối không ghép bộ 95 test này với bộ 446 test của nhánh C** (nhánh C chuyên trách pipeline dữ liệu, selection gate, và exclusion registry).

---

### 3. Kiểm chứng 7 hành vi kỹ thuật với Fixture tổng hợp độc lập (`PASS`)

Thành viên B đã tự xây dựng script kiểm thử độc lập sử dụng các fixture nhân tạo (synthetic fixture), thu được kết quả:

1. **Chuyển đổi cờ cách ly từ JSON và CSV thành ID**:
   - Tạo tệp JSON và CSV chứa mẫu hợp lệ `s1` (không cách ly), mẫu `s2` (`dataset_split="calibration_offline_excluded"` và 3 cờ True), mẫu `s3` (`excluded_from_model_training=True`).
   - Cả hai định dạng đều được `load_isolated_ids` nạp chính xác thành `frozenset({'s2', 's3'})`.
2. **Từ chối mẫu cách ly ở cả 3 phân vùng của `RunPlan.validate` thật**:
   - Tạo kế hoạch chạy thử nghiệm với nhóm mẫu kiểm soát (positive control): `check_run_plan_isolation` trả về kết quả hợp lệ `samples: [1, 1, 1]`.
   - Đưa mẫu bị cách ly `s2` vào lần lượt phân vùng `train`, `validation`, và `test`: Cả 3 trường hợp đều bị `RunPlan.validate` thật từ chối với ngoại lệ `ValueError: Pilot/reserved samples entered the run plan`.
3. **Chặn lỗi mã băm, thiếu siêu dữ liệu, ID sai và cờ boolean nhập nhằng**:
   - Sai mã băm SHA-256: Bị chặn với `Isolation artifact checksum mismatch`.
   - Thiếu trường siêu dữ liệu bắt buộc: Bị chặn với `Complete row-level isolation metadata required`.
   - Cờ boolean dạng chuỗi `"False"` trong JSON: Bị chặn với `Isolation flags must be JSON booleans`.
4. **Dữ liệu kiểm soát hợp lệ đi qua**:
   - Tệp manifest demo hợp lệ đi qua hàm `check_training_inputs` thành công, xác nhận cờ `research_training_allowed: False`.
5. **Chặn cờ cách ly trong cả `index` lẫn `labels`**:
   - Khi sửa trường `excluded_from_model_training: True` trong `index.json`: `check_training_inputs` từ chối với `Isolated sample entered input cohort`.
   - Khi sửa trường trong `labels.json`: `check_training_inputs` từ chối với cùng lý do `Isolated sample entered input cohort`.
6. **`fit_fold` từ chối mẫu ngoài fixture trước khi gọi `make_pipeline`**:
   - Thay đổi `group_id` của mẫu thành `research-domain`: Hàm `fit_fold` ném ngoại lệ `ValueError: This handoff is restricted to invented fixture samples`.
   - Sử dụng `unittest.mock.patch` để theo dõi `make_pipeline`: Xác nhận `make_pipeline.assert_not_called()` đạt (mô hình hoàn toàn không được dựng).
7. **Khóa cứng phạm vi nghiên cứu (Research Scope)**:
   - Sửa trường `scope: "research"` trong tệp manifest: `check_training_inputs` lập tức ném ngoại lệ `Research inputs blocked: C adapter and approvals are not integrated`. Kết quả fixture hoàn toàn không cấp quyền huấn luyện nghiên cứu.

---

### 4. Đánh giá Script `verify_real24.py` và phân định kết quả của Lead D (`PASS`)

1. **Đánh giá phương pháp luận của `verify_real24.py`**:
   - Script thực hiện đối soát nghiêm ngặt mã băm của gói nén hiệu chuẩn `e0bb55e8...`, trích xuất trong thư mục tạm, nạp nhãn và đối soát trên `RunPlan` thật và `check_training_inputs`.
   - Script chỉ in ra các chỉ số đếm tổng hợp dạng JSON (`real_runplan_rejections`, `real_readiness_rejections`, `positive_controls`), hoàn toàn không in ra văn bản nhãn, HTML hay định danh mẫu chi tiết.
   - Thiết kế này đạt chuẩn mực ARS và bảo vệ an toàn tính mù của người chấm.
2. **Phân định ranh giới kết quả thực thi của Lead D và phạm vi của QA Lead B**:
   - **Kết quả do Lead D thực hiện và bàn giao** (trên gói hiệu chuẩn `e0bb55e8...` nguyên byte):
     + $24 \text{ ID} \times 2 \text{ định dạng (JSON, CSV)} \times 3 \text{ phân vùng} = 144$ lần gọi `RunPlan.validate` thật đều bị chặn đúng lý do `Pilot/reserved`.
     + $24 \text{ bộ metadata cách ly} \times 3 \text{ vị trí} = 72$ lần gọi `check_training_inputs` đều bị chặn đúng lý do `Isolated sample entered input cohort`.
     + 3 phép kiểm dương tính (positive control) đi qua; 16 mẫu có cờ `binary_model_eligible=true` vẫn bị cách ly tuyệt đối.
     + Số mô hình được fit: đúng bằng 0 (`models_fitted = 0`).
   - **Ranh giới công bố của QA Lead B**:
     + Thành viên B ghi nhận các con số 144 và 72 nêu trên là **kết quả bàn giao do Lead D thực thi**.
     + Thành viên B **chưa mở tệp nén `e0bb55e8...`, không mở nhãn, không mở HTML thật** nhằm bảo toàn tính mù độc lập của Annotator B.
     + Phép kiểm độc lập của B tập trung vào: Đọc diff, đối soát mã băm gói bàn giao, chạy lại toàn bộ suite 95 test trên clean checkout, và kiểm chứng hành vi bằng các fixture tổng hợp.

---

## IV. BẢN KIẾN NGHỊ VÀ CÁC BƯỚC TIẾP THEO

1. **Tích hợp vào nhánh chung của Thành viên C**:
   - Bản vá `isolation_guard_b31a1b1.patch` hiện đang ở dạng working-tree diff trên workspace của Lead D (trên nền base `b31a1b1`).
   - Sau khi Lead D commit/push, Thành viên C cần tích hợp các module này vào nhánh vận hành chung (hiện tại nhánh C `8643f55` chưa có các module training này).
   - **Lưu ý quản trị**: Kết luận QA đạt tại base D này **không tự động chuyển thành chữ ký QA cho nhánh C**. Sau khi C tích hợp, Thành viên B sẽ thực hiện thẩm định hồi quy lại trên đúng commit tích hợp của nhánh C.
2. **Khai báo môi trường**:
   - Khi chạy test trên PowerShell/Windows, cần chú ý khai báo đường dẫn `pythonpath=src` (thông qua cờ `-o pythonpath=src` của pytest hoặc cấu hình trong `pytest.ini`) để tránh lỗi `ModuleNotFoundError`.

---

## V. KẾT LUẬN VÀ TRẠNG THÁI QUẢN TRỊ

1. **Kết luận thẩm định QA độc lập**:
   - Tệp gói nén bàn giao `lead_d_real_isolation_verification_b31a1b1.zip` và toàn bộ mã băm thành phần: **`PASS`**.
   - Thiết kế kỹ thuật bản vá `isolation_guard_b31a1b1.patch` (thay thế giả lập bằng `RunPlan.validate` thật, chặn mẫu ngoài fixture trong `fit_fold`): **`PASS`**.
   - Bộ 95 bài kiểm thử hồi quy của nhánh D trên clean checkout (`b31a1b1` + patch): **`PASS`**.
   - Bộ 7 phép kiểm chứng hành vi với fixture tổng hợp độc lập của B: **`PASS`**.
   - Phương pháp luận script `verify_real24.py` và tính toàn vẹn bảo vệ tính mù: **`PASS`**.
   - Tích hợp vào nhánh chung và kiểm thử liên nhánh: **`PENDING`** (Chờ C thực hiện tích hợp và gửi yêu cầu thẩm định mới).
2. **Trạng thái cổng quản trị hiện hành**:
   - `main_annotation_status = "LOCKED"`
   - `training_blocked = true`
   - `official_test_used = false`
   - Tuyệt đối không coi kết quả thẩm định fixture này là việc cấp quyền huấn luyện nghiên cứu hoặc cấp quyền phát hành Blind View.
