"""Bộ kiểm thử đơn vị & tích hợp toàn diện cho quy trình Main Annotation Đợt 1.

Kiểm tra nghiêm ngặt theo 6 chỉ đạo của Lead D:
1. Định dạng Blind ID trung tính: BLIND-xxxxxxxx (8 hex), không chứa số lô, nhãn, nhóm.
2. Tính xác định và chống trùng lặp (deterministic & no duplicates):
   - Cùng seed sinh kết quả giống hệt.
   - 100 mẫu Main không có trùng lặp.
   - 30 mẫu của B là tập con thực sự của 100 mẫu Main và dùng chung blind_id.
3. Xáo trộn thứ tự phát hành độc lập cho A và B.
4. Hợp đồng Blind View v1.2.0:
   - Allowlist chuẩn hóa, giữ nguyên URL quan sát được.
   - Chặn tuyệt đối: source_label, locator, parquet_file, source_row, model_score, random_subset.
5. Sổ quản lý lô (LotManagementLedger):
   - Chuỗi băm SHA-256 bảo vệ toàn vẹn (hash chaining).
   - Phát hiện can thiệp lịch sử (tamper-evident).
   - Truy vết các candidate_id đã phân bổ.
6. Cách ly Git thực tế (Git Isolation):
   - Không có tệp restricted nào bị Git theo dõi.
"""

import copy
import hashlib
import json
from pathlib import Path
import pytest

from phishing.annotation.blind_view import (
    BLIND_CONTRACT_VERSION_V1_2_0,
    assert_no_label_leak,
)
from phishing.data.lot_ledger import (
    LedgerEvent,
    LedgerIntegrityError,
    LotManagementLedger,
)
from phishing.data.main_sampling import (
    compute_population_fingerprint,
    compute_seed_commitment,
    generate_blind_id,
    run_main_batch1_sampling,
)
from scripts.data.verify_git_isolation import verify_git_isolation


@pytest.fixture
def dummy_candidates_150():
    """Tạo fixture 150 ứng viên giả lập hợp lệ để kiểm thử quy trình sampling."""
    candidates = []
    for i in range(150):
        url = f"https://service-{i:03d}.example.org/login"
        html = f"<html><head><title>Page {i}</title></head><body><h1>Login Form {i}</h1><form action='/auth'><input type='password' name='p'/><button>Sign In</button></form></body></html>"
        candidates.append({
            "candidate_uid": f"cand_{i:04d}",
            "url": url,
            "html": html,
            "source_label": "phish" if i % 2 == 0 else "benign",
            "source_shard": "train-001.parquet",
            "source_row": i * 10,
        })
    return candidates


def test_generate_blind_id_format_and_determinism():
    """Kiểm tra blind_id tuân thủ BLIND-xxxxxxxx (8 hex) và có tính xác định."""
    salt = "test_salt_secret_123"
    uid = "cand_0042"
    b_id1 = generate_blind_id(salt, uid)
    b_id2 = generate_blind_id(salt, uid)

    assert b_id1 == b_id2
    assert b_id1.startswith("BLIND-")
    assert len(b_id1) == 14  # 'BLIND-' (6) + 8 hex = 14 chars
    hex_part = b_id1.replace("BLIND-", "")
    assert all(c in "0123456789abcdef" for c in hex_part)

    # Đảm bảo UID khác sinh ID khác
    b_id3 = generate_blind_id(salt, "cand_0043")
    assert b_id1 != b_id3


def test_blind_id_has_no_lot_or_label_leakage():
    """Kiểm tra ID trung tính tuyệt đối không chứa số lô (MAIN-01) hay nhãn."""
    salt = "salt_check"
    for i in range(50):
        bid = generate_blind_id(salt, f"sample_{i}")
        assert "main" not in bid.lower()
        assert "lot" not in bid.lower()
        assert "phish" not in bid.lower()
        assert "benign" not in bid.lower()


def test_main_batch1_sampling_determinism(dummy_candidates_150, tmp_path):
    """Kiểm tra quy trình rút mẫu xác định hoàn toàn với cùng bộ seed."""
    ledger_path1 = tmp_path / "ledger1.json"
    ledger1 = LotManagementLedger(ledger_path1)

    res1 = run_main_batch1_sampling(
        dummy_candidates_150,
        seed_lot_100=1017,
        seed_b_subset_30=2042,
        seed_release_shuffle=2026,
        blind_salt="salt_test_1",
        ledger=ledger1,
    )

    ledger_path2 = tmp_path / "ledger2.json"
    ledger2 = LotManagementLedger(ledger_path2)

    res2 = run_main_batch1_sampling(
        dummy_candidates_150,
        seed_lot_100=1017,
        seed_b_subset_30=2042,
        seed_release_shuffle=2026,
        blind_salt="salt_test_1",
        ledger=ledger2,
    )

    # 1. So khớp tính xác định
    assert res1.population_hash == res2.population_hash
    assert res1.seed_commitment == res2.seed_commitment
    assert res1.lot_100_blind_ids == res2.lot_100_blind_ids
    assert res1.b_subset_30_blind_ids == res2.b_subset_30_blind_ids
    assert len(res1.lot_100_blind_ids) == 100
    assert len(res1.b_subset_30_blind_ids) == 30


def test_b_subset_is_exact_subset_with_paired_blind_id(dummy_candidates_150, tmp_path):
    """Kiểm tra 30 mẫu của B là tập con của 100 mẫu A và dùng chung blind_id."""
    res = run_main_batch1_sampling(
        dummy_candidates_150,
        seed_lot_100=4321,
        seed_b_subset_30=8765,
        seed_release_shuffle=9999,
        blind_salt="salt_pairing_check",
    )

    set_a_ids = set(res.lot_100_blind_ids)
    set_b_ids = set(res.b_subset_30_blind_ids)

    # B phải là tập con thực sự của A
    assert len(set_b_ids) == 30
    assert set_b_ids.issubset(set_a_ids)

    # Không có mẫu trùng lặp trong A
    assert len(set_a_ids) == 100

    # Kiểm tra mapping có đủ thông tin ghép cặp
    paired_count = 0
    for m in res.mapping_restricted:
        if m["is_b_kappa_sample"]:
            paired_count += 1
            assert "A" in m["assigned_to"] and "B" in m["assigned_to"]
            assert m["presentation_order_a"] is not None
            assert m["presentation_order_b"] is not None
    assert paired_count == 30


def test_presentation_order_is_shuffled(dummy_candidates_150):
    """Kiểm tra thứ tự hiển thị được xáo trộn khác với thứ tự trích xuất."""
    res = run_main_batch1_sampling(
        dummy_candidates_150,
        seed_lot_100=111,
        seed_b_subset_30=222,
        seed_release_shuffle=333,
        blind_salt="shuffle_salt",
    )

    # Lấy danh sách blind_id theo thứ tự Blind View phát hành
    release_order_a = [sample["sample_id"] for sample in res.blind_view_a]
    canonical_mapping_order = [m["blind_id"] for m in res.mapping_restricted]

    # Thứ tự phát hành không được trùng với thứ tự canonical
    assert release_order_a != canonical_mapping_order


def test_blind_view_v120_schema_and_allowlist(dummy_candidates_150):
    """Kiểm tra Blind View v1.2.0 giữ đúng URL, đúng schema và không chứa trường cấm."""
    res = run_main_batch1_sampling(
        dummy_candidates_150,
        seed_lot_100=555,
        seed_b_subset_30=666,
        seed_release_shuffle=777,
        blind_salt="schema_salt",
    )

    for sample in res.blind_view_a:
        assert sample["blind_contract_version"] == "1.2.0"
        assert sample["codebook_version"] == "1.1.0"
        assert sample["sample_id"].startswith("BLIND-")
        assert sample["url"].startswith("http")
        assert "random_subset" not in sample
        assert "source_label" not in sample
        assert "locator" not in sample
        assert "model_score" not in sample
        # Phải pass assert_no_label_leak
        assert_no_label_leak(sample)


def test_blind_view_v120_rejects_forbidden_fields():
    """Kiểm tra assert_no_label_leak từ chối các mẫu có trường cấm trong v1.2.0."""
    valid_sample = {
        "sample_id": "BLIND-0123abcd",
        "url": "https://secure-login.example.com",
        "page_text": "Sign In Form",
        "structure_summary": {"forms": 1},
        "codebook_version": "1.1.0",
        "blind_contract_version": "1.2.0",
        "translation_provided": False,
    }
    assert_no_label_leak(valid_sample)

    # 1. Chặn random_subset
    bad_sample1 = copy.deepcopy(valid_sample)
    bad_sample1["random_subset"] = "random_30"
    with pytest.raises(ValueError, match="random_subset bị cấm tuyệt đối"):
        assert_no_label_leak(bad_sample1)

    # 2. Chặn source_label
    bad_sample2 = copy.deepcopy(valid_sample)
    bad_sample2["source_label"] = "phishing"
    with pytest.raises(ValueError, match="ngoài allowlist"):
        assert_no_label_leak(bad_sample2)

    # 3. Chặn locator
    bad_sample3 = copy.deepcopy(valid_sample)
    bad_sample3["locator"] = "train-001.parquet:row:42"
    with pytest.raises(ValueError, match="ngoài allowlist"):
        assert_no_label_leak(bad_sample3)

    # 4. Chặn sample_id sai định dạng
    bad_sample4 = copy.deepcopy(valid_sample)
    bad_sample4["sample_id"] = "MAIN-01-0042"
    with pytest.raises(ValueError, match="không đúng định dạng trung tính"):
        assert_no_label_leak(bad_sample4)


def test_lot_management_ledger_integrity_and_tamper_detection(tmp_path):
    """Kiểm tra Sổ cái quản lý lô append-only, tính toàn vẹn hash-chain và phát hiện sửa đổi trái phép."""
    ledger_path = tmp_path / "test_ledger.json"
    ledger = LotManagementLedger(ledger_path)

    # Ghi nhận sự kiện 1
    ev1 = ledger.append_event(
        event_type="REGISTER_MAIN_BATCH1_SAMPLES",
        actor="Member C",
        lot_id="batch_001",
        status="RESERVED",
        details={"allocated_candidate_ids": ["cand_01", "cand_02"], "count": 2},
    )
    assert ev1.seq == 1
    assert ev1.prev_hash == ledger.events[0].event_hash
    assert ledger.is_candidate_allocated("cand_01")
    assert ledger.is_candidate_allocated("cand_02")
    assert not ledger.is_candidate_allocated("cand_03")

    # Đọc lại từ đĩa để xác minh hash-chain
    reloaded = LotManagementLedger(ledger_path)
    assert len(reloaded.events) == 2
    assert reloaded.events[1].event_hash == ev1.event_hash

    # Can thiệp dữ liệu trên đĩa để kiểm tra phát hiện vi phạm
    raw = json.loads(ledger_path.read_text(encoding="utf-8"))
    raw["events"][1]["status"] = "RELEASED"  # Chỉnh sửa trái phép status
    ledger_path.write_text(json.dumps(raw), encoding="utf-8")

    with pytest.raises(LedgerIntegrityError, match="Sai lệch event_hash"):
        LotManagementLedger(ledger_path)


def test_git_isolation_verification_passes():
    """Kiểm tra công cụ verify_git_isolation đạt PASS trên working tree hiện tại."""
    report = verify_git_isolation()
    assert report["overall_status"] == "PASS"
    assert report["checks"]["check_ignore_probes"]["status"] == "PASS"
    assert report["checks"]["tracked_files_inspection"]["status"] == "PASS"
    assert report["checks"]["public_content_leak_inspection"]["status"] == "PASS"


# =========================================================================
# CÁC TEST BỔ SUNG THEO 5 PROBE KIỂM ĐỊNH ĐỘC LẬP CỦA LEAD D
# =========================================================================

def test_probe_1_main_sample_without_contract_version_fails_closed():
    """Probe 1: Mẫu mang ID BLIND-xxxxxxxx nhưng thiếu blind_contract_version phải bị chặn (fail-closed)."""
    sample = {
        "sample_id": "BLIND-0123abcd",
        "url": "https://secure-login.example.com",
        "page_text": "Sign In Form",
        "structure_summary": {"forms": 1},
        "codebook_version": "1.1.0",
        "translation_provided": False,
    }
    with pytest.raises(ValueError, match="thiếu hoặc sai blind_contract_version"):
        assert_no_label_leak(sample)


def test_probe_2_population_fingerprint_seals_html_and_provenance():
    """Probe 2: Giữ nguyên candidate_uid, chỉ sửa đổi nội dung HTML phải làm đổi fingerprint quần thể."""
    pool1 = [
        {"candidate_uid": "cand_01", "url": "https://test.example/1", "html": "<html><body>Original Page</body></html>", "source_shard": "train-001.parquet", "source_row": 10},
        {"candidate_uid": "cand_02", "url": "https://test.example/2", "html": "<html><body>Page Two</body></html>", "source_shard": "train-001.parquet", "source_row": 20},
    ]
    pool2 = [
        {"candidate_uid": "cand_01", "url": "https://test.example/1", "html": "<html><body>MODIFIED Page HTML</body></html>", "source_shard": "train-001.parquet", "source_row": 10},
        {"candidate_uid": "cand_02", "url": "https://test.example/2", "html": "<html><body>Page Two</body></html>", "source_shard": "train-001.parquet", "source_row": 20},
    ]

    hash1 = compute_population_fingerprint(pool1)
    hash2 = compute_population_fingerprint(pool2)
    assert hash1 != hash2, "Thay đổi nội dung HTML nhưng fingerprint quần thể không thay đổi!"


def test_probe_3_cli_loads_envelope_and_omits_random_subset(tmp_path):
    """Probe 3: CLI nạp đúng cấu trúc envelope và bản ghi Main 1.2.0 hoàn toàn không chứa random_subset."""
    from scripts.annotate_cli import annotate_interactive_session
    from scripts.data.run_main_batch1_pipeline import export_main_batch1

    candidates = []
    for i in range(120):
        candidates.append({
            "candidate_uid": f"cand_{i:04d}",
            "url": f"https://service-{i:03d}.example.org/login",
            "html": f"<html><body>Login {i}</body></html>",
            "source_label": "phish" if i % 2 == 0 else "benign",
            "source_shard": "train-001.parquet",
            "source_row": i,
        })

    restricted_dir = tmp_path / "restricted"
    public_dir = tmp_path / "public"
    ledger_file = restricted_dir / "ledger.json"

    export_main_batch1(
        candidates,
        output_dir_restricted=restricted_dir,
        public_artifacts_dir=public_dir,
        seed_lot_100=100,
        seed_b_subset_30=200,
        seed_release_shuffle=300,
        blind_salt="test_salt_secret_probe_3",
        ledger_path=ledger_file,
    )

    view_a_path = restricted_dir / "blind_view_a.json"
    view_data = json.loads(view_a_path.read_text(encoding="utf-8"))
    assert isinstance(view_data, dict), "Gói view xuất ra đĩa phải là dict envelope, không được là bare list!"
    assert "samples" in view_data
    assert len(view_data["samples"]) == 100

    # Chạy một phiên dry-run giả lập qua CLI thật với fixture synthetic
    view_data_synth = dict(view_data)
    view_data_synth["is_synthetic"] = True
    synth_view_path = tmp_path / "synth_view_a.json"
    synth_view_path.write_text(json.dumps(view_data_synth), encoding="utf-8")

    out_jsonl = tmp_path / "output_a.jsonl"
    annotate_interactive_session(
        annotator_id="A",
        input_path=synth_view_path,
        output_path=out_jsonl,
        dry_run=True,
    )

    # Đọc bản ghi đã lưu từ CLI thật (dry_run lưu tại .dryrun.jsonl)
    dryrun_out = tmp_path / "output_a.dryrun.jsonl"
    records = [json.loads(line) for line in dryrun_out.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(records) == 100
    for r in records:
        assert "random_subset" not in r, f"Phát hiện trường cấm random_subset trong bản ghi Main 1.2.0: {r}"
        assert r.get("blind_contract_version") == "1.2.0"
        assert r["sample_id"].startswith("BLIND-")


def test_probe_4_ledger_prevents_duplicate_allocation_across_lots(tmp_path):
    """Probe 4: Hai lot dùng chung ledger không thể lấy trùng candidate_id."""
    ledger_path = tmp_path / "shared_ledger.json"
    ledger = LotManagementLedger(ledger_path)

    # Tạo pool 120 ứng viên có gắn locator dòng nguồn gốc
    candidates_120 = []
    for i in range(120):
        candidates_120.append({
            "candidate_uid": f"uid_{i:04d}",
            "url": f"https://svc-{i}.test/auth",
            "html": f"<html><body>Auth {i}</body></html>",
            "source_row": i,
            "source_shard": "train-001.parquet",
            "source_revision": "eabec4b7a66324b79cc8a0ad856d1731dc26fe1a",
        })

    # Lot 1 rút 100 mẫu
    res1 = run_main_batch1_sampling(
        candidates_120,
        seed_lot_100=111,
        seed_b_subset_30=222,
        seed_release_shuffle=333,
        blind_salt="salt_lot1",
        ledger=ledger,
        lot_id="lot_001",
    )
    assert len(res1.lot_100_blind_ids) == 100

    # Lot 2 cố rút 100 mẫu từ cùng pool 120 mẫu (chỉ còn 20 mẫu khả dụng) -> phải bị chặn!
    with pytest.raises(ValueError, match="không đủ 100 mẫu để rút"):
        run_main_batch1_sampling(
            candidates_120,
            seed_lot_100=111,
            seed_b_subset_30=222,
            seed_release_shuffle=333,
            blind_salt="salt_lot2",
            ledger=ledger,
            lot_id="lot_002",
        )

    # Nhưng nếu retry chính Lot 1 với cùng lot_id -> idempotent, không lỗi
    res1_retry = run_main_batch1_sampling(
        candidates_120,
        seed_lot_100=111,
        seed_b_subset_30=222,
        seed_release_shuffle=333,
        blind_salt="salt_lot1",
        ledger=ledger,
        lot_id="lot_001",
    )
    assert res1_retry.lot_100_blind_ids == res1.lot_100_blind_ids


def test_probe_5_export_verifier_fails_closed_on_isolation_failure(monkeypatch, tmp_path):
    """Probe 5: Nếu verify_git_isolation thất bại, export_main_batch1 phải chặn phát hành (fail-closed)."""
    import scripts.data.run_main_batch1_pipeline as runner
    from scripts.data.run_main_batch1_pipeline import export_main_batch1

    candidates = [{"candidate_uid": f"c_{i}", "url": f"https://u.test/{i}", "html": "p"} for i in range(110)]

    # Mock verify_git_isolation trả về FAIL
    monkeypatch.setattr(
        runner,
        "verify_git_isolation",
        lambda *args, **kwargs: {"overall_status": "FAIL", "conclusion": "Mock isolation leak detected"},
    )

    with pytest.raises(RuntimeError, match="EXPORT BLOCKED"):
        export_main_batch1(
            candidates,
            output_dir_restricted=tmp_path / "restricted",
            public_artifacts_dir=tmp_path / "public",
            seed_lot_100=1,
            seed_b_subset_30=2,
            seed_release_shuffle=3,
            blind_salt="test_salt",
            ledger_path=tmp_path / "ledger.json",
        )


def test_cohort_preservation_and_rejection_on_rerun(tmp_path):
    """Kiểm tra: Rerun cùng lot bảo toàn cohort; đổi seed/population bị từ chối; cấp lot khác không ảnh hưởng."""
    from phishing.data.lot_ledger import LotManagementLedger
    from phishing.data.main_sampling import run_main_batch1_sampling, supersede_lot_sampling

    ledger_path = tmp_path / "ledger_cohort.json"
    ledger = LotManagementLedger(ledger_path)

    # 150 ứng viên có locator nguồn
    pool_150 = [
        {
            "candidate_uid": f"uid_{i:04d}",
            "url": f"https://svc-{i}.test/auth",
            "html": f"<html><body>Auth {i}</body></html>",
            "source_row": i,
            "source_shard": "train-001.parquet",
            "source_revision": "eabec4b7a66324b79cc8a0ad856d1731dc26fe1a",
        }
        for i in range(150)
    ]

    # Rút lot_001 (100 mẫu)
    res_001 = run_main_batch1_sampling(
        pool_150,
        seed_lot_100=1001,
        seed_b_subset_30=2001,
        seed_release_shuffle=3001,
        blind_salt="salt_lot_1",
        ledger=ledger,
        lot_id="lot_001",
    )
    lot_001_candidates = [m["candidate_uid"] for m in res_001.mapping_restricted]
    lot_001_b_candidates = [m["candidate_uid"] for m in res_001.mapping_restricted if m["is_b_kappa_sample"]]
    assert len(lot_001_candidates) == 100
    assert len(lot_001_b_candidates) == 30

    # Rút lot_002 từ pool (chỉ còn 50 mẫu khả dụng -> phải bị chặn)
    with pytest.raises(ValueError, match="không đủ 100 mẫu để rút"):
        run_main_batch1_sampling(
            pool_150,
            seed_lot_100=1002,
            seed_b_subset_30=2002,
            seed_release_shuffle=3002,
            blind_salt="salt_lot_2",
            ledger=ledger,
            lot_id="lot_002",
        )

    # Rerun lại lot_001 cùng tham số -> BẢO TOÀN COHORT 100%
    res_001_rerun = run_main_batch1_sampling(
        pool_150,
        seed_lot_100=1001,
        seed_b_subset_30=2001,
        seed_release_shuffle=3001,
        blind_salt="salt_lot_1",
        ledger=ledger,
        lot_id="lot_001",
    )
    rerun_candidates = [m["candidate_uid"] for m in res_001_rerun.mapping_restricted]
    assert rerun_candidates == lot_001_candidates
    assert res_001_rerun.lot_100_blind_ids == res_001.lot_100_blind_ids

    # Rerun lot_001 nhưng đổi seed -> BỊ TỪ CHỐI
    with pytest.raises(ValueError, match="TỪ CHỐI RERUN LOT 'lot_001': seed_commitment không khớp"):
        run_main_batch1_sampling(
            pool_150,
            seed_lot_100=9999,  # Đổi seed
            seed_b_subset_30=2001,
            seed_release_shuffle=3001,
            blind_salt="salt_lot_1",
            ledger=ledger,
            lot_id="lot_001",
        )

    # Rerun lot_001 nhưng đổi pool (thay đổi quần thể) -> BỊ TỪ CHỐI
    pool_altered = list(pool_150)
    pool_altered[0] = dict(pool_150[0], html="<html>Altered</html>")
    with pytest.raises(ValueError, match="TỪ CHỐI RERUN LOT 'lot_001': population_hash không khớp"):
        run_main_batch1_sampling(
            pool_altered,
            seed_lot_100=1001,
            seed_b_subset_30=2001,
            seed_release_shuffle=3001,
            blind_salt="salt_lot_1",
            ledger=ledger,
            lot_id="lot_001",
        )

    # Supersede lot_001 với salt mới -> BẢO LƯU COHORT NHƯNG ĐỔI BLIND IDS
    res_supersede = supersede_lot_sampling(
        pool_150,
        ledger=ledger,
        lot_id="lot_001",
        new_blind_salt="new_secure_salt_2026",
        new_seed_release_shuffle=7777,
    )
    sup_candidates = [m["candidate_uid"] for m in res_supersede.mapping_restricted]
    sup_b_candidates = [m["candidate_uid"] for m in res_supersede.mapping_restricted if m["is_b_kappa_sample"]]
    assert sup_candidates == lot_001_candidates
    assert sup_b_candidates == lot_001_b_candidates
    # Blind IDs phải hoàn toàn mới
    assert res_supersede.lot_100_blind_ids != res_001.lot_100_blind_ids
    assert res_supersede.seed_commitment != res_001.seed_commitment


def test_main_contract_envelope_and_sample_cross_validation():
    """Kiểm tra: Envelope Main 1.2.0 chặn mẫu legacy; Envelope legacy chặn mẫu Main BLIND-xxxxxxxx."""
    from phishing.annotation.blind_view import assert_no_label_leak

    # 1. Envelope Main 1.2.0 chứa mẫu có 'random_subset' -> BỊ CHẶN
    bad_env_main = {
        "dataset_id": "MAIN-BATCH1-A",
        "blind_contract_version": "1.2.0",
        "samples": [
            {
                "sample_id": "BLIND-00000001",
                "url": "https://test.site",
                "page_text": "Sample text",
                "blind_contract_version": "1.2.0",
                "random_subset": True,  # Cấm trong Main 1.2.0
            }
        ],
    }
    with pytest.raises(ValueError, match="chứa trường cấm 'random_subset'"):
        assert_no_label_leak(bad_env_main)

    # 2. Envelope Main 1.2.0 chứa mẫu không khai báo blind_contract_version="1.2.0" -> BỊ CHẶN
    mixed_env = {
        "dataset_id": "MAIN-BATCH1-A",
        "blind_contract_version": "1.2.0",
        "samples": [
            {
                "sample_id": "BLIND-00000001",
                "url": "https://test.site",
                "page_text": "Sample text",
                "blind_contract_version": "1.0.0",  # Mixed version
            }
        ],
    }
    with pytest.raises(ValueError, match="LỖI MIXED VERSION"):
        assert_no_label_leak(mixed_env)

    # 3. Envelope legacy (1.1.0) chứa mẫu Main định dạng BLIND-xxxxxxxx -> BỊ CHẶN
    legacy_env_with_main_id = {
        "dataset_id": "PILOT-V2",
        "blind_contract_version": "1.1.0",
        "samples": [
            {
                "sample_id": "BLIND-aabbccdd",
                "url": "https://test.site",
                "page_text": "Sample text",
            }
        ],
    }
    with pytest.raises(ValueError, match="LỖI MIXED VERSION: Envelope legacy"):
        assert_no_label_leak(legacy_env_with_main_id)

    # 4. Envelope thiếu blind_contract_version nhưng chứa mẫu Main BLIND-xxxxxxxx -> BỊ CHẶN
    no_ver_env_with_main_id = {
        "dataset_id": "UNKNOWN",
        "samples": [
            {
                "sample_id": "BLIND-aabbccdd",
                "url": "https://test.site",
                "page_text": "Sample text",
            }
        ],
    }
    with pytest.raises(ValueError, match="LỖI ENVELOPE: Envelope chứa mẫu Main"):
        assert_no_label_leak(no_ver_env_with_main_id)


def test_record_main_downgrade_and_provenance_enforcement():
    """Kiểm tra: Record Main BLIND-xxxxxxxx cấm hạ cấp và bắt buộc đủ provenance."""
    from phishing.annotation.blind_view import validate_annotation_record

    base_record = {
        "annotator_id": "A",
        "sample_id": "BLIND-12345678",
        "pass_id": 1,
        "class_label": "phishing",
        "primary_org_status": "identified",
        "catalog_status": "in_catalog",
        "observed_service": "banking",
        "org_targets": ["microsoft"],
        "primary_org": "microsoft",
        "identity_role": "identity_claim",
        "domain_role": "unverified",
        "evidence_note": "Giao diện giả mạo",
        "seconds_spent": 120.0,
        "difficult_case": False,
        "codebook_version": "1.1.0",
        "pause_count": 0,
        "paused_seconds": 0.0,
        "org_evidence": [{"org_id": "microsoft", "evidence_basis": "heading", "evidence_quote": "Sign in to Microsoft"}],
        "primary_phishing_type": "credential_collection",
        "confidence": "high",
        "dataset_id": "MAIN-BATCH1-A",
        "dataset_hash": "a" * 64,
        "codebook_hash": "b" * 64,
        "sample_content_hash": "c" * 64,
        "sampling_plan_version": "MAIN-PLAN-V1.0",
        "timestamp_utc": "2026-11-19T10:00:00Z",
        "blind_contract_version": "1.2.0",
    }

    # Hợp lệ
    rec_valid = validate_annotation_record(base_record)
    assert rec_valid.blind_contract_version == "1.2.0"
    assert rec_valid.random_subset is None

    # Hạ cấp: Xóa blind_contract_version để giả mạo legacy -> BỊ TỪ CHỐI
    downgrade_record = dict(base_record)
    del downgrade_record["blind_contract_version"]
    with pytest.raises(ValueError, match="Cấm hạ cấp bản ghi Main xuống legacy"):
        validate_annotation_record(downgrade_record)

    # Record Main chứa random_subset -> BỊ TỪ CHỐI
    leak_subset_record = dict(base_record, random_subset=True)
    with pytest.raises(ValueError, match="Trường 'random_subset' bị cấm tuyệt đối trong bản ghi Main 1.2.0"):
        validate_annotation_record(leak_subset_record)

    # Record Main thiếu provenance (ví dụ: sample_content_hash rỗng) -> BỊ TỪ CHỐI
    missing_prov_record = dict(base_record, sample_content_hash="")
    with pytest.raises(ValueError, match="LỖI PROVENANCE MAIN 1.2.0"):
        validate_annotation_record(missing_prov_record)

    # Record Main thiếu timestamp_utc -> BỊ TỪ CHỐI, không fallback
    missing_time_record = dict(base_record, timestamp_utc="")
    with pytest.raises(ValueError, match="LỖI PROVENANCE MAIN 1.2.0"):
        validate_annotation_record(missing_time_record)


def test_source_row_required_for_main_sampling():
    """Kiểm tra: Thiếu hoặc sai source_row bị chặn fail-closed trước khi rút mẫu."""
    from phishing.data.main_sampling import run_main_batch1_sampling

    pool_missing_row = [
        {
            "candidate_uid": f"uid_{i:04d}",
            "url": f"https://svc-{i}.test/auth",
            "html": f"<html><body>Auth {i}</body></html>",
        }
        for i in range(110)
    ]

    with pytest.raises(ValueError, match="Bắt buộc gắn locator dòng nguồn gốc trước khi lọc"):
        run_main_batch1_sampling(
            pool_missing_row,
            seed_lot_100=1,
            seed_b_subset_30=2,
            seed_release_shuffle=3,
            blind_salt="test_salt",
        )


def test_isolation_scanner_detects_literal_salt_assignment_and_read_errors(tmp_path):
    """Kiểm tra: Scanner phát hiện literal string gán cho salt/secret mới và phát hiện lỗi đọc tệp."""
    from scripts.data.verify_git_isolation import scan_public_docs_for_leaks

    scan_dir = tmp_path / "scripts"
    scan_dir.mkdir()

    # 1. Tệp có gán literal salt cứng
    bad_code_file = scan_dir / "bad_runner.py"
    bad_code_file.write_text("blind_salt = 'my_secret_production_salt_2026'\n", encoding="utf-8")

    res = scan_public_docs_for_leaks(target_dirs=[str(scan_dir)])
    assert res["status"] == "FAIL"
    assert any("LITERAL_SALT_ASSIGNMENT" in leak["term"] for leak in res["leaks"])

    # 2. Xóa tệp vi phạm -> trạng thái trở về PASS
    bad_code_file.unlink()
    good_code_file = scan_dir / "good_runner.py"
    good_code_file.write_text("b_salt = load_private_salt()\n", encoding="utf-8")
    res_good = scan_public_docs_for_leaks(target_dirs=[str(scan_dir)])
    assert res_good["status"] == "PASS"


def test_staging_and_atomic_publish_preserves_old_bytes_on_failure(monkeypatch, tmp_path):
    """Kiểm tra: Staging + Atomic publishing không ghi đè hiện vật cũ và phục hồi byte ledger khi lỗi."""
    import scripts.data.run_main_batch1_pipeline as runner
    from scripts.data.run_main_batch1_pipeline import export_main_batch1

    candidates = [
        {
            "candidate_uid": f"c_{i:04d}",
            "url": f"https://u.test/{i}",
            "html": "p",
            "source_row": i,
            "source_shard": "train-001.parquet",
            "source_revision": "eabec4b7a66324b79cc8a0ad856d1731dc26fe1a",
        }
        for i in range(220)
    ]

    p_rest = tmp_path / "restricted"
    p_pub = tmp_path / "public"
    p_ledger = tmp_path / "ledger.json"

    # Lần 1: Xuất thành công
    res1 = export_main_batch1(
        candidates,
        output_dir_restricted=p_rest,
        public_artifacts_dir=p_pub,
        seed_lot_100=10,
        seed_b_subset_30=20,
        seed_release_shuffle=30,
        blind_salt="salt_1",
        ledger_path=p_ledger,
        lot_id="lot_first",
    )
    assert res1["status"] == "SUCCESS"

    old_view_a_bytes = (p_rest / "blind_view_a.json").read_bytes()
    old_ledger_bytes = p_ledger.read_bytes()

    # Lần 2: Xuất lot khác nhưng mock lỗi ở bước hậu kiểm (Postflight check)
    original_verify = runner.verify_git_isolation
    call_count = 0

    def mock_verify(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count > 1:
            return {"overall_status": "FAIL", "conclusion": "Mock postflight failure"}
        return original_verify(*args, **kwargs)

    monkeypatch.setattr(runner, "verify_git_isolation", mock_verify)

    with pytest.raises(RuntimeError, match="EXPORT BLOCKED: Vi phạm quy tắc cách ly Git sau khi chuẩn bị staging"):
        export_main_batch1(
            candidates,
            output_dir_restricted=p_rest,
            public_artifacts_dir=p_pub,
            seed_lot_100=11,
            seed_b_subset_30=21,
            seed_release_shuffle=31,
            blind_salt="salt_2",
            ledger_path=p_ledger,
            lot_id="lot_second",
        )

    # Xác nhận: Byte của gói cũ và byte của Ledger cũ không hề bị thay đổi
    assert (p_rest / "blind_view_a.json").read_bytes() == old_view_a_bytes
    assert p_ledger.read_bytes() == old_ledger_bytes
    # Xác nhận không còn thư mục staging nào còn sót lại
    staging_dirs = list(p_rest.parent.glob(".staging_*"))
    assert len(staging_dirs) == 0


def test_receive_main_batch1_intake_pipeline(tmp_path):
    """Kiểm tra: Pipeline intake Main nhận gói hợp lệ, từ chối random_subset và kiểm toán receipt."""
    from scripts.data.receive_main_batch1 import receive_main_batch1
    from scripts.data.run_main_batch1_pipeline import export_main_batch1

    candidates = [
        {
            "candidate_uid": f"c_{i:04d}",
            "url": f"https://u.test/{i}",
            "html": "<html><body>Main candidate</body></html>",
            "source_row": i,
            "source_shard": "train-001.parquet",
            "source_revision": "eabec4b7a66324b79cc8a0ad856d1731dc26fe1a",
        }
        for i in range(220)
    ]

    p_rest = tmp_path / "restricted"
    p_pub = tmp_path / "public"
    p_ledger = tmp_path / "ledger.json"
    p_intake = tmp_path / "intake"

    export_res = export_main_batch1(
        candidates,
        output_dir_restricted=p_rest,
        public_artifacts_dir=p_pub,
        seed_lot_100=401,
        seed_b_subset_30=501,
        seed_release_shuffle=601,
        blind_salt="salt_intake_test",
        ledger_path=p_ledger,
        lot_id="lot_intake",
    )
    assert export_res["status"] == "SUCCESS"

    view_a = json.loads((p_rest / "blind_view_a.json").read_text(encoding="utf-8"))
    manifest_a = json.loads((p_rest / "manifest_a.json").read_text(encoding="utf-8"))

    # Tạo tệp kết quả JSONL hợp lệ cho A (100 mẫu)
    valid_records_a = []
    for s in view_a["samples"]:
        sid = s["sample_id"]
        from phishing.annotation.blind_view import compute_sample_content_hash
        s_hash = compute_sample_content_hash(s)
        rec = {
            "annotator_id": "A",
            "sample_id": sid,
            "pass_id": 1,
            "class_label": "benign",
            "primary_org_status": "no_clear_target",
            "catalog_status": "unresolved",
            "observed_service": "generic_site",
            "org_targets": [],
            "primary_org": "no_clear_target",
            "identity_role": "unclear",
            "domain_role": "unverified",
            "evidence_note": "Trang dịch vụ bình thường",
            "seconds_spent": 45.0,
            "difficult_case": False,
            "codebook_version": "1.1.0",
            "pause_count": 0,
            "paused_seconds": 0.0,
            "org_evidence": [],
            "primary_phishing_type": None,
            "hard_benign_type": None,
            "confidence": "high",
            "dataset_id": manifest_a["dataset_id"],
            "dataset_hash": manifest_a["blind_view_sha256"],
            "codebook_hash": manifest_a["codebook_sha256"],
            "sampling_plan_version": manifest_a["sampling_plan_version"],
            "sample_content_hash": s_hash,
            "timestamp_utc": "2026-11-19T12:00:00Z",
            "blind_contract_version": "1.2.0",
            "is_dry_run": False,
            "is_synthetic": False,
        }
        valid_records_a.append(rec)

    input_jsonl = tmp_path / "submission_a.jsonl"
    with input_jsonl.open("w", encoding="utf-8") as f:
        for r in valid_records_a:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    # Tiếp nhận submission hợp lệ -> ACCEPTED
    rcp = receive_main_batch1(input_jsonl, "A", out_root=p_intake, restricted_dir=p_rest)
    assert rcp["status"] == "accepted"
    assert rcp["sample_count"] == 100

    # Nếu gửi lại cùng submission -> idempotent
    rcp_dup = receive_main_batch1(input_jsonl, "A", out_root=p_intake, restricted_dir=p_rest)
    assert rcp_dup["status"] == "accepted"

    # Tạo submission vi phạm có 'random_subset' -> REJECTED
    bad_records = list(valid_records_a)
    bad_records[0] = dict(bad_records[0], random_subset=True)
    bad_jsonl = tmp_path / "submission_bad.jsonl"
    with bad_jsonl.open("w", encoding="utf-8") as f:
        for r in bad_records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    rcp_bad = receive_main_batch1(bad_jsonl, "A", out_root=p_intake, restricted_dir=p_rest)
    assert rcp_bad["status"] == "rejected"
    assert "Trường 'random_subset' bị cấm tuyệt đối" in rcp_bad["reason"]
