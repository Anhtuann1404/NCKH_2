## Đánh giá sự cố lộ định danh trong `data/exclusion_registry.json` tại commit `f89dccc`

### 1. Tóm tắt sự cố và bối cảnh

Tại commit `f89dccc`, tệp `data/exclusion_registry.json` – vốn được tạo ra như một phần của quy trình khắc phục sự cố lộ locator (Sự cố 01 & 02) – lại tiếp tục chứa **thông tin định danh thô** của 32 mẫu Clean Calibration. Cụ thể, các trường `group_id` (định dạng `domain:<tên-miền-thực>`) và `source_date` (ngày thu thập từ shard nguồn) xuất hiện công khai trong registry trên Git. Điều này tạo ra một **lỗ hổng rò rỉ định danh mới**, mặc dù các mẫu này đã bị loại khỏi tập huấn luyện/kiểm thử theo đúng quy trình của Sự cố 01.

### 2. Đánh giá mức độ lộ thông tin định danh

So sánh với các tiền lệ đã ghi nhận:

| Tiêu chí | Sự cố 01 | Sự cố 02 | Sự cố f89dccc (registry) |
|----------|-----------|-----------|---------------------------|
| **Loại dữ liệu lộ** | `relative_path`, `row_offset` | `relative_path`, `row_offset`, `url_sha256`, `html_sha256`, `group_id` (domain) | `group_id` (domain), `source_date` |
| **Khả năng truy ngược nguồn** | Cần truy cập vào parquet nội bộ | Có thể truy ngược bằng cách khớp hash hoặc domain | Có thể truy ngược trực tiếp bằng domain và ngày thu thập |
| **Ảnh hưởng đến mù đôi** | Cao – lộ vị trí dòng trong dữ liệu gốc | Rất cao – lộ định danh trang web thực tế | **Rất cao** – domain thực là định danh duy nhất của mẫu phishing, source_date giúp xác định snapshot dữ liệu |
| **Khả năng bị lạm dụng** | Nội bộ: rà soát thủ công | Bên thứ ba có thể truy cập website phishing trực tiếp | Tương tự Sự cố 02 – domain là đủ để mở trang web, source_date giúp tìm đúng phiên bản lưu trữ |

**Kết luận mức độ:** Sự cố này có mức độ nghiêm trọng **tương đương Sự cố 02** (lộ `group_id` dạng domain) và có phần nhẹ hơn vì không kèm `relative_path`/`row_offset`, nhưng vẫn là vi phạm nguyên tắc **Zero Data Leakage** và **double‑blind annotation** vì domain thực tế chính là yếu tố định danh mạnh nhất. `source_date` bổ sung thông tin thời gian, giúp thu hẹp phạm vi tìm kiếm trong nguồn dữ liệu gốc hoặc trên Internet.

### 3. Đối chiếu với tiền lệ xử lý Sự cố 01 & 02

- **Sự cố 01** (32 mẫu lộ locator): Đã loại toàn bộ 32 mẫu, đăng ký vào registry với batch `EXCL-CALIB-CLEAN-32-EXPOSED-ON-GIT`.  
  **Sai lầm hiện tại:** Khi đăng ký, registry không được sanitize kỹ lưỡng; thông tin `group_id` và `source_date` được giữ nguyên thay vì chỉ lưu hash hoặc ID mù.

- **Sự cố 02** (2 mẫu lộ locator + domain): Đã loại 2 mẫu, đăng ký vào batch `EXCL-CALIB-CLEAN-02-PAIRWISE-RESOLUTION-LOCATOR-EXPOSED`.  
  **Lỗi tương tự:** registry vẫn chứa `group_id` dạng domain (như đã thấy trong `leak_incident_2.exposed_locators`).

Cả hai tiền lệ đều nhấn mạnh nguyên tắc: **tất cả artifact công khai trên Git phải không chứa bất kỳ locator nào (path, row offset) cũng như định danh thô (domain, hash URL/HTML)**. Sự cố tại `f89dccc` cho thấy quy trình sanitize đã không được áp dụng triệt để cho chính `exclusion_registry.json`.

### 4. Phản biện phương án “Giữ” vs “Loại” cả 32 mẫu

#### 4.1. Phương án Giữ nguyên registry (chỉ sửa nội dung)

**Ưu điểm:**
- Các mẫu đã bị loại vĩnh viễn khỏi mọi tập dữ liệu, không ảnh hưởng đến quá trình huấn luyện hay đánh giá hiện tại.
- Registry chỉ phục vụ mục đích đối chiếu trùng lặp, không dùng lại mẫu.
- Tiết kiệm công sức tuyển chọn lại.

**Nhược điểm:**
- Vi phạm nguyên tắc Zero Git Leakage: domain thực là định danh trực tiếp, có thể bị bên thứ ba thu thập và sử dụng cho các mục đích khác (ví dụ: dò quét phishing, học máy đối thủ).
- Tạo tiền lệ xấu: nếu chấp nhận domain trong registry, các bước sau khó kiểm soát được rò rỉ.
- Khó đảm bảo mù đôi cho các đợt tuyển chọn tương lai nếu thông tin domain bị lộ ra ngoài.

#### 4.2. Phương án Loại bỏ hoàn toàn định danh khỏi registry công khai

**Ưu điểm:**
- Tuân thủ nghiêm ngặt nguyên tắc “zero identifier” trong mọi artifact công khai.
- Giảm thiểu rủi ro bị lạm dụng thông tin.
- Buộc thiết kế registry theo hướng hash‑based, tách biệt dữ liệu nhạy cảm vào khu vực hạn chế.

**Nhược điểm:**
- Cần phát triển thêm cơ chế hash có salt, quản lý khóa bí mật.
- Mất khả năng tra cứu nhanh bằng domain (nhưng điều này không cần thiết cho mục đích loại trừ).

#### 4.3. Kết luận phản biện

Không cần phải **hủy bỏ việc loại trừ** 32 mẫu – vì chúng đã bị loại và không được sử dụng lại. Tuy nhiên, cần phải **loại bỏ toàn bộ thông tin định danh thô** khỏi registry công khai. Nghĩa là:

- **Không “Giữ”** registry như hiện trạng (chứa domain + source_date).
- **Không “Loại”** 32 mẫu khỏi trạng thái loại trừ (vì chúng vẫn phải được loại trừ vĩnh viễn).  
- **Chuyển đổi** registry sang dạng chỉ lưu hash không thể đảo ngược của định danh (salted SHA‑256) và lý do loại trừ; chi tiết thô được cất trong `data/restricted/` (ngoài Git).

Việc tuyển lại tập mới (Đợt B, 24 chính + 8 dự phòng) đã được thực hiện đúng cách sau Sự cố 01, không cần lặp lại vì sự cố registry mới này không làm thay đổi tính hợp lệ của các mẫu mới. Do đó, **không cần tuyển lại tập mới** do sự cố này; chỉ cần sửa lại registry và tăng cường kiểm thử chống rò rỉ.

### 5. Thiết kế cấu trúc Zero Git Leakage cho registry

#### 5.1. Nguyên tắc thiết kế

- **Tách biệt công khai / hạn chế:** Mọi thông tin định danh thô (domain, source_date, relative_path, row_offset, url_sha256, html_sha256) chỉ được lưu trong thư mục `data/restricted/` – không được commit lên Git (được thêm vào `.gitignore`).
- **Băm có salt:** Sử dụng SHA‑256 với salt ngẫu nhiên (lưu trong biến môi trường hoặc file secret không công khai) để tạo `uid_hash` cho mỗi mẫu. Salt phải đủ dài để chống brute‑force.
- **Không lưu bất kỳ trường nào có thể dùng để tái định danh trực tiếp:** Chỉ lưu hash, batch id, lý do loại trừ, ngày loại trừ (không phải source_date của mẫu).

#### 5.2. Schema đề xuất cho `data/exclusion_registry.json` (bản công khai)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "registry_version": "1.2.0-ZERO-LEAK",
  "last_updated_utc": "2026-10-24T12:00:00Z",
  "entries": [
    {
      "batch_id": "EXCL-CALIB-CLEAN-32-EXPOSED-ON-GIT",
      "uid_hash": "sha256:9f2c4f6a...",           // salted hash của định danh mẫu
      "exclusion_reason": "git_locator_exposure",
      "exclusion_date_utc": "2026-10-24"
    },
    {
      "batch_id": "EXCL-CALIB-CLEAN-02-PAIRWISE-RESOLUTION-LOCATOR-EXPOSED",
      "uid_hash": "sha256:b3a7e2d1...",
      "exclusion_reason": "git_locator_and_domain_exposure",
      "exclusion_date_utc": "2026-10-24"
    }
  ]
}
```

#### 5.3. File ánh xạ hạn chế (nằm trong `data/restricted/`)

`data/restricted/clean_calibration_exclusion_mapping_32.json` chứa:

```json
{
  "salt_version": "v1",
  "salt_sha256": "abc123...",   // hash của salt (để kiểm tra tính nhất quán)
  "mappings": [
    {
      "uid_hash": "sha256:9f2c4f6a...",
      "sample_id": "SMP-001",
      "group_id": "domain:learngala.com",
      "source_date": "2025-07-14",
      "relative_path": "data/train-000.parquet",
      "row_offset": 51,
      "url_sha256": "51f22da...",
      "html_sha256": "b4f90cf..."
    }
  ]
}
```

File này **không bao giờ được commit**, phải có trong `.gitignore`.

#### 5.4. Quy trình bảo mật

- **Pre‑commit hook:** Chặn mọi commit có chứa pattern `domain:`, `source_date`, `relative_path`, `row_offset`, `sha256` (nếu không được whitelist).
- **Salt rotation:** Khi cần thay đổi salt, phải cập nhật lại toàn bộ hash; phiên bản salt được lưu trong registry công khai dưới dạng hash để xác minh.

### 6. Đặc tả regression tests quét toàn bộ artifact công khai

#### 6.1. Mục tiêu

Đảm bảo **không có bất kỳ artifact công khai nào** (bao gồm registry, manifest, audit, báo cáo, mã nguồn scripts) chứa thông tin định danh thô hoặc locator. Các test phải chạy tự động trong CI và có thể chạy local.

#### 6.2. Phạm vi quét

- Toàn bộ repository, trừ các thư mục: `.git/`, `data/restricted/`, `.gitignore`, `*.log`, `venv/`, `__pycache__/`.
- Các file văn bản: `.json`, `.py`, `.md`, `.txt`, `.yaml`, `.yml`, `.toml`.

#### 6.3. Các pattern cần phát hiện (blacklist)

| Loại thông tin | Biểu thức chính quy (regex) | Ghi chú |
|----------------|------------------------------|---------|
| `group_id` dạng domain | `"group_id"\s*:\s*"domain:[^"]+"` hoặc `domain:[a-zA-Z0-9.-]+` | Bắt cả domain thô sau tiền tố `domain:` |
| `source_date` | `"source_date"\s*:\s*"\d{4}-\d{2}-\d{2}"` | Ngày thu thập |
| `relative_path` | `"relative_path"\s*:\s*"data/train-\d+\.parquet"` | Đường dẫn tới shard nguồn |
| `row_offset` | `"row_offset"\s*:\s*\d+` | Vị trí dòng trong parquet |
| `url_sha256` / `html_sha256` | `"(url\|html)_sha256"\s*:\s*"[0-9a-f]{64}"` | Hash 64 ký tự hex |
| URL đầy đủ (nếu có) | `https?://[^\s"]+` | Có thể cần whitelist các URL chính thức của tổ chức (không liên quan đến mẫu) |

#### 6.4. Các test case cụ thể

1. **Test `test_public_artifacts_do_not_contain_group_id`**  
   - Quét tất cả file công khai, assert không tìm thấy pattern `domain:[a-zA-Z0-9.-]+` hoặc `"group_id"\s*:\s*"domain:`.  
   - Expected: không có match.

2. **Test `test_public_artifacts_do_not_contain_source_date`**  
   - Tìm `"source_date"` hoặc chuỗi ngày dạng `YYYY-MM-DD` (trong ngữ cảnh source_date).  
   - Expected: không có match.

3. **Test `test_public_artifacts_do_not_contain_relative_path`**  
   - Tìm `"relative_path"\s*:\s*"data/train-\d+\.parquet"`.  
   - Expected: không có match.

4. **Test `test_public_artifacts_do_not_contain_row_offset`**  
   - Tìm `"row_offset"\s*:\s*\d+`.  
   - Expected: không có match.

5. **Test `test_public_artifacts_do_not_contain_sha256_hashes_of_samples`**  
   - Tìm `"(url|html)_sha256"\s*:\s*"[0-9a-f]{64}"`.  
   - Expected: không có match.

6. **Test `test_exclusion_registry_schema_is_zero_leak`**  
   - Đọc `data/exclusion_registry.json`, parse JSON.  
   - Đảm bảo mỗi entry chỉ có các khóa: `batch_id`, `uid_hash`, `exclusion_reason`, `exclusion_date_utc` (và có thể `$schema`, `registry_version`, `last_updated_utc`).  
   - Đảm bảo `uid_hash` phải match pattern `^sha256:[0-9a-f]{64}$`.  
   - Đảm bảo không tồn tại bất kỳ khóa nào trong blacklist.

7. **Test `test_manifest_and_audit_reports_do_not_leak_identifiers`**  
   - Kiểm tra các file `calibration_clean_a_manifest.json`, `clean_calibration_git_leak_audit.json` (và các file tương tự) xem có chứa pattern blacklist không.  
   - Lưu ý: file audit có thể chứa mô tả sự cố nhưng phải được sanitize (không chứa domain thô, hash, row offset).  
   - Expected: không có match.

8. **Test `test_restricted_files_are_not_tracked_by_git`**  
   - Dùng `git ls-files` để liệt kê các file được theo dõi; assert không có file nào thuộc `data/restricted/`.  
   - Assert `.gitignore` chứa `data/restricted/`.

#### 6.5. Kỹ thuật thực thi

- Sử dụng Python `pytest` kết hợp với `pathlib` để duyệt cây thư mục, `re` để so khớp.
- Đọc nội dung file an toàn (xử lý encoding).
- Cho phép whitelist một số file nhất định (ví dụ: tài liệu chính sách có thể chứa ví dụ URL chung của tổ chức, nhưng không phải domain của mẫu phishing). Whitelist phải được khai báo tường minh trong cấu hình test.
- Kết quả test phải fail nếu bất kỳ pattern nào xuất hiện.

### 7. Kết luận

Sự cố tại commit `f89dccc` là một **lỗ hổng rò rỉ định danh nghiêm trọng** do thiếu sanitize khi tạo `data/exclusion_registry.json`. So với Sự cố 01 và 02, mức độ lộ tương đương Sự cố 02 (lộ domain thực) và cần được khắc phục ngay lập tức. Phương án đúng đắn là **không giữ nguyên registry** nhưng cũng **không hủy bỏ trạng thái loại trừ** của 32 mẫu; thay vào đó là **chuyển đổi registry sang dạng hash‑based zero‑leak**, tách biệt dữ liệu nhạy cảm vào khu vực hạn chế. Đồng thời, bổ sung **regression tests** quét toàn bộ artifact công khai để ngăn chặn tái diễn. Các biện pháp này đảm bảo tính toàn vẹn của giao thức phòng sạch và tuân thủ nguyên tắc Zero Data Leakage trong toàn bộ dự án NCKH.