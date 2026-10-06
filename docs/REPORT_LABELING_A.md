# Phần báo cáo của A — phương pháp nhãn và bằng chứng nội dung

Cập nhật 06/10/2026: A đã hoàn thành 32 bản ghi V1, kiểm kỹ thuật đạt, nhưng nhóm đã vô hiệu hóa REAL-PILOT-32-V1 do sự cố độc lập/nguồn và trùng tập dượt. Không dùng nhãn, Kappa hoặc timing V1 làm kết quả nghiên cứu/PLAN-01; giữ nguyên hồ sơ để audit. REAL-PILOT-32-V2 chưa nghiệm thu/mở gán nhãn. Các câu “chưa có annotation thật” trong bản thảo dưới mô tả thời điểm soạn ban đầu; hiện chưa có pilot hợp lệ để báo cáo kết quả.

Chuẩn bị 04/10/2026, cập nhật trạng thái/disclosure 05/10/2026. **Bản thảo mô tả phương pháp dự kiến**, dựa trên đề cương 5.2b–c và DATA_PROTOCOL. Chưa có annotation thật, pilot thời gian hoặc phân xử; không sử dụng đoạn này như báo cáo kết quả đã thực hiện.

## Quy trình dự kiến

Sau khi thành viên C kiểm nguồn, cửa sổ dữ liệu và khóa danh mục/codebook, thành viên A sẽ đọc toàn bộ phần phishing được giữ lại qua view mù chỉ gồm mã mẫu, URL và nội dung trình bày an toàn. Lượt độc lập không tiếp cận nhãn/target nguồn, gợi ý từ bộ so khớp, điểm số mô hình hoặc nhãn của thành viên B. Nội dung được đọc từ bản trích/snapshot do C cung cấp, không chạy HTML nguồn như trang web thông thường.

A sẽ ghi tên thương hiệu/dịch vụ tự do và bằng chứng nội dung trước khi chuẩn hóa sang mã tổ chức. Hồ sơ lưu vị trí bằng chứng, vai trò tên đang tuyên bố danh tính hay chỉ được nhắc đến, nhiều mục tiêu nếu có, và trạng thái chưa xác định khi thiếu nội dung. Tên dịch vụ được giữ riêng với mã tổ chức để bảo toàn thông tin về thương hiệu con. Tổ chức ngoài danh mục có bằng chứng được phân biệt với chưa xác định; quan hệ ủy quyền chưa xác minh không được dùng để kết luận chắc chắn phishing hoặc benign.

Việc đối chiếu miền sẽ dùng phạm vi hostname/endpoint và ranh giới DNS trong quy tắc đã khóa. Hạ tầng nội dung người dùng, tenant, biểu mẫu hay kho lưu trữ của Google/Microsoft/Amazon không tự chứng minh chủ trang thuộc tổ chức đó. Trang nhắc tên tổ chức trong bài viết, trang đối tác và form đăng nhập cần được xét theo ngữ cảnh và đích thu thập thông tin. A sẽ kiểm toàn bộ hard benign đã chọn; nhãn phụ cho phân tích RQ3 được đọc tay hoặc để chưa xác định, không suy từ tín hiệu M3.

B sẽ gán độc lập 30% mẫu phishing ngẫu nhiên phân tầng và phần hard benign tương ứng, cùng các ca khó bổ sung. C sẽ tách membership ngẫu nhiên khỏi ca khó thêm và tính đồng thuận trước phân xử trên phần ngẫu nhiên. Ca khó vốn thuộc phần ngẫu nhiên vẫn giữ trong phần đó. Nhóm sẽ phân xử bằng bằng chứng, lưu lượt A/B gốc, nhãn cuối và lý do; A kiểm sự đầy đủ của nhãn cuối, C lưu phiên bản. A không tự sửa lượt B hoặc một mình quyết định bất đồng.

Pilot dự kiến gồm 20 mẫu kỹ thuật và 12 phishing bổ sung để có 20 phishing, được C loại khỏi tập đánh giá theo ID/hash/nhóm. A/B ghi riêng thời gian đọc, tra cứu, chuẩn hóa và phân xử. Trung bình phishing và benign được báo riêng; thời gian parser hoặc AI không đại diện giờ người. Nếu trung bình vượt 5 phút/phishing hoặc ngân sách A/B không đủ, nhóm sẽ giảm mục tiêu từ khoảng 2.000 xuống khoảng 1.200 và giảm tiếp nếu cần, trước xem kết quả mô hình.

## Số liệu phải bổ sung từ hồ sơ thực

| Chỉ tiêu | Hiện trạng | Bằng chứng cần có |
| --- | --- | --- |
| Số phishing/hard benign A được giao và hoàn thành | Chưa có batch | Manifest C và lượt A khóa |
| Pilot: số hoàn thành/thiếu, trung bình phút/phishing/benign | Chưa đo | Membership pilot, log thời gian người, điều kiện hỗ trợ AI |
| Tổng giờ A và quy mô chốt | A xác nhận 49 giờ/tuần; số tuần/quy mô chưa chốt | Số tuần thực, pilot, dự phòng, ngân sách B và quyết định nhóm |
| Tỷ lệ phủ tổ chức trong danh mục theo trang/miền | Chưa tính | Nhãn độc lập/cuối và group index C; nêu mẫu số rõ |
| Ngoài danh mục/chưa xác định/đa mục tiêu | Chưa tính | Codebook và counts thực, không gộp các trạng thái |
| Đồng thuận/kappa trước phân xử | Chưa tính | Lượt A/B khóa và subset random của C/B |
| Ca khó thêm, bất đồng, kết quả phân xử | Chưa phát sinh | Ca khó và adjudication log nhóm |
| Hỗ trợ AI trong lượt thật | Chưa có lượt thật | Provenance theo lượt và xác nhận người kiểm |

Không thay ô chưa có bằng số 0 khi chưa đo. Hiện tại 0 nhãn đã tạo chỉ mô tả hồ sơ A, không phải số mẫu corpus hoặc kết quả khảo sát.

## Giới hạn cần báo cáo sau thực hiện

Khoảng 70% phishing ngoài subset random chỉ có một lượt gán của A, trừ ca khó kiểm thêm. Đồng thuận cao không bảo đảm nhãn đúng. Cần báo phần nội dung thiếu/ảnh không đọc được, capture/time/source bias, ủy quyền không rõ, tác động hỗ trợ AI nếu sử dụng và việc quy mô thay đổi do giờ thực. Audit lớp khoảng 200 mẫu không thay gán tổ chức cho toàn bộ phishing giữ lại, và không chứng minh toàn corpus đã được nhóm kiểm thủ công.

## Dấu vết hỗ trợ soạn thảo

Codex hỗ trợ rà tài liệu, soạn hồ sơ và chuẩn bị công cụ ngày 04–05/10/2026. Theo yêu cầu người dùng, AI đã tạo riêng 20 nhãn tham khảo có lý do trên gói SYNTHETIC-PILOT-PRACTICE-V1; không phải nhãn chuẩn, chưa được người kiểm chứng và không đưa vào PLAN-01/kappa/huấn luyện/kết quả nghiên cứu. Bản ghi dùng simulated_A, is_dry_run=true, thời gian người không đo; không gửi đáp án này cho lượt độc lập B.

Chưa dùng AI để gán nhãn mẫu thật; chưa có lượt người A, đồng thuận hoặc thời gian pilot thực. Lượt độc lập thật tuân thủ R-A09: con người thực hiện, không dùng AI hỗ trợ quyết định nhãn. Khi có dữ liệu thật, A kiểm và cập nhật văn bản từ bằng chứng, nhóm công bố phạm vi hỗ trợ AI đúng thực tế.
