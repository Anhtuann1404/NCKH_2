# Pilot V2: chưa nghiệm thu, yêu cầu xây lại từ nguồn xác minh

Cập nhật của Lead D ngày 06/10/2026: gói V2 cũ chưa chứng minh nguồn thực tế;
script cũ khai báo HTML/nhãn trực tiếp và bảng nhãn từng xuất hiện trên Git chung.
Gói này không được dùng cho Kappa, PLAN-01 hoặc kết quả nghiên cứu.
V1 tiếp tục invalidated; mọi dữ liệu, nhãn, log và exclusion cũ phải giữ nguyên.

Bảng ánh xạ đã được gỡ khỏi phiên bản hiện tại. Lịch sử Git vẫn chứa bản cũ:
không tuyên bố đã khôi phục tính mù bằng việc xóa bảng. A/B phải xác nhận phạm vi
đã xem; C/D kiểm tra hồ sơ tiếp xúc trước khi cấp gói mới. Không gửi raw/mapping
cho A/B. Chỉ giao view mù đã duyệt qua kênh riêng.

## Xây lại gói (C/D, máy cục bộ)

`scripts/data/build_real_pilot_v2.py` đọc đúng dòng từ shard train đã kiểm SHA-256
và kích thước theo source_manifest. Không nhận HTML/nhãn khai báo trong selection.
Không sửa hoặc ghi đè manifest/registry/gói cũ. Output mới nằm trong data/raw,
gồm view mù, source_mapping, blind_order, manifest pending và registry đề xuất.

Selection JSON hạn chế: revision khớp source_manifest; records gồm đúng 32 object
chỉ có relative_path (ví dụ data/train-000.parquet) và row_offset (int >= 0).
Nhãn nguồn chỉ để chọn 20 phishing/12 benign, không phải nhãn tham chiếu đã kiểm chứng.

Prior evidence JSON hạn chế: packages gồm đúng bốn loại practice (20), v1 (32),
audit (20), v2_unverified (32). Mỗi object có kind, path (tương đối so với file evidence)
và sha256 byte file. Mỗi file chứa mảng các record url/html nguyên bản đã từng mở.
C/D phải đối chiếu hash và độ đầy đủ với hồ sơ bàn giao lưu giữ. Thiếu raw/history
là blocker; không tự dựng HTML thay thế hoặc bỏ qua một nhóm để kết luận không trùng.
Cần kiểm soát cả các lượt tiếp xúc khác ngoài bốn nhóm; nếu phát sinh phải cập nhật
hồ sơ và bộ kiểm tra trước khi xây gói.

```bash
PYTHONPATH=src python scripts/data/build_real_pilot_v2.py \
  --selection data/raw/pilot_rebuild/selection.json \
  --source-root data/raw/phreshphish \
  --prior-evidence data/raw/pilot_rebuild/prior_evidence.json \
  --output data/raw/pilot_rebuild/package-new
```

Builder so trùng URL, URL chuẩn hóa, HTML byte và nội dung view cùng nhóm miền/tenant
bằng quy tắc offline dùng chung. HTML không strip trước khi hash. Nếu bất kỳ đầu vào,
checksum, offset, nhãn nguồn hoặc đối chiếu chống trùng sai thì dừng trước công bố.

Sau khi D/B nghiệm thu nguồn, tính mù, hash và registry đề xuất, C/D mới cập nhật
registry chính (giữ mọi entry cũ), sao chép manifest và view tới đường dẫn bàn giao.
D/B ký acceptance=approved; exposure_review A/B/D phải approved và ready_for_annotation
chỉ mở sau khi đối chiếu cuối. Builder không thực hiện các phê duyệt này.

```bash
python scripts/annotate_cli.py --annotator A \
  --manifest data/raw/pilot_rebuild/package-new/pilot_manifest_v2.json \
  --input data/raw/pilot_rebuild/package-new/blind_view_pilot_real_v2.json \
  --output data/labels/A/labels_pass1_v2.jsonl
```

B dùng annotator B và output riêng. Hai người tự đọc/chọn nhãn theo codebook,
không AI gợi ý nhãn, không trao đổi Pass 1. seconds_spent do CLI ghi.
Lệnh trên cố ý bị chặn với gói pending; không sửa cờ để tập dượt bằng gói thật.

## Kiểm thử

Unit test tự chứa: `python -m pytest tests -q -m "not integration"`.
Integration test cần gói riêng: `python -m pytest tests -q -m integration`.
Không chạy builder để tạo dữ liệu hư cấu rồi gọi đó là bằng chứng nghiệm thu dữ liệu thật.
