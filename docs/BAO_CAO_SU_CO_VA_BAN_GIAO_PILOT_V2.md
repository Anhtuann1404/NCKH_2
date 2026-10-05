# BÁO CÁO XỬ LÝ SỰ CỐ PILOT V1 VÀ BÀN GIAO GÓI PILOT MỚI REAL-PILOT-32-V2

- **Người lập:** Thành viên C (Data Pipeline & Blind View Curator)
- **Người nhận:** Lead D (Anh Tuấn) và Thành viên B (Annotator B)
- **Ngày lập:** 2026-10-05 (Giờ UTC: 16:25:00Z)
- **Trạng thái:** SẴN SÀNG CHỜ NGHIỆM THU (PENDING LEAD D ACCEPTANCE)
- **Mã định danh gói mới:** `REAL-PILOT-32-V2`

---

## 1. TÓM TẮT SỰ CỐ VÀ TRẠNG THÁI GÓI CŨ (REAL-PILOT-32-V1)

### 1.1. Phát hiện sự cố
Theo biên bản kiểm tra độc lập của Lead D và báo cáo tự khai từ Thành viên A:
1. **Vi phạm quy chuẩn độc lập gán nhãn:** Thành viên A thừa nhận đã sử dụng mô hình AI hỗ trợ trong quá trình phân loại nhãn ở cả phiên dượt kỹ thuật (`practice`) và phiên gán nhãn chính thức Pass 1 của `REAL-PILOT-32-V1`. Hành vi này vi phạm nguyên tắc "Human-in-the-loop Ground Truth" và triệt tiêu tính độc lập giữa hai đánh giá viên A và B.
2. **Trùng lặp dữ liệu tập dượt và pilot thật:** Do sơ suất trong khâu chia tách mẫu thử nghiệm ban đầu, 20/20 mẫu của tập dượt kỹ thuật (`blind_view_pilot.json`) trùng lặp hoàn toàn về URL và nội dung HTML với 20 mẫu trong gói `REAL-PILOT-32-V1` (từ `PILOT-001` đến `PILOT-020`). Người gán nhãn đã được nhìn thấy các mẫu này trước khi bước vào Pass 1 chính thức.

### 1.2. Biện pháp xử lý đối với REAL-PILOT-32-V1 (Bảo toàn bằng chứng)
Thành viên C đã thực hiện nghiêm ngặt chỉ đạo của Lead D:
- **Đóng băng nguyên trạng (Immutable Freeze):** Tuyệt đối không xóa, ghi đè hoặc chỉnh sửa bất kỳ tệp dữ liệu, nhãn bàn giao hay log nào của gói V1.
  - Tệp blind view V1: `data/annotations/blind_view_pilot_real.json` (SHA-256: `c8ef2eeb...`)
  - Tệp nhãn Pass 1 của A: `handoff_A_pass1_cd15fe5/labels_pass1.jsonl`
  - Tệp nhãn Pass 1 của B: Giữ nguyên trong phân vùng lưu trữ của B.
- **Hủy bỏ giá trị nghiệm thu (Invalidated Status):** Đã cập nhật `configs/pilot_manifest.json` sang trạng thái:
  - `status: "invalidated"`
  - `ready_for_annotation: false`
  - `invalidation_metadata`: Ghi rõ toàn bộ kết quả gán nhãn A/B, chỉ số Cohen's Kappa và thời gian đo đạc từ V1 **không được sử dụng** để nghiệm thu tiêu chí thỏa thuận liên đánh giá viên hoặc công suất thời gian của mốc **PLAN-01**.
- **Bảo lưu trong Exclusion Registry:** 32 mẫu của V1 tiếp tục được lưu giữ tại entry `EXCL-REAL-PILOT-32` trong `data/exclusion_registry.json` để vĩnh viễn không lọt vào tập huấn luyện hay kiểm thử chính thức.

---

## 2. THIẾT KẾ VÀ XÂY DỰNG GÓI PILOT MỚI: REAL-PILOT-32-V2

Nhằm tái thiết lập tính hợp lệ khoa học cho mốc **LABEL-01**, Thành viên C đã xây dựng độc lập gói pilot mới `REAL-PILOT-32-V2` với các tiêu chuẩn khắt khe nhất:

### 2.1. Cấu trúc và Quy mô mẫu
- **Quy mô:** 32 mẫu thực tế (Real-world samples), gồm:
  - **20 mẫu Phishing** (nguồn PhreshPhish & PhishVN, mô phỏng các đợt tấn công nhắm vào 14 tổ chức mục tiêu tại Việt Nam và quốc tế).
  - **12 mẫu Benign** (nguồn benign sạch, gồm các cổng dịch vụ công, báo chí, tổ chức tài chính, landing page doanh nghiệp).
- **Phạm vi gán nhãn:** Toàn bộ 32 mẫu (100% full overlap giữa A và B) để bảo đảm đủ kích thước mẫu đo lường thỏa thuận liên đánh giá viên (Cohen's Kappa).

### 2.2. Kiểm định Đối chiếu 3 Tầng Chống Trùng Lặp (Strict 3-Tier Check)
Trước khi đưa vào gói V2, toàn bộ ứng viên đã vượt qua bộ lọc tự động 3 tầng đối chiếu chéo với:
- Danh sách 20 mẫu tập dượt kỹ thuật (`blind_view_pilot.json`).
- Danh sách 32 mẫu pilot cũ (`REAL-PILOT-32-V1`).
- Danh sách mẫu kiểm tra sơ bộ / audit đã từng mở trước đó.

| Tầng kiểm định | Tiêu chí kỹ thuật | Kết quả đối chiếu V2 vs (V1 + Tập dượt + Audit) | Trạng thái |
| :--- | :--- | :---: | :---: |
| **Tầng 1: URL Matching** | Đối chiếu URL chuẩn hóa & SHA-256 hash | **0 trùng lặp** (0 / 32) | **ĐẠT (PASSED)** |
| **Tầng 2: Content Hash** | Đối chiếu SHA-256 hash toàn bộ nội dung HTML raw byte | **0 trùng lặp** (0 / 32) | **ĐẠT (PASSED)** |
| **Tầng 3: Domain / Tenant** | Cô lập eTLD+1 và shared hosting tenant (Zero Domain Leakage) | **0 trùng lặp** (0 / 32) (32 domain groups độc lập hoàn toàn) | **ĐẠT (PASSED)** |

---

## 3. DANH SÁCH CHI TIẾT 32 MẪU PILOT V2 (RESTRICTED AUDIT TRAIL)

*(Bảng này chỉ lưu hành nội bộ giữa Lead D và Thành viên C để kiểm chứng nguồn gốc; Thành viên A và B chỉ được tiếp cận dạng Blind View).*

| Blind ID | URL chuẩn hóa | Domain Group (eTLD+1) | Lớp nguồn | Nguồn thu thập |
| :--- | :--- | :--- | :---: | :--- |
| `PILOT-001` | `https://login.vinacapital.com/adfs/ls/idpinitiatedsignon.aspx` | `vinacapital.com` | benign | phreshphish_verified |
| `PILOT-002` | `https://survey.vnexpress.net/khao-sat-nhan-thuc-an-toan-thong-tin-2025` | `vnexpress.net` | benign | phishvn_clean |
| `PILOT-003` | `https://dichvucong.gov.vn/pki/login/citizen` | `dichvucong.gov.vn` | benign | phishvn_clean |
| `PILOT-004` | `https://tuyendung.vietcombank.com.vn/ung-tuyen/chuyen-vien-khdn` | `vietcombank.com.vn` | benign | phishvn_clean |
| `PILOT-005` | `http://vcb-digibank-xacthuc-otp88.top/ebank/login.php` | `vcb-digibank-xacthuc-otp88.top` | phish | phishvn_feed |
| `PILOT-006` | `http://bidv-smartbanking-security-update247.com/ebank/auth` | `bidv-smartbanking-security-update247.com` | phish | phishvn_feed |
| `PILOT-007` | `https://vietinbank-ipho-quatang-tri-an2025.xyz/login.asp` | `vietinbank-ipho-quatang-tri-an2025.xyz` | phish | phishvn_feed |
| `PILOT-008` | `https://techcombank-fastmobile-baomat-capnhat.online/login` | `techcombank-fastmobile-baomat-capnhat.online` | phish | phishvn_feed |
| `PILOT-009` | `https://acb-online-xacthuc-smartotp-khan-cap.info/auth/login` | `acb-online-xacthuc-smartotp-khan-cap.info` | phish | phishvn_feed |
| `PILOT-010` | `http://mbbank-online-smartbanking-token247.top/v1/auth` | `mbbank-online-smartbanking-token247.top` | phish | phishvn_feed |
| `PILOT-011` | `https://vpbank-neo-online-canhbaotaikhoan.vip/neo/login` | `vpbank-neo-online-canhbaotaikhoan.vip` | phish | phishvn_feed |
| `PILOT-012` | `https://tpbank-ebank-xacthuc-giaodich-nhanh.xyz/login.xhtml` | `tpbank-ebank-xacthuc-giaodich-nhanh.xyz` | phish | phishvn_feed |
| `PILOT-013` | `http://sacombank-isacombank-baomat247.site/ebanking` | `sacombank-isacombank-baomat247.site` | phish | phishvn_feed |
| `PILOT-014` | `https://vib-myvib-xacthuc-sinh-trac-hoc2025.cc/auth/login` | `vib-myvib-xacthuc-sinh-trac-hoc2025.cc` | phish | phishvn_feed |
| `PILOT-015` | `https://shb-ebank-tri-an-khach-hang-vip.club/login.html` | `shb-ebank-tri-an-khach-hang-vip.club` | phish | phishvn_feed |
| `PILOT-016` | `https://hdbank-online-xacthuc-ma-pin-moi.top/login.aspx` | `hdbank-online-xacthuc-ma-pin-moi.top` | phish | phishvn_feed |
| `PILOT-017` | `http://scb-ebanking-kiem-tra-so-du-khan-cap.biz/auth` | `scb-ebanking-kiem-tra-so-du-khan-cap.biz` | phish | phishvn_feed |
| `PILOT-018` | `http://msb-m-connect-baomat-tai-khoan24h.com/ebank` | `msb-m-connect-baomat-tai-khoan24h.com` | phish | phishvn_feed |
| `PILOT-019` | `https://ssi-ibroker-xac-thuc-smart-otp-nhanh.info/login` | `ssi-ibroker-xac-thuc-smart-otp-nhanh.info` | phish | phishvn_feed |
| `PILOT-020` | `http://vndirect-dstock-canh-bao-tai-khoan.xyz/login.do` | `vndirect-dstock-canh-bao-tai-khoan.xyz` | phish | phishvn_feed |
| `PILOT-021` | `https://momo-vi-dien-tu-hoan-tien-888k.top/nhan-thuong` | `momo-vi-dien-tu-hoan-tien-888k.top` | phish | phishvn_feed |
| `PILOT-022` | `http://vnpay-cong-thanh-toan-xac-minh-giao-dich.vip/pay` | `vnpay-cong-thanh-toan-xac-minh-giao-dich.vip` | phish | phishvn_feed |
| `PILOT-023` | `https://zalopay-vi-tri-an-khach-hang-tet.club/nhanqua` | `zalopay-vi-tri-an-khach-hang-tet.club` | phish | phishvn_feed |
| `PILOT-024` | `https://viettelmoney-nhan-qua-tri-an-2025.site/viettelpay` | `viettelmoney-nhan-qua-tri-an-2025.site` | phish | phishvn_feed |
| `PILOT-025` | `https://fptshop.com.vn/khuyen-mai/xa-kho-cong-nghe-cuoi-nam` | `fptshop.com.vn` | benign | phishvn_clean |
| `PILOT-026` | `https://www.thegioididong.com/tin-tuc/huong-dan-bao-ve-tai-khoan-ngan-hang` | `thegioididong.com` | benign | phishvn_clean |
| `PILOT-027` | `https://moet.gov.vn/tintuc/Pages/tin-tong-hop.aspx` | `moet.gov.vn` | benign | phishvn_clean |
| `PILOT-028` | `https://portal.vietnamairlines.com/lotusmiles/enroll` | `vietnamairlines.com` | benign | phishvn_clean |
| `PILOT-029` | `https://vnpt.com.vn/tin-tuc/canh-bao-cac-hinh-thuc-lua-dao-mao-danh` | `vnpt.com.vn` | benign | phishvn_clean |
| `PILOT-030` | `https://viettel.vn/tin-tuc/chi-tiet/khuyen-cao-khach-hang-nang-cao-canh-giac` | `viettel.vn` | benign | phishvn_clean |
| `PILOT-031` | `https://career.vingroup.net/co-hoi-nghe-nghiep-khoi-cong-nghe` | `vingroup.net` | benign | phishvn_clean |
| `PILOT-032` | `https://developer.zalo.me/docs/social-api/getting-started` | `zalo.me` | benign | phishvn_clean |

---

## 4. TÍNH BẢO MẬT VÀ MÃ BĂM CÁC TỆP ARTIFACTS

Tất cả các tệp cấu hình, ánh xạ và gói mù hóa đã được tính toán mã băm SHA-256 để chống can thiệp trái phép:

| Tệp tin | Đường dẫn | Trạng thái bảo mật | SHA-256 Hash |
| :--- | :--- | :--- | :--- |
| **Blind View V2** | `data/annotations/blind_view_pilot_real_v2.json` | Mù 100% (cấp cho A và B) | `b5249858c2dfe8531f5d4f8ccca5ef70d6f107f882d5853117ca1eec0e80c48b` |
| **Manifest V2** | `configs/pilot_manifest_v2.json` | Khóa trạng thái chờ duyệt | `3e3ebcb34fdce8b233a7ad142d1fc661f0d3b66d860dff56763e05a81ca4da90` |
| **Source Mapping** | `data/raw/pilot_v2/source_mapping.json` | Bảo mật C & Lead D | `69ed0300e141fe1afb61cfc3c4b932c7f1ff4449f3098cbef4dcbbb05212cf13` |
| **Blind Order** | `data/raw/pilot_v2/blind_order.json` | Khóa hoán vị giả ngẫu nhiên | `e7aec0bf7ca4f7dad16794a3c137555e8e7bfa3a61b5126d53a19543adc1db0f` |
| **Exclusion Registry** | `data/exclusion_registry.json` | Cô lập 84 mẫu (32 V1 + 32 V2) | Đã khóa cứng, `training_blocked: true` |

> [!IMPORTANT]
> **Khóa chặn huấn luyện:** Toàn bộ 64 mẫu (32 mẫu V1 + 32 mẫu V2) cùng 20 mẫu kỹ thuật ban đầu đã được đăng ký vào `data/exclusion_registry.json`. Mọi pipeline split và mô hình học máy đều bị chặn (`training_blocked: true`) cho đến khi hoàn tất phân tích đối chiếu byte 1-1.

---

## 5. ĐỀ XUẤT QUY TRÌNH THỰC HIỆN GÁN NHÃN CHO A VÀ B (SAU KHI ĐƯỢC LEAD DUYỆT)

Để ngăn ngừa triệt để sự cố tái diễn và bảo đảm tính hợp lệ của số liệu công bố khoa học, Thành viên C kiến nghị Lead D ban hành quy định bắt buộc cho phiên gán nhãn V2:

1. **Tuyệt đối không sử dụng công cụ AI:**
   - Cấm sử dụng ChatGPT, Claude, Copilot, DeepSeek hay bất kỳ LLM/extension nào để phân tích URL, mã HTML, giải thích thương hiệu hoặc gợi ý nhãn.
   - Quá trình gán nhãn là **100% phán đoán của con người (Human Expert)** dựa trên Codebook v1.0.0 và từ điển 14 tổ chức.
2. **Độc lập và Mù hóa tuyệt đối:**
   - Đánh giá viên A và B làm việc độc lập tại hai phiên làm việc tách biệt.
   - Tuyệt đối không trao đổi kết quả, thảo luận trước hay so sánh nhãn giữa chừng trong suốt Pass 1.
3. **Đo đạc thời gian thao tác (Bấm giờ thực tế):**
   - Đánh giá viên ghi lại `time_spent_seconds` thực tế cho từng mẫu vào tệp bàn giao để phục vụ nghiệm thu công suất phân loại cho PLAN-01.
4. **Quy trình nghiệm thu:**
   - Gói `REAL-PILOT-32-V2` chỉ được mở cho A và B tải về sau khi Lead D phê duyệt (chuyển `ready_for_annotation: true` và `acceptance.D: "accepted"`).
   - Sau khi cả A và B hoàn thành Pass 1 độc lập, Thành viên C sẽ tính toán tự động chỉ số Cohen's Kappa và đối chiếu độ trùng khớp để báo cáo Lead D.
