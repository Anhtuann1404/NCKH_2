# BÁO CÁO KIỂM TOÁN TỔNG HỢP 20 MẪU PILOT (EXCL-PILOT-01), CỔNG CHỌN MẪU MAIN ĐỢT 1 & XỬ LÝ SỰ CỐ LỊCH SỬ COMMIT

**Kính gửi:** Lead D (Anh Tuấn)  
**Người thực hiện:** Thành viên C (Data Pipeline & Thư ký Kiểm toán)  
**Ngày cập nhật:** 15/11/2026 (Bản sửa đổi V2 sau phản biện Lead D)  
**Chế độ thực thi:** Duo Mode (Antigravity & DeepSeek Reason Architecture Review)  
**Trạng thái Quản trị:** `main_annotation_status="LOCKED"`, `training_blocked=true`, `official_test_used=false`

---

## 1. Báo cáo Sự cố Tiếp xúc Dữ liệu Cấp Mẫu trên Lịch sử Git (Commit `ad445a7`)

### A. Mô tả Sự cố:
Trong commit `ad445a7` trên nhánh `feat/c-calibration-v1-1-4-adjudication`, tệp báo cáo `docs/PILOT_BATCH1_AUDIT_AND_SELECTION_GATE_REPORT_LEAD_D.md` đã vô tình chứa bảng kê chi tiết cấp mẫu (gồm Entry ID, locator `train-000:0..19`, nhãn nguồn, ngày thu thập và tên miền `group_id` của 20 mẫu Pilot Lô 1).

### B. Phạm vi Ảnh hưởng & Tiếp xúc:
* **Mức độ phân tán:** Commit đã được push lên remote repository GitHub tại nhánh tính năng `feat/c-calibration-v1-1-4-adjudication`.
* **Tiếp xúc tiềm tàng:** Bất kỳ thành viên nào có quyền đọc kho lưu trữ GitHub đều có thể xem lịch sử commit này nếu truy cập cây commit hoặc nhật ký diff.
* **Tuyên bố trung thực theo ARS:** Do Thành viên C không có quyền truy cập nhật ký truy cập (access/traffic logs) của GitHub server, C **tuyệt đối không đưa ra tuyên bố "0 lượt tiếp xúc"**. Sự cố này được ghi nhận chính thức vào hồ sơ kiểm toán.

### C. Hành động Khắc phục Lập tức từ C:
1. Đã chuyển toàn bộ bảng kê cấp mẫu chi tiết ra khỏi Git và niêm phong an toàn tại:  
   `data/restricted/pilot_batch1_sample_level_audit_table.json` (21,023 bytes | SHA-256: `29d107535d185c3369e615f99a63d9190a485b47f01a3bc7743cf46c802701bc`).
2. Phát hành lại báo cáo này trên Git **chỉ chứa số liệu thống kê tổng hợp**, không chứa bất kỳ danh sách URL, locator, nhãn nguồn hay tên miền cụ thể nào.
3. Tuân thủ kỷ luật: C **không tự ý viết lại lịch sử Git** (`git push --force` hay `git rebase`), giữ nguyên hiện trạng commit để Lead D chỉ đạo.

### D. Các Phương án Xử lý Lịch sử Commit Trình Lead D:
* **Phương án A (Forward-Fix & Administrative Retirement - Khuyến nghị):** Giữ nguyên cây commit lịch sử; đánh dấu 20 mẫu này là đã bị phơi nhiễm locator trong lịch sử nội bộ và **loại trừ vĩnh viễn** khỏi toàn bộ tập huấn luyện và kiểm thử (M0–M3). Phương án này bảo đảm tính minh bạch, không làm gãy nhánh hay xung đột git của các thành viên khác.
* **Phương án B (Git History Rewrite):** Nếu Lead D yêu cầu xóa sạch dấu vết commit `ad445a7`, C sẽ phối hợp cùng Lead D sử dụng `git-filter-repo` hoặc BFG Repo-Cleaner trên repository, sau đó toàn bộ nhóm (A, B, D) sẽ clone lại repository sạch.

---

## 2. Chuỗi Bằng chứng Pilot Gốc & Nguồn gốc Mã băm

### A. Tình trạng Hiện vật Gốc (Evidence Chain Audit):
C đã kiểm tra toàn bộ kho lưu trữ và xác nhận:
1. **Không còn tệp phản hồi Rows API nguyên byte** (raw HTTP response body dump) từ lượt gọi API ban đầu tháng 10/2026.
2. Tệp bằng chứng duy nhất còn lưu lại là:  
   `data/source_audit/phreshphish/pilot_summary.json` (5,344 bytes | SHA-256: `3889bf2f0c63789495aedd4c61132ee58454839eae6fbd885632bbdcab43d663`).
3. Checksum mảng phản hồi gốc Rows API được ghi nhận trong metadata: `738ea69b920cb3037d7e9da38590024d8faa5f34c2eca6c760cb34690f2f190f`.

### B. Hạ cấp Kết luận Khoa học theo ARS (Honest Downgrading):
Theo chỉ đạo của Lead D, do không có bản dump byte của phản hồi API gốc, C **hạ kết luận từ "khớp byte với Pilot gốc 20/20" xuống đúng mức độ đã chứng minh được**:
* **Khớp thống kê cấu trúc:** 20 bản ghi khớp 100% với `pilot_summary.json` về thứ tự nhãn (12 benign : 8 phish), độ dài ký tự HTML, số form, số input, trường ngôn ngữ và ngày thu thập.
* **Đối chiếu trên shard hiện tại:** Toàn bộ 20 bộ mã băm trong hồ sơ hạn chế `pilot_batch1_recovery_dossier_restricted.json` được **trích xuất và tính toán trực tiếp từ các hàng 0 đến 19 của shard `train-000.parquet` tại Git revision đã khóa `eabec4b7a66324b79cc8a0ad856d1731dc26fe1a`**, không phải từ bản lưu byte của lệnh gọi API quá khứ.
* **Định vị lịch sử (Historical Locator):** Do lệnh gọi Rows API ban đầu chưa khóa revision (`rows_api_revision_pinned = false`), C không khẳng định đây là locator lịch sử bất biến mà chỉ là **locator đối soát thực nghiệm tại revision đã khóa**.

### C. Số liệu Tổng hợp 20 Mẫu Pilot Lô 1 (Không lộ cấp mẫu):
* **Tổng số mẫu:** 20 mẫu.
* **Phân bố nhãn nguồn:** 12 Benign (60.0%), 8 Phish (40.0%).
* **Số nhóm miền duy nhất (eTLD+1):** 19 nhóm miền trên 20 mẫu (có 1 tên miền hosting chia sẻ xuất hiện ở 2 mẫu phish).
* **Ngày thu thập nguồn:** Toàn bộ 20 mẫu đều có ngày `2025-08-25`.
* **Phân bố độ dài HTML:** Ngắn nhất: 4,643 ký tự; Dài nhất: 1,736,334 ký tự; Trung vị: 156,511 ký tự.
* **Phân bố ngôn ngữ (`lang`):** Tiếng Anh (16), Tiếng Hà Lan (1), Tiếng Nhật (1), Tiếng Latinh (1), Không xác định (1).

### D. Mối quan hệ với Pilot Lô 2 & Khác biệt Quy tắc Mã băm Nhóm Miền:
1. **Quan hệ trùng lặp với Pilot Lô 2 (`EXCL-PILOT-02` / `EXCL-PILOT-02-REBUILD`):**
   * Đối soát URL & HTML: Trùng lặp **chính xác 0% (0/20 mẫu)**. Toàn bộ các mẫu của Pilot Lô 1 hoàn toàn độc lập với Pilot Lô 2.
2. **Quan hệ với `EXCL-REAL-PILOT-32`:**
   * 20 mẫu của Pilot Lô 1 chính là 20 mẫu đầu tiên của `EXCL-REAL-PILOT-32`.
   * 12 mẫu còn lại trong `EXCL-REAL-PILOT-32` tương ứng với 12 mẫu phish bổ sung từ shard `train-055.parquet`.
3. **Tổng số mẫu duy nhất sau khử trùng trên toàn bộ các lô Pilot:**
   * `EXCL-REAL-PILOT-32`: 32 mẫu duy nhất.
   * `EXCL-PILOT-02`: 32 mẫu duy nhất.
   * `EXCL-PILOT-02-REBUILD`: 32 mẫu duy nhất.
   * **Tổng số mẫu Pilot độc nhất đã loại trừ toàn hệ thống:** **96 mẫu duy nhất** (không có bất kỳ URL hay HTML nào trùng lặp chéo giữa 3 nhóm này).
4. **Khác biệt Quy tắc Mã băm Nhóm Miền (Domain Group Hash Rules):**
   * Trong danh mục cũ (`EXCL-REAL-PILOT-32`): Mã băm nhóm miền được tính trực tiếp trên chuỗi tên miền trần (bare domain, ví dụ `hashlib.sha256("example.com".encode())`).
   * Trong pipeline chuẩn hóa mới: Mã băm nhóm miền được tính có tiền tố chuẩn (prefixed group, ví dụ `hashlib.sha256("domain:example.com".encode())`).
   * **Cơ chế xử lý:** `ExclusionRegistry` và `SelectionGatePipeline` được lập trình hỗ trợ song song cả hai cơ chế băm (bare domain và prefixed group), bảo đảm không bỏ sót bất kỳ biến thể nào.

---

## 3. Khảo sát Rò rỉ Ngoài 20 Hàng Đầu (Scan Shards 000 & 055)

* **Trùng URL thô / URL chuẩn hóa:** 0 bản ghi trùng lặp trên cả hai shard.
* **Trùng HTML thô / HTML làm sạch:** 0 bản ghi trùng lặp trên cả hai shard.
* **Trùng Nhóm Miền / Tenant (`group_id` eTLD+1):**
  * Trong `train-000` (hàng 20..999): có **73 bản ghi** cùng chia sẻ tên miền/tenant với các mẫu pilot.
  * Trong `train-055` (0..999): có **21 bản ghi** cùng chia sẻ tên miền/tenant với các mẫu pilot.

---

## 4. Đề xuất Phạm vi Nguồn An toàn & Công bố Rủi ro Tồn dư

1. **Cách ly tuyệt đối (Strict Quarantine):** `train-000.parquet` và `train-055.parquet`. Hai shard này chứa vết pilot và 94 bản ghi trùng tenant miền.
2. **Chặn nguồn chưa duyệt:** Nguồn `PhishVN` tiếp tục bị chặn 100% khỏi pipeline chọn mẫu.
3. **Công bố rủi ro tồn dư trung thực:** 54 shard còn lại (`train-001` đến `train-054`) chỉ mới có mã băm Git-LFS SHA-256 từ siêu dữ liệu, chưa tải về và chưa quét byte cục bộ. C khẳng định trung thực: việc cách ly `train-000` và `train-055` **không phải là bằng chứng** cho thấy 54 shard còn lại là "hoàn toàn sạch". Rủi ro rò rỉ tenant hoặc template kit vẫn có thể xảy ra và bắt buộc phải được xử lý qua Cổng 2 và Cổng 3.

---

## 5. Nâng cấp Cổng Chọn Mẫu Main 5 Giai đoạn Đạt Chuẩn Fail-Closed

Đã hoàn thiện module [`src/phishing/data/selection_gate.py`](file:///D:/nguyen%20thang/NCKH/NCKH_2/src/phishing/data/selection_gate.py) và runner thực thi [`scripts/data/run_main_selection.py`](file:///D:/nguyen%20thang/NCKH/NCKH_2/scripts/data/run_main_selection.py):

* **Cổng 0 (Gate 0 - Shard & Source Integrity):**
  * Bắt buộc nguồn `phreshphish`, chặn `PhishVN`.
  * Bắt buộc revision khớp `eabec4b7a66324b79cc8a0ad856d1731dc26fe1a`.
  * Cách ly tuyệt đối `train-000` và `train-055`.
  * **Tự đối chiếu mã băm byte thực tế:** Tự động đọc từng khối byte (chunked 64KB) của tệp shard trên đĩa để tính SHA-256 thực tế và đối chiếu với `source_manifest.json`. Không chấp nhận hash do bên ngoài truyền vào.
* **Cổng 1 (Gate 1 - Field Validity & Operational Windows):**
  * Bắt buộc URL HTTP/HTTPS tuyệt đối qua `normalize_url`.
  * Giới hạn ký tự HTML `[1, 2,000,000]`.
  * **Ngày bắt buộc:** Yêu cầu trường ngày phải có mặt, đúng định dạng `YYYY-MM-DD` và nằm nghiêm ngặt trong cửa sổ `[2024-07-04, 2025-09-08]`.
* **Cổng 2 (Gate 2 - Cryptographic Anti-Leakage Filter):**
  * Fail-closed: ném `RuntimeError` nếu thiếu hoặc sai SHA-256 hồ sơ hạn chế.
  * Kiểm tra 6 lớp: URL thô, URL chuẩn hóa, HTML thô, HTML làm sạch, bare domain hash và prefixed domain group hash.
* **Cổng 3 (Gate 3 - Candidate Deduplication & Sequential Template Clustering):**
  * Khử trùng URL thô và URL chuẩn hóa.
  * Khử trùng HTML thô.
  * Giới hạn mật độ miền (Domain Diversity): tối đa 1 mẫu cho mỗi domain (eTLD+1).
  * **Kiểm tra template tuần tự:** Trích xuất khung sườn cấu trúc thẻ HTML (HTML tag skeleton hash, loại bỏ text, thuộc tính, script, style) để nhận diện và chặn các mẫu clone sinh từ cùng phishing kit.
* **Cổng 4 (Gate 4 - Sealed Seed Stratified Sampling & Quota Enforcement):**
  * Phân tầng theo PRNG Seed niêm phong.
  * **Thực thi nghiêm ngặt Quota (Fail-Closed):** Nếu số lượng ứng viên sạch sau Cổng 3 nhỏ hơn chỉ tiêu quota (`target_quota`), pipeline lập tức dừng và ném `SelectionGateError`, tuyệt đối không trả về tập mẫu thiếu quota.

---

## 6. Kết quả Kiểm thử Toàn diện (32 Tests PASSED)

Đã thiết kế lại toàn bộ bộ kiểm thử tại [`tests/test_pilot_batch1_exclusion.py`](file:///D:/nguyen%20thang/NCKH/NCKH_2/tests/test_pilot_batch1_exclusion.py) phân định rõ ràng giữa Fixture giả lập và Shard thật:

* **Môi trường chạy:** Python 3.13.14, pytest-7.4.0, Windows 10
* **Lệnh chạy:** `python -m pytest tests/test_pilot_batch1_exclusion.py -v`
* **Kết quả:** **32 passed, 0 failed, 0 skipped** (100% passed, thời gian: 5.20s):
  * [Gate 0 - 9 tests]: Chặn shard cách ly trên cả đường dẫn shard thật và tên chuỗi; chặn PhishVN; chặn nguồn/revision sai; chặn file không tồn tại; chặn file sai mã băm byte thực tế; chấp nhận file khớp byte.
  * [Gate 1 - 9 tests]: Chặn URL rỗng/sai scheme; chặn HTML rỗng/quá 2MB; chặn thiếu ngày, sai định dạng ngày, ngày trước min, ngày sau max; chấp nhận mẫu hợp lệ.
  * [Gate 2 - 5 tests]: Cố ý đưa URL thô từ shard thật của pilot vào -> BỊ CHẶN; Cố ý đưa HTML thô từ shard thật vào -> BỊ CHẶN; Cố ý đưa mẫu cùng tên miền vào -> BỊ CHẶN; Thiếu hồ sơ hạn chế -> ném RuntimeError dừng an toàn; Sửa sai hash cam kết -> ném RuntimeError dừng an toàn.
  * [Gate 3 - 3 tests]: Khử trùng URL & HTML; giới hạn 1 mẫu/domain; chặn template clone kit tuần tự.
  * [Gate 4 - 2 tests]: Thiếu quota mẫu ném `SelectionGateError` dừng an toàn; tính xác định của PRNG seed.
  * [End-to-End & Runner - 4 tests]: Chặn đứng `train-000` thật; chặn đứng `train-055` thật; chạy toàn bộ pipeline với mẫu pilot thật lẫn vào (pilot bị loại ở Cổng 2, mẫu sạch qua đủ 5 cổng); runner CLI thực tế trả về exit code 1 và dừng fail-closed khi nạp shard cách ly.
* **Kiểm thử hồi quy toàn hệ thống:** 5 tệp kiểm thử chuẩn (`test_pilot_batch1_exclusion.py`, `test_exclusion_registry.py`, `test_domain_rules.py`, `test_evaluate_kappa.py`, `test_clean_calibration_selection.py`): **115 passed / 0 failed**.

---

## 7. Hồ sơ Hạn chế Đã Niêm Phong Ngoài Git

1. **Hồ sơ đối soát cam kết Pilot 20:**  
   `data/restricted/pilot_batch1_recovery_dossier_restricted.json` (21,191 bytes | SHA-256: `7ab0d5cb637eb351eb4de39f5f9635c0f22cfb9c3a477fa197df59da28ad4d27`).
2. **Bảng kê chi tiết cấp mẫu (đã chuyển khỏi Git):**  
   `data/restricted/pilot_batch1_sample_level_audit_table.json` (21,023 bytes | SHA-256: `29d107535d185c3369e615f99a63d9190a485b47f01a3bc7743cf46c802701bc`).

---

## 8. Khuyến nghị Quản trị từ Thành viên C

1. **Giữ nguyên khuyến nghị `NO-GO` đối với việc rút mẫu và mở Đợt 1 ngay lúc này:**  
   Do cả 2 shard cục bộ đều bị cách ly; 54 shard còn lại chưa tải về và chưa kiểm toán byte; và sự cố phơi nhiễm locator trong commit `ad445a7` đang chờ Lead D quyết định phương án xử lý lịch sử.
2. **Cổng Quản trị tiếp tục khóa nghiêm ngặt:**  
   `main_annotation_status = "LOCKED"`, `training_blocked = true`, `official_test_used = false`. C cam kết **chưa rút 100 mẫu thật, chưa tạo hoặc phát Blind View, chưa mở Pass 1**.
