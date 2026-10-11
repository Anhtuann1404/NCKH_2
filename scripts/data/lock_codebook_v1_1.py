#!/usr/bin/env python3
"""Lock Codebook v1.1 from draft, creating docs/CODEBOOK_V1_1.md with locked header.

Preserves 100% of the agreed consensus rules from docs/CODEBOOK_V1_1_DRAFT.md.
Formats header with:
  **Phiên bản:** `1.1.0`
  **Trạng thái:** `locked` (Đã được Thành viên B nghiệm thu kỹ thuật mù và Lead D phê duyệt; đã khóa phiên bản 1.1.0 chính thức)
"""

from __future__ import annotations

import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def build_locked_codebook() -> tuple[Path, str]:
    draft_path = ROOT / "docs/CODEBOOK_V1_1_DRAFT.md"
    draft_lines = draft_path.read_text(encoding="utf-8").splitlines()

    # The body starts at line 5 (index 4), which is '## 1. Vai trò miền và nền tảng dùng chung'
    body = "\n".join(draft_lines[4:])

    header = """# SỔ TAY QUY TẮC GÁN NHÃN (CODEBOOK V1.1 - CHÍNH THỨC)

**Dự án:** NCKH_2 — Phát hiện website phishing mạo danh tổ chức  
**Phiên bản:** 1.1.0  
**Ngày cập nhật:** 12/10/2026  
**Trạng thái:** locked (Đã được Thành viên B nghiệm thu kỹ thuật mù và Lead D phê duyệt; đã khóa phiên bản 1.1.0 chính thức)  
**Kế thừa:** [Codebook v1.0](CODEBOOK_V1.md) đã khóa (SHA-256 `12de9c2f3b457938039b05c72c651d6650f403b620216516262134a3313a2ed1`) và dự thảo [Codebook v1.1 Draft](CODEBOOK_V1_1_DRAFT.md) (SHA-256 `20b4c181ca1da195c8cd86848ce084035e202ca22b56673cc1aa2e6a911c2b3b`). Mọi quy tắc dưới đây là chuẩn mực thực thi chính thức cho các đợt gán nhãn Calibration và Main Annotation. Không sửa file v1.0, lượt B/E Pass 1, Kappa pilot hoặc `labels_final.json` của pilot.  
**Mã băm từ điển đối chiếu (`configs/dictionary_v1.json`):**  
`SHA-256: 7aa83b68fdb4bb288460c00523e38e0779e8cbeb81ae879e7a5d27e771fcd3b3`  
**Dải ngày corpus train đã kiểm kê:** `02/07/2024` đến `08/09/2025` (Task DATA-01, 56 shards, 498.255 dòng)  
**Người biên soạn & quản lý:** Thành viên C (Data Pipeline & Blind View)  
**Hiện trạng rà soát & Nghiệm thu:**
- **Thành viên A (Annotator chính):** Đã rà soát quy chuẩn gán nhãn mù.
- **Thành viên B (QA & Kiểm độc lập):** Đã nghiệm thu kỹ thuật mù độc lập 11/11 mục tại commit `7bfafcf`.
- **Thành viên D (Lead):** Đã đối soát kỹ thuật nguồn, nghiệm thu Release View và chính thức phê duyệt khóa Codebook v1.1.0.

---

"""

    locked_content = header + body + "\n"
    out_path = ROOT / "docs/CODEBOOK_V1_1.md"
    out_path.write_text(locked_content, encoding="utf-8")
    cb_hash = hashlib.sha256(out_path.read_bytes()).hexdigest()
    print(f"Locked Codebook v1.1 created: {out_path} ({len(out_path.read_bytes())} bytes, sha256={cb_hash})")
    return out_path, cb_hash


if __name__ == "__main__":
    build_locked_codebook()
