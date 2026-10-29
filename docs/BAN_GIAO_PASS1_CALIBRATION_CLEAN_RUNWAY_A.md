# BIÊN BẢN BÀN GIAO & KÍCH HOẠT GÁN NHÃN PASS 1: CALIBRATION CLEAN RUNWAY A

- **Mã đợt gán nhãn**: `CALIBRATION-CLEAN-24`
- **Phiên bản phát hành**: `1.1.0` (Đợt C)
- **Căn cứ pháp lý & học thuật**: Quyết định phê duyệt chính thức từ Lead D (Anh Tuấn) sau khi xác nhận Thành viên A hoàn toàn chưa tiếp xúc 24 mẫu Đợt C.
- **Thời điểm bàn giao (UTC)**: `2026-10-29T17:45:00Z` (`2026-10-30T00:45:00+07:00`)
- **Đơn vị bàn giao**: Thành viên C (Data Pipeline & Blind View)
- **Người nhận bàn giao**:
  1. Thành viên A: **Trần Hồng Khải** (Annotator A)
  2. Thành viên B: **Phùng Tấn Minh** (Annotator B / QA Lead)

---

## 1. Danh mục Tài nguyên Bàn giao & Bảo chứng Mật mã

Toàn bộ tài nguyên phục vụ gán nhãn Pass 1 được niêm phong mật mã với các giá trị băm tuyệt đối:

| Tài nguyên | Đường dẫn nội bộ | Dung lượng | SHA-256 Checksum |
| :--- | :--- | :--- | :--- |
| **Gói Blind View 24 mẫu** | `data/annotations/clean_calibration_blind_view_24.json` | 154,350 bytes | `0164b2a5499c10c824f7e559c9a351c958adcfe627648ac537179dfe4dbf2b6b` |
| **Manifest mở phiên đã duyệt** | `configs/calibration_clean_a_manifest.json` | 7,365 bytes | `9d94dd3e33134131047600d9297f3058b3049a946863cac24fe34b7fd110a32b` |
| **Codebook v1.1** | `docs/CODEBOOK_V1_1.md` | 22,160 bytes | `e30871b87911992110e77ad0dcca8bbf64b916086f496555599e43730af0adbd` |
| **Từ điển 14 tổ chức chuẩn hóa**| `configs/dictionary_v1.json` | 15,329 bytes | `7aa83b68fdb4bb288460c00523e38e0779e8cbeb81ae879e7a5d27e771fcd3b3` |
| **Gói phân phối độc lập (ZIP)** | `GOI_BAN_GIAO_PASS1_CALIBRATION_CLEAN_24.zip` | 75,884 bytes | `9101164c9fe34aebc145f4e8ef6faa1fcb136cdc4684e9591dda05cda6189f60` |

---

## 2. Lệnh Khởi chạy Phiên Gán Nhãn CLI có Bấm giờ Tương tác

### A. Dành cho Thành viên A (Trần Hồng Khải)
```bash
python scripts/annotate_cli.py \
  --annotator A \
  --input data/annotations/clean_calibration_blind_view_24.json \
  --output data/annotations/A/clean_calibration_pass1.jsonl \
  --manifest configs/calibration_clean_a_manifest.json \
  --pass-id 1
```

### B. Dành cho Thành viên B (Phùng Tấn Minh)
```bash
python scripts/annotate_cli.py \
  --annotator B \
  --input data/annotations/clean_calibration_blind_view_24.json \
  --output data/annotations/B/clean_calibration_pass1.jsonl \
  --manifest configs/calibration_clean_a_manifest.json \
  --pass-id 1
```

---

## 3. Quy chuẩn Nghiên cứu Hàn lâm & Kỷ luật Bắt buộc (ARS Protocols)

1. **Độc lập mù đôi tuyệt đối (Double-Blind Independence):**
   - Thành viên A và B không thảo luận, không so sánh kết quả, không chia sẻ file kết quả trong suốt quá trình thực hiện Pass 1.
   - Không trao đổi bất kỳ bằng chứng nhận diện thương hiệu hay phán đoán nào trước khi cả hai nộp file và khóa phiên.
2. **Không sử dụng AI / Bên thứ ba:**
   - 100% quyết định nhãn (`label`, `target`, `confidence`) do chính annotator đánh giá dựa trên văn bản và cấu trúc hiển thị trên CLI.
   - Tuyệt đối cấm sử dụng LLM, extension AI hoặc người ngoài để đưa ra gợi ý nhãn.
3. **Bấm giờ thực tế & Ghi nhận tạm dừng (Interactive Pause / Resume):**
   - Khi tạm dừng phiên làm việc để giải lao hoặc xử lý công việc cá nhân, bắt buộc sử dụng phím `p` (Pause) trong CLI để trừ thời gian nghỉ, bảo đảm `seconds_spent` phản ánh chính xác nỗ lực nhận thức (cognitive effort).
4. **Bảo mật và an toàn chống rò rỉ (Fail-Closed Governance):**
   - Chỉ phát hành đúng 24 mẫu chính (`SMP-001` đến `SMP-024`).
   - Giữ kín tuyệt đối 8 mẫu dự phòng (`RSV-001` đến `RSV-008`), locator shard/row và hồ sơ ánh xạ hạn chế.
   - Tiếp tục khóa cứng cờ học máy: `training_blocked = true`, `official_test_used = false`.

---

## 4. Quy trình Thu nhận Kết quả & Tính toán Cohen's Kappa

1. **Thu nhận file gốc**: Sau khi hoàn thành gán nhãn 24 mẫu, A và B gửi file kết quả `clean_calibration_pass1.jsonl` qua kênh hạn chế riêng cho Thành viên C và Lead D.
2. **Tiền kiểm kỹ thuật**: Thành viên C thực hiện đối soát tự động:
   - Đủ đúng 24 bản ghi JSONL tương ứng `SMP-001` đến `SMP-024`.
   - Chuẩn hóa kết thúc dòng Unix LF.
   - `seconds_spent >= 0` trên tất cả bản ghi.
   - Không có can thiệp sửa tay sau khi CLI ghi nhận.
3. **Tính toán Cohen's Kappa**: Chỉ sau khi cả hai file đạt tiền kiểm, hội đồng mới tiến hành đo lường độ thỏa thuận liên đánh giá viên (Inter-Annotator Agreement) và lập báo cáo Pass 1.
