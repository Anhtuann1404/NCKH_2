"""Module trích xuất mẫu ngẫu nhiên không hoàn lại (SRS) cho Main Annotation Đợt 1.

Tuân thủ nghiêm ngặt 6 chỉ đạo của Lead D và phản biện của Mô hình Duo:
1. SRS không hoàn lại: Rút 100 mẫu Main từ 1.232 ứng viên đã khóa, mọi ứng viên đồng xác suất.
2. Tập 30 mẫu cho B: Rút ngẫu nhiên độc lập 30 mẫu từ lô 100 mẫu Main trước Pass 1 để tính Cohen's Kappa chính.
3. ID trung tính không mã hóa lô: Định dạng BLIND-xxxxxxxx (8 ký tự hex), không chứa số lô, nhãn, nhóm hay phân tầng.
4. Ghép cặp nhất quán: Mẫu được A và B cùng gán dùng CHUNG blind_id, lưu mapping trong data/restricted/.
5. Xáo trộn phát hành: Dùng seed riêng để xáo trộn thứ tự hiển thị tránh order bias.
6. Bảo mật & Chống rò rỉ: URL quan sát được giữ nguyên; chặn tuyệt đối locator, metadata Parquet, nhãn nguồn, matcher, điểm mô hình.
"""

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import random
import re
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

from phishing.annotation.blind_view import (
    ALLOWED_BLIND_SAMPLE_KEYS,
    FORBIDDEN_LEAK_KEYS,
    assert_no_label_leak,
    extract_safe_view_content,
    normalize_url,
)
from phishing.data.lot_ledger import LotManagementLedger


BLIND_ID_PATTERN = re.compile(r"^BLIND-[a-f0-9]{8}$")


def generate_blind_id(salt: str, candidate_uid: str) -> str:
    """Sinh ID trung tính định dạng BLIND-xxxxxxxx (8 ký tự hex), không mã hóa lô hay nhãn."""
    h = hashlib.sha256(f"{salt}:{candidate_uid}".encode("utf-8")).hexdigest()
    blind_id = f"BLIND-{h[:8]}"
    if not BLIND_ID_PATTERN.match(blind_id):
        raise ValueError(f"Định dạng blind_id không hợp lệ: {blind_id}")
    return blind_id


def compute_seed_commitment(
    seed_lot_100: int,
    seed_b_subset_30: int,
    seed_release_shuffle: int,
    salt: str,
) -> str:
    """Tạo cam kết băm SHA-256 công khai cho bộ seed lựa chọn trước khi rút mẫu."""
    payload = f"lot100:{seed_lot_100}|b30:{seed_b_subset_30}|shuffle:{seed_release_shuffle}|salt:{salt}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def compute_population_fingerprint(candidates: Sequence[Dict[str, Any]]) -> str:
    """Tính mã băm chuẩn hóa của toàn bộ 1.232 ứng viên đầu vào."""
    uids = []
    for c in candidates:
        uid = c.get("candidate_uid") or c.get("sample_uid") or c.get("url") or str(c)
        uids.append(uid)
    uids.sort()
    canonical_bytes = json.dumps(uids, sort_keys=True).encode("utf-8")
    return hashlib.sha256(canonical_bytes).hexdigest()


@dataclass
class SamplingResult:
    population_count: int
    population_hash: str
    lot_100_blind_ids: List[str]
    b_subset_30_blind_ids: List[str]
    seed_commitment: str
    mapping_restricted: List[Dict[str, Any]]
    blind_view_a: List[Dict[str, Any]]
    blind_view_b: List[Dict[str, Any]]
    ledger_event_seq: int


def run_main_batch1_sampling(
    candidates: List[Dict[str, Any]],
    *,
    seed_lot_100: int,
    seed_b_subset_30: int,
    seed_release_shuffle: int,
    blind_salt: str,
    ledger: Optional[LotManagementLedger] = None,
    lot_id: str = "main_lot_batch_001",
    actor: str = "Member C (Nguyễn Thắng)",
    codebook_version: str = "1.1.0",
    blind_contract_version: str = "1.2.0",
) -> SamplingResult:
    """Thực thi toàn bộ quy trình lấy mẫu ngẫu nhiên không hoàn lại cho Main Annotation Đợt 1."""
    if len(candidates) < 100:
        raise ValueError(f"Quần thể ứng viên ({len(candidates)}) không đủ 100 mẫu để rút!")

    # 1. Khóa và tính fingerprint của quần thể 1.232 ứng viên
    # Sắp xếp canonical theo url và hash nội dung để đảm bảo độc lập thứ tự đầu vào
    sorted_candidates = sorted(
        candidates,
        key=lambda s: (
            s.get("url", ""),
            hashlib.sha256((s.get("html") or "").encode("utf-8")).hexdigest(),
        ),
    )
    pop_hash = compute_population_fingerprint(sorted_candidates)
    seed_commit = compute_seed_commitment(seed_lot_100, seed_b_subset_30, seed_release_shuffle, blind_salt)

    # 2. Rút ngẫu nhiên không hoàn lại 100 mẫu Main cho Annotator A
    rng_lot = random.Random(seed_lot_100)
    selected_indices_100 = rng_lot.sample(range(len(sorted_candidates)), 100)
    selected_indices_100.sort()  # Sắp xếp chỉ số canonical trước khi gán
    lot_100 = [sorted_candidates[i] for i in selected_indices_100]

    # 3. Rút ngẫu nhiên không hoàn lại 30 mẫu từ lô 100 cho Annotator B (tính Kappa chính)
    rng_b = random.Random(seed_b_subset_30)
    b_indices_in_lot100 = rng_b.sample(range(100), 30)
    b_indices_in_lot100.sort()
    b_subset_set = set(b_indices_in_lot100)

    # 4. Sinh Blind ID trung tính duy nhất (BLIND-xxxxxxxx) và thiết lập ánh xạ hạn chế
    mapping_restricted: List[Dict[str, Any]] = []
    lot_100_with_blind: List[Tuple[Dict[str, Any], Dict[str, Any]]] = []

    seen_blind_ids: Set[str] = set()

    for idx, sample in enumerate(lot_100):
        c_uid = (
            sample.get("candidate_uid")
            or sample.get("sample_uid")
            or hashlib.sha256(sample.get("url", "").encode("utf-8")).hexdigest()[:16]
        )
        b_id = generate_blind_id(blind_salt, c_uid)
        if b_id in seen_blind_ids:
            # Xử lý va chạm cực hiếm bằng salt dẫn xuất
            alt_salt = f"{blind_salt}_{idx}"
            b_id = generate_blind_id(alt_salt, c_uid)
        seen_blind_ids.add(b_id)

        is_for_b = idx in b_subset_set
        assigned_to = ["A", "B"] if is_for_b else ["A"]

        # Blind View representation
        html_content = sample.get("html", "")
        cleaned_text, struct_summary = extract_safe_view_content(html_content, page_url=sample.get("url", ""))

        blind_sample = {
            "sample_id": b_id,
            "url": sample.get("url", ""),
            "page_text": cleaned_text,
            "structure_summary": struct_summary,
            "codebook_version": codebook_version,
            "blind_contract_version": blind_contract_version,
            "translation_provided": False,
        }

        # Kiểm tra chống rò rỉ nghiêm ngặt: không có bất kỳ trường cấm nào
        assert_no_label_leak(blind_sample)
        for forbidden in ("source_label", "locator", "parquet_file", "source_row", "model_score", "random_subset"):
            if forbidden in blind_sample:
                raise ValueError(f"RÒ RỈ DỮ LIỆU: Trường cấm '{forbidden}' xuất hiện trong Blind View!")

        mapping_entry = {
            "blind_id": b_id,
            "candidate_uid": c_uid,
            "url": sample.get("url", ""),
            "canonical_pop_index": selected_indices_100[idx],
            "assigned_to": assigned_to,
            "is_b_kappa_sample": is_for_b,
            "source_label": sample.get("source_label") or sample.get("label"),
            "source_shard": sample.get("source_shard", "train-001.parquet"),
            "source_row": sample.get("source_row"),
        }

        mapping_restricted.append(mapping_entry)
        lot_100_with_blind.append((blind_sample, mapping_entry))

    # 5. Xáo trộn thứ tự hiển thị phát hành (chống order bias)
    # A nhận đủ 100 mẫu xáo trộn theo seed_release_shuffle
    rng_shuffle_a = random.Random(seed_release_shuffle)
    shuffled_lot_a = list(lot_100_with_blind)
    rng_shuffle_a.shuffle(shuffled_lot_a)

    blind_view_a = [item[0] for item in shuffled_lot_a]

    # Cập nhật presentation_order_a trong mapping
    for order, (b_sample, m_entry) in enumerate(shuffled_lot_a):
        m_entry["presentation_order_a"] = order

    # B nhận đúng 30 mẫu xáo trộn theo stream riêng của seed_release_shuffle
    rng_shuffle_b = random.Random(seed_release_shuffle + 1000)
    b_candidates_with_blind = [item for item in lot_100_with_blind if item[1]["is_b_kappa_sample"]]
    if len(b_candidates_with_blind) != 30:
        raise ValueError(f"Số lượng mẫu cho B ({len(b_candidates_with_blind)}) không khớp 30!")

    shuffled_lot_b = list(b_candidates_with_blind)
    rng_shuffle_b.shuffle(shuffled_lot_b)

    blind_view_b = [item[0] for item in shuffled_lot_b]

    # Cập nhật presentation_order_b trong mapping
    for order, (b_sample, m_entry) in enumerate(shuffled_lot_b):
        m_entry["presentation_order_b"] = order

    # 6. Ghi nhận vào Sổ quản lý lô (Append-only Ledger) nếu được cấp
    seq_num = -1
    if ledger:
        event = ledger.append_event(
            event_type="REGISTER_MAIN_BATCH1_SAMPLES",
            actor=actor,
            lot_id=lot_id,
            status="RESERVED",
            details={
                "population_count": len(sorted_candidates),
                "population_hash": pop_hash,
                "lot_size": 100,
                "b_subset_size": 30,
                "seed_commitment": seed_commit,
                "allocated_candidate_ids": [m["candidate_uid"] for m in mapping_restricted],
                "blind_ids": [m["blind_id"] for m in mapping_restricted],
            },
        )
        seq_num = event.seq

    return SamplingResult(
        population_count=len(sorted_candidates),
        population_hash=pop_hash,
        lot_100_blind_ids=[m["blind_id"] for m in mapping_restricted],
        b_subset_30_blind_ids=[m["blind_id"] for m in mapping_restricted if m["is_b_kappa_sample"]],
        seed_commitment=seed_commit,
        mapping_restricted=mapping_restricted,
        blind_view_a=blind_view_a,
        blind_view_b=blind_view_b,
        ledger_event_seq=seq_num,
    )
