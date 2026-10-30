# BÁO CÁO KỸ THUẬT TIỀN PHÂN XỬ & ĐỐI SOÁT ĐỘC LẬP
## Calibration Clean Runway A (Đợt C) — Pass 1 Parallel Annotation

> **Dự án**: Nghiên cứu phát hiện website phishing kết hợp URL và nội dung trang (NCKH_2)  
> **Giai đoạn**: Tiền phân xử (Pre-adjudication) — Pass 1 Calibration Runway A  
> **Chỉ đạo thực hiện**: Lead D (Anh Tuấn)  
> **Đơn vị lập hồ sơ**: Thành viên C (Data Pipeline & Blind View)  
> **Cơ chế thực thi**: Duo Mode (Antigravity & DeepSeek Bridge)  
> **Ngày lập**: 31/10/2026  
> **Trạng thái**: Khóa đối soát kỹ thuật (Locked Technical Audit)

---

## 1. TỔNG QUAN VÀ TÍNH CHÍNH THỨC CỦA ĐỐI SOÁT

Thực hiện chỉ đạo đối soát của Lead D (Anh Tuấn) đối với dữ liệu gán nhãn độc lập Pass 1 thuộc tập **Calibration Clean Runway A (Đợt C)**, Thành viên C đã hoàn tất kiểm toán mã băm mật mã học (cryptographic checksums), tính toán độc lập các chỉ số thống kê thỏa thuận liên đánh giá viên (Inter-Rater Agreement), và lập hồ sơ kỹ thuật phục vụ phiên phân xử trung lập Pass 2.

### 1.1. Bảng xác thực tính toàn vẹn gói dữ liệu và mã băm

| Hạng mục artifact | Đường dẫn quy ước | Số lượng | SHA-256 Checksum | Trạng thái |
| :--- | :--- | :---: | :--- | :--- |
| **Blind View đầu vào** | `data/annotations/clean_calibration_blind_view_24.json` | 24 mẫu | `0164b2a5499c10c824f7e559c9a351c958adcfe627648ac537179dfe4dbf2b6b` | Đã khóa |
| **Codebook v1.1** | `docs/CODEBOOK_V1_1.md` | — | `e30871b87911992110e77ad0dcca8bbf64b916086f496555599e43730af0adbd` | Đã khóa |
| **Manifest Runway A** | `configs/calibration_clean_a_manifest.json` | — | `9d94dd3e33134131047600d9297f3058b3049a946863cac24fe34b7fd110a32b` | Đã khóa |
| **Từ điển tổ chức v1** | `configs/dictionary_v1.json` | 14 orgs | `7aa83b68fdb4bb288460c00523e38e0779e8cbeb81ae879e7a5d27e771fcd3b3` | Đã khóa |
| **File gán nhãn A** | `data/annotations/A/clean_calibration_pass1.jsonl` | 24 mẫu | `1c60d10ac4056679d8aafe2b13dcf4f00ffc0f332d34f5413f4b922164eac7f` | Chính thức Pass 1 |
| **File gán nhãn B** | `data/annotations/B/clean_calibration_pass1.jsonl` | 24 mẫu | `6069f61c5550f39e2aa39158ec0d3f183c01198b5b0d6e0479ab792bd15cc3f0` | Chính thức Pass 1 |

*Ghi chú định lượng thời gian*:
- **Đánh giá viên A (Trần Hồng Khải)**: 24/24 ID hoàn thành, tổng thời gian thao tác ghi nhận: **9.123,72 giây** (trung bình ~380,16 giây/mẫu).
- **Đánh giá viên B (Phùng Tấn Minh)**: 24/24 ID hoàn thành, tổng thời gian thao tác ghi nhận: **6.008,72 giây** (trung bình ~250,36 giây/mẫu).

---

## 2. KẾT QUẢ ĐỐI SOÁT ĐỘC LẬP CHỈ SỐ THỐNG KÊ (PRE-ADJUDICATION)

Thành viên C đã tiến hành tính toán độc lập từ các tệp nhãn gốc được khóa. Kết quả xác nhận khớp 100% với số liệu đối soát sơ bộ của Lead D.

### 2.1. Các chỉ số đồng thuận liên đánh giá viên

- **Tổng số mẫu hiệu chuẩn**: $N = 24$.
- **Số mẫu đồng thuận tuyệt đối**: $21 / 24$.
- **Tỷ lệ đồng thuận quan sát ($P_o$)**:
  $$P_o = \frac{21}{24} = 0{,}875 \quad (87{,}50\%)$$
- **Tỷ lệ đồng thuận kỳ vọng ngẫu nhiên ($P_e$)**:
  $$P_e = \frac{14 \times 11 + 10 \times 11 + 0 \times 2}{24 \times 24} = \frac{154 + 110 + 0}{576} = \frac{264}{576} = \frac{11}{24} \approx 0{,}458333$$
- **Hệ số Cohen’s Kappa ($\kappa$)**:
  $$\kappa = \frac{P_o - P_e}{1 - P_e} = \frac{\frac{21}{24} - \frac{11}{24}}{1 - \frac{11}{24}} = \frac{\frac{10}{24}}{\frac{13}{24}} = \frac{10}{13} \approx 0{,}769230769... \approx 0{,}769231$$

> [!NOTE]
> Theo thang phân loại chuẩn của Landis & Koch (1977), hệ số $\kappa = 0{,}769231$ nằm trong khoảng $[0{,}61 - 0{,}80]$, tương ứng mức **Substantial Agreement** (Thỏa thuận rất cao). Đây là mức độ tin cậy vượt trội trong gán nhãn độc lập song song trước khi bước vào phiên phân xử.

### 2.2. Ma trận nhầm lẫn 3x3 trước phân xử (Confusion Matrix)

Ma trận phản ánh sự phân bố phân loại nhãn lớp giữa Đánh giá viên A (dòng) và Đánh giá viên B (cột):

| Đánh giá viên A \ B | Benign (B) | Phishing (B) | Insufficient Evidence (B) | Tổng dòng (A) |
| :--- | :---: | :---: | :---: | :---: |
| **Benign (A)** | **11** | 1 (`SMP-024`) | 2 (`SMP-012`, `SMP-014`) | **14** |
| **Phishing (A)** | 0 | **10** | 0 | **10** |
| **Insufficient Evidence (A)** | 0 | 0 | **0** | **0** |
| **Tổng cột (B)** | **11** | **11** | **2** | **24** |

---

## 3. KIỂM TOÁN SỰ CỐ THAO TÁC SMP-001 (ĐÁNH GIÁ VIÊN A)

### 3.1. Bối cảnh và Xác nhận của Lead D
Trong quá trình gán nhãn mẫu `SMP-001`, giao diện CLI gặp hiện tượng lag hiển thị dẫn đến việc ghi nhận trạng thái chưa đúng với nhận định ban đầu của Đánh giá viên A.
Lead D xác nhận:
1. Bản trước sửa là lỗi thao tác do lag giao diện, không phải là sự thay đổi quyết định gán nhãn chuyên môn.
2. Việc phê duyệt sửa đổi được thực hiện khi A hoàn toàn chưa tiếp cận nhãn hay dữ liệu gán của B (bảo đảm nguyên tắc mù song song tuyệt đối).

### 3.2. Chính sách quản trị dữ liệu áp dụng
- **Tệp chính thức**: Tệp gán nhãn Pass 1 chính thức của Đánh giá viên A có mã băm SHA-256 là `1c60d10ac4056679d8aafe2b13dcf4f00ffc0f332d34f5413f4b922164eac7f`. Toàn bộ các phép tính thống kê và nghị trình phân xử sử dụng tệp này.
- **Lưu trữ kiểm toán**: Tệp nháp tiền chỉnh sửa được lưu trữ độc lập tại phân vùng hạn chế ngoài Git nhằm mục đích phục vụ hậu kiểm (audit trail).
- **Quy tắc bất biến**:
  - Không tính Kappa trên bản lỗi.
  - Không yêu cầu Đánh giá viên A gán lại toàn bộ tập dữ liệu.
  - Tuyệt đối không chỉnh sửa tệp đã khóa `1c60d10a...`.

---

## 4. BÁO CÁO KIỂM SOÁT CHẤT LƯỢNG TỔ CHỨC (ORGANIZATION QC AUDIT)

### 4.1. Hiện tượng ghi nhận
Qua rà soát đối chiếu trường dữ liệu, tệp Pass 1 của Đánh giá viên A ghi nhận **12 trường hợp** xuất hiện mâu thuẫn hình thức:
- Giá trị trường: `primary_org_status = "identified"`
- Giá trị trường: `primary_org = "unknown"`
- Danh sách 12 mã mẫu vi phạm: `SMP-001`, `SMP-002`, `SMP-003`, `SMP-006`, `SMP-010`, `SMP-011`, `SMP-014`, `SMP-017`, `SMP-019`, `SMP-022`, `SMP-023`, `SMP-024`.

### 4.2. Đánh giá theo Codebook v1.1
Theo quy định tại **Mục 3 và Mục 4 của Codebook v1.1**:
- Khi đánh giá viên xác định được tổ chức/thương hiệu bị nhắm tới hoặc tổ chức sở hữu hợp pháp (`primary_org_status = "identified"`), trường `primary_org` bắt buộc phải là một chuỗi định danh tổ chức cụ thể (nằm trong 14 tổ chức chuẩn hóa hoặc thương hiệu ngoài danh mục), tuyệt đối không được để `"unknown"`.
- Do đó, 12 ca trên là mâu thuẫn hình thức cần đưa vào quy trình Kiểm soát Chất lượng (QC).

### 4.3. Quyết định kỹ thuật của Thành viên C
1. **Không công bố Kappa tổ chức như kết luận chính thức**: Do 12 ca gặp lỗi nhập liệu hình thức trường `primary_org`, việc tính Kappa tổ chức trực tiếp trên dữ liệu thô sẽ bóp méo chất lượng thực nghiệm thực tế.
2. **Bảo toàn nguyên bản dữ liệu**: Giữ nguyên vẹn 100% bản ghi Pass 1 của Đánh giá viên A; không tự ý sửa đổi tệp Pass 1 thô.
3. **Phân luồng xử lý**: Đưa toàn bộ 12 ca này vào **Hồ sơ phân xử riêng** để hội đồng phân xử (Lead D, A, B) chuẩn hóa nhãn tổ chức trong phiên Pass 2.

---

## 5. NGHỊ TRÌNH TRUNG LẬP PHÂN XỬ PASS 2 (NEUTRAL ADJUDICATION AGENDA)

Phiên phân xử Pass 2 được chủ trì bởi Lead D (Anh Tuấn) với sự tham gia của Đánh giá viên A và B. Thành viên C đóng vai trò cung cấp hồ sơ trung lập mù.

### 5.1. Nguyên tắc trung lập cốt lõi
1. **Zero External Metadata**: Tuyệt đối không đưa nhãn nguồn (ground truth), bộ định vị parquet (file, offset), bộ so khớp thương hiệu tự động (rule matchers), hay điểm số mô hình máy học (model scores) vào phòng họp phân xử.
2. **Bộ tài liệu duy nhất được cấp phép**:
   - `clean_calibration_blind_view_24.json` (SHA-256: `0164b2a5...`)
   - `docs/CODEBOOK_V1_1.md` (SHA-256: `e30871b8...`)
   - Bằng chứng và ghi chú quan sát (`evidence_note`) nguyên văn đã khóa của A và B.
3. **Phân tách ranh giới dữ liệu**: Hồ sơ chi tiết (kèm nội dung DOM/URL) được lưu trữ tại `data/restricted/clean_calibration_adjudication_dossier_restricted.json`. Bản báo cáo công khai trên Git tuyệt đối không tiết lộ URL thô hay thông tin nhạy cảm.

### 5.2. Nội dung phiên họp phân xử Pass 2

#### Phần 1: Phân xử Nhãn lớp cho 3 ca bất đồng (Class Label Adjudication)

| Mã nghị trình | Mã mẫu | Nhãn A | Nhãn B | Trọng tâm thảo luận đối chiếu Codebook v1.1 |
| :--- | :--- | :---: | :---: | :--- |
| **ADJ-LABEL-01** | `SMP-012` | `benign` | `insufficient_evidence` | **Quy tắc R-A05 vs R-A02**: Trang hiển thị thông báo Exception kỹ thuật của ứng dụng ASP.NET nội bộ, văn bản thưa thớt, không có form nhập liệu. Xem xét bản chất là lỗi hệ thống an toàn (`benign`) hay thiếu dữ liệu quan sát hành vi (`insufficient_evidence`). |
| **ADJ-LABEL-02** | `SMP-014` | `benign` | `insufficient_evidence` | **Quy tắc R-A05 vs Nhận diện dịch vụ**: Trang đăng nhập khảo sát tiếng Nhật (`ログイン \| Ipsos iSay`). DOM thưa thớt không trích xuất được form tĩnh trên view nhưng tiêu đề xác thực dịch vụ. Phân định ranh giới giữa snapshot lỗi hiển thị và trang xác thực thực tế. |
| **ADJ-LABEL-03** | `SMP-024` | `benign` | `phishing` | **Quy tắc R-P01 (Mạo danh thương hiệu trên hạ tầng rủi ro)**: Nội dung sao chép dịch vụ truyền thông/viễn thông Xfinity nhưng lưu trữ trên tên miền Dynamic DNS (`dpdns.org`). Đánh giá hành vi mồi nhử lừa đảo tài khoản người dùng. |

#### Phần 2: Chuẩn hóa Nhãn tổ chức cho 12 ca QC (Organization Standardization)

Hội đồng phân xử sẽ rà soát ghi chú bằng chứng (`evidence_note`) của A và nhận diện tổ chức của B để chuẩn hóa mã định danh tổ chức thống nhất:
- `SMP-001`, `SMP-002`, `SMP-003`, `SMP-006`, `SMP-010`, `SMP-011`, `SMP-014`, `SMP-017`, `SMP-019`, `SMP-022`, `SMP-023`, `SMP-024`.
- Đối chiếu với từ điển 14 tổ chức mục tiêu (`configs/dictionary_v1.json`) hoặc gán mã thương hiệu hợp lệ ngoài danh mục (non-catalog organization).

---

## 6. QUẢN TRỊ BẢO MẬT VÀ KHÓA CHỐNG RÒ RỈ DỮ LIỆU

Nhằm duy trì tính nghiêm cẩn hàn lâm (Academic Research Skills) và kỷ luật Ponytail:
1. **Khóa huấn luyện**: `training_blocked = true`. Tuyệt đối không đưa tập hiệu chuẩn hay dữ liệu phân xử vào bất kỳ quá trình huấn luyện mô hình nào.
2. **Cô lập tập kiểm thử chính thức**: `official_test_used = false`. Toàn bộ dữ liệu Official Test được bảo vệ biệt lập 100%.
3. **Mã băm các artifact hạn chế**:
   - `data/restricted/clean_calibration_adjudication_dossier_restricted.json`: `e2817074b3a7de14b51aa933761a7297be957ec8f06836156a21ca099837e4aa`
   - `data/source_audit/clean_calibration_pre_adjudication_audit.json`: `3e7dba04373a2a92c7bd8cf76c2357c0a1b207248fba3e6da68b9bb3d11076a9`
   - `data/restricted/intake_pass1_B_6069f61c.jsonl`: `6069f61c5550f39e2aa39158ec0d3f183c01198b5b0d6e0479ab792bd15cc3f0`

---
*Báo cáo được lập bởi Thành viên C. Đã sẵn sàng mở phiên phân xử trung lập Pass 2 theo quyết định của Lead D.*
