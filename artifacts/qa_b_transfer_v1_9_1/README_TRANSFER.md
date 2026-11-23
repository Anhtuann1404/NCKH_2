# Bàn giao file QA gốc để C lưu

Bốn file trongdocs/khớp byte/hash B đã công bố. GiữV1.8FAIL vàV1.9bảncóerratalàm lịch sử;V1.9.1ghiđínhchính vàQAphạmvimã/fixture. C không sửa nội dungB hoặc ghi trước quyếtđịnhD.

Wrapper log5.823bytes được tái dựng từ bản dán thiếu LFcuối bằng thêm đúng1LF,đã khớp SHA B công bố. Đây không phải file rawtask-4524.log. XemTRANSFER_PROVENANCE.json. FileV1.9gốc dùngbản26.080bytes đãcó,không dùngbảndán mấtMarkdown24.087bytes.

C đối chiếu hash trước/sau lưu và Git,không đổi encoding/newline; nếu cófilecùngtên khácbyte thìbảolưuriêng vàđốisoát,khôngghiđèâmthầm. Đánhdấu file gốc/notice/erratađúngloại. Sourcecode/tests/data/ledger không được thay đổi do gói chuyểnfile này.

Hai ghi chú trìnhbày còn lại của errata được D ghi riêng ở báo cáo kiểm: mục5.2đãđổi%thànhpct nên gọi bản trích hiểnthị đãchuyểnđổi,khôngbyteoriginal; `_build_blind_record` khôngcótrongmain_sampling tạicommitđãkiểm,nênbỏtênhelperđó. B cóthểxácnhậnbằngnoteđínhchínhngắn;CkhôngsửathayB. Khôngcầnchạylại165test.

Chưa cóquyếtđịnhDápdụngledgerthật/phátview;MainLOCKED,training_blocked=true,official_test_used=false.
