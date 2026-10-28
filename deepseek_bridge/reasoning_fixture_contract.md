## Phân tích thiết kế cơ chế fail‑closed cho `generate_splits.py`

### 1. Nguyên tắc cốt lõi

Mục tiêu là đảm bảo bất kỳ dữ liệu nào không được chứng minh rõ ràng là dữ liệu tổng hợp (fixture) đều phải tuân thủ đầy đủ quy trình loại trừ dữ liệu thật. Cụ thể:

- **Mặc định là dữ liệu thật** : nếu không có cờ `--fixture-mode`, toàn bộ input (kể cả sample_id trung tính, không có metadata nguồn) được coi là dữ liệu thật.
- **Nhánh fixture chỉ kích hoạt khi có đủ hai yếu tố** : (1) user truyền `--fixture-mode`; (2) **100%** bản ghi có bằng chứng tổng hợp tường minh (`is_synthetic=true` và không có bất kỳ dấu vết dữ liệu thật nào theo `detect_real_data_record`).
- **Fail‑closed** : nếu ở chế độ dữ liệu thật mà thiếu `ExclusionRegistry` hoặc registry ở trạng thái không hợp lệ → thoát mã 1, không tạo bất kỳ artifact nào (groups, splits, manifest). Nếu chế độ fixture được yêu cầu nhưng dữ liệu không đạt chuẩn → thoát mã 1.

### 2. Sơ đồ luồng xử lý

```
Đọc input records
        |
        ├── args.fixture_mode == True ?
        │        |
        │        ├── YES: kiểm tra 100% bản ghi có is_synthetic=true và detect_real_data_record(record) is None
        │        │        ├── PASS → vào nhánh fixture (bỏ qua registry)
        │        │        └── FAIL → log lỗi chi tiết, sys.exit(1)
        │        |
        │        └── NO (mặc định dữ liệu thật)
        │                 ├── Kiểm tra file exclusion_registry.json tồn tại
        │                 │      └── KHÔNG → log lỗi "Missing ExclusionRegistry", sys.exit(1)
        │                 ├── Load registry và gọi assert_training_allowed()
        │                 │      └── RAISE → log lỗi, sys.exit(1)
        │                 └── Kiểm tra từng record có bị exclude không
        │                        └── CÓ → log lỗi "record X is excluded", sys.exit(1)
        │
        └── Nếu vượt qua tất cả kiểm tra → tiến hành tạo groups, splits, manifest
```

### 3. Thay đổi cụ thể trong `generate_splits.py`

#### 3.1. Thêm tham số dòng lệnh

Trong hàm `parse_args()` (hoặc tương đương), bổ sung:

```python
parser.add_argument(
    "--fixture-mode",
    action="store_true",
    help="Bật chế độ xử lý fixture: bỏ qua ExclusionRegistry, yêu cầu tất cả record phải có is_synthetic=true và không có dấu vết dữ liệu thật.",
)
```

#### 3.2. Thêm hàm kiểm tra fixture

```python
def validate_fixture_records(records: List[Dict[str, Any]]) -> List[str]:
    """Trả về danh sách lỗi nếu có record không đạt chuẩn fixture.

    Mỗi record phải có is_synthetic == True và không được detect ra dấu vết dữ liệu thật.
    """
    errors = []
    for idx, rec in enumerate(records):
        is_synthetic = rec.get("is_synthetic", False)
        if is_synthetic is not True:
            errors.append(f"Record #{idx} (sample_id={rec.get('sample_id', '?')}) thiếu is_synthetic=true")
            continue

        # Kiểm tra dấu vết dữ liệu thật
        real_data_reason = detect_real_data_record(rec)
        if real_data_reason is not None:
            errors.append(
                f"Record #{idx} (sample_id={rec.get('sample_id', '?')}) có dấu vết dữ liệu thật: {real_data_reason}"
            )
    return errors
```

#### 3.3. Thêm hàm kiểm tra dữ liệu thật

```python
def validate_real_data_compliance(
    records: List[Dict[str, Any]],
    registry_path: Path = REPO_ROOT / "data" / "exclusion_registry.json",
) -> None:
    """Kiểm tra tuân thủ chống rò rỉ cho dữ liệu thật.

    - File registry phải tồn tại.
    - Registry phải ở trạng thái cho phép huấn luyện (assert_training_allowed() pass).
    - Không bản ghi nào bị exclude theo registry.

    Nếu vi phạm, raise SystemExit(1).
    """
    # 1. Kiểm tra sự tồn tại của registry
    if not registry_path.exists():
        logger.error(
            "Chế độ dữ liệu thật yêu cầu ExclusionRegistry nhưng không tìm thấy file: %s",
            registry_path,
        )
        sys.exit(1)

    # 2. Load registry và kiểm tra trạng thái
    try:
        registry = ExclusionRegistry(registry_path)
        registry.assert_training_allowed()
    except (FileNotFoundError, RuntimeError) as exc:
        logger.error("ExclusionRegistry không hợp lệ: %s", exc)
        sys.exit(1)

    # 3. Kiểm tra từng record không bị exclude
    for idx, rec in enumerate(records):
        if registry.is_excluded(rec):
            sid = rec.get("sample_id", f"index_{idx}")
            logger.error(
                "Bản ghi %s (sample_id=%s) nằm trong ExclusionRegistry – không được phép đưa vào splits.",
                idx,
                sid,
            )
            sys.exit(1)
```

#### 3.4. Tích hợp vào hàm `main()`

Sau khi load records, trước khi thực hiện bất kỳ thao tác tạo file nào, chèn đoạn validation:

```python
def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    records = load_records(args.input_path)

    if args.fixture_mode:
        # Nhánh fixture: yêu cầu 100% bản ghi có bằng chứng fixture
        errors = validate_fixture_records(records)
        if errors:
            logger.error("Fixture mode được yêu cầu nhưng dữ liệu không đạt chuẩn:")
            for err in errors:
                logger.error("  - %s", err)
            return 1  # hoặc sys.exit(1)
        logger.info("Fixture mode: bỏ qua ExclusionRegistry.")
    else:
        # Mặc định dữ liệu thật
        validate_real_data_compliance(records)

    # ----- Các bước tiếp theo tạo groups, splits, manifest -----
    # (giữ nguyên logic hiện có, nhưng đảm bảo không tạo file trước khi qua validation)
    ...
    return 0
```

> **Lưu ý** : `return 1` từ `main()` thường được gọi qua `sys.exit(main())` ở cuối file. Đảm bảo mã thoát là 1 khi lỗi.

### 4. Backward compatibility với `tests/test_splits.py`

Các unit test hiện có thường dùng fixture data không có cờ và không có registry. Để giữ chúng pass, có hai hướng:

1. **Cập nhật test fixture** : thêm trường `is_synthetic: true` cho mọi record và truyền thêm `--fixture-mode` khi gọi CLI.
2. **Mock registry** : trong các test, tạo temporary registry hợp lệ và đặt environment variable hoặc truyền đường dẫn registry để tránh phụ thuộc file thật.

Khuyến nghị chọn hướng 1 vì nó rõ ràng và không che giấu bản chất dữ liệu.

#### Ví dụ cập nhật test:

```python
# Trước đây
result = runner.invoke(app, ["--input", str(fixture_path), ...])

# Sau khi thay đổi
result = runner.invoke(app, [
    "--fixture-mode",              # Bật chế độ fixture
    "--input", str(fixture_path),
    ...])
```

Và fixture file JSON phải có `"is_synthetic": true` trong mỗi record.

### 5. Đề xuất các test case hồi quy

Thêm vào `tests/test_splits.py` (hoặc file mới `tests/test_generate_splits_fail_closed.py`):

1. **Test chế độ dữ liệu thật thiếu registry**  
   - Tạo input JSON với 1 record trung tính (không có `is_synthetic`, không có dấu vết thật).  
   - Xoá hoặc đổi tên `data/exclusion_registry.json` (hoặc mock `REPO_ROOT` trỏ đến thư mục tạm).  
   - Chạy CLI **không** có `--fixture-mode`.  
   - Kiểm tra `exit_code == 1` và **không** có file `groups.json`, `grouped_5fold_splits.json`, ... được tạo.

2. **Test registry không hợp lệ (training_blocked hoặc unresolved mapping)**  
   - Dùng registry tạm có `training_blocked: true` hoặc `mapping_status: "unresolved_source_mapping"`.  
   - Chạy CLI với input thật.  
   - Kiểm tra `exit_code == 1`.

3. **Test record bị exclude trong dữ liệu thật**  
   - Tạo registry với một fingerprint giả, input chứa record có hash trùng.  
   - Chạy CLI, kiểm tra `exit_code == 1`.

4. **Test fixture mode thành công**  
   - Input chứa ít nhất 2 record, mỗi record có `is_synthetic=true` và không có dấu vết thật.  
   - Chạy CLI với `--fixture-mode`.  
   - Kiểm tra `exit_code == 0` và các artifact được tạo.

5. **Test fixture mode bị từ chối nếu thiếu is_synthetic**  
   - Input có 1 record fixture hợp lệ, 1 record thiếu `is_synthetic`.  
   - Chạy `--fixture-mode`.  
   - Kiểm tra `exit_code == 1`.

### 6. Các điểm cần chú ý khi triển khai

- **Thứ tự kiểm tra** : thực hiện validate **trước** khi gọi bất kỳ hàm nào ghi file (ví dụ `Path.mkdir()`, `write_text()`). Điều này đảm bảo không có artifact rác khi lỗi.
- **Logging** : sử dụng `logger.error` với thông điệp rõ ràng để người dùng biết lý do thất bại.
- **Không dùng `assert`** : vì có thể bị tắt trong môi trường production. Sử dụng `sys.exit(1)` hoặc `raise SystemExit`.
- **Tương thích với Python 3.10+** : đã import `from __future__ import annotations`, nên có thể dùng type hint hiện đại.

### Kết luận

Cơ chế trên đảm bảo an toàn tuyệt đối cho dữ liệu thật, đồng thời linh hoạt cho phát triển với fixture thông qua cờ tường minh. Việc cập nhật test giúp duy trì chất lượng và phản ánh đúng hành vi mới.