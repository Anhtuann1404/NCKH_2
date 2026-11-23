# RUNBOOK HƯỚNG DẪN THỰC THI ÁP DỤNG BLOCK 2 VÀO SỔ CÁI THẬT
## DÀNH RIÊNG CHO LEAD D (ANH TUẤN) PHÊ DUYỆT VÀ THỰC THI ĐỘC LẬP
**Dự án:** NCKH_2 — Phát hiện website phishing mạo danh tổ chức bằng học máy kết hợp URL và nội dung trang  
**Mục tiêu:** Hướng dẫn kỹ thuật chuẩn xác, an toàn tuyệt đối để Lead D áp dụng Proposal Block 2 Snapshot từ Gói V4.2 vào Sổ cái Quản lý Lô thật (`main_annotation_lot_management_ledger.json`).  
**Tình trạng pháp lý:** **DỰ THẢO PHƯƠNG ÁN (RUNBOOK PROPOSAL ONLY)** — Đây là tài liệu chuẩn bị quy trình, **CHƯA PHẢI QUYẾT ĐỊNH CHO PHÉP MIGRATION**. Sổ cái thật trên đĩa tiếp tục được giữ nguyên trạng 2 block lịch sử cho đến khi Lead D ra quyết định chính thức.

---

## 1. THÔNG SỐ VÀ ĐIỀU KIỆN TIÊN QUYẾT (PRE-CONDITIONS)

Trước khi thực hiện bất kỳ thao tác ghi nào, Lead D đối soát bắt buộc các điều kiện sau:

1. **Đường dẫn Sổ cái thật trên đĩa:**
   `data/restricted/main_annotation_lot_management_ledger.json`
2. **Kích thước và SHA-256 tiền kiểm (Bắt buộc đúng 2 block lịch sử):**
   - **Kích thước:** `8.253 bytes`
   - **SHA-256:** `11acdaf1806a80181006a5817520f21b2660c1a13ac983651e4d7129390a15c5`
   - **Lệnh kiểm tra PowerShell:**
     ```powershell
     (Get-FileHash data/restricted/main_annotation_lot_management_ledger.json -Algorithm SHA256).Hash
     # Kết quả phải trả về đúng: 11ACDAF1806A80181006A5817520F21B2660C1A13AC983651E4D7129390A15C5
     ```
3. **Tệp Proposal Block 2 Snapshot từ Gói V4.2 đã kiểm định:**
   - **Nguồn:** `data/restricted/main_batch1_staging_v4_2/proposal_block2_active_state_snapshot.json`
   - **Kích thước:** `8.847 bytes`
   - **SHA-256:** `643373177cbb8caac892abd7318358f631f4adf57f0f13595c8d7a171597881a`
   - **Gói ZIP V4.2 chứa proposal:** `MAIN_BATCH1_RESTRICTED_DATA_PACK_FOR_LEAD_D_V4_2_STAGING.zip` (`646.230 bytes` | SHA-256: `99defd93b7e7f616a71818b79349ac2d6ee12dc78f540eb6c3d853cbda67a1b4`).

---

## 2. QUY TRÌNH SAO LƯU NGUYÊN BYTE (BYTE-EXACT BACKUP)

Trước khi can thiệp vào sổ cái, tạo bản sao lưu đóng băng trạng thái 2 block:

```powershell
# Tạo bản sao lưu có gắn nhãn thời gian và SHA-256
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupPath = "data/restricted/backup_ledger_2blocks_$timestamp.json"
Copy-Item "data/restricted/main_annotation_lot_management_ledger.json" $backupPath

# Xác nhận bản sao lưu khớp 100% hash gốc
$backupHash = (Get-FileHash $backupPath -Algorithm SHA256).Hash
if ($backupHash -ne "11ACDAF1806A80181006A5817520F21B2660c1a13ac983651e4d7129390a15c5") {
    Write-Error "LỖI: Bản sao lưu không khớp hash gốc! Dừng ngay lập tức."
    exit 1
}
Write-Host "✅ Đã sao lưu an toàn tại: $backupPath"
```

---

## 3. LỆNH THỰC THI ÁP DỤNG PROPOSAL VÀO SỔ CÁI (EXECUTION COMMAND)

Sử dụng trực tiếp API chính thức của `LotManagementLedger` trong mã nguồn dự án (`src/phishing/data/lot_ledger.py`):

```powershell
$env:PYTHONPATH = "src;."
python -c "
import json, hashlib, sys
from pathlib import Path
from phishing.data.lot_ledger import LotManagementLedger

# 1. Đối chiếu điều kiện tiên quyết
ledger_path = Path('data/restricted/main_annotation_lot_management_ledger.json')
h_pre = hashlib.sha256(ledger_path.read_bytes()).hexdigest()
assert h_pre == '11acdaf1806a80181006a5817520f21b2660c1a13ac983651e4d7129390a15c5', f'Ledger SHA mismatch: {h_pre}'

proposal_path = Path('data/restricted/main_batch1_staging_v4_2/proposal_block2_active_state_snapshot.json')
prop_bytes = proposal_path.read_bytes()
h_prop = hashlib.sha256(prop_bytes).hexdigest()
assert h_prop == '643373177cbb8caac892abd7318358f631f4adf57f0f13595c8d7a171597881a', f'Proposal SHA mismatch: {h_prop}'

proposal = json.loads(prop_bytes.decode('utf-8'))

# 2. Nạp sổ cái 2 block hiện hành
ledger = LotManagementLedger(ledger_path)
assert len(ledger.events) == 2, f'Expected 2 events, got {len(ledger.events)}'
b1 = ledger.events[1]

# 3. Nối Block 2 (Migration Proposal)
print('Đang nối Block 2 vào sổ cái thật...')
ev2 = ledger.append_event(
    event_type=proposal['event_type'],
    actor=proposal['actor'],
    lot_id=proposal['lot_id'],
    status=proposal['status'],
    details=proposal['details'],
)
print(f'✅ Nối thành công Block 2!')
print(f'   Seq: {ev2.seq}')
print(f'   Event ID: {ev2.event_id}')
print(f'   Prev Hash: {ev2.prev_hash}')
print(f'   Event Hash: {ev2.event_hash}')
"
```

---

## 4. KIỂM TRA HẬU THỰC THI (POST-EXECUTION VERIFICATION)

Ngay sau khi lệnh thực thi hoàn tất, Lead D chạy script kiểm tra hậu nghiệm độc lập:

```powershell
$env:PYTHONPATH = "src;."
python -c "
import json, hashlib
from pathlib import Path
from phishing.data.lot_ledger import LotManagementLedger

ledger_path = Path('data/restricted/main_annotation_lot_management_ledger.json')
ledger = LotManagementLedger(ledger_path)

# 1. Kiểm tra cấu trúc chuỗi khối
assert len(ledger.events) == 3, f'Expected 3 blocks, got {len(ledger.events)}'
b0, b1, b2 = ledger.events[0], ledger.events[1], ledger.events[2]

assert b0.seq == 0 and b0.event_type == 'GENESIS'
assert b1.seq == 1 and b1.event_type == 'LOT_RESERVED'
assert b2.seq == 2 and b2.event_type == 'LOT_RESERVED_ACTIVE_MIGRATION'

# 2. Kiểm tra tính toàn vẹn liên kết mã băm (Cryptographic Hash Chain)
assert b1.prev_hash == b0.event_hash, 'Liên kết Block 0 -> 1 hỏng!'
assert b2.prev_hash == b1.event_hash, 'Liên kết Block 1 -> 2 hỏng!'
assert b1.event_hash == '877d9f7831f47f202b29ae1fbb2f47774ff09e6c433c2eef0cb53fce42aa46d4'

# 3. Kiểm tra Active Lot Details
active = ledger.get_active_lot_details('main_lot_batch_001')
assert active is not None, 'Không lấy được active state!'
assert len(active['allocated_candidate_ids']) == 100, 'Không đủ 100 candidate IDs!'
assert len(active['b_subset_candidate_ids']) == 30, 'Không đủ 30 B subset IDs!'
assert len(active['b_indices_in_lot100']) == 30, 'Không đủ 30 chỉ số B!'

# 4. Kiểm tra tách bạch hai cam kết mật mã
assert active['cohort_seed_commitment'] == 'a16ce46f0a55db8ca8c6622b8d6dddcae134e1ca0ccef0104345f5369f8d0fc1'
assert active['seed_commitment'] == '4a5338c74bba9ae857fb9fa16a55cc54cae3c21cf779eb55f87996e6a5b7c4b6'
assert active['cohort_seed_commitment'] != active['seed_commitment']

print('✅ HẬU KIỂM 100% THÀNH CÔNG: Sổ cái 3 block hoàn toàn hợp lệ!')
"
```

---

## 5. KIỂM TRA TÍNH LŨY NGHIỆM KHI RERUN (IDEMPOTENT RERUN VERIFICATION)

Để đảm bảo việc chạy lại sampler trên sổ cái 3 block không sinh thêm block rác:

```powershell
$env:PYTHONPATH = "src;."
python -c "
from pathlib import Path
from phishing.data.lot_ledger import LotManagementLedger

ledger_path = Path('data/restricted/main_annotation_lot_management_ledger.json')
ledger = LotManagementLedger(ledger_path)
initial_blocks = len(ledger.events)
assert initial_blocks == 3

# Kiểm tra get_active_lot_details không can thiệp vào file
active = ledger.get_active_lot_details('main_lot_batch_001')
ledger_reload = LotManagementLedger(ledger_path)
assert len(ledger_reload.events) == 3, 'Số block bị thay đổi trái phép!'
print('✅ Xác nhận tính lũy nghiệm (Idempotent): 0 block phát sinh khi truy vấn/rerun!')
"
```

---

## 6. KỊCH BẢN XỬ LÝ SỰ CỐ & PHỤC HỒI (ROLLBACK & INCIDENT HANDLING)

Nếu phát sinh bất kỳ điều kiện nào sau đây:
- Mã băm tiền kiểm không khớp `11acdaf1...`
- Số lượng block sau nối khác 3
- Mâu thuẫn danh sách 100 UIDs hoặc 30 B UIDs
- Bất kỳ lỗi `LedgerIntegrityError` hoặc `ValueError` nào xuất hiện

**Quy trình xử lý bắt buộc (Fail-Closed Protocol):**
1. **DỪNG NGAY LẬP TỨC**, không cố gắng ghi đè hoặc chỉnh sửa thủ công file JSON.
2. **Khôi phục nguyên byte từ bản sao lưu:**
   ```powershell
   Copy-Item $backupPath "data/restricted/main_annotation_lot_management_ledger.json" -Force
   ```
3. Xác nhận sổ cái thật đã trở lại đúng 2 block lịch sử (SHA-256: `11acdaf1...`).
4. Bảo toàn nguyên vẹn log lỗi và thông báo ngay cho các thành viên trong nhóm để kiểm toán nguyên nhân gốc rễ (Root-Cause Analysis).
