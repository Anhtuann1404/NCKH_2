# Kiểm Main Batch 1 Staging V4.2 — 23/11/2026

**Kết luận kỹ thuật:** Hai hồi quy raw/hash và metadata-only đã khép trong các phép kiểm D tái lập. Raw-source rehearsal của đúng proposal khớp view đã niêm phong và không append khi rerun. Chưa áp dụng ledger thật hoặc phát hành; chuyển B QA đúng commit cuối, hoàn tất hồ sơ và D quyết định riêng.

## 1. Mục tiêu và phạm vi

Kiểm bản sửa R1/R2, commit, ZIP, manifest/lineage, dữ liệu bất biến và rehearsal từ raw Parquet trên bản sao ledger. Không gán/gợi ý nhãn hoặc mở phiên thật.

## 2. Owner và người kiểm

C sở hữu mã/hiện vật; B QA độc lập phần bổ sung. Codex hỗ trợ D kiểm kỹ thuật hiện vật thật và fixture. Báo cáo không thay quyết định D hoặc chữ ký B.

## 3. AI và dữ liệu

Chỉ đọc kỹ thuật local; log/report không có nội dung mẫu, URL/UID/row thật hoặc salt. Tải lại shard công khai đúng revision khóa để kiểm, không gửi dữ liệu hạn chế ra ngoài. ZIP thật không được chép vào public artifacts.

## 4. Phiên bản và toàn vẹn

- Remote HEAD đúng `ac2cf1d82d9a742ec0f5e9af81e0ce116fdfbe3d`.
- Core fix `fb487540aa6c877553eeb9e0978437642a4173b1` tồn tại và là ancestor. CommitHEAD chỉ đổi báo cáo isolation so với corefix; mã/test không khác ở hai mốc này.
- ZIP646.230bytes, SHA-256 `99defd93b7e7f616a71818b79349ac2d6ee12dc78f540eb6c3d853cbda67a1b4`; CRC tốt. Có **26 tệp tổng cộng =25hiện vật được đối chiếu hash +SHA256SUMS.txt**;25/25mục bảng kê khớp.
- Shard tải lại từ source URL đúng revision:322.018.201bytes,SHA260cb9c93299f6b244d48321fe115523159770f4e73446b382473628c6e81d74, tính lại trước replay.

## 5. Các phần được kiểm đạt

- 13 tệp chọn lọc: **167passed in6.85s**,0failed/skipped. Bao gồm nguyên hai probe D từng failed. File probe trong ZIP trùng nguyên byte D gốc.
- Fingerprint tính lại từ raw URL/HTML; dữ liệu hash/normalized mâu thuẫn bị từ chối. Probe HTML đổi giữhashcũ đạt; sealed metadata-only rerun bịValueError.
- View A/B, mapping, canonical metadata, UID lịch sử, registry, dossier, audit nguồn và ledger thật giữ nguyên byte V4.1. Salt/seed giữ nguyên; không chọn lại cohort hoặc sinhID mới.
- Manifest đủ trường/hash, pending/false; CLI thật dừng đúng “CHƯA NGHIỆM THU”, không tạoJSONL.
- cohort_seed_commitment theo block1, seed_commitment theo salt phát hành hiện hành, hai giá trị tách biệt đúng.
- Scanner PASS trong phạm vi đã công bố, không phải chứng minh không có mọi dạng rò rỉ.

## 6. Rehearsal bằng nguồn thật trên bản sao

D dùng Parquet vừa tải đúng hash, hydrate raw candidates theo canonical source_row, ghi đúng proposal V4.2 vào ledgerCOPY rồi gọi sampler thật hai lần:

- Hai sự kiện lịch sử giữ nguyên.
- Bản sao có3events, rerun không ghi thêm hoặc sửa byte.
- View A100/B30 trùng nội dung/structure/hợp đồng/thứtự của gói đã niêm phong.
- Metadata-only bị từ chối, bản sao không đổi.
- Ledger thật không áp dụng migration; trongZIP vẫn là hai block lịch sử.

D so sánh payload bằng cấu trúc JSON/giá trị trường; fileview trongZIP được đối chiếu nguyênbyte với bản trước. Không dùng cụm “byte-for-byte” để ngụ ý mọi cách serialization khác nhau cũng cùnghash.

## 7. Đính chính nhỏ về cách báo cáo, không cần đổi dữ liệu

A có100mẫu:97page_text không rỗng,3page_text rỗng theo `.strip()`; B30/30khôngrỗng. Các giá trị này giữ nguyên từ trước và viewrerun khớp bảnniêmphong. C nên ghi “không phát sinh view rỗng do lỗi metadata-only/rerun”, thay câu “0viewrỗng” chung chung. Không yêu cầu đổi nhãn, điền text hoặc thay3mẫu để làm đẹp số liệu.

Số đếm ZIP nên ghi rõ25hiện vật đối chiếuhash và1bảngkê,26tệp tổng. Chỉ cần đính chính thông báo nếu hồ sơJSON đã đúng, không cần repack hoặc đổi salt/cohort vì câu chữ.

## 8. Hồ sơ QA còn cần hoàn tất

Tại HEADac2, file Git mang tên phụ lụcQA V1.7 vẫn là notice8.434bytes/hashc34cfb04...,chưa phải fullQA20.658bytes/hash3fecd1ef... Dđãnhận. C cần lưu notice bằng tên riêng và phục hồi bản gốc đúng đường dẫn; không sửa nội dung QA hoặc xóa lịch sử. Đây là việc lưu artifact,không phải lỗi sampler mới.

B đã báoV1.8FAILcho28462fc trước sửa; chưa nhận QA cuối choac2/corefb48754. Chuyển B fixture/commit cuối để kiểm167hồi quy hoặc bộ tương đương được liệt kê rõ. B có thể có tổng165 vì không chọn hai purefixturetests bổ sung ngoài repo củaD; phải đối chiếu danh sách,không coi chênhcount là sai mặc định. Không gửi B dữ liệu thật.

## 9. Giới hạn

Không chạy toànrepo ở lượt này;167là bộ chọnlọc. Các kết quả nguồn/provenance/exclusion từV3/V4 áp dụng do byteinput giữ nguyên; lượt này đã tái chạy raw-source proposal với shard tải lại đúnghash. Không có phán quyết nhãn mẫu hoặc chứng nhận sạch tuyệt đối. Không yêu cầu C mở thêm vòng sửa mã khi chưa có lỗi mới.

## 10. Trạng thái và bước tiếp theo

D có bằng chứng để xem xét nghiệm thu kỹ thuật bản sửa; B QA cuối và việc lưu hồ sơ còn mở. Sau đó D quyết định riêng phạm vi ghi block2 vào ledger thật, rồi đối soát trạng thái sau ghi. Mở phát hành/Pass1 là quyết định riêng; hiện MainHOLD/LOCKED,ready=false,acceptancepending,training_blocked=true,official_test_used=false. Không sửa mãC/commitpush/migration thật hoặc phátview trong lượt này.
