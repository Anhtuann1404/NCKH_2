# BIÊN BẢN BÀN GIAO & KÍCH HOẠT GÁN NHÃN PASS 1: CALIBRATION CLEAN RUNWAY A (BẢN ĐÍNH CHÍNH VẬN HÀNH)

- **Mã đợt gán nhãn**: `CALIBRATION-CLEAN-24`
- **Phiên bản phát hành**: `1.1.0` (Đợt C)
- **Căn cứ pháp lý & học thuật**: Quyết định phê duyệt chính thức từ Lead D (Anh Tuấn) sau khi xác nhận Thành viên A hoàn toàn chưa tiếp xúc 24 mẫu Đợt C.
- **Thời điểm bàn giao (UTC)**: `2026-10-29T17:45:00Z` (`2026-10-30 00:45:00 GMT+7`)
- **Thời điểm đính chính vận hành (UTC)**: `2026-10-29T18:10:00Z` (`2026-10-30 01:10:00 GMT+7`)
- **Đơn vị bàn giao**: Thành viên C (Data Pipeline & Blind View)
- **Người nhận bàn giao**:
  1. Thành viên A: **Trần Hồng Khải** (Annotator A)
  2. Thành viên B: **Phùng Tấn Minh** (Annotator B / QA Lead)

---

## 1. Danh mục Tài nguyên Bàn giao & Bảo chứng Mật mã

Toàn bộ tài nguyên phục vụ gán nhãn Pass 1 được niêm phong mật mã với các giá trị băm tuyệt đối:

| Tài nguyên | Đường dẫn nội bộ trong Repo | Dung lượng | SHA-256 Checksum |
| :--- | :--- | :--- | :--- |
| **Gói Blind View 24 mẫu** | `data/annotations/clean_calibration_blind_view_24.json` | 154,350 bytes | `0164b2a5499c10c824f7e559c9a351c958adcfe627648ac537179dfe4dbf2b6b` |
| **Manifest mở phiên đã duyệt** | `configs/calibration_clean_a_manifest.json` | 7,365 bytes | `9d94dd3e33134131047600d9297f3058b3049a946863cac24fe34b7fd110a32b` |
| **Codebook v1.1** | `docs/CODEBOOK_V1_1.md` | 22,160 bytes | `e30871b87911992110e77ad0dcca8bbf64b916086f496555599e43730af0adbd` |
| **Từ điển 14 tổ chức chuẩn hóa**| `configs/dictionary_v1.json` | 15,329 bytes | `7aa83b68fdb4bb288460c00523e38e0779e8cbeb81ae879e7a5d27e771fcd3b3` |
| **Gói phân phối độc lập (ZIP)** | `GOI_BAN_GIAO_PASS1_CALIBRATION_CLEAN_24.zip` | 77,240 bytes | `10cf1406341b21161f10b7083ee376099a0feb9ec5fb7021adbf7beec30f570a` |

---

## 2. Phân biệt Giữa "Kiểm Tra Hash" và "Preflight Thật"

- **Kiểm tra hash tĩnh (`verify_handover_pass1.py`):**
  - Chỉ đối soát giá trị băm SHA-256 của 4 tệp tài nguyên trên đĩa để xác nhận tệp giải nén không bị lỗi truyền dẫn hay đặt nhầm chỗ.
  - **Không** gọi hàm `validate_manifest_preflight` và **không** thay thế cho bước tiền kiểm vận hành.
- **Preflight nghiệp vụ thật (`scripts/annotate_cli.py`):**
  - Được CLI tự động kích hoạt ngay khi mở phiên làm việc, trước khi hiển thị mẫu đầu tiên cho annotator.
  - Thực hiện xác minh toàn diện: cờ `ready_for_annotation=true`, `acceptance.B=approved`, `acceptance.D=approved`, `training_blocked=true`, trạng thái khóa `codebook_status=locked`, `dictionary_status=locked`, số lượng mẫu đúng 24, đối chiếu chéo metadata giữa Blind View và Manifest.

---

## 3. Hướng dẫn Bố trí Tệp từ Gói ZIP Phẳng vào Git Checkout

Do tệp ZIP có **cấu trúc thư mục phẳng** và **không chứa mã nguồn CLI**, người gán nhãn bắt buộc phải sử dụng mã nguồn trong Git repository đã đồng bộ nhánh mới nhất (`feat/c-calibration-v1-1-4-adjudication`):

1. **Đồng bộ mã nguồn repo:**
   ```bash
   git fetch origin
   git checkout feat/c-calibration-v1-1-4-adjudication
   git pull origin feat/c-calibration-v1-1-4-adjudication
   ```
2. **Bố trí 4 tệp từ ZIP vào đúng thư mục:**
   - `clean_calibration_blind_view_24.json` → đặt vào `data/annotations/`
   - `calibration_clean_a_manifest.json` → đặt vào `configs/`
   - `CODEBOOK_V1_1.md` → đặt vào `docs/`
   - `dictionary_v1.json` → đặt vào `configs/`
   - `verify_handover_pass1.py` → đặt tại thư mục gốc repository để chạy kiểm tra.
3. **Chạy kiểm tra hash tĩnh:**
   ```bash
   python verify_handover_pass1.py
   ```
4. **Khởi chạy phiên gán nhãn có bấm giờ:**
   - **Thành viên A (Trần Hồng Khải):**
     ```bash
     python scripts/annotate_cli.py --annotator A --input data/annotations/clean_calibration_blind_view_24.json --output data/annotations/A/clean_calibration_pass1.jsonl --manifest configs/calibration_clean_a_manifest.json --pass-id 1
     ```
   - **Thành viên B (Phùng Tấn Minh):**
     ```bash
     python scripts/annotate_cli.py --annotator B --input data/annotations/clean_calibration_blind_view_24.json --output data/annotations/B/clean_calibration_pass1.jsonl --manifest configs/calibration_clean_a_manifest.json --pass-id 1
     ```

---

## 4. Xử lý Trạng thái Khởi chạy của A và B

- **Trường hợp đã bắt đầu:** Nếu Thành viên A hoặc B đã chạy đúng CLI trên checkout mới, các mã băm khớp và preflight thật đã vượt qua thành công: **Giữ nguyên lượt gán nhãn**, không yêu cầu làm lại; chỉ cần ghi nhận biên nhận kỹ thuật và mã commit khởi chạy.
- **Trường hợp chưa bắt đầu:** Gửi ngay văn bản hướng dẫn đính chính này để annotator nắm rõ quy trình bố trí tệp và phân biệt hash check vs preflight trước khi mở mẫu đầu tiên.
- **Báo cáo khởi chạy bắt buộc:** Mỗi annotator khi khởi chạy thành công cần gửi tin nhắn báo lại:
  1. Commit hash CLI (`git rev-parse --short HEAD`).
  2. Kết quả kiểm tra hash (`verify_handover_pass1.py`).
  3. Kết quả preflight hiển thị trên terminal khi CLI khởi động.

---

## 5. Giao thức Thu nhận JSONL Gốc & Tính Khiêm tốn Khoa học (Epistemic Humility)

1. **Bảo toàn byte gốc (Raw Bytes Integrity):**
   - Khi nhận tệp `clean_calibration_pass1.jsonl` từ A và B qua kênh hạn chế, lập tức tính mã băm SHA-256 trên chuỗi byte gốc thô trước khi thực hiện bất kỳ thao tác đọc hay sao chép nào.
   - Lưu trữ bản sao nguyên vẹn của byte gốc vào khu vực hạn chế (`data/restricted/`).
2. **Chấp nhận định dạng dòng tự nhiên theo OS:**
   - CLI ghi kết thúc dòng tự nhiên theo hệ điều hành của annotator (Windows ghi `\r\n` CRLF, Linux/macOS ghi `\n` LF).
   - **Tuyệt đối không sửa file gốc để ép chuẩn hóa LF.** Mọi chuẩn hóa phục vụ phân tích ma trận chỉ được thực hiện trên bản sao làm việc (working copy).
3. **Tính khiêm tốn khoa học trong hồ sơ kiểm toán:**
   - Không đưa ra tuyên bố tuyệt đối mang tính phán đoán như "chứng minh 100% không sửa tay" (zero manual tampering) chỉ dựa vào nội dung JSONL.
   - Hồ sơ học thuật ghi nhận đầy đủ bằng chứng khoa học thực nghiệm có thể kiểm chứng được:
     - Tính toàn vẹn mật mã: `raw_bytes_sha256`, dung lượng `byte_size`.
     - Xuất xứ và siêu dữ liệu phiên: `provenance`, chuỗi thời gian tăng tiến hợp lý, `seconds_spent >= 0`, enum `confidence` hợp lệ.
     - Văn bản cam đoan/xác nhận độc lập từ chính annotator về việc không can thiệp thủ công vào dữ liệu kết quả.
