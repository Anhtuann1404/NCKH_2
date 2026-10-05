# Quy trình phát triển và bàn giao

Theo đề cương đã duyệt; tài liệu dự án nằm trong docs, không tạo nhiều bản sao theo ngày.

## Luồng nhánh đã thống nhất — 05/10/2026

`nhánh công việc → develop → main`.

- `develop` là nhánh tích hợp để nhóm clone, chạy và kiểm tra các phần đã nghiệm thu kỹ thuật. Phần D tại `1614d84` đã được merge bằng merge commit, giữ lịch sử nhánh.
- Mỗi thành viên tạo nhánh công việc từ develop và mở PR đích develop. Giữ owner review, kiểm thử phù hợp, không gộp dữ liệu hạn chế/secret hoặc phần còn lỗi. Các nhánh đang làm từ base cũ có thể cập nhật develop và xử lý conflict sau khi bảo toàn thay đổi local; không reset hoặc force push.
- `main` dành cho giai đoạn ổn định đã được Lead nghiệm thu. Chỉ mở PR develop → main khi giai đoạn đủ tiêu chí; không tự merge main khi hoàn thành một task.
- Các PR xếp chồng có thể giữ base là nhánh phụ thuộc để review; trước tích hợp cuối phải đưa về develop sau khi phụ thuộc được nghiệm thu.

Bắt đầu công việc mới từ checkout sạch:

```sh
git fetch origin
git switch develop
git pull --ff-only origin develop
git switch -c codex/my-task
```

Nếu có thay đổi chưa commit, bảo toàn chúng trước khi đổi nhánh. Không dùng lệnh reset/clean để làm checkout sạch. Commit trên nhánh công việc rồi mở PR đích develop, không push trực tiếp main.

Điều kiện chốt một giai đoạn: các task trong phạm vi được nghiệm thu; tests/integration chạy lại trên develop; lỗi còn lại và giới hạn được ghi; docs/cách chạy đồng bộ; nguồn/nhãn/training readiness đáp ứng giao thức nếu giai đoạn chứa thực nghiệm thật. Lead review diff develop → main trước quyết định merge.

Hiện chỉ phần D fixture/demo được tích hợp. DATA-03, ingestion và công cụ nghiệm thu Pass 1 của C còn các điểm review tại bbf886c/98cb37e nên chưa merge; A/B tiếp tục pilot độc lập bằng gói đã khóa. Windows chưa được kiểm thực tế. Có develop không đồng nghĩa được mở training corpus chính.

## Bàn giao D để nhóm review — 05/10/2026

Owner: D (Anh Tuấn), lead/model/API–extension. Repo gốc: `/Users/yingjunn_/Study_/NCKH_2`, nhánh `feat/local-dev-01`, base `f4b2e09`. Bản bàn giao để review nằm trên nhánh riêng `codex/d-demo-integration`, tạo từ `origin/main` và chỉ gồm mã D cùng các phần phụ thuộc. Repo gốc và nhánh local vẫn giữ nguyên. Phần D đã tích hợp vào develop để nhóm kiểm tra; chưa merge vào main.

### Kết quả và file cần đọc

| Hạng mục | Thay đổi và nơi review |
| --- | --- |
| MODEL-API-EXT-01 | [demo_model.py](../src/phishing/serving/demo_model.py), [mock_api.py](../src/phishing/serving/mock_api.py), [run_demo_model_api.py](../scripts/run_demo_model_api.py): M0/M3 fixture trả score theo pipeline, giữ hợp đồng/auth/limits API |
| MODEL-BUNDLE-01 | [build_demo_bundle.py](../scripts/build_demo_bundle.py), demo_model.save/load: lưu/tải TF-IDF/scaler/LR, ngưỡng, versions và checksum; không fit khi load |
| Extension runtime | [core.ts](../extension/src/core.ts), [background.ts](../extension/src/background.ts), [content.ts](../extension/src/content.ts), [popup.ts](../extension/src/popup.ts): phân biệt mock/model-demo, giữ nhãn DEMO, timing chỉ lưu số đo và state |
| PERF-DEMO-01 | [browser-smoke.mjs](../extension/tests/browser-smoke.mjs), [core.test.mjs](../extension/tests/core.test.mjs): cổng/profile riêng, p50/p95 và token sai/offline/navigation/DOM/limits |
| PARITY-DOM-01 | [snapshot-parity.mjs](../extension/tests/snapshot-parity.mjs), [check_snapshot_parity.py](../scripts/check_snapshot_parity.py), [build.mjs](../extension/build.mjs): đối chiếu chữ ký URL/DOM/text, phát hiện lệch stored/rendered |
| Python regression | [test_demo_model_api.py](../tests/test_demo_model_api.py), [test_demo_bundle.py](../tests/test_demo_bundle.py), [test_mock_api.py](../tests/test_mock_api.py): schema/parity score/load không fit/checksum lỗi/Host cổng riêng |

Không đổi dependency hoặc hợp đồng request/response OpenAPI. Extension chỉ bổ sung timing nội bộ và chấp nhận backend synthetic có limitations bắt buộc; API mới dùng chung các route hiện có. `scripts/run_mock_api.py` và launcher model thêm cổng tùy chọn cho test cách ly. Các phần nghiên cứu M0–M3/grouped CV hiện có giữ nguyên; không thay đề cương, nhãn, split hay danh mục thật.

### Chạy bản bàn giao

Từ thư mục clone develop, tạo venv và cài dependency locks như hướng dẫn bên dưới:

```sh
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -q
cd extension
npm ci
npm test
npm run test:parity
npm run test:browser
npm run benchmark
```

Trên máy khác dùng Python từ venv tương ứng. Môi trường xác minh hiện tại là macOS arm64/CPython 3.14.6/Node 26.7.0/Chromium 153.0.8010.12; chưa chứng nhận Windows. Bundle local buộc khớp runtime, vì vậy thành viên khác phải build gói trên môi trường của mình, không sao chép joblib không rõ nguồn. Chạy demo thường, token và cài MV3 theo các mục bên dưới; server lần đầu tự build fixture, những lần sau chỉ tải bundle. Không cần dữ liệu thật để review bản này.

### Bằng chứng hiện có

- 55 Python tests và 11 Node tests đạt.
- Browser smoke mới nhất: 15/15 checks đạt; benchmark gồm latency thì 16 checks với bản hiện tại. Kết quả benchmark đã lưu trước khi thêm hai ca DOM lớn, không coi nó là phép đo DOM lớn.
- Parity: 6/6 fixture khớp khi cùng DOM rendered. Stored HTML khác rendered ở table repair, nested form và DOM động; không khẳng định hai capture mode tương đương.
- D đã chạy trên máy: model lưu sẵn → API → extension cho kết quả khác nhau trên login/ordinary fixture; người dùng xác nhận demo và các lệnh kiểm chạy được.
- Báo cáo local (ignored): `artifacts/smoke/browser-report.json`, `parity-report.json`, `latency-report.json`. Logs kiểm thử thuộc dữ liệu mô phỏng, không là kết quả nghiên cứu. Chạy lại sẽ cập nhật report, cần giữ bản cũ nếu muốn so các lần đo.

Số đo gửi–nhận từ report hiện có, thời điểm **05/10/2026 16:42:54 UTC+7**:

| Pha | Số lần | p50 | p95 |
| --- | ---: | ---: | ---: |
| URL-only (M0) | 30 | 3.40 ms | 3.98 ms |
| URL + nội dung (M3) | 30 | 9.90 ms | 12.46 ms |

Phép đo trong service worker từ trước serialize/fetch đến sau parse/validate; không gồm dựng DOM, debounce500ms, navigation/render/banner hoặc startup. Tách riêng server stages trong report; không dùng số đo fixture nhỏ để cam kết website thật. Benchmark dùng rate limit300/phút trên server riêng; demo thường giữ90/phút.

### Phân công review và tiêu chí nhận

- **B:** chạy lại trên fixture, kiểm completed/insufficient/offline/token sai, response stale, timing và load bundle không fit; báo môi trường, lệnh và khác biệt. Không cần mở mẫu nghiên cứu để review demo.
- **C:** đối chiếu hợp đồng snapshot/capture_mode với nguồn corpus, xem ba ca stored/rendered khác nhau trong parity report. Ghi capture mode và rủi ro lệch nguồn trước thực nghiệm chính; không tự đổi protocol/corpus để làm parity bằng nhau.
- **A:** có thể thử UI trên fixture và báo thông báo khó hiểu; pilot nhãn thật vẫn theo gói và lệnh riêng, không lấy thời gian demo làm PLAN-01.
- **D:** nhận phản hồi, xử lý khác biệt môi trường/capture, hoàn thiện nhánh review và PR theo yêu cầu của người dùng.

Nhận bản demo khi chạy được tests và kịch bản fixture, score sau load bằng trước save, không gửi payload khi tắt/không consent, lỗi không biến thành no_indication, report ghi phạm vi/versions. Gói này chưa bao gồm huấn luyện/đánh giá corpus chính, threshold nghiên cứu, dictionary thật trong M3 hoặc phép đo trang thật.

### Giới hạn và các chốt dữ liệu

Mô hình/bundle chỉ học fixture hư cấu; joblib chỉ tải gói do nhóm tạo cục bộ, checksum không là chữ ký nguồn. API không fetch URL/thực thi HTML; server timeout không cưỡng chế dừng worker đã chạy. Capture/CSS/tree repair và giới hạn UTF-16/codepoint/UTF-8 còn cần kiểm rộng hơn trên dữ liệu được phép.

Gói pilot C tại `0bf180c` đã được Lead nghiệm thu với view SHA-256 `8be1c642e5534eeaad01b0ab9d2e8fc6d428ec131585631102a791e0f8d9a749`. Việc ký/mở pilot được điều phối trên nhánh C; chưa nhận commit kích hoạt hoặc nhãn A/B trong bản local D. Training corpus chính vẫn blocked bởi mapping/exclusion và điều kiện nguồn/nhãn chưa hoàn tất. Phê duyệt pilot không biến MODEL-API-EXT-01 thành mô hình nghiên cứu.

Không đưa `.env*`, raw/view/labels, bundle hoặc reports sinh vào commit demo; thư mục `output/` hiện có thuộc người dùng, không nằm trong phạm vi bản bàn giao. Các thay đổi D và docs được tích hợp vào develop qua nhánh riêng; chưa merge vào main.

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

Đã có preprocessing/features DEV-01, kiểm split/ngưỡng/chỉ số tại `training/plan.py` và `evaluation/metrics.py`, FastAPI mock tại `serving/mock_api.py`, TypeScript MV3 trong `extension/`, CLI và tests/fixtures. Đã có trainer TF-IDF/LR và grouped CV chạy riêng bằng dữ liệu mô phỏng; data/annotation và huấn luyện chính vẫn chờ các bước khóa dữ liệu.

## Cách bắt đầu

Đọc CURRENT_TASKS, hoàn thành START-01 rồi DATA-01/DATA-02 trước các bước dữ liệu phụ thuộc. D có thể làm EXT-01 bằng mock/fixture, D làm preprocessing/features của DEV-01, C làm import/index; A/B chưa đọc nội dung chính trước khóa dictionary. Repo đã có Git/remote. Theo yêu cầu của D, triển khai trực tiếp trong thư mục repo gốc trên máy, hiện trên nhánh cục bộ `feat/local-dev-01` từ main mới nhất. Chỉ commit/push khi người dùng yêu cầu; code đang là thay đổi trong working tree để xem và sửa tại chỗ.

Khi bắt đầu code: môi trường Python riêng, TypeScript/Node riêng cho extension; khóa dependency bằng công cụ nhóm chọn sau compatibility check. Ghi OS/Python/Node/dependency versions và lock trong run manifest. Không load pickle/joblib không rõ nguồn hoặc từ upload API.

## Chạy scaffold DEV-01

Môi trường đã kiểm là CPython 3.14.6 và Node 26.7.0 trên macOS arm64. Source dùng Python 3.11 trở lên nhưng chưa kiểm đa phiên bản. Preprocessing/features/metrics/run-plan chỉ dùng thư viện chuẩn; API và test dùng các dependency đã pin trong [requirements-dev.lock](../requirements-dev.lock). Extension có [package-lock.json](../extension/package-lock.json). [dev_environment.lock.json](../configs/dev_environment.lock.json) ghi môi trường đã chạy; scikit-learn 1.9.1, NumPy 2.5.3 và SciPy 1.18.1 đã khóa và chạy thử bằng fixture; chưa fit dữ liệu nghiên cứu. Không gọi DeepSeek trong pipeline này.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.lock
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v
PYTHONPATH=src .venv/bin/python scripts/inspect_snapshot.py --url 'https://org.fixture.test/login?ticket=synthetic' --html tests/fixtures/synthetic_login.html
```

Lệnh inspect chỉ đọc file cục bộ và xuất đặc trưng URL/DOM/văn bản, không phân loại phishing. CLI dùng để kiểm tra fixture; đầu ra có văn bản và có thể chứa thông tin cá nhân nếu dùng trang thật, không đưa đầu ra đó lên Git. Phiên bản hiện tại là `snapshot-dev-0`/`features-dev-0`, chưa phải `snapshot-v1` dự kiến trong API và chưa được khóa cho thực nghiệm.

48 Python unittest đạt: 17 preprocessing/domain, 11 API mock, 7 metrics/run-plan và 13 pipeline/grouped/bootstrap. Đây là kiểm chức năng trên dữ liệu mô phỏng, không là đánh giá hiệu năng mô hình.

## Demo API và extension — EXT-01

### 1. Build và cài cục bộ

```sh
cd extension
npm ci
npm run build
```

Mở `chrome://extensions`, bật Developer mode, chọn **Load unpacked** và chọn thư mục `extension/dist` trong repo. Xem ID extension ở trang đó hoặc cuối popup. Popup luôn có nhãn DEMO MÔ PHỎNG; mặc định phân tích và gửi nội dung đều tắt.

### 2. Chạy API mock

Từ thư mục gốc repo (thay `<extension-id>` bằng ID vừa xem):

```sh
PYTHONPATH=src .venv/bin/python scripts/run_mock_api.py --extension-id <extension-id> --scenario warning
```

Server chỉ bind `127.0.0.1:8765`. Lần đầu tự tạo `.env.phishing.local` bị Git bỏ qua, quyền file 0600; mở file trên máy, sao chép **giá trị** `PHISHING_LOCAL_API_TOKEN` vào ô token của popup và lưu. Không chia sẻ token/commit file đó. Nếu dùng biến môi trường, script ưu tiên giá trị môi trường; không in token ra log.

Scenario là tham số server: `warning`, `no_indication`, `insufficient_content` hoặc `unavailable`; chọn lại bằng cách dừng server rồi chạy lại lệnh. `--delay-ms` dùng thử phản hồi trễ. Score/ngưỡng là số cố định mô phỏng, không phụ thuộc nhãn hoặc hiệu quả thật của trang. `/health` luôn có `model_ready=false`; `/v1/model` mô tả bundle giả có tên `mock-only-*`, không phải bundle đã huấn luyện.

### 3. Mở trang mô phỏng

Trong terminal khác, từ gốc repo:

```sh
python3 -m http.server 9000 --bind 127.0.0.1 --directory tests/fixtures/demo_pages
```

Mở `http://127.0.0.1:9000/login.html`, bật phân tích demo trong popup. Ban đầu chỉ gửi URL đã chuẩn hóa. Bật thêm cho phép nội dung để gửi HTML đã lọc; có nút thử DOM động, SPA và liên kết đổi trang. Banner/popup hiện MOCK ngay cả khi scenario trả warning/no_indication. Extension hoạt động trên HTTP(S), chỉ dùng trang mô phỏng để thử trước khi đánh giá privacy/runtime.

Popup và service worker là trusted contexts được phép đọc token; content script chỉ nhận hai cờ bật/tắt, không nhận token. Session chỉ lưu IDs/revision/phase/trạng thái, không lưu URL/HTML/token. Request mới hủy request cũ, xử lý tuần tự mỗi tab; response phải khớp navigation/revision/phase/request ID. Retry tối đa một lần cho lỗi kết nối/timeout/429/504, ID mới; lỗi/thiếu nội dung hiện chưa đánh giá được. Đóng/tắt hoặc chuyển trang xóa trạng thái cũ; service worker khởi động lại đổi pending sang chưa đánh giá được.

### 4. Chạy kiểm thử extension

Từ `extension/`:

```sh
npm test
npx playwright install chromium
npm run test:browser
```

9 Node tests đạt cho identity/retry/timeout và contract UI. Browser smoke dùng Chromium/profile tạm, chỉ trang mô phỏng và API trên loopback, rồi tự dọn profile/server. 11 tình huống đạt: mặc định tắt, consent URL-only/nội dung, làm sạch, state không chứa payload, DOM động, SPA, warning/no-indication, thiếu nội dung, chuyển trang, offline và tắt. Smoke cần cổng 8765 trống; không dừng một dịch vụ khác đang dùng cổng. Kết quả/ảnh ở `artifacts/smoke/` bị Git bỏ qua, có thể tái tạo bằng lệnh trên. Timeout kiểm bằng Node/API tests; chưa đo p50/p95 của mô hình thật.

Tài liệu triển khai: [Chrome storage/access level](https://developer.chrome.com/docs/extensions/reference/api/storage), [cross-origin requests](https://developer.chrome.com/docs/extensions/develop/concepts/network-requests), [FastAPI testing](https://fastapi.tiangolo.com/tutorial/testing/), [Playwright MV3](https://playwright.dev/docs/chrome-extensions).

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

## MODEL-PREP-02 — TF-IDF/LR và grouped CV mô phỏng

### Đọc lỗi M2–M3 từ run đã lưu

Sau khi có run mô phỏng, dùng thư mục run mà CLI đã in ra:

```sh
PYTHONPATH=src .venv/bin/python scripts/analyze_synthetic_errors.py --run artifacts/runs/synthetic-report-final
```

`synthetic-report-final` chỉ là ví dụ; thay bằng đường dẫn run trên máy. Trên PowerShell:

```powershell
$env:PYTHONPATH = "src"
.\.venv\Scripts\python.exe scripts/analyze_synthetic_errors.py --run artifacts/runs/synthetic-report-final
```

CLI in đường dẫn thư mục phân tích mới trong `artifacts/runs/` (ignored). `--output` chọn thư mục khác nhưng phải chưa tồn tại; dữ liệu run đầu vào giữ nguyên. Công cụ dùng được với run fixture của runner hiện tại và run có hash artifact từ công cụ báo cáo; run cũ chưa có hash được ghi rõ `recorded_only_legacy_run`.

- `error_cases.csv`: sample/group ID, nhãn fixture, seed, fold, target FPR, score/threshold/warning/outcome của M2/M3. Chỉ xuất ca có lỗi hoặc thiếu ngưỡng, không xuất raw URL/HTML. Nhãn 0=benign, 1=phishing; fold đánh số từ 0.
- `category`: `m3_corrected` (M2 sai, M3 đúng), `m3_regressed` (M2 đúng, M3 sai), `both_wrong`, hoặc `missing_operating_point`. `false_positive` là cảnh báo nhầm benign; `false_negative` là bỏ sót phishing.
- `error_summary.json`: counts theo từng seed × FPR, gồm cả `both_correct`, FP/FN/missing riêng từng mô hình; SHA-256 input, CSV và mã inspector. Không cộng các seed thành cỡ mẫu độc lập.

Kiểm tra độc lập ID/cohort/group/fold và ngưỡng–score–warning trước xuất. Khi manifest có hash artifact, phải khớp mọi input cần dùng. Không fit, không sửa threshold, không kết nối ingestion của C; chỉ nhận scope fixture và `research_evidence=false`. Mục tiêu FPR là ràng buộc validation, không bảo đảm FPR test. Ca M3 sửa/sai thêm chỉ mô tả khác biệt dự đoán, chưa chứng minh nguyên nhân hoặc hiệu quả tín hiệu mạo danh. B kiểm tra CLI trên Windows; nhãn mô phỏng không dùng cho PLAN-01/Kappa hoặc kết quả nghiên cứu.

### Chạy mô hình mô phỏng

Chạy tại repo gốc, không cần B tham gia và không cần tải dữ liệu thật:

```sh
PYTHONPATH=src .venv/bin/python scripts/run_synthetic_experiment.py
```

Trên PowerShell, tại thư mục gốc dự án:

```powershell
$env:PYTHONPATH = "src"
.\.venv\Scripts\python.exe scripts/run_synthetic_experiment.py
```

CLI đọc `configs/synthetic_experiment.json`; lưu cấu hình hiệu lực thành `config.json` trong run. Các trường scope, seed, fold, variants, C-grid và FPR được kiểm tra theo cấu hình fixture cố định; chỉ số nhóm và số lần bootstrap có thể đổi để kiểm thử nhanh. Đây là cấu hình mô phỏng, không thay giao thức dữ liệu thật. B kiểm tra chạy trên Windows và gửi đường dẫn run cùng manifest; không dùng kết quả fixture để chốt hiệu năng hoặc PLAN-01.

Mặc định sinh 160 snapshot trên 40 nhóm miền `.test`, chạy outer StratifiedGroupKFold 5 fold × seed 17/42/2026, inner 3-fold lấy một fold làm validation. M0/M1/M2/M3, ba ablation và B-rule dùng cùng phân vùng và cùng cohort có HTML. `--groups` thay số nhóm fixture; `--bootstrap-repetitions` thay số lượt bootstrap (mặc định 2000); `--output` chỉ thư mục mới để tránh ghi đè run. Không có tùy chọn đọc tập dữ liệu thật ở CLI này.

Các file `config.json`, `manifest.json`, `sample_index.json`, `folds.json`, `metrics.json`, `predictions.jsonl`, `paired_ci.json`, `summary.json`, `summary.csv`, `report.md` nằm trong `artifacts/runs/synthetic-.../` được ignore. Manifest có dấu `research_evidence: false`, dictionary fixture, SHA-256 code/dữ liệu/lock/các tệp kết quả và phiên bản môi trường. Các fold lưu chỉ số hàng, đối chiếu bằng sample_index. Run grouped CV không xuất bundle mô hình cho API; launcher API riêng tải bundle fixture đã lưu, không fit khi khởi động.

Mở `report.md` trong thư mục CLI in ra để xem bảng theo seed/model/FPR, average precision theo fold, dao động seed và paired CI. `summary.csv` dùng cho bảng tính; `summary.json` giữ cả độ phân tán fold/seed và CI. TP/FN/FP/TN được cộng trên toàn bộ OOF của **từng seed** trước khi tính recall/FPR; không lấy trung bình tỷ lệ fold làm tỷ lệ toàn tập hoặc nhân ba cỡ mẫu. AP là average precision, chưa phải phép tích phân PR-AUC hình thang. Một fold thiếu operating point thì tỷ lệ OOF cả seed/variant/target giữ NA, không âm thầm bỏ các mẫu này. CLI từ chối ghi đè run cũ. Kết quả fixture chỉ kiểm quy trình; không chứng minh hiệu năng phishing thực tế.

M2/M3 dùng word TF-IDF (1,2), char TF-IDF (3,5), ngân sách 1000/1500 từ vựng. Numeric scaler, vocabulary, IDF và LR chỉ fit inner-train. Chọn C từ 0.25/1/4 bằng average precision trên validation, hòa chọn C nhỏ hơn. Chọn threshold riêng ở FPR validation 1%/5%, tối đa recall, hòa chọn ngưỡng cao hơn. **Không refit trên validation sau chọn ngưỡng**; test dùng đúng mô hình đã tạo score validation. Đây là triển khai holdout nhóm nội bộ; chưa triển khai nested tuning nhiều fold nội bộ. Với data thật, phải chốt cấu hình triển khai cùng giao thức trước run chính.

`test_ap` là average precision (tổng theo bước precision–recall), báo riêng từng outer fold, không tính PR-AUC bằng hình thang. Test FPR được báo giá trị thực tế, không giả định bằng mức mục tiêu. Báo số benign trong validation/test: fixture nhỏ không đủ kết luận ở FPR 1%. Điểm vận hành không khả thi giữ trạng thái thiếu và không coi là benign.

M3 hiện là quy tắc exact alias với ranh giới từ, quan hệ miền theo primitives đã có và dấu hiệu form/password/login. Danh mục chỉ gồm ba tổ chức **hư cấu**, độc lập với train/test. B-rule có trọng số fixture cố định; chưa phải quy tắc cuối dùng nghiên cứu. Ablation bỏ cột của từng khối organization/domain/intention; các khối vẫn có phụ thuộc (tín hiệu domain cần candidate tổ chức), vì vậy không diễn giải là tác động nhân quả độc lập. Chưa thực hiện so khớp mờ/codebook thương hiệu con; C bàn giao danh mục thật đã khóa trước khi hoàn thiện phần này.

Paired bootstrap lấy lại **toàn bộ nhóm có hoàn lại**, cùng draw cho hai mô hình, CI percentile 95%, riêng từng seed và mức FPR, so M3–M2, M3–B-rule và M3–từng ablation. Không gộp các seed thành mẫu độc lập. Số replicate có metric không xác định được ghi riêng; không thay bằng 0. CI có điều kiện trên các mô hình đã fit, không bao gồm bất định do huấn luyện lại.

Kiểm thử chống rò rỉ: nhóm không giao giữa train/validation/test; mỗi mẫu test một lần/seed; vocabulary và scaler chỉ fit train; đổi nhãn test không đổi score/ngưỡng/C; M2/M3 dùng chung từ vựng/IDF; metadata không vào feature input; ablation đúng khối; bootstrap giữ nguyên nhóm và đếm replicate thiếu lớp. Đây là kiểm mã, không thay thế audit dữ liệu của B sau này.

Còn chờ: quyền/revision nguồn, labels/codebook/dictionary khóa, loại pilot/official test, groups và kiểm trùng từ C, audit A/B. Temporal split và kiểm thử độc lập official test chưa triển khai. Chưa huấn luyện tập chính hoặc đưa mô hình thật vào extension.

Tài liệu API đã đối chiếu: [sklearn pipeline và tránh rò rỉ](https://scikit-learn.org/stable/common_pitfalls.html), [StratifiedGroupKFold](https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.StratifiedGroupKFold.html), [TF-IDF](https://scikit-learn.org/stable/modules/generated/sklearn.feature_extraction.text.TfidfVectorizer.html), [average precision](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.average_precision_score.html).


## MODEL-API-EXT-01 — demo mô hình TF-IDF qua API và extension

Đã nối mô hình được fit thực sự từ fixture vào cùng hợp đồng API hiện có. M0 chạy URL-only; M3 dùng URL, DOM, TF-IDF word/char và tín hiệu tổ chức hư cấu. Server khởi động sinh 160 mẫu/40 nhóm: 120 mẫu thuộc 30 nhóm train, 40 mẫu thuộc 10 nhóm validation. Fit train, chọn ngưỡng từ validation ở FPR tham chiếu 5%, không refit validation. Đây là demo tích hợp, không phải run đánh giá nghiên cứu hoặc lựa chọn mô hình chính thức.

Build/load extension như mục EXT-01, sau đó từ gốc repo chạy:

```sh
PYTHONPATH=src .venv/bin/python scripts/run_demo_model_api.py --extension-id <extension-id>
```

Chỉ chạy một API trên cổng 8765; dừng mock API trước nếu đang chạy. Token dùng cùng `.env.phishing.local`/biến môi trường và ô token trong popup. Mở trang fixture local, bật phân tích và cho phép nội dung để chạy M3. Không cần tải dữ liệu nghiên cứu hoặc nhận nhãn từ A/B/C.

`/health` có `model_ready=true` vì hai predictor demo đã fit; `/v1/model` có bundle `synthetic-demo-tfidf-lr-v1`. Kết quả dùng model ID `synthetic-demo-*`, limitations `synthetic_training_only` và `not_research_evidence`; score là điểm chưa hiệu chỉnh, không diễn giải thành xác suất bị lừa. Banner/popup ghi mô hình học từ dữ liệu hư cấu. State chỉ thêm loại demo, không lưu score/payload/token. Client vẫn từ chối mô hình nghiên cứu chưa được hỗ trợ.

Server tạo bundle demo ở lần đầu nếu chưa có, sau đó tải lại; xem MODEL-BUNDLE-01 bên dưới. Không có tùy chọn đọc corpus thật, không mở chốt training chính. Không dùng kết quả demo để báo recall/FPR nghiên cứu hoặc đánh giá trang thật. Content rỗng vẫn trả unable_to_assess; API không fetch URL hoặc thực thi HTML. CPU inference chạy ngoài event loop; timeout kết thúc chờ phản hồi, không cưỡng chế dừng tác vụ thread đã chạy.

Kiểm chứng: 51 Python tests, 10 Node tests, 12 Chromium smoke checks đạt trên môi trường đã khóa. Test mới đối chiếu score API với pipeline offline, kiểm thay nội dung làm đổi score, schema hai pha, auth/thiếu nội dung và toàn luồng backend demo → extension. Report browser tại `artifacts/smoke/browser-report.json` bị Git ignore.


## MODEL-BUNDLE-01 — lưu/tải mô hình demo

API mặc định dùng `artifacts/models/synthetic-demo-v1/`. Thư mục chứa `predictors.joblib` (M0/M3, scaler, vocabulary/IDF, classifier và dictionary fixture trong pipeline) và `manifest.json` (threshold, metadata train/validation, phiên bản runtime, checksum predictor và mã nguồn). Thư mục được Git ignore. Đã tạo gói local trên máy D.

Lệnh API như trước: lần đầu thiếu bundle thì fit fixture và lưu; những lần sau chỉ tải, không fit. Có thể tự tạo bundle ở đường dẫn mới:

```sh
PYTHONPATH=src .venv/bin/python scripts/build_demo_bundle.py --output artifacts/models/synthetic-demo-v2
PYTHONPATH=src .venv/bin/python scripts/run_demo_model_api.py --extension-id <extension-id> --bundle artifacts/models/synthetic-demo-v2
```

Builder từ chối ghi đè thư mục có sẵn. Khi runtime hoặc mã preprocessing/features/training thay đổi, loader từ chối bundle cũ; tạo bundle ở đường dẫn mới. Hash và metadata được kiểm trước deserialize, predictor phase và lớp 0/1 được kiểm sau load. Hash phát hiện hỏng/thay đổi, không chứng minh nguồn đáng tin: joblib có thể thực thi mã khi tải. Chỉ dùng gói do nhóm tạo cục bộ, không nhận model upload qua API. Manifest không phải chữ ký số.

54 Python tests đạt; kiểm persistence xác nhận scores/thresholds giống hệt trước lưu, không gọi trainer khi load, chặn checksum/runtime/source/threshold sai trước deserialize. Extension build đạt. Lượt đầu smoke persistence bị chặn vì cổng 8765 của người dùng đang chạy; các bước PERF-DEMO-01/PARITY-DOM-01 sau đó đã dùng cổng/profile riêng và kiểm được bundle loaded xuyên suốt. Không dừng dịch vụ của người dùng để chạy test. Sau khi dừng API cũ, chạy lại như hướng dẫn; server mới sẽ báo Loaded local synthetic demo bundle.


## PERF-DEMO-01 — đo độ trễ và kiểm lỗi tích hợp

Từ `extension/` chạy:

```sh
npm run benchmark
```

Công cụ build extension, sao chép sang thư mục tạm và thay endpoint chỉ trong bản sao; API chạy trên cổng loopback riêng. Chromium dùng profile riêng, chỉ trang fixture local; không ngắt API 8765 hoặc đụng profile Chrome người dùng. Bản extension dùng thường giữ endpoint 8765. Launcher API có `--port` để phục vụ cách ly và backend demo có `--requests-per-minute` (mặc định 90, benchmark dùng 300 để không đo tác động rate limit).

Mỗi pha URL-only và URL+content đo 30 lần trên hai fixture login/ordinary luân phiên, bỏ hai warmup mỗi pha, chạy tuần tự. p50/p95 dùng nội suy tuyến tính trên danh sách đã sắp. `client_roundtrip` đo trong service worker từ trước serialize/fetch đến sau parse/validate response, bao gồm retry/delay nếu có. Không bao gồm dựng snapshot DOM, debounce 500ms, tải trang, hiển thị banner hoặc startup/load bundle. Vì vậy không gọi đây là thời gian từ người dùng mở trang đến cảnh báo.

Server báo preprocess/extract/infer/server_total; thời gian infer hiện bao gồm các bước transform của sklearn pipeline (trích đặc trưng lại, scale/TF-IDF và classifier), không chỉ phép nhân classifier. Server_total bắt đầu trong worker inference, không gồm middleware/auth/JSON validation hoặc thời gian xếp hàng thread. Không lấy hiệu client_roundtrip-server_total làm ước lượng riêng độ trễ mạng.

Report nằm ở `artifacts/smoke/latency-report.json`, gồm 60 mẫu thời gian, p50/p95, runtime/bundle/checksum và danh sách kiểm lỗi; `browser-report.json` là kết quả smoke. Không lưu URL/HTML/token trong report latency hoặc extension state. Chạy lại sẽ cập nhật hai báo cáo demo này; sao chép bản cần giữ trước lần đo tiếp theo. Các file được Git ignore và không là kết quả nghiên cứu.

Ngày 05/10/2026: gửi–nhận URL-only p50=3.25ms, p95=3.965ms; URL+content p50=9.50ms, p95=10.50ms trên Chromium headless 153.0.8010.12. Server_total tương ứng p50/p95=0.589/0.665ms và 3.880/4.339ms. Đây là số đo hai fixture nhỏ trên máy D, không cam kết độ trễ trang thật.

55 Python tests, 11 Node tests và 14 Chromium checks đạt. Browser kiểm thêm token sai => chưa đánh giá được, offline, DOM động, SPA, phản hồi khi chuyển trang, thiếu nội dung, tắt phân tích, privacy snapshot và mô hình lưu sẵn. Python kiểm giới hạn body, auth/Host/Origin, schema, timeout/rate limit; không diễn giải các API test payload lớn thành kiểm nghiệm đầy đủ DOM lớn trong trình duyệt.


## PARITY-DOM-01 — DOM lớn và đối chiếu runtime/offline

Từ `extension/`:

```sh
npm run test:parity
npm run test:browser
```

`test:parity` chạy sáu fixture trên Chromium riêng: form/link tương đối, hidden/editable/script/comment, Unicode/duplicate attributes, table sai cấu trúc, nested form và DOM động. So đặc trưng URL/DOM cùng hash văn bản đã chuẩn hóa giữa (a) HTML snapshot extension rồi qua Python, và (b) DOM rendered nguyên bản rồi qua Python. Không yêu cầu byte HTML bằng nhau vì trình duyệt và Python serialize attribute khác thứ tự. Sáu ca đều khớp; marker private fixture không xuất hiện trong snapshot.

Report `artifacts/smoke/parity-report.json` cũng so HTML thô lưu trước render với DOM đã dựng: ba ca table repair, nested form repair và nội dung động khác đặc trưng/văn bản. Đây là chênh lệch capture đã tái hiện, không được diễn giải rằng stored_html và rendered_dom luôn tương đương. Script không truy cập website thật, không render HTML nghiên cứu và không thay phạm vi/giao thức đã chốt. Trước huấn luyện thật cần nhóm xác nhận capture mode và phân tích độ lệch nguồn theo DATA_PROTOCOL; chưa tự chuyển corpus hoặc áp dụng renderer mới để sửa số đo.

Browser smoke hiện có 15 checks (benchmark bật latency thêm một check => 16). Fixture lớn sinh tại HTTP server tạm: 6.000 paragraph, khoảng 594KB ASCII sau snapshot, M3 xử lý thành công. Fixture vượt 1.100.000 ký tự bị snapshotHTML chặn: không gửi url_content, không truncate, trạng thái unable_to_assess/snapshot_too_large. URL-only vẫn có thể chạy sơ bộ trước phát hiện DOM quá lớn. API/profile/cổng của người dùng không bị ảnh hưởng.

Report chỉ lưu chữ ký đặc trưng/hashes/count và tên fixture; input HTML tạm được xóa sau test. Snapshot lớn được giữ trong RAM test, không lưu corpus. Giới hạn snapshot phía JS dùng độ dài UTF-16 còn Python dùng số codepoint; JSON API còn có giới hạn byte UTF-8. Sáu fixture không chứng minh mọi encoding/trang thật đều tương đương. Các limits được xử lý bằng lỗi, không cắt nội dung để làm thành dự đoán hoàn chỉnh. Số đo độ trễ trước đó vẫn thuộc fixture nhỏ; các ca DOM lớn không nằm trong mẫu p50/p95.

Bản này chỉ thêm kiểm chứng và báo cáo: không đổi preprocessing/features version, không làm mới bundle hoặc mở chốt training thật.

## Windows và checklist bàn giao — 05/10/2026

Phần D từ `codex/d-demo-integration`, PR #3, đã tích hợp vào `develop`. Clone develop để review; chưa gộp adapter C. Logic chọn interpreter Windows đã có test, nhưng chưa chạy thực tế trên Windows. B cần ghi OS/Python/Node/Chrome và kết quả để xác nhận.

### Windows / PowerShell

Từ repo gốc, dùng Python 3.14 phù hợp lock demo:

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.lock
$env:PYTHONPATH = "src"
.\.venv\Scripts\python.exe -m unittest discover -s tests -q
.\.venv\Scripts\python.exe scripts/check_training_inputs.py --demo-fixture
cd extension
npm ci
npx playwright install chromium
npm test
npm run test:browser
npm run test:parity
cd ..
```

Nếu cài lock thất bại, gửi lỗi và phiên bản môi trường cho D; không tự nới version. Tests chọn `.venv/Scripts/python.exe` trên Windows và `.venv/bin/python` trên macOS/Linux. Có thể đặt `$env:PHISHING_PYTHON = (Resolve-Path .\.venv\Scripts\python.exe).Path` từ repo gốc để chọn interpreter riêng; giá trị là đường dẫn executable, không kèm tham số. macOS/Linux dùng `export PHISHING_PYTHON=/absolute/path/to/python`. Tests kiểm interpreter/dependency trước khi mở Chromium.

Trong Chrome mở `chrome://extensions`, bật Developer mode, Load unpacked → `extension/dist`, copy ID trên máy mình. Chạy API ở terminal tại repo gốc, thay `YOUR_EXTENSION_ID` bằng ID đó:

```powershell
$env:PYTHONPATH = "src"
.\.venv\Scripts\python.exe scripts/run_demo_model_api.py --extension-id YOUR_EXTENSION_ID
```

Terminal thứ hai tại repo gốc:

```powershell
.\.venv\Scripts\python.exe -m http.server 9000 --bind 127.0.0.1 --directory tests/fixtures/demo_pages
```

Nhập token từ `.env.phishing.local` của máy mình vào popup extension; không gửi token vào báo cáo/Git. Nếu ID đổi khi clone/build thì dùng ID mới, không dùng ID của D. Mỗi máy build bundle riêng, không sao chép joblib không rõ nguồn.

### Checklist B

Chỉ dùng `http://127.0.0.1:9000/login.html` và `ordinary.html`; giữ banner DEMO MÔ PHỎNG. Không dùng fixture để kết luận trang thật an toàn.

- [ ] Cài/build/tests chạy được; ghi môi trường và số tests thực tế.
- [ ] Mặc định extension tắt; tắt thì không gửi snapshot và xóa trạng thái cũ.
- [ ] Bật phân tích URL trước; chưa consent nội dung thì chỉ URL-only, consent mới gửi nội dung.
- [ ] Với content consent/bundle fixture mặc định: login cảnh báo, ordinary chưa phát hiện; cả hai giữ thông báo mô hình hư cấu. Nếu khác, ghi bundle/môi trường/bước tái hiện.
- [ ] Tắt API hoặc nhập token sai: chưa đánh giá được, không biến lỗi thành chưa phát hiện phishing. Sau đó phục hồi token/API đúng.
- [ ] Đổi trang/DOM không giữ cảnh báo của trang trước; có kiểm tự động trong browser smoke.
- [ ] API lần hai tải bundle local, không fit lúc startup; chạy parity và giữ report local.

Báo cáo gồm branch/commit, OS/Python/Node/Chrome, lệnh, PASS/FAIL và bước tái hiện. Che token/URL nhạy cảm trong ảnh/log. Không commit raw/view/labels, bundle hoặc reports sinh. Benchmark là phép đo riêng trên fixture, không là hiệu năng nghiên cứu.

### Kiểm đầu vào trước fit — chỉ fixture

```sh
PYTHONPATH=src .venv/bin/python scripts/check_training_inputs.py --demo-fixture
PYTHONPATH=src .venv/bin/python scripts/check_training_inputs.py --manifest /path/to/fixture/manifest.json
```

PowerShell dùng `$env:PYTHONPATH = "src"` và `.\.venv\Scripts\python.exe`. Demo tạo gói tạm rồi xóa, không fit/đọc data thật hoặc sửa registry C. Exit 0 là fixture hợp lệ; exit 1 là bị chặn. Kết quả luôn có `research_training_allowed: false`.

Hợp đồng thử của D: manifest có `contract_version: training-input-fixture-v0`, `scope: synthetic_fixture_only`, `artifacts` đủ `index`, `labels`, `groups`, `split`, `exclusion`. Mỗi artifact có `path` tương đối trong gói và SHA-256 byte thực. Không phải schema corpus C đã được duyệt.

- Index JSON: danh sách `sample_id`, `html_path`, `html_sha256`, `capture_mode` (`stored_html`/`rendered_dom`), `exclusion_reason: null`.
- Labels JSON riêng: danh sách `sample_id`, `class_label` (`phishing`/`benign`), `final: true`. Groups JSON ánh xạ ID → group cuối được cung cấp.
- Split JSON: `variant`, `seed`, `train_ids`, `validation_ids`, `test_ids`. Exclusion JSON: danh sách `excluded_ids` tường minh.

Checker kiểm hashes artifact/HTML; ID duy nhất/khớp; mẫu loại trừ và cohort có nội dung; split phủ cohort, không trùng ID/nhóm và đủ hai lớp cả ba phần. Dùng lại RunPlan, không tự tạo split hoặc thay nhãn cuối bằng nhãn nguồn.

Chưa xác minh nguồn thật, component trùng nội dung, annotation QC, lịch sử dictionary, thời gian hay chữ ký nghiệm thu. Checker từ chối scope nghiên cứu và chưa nối vào fit corpus thật. Sau nghiệm thu C mới nối adapter/readiness theo giao thức hiện có; không đổi schema C để ép khớp hợp đồng fixture này.


### Tín hiệu quan sát trên demo extension

Popup và banner có thể hiển thị ô mật khẩu, tên tổ chức hư cấu, quan hệ miền chưa xác minh và biểu mẫu gửi tới hostname khác. API lấy các tín hiệu từ bộ trích hiện có và từ điển fixture của bundle; không thay score/threshold. Đây là quan sát, không phải phép giải thích quyết định mô hình hoặc bằng chứng website lừa đảo.

UI chỉ hiển thị mã tín hiệu đã biết bằng câu chữ cố định, ở kết quả content hoàn tất của synthetic model. Đổi trang, lỗi, URL-only và pending xóa/ẩn tín hiệu cũ. Thiếu nội dung và lỗi API là “Chưa đánh giá được”, khác với “Chưa phát hiện dấu hiệu phishing”. Nhãn DEMO và giới hạn dữ liệu hư cấu tiếp tục hiển thị.

Sau khi cập nhật nhánh, chạy `npm run build` tại extension rồi bấm Reload ở chrome://extensions. Dừng API demo cũ trong terminal bằng Ctrl+C và chạy lại launcher với ID extension của máy mình. Mặc định bundle mới là `artifacts/models/synthetic-demo-observed-v1`: lần đầu tạo từ fixture, lần sau tải local không fit. Bundle cũ được giữ nguyên vì loader kiểm source hash và sẽ từ chối bundle tạo từ mã nguồn khác. Không dùng bundle từ người lạ.

Kiểm tra: 62 Python tests, 13 Node tests và 17 Chromium smoke checks đạt trên macOS; ảnh popup ở artifacts/smoke/observed-popup.png (ignored). Chưa kiểm trực tiếp Windows. Không đọc pilot/corpus thật, không mở training nghiên cứu và không thay giao thức đã duyệt.


### Kiểm tra tích hợp develop — 05/10/2026

Phần D của PR #4/#5/#6 được review và kiểm tra chung trên nhánh codex/d-develop-integration trước khi đưa vào develop. 71 Python tests, 13 Node tests và 17 Chromium smoke checks đạt. Hai lượt runner mặc định (160 mẫu hư cấu/40 nhóm, 5 outer fold × 3 seed, 8 variants, 2.000 bootstrap) cho 10 tệp kết quả giống nhau từng byte. Có 48 dòng summary, 30 paired comparisons và 32 dòng ca lỗi; hash đầu vào của inspector khớp run manifest. Đây là kiểm tra phần mềm trên fixture, không là bằng chứng hiệu quả phát hiện website thật.

Chạy từ repo gốc (đặt tên output mới cho mỗi lượt):

```sh
PYTHONPATH=src .venv/bin/python scripts/check_training_inputs.py --demo-fixture
PYTHONPATH=src .venv/bin/python scripts/run_synthetic_experiment.py --output artifacts/runs/my-fixture-run
PYTHONPATH=src .venv/bin/python scripts/analyze_synthetic_errors.py --run artifacts/runs/my-fixture-run --output artifacts/runs/my-fixture-errors
```

Runner dùng cohort chung, nhóm không giao nhau và chọn C/threshold bằng validation; test chỉ đánh giá. Reporter không gộp seed thành mẫu độc lập; inspector dùng nguyên ngưỡng đã lưu, kiểm hashes và không ghi đè run. Unit tests kiểm đầu vào sai, trộn nhóm/ID, nhãn/quyết định lệch, thiếu operating point, hash bị sửa và bảo vệ output cũ. Checker input fixture vẫn trả research_training_allowed=false.

Lượt nghiệm thu local nằm ở artifacts/runs/develop-integration-20261005 và develop-integration-errors-20261005 (ignored). Không ngắt API 8765 của người dùng. Windows cần B kiểm độc lập.

Điều kiện nối model thật: corpus/index/exclusion và nhãn cuối đã nghiệm thu; vấn đề tiếp xúc nhãn AI của pilot đã được xử lý; split/group và dictionary/codebook đã khóa; preprocessing/capture mode phù hợp luồng serving. Sau đó D mới kiểm readiness theo hợp đồng C, xuất bundle đúng preprocessing/dictionary/feature version và threshold validation, rồi kiểm parity API–extension. Runner hiện tại chỉ nhận fixture, không tự chuyển bundle demo thành model nghiên cứu và không tự mở training thật.


### Xuất một CV-fit mô phỏng sang API–extension

Chế độ selected-fit cố định seed 17/fold 0 trước khi xem test, dùng fit_fold hiện có cho M0/M3. C được chọn bằng validation AP (hòa chọn C nhỏ), ngưỡng chọn trên validation tại FPR mục tiêu 5%, không refit với validation. Đây là một bundle kiểm thử serving, không là mô hình tổng hợp từ CV hoặc kết quả nghiên cứu. Test metrics từ fit_fold không dùng để chọn bundle và không xuất vào provenance.

```sh
PYTHONPATH=src .venv/bin/python scripts/build_demo_bundle.py --selected-fit --output artifacts/models/my-selected-fit
PYTHONPATH=src .venv/bin/python scripts/run_demo_model_api.py --selected-fit --bundle artifacts/models/my-selected-fit --extension-id YOUR_EXTENSION_ID
```

Output phải là đường dẫn mới, không ghi đè bundle cũ. API selected-fit bắt buộc bundle đã tồn tại; thiếu/sai sẽ dừng, không tự fit hoặc chuyển sang demo khác. Chỉ dùng bundle tự tạo cục bộ: joblib có thể thực thi mã, checksum không xác thực một người gửi đáng tin cậy. Không nạp bundle tải lên hay nhận từ nguồn ngoài.

Manifest lưu preprocessing/feature/runtime/source versions & hashes, predictor checksum, hash từ điển fixture thực tế, config/dataset hashes, ID các phân vùng, seed/fold, C và chỉ số validation. Loader kiểm metadata/provenance trước deserialize; sau load kiểm từ điển trong predictor và tái tính validation để đối chiếu threshold/AP/metrics. Không fit trên load path. Scope luôn synthetic_fixture_only, research_evidence=false, chưa nối hợp đồng corpus C hoặc mở training thật.

Kiểm tra Chromium bằng bundle này (đường dẫn tương đối tính từ repo gốc):

```sh
cd extension
npm run test:browser -- --selected-fit-bundle artifacts/models/my-selected-fit
```

Lượt nghiệm thu: 77 Python tests, 13 Node tests và 18 Chromium checks đạt. Parity kiểm 24 request URL-only/stored_html/rendered_dom từ outer-test fixture: score và verdict khớp pipeline offline sau lưu/tải; empty content vẫn unable_to_assess. Các ca thiếu metadata, sai checksum/versions/identity/provenance và threshold bị sửa đều bị từ chối. Bundle tham chiếu local ở artifacts/models/selected-fit-reviewed-v1; các artifact bị ignore. Chưa kiểm trực tiếp Windows. Demo mặc định và API đang chạy của người dùng được giữ nguyên.
