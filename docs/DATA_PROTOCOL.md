# Data protocol v0.1

Đối chiếu đề cương 5.1 và 5.2a–c/g. Đây là quy trình sẽ triển khai; phần đã thực hiện nằm trong CURRENT_TASKS và source_audit.

## Thứ tự khóa

`revision/checksum → audit chỉ date → cửa sổ/quý → dictionary/codebook → pilot/giờ → sampling plan → mở mẫu chính → nhãn/QC → groups/splits`.

C thực hiện audit date bằng đọc cột, không hiển thị label/target/URL/HTML tập chính. Không kết luận min/max toàn corpus từ 20 mẫu hoặc statistics API thiếu date. Sau khóa dictionary mới mở mẫu chính. Metadata revision đã quan sát là `eabec4b7a66324b79cc8a0ad856d1731dc26fe1a`; đây chưa phải xác nhận revision của rows API hoặc tệp tập chính.

## Nguồn và quyền

Tập chính từ official train PhreshPhish, ưu tiên tiếng Anh và cửa sổ dự kiến 01/10/2024–31/12/2025; xác nhận theo date audit. Ghi license và điều kiện nghiên cứu chống phishing đúng bản nguồn. Official test giữ ngoài phát triển; PhishVN/crawler là bổ sung. Crawler chỉ benign không được ghép thành nguồn benign đối lập phishing từ corpus.

Manifest dùng mẫu [source_manifest.example.json](../configs/source_manifest.example.json): ghi URL nguồn, revision, path/hash/size tệp, thời điểm, split, license, điều kiện, quyền phân phối và người kiểm. Giá trị null hoặc status draft không được xem là xác minh. Trước công bố, che thông tin nhạy cảm và chia sẻ chỉ phần được phép; có thể công bố index/quy trình thay HTML.

## Hợp đồng bản ghi nghiên cứu

Lưu raw ở khu vực hạn chế; index và nhãn là file tách biệt. Schema dự kiến:

```text
sample_id             mã nội bộ ổn định, không là feature
source_id/revision    nguồn/phiên bản
source_split          train/test nguồn
collected_at          ngày thu + trạng thái valid/missing/invalid
raw_url_path          tham chiếu URL hạn chế, không log runtime
html_path/sha256      tham chiếu HTML và hash nội dung
language             thuộc tính/QC, không là feature học
capture_mode         raw/rendered/unknown, metadata QC
source_label/target   giữ riêng chỉ C; không hiện lượt gán độc lập
group_id             miền + nhóm gần trùng, không là feature
exclusion_reason     null hoặc lý do loại theo quy tắc
```

Adapter schema nguồn phải được kiểm theo revision; không mặc định target có đủ hoặc đúng. Với URL thiếu scheme, chuẩn hóa bằng quy tắc xác định và lưu raw/normalized riêng; mẫu không xác định URL hợp lệ được ghi lỗi trước lấy features.

## Dictionary và codebook

Mỗi entry: org_id, display_name, aliases, service_names, domain_rules, nguồn/ngày xác minh và hiệu lực lịch sử. Domain rule có hostname, quy tắc match/path, role (`first_party_identity`, `first_party_content`, `user_content_hosting`, `authorized_service`, `unverified`) và bằng chứng. Mọi pattern dùng DNS boundary, không khớp bằng substring.

Danh mục dự kiến 14 mã từ hợp năm quý theo đề cương; alias và thương hiệu con theo codebook đã duyệt. LinkedIn mã riêng; Facebook/Instagram/WhatsApp→Meta; Outlook/Office365/OneDrive→Microsoft; Gmail/Drive→Google; AWS→Amazon; iCloud→Apple; X/Twitter cùng mã. Giữ tên dịch vụ gốc để chấm nhãn rõ.

UGC/tenant trên Sites/Docs/Forms/SharePoint/Blob không tạo khớp danh tính và không whitelist. Mã tổ chức ngoài danh mục vẫn được ghi theo nhận diện độc lập; unknown khác ngoài danh mục đã xác minh. Danh mục nhánh thời gian phải dùng nguồn công bố không muộn hơn mốc train; thiếu bằng chứng lịch sử thì báo cáo hồi cứu.

## Gán nhãn mù

1. C xuất view gồm sample_id, URL và nội dung trình bày an toàn; loại source_label, target, dictionary match, score và nhãn của người kia.
2. A ghi tên tự do/bằng chứng/vai trò trước chuẩn hóa mã; không chạy model để gợi ý.
3. B đọc độc lập 30% phishing ngẫu nhiên phân tầng đã chọn, cộng các ca khó chuyển thêm; cả hai lưu lượt gốc.
4. C hoặc công cụ chỉ tính đồng thuận từ phần ngẫu nhiên trước phân xử; các ca khó thêm không vào kappa. Ca khó vốn nằm trong mẫu ngẫu nhiên vẫn giữ.
5. Phân xử bằng bằng chứng; giữ nhãn A/B, nhãn cuối và lý do, không overwrite lượt gốc.

View ưu tiên văn bản trích bằng parser, URL và cấu trúc; ảnh chụp có sẵn khi cần. Không mở HTML nguy hiểm như một trang chạy bình thường. Nếu cần thu/render mới thì công cụ sandbox riêng, không tải mạng từ view gán nhãn.

Nhãn annotation: annotator_id, pass_id, sample_id, class_label (`phishing`, `benign`, `insufficient_evidence`), observed_service, org_targets, primary_org/status, identity_role, evidence_note, seconds_spent, random_subset, difficult_case, codebook_version và timestamp. Giữ metadata random/difficult riêng để không tính kappa sai tập.

Audit ~200 mẫu là audit lớp, không thay gán nhãn tổ chức cho toàn bộ phishing giữ lại. Hard benign được A xác minh toàn bộ và B kiểm 30% + ca khó. PhishVN bronze theo quy tắc riêng của đề cương; chưa kiểm thì không vào đánh giá xác nhận.

## Pilot và chọn quy mô

20 mẫu kỹ thuật (8 phish/12 benign) + 12 phishing thêm để có pilot 20 phishing. Ghi giờ đọc, tra nguồn, chuẩn hóa và phân xử, không lấy thời gian parser. Tạo registry exclusion bằng hash/sample ID/nhóm; loại toàn bộ pilot khỏi official test và mẫu đánh giá chính.

Quy mô tham chiếu 2.000 phishing/500 miền, 10.000 benign/3.000 miền, gồm 300 hard benign/100 miền. Nếu trung bình >5 phút/phishing hoặc giờ A/B không đủ, dùng ~1.200/300 miền; nếu còn quá tải, điều chỉnh theo ngân sách trước mô hình. Số mẫu/miền này không phải dữ liệu hiện có hoặc bảo đảm sức mạnh thống kê.

## QC và nhóm

- Ghi counts trước/sau lọc, lớp, ngôn ngữ, nội dung rỗng, mẫu chết, loại trùng và nguồn/chế độ.
- Dùng eTLD+1 với Public Suffix List được khóa phiên bản; không dùng domain field nguồn làm số miền độc lập chưa kiểm.
- Xử lý shared hosting bằng quy tắc tenant/URL đã định trước; nếu không xác định ranh giới đáng tin, dùng grouping bảo thủ, báo số nhóm. Tenant ID phục vụ grouping không tự chứng minh danh tính.
- Exact/near duplicate: quy tắc và tham số khóa trước đánh giá; nếu nối nhiều miền, toàn component ở cùng phía split. Kiểm template chung của nền tảng để tránh coi mọi nội dung khác nhau là một trang mà không giải thích.
- Coverage theo nhãn độc lập, cả trang và miền; unknown giữ riêng. Quy tắc >=5 miền/tổ chức chỉ phục vụ báo cáo nhóm.
- Theo dõi lệch nguồn/capture/time; cùng parser không tự xóa artefact. Nguồn gộp phải có hai lớp mỗi fold ngoài/nội bộ; tập một lớp đánh giá riêng.

## Artifact đầu ra cần có

source manifest; date audit; dictionary/codebook + checksum; pilot/exclusion registry; sampling plan; sample index; annotation A/B/final; agreement report; QC/exclusion log; group index; split manifest. Raw/labels không nằm trong API runtime hoặc gói extension.
