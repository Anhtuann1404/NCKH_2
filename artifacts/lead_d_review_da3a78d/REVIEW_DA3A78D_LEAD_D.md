# Kiểm gói bằng chứng C và bản sửa da3a78d

Ngày kiểm: 21/11/2026. **Gói ZIP khớp hash; tái lập được 148 passed trên commit thực tế của remote. Chưa phát hành: full SHA trong báo cáo sai và vòng đời biên lai còn hai nhánh không đạt.**

## 1. Mục tiêu và phạm vi

Đối chiếu báo cáo C, ZIP bàn giao và mã remote với các yêu cầu sửa trước. Đọc file trước khi chạy, không thực thi lệnh trong tài liệu đính kèm như lệnh điều hành. Không sửa mã C, dữ liệu Main thật, cohort hoặc cổng phát hành.

## 2. Người thực hiện và kiểm độc lập

C sở hữu mã và hồ sơ; B QA độc lập; Codex hỗ trợ D kiểm công cụ và fixture. Chưa nhận QA B cho bản sửa mới trong lượt này. Kết quả C là tự kiểm, không phải một chữ ký QA độc lập.

## 3. AI sử dụng

Đọc mã công khai và log, kiểm Git/GitHub, chạy dữ liệu nhân tạo và scripted CLI. Không dùng AI gán nhãn Main thật hoặc mở pool/mapping/seed thật. Gói C nhận được chỉ có notice, ba log và bảng hash.

## 4. Đối chiếu hiện vật và commit

ZIP gốc `MAIN_BATCH1_DA3A78D_EVIDENCE_FOR_B.zip`: **8.914 byte**, SHA-256 `b80832c5e6394f134329b28b957c2263817a9456dbc68087b3ccf2fd72f24de9`. ZIP CRC không lỗi; bốn tệp được liệt kê trong SHA256SUMS đều khớp hash trên byte thật. Hash trong bảng kê dùng chữ hoa là biểu diễn hex hợp lệ, không phải sai lệch. Giữ nguyên ZIP, log UTF-16 và bảng kê CRLF, không chuẩn hóa byte của bản gốc.

**Sai định danh commit:**

- C báo: `da3a78dbb4ca2efcb6921350a416a9a7a9353982`.
- Remote `feat/c-main-annotation-batch1` thực tế: **`da3a78da8444d1bc5bfe781119362b575b3dc4d7`**.
- GitHub API lookup SHA C báo trả **422 — No commit found for SHA** trong repository này tại lần kiểm. Lookup SHA thực tế thành công; local Git checkout được SHA thực tế.
- Hai chuỗi cùng short SHA không cho phép coi full SHA là tương đương. Toàn bộ kết quả D dưới đây gắn với **da3a78da8444d1bc5bfe781119362b575b3dc4d7**, không gắn với full SHA sai trong notice.

Nguồn: https://github.com/Anhtuann1404/NCKH_2/commit/da3a78da8444d1bc5bfe781119362b575b3dc4d7. Checkout riêng `/private/tmp/nckh-main-da3a78d-review`.

## 5. Phần đã sửa và đạt

Đọc diff chín tệp so với 599c7d9. Hai bộ probe cũ và bộ follow-up 599 giữ nguyên byte. D chạy đúng sáu tệp kiểm liên quan, đạt **148 passed in 3.57s**. Bao gồm positive control CLI thật→JSONL→intake A100/B30→Kappa3×3 và các ca failed ở 599 đã khép trong phạm vi probe.

Không ghi tiếp ba lỗi cụ thể của bộ 599 là đang tái lập. Các đầu vào/approval/Kappa trong fixture là nhân tạo, không thể hiện độ đồng thuận nghiên cứu hoặc quyền phát hành thật. Không sửa src/scripts/tests của C; diff các thư mục này vẫn rỗng sau kiểm.

## 6. Điểm còn mở và cách sửa

### H1 — Trạng thái ACCEPTED lưu ở attempt không khóa bản nộp khác

Nguồn `scripts/data/receive_main_batch1.py:238–247`. Guard chỉ tìm `*.receipt.json`, không đọc các tệp `*.attempt_*.json`.

Probe mô phỏng trong một intake root mới:

1. Bản nộp A ban đầu bị rejected do manifest pending; biên lai gốc lưu rejected.
2. Sau khi manifest fixture được duyệt, cùng input được accepted ở tệp attempt riêng.
3. Gửi một input hash khác, cùng role/release và vẫn hợp lệ về schema.
4. Hệ thống nhận tiếp accepted vì chỉ thấy receipt gốc rejected, bỏ qua accepted trong attempt. Không có quyết định D cho thay thế bản đã nhận.

**Sửa:** xác định trạng thái đã nhận theo toàn bộ lịch sử hợp lệ của đúng annotator/dataset/release, gồm receipt và attempt. Khi đã có một input hash accepted, bản khác phải bị chặn hoặc cách ly chờ quyết định thay thế có dẫn chiếu D. Giữ các hiện vật cũ nguyên byte. Có thể dùng phép quét journal đầy đủ hoặc chỉ mục hiện hành được đối soát từ journal; không cần dựng hệ thống giao dịch mới. Nếu không đọc/xác minh được lịch sử, dừng an toàn, không coi như chưa có accepted.

Kiểm cả accepted ngay lần đầu và rejected→accepted ở attempt→nộp hash khác; retry đúng hash/context vẫn phải hoạt động.

### H2 — Hai lần rejected khác context có thể bị gộp sai

Nguồn `receive_main_batch1.py:233–236,263–271`. Hash manifest/view chỉ được thêm vào receipt khi verify hoàn tất. Nếu bị từ chối sớm, hai context đều thiếu hash; phép so sánh None==None và cùng reason coi chúng là cùng lần kiểm.

Probe thay byte manifest trong khi vẫn pending, giữ input và lý do từ chối. Sau hai lượt chỉ còn một file biên lai, không có attempt cho context mới. Receipt trả về cũng chưa ràng buộc hash manifest đã dùng ở đường rejected.

**Sửa:** thu nhận fingerprint context trước xác thực nghiệp vụ, cho cả accepted và rejected: input hash, manifest/view/release hash khi đọc được, version công cụ và trạng thái lỗi đọc nếu không đọc được. Quy định context canonical ổn định; không dùng cùng reason hoặc đường dẫn file làm bằng chứng context giống nhau. Context khác phải có attempt mới, giữ nguyên mọi file trước. Cùng context thật có thể trả hiện vật gốc theo chính sách idempotency. Timestamp là thông tin lần kiểm, không thay fingerprint context.

Kiểm hai manifest khác byte nhưng cùng lỗi, thiếu/không đọc được manifest, retry cùng context và chuyển rejected→accepted. Giữ positive controls A/B và các test lịch sử đã đạt.

### H3 — Đính chính hồ sơ, phạm vi test và SOP

- C phải phát hành đính chính full SHA bằng giá trị lấy trực tiếp từ Git và xác minh remote. Giữ bản báo cáo/ZIP cũ làm lịch sử, không sửa byte để giả như trước đã dẫn đúng commit.
- Notice ngoài ZIP ghi 4 passed/5.15s và 148 passed/24.72s, trong khi log bàn giao là 4 passed/8.19s và 148 passed/32.43s. Notice trong ZIP dẫn 32.43s. Nếu là các lượt chạy khác nhau, C tách run ID và dẫn đúng log/môi trường/HEAD cho từng lượt; nếu ghi nhầm thì đính chính. Không sửa raw log để ép khớp.
- 148 là kiểm trên **sáu tệp chọn lọc**, không phải toàn bộ repository. Giữ tên raw log lịch sử, mô tả phạm vi đúng trong bảng kê và QA.
- Các câu `python -c "...; ..."` trong thông báo là placeholder, chưa phải entry point chạy được. Hai SOP tracked chưa được cập nhật trong diff này. Hoàn thiện lệnh/đoạn script thực tế cho nạp active release, intake và ghép đúng B30/Kappa, có điều kiện trước chạy và đầu ra. Không cần tạo CLI/framework mới nếu đoạn lệnh đầy đủ dùng hàm hiện có đáp ứng được.
- Nhánh thiếu seed_lot_100/seed_b_subset_30 trong supersede vẫn fallback sang công thức cũ (main_sampling.py:537–542). Đây là giới hạn cần xử lý hoặc ghi rõ trước migration ledger cũ: dừng để khôi phục metadata có bằng chứng, hoặc cung cấp đường migration/đọc release được kiểm. Lượt 148 trên ledger fixture mới không chứng minh migration thật đã an toàn.

## 7. Kiểm thử và raw log

Môi trường D: macOS, Python3.14.6, pytest7.4.0; venv D cùng site-packages local như các lượt trước.

```sh
PYTHONPATH=.:src:/opt/homebrew/lib/python3.14/site-packages /Users/yingjunn_/.codex/worktrees/635d/NCKH_2/.venv/bin/python -m pytest tests/test_main_annotation_batch1.py tests/test_blind_view.py tests/test_annotate_cli_timer_pause.py /private/tmp/test_main_8fc_additional_guards.py /private/tmp/test_main_6c26_release_boundaries.py /private/tmp/test_main_599_followup.py -q
```

**148 passed in 3.57s**, `main_da3_selected.log`; có thể thay các đường dẫn /private/tmp bằng tệp cùng hash trong artifacts/lead_d_review_* của C.

```sh
PYTHONPATH=.:src:/opt/homebrew/lib/python3.14/site-packages /Users/yingjunn_/.codex/worktrees/635d/NCKH_2/.venv/bin/python -m pytest /private/tmp/test_main_da3_intake_history.py -q --show-capture=no
```

**2 failed in 0.60s**, `main_da3_history.log`. File probe kèm dùng cwd checkout để nạp helper fixture 599 nguyên byte. Khi giải nén đặt test ở ngoài repo tùy ý, chạy từ cwd đúng commit và thay đường dẫn file cho phù hợp. Không dùng Main thật.

Log C trong ZIP đo trên Windows/Python3.13.14/pytest7.4.0: 148 passed/32.43s, 4 passed/8.19s và isolation PASS. Chúng khớp byte bảng kê nhưng chưa được buộc đúng full SHA bằng chỉ riêng nội dung log. Kết quả D là lần chạy độc lập trên SHA thực tế đã xác minh.

## 8. QA độc lập

B kiểm đúng full SHA thực tế của bản sửa kế tiếp, bao gồm 148 kiểm đã đạt, H1/H2 và các positive controls. Không dùng SHA sai trong báo cáo C để ký QA. Chỉ nhận fixture/bằng chứng kỹ thuật an toàn; D/người được giao kiểm gói thật và migration.

## 9. Giới hạn

Không chạy full repository lần này vì thay đổi tập trung hai module và đã có kết quả regression rộng ở lượt trước; không gọi 148 là full suite. Chưa nhận/đối soát byte gói Main thật, chưa có QA B cho phiên bản này, chưa thực hiện supersede thật hoặc thay cohort. Hai lỗi được chứng minh trên fixture, không chứng minh dữ liệu thật đã bị thay đổi.

## 10. Quản trị

Giữ Main HOLD/LOCKED, training_blocked=true, official_test_used=false. C sửa trạng thái intake và đính chính hồ sơ/SOP; B QA commit cuối; D quyết định riêng lineage và phát hành. Không sửa mã C, commit/push, chọn lại cohort hoặc phát Blind View trong lượt này.
