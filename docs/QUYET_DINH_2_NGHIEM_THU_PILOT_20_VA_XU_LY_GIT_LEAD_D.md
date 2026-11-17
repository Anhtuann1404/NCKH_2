# VĂN BẢN QUYẾT ĐỊNH CHÍNH THỨC: QUYẾT ĐỊNH 2 CỦA LEAD D
## Về việc Xử lý Sự cố Git của Pilot tại Commit ad445a7 & Nghiệm thu Chuỗi Bằng chứng Pilot 20

* **Cơ quan ban hành:** Ban Chủ nhiệm Đề tài Nghiên cứu Khoa học NCKH_2  
* **Người phê duyệt & ban hành:** Lead D (Anh Tuấn - Chủ nhiệm Đề tài)  
* **Người tiếp nhận & lưu trữ:** Thành viên C (Data Pipeline & Thư ký Kiểm toán)  
* **Thời điểm Lead D phê duyệt thực tế:** `2026-11-17T13:26:46+07:00` (13:26:46 ngày 17/11/2026)  
* **Trạng thái pháp lý:** **ĐÃ CÓ HIỆU LỰC THI HÀNH CHÍNH THỨC**  
* **Commit tham chiếu đối chiếu kỹ thuật:** `9ca8f701526fc7a38133c685f56931a0c4bb9527`  
* **Commit hoàn tất rà soát tài liệu Git:** `47e1a2fb01a9297c03885a54a8f45705d140baa7`  

---

### CĂN CỨ BAN HÀNH:
1. Căn cứ Kỷ luật Nghiên cứu Hàn lâm (ARS) và Giao thức Chống rò rỉ dữ liệu (Mục 2 & Mục 6 `AGENTS.md`).
2. Căn cứ Biên bản Sự cố tiếp xúc dữ liệu Git `docs/INCIDENT_REPORT_GIT_EXPOSURE_AD445A7.md`.
3. Căn cứ Gói bằng chứng phục hồi hạn chế `data/restricted/pilot_batch1_remediation_pack_lead_d_v4_4.zip` (SHA-256: `91ccfa65078f1676695ccff91026cd37b38e0e63dde6f79a7b63bf9d1beec107`).
4. Căn cứ Hồ sơ hạn chế V4 `data/restricted/pilot_batch1_recovery_dossier_restricted_v4.json` (SHA-256: `17f71f23c2314ebf9c36a0a07f9fe21fe56aa18efec682b75f7ec06baf196171`).
5. Căn cứ Kết quả Lead D đối soát độc lập: 20/20 mẫu Pilot khớp tệp Rows API gốc và vị trí Parquet, tái lập độc lập 226 cặp URL/HTML duy nhất từ đủ 10 lô, và 41/41 bài kiểm thử Selection Gate đạt trong môi trường cô lập.

---

### NỘI DUNG QUYẾT ĐỊNH:

#### Điều 1. Phê duyệt áp dụng Phương án A (Forward-Fix & Administrative Retirement):
1. Giữ nguyên lịch sử commit trên Git nhằm bảo toàn audit trail minh bạch, phục vụ đánh giá khoa học và kiểm toán độc lập.
2. Không thực hiện force-push hoặc viết lại lịch sử Git (`git-filter-repo`, `git rebase`, `git reset`) trên nhánh cộng tác.
3. Thừa nhận trung thực theo chuẩn mực ARS: Phạm vi tiếp xúc lịch sử Git của commit `ad445a7` **chưa được xác minh đầy đủ** (do không có access/traffic log máy chủ GitHub; không tuyên bố "0 lượt tiếp xúc" hay "đã xóa sạch lịch sử Git").
4. Toàn bộ thông tin định vị dòng cụ thể và locator cấp mẫu đã được gỡ bỏ triệt để khỏi toàn bộ các tài liệu trên cây Git hiện hành (`0..19`, `row_offset`). Các tài liệu công khai trên Git chỉ lưu giữ commit sự cố, loại thông tin từng xuất hiện và số đếm tổng hợp. Toàn bộ chi tiết cấp mẫu được lưu trữ an toàn trong hồ sơ hạn chế ngoài Git (`data/restricted/`).

#### Điều 2. Nghiệm thu chuỗi bằng chứng xác minh Pilot 20:
1. Nghiệm thu bản phản hồi Rows API gốc `data/source_audit/phreshphish/pilot_20_rows.json` (7,186,229 bytes | SHA-256: `738ea69b920cb3037d7e9da38590024d8faa5f34c2eca6c760cb34690f2f190f`), khớp 100% hash lịch sử công bố tại `bc674e9` và `a62105a`.
2. Nghiệm thu kết quả đối chiếu Parquet tại revision khóa `eabec4b7a66324b79cc8a0ad856d1731dc26fe1a`: **20/20 khớp tại `train-000`, 0/20 khớp tại `train-055`, trong phạm vi hai shard đã kiểm**.
3. Xác nhận giữ nguyên thuộc tính `rows_api_revision_pinned = false` theo đúng phương thức thu thập lịch sử ban đầu.
4. Phê duyệt chính thức Hồ sơ hạn chế V4 (`pilot_batch1_recovery_dossier_restricted_v4.json` - SHA-256: **`17f71f23c2314ebf9c36a0a07f9fe21fe56aa18efec682b75f7ec06baf196171`**), giữ nguyên trường `lang = null` nguyên bản từ Rows API gốc.

#### Điều 3. Xác nhận số đếm khoa học và Thực thi loại trừ các mẫu đã biết:
1. Xác nhận quy chuẩn công bố số đếm chính xác: **246 mục khai báo theo 10 lô** và **226 cặp URL/HTML duy nhất** (đã được Lead D và Thành viên C tái lập độc lập từ đủ 10 lô).
2. Duy trì mã cam kết `EXCL-PILOT-01` trong `data/exclusion_registry.json` gắn với đúng cam kết Hồ sơ hạn chế V4 (`commitment_sha256 = "17f71f23c2314ebf9c36a0a07f9fe21fe56aa18efec682b75f7ec06baf196171"`).
3. Toàn bộ 20 mẫu Pilot Lô 1 bị loại trừ vĩnh viễn (retired) khỏi mọi tập dữ liệu huấn luyện (training), thẩm định (validation) và đánh giá chính thức (test) của các mô hình M0–M3.

#### Điều 4. Phạm vi Shard cách ly:
1. Cách ly vĩnh viễn shard `train-000.parquet` (`QUARANTINED`), cấm mọi hành vi trích xuất từ shard này cho Main Annotation.
2. Shard `train-055.parquet` tiếp tục áp dụng trạng thái cách ly hiện hành (`QUARANTINED`) để bảo vệ tính toàn vẹn của đợt Hiệu chuẩn sạch.

#### Điều 5. Thừa nhận giới hạn khoa học & Rủi ro tồn dư:
1. Thừa nhận trung thực trong các báo cáo khoa học: Phạm vi kiểm vị trí duy nhất đã hoàn thành trên 2 shard đã quét (`train-000` và `train-055`). Cổng 2 (xác thực các cam kết hồ sơ hạn chế và kiểm từng bản ghi theo các lớp hash trong registry) cùng Cổng 3 (lọc tương đồng template) sẽ tiếp tục bảo vệ các đợt trích xuất mới.
2. Toàn bộ bảng chi tiết cấp mẫu (ID, locator, nhãn nguồn, tên miền) tiếp tục được niêm phong an toàn tại khu vực hạn chế ngoài Git (`data/restricted/`).

---

### HIỆU LỰC THI HÀNH:
* Quyết định này có hiệu lực kể từ thời điểm Lead D gửi thông báo phê duyệt (`2026-11-17T13:26:46+07:00`).
* Thành viên C chịu trách nhiệm lưu trữ văn bản, đối soát mã băm và cập nhật vào lịch sử kiểm toán của dự án.
* Quyết định 1 (về tải và kiểm nguồn shard `train-001.parquet`) vẫn đang ở trạng thái dự thảo chờ Lead D phê duyệt riêng.
