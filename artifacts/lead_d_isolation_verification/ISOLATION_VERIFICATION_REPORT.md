# Bằng chứng kiểm cách ly dữ liệu bằng mã thật

## 1. Mục tiêu và phạm vi
Khép điểm thiếu phép kiểm file nhãn → ID loại trừ → RunPlan.validate thật và chặn cờ cách ly trong bộ kiểm đầu vào. Không cấp quyền huấn luyện nghiên cứu, chọn mẫu Main hoặc phát Blind View.

## 2. Người thực hiện / người kiểm độc lập
AI hỗ trợ Lead D triển khai và kiểm trực tiếp tại workspace D. Bản sửa cần B tái kiểm và C tích hợp vào phiên bản vận hành chung trước khi được gọi là nghiệm thu nhóm. Đây không phải chữ ký QA độc lập do AI tự cấp.

## 3. AI đã dùng
Codex hỗ trợ đọc mã, sửa guard, viết test, thực thi local và lập báo cáo. Không dùng AI chọn nhãn. Công cụ local đọc gói hiệu chuẩn được D cho phép; chỉ xuất số liệu tổng hợp, không xuất nội dung mẫu hay nhãn cấp mẫu.

## 4. Đầu vào đã khóa
Base D: b31a1b1c35192a69e8acf8224f17523a4ff56f12. Bản sửa hiện là working-tree diff, chưa commit/push. Gói hiệu chuẩn nguyên byte e0bb55e8be1e0d9bad996bcdfbc2b1401bcbfcdcf207fec78b9219cc3961bd12 được kiểm toàn bộ SHA256SUMS trước khi dùng. Nhãn JSON SHA c853758421c15271fc6c34e3dc40203fcb55c770c3e651eb9336094ec2626c43; CSV SHA7cf9d7704b1c64c6d9f453a48bf0ee37b2e317bcdf1dca7e213d98fcc13714c7. Không sửa các tệp này.

## 5. Thay đổi thực tế
- readiness.py: load_isolated_ids đọc tệp JSON/CSV đã khóa hash, yêu cầu metadata cấp dòng, kiểm kiểu boolean và ID. check_run_plan_isolation chuyển các ID đó vào RunPlan.validate thật. check_training_inputs đọc cờ cách ly từ cả index lẫn labels và từ chối bản ghi bị cách ly.
- experiment.py: dùng assert_fixture_cohort đã có tại đầu fit_fold để chặn đầu vào ngoài fixture trước khi dựng mô hình.
- Thêm test_label_isolation.py và mở rộng test_training_readiness/test_training_pipeline. Không dùng simulate_runplan_validate, không sửa RunPlan để làm phép kiểm đạt.
- Không thay file gốc/khóa dữ liệu. Patch áp dụng trên base D b31a1b1, không tuyên bố đã có trong nhánh C8643f55 vốn thiếu các module training này.

## 6. Tự kiểm bằng hiện vật thật
- Adapter đọc riêng cả JSON và CSV gốc, nhận đúng24ID bị cách ly, bao gồm16mẫu binary_model_eligible=true.
- 24ID × 2định dạng × 3partition =144lần gọi RunPlan.validate thật đều từ chối đúng lý do Pilot/reserved.
- 24bộ metadata cách ly thật × 3vị trí train/validation/test trong hợp đồng fixture hợp lệ =72lần check_training_inputs thật đều từ chối đúng lý do Isolated sample entered input cohort. Đây là phép kiểm hợp đồng có cờ thật, không phải chạy research loader hoặc nạp HTML mẫu thật.
- 3positive control đi qua; đầu ra fixture vẫn research_training_allowed=false. Research scope bị chặn.
- Bài test fit_fold kiểm đầu vào ngoài fixture bị chặn và make_pipeline chưa được gọi. Script real24 không fit mô hình nào; full-suite có các phép fit fixture tổng hợp sẵn có.

## 7. Kiểm thử và độ ổn định
Lần1 trên bản trích xuất sạch base D cộng patch:95passed in1.87s. Lần2 trên workspace D sau áp dụng:95passed in1.87s,0failed,0skipped. Các test này là suite D, KHÔNG phải446test nhánh C. git diff --check đạt. Môi trường Python3.14,pytest7.4.0 trong635dvenv. Lệnh:

```
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src .venv/bin/python -m pytest tests/ -q -p no:cacheprovider
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src .venv/bin/python artifacts/lead_d_isolation_verification/verify_real24.py --pack /duong-dan/goi-e0bb55e8.zip
```

Hash mã sửa và log nằm trong SHA256SUMS.txt. Script đối soát đòi hỏi đúng gói gốc; gói bàn giao kiểm này không chứa dữ liệu cấp mẫu.

## 8. QA độc lập
Đã có bằng chứng thực thi trực tiếp trên máy D và hồi quy lại trong workspace. Chờ B kiểm patch theo base/version và C tích hợp vào code chung. Không kế thừa QA C8643f55 cho patch D này.

## 9. Giới hạn và việc tiếp theo
- RunPlan bản thân chỉ kiểm excluded_ids được truyền; adapter mới chịu trách nhiệm đọc cờ từ tệp. Gọi RunPlan trực tiếp không tự đọc mọi tệp nhãn trên đĩa.
- check_training_inputs vẫn fixture-only và cố ý chặn nghiên cứu. Chưa có hợp đồng loader nghiên cứu chính thức để nghiệm thu đầu-cuối với Main Corpus; cần C/D thiết kế, tích hợp và QA riêng trước mở training.
- Chưa hợp nhất nhánh C với base D; vì vậy khép được phép kiểm kỹ thuật tại D, chưa gọi cổng huấn luyện nhóm là hoàn tất.
- Các lớp chống trùng URL/HTML/domain/template thuộc kiểm nguồn C, không được thay bằng so ID của RunPlan. Tái lập train001 trước đó là hồ sơ riêng.

## 10. Quản trị
Giữ training_blocked=true,official_test_used=false,MainLOCKED. Không phê duyệt thay D/B. Không sửa nhãn nguyên byte hay phát mẫu.
