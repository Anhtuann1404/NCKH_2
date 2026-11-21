#!/usr/bin/env python3
"""Intake pipeline cho Main Annotation Đợt 1 (Hợp đồng Main v1.2.0).

Tiếp nhận tệp kết quả JSONL từ Annotator A (100 mẫu) hoặc B (30 mẫu),
đối chiếu với gói Blind View và manifest hạn chế đã niêm phong,
không yêu cầu hay chấp nhận trường 'random_subset' của pilot.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import re
import sys
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from phishing.annotation.blind_view import (
    BLIND_CONTRACT_VERSION_V1_2_0,
    compute_sample_content_hash,
    validate_annotation_record,
)


def compute_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    records = []
    with path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            line_str = line.strip()
            if not line_str:
                continue
            try:
                records.append(json.loads(line_str))
            except json.JSONDecodeError as exc:
                raise ValueError(f"Lỗi cú pháp JSON tại dòng {line_no} của '{path}': {exc}")
    return records


def verify_main_batch1_records(
    records: List[Dict[str, Any]],
    annotator: str,
    manifest_path: Path,
    view_path: Path,
) -> Dict[str, Any]:
    """Kiểm tra toàn diện tệp kết quả gán nhãn Main Đợt 1 đối chiếu với Blind View và manifest."""
    if annotator not in {"A", "B"}:
        raise ValueError("annotator phải là 'A' hoặc 'B' trong Main Đợt 1")

    expected_count = 100 if annotator == "A" else 30

    if not manifest_path.exists():
        raise FileNotFoundError(f"Không tìm thấy manifest tại '{manifest_path}'")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    # Kiểm tra quyền phát hành chính thức (chặn manifest pending / chưa duyệt)
    if manifest.get("ready_for_annotation") is not True or manifest.get("acceptance") != {"B": "approved", "D": "approved"}:
        raise ValueError(
            "LỖI QUYỀN PHÁT HÀNH: Manifest chưa được phê duyệt chính thức (yêu cầu ready_for_annotation=True và acceptance={'B': 'approved', 'D': 'approved'})!"
        )

    if manifest.get("blind_contract_version") != BLIND_CONTRACT_VERSION_V1_2_0:
        raise ValueError(
            f"Manifest không thuộc hợp đồng Main 1.2.0 (nhận '{manifest.get('blind_contract_version')}')"
        )
    if manifest.get("sample_count") != expected_count:
        raise ValueError(
            f"Manifest sample_count ({manifest.get('sample_count')}) không khớp kỳ vọng {expected_count} cho {annotator}"
        )

    if not view_path.exists():
        raise FileNotFoundError(f"Không tìm thấy blind view tại '{view_path}'")
    view_sha = compute_sha256(view_path)
    if view_sha != manifest.get("blind_view_sha256"):
        raise ValueError(
            f"Blind view SHA-256 ('{view_sha}') không khớp manifest ('{manifest.get('blind_view_sha256')}')"
        )

    view_data = json.loads(view_path.read_text(encoding="utf-8"))
    if view_data.get("blind_contract_version") != BLIND_CONTRACT_VERSION_V1_2_0:
        raise ValueError("Blind view envelope thiếu hoặc không khớp blind_contract_version='1.2.0'")
    if "samples" not in view_data or not isinstance(view_data["samples"], list):
        raise ValueError("Blind view envelope thiếu danh sách 'samples'")

    samples_list = view_data["samples"]
    if len(samples_list) != expected_count:
        raise ValueError(
            f"Blind view chứa {len(samples_list)} mẫu, kỳ vọng đúng {expected_count} cho {annotator}"
        )

    samples_by_id = {}
    for s in samples_list:
        sid = s.get("sample_id", "")
        if not re.match(r"^BLIND-[a-f0-9]{8}$", str(sid)):
            raise ValueError(f"Blind view chứa sample_id '{sid}' không đúng định dạng BLIND-xxxxxxxx")
        if sid in samples_by_id:
            raise ValueError(f"Blind view chứa sample_id trùng lặp: '{sid}'")
        samples_by_id[sid] = s

    if len(records) != expected_count:
        raise ValueError(
            f"Tệp kết quả chứa {len(records)} bản ghi, kỳ vọng đúng {expected_count} bản ghi hoàn chỉnh cho {annotator}"
        )

    expected_provenance = {
        "dataset_id": manifest.get("dataset_id"),
        "dataset_hash": manifest.get("blind_view_sha256"),
        "codebook_version": manifest.get("codebook_version"),
        "codebook_hash": manifest.get("codebook_sha256"),
        "sampling_plan_version": manifest.get("sampling_plan_version"),
    }

    seen_rec_ids = set()
    for idx, record in enumerate(records, start=1):
        rec_annotator = record.get("annotator_id")
        if rec_annotator != annotator:
            raise ValueError(
                f"Dòng {idx}: Bản ghi có annotator_id='{rec_annotator}', không khớp '{annotator}'"
            )

        if record.get("pass_id") != 1:
            raise ValueError(
                f"Dòng {idx}: pass_id={record.get('pass_id')!r} không hợp lệ, tiếp nhận chính thức Main Đợt 1 chỉ chấp nhận pass_id=1"
            )

        if type(record.get("is_dry_run")) is not bool or record.get("is_dry_run") is not False:
            raise ValueError(
                f"Dòng {idx}: is_dry_run={record.get('is_dry_run')!r} không hợp lệ, phải là boolean False thật trong kết quả chính thức"
            )

        if type(record.get("is_synthetic")) is not bool or record.get("is_synthetic") is not False:
            raise ValueError(
                f"Dòng {idx}: is_synthetic={record.get('is_synthetic')!r} không hợp lệ, phải là boolean False thật trong kết quả chính thức"
            )

        sid = record.get("sample_id")
        if sid not in samples_by_id:
            raise ValueError(f"Dòng {idx}: sample_id='{sid}' không tồn tại trong Blind View {annotator}")
        if sid in seen_rec_ids:
            raise ValueError(f"Dòng {idx}: sample_id='{sid}' xuất hiện trùng lặp trong tệp kết quả")
        seen_rec_ids.add(sid)

        # Chặn tuyệt đối random_subset của pilot trong Main 1.2.0
        if "random_subset" in record:
            raise ValueError(
                f"Dòng {idx}: Trường 'random_subset' bị cấm tuyệt đối trong bản ghi Main 1.2.0"
            )

        # Kiểm tra provenance
        for pf, pval in expected_provenance.items():
            if record.get(pf) != pval:
                raise ValueError(
                    f"Dòng {idx} ({sid}): Trường {pf} ('{record.get(pf)}') không khớp kỳ vọng ('{pval}')"
                )

        # Kiểm tra tính toàn vẹn nội dung mẫu bằng hàm canonical
        curr_sample = samples_by_id[sid]
        expected_content_hash = compute_sample_content_hash(curr_sample)
        if record.get("sample_content_hash") != expected_content_hash:
            raise ValueError(
                f"Dòng {idx} ({sid}): sample_content_hash ('{record.get('sample_content_hash')}') "
                f"không khớp nội dung mẫu ('{expected_content_hash}')"
            )

        # Kiểm tra thời gian thao tác
        sec = record.get("seconds_spent")
        if type(sec) not in (int, float) or not math.isfinite(sec) or sec < 0:
            raise ValueError(f"Dòng {idx} ({sid}): seconds_spent ({sec!r}) phải là số hữu hạn không âm")

        # Xác thực toàn bộ ràng buộc của Codebook và hợp đồng Main 1.2.0
        validate_annotation_record(record)

    if seen_rec_ids != set(samples_by_id.keys()):
        missing_ids = sorted(list(set(samples_by_id.keys()) - seen_rec_ids))
        raise ValueError(f"Tệp kết quả thiếu {len(missing_ids)} mẫu trong Blind View: {missing_ids[:5]}...")

    return {
        "annotator": annotator,
        "sample_count": expected_count,
        "manifest_sha256": compute_sha256(manifest_path),
        "blind_view_sha256": view_sha,
        "contract_version": BLIND_CONTRACT_VERSION_V1_2_0,
    }


def _check_accepted_history(
    ann_dir: Path,
    annotator: str,
    current_digest: str,
    dataset_id: str | None,
    contract_version: str | None,
    d_replacement_approval: str | None = None,
) -> None:
    """Quét toàn bộ lịch sử (cả receipt và attempt) để khóa bản nộp khi đã có ACCEPTED."""
    for p in sorted(ann_dir.glob("*.json")):
        if not (p.name.endswith(".receipt.json") or ".attempt_" in p.name):
            continue
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except Exception as exc:
            raise RuntimeError(
                f"LỖI BẢO TOÀN LỊCH SỬ: Không thể đọc tệp lịch sử biên lai '{p}': {exc}. Dừng an toàn để bảo vệ tính toàn vẹn!"
            )
        if data.get("status") == "accepted":
            is_same_annotator = data.get("annotator") == annotator
            is_same_release = (
                (dataset_id is not None and data.get("dataset_id") == dataset_id)
                or (contract_version is not None and data.get("contract_version") == contract_version)
                or (data.get("dataset_type") == "main_annotation_batch1")
            )
            if is_same_annotator and is_same_release:
                accepted_digest = data.get("file_sha256")
                if accepted_digest and accepted_digest != current_digest:
                    raise ValueError(
                        f"Đã tồn tại bản nộp ACCEPTED khác cho annotator {annotator} "
                        f"(tệp lịch sử: {p.name}, digest: {accepted_digest}). "
                        "Thay thế bản nộp chưa được hỗ trợ tự động trong pipeline intake; "
                        "mọi trường hợp thay thế cần quyết định và quy trình xử lý riêng của Lead D."
                    )


def receive_main_batch1(
    input_path: Path | str,
    annotator: str,
    *,
    out_root: Path | str = "data/labels/intake_main_batch1",
    restricted_dir: Path | str = "data/restricted/main_batch1",
    d_replacement_approval: str | None = None,
) -> Dict[str, Any]:
    """Tiếp nhận tệp JSONL Main Đợt 1, bảo toàn byte và xuất biên lai kiểm toán."""
    p_in = Path(input_path)
    p_out = Path(out_root)
    p_rest = Path(restricted_dir)

    if annotator not in {"A", "B"}:
        raise ValueError("annotator phải là 'A' hoặc 'B'")

    raw = p_in.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()

    ann_dir = p_out / annotator
    ann_dir.mkdir(parents=True, exist_ok=True)
    saved_jsonl = ann_dir / f"{digest}.jsonl"

    if not saved_jsonl.exists():
        saved_jsonl.write_bytes(raw)
    elif saved_jsonl.read_bytes() != raw:
        raise ValueError("Xung đột SHA-256: Tệp cùng mã băm nhưng nội dung byte khác nhau!")

    manifest_file = p_rest / ("manifest_a.json" if annotator == "A" else "manifest_b.json")
    view_file = p_rest / ("blind_view_a.json" if annotator == "A" else "blind_view_b.json")

    # 1. Thu nhận fingerprint context trước bước kiểm nghiệp vụ (cho cả accepted và rejected)
    manifest_sha256 = None
    manifest_read_error = None
    manifest_data = None
    if not manifest_file.exists():
        manifest_read_error = f"FileNotFound: {manifest_file}"
    else:
        try:
            m_bytes = manifest_file.read_bytes()
            manifest_sha256 = hashlib.sha256(m_bytes).hexdigest()
            try:
                manifest_data = json.loads(m_bytes.decode("utf-8"))
            except Exception as exc:
                manifest_read_error = f"JSONDecodeError: {exc}"
        except Exception as exc:
            manifest_read_error = f"ReadError: {exc}"

    view_sha256 = None
    view_read_error = None
    if not view_file.exists():
        view_read_error = f"FileNotFound: {view_file}"
    else:
        try:
            v_bytes = view_file.read_bytes()
            view_sha256 = hashlib.sha256(v_bytes).hexdigest()
        except Exception as exc:
            view_read_error = f"ReadError: {exc}"

    dataset_id = manifest_data.get("dataset_id") if isinstance(manifest_data, dict) else None
    contract_version = (
        manifest_data.get("blind_contract_version")
        if isinstance(manifest_data, dict) and manifest_data.get("blind_contract_version")
        else BLIND_CONTRACT_VERSION_V1_2_0
    )

    receipt: Dict[str, Any] = {
        "dataset_type": "main_annotation_batch1",
        "annotator": annotator,
        "contract_version": contract_version,
        "file_sha256": digest,
        "saved_path": str(saved_jsonl),
        "tool_version": "1.2.0",
        "manifest_path": str(manifest_file),
        "view_path": str(view_file),
        "manifest_sha256": manifest_sha256,
        "blind_view_sha256": view_sha256,
    }
    if dataset_id:
        receipt["dataset_id"] = dataset_id
    if manifest_read_error:
        receipt["manifest_read_error"] = manifest_read_error
    if view_read_error:
        receipt["view_read_error"] = view_read_error
    if d_replacement_approval:
        receipt["d_replacement_approval"] = d_replacement_approval

    try:
        records = load_jsonl(saved_jsonl)
        v_res = verify_main_batch1_records(records, annotator, manifest_file, view_file)
        receipt.update(v_res)

        # 2. H1: Khóa bản nộp dựa trên toàn bộ lịch sử ACCEPTED (cả *.receipt.json và *.attempt_*.json)
        _check_accepted_history(ann_dir, annotator, digest, dataset_id, contract_version, d_replacement_approval)

        receipt["status"] = "accepted"
        receipt["reason"] = None
    except Exception as exc:
        receipt["status"] = "rejected"
        receipt["reason"] = str(exc)

    receipt_path = ann_dir / f"{digest}.receipt.json"
    if receipt_path.exists():
        try:
            prior_r = json.loads(receipt_path.read_text(encoding="utf-8"))
        except Exception as exc:
            raise RuntimeError(
                f"LỖI BẢO TOÀN BIÊN LAI: Không thể đọc biên lai gốc '{receipt_path}': {exc}. Dừng để bảo toàn byte!"
            )

        # Kiểm tra idempotent retry cùng ngữ cảnh (ràng buộc file_sha256, manifest_sha256, view_sha256, tool_version, status, reason)
        is_identical_context = (
            prior_r.get("file_sha256") == receipt.get("file_sha256")
            and prior_r.get("manifest_sha256") == receipt.get("manifest_sha256")
            and prior_r.get("blind_view_sha256") == receipt.get("blind_view_sha256")
            and prior_r.get("manifest_read_error") == receipt.get("manifest_read_error")
            and prior_r.get("view_read_error") == receipt.get("view_read_error")
            and prior_r.get("tool_version") == receipt.get("tool_version")
            and prior_r.get("status") == receipt.get("status")
            and prior_r.get("reason") == receipt.get("reason")
        )
        if is_identical_context:
            return prior_r

        # Kiểm tra idempotency trên các attempt đã ghi trước đó
        existing_attempts = sorted(ann_dir.glob(f"{digest}.attempt_*.json"))
        for att_file in existing_attempts:
            try:
                att_data = json.loads(att_file.read_text(encoding="utf-8"))
            except Exception as exc:
                raise RuntimeError(
                    f"LỖI BẢO TOÀN LỊCH SỬ: Không thể đọc attempt '{att_file}': {exc}. Dừng an toàn để bảo vệ tính toàn vẹn!"
                )
            if (
                att_data.get("file_sha256") == receipt.get("file_sha256")
                and att_data.get("manifest_sha256") == receipt.get("manifest_sha256")
                and att_data.get("blind_view_sha256") == receipt.get("blind_view_sha256")
                and att_data.get("manifest_read_error") == receipt.get("manifest_read_error")
                and att_data.get("view_read_error") == receipt.get("view_read_error")
                and att_data.get("tool_version") == receipt.get("tool_version")
                and att_data.get("status") == receipt.get("status")
                and att_data.get("reason") == receipt.get("reason")
            ):
                return att_data

        # Nếu ngữ cảnh hoặc kết quả thay đổi: BẢO LƯU NGUYÊN VẸN biên lai gốc và ghi attempt mới
        attempt_num = len(existing_attempts) + 2

        m_sha = (receipt.get("manifest_sha256") or "nomanifest")[:8]
        status_tag = receipt.get("status", "unknown")
        ctx_sig = hashlib.sha256(
            f"{digest}:{m_sha}:{status_tag}:{receipt.get('reason')}:{datetime.now(timezone.utc).isoformat()}".encode("utf-8")
        ).hexdigest()[:8]

        attempt_filename = f"{digest}.attempt_{attempt_num:02d}_{status_tag}_{ctx_sig}.json"
        attempt_path = ann_dir / attempt_filename
        while attempt_path.exists():
            attempt_num += 1
            ctx_sig = hashlib.sha256(f"{ctx_sig}:{attempt_num}".encode("utf-8")).hexdigest()[:8]
            attempt_path = ann_dir / f"{digest}.attempt_{attempt_num:02d}_{status_tag}_{ctx_sig}.json"

        receipt["attempt_index"] = attempt_num
        receipt["checked_at_utc"] = datetime.now(timezone.utc).isoformat()
        receipt["prior_receipt_path"] = str(receipt_path)

        attempt_path.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        return receipt

    receipt["attempt_index"] = 1
    receipt["checked_at_utc"] = datetime.now(timezone.utc).isoformat()
    receipt["prior_receipt_path"] = None

    receipt_path.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--annotator", choices=("A", "B"), required=True, help="Annotator ('A' hoặc 'B')")
    parser.add_argument("--input", type=Path, required=True, help="Đường dẫn tệp kết quả JSONL")
    parser.add_argument("--restricted-dir", type=Path, default=Path("data/restricted/main_batch1"), help="Thư mục gói hạn chế")
    parser.add_argument("--out-root", type=Path, default=Path("data/labels/intake_main_batch1"), help="Thư mục lưu biên lai intake")
    parser.add_argument(
        "--d-replacement-approval",
        type=str,
        default=None,
        help="Mã quyết định của Lead D (tính năng thay thế bản nộp chưa hỗ trợ tự động trong Đợt 1; mọi thay thế cần quyết định riêng từ Lead D)",
    )
    args = parser.parse_args()

    receipt = receive_main_batch1(
        args.input,
        args.annotator,
        out_root=args.out_root,
        restricted_dir=args.restricted_dir,
        d_replacement_approval=args.d_replacement_approval,
    )
    print(f"Trạng thái tiếp nhận: {receipt['status']} (Annotator {args.annotator}, SHA-256={receipt['file_sha256']})")
    if receipt["status"] != "accepted":
        print(f"Lý do từ chối: {receipt['reason']}", file=sys.stderr)
        return 1
    print(f"Đã lưu tại: {receipt['saved_path']}")
    print("Biên lai: ACCEPTED. Ghi nhận thành công đợt gán nhãn Main.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
