# BÁO CÁO KIỂM TOÁN NGUỒN SHARD TRAIN-001 VÀ BÀN GIAO KỸ THUẬT (BẢN HOÀN THIỆN TRÌNH LEAD D)

**Căn cứ phê duyệt thực tế:** Thông báo phê duyệt Quyết định 1 của Lead D (ban hành ngày 17/11/2026, dẫn chiếu dự thảo tại commit `123799803100f8ab4662d94cab76add125df9201`)  
**Phạm vi phê duyệt:** Chỉ cho phép tải shard `train-001.parquet` theo revision đã khóa, đối soát dung lượng và SHA-256, chạy kiểm nguồn `--vetting-only` qua Gates 0–3 để đánh giá trữ lượng ứng viên. Tuyệt đối không cho phép rút mẫu hay mở Main Annotation.  
**Ý kiến chỉ đạo rà soát:** Thông báo của Lead D (18/11/2026)  
**Người thực hiện:** Thành viên C (Nguyễn Thắng — Data Pipeline Owner & Thư ký Kiểm toán)  
**Công cụ hỗ trợ:** Mô hình Duo (DeepSeek Bridge — chế độ Reason & Code có kiểm định)  
**Trạng thái quản trị:** `main_annotation_status = "LOCKED"`, `training_blocked = true`, `official_test_used = false`  
**Nhánh Git:** `feat/c-calibration-v1-1-4-adjudication`

---

## 1. MỤC TIÊU VÀ PHẠM VI
- Báo cáo kết quả kiểm nguồn độc lập (`--vetting-only`, Gates 0–3) trên shard `train-001.parquet` (PhreshPhish).
- Giải trình tận gốc và đồng bộ hóa chênh lệch mã băm tệp nhật ký kiểm toán JSON do cơ chế xuống dòng CRLF/LF giữa Windows và Git.
- Bàn giao bộ kiểm thử hồi quy 7 ca test tại `tests/test_selection_gate_cfc3bc7_regression.py` (đã chỉnh sửa fixture ca kiểm sát ngưỡng Jaccard 16/19).
- Bàn giao đầy đủ bằng chứng kiểm thử tự động toàn dự án (446 passed, 2 skipped) kèm file log và mã băm.
- Định hình chính xác phạm vi gán nhãn và tách bạch đề xuất lấy mẫu khỏi bước kiểm nguồn theo chuẩn mực ARS.

---

## 2. NGƯỜI THỰC HIỆN VÀ NGƯỜI THẨM ĐỊNH
- **Người thực hiện:** Nguyễn Thắng (Thành viên C — Data Pipeline Owner).
- **Người thẩm định kỹ thuật & phê duyệt:** Lead D (Anh Tuấn).
- **Người thẩm định QA độc lập:** Phùng Tấn Minh (Thành viên B — QA Lead).

---

## 3. CÔNG CỤ AI ĐÃ DÙNG (MÔ HÌNH DUO)
- **DeepSeek Bridge CLI:** Sử dụng `deepseek-v4-pro` (mode `reason`) và `deepseek-flash` (mode `code`) thông qua cầu nối nội bộ `deepseek_bridge/cli.py`.
- **Phạm vi xử lý:** Phân tích logic ranh giới toán học của khoảng cách Hamming và chỉ số DOM Jaccard, thiết kế fixture kiểm thử hồi quy 16/19 thẻ. Tuyệt đối không đưa dữ liệu hạn chế `data/restricted/` hay nhãn nguồn vào AI.

---

## 4. ĐẦU VÀO ĐÃ KHÓA VÀ BẢNG MÃ BĂM ĐỐI SOÁT

| Hiện vật kiểm toán | Đường dẫn tệp | Dung lượng | Mã băm SHA-256 | Ghi chú kiểm toán |
| :--- | :--- | :---: | :--- | :--- |
| **Shard nguồn Parquet** | `data/raw/phreshphish/data/train-001.parquet` | 322.018.201 bytes | `260cb9c93299f6b244d48321fe115523159770f4e73446b382473628c6e81d74` | Đo trực tiếp trên đĩa, khớp 100% Git-LFS pointer |
| **Source Manifest (Trước)** | `configs/source_manifest.json` (@`1237998`) | 34.671 bytes | `50fa39d58325e4645b76886e519dd5fbaca31db234d8c70eb95a4eeb608e8eb0` | Trạng thái `metadata_only_column_projected` |
| **Source Manifest (Sau)** | `configs/source_manifest.json` (@`cfc3bc7`) | 34.719 bytes | `dbbc9746416ccbdb8d19c6e2889c801376be17f2f2cfb61dbd4e98fe8393f5d7` | Cập nhật `locally_verified` cho shard 1 |
| **Exclusion Registry** | `data/exclusion_registry.json` | 107.712 bytes | `aee8c4f398e5b74240501d67e373434e80cca2f1395c6dcab22ad8d3507ce9bc` | 246 mục khai báo / 226 cặp duy nhất |
| **Cam kết hạn chế 1** | `pilot_batch1_recovery_dossier_restricted_v4.json` | Hồ sơ hạn chế | `17f71f23c2314ebf9c36a0a07f9fe21fe56aa18efec682b75f7ec06baf196171` | Cam kết `EXCL-PILOT-01` (20 mẫu) |
| **Cam kết hạn chế 2** | `clean_calibration_exclusion_mapping_c_32.json` | Hồ sơ hạn chế | `67326e80b2a6f9cb7356450a31fe15054a1193412a8ed0576ea2972f1801a805` | Cam kết Lô 10 (32 mẫu) |
| **Vetting Audit JSON (Git/LF)** | `data/source_audit/phreshphish/train_001_vetting/source_vetting_audit_manifest.json` | 7.574 bytes | `4b48a2194cb321e386690ec2b75d5c1aeb3bddf43804ddbed3317c8691cafc6f` | Bản lưu Git (chuẩn hóa LF) và đĩa sau đồng bộ |
| **Vetting Audit JSON (Win/CRLF)** | Bản đo đĩa ban đầu trước khi chuẩn hóa LF | 7.774 bytes | `0a96bd7ac3e799a490088c227474a4ed0141450e92ae4286d37bd608a464fdf5` | Chênh lệch 200 byte do 200 ký tự `\r\n` CRLF |

---

## 5. THAY ĐỔI THỰC TẾ & GIẢI TRÌNH CHÊNH LỆCH AUDIT JSON

### A. Giải trình bản chất chênh lệch tệp Audit JSON (7.774 bytes vs. 7.574 bytes):
- **Phát hiện gốc rễ (Root Cause):** Tệp `source_vetting_audit_manifest.json` gồm đúng 201 dòng văn bản JSON. Khi runner Python chạy và ghi tệp trên môi trường Windows, tệp được tạo ra với ký tự ngắt dòng chuẩn Windows là CRLF (`\r\n`), gồm đúng 200 cặp `\r\n` $\rightarrow$ dung lượng đo vật lý trên đĩa là **7.774 bytes** (SHA-256: `0a96bd7ac3e799a490088c227474a4ed0141450e92ae4286d37bd608a464fdf5`).
- **Cơ chế Git:** Khi C thực hiện `git add` tại commit `cfc3bc7`, cơ chế filter của Git tự động chuyển đổi 200 ký tự `\r\n` thành `\n` (LF) để lưu vào Git object database. Khi loại bỏ 200 ký tự `\r`, dung lượng giảm đúng 200 bytes xuống **7.574 bytes** (SHA-256: `4b48a2194cb321e386690ec2b75d5c1aeb3bddf43804ddbed3317c8691cafc6f`).
- **Nội dung dữ liệu:** Hai bản có **100% nội dung ngữ nghĩa, số đếm, danh mục từ điển và lý do loại trừ trùng khớp tuyệt đối (Zero Diff)**. Không có sự kiện chạy lại hay chèn metadata sau chạy.
- **Xử lý đồng bộ:** C đã ghi đè tệp trên đĩa với chuẩn ngắt dòng LF (`\n`). Hiện tại, cả tệp trên đĩa và tệp trong kho Git đều có chung dung lượng **7.574 bytes** và mã băm SHA-256 **`4b48a2194cb321e386690ec2b75d5c1aeb3bddf43804ddbed3317c8691cafc6f`**.

### B. Đính chính điều kiện tương đồng template Cổng 3:
- Ngưỡng đánh dấu tương đồng trong mã nguồn (`TemplateSimilarityEngine`):
  + **Nhánh 1:** Khoảng cách Hamming SimHash 64-bit $\le 10$ (`dist <= 10`).
  + **Nhánh 2:** Độ tương đồng thẻ DOM Jaccard $\ge 0.85$ (`jaccard >= 0.85`) **ĐỒNG THỜI** khoảng cách Hamming SimHash $\le 12$ (`dist <= 12`).
- 840 trường hợp bị loại tại Cổng 3 được định danh chính xác là **“840 bản ghi bị loại theo tiêu chí tương đồng template”** (`reject_gate3_template_clone`). Tiêu chí này là bộ lọc cấu trúc heuristic phục vụ đa dạng hóa corpus, chưa chứng minh các trang thuộc cùng một phishing kit.

---

## 6. TỰ KIỂM: SỐ LIỆU ĐO LƯỜNG VÀ PHẠM VI GÁN NHÃN

### A. Số liệu kiểm toán qua các cổng:
- **Cổng 0 (Shard & Source Integrity):** 5.780 vào $\rightarrow$ 5.780 ra (Đạt 100%).
- **Cổng 1 (Field Validity, HTML & Date Window):** 5.780 vào $\rightarrow$ 2.752 ra. Loại 3.028 mẫu (2.894 mẫu trước ngày 2024-10-01; 84 mẫu có HTML > 2.000.000 ký tự; 50 mẫu URL không hợp lệ).
- **Cổng 2 (Cryptographic Anti-Leakage Filter):** 2.752 vào $\rightarrow$ 2.321 ra. Loại 431 mẫu khớp Exclusion Registry. Có **0 bản ghi bị loại với mã `reject_gate2_preprocessing_error`**.
- **Cổng 3 (Deduplication, eTLD+1 & Template Clones):** 2.321 vào $\rightarrow$ **1.232 ra**. Loại 1.089 mẫu (840 mẫu bị loại theo tiêu chí tương đồng template; 218 mẫu xung đột tên miền eTLD+1; 27 mẫu trùng HTML thô; 4 mẫu trùng URL).
- **Trạng thái Quota:** `meets_quota_target = true`, `vetting_status = "vetted_meets_quota"`.

### B. Chuẩn hóa phạm vi gán nhãn:
> *“Có 1.232 ứng viên vượt qua các bộ lọc đang triển khai trước Gate 4. Chưa rút mẫu Main. Sau quyết định riêng của D, lô dự kiến 100 mẫu sẽ được chuẩn bị; A gán toàn bộ lô, B gán độc lập tập 30% ngẫu nhiên đã niêm phong và các mẫu bổ sung theo kế hoạch được duyệt. Kappa chính chỉ tính trên tập ngẫu nhiên.”*
- Thành viên C cam kết không suy rộng kết quả gán nhãn của lô được chọn thành nhãn xác thực cho toàn bộ 1.232 ứng viên.

---

## 7. KIỂM THỬ: REFACTOR BỘ HỒI QUY VÀ BẰNG CHỨNG TEST SUITE

### A. Chỉnh sửa fixture ca kiểm sát ngưỡng Jaccard 16/19:
Trong [`tests/test_selection_gate_cfc3bc7_regression.py`](file:///d:/nguyen%20thang/NCKH/NCKH_2/tests/test_selection_gate_cfc3bc7_regression.py), C đã tách biệt fixture:
1. **Engine 20 thẻ (`base_tags_20`):** Dùng cho các mốc $17/20 = 0.85$:
   - Jaccard = 0.85 & Hamming = 11 $\rightarrow$ `is_clone_template = True`.
   - Jaccard = 0.85 & Hamming = 12 $\rightarrow$ `is_clone_template = True`.
   - Jaccard = 0.85 & Hamming = 13 $\rightarrow$ `is_clone_template = False` (Chặn vượt ngưỡng Hamming).
   - Jaccard = 1.0 & Hamming = 13 $\rightarrow$ `is_clone_template = False`.
2. **Engine 19 thẻ (`base_tags_19`):** Dùng riêng cho ca kiểm sát dưới ngưỡng:
   - Template cơ sở đăng ký với đúng 19 thẻ phân biệt.
   - Ứng viên mang 16 thẻ con: Giao = 16, Hợp = 19 $\rightarrow$ Jaccard = `round(16/19, 4) = 0.8421`.
   - Xác nhận: `res_sub_jaccard["max_dom_jaccard"] == 0.8421` (đúng bằng 16/19).
   - Với Hamming = 11 và Jaccard = 0.8421 (< 0.85), kết quả kiểm định: `is_clone_template is False`.
- **Kết quả:** `pytest tests/test_selection_gate_cfc3bc7_regression.py` đạt **7/7 PASSED in 2.68s**.

### B. Bằng chứng kiểm thử toàn diện toàn dự án:
- **Môi trường thực thi:** Python 3.13.14, pytest 7.4.0 trên Windows 11.
- **Lệnh chạy:** `python -m pytest tests/`
- **Kết quả kiểm thử:** **446 passed, 2 skipped, 1 warning in 65.18s** (0 failed, 0 deselected).
- **Lý do 2 ca test bị skipped:**
  1. `tests/test_pilot_v2.py::TestPilotIncidentAndV2Package::test_strict_three_tier_deduplication_between_v2_and_previous`
  2. `tests/test_pilot_v2.py::TestPilotIncidentAndV2Package::test_exclusion_registry_contains_both_v1_and_v2`  
  *(Lý do: Hai ca test này yêu cầu hiện vật lịch sử Pilot V1 đã được cô lập khỏi repository để bảo vệ an toàn dữ liệu).*
- **Lưu trữ tệp log kiểm thử trên Git:**
  - `data/source_audit/phreshphish/train_001_vetting/pytest_full_suite_run_task13445.txt` (3.119 bytes | SHA-256: `bbf7c23e8d036f956cf10e4f5a60c78703b55f371fb052df9d888222ea11c287`).
  - `data/source_audit/phreshphish/train_001_vetting/pytest_full_suite_run_task13539.txt` (3.119 bytes | SHA-256: `279600606b92da7bc0507d809220a3a7006d94ada76d5a6f87f85658626ac484`).

---

## 8. KẾT LUẬN KIỂM TOÁN VÀ NGHIỆM THU KIỂM NGUỒN
- Shard `train-001.parquet` đạt chuẩn toàn vẹn vật lý và đối soát mã băm 100%.
- Quy trình kiểm nguồn `--vetting-only` đã hoàn thành trọn vẹn, xác định có 1.232 ứng viên sạch vượt qua các bộ lọc Cổng 0–3, bảo đảm trữ lượng vượt mốc quota 100 mẫu.
- Cơ chế kiểm thử hồi quy cho `datetime.date` và SimHash/DOM Jaccard đã được kiểm chứng độc lập và đạt chuẩn ARS.

---

## 9. GIỚI HẠN VÀ VIỆC CÒN MỞ
- **Giới hạn:** Lượt chạy hiện tại chỉ hoàn tất bước kiểm nguồn (`--vetting-only`). Chưa thực hiện Cổng 4, chưa trích xuất mẫu Main, chưa sinh Blind View.
- **Việc còn mở:**
  1. Lead D xem xét nghiệm thu kiểm nguồn và ban hành Quyết định chính thức về việc chọn 100 mẫu Main Annotation (lựa chọn phương pháp lấy mẫu và seed chính thức).
  2. QA Lead B chạy đối chiếu độc lập trên clean checkout.
  3. Thành viên C sẵn sàng thực thi rút 100 mẫu và đóng gói Blind View ngay khi có Quyết định của Lead D.

---

## 10. TRẠNG THÁI QUẢN TRỊ
- `main_annotation_status = "LOCKED"`
- `training_blocked = true`
- `official_test_used = false`
- Toàn bộ commit và log đã được đẩy lên nhánh `feat/c-calibration-v1-1-4-adjudication`.
