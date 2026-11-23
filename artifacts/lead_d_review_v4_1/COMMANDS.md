# Lệnh kiểm V4.1

Checkout chính: `/private/tmp/nckh-main-28462fc-review`, actual commit28462fcece5883a652779976e342d939f7a81e5a. Cần chạy trong checkout tương ứng; không dùng full SHA sai trong thông báo C.

```sh
PYTHONPATH=.:src:/opt/homebrew/lib/python3.14/site-packages /Users/yingjunn_/.codex/worktrees/635d/NCKH_2/.venv/bin/python -m pytest tests/test_main_annotation_batch1.py tests/test_blind_view.py tests/test_annotate_cli_timer_pause.py tests/test_ledger_migration_proposal.py tests/test_isolation_scanner_regression.py tests/test_main_batch1_manifest_preflight.py /private/tmp/test_main_8fc_additional_guards.py /private/tmp/test_main_6c26_release_boundaries.py /private/tmp/test_main_599_followup.py /private/tmp/test_main_da3_intake_history.py /private/tmp/test_main_a12_approval_and_sop.py /private/tmp/test_main_v3_pure_fixture_migration.py -q
PYTHONPATH=.:src:/opt/homebrew/lib/python3.14/site-packages /Users/yingjunn_/.codex/worktrees/635d/NCKH_2/.venv/bin/python -m pytest /private/tmp/test_main_v41_fingerprint_integrity.py -q --show-capture=no
PYTHONPATH=.:src:/opt/homebrew/lib/python3.14/site-packages /Users/yingjunn_/.codex/worktrees/635d/NCKH_2/.venv/bin/python scripts/data/verify_git_isolation.py
PYTHONPATH=.:src:/opt/homebrew/lib/python3.14/site-packages /Users/yingjunn_/.codex/worktrees/635d/NCKH_2/.venv/bin/python /private/tmp/audit_main_v41_metadata.py
```

Lệnh probe thứ hai được chạy lại trong checkout `/private/tmp/nckh-main-9367288-review` với cùng file probe nguyên byte để kiểm hồi quy. Audit gói thật chỉ dành cho D/môi trường được phép; B không nhận ledger hoặc view thật.
