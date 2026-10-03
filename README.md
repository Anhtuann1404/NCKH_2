# Phát hiện website phishing mạo danh tổ chức bằng học máy kết hợp URL và nội dung trang

Đề tài Nghiên cứu Khoa học (NCKH) sinh viên — Lĩnh vực Công nghệ thông tin, Học máy & An toàn thông tin.

---

## 📌 Giới thiệu đề tài

Website phishing mạo danh các tổ chức, thương hiệu lớn ngày càng tinh vi và khó nhận biết nếu chỉ dựa vào URL hoặc bộ từ khóa thông thường. Đề tài tập trung xây dựng và đánh giá thực nghiệm có kiểm soát phương pháp phát hiện website phishing bằng học máy kết hợp đa tầng:
1. **URL features:** Cấu trúc từ vựng, độ dài, đặc trưng miền.
2. **DOM features:** Cấu trúc HTML, thẻ form, liên kết nội/ngoại miền, iframe.
3. **Văn bản trang:** Biểu diễn TF-IDF từ và char n-gram.
4. **Tín hiệu mạo danh có cấu trúc (Lõi nghiên cứu):** Bộ ba tín hiệu **Tổ chức – Tên miền – Ý định thu thập thông tin**, phân định rạch ròi giữa first-party domain, hạ tầng dùng chung (shared hosting / user-generated content) và miền giả mạo.

Hệ thống được kiểm chứng với giao thức chống rò rỉ dữ liệu nghiêm ngặt (**Grouped 5-fold CV theo `eTLD+1`**) và triển khai thành tiện ích trình duyệt cảnh báo thời gian thực (**Chrome Extension Manifest V3**).

---

## 📂 Cấu trúc thư mục

```text
NCKH_2/
├── docs/                      # Toàn bộ tài liệu nghiên cứu và đặc tả kỹ thuật
│   ├── README.md              # Hướng dẫn khởi động & thứ tự đọc tài liệu
│   ├── CURRENT_TASKS.md       # Bảng công việc hiện tại & tiến độ từng thành viên
│   ├── De_cuong_NCKH_Phishing_Mau_2.md # Đề cương nghiên cứu chính thức
│   ├── Ghi_chu_nghien_cuu.md  # Nhật ký nghiên cứu, rà soát và xác minh văn liệu
│   ├── TEAM.md                # Phân công vai trò A/B/C/D
│   ├── ROADMAP.md             # Lộ trình 6–7 tháng của đề tài
│   ├── TECH_SPEC.md           # Kiến trúc kỹ thuật và công nghệ đề xuất
│   ├── DATA_PROTOCOL.md       # Giao thức dữ liệu và quy trình gán nhãn mù
│   ├── EXPERIMENT_PROTOCOL.md # Giao thức thực nghiệm (M0–M3, B-rule, bootstrap CI)
│   ├── API_SPEC.md            # Đặc tả API giữa Backend và Extension
│   ├── openapi.json           # Schema OpenAPI v3
│   └── archive/               # Lưu trữ các phiên bản thảo luận trước
├── configs/                   # Cấu hình dự án mẫu và manifest nguồn dữ liệu
│   ├── project.example.json
│   └── source_manifest.example.json
├── data/                      # Dữ liệu phục vụ kiểm kê và thực nghiệm (đã ignore file nén lớn)
│   └── source_audit/          # Báo cáo kiểm kê nguồn (PhishVN, PhreshPhish, Crossref)
├── deepseek_bridge/           # Công cụ điều phối & nén ngữ cảnh kết nối DeepSeek API
└── src/                       # Mã nguồn nghiên cứu chính: pipeline, features, model & extension
```

---

## 📖 Bắt đầu từ đâu?

Vui lòng tham khảo bộ tài liệu chi tiết tại thư mục [`docs/`](docs/):
* **[docs/README.md](docs/README.md)**: Hướng dẫn đọc tài liệu theo thứ tự ưu tiên.
* **[docs/CURRENT_TASKS.md](docs/CURRENT_TASKS.md)**: Danh sách công việc cần làm ngay trong Sprint khởi động.
* **[docs/De_cuong_NCKH_Phishing_Mau_2.md](docs/De_cuong_NCKH_Phishing_Mau_2.md)**: Bản đề cương chi tiết đã bảo vệ thành công và được GVHD phê duyệt.

---

## 👥 Phân công vai trò dự án

| Vai trò | Phụ trách chính | Trách nhiệm cốt lõi |
| :---: | :---: | :--- |
| **A** | Gán nhãn dữ liệu | Đọc độc lập 100% mẫu phishing, trích xuất tên tổ chức tự do & bằng chứng |
| **B** | Kiểm nhãn độc lập & QA | Kiểm chéo độc lập 30% mẫu ngẫu nhiên + các ca khó, tính Cohen's Kappa |
| **C** | Quản lý dữ liệu & Giao diện mù | Pipeline thu thập, kiểm kê date, dựng blind labeling view, chuẩn bị split |
| **D** | Lead / Model & Extension | Lead dự án (Tuấn), chủ nhiệm xây dựng mô hình M0–M3, backend API & Chrome Extension |
