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

    # Lập bản đồ tra cứu toàn bộ ứng viên theo candidate_uid và vị trí gốc trong quần thể
    cand_map: Dict[str, Dict[str, Any]] = {}
    pop_index_by_uid: Dict[str, int] = {}
    for idx, c in enumerate(sorted_candidates):
        c_uid = (
            c.get("candidate_uid")
            or c.get("sample_uid")
            or hashlib.sha256(c.get("url", "").encode("utf-8")).hexdigest()[:16]
        )
        cand_map[c_uid] = c
        pop_index_by_uid[c_uid] = idx

    existing_details = ledger.get_active_lot_details(lot_id) if ledger else None
    is_idempotent_rerun = False

    if existing_details:
        # Trường hợp 1: Chạy lại đúng lot đã niêm phong -> BẮT BUỘC BẢO TOÀN COHORT
        # Kiểm tra cam kết quần thể và cam kết seed/salt trước khi tiếp tục
        prior_pop_hash = existing_details.get("population_hash")
        if prior_pop_hash and prior_pop_hash != pop_hash:
            raise ValueError(
                f"TỪ CHỐI RERUN LOT '{lot_id}': population_hash không khớp với lot đã niêm phong "
                f"(kỳ vọng '{prior_pop_hash}', thực tế '{pop_hash}')!"
            )

        prior_seed_commit = existing_details.get("seed_commitment") or existing_details.get("new_seed_commitment")
        prior_seed_lot_100 = existing_details.get("seed_lot_100")
        if (prior_seed_commit and prior_seed_commit != seed_commit) or (prior_seed_lot_100 is not None and prior_seed_lot_100 != seed_lot_100):
            raise ValueError(
                f"TỪ CHỐI RERUN LOT '{lot_id}': seed_commitment không khớp với lot đã niêm phong "
                f"(kỳ vọng '{prior_seed_commit}', thực tế '{seed_commit}', seed_lot_100={seed_lot_100})! "
                "Tuyệt đối không được đổi seed để chọn lại mẫu cho lot cũ. Dùng supersede_lot_sampling nếu cần cấp lại ID."
            )

        # Nạp lại đúng 100 mẫu và 30 mẫu B đã khóa từ ledger, KHÔNG chạy random sampling lại
        allocated_uids = existing_details.get("allocated_candidate_ids", [])
        if len(allocated_uids) != 100:
            raise ValueError(f"Dữ liệu ledger hỏng: lot '{lot_id}' không có đủ 100 candidate_ids đã cấp.")

        lot_100 = [cand_map[uid] for uid in allocated_uids]
        b_subset_uids = set(existing_details.get("b_subset_candidate_ids", []))
        if b_subset_uids:
            b_subset_set = {i for i, sample in enumerate(lot_100) if (sample.get("candidate_uid") or sample.get("sample_uid") or hashlib.sha256(sample.get("url", "").encode("utf-8")).hexdigest()[:16]) in b_subset_uids}
        else:
            b_subset_set = set(existing_details.get("b_indices_in_lot100", []))

        is_idempotent_rerun = True

    else:
        # Trường hợp 2: Lô mới -> Rút từ các ứng viên chưa từng phân bổ cho bất kỳ lô nào
        other_lot_allocated = ledger.get_allocated_candidate_ids() if ledger else set()
        available_candidates = [
            c for c in sorted_candidates
            if (c.get("candidate_uid") or c.get("sample_uid") or hashlib.sha256(c.get("url", "").encode("utf-8")).hexdigest()[:16]) not in other_lot_allocated
        ]

        if len(available_candidates) < 100:
            raise ValueError(
                f"Quần thể ứng viên khả dụng sau khi trừ các lô khác ({len(available_candidates)}) không đủ 100 mẫu để rút!"
            )

        # Rút ngẫu nhiên không hoàn lại 100 mẫu Main cho Annotator A
        rng_lot = random.Random(seed_lot_100)
        selected_indices_100 = rng_lot.sample(range(len(available_candidates)), 100)
        selected_indices_100.sort()  # Sắp xếp chỉ số canonical trước khi gán
        lot_100 = [available_candidates[i] for i in selected_indices_100]

        # Rút ngẫu nhiên không hoàn lại 30 mẫu từ lô 100 cho Annotator B (tính Kappa chính)
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

        # Kiểm tra bắt buộc provenance source_row
        s_row = sample.get("source_row")
        if s_row is None or type(s_row) is not int or s_row < 0:
            raise ValueError(
                f"THIẾU PROVENANCE: Mẫu '{c_uid}' thiếu hoặc có source_row không hợp lệ ({s_row!r}). "
                "Bắt buộc gắn locator dòng nguồn gốc trước khi lọc."
            )

        sample_content_hash = compute_sample_content_hash(blind_sample)
        # canonical_pop_index phải chỉ đúng vị trí trong quần thể gốc ban đầu (1.232 mẫu)
        canonical_pop_idx = pop_index_by_uid[c_uid]

        mapping_entry = {
            "blind_id": b_id,
            "candidate_uid": c_uid,
            "url": sample.get("url", ""),
            "url_normalized": normalize_url(sample.get("url", "")),
            "url_sha256": hashlib.sha256(sample.get("url", "").encode("utf-8")).hexdigest(),
            "html_sha256": hashlib.sha256((sample.get("html") or "").encode("utf-8")).hexdigest(),
            "sample_content_hash": sample_content_hash,
            "canonical_pop_index": canonical_pop_idx,
            "assigned_to": assigned_to,
            "is_b_kappa_sample": is_for_b,
            "source_label": sample.get("source_label") or sample.get("label"),
            "source_shard": sample.get("source_shard", "train-001.parquet"),
            "source_row": s_row,
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
                    "seed_lot_100": seed_lot_100,
                    "seed_b_subset_30": seed_b_subset_30,
                    "seed_release_shuffle": seed_release_shuffle,
                    "seed_commitment": seed_commit,
                    "cohort_seed_commitment": seed_commit,
                    "allocated_candidate_ids": [m["candidate_uid"] for m in mapping_restricted],
                    "b_subset_candidate_ids": [m["candidate_uid"] for m in mapping_restricted if m["is_b_kappa_sample"]],
                    "b_indices_in_lot100": [idx for idx, m in enumerate(mapping_restricted) if m["is_b_kappa_sample"]],
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


def supersede_lot_sampling(
    sorted_candidates: List[Dict[str, Any]],
    *,
    ledger: LotManagementLedger,
    lot_id: str,
    new_blind_salt: str,
    new_seed_release_shuffle: int,
    actor: str = "Member C (Nguyễn Thắng)",
    codebook_version: str = "1.1.0",
    blind_contract_version: str = "1.2.0",
) -> SamplingResult:
    """Tái cấp ID trung tính và thứ tự hiển thị phát hành cho một lô đã niêm phong (Supersede), bảo toàn 100% cohort A và B."""
    existing_details = ledger.get_active_lot_details(lot_id)
    if not existing_details:
        raise ValueError(f"Không tìm thấy lô đang hoạt động để supersede: '{lot_id}'")

    pop_hash = compute_population_fingerprint(sorted_candidates)
    prior_pop_hash = existing_details.get("population_hash")
    if prior_pop_hash and prior_pop_hash != pop_hash:
        raise ValueError(f"Không thể supersede lô '{lot_id}': Quần thể ứng viên không khớp hash đã niêm phong!")

    # Lập bản đồ tra cứu ứng viên
    cand_map: Dict[str, Dict[str, Any]] = {}
    pop_index_by_uid: Dict[str, int] = {}
    for idx, c in enumerate(sorted_candidates):
        c_uid = (
            c.get("candidate_uid")
            or c.get("sample_uid")
            or hashlib.sha256(c.get("url", "").encode("utf-8")).hexdigest()[:16]
        )
        cand_map[c_uid] = c
        pop_index_by_uid[c_uid] = idx

    # Bảo toàn nguyên vẹn 100 mẫu A và 30 mẫu B
    allocated_uids = existing_details.get("allocated_candidate_ids")
    if not allocated_uids or len(allocated_uids) != 100 or len(set(allocated_uids)) != 100:
        raise ValueError(f"LỖI SUPERSÈDE: Lô '{lot_id}' không có đủ 100 candidate_uids duy nhất!")

    b_subset_raw = existing_details.get("b_subset_candidate_ids")
    b_indices_raw = existing_details.get("b_indices_in_lot100")
    if not b_subset_raw and not b_indices_raw:
        raise ValueError(f"LỖI SUPERSÈDE: Lô '{lot_id}' thiếu thông tin niêm phong tập B30 (cả b_subset_candidate_ids và b_indices_in_lot100 đều thiếu)!")

    if b_subset_raw:
        b_subset_uids = set(b_subset_raw)
    elif b_indices_raw:
        b_subset_uids = {allocated_uids[i] for i in b_indices_raw if 0 <= i < len(allocated_uids)}
    else:
        raise ValueError(f"LỖI SUPERSÈDE: Lô '{lot_id}' thiếu tập B30!")

    if len(b_subset_uids) != 30 or not b_subset_uids.issubset(set(allocated_uids)):
        raise ValueError(f"LỖI SUPERSÈDE: Tập B30 không đủ 30 mẫu duy nhất hoặc không phải tập con của A100 ({len(b_subset_uids)} mẫu)!")

    lot_100 = [cand_map[uid] for uid in allocated_uids]
    b_subset_set = {i for i, c in enumerate(lot_100) if (c.get("candidate_uid") or c.get("sample_uid") or hashlib.sha256(c.get("url", "").encode("utf-8")).hexdigest()[:16]) in b_subset_uids}

    mapping_restricted: List[Dict[str, Any]] = []
    lot_100_with_blind: List[Tuple[Dict[str, Any], Dict[str, Any]]] = []
    seen_blind_ids: Set[str] = set()

    for idx, sample in enumerate(lot_100):
        c_uid = (
            sample.get("candidate_uid")
            or sample.get("sample_uid")
            or hashlib.sha256(sample.get("url", "").encode("utf-8")).hexdigest()[:16]
        )
        b_id = generate_blind_id(new_blind_salt, c_uid)
        if b_id in seen_blind_ids:
            b_id = generate_blind_id(f"{new_blind_salt}_{idx}", c_uid)
        seen_blind_ids.add(b_id)

        is_for_b = idx in b_subset_set
        assigned_to = ["A", "B"] if is_for_b else ["A"]

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
        assert_no_label_leak(blind_sample)

        s_row = sample.get("source_row")
        if s_row is None or type(s_row) is not int or s_row < 0:
            raise ValueError(f"THIẾU PROVENANCE: Mẫu '{c_uid}' thiếu locator source_row!")

        sample_content_hash = compute_sample_content_hash(blind_sample)
        mapping_entry = {
            "blind_id": b_id,
            "candidate_uid": c_uid,
            "url": sample.get("url", ""),
            "url_normalized": normalize_url(sample.get("url", "")),
            "url_sha256": hashlib.sha256(sample.get("url", "").encode("utf-8")).hexdigest(),
            "html_sha256": hashlib.sha256((sample.get("html") or "").encode("utf-8")).hexdigest(),
            "sample_content_hash": sample_content_hash,
            "canonical_pop_index": pop_index_by_uid[c_uid],
            "assigned_to": assigned_to,
            "is_b_kappa_sample": is_for_b,
            "source_label": sample.get("source_label") or sample.get("label"),
            "source_shard": sample.get("source_shard", "train-001.parquet"),
            "source_row": s_row,
            "source_revision": sample.get("source_revision", "eabec4b7a66324b79cc8a0ad856d1731dc26fe1a"),
        }
        mapping_restricted.append(mapping_entry)
        lot_100_with_blind.append((blind_sample, mapping_entry))

    # Xáo trộn thứ tự phát hành mới
    rng_shuffle_a = random.Random(new_seed_release_shuffle)
    shuffled_lot_a = list(lot_100_with_blind)
    rng_shuffle_a.shuffle(shuffled_lot_a)
    blind_view_a = [item[0] for item in shuffled_lot_a]
    for order, (b_sample, m_entry) in enumerate(shuffled_lot_a):
        m_entry["presentation_order_a"] = order

    rng_shuffle_b = random.Random(new_seed_release_shuffle + 1000)
    b_candidates = [item for item in lot_100_with_blind if item[1]["is_b_kappa_sample"]]
    shuffled_lot_b = list(b_candidates)
    rng_shuffle_b.shuffle(shuffled_lot_b)
    blind_view_b = [item[0] for item in shuffled_lot_b]
    for order, (b_sample, m_entry) in enumerate(shuffled_lot_b):
        m_entry["presentation_order_b"] = order

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

    s_lot_100 = existing_details.get("seed_lot_100")
    s_b_30 = existing_details.get("seed_b_subset_30")
    if s_lot_100 is None or s_b_30 is None:
        raise ValueError(
            f"LỖI THIẾU SEED METADATA: Ledger thiếu 'seed_lot_100' hoặc 'seed_b_subset_30' cho lot '{lot_id}'. "
            "Dừng an toàn để khôi phục metadata có bằng chứng hoặc thực hiện quy trình migration riêng của Lead D."
        )
    new_seed_commit = compute_seed_commitment(s_lot_100, s_b_30, new_seed_release_shuffle, new_blind_salt)

    event = ledger.append_event(
        event_type="SUPERSEDE_LOT_BLIND_VIEW",
        actor=actor,
        lot_id=lot_id,
        status="RESERVED",
        details={
            "prior_seed_commitment": existing_details.get("seed_commitment"),
            "new_seed_commitment": new_seed_commit,
            "seed_commitment": new_seed_commit,
            "cohort_seed_commitment": existing_details.get("cohort_seed_commitment") or existing_details.get("seed_commitment"),
            "seed_lot_100": s_lot_100,
            "seed_b_subset_30": s_b_30,
            "seed_release_shuffle": new_seed_release_shuffle,
            "blind_salt_hash": hashlib.sha256(new_blind_salt.encode("utf-8")).hexdigest(),
            "population_hash": pop_hash,
            "allocated_candidate_ids": allocated_uids,
            "b_subset_candidate_ids": list(b_subset_uids),
            "b_indices_in_lot100": existing_details.get("b_indices_in_lot100", []),
            "blind_ids": [m["blind_id"] for m in mapping_restricted],
            "reason": "Supersede blind IDs and release shuffle after salt incident while preserving original cohort",
        },
    )

    return SamplingResult(
        population_count=len(sorted_candidates),
        population_hash=pop_hash,
        lot_100_blind_ids=[m["blind_id"] for m in mapping_restricted],
        b_subset_30_blind_ids=[m["blind_id"] for m in mapping_restricted if m["is_b_kappa_sample"]],
        seed_commitment=new_seed_commit,
        mapping_restricted=mapping_restricted,
        blind_view_a=blind_view_a,
        blind_view_b=blind_view_b,
        ledger_event_seq=event.seq,
        blind_view_a_envelope=envelope_a,
        blind_view_b_envelope=envelope_b,
    )
