# Báo Cáo Xử Lý Sự Cố Nghiên Cứu Khoa Học: Pilot REAL-PILOT-32-V1

- **Ngày ghi nhận**: 05/10/2026
- **Người báo cáo**: Thành viên C (Data Pipeline & Blind View) theo xác nhận của Lead D
- **Phạm vi tác động**: Task LABEL-01 (Pilot gán nhãn có bấm giờ đợt 1)
- **Tình trạng hiện tại**: **VÔ HIỆU HÓA (INVALIDATED) & ĐÓNG BĂNG BẰNG CHỨNG (FROZEN)**

---

## 1. Bản Chất Sự Cố (Root Causes)

Theo kết luận điều tra và rà soát độc lập của Lead D:
1. **Vi phạm tính độc lập người gán nhãn (AI Contamination)**:
   - Thành viên A thừa nhận đã sử dụng mô hình trí tuệ nhân tạo (AI) để hỗ trợ lựa chọn nhãn, xác định tổ chức mục tiêu và bằng chứng ở cả phiên tập dượt kỹ thuật và phiên gán nhãn thật Pass 1.
   - Hành vi này vi phạm trực tiếp nguyên tắc nền tảng của đề tài: *Dữ liệu mặt đất (ground truth) phải là sản phẩm đánh giá độc lập của con người dựa trên Codebook v1.0.0, tuyệt đối không bị dẫn dắt bởi AI hay điểm số mô hình*.
2. **Trùng lặp nội dung giữa tập dượt và pilot thật (Dataset Overlap)**:
   - 20 mẫu trong gói tập dượt kỹ thuật (`data/annotations/blind_view_pilot.json`) có nội dung bị trùng lặp với 20 mẫu trong gói pilot thật `REAL-PILOT-32-V1` (`data/annotations/blind_view_pilot_real.json`), do cả hai gói đều trích xuất từ tập `technical20_api.json`.
   - Điều này làm triệt tiêu tính chất "mù" (blind view) và làm sai lệch thống kê thời gian thao tác `seconds_spent` của người đánh giá.

---

## 2. Quyết Định Xử Lý Của Nhóm Nghiên Cứu

Theo chỉ đạo của Lead D và sự đồng thuận của nhóm:
1. **Hủy bỏ hoàn toàn giá trị đo đạc của Pilot V1**:
   - Toàn bộ kết quả gán nhãn của Pass 1 trên `REAL-PILOT-32-V1` bị **vô hiệu hóa 100%**.
   - Tuyệt đối **KHÔNG sử dụng** hệ số Cohen's Kappa của V1 để làm căn cứ nghiệm thu khoa học.
   - Tuyệt đối **KHÔNG sử dụng** dữ liệu thời gian trung bình của V1 để chốt cỡ mẫu cho PLAN-01 (nguy cơ sai lệch ngân sách thời gian do A dùng AI rút ngắn thời gian bất thường).
2. **Đóng băng toàn bộ bằng chứng (Evidence Preservation)**:
   - Toàn bộ tệp blind view (`data/annotations/blind_view_pilot_real.json`), manifest (`configs/pilot_manifest.json`), kết quả nhãn gốc của A/B và logs được giữ nguyên vẹn 100% trên hệ thống để phục vụ kiểm toán khoa học (audit trail).
   - Tuyệt đối không xóa, ghi đè hoặc chỉnh sửa bất kỳ tệp dữ liệu nào của V1.
3. **Thiết lập Gói Pilot Mới 32 Mẫu (`REAL-PILOT-32-V2`)**:
   - Xây dựng gói pilot mới gồm 32 mẫu độc lập hoàn toàn, chọn lọc từ nguồn dữ liệu chuẩn chưa từng được công bố hay mở cho A và B.
   - Áp dụng bộ lọc 3 tầng nghiêm ngặt (URL canonical, HTML byte hash, và domain group eTLD+1) nhằm bảo đảm 0% trùng lặp.
   - A và B sẽ tiến hành gán nhãn lại Pass 1 thủ công 100% (không có sự tham gia của AI) sau khi gói mới được Lead D nghiệm thu.

---

## 3. Khóa Bằng Chứng Gói Pilot V1

| Hạng mục | Đường dẫn tệp | SHA-256 Checksum | Trạng thái |
| :--- | :--- | :--- | :--- |
| Blind View V1 | `data/annotations/blind_view_pilot_real.json` | `8be1c642e5534eeaad01b0ab9d2e8fc6d428ec131585631102a791e0f8d9a749` | Frozen (Invalidated) |
| Manifest V1 | `configs/pilot_manifest.json` | _(Cập nhật invalidation metadata)_ | Invalidated |
| Restricted Mapping | `data/raw/pilot/source_mapping.json` | `36215a9b2e89d59b0554bd99e96c11dd7d189e3b5e8da459fe9f6ed75a388347` | Frozen |
| Blind Order V1 | `data/raw/pilot/blind_order.json` | `d988eb711b8f8ebc76025117c0138a731157438c716bcfb172a7fd3f1209d771` | Frozen |

---

## 4. Cam Kết Ranh Giới Nghiên Cứu
- Không thay đổi đề cương nghiên cứu, câu hỏi nghiên cứu (RQ) hay taxonomy 14 tổ chức trong `CODEBOOK_V1.md`.
- Vĩnh viễn cô lập cả 32 mẫu V1 và 32 mẫu V2 trong `data/exclusion_registry.json` để ngăn chặn rò rỉ dữ liệu vào tập huấn luyện và đánh giá chính thức của Lead D.
