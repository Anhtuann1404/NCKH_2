"""Template Similarity & Near-Duplicate Detection Engine (Task DEV-02 / Thành viên C).

Tuân thủ nghiêm ngặt chỉ đạo của Lead D (22/10/2026):
1. Quét đối soát độ tương đồng cấu trúc và nội dung giữa các ứng viên tuyển chọn
   với các mẫu template clone đã biết (như template shop tiếng Nhật .shop, clone Google/Meta).
2. Sử dụng thuật toán SimHash 64-bit và DOM Tag Jaccard Similarity hoàn toàn bằng
   Thư viện chuẩn (Standard Library: re, hashlib) theo kỷ luật Ponytail Engineering.
3. Không làm rò rỉ nhãn nguồn; đánh giá thuần túy trên cấu trúc DOM và văn bản snapshot tĩnh.
"""

from __future__ import annotations

import hashlib
import re
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple


def compute_token_simhash_64(text: str) -> int:
    """Tính toán mã băm SimHash 64-bit từ văn bản hoặc chuỗi thẻ HTML.

    Args:
        text: Chuỗi văn bản hoặc HTML cần băm.

    Returns:
        Số nguyên 64-bit biểu diễn fingerprint độ tương đồng ngữ nghĩa.
    """
    if not text or not text.strip():
        return 0

    tokens = re.findall(r"\w+", text.lower())
    if not tokens:
        return 0

    # Sinh danh sách các feature tokens kèm word bigrams để tăng tính bền vững cấu trúc
    features: List[str] = list(tokens)
    for i in range(len(tokens) - 1):
        features.append(f"{tokens[i]} {tokens[i+1]}")

    vector = [0] * 64
    for feat in features:
        # Băm token thành 64-bit integer bằng sha256
        h = int(hashlib.sha256(feat.encode("utf-8")).hexdigest()[:16], 16)
        for i in range(64):
            if (h >> i) & 1:
                vector[i] += 1
            else:
                vector[i] -= 1

    simhash = 0
    for i in range(64):
        if vector[i] > 0:
            simhash |= 1 << i

    return simhash


def hamming_distance_64(hash1: int, hash2: int) -> int:
    """Tính khoảng cách Hamming giữa hai số nguyên 64-bit (số bit khác biệt)."""
    return bin(hash1 ^ hash2).count("1")


def extract_dom_tag_multiset(html: str) -> List[str]:
    """Trích xuất danh sách thứ tự các thẻ HTML (DOM tags) bỏ qua thuộc tính và JavaScript."""
    if not html:
        return []
    # Loại bỏ nội dung bên trong <script> và <style> trước khi trích xuất
    cleaned = re.sub(r"(?is)<script.*?</script>", " ", html)
    cleaned = re.sub(r"(?is)<style.*?</style>", " ", cleaned)
    # Lấy tên thẻ
    tags = re.findall(r"<([a-zA-Z0-9]+)", cleaned)
    return [t.lower() for t in tags]


def compute_dom_jaccard_similarity(tags1: Sequence[str], tags2: Sequence[str]) -> float:
    """Tính chỉ số tương đồng Jaccard giữa hai tập thẻ DOM."""
    set1, set2 = set(tags1), set(tags2)
    if not set1 and not set2:
        return 1.0
    if not set1 or not set2:
        return 0.0
    intersection = len(set1 & set2)
    union = len(set1 | set2)
    return round(intersection / union, 4)


class TemplateSimilarityEngine:
    """Động cơ rà soát và đánh giá độ tương đồng template clone.

    Dùng để hậu kiểm tập ứng viên ngẫu nhiên sau khi rút từ shard, ngăn chặn việc đưa vào
    nhiều mẫu cùng 1 clone kit hoặc cùng một template sinh tự động.
    """

    def __init__(
        self,
        known_templates: Optional[List[Dict[str, Any]]] = None,
        max_allowed_simhash_distance: int = 10,
        max_allowed_dom_jaccard: float = 0.85,
    ) -> None:
        self.max_allowed_simhash_distance = max_allowed_simhash_distance
        self.max_allowed_dom_jaccard = max_allowed_dom_jaccard
        self.registered_templates: List[Dict[str, Any]] = []
        if known_templates:
            for kt in known_templates:
                self.register_template(
                    template_id=kt.get("template_id", "unknown"),
                    description=kt.get("description", ""),
                    sample_text=kt.get("sample_text", ""),
                    sample_html=kt.get("sample_html", ""),
                )

    def register_template(
        self,
        template_id: str,
        description: str,
        sample_text: str = "",
        sample_html: str = "",
    ) -> None:
        """Đăng ký một template đã biết để làm căn cứ phát hiện clone."""
        simhash = compute_token_simhash_64(sample_text or sample_html)
        dom_tags = extract_dom_tag_multiset(sample_html) if sample_html else []
        self.registered_templates.append({
            "template_id": template_id,
            "description": description,
            "simhash": simhash,
            "dom_tags": dom_tags,
        })

    def check_candidate_similarity(
        self,
        candidate_text: str,
        candidate_html: str = "",
    ) -> Dict[str, Any]:
        """Kiểm tra một ứng viên xem có bị trùng lặp template với các mẫu đã đăng ký hay không."""
        c_simhash = compute_token_simhash_64(candidate_text or candidate_html)
        c_dom_tags = extract_dom_tag_multiset(candidate_html) if candidate_html else []

        min_distance = 64
        max_jaccard = 0.0
        closest_template_id: Optional[str] = None
        is_clone = False
        reasons: List[str] = []

        for kt in self.registered_templates:
            # 1. Đo SimHash distance
            dist = hamming_distance_64(c_simhash, kt["simhash"])
            if dist < min_distance:
                min_distance = dist
                closest_template_id = kt["template_id"]

            if dist <= self.max_allowed_simhash_distance:
                is_clone = True
                reasons.append(
                    f"Khoảng cách SimHash = {dist} <= {self.max_allowed_simhash_distance} "
                    f"với template '{kt['template_id']}'"
                )

            # 2. Đo DOM Jaccard similarity (nếu có cấu trúc DOM)
            if c_dom_tags and kt["dom_tags"]:
                jaccard = compute_dom_jaccard_similarity(c_dom_tags, kt["dom_tags"])
                if jaccard > max_jaccard:
                    max_jaccard = jaccard
                if jaccard >= self.max_allowed_dom_jaccard and dist <= 12:
                    is_clone = True
                    reasons.append(
                        f"Độ tương đồng DOM Jaccard = {jaccard:.2f} >= {self.max_allowed_dom_jaccard} "
                        f"kèm SimHash gần (dist={dist}) với template '{kt['template_id']}'"
                    )

        return {
            "is_clone_template": is_clone,
            "min_simhash_distance": min_distance,
            "max_dom_jaccard": max_jaccard,
            "closest_template_id": closest_template_id,
            "candidate_simhash_hex": f"{c_simhash:016x}",
            "reasons": reasons,
        }
