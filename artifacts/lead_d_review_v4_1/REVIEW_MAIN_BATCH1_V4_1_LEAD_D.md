# Kiểm Main Batch 1 Staging V4.1 — 23/11/2026

**Kết luận:** Hai điểm manifest/cohort commitment đã sửa đúng; dữ liệu staging giữ nguyên V4. Tuy nhiên có thay đổi mới trong sampler làm yếu fingerprint và cho metadata-only rerun tạo view rỗng. Giữ HOLD; cần sửa hồi quy mã và đính chính full SHA trước QA/duyệt phiên bản cuối.

## 1. Mục tiêu và phạm vi

Đối soát ZIP V4.1, manifest, lineage và thay đổi mã. Chạy hồi quy trên fixture và rehearsal chỉ trên bản sao ledger tạm. Không chọn/gợi ý nhãn hoặc áp dụng ledger thật.

## 2. Owner và kiểm độc lập

C sở hữu mã/hiện vật; B QA độc lập phần bổ sung theo commit cuối. Codex hỗ trợ D kiểm kỹ thuật, không ký thay B/D. Báo cáo C dán hai lần được coi là một thông báo bàn giao.

## 3. AI và dữ liệu

Công cụ local chỉ xuất số đếm/boolean/hash. Không xuất nội dung mẫu, URL/UID thật hoặc salt. Không sao ZIP thật vào artifacts công khai. Các probe mới dùng dữ liệu giả hoàn toàn.

## 4. Hiện vật và sai lệch commit

ZIP **644.720 bytes**, SHA-256 `5c3e23eac2082ac96b8d3f09beebd59317a98a56dd630d6398d1fa731bd1f6c8`; CRC tốt, **24/24 hash thành phần khớp**.

Full SHA C ghi `28462fc48f29bf4244f77c2aa5b214f4eb04c54e` không tồn tại theo GitHub API (422 No commit found). Commit thực tế trên nhánh remote, đã kiểm bằng Git và GitHub API:

`28462fcece5883a652779976e342d939f7a81e5a`

Hai chuỗi có cùng short SHA, không được dùng thay nhau. C cần đính chính rõ, bảo lưu thông báo cũ; B ký đúng full SHA thực tế sau sửa. Không coi lỗi ghi SHA này là bằng chứng mã không tồn tại.

## 5. Các phần đã khép và được giữ

- Manifest A/B có đủ trường bắt buộc, hash view/Codebook/dictionary khớp; pending/false đúng. CLI thật dừng tại “CHƯA NGHIỆM THU”, không tạo JSONL, không hiển thị mẫu.
- Proposal giữ cohort_seed_commitment theo block1 lịch sử; seed_commitment khớp salt phát hành V4 và khác cam kết cohort.
- Hai view, mapping, quần thể, registry, dossier, audit nguồn và ledger thật trùng nguyên byte V4. Salt và seed không đổi. Các kiểm nguồn/fingerprint/provenance/exclusion đã làm ở V3 được giữ cho đầu vào không đổi, không kết luận dữ liệu bàn giao bị hỏng.
- Scanner đã thu hẹp câu kết luận theo phạm vi blacklist thực tế.

## 6. Hồi quy mới cần sửa

### R1. Fingerprint tin hash truyền sẵn thay cho HTML thật

Diff mới trong src/phishing/data/main_sampling.py thay cách tính hash bằng `c.get("html_sha256") or sha256(html)`, tương tự dùng giá trị url_raw/url_normalized/url_sha256 được cấp sẵn. Đây là thay đổi mã ngoài hai mục metadata C tóm tắt.

Probe tổng hợp cung cấp HTML cùng html_sha256 nhất quán, sau đó thay HTML nhưng giữ hash cũ. Fingerprint mới vẫn bằng fingerprint ban đầu. Trên bản9367288, chính probe này đạt: fingerprint thay đổi. Đây là hồi quy tái lập, không chỉ suy đoán.

**Sửa tối giản:** giữ fingerprint nguồn lấy byte URL/HTML làm căn cứ. Ưu tiên hoàn nguyên phần nới lỏng sampler và dùng verifier canonical metadata riêng đã có. Nếu cần chấp nhận cả raw và hash khai báo, tính từ raw và kiểm nhất quán; không để hash khai báo che thay đổi raw. Khi các biểu diễn URL cùng có mặt mà mâu thuẫn, xử lý rõ thay vì âm thầm ưu tiên. Không cần thiết kế lại toàn pipeline.

### R2. Metadata-only rerun được gọi là idempotent dù nội dung view mất

prepare_main_batch1_successor_v4_1.py dựng candidates_pool từ canonical metadata, không có HTML. Với nới lỏng ở R1, sampler vẫn khớp fingerprint lịch sử, tiếp tục trích xuất nội dung từ HTML rỗng. Script C chỉ kiểm ID/count và số block, không so view payload.

D tái lập bằng fixture: sealed ledger tạo từ raw candidates, sau đó rerun metadata-only không bị từ chối. Probe đòi dừng an toàn bị failed. Chính probe đó trên9367288 đạt vì input metadata không vượt được fingerprint nguồn.

D cũng chạy đường metadata-only đúng như C trên COPY của proposal/gói V4.1: trả100viewA và30viewB, **100/100A và30/30B có page_text rỗng**; cả hai không bằng view trong ZIP. Ledger thật và view ZIP không bị thay đổi. Đúng ID không chứng minh đúng nội dung.

**Sửa:** rehearsal sampler phải dùng raw HTML/URL lấy từ Parquet đã khóa, kiểm source row/hash trước khi dựng input. So sánh đầy đủ view/content hash/structure và cohort/B30/thứ tự sau hai rerun với gói đã niêm phong. Nếu chỉ có metadata, chỉ xác minh trạng thái ledger/fingerprint metadata trong verifier riêng và ghi đúng giới hạn; không gọi sampler render hoặc báo E2E/payload idempotent. Giữ fail-closed khi thiếu raw payload cho đường cần render.

### R3. Đính chính run/commit lineage

Dùng full SHA thực tế, liệt kê main_sampling.py đã thay đổi và đánh giá tác động. Log165 test hiện có không bao phủ hai trường hợp R1/R2. B kiểm thêm probe D trên commit sửa cuối; không kế thừa QA baseline cho phần nới lỏng vừa thêm.

## 7. Kết quả kiểm thử

Môi trường D: Python3.14.6/pytest7.4.0, clean checkout actual28462fc.

- 12 tệp chọn lọc: **165passed in6.45s**,0failed/skipped.
- Hai probe mới: **2failed in0.11s** trên actual28462fc.
- Cùng probe nguyên byte trên9367288: **2passed in0.10s**.
- Scanner hiện hành PASS trong phạm vi được quét.
- CLI preflight gói thật: cả A/B dừng đúng pending, không có output.
- Không chạy toàn repository hoặc áp dụng migration thật. Không cộng165pass và2fail thành kết luận toànrepo.

Lệnh đầy đủ ở COMMANDS.md, raw log và probe kèm. Không sửa test cũ để làm thay kết quả.

## 8. Phương án xử lý tiếp

C giữ nguyên dữ liệu/salt/ID/cohort V4.1 và hai điểm metadata đã khép; sửa đúng R1/R2 bằng cách tách verifier metadata khỏi sampler cần raw payload. Không chạy lại từ đầu để sinh salt hoặc chọn mẫu mới. Tạo commit sửa và báo cáo đính chính cùng raw log; chỉ thay rehearsal/report/hiện vật phụ thuộc khi cần, bảo lưu ZIP cũ. B dùng fixture để QA commit cuối, D kiểm gói hạn chế và quyền áp dụng riêng.

## 9. Giới hạn

File Parquet tạm D dùng ở các phiên trước không còn tại đường dẫn đó trong lượt này; không chạy lại raw-source rehearsal tại phiên23/11. Các hiện vật nguồn/view giữ nguyên byte V4 nên bằng chứng nguồn trước vẫn áp dụng. Việc này không cản hai probe tổng hợp hoặc tái lập đường metadata-only trên bản sao. Chưa nhận QA B cho actual28462fc hoặc bản sửa tiếp theo.

## 10. Trạng thái quản trị

MainHOLD/LOCKED, ready_for_annotation=false, acceptanceB/Dpending, training_blocked=true,official_test_used=false. Ledger thật trong ZIP vẫn nguyên byte hai block. Không sửa mã C, không commit/push, không đổi gói/cohort/salt, không phát view hoặc mởPass1 trong phiên kiểm.
