# BÁO CÁO KỸ THUẬT TIỀN PHÂN XỬ & ĐỐI SOÁT ĐỘC LẬP
## Calibration Clean Runway A (Đợt C) — Pass 1 Parallel Annotation

> **Dự án**: Nghiên cứu phát hiện website phishing kết hợp URL và nội dung trang (NCKH_2)  
> **Giai đoạn**: Tiền phân xử (Pre-adjudication) — Pass 1 Calibration Runway A  
> **Chỉ đạo thực hiện & Chủ trì phân xử**: Lead D (Anh Tuấn)  
> **Đơn vị lập hồ sơ**: Thành viên C (Data Pipeline & Blind View)  
> **Cơ chế phối hợp**: Duo Mode (Antigravity & DeepSeek Bridge)  
> **Phiên bản hồ sơ**: 1.5.0  
> **Ngày cập nhật**: 31/10/2026  
> **Trạng thái quản trị**: Lead D đã chính thức DUYỆT NGHỊ TRÌNH; sẵn sàng mở phiên phân xử Pass 2 (`ready_for_adjudication_pass2 = true`)

---

## 1. TỔNG QUAN VÀ TÍNH CHÍNH THỨC CỦA ĐỐI SOÁT

Thực hiện chỉ đạo đối soát của Lead D (Anh Tuấn) đối với dữ liệu gán nhãn độc lập Pass 1 thuộc tập **Calibration Clean Runway A (Đợt C)**, Thành viên C đã hoàn tất kiểm toán mã băm mật mã học (cryptographic checksums), tính toán độc lập các chỉ số thống kê thỏa thuận liên đánh giá viên (Inter-Rater Agreement), và lập hồ sơ kỹ thuật phục vụ phiên phân xử trung lập Pass 2.

### 1.1. Bảng xác thực tính toàn vẹn gói dữ liệu và mã băm

| Hạng mục artifact | Đường dẫn quy ước | Quy mô | SHA-256 Checksum | Trạng thái |
| :--- | :--- | :---: | :--- | :--- |
| **Blind View đầu vào** | `data/annotations/clean_calibration_blind_view_24.json` | 24 mẫu | `0164b2a5499c10c824f7e559c9a351c958adcfe627648ac537179dfe4dbf2b6b` | Đã khóa |
| **Codebook v1.1** | `docs/CODEBOOK_V1_1.md` | — | `e30871b87911992110e77ad0dcca8bbf64b916086f496555599e43730af0adbd` | Đã khóa |
| **Manifest Runway A** | `configs/calibration_clean_a_manifest.json` | — | `9d94dd3e33134131047600d9297f3058b3049a946863cac24fe34b7fd110a32b` | Đã khóa |
| **Từ điển tổ chức v1** | `configs/dictionary_v1.json` | 14 orgs | `7aa83b68fdb4bb288460c00523e38e0779e8cbeb81ae879e7a5d27e771fcd3b3` | Đã khóa |
| **File gán nhãn A** | `data/annotations/A/clean_calibration_pass1.jsonl` | 24 mẫu | `1c60d10ac4056679d8aafe2b13dcf4f00ffc0f332d34f5413f4b922164eac7f1` | Chính thức Pass 1 |
| **File gán nhãn B** | `data/annotations/B/clean_calibration_pass1.jsonl` | 24 mẫu | `6069f61c5550f39e2aa39158ec0d3f183c01198b5b0d6e0479ab792bd15cc3f0` | Chính thức Pass 1 |

*Ghi chú định lượng thời gian*:
- **Đánh giá viên A (Trần Hồng Khải)**: 24/24 ID hoàn thành, tổng thời gian thao tác ghi nhận: **9.123,72 giây** (trung bình ~380,16 giây/mẫu). File lưu trữ an toàn tại `data/annotations/A/clean_calibration_pass1.jsonl`.
- **Đánh giá viên B (Phùng Tấn Minh)**: 24/24 ID hoàn thành, tổng thời gian thao tác ghi nhận: **6.008,72 giây** (trung bình ~250,36 giây/mẫu). File lưu trữ an toàn tại `data/annotations/B/clean_calibration_pass1.jsonl`.

---

## 2. KẾT QUẢ ĐỐI SOÁT ĐỘC LẬP CHỈ SỐ THỐNG KÊ (PRE-ADJUDICATION)

Thành viên C đã tiến hành tính toán độc lập từ hai tệp nhãn gốc được khóa. Kết quả xác nhận khớp 100% với số liệu đối soát sơ bộ của Lead D.

### 2.1. Các chỉ số đồng thuận liên đánh giá viên

- **Tổng số mẫu hiệu chuẩn**: $N = 24$.
- **Số mẫu đồng thuận tuyệt đối**: $21 / 24$.
- **Tỷ lệ đồng thuận quan sát ($P_o$)**:
  $$P_o = \frac{21}{24} = 0{,}875 \quad (87{,}50\%)$$
- **Tỷ lệ đồng thuận kỳ vọng ngẫu nhiên ($P_e$)**:
  $$P_e = \frac{14 \times 11 + 10 \times 11 + 0 \times 2}{24 \times 24} = \frac{154 + 110 + 0}{576} = \frac{264}{576} = \frac{11}{24} \approx 0{,}458333$$
- **Hệ số Cohen’s Kappa nhãn lớp ($\kappa$)**:
  $$\kappa = \frac{P_o - P_e}{1 - P_e} = \frac{\frac{21}{24} - \frac{11}{24}}{1 - \frac{11}{24}} = \frac{\frac{10}{24}}{\frac{13}{24}} = \frac{10}{13} \approx 0{,}769230769... \approx 0{,}769231$$

> [!NOTE]
> Theo thang phân loại chuẩn của Landis & Koch (1977), hệ số $\kappa = 0{,}769231$ nằm trong khoảng $[0{,}61 - 0{,}80]$, tương ứng mức **Substantial Agreement** (Thỏa thuận rất cao). Đây là mức độ tin cậy vượt trội trong gán nhãn độc lập song song trước khi bước vào phiên phân xử.

### 2.2. Ma trận nhầm lẫn tổng hợp 3x3 trước phân xử (Confusion Matrix)

Ma trận phản ánh số lượng phân loại nhãn lớp tổng hợp giữa Đánh giá viên A (dòng) và Đánh giá viên B (cột):

| Đánh giá viên A \ B | Benign (B) | Phishing (B) | Insufficient Evidence (B) | Tổng dòng (A) |
| :--- | :---: | :---: | :---: | :---: |
| **Benign (A)** | **11** | 1 | 2 | **14** |
| **Phishing (A)** | 0 | **10** | 0 | **10** |
| **Insufficient Evidence (A)** | 0 | 0 | **0** | **0** |
| **Tổng cột (B)** | **11** | **11** | **2** | **24** |

*Tổng số ca bất đồng nhãn lớp ghi nhận trước phân xử là 3 ca (chi tiết từng ca được lưu trữ bảo mật tại phân vùng hạn chế).*

---

## 3. KIỂM TOÁN SỰ CỐ THAO TÁC GIAO DIỆN VÀ TÍNH CHÍNH THỨC CỦA TỆP PASS 1

### 3.1. Bối cảnh và Xác nhận của Lead D
Trong quá trình gán nhãn Pass 1 của Đánh giá viên A, giao diện CLI gặp hiện tượng lag hiển thị trên 01 mẫu khảo sát dẫn đến việc ghi nhận trạng thái chưa đúng với nhận định ban đầu.
Lead D xác nhận:
1. Bản trước sửa là lỗi thao tác do lag giao diện, không phải là sự thay đổi quyết định gán nhãn chuyên môn.
2. Việc phê duyệt sửa đổi được thực hiện khi A hoàn toàn chưa tiếp cận nhãn hay dữ liệu gán của B (bảo đảm nguyên tắc mù song song tuyệt đối).

### 3.2. Chính sách quản trị dữ liệu áp dụng
- **Tệp chính thức**: Tệp gán nhãn Pass 1 chính thức của Đánh giá viên A có mã băm SHA-256 là `1c60d10ac4056679d8aafe2b13dcf4f00ffc0f332d34f5413f4b922164eac7f1` (đã được tiếp nhận đầy đủ tại `data/annotations/A/clean_calibration_pass1.jsonl` và lưu trữ bản sao tại phân vùng hạn chế). Toàn bộ các phép tính thống kê và nghị trình phân xử sử dụng tệp này.
- **Lưu trữ kiểm toán**: Mã định danh mẫu cụ thể, tệp nháp tiền sửa lỗi và chi tiết diff là mục kiểm toán còn mở, đang chờ Đánh giá viên A bàn giao; sau khi nhận mới tính SHA-256, lập diff chi tiết và lưu vào audit hạn chế ngoài Git (`data/restricted/`). Tuyệt đối không suy đoán nội dung khi chưa nhận bàn giao.
- **Quy tắc bất biến**:
  - Không tính Kappa trên bản lỗi.
  - Không yêu cầu Đánh giá viên A gán lại toàn bộ tập dữ liệu.
  - Tuyệt đối không chỉnh sửa tệp đã khóa `1c60d10a...`.
  - Không tự suy đoán diff trường dữ liệu khi chưa nhận bàn giao tệp nháp gốc từ Đánh giá viên A.

---

## 4. BÁO CÁO KIỂM SOÁT CHẤT LƯỢNG TỔ CHỨC (ORGANIZATION QC AUDIT)

### 4.1. Hiện tượng và Quy mô rà soát
Qua rà soát đối chiếu trường dữ liệu, hồ sơ ghi nhận:
1. **12 trường hợp mâu thuẫn hình thức trong tệp của A**: Giá trị trường `primary_org_status = "identified"` nhưng `primary_org = "unknown"`.
2. **5 trường hợp bất đồng thô về định danh tổ chức**:
   - **3 trường hợp được giải quyết bằng bảng alias đã khóa (`configs/dictionary_v1.json`)**: Đánh giá viên A ghi nhận thương hiệu con/alias (ví dụ `facebook`), Đánh giá viên B ghi nhận mã chuẩn `meta`. Bảng alias ánh xạ thống nhất về mã canonical `meta`, giải quyết hoàn toàn bất đồng trước phân xử.
   - **2 trường hợp bất đồng tổ chức ngoài danh mục**: Cần chuyển vào phiên phân xử để hội đồng chuẩn hóa định danh thống nhất.

### 4.2. Mẫu số đủ điều kiện và Chính sách công bố
- Theo quy định tại **Mục 6 của Codebook v1.1**: Hệ số Cohen's Kappa cho mã tổ chức `primary_org` đơn trị chỉ được tính trên các cặp mẫu mà cả hai bên đều xác định được mục tiêu chính đơn trị hợp lệ.
- Do 12 ca của A gặp lỗi hình thức và các ca `unknown` / `no_clear_target`, mẫu số đủ điều kiện tính Kappa mã đơn trị trước phân xử bị thu hẹp đáng kể.
- **Quyết định kỹ thuật**: Giữ nguyên vẹn 100% bản ghi Pass 1 của A; **chưa công bố Kappa tổ chức như kết luận chính thức**; đưa toàn bộ các ca cần chuẩn hóa vào hồ sơ phân xử riêng.

---

## 5. NGHỊ TRÌNH TRUNG LẬP PHÂN XỬ PASS 2 & QUYẾT ĐỊNH DUYỆT CỦA LEAD D

### 5.1. Quyết định duyệt và Chủ trì phiên
Lead D (Anh Tuấn) đã kiểm tra toàn diện và **chính thức DUYỆT NGHỊ TRÌNH** cho phép mở phiên phân xử Pass 2. Lead D trực tiếp chủ trì phiên phân xử.

### 5.2. Thứ tự tiến hành phiên phân xử Pass 2
1. **Phần 1: Phân xử nhãn lớp (3 ca bất đồng)**: Đánh giá viên A và B lần lượt trình bày bằng chứng quan sát từ Blind View và quy tắc Codebook v1.1; Lead D ghi nhận quyết định cùng lý do.
2. **Phần 2: QC tổ chức (14 ca)**: Rà soát 12 ca A ghi `identified/unknown` và 2 ca bất đồng ngoài danh mục. Ghi nhận rõ 3 ca alias `facebook` → `meta` đã giải quyết theo từ điển khóa là chuẩn hóa alias, không sửa Pass 1.
3. **Phần 3: Xử lý ca thiếu chứng cứ**: Với các ca chưa đủ dữ liệu quan sát hành vi, ghi trạng thái QC phù hợp; tuyệt đối không ép chọn nhãn nhị phân hoặc gán mã tổ chức khi chưa đủ cơ sở.

### 5.3. Nguyên tắc trung lập và Bảo mật ranh giới
1. **Chỉ sử dụng hồ sơ hạn chế đã duyệt**: Cung cấp cùng một bản hồ sơ hạn chế đã duyệt cho A và B trong phiên.
2. **Zero External Metadata**: Tuyệt đối không đưa nhãn nguồn, locator Parquet, matcher hoặc kết quả mô hình vào tài liệu thảo luận.
3. **Bảo toàn nguyên bản Pass 1**: Giữ nguyên từng byte hai file Pass 1 gốc và kết quả thống kê trước phân xử ($N=24, P_o=21/24, P_e=11/24, \kappa=10/13$).
4. **Khóa xuất nhãn**: Chưa xuất `labels_final` hoặc chốt `PLAN-01` trước khi Lead D duyệt biên bản quyết định đầy đủ.

---

## 6. KIỂM TOÁN RANH GIỚI DỮ LIỆU & GHI NHẬN SỰ CỐ COMMIT e7a450c

1. **Ghi nhận sự cố cam kết e7a450c**:
   Tại commit `e7a450c` trên nhánh nghiên cứu `feat/c-calibration-v1-1-4-adjudication`, tệp báo cáo công khai từng xuất hiện thông tin chi tiết nhãn A/B và mô tả nội dung theo từng mã mẫu.
2. **Phạm vi có thể xác minh**:
   - Nhánh nghiên cứu nội bộ của nhóm (`feat/c-calibration-v1-1-4-adjudication`);
   - Kho lưu trữ không lưu nhật ký truy cập mạng độc lập (access logs) nên không đưa ra khẳng định tuyệt đối về số lượt truy cập từ bên ngoài;
   - Ghi nhận trung thực rằng nội dung cấp mẫu tại commit `e7a450c` vẫn còn lưu lại trong lịch sử Git trừ khi có quy trình thanh lọc lịch sử độc lập được phê duyệt.
3. **Quy trình khắc phục**:
   - Khắc phục triệt để bằng việc chuyển toàn bộ danh sách ca, bằng chứng và câu hỏi nghị trình chi tiết sang phân vùng hạn chế ngoài Git (`data/restricted/`); bản công khai trên Git chỉ giữ số liệu tổng hợp, phương pháp luận và bảng mã băm.
   - Giữ nguyên lịch sử commit (không force-push, không viết lại lịch sử) nhằm duy trì tính bất biến và trung thực của audit trail.

---

## 7. QUẢN TRỊ BẢO MẬT VÀ MÃ BĂM ARTIFACT

- **Khóa huấn luyện**: `training_blocked = true`. Tuyệt đối không đưa tập hiệu chuẩn hay dữ liệu phân xử vào bất kỳ quá trình huấn luyện mô hình nào.
- **Cô lập tập kiểm thử chính thức**: `official_test_used = false`. Toàn bộ dữ liệu Official Test được bảo vệ biệt lập 100%.
- **Trạng thái sẵn sàng**: `ready_for_adjudication_pass2 = true` (Đã được Lead D chính thức duyệt mở phiên phân xử).
- **Mã băm các artifact hạn chế và công khai**:
  - `data/restricted/clean_calibration_adjudication_dossier_restricted.json`: `658ea07a846c2adc79609f34bab833145a61d62fe026e0c928e7d7b40e16a92f`
  - `data/restricted/intake_pass1_B_6069f61c.jsonl`: `6069f61c5550f39e2aa39158ec0d3f183c01198b5b0d6e0479ab792bd15cc3f0`
  - `data/restricted/intake_pass1_A_1c60d10a.jsonl`: `1c60d10ac4056679d8aafe2b13dcf4f00ffc0f332d34f5413f4b922164eac7f1`
  - `data/source_audit/clean_calibration_pre_adjudication_audit.json`: `33f41531344b700a0407da908c0832c39a9a6e0c0ec9111ceaf6cd82d5a676eb`

---
*Báo cáo được lập bởi Thành viên C. Đã được Lead D chính thức duyệt mở phiên phân xử Pass 2.*
