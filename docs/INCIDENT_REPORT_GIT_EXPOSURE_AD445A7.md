# BIÊN BẢN SỰ CỐ TIẾP XÚC DỮ LIỆU CẤP MẪU TRÊN LỊCH SỬ GIT (INCIDENT GIT-EXP-01)

**Kính gửi:** Lead D (Anh Tuấn)  
**Người lập:** Thành viên C (Data Pipeline & Thư ký Kiểm toán)  
**Ngày lập:** 15/11/2026  
**Mã định danh sự cố:** `INCIDENT-GIT-EXP-01`  
**Commit phát sinh:** `ad445a7940010c002fa47484c7c90f956421f46a` (nhánh `feat/c-calibration-v1-1-4-adjudication`)  
**Quy chuẩn tham chiếu:** Kỷ luật Nghiên cứu Hàn lâm (ARS) & Anti-Leakage Protocols (Mục 2 & Mục 6 `AGENTS.md`)

---

## 1. Mô tả Sự cố & Dữ liệu Từng Xuất hiện

Trong commit `ad445a7` (được đẩy lên remote repository GitHub), tài liệu `docs/PILOT_BATCH1_AUDIT_AND_SELECTION_GATE_REPORT_LEAD_D.md` đã vô tình chứa một bảng đối soát chi tiết cấp mẫu 20 dòng thuộc Lô Pilot 1 (`EXCL-PILOT-01`).

* **Các trường dữ liệu cụ thể từng xuất hiện công khai trên Git:**
  1. `entry_id`: Từ `EXCL-PLT-001` đến `EXCL-PLT-020`.
  2. `locator`: Vị trí dòng cụ thể trong shard Parquet (`data/train-000.parquet:0..19`).
  3. `source_label`: Nhãn nguồn ban đầu (12 benign, 8 phishing).
  4. `source_date`: Ngày thu thập gốc trong shard (`YYYY-MM-DD`).
  5. `group_id`: Tên định danh nhóm miền (tiền tố `domain:...`).
  6. `html_chars`: Độ dài số lượng ký tự HTML.
* **Các trường dữ liệu KHÔNG xuất hiện:** Tệp không chứa chuỗi URL thô hay toàn văn mã nguồn HTML thô.

---

## 2. Phạm vi Tiếp xúc & Đánh giá Rủi ro (ARS Disclosure)

* **Tình trạng phân tán:** Commit `ad445a7` đã tồn tại trên nhánh làm việc từ xa trên máy chủ GitHub.
* **Đánh giá rủi ro tiếp xúc:**
  - Bất kỳ thành viên nào trong dự án (bao gồm Annotator A và Annotator B) có quyền đọc kho lưu trữ GitHub đều có khả năng xem commit này thông qua giao diện Web GitHub hoặc lệnh `git log -p` / `git diff`.
  - **Tuyên bố trung thực theo chuẩn mực ARS:** Do Thành viên C không có quyền quản trị máy chủ GitHub và không có quyền truy cập access/traffic logs (nhật ký truy cập IP/HTTP), **C tuyệt đối không tuyên bố "0 lượt tiếp xúc" hoặc "không có người xem"**. Sự cố này được phân loại chính thức là: **Phạm vi tiếp xúc tiềm tàng chưa xác minh (Unverified Exposure Scope)**.
* **Tình trạng trong Git:** Bản ghi dữ liệu trong commit `ad445a7` vẫn tồn tại trong lịch sử Git của repository. C **không tuyên bố đã xóa sạch lịch sử Git**.

---

## 3. Các Biện pháp Khắc phục Lập tức đã Thực hiện

1. **Cách ly dữ liệu cấp mẫu khỏi Git:**
   - Đã gỡ bỏ 100% bảng kê cấp mẫu ra khỏi toàn bộ tài liệu Markdown theo dõi trên Git.
   - Chuyển toàn bộ 20 dòng chi tiết cấp mẫu vào tệp hạn chế được `.gitignore` bảo vệ tuyệt đối:  
     `data/restricted/pilot_batch1_sample_level_audit_table.json`  
     *Kích thước:* `21,023 bytes` | *SHA-256:* `29d107535d185c3369e615f99a63d9190a485b47f01a3bc7743cf46c802701bc`.
2. **Rà soát tài liệu công khai & Gói QA cho B:**
   - Tài liệu báo cáo trên Git (`docs/PILOT_BATCH1_AUDIT_AND_SELECTION_GATE_REPORT_LEAD_D.md`) và đặc tả QA cho B (`docs/SELECTION_GATE_QA_SPEC_PACK_B.md`) được phát hành lại **chỉ chứa số liệu thống kê tổng hợp**, không chứa bất kỳ danh sách URL, locator, nhãn nguồn hay tên miền cụ thể nào.
   - Đã gỡ bỏ hoàn toàn tên miền thật khỏi các fixture trong bài kiểm thử (sửa dòng 255 của `tests/test_pilot_batch1_exclusion.py` sang dùng tên miền giả lập `mock-pilot-site.org`).
3. **Kỷ luật kỹ thuật Ponytail & ARS:**
   - C cam kết **không tự ý force-push hoặc viết lại lịch sử Git** (`git rebase -i` hay `git push --force`) khi chưa có lệnh bằng văn bản từ Lead D, nhằm bảo toàn chuỗi kiểm toán độc lập và tránh xung đột với các thành viên khác.

---

## 4. Hai Phương án Quản trị Lịch sử Git Trình Lead D Quyết định

| Tiêu chí so sánh | Phương án A (Forward-Fix & Administrative Retirement) - Khuyến nghị | Phương án B (Git History Rewrite via git-filter-repo) |
| :--- | :--- | :--- |
| **Cách thức thực hiện** | Giữ nguyên cây commit lịch sử; đánh dấu 20 mẫu này là đã bị phơi nhiễm locator trong lịch sử nội bộ và **loại trừ vĩnh viễn (retired)** khỏi toàn bộ quá trình phát triển, huấn luyện và kiểm thử mô hình (M0–M3). | Dùng công cụ `git-filter-repo` để xóa vĩnh viễn commit `ad445a7` và viết lại toàn bộ lịch sử commit tiếp theo, sau đó thực hiện `git push --force --all`. |
| **Ưu điểm** | - Minh bạch khoa học 100%, bảo toàn audit trail.<br>- Không làm gãy nhánh hay xung đột git của các thành viên khác.<br>- Đơn giản, an toàn theo kỷ luật Ponytail. | Xóa sạch triệt để dấu vết dữ liệu cấp mẫu khỏi cây commit GitHub từ xa. |
| **Nhược điểm & Hệ quả** | - Shard `train-000` (chứa 20 mẫu này) phải chịu lệnh cách ly vĩnh viễn (đã được Cổng 0 thực thi). | - Làm thay đổi toàn bộ commit hash sau `ad445a7`.<br>- Toàn bộ thành viên (Lead D, Annotator A, B) phải xóa repo cục bộ và clone lại từ đầu.<br>- Nguy cơ rủi ro mất mát dữ liệu nếu thành viên khác push đè nhánh cũ. |
| **Trạng thái phê duyệt** | **Đề xuất Lead D lựa chọn.** | **Chờ lệnh trực tiếp từ Lead D (nếu D yêu cầu).** |

---

## 5. Kết luận & Cam kết Quản trị
Thành viên C xin nhận trách nhiệm về việc sơ suất đưa bảng cấp mẫu vào commit `ad445a7` và cam kết tuân thủ tuyệt đối quy trình kiểm soát diff trước mọi commit tiếp theo. C kính đề nghị Lead D xem xét và ban hành quyết định lựa chọn Phương án A hoặc Phương án B.
