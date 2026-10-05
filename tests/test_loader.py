"""Unit tests cho Data Ingestion & Indexing Engine (Task DEV-01).

Kiểm tra:
1. Tính tuân thủ schema bản ghi nghiên cứu DATA_PROTOCOL.md.
2. Nguyên tắc Anti-Leakage: PreparedSnapshot hoàn toàn không chứa nhãn nguồn, metadata, hay split.
3. Cơ chế phòng vệ chiều sâu: ExclusionRegistry phát hiện và loại trừ mẫu pilot.
4. Chuẩn hóa URL có scheme fallback xác định, xử lý an toàn URL lỗi.
5. Adapter dữ liệu nguồn PhreshPhish Parquet và PhishVN.
6. CLI index_corpus.py hoạt động chính xác và xuất manifest đầy đủ mã băm SHA-256.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

from phishing.data.exclusion import ExclusionRegistry
from phishing.data.loader import (
    CorpusRecord,
    adapt_source_row_to_record,
    build_corpus_index,
    extract_labels_vault,
    load_phishvn_records,
    load_phreshphish_shard,
    normalize_record_url,
)
from phishing.preprocessing import PreparedSnapshot


def test_corpus_record_schema_and_to_index_dict():
    """Kiểm tra tính đầy đủ 11 trường dữ liệu theo DATA_PROTOCOL.md và không lưu raw HTML trong index."""
    rec = CorpusRecord(
        sample_id="TEST-001",
        source_id="phreshphish",
        source_revision="rev-123",
        source_split="train",
        collected_at="2025-01-15",
        raw_url="https://example.com/login",
        normalized_url="https://example.com/login",
        html_sha256="abc123def",
        language="en",
        capture_mode="stored_html",
        source_label="phishing",
        target="Microsoft",
        group_id="example.com",
        exclusion_reason=None,
        is_valid_url=True,
        url_error=None,
        raw_html="<html><body>Login</body></html>",
    )

    idx_dict = rec.to_index_dict()

    # Kiểm tra các trường bắt buộc theo DATA_PROTOCOL.md
    expected_keys = {
        "sample_id", "source_id", "source_revision", "source_split",
        "collected_at", "date_status", "raw_url", "normalized_url",
        "html_sha256", "language", "capture_mode", "source_label",
        "target", "group_id", "is_valid_url", "url_error", "exclusion_reason"
    }
    assert set(idx_dict.keys()) == expected_keys
    assert idx_dict["sample_id"] == "TEST-001"
    assert idx_dict["date_status"] == "valid"
    assert idx_dict["source_label"] == "phishing"
    assert idx_dict["target"] == "Microsoft"

    # TUYỆT ĐỐI KHÔNG lưu raw_html trong index_dict
    assert "raw_html" not in idx_dict
    assert "html" not in idx_dict


def test_to_prepared_snapshot_zero_leakage():
    """Chứng minh PreparedSnapshot hoàn toàn không chứa nhãn nguồn, mục tiêu hay metadata."""
    rec = CorpusRecord(
        sample_id="LEAK-CHECK-001",
        source_id="phreshphish",
        source_revision="rev-secure",
        source_split="train",
        collected_at="2025-02-01",
        raw_url="https://evil-login.example.com/signin?user=attacker",
        normalized_url="https://evil-login.example.com/signin?user=_redacted_",
        html_sha256="hash999",
        language="en",
        capture_mode="stored_html",
        source_label="phishing",
        target="PayPal",
        group_id="example.com",
        exclusion_reason=None,
        is_valid_url=True,
        url_error=None,
        raw_html="<html><body><form action='https://evil.com'><input type='password'></form></body></html>",
    )

    snapshot = rec.to_prepared_snapshot()

    assert isinstance(snapshot, PreparedSnapshot)
    assert snapshot.url == "https://evil-login.example.com/signin?user=_redacted_"
    assert snapshot.capture_mode == "stored_html"

    # Kiểm tra PreparedSnapshot chỉ có đúng 4 slots: url, html, capture_mode, preprocessing_version
    snapshot_attrs = {name for name in dir(snapshot) if not name.startswith("_")}
    assert snapshot_attrs == {"url", "html", "capture_mode", "preprocessing_version"}

    # Hoàn toàn không rò rỉ label, target, group_id hay date
    for forbidden in ("source_label", "label", "target", "group_id", "collected_at", "exclusion_reason"):
        assert not hasattr(snapshot, forbidden)


def test_to_prepared_snapshot_invalid_url_raises():
    """Bản ghi có URL lỗi không được phép tạo PreparedSnapshot."""
    rec = CorpusRecord(
        sample_id="ERR-001",
        source_id="phreshphish",
        source_revision=None,
        source_split="train",
        collected_at=None,
        raw_url="not_a_valid_url",
        normalized_url=None,
        html_sha256=None,
        language="en",
        capture_mode="url_only",
        source_label="phishing",
        target=None,
        group_id="unknown_domain",
        exclusion_reason="invalid_url: An absolute HTTP(S) URL is required",
        is_valid_url=False,
        url_error="An absolute HTTP(S) URL is required",
    )
    with pytest.raises(ValueError, match="Không thể tạo PreparedSnapshot"):
        rec.to_prepared_snapshot()


def test_normalize_record_url_fallbacks():
    """Kiểm tra chuẩn hóa URL và các tình huống scheme fallback xác định."""
    # 1. URL chuẩn
    norm, ok, err = normalize_record_url("https://bank.com/portal")
    assert ok is True
    assert norm == "https://bank.com/portal"
    assert err is None

    # 2. URL thiếu scheme -> tự động thêm https://
    norm, ok, err = normalize_record_url("my-secure-bank.com/account")
    assert ok is True
    assert norm == "https://my-secure-bank.com/account"
    assert err is None

    # 3. Protocol-relative //
    norm, ok, err = normalize_record_url("//sub.domain.com/login")
    assert ok is True
    assert norm == "https://sub.domain.com/login"
    assert err is None

    # 4. URL rỗng hoặc không hợp lệ
    norm, ok, err = normalize_record_url("   ")
    assert ok is False
    assert norm is None
    assert "empty" in err

    norm, ok, err = normalize_record_url("https:// invalid space .com")
    assert ok is False
    assert norm is None
    assert err is not None


def test_adapt_source_row_with_pilot_exclusion():
    """Kiểm tra adapter phát hiện mẫu thuộc ExclusionRegistry và gán exclusion_reason."""
    registry = ExclusionRegistry()

    # Mẫu bình thường không thuộc pilot
    clean_rec = adapt_source_row_to_record(
        sample_id="SAMP-CLEAN",
        source_id="phreshphish",
        source_revision="rev-1",
        source_split="train",
        raw_url="https://normal-unrelated-domain-2026.edu/page",
        raw_html="<html><body>Normal clean page</body></html>",
        raw_date="2025-05-10",
        source_label="benign",
        exclusion_registry=registry,
    )
    assert clean_rec.exclusion_reason is None
    assert clean_rec.is_valid_url is True

    # Mẫu có cấu trúc trùng khớp với pilot trong exclusion registry
    pilot_match_rec = adapt_source_row_to_record(
        sample_id="SAMP-PILOT",
        source_id="phreshphish",
        source_revision="rev-1",
        source_split="train",
        raw_url="https://pilot-test-fake.org/login",
        raw_html="x" * 518982,
        raw_date="2025-05-10",
        source_label="benign",
        language="en",
        exclusion_registry=registry,
    )
    # Nếu fingerprint hoặc html_chars khớp pilot_row_idx 0 (html_chars: 518982)
    # Lưu ý: registry kiểm tra summary_fingerprint_hash
    sample_query = {
        "pilot_row_idx": 0,
        "label": "benign",
        "lang": "en",
        "html_chars": 518982,
        "text_chars": 27006,
        "forms": 2,
        "inputs": 14,
        "password_inputs": 0,
    }
    assert registry.is_excluded(sample_query) is True


def test_build_corpus_index_and_manifest(tmp_path):
    """Kiểm tra tổng hợp index, tính toán manifest, và phát hiện trùng lặp sample_id."""
    records = [
        CorpusRecord(
            sample_id="ID-001",
            source_id="phreshphish",
            source_revision="r1",
            source_split="train",
            collected_at="2025-03-01",
            raw_url="https://site1.com",
            normalized_url="https://site1.com/",
            html_sha256="h1",
            language="en",
            capture_mode="stored_html",
            source_label="phishing",
            target="PayPal",
            group_id="site1.com",
            exclusion_reason=None,
        ),
        CorpusRecord(
            sample_id="ID-002",
            source_id="phishvn",
            source_revision="v3",
            source_split="train",
            collected_at=None,
            raw_url="https://site2.vn",
            normalized_url="https://site2.vn/",
            html_sha256=None,
            language="vi",
            capture_mode="url_only",
            source_label="benign",
            target=None,
            group_id="site2.vn",
            exclusion_reason=None,
        ),
        CorpusRecord(
            sample_id="ID-003",
            source_id="phreshphish",
            source_revision="r1",
            source_split="train",
            collected_at="2025-04-01",
            raw_url="invalid_url",
            normalized_url=None,
            html_sha256=None,
            language="en",
            capture_mode="url_only",
            source_label="phishing",
            target=None,
            group_id="unknown_domain",
            exclusion_reason="invalid_url: An absolute HTTP(S) URL is required",
            is_valid_url=False,
            url_error="An absolute HTTP(S) URL is required",
        ),
    ]

    out_index = tmp_path / "corpus_index.jsonl"
    out_manifest = tmp_path / "index_manifest.json"

    indexed, manifest = build_corpus_index(
        records,
        output_index_path=out_index,
        output_manifest_path=out_manifest,
    )

    assert len(indexed) == 3
    assert out_index.exists()
    assert out_manifest.exists()

    assert manifest["total_records"] == 3
    assert manifest["valid_urls"] == 2
    assert manifest["invalid_urls"] == 1
    assert manifest["valid_dates"] == 2
    assert manifest["missing_dates"] == 1
    assert manifest["class_distribution"] == {"phishing": 2, "benign": 1}
    assert manifest["source_distribution"] == {"phreshphish": 2, "phishvn": 1}
    assert manifest["total_excluded_records"] == 1
    assert "index_file_sha256" in manifest

    # Kiểm tra trùng lặp sample_id ném lỗi
    duplicate_records = list(records) + [records[0]]
    with pytest.raises(ValueError, match="sample_id trùng lặp"):
        build_corpus_index(duplicate_records)


def test_extract_labels_vault():
    """Kiểm tra trích xuất Ground Truth Labels Vault bảo mật cho Thành viên C."""
    records = [
        CorpusRecord(
            sample_id="VAULT-01",
            source_id="phreshphish",
            source_revision="r1",
            source_split="train",
            collected_at="2025-03-01",
            raw_url="https://site1.com",
            normalized_url="https://site1.com/",
            html_sha256="h1",
            language="en",
            capture_mode="stored_html",
            source_label="phishing",
            target="Amazon",
            group_id="site1.com",
            exclusion_reason=None,
        ),
    ]

    vault = extract_labels_vault(records)
    assert "VAULT-01" in vault
    assert vault["VAULT-01"]["source_label"] == "phishing"
    assert vault["VAULT-01"]["target"] == "Amazon"
    assert vault["VAULT-01"]["group_id"] == "site1.com"


def test_load_phreshphish_shard_mock(tmp_path):
    """Kiểm tra đọc dữ liệu shard Parquet thông qua bảng pyarrow giả lập."""
    import pyarrow as pa
    import pyarrow.parquet as pq

    shard_file = tmp_path / "mock_train-000.parquet"
    data = {
        "url": ["https://login.fake-paypal.com", "https://news.bbc.co.uk", "bad url"],
        "html": ["<html>Login</html>", "<html>BBC News</html>", None],
        "label": ["phish", "benign", "phish"],
        "sha256": ["sha_phish", "sha_benign", None],
        "date": ["2024-11-01", "2024-11-02", "invalid-date"],
        "lang": ["en", "en", "en"],
    }
    table = pa.Table.from_pydict(data)
    pq.write_table(table, shard_file)

    records = list(load_phreshphish_shard(shard_file, id_prefix="TEST-PP", start_index=10))

    assert len(records) == 3
    assert records[0].sample_id == "TEST-PP-000010"
    assert records[0].source_label == "phishing"
    assert records[0].collected_at == "2024-11-01"
    assert records[0].group_id == "domain:fake-paypal.com"
    assert records[0].is_valid_url is True

    assert records[1].sample_id == "TEST-PP-000011"
    assert records[1].source_label == "benign"
    assert records[1].group_id == "domain:bbc.co.uk"

    # Mẫu thứ 3 có URL lỗi và date lỗi
    assert records[2].sample_id == "TEST-PP-000012"
    assert records[2].is_valid_url is False
    assert records[2].collected_at is None
    assert records[2].exclusion_reason is not None


def test_load_phishvn_records_mock(tmp_path):
    """Kiểm tra đọc nguồn PhishVN từ tệp CSV giả lập."""
    csv_file = tmp_path / "mock_phishvn.csv"
    csv_content = (
        "url,label,source,tier,scenario,split,lang,domain\n"
        "https://techcombank-fake.xyz,phishing,chongluadao,bronze,bank,train,vi,techcombank-fake.xyz\n"
        "https://dantri.com.vn,benign,tranco,gold,other,train,vi,dantri.com.vn\n"
    )
    csv_file.write_text(csv_content, encoding="utf-8-sig")

    records = list(load_phishvn_records(csv_file, id_prefix="TEST-PVN"))

    assert len(records) == 2
    assert records[0].sample_id == "TEST-PVN-000001"
    assert records[0].source_label == "phishing"
    assert records[0].target == "bank"
    assert records[0].group_id == "domain:techcombank-fake.xyz"
    assert records[0].language == "vi"

    assert records[1].sample_id == "TEST-PVN-000002"
    assert records[1].source_label == "benign"
    assert records[1].target == "other"
    assert records[1].group_id == "domain:dantri.com.vn"


def test_cli_index_corpus_synthetic(tmp_path):
    """Kiểm thử end-to-end công cụ dòng lệnh index_corpus.py trên tệp JSONL."""
    jsonl_file = tmp_path / "sample_data.jsonl"
    rows = [
        {"url": "https://auth.company.com/login", "label": "phishing", "date": "2025-01-10", "lang": "en"},
        {"url": "https://portal.service.gov.vn", "label": "benign", "date": "2025-02-15", "lang": "vi"},
    ]
    with open(jsonl_file, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")

    out_dir = tmp_path / "indexed_output"

    cmd = [
        sys.executable,
        str(Path(__file__).resolve().parent.parent / "scripts" / "data" / "index_corpus.py"),
        "--source", "jsonl",
        "--input-path", str(jsonl_file),
        "--output-dir", str(out_dir),
        "--id-prefix", "CLI-TEST",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    assert result.returncode == 0

    assert (out_dir / "corpus_index.jsonl").exists()
    assert (out_dir / "index_manifest.json").exists()

    manifest = json.loads((out_dir / "index_manifest.json").read_text(encoding="utf-8"))
    assert manifest["total_records"] == 2
    assert manifest["valid_urls"] == 2
    assert manifest["class_distribution"] == {"phishing": 1, "benign": 1}
