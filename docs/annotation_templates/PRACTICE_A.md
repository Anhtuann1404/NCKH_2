# Thực hành đọc mẫu cho A — Trần Hồng Khải

Chuẩn bị 04/10/2026. Sáu tình huống dưới **hoàn toàn mô phỏng bằng văn bản**, dùng miền dành cho ví dụ `.invalid`. Không chứa HTML chạy, không lấy từ corpus, không phải pilot hoặc dữ liệu đánh giá. Đáp án là hướng dẫn do AI soạn để làm quen quy trình, không chứng nhận A đã thực hành/đồng ý hay thay codebook C khóa.

## Cách dùng

Với từng tình huống, đọc phần snapshot trước đáp án; thử ghi tên dịch vụ, vai trò, mục tiêu chính, bằng chứng, trạng thái lớp và điều cần bổ sung. Sau đó đối chiếu giải thích. Nếu chưa đủ bằng chứng, ghi thiếu thay vì đoán. Không nhập các ví dụ này vào `data/annotations/A/annotations.jsonl` hoặc tính thời gian của chúng thành pilot LABEL-01.

## PRACTICE-01 — Tên rõ, lớp chưa rõ

**Snapshot mô phỏng:** URL `https://account-gateway.invalid/verify`; heading “OneDrive account verification”; form có email/password; nút “Verify”; đích gửi `https://receiver.invalid/submit`. Không có tài liệu về chủ trang hoặc ủy quyền.

**Đọc mẫu:** ghi tên tự do “OneDrive”, vai trò tự nhận danh tính; mã dự kiến Microsoft theo ánh xạ đề cương, chỉ dùng mã thực sau codebook khóa. Mục tiêu chính dự kiến Microsoft vì tên dịch vụ gắn trực tiếp với form. Evidence: heading, trường nhập và đích form, kèm vị trí.

Lớp: `insufficient_evidence` trong bài tập này vì snapshot chưa cung cấp đủ bằng chứng kết luận lớp theo quy tắc khóa. Ghi quan hệ miền/ủy quyền chưa xác minh và chuyển ca khó. Việc xác định được mục tiêu không tự xác định được lớp.

## PRACTICE-02 — Nhắc thương hiệu trong bài viết

**Snapshot mô phỏng:** URL `https://tech-review.invalid/articles/storage`; title “So sánh Google Drive và OneDrive”; nội dung là bài so sánh dung lượng; không có lời tự nhận là Google/Microsoft và không có form trong snapshot.

**Đọc mẫu:** giữ tên Google Drive và OneDrive là tên quan sát, vai trò `mention_only`; không biến chúng thành hai mục tiêu mạo danh. Nếu codebook khóa phù hợp, trạng thái mục tiêu chính `no_clear_target` trong phạm vi nội dung đủ quan sát. Không có form trong snapshot khác với chứng minh toàn bộ trang không có form.

Lớp: chưa đủ bằng chứng kết luận benign chỉ từ đoạn bài viết. Cần nội dung/bằng chứng phù hợp nếu batch yêu cầu kiểm lớp. Bài tập nhấn mạnh phân biệt nhắc tên với tuyên bố danh tính.

## PRACTICE-03 — Hạ tầng chung không quyết định chủ nội dung

**Snapshot mô phỏng:** URL `https://tenant-space.invalid/form/37`; manifest mô phỏng cho biết host này là dịch vụ cho người dùng tự tạo form, không có whitelist danh tính. Heading “PayPal account support”; form hỏi email và OTP. Chủ tenant và quan hệ ủy quyền chưa biết.

**Đọc mẫu:** tên “PayPal” gắn với danh tính của vùng yêu cầu thông tin; ghi PayPal là mục tiêu quan sát dự kiến theo mã khóa. `domain_role` dự kiến `user_content_hosting` dựa trên manifest mô phỏng, không suy là miền first-party PayPal. Ghi yêu cầu OTP và vị trí làm evidence; OTP chỉ là tín hiệu quan sát, không tự quyết lớp.

Lớp/ủy quyền chưa xác minh thì giữ thiếu bằng chứng. Không coi form an toàn chỉ vì nhà cung cấp hạ tầng có uy tín và không coi tất cả nội dung người dùng là phishing.

## PRACTICE-04 — Nhiều mục tiêu ngang hàng

**Snapshot mô phỏng:** URL `https://mail-access.invalid/`; heading “Choose your email provider”; hai khối ngang hàng “Gmail” và “Outlook”, mỗi khối có form đăng nhập riêng; không có lựa chọn mặc định trong snapshot.

**Đọc mẫu:** lưu hai tên tự do, ánh xạ dự kiến Google và Microsoft theo codebook. Evidence riêng cho từng khối/form; giữ hai mục tiêu. `primary_org_status` dự kiến `multi_target`, `primary_org` không gán tùy ý. Tên đầu tiên trong DOM không tự là mục tiêu chính.

Lớp chưa đủ bằng chứng trong tình huống này; chuyển ca khó cho quy tắc nhiều luồng. Không click lựa chọn để tự tạo thêm dữ liệu.

## PRACTICE-05 — Ngoài danh mục khác với chưa xác định

**Snapshot mô phỏng:** URL `https://login-port.invalid/`; heading “Northstar University student portal”; form “University ID” và password. Phụ lục mô phỏng đã xác nhận Northstar University là một tổ chức hư cấu của bài tập, nằm ngoài 14 tổ chức dự kiến; không có bằng chứng về chủ website này.

**Đọc mẫu:** ghi đúng tên “Northstar University”, vai trò tự nhận danh tính và evidence form. Tình trạng danh mục `outside_catalog` trong bài tập; mục tiêu chính có thể `identified` nếu nhóm chốt cách tách hai trục như góp ý R-A01. Không gán `unknown` chỉ vì thiếu tên trong danh mục và không thêm tổ chức vào dictionary mô hình.

Mã máy ngoài danh mục do C quy định, A không tự tạo mã dùng tính kappa. Lớp/ủy quyền vẫn thiếu bằng chứng. Phụ lục mô phỏng không phải nguồn xác minh một tổ chức thật.

## PRACTICE-06 — Trang rỗng hoặc ảnh không đọc được

**Snapshot mô phỏng:** URL `https://portal-check.invalid/`; parser chỉ có “Loading…” và một ảnh không đọc được; không thấy form/title dịch vụ hoặc văn bản khác.

**Đọc mẫu:** không có tên dịch vụ đủ căn cứ; trạng thái tổ chức `unknown`, lớp `insufficient_evidence`. Evidence note: “Bản trích chỉ có Loading…, ảnh không đọc được; thiếu thông tin để xác định lớp/tổ chức.” Chuyển C yêu cầu nội dung/snapshot bổ sung; không suy tổ chức từ token URL hoặc nhãn nguồn.

Không dùng `no_clear_target` để thay cho `unknown`: ở đây thiếu nội dung, chưa đủ căn cứ nói trang không có mục tiêu rõ.

## Mẫu ghi một lượt đã điền cho bài tập

Ví dụ PRACTICE-06, chỉ để đọc:

| Trường | Cách ghi minh họa |
| --- | --- |
| sample_id/pass_id | `PRACTICE-06` / `practice-only` |
| annotator | AI soạn minh họa, chưa phải lượt người A |
| codebook/export version | Chưa áp dụng, bài tập mô phỏng |
| observed_service/org_targets | Chưa xác định / không có mục tiêu đủ bằng chứng để ghi |
| class_label | `insufficient_evidence` |
| primary_org/status | Không xác định / `unknown` dự kiến |
| identity_role/domain_role | Chưa rõ / chưa xác minh |
| evidence | “Loading…” trong bản trích; ảnh không đọc được |
| difficult_case/reason | Có / thiếu nội dung và ảnh đọc được |
| seconds_spent | Chưa đo giờ người, không điền số giả |
| provenance | Codex soạn đáp án mô phỏng, chưa có human verification |

## Tự kiểm trước khi nhận pilot thật

- [ ] Tôi phân biệt được tên quan sát, mục tiêu và nhãn lớp.
- [ ] Tôi phân biệt được `unknown`, `no_clear_target`, `outside_catalog` và `multi_target` theo bản khóa.
- [ ] Tôi biết ghi evidence có vị trí và không suy chủ trang từ hosting/logo/token URL.
- [ ] Tôi biết giữ ca khó thay vì ép nhãn và không nhìn target nguồn/lượt B.
- [ ] Tôi biết ghi giờ đọc/tra cứu/chuẩn hóa thực, tách nghỉ và phân xử phát sinh.

Các ô để A tự xác nhận sau thực hành, không được đánh dấu sẵn bởi AI.
