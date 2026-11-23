========================================================================================
PHỤ LỤC THẨM ĐỊNH QA ĐỘC LẬP (PHIÊN BẢN V1.7):
XÁC NHẬN COMMIT b5b7db2 CHỈ ĐỔI MANIFEST, BÀN GIAO NGUYÊN BYTE HỒ SƠ QA V1.6 GỐC & RAW LOG (33e8bb6),
VÀ KHÓA CỔNG KIỂM MIGRATION LEDGER / VERIFIER FINGERPRINT (TRẠNG THÁI PENDING)
========================================================================================

Kính gửi: Lead D (Anh Tuấn) và Thành viên C (Nguyễn Thắng)
Người gửi: Phùng Tấn Minh (Thành viên B — Annotator B kiêm QA Lead & Nhóm trưởng)
Ngày báo cáo: 22/11/2026
Repository & Nhánh: Anhtuann1404/NCKH_2 — nhánh origin/feat/c-main-annotation-batch1
Commit đã QA mã/fixture giữ nguyên: 33e8bb6c29c7ee15209ae5847d48aae973a3f536
Commit cập nhật manifest đã đối chiếu diff: b5b7db2900fefd142c211fb2045a3e2bf3272298
Tài liệu Phụ lục QA V1.7: docs/QA_ADDENDUM_MAIN_BATCH1_B5B7DB2_MIGRATION_VERIFIER_PENDING_V1_7_B.md
(Dung lượng: 20.658 bytes | SHA-256: 3fecd1ef8f7cffd4a537ea45d4285c823eb0f557c9bd36f213779c0794e15007)
Hồ sơ QA V1.6 gốc và Raw Log bàn giao nguyên byte để C lưu trữ:
1. docs/QA_REPORT_MAIN_BATCH1_33E8BB6_CONSOLIDATED_V1_6_B.md
   (Dung lượng: 37.162 bytes | SHA-256: bfeb73d97db47fdb6741ce47849254d4f3a9483120bd533a3cb0f357f8a41e09)
2. docs/QA_RAW_LOG_MAIN_BATCH1_33E8BB6_B.txt
   (Dung lượng: 10.920 bytes | SHA-256: 29b452ff6b2debfd2826d3ac3f15678a7f07aff3b45012e53ff3462c17c30ee7)

1. MỤC TIÊU VÀ PHẠM VI:
- Đối chiếu commit b5b7db2900fefd142c211fb2045a3e2bf3272298 với commit đã QA 33e8bb6c29c7ee15209ae5847d48aae973a3f536; giữ nguyên kết quả QA kỹ thuật trên mã/fixture tại 33e8bb6 (154 passed trong 8 tệp chọn lọc) mà không cần chạy lại test chỉ vì release manifest thay đổi.
- Bàn giao nguyên byte báo cáo QA V1.6 gốc cùng tệp raw log đã chạy tại 33e8bb6 để Thành viên C lưu hồ sơ.
- Ghi nhận trạng thái PENDING (không ký trước) đối với phần QA mã Migration Ledger và Verifier Fingerprint, đồng thời khóa danh mục tiêu chí kiểm thử bằng fixture tổng hợp (Mục 3 và Mục 4 chỉ đạo của Lead D) để thực thi ngay khi C bàn giao commit mã mới.

2. NGƯỜI THỰC HIỆN / NGƯỜI KIỂM ĐỘC LẬP:
- Người lập phụ lục QA V1.7 & bàn giao hồ sơ V1.6 gốc: Phùng Tấn Minh (Thành viên B — Annotator B kiêm QA Lead & Nhóm trưởng).
- Người tiếp nhận lưu hồ sơ V1.6 & chuẩn bị mã migration/verifier mới: Nguyễn Thắng (Thành viên C — Data Pipeline & Thư ký).
- Người kiểm định trực tiếp gói dữ liệu thật V2 & phê duyệt phương án migration/phát hành: Lead D (Anh Tuấn).

3. AI ĐÃ DÙNG:
- AI hỗ trợ kiểm tra git diff giữa 33e8bb6 và b5b7db2, trích xuất nguyên vẹn raw log đã chạy tại 33e8bb6, phân tích cấu trúc lot_ledger.py và main_sampling.py để lập đặc tả kiểm thử fixture cho migration/verifier trong phụ lục V1.7.
- Không dùng AI cho dữ liệu hạn chế, quần thể thật, mapping thật, seed/salt thật, Blind View A hay nhãn nguồn.

4. ĐẦU VÀO ĐÃ KHÓA:
- Commit mã nguồn đã QA kỹ thuật: 33e8bb6c29c7ee15209ae5847d48aae973a3f536 (origin/feat/c-main-annotation-batch1).
- Commit cập nhật manifest hiện hành: b5b7db2900fefd142c211fb2045a3e2bf3272298 (origin/feat/c-main-annotation-batch1).
- Hồ sơ QA V1.6 gốc và Raw Log bàn giao nguyên byte:
  + docs/QA_REPORT_MAIN_BATCH1_33E8BB6_CONSOLIDATED_V1_6_B.md (37.162 bytes | SHA-256: bfeb73d97db47fdb6741ce47849254d4f3a9483120bd533a3cb0f357f8a41e09)
  + docs/QA_RAW_LOG_MAIN_BATCH1_33E8BB6_B.txt (10.920 bytes | SHA-256: 29b452ff6b2debfd2826d3ac3f15678a7f07aff3b45012e53ff3462c17c30ee7)
- Các nhận định về gói dữ liệu hạn chế thật V2 (hai view thật đã sửa sang envelope, cohort và thứ tự A100/B30 giữ nguyên; hồ sơ quần thể còn thiếu 1.232 metadata records; đầu vào/log kiểm loại trừ chưa đủ để D tái lập; phương án block kế nhiệm chưa khớp loader hiện hành và chưa được D duyệt áp dụng lên ledger thật) được ghi nhận rõ là kết quả do Lead D kiểm trực tiếp, không ghi thành B đã trực tiếp kiểm.

5. THAY ĐỔI THỰC TẾ:
- Trích xuất nguyên byte raw log đã chạy ở lượt 33e8bb6 thành tệp docs/QA_RAW_LOG_MAIN_BATCH1_33E8BB6_B.txt (10.920 bytes | SHA-256: 29b452ff...) để bàn giao cùng báo cáo V1.6 gốc cho C lưu trữ.
- Phát hành phụ lục docs/QA_ADDENDUM_MAIN_BATCH1_B5B7DB2_MIGRATION_VERIFIER_PENDING_V1_7_B.md (20.658 bytes | SHA-256: 3fecd1ef8f7cffd4a537ea45d4285c823eb0f557c9bd36f213779c0794e15007); không sửa bất kỳ tệp nào của C.

6. TỰ KIỂM:
- Đối chiếu git diff --stat 33e8bb6c29c7ee15209ae5847d48aae973a3f536 b5b7db2900fefd142c211fb2045a3e2bf3272298: xác nhận chỉ thay đổi đúng 1 tệp artifacts/main_batch1_release_manifest.json (1 file changed, 8 insertions(+), 7 deletions(-)), toàn bộ mã nguồn và test giữ nguyên byte.
- Kiểm tra bảo toàn nguyên byte toàn bộ các văn bản QA lịch sử của B (V1.6, V1.5, V1.4, V1.3, V1.2, V1.1, V1.0, Phụ lục 02fca4f).

7. KIỂM THỬ:
- Phần giữ nguyên từ QA V1.6 tại 33e8bb6c29c7ee15209ae5847d48aae973a3f536: Không chạy lại 154 phép kiểm chọn lọc (passed=154, failed=0, skipped=0, deselected=0 in 19.82s) và lượt chạy rộng (passed=421, failed=6, skipped=38, deselected=0, subtests passed=32 in 27.32s) do mã nguồn và bộ test tại b5b7db2 không đổi so với 33e8bb6.
- Phần kiểm mới cho Migration Ledger & Verifier Fingerprint: N/A (PENDING) tại thời điểm này do đang chờ Thành viên C bàn giao commit mã migration và verifier mới.

8. QA ĐỘC LẬP (THEO TỪNG PHẠM VI HIỆN HÀNH):
- Phạm vi 1 — Mã nguồn, SOP và fixture tổng hợp đã kiểm tại 33e8bb6 (giữ nguyên tại b5b7db2): PASS (154 passed trong 8 tệp chọn lọc).
- Phạm vi 2 — Phương án Migration Ledger trên fixture tổng hợp (Mục 3 chỉ đạo D): PENDING (Chờ C bàn giao mã migration đã chỉnh; khi kiểm sẽ tách rõ ca chẩn đoán tái lập lỗi block sparse khỏi ca chứng minh bản sửa đạt đủ 7 tiêu chí).
- Phạm vi 3 — Verifier Fingerprint trên fixture tổng hợp (Mục 4 chỉ đạo D): PENDING (Chờ C bàn giao mã verifier phân định rõ raw input và canonical metadata 8 trường, không băm HTML rỗng khi chỉ cung cấp html_sha256, báo rõ khi thiếu trường/sai hash và đối chiếu bằng phép tính độc lập trên fixture).
- Phạm vi 4 — Hiện vật hạn chế thật V2 & Áp dụng Migration lên Ledger thật: HOLD / PENDING (Do Lead D kiểm chứng trực tiếp và phê duyệt).

9. GIỚI HẠN VÀ VIỆC CÒN MỞ:
- Giới hạn: B giữ tính mù, không nhận hoặc mở quần thể thật, mapping thật, seed/salt thật, nhãn nguồn hay Blind View A.
- Việc còn mở:
  + Thành viên C lưu nguyên byte tệp báo cáo QA V1.6 gốc (docs/QA_REPORT_MAIN_BATCH1_33E8BB6_CONSOLIDATED_V1_6_B.md) và tệp raw log (docs/QA_RAW_LOG_MAIN_BATCH1_33E8BB6_B.txt).
  + Thành viên C hoàn thiện mã migration ledger và verifier fingerprint theo chỉ đạo của Lead D, đồng thời bổ sung đủ 1.232 metadata records và đầu vào/log kiểm loại trừ cho gói thật V2.
  + Ngay khi C bàn giao commit mã migration/verifier mới, B xác nhận full commit SHA, đọc diff và chạy bộ kiểm thử fixture để phát hành kết luận QA cho phần migration/verifier.

10. TRẠNG THÁI QUẢN TRỊ:
- Phạm vi mã nguồn, SOP và fixture tại 33e8bb6 (kế thừa tại b5b7db2): QA PASS.
- Phạm vi mã Migration Ledger & Verifier Fingerprint: PENDING.
- Gói dữ liệu Main Annotation Đợt 1: HOLD / LOCKED.
- Các cờ khóa quản trị hiện hành: main_annotation_status="LOCKED", training_blocked=true, official_test_used=false (QA đạt không tự cấp quyền migration thật hoặc mở Pass 1; các bước đó chờ quyết định riêng của Lead D).
========================================================================================
