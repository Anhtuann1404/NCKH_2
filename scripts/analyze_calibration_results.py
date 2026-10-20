#!/usr/bin/env python3
"""Phân tích chi tiết kết quả Calibration Pass 1 giữa A và B."""
import json
from pathlib import Path
import sys

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
kappa_json_path = ROOT / "tmp/kappa_calibration_v1_1_4.json"
data = json.loads(kappa_json_path.read_text(encoding="utf-8"))

rows_a = [json.loads(line) for line in (ROOT / "data/annotations/A/calibration_pass1.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
rows_b = [json.loads(line) for line in (ROOT / "data/annotations/B/calibration_pass1.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]

map_a = {r["sample_id"]: r for r in rows_a}
map_b = {r["sample_id"]: r for r in rows_b}

print(f"Tổng số mẫu ghép cặp: {data['paired_sample_count']}")
cl = data['kappa']['class_label']
print(f"Class Label Kappa: {cl['kappa']:.4f} (Observed: {cl['observed_agreement']*100:.2f}%)")

print("\n--- CÁC CA BẤT ĐỒNG THUẬN VỀ CLASS_LABEL ---")
cl_diffs = []
for d in data['disagreements']:
    la = d['label_a']
    lb = d['label_b']
    if la != lb:
        sid = d['sample_id']
        cl_diffs.append(d)
        ra = map_a[sid]
        rb = map_b[sid]
        print(f"\nMẫu: {sid}")
        print(f"  Annotator A (Khải):")
        print(f"    - Nhãn: {la}")
        print(f"    - Tổ chức: {d['org_a']}")
        print(f"    - Confidence: {ra.get('confidence')}")
        print(f"    - Kiểu: phishing_type={ra.get('primary_phishing_type')}, hard_benign={ra.get('hard_benign_type')}")
        print(f"    - Ghi chú: {d['evidence_note_a']}")
        print(f"  Annotator B (Tấn Minh):")
        print(f"    - Nhãn: {lb}")
        print(f"    - Tổ chức: {d['org_b']}")
        print(f"    - Confidence: {rb.get('confidence')}")
        print(f"    - Kiểu: phishing_type={rb.get('primary_phishing_type')}, hard_benign={rb.get('hard_benign_type')}")
        print(f"    - Ghi chú: {d['evidence_note_b']}")

print(f"\nTổng số ca bất đồng thuận class_label: {len(cl_diffs)}/24")

print("\n--- PHÂN TÍCH THỜI GIAN GÁN NHÃN ---")
sa = data['seconds_spent']['rater_a']['overall']
sb = data['seconds_spent']['rater_b']['overall']
print(f"Annotator A: Tổng = {sa['total']/60:.2f} phút ({sa['total']:.1f}s) | Trung bình = {sa['mean']:.1f}s/mẫu ({sa['mean']/60:.2f}p) | Median = {sa['median']:.1f}s")
print(f"Annotator B: Tổng = {sb['total']/60:.2f} phút ({sb['total']:.1f}s) | Trung bình = {sb['mean']:.1f}s/mẫu ({sb['mean']/60:.2f}p) | Median = {sb['median']:.1f}s")

conf_a = {c: sum(1 for r in rows_a if r.get("confidence") == c) for c in ["low", "medium", "high"]}
conf_b = {c: sum(1 for r in rows_b if r.get("confidence") == c) for c in ["low", "medium", "high"]}
print("\n--- PHÂN BỔ CONFIDENCE ---")
print(f"Annotator A: low={conf_a['low']}, medium={conf_a['medium']}, high={conf_a['high']}")
print(f"Annotator B: low={conf_b['low']}, medium={conf_b['medium']}, high={conf_b['high']}")

# Kiểm tra tương quan giữa bất đồng thuận và confidence
print("\n--- CONFIDENCE TẠI 2 CA BẤT ĐỒNG THUẬN CLASS_LABEL ---")
for d in cl_diffs:
    sid = d['sample_id']
    print(f"Mẫu {sid}: A={map_a[sid].get('confidence')} ({map_a[sid]['class_label']}) vs B={map_b[sid].get('confidence')} ({map_b[sid]['class_label']})")
