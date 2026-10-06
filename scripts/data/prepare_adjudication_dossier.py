"""Chuẩn bị hồ sơ và nghị trình phiên phân xử (Adjudication Dossier & Agenda).

Tuân thủ nghiêm ngặt nguyên tắc Academic Research Skills (ARS):
- Chỉ sử dụng nội dung Blind View an toàn và bằng chứng, ghi chú của A và B.
- Tuyệt đối KHÔNG đọc nhãn nguồn, ground-truth, điểm mô hình hay Official Test.
- Lưu toàn bộ hồ sơ chi tiết trong thư mục hạn chế (data/labels/intake_v2/ - gitignored).
- Chuẩn bị template sẵn sàng cho labels_final.json, chưa ghi nhãn phân xử khi chưa họp.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from scripts.data.analyze_pass1_v2 import to_canonical_json_bytes, write_canonical_json

DISAGREEMENT_TABLE_PATH = PROJECT_ROOT / "data" / "labels" / "intake_v2" / "adjudication_disagreement_table.json"
BLIND_VIEW_PATH = PROJECT_ROOT / "data" / "annotations" / "blind_view_pilot_real_v2.json"
OUT_DOSSIER_PATH = PROJECT_ROOT / "data" / "labels" / "intake_v2" / "adjudication_dossier.json"
OUT_AGENDA_MD_PATH = PROJECT_ROOT / "data" / "labels" / "intake_v2" / "adjudication_agenda.md"
TEMPLATE_FINAL_PATH = PROJECT_ROOT / "data" / "labels" / "intake_v2" / "labels_final_template.json"


def prepare_dossier(
    disagreement_table_path: Path = DISAGREEMENT_TABLE_PATH,
    blind_view_path: Path = BLIND_VIEW_PATH,
) -> dict[str, Any]:
    if not disagreement_table_path.is_file():
        raise FileNotFoundError(f"Không tìm thấy bảng bất đồng: {disagreement_table_path}")
    if not blind_view_path.is_file():
        raise FileNotFoundError(f"Không tìm thấy blind view: {blind_view_path}")

    tbl_data = json.loads(disagreement_table_path.read_text(encoding="utf-8"))
    bv_data = json.loads(blind_view_path.read_text(encoding="utf-8"))
    samples_map = {s["sample_id"]: s for s in bv_data.get("samples", [])}

    disagreements = tbl_data.get("disagreements", [])

    # Phân loại các ca
    class_disagreements = []
    anomaly_only_cases = []
    org_only_disagreements = []

    for r in disagreements:
        sid = r["sample_id"]
        s_view = samples_map.get(sid, {})
        url_preview = s_view.get("url_hint") or s_view.get("url") or "N/A"
        title_preview = s_view.get("title") or "N/A"
        text_snippet = (s_view.get("page_text") or "")[:200].replace("\n", " ").strip()

        case_item = {
            "sample_id": sid,
            "url_preview": url_preview,
            "title_preview": title_preview,
            "text_snippet": text_snippet,
            "class_label_a": r["class_label_a"],
            "class_label_b": r["class_label_b"],
            "class_disagreement": r["class_disagreement"],
            "primary_org_raw_a": r["primary_org_raw_a"],
            "primary_org_raw_b": r["primary_org_raw_b"],
            "primary_org_norm_a": r["primary_org_norm_a"],
            "primary_org_norm_b": r["primary_org_norm_b"],
            "org_disagreement": r["org_disagreement"],
            "consistency_anomaly_a": r.get("consistency_anomaly_a"),
            "consistency_anomaly_b": r.get("consistency_anomaly_b"),
            "difficult_case_a": r.get("difficult_case_a", False),
            "difficult_case_b": r.get("difficult_case_b", False),
            "evidence_note_a": r.get("evidence_note_a", ""),
            "evidence_note_b": r.get("evidence_note_b", ""),
        }

        if r["class_disagreement"]:
            class_disagreements.append(case_item)
        elif r.get("consistency_anomaly_a") or r.get("consistency_anomaly_b"):
            anomaly_only_cases.append(case_item)
        elif r["org_disagreement"]:
            org_only_disagreements.append(case_item)

    # Phân nhóm 14 ca bất đồng class_label theo pattern
    class_patterns = {
        "A=benign / B=phishing": [c for c in class_disagreements if c["class_label_a"] == "benign" and c["class_label_b"] == "phishing"],
        "A=insufficient_evidence / B=benign": [c for c in class_disagreements if c["class_label_a"] == "insufficient_evidence" and c["class_label_b"] == "benign"],
        "A=insufficient_evidence / B=phishing": [c for c in class_disagreements if c["class_label_a"] == "insufficient_evidence" and c["class_label_b"] == "phishing"],
        "A=phishing / B=insufficient_evidence": [c for c in class_disagreements if c["class_label_a"] == "phishing" and c["class_label_b"] == "insufficient_evidence"],
        "A=benign / B=insufficient_evidence": [c for c in class_disagreements if c["class_label_a"] == "benign" and c["class_label_b"] == "insufficient_evidence"],
    }

    # Tổng hợp tất cả các ca có anomaly (cả có lệch class và không lệch class)
    all_anomalies = [c for c in (class_disagreements + anomaly_only_cases + org_only_disagreements) if c["consistency_anomaly_a"] or c["consistency_anomaly_b"]]

    dossier = {
        "dataset_id": bv_data.get("dataset_id", "REAL-PILOT-32-V2"),
        "total_adjudication_cases": len(disagreements),
        "priority_1_class_disagreements": {
            "count": len(class_disagreements),
            "patterns": {name: [c["sample_id"] for c in items] for name, items in class_patterns.items()},
            "cases": class_disagreements,
        },
        "priority_2_consistency_anomalies": {
            "total_samples_affected": len(all_anomalies),
            "rater_a_count": sum(1 for c in all_anomalies if c["consistency_anomaly_a"]),
            "rater_b_count": sum(1 for c in all_anomalies if c["consistency_anomaly_b"]),
            "cases": all_anomalies,
        },
        "priority_3_org_only_disagreements": {
            "count": len(org_only_disagreements),
            "cases": org_only_disagreements,
        },
    }

    return dossier


def render_agenda_markdown(dossier: dict[str, Any]) -> str:
    lines = []
    lines.append("# NGHỊ TRÌNH PHIÊN PHÂN XỬ PILOT PASS 1 (REAL-PILOT-32-V2)")
    lines.append("")
    lines.append("> **LƯU Ý BẢO MẬT & HỌC THUẬT (ARS):**")
    lines.append("> - Nghị trình chỉ sử dụng nội dung an toàn từ Blind View và bằng chứng do Annotator A/B ghi nhận.")
    lines.append("> - Tuyệt đối không đọc nhãn nguồn, ground-truth, điểm mô hình hay Official Test.")
    lines.append("> - File này nằm trong khu vực hạn chế (`data/labels/intake_v2/`), không đưa lên Git.")
    lines.append("")
    lines.append(f"**Tổng số ca cần phân xử:** {dossier['total_adjudication_cases']} ca.")
    lines.append("")

    # Nhóm 1
    p1 = dossier["priority_1_class_disagreements"]
    lines.append(f"## 1. ƯU TIÊN 1: 14 CA BẤT ĐỒNG NHÃN LỚP (class_label)")
    lines.append("")
    for pat_name, pat_cases in p1["patterns"].items():
        lines.append(f"### Nhóm: {pat_name} ({len(pat_cases)} ca: {', '.join(pat_cases)})")
        lines.append("")
        for sid in pat_cases:
            c = next(item for item in p1["cases"] if item["sample_id"] == sid)
            lines.append(f"#### Mẫu `{sid}`")
            lines.append(f"- **URL hint:** `{c['url_preview']}`")
            lines.append(f"- **Tiêu đề:** {c['title_preview']}")
            lines.append(f"- **Nhãn A:** `{c['class_label_a']}` (difficult: {c['difficult_case_a']}) | Ghi chú: *\"{c['evidence_note_a']}\"*")
            lines.append(f"- **Nhãn B:** `{c['class_label_b']}` (difficult: {c['difficult_case_b']}) | Ghi chú: *\"{c['evidence_note_b']}\"*")
            lines.append(f"- **Trích dẫn nội dung:** \"{c['text_snippet']}\"")
            if c["consistency_anomaly_a"] or c["consistency_anomaly_b"]:
                lines.append(f"- ⚠️ **Anomaly:** A: `{c['consistency_anomaly_a']}` | B: `{c['consistency_anomaly_b']}`")
            lines.append(f"- **Câu hỏi phân xử:** A và B trình bày bằng chứng văn bản/DOM để xác định rõ giữa `{c['class_label_a']}` và `{c['class_label_b']}`.")
            lines.append("")

    # Nhóm 2
    p2 = dossier["priority_2_consistency_anomalies"]
    lines.append(f"## 2. ƯU TIÊN 2: {p2['total_samples_affected']} CA MÂU THUẪN LOGIC (Consistency Anomalies)")
    lines.append("")
    lines.append("Các ca có `primary_org_status = 'identified'` nhưng `primary_org` lại là `unknown` hoặc `no_clear_target`.")
    lines.append(f"- Annotator A: {p2['rater_a_count']} ca | Annotator B: {p2['rater_b_count']} ca.")
    lines.append("")
    for c in p2["cases"]:
        lines.append(f"- **`{c['sample_id']}`**: A=`{c['primary_org_norm_a']}` (anomaly: {c['consistency_anomaly_a']}) | B=`{c['primary_org_norm_b']}` (anomaly: {c['consistency_anomaly_b']})")
        lines.append(f"  + URL: `{c['url_preview']}` | Title: `{c['title_preview']}`")
        lines.append(f"  + Trọng tâm: Làm rõ người gán nhãn thực sự nhận diện được tổ chức nào hay bấm nhầm trạng thái status sang identified?")
        lines.append("")

    # Nhóm 3
    p3 = dossier["priority_3_org_only_disagreements"]
    lines.append(f"## 3. ƯU TIÊN 3: {p3['count']} CA BẤT ĐỒNG TỔ CHỨC ĐƠN THUẦN (Sau chuẩn hóa, cùng class_label)")
    lines.append("")
    for c in p3["cases"]:
        lines.append(f"- **`{c['sample_id']}`**: Cùng lớp `{c['class_label_a']}` | A=`{c['primary_org_norm_a']}` vs B=`{c['primary_org_norm_b']}`")
        lines.append(f"  + Note A: *\"{c['evidence_note_a']}\"* | Note B: *\"{c['evidence_note_b']}\"*")
        lines.append("")

    lines.append("## 4. QUY TRÌNH KẾT THÚC PHÂN XỬ")
    lines.append("1. Lead D chủ trì, A và B đối thoại bằng chứng.")
    lines.append("2. Ghi nhận kết quả thống nhất vào `data/labels/intake_v2/labels_final.json`.")
    lines.append("3. Giữ nguyên 100% hai file Pass 1 gốc của A và B để bảo toàn Kappa trước phân xử.")
    return "\n".join(lines) + "\n"


def create_labels_final_template(dossier: dict[str, Any]) -> dict[str, Any]:
    """Tạo file template trống sẵn sàng cho phiên phân xử."""
    all_sids = [f"PILOT-{i:03d}" for i in range(1, 33)]
    return {
        "dataset_id": dossier["dataset_id"],
        "adjudication_status": "pending_session",
        "adjudicated_by": "Lead D (Anh Tuan)",
        "participants": ["Annotator A", "Annotator B", "Member C", "Lead D"],
        "records": [
            {
                "sample_id": sid,
                "final_class_label": None,
                "final_primary_org": None,
                "final_primary_org_status": None,
                "requires_adjudication": sid in [c["sample_id"] for c in dossier["priority_1_class_disagreements"]["cases"] + dossier["priority_2_consistency_anomalies"]["cases"] + dossier["priority_3_org_only_disagreements"]["cases"]],
                "adjudication_rationale": "",
                "agreed_unanimously": False,
            }
            for sid in all_sids
        ],
    }


def main() -> int:
    dossier = prepare_dossier()

    # 1. Ghi dossier JSON canonical
    dossier_hash = write_canonical_json(OUT_DOSSIER_PATH, dossier)
    print(f"[DOSSIER] Đã tạo: {OUT_DOSSIER_PATH} (SHA-256: {dossier_hash})")

    # 2. Ghi agenda Markdown
    agenda_md = render_agenda_markdown(dossier)
    agenda_bytes = agenda_md.replace("\r\n", "\n").encode("utf-8")
    OUT_AGENDA_MD_PATH.write_bytes(agenda_bytes)
    agenda_hash = hashlib.sha256(agenda_bytes).hexdigest()
    print(f"[AGENDA]  Đã tạo: {OUT_AGENDA_MD_PATH} (SHA-256: {agenda_hash})")

    # 3. Ghi template labels_final
    template = create_labels_final_template(dossier)
    template_hash = write_canonical_json(TEMPLATE_FINAL_PATH, template)
    print(f"[TEMPLATE] Đã tạo: {TEMPLATE_FINAL_PATH} (SHA-256: {template_hash})")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
