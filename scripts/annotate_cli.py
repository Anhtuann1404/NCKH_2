"""Script CLI hỗ trợ gán nhãn mù độc lập có bấm giờ tự động (Task LABEL-01).

Dành cho Thành viên A và B thực hiện gán nhãn theo đúng quy chuẩn docs/CODEBOOK_V1.md:
- Bấm giờ chính xác từng mẫu (seconds_spent).
- Tự động kiểm tra và xác thực enum trước khi ghi vào tệp JSON Lines.
- Hỗ trợ tạm dừng và tiếp tục (resume) mà không làm mất tiến độ gán nhãn.
- Tuyệt đối không tải mạng, không render HTML sống, không hiển thị nhãn nguồn.

Cách sử dụng:
    python scripts/annotate_cli.py --annotator A --input data/annotations/blind_view_pilot.json --output data/annotations/A/pilot_pass1.jsonl
    python scripts/annotate_cli.py --annotator B --input data/annotations/blind_view_pilot.json --output data/annotations/B/pilot_pass1.jsonl
"""

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import time
from typing import Any, Dict, List, Set

# Đảm bảo mã hóa UTF-8 an toàn trên console Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Thêm src vào sys.path để import phishing
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from phishing.annotation import (
    AnnotationRecord,
    assert_no_label_leak,
    validate_annotation_record,
)


CLASS_LABEL_CHOICES = {
    "1": "phishing",
    "2": "benign",
    "3": "insufficient_evidence",
}

PRIMARY_ORG_STATUS_CHOICES = {
    "1": "identified",
    "2": "unknown",
    "3": "no_clear_target",
    "4": "multi_target",
}

CATALOG_STATUS_CHOICES = {
    "1": "in_catalog",
    "2": "outside_catalog",
    "3": "unresolved",
}

IDENTITY_ROLE_CHOICES = {
    "1": "identity_claim",
    "2": "mention_only",
    "3": "unclear",
}

DOMAIN_ROLE_CHOICES = {
    "1": "first_party_identity",
    "2": "first_party_content",
    "3": "user_content_hosting",
    "4": "authorized_service",
    "5": "unverified",
}


def prompt_choice(prompt_text: str, choices: Dict[str, str], default_key: str | None = None) -> str:
    """Yêu cầu người dùng chọn từ menu số, hỗ trợ giá trị mặc định."""
    opts_str = " / ".join(f"[{k}] {v}" for k, v in choices.items())
    default_str = f" (Mặc định: [{default_key}])" if default_key else ""
    while True:
        try:
            val = input(f"{prompt_text} ({opts_str}){default_str}: ").strip()
            if not val and default_key:
                return choices[default_key]
            if val in choices:
                return choices[val]
            print(f"Lựa chọn '{val}' không hợp lệ. Vui lòng nhập lại số tương ứng.")
        except EOFError:
            raise KeyboardInterrupt


def load_already_annotated_sample_ids(output_path: Path) -> Set[str]:
    """Đọc các sample_id đã hoàn thành trước đó từ file output JSONL để hỗ trợ resume."""
    if not output_path.exists():
        return set()
    annotated = set()
    with open(output_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
                sid = rec.get("sample_id")
                if sid:
                    annotated.add(sid)
            except Exception:
                pass
    return annotated


def display_sample(sample: Dict[str, Any], current_idx: int, total_samples: int) -> None:
    """Hiển thị thông tin mù an toàn của mẫu cho đánh giá viên."""
    print("\n" + "=" * 80)
    print(f" MẪU GÁN NHÃN MÙ [{current_idx}/{total_samples}]: ID = {sample.get('sample_id')}")
    print("=" * 80)
    print(f"[URL] URL: {sample.get('url')}")
    
    summary = sample.get("structure_summary", {})
    title = summary.get("title", "")
    if title:
        print(f"[TITLE] Tiêu đề: {title}")
    
    forms = summary.get("forms", 0)
    inputs = summary.get("inputs", 0)
    pwd = summary.get("password_inputs", 0)
    ext_links = summary.get("external_links", 0)
    has_login = summary.get("has_login_form", False)
    
    print(f"[DOM] Cấu trúc: Forms: {forms} | Inputs: {inputs} | Passwords: {pwd} (Login Form: {has_login}) | External Links: {ext_links}")
    print("-" * 80)
    print("[TEXT] Nội dung văn bản an toàn đã trích xuất:")
    text = sample.get("page_text", "")
    if len(text) > 600:
        print(f"   {text[:600]} ... [Cắt hiển thị, tổng độ dài: {len(text)} ký tự]")
    else:
        print(f"   {text or '[Không có nội dung văn bản]'}")
    print("-" * 80)


def annotate_interactive_session(
    annotator_id: str,
    input_path: Path,
    output_path: Path,
    pass_id: int = 1,
    dry_run: bool = False,
) -> None:
    """Phiên làm việc gán nhãn có bấm giờ tương tác."""
    if not input_path.exists():
        print(f"LỖI: Không tìm thấy gói dữ liệu mù tại: {input_path}")
        sys.exit(1)

    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Đảm bảo gói dữ liệu đầu vào không rò rỉ nhãn
    assert_no_label_leak(data)
    samples = data.get("samples", [])
    total_samples = len(samples)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    done_ids = load_already_annotated_sample_ids(output_path)
    
    remaining_samples = [s for s in samples if s.get("sample_id") not in done_ids]
    print(f"\n[START] Khởi động phiên gán nhãn cho Thành viên: {annotator_id}")
    print(f"[SAMPLES] Tổng số mẫu: {total_samples} | Đã hoàn thành: {len(done_ids)} | Còn lại: {len(remaining_samples)}")
    print(f"[OUTPUT] Tệp kết quả: {output_path}")

    if not remaining_samples:
        print("[COMPLETE] Bạn đã hoàn thành toàn bộ các mẫu trong gói này!")
        return

    for idx, sample in enumerate(remaining_samples, len(done_ids) + 1):
        sid = sample.get("sample_id", "UNKNOWN")
        display_sample(sample, idx, total_samples)

        # BẮT ĐẦU ĐỒNG HỒ BẤM GIỜ
        start_time = time.perf_counter()

        if dry_run:
            # Chế độ dry-run tự động giả lập 1 mẫu để kiểm thử không treo input
            elapsed = 0.5
            record_dict = {
                "annotator_id": annotator_id,
                "sample_id": sid,
                "pass_id": pass_id,
                "class_label": "phishing" if "login" in sample.get("url", "") else "benign",
                "primary_org_status": "identified" if "login" in sample.get("url", "") else "unknown",
                "catalog_status": "in_catalog" if "login" in sample.get("url", "") else "unresolved",
                "observed_service": "Office 365" if "office" in sample.get("url", "") else "None",
                "org_targets": ["microsoft"] if "office" in sample.get("url", "") else [],
                "primary_org": "microsoft" if "office" in sample.get("url", "") else "unknown",
                "identity_role": "identity_claim" if "login" in sample.get("url", "") else "unclear",
                "domain_role": "unverified",
                "evidence_note": "Dry-run automated testing record",
                "seconds_spent": elapsed,
                "random_subset": True,
                "difficult_case": False,
                "codebook_version": "1.0.0",
                "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            }
            validated_record = validate_annotation_record(record_dict)
            with open(output_path, "a", encoding="utf-8", newline="\n") as out_f:
                out_f.write(json.dumps(validated_record.to_dict(), ensure_ascii=False) + "\n")
            print(f"[OK] [Dry-Run] Đã lưu mẫu {sid} thành công.")
            continue

        try:
            print("\n[INPUT] Nhập thông tin đánh giá (Theo Codebook v1):")
            c_label = prompt_choice("1. Nhãn phân loại", CLASS_LABEL_CHOICES)
            p_org_status = prompt_choice("2. Trạng thái tổ chức", PRIMARY_ORG_STATUS_CHOICES)
            cat_status = prompt_choice("3. Tình trạng từ điển", CATALOG_STATUS_CHOICES)
            
            obs_service = input("4. Tên dịch vụ quan sát tự do (Enter để bỏ trống): ").strip() or "None"
            primary_org = input("5. Mã tổ chức chính (ví dụ: microsoft, google, unknown): ").strip() or "unknown"
            
            targets_input = input("6. Các tổ chức bị mạo danh (phân tách bởi dấu phẩy, Enter nếu rỗng): ").strip()
            org_targets = [t.strip() for t in targets_input.split(",") if t.strip()] if targets_input else []
            if primary_org not in {"unknown", "no_clear_target"} and primary_org not in org_targets:
                org_targets.append(primary_org)

            id_role = prompt_choice("7. Vai trò danh tính trên trang", IDENTITY_ROLE_CHOICES)
            dom_role = prompt_choice("8. Vai trò tên miền", DOMAIN_ROLE_CHOICES)
            
            evidence = input("9. Ghi chú bằng chứng nội dung/form: ").strip() or "Quan sát theo URL và cấu trúc trang"
            
            diff_str = input("10. Đánh dấu ca khó? [y/N]: ").strip().lower()
            is_diff = diff_str in {"y", "yes", "true", "1"}

            # DỪNG BẤM GIỜ
            elapsed = round(time.perf_counter() - start_time, 2)
            print(f"[TIMER] Thời gian thao tác mẫu: {elapsed} giây")

            record_dict = {
                "annotator_id": annotator_id,
                "sample_id": sid,
                "pass_id": pass_id,
                "class_label": c_label,
                "primary_org_status": p_org_status,
                "catalog_status": cat_status,
                "observed_service": obs_service,
                "org_targets": org_targets,
                "primary_org": primary_org,
                "identity_role": id_role,
                "domain_role": dom_role,
                "evidence_note": evidence,
                "seconds_spent": elapsed,
                "random_subset": True,
                "difficult_case": is_diff,
                "codebook_version": "1.0.0",
                "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            }

            validated_record = validate_annotation_record(record_dict)

            # Ghi nối tiếp ngay vào tệp JSON Lines
            with open(output_path, "a", encoding="utf-8", newline="\n") as out_f:
                out_f.write(json.dumps(validated_record.to_dict(), ensure_ascii=False) + "\n")

            print(f"[OK] Đã lưu kết quả mẫu {sid} vào {output_path}")

        except KeyboardInterrupt:
            print("\n\n[PAUSE] Bạn đã tạm dừng phiên gán nhãn. Tiến độ đã được lưu tự động.")
            print(f"Lần tới bạn có thể chạy lại lệnh để tiếp tục từ mẫu index {idx}.")
            break


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--annotator", required=True, choices=["A", "B", "adjudicator"], help="Mã người gán nhãn (A, B hoặc adjudicator)")
    parser.add_argument("--input", default="data/annotations/blind_view_pilot.json", type=Path, help="Đường dẫn tệp Blind View đầu vào")
    parser.add_argument("--output", required=True, type=Path, help="Đường dẫn tệp JSONL xuất kết quả gán nhãn")
    parser.add_argument("--pass-id", default=1, type=int, help="Lượt gán nhãn: 1 (độc lập), 2 (phân xử)")
    parser.add_argument("--dry-run", action="store_true", help="Chạy tự động không chờ nhập liệu bàn phím (dùng cho CI/test)")

    args = parser.parse_args()
    annotate_interactive_session(
        annotator_id=args.annotator,
        input_path=args.input,
        output_path=args.output,
        pass_id=args.pass_id,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
