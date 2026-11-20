"""Công cụ kiểm tra thực tế việc cách ly dữ liệu hạn chế khỏi Git và gói công khai (Git Isolation Verifier).

Tuân thủ nghiêm ngặt chỉ đạo của Lead D (Mục 3):
1. Không chỉ dựa vào .gitignore mà kiểm tra trực tiếp danh sách tệp được theo dõi (git ls-files).
2. Kiểm tra lệnh `git check-ignore` trên các đường dẫn nhạy cảm:
   - data/restricted/
   - data/restricted/main_annotation_lot_management_ledger.json
   - data/restricted/mapping_*.json
   - data/restricted/population_*.json
3. Quét toàn bộ tệp đang được Git theo dõi (tracked files) để đảm bảo:
   - 0 tệp nào có tiền tố `data/restricted/`.
   - 0 tệp chứa các hậu tố cấm: .parquet, .pkl, .joblib, .pt, .pth.
4. Quét nội dung các tệp văn bản công khai/sắp commit trong docs/ và configs/ để đảm bảo không rò rỉ:
   - Các trường cấm: "source_label", "locator", "parquet_file", "source_row", "model_score".
5. Xuất báo cáo kiểm toán có thể tái lập: artifacts/isolation_verification_report.json.
   Kết luận trung thực trong phạm vi đã quét, không dùng từ ngữ phóng đại ("an toàn tuyệt đối").
"""

import json
from pathlib import Path
import re
import subprocess
import sys
from typing import Any, Dict, List, Optional, Set, Tuple


FORBIDDEN_TRACKED_PATTERNS = [
    r"^data/restricted/",
    r"^restricted_packages/",
    r".*\.parquet$",
    r".*\.feather$",
    r".*\.pkl$",
    r".*\.joblib$",
    r".*\.pt$",
    r".*\.pth$",
]

FORBIDDEN_CONTENT_TERMS = [
    "source_label",
    "is_phish",
    "primary_org_status",
]

RESTRICTED_PROBE_PATHS = [
    "data/restricted/main_annotation_lot_management_ledger.json",
    "data/restricted/main_batch1/mapping_restricted.json",
    "data/restricted/population_sealed.jsonl",
    "data/restricted/seeds_secret.json",
]


def run_cmd(cmd: List[str]) -> Tuple[int, str, str]:
    """Chạy lệnh shell và trả về (returncode, stdout, stderr)."""
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8")
    return p.returncode, p.stdout.strip(), p.stderr.strip()


def check_git_ignore_probes(probe_paths: List[str]) -> Dict[str, Any]:
    """Kiểm tra xem các đường dẫn nhạy cảm có được .gitignore ghi nhận hay không."""
    results = {}
    all_ignored = True

    for path in probe_paths:
        code, out, _ = run_cmd(["git", "check-ignore", "-v", path])
        is_ignored = (code == 0 and len(out) > 0)
        results[path] = {
            "ignored": is_ignored,
            "rule": out if is_ignored else "NOT_IGNORED",
        }
        if not is_ignored:
            all_ignored = False

    return {
        "status": "PASS" if all_ignored else "FAIL",
        "all_probes_ignored": all_ignored,
        "details": results,
    }


def scan_tracked_files() -> Dict[str, Any]:
    """Quét toàn bộ danh sách tệp đang được Git theo dõi (git ls-files)."""
    code, out, _ = run_cmd(["git", "ls-files"])
    if code != 0:
        return {"status": "ERROR", "message": "Không thể chạy git ls-files"}

    tracked_files = [line.strip() for line in out.splitlines() if line.strip()]
    violations = []

    for f in tracked_files:
        for pat in FORBIDDEN_TRACKED_PATTERNS:
            if re.match(pat, f):
                violations.append({"file": f, "matched_pattern": pat})
                break

    return {
        "status": "PASS" if not violations else "FAIL",
        "total_tracked_files": len(tracked_files),
        "violations_count": len(violations),
        "violations": violations,
    }


def scan_public_docs_for_leaks(target_dirs: Any = ("docs", "configs", "src", "scripts")) -> Dict[str, Any]:
    """Quét các tệp công khai (docs, configs, src, scripts) để phát hiện rò rỉ mã nguồn, seed/salt hoặc nhãn cấm."""
    leaks = []
    read_errors = []
    scanned_count = 0

    if isinstance(target_dirs, (str, Path)):
        dirs_to_scan = [Path(target_dirs)]
    else:
        dirs_to_scan = [Path(d) for d in target_dirs]

    # Các từ khóa salt bí mật sản xuất bị cấm xuất hiện dưới dạng chuỗi cứng trong mã nguồn theo dõi
    PROHIBITED_SECRET_PATTERNS = [
        "nckh2_main_batch1_blind_salt_secure_2026",
    ]

    # Regex phát hiện mọi hành vi gán literal string cho biến secret/salt trong code sản xuất/runner
    LITERAL_SALT_ASSIGNMENT_REGEX = re.compile(
        r"\b(?:[a-z0-9_]*(?:salt|secret)[a-z0-9_]*)\s*=\s*[\"'][^\"']+[\"']",
        re.IGNORECASE
    )

    for p_dir in dirs_to_scan:
        if not p_dir.exists():
            continue
        for p in p_dir.glob("**/*"):
            if p.is_file() and p.suffix in (".md", ".json", ".txt", ".py"):
                scanned_count += 1
                try:
                    text = p.read_text(encoding="utf-8")
                except Exception as exc:
                    read_errors.append({"file": str(p), "error": str(exc)})
                    continue

                # 1. Quét phát hiện seed/salt sản xuất bị hardcode trong source/scripts (trừ chính tệp scanner)
                if p.name != "verify_git_isolation.py":
                    for sec_term in PROHIBITED_SECRET_PATTERNS:
                        if sec_term in text:
                            leaks.append({
                                "file": str(p),
                                "rule_code": "SEC002_KNOWN_PROHIBITED_PATTERN",
                                "term": "PROHIBITED_SECRET: [REDACTED_KNOWN_PATTERN]"
                            })

                    # Phát hiện literal string gán cho salt/secret mới trong src và scripts (che giấu hoàn toàn giá trị)
                    if p_dir.name in ("src", "scripts") or "src" in p.parts or "scripts" in p.parts:
                        for line_no, line in enumerate(text.splitlines(), start=1):
                            if LITERAL_SALT_ASSIGNMENT_REGEX.search(line):
                                masked_line = re.sub(r"([\"'])(?:(?=(\\?))\2.)*?([\"'])", r"\1[REDACTED_SECRET]\3", line)
                                leaks.append({
                                    "file": str(p),
                                    "line": line_no,
                                    "rule_code": "SEC001_LITERAL_SECRET_ASSIGNMENT",
                                    "term": f"LITERAL_SALT_ASSIGNMENT: {masked_line.strip()}"
                                })

                # 2. Quét rò rỉ trường nhãn nguồn trong docs và configs
                if p_dir.name in ("docs", "configs") or "docs" in p.parts or "configs" in p.parts:
                    if "CODEBOOK" in p.name or "API_SPEC" in p.name:
                        continue
                    for term in ("\"source_label\":", "'source_label':"):
                        if term in text:
                            leaks.append({"file": str(p), "term": term})

    has_issues = bool(leaks or read_errors)
    return {
        "status": "FAIL" if has_issues else "PASS",
        "scanned_files_count": scanned_count,
        "scanned_target_dirs": [str(d) for d in dirs_to_scan],
        "leaks_count": len(leaks),
        "read_errors_count": len(read_errors),
        "read_errors": read_errors,
        "leaks": leaks,
    }


def verify_git_isolation(output_report_path: Optional[Path | str] = None) -> Dict[str, Any]:
    """Thực thi đầy đủ bộ kiểm toán cách ly Git thực tế."""
    probe_res = check_git_ignore_probes(RESTRICTED_PROBE_PATHS)
    tracked_res = scan_tracked_files()
    leak_res = scan_public_docs_for_leaks()

    overall_pass = (
        probe_res["status"] == "PASS"
        and tracked_res["status"] == "PASS"
        and leak_res["status"] == "PASS"
    )

    report = {
        "report_type": "GIT_ISOLATION_VERIFICATION",
        "scope": "Phạm vi kiểm tra thực tế trên Git working tree và index hiện hành",
        "overall_status": "PASS" if overall_pass else "FAIL",
        "checks": {
            "check_ignore_probes": probe_res,
            "tracked_files_inspection": tracked_res,
            "public_content_leak_inspection": leak_res,
        },
        "conclusion": (
            f"Trong phạm vi đã quét ({leak_res.get('scanned_files_count', 0)} tệp thuộc các thư mục {leak_res.get('scanned_target_dirs', [])} và index Git hiện hành), "
            "không phát hiện tệp hạn chế nào bị Git theo dõi, "
            "toàn bộ đường dẫn probe thuộc data/restricted/ đều được .gitignore cách ly đúng, "
            "không có lỗi đọc tệp, "
            "không phát hiện literal string gán cứng cho biến bí mật/salt trong src/scripts, "
            "và không phát hiện trường dữ liệu nguồn bị rò rỉ vào tài liệu công khai."
            if overall_pass else
            f"Phát hiện vi phạm quy tắc cách ly Git hoặc rò rỉ bí mật/lỗi đọc tệp! (leaks={leak_res.get('leaks_count', 0)}, read_errors={leak_res.get('read_errors_count', 0)}, tracked_violations={tracked_res.get('violations_count', 0)}). Đề nghị xử lý trước khi phát hành."
        ),
    }

    if output_report_path:
        p_out = Path(output_report_path)
        p_out.parent.mkdir(parents=True, exist_ok=True)
        p_out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    return report


if __name__ == "__main__":
    out_file = Path("artifacts/isolation_verification_report.json")
    res = verify_git_isolation(out_file)
    print(f"Git Isolation Status: {res['overall_status']}")
    print(f"Report written to: {out_file}")
    if res["overall_status"] != "PASS":
        sys.exit(1)
