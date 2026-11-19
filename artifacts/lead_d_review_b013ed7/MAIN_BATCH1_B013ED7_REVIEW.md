# Kiểm độc lập bàn giao Main Batch1 b013ed7

1. Mục tiêu: kiểm sản phẩm C trước phát hành A/B; không sửa mã C hoặc mở annotation.
2. Người thực hiện: Codex hỗ trợ Lead D, không thay QA độc lập B hoặc phán quyết D.
3. AI: đọc mã công khai, chạy fixture nhân tạo; không dùng AI gán nhãn mẫu thật. Không nhận Blind View/mapping hạn chế mới từ C để kiểm byte.
4. Đầu vào: Git commit b013ed726b8d694679ca7447adbd3d64f0f97bca, checkout riêng có metadata Git tại /private/tmp/nckh-main-b013-gitreview. Interpreter635dvenv Python3.14.6/pytest7.4; thêmsite-packageslocal cho phụ thuộc. Không chỉnh src/tests tracked. Seed/salt vận hành đã được C ghi trong source công khai; không chép giá trị vào báo cáo này.
5. Thực hiện: đọc sampler,ledger,exporter,verifier,BlindView,CLI và SOP; chạy3suitevà5probe hành vi.
6. Kết quả probe đã đo:
- Main sample BLIND không có blind_contract_version vẫn được assert_no_label_leak nhận: thiếu fail-closed Main/legacy phân biệt.
- Giữ candidate_uid,đổiHTML thì compute_population_fingerprint trả cùng hash. Fingerprint hiện chỉsealUIDsort,khôngsealnộidung/order/source.
- Filelistđúngcấutrúc samplerxuất đưa vàoCLI thật (fixture,stdinđóng):exit1/AttributeError:list has no attribute get. CLIexpectsobject.samples,export writesbarelist.
- Cùngpool120fixture,cùngseed,ledgerchung,2lotkhác:100IDtrùngnhauđượcRESERVEDlần2. Samplerkhônglọc/rejectallocated_ids.
- Public defaultseeds+salt tính ra đúngseed_commitment trongpublicrelease: camkết khôngcònbímật. VerifiervẫnbáoPASSvàquét68docs/configs;khôngkiểmseed/salttrongsrc/scripts.
7. Test: tests/test_main_annotation_batch1.py + tests/test_blind_view.py + tests/test_annotate_cli_timer_pause.py:74passed/35failed in1.08s.9testmớikhôngfail;35faillegacyhầuhếtdođưarandom_subsetvàoFORBIDDEN_LEAK_KEYSglobal. Chạybanđầutrongarchivekhông.gitthìtestGitfailvìthiếurepometadata;khôngdùngkếtquảnàyđểkếtluậnlỗimã. KếtquảchínhởcheckoutGitđúngcommit. Khôngchạylạifullrepo/chưaphụthuộcthật2góirestricted.
8. QA khuyến nghị: HOLDpháthành. 9tests khôngkiểmCLI/intake/chínhsáchlegacyend-to-end;chưacótệpinputgóithậtđểđốisoáthashCôngbố.
9. Việc cầnC xửlý: versionedCLI/load/record/validator1.2;giữlegacyquaallowlisthashđúngloại;regressionlegacy;seed/saltprivateinputkhôngdefaults+ghiincidentphạmvingườinhận;poolsealURLraw/normalizedhash+HTMLhash+source/revision/shard/row/order+configs;mappingcầnsample_content_hash/provenanceđểSOPthựcthi;ledgerchặntrùng,ghiatomicvàcommitđượcchứngthựctrướcsampling. ExportverifierFAILphảichặnpháthành,khôngtrảSUCCESSsaukhighiđègói. Khoárole-specificmanifestdùngCLIđược. Khôngtựđổitập100đểchọnkếtquảthuậnlợi;Dduyệtcáchxửlýseedđãlộvàcácgóichuẩnbị,cólineage/REVOKEDcầnthiết. Khônggọirònhãnnguồnkhibằngchứngchỉlộseed/salt.
10. Quảntrị:MainLOCKED,trainingblockedtrue,officialtestfalse. ChưaA/BPass1,chưaphátview. Đây là lỗi triển khai phát hiện trước release, không phủ nhận kiểmnguồnđãtáilập.

Lệnh chính:
PYTHONPATH=src:/opt/homebrew/lib/python3.14/site-packages /Users/yingjunn_/.codex/worktrees/635d/NCKH_2/.venv/bin/python -m pytest tests/test_main_annotation_batch1.py tests/test_blind_view.py tests/test_annotate_cli_timer_pause.py -q
