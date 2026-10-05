# API specification v0.1

**Trạng thái:** hợp đồng v0.1; đã có FastAPI mock và MV3 demo, chưa có server suy luận mô hình thật. Nguồn schema máy đọc: [openapi.json](openapi.json), OpenAPI 3.1. Ví dụ là mô phỏng với URL example.org; không có kết quả mô hình thật.

Backend synthetic model đã nối cùng các route API, dùng model/bundle `synthetic-demo-*`, health `model_ready=true` khi tải thành công và các limitation bắt buộc `synthetic_training_only`, `not_research_evidence`. Bundle này chỉ phục vụ demo bằng fixture; xem DEVELOPMENT để build/tải và chạy.

Mock hiện chạy với `snapshot-dev-0`, model/bundle có prefix `mock-only-*` và limitation `mock_response_not_model_result`; health `model_ready=false`. Scenario là cấu hình server, không là trường request. Ví dụ `snapshot-v1` bên dưới vẫn là thiết kế pipeline tương lai và sẽ bị mock trả 409. Lệnh cài/chạy/mock scenarios ở [DEVELOPMENT](DEVELOPMENT.md). Schema JSON không đổi trong lượt triển khai này.

## Kết nối

Base URL demo dự kiến `http://127.0.0.1:8765`. API bind loopback, kiểm Host; không public mặc định. `/v1/*` yêu cầu `Authorization: Bearer <local-token>` sinh ngẫu nhiên khi setup; token không nằm trong code, docs hoặc Git.

Cho phép origin extension ID được cấu hình rõ, không CORS `*` và không tin mọi chrome-extension origin. Service worker gửi request, content script không giữ token. Token đặt trong storage cục bộ hạn chế truy cập content scripts khi triển khai; không storage.sync. HTTP body JSON, giới hạn 2 MiB UTF-8 ở server trước parse; JSON Schema maxLength không thay giới hạn byte. Chỉ chấp nhận URL http/https hợp lệ sau chuẩn hóa.

## Endpoint

- `GET /health`: liveness công khai trên loopback, status ok và model_ready. Model chưa load vẫn liveness 200; không có nghĩa đã sẵn sàng phân tích.
- `GET /v1/model`: metadata bundle đang active; 503 khi chưa load hoặc checksum/version không khớp.
- `POST /v1/analyze`: phân tích snapshot, 200 khi xử lý xong hoặc nội dung chưa đủ; 503 khi mô hình không sẵn sàng.

Không có endpoint nhận label/target, upload mô hình, train, fetch URL hay lưu lịch sử duyệt.

## Request analyze

Trường chung: request_id UUID, navigation_id UUID, dom_revision >=0, phase, url đã chuẩn hóa không userinfo/fragment và không query values nhạy cảm, preprocessing_version, capture_mode.

- `phase=url_only`: không có html, dùng M0 cho sơ bộ; capture_mode `url_only`.
- `phase=url_content`: html snapshot đã làm sạch, tối đa 1.000.000 ký tự; capture_mode `rendered_dom` hoặc `stored_html` cho replay. Backend không thực thi/fetch tài nguyên.
- Hai phase là schema oneOf; không nhận trường thừa, source_label, target, tier hoặc score client.
- Preprocessing version không được bundle hỗ trợ → 409; không ngầm phân tích bằng pipeline khác.

```json
{
  "request_id": "11111111-1111-4111-8111-111111111111",
  "navigation_id": "22222222-2222-4222-8222-222222222222",
  "dom_revision": 1,
  "phase": "url_content",
  "url": "https://example.org/account",
  "html": "<html><body><h1>Example account</h1><form><input type=\"password\"></form></body></html>",
  "preprocessing_version": "snapshot-v1",
  "capture_mode": "rendered_dom"
}
```

## Response analyze

Echo request_id/navigation_id/dom_revision/phase; status `completed` hoặc `insufficient_content`; verdict `warning`, `no_indication`, `unable_to_assess`; score/threshold; model metadata; signals; limitations; timing_ms.

Score là điểm 0–1 chưa hiệu chuẩn, không gọi là xác suất lừa đảo. Completed có score/threshold và verdict nhất quán score >= threshold. Insufficient content: score/threshold null, verdict unable_to_assess, không tự lấy M0 thay cho nội dung mà không nói rõ; extension có thể hiện kết quả URL sơ bộ trước đó với nhãn phù hợp.

Signal có code, org_candidate_id nullable, domain_relation (`verified_first_party`, `verified_authorized`, `unverified_shared_hosting`, `unverified`, `mismatch`, `not_applicable`) và thông điệp tĩnh. Chỉ là quan sát/ứng viên, không phải nhãn tổ chức chuẩn hoặc giải thích nhân quả model. Không trả raw HTML, URL đầy đủ hoặc đoạn có dữ liệu điền.

```json
{
  "request_id": "11111111-1111-4111-8111-111111111111",
  "navigation_id": "22222222-2222-4222-8222-222222222222",
  "dom_revision": 1,
  "phase": "url_content",
  "status": "completed",
  "verdict": "warning",
  "score": 0.82,
  "threshold": 0.75,
  "model": {
    "model_id": "demo-example-only",
    "variant": "M3",
    "preprocessing_version": "snapshot-v1",
    "dictionary_version": "example-only",
    "score_semantics": "uncalibrated_model_score"
  },
  "signals": [{
    "code": "sensitive_form_detected",
    "org_candidate_id": null,
    "domain_relation": "not_applicable",
    "message": "Quan sát thấy trường yêu cầu mật khẩu."
  }],
  "limitations": ["example_response_not_model_result"],
  "timing_ms": {"preprocess": 3, "extract": 8, "infer": 2, "server_total": 14}
}
```

Các số trên chỉ minh họa contract, không là ngưỡng được chọn hoặc độ trễ đã đo. timing server dùng monotonic clock; độ trễ từ điều hướng/DOM đến cảnh báo do extension đo riêng, không trừ đồng hồ client/server.

## Lỗi

Error body chung: error.code, error.message an toàn, request_id nullable. Không echo input nhạy cảm.

- 401: missing/invalid token.
- 403: origin/host bị từ chối.
- 409: preprocessing/bundle không tương thích.
- 413: payload quá lớn; client báo chưa đánh giá, không cắt HTML im lặng.
- 415: content type không hỗ trợ.
- 422: request/schema/URL không hợp lệ.
- 429: quá nhiều request, client debounce/backoff.
- 500: lỗi nội bộ, không trả stack trace/data.
- 503: bundle chưa sẵn sàng.
- 504: vượt ngân sách xử lý server.

Client timeout/network error là lỗi kết nối cục bộ, không phải kết luận benign. Retry tối đa một lần còn cùng navigation/revision; request_id mới cho lần thử, không lặp vô hạn.

## Hiển thị và cạnh tranh request

`warning` → “Có dấu hiệu phishing”; `no_indication` → “Chưa phát hiện dấu hiệu phishing”; `unable_to_assess`/API lỗi → “Chưa đánh giá được”. URL-only phải có nhãn sơ bộ. Response đến muộn/navigation khác/revision cũ bị bỏ; không cập nhật UI trang mới bằng kết quả trang cũ.

API không log body/raw URL. Diagnostic log chỉ mã yêu cầu, code lỗi, version và timing không chứa nội dung; cache ban đầu tắt để tránh lưu trang nhạy cảm. Health/metadata không chứng minh privacy tự động; kiểm bằng fixture/network log an toàn khi triển khai.

## Tiêu chí nghiệm thu API sau này

Contract examples hợp schema; token/origin/body-limit có test; malformed URL và metadata labels bị từ chối; không outbound fetch khi infer; checksum sai không ready; version mismatch 409; content thiếu không verdict benign; timing và active model đúng bundle. Cặp replay offline/API cùng snapshot có điểm/tín hiệu nhất quán trong tolerance định trước.

[OpenAPI 3.1](https://spec.openapis.org/oas/v3.1.0) là chuẩn hợp đồng. Sửa contract phải cập nhật JSON và tài liệu trong cùng thay đổi; breaking change tăng version, không tự sửa client/server lệch nhau.
