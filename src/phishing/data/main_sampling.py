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
    compute_sample_content_hash,
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
    """Tính mã băm chuẩn hóa toàn vẹn của quần thể ứng viên đầu vào.
    
    Khóa cứng: candidate_uid, URL raw, URL normalized, URL SHA-256,
    HTML SHA-256, source_shard, source_row, source_revision.
    Bất kỳ sự thay đổi nào về nội dung HTML, URL, shard, dòng nguồn hay bản sửa đổi
    đều làm thay đổi mã băm quần thể.
    """
    records = []
    for c in candidates:
        uid = str(c.get("candidate_uid") or c.get("sample_uid") or "")
        raw_url = str(c.get("url", ""))
        norm_url = normalize_url(raw_url)
        url_hash = hashlib.sha256(raw_url.encode("utf-8")).hexdigest()
        html_content = c.get("html") or ""
        html_hash = hashlib.sha256(html_content.encode("utf-8")).hexdigest()
        shard = str(c.get("source_shard", "train-001.parquet"))
        row = c.get("source_row")
        revision = str(c.get("source_revision", "eabec4b7a66324b79cc8a0ad856d1731dc26fe1a"))

        records.append({
            "candidate_uid": uid,
            "url_raw": raw_url,
            "url_normalized": norm_url,
            "url_sha256": url_hash,
            "html_sha256": html_hash,
            "source_shard": shard,
            "source_row": row,
            "source_revision": revision,
        })

    # Sắp xếp canonical theo url_normalized, html_sha256, candidate_uid
    records.sort(key=lambda r: (r["url_normalized"], r["html_sha256"], r["candidate_uid"]))
    canonical_bytes = json.dumps(records, sort_keys=True, ensure_ascii=False).encode("utf-8")
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
    blind_view_a_envelope: Optional[Dict[str, Any]] = None
    blind_view_b_envelope: Optional[Dict[str, Any]] = None


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

    # Kiểm tra loại trừ các ứng viên đã phân bổ cho các lô khác trong ledger
    other_lot_allocated: Set[str] = set()
    is_idempotent_rerun = False
    if ledger:
        for ev in ledger.events:
            if ev.lot_id != lot_id and ev.status in ("PREPARED", "RESERVED", "RELEASED", "COMPLETED"):
                for cid in ev.details.get("allocated_candidate_ids", []):
                    other_lot_allocated.add(cid)
            elif ev.lot_id == lot_id and ev.status in ("RESERVED", "RELEASED"):
                if ev.details.get("seed_commitment") == seed_commit and ev.details.get("population_hash") == pop_hash:
                    is_idempotent_rerun = True

    available_candidates = [
        c for c in sorted_candidates
        if (c.get("candidate_uid") or c.get("sample_uid") or hashlib.sha256(c.get("url", "").encode("utf-8")).hexdigest()[:16]) not in other_lot_allocated
    ]

    if len(available_candidates) < 100:
        raise ValueError(
            f"Quần thể ứng viên khả dụng sau khi trừ các lô khác ({len(available_candidates)}) không đủ 100 mẫu để rút!"
        )

    # 2. Rút ngẫu nhiên không hoàn lại 100 mẫu Main cho Annotator A
    rng_lot = random.Random(seed_lot_100)
    selected_indices_100 = rng_lot.sample(range(len(available_candidates)), 100)
    selected_indices_100.sort()  # Sắp xếp chỉ số canonical trước khi gán
    lot_100 = [available_candidates[i] for i in selected_indices_100]

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

        sample_content_hash = compute_sample_content_hash(blind_sample)
        mapping_entry = {
            "blind_id": b_id,
            "candidate_uid": c_uid,
            "url": sample.get("url", ""),
            "url_normalized": normalize_url(sample.get("url", "")),
            "url_sha256": hashlib.sha256(sample.get("url", "").encode("utf-8")).hexdigest(),
            "html_sha256": hashlib.sha256((sample.get("html") or "").encode("utf-8")).hexdigest(),
            "sample_content_hash": sample_content_hash,
            "canonical_pop_index": selected_indices_100[idx],
            "assigned_to": assigned_to,
            "is_b_kappa_sample": is_for_b,
            "source_label": sample.get("source_label") or sample.get("label"),
            "source_shard": sample.get("source_shard", "train-001.parquet"),
            "source_row": sample.get("source_row"),
            "source_revision": sample.get("source_revision", "eabec4b7a66324b79cc8a0ad856d1731dc26fe1a"),
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

    # Tạo Envelope thống nhất cho Blind View A và B
    envelope_a = {
        "dataset_id": "MAIN-BATCH1-A",
        "dataset_type": "main_annotation",
        "blind_contract_version": blind_contract_version,
        "codebook_version": codebook_version,
        "sampling_plan_version": "MAIN-PLAN-V1.0",
        "sample_count": len(blind_view_a),
        "total_samples": len(blind_view_a),
        "is_synthetic": False,
        "samples": blind_view_a,
    }
    envelope_b = {
        "dataset_id": "MAIN-BATCH1-B",
        "dataset_type": "main_annotation",
        "blind_contract_version": blind_contract_version,
        "codebook_version": codebook_version,
        "sampling_plan_version": "MAIN-PLAN-V1.0",
        "sample_count": len(blind_view_b),
        "total_samples": len(blind_view_b),
        "is_synthetic": False,
        "samples": blind_view_b,
    }
    assert_no_label_leak(envelope_a)
    assert_no_label_leak(envelope_b)

    # 6. Ghi nhận vào Sổ quản lý lô (Append-only Ledger) nếu được cấp
    seq_num = -1
    if ledger:
        if not is_idempotent_rerun:
            event = ledger.append_event(
                event_type="REGISTER_MAIN_BATCH1_SAMPLES",
                actor=actor,
                lot_id=lot_id,
                status="RESERVED",
                details={
                    "population_count": len(sorted_candidates),
                    "population_hash": pop_hash,
                    "available_candidates_count": len(available_candidates),
                    "lot_size": 100,
                    "b_subset_size": 30,
                    "seed_commitment": seed_commit,
                    "allocated_candidate_ids": [m["candidate_uid"] for m in mapping_restricted],
                    "blind_ids": [m["blind_id"] for m in mapping_restricted],
                },
            )
            seq_num = event.seq
        else:
            for ev in reversed(ledger.events):
                if ev.lot_id == lot_id:
                    seq_num = ev.seq
                    break

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
        blind_view_a_envelope=envelope_a,
        blind_view_b_envelope=envelope_b,
    )
