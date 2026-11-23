# RUNBOOK HƯỚNG DẪN THỰC THI DI TRÚ BLOCK 2 VÀO SỔ CÁI QUẢN LÝ LÔ
## DÀNH RIÊNG CHO LEAD D (ANH TUẤN) THẨM DUYỆT VÀ THỰC THI ĐỘC LẬP
**Dự án:** NCKH_2 — Phát hiện website phishing mạo danh tổ chức bằng học máy kết hợp URL và nội dung trang  
**Mục tiêu:** Cung cấp quy trình thủ tục từng bước có kiểm soát chặt chẽ để Lead D thẩm định và thực thi áp dụng Proposal Block 2 Snapshot từ Gói V4.2 vào Sổ cái Quản lý Lô (`main_annotation_lot_management_ledger.json`).  
**Tình trạng pháp lý:** **DỰ THẢO PHƯƠNG ÁN (RUNBOOK PROPOSAL ONLY)** — Đây là tài liệu quy trình kỹ thuật, **CHƯA PHẢI QUYẾT ĐỊNH THỰC THI TRÊN SỔ CÁI THẬT**. Sổ cái thật trên đĩa tiếp tục được giữ nguyên trạng 2 block lịch sử (SHA-256: `11acdaf1...`) cho đến khi Lead D ra quyết định chính thức.

> [!NOTE]
> **Đặc tính kỹ thuật về tính nguyên tử (Atomicity Boundary):**  
> Mã nguồn `LotManagementLedger` trong `src/phishing/data/lot_ledger.py` thực hiện ghi tệp xuống đĩa thông qua tệp tạm và hoán đổi nguyên tử (`os.replace`). Tuy nhiên, toàn bộ chuỗi quy trình bao gồm: Tiền kiểm $\rightarrow$ Sao lưu $\rightarrow$ Nối Block 2 $\rightarrow$ Hậu kiểm $\rightarrow$ Phục hồi sự cố là một quy trình thủ tục tuần tự nhiều bước (Guarded Procedural Execution), không cấu thành một giao dịch ACID duy nhất trên toàn hệ thống. Mọi điều kiện dừng và phục hồi phải tuân thủ nghiêm ngặt các cổng kiểm tra độc lập dưới đây.

---

## 1. THÔNG SỐ VÀ ĐIỀU KIỆN TIÊN QUYẾT (PRE-CONDITIONS)

Trước khi thực hiện bất kỳ thao tác ghi nào, thiết lập môi trường và kiểm tra các điều kiện tiên quyết:

```powershell
$env:PYTHONPATH = "src;."
$env:LEDGER_PATH = "data/restricted/main_annotation_lot_management_ledger.json"
$env:PROPOSAL_PATH = "data/restricted/main_batch1_staging_v4_2/proposal_block2_active_state_snapshot.json"
```

Chạy script tiền kiểm độc lập (sử dụng kiểm tra rõ ràng và ném ngoại lệ khi có sai lệch, không phụ thuộc vào `assert`):

```powershell
python -c @"
import os, sys, json, hashlib
from pathlib import Path
from phishing.data.lot_ledger import LotManagementLedger

ledger_path = Path(os.environ.get('LEDGER_PATH', 'data/restricted/main_annotation_lot_management_ledger.json'))
proposal_path = Path(os.environ.get('PROPOSAL_PATH', 'data/restricted/main_batch1_staging_v4_2/proposal_block2_active_state_snapshot.json'))

print('=== [BƯỚC 1] TIỀN KIỂM MIGRATION BLOCK 2 ===')
print(f'Đường dẫn sổ cái: {ledger_path}')
print(f'Đường dẫn proposal: {proposal_path}')

# 1. Kiểm tra sự tồn tại của tệp
if not ledger_path.exists():
    raise FileNotFoundError(f'Không tìm thấy sổ cái tại: {ledger_path}')
if not proposal_path.exists():
    raise FileNotFoundError(f'Không tìm thấy proposal tại: {proposal_path}')

# 2. Kiểm tra kích thước và SHA-256 sổ cái 2 block ban đầu
raw_ledger = ledger_path.read_bytes()
h_ledger = hashlib.sha256(raw_ledger).hexdigest()
expected_ledger_hash = '11acdaf1806a80181006a5817520f21b2660c1a13ac983651e4d7129390a15c5'
if h_ledger != expected_ledger_hash:
    raise ValueError(f'SHA-256 sổ cái không khớp! Kỳ vọng: {expected_ledger_hash}, thực tế: {h_ledger}')
if len(raw_ledger) != 8253:
    raise ValueError(f'Dung lượng sổ cái không khớp! Kỳ vọng 8253 bytes, thực tế: {len(raw_ledger)}')

# 3. Nạp và kiểm tra tính hợp lệ của sổ cái 2 block hiện hành
ledger = LotManagementLedger(ledger_path)
if len(ledger.events) != 2:
    raise ValueError(f'Sổ cái phải có đúng 2 block lịch sử! Thực tế có: {len(ledger.events)}')

b0, b1 = ledger.events[0], ledger.events[1]
if b0.seq != 0 or b0.event_type != 'LEDGER_INITIALIZED' or b0.event_id != 'GENESIS':
    raise ValueError(f'Block 0 không đúng cấu trúc: seq={b0.seq}, event_type={b0.event_type}, event_id={b0.event_id}')
if b1.seq != 1 or b1.event_type != 'REGISTER_MAIN_BATCH1_SAMPLES':
    raise ValueError(f'Block 1 không đúng cấu trúc: seq={b1.seq}, event_type={b1.event_type}')

expected_b1_hash = '675440ba606a56a117494ac979f842d0881104639b7fa8dee771aa85680dd6ba'
if b1.event_hash != expected_b1_hash:
    raise ValueError(f'Mã băm Block 1 sai lệch! Kỳ vọng: {expected_b1_hash}, thực tế: {b1.event_hash}')

# 4. Kiểm tra proposal Block 2
raw_prop = proposal_path.read_bytes()
h_prop = hashlib.sha256(raw_prop).hexdigest()
expected_prop_hash = '643373177cbb8caac892abd7318358f631f4adf57f0f13595c8d7a171597881a'
if h_prop != expected_prop_hash:
    raise ValueError(f'SHA-256 proposal không khớp! Kỳ vọng: {expected_prop_hash}, thực tế: {h_prop}')
if len(raw_prop) != 8847:
    raise ValueError(f'Dung lượng proposal không khớp! Kỳ vọng 8847 bytes, thực tế: {len(raw_prop)}')

proposal_data = json.loads(raw_prop.decode('utf-8'))
prop_lot = proposal_data.get('lot_id')
prop_type = proposal_data.get('event_type')
if prop_lot != 'main_lot_batch_001':
    raise ValueError(f'Proposal không đúng lot_id: {prop_lot}')
if prop_type != 'MIGRATE_MAIN_BATCH1_SUPERSEDE_SALT_AND_LINEAGE_ENRICHMENT':
    raise ValueError(f'Proposal không đúng event_type: {prop_type}')

print('✅ TIỀN KIỂM ĐẠT 100%: Sổ cái 2 block và Proposal hoàn toàn hợp lệ.')
"@
```

---

## 2. QUY TRÌNH SAO LƯU NGUYÊN BYTE (BYTE-EXACT BACKUP)

Ngay sau khi tiền kiểm đạt, tạo bản sao lưu đóng băng trạng thái 2 block trước khi thực hiện bất kỳ thao tác ghi nào:

```powershell
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupPath = "$($env:LEDGER_PATH).bak.$timestamp"
Copy-Item $env:LEDGER_PATH $backupPath

# Xác nhận bản sao lưu khớp 100% hash gốc
$backupHash = (Get-FileHash $backupPath -Algorithm SHA256).Hash
if ($backupHash -ne "11ACDAF1806A80181006A5817520F21B2660C1A13AC983651E4D7129390A15C5") {
    Write-Error "LỖI: Bản sao lưu không khớp hash gốc! Dừng ngay lập tức."
    exit 1
}
Write-Host "✅ Đã sao lưu an toàn tại: $backupPath"
$env:BACKUP_PATH = $backupPath
```

---

## 3. LỆNH THỰC THI NỐI BLOCK 2 (EXECUTION COMMAND)

Thực hiện nối Block 2 vào sổ cái thông qua API chính thức của `LotManagementLedger`:

```powershell
python -c @"
import os, sys, json, hashlib
from pathlib import Path
from phishing.data.lot_ledger import LotManagementLedger

ledger_path = Path(os.environ.get('LEDGER_PATH', 'data/restricted/main_annotation_lot_management_ledger.json'))
proposal_path = Path(os.environ.get('PROPOSAL_PATH', 'data/restricted/main_batch1_staging_v4_2/proposal_block2_active_state_snapshot.json'))

print('=== [BƯỚC 2] THỰC THI NỐI BLOCK 2 ===')
proposal_data = json.loads(proposal_path.read_text(encoding='utf-8'))

ledger = LotManagementLedger(ledger_path)
if len(ledger.events) != 2:
    raise RuntimeError(f'Trạng thái sổ cái không hợp lệ (số events != 2, thực tế: {len(ledger.events)})')

ev2 = ledger.append_event(
    event_type=proposal_data['event_type'],
    actor=proposal_data['actor'],
    lot_id=proposal_data['lot_id'],
    status=proposal_data['status'],
    details=proposal_data['details']
)

print('✅ Đã nối Block 2 thành công:')
print(f'   Seq: {ev2.seq}')
print(f'   Event ID: {ev2.event_id}')
print(f'   Event Type: {ev2.event_type}')
print(f'   Prev Hash: {ev2.prev_hash}')
print(f'   Event Hash: {ev2.event_hash}')
print(f'   Timestamp: {ev2.timestamp}')

new_bytes = ledger_path.read_bytes()
new_hash = hashlib.sha256(new_bytes).hexdigest()
print(f'   Sổ cái mới trên đĩa: {len(new_bytes)} bytes | SHA-256: {new_hash}')
"@
```

---

## 4. HẬU KIỂM TOÀN DIỆN (POST-EXECUTION VERIFICATION)

Chạy script hậu kiểm độc lập nạp lại sổ cái từ đĩa, đối soát sequence, liên kết mật mã, tính toàn vẹn của 2 block lịch sử so với bản sao lưu, và cấu trúc payload của Block 2:

```powershell
python -c @"
import os, sys, json, hashlib
from pathlib import Path
from phishing.data.lot_ledger import LotManagementLedger

ledger_path = Path(os.environ.get('LEDGER_PATH', 'data/restricted/main_annotation_lot_management_ledger.json'))
proposal_path = Path(os.environ.get('PROPOSAL_PATH', 'data/restricted/main_batch1_staging_v4_2/proposal_block2_active_state_snapshot.json'))
backup_path = Path(os.environ['BACKUP_PATH']) if 'BACKUP_PATH' in os.environ else None

print('=== [BƯỚC 3] HẬU KIỂM TOÀN DIỆN SỔ CÁI 3 BLOCK ===')

# 1. Tải lại độc lập từ đĩa và xác thực sequence / cryptographic hash chain
ledger = LotManagementLedger(ledger_path)
if len(ledger.events) != 3:
    raise ValueError(f'Số lượng block không đúng! Kỳ vọng: 3, thực tế: {len(ledger.events)}')

b0, b1, b2 = ledger.events[0], ledger.events[1], ledger.events[2]

# 2. Kiểm tra tính toàn vẹn 2 sự kiện lịch sử so với bản sao lưu
if backup_path and backup_path.exists():
    backup_ledger = LotManagementLedger(backup_path)
    bk0, bk1 = backup_ledger.events[0], backup_ledger.events[1]
    for field in ['seq', 'event_id', 'timestamp', 'event_type', 'actor', 'lot_id', 'status', 'details', 'prev_hash', 'event_hash']:
        v0, v_bk0 = getattr(b0, field), getattr(bk0, field)
        if v0 != v_bk0:
            raise ValueError(f'Block 0 bị sai khác trường \"{field}\" so với bản sao lưu!')
        v1, v_bk1 = getattr(b1, field), getattr(bk1, field)
        if v1 != v_bk1:
            raise ValueError(f'Block 1 bị sai khác trường \"{field}\" so với bản sao lưu!')
    print('✅ Hai sự kiện lịch sử (Block 0 & Block 1) được bảo toàn nguyên vẹn so với bản sao lưu.')

# 3. Kiểm tra chi tiết Block 0 & Block 1
if b0.seq != 0 or b0.event_type != 'LEDGER_INITIALIZED' or b0.event_id != 'GENESIS':
    raise ValueError('Sai lệch cấu trúc Block 0')
if b1.seq != 1 or b1.event_type != 'REGISTER_MAIN_BATCH1_SAMPLES':
    raise ValueError('Sai lệch cấu trúc Block 1')
if b1.event_hash != '675440ba606a56a117494ac979f842d0881104639b7fa8dee771aa85680dd6ba':
    raise ValueError('Mã băm Block 1 bị sai lệch')

# 4. Kiểm tra chi tiết Block 2
proposal_data = json.loads(proposal_path.read_text(encoding='utf-8'))
if b2.seq != 2:
    raise ValueError(f'Block 2 seq sai: {b2.seq}')
if b2.prev_hash != b1.event_hash:
    raise ValueError('Block 2 prev_hash không trỏ tới Block 1!')
if b2.event_type != 'MIGRATE_MAIN_BATCH1_SUPERSEDE_SALT_AND_LINEAGE_ENRICHMENT':
    raise ValueError(f'Block 2 event_type sai: {b2.event_type}')
if b2.actor != 'Member C (Nguyễn Thắng)':
    raise ValueError(f'Block 2 actor sai: {b2.actor}')
if b2.lot_id != 'main_lot_batch_001':
    raise ValueError(f'Block 2 lot_id sai: {b2.lot_id}')
if b2.status != 'RESERVED':
    raise ValueError(f'Block 2 status sai: {b2.status}')
if b2.details != proposal_data['details']:
    raise ValueError('Block 2 details không khớp 100% với proposal!')

# 5. Kiểm tra Active Lot Details
active = ledger.get_active_lot_details('main_lot_batch_001')
if active is None:
    raise ValueError('Không lấy được active state cho main_lot_batch_001!')

prop_details = proposal_data['details']
# Kiểm tra danh sách và thứ tự A100 và B30
if active['allocated_candidate_ids'] != prop_details['allocated_candidate_ids']:
    raise ValueError('Danh sách/thứ tự 100 candidate IDs không khớp proposal!')
if active['b_subset_candidate_ids'] != prop_details['b_subset_candidate_ids']:
    raise ValueError('Danh sách/thứ tự 30 B subset IDs không khớp proposal!')
if active['b_indices_in_lot100'] != prop_details['b_indices_in_lot100']:
    raise ValueError('Danh sách/thứ tự 30 chỉ số B không khớp proposal!')

# Kiểm tra hai cam kết hạt giống độc lập
exp_cohort_commit = 'a16ce46f0a55db8ca8c6622b8d6dddcae134e1ca0ccef0104345f5369f8d0fc1'
exp_seed_commit = '4a5338c74bba9ae857fb9fa16a55cc54cae3c21cf779eb55f87996e6a5b7c4b6'

if active['cohort_seed_commitment'] != exp_cohort_commit:
    raise ValueError(f'cohort_seed_commitment sai lệch: {active[\"cohort_seed_commitment\"]} != {exp_cohort_commit}')
if active['seed_commitment'] != exp_seed_commit:
    raise ValueError(f'seed_commitment sai lệch: {active[\"seed_commitment\"]} != {exp_seed_commit}')
if active['cohort_seed_commitment'] == active['seed_commitment']:
    raise ValueError('cohort_seed_commitment không được trùng seed_commitment!')

new_bytes = ledger_path.read_bytes()
new_sha = hashlib.sha256(new_bytes).hexdigest()
print('✅ HẬU KIỂM 100% THÀNH CÔNG: Sổ cái 3 block hoàn toàn hợp lệ.')
print(f'   Dung lượng sổ cái 3 block: {len(new_bytes)} bytes | SHA-256: {new_sha}')
print(f'   Block 2 event_id: {b2.event_id}')
print(f'   Block 2 timestamp: {b2.timestamp}')
print(f'   Block 2 event_hash: {b2.event_hash}')
"@
```

> [!IMPORTANT]
> **Lưu ý về tính động của mã băm Block 2:**  
> API `LotManagementLedger.append_event` tự động sinh `timestamp` và `event_id` ngẫu nhiên/thời gian thực thi khi ghi nhận sự kiện mới, do đó `event_hash` của Block 2 trên sổ cái thật không nhất thiết phải trùng khớp mã băm của lần rehearsal trước. Tiêu chí nghiệm thu là sự kiện hợp lệ về mặt mật mã (`event_hash == compute_hash()`), `prev_hash` trỏ đúng vào Block 1 (`675440ba...`), và toàn bộ cấu trúc `details` khớp 100% snapshot của proposal.

---

## 5. KIỂM TRA TÍNH BẤT BIẾN KHI ĐỌC & BẰNG CHỨNG SAMPLER RERUN

### A. Kiểm tra tính bất biến khi đọc (Read-Only Invariance Check)
Thao tác truy vấn đọc trạng thái hoạt động của lô tuyệt đối không làm thay đổi hoặc phát sinh block mới trên sổ cái:

```powershell
python -c @"
import os, sys, hashlib
from pathlib import Path
from phishing.data.lot_ledger import LotManagementLedger

ledger_path = Path(os.environ.get('LEDGER_PATH', 'data/restricted/main_annotation_lot_management_ledger.json'))
h_before = hashlib.sha256(ledger_path.read_bytes()).hexdigest()

ledger = LotManagementLedger(ledger_path)
active = ledger.get_active_lot_details('main_lot_batch_001')
ledger_reloaded = LotManagementLedger(ledger_path)
h_after = hashlib.sha256(ledger_path.read_bytes()).hexdigest()

if len(ledger_reloaded.events) != 3:
    raise ValueError(f'Số block bị biến động khi đọc: {len(ledger_reloaded.events)}')
if h_before != h_after:
    raise ValueError('Tệp sổ cái bị ghi sửa khi thực hiện thao tác đọc!')
print('✅ Xác nhận tính bất biến khi đọc: 0 block phát sinh, 0 byte thay đổi.')
print(f'   SHA-256 sổ cái trước và sau khi đọc: {h_after}')
"@
```

### B. Bằng chứng kiểm tra Sampler Rerun (Rehearsal Verification Evidence)
Khi thực hiện chạy lại hàm `run_main_batch1_sampling` trên sổ cái 3 block với đầu vào là tập raw pool được hydrate đầy đủ từ nguồn Parquet đã khóa (`data/raw/phreshphish/data/train-001.parquet` theo `source_row`):
1. **Lũy nghiệm sổ cái (Idempotency)**: Sampler phát hiện lô `main_lot_batch_001` đã ở trạng thái `RESERVED` trong Block 2, tái sử dụng toàn bộ phân bổ đã cấp và **không ghi thêm bất kỳ block nào vào sổ cái** (số block giữ nguyên 3).
2. **Bảo toàn phân bổ**: Tập 100 blind IDs và 30 B subset IDs giữ nguyên thứ tự và giá trị, khớp 100% với các tệp view đã niêm phong (`blind_view_a.json` và `blind_view_b.json`).
3. **Phân bố nội dung văn bản thực tế**:
   - **View A**: Đúng **97/100 mẫu có text** và **3 mẫu rỗng nguyên bản** (do HTML gốc từ nguồn không có nội dung văn bản hiển thị sau khi trích xuất DOM an toàn). Tuyệt đối không quy kết thành "100 mẫu đều có text".
   - **View B**: Đúng **30/30 mẫu có text đầy đủ**.
4. **Bằng chứng kiểm chứng**: Toàn bộ quy trình rehearsal sampler này đã được thực thi và xác thực độc lập trong kịch bản chuẩn bị `scripts/data/prepare_main_batch1_successor_v4_2.py`, lưu trữ tại gói `MAIN_BATCH1_RESTRICTED_DATA_PACK_FOR_LEAD_D_V4_2_STAGING.zip`. Không dùng sổ cái thật hoặc ghi đè các view đã niêm phong để chạy phép kiểm này.

---

## 6. QUY TRÌNH XỬ LÝ SỰ CỐ & HOÀN NGUYÊN CÓ PHẠM VI (FAIL-CLOSED & SCOPED ROLLBACK PROTOCOL)

Quy trình xử lý sự cố phân định rõ ràng giữa hai pha và tuyệt đối không áp dụng lệnh sao chép đè chung chung:

### Pha 1: Lỗi phát sinh TRƯỚC KHI GHI (Pre-write Error)
- **Dấu hiệu**: Bất kỳ bước nào trong Mục 1 (Tiền kiểm) hoặc Mục 2 (Sao lưu) ném ngoại lệ hoặc không khớp hash (`11acdaf1...`).
- **Quy tắc ứng xử**:
  1. **DỪNG NGAY LẬP TỨC**.
  2. **GIỮ NGUYÊN SỔ CÁI HIỆN TẠI TRÊN ĐĨA**. Tuyệt đối **KHÔNG** tự ý sao chép đè bản sao lưu cũ lên sổ cái, vì trạng thái khác biệt có thể phản ánh một thay đổi hợp lệ ngoài phạm vi runbook.
  3. Ghi nhận log chi tiết thông báo lỗi và báo cáo cho Lead D.

### Pha 2: Lỗi phát sinh SAU KHI ĐÃ GHI (Post-write Error)
- **Dấu hiệu**: Lệnh nối Block 2 hoàn tất nhưng script Mục 4 (Hậu kiểm) thất bại (số lượng block khác 3, liên kết hash bị đứt đoạn, trường dữ liệu không khớp snapshot, hoặc vi phạm cam kết hạt giống).
- **Quy tắc ứng xử**:
  1. **DỪNG TOÀN BỘ CÁC THAO TÁC TIẾP THEO**.
  2. **BẢO LƯU NGUYÊN TRẠNG TỆP SỰ CỐ ĐỂ PHỤC VỤ ĐIỀU TRA**: Lưu nguyên byte trạng thái sổ cái lỗi sang tệp lưu vết sự cố:
     ```powershell
     $incidentTimestamp = Get-Date -Format "yyyyMMdd_HHmmss"
     $incidentPath = "$($env:LEDGER_PATH).incident.$incidentTimestamp"
     Copy-Item $env:LEDGER_PATH $incidentPath
     $incidentHash = (Get-FileHash $incidentPath -Algorithm SHA256).Hash
     Write-Host "⚠️ Đã lưu nguyên trạng tệp sự cố tại: $incidentPath (SHA-256: $incidentHash)"
     ```
  3. **CHỈ HOÀN NGUYÊN KHI CÓ QUYẾT ĐỊNH CỦA LEAD D**: Sau khi Lead D xem xét và phê duyệt hoàn nguyên từ bản sao lưu đã kiểm định ở Mục 2:
     ```powershell
     Copy-Item $env:BACKUP_PATH $env:LEDGER_PATH
     
     # Kiểm tra lại byte và hash sau hoàn nguyên
     $restoredHash = (Get-FileHash $env:LEDGER_PATH -Algorithm SHA256).Hash
     if ($restoredHash -ne "11ACDAF1806A80181006A5817520F21B2660C1A13AC983651E4D7129390A15C5") {
         Write-Error "NGHIÊM TRỌNG: Hoàn nguyên không phục hồi đúng hash ban đầu!"
         exit 1
     }
     Write-Host "✅ Hoàn nguyên thành công: Sổ cái trở lại nguyên trạng 2 block ban đầu."
     ```
  4. Lập biên bản audit trail đầy đủ ghi nhận nguyên nhân lỗi, mã băm tệp sự cố và xác nhận trạng thái hoàn nguyên. Không âm thầm xóa một sự kiện hợp lệ hoặc làm mất dấu vết lỗi.
