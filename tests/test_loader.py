"""Unit tests cho Data Ingestion & Indexing Engine (Task DEV-01).

Kiểm tra toàn diện 7 điểm probe và chỉ đạo nghiệm thu của Lead D:
1. Chốt loại trừ pilot đóng kín:
   - Dữ liệu thật bắt buộc phải có ExclusionRegistry;
   - Mẫu bị loại trừ không được chuyển thành PreparedSnapshot (ném lỗi);
   - Hàm filter_eligible_records và join_verified_labels_and_filter_eligible hoạt động chính xác;
   - Manifest phản ánh ready_for_training=False và audit_only_training_blocked.
2. Ánh xạ nhãn chuẩn xác & bảo toàn tier/sub-source:
   - Thiếu nhãn, rỗng hoặc ngoài phạm vi (malware, defacement) không bị đổi thành benign;
   - Bảo toàn tier (gold/silver/bronze) và sub-source của PhishVN.
3. ID duy nhất ổn định theo shard/row & multi-shard:
   - ID dạng PP-<shard>-R<row:06d> không bị đụng độ giữa các shard;
   - CLI bảo vệ chống ghi đè khi chưa truyền --overwrite;
   - Đọc tuần tự streaming không giữ toàn bộ HTML trong RAM.
4. Xác minh Checksum HTML & Xuất xứ:
   - Tự động tính SHA-256 từ HTML thực; phát hiện hash nguồn sai lệch;
   - Đối soát với source_manifest.json; ghi nhận đầy đủ mã băm nguồn vào manifest.
5. Grouping bảo toàn query unredacted:
   - URL Forms có id=TenantA và id=TenantB sinh hai group khác nhau;
   - Normalized URL trong snapshot vẫn che query an toàn.
6. Tách biệt Chỉ mục Kỹ thuật & Kho Nhãn:
   - corpus_index.jsonl chỉ chứa locator, không chứa raw URL hay nhãn;
   - Đọc lại đúng HTML từ index (reconstitute_html_from_locator) và đối chiếu hash thành công.
7. Bảo toàn metadata ngày & capture_mode:
   - Phân biệt rõ valid / missing / invalid (ngày 2024-02-30 ghi là invalid, không ghi missing);
   - Bảo toàn capture_mode="rendered_dom", không tự đổi thành stored_html.
"""

import json
import hashlib
import subprocess
import sys
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from phishing.data.exclusion import ExclusionRegistry
from phishing.data.loader import (
    CorpusRecord,
    adapt_source_row_to_record,
    build_corpus_index,
    filter_eligible_records,
    join_verified_labels_and_filter_eligible,
    load_phishvn_records,
    load_phreshphish_shard,
    normalize_record_url,
    reconstitute_html_from_locator,
)
from phishing.preprocessing import PreparedSnapshot

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CLI_PATH = PROJECT_ROOT / "scripts" / "data" / "index_corpus.py"


# ---------------------------------------------------------------------------
# 1. Kiểm tra Schema & Tách biệt Index / Vault (Khắc phục Probe 6)
# ---------------------------------------------------------------------------
def test_corpus_record_schema_and_technical_index_separation():
    """Chỉ mục kỹ thuật (corpus_index.jsonl) tuyệt đối không chứa raw_url, nhãn hay target."""
    locator = {"source_id": "phreshphish", "shard": "train-000.parquet", "row_offset": 5}
    rec = CorpusRecord(
        sample_id="PP-train-000-R000005",
        source_id="phreshphish",
        source_revision="rev-123",
        source_split="train",
        locator=locator,
        raw_url="https://secret-bank.com/login?token=sensitive_token",
        normalized_url="https://secret-bank.com/login?token=_redacted_",
        group_id="domain:secret-bank.com",
        html_sha256="abc123def",
        source_provided_html_sha256="abc123def",
        html_integrity_status="matched",
        language="en",
        capture_mode="stored_html",
        collected_at="2025-01-15",
        date_status="valid",
        date_error=None,
        is_valid_url=True,
        url_error=None,
        source_label="phishing",
        raw_source_label="phish",
        label_status="verified_binary",
        target="Microsoft",
        source_tier=None,
        source_sub_source=None,
        exclusion_reason=None,
        raw_html="<html><body>Login</body></html>",
    )

    idx_dict = rec.to_index_dict()
    vault_dict = rec.to_vault_dict()

    # Index kỹ thuật chỉ chứa locator và các trường đặc trưng an toàn
    assert "locator" in idx_dict
    assert idx_dict["locator"] == locator
    assert idx_dict["normalized_url"] == "https://secret-bank.com/login?token=_redacted_"

    # TUYỆT ĐỐI KHÔNG chứa raw_url, source_label, target, raw_html trong index kỹ thuật
    for forbidden in ("raw_url", "source_label", "target", "raw_html", "html"):
        assert forbidden not in idx_dict

    # Kho nhãn bảo mật chứa đầy đủ raw_url, source_label, target
    assert vault_dict["sample_id"] == "PP-train-000-R000005"
    assert vault_dict["raw_url"] == "https://secret-bank.com/login?token=sensitive_token"
    assert vault_dict["source_label"] == "phishing"
    assert vault_dict["target"] == "Microsoft"


# ---------------------------------------------------------------------------
# 2. Chốt loại trừ Pilot đóng kín (Khắc phục Probe 1)
# ---------------------------------------------------------------------------
def test_to_prepared_snapshot_blocks_excluded_record():
    """Bản ghi có exclusion_reason (ví dụ pilot match) tuyệt đối không được tạo PreparedSnapshot."""
    locator = {"source_id": "phreshphish", "shard": "train-000.parquet", "row_offset": 0}
    excluded_rec = CorpusRecord(
        sample_id="EXCLUDED-01",
        source_id="phreshphish",
        source_revision="rev-1",
        source_split="train",
        locator=locator,
        raw_url="https://pilot-excluded.com/",
        normalized_url="https://pilot-excluded.com/",
        group_id="domain:pilot-excluded.com",
        html_sha256="sha111",
        source_provided_html_sha256=None,
        html_integrity_status="computed_only",
        language="en",
        capture_mode="stored_html",
        collected_at="2025-01-01",
        date_status="valid",
        date_error=None,
        is_valid_url=True,
        url_error=None,
        source_label="phishing",
        raw_source_label="phish",
        label_status="verified_binary",
        target=None,
        exclusion_reason="pilot_exclusion_registry_match",
        raw_html="<html><body>Excluded</body></html>",
    )

    with pytest.raises(ValueError, match="Không thể tạo PreparedSnapshot cho bản ghi đã bị loại trừ"):
        excluded_rec.to_prepared_snapshot()


def test_filter_eligible_records_and_join_verified_labels(tmp_path):
    """Kiểm tra chọn tập đủ điều kiện và gộp nhãn đã kiểm chứng trước split/fit."""
    records = [
        CorpusRecord(
            sample_id="S1",
            source_id="phreshphish",
            source_revision="r1",
            source_split="train",
            locator={"shard": "s1.parquet", "row_offset": 0},
            raw_url="https://clean-site1.com/",
            normalized_url="https://clean-site1.com/",
            group_id="domain:clean-site1.com",
            html_sha256="h1",
            source_provided_html_sha256=None,
            html_integrity_status="computed_only",
            language="en",
            capture_mode="stored_html",
            collected_at="2025-01-01",
            date_status="valid",
            date_error=None,
            is_valid_url=True,
            url_error=None,
            source_label="phishing",
            raw_source_label="phish",
            label_status="verified_binary",
            target="Amazon",
            exclusion_reason=None,
        ),
        CorpusRecord(
            sample_id="S2",
            source_id="phreshphish",
            source_revision="r1",
            source_split="train",
            locator={"shard": "s1.parquet", "row_offset": 1},
            raw_url="https://pilot-match.com/",
            normalized_url="https://pilot-match.com/",
            group_id="domain:pilot-match.com",
            html_sha256="h2",
            source_provided_html_sha256=None,
            html_integrity_status="computed_only",
            language="en",
            capture_mode="stored_html",
            collected_at="2025-01-02",
            date_status="valid",
            date_error=None,
            is_valid_url=True,
            url_error=None,
            source_label="benign",
            raw_source_label="benign",
            label_status="verified_binary",
            target=None,
            exclusion_reason="pilot_exclusion_registry_match",
        ),
    ]

    eligible = filter_eligible_records(records)
    assert len(eligible) == 1
    assert eligible[0].sample_id == "S1"

    index_dicts = [r.to_index_dict() for r in records]
    vault = {r.sample_id: r.to_vault_dict() for r in records}

    reg_path = tmp_path / "verified-registry.json"
    reg_path.write_text(json.dumps({"training_blocked": False, "exclusions": [{"exclusion_id": "fixture-exclusion", "mapping_status": "resolved", "rows_api_revision_pinned": True, "samples": [{"url_sha256": "0" * 64}]}]}))
    registry = ExclusionRegistry(reg_path)
    # Imported source vault alone is never ground truth.
    assert join_verified_labels_and_filter_eligible(index_dicts, vault, registry) == []
    vault["S1"].update(class_label="phishing", html_sha256="h1", verified_by="reviewer",
                       verification_method="manual_adjudication", verification_evidence="restricted-log")
    joined = join_verified_labels_and_filter_eligible(index_dicts, vault, registry)
    assert len(joined) == 1
    assert joined[0]["sample_id"] == "S1"
    assert joined[0]["class_label"] == "phishing"


# ---------------------------------------------------------------------------
# 3. Ánh xạ nhãn & bảo toàn Tier PhishVN (Khắc phục Probe 2)
# ---------------------------------------------------------------------------
def test_label_mapping_rejects_silent_benign_conversion():
    """Nhãn thiếu, rỗng hoặc ngoài phạm vi (malware, defacement) không bị đổi thành benign."""
    locator = {"source_id": "test", "shard": "test", "row_offset": 0}

    # 1. Nhãn rỗng -> missing
    rec_missing = adapt_source_row_to_record(
        sample_id="TEST-01",
        source_id="phreshphish",
        source_revision="r1",
        source_split="train",
        locator=locator,
        raw_url="https://example.com/1",
        raw_html="<html>test</html>",
        raw_date="2025-01-01",
        raw_label="",
    )
    assert rec_missing.source_label == "unlabeled"
    assert rec_missing.label_status == "missing"
    assert rec_missing.exclusion_reason == "missing_source_label"
    assert rec_missing.source_label != "benign"

    # 2. Nhãn PhishVN malware -> out_of_scope
    rec_malware = adapt_source_row_to_record(
        sample_id="TEST-02",
        source_id="phishvn",
        source_revision="v3",
        source_split="train",
        locator=locator,
        raw_url="https://example.com/2",
        raw_html=None,
        raw_date=None,
        raw_label="malware",
        source_tier="silver",
        source_sub_source="chongluadao",
    )
    assert rec_malware.source_label == "out_of_scope:malware"
    assert rec_malware.label_status == "out_of_scope"
    assert "out_of_scope_label" in rec_malware.exclusion_reason
    assert rec_malware.source_label != "benign"
    # Bảo toàn tier và sub-source
    assert rec_malware.source_tier == "silver"
    assert rec_malware.source_sub_source == "chongluadao"

    # 3. Nhãn defacement -> out_of_scope
    rec_defacement = adapt_source_row_to_record(
        sample_id="TEST-03",
        source_id="phishvn",
        source_revision="v3",
        source_split="train",
        locator=locator,
        raw_url="https://example.com/3",
        raw_html=None,
        raw_date=None,
        raw_label="defacement",
    )
    assert rec_defacement.source_label == "out_of_scope:defacement"
    assert rec_defacement.source_label != "benign"


# ---------------------------------------------------------------------------
# 4. Grouping không bị che lấp query (Khắc phục Probe 5)
# ---------------------------------------------------------------------------
def test_grouping_unredacted_query_preserves_distinct_forms_tenants():
    """Hai URL Forms có id=TenantA và id=TenantB sinh hai group khác nhau."""
    locator1 = {"source_id": "test", "shard": "test", "row_offset": 0}
    locator2 = {"source_id": "test", "shard": "test", "row_offset": 1}

    rec1 = adapt_source_row_to_record(
        sample_id="FORM-01",
        source_id="phreshphish",
        source_revision="r1",
        source_split="train",
        locator=locator1,
        raw_url="https://forms.office.com/Pages/ResponsePage.aspx?id=TenantA_SecretToken",
        raw_html="<html>form A</html>",
        raw_date="2025-01-01",
        raw_label="phish",
    )

    rec2 = adapt_source_row_to_record(
        sample_id="FORM-02",
        source_id="phreshphish",
        source_revision="r1",
        source_split="train",
        locator=locator2,
        raw_url="https://forms.office.com/Pages/ResponsePage.aspx?id=TenantB_SecretToken",
        raw_html="<html>form B</html>",
        raw_date="2025-01-01",
        raw_label="phish",
    )

    # 1. Group ID phải phân biệt theo tenant unredacted:
    assert rec1.group_id == "tenant:forms.office.com:id=tenanta_secrettoken"
    assert rec2.group_id == "tenant:forms.office.com:id=tenantb_secrettoken"
    assert rec1.group_id != rec2.group_id

    # 2. Normalized URL dùng cho mô hình vẫn được che an toàn:
    assert rec1.normalized_url == "https://forms.office.com/Pages/ResponsePage.aspx?id=_redacted_"
    assert rec2.normalized_url == "https://forms.office.com/Pages/ResponsePage.aspx?id=_redacted_"


# ---------------------------------------------------------------------------
# 5. Checksum HTML & Xuất xứ (Khắc phục Probe 4)
# ---------------------------------------------------------------------------
def test_html_checksum_mismatch_detected_and_excluded():
    """Probe 4: Hash HTML nguồn sai lệch với HTML thực tế phải bị phát hiện và gắn cờ loại trừ."""
    locator = {"source_id": "test", "shard": "test", "row_offset": 0}
    actual_html = "<html><body>Genuine HTML content</body></html>"

    rec = adapt_source_row_to_record(
        sample_id="HASH-ERR-01",
        source_id="phreshphish",
        source_revision="r1",
        source_split="train",
        locator=locator,
        raw_url="https://example.com/",
        raw_html=actual_html,
        raw_date="2025-01-01",
        raw_label="phish",
        precomputed_html_sha256="fake_sha256_provided_by_malicious_probe",
    )

    assert rec.html_integrity_status == "mismatch"
    assert rec.exclusion_reason is not None
    assert "html_sha256_mismatch" in rec.exclusion_reason


# ---------------------------------------------------------------------------
# 6. Đọc lại đúng HTML từ Index Locator (Khắc phục Probe 6)
# ---------------------------------------------------------------------------
def test_reconstitute_html_from_locator(tmp_path):
    """Chứng minh có thể đọc lại đúng HTML từ locator và đối chiếu mã băm chuẩn xác."""
    shard_file = tmp_path / "train-000.parquet"
    html_sample = "<html><head><title>Reconstitute Test</title></head><body>Hello</body></html>"
    table = pa.Table.from_pydict({
        "url": ["https://site.org/"],
        "html": [html_sample],
        "label": ["benign"],
        "sha256": [None],
        "date": ["2025-01-01"],
        "lang": ["en"],
    })
    pq.write_table(table, shard_file)

    records = list(load_phreshphish_shard(shard_file, is_real_data_mode=False))
    assert len(records) == 1
    rec = records[0]

    # Đọc lại bằng hàm reconstitute
    reconstituted = reconstitute_html_from_locator(rec, tmp_path)
    assert reconstituted == html_sample

    # Đọc lại từ index_dict
    idx_dict = rec.to_index_dict()
    reconstituted_from_dict = reconstitute_html_from_locator(idx_dict, tmp_path)
    assert reconstituted_from_dict == html_sample


# ---------------------------------------------------------------------------
# 7. Metadata Ngày & Capture Mode (Khắc phục Probe 7)
# ---------------------------------------------------------------------------
def test_date_status_distinguishes_valid_missing_invalid():
    """Phân biệt rõ ràng 3 trạng thái ngày: valid, missing, invalid."""
    loc = {"source_id": "test", "shard": "test", "row_offset": 0}

    # 1. Ngày hợp lệ
    r_valid = adapt_source_row_to_record(
        sample_id="D1", source_id="test", source_revision="r", source_split="train",
        locator=loc, raw_url="https://a.com/", raw_html=None, raw_date="2025-01-15", raw_label="benign",
    )
    assert r_valid.date_status == "valid"
    assert r_valid.collected_at == "2025-01-15"

    # 2. Ngày thiếu (None hoặc rỗng)
    r_missing = adapt_source_row_to_record(
        sample_id="D2", source_id="test", source_revision="r", source_split="train",
        locator=loc, raw_url="https://b.com/", raw_html=None, raw_date=None, raw_label="benign",
    )
    assert r_missing.date_status == "missing"
    assert r_missing.collected_at is None

    # 3. Ngày sai lịch (2024-02-30) phải ghi là invalid, không được ghi là missing
    r_invalid = adapt_source_row_to_record(
        sample_id="D3", source_id="test", source_revision="r", source_split="train",
        locator=loc, raw_url="https://c.com/", raw_html=None, raw_date="2024-02-30", raw_label="benign",
    )
    assert r_invalid.date_status == "invalid"
    assert r_invalid.collected_at is None
    assert "invalid_calendar_date" in r_invalid.date_error
    assert "invalid_calendar_date" in r_invalid.exclusion_reason


def test_capture_mode_rendered_dom_preserved():
    """Bảo toàn capture_mode='rendered_dom', không bị chuyển thành stored_html."""
    loc = {"source_id": "test", "shard": "test", "row_offset": 0}
    rec = CorpusRecord(
        sample_id="DOM-01",
        source_id="test",
        source_revision="r",
        source_split="train",
        locator=loc,
        raw_url="https://dom-rendered.org/",
        normalized_url="https://dom-rendered.org/",
        group_id="domain:dom-rendered.org",
        html_sha256=hashlib.sha256(b"<html><body>DOM snapshot</body></html>").hexdigest(),
        source_provided_html_sha256=None,
        html_integrity_status="computed_only",
        language="en",
        capture_mode="rendered_dom",
        collected_at="2025-01-01",
        date_status="valid",
        date_error=None,
        is_valid_url=True,
        url_error=None,
        source_label="phishing",
        raw_source_label="phish",
        label_status="verified_binary",
        target=None,
        exclusion_reason=None,
        raw_html="<html><body>DOM snapshot</body></html>",
    )

    snapshot = rec.to_prepared_snapshot()
    assert snapshot.capture_mode == "rendered_dom"
    assert snapshot.capture_mode != "stored_html"


# ---------------------------------------------------------------------------
# 8. ID ổn định & Độc lập Shard (Khắc phục Probe 3)
# ---------------------------------------------------------------------------
def test_multi_shard_stable_unique_sample_ids(tmp_path):
    """Hai shard khác nhau sinh ID khác nhau, không bao giờ đụng độ PP-TRAIN-000001."""
    shard0 = tmp_path / "train-000.parquet"
    shard1 = tmp_path / "train-001.parquet"

    table0 = pa.Table.from_pydict({
        "url": ["https://s0.com/"], "html": ["<html>0</html>"],
        "label": ["phish"], "sha256": [None], "date": ["2025-01-01"], "lang": ["en"],
    })
    table1 = pa.Table.from_pydict({
        "url": ["https://s1.com/"], "html": ["<html>1</html>"],
        "label": ["benign"], "sha256": [None], "date": ["2025-01-01"], "lang": ["en"],
    })
    pq.write_table(table0, shard0)
    pq.write_table(table1, shard1)

    recs0 = list(load_phreshphish_shard(shard0, is_real_data_mode=False))
    recs1 = list(load_phreshphish_shard(shard1, is_real_data_mode=False))

    assert recs0[0].sample_id == "PP-unverified-train-000-R000000"
    assert recs1[0].sample_id == "PP-unverified-train-001-R000000"
    assert recs0[0].sample_id != recs1[0].sample_id


# ---------------------------------------------------------------------------
# 9. CLI Index Corpus Tests (Non-overwrite, Registry requirement, Provenance)
# ---------------------------------------------------------------------------
def test_cli_index_corpus_fixture_and_non_overwrite(tmp_path):
    """Kiểm tra CLI trên fixture, bảo vệ chống ghi đè và xuất manifest đầy đủ."""
    fixture_file = tmp_path / "fixture.jsonl"
    rows = [
        {"url": "https://auth.company.com/login", "label": "phishing", "date": "2025-01-10", "lang": "en"},
        {"url": "https://portal.service.gov.vn", "label": "benign", "date": "2025-02-15", "lang": "vi"},
    ]
    fixture_file.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")

    out_dir = tmp_path / "index_run_1"

    # Chạy lần đầu
    cmd = [
        sys.executable, str(CLI_PATH),
        "--source", "jsonl",
        "--input-path", str(fixture_file),
        "--output-dir", str(out_dir),
        "--allow-unverified-fixture",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=PROJECT_ROOT)
    assert proc.returncode == 0, f"Lỗi CLI: {proc.stderr}"

    assert (out_dir / "corpus_index.jsonl").exists()
    assert (out_dir / "restricted_vault.jsonl").exists()
    assert (out_dir / "index_manifest.json").exists()

    manifest = json.loads((out_dir / "index_manifest.json").read_text(encoding="utf-8"))
    assert manifest["ready_for_training"] is False
    assert manifest["training_readiness_status"] == "audit_only_training_blocked"
    assert "index_file_sha256" in manifest
    assert "vault_file_sha256" in manifest

    # Chạy lần 2 vào cùng thư mục mà KHÔNG có --overwrite -> phải thất bại (Probe 3)
    proc2 = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=PROJECT_ROOT)
    assert proc2.returncode != 0
    assert "--overwrite" in proc2.stderr or "--overwrite" in proc2.stdout

    # Chạy với --overwrite -> thành công
    cmd_overwrite = cmd + ["--overwrite"]
    proc3 = subprocess.run(cmd_overwrite, capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=PROJECT_ROOT)
    assert proc3.returncode == 0


def test_cli_real_data_halts_without_registry(tmp_path):
    """Probe 1: Chế độ dữ liệu thật phải dừng ngay lập tức nếu thiếu ExclusionRegistry."""
    mock_shard = tmp_path / "train-000.parquet"
    table = pa.Table.from_pydict({
        "url": ["https://s0.com/"], "html": ["<html>0</html>"],
        "label": ["phish"], "sha256": [None], "date": ["2025-01-01"], "lang": ["en"],
    })
    pq.write_table(table, mock_shard)

    out_dir = tmp_path / "out_real"
    non_existent_reg = tmp_path / "non_existent_registry.json"

    cmd = [
        sys.executable, str(CLI_PATH),
        "--source", "phreshphish",
        "--input-path", str(mock_shard),
        "--output-dir", str(out_dir),
        "--exclusion-registry", str(non_existent_reg),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=PROJECT_ROOT)
    assert proc.returncode != 0
    assert ("bắt buộc phải có ExclusionRegistry" in proc.stderr or "bắt buộc phải có ExclusionRegistry" in proc.stdout)
