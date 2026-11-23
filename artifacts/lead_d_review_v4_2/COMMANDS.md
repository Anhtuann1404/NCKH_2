# Lệnh kiểm V4.2

Checkout `/private/tmp/nckh-main-ac2cf1d-review`, commitac2cf1d82d9a742ec0f5e9af81e0ce116fdfbe3d.

```sh
PYTHONPATH=.:src:/opt/homebrew/lib/python3.14/site-packages /Users/yingjunn_/.codex/worktrees/635d/NCKH_2/.venv/bin/python -m pytest tests/test_main_annotation_batch1.py tests/test_blind_view.py tests/test_annotate_cli_timer_pause.py tests/test_ledger_migration_proposal.py tests/test_isolation_scanner_regression.py tests/test_main_batch1_manifest_preflight.py /private/tmp/test_main_8fc_additional_guards.py /private/tmp/test_main_6c26_release_boundaries.py /private/tmp/test_main_599_followup.py /private/tmp/test_main_da3_intake_history.py /private/tmp/test_main_a12_approval_and_sop.py /private/tmp/test_main_v3_pure_fixture_migration.py /private/tmp/test_main_v41_fingerprint_integrity.py -q
PYTHONPATH=.:src:/opt/homebrew/lib/python3.14/site-packages /Users/yingjunn_/.codex/worktrees/635d/NCKH_2/.venv/bin/python scripts/data/verify_git_isolation.py
PYTHONPATH=.:src:/opt/homebrew/lib/python3.14/site-packages /Users/yingjunn_/.codex/worktrees/635d/NCKH_2/.venv/bin/python /private/tmp/audit_main_v42_metadata.py
```

Audit gói thật chỉ dành cho D/môi trường được phép; B chỉ dùng fixture. File audit hydrate từ shard đã đo hash ởSOURCE_VERIFIED.json và rehearsal trên COPY tạm. Không chạy script tạo gói có quyền ghi/xóa staging để thực hiện kiểm này.
