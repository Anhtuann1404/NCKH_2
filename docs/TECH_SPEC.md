# Technical specification v0.1

Trạng thái: đã có preprocessing/features DEV-01, khung kiểm run-plan/metrics và FastAPI–MV3 mock chạy bằng fixture. Đã có TF-IDF/LR, grouped CV và bootstrap mô phỏng; chưa có model/API suy luận từ dữ liệu thật hoặc pipeline đã khóa. Phạm vi theo đề cương đã duyệt. Tham chiếu: đề cương 5.2c–f.

## Kiến trúc

```mermaid
flowchart LR
  S[Nguồn URL–HTML] --> I[Kiểm kê date / khóa nguồn]
  I --> L[Gán nhãn độc lập và xử lý dữ liệu]
  L --> F[Bộ trích đặc trưng chung]
  F --> E[Huấn luyện và đánh giá]
  E --> B[Bundle mô hình + danh mục + ngưỡng]
  P[Trang đang mở] --> X[Content script: snapshot đã làm sạch]
  X --> W[Service worker: quản lý yêu cầu]
  W --> A[API cục bộ]
  B --> A
  A --> F
  A --> W
  W --> U[Cảnh báo / popup]
```

API chỉ phân tích đầu vào gửi đến; không tự truy cập URL hoặc chạy HTML. Crawler là công cụ thu thập riêng trong sandbox, không nằm trong đường suy luận API.

## Stack khởi đầu

- Python cho import, xử lý, đặc trưng và thực nghiệm; môi trường dự án riêng, khóa phiên bản sau thử tương thích.
- scikit-learn cho TF-IDF, Logistic Regression, pipeline và chỉ số; LightGBM là nhánh so sánh M2/M3 sau baseline.
- FastAPI cho API demo cục bộ; OpenAPI 3.1 cho hợp đồng.
- TypeScript và Chrome Manifest V3 cho extension; parser Python xử lý HTML offline, content script lấy DOM runtime.
- JSON/JSONL và file manifest cho cấu hình/nhãn giai đoạn đầu. Chưa cần cơ sở dữ liệu, hàng đợi hoặc dịch vụ cloud.

[FastAPI](https://fastapi.tiangolo.com/), [content scripts Chrome](https://developer.chrome.com/docs/extensions/develop/concepts/content-scripts) là tài liệu kỹ thuật chính thức đã kiểm. Không cài dependency chỉ để dựng tài liệu.

## Ownership

Theo [TEAM](TEAM.md): C sở hữu data/annotation tooling; A/B sở hữu lượt nhãn độc lập; D (người dùng/lead) sở hữu preprocessing/features/training/evaluation/serving và extension. B kiểm tái lập/chức năng sau khóa nhãn, C kiểm dữ liệu/split.

## Module và hợp đồng nội bộ

**data:** import theo revision, audit date, hash, chuẩn hóa metadata và loại mẫu. Output là index mẫu + manifest; các trường label/target/date được tách khỏi feature input.

**annotation:** C xuất view mù; A/B lưu lượt độc lập; công cụ tính đồng thuận chỉ đọc đúng mẫu ngẫu nhiên; phân xử tạo nhãn cuối và giữ bản gốc.

**preprocessing:** một quy tắc version hóa cho URL/HTML trước features. Đầu vào feature extractor chỉ có URL chuẩn hóa, HTML đã làm sạch, chế độ thu và danh mục được phép; chế độ thu phục vụ QC, không đưa vào vector học.

**features:** URL, DOM, văn bản, tín hiệu mạo danh; hàm `extract(snapshot, dictionary)` không fetch mạng, không đọc nhãn hoặc target. Dữ liệu tính được độc lập có thể cache theo hash + phiên bản; TF-IDF/SVD và tham số thích nghi không fit toàn tập.

**training/evaluation:** nhận index, labels và split đã khóa; tạo pipeline, ngưỡng từ validation nội bộ và dự đoán ngoài mẫu. Manifest run ghi nguồn, split, danh mục và config checksum.

**serving:** load bundle đáng tin cậy của nhóm; xác minh phiên bản preprocessing/features, ngưỡng và checksum danh mục trước ready. Không load mô hình được người dùng upload. Tài liệu [model persistence của scikit-learn](https://scikit-learn.org/stable/model_persistence.html) mô tả yêu cầu tin cậy và tương thích môi trường; lựa chọn định dạng lưu được chốt khi triển khai.

**extension:** content script quan sát trang; service worker gọi API; popup/banner hiển thị trạng thái. Nhận diện do mô hình trả là ứng viên, không trình bày như nhãn tổ chức đã xác minh.

## Tiền xử lý dùng chung

Thiết kế ban đầu: URL giữ scheme/host/path và tên tham số; giá trị query được thay bằng marker cố định, bỏ fragment và userinfo. Giới hạn path chứa token cũng cần quy tắc xác định và fixture trước khóa; không ghi raw URL vào log runtime. Đặc trưng URL dùng đúng biểu diễn này trong huấn luyện và serving, không âm thầm đổi giữa hai môi trường.

HTML loại script, inline handler và giá trị điền trong biểu mẫu/textarea/contenteditable trước gửi; giữ cấu trúc và thuộc tính cần trích đặc trưng. Parser offline không tải tài nguyên. Đếm script/iframe nếu cần phải được tính bằng pipeline thống nhất trước loại, với trường thống kê được kiểm soát phiên bản; API v0.1 chưa nhận các thống kê tự do từ client. Vì vậy những đặc trưng không thể tái lập từ snapshot làm sạch sẽ chưa dùng trong bundle v0.1, phải ghi rõ khi đặc tả M1.

Không thu phím bấm, cookie, storage, mật khẩu/OTP hay lịch sử duyệt. Làm sạch không bảo đảm xóa mọi thông tin cá nhân trong văn bản; demo chỉ chạy trên trang được phép và có công tắc bật phân tích nội dung. Nội dung gửi máy chủ cục bộ cũng cần được giải thích trong giao diện.

### Scaffold hiện có — DEV-01

- `prepare_snapshot(url, html, capture_mode=...)` chỉ nhận URL/HTML/chế độ; `extract(snapshot)` từ chối dataset row chứa label/target. Mode/version kiểm đầu vào, không đưa vào vector.
- URL bỏ userinfo/fragment, thay giá trị query bằng `_redacted_`, giữ thứ tự và query key lặp, chuẩn hóa host/port/IDNA. Path và query key còn có thể chứa thông tin cá nhân; quy tắc xử lý token path cần chốt trước run chính.
- HTMLParser từ thư viện chuẩn không fetch tài nguyên hay chạy script. Loại script/style/template/noscript/object/embed, event handler, thuộc tính ngoài danh sách, giá trị input, nội dung textarea/contenteditable/hidden và comments. URL trong thuộc tính được làm sạch và giải tương đối theo URL trang.
- DOM draft gồm số thẻ, form/input/iframe/image, link và link cùng/khác **hostname**; không có script count hoặc metadata nguồn. Text trích thô gồm title; trainer MODEL-PREP-02 đã fit TF-IDF chỉ trên inner-train của fixture.
- `DomainRule` kiểm hostname/path scope, subdomain chỉ khi cho phép; UGC lấn át quy tắc nhà cung cấp rộng. Chỉ thử bằng tổ chức `.test` mô phỏng, chưa có danh mục thương hiệu chính thức. M3/B-rule có bản fixture với alias/form/login, chưa phải bộ tín hiệu nghiên cứu đã khóa.
- Version `snapshot-dev-0`/`features-dev-0` phân biệt rõ với `snapshot-v1` mới là đề xuất trong hợp đồng API. Không dùng scaffold để tự đánh dấu freeze preprocessing hoặc training readiness.

Giới hạn cần giải quyết trước khóa pipeline: HTMLParser không dựng DOM theo đầy đủ quy tắc trình duyệt; bản hiện tại bỏ qua `<base>` và CSS visibility, không phải bộ lọc an toàn để render HTML. Dùng IDNA của Python, chưa kiểm parity với URL WHATWG phía extension. So sánh link theo hostname không thay eTLD+1, phân nhóm miền hoặc xác minh quyền sở hữu; PSL/grouping thuộc phần bàn giao của C. Domain rule hiện là primitive bảo thủ, chưa tải bằng chứng/historical validity từ dictionary thật. Không đưa text fixture vào đánh giá nghiên cứu.

Tài liệu parser/URL chính thức: [HTMLParser](https://docs.python.org/3/library/html.parser.html), [urllib.parse](https://docs.python.org/3/library/urllib.parse.html). Thư viện phân tách URL không tự kiểm mọi trường hợp; scaffold bổ sung kiểm HTTP(S), hostname, whitespace/control, escaping và giới hạn.

## Snapshot và phản hồi

- Điều hướng mới tạo `navigation_id`; mỗi snapshot có `request_id`, `dom_revision` và `phase`.
- Phase `url_only` dùng M0 để cảnh báo sơ bộ; phase `url_content` dùng bundle nội dung đã chọn. M0 sơ bộ không được coi là đánh giá đủ nội dung.
- Chỉ áp dụng kết quả khớp navigation hiện tại và revision mới nhất; bỏ phản hồi đến muộn. Khi snapshot mới đang phân tích, đánh dấu kết quả cũ đã cũ, không coi là xác nhận trang hiện tại.
- DOM thay đổi: debounce dự kiến 500 ms, một request nội dung đang chạy mỗi tab, timeout client dự kiến 5 giây. Đây là tham số kỹ thuật sẽ đo và điều chỉnh, không là cam kết p95.
- Không có mô hình, API lỗi hoặc thiếu nội dung: hiện “Chưa đánh giá được”, không báo an toàn.
- `score` là điểm mô hình, không gọi là xác suất lừa đảo đã hiệu chuẩn. Giải thích là tín hiệu quan sát, không là chứng minh nguyên nhân quyết định.

## Bundle triển khai

Manifest phải có model_id, variant, score_semantics, model checksum, feature/preprocessing version, dictionary checksum, environment lock, training data/split/config hashes và ngưỡng vận hành. Ngưỡng 5% là điểm nghiên cứu; dùng demo phải chọn cấu hình riêng từ validation phát triển và ghi FPR đo được. Bundle phục vụ demo được fit lại trên phần phát triển cho phép; không lấy một mô hình fold test làm bằng chứng hiệu năng toàn hệ thống.

### Mock đã triển khai — EXT-01

FastAPI đọc schema request trực tiếp từ OpenAPI v0.1, từ chối trường thừa; middleware kiểm Host/origin/token, preflight và giới hạn byte trước parse, rate limit. Mock scenarios chọn từ CLI, không nhận label/target/scenario trong snapshot; điểm và ngưỡng cố định chỉ thử UI. Version dev-0, health `model_ready=false`, metadata `mock-only-*`, limitation bắt buộc `mock_response_not_model_result`. Demo synthetic đã có bundle loader/checksum/version/readiness và kiểm parity trên fixture. API phục vụ mô hình nghiên cứu vẫn chờ dữ liệu và mô hình đã nghiệm thu.

MV3 dùng service worker gọi loopback, content script ở frame chính tạo snapshot, popup bật/tắt và consent nội dung. Storage token giới hạn trusted contexts; session state không chứa URL/HTML/token. Kiểm document_id với webNavigation trước nhận snapshot; request tuần tự từng tab, hủy request cũ và bỏ response không khớp identity. Worker khởi động lại chuyển pending thành chưa đánh giá được. Khung demo chưa có ad block, model ONNX hoặc đo latency mô hình thật.

Evaluation dùng groups được cung cấp và threshold từ validation. Grouped CV, TF-IDF/LR và paired bootstrap đã chạy bằng fixture ở MODEL-PREP-02. Chưa tính public suffix/grouping dữ liệu thật hoặc temporal analysis; thực nghiệm chính chờ các bước khóa nguồn/nhãn/groups, giữ giao thức đã duyệt.

## Quyết định kỹ thuật hiện tại

- ADR-001: API localhost cho demo đầu tiên; ưu tiên dùng lại pipeline Python. Chuyển mô hình vào trình duyệt là tối ưu sau khi có bundle đúng.
- ADR-002: file/manifest thay database ở giai đoạn đầu; cân nhắc thay khi đã có nhu cầu cộng tác thực tế.
- ADR-003: backend không crawler; không thực thi nội dung được gửi.
- ADR-004: dùng chung preprocessing; mọi thay đổi biểu diễn phải tăng version và đánh giá tác động.
- ADR-005: hạ tầng người dùng/tenant là quan hệ chưa xác minh; không whitelist theo nhà cung cấp cho M3 hoặc B-rule.
- ADR-006 (04/10/2026): mock dev-0 chạy cùng shape API v0.1, ID/model/limitation ghi rõ synthetic; không tự thay example snapshot-v1 thành version đã khóa. API/extension có dependency version lock, trainer thật chưa có.

Stack/ADR là quyết định triển khai có thể tinh chỉnh có ghi nhận; RQ, phạm vi và giao thức nghiên cứu vẫn theo đề cương.

## Trainer mô phỏng đã triển khai

Factory tại `training/pipeline.py`; metadata labels/groups nằm ngoài PreparedSnapshot. `evaluation/grouped.py` tạo fold cố định dùng chung mọi variant; `training/experiment.py` fit/tune trên inner train/validation, không refit sau chọn threshold. `evaluation/bootstrap.py` lấy mẫu toàn nhóm theo cặp, riêng seed. CLI `scripts/run_synthetic_experiment.py` chỉ tạo fixture. Chi tiết tham số, hạn chế và lệnh trong DEVELOPMENT.
