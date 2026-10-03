# Quy trình phát triển và bàn giao

Theo đề cương đã duyệt; tài liệu dự án nằm trong docs, không tạo nhiều bản sao theo ngày.

## Cấu trúc dự kiến

```text
docs/                       tài liệu khởi động và OpenAPI
configs/                    cấu hình mẫu, kế hoạch/manifest đã khóa sau này
src/phishing/               preprocessing, features, training, evaluation, serving
extension/                  MV3, service worker, content script, popup
tests/fixtures/             HTML/URL mô phỏng sạch; không là dataset đánh giá
scripts/                    CLI import/date audit/annotation/train/evaluate
data/source_audit/          bằng chứng đã có, phân biệt nguồn công khai/hạn chế
data/raw|processed|labels/  dữ liệu nghiên cứu hạn chế, không commit
artifacts/models|runs/      bundle và run output, không commit mặc định
docs/archive/               lịch sử đề cương/ghi chú
```

Đã có scaffold DEV-01 của D tại `src/phishing/preprocessing/`, `src/phishing/features/`, CLI `scripts/inspect_snapshot.py` và tests/fixtures mô phỏng. Data/annotation/training/evaluation/serving và extension vẫn là cấu trúc mục tiêu; chưa có lệnh train hoặc server chạy thật.

## Cách bắt đầu

Đọc CURRENT_TASKS, hoàn thành START-01 rồi DATA-01/DATA-02 trước các bước dữ liệu phụ thuộc. D có thể làm EXT-01 bằng mock/fixture, D làm preprocessing/features của DEV-01, C làm import/index; A/B chưa đọc nội dung chính trước khóa dictionary. Repo đã có Git/remote; nhánh triển khai scaffold là `feat/dev-01-preprocessing`, tách khỏi `main`.

Khi bắt đầu code: môi trường Python riêng, TypeScript/Node riêng cho extension; khóa dependency bằng công cụ nhóm chọn sau compatibility check. Ghi OS/Python/Node/dependency versions và lock trong run manifest. Không load pickle/joblib không rõ nguồn hoặc từ upload API.

## Chạy scaffold DEV-01

Từ thư mục gốc repo, dùng Python 3.11 trở lên; môi trường đã kiểm là CPython 3.14.6 trên macOS arm64. Các module hiện tại và unittest chỉ dùng thư viện chuẩn, không cần cài thư viện học máy hoặc gọi DeepSeek. [dev_environment.lock.json](../configs/dev_environment.lock.json) ghi môi trường đã chạy; dependency cho train/API sẽ được khóa riêng sau thử tương thích.

```sh
python3 -m venv .venv
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v
PYTHONPATH=src .venv/bin/python scripts/inspect_snapshot.py --url 'https://org.fixture.test/login?ticket=synthetic' --html tests/fixtures/synthetic_login.html
```

Lệnh inspect chỉ đọc file cục bộ và xuất đặc trưng URL/DOM/văn bản, không phân loại phishing. CLI dùng để kiểm tra fixture; đầu ra có văn bản và có thể chứa thông tin cá nhân nếu dùng trang thật, không đưa đầu ra đó lên Git. Phiên bản hiện tại là `snapshot-dev-0`/`features-dev-0`, chưa phải `snapshot-v1` dự kiến trong API và chưa được khóa cho thực nghiệm.

17 unittest kiểm ranh giới DNS, path/UGC, dữ liệu điền, script/event handler, no-network/no-process, metadata nhãn, replay, mode/version và giới hạn đầu vào. Đây là kiểm chức năng trên dữ liệu mô phỏng, không là đánh giá hiệu năng mô hình.

## Ownership

Theo [TEAM](TEAM.md): A sở hữu nhãn/evidence, B lượt kiểm độc lập và QA, C nguồn/dictionary/annotation tooling/groups/splits; D là người dùng, lead và owner preprocessing/features/training/evaluation/serving/extension. Model do D trực tiếp xây dựng và huấn luyện, B hỗ trợ chạy lại sau khóa nhãn; C không là owner model.

## Mỗi thay đổi

1. Chọn task ID, xác định output và nghiệm thu trước làm.
2. Thay đổi nhỏ theo module; cập nhật docs/contract/config liên quan.
3. Chạy kiểm tra phù hợp mức ảnh hưởng; lưu lệnh thực đã chạy và kết quả.
4. Review bởi người khác khi đổi nhãn/codebook/splits, features hoặc contract.
5. Cập nhật CURRENT_TASKS với trạng thái và đường dẫn bằng chứng.

Không thay test labels/dictionary/threshold sau xem test để báo như phép đo ban đầu. Sửa lỗi protocol có run/version mới và ghi kết quả nào bị thay. Thay nguồn không chuyển lõi URL–nội dung–tín hiệu mạo danh đã được duyệt.

## Những kiểm tra đáng làm khi có code

**Dữ liệu/nghiên cứu:** kiểm nguồn pinned/hash; blind export không có target/label/prediction; kappa chỉ phần random; pilot/test exclusion; group intersections; TF-IDF/SVD không fit validation/test; cùng samples/splits M2–M3; threshold chỉ từ inner validation; metrics undefined được báo đúng.

**Tín hiệu:** DNS boundary, thương hiệu trong path, sub-brand map, bài viết nhắc thương hiệu, shared hosting, unauthorized form destination và nhiều mục tiêu. Fixtures được thiết kế để có thể bắt lỗi thực, không chỉ sao lại implementation.

**API:** schemas, auth/origin, body limits/version, model chưa ready, không fetch URL/thực thi HTML, không log payload. Không gọi endpoint test đến trang phishing thật.

**Extension:** navigation/DOM revision, phản hồi sai thứ tự, DOM trễ, SPA, tắt API, thiếu quyền, snapshot làm sạch và bật/tắt nội dung. Demo bằng trang mô phỏng rõ nhãn; độ trễ mô hình thật được đo riêng.

**Tài liệu:** links nội bộ tồn tại, JSON parse được, OpenAPI refs/schema/examples nhất quán. Không cần tạo test suite chỉ cho sửa văn bản.

## Điều kiện hoàn thành task/code

Có artifact chạy/đọc được; acceptance của task đạt; lỗi/giới hạn ghi rõ; không đưa raw data/secret vào Git; docs/current task cùng trạng thái; commit/run hash nếu đã có Git. Mock, pilot và thực nghiệm thật phải phân biệt rõ trong tên output/báo cáo.

## Quản lý quyết định và rủi ro

ADR nằm trong TECH_SPEC, không cần tạo file cho mỗi quyết định nhỏ. Ghi ngày, lý do, tác động/version khi đổi API, preprocessing hoặc lưu mô hình. Rủi ro cần theo dõi trong CURRENT_TASKS: nguồn/permission, ngân sách nhãn, coverage, nguồn/capture bias, lịch sử dictionary và parity offline/runtime. Cập nhật khi có bằng chứng mới; không ghi phần trăm rủi ro chưa đo.

## Bàn giao

Báo cáo, environment locks, code/config, run/split/dictionary manifests, mô hình được phép, hướng dẫn cài demo và kịch bản lỗi. Dữ liệu chia sẻ theo quyền nguồn; nếu không chia sẻ HTML, cung cấp index/recipe được phép. Người mới phải lần được từ kết quả về run → config/split/labels/source, và từ cảnh báo demo về bundle/version.
