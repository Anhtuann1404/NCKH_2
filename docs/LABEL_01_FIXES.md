# Bàn giao sửa lỗi L-B01–L-B06 và pilot thật

Ngày 04/10/2026. Checkout riêng từ `feat/data-pipeline` tại `ccdfdbb`; không thay `main` hoặc lượt nhãn A/B. Đây là sản phẩm kỹ thuật, chưa phải nhãn người, nghiệm thu B/D hay khóa codebook.

## Sáu lỗi và bằng chứng

| ID | Xử lý |
| --- | --- |
| L-B01 | Giữ `v` xem toàn văn, sửa `m` để tiến từng đoạn 600 ký tự thay vì lặp đoạn 600–1.200; đồng hồ chạy suốt lúc đọc |
| L-B02 | Dry-run ghi `.dryrun.jsonl`, annotator `simulated_A/B`; kiểm hai chiều mode khi resume, cấm phiên người ghi tệp dry-run |
| L-B03 | Tận dụng kiểm annotator/pass đã có; bổ sung phát hiện ID trùng trước tiếp tục |
| L-B04 | Tận dụng lỗi JSON có số dòng; bổ sung từ chối dòng không phải object hoặc thiếu ID, giữ tệp cũ nguyên vẹn |
| L-B05 | Đọc metadata sample/package hoặc tham số CLI; từ chối thiếu codebook/random membership và random là chuỗi thay vì boolean; không mặc định mọi mẫu random hoặc version đã khóa |
| L-B06 | `random_subset` quyết mẫu số, giữ ca khó random; bỏ ca ngoài random. Kiểm A/B membership khớp, yêu cầu membership nếu chỉ có chuỗi kèm cờ khó. `label_field` tách kappa lớp và tổ chức |

Codebook mục 6 làm rõ mục tiêu/lớp, outside catalog, OAuth và UGC; mục 5 sửa quy tắc giữ ca khó random. Codebook/dictionary vẫn `pending_review`; không tự ghi B đã đồng ý.

## Gói pilot thật đã xuất local

- `data/annotations/blind_view_pilot_real.json`: 32 mẫu thật, không có source label/target/prediction/lượt B; version lấy từ dictionary nháp. Gói bị CLI chặn nhập người cho tới khi B/D nghiệm thu và C xuất bản khóa.
- `configs/pilot_manifest.json`: manifest chia sẻ được, hash codebook/dictionary/view/mapping, revision/shard/checksum nguồn bổ sung, phiên bản Python/PyArrow/TLDExtract và hash snapshot PSL.
- `data/raw/pilot/source_mapping.json`: **C-only**, có lớp nguồn, ID–nguồn–offset, hash raw URL/HTML và nhóm miền. Không chia sẻ cho A/B trước khóa lượt độc lập.
- `data/raw/pilot/blind_order.json`: hoán vị random giữ riêng ở C để ID không lộ 12 mẫu bổ sung đều phishing. Dùng lại hoán vị khi tái xuất cùng batch; không công bố seed/mapping.
- `data/raw/pilot/exclusion_registry_real.json`: registry chi tiết C-only. Registry chia sẻ `data/exclusion_registry.json` có union hashes URL/HTML/nhóm của 32 mẫu, không ghép lớp nguồn theo ID. 20 mẫu cũ là subset, không cộng thành 52.

Raw, view thật, bảng ánh xạ và hoán vị đều được Git ignore. Không đổi gói synthetic đã có thành “thật”; giữ hai gói riêng. View là trích văn bản/cấu trúc, không render HTML, không truy cập URL website. Không chứng nhận mọi text/URL là đã ẩn hết thông tin cá nhân; gói được giữ ở khu vực hạn chế.

### Nguồn và giới hạn xác minh

20 mẫu kỹ thuật được khôi phục từ rows API train offset 0, length 20; **SHA-256 toàn bộ byte khớp chính xác checksum lưu từ lần thu trước**: `738ea69b920cb3037d7e9da38590024d8faa5f34c2eca6c760cb34690f2f190f`. Có 8 source-phish và 12 source-benign; đây chưa là lớp đã được người xác nhận. API cũ không pinned revision, nên không tự gán 20 dòng đó thuộc commit metadata. Mapping shard/offset pinned của 20 mẫu vẫn unresolved và training tiếp tục bị chặn.

12 source-phish bổ sung lấy từ `data/train-055.parquet` của revision `eabec4b7a66324b79cc8a0ad856d1731dc26fe1a`. Đã tải tệp 20.213.199 byte và xác minh SHA-256 cục bộ khớp Git-LFS metadata `205a7e1cf4fb11032683e90fdbd1c13ddc9d9dd86109658d13e69929b53b31d0`. Chọn 12 đầu theo thứ tự row trong shard, HTML không rỗng và <=2.000.000 ký tự, loại trùng exact URL+HTML với pilot cũ; không chọn theo brand/target/model. Không mở official test.

HTML của một mẫu cũ vượt giới hạn parser mặc định 1.000.000 ký tự. Export offline dùng giới hạn tường minh 2.000.000 và giữ nguyên nội dung, không truncate; giới hạn mặc định runtime giữ 1.000.000. URL thiếu scheme thêm HTTPS theo quy tắc cố định và giữ raw ở nguồn hạn chế, không chứng minh endpoint thật dùng HTTPS.

Exclusion lọc bằng hash raw URL, hash raw HTML và hash miền từ PSL offline có private suffixes, để cùng miền/tenant bảo thủ không vào đánh giá. Vẫn cần C nối near-duplicate components trong pipeline chính; bộ lọc hash không tự chứng minh đã giải quyết mọi gần trùng.

## Tái xuất và kiểm kỹ thuật

Sau khi C có hai tệp nguồn đúng checksum trong khu vực hạn chế:

```powershell
python scripts/data/build_real_pilot.py --technical-json data/raw/pilot/technical20_api.json --extra-parquet data/raw/pilot/train-055.parquet
$env:PYTHONPATH = 'src'
python -m pytest tests/ -q --basetemp=tmp/pytest-label-review
```

Builder từ chối checksum sai. Tái lập cần Python, PyArrow và TLDExtract đúng runtime/PSL trong manifest. Lệnh pytest cần thư mục cha `tmp` tồn tại và basetemp riêng trong workspace.

Đã chạy toàn bộ `tests/`: **86 passed, 32 subtests passed** trên Python 3.14.3, pytest 9.1.1; builder dùng PyArrow 25.0.1 và TLDExtract 5.4.0. Kiểm thêm gói real32: hash view, allowlist/ID, version, counts nguồn và exclusion đều đạt; CLI dry-run xuất 32 bản ghi `simulated_A` trong `tmp/real32_cli.dryrun.jsonl`, không tạo lượt người. Các kết quả này chỉ kiểm kỹ thuật, không phải kappa hoặc giờ pilot thực.

Gói pilot có full overlap A/B để đo giờ/đồng thuận pilot; không gọi đó là subset 30% của tập chính. Chỉ thời gian đọc người thực trên gói thật sau nghiệm thu được đưa vào PLAN-01. Dry-run hardcode thời gian 0,5 giây là kiểm kỹ thuật.

## Điều kiện bàn giao còn lại

1. B/D rà bốn quy tắc, nguồn/hashes và ký nghiệm thu; C khóa version/hash, tái xuất view và manifest đồng bộ.
2. C giải quyết pinned-shard mapping của 20 mẫu cũ trước mở huấn luyện/đánh giá chính. Checksum batch cũ và hash/nhóm đã có giúp exclusion, chưa thay chứng minh mapping revision.
3. B/D kiểm nội dung/sanitization và phạm vi riêng tư trong gói hạn chế. A/B chỉ nhận view và metadata nhãn mù, không nhận mapping/classes/order của C.
4. Sau đó A/B tự đọc độc lập, ghi thời gian thật; chưa có lượt người hoặc chỉ số kappa thật từ thay đổi này.
