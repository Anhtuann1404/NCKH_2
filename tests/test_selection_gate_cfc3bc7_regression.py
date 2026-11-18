"""Bộ kiểm thử hồi quy nghiêm ngặt cho 2 thay đổi mã tại commit cfc3bc7 (Task DATA-03).

Thiết kế theo chuẩn mực Academic Research Skills (ARS) và yêu cầu thẩm định của Lead D:
1. Phần 1 - Hỗ trợ datetime.date từ Parquet (PyArrow/Pandas):
   - Fixture Parquet đọc qua PyArrow/Pandas.
   - Nhận diện đúng hai ngày biên: 2024-10-01 và 2025-09-08 (Passed).
   - Từ chối ngày sát ngoài biên: 2024-09-30 và 2025-09-09.
   - Từ chối chuỗi có hậu tố rác: '2024-10-01T00:00:00', '2024-10-01-extra', '2024-10-01xyz'.
   - Xử lý đối tượng datetime có giờ và missing value (None, '', rỗng, missing key).

2. Phần 2 - Tối ưu hóa SimHash 64-bit và DOM Tag Jaccard:
   - Đối chiếu toán học giữa phiên bản tuần tự và Counter trên fixture có token/DOM lặp.
   - Ranh giới Hamming: 10, 11, 12, 13.
   - Ranh giới DOM Jaccard quanh 0.85 kết hợp Hamming <= 12.
   - Xác nhận tính bất biến của quyết định clone khi dùng precomputed fingerprint.
"""

from collections import Counter
from datetime import date, datetime
import hashlib
import io
import re
from typing import Any, Dict, List

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from phishing.data.selection_gate import SelectionGatePipeline
from phishing.data.template_similarity import (
    TemplateSimilarityEngine,
    compute_dom_jaccard_similarity,
    compute_token_simhash_64,
    extract_dom_tag_multiset,
    hamming_distance_64,
)


@pytest.fixture
def gate_pipeline():
    return SelectionGatePipeline(
        min_date="2024-10-01",
        max_date="2025-09-08",
        min_html_chars=1,
        max_html_chars=2000000,
    )


# ============================================================================
# PHẦN 1: KIỂM HỒI QUY XỬ LÝ NGÀY (datetime.date, Parquet Fixture, Hậu tố rác)
# ============================================================================

class TestGate1DateRegression:
    """Kiểm hồi quy tính hợp lệ trường ngày trong Cổng 1."""

    def test_parquet_pyarrow_date32_roundtrip_boundaries(self, gate_pipeline):
        """Tạo tệp Parquet thật với kiểu pa.date32() qua PyArrow và đọc lại bằng Pandas."""
        # Tạo bảng PyArrow với cột date là date32
        dates = [
            date(2024, 10, 1),   # Biên dưới hợp lệ
            date(2025, 9, 8),    # Biên trên hợp lệ
            date(2024, 9, 30),   # Sát ngoài biên dưới (loại)
            date(2025, 9, 9),    # Sát ngoài biên trên (loại)
            date(2025, 1, 15),   # Giữa khoảng (hợp lệ)
        ]
        urls = [f"https://example{i}.com" for i in range(len(dates))]
        htmls = ["<p>Valid content</p>"] * len(dates)

        table = pa.Table.from_arrays(
            [
                pa.array(urls, type=pa.string()),
                pa.array(htmls, type=pa.string()),
                pa.array(dates, type=pa.date32()),
            ],
            names=["url", "html", "date"],
        )

        sink = io.BytesIO()
        pq.write_table(table, sink)
        sink.seek(0)

        # Đọc lại bằng Pandas như trong pipeline thật
        df_read = pq.read_table(sink).to_pandas()
        records = df_read.to_dict(orient="records")

        # 1. Biên dưới 2024-10-01: Nhận
        ok_min, reason_min = gate_pipeline.gate_1_field_validity(records[0])
        assert ok_min is True
        assert reason_min == "passed"

        # 2. Biên trên 2025-09-08: Nhận
        ok_max, reason_max = gate_pipeline.gate_1_field_validity(records[1])
        assert ok_max is True
        assert reason_max == "passed"

        # 3. Sát ngoài biên dưới 2024-09-30: Loại
        ok_out_min, reason_out_min = gate_pipeline.gate_1_field_validity(records[2])
        assert ok_out_min is False
        assert reason_out_min == "reject_date_before_min_2024-09-30"

        # 4. Sát ngoài biên trên 2025-09-09: Loại
        ok_out_max, reason_out_max = gate_pipeline.gate_1_field_validity(records[3])
        assert ok_out_max is False
        assert reason_out_max == "reject_date_after_max_2025-09-09"

        # 5. Ngày ở giữa: Nhận
        ok_mid, reason_mid = gate_pipeline.gate_1_field_validity(records[4])
        assert ok_mid is True
        assert reason_mid == "passed"

    def test_reject_string_with_garbage_suffixes_and_time(self, gate_pipeline):
        """Bắt buộc từ chối chuỗi có hậu tố rác, timestamp ISO có giờ, hoặc định dạng không chuẩn."""
        base_sample = {"url": "https://example.com/test", "html": "<html><body>Hello</body></html>"}

        # Hậu tố rác ISO datetime
        s1 = {**base_sample, "date": "2024-10-01T00:00:00"}
        ok1, r1 = gate_pipeline.gate_1_field_validity(s1)
        assert ok1 is False
        assert r1 == "reject_invalid_date_format"

        # Hậu tố rác chuỗi
        s2 = {**base_sample, "date": "2024-10-01-extra"}
        ok2, r2 = gate_pipeline.gate_1_field_validity(s2)
        assert ok2 is False
        assert r2 == "reject_invalid_date_format"

        s3 = {**base_sample, "date": "2024-10-01xyz"}
        ok3, r3 = gate_pipeline.gate_1_field_validity(s3)
        assert ok3 is False
        assert r3 == "reject_invalid_date_format"

        # Định dạng DD/MM/YYYY không đúng YYYY-MM-DD
        s4 = {**base_sample, "date": "01/10/2024"}
        ok4, r4 = gate_pipeline.gate_1_field_validity(s4)
        assert ok4 is False
        assert r4 == "reject_invalid_date_format"

    def test_handle_datetime_object_and_missing_values(self, gate_pipeline):
        """Xử lý đối tượng datetime có giờ và các trường hợp giá trị khuyết thiếu (Fail-closed)."""
        base_sample = {"url": "https://example.com/test", "html": "<html><body>Hello</body></html>"}

        # Đối tượng datetime (có giờ) không phải date thuần túy -> từ chối để chống lệch múi giờ
        dt_val = datetime(2024, 10, 1, 14, 30, 0)
        s_dt = {**base_sample, "date": dt_val}
        ok_dt, r_dt = gate_pipeline.gate_1_field_validity(s_dt)
        assert ok_dt is False
        assert r_dt == "reject_invalid_date_format"

        # None
        s_none = {**base_sample, "date": None}
        ok_none, r_none = gate_pipeline.gate_1_field_validity(s_none)
        assert ok_none is False
        assert r_none == "reject_missing_date"

        # Chuỗi rỗng / whitespace
        s_empty = {**base_sample, "date": "   "}
        ok_empty, r_empty = gate_pipeline.gate_1_field_validity(s_empty)
        assert ok_empty is False
        assert r_empty == "reject_missing_date"

        # Không có trường date
        s_missing = {**base_sample}
        ok_missing, r_missing = gate_pipeline.gate_1_field_validity(s_missing)
        assert ok_missing is False
        assert r_missing == "reject_missing_date"


# ============================================================================
# PHẦN 2: KIỂM HỒI QUY SIMHASH 64-BIT & DOM TAG JACCARD (Tối ưu hóa & Ngưỡng biên)
# ============================================================================

def _unoptimized_simhash(text: str) -> int:
    """Phiên bản SimHash tuần tự nguyên thủy chưa tối ưu hóa bằng Counter."""
    if not text or not text.strip():
        return 0
    tokens = re.findall(r"\w+", text.lower())
    if not tokens:
        return 0
    features = list(tokens)
    for i in range(len(tokens) - 1):
        features.append(f"{tokens[i]} {tokens[i+1]}")
    vector = [0] * 64
    for feat in features:
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


class TestTemplateSimilarityOptimizationAndBoundaries:
    """Kiểm hồi quy tính chính xác toán học và ranh giới clone trong TemplateSimilarityEngine."""

    def test_simhash_counter_optimization_equivalence_on_repeated_tokens(self):
        """Bảo đảm 100% khớp giá trị hash giữa Counter và vòng lặp tuần tự trên dữ liệu lặp cao."""
        test_samples = [
            "<div><p>Hello world</p></div>",
            # Lặp nhiều từ khóa và thẻ DOM như phishing kit thật
            " ".join(["bank", "login", "secure", "account", "verify"] * 200),
            # Cấu trúc HTML lặp phức tạp
            "<html><body>" + ("<div class='row'><span class='col'>item</span></div>" * 50) + "</body></html>",
            # Văn bản rỗng hoặc không có từ
            "",
            "   \n\t  ",
            "!@#$%^&*()",
        ]

        for idx, sample in enumerate(test_samples):
            expected = _unoptimized_simhash(sample)
            actual = compute_token_simhash_64(sample)
            assert actual == expected, f"Sai lệch mã băm SimHash tại mẫu {idx}: {actual:#x} != {expected:#x}"

    def test_simhash_hamming_boundary_conditions(self):
        """Kiểm tra chính xác ngưỡng biên khoảng cách Hamming: 10, 11, 12, 13."""
        engine = TemplateSimilarityEngine(max_allowed_simhash_distance=10, max_allowed_dom_jaccard=0.85)

        # Đăng ký template cơ sở với SimHash = 0x0 và tập thẻ DOM rỗng
        engine.register_template(
            template_id="tpl_base",
            description="Base template with zero hash",
            sample_simhash=0x0,
            sample_dom_tags=[],
        )

        # 1. Hamming = 10 (chính xác 10 bit 1): Bắt buộc nhận diện là clone (Nhánh 1)
        hash_10 = (1 << 10) - 1  # 0b1111111111 (10 bit 1)
        assert hamming_distance_64(0x0, hash_10) == 10
        res_10 = engine.check_candidate_similarity(candidate_simhash=hash_10, candidate_dom_tags=[])
        assert res_10["is_clone_template"] is True
        assert res_10["min_simhash_distance"] == 10
        assert any("Khoảng cách SimHash = 10 <= 10" in r for r in res_10["reasons"])

        # 2. Hamming = 11 (11 bit 1, không có DOM Jaccard): Bắt buộc KHÔNG coi là clone
        hash_11 = (1 << 11) - 1  # 0b11111111111 (11 bit 1)
        assert hamming_distance_64(0x0, hash_11) == 11
        res_11 = engine.check_candidate_similarity(candidate_simhash=hash_11, candidate_dom_tags=[])
        assert res_11["is_clone_template"] is False
        assert res_11["min_simhash_distance"] == 11

        # 3. Hamming = 12 (12 bit 1, không có DOM Jaccard): Bắt buộc KHÔNG coi là clone
        hash_12 = (1 << 12) - 1
        assert hamming_distance_64(0x0, hash_12) == 12
        res_12 = engine.check_candidate_similarity(candidate_simhash=hash_12, candidate_dom_tags=[])
        assert res_12["is_clone_template"] is False

        # 4. Hamming = 13 (13 bit 1, không có DOM Jaccard): Bắt buộc KHÔNG coi là clone
        hash_13 = (1 << 13) - 1
        assert hamming_distance_64(0x0, hash_13) == 13
        res_13 = engine.check_candidate_similarity(candidate_simhash=hash_13, candidate_dom_tags=[])
        assert res_13["is_clone_template"] is False

    def test_dom_jaccard_and_hamming_combined_branch_boundaries(self):
        """Kiểm tra điều kiện kết hợp Nhánh 2: DOM Jaccard >= 0.85 ĐỒNG THỜI Hamming SimHash <= 12."""
        engine = TemplateSimilarityEngine(max_allowed_simhash_distance=10, max_allowed_dom_jaccard=0.85)

        # Tập thẻ chuẩn có 20 thẻ duy nhất
        base_tags = [f"tag_{i}" for i in range(20)]
        engine.register_template(
            template_id="tpl_dom",
            description="Base DOM template",
            sample_simhash=0x0,
            sample_dom_tags=base_tags,
        )

        hash_11 = (1 << 11) - 1  # dist = 11 (thỏa <= 12)
        hash_12 = (1 << 12) - 1  # dist = 12 (thỏa <= 12)
        hash_13 = (1 << 13) - 1  # dist = 13 (vượt > 12)

        # Trường hợp 1: Jaccard = 17 / 20 = 0.85 (Đạt ngưỡng 0.85) và Hamming = 11 (<= 12)
        # Giao = 17 thẻ (0..16), Hợp = 20 thẻ (0..19)
        tags_jaccard_085 = [f"tag_{i}" for i in range(17)]
        j_val = compute_dom_jaccard_similarity(base_tags, tags_jaccard_085)
        assert j_val == 0.85

        res_h11_j085 = engine.check_candidate_similarity(
            candidate_simhash=hash_11,
            candidate_dom_tags=tags_jaccard_085,
        )
        assert res_h11_j085["is_clone_template"] is True
        assert any("Độ tương đồng DOM Jaccard = 0.85 >= 0.85 kèm SimHash gần (dist=11)" in r for r in res_h11_j085["reasons"])

        # Trường hợp 2: Jaccard = 0.85 và Hamming = 12 (<= 12) -> Clone
        res_h12_j085 = engine.check_candidate_similarity(
            candidate_simhash=hash_12,
            candidate_dom_tags=tags_jaccard_085,
        )
        assert res_h12_j085["is_clone_template"] is True

        # Trường hợp 3: Jaccard = 0.85 NHƯNG Hamming = 13 (> 12) -> KHÔNG CLONE (kiểm soát chặt chẽ)
        res_h13_j085 = engine.check_candidate_similarity(
            candidate_simhash=hash_13,
            candidate_dom_tags=tags_jaccard_085,
        )
        assert res_h13_j085["is_clone_template"] is False

        # Trường hợp 4: Jaccard = 1.0 (trùng hệt DOM) NHƯNG Hamming = 13 (> 12) -> VẪN KHÔNG CLONE
        res_h13_j100 = engine.check_candidate_similarity(
            candidate_simhash=hash_13,
            candidate_dom_tags=base_tags,
        )
        assert res_h13_j100["is_clone_template"] is False

        # Trường hợp 5: Jaccard quanh 0.85 nhưng chưa đạt (16 / 19 = 0.8421 < 0.85) và Hamming = 11
        # Giao = 16 (0..15), Hợp = 19
        tags_jaccard_sub_085 = [f"tag_{i}" for i in range(16)]
        j_sub = compute_dom_jaccard_similarity([f"tag_{i}" for i in range(19)], tags_jaccard_sub_085)
        assert j_sub < 0.85
        res_sub_jaccard = engine.check_candidate_similarity(
            candidate_simhash=hash_11,
            candidate_dom_tags=tags_jaccard_sub_085,
        )
        assert res_sub_jaccard["is_clone_template"] is False

    def test_precomputed_fingerprint_preserves_registered_templates_behavior(self):
        """Xác nhận việc đăng ký bằng fingerprint tính sẵn (sample_simhash, sample_dom_tags) hoàn toàn bất biến."""
        sample_html = "<html><body><h1>Title</h1><p>Paragraph content</p><a href='#'>Link</a></body></html>"

        # Đăng ký cách 1: Truyền trực tiếp HTML (tự băm)
        engine1 = TemplateSimilarityEngine()
        engine1.register_template("tpl_1", "HTML direct", sample_html=sample_html)

        # Đăng ký cách 2: Truyền precomputed fingerprint
        simhash_calc = compute_token_simhash_64(sample_html)
        dom_tags_calc = extract_dom_tag_multiset(sample_html)
        engine2 = TemplateSimilarityEngine()
        engine2.register_template(
            "tpl_1",
            "Precomputed fingerprint",
            sample_html="",
            sample_simhash=simhash_calc,
            sample_dom_tags=dom_tags_calc,
        )

        # Đối chiếu 2 engine trên cùng ứng viên
        test_candidate_html = "<html><body><h1>Title</h1><p>Another content</p><a href='#'>Link</a></body></html>"
        res1 = engine1.check_candidate_similarity(candidate_html=test_candidate_html)
        res2 = engine2.check_candidate_similarity(candidate_html=test_candidate_html)

        assert res1["is_clone_template"] == res2["is_clone_template"]
        assert res1["min_simhash_distance"] == res2["min_simhash_distance"]
        assert res1["max_dom_jaccard"] == res2["max_dom_jaccard"]
        assert res1["reasons"] == res2["reasons"]
