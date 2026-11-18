# BÁO CÁO KIỂM TOÁN NGUỒN TỔNG HỢP SHARD TRAIN-001 (BẢN ĐÍNH CHÍNH TRÌNH LEAD D)

**Căn cứ phê duyệt:** Quyết định 1 của Lead D (commit `123799803100f8ab4662d94cab76add125df9201`)  
**Ý kiến chỉ đạo đính chính:** Thông báo rà soát của Lead D (18/11/2026)  
**Người thực hiện:** Thành viên C (Data Pipeline Owner & Thư ký Kiểm toán)  
**Thời điểm lập:** 18/11/2026 16:40 (UTC+7)  
**Commit tham chiếu:** `cfc3bc7` (Mã nguồn kiểm nguồn & manifest) và `ee921e0` (Bộ kiểm thử hồi quy)  
**Nhánh Git:** `feat/c-calibration-v1-1-4-adjudication`

---

## I. ĐÍNH CHÍNH NGƯỠNG PHÁT HIỆN TƯƠNG ĐỒNG TEMPLATE

Theo đúng triển khai mã nguồn tại `src/phishing/data/template_similarity.py` (dòng 152–171), tiêu chí đánh dấu tương đồng template bao gồm hai nhánh độc lập:
1. **Nhánh 1 (SimHash đơn thuần):** Khoảng cách Hamming SimHash 64-bit $\le 10$ (`dist <= self.max_allowed_simhash_distance`).
2. **Nhánh 2 (DOM Jaccard kết hợp SimHash gần):** Độ tương đồng thẻ DOM Jaccard $\ge 0.85$ (`jaccard >= self.max_allowed_dom_jaccard`) **ĐỒNG THỜI** khoảng cách Hamming SimHash $\le 12$ (`dist <= 12`).

**Đính chính phân loại số liệu:**
- **840 trường hợp** bị chặn tại Cổng 3 được định danh chính xác là **“bản ghi bị loại theo tiêu chí tương đồng template”** (`reject_gate3_template_clone`).
- Tiêu chí này là bộ lọc heuristic cấu trúc nhằm đảm bảo tính phân tán mẫu của corpus, **chưa chứng minh các trang web này thuộc cùng một phishing kit hay có cùng nguồn gốc tác giả**.

---

## II. KẾT LUẬN ĐO LƯỜNG VỀ 1.232 ỨNG VIÊN HỢP LỆ TRƯỚC CỔNG 4

Tuân thủ nghiêm cẩn kỷ luật Academic Research Skills (ARS), Thành viên C ghi nhận đúng mức kết quả đã đo đạc thực tế, loại bỏ mọi nhận định chủ quan:
1. **Toàn vẹn tệp nguồn:** Mã băm byte thực tế của shard `train-001.parquet` trên đĩa được C tự đo và ghi nhận khớp tuyệt đối 100% với mã băm Git-LFS pointer trong `source_manifest.json` (`locally_verified`).
2. **Số lượng ứng viên vượt qua bộ lọc:** Có đúng **1.232 ứng viên vượt qua các bộ lọc đang triển khai** (Cổng 0, Cổng 1, Cổng 2, Cổng 3), trước Cổng 4.
3. **Tiền xử lý:** Có **0 bản ghi bị loại với mã `reject_gate2_preprocessing_error`** trong lượt chạy này.
4. **Trạng thái Quota:** Kết quả ghi nhận chính xác theo nhật ký kiểm toán JSON:
   - `meets_quota_target = true`
   - `vetting_status = "vetted_meets_quota"`
5. **Ranh giới khoa học:** Kết quả kiểm nguồn chỉ xác nhận **đủ số lượng ứng viên hợp lệ sau các lớp lọc kỹ thuật**; bản chất nhãn (benign / phishing) và đối tượng mạo danh của các ứng viên này hoàn toàn **chưa được xác định và đang chờ gán nhãn độc lập mù đôi** bởi Đánh giá viên A và B.

---

## III. BẰNG CHỨNG LẦN CHẠY THỰC TẾ & BẢNG MÃ BĂM ĐỐI SOÁT

### 1. Thông số môi trường và lệnh thực thi:
- **Hệ điều hành:** Windows 11 (build 26100)
- **Môi trường Python:** Python 3.13.14 (x64)
- **Thư viện phụ thuộc:** `pyarrow` 25.0.1, `pandas` 3.0.5, `tldextract` 5.4.0, `requests` 2.31.0, `pytest` 7.4.0
- **Lệnh thực thi runner nguyên bản:**
  ```bash
  python scripts/data/run_main_selection.py \
    --shard-path data/raw/phreshphish/data/train-001.parquet \
    --source phreshphish \
    --revision eabec4b7a66324b79cc8a0ad856d1731dc26fe1a \
    --min-date 2024-10-01 \
    --max-date 2025-09-08 \
    --quota 100 \
    --vetting-only \
    --output-dir data/source_audit/phreshphish/train_001_vetting
  ```

### 2. Bảng đối soát mã băm SHA-256 các hiện vật đầu vào và đầu ra:

| Hiện vật kiểm toán | Đường dẫn tệp | Dung lượng | Mã băm SHA-256 | Ghi chú kiểm toán |
| :--- | :--- | :---: | :--- | :--- |
| **Shard nguồn Parquet** | `data/raw/phreshphish/data/train-001.parquet` | 322.018.201 bytes | `260cb9c93299f6b244d48321fe115523159770f4e73446b382473628c6e81d74` | Đo trên đĩa, khớp Git-LFS pointer |
| **Source Manifest (Trước)** | `configs/source_manifest.json` (@`1237998`) | 34.671 bytes | `50fa39d58325e4645b76886e519dd5fbaca31db234d8c70eb95a4eeb608e8eb0` | Trạng thái `metadata_only` |
| **Source Manifest (Sau)** | `configs/source_manifest.json` (@`cfc3bc7`) | 34.719 bytes | `dbbc9746416ccbdb8d19c6e2889c801376be17f2f2cfb61dbd4e98fe8393f5d7` | Cập nhật `locally_verified` cho shard 1 |
| **Exclusion Registry** | `data/exclusion_registry.json` | 107.712 bytes | `aee8c4f398e5b74240501d67e373434e80cca2f1395c6dcab22ad8d3507ce9bc` | 246 mục khai báo / 226 cặp duy nhất |
| **Cam kết hạn chế 1** | `pilot_batch1_recovery_dossier_restricted_v4.json` | Hồ sơ hạn chế | `17f71f23c2314ebf9c36a0a07f9fe21fe56aa18efec682b75f7ec06baf196171` | Cam kết `EXCL-PILOT-01` (20 mẫu) |
| **Cam kết hạn chế 2** | `clean_calibration_exclusion_mapping_c_32.json` | Hồ sơ hạn chế | `67326e80b2a6f9cb7356450a31fe15054a1193412a8ed0576ea2972f1801a805` | Cam kết Lô 10 (32 mẫu) |
| **Vetting Audit JSON (Ra)** | `data/source_audit/phreshphish/train_001_vetting/source_vetting_audit_manifest.json` | 7.774 bytes | `0a96bd7ac3e799a490088c227474a4ed0141450e92ae4286d37bd608a464fdf5` | Nhật ký số đếm và lý do loại trừ |

### 3. Log thực thi kiểm nguồn nguyên bản:
```
  [Cổng 3] Tiến độ: 200/2321 (Đã chọn: 161)
  [Cổng 3] Tiến độ: 400/2321 (Đã chọn: 293)
  [Cổng 3] Tiến độ: 1000/2321 (Đã chọn: 619)
  [Cổng 3] Tiến độ: 1200/2321 (Đã chọn: 715)
  [Cổng 3] Tiến độ: 1400/2321 (Đã chọn: 819)
  [Cổng 3] Tiến độ: 1600/2321 (Đã chọn: 918)
  [Cổng 3] Tiến độ: 2000/2321 (Đã chọn: 1091)
  [Cổng 3] Tiến độ: 2200/2321 (Đã chọn: 1175)
  [Cổng 3] Tiến độ: 2321/2321 (Đã chọn: 1232)
✅ KIỂM NGUỒN (VETTING ONLY) THÀNH CÔNG!
Số lượng ứng viên hợp lệ trước Cổng 4: 1232
Chỉ tiêu quota yêu cầu: 100
Đạt chỉ tiêu quota: CÓ
Chi tiết số đếm qua từng cổng:
  • gate_0_in: 5780
  • gate_0_out: 5780
  • gate_1_in: 5780
  • gate_1_out: 2752
  • gate_2_in: 2752
  • gate_2_out: 2321
  • gate_3_in: 2321
  • gate_3_out: 1232
```

### 4. Đối soát kết quả kiểm thử tự động toàn diện:
- **Lệnh chạy:** `python -m pytest tests/`
- **Kết quả tại commit `cfc3bc7`:** **439 passed, 2 skipped, 0 failed, 1 warning** trong 60.00s.
- **Danh tính 2 ca test bị skipped:**
  1. `tests/test_pilot_v2.py::TestPilotIncidentAndV2Package::test_strict_three_tier_deduplication_between_v2_and_previous`
  2. `tests/test_pilot_v2.py::TestPilotIncidentAndV2Package::test_exclusion_registry_contains_both_v1_and_v2`  
  *(Lý do: Hai ca test này yêu cầu hiện vật lịch sử Pilot V1 đã được cách ly khỏi cây làm việc chính).*
- **Đính chính danh xưng test:** Cụm từ "41/41 test Exclusion Registry" trong báo cáo trước được đính chính chuẩn xác là **41 ca test thuộc tệp `tests/test_pilot_batch1_exclusion.py`** (chuyên trách kiểm tra tính toàn vẹn của 5 cổng chọn mẫu Selection Gate và Exclusion Registry).
- **Kết quả sau khi bổ sung bài test hồi quy (commit `ee921e0`):** **446 passed, 2 skipped, 0 failed** trong 121.51s.

---

## IV. BỘ KIỂM THỬ HỒI QUY CHO HAI THAY ĐỔI MÃ TẠI COMMIT `cfc3bc7`

Thành viên C (kết hợp phân tích chuyên sâu qua Mô hình Duo / DeepSeek Bridge) đã xây dựng tệp kiểm thử hồi quy độc lập tại [`tests/test_selection_gate_cfc3bc7_regression.py`](file:///d:/nguyen%20thang/NCKH/NCKH_2/tests/test_selection_gate_cfc3bc7_regression.py) gồm 7 ca test chuyên biệt:

### 1. Nhóm kiểm hồi quy Ngày (Gate 1 Date Handling):
- `test_parquet_pyarrow_date32_roundtrip_boundaries`: Tạo fixture Parquet thật với kiểu `pa.date32()`, đọc qua `to_pandas()` thành `datetime.date`. Kiểm tra 2 ngày biên `2024-10-01` và `2025-09-08` được nhận (`passed`); 2 ngày sát ngoài biên `2024-09-30` và `2025-09-09` bị loại (`reject_date_before_min`, `reject_date_after_max`).
- `test_reject_string_with_garbage_suffixes_and_time`: Kiểm tra chuỗi ngày có hậu tố rác (`"2024-10-01T00:00:00"`, `"2024-10-01-extra"`, `"2024-10-01xyz"`, sai định dạng `"01/10/2024"`) đều bị từ chối fail-closed với mã `reject_invalid_date_format`.
- `test_handle_datetime_object_and_missing_values`: Đối tượng `datetime` có giờ (`datetime(2024, 10, 1, 14, 30, 0)`) bị từ chối với mã `reject_invalid_date_format` để chống lệch múi giờ; các giá trị thiếu (`None`, khoảng trắng `"   "`, thiếu trường `"date"`) bị từ chối với mã `reject_missing_date`.

### 2. Nhóm kiểm hồi quy SimHash 64-bit & DOM Jaccard (Gate 3 Optimization):
- `test_simhash_counter_optimization_equivalence_on_repeated_tokens`: So sánh đối đầu giữa thuật toán tuần tự nguyên thủy và thuật toán tối ưu `Counter`. Khẳng định **100% khớp giá trị hash 64-bit** trên các mẫu văn bản lặp từ khóa và thẻ DOM phức tạp.
- `test_simhash_hamming_boundary_conditions`: Kiểm tra chính xác các ranh giới Hamming:
  - Hamming = 10 $\rightarrow$ `is_clone_template = True` (Nhánh 1).
  - Hamming = 11, 12, 13 (khi không có DOM) $\rightarrow$ `is_clone_template = False`.
- `test_dom_jaccard_and_hamming_combined_branch_boundaries`: Kiểm tra điều kiện kết hợp Nhánh 2:
  - Jaccard = 0.85 và Hamming = 11 $\rightarrow$ `is_clone_template = True`.
  - Jaccard = 0.85 và Hamming = 12 $\rightarrow$ `is_clone_template = True` (Biên Hamming của Nhánh 2).
  - Jaccard = 0.85 nhưng Hamming = 13 $\rightarrow$ `is_clone_template = False` (Chặn vượt ngưỡng Hamming dù Jaccard cao).
  - Jaccard = 1.0 (trùng hệt thẻ DOM) nhưng Hamming = 13 $\rightarrow$ `is_clone_template = False`.
  - Jaccard = 0.8421 (< 0.85) và Hamming = 11 $\rightarrow$ `is_clone_template = False`.
- `test_precomputed_fingerprint_preserves_registered_templates_behavior`: Xác nhận việc dùng precomputed fingerprint (`sample_simhash`, `sample_dom_tags`) khi đăng ký template bảo toàn hoàn toàn quyết định phân loại, khoảng cách đo và lý do loại trừ so với việc băm lại từ HTML thô.

**Kết quả thực thi:** `7 passed in 7.61s`. Bộ test được bàn giao trên Git để QA Lead B chạy độc lập trên clean checkout.

---

## V. TÁCH ĐỀ XUẤT CHỌN MẪU KHỎI KẾT QUẢ KIỂM NGUỒN

### 1. Hiện trạng kỹ thuật của Cổng 4 trong mã nguồn:
- Cổng 4 (`gate_4_stratified_sampling`) hiện đang triển khai thuật toán **lấy mẫu ngẫu nhiên xác định theo PRNG seed** (`random.Random(seed)`), chưa áp dụng phân tầng theo độ phức tạp HTML ("locked strata").
- Giá trị `--seed 42` sử dụng trong lệnh kiểm nguồn `--vetting-only` chỉ là tham số khởi tạo mặc định của script runner, **hoàn toàn chưa phải là seed chính thức được Lead D phê duyệt cho tập Main**.

### 2. Trình Lead D các phương án cho Quyết định chọn 100 mẫu tiếp theo:
Thành viên C kính trình Lead D xem xét và quyết định riêng về phương án chọn mẫu:
- **Lựa chọn 1 (Lấy mẫu ngẫu nhiên xác định theo seed):**
  - Rút ngẫu nhiên đồng đều 100 mẫu từ 1.232 ứng viên đã vượt qua Cổng 3.
  - Lead D chỉ định giá trị PRNG Seed chính thức (ví dụ: Seed 42, Seed 2026, hoặc seed khác do D quyết định).
- **Lựa chọn 2 (Lấy mẫu phân tầng - Stratified Sampling):**
  - Triển khai phân tầng mẫu theo các strata độ dài / cấu trúc DOM HTML đã được thống nhất trong Codebook V1.1.
- **Quy cách niêm phong hiện vật trích xuất:**
  - Khóa tệp `selected_samples.parquet` (100 mẫu) kèm mã băm SHA-256.
  - Sinh gói Blind View độc lập cho Đánh giá viên A và B (ẩn hoàn toàn nhãn nguồn, điểm số và gợi ý matcher).

---

## VI. TRẠNG THÁI QUẢN TRỊ & CÁC VIỆC CÒN MỞ

1. **Các chốt an toàn tiếp tục duy trì hiệu lực nghiêm ngặt:**
   - `main_annotation_status = "LOCKED"`
   - `training_blocked = true`
   - `official_test_used = false`
2. **Cam kết dữ liệu:** Toàn bộ 1.232 ứng viên tiếp tục nằm trong vùng kiểm nguồn an toàn, 0 mẫu nào bị rút, 0 gói Blind View nào được phát hành trước khi có Quyết định chính thức.
3. **Danh mục việc còn mở:**
   - [ ] QA Lead B kéo commit `ee921e0` và chạy kiểm định độc lập bộ test hồi quy.
   - [ ] Lead D xem xét báo cáo đính chính và ban hành Quyết định chính thức về việc rút 100 mẫu Main Annotation.
   - [ ] Thành viên C chuẩn bị script rút mẫu và xuất Blind View theo đúng chỉ đạo của Lead D.
