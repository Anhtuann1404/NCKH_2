# RUNBOOK HƯỚNG DẪN THỰC THI DI TRÚ BLOCK 2 VÀO SỔ CÁI QUẢN LÝ LÔ
## DÀNH RIÊNG CHO LEAD D (ANH TUẤN) THẨM DUYỆT VÀ THỰC THI ĐỘC LẬP
**Dự án:** NCKH_2 — Phát hiện website phishing mạo danh tổ chức bằng học máy kết hợp URL và nội dung trang  
**Mục tiêu:** Cung cấp công cụ và quy trình thủ tục từng bước có kiểm soát chặt chẽ để Lead D thẩm định và thực thi áp dụng Proposal Block 2 Snapshot từ Gói V4.2 vào Sổ cái Quản lý Lô (`main_annotation_lot_management_ledger.json`).  
**Tình trạng pháp lý:** **DỰ THẢO PHƯƠNG ÁN (RUNBOOK PROPOSAL ONLY)** — Đây là tài liệu quy trình kỹ thuật, **CHƯA PHẢI QUYẾT ĐỊNH THỰC THI TRÊN SỔ CÁI THẬT**. Sổ cái thật trên đĩa tiếp tục được giữ nguyên trạng 2 block lịch sử (SHA-256: `11acdaf1...`) cho đến khi Lead D ra quyết định chính thức.

> [!NOTE]
> **Đặc tính kỹ thuật & Giới hạn khóa đồng thời:**  
> 1. Mã nguồn thực thi được chuyển hoàn toàn vào công cụ chuyên dụng [`scripts/data/execute_block2_migration.py`](file:///d:/nguyen%20thang/NCKH/NCKH_2/scripts/data/execute_block2_migration.py) để loại bỏ rủi ro escape nháy trong PowerShell và đảm bảo cú pháp Python chuẩn xác tuyệt đối.  
> 2. Quá trình ghi tệp của `LotManagementLedger` sử dụng tệp tạm và hoán đổi nguyên tử (`os.replace`). Tuy nhiên, toàn bộ chuỗi quy trình (Tiền kiểm $\rightarrow$ Sao lưu $\rightarrow$ Nối Block 2 $\rightarrow$ Hậu kiểm $\rightarrow$ Phục hồi) là quy trình thủ tục tuần tự nhiều bước, **không cấu thành một giao dịch ACID phân tán duy nhất**.  
> 3. **Yêu cầu đơn tiến trình (Single-Process Requirement):** Bắt buộc chỉ có duy nhất một tiến trình thực hiện thao tác trên sổ cái trong suốt cửa sổ thực thi. Các điều kiện kiểm tra trong runbook không đóng vai trò cơ chế khóa phân tán tự động.

---

## 1. THIẾT LẬP MÔI TRƯỜNG & TIỀN KIỂM (PRE-CHECK)

### A. Thiết lập biến môi trường thao tác
Trong cửa sổ PowerShell làm việc tại thư mục gốc repository:

```powershell
$env:PYTHONPATH = "src;."
$env:LEDGER_PATH = "data/restricted/main_annotation_lot_management_ledger.json"
$env:PROPOSAL_PATH = "data/restricted/main_batch1_staging_v4_2/proposal_block2_active_state_snapshot.json"
```

### B. Chạy lệnh tiền kiểm độc lập
Lệnh gọi công cụ `execute_block2_migration.py` kiểm tra toàn bộ điều kiện tiên quyết:

```powershell
python scripts/data/execute_block2_migration.py precheck
```

**Cơ chế kiểm soát tại bước Tiền kiểm:**
- Xác thực sự tồn tại của sổ cái và proposal snapshot; ném lỗi tường minh nếu thiếu tệp.
- Sổ cái hiện hành phải đúng **8.253 bytes** và SHA-256: `11acdaf1806a80181006a5817520f21b2660c1a13ac983651e4d7129390a15c5`.
- Sổ cái nạp qua `LotManagementLedger` phải có đúng **2 sự kiện lịch sử**:
  * Block 0: `event_id="GENESIS"`, `event_type="LEDGER_INITIALIZED"`, `event_hash="239f5263bf7dcd05dab13b7bc6214b631d90cc42164662ea29b4619cae87c3fd"`.
  * Block 1: `event_id="f3d58599b084b9b8"`, `event_type="REGISTER_MAIN_BATCH1_SAMPLES"`, `event_hash="675440ba606a56a117494ac979f842d0881104639b7fa8dee771aa85680dd6ba"`.
- Proposal snapshot phải đúng **8.847 bytes** và SHA-256: `643373177cbb8caac892abd7318358f631f4adf57f0f13595c8d7a171597881a`.
- Proposal phải đúng `lot_id="main_lot_batch_001"`, `event_type="MIGRATE_MAIN_BATCH1_SUPERSEDE_SALT_AND_LINEAGE_ENRICHMENT"`, `actor="Member C (Nguyễn Thắng)"`, `status="RESERVED"`, và cấu trúc details hợp lệ.

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

## 3. LỆNH THỰC THI NỐI BLOCK 2 (EXECUTION COMMAND - APPLY)

Thực hiện nối Block 2 vào sổ cái thông qua lệnh `apply`:

```powershell
python scripts/data/execute_block2_migration.py apply
```

**Cơ chế tự kiểm tra lại đầu vào ngay trong bước ghi:**
Công cụ `apply` tự động tái xác thực toàn bộ các điều kiện tiên quyết **ngay trước khi gọi `append_event`**:
1. Bắt buộc đường dẫn sổ cái, proposal và backup đã được cung cấp và các tệp phải tồn tại trên đĩa; tuyệt đối không tự khởi tạo sổ cái mới nếu thiếu tệp.
2. Cả sổ cái và bản sao lưu đều phải khớp đúng dung lượng 8.253 bytes và SHA-256 `11acdaf1...`.
3. Proposal phải khớp đúng dung lượng 8.847 bytes và SHA-256 `64337317...`.
4. Sổ cái phải có đúng 2 block lịch sử hợp lệ với hash Block 1 là `675440ba...`.
5. Proposal phải đúng lô, loại sự kiện, tác nhân và trạng thái đã kiểm định.
6. **Nguyên tắc dừng an toàn (Fail-Closed):** Nếu sai bất kỳ điều kiện nào, công cụ dừng ngay lập tức trước khi ghi, không can thiệp tệp và không tự động sao chép đè bản sao lưu.

---

## 4. HẬU KIỂM TOÀN DIỆN VÀ ĐỐI SOÁT SAO LƯU (POST-VERIFICATION)

Chạy lệnh hậu kiểm độc lập nạp lại sổ cái từ đĩa, bắt buộc có bản sao lưu hợp lệ để đối soát:

```powershell
python scripts/data/execute_block2_migration.py verify
```

**Cơ chế kiểm soát bắt buộc tại bước Hậu kiểm:**
1. **Bắt buộc có bản sao lưu hợp lệ:** Nếu thiếu `BACKUP_PATH`, tệp sao lưu không tồn tại, sai kích thước, sai hash hoặc không tải được thành 2 sự kiện hợp lệ $\rightarrow$ **DỪNG NGAY LẬP TỨC**. Tuyệt đối không in kết luận hậu kiểm đạt khi chưa hoàn thành đối soát sao lưu.
2. **Đối soát 100% hai sự kiện lịch sử:** Đối chiếu toàn bộ 10 trường (`seq`, `event_id`, `timestamp`, `event_type`, `actor`, `lot_id`, `status`, `details`, `prev_hash`, `event_hash`) của Block 0 và Block 1 so với bản sao lưu ban đầu; mọi trường phải trùng khớp hoàn toàn.
3. **Kiểm tra Block 2:**
   - `seq == 2`.
   - `prev_hash` trỏ đúng vào Block 1: `675440ba606a56a117494ac979f842d0881104639b7fa8dee771aa85680dd6ba`.
   - `event_type == "MIGRATE_MAIN_BATCH1_SUPERSEDE_SALT_AND_LINEAGE_ENRICHMENT"`.
   - `actor == "Member C (Nguyễn Thắng)"`.
   - `lot_id == "main_lot_batch_001"`.
   - `status == "RESERVED"`.
   - `details` khớp 100% proposal snapshot.
4. **Kiểm tra Active Lot Details:**
   - Khớp danh sách và thứ tự 100 candidate IDs.
   - Khớp danh sách và thứ tự 30 B subset IDs.
   - Khớp danh sách và thứ tự 30 chỉ số B trong lot 100.
   - `cohort_seed_commitment`: `a16ce46f0a55db8ca8c6622b8d6dddcae134e1ca0ccef0104345f5369f8d0fc1`.
   - `seed_commitment`: `4a5338c74bba9ae857fb9fa16a55cc54cae3c21cf779eb55f87996e6a5b7c4b6`.
   - Hai cam kết mật mã phải hoàn toàn độc lập (`cohort_seed_commitment != seed_commitment`).

> [!IMPORTANT]
> **Lưu ý về tính động của mã băm Block 2:**  
> API `append_event` tự động sinh `timestamp` và `event_id` thời gian thực khi nối sự kiện mới, do đó `event_hash` của Block 2 trên sổ cái thật không nhất thiết phải trùng khớp mã băm của lần rehearsal trước. Tiêu chuẩn nghiệm thu là sự kiện hợp lệ về mặt mật mã (`event_hash == compute_hash()`), `prev_hash` trỏ đúng vào Block 1 (`675440ba...`), và toàn bộ cấu trúc `details` khớp 100% snapshot proposal.

---

## 5. KIỂM TRA TÍNH BẤT BIẾN KHI ĐỌC & BẰNG CHỨNG SAMPLER RERUN

### A. Kiểm tra tính bất biến khi đọc (Read-Only Invariance Check)
Thao tác truy vấn đọc trạng thái hoạt động của lô tuyệt đối không làm thay đổi hoặc phát sinh block mới trên sổ cái:

```powershell
python scripts/data/execute_block2_migration.py invariance-check
```
*Kết quả kỳ vọng: 0 block phát sinh, 0 byte thay đổi, SHA-256 sổ cái trước và sau khi đọc hoàn toàn trùng khớp.*

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
- **Dấu hiệu**: Bất kỳ bước nào trong Mục 1 (Tiền kiểm), Mục 2 (Sao lưu) hoặc các bước tự kiểm trước ghi của Mục 3 (Apply) ném ngoại lệ hoặc không khớp hash (`11acdaf1...`).
- **Quy tắc ứng xử**:
  1. **DỪNG NGAY LẬP TỨC**.
  2. **GIỮ NGUYÊN SỔ CÁI HIỆN TẠI TRÊN ĐĨA**. Tuyệt đối **KHÔNG** tự ý sao chép đè bản sao lưu cũ lên sổ cái, vì trạng thái khác biệt có thể phản ánh một thay đổi hợp lệ ngoài phạm vi runbook.
  3. Ghi nhận log chi tiết thông báo lỗi và báo cáo cho Lead D.

### Pha 2: Lỗi phát sinh SAU KHI ĐÃ GHI (Post-write Error)
- **Dấu hiệu**: Lệnh nối Block 2 hoàn tất nhưng lệnh Mục 4 (Hậu kiểm) thất bại (số lượng block khác 3, liên kết hash bị đứt đoạn, trường dữ liệu không khớp snapshot, hoặc vi phạm cam kết hạt giống).
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
