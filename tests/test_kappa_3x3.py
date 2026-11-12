"""Bộ kiểm thử độc lập cho Module Cohen's Kappa Ma trận 3x3 (Codebook v1.1).

Kiểm chứng toàn diện các tiêu chuẩn ARS:
1. Tính toán chính xác ma trận 3x3 trên 3 nhãn: phishing, benign, insufficient_evidence.
2. Kiểm thử sai số chuẩn tiệm cận Fleiss và khoảng tin cậy 95% Fleiss.
3. Kiểm thử khoảng tin cậy 95% Bootstrap phi tham số (1.000 lượt).
4. Phân vùng quyết định chuẩn xác: Pass (>=0.75), Conditional Review (0.60-0.75), Stop (<0.60).
5. Ghép cặp tuyệt đối theo sample_id không phụ thuộc thứ tự, bỏ qua dry-run.
6. Bắt lỗi nghiêm ngặt khi gặp nhãn lạ hoàn toàn (fail-closed).
"""

import pytest

from phishing.annotation import (
    CODEBOOK_V1_1_LABELS,
    AnnotationRecord,
    Kappa3x3Result,
    compute_kappa_3x3,
    compute_kappa_3x3_from_records,
    format_kappa_3x3_report,
)


class TestKappa3x3Core:
    """Kiểm thử các tính toán toán học cốt lõi của Cohen's Kappa ma trận 3x3."""

    def test_perfect_agreement(self):
        """Đồng thuận tuyệt đối trên cả 3 danh mục -> Kappa = 1.0, zone = pass."""
        a = ["phishing"] * 15 + ["benign"] * 10 + ["insufficient_evidence"] * 5
        b = list(a)

        res = compute_kappa_3x3(a, b, bootstrap_iterations=500, random_seed=42)

        assert res.sample_count == 30
        assert res.observed_agreement == 1.0
        assert res.kappa == 1.0
        assert res.se_fleiss == 0.0
        assert res.ci95_fleiss == (1.0, 1.0)
        assert res.ci95_bootstrap == (1.0, 1.0)
        assert res.status == "valid"
        assert res.zone == "pass"
        assert res.matrix_3x3[0][0] == 15
        assert res.matrix_3x3[1][1] == 10
        assert res.matrix_3x3[2][2] == 5

    def test_realistic_pass_zone(self):
        """30 mẫu: 28 mẫu đồng thuận, 2 mẫu bất đồng -> Kappa >= 0.75 (Vùng Đạt chuẩn)."""
        a = ["phishing"] * 15 + ["benign"] * 10 + ["insufficient_evidence"] * 5
        b = list(a)
        # 1 mẫu phishing -> B gán benign; 1 mẫu insufficient_evidence -> B gán benign
        b[0] = "benign"
        b[25] = "benign"

        res = compute_kappa_3x3(a, b, bootstrap_iterations=1000, random_seed=42)

        assert res.sample_count == 30
        assert res.observed_agreement == pytest.approx(28 / 30, rel=1e-3)
        assert res.kappa is not None
        assert res.kappa >= 0.75
        assert res.zone == "pass"
        assert res.se_fleiss is not None and res.se_fleiss > 0.0
        assert res.ci95_fleiss is not None
        assert res.ci95_fleiss[0] <= res.kappa <= res.ci95_fleiss[1]
        assert res.ci95_bootstrap is not None
        assert res.ci95_bootstrap[0] <= res.kappa <= res.ci95_bootstrap[1]

    def test_conditional_review_zone(self):
        """Mức đồng thuận vùng ranh giới 0.60 <= kappa < 0.75 -> zone = conditional_review."""
        a = ["phishing"] * 12 + ["benign"] * 12 + ["insufficient_evidence"] * 6
        b = list(a)
        # B bất đồng 6 mẫu
        b[0] = "benign"
        b[1] = "benign"
        b[12] = "phishing"
        b[13] = "insufficient_evidence"
        b[24] = "benign"
        b[25] = "phishing"

        res = compute_kappa_3x3(a, b, bootstrap_iterations=500, random_seed=42)

        assert 0.60 <= res.kappa < 0.75
        assert res.zone == "conditional_review"

    def test_stop_zone(self):
        """Mức đồng thuận thấp kappa < 0.60 -> zone = stop."""
        a = ["phishing"] * 10 + ["benign"] * 10 + ["insufficient_evidence"] * 10
        b = ["benign"] * 8 + ["phishing"] * 2 + ["insufficient_evidence"] * 8 + ["benign"] * 2 + ["phishing"] * 8 + ["insufficient_evidence"] * 2

        res = compute_kappa_3x3(a, b, bootstrap_iterations=500, random_seed=42)

        assert res.kappa < 0.60
        assert res.zone == "stop"

    def test_single_class_edge_case(self):
        """Trường hợp toàn bộ mẫu chỉ có 1 danh mục (Pe = 1.0) -> Kappa = None, undefined."""
        a = ["phishing"] * 30
        b = ["phishing"] * 30

        res = compute_kappa_3x3(a, b)

        assert res.kappa is None
        assert res.status == "undefined_single_class"
        assert res.zone == "undefined"
        assert res.observed_agreement == 1.0
        assert res.expected_agreement == 1.0

    def test_reject_unauthorized_label(self):
        """Bắt buộc chỉ nhận 3 nhãn Codebook v1.1. Nhãn lạ phải bị từ chối ngay."""
        a = ["phishing", "benign", "malicious"]
        b = ["phishing", "benign", "benign"]

        with pytest.raises(ValueError, match="malicious"):
            compute_kappa_3x3(a, b)

    def test_reject_empty_or_mismatched_length(self):
        """Lệch độ dài hoặc danh sách rỗng ném ValueError."""
        with pytest.raises(ValueError, match="cùng độ dài"):
            compute_kappa_3x3(["phishing"], ["phishing", "benign"])

        with pytest.raises(ValueError, match="không được rỗng"):
            compute_kappa_3x3([], [])


class TestKappa3x3FromRecords:
    """Kiểm thử tính toán từ AnnotationRecord của A và B."""

    def test_records_paired_by_sample_id_independent_of_order(self):
        """Ghép cặp tuyệt đối theo sample_id khi thứ tự danh sách của A và B bị xáo trộn."""
        recs_a = [
            {"sample_id": f"BLIND-{i:03d}", "class_label": "phishing"} for i in range(1, 11)
        ] + [
            {"sample_id": f"BLIND-{i:03d}", "class_label": "benign"} for i in range(11, 21)
        ] + [
            {"sample_id": f"BLIND-{i:03d}", "class_label": "insufficient_evidence"} for i in range(21, 31)
        ]

        recs_b = list(reversed(recs_a))

        res = compute_kappa_3x3_from_records(recs_a, recs_b, bootstrap_iterations=500)

        assert res.sample_count == 30
        assert res.kappa == 1.0
        assert res.zone == "pass"

    def test_records_filters_dry_run_automatically(self):
        """Tự động bỏ qua các bản ghi dry-run (is_dry_run=True)."""
        recs_a = [
            {"sample_id": "BLIND-001", "class_label": "phishing", "is_dry_run": False},
            {"sample_id": "BLIND-002", "class_label": "benign", "is_dry_run": False},
            {"sample_id": "BLIND-003", "class_label": "insufficient_evidence", "is_dry_run": True},
        ]
        recs_b = [
            {"sample_id": "BLIND-001", "class_label": "phishing", "is_dry_run": False},
            {"sample_id": "BLIND-002", "class_label": "benign", "is_dry_run": False},
            {"sample_id": "BLIND-003", "class_label": "benign", "is_dry_run": True},
        ]

        res = compute_kappa_3x3_from_records(recs_a, recs_b, allow_dry_run=False, bootstrap_iterations=200)

        assert res.sample_count == 2
        assert res.matrix_3x3[0][0] == 1
        assert res.matrix_3x3[1][1] == 1

    def test_records_rejects_sample_id_mismatch(self):
        """Ném ValueError nếu tập sample_id giữa A và B không khớp 100%."""
        recs_a = [{"sample_id": "BLIND-001", "class_label": "phishing"}]
        recs_b = [{"sample_id": "BLIND-002", "class_label": "phishing"}]

        with pytest.raises(ValueError, match="không khớp"):
            compute_kappa_3x3_from_records(recs_a, recs_b)


class TestFormatKappa3x3Report:
    """Kiểm thử xuất báo cáo Markdown đồng thuận."""

    def test_report_formatting(self):
        a = ["phishing"] * 15 + ["benign"] * 10 + ["insufficient_evidence"] * 5
        b = list(a)
        b[0] = "benign"

        res = compute_kappa_3x3(a, b, bootstrap_iterations=500, random_seed=42)
        report = format_kappa_3x3_report(res)

        assert "BÁO CÁO ĐỒNG THUẬN COHEN'S KAPPA MA TRẬN 3x3" in report
        assert "Quy mô mẫu đối soát ($N$):** 30 mẫu" in report
        assert "VÙNG ĐẠT CHUẨN" in report
        assert "| Rater A (Hàng) \\ Rater B (Cột) | Phishing | Benign | Insufficient Evidence |" in report
        assert "Hệ số Cohen's Kappa ($3 \\times 3$):" in report
        assert "Fleiss CI 95%" in report
        assert "Bootstrap CI 95%" in report
