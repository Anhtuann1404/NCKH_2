1. **Khóa cam kết commitment hash (không lộ fingerprint):**  
   Dùng HMAC-SHA256 với khóa bí mật độc lập (lưu ngoài registry, ví dụ biến môi trường) kết hợp salt ngẫu nhiên đủ entropy (≥128 bit) cho mỗi mục; lưu dạng `salt$hmac`. Không dùng hash thuần hoặc salt ngắn vì fingerprint có thể bị brute-force ngược; tuyệt đối không commit secret key vào repo.

2. **Cơ chế fail-closed trong split/train:**  
   Trước mỗi phép chia tập, kiểm tra chồng lấn eTLD+1 giữa các fold và giữa train/test bằng assertion độc lập; nếu phát hiện trùng lặp, raise `DataLeakageError` và dừng pipeline ngay lập tức, không có fallback âm thầm. Đồng thời validate cấu trúc registry (hash khớp, đủ trường) trước khi train, nếu không hợp lệ thì abort toàn bộ tiến trình.

3. **Gói QA cho Member B:**  
   Cung cấp bộ pytest bao gồm: (i) unit test cho trích xuất đặc trưng URL/DOM/Text; (ii) test tính đúng đắn của commitment hash (verify và phát hiện giả mạo); (iii) test grouped split chống rò rỉ với fixture domain trùng; (iv) test các cờ `shared_unverified` cho Shared Hosting/UGC; (v) test reproducibility với 3 seed (17, 42, 2026) và so sánh kết quả bootstrap CI; (vi) test biên (URL rỗng, HTML thiếu thẻ, mã hóa lạ). Chạy tự động trên CI/CD, có báo cáo coverage.

4. **Quy trình bàn giao cho Lead D:**  
   Bàn giao bộ tài liệu gồm: kiến trúc hệ thống, mô tả dữ liệu và registry, hướng dẫn tái lập (cấu hình môi trường, seed, tham số), bộ kết quả thực nghiệm đầy đủ (M0–M3, thresholds, CI), biên bản audit chống rò rỉ (kèm hash kiểm tra), và hướng dẫn lưu trữ secret key an toàn ngoài repo. Kèm theo checklist QA đã vượt qua và đầu mối liên hệ (Member B) để Lead D phản hồi trực tiếp.