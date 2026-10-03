# Experiment protocol v0.1

Theo RQ1–RQ3 và 5.2d–e đề cương. Không đổi câu hỏi sau khi xem kết quả. Chưa có run thật.

## Cấu hình

- M0: URL.
- M1: M0 + thống kê DOM đã đặc tả và tái lập được.
- M2: M1 + TF-IDF từ/char n-gram.
- M3: M2 + tín hiệu tổ chức–miền–ý định.
- B-rule: quy tắc danh tính/miền/ý định; shared hosting không tự được coi là nhất quán.

Logistic Regression trước; LightGBM so sánh M2/M3 khi baseline ổn định. Cặp M2/M3 cùng họ mô hình, biểu diễn, split và ngân sách tối ưu. Đặc trưng cụ thể và preprocessing khóa trước run chính; metadata label/target/tier/date/split/hash/id/group không vào X. M0–M3 đánh giá trên cùng mẫu có đủ URL–nội dung.

## Hai phân tích chính

**A:** toàn tập chính, recall/FPR và chênh M3–M2.

**B:** phishing trong danh mục theo nhãn độc lập, cùng model/ngưỡng của A; không tối ưu threshold trên tập con. Báo coverage, counts/miền, unknown và FPR benign chung/hard benign. Tỷ lệ phủ thấp không là lý do thêm thương hiệu sau kết quả.

## Grouped evaluation

5-fold × seed 17, 42, 2026; dùng cùng fold cho M0–M3/B-rule. Nếu nhóm không đủ, giảm fold và ghi lý do trước run chính. Nhóm nối từ miền/trùng không vượt train/validation/test.

Trong outer train: chia nhóm nội bộ cho chọn hyperparameter, fuzzy threshold và operating threshold. Fit vocabulary, IDF, SVD, scaler/selector/model bằng phần huấn luyện tương ứng. Tạo điểm chọn ngưỡng từ validation nội bộ; outer test chỉ đo. Nếu inner CV để chọn cấu hình, lưu predictions nội bộ đúng nguồn, không dùng dự đoán in-sample để giả làm validation.

Chọn threshold để FPR validation không vượt mục tiêu 1%/5% theo quy tắc xác định: score >= threshold là warning; xét unique scores/ties, lấy điểm có recall cao nhất trong phần chọn ngưỡng với ràng buộc FPR; tie chọn threshold cao hơn. Trường hợp không có benign hoặc không có điểm vận hành hữu ích được ghi rõ. FPR test thực tế có thể khác mục tiêu.

Chọn threshold không đọc tổ chức/phân nhóm test. Dictionary cơ sở cố định mọi fold; nhánh thích nghi theo dữ liệu, nếu có, dựng từ inner/outer training đúng phạm vi.

## Ablation và lỗi

M3 bỏ lần lượt tín hiệu tổ chức, quan hệ miền, ý định; nếu đủ giờ, thêm so khớp mờ/biến thể. Các ablation dùng splits và quy trình chọn ngưỡng giống nhau. Phân nhóm URL có/không token, trong/ngoài danh mục, unknown, shared hosting và benign khó. Phân nhóm từ nhãn tham chiếu/QC độc lập, không từ prediction để tự chứng minh prediction.

Đọc lỗi sau khóa nhãn: nhắc thương hiệu trong tin tức, SSO hợp lệ, tenant chưa xác minh, nhiều mục tiêu, tên mới, chữ trong ảnh và DOM runtime khác HTML offline. Không dùng test errors để sửa dictionary rồi báo cùng test như chưa gặp.

## Chỉ số và CI

Recall, FPR, precision, F1, PR-AUC; TP/FN/FP/TN, base rate, counts và FPR thực đo ở từng threshold/fold. Không diễn giải precision của tập lấy mẫu thành precision ngoài thực tế.

Chênh recall M3–M2 và B-rule dùng cùng mẫu. CI 95% bằng paired group bootstrap: resample group, giữ tất cả trang trong group, cùng lần resample cho các cấu hình; tính riêng mỗi seed. Lưu seed và số bootstrap (đề xuất 2.000 lần, khóa trước báo cáo). Không nhân 3 số mẫu độc lập vì lặp seed. Nếu một replicate thiếu lớp thì không tính chỉ số không xác định, báo số valid/invalid. CI có điều kiện trên mô hình đã fit; trình bày thêm dao động fold/seed.

## Phân tích phụ thời gian đã định trước

Mốc 60%/80% date, không tách cùng ngày; train sớm, validation giữa, test muộn. Loại bản ghi muộn trùng group sớm; không chuyển tương lai vào train. Cấu hình, vocab, model và threshold chỉ chọn từ phần trước tương ứng; không dùng CV chính chứa test muộn để chọn nhánh này.

Dictionary riêng as-of cuối train: chỉ thương hiệu trong báo cáo đã công bố trước mốc đó; miền/bí danh/ủy quyền cần bằng chứng hiệu lực. Nếu chỉ có tri thức hiện tại, báo hồi cứu và giới hạn, không nói đã chứng minh hiệu quả triển khai tương lai. Thiếu date/lớp/nhóm sau loại trùng phải báo counts và tính bất khả ước lượng, không chọn lại cutoff bằng hiệu năng.

## Official test và nhánh khác

Official test giữ ngoài phát triển: chạy thêm sau freeze, loại trùng group với fit/validation/pilot/đã xem phát triển. Ghi cửa sổ date thực; không mặc định đó là tương lai. Việt Nam có danh mục mở rộng khóa trước nhãn/đánh giá, báo cáo riêng. Trang mô phỏng chỉ đo chức năng/độ trễ; không thay dữ liệu phishing thật.

## Run manifest

Mỗi run_id có: git commit hoặc code hash; environment lock; source/sampling/label/group/split/dictionary hashes; feature/preprocessing version; model variant/family; seed; parameters/search budget; validation threshold và FP counts; scores/predictions ngoài mẫu; metrics, CI config; exclusion log và ngày.

Artifacts dự kiến `artifacts/runs/<run_id>/`: config.json, manifest.json, thresholds.json, predictions.jsonl, metrics.json, notes.md. Thư mục này hạn chế/chưa có, không commit raw rows hoặc predictions kèm URL nhạy cảm.

## Bundle demo

Sau nghiên cứu, train bundle triển khai bằng phần phát triển cho phép và ghi ngưỡng riêng từ validation. Không dùng official test chọn ngưỡng demo. Report hiệu năng nghiên cứu từ OOF/time/test đã khóa; đo runtime API/extension riêng. Payload không đủ/timeout là chưa đánh giá được, không là true negative.
