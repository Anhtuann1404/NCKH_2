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


## Checklist nghiệm thu và mở training

Checklist vận hành cho Lead D ngày 06/10/2026, đối chiếu các mục ở trên và EXPERIMENT_PROTOCOL; không thay đổi thiết kế nghiên cứu. Chỉ đánh dấu khi có bằng chứng kiểm được. Nghiệm thu code, nghiệm thu gói pilot, chốt PLAN-01 và cho phép huấn luyện là các quyết định riêng. Tests đạt hoặc checksum khớp không tự chứng minh mẫu là dữ liệu thật hay nhãn độc lập.

### 1. Nghiệm thu kỹ thuật — C bàn giao, D review, B kiểm tái lập

- [ ] Ghi đúng branch/commit, môi trường/lock và phạm vi task; đối chiếu diff với lần review trước.
- [ ] Tests trên checkout sạch dùng fixture tự chứa; tests cần dữ liệu hạn chế có marker integration và skip có lý do khi thiếu. Báo riêng passed/failed/skipped/deselected.
- [ ] Probe rollback giữ run cũ khi công bố lỗi; nếu khôi phục cũng lỗi, giữ backup và báo đường dẫn phục hồi. Output cũ không bị ghi đè khi chưa yêu cầu.
- [ ] Bản ghi thiếu nhãn/nhãn ngoài bài toán không được coi là benign hoặc đủ điều kiện đánh giá; ngày thiếu/sai giữ đúng trạng thái.
- [ ] Ingestion kiểm byte hash/size/revision từng shard theo nguồn khóa, ID ổn định, checksum HTML thực tế, streaming và khôi phục HTML từ locator có kiểm hash.
- [ ] Thiếu registry hoặc mapping pilot chưa giải quyết phải chặn luồng thật; không chỉ tin cờ training_blocked. Mẫu bị loại không vào snapshot/feature/fit.
- [ ] Index kỹ thuật tách raw URL/HTML/nhãn nguồn và target hạn chế; X chỉ chứa URL–nội dung đã chuẩn bị, không có metadata nhãn/ID/group/date/hash/tier/split.

Đạt bước này chỉ xác nhận công cụ trong phạm vi đã kiểm. DATA-03 và DEV-01 được nghiệm thu riêng; không kế thừa kết luận từ task khác hoặc từ số tests tổng.

### 2. Nghiệm thu gói pilot trước mở phiên — C chuẩn bị, B/D đối soát

- [ ] V1 và kết quả/log cũ được bảo tồn, ghi rõ không dùng Kappa/PLAN-01 vì lượt A có AI chọn nhãn. Chữ ký duyệt cũ không được kế thừa sang V2.
- [ ] Gói mới có dataset ID/version/hash riêng và đúng 32 mẫu theo kế hoạch A/B full-overlap; số lớp nguồn được kiểm trong kênh C/D, không gửi cho người gán.
- [ ] Mỗi mẫu đối chiếu được tới shard/dòng của nguồn train đã khóa: hash tệp, locator, URL và HTML thực tế. HTML/nhãn tự dựng chỉ là fixture, không gắn nhãn dữ liệu thật.
- [ ] Đủ đầu vào đối chiếu V1, tập dượt và các mẫu đã mở; thiếu đầu vào hoặc lỗi đọc phải dừng. Kiểm URL, HTML/nội dung view và nhóm bằng quy tắc chung đã khóa, giữ báo cáo phương pháp/counts.
- [ ] Không còn nhãn/target hoặc bảng URL–nhãn của gói trên Git chung. Nếu từng lộ, ghi lịch sử và xác nhận riêng mức tiếp xúc A/B; xóa ở commit mới không xóa được sự tiếp xúc. Mẫu đã tiếp xúc được xử lý trước duyệt gói.
- [ ] View mù đủ metadata dataset_id, is_synthetic, codebook_version, sampling_plan_version; ID duy nhất, nội dung an toàn và không chứa nhãn nguồn, matcher/score hoặc kết quả người khác.
- [ ] Hash byte của view, dictionary và codebook khớp manifest; version/trạng thái khóa trên đĩa đúng bản được duyệt. C bàn giao file thật qua kênh hạn chế để D/B kiểm theo quyền truy cập, không chỉ gửi chuỗi hash.
- [ ] CLI/đánh giá hỗ trợ V2 và manifest V2 tường minh; thử preflight, resume, provenance từng mẫu, không trộn gói/lượt và không cho người gán sửa random subset/version.
- [ ] Registry chứa mọi tập dượt/pilot đã mở và gói mới; đối chiếu ánh xạ nguồn/ID/hash/nhóm để loại khỏi thực nghiệm. Không suy tổng số từ phép cộng các lô chưa kiểm trùng.
- [ ] D/B có quyết định riêng cho đúng gói và hash; trước quyết định, ready_for_annotation=false. Khi đủ điều kiện, ghi commit kích hoạt và phát lệnh A/B, giữ training thật bị chặn.

A/B tự đọc và chọn nhãn độc lập theo codebook, không dùng AI gợi ý nhãn/tổ chức/lý do hoặc xem lựa chọn của nhau. Hỗ trợ lỗi công cụ không được đưa nội dung mẫu sang AI để chọn nhãn. Không mở HTML nguồn như trang chạy bình thường.

### 3. Nghiệm thu pilot và chốt PLAN-01 — A/B bàn giao, C tính, D quyết định

- [ ] Hai file Pass 1 giữ nguyên, đúng annotator A/B khác nhau, pass_id=1 và đúng bộ ID/provenance/hash của gói đã duyệt; dry-run/synthetic không vào Kappa hoặc thời gian.
- [ ] Pilot full-overlap có đủ 32 cặp; ca khó nằm trong tập đã chọn vẫn giữ. Với QC chính, Kappa chỉ tính mẫu ngẫu nhiên phân tầng 30%, không thêm ca khó ngoài phần đó.
- [ ] Báo Kappa lớp/tổ chức, số cặp, bất đồng thuận và xử lý chỉ số không xác định; không tự đặt ngưỡng Kappa mới để duyệt. Giữ nhãn gốc và nhãn cuối/lý do phân xử riêng.
- [ ] Kiểm thời gian thực đọc/tra cứu, gián đoạn và độ quen mẫu; tách theo lớp/người. Lượt có AI hỗ trợ hoặc thời gian công cụ mô phỏng không dùng chốt PLAN-01.
- [ ] Chốt ngân sách A/B/C/D và quy mô theo quy tắc đã nêu: mục tiêu 2.000 phishing hoặc khoảng 1.200 khi >5 phút/phishing hay thiếu giờ; không biến mục tiêu thành dữ liệu đã có.
- [ ] Khóa sampling plan, seed, audit lớp, 30% kiểm chéo, hard benign và quy tắc giảm quy mô trước xem kết quả mô hình. Mẫu main chưa kiểm chéo chỉ ước lượng nhiễu qua mẫu con.

### 4. Nghiệm thu corpus, nhãn và split — C bàn giao, A/B QC, D kiểm

- [ ] Source/date/window/dictionary/codebook/sampling hashes và quyền dùng/phân phối khớp bản đã khóa; official test không dùng phát triển.
- [ ] Index–nhãn cuối–groups có ID duy nhất, join đầy đủ; nhãn nguồn không tự trở thành nhãn tham chiếu đã kiểm. Mẫu thiếu nội dung/insufficient_evidence/out-of-scope có lý do và cách xử lý rõ.
- [ ] Nhãn tổ chức độc lập phủ toàn bộ phishing giữ lại, không chỉ phần audit ~200 mẫu; unknown/outside_catalog có định nghĩa thống nhất. Hard benign và PhishVN bronze theo quy tắc QC đã chốt.
- [ ] Counts trước/sau lọc, lớp/nguồn/capture/date, nhóm và coverage có bằng chứng; nhánh dữ liệu không đủ để kết luận được báo riêng.
- [ ] Groups khóa PSL/tenant và component exact/near duplicate liên miền; không có sample/group/component vượt train–validation–test hoặc lọt từ pilot/đã mở/official test vào phần không được phép.
- [ ] M0–M3/B-rule/ablation dùng cùng cohort và grouped 5-fold × seeds 17/42/2026; đủ hai lớp ở mọi phân vùng dùng đánh giá. Thiếu nhóm/lớp phải báo, không tự chọn cấu hình khác bằng hiệu năng.
- [ ] Kiểm nguồn gộp có hai lớp trong fold hoặc dùng phân tích riêng đã quy định; không học nhầm nguồn benign tự cào với phishing từ corpus khác.
- [ ] Temporal giữ cutoff 60%/80% theo ngày, purge nhóm trùng quá khứ và báo counts/status; dictionary as-of hoặc giới hạn hồi cứu rõ. Mẫu thiếu ngày có thể thuộc grouped nếu đủ điều kiện, không tự loại khỏi mọi nhánh chỉ vì thiếu ngày.

### 5. Quyết định mở training nghiên cứu — D

- [ ] Các điều kiện corpus/nhãn/split ở bước 4 đã được nghiệm thu; các bước nguồn và PLAN-01 hoàn tất theo thứ tự khóa.
- [ ] Adapter dữ liệu thật và kiểm readiness của C đã được tích hợp/review với code D; kiểm runtime chặn missing registry, unresolved mapping, hash lệch và mẫu loại trừ. Checker fixture hiện tại luôn research_training_allowed=false, không dùng nó cấp phép run thật.
- [ ] Khóa feature/preprocessing/capture versions, config/splits/dictionary và ngân sách tối ưu; TF-IDF/scaler/model chỉ fit train, C/ngưỡng 1%/5% chỉ chọn validation, outer test chỉ đo.
- [ ] Chuẩn bị manifest cho đúng run/cohort: hashes đầu vào, commit/environment, model/seed, ngưỡng/FP validation, OOF metrics/CI và exclusion log; không ghi đè run trước.
- [ ] D ghi quyết định có ngày, phạm vi dataset/run, commit/hash được duyệt và các nhánh chưa đủ điều kiện. Không chỉ sửa training_blocked=false để vượt guard; chưa có quyết định hoặc còn lỗi ánh xạ thì tiếp tục chặn.

Nghiệm thu grouped không tự cấp nghiệm thu temporal/official test/nhánh Việt Nam khi các nhánh đó thiếu điều kiện. Sau run thật, xuất serving bundle và kiểm offline–API–extension riêng theo EXPERIMENT_PROTOCOL; bundle selected-fit hiện có vẫn chỉ là fixture.

### Cách ghi biên bản trong tài liệu hiện có

Ghi tại CURRENT_TASKS hoặc biên bản bàn giao hiện hành, không tạo thêm checklist theo ngày. Mỗi quyết định có: task/gói/run; commit/version; hash và locator bằng chứng (phần hạn chế ghi nơi lưu, không công bố raw/nhãn); người kiểm/ngày; kết quả tests/probes; counts; trạng thái đạt/chưa đạt/không áp dụng và lý do; việc còn thiếu; phạm vi được phép chạy. Hash thay đổi cần đối soát lại đúng artifact và ghi bản thay thế; không trộn kết quả hai phiên bản.
