# HƯỚNG DẪN THAO TÁC GÁN NHÃN CLI TRUNG TÍNH (MAIN ANNOTATION ĐỢT 1)

- **Mã văn bản**: `GUIDE-CLI-MAIN-BATCH1-NEUTRAL`
- **Phiên bản Hợp đồng Blind View**: `1.2.0`
- **Phiên bản Codebook**: `1.1.0` (tuân thủ `docs/CODEBOOK_V1.md`)
- **Đối tượng áp dụng**: Annotator A và Annotator B
- **Người ban hành**: Thành viên C (Data Pipeline Owner)
- **Trạng thái**: Hướng dẫn kỹ thuật chuẩn bị; **CHƯA MỞ GÁN NHÃN CHO ĐẾN KHI CÓ LỆNH RIÊNG TỪ LEAD D**.

---

## 1. NGUYÊN TẮC BẢO VỆ TÍNH MÙ & ĐỘC LẬP
1. **Độc lập tuyệt đối**: Annotator A và B thực hiện gán nhãn riêng biệt, không trao đổi về bất kỳ mẫu nào trước khi hoàn tất Pass 1 và nộp file cho Thành viên C.
2. **Không tra cứu ngoài**: Chỉ sử dụng thông tin hiển thị trên màn hình CLI (URL quan sát được, văn bản đã làm sạch, tóm tắt cấu trúc DOM). Tuyệt đối **không truy cập URL sống** ra ngoài Internet.
3. **Mã định danh trung tính**: Toàn bộ mẫu mang định danh `BLIND-xxxxxxxx`. Định danh này không chứa số lô, nhãn, phân tầng hay nguồn gốc.

---

## 2. CÀI ĐẶT MÔI TRƯỜNG & CHUẨN BỊ
Mở cửa sổ dòng lệnh (Terminal/PowerShell) tại thư mục gốc của dự án `NCKH_2`:

```bash
# Đảm bảo UTF-8 trên Windows
$env:PYTHONUTF8=1
```

---

## 3. LỆNH THỰC THI CHO ANNOTATOR A (LÔ 100 MẪU)
Khi nhận được thông báo gói phát hành chính thức từ Lead D, Annotator A chạy lệnh:

```bash
python scripts/annotate_cli.py `
  --annotator A `
  --input data/restricted/main_batch1/blind_view_a.json `
  --output data/annotations/A/main_batch1_pass1_A.jsonl `
  --pass-id 1
```

---

## 4. LỆNH THỰC THI CHO ANNOTATOR B (TẬP 30 MẪU)
Khi nhận được thông báo gói phát hành chính thức từ Lead D, Annotator B chạy lệnh:

```bash
python scripts/annotate_cli.py `
  --annotator B `
  --input data/restricted/main_batch1/blind_view_b.json `
  --output data/annotations/B/main_batch1_pass1_B.jsonl `
  --pass-id 1
```

---

## 5. CÁC TÍNH NĂNG VẬN HÀNH CHÍNH
- **Tự động bấm giờ (`seconds_spent`)**: Đồng hồ tự động tính thời gian từ lúc mẫu hiển thị đến khi người gán bấm phím xác nhận nhãn.
- **Tạm dừng và tiếp tục phiên (Pause/Resume)**:
  - Nếu cần nghỉ giải lao giữa phiên, gõ `pause` hoặc `quit` để CLI lưu trạng thái an toàn.
  - Khi chạy lại đúng câu lệnh ban đầu, CLI sẽ tự động tải lại tệp JSONL đã gán dở, kiểm tra tính toàn vẹn và tiếp tục từ mẫu tiếp theo.
- **Xem toàn bộ văn bản**: Gõ `full` khi cần đọc toàn bộ văn bản của trang thay vì bản tóm tắt.
- **Đánh dấu ca khó**: Nếu gặp ca nghi ngờ hoặc không chắc chắn, chọn cờ ca khó để ghi nhận chuyển sang phân xử của Lead D sau này.

---

## 6. NỘP FILE & BƯỚC TIẾP THEO
Sau khi hoàn thành tất cả các mẫu trong danh sách:
1. Xác nhận tệp JSONL tại `data/annotations/A/...` hoặc `data/annotations/B/...` không bị lỗi.
2. Gửi tệp JSONL cho Thành viên C để thực hiện kiểm tra Intake.
3. Chờ Lead D chủ trì phiên phân xử đối với các ca có sự bất đồng.
