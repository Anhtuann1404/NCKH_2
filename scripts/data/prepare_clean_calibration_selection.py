#!/usr/bin/env python3
"""Thuật toán tuyển chọn Gói Hiệu chuẩn Sạch cho Thành viên A (CALIBRATION-CLEAN-A).

Tuân thủ nghiêm ngặt chỉ đạo của Lead D (22/10/2026) và Đề án v1.1:
1. Nguồn trích xuất: Khóa đúng 2 verified source shards (data/train-000.parquet và data/train-055.parquet)
   đã đối chiếu checksum trong configs/source_manifest.json.
2. Bộ lọc Anti-Leakage 3 chiều: Loại trừ triệt để 116 mẫu đã biết trong data/exclusion_registry.json.
3. Phân tầng tất định: 12 phish + 12 benign (chính, shuffle seed 20261023) và 4 phish + 4 benign
   (dự phòng, shuffle seed 20261024). Tổng cộng 32 mẫu.
4. Quét Template Similarity (Hậu kiểm sau khi rút ứng viên):
   Sử dụng TemplateSimilarityEngine để đo SimHash distance và DOM Jaccard similarity
   giữa 32 ứng viên với các template clone đã biết; ghi nhận vào báo cáo nghiệm thu ứng viên.
5. Đánh giá 6 tầng độ khó bề mặt (difficulty_strata) độc lập, không nhìn trước nhãn nguồn.
6. Kỷ luật hệ thống: ready_for_annotation = False, training_blocked = True.
"""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import date
import hashlib
import json
from pathlib import Path
import random
import sys
from typing import Any, Dict, List, Optional, Set, Tuple

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from phishing.data.date_parser import parse_strict_date
from phishing.data.difficulty_strata import (
    DIFFICULTY_RULES,
    evaluate_difficulty_flags,
    is_hard_case,
)
from phishing.data.template_similarity import TemplateSimilarityEngine


def source_label(value: Any) -> Optional[str]:
    """Chuẩn hóa nhãn nguồn, không tự động biến unknown thành benign."""
    if isinstance(value, int):
        return {0: "benign", 1: "phish"}.get(value)
    if isinstance(value, str):
        v = value.strip().lower()
        if v in {"phishing", "phish"}:
            return "phish"
        if v == "benign":
            return "benign"
    return None


def load_blocked_fingerprints_from_registry(registry_path: Path) -> Dict[str, Set[str]]:
    """Đọc toàn bộ 116 mẫu loại trừ từ data/exclusion_registry.json để tạo bộ lọc 3 chiều."""
    with open(registry_path, encoding="utf-8") as f:
        registry = json.load(f)

    blocked = {
        "url_sha256": set(),
        "html_sha256": set(),
        "group_sha256": set(),
    }

    for entry in registry.get("exclusions", []):
        for s in entry.get("samples", []):
            if "url_sha256" in s:
                blocked["url_sha256"].add(s["url_sha256"])
            if "html_sha256" in s:
                blocked["html_sha256"].add(s["html_sha256"])
            if "group_sha256" in s:
                blocked["group_sha256"].add(s["group_sha256"])

    return blocked


def select_clean_candidates(
    candidates: List[Tuple[Dict[str, Any], str, Dict[str, str]]],
    blocked: Dict[str, Set[str]],
    seed: int = 20261022,
    main_shuffle_seed: int = 20261023,
    reserve_shuffle_seed: int = 20261024,
    main_per_class: int = 12,
    reserve_per_class: int = 4,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Thuật toán chọn 12+12 mẫu chính và 4+4 mẫu dự phòng có thứ tự.

    Đảm bảo:
    - Nhãn nguồn chỉ dùng để phân tầng (stratified quota).
    - Các mẫu không trùng lặp URL và không trùng lặp Domain Group với bất kỳ mẫu nào đã chọn hoặc bị chặn.
    - Shuffle độc lập bằng seed đã khóa trong manifest.
    """
    shuffled = list(candidates)
    random.Random(seed).shuffle(shuffled)

    target_total_per_class = main_per_class + reserve_per_class
    selected: Dict[str, List[Dict[str, Any]]] = {"phish": [], "benign": []}
    seen: Dict[str, Set[str]] = {key: set(blocked[key]) for key in blocked}

    for locator, label, fp in shuffled:
        if label not in selected:
            continue
        if len(selected[label]) >= target_total_per_class:
            continue

        # Kiểm tra chống rò rỉ 3 chiều
        if any(fp.get(k) in seen[k] for k in blocked if k in fp):
            continue

        selected[label].append(locator)
        for k in blocked:
            if k in fp:
                seen[k].add(fp[k])

    if any(len(selected[lbl]) != target_total_per_class for lbl in ["phish", "benign"]):
        raise ValueError(
            f"Không đủ ứng viên độc lập cho chỉ tiêu phân tầng: "
            f"phish={len(selected['phish'])}/{target_total_per_class}, "
            f"benign={len(selected['benign'])}/{target_total_per_class}"
        )

    # Tách mẫu chính và dự phòng
    main = selected["phish"][:main_per_class] + selected["benign"][:main_per_class]
    reserve = selected["phish"][main_per_class:] + selected["benign"][main_per_class:]

    # Xáo trộn độc lập bằng random seeds đã đăng ký trong manifest
    random.Random(main_shuffle_seed).shuffle(main)
    random.Random(reserve_shuffle_seed).shuffle(reserve)

    return main, reserve


def scan_candidates_template_similarity(
    locators: List[Dict[str, Any]],
    html_provider: Any,
    known_templates: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Hậu kiểm quét độ tương đồng template (Template Similarity Scan) cho tập ứng viên đã chọn."""
    engine = TemplateSimilarityEngine(known_templates=known_templates)

    # Đăng ký các mẫu template mẫu nhận diện (ví dụ: Japanese .shop template signature)
    default_templates = [
        {
            "template_id": "TPL-JAPANESE-SHOP-CLONE",
            "description": "Template cửa hàng thương mại điện tử tiếng Nhật sinh hàng loạt (.shop)",
            "sample_text": "ショッピングカート お問い合わせ 特定商取引法に基づく表記 プライバシーポリシー 決済方法について クレジットカード",
            "sample_html": "<html><body><header><h1>Shop</h1></header><div class='cart'>Cart</div><form action='/checkout'><input type='text'/></form><footer>Tokushoho</footer></body></html>",
        },
        {
            "template_id": "TPL-GOOGLE-DRIVE-LURE",
            "description": "Trang mồi nhử tệp chia sẻ Google Drive lưu trữ trên web.app",
            "sample_text": "Google Drive File Sharing View Document Download PDF Attachment Sign in to view file",
            "sample_html": "<html><body><div><img src='google.png'/><h3>Shared Document</h3><a href='/login'>Open File</a></div></body></html>",
        },
        {
            "template_id": "TPL-META-COMMUNITY-LURE",
            "description": "Trang mạo danh Meta Business / Community Standards đe dọa khóa tài khoản",
            "sample_text": "Meta Community Standards Policy Violation Notice Page Restriction Verification Appeal Form Submit Appeal",
            "sample_html": "<html><body><div><h2>Meta Business Support</h2><p>Your page will be unpublished</p><form><input type='submit'/></form></div></body></html>",
        },
    ]

    for dt in default_templates:
        engine.register_template(
            template_id=dt["template_id"],
            description=dt["description"],
            sample_text=dt["sample_text"],
            sample_html=dt["sample_html"],
        )

    results = []
    clone_detected_count = 0

    for loc in locators:
        html = html_provider(loc)
        sim_res = engine.check_candidate_similarity(candidate_text=html, candidate_html=html)
        if sim_res["is_clone_template"]:
            clone_detected_count += 1
        results.append({
            "locator": loc,
            "min_simhash_distance": sim_res["min_simhash_distance"],
            "max_dom_jaccard": sim_res["max_dom_jaccard"],
            "closest_template_id": sim_res["closest_template_id"],
            "is_clone_template": sim_res["is_clone_template"],
            "reasons": sim_res["reasons"],
        })

    return {
        "status": "template_similarity_scan_completed",
        "total_scanned": len(locators),
        "clone_detected_count": clone_detected_count,
        "scanned_results": results,
    }


def evaluate_clean_selection_strata(
    locators: List[Dict[str, Any]],
    row_provider: Any,
) -> Tuple[Dict[str, int], int]:
    """Đánh giá 6 tầng độ khó bề mặt hoàn toàn độc lập với nhãn nguồn."""
    rule_counts = Counter()
    hard_cases = 0

    for loc in locators:
        row = row_provider(loc)
        url = row.get("url", "")
        html = row.get("html", "") or ""
        flags = evaluate_difficulty_flags(url, html, max_html_characters=2_000_000)
        for r, val in flags.items():
            if val:
                rule_counts[r] += 1
        if is_hard_case(flags):
            hard_cases += 1

    return dict(rule_counts), hard_cases
