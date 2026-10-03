# Phân công và quyền sở hữu công việc — 4 người

Cập nhật 04/10/2026. D là người dùng/chủ nhiệm đã nhận lead, mô hình và API–extension. A/B/C chưa chốt họ tên. Phân công này cụ thể hóa triển khai trong hướng đề cương đã duyệt; không thay RQ hoặc giao thức nghiên cứu.

“Owner” là người chịu trách nhiệm hoàn thành, giải thích quyết định, lưu bằng chứng và bàn giao phần việc; không có nghĩa chỉ người đó được sửa code. Reviewer kiểm độc lập trước bàn giao. File code bên dưới là vị trí dự kiến khi scaffold, chưa phải module đã có.

## A — Owner nhãn và bằng chứng nội dung

**Trách nhiệm:** gán nhãn tổ chức cho toàn bộ phishing giữ lại; ghi tên dịch vụ, mục tiêu, vai trò, bằng chứng và thời gian; kiểm hard benign; viết phần mô tả nhãn/phân tích nội dung cho báo cáo. A/B dùng codebook chung, không nhìn target nguồn hoặc prediction trong lượt nhãn độc lập.

**Sở hữu:** lượt annotation A, ghi chú bằng chứng, danh sách ca khó, thống kê công sức A; `data/annotations/A/` và tài liệu nhãn. Đầu vào là view mù do C cung cấp. Không tự sửa nhãn của B hoặc dictionary từ kết quả mô hình.

**Bàn giao:** nhãn A đủ phần đã chọn, evidence/unknown rõ, ca khó chuyển kiểm tra, log thời gian; B review và nhóm phân xử trước khóa nhãn cuối. A chịu trách nhiệm sự đầy đủ của bộ nhãn cuối, giữ lịch sử A/B/phân xử; không một mình tự quyết các bất đồng.

**Mức giờ tham chiếu:** 15–25 giờ/tuần trong đợt gán nhãn nếu giữ 2.000 mẫu; đo lại bằng pilot và ngân sách thực có.

## B — Owner kiểm nhãn độc lập và QA

**Trách nhiệm:** kiểm 30% random cùng ca khó; ghi lượt riêng trước xem A; cùng phân xử. Sau khóa nhãn, chạy lại cấu hình D đã bàn giao, kiểm bảng/counts và kiểm thử extension bằng fixture/kịch bản; không dùng prediction để sửa lượt nhãn cũ.

**Sở hữu:** annotation B, biên bản QA, kiểm counts/đồng thuận, báo cáo tái lập và lỗi demo; `data/annotations/B/`, `tests/` và báo cáo QA dự kiến. Công cụ tính kappa do C chuẩn bị, B kiểm đúng subset trước phân xử.

**Bàn giao:** mẫu random đủ, ca khó thêm được tách, bất đồng có lý do; sau thực nghiệm có kết quả chạy lại theo hướng dẫn hoặc danh sách lỗi có thể tái hiện. A review quy tắc nhãn, C hỗ trợ dữ liệu, D sửa lỗi mô hình/API/extension.

**Mức giờ tham chiếu:** 5–10 giờ/tuần đợt nhãn; đợt QA sau đó dự trù 4–6 giờ/tuần. Lịch thay đổi theo pilot.

## C — Owner nguồn, pipeline dữ liệu và view mù

**Trách nhiệm:** khóa revision/checksum, kiểm riêng date, quản lý quyền nguồn, dictionary/codebook từ nguồn ngoài, xuất view mù; lấy mẫu kiểm chéo trước kết quả; chuẩn hóa index, QC, nhóm miền/trùng và tạo split theo protocol. C là người khác A/B và không tiết lộ label/target/score/nhãn người kia trong lượt độc lập.

**Sở hữu:** manifest nguồn, dictionary/codebook version, blind export, sampling/group/split manifests, công cụ gán nhãn/đồng thuận; `scripts/data/`, `src/phishing/data/`, `src/phishing/annotation/`, `configs/` phần dữ liệu và dữ liệu hạn chế. C không là owner huấn luyện model.

**Bàn giao cho D:** index, labels cuối đã phân xử, dictionary, preprocessing interface, group/splits, checksum và QC/coverage/exclusion report. A/B kiểm chất lượng/đồng thuận; D kiểm split và hợp đồng trước training. Nếu split thay đổi vì sửa lỗi, C tạo version mới và báo D, không overwrite bằng chứng run.

**Mức giờ tham chiếu:** 8–12 giờ/tuần tập trung T1–T2, còn hỗ trợ dữ liệu/tái lập về sau.

## D — Cậu: lead và owner model, API, extension

**Lead:** điều phối nhiệm vụ/phụ thuộc, tổng hợp báo cáo, review tích hợp, quản lý version/release và trao đổi với GVHD. Mỗi người vẫn viết và kiểm phần mình; lead không làm thay toàn bộ báo cáo.

**Model — chính D xây dựng và huấn luyện:** đặc tả preprocessing/features; code M0–M3 và B-rule; TF-IDF/Logistic Regression, nhánh LightGBM; train, chọn tham số/ngưỡng trong train/validation; chạy grouped CV, ablation, thời gian và test độc lập theo protocol; giải thích metrics/CI và xuất bundle. B chạy lại/QA sau khóa, C hỗ trợ dữ liệu; hai bạn đó không thay owner model.

**API–extension:** xây serving từ bundle, endpoint theo API_SPEC, extension snapshot/cảnh báo; xử lý version/timeout/navigation và đo p50/p95. B hỗ trợ kiểm thử, C kiểm đầu vào/phiên bản.

**Sở hữu:** `src/phishing/preprocessing/`, `features/`, `training/`, `evaluation/`, `serving/`; `extension/`; run/model manifests, configs phần model, API contract và tài liệu kỹ thuật. D kiểm tra bundle/version, không chỉnh test labels/dictionary sau xem kết quả để tăng hiệu năng.

**Bàn giao:** cấu hình/lệnh chạy thật + environment lock, OOF/temporal results và giới hạn, model bundle + checksums/ngưỡng, API–extension demo và hướng dẫn đo/tái lập. B review tái lập/chức năng; C review tính tách dữ liệu; GVHD hỗ trợ diễn giải nghiên cứu.

**Mức giờ:** cần chốt ngân sách riêng; phần mô hình và API–extension trước đây được dự trù tổng 16–24 giờ/tuần khi chồng lịch, chưa tính lead. Ưu tiên model T2–T4, tích hợp thật T4–T5; khung mock có thể làm sớm. Không coi kiêm nhiệm là đủ thời gian mặc định.

## Ranh giới bàn giao

1. C chuẩn bị nguồn/view → A/B gán độc lập → A/B phân xử, C lưu nhãn/version.
2. C bàn giao dataset/dictionary/groups/splits khóa → D xây dựng và huấn luyện model.
3. D bàn giao run/config cho B chạy lại; C kiểm split/hash. Không dùng official test cho debug/tuning.
4. D xuất bundle → API → extension; B kiểm kịch bản và lỗi, C kiểm phiên bản/đầu vào.
5. Mỗi người viết phần sở hữu, D tổng hợp, cả nhóm và GVHD rà báo cáo.

Nếu có thêm người, phân hỗ trợ cho owner hiện tại theo task; vẫn giữ một owner rõ cho mỗi output. Họ tên và giờ tuần điền trong CURRENT_TASKS. Các mốc giờ là dự trù lập kế hoạch, không bảo đảm hoặc kết quả đã đo.
