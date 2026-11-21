# QUY TRÌNH KIỂM TRA ĐẦU VÀO GÁN NHÃN (INTAKE VERIFICATION) MAIN ANNOTATION ĐỢT 1

- **Mã văn bản**: `SOP-INTAKE-MAIN-BATCH1`
- **Phiên bản**: `1.0`
- **Người thực hiện**: Thành viên C (Data Pipeline Owner)
- **Người chủ trì phân xử**: Lead D (Chủ nhiệm đề tài)
- **Người giám sát QA**: QA Lead B

---

## 1. MỤC TIÊU
Đảm bảo các tệp kết quả gán nhãn JSON Lines do Annotator A và Annotator B nộp đáp ứng đầy đủ tính toàn vẹn kỹ thuật, không bị thiếu sót, không lỗi cú pháp, và sẵn sàng cho việc tính toán độ tin cậy liên đánh giá viên (Cohen's Kappa) cũng như phiên phân xử do Lead D chủ trì.

---

## 2. CÁC TIÊU CHÍ KIỂM TRA BẮT BUỘC (FAIL-CLOSED INTAKE)
1. **Kiểm tra định dạng & cú pháp JSONL**:
   - Mỗi dòng là một JSON object hợp lệ, không có dòng trống ở giữa.
   - Không chứa bất kỳ bản ghi dry-run (`is_dry_run == True`) trong tệp chính thức.
2. **Kiểm tra tính đầy đủ số lượng (Completeness)**:
   - Tệp của Annotator A: Phải chứa chính xác **100 bản ghi** tương ứng với 100 `blind_id` đã phát hành.
   - Tệp của Annotator B: Phải chứa chính xác **30 bản ghi** tương ứng với 30 `blind_id` đã phát hành.
   - Tuyệt đối không có bản ghi trùng lặp `sample_id`.
3. **Kiểm tra tính toàn vẹn nội dung (`sample_content_hash`)**:
   - Đối chiếu `sample_content_hash` trong từng bản ghi của người gán với hash nội dung gốc được lưu trong `mapping_restricted.json`.
   - Nếu hash không khớp, tệp bị từ chối do có sự can thiệp hoặc lỗi hiển thị.
4. **Kiểm tra hợp lệ Enum**:
   - `class_label` thuộc `{phishing, benign, insufficient_evidence}`.
   - `primary_org_status` thuộc `{identified, unknown, no_clear_target, multi_target}`.
   - `seconds_spent` > 0 (không chấp nhận thời gian âm hoặc bằng 0).

---

## 3. QUY TRÌNH THỰC THI INTAKE & GHÉP CẶP ĐÁNH GIÁ ĐỘ ĐỒNG THUẬN (KAPPA)

### A. Lệnh thực thi tiếp nhận kết quả (Intake Execution)
**Điều kiện tiên quyết**:
- Gói phát hành `data/restricted/main_batch1/` đã được Lead D và QA Lead B phê duyệt chính thức (`ready_for_annotation=True`, `acceptance={'B': 'approved', 'D': 'approved'}`).
- Tệp kết quả JSONL từ người gán đã hoàn tất toàn bộ số mẫu (100 mẫu cho A, 30 mẫu cho B).

**Lệnh chạy intake cho Annotator A**:
```bash
python scripts/data/receive_main_batch1.py \
  --annotator A \
  --input data/annotations/A/main_batch1_pass1_A.jsonl \
  --restricted-dir data/restricted/main_batch1 \
  --out-root data/labels/intake_main_batch1
```

**Lệnh chạy intake cho Annotator B**:
```bash
python scripts/data/receive_main_batch1.py \
  --annotator B \
  --input data/annotations/B/main_batch1_pass1_B.jsonl \
  --restricted-dir data/restricted/main_batch1 \
  --out-root data/labels/intake_main_batch1
```

**Đầu ra xác định**:
- Tệp kết quả được lưu bất biến theo hash SHA-256: `data/labels/intake_main_batch1/{annotator}/{digest}.jsonl`.
- Biên lai kiểm toán sơ cấp `{digest}.receipt.json` (hoặc các nỗ lực kiểm tra lại độc lập `{digest}.attempt_{idx}_{status}_{ctx_sig}.json`).
- Nếu trạng thái là `accepted`, bản nộp được khóa vĩnh viễn; mọi bản nộp thay thế khác hash bắt buộc phải có cờ phê duyệt `--d-replacement-approval` từ Lead D.

---

### B. Kịch bản ghép cặp và tính toán Cohen's Kappa 3x3
**Điều kiện tiên quyết**:
- Cả hai bản nộp của Annotator A và B đều đã đạt trạng thái `accepted` tại pipeline intake.
- Đọc lại trực tiếp từ tệp byte JSONL đã được tiếp nhận chính thức, không ghép từ danh sách nhãn trôi nổi bên ngoài.

**Đoạn mã Python thực thi chuẩn hóa (chạy độc lập, không dùng placeholder)**:
```python
import json
from pathlib import Path
import sys

from phishing.annotation.kappa_3x3 import compute_kappa_3x3_from_records

intake_root = Path("data/labels/intake_main_batch1")
restricted_dir = Path("data/restricted/main_batch1")

# 1. Tìm và nạp biên lai accepted của A và B
receipts = {}
for role in ("A", "B"):
    ann_dir = intake_root / role
    accepted_files = [
        p for p in ann_dir.glob("*.json")
        if (p.name.endswith(".receipt.json") or ".attempt_" in p.name)
        and json.loads(p.read_text(encoding="utf-8")).get("status") == "accepted"
    ]
    if not accepted_files:
        raise FileNotFoundError(f"Không tìm thấy biên lai ACCEPTED cho annotator {role}")
    receipts[role] = json.loads(accepted_files[0].read_text(encoding="utf-8"))

# 2. Đọc lại các bản ghi từ tệp JSONL đã được intake tiếp nhận
saved_records = {}
for role, rcp in receipts.items():
    jsonl_path = Path(rcp["saved_path"])
    saved_records[role] = [
        json.loads(line) for line in jsonl_path.read_text(encoding="utf-8").splitlines() if line.strip()
    ]

# 3. Lấy danh sách sample_id của tập 30 mẫu B30 từ Blind View B đã niêm phong
blind_view_b = json.loads((restricted_dir / "blind_view_b.json").read_text(encoding="utf-8"))
target_ids = [s["sample_id"] for s in blind_view_b["samples"]]

# 4. Tính toán độ đồng thuận Kappa 3x3 với 100 lần bootstrap
result = compute_kappa_3x3_from_records(
    saved_records["A"],
    saved_records["B"],
    target_sample_ids=target_ids,
    bootstrap_iterations=100,
)

print(f"=== KẾT QUẢ ĐỘ ĐỒNG THUẬN COHEN'S KAPPA (TẬP 30 MẪU CHUNG) ===")
print(f"Tổng số mẫu đánh giá: {result.sample_count}")
print(f"Chỉ số thỏa thuận quan sát (Po): {result.observed_agreement:.4f}")
print(f"Chỉ số thỏa thuận kỳ vọng (Pe):   {result.expected_agreement:.4f}")
print(f"Hệ số Cohen's Kappa:             {result.kappa:.4f}")
print(f"Khoảng tin cậy 95% Bootstrap:   [{result.ci_lower:.4f}, {result.ci_upper:.4f}]")
```

---

## 4. PHÂN ĐỊNH VAI TRÒ TRONG PHÂN XỬ (ADJUDICATION)
Theo đúng chỉ đạo của Lead D:
1. **Annotator A và B**: Khóa tệp độc lập, trình bày lý do và bằng chứng khi được Lead D yêu cầu.
2. **Thành viên C (Data Pipeline)**:
   - Thực hiện kiểm tra intake kỹ thuật.
   - Lập biên bản phiên phân xử, ghi nhận quyết định cuối cùng kèm dấu vết nguồn gốc (provenance).
   - Tuyệt đối không tự ý phân xử hoặc chốt nhãn thay Lead D.
3. **Lead D (Chủ nhiệm đề tài)**:
   - **Trực tiếp chủ trì và ra quyết định phân xử cuối cùng** đối với mọi ca bất đồng hoặc ca khó.
4. **QA Lead B**:
   - Kiểm tra độc lập chất lượng và kỹ thuật theo phân công.
