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
