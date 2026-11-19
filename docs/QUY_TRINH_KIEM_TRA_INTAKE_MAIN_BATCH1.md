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

## 3. QUY TRÌNH GHÉP CẶP VÀ ĐÁNH GIÁ ĐỘ ĐỒNG THUẬN (KAPPA)
1. **Ghép cặp 30 mẫu chung**:
   - Thành viên C sử dụng trường `blind_id` để ghép cặp 1-1 giữa kết quả của A và kết quả của B trên đúng 30 mẫu đã niêm phong.
2. **Tính toán Cohen's Kappa 3x3**:
   - Chạy module `phishing.annotation.kappa_3x3` trên 30 mẫu ghép cặp.
   - Xuất ma trận nhầm lẫn (confusion matrix) 3x3 và chỉ số thỏa thuận quan sát ($P_o$), chỉ số kỳ vọng ($P_e$), và hệ số $\kappa$.
3. **Lập danh sách ca bất đồng**:
   - Lọc tất cả các mẫu trong 30 mẫu mà A và B không đồng thuận nhãn (`label_A != label_B`).
   - Lọc tất cả các ca mà A hoặc B đánh dấu cờ ca khó.

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
