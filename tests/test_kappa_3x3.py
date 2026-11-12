"""Bộ kiểm thử độc lập cho Module Cohen's Kappa Ma trận 3x3 (Codebook v1.1).

Kiểm chứng toàn diện 5 yêu cầu vòng 8 của Lead D:
1. Loại bỏ triệt để công thức Fleiss rút gọn, chỉ dùng Paired Bootstrap.
2. Kiểm tra chặt chẽ ngưỡng suy biến B_deg/B: dưới 5% thì công bố CI, vượt 5% thì KHÔNG công bố CI.
3. Đối chiếu độc lập ma trận chuẩn N=30 (Po=0.8333, Pe=0.3367, Kappa=0.7487, CI 95%=[0.5361, 0.9468], seed 2026).
4. Kiểm tra tính tái lập tuyệt đối (reproducibility) khi chạy cùng seed 2026.
5. Kiểm tra ranh giới ghép cặp Đợt 1 (A có 100 mẫu, B có 30 mẫu) qua target_sample_ids.
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
        """Đồng thuận tuyệt đối trên cả 3 danh mục -> Kappa = 1.0, zone = pass, B_deg = 0."""
        a = ["phishing"] * 15 + ["benign"] * 10 + ["insufficient_evidence"] * 5
        b = list(a)

        res = compute_kappa_3x3(a, b, bootstrap_iterations=500, random_seed=2026)

        assert res.sample_count == 30
        assert res.observed_agreement == 1.0
        assert res.kappa == 1.0
        assert res.ci95_bootstrap == (1.0, 1.0)
        assert res.bootstrap_degenerate_count == 0
        assert res.bootstrap_degenerate_ratio == 0.0
        assert res.bootstrap_warning is None
        assert res.status == "valid"
        assert res.zone == "pass"

    def test_realistic_pass_zone(self):
        """30 mẫu: 28 mẫu đồng thuận, 2 mẫu bất đồng -> Kappa >= 0.75 (Vùng Đạt chuẩn)."""
        a = ["phishing"] * 15 + ["benign"] * 10 + ["insufficient_evidence"] * 5
        b = list(a)
        b[0] = "benign"
        b[25] = "benign"

        res = compute_kappa_3x3(a, b, bootstrap_iterations=1000, random_seed=2026)

        assert res.sample_count == 30
        assert res.observed_agreement == pytest.approx(28 / 30, rel=1e-3)
        assert res.kappa is not None
        assert res.kappa >= 0.75
        assert res.zone == "pass"
        assert res.ci95_bootstrap is not None
        assert res.ci95_bootstrap[0] <= res.kappa <= res.ci95_bootstrap[1]
        assert res.bootstrap_degenerate_count == 0

    def test_conditional_review_zone(self):
        """Mức đồng thuận vùng ranh giới 0.60 <= kappa < 0.75 -> zone = conditional_review."""
        a = ["phishing"] * 12 + ["benign"] * 12 + ["insufficient_evidence"] * 6
        b = list(a)
        b[0] = "benign"
        b[1] = "benign"
        b[12] = "phishing"
        b[13] = "insufficient_evidence"
        b[24] = "benign"
        b[25] = "phishing"

        res = compute_kappa_3x3(a, b, bootstrap_iterations=500, random_seed=2026)

        assert 0.60 <= res.kappa < 0.75
        assert res.zone == "conditional_review"

    def test_stop_zone(self):
        """Mức đồng thuận thấp kappa < 0.60 -> zone = stop."""
        a = ["phishing"] * 10 + ["benign"] * 10 + ["insufficient_evidence"] * 10
        b = ["benign"] * 8 + ["phishing"] * 2 + ["insufficient_evidence"] * 8 + ["benign"] * 2 + ["phishing"] * 8 + ["insufficient_evidence"] * 2

        res = compute_kappa_3x3(a, b, bootstrap_iterations=500, random_seed=2026)

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
        assert res.ci95_bootstrap is None

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


class TestBootstrapDegenerateThreshold:
    """Kiểm thử hai phía của ngưỡng suy biến B_deg / B (Directive 2 của Lead D)."""

    def test_degenerate_rate_below_threshold_publishes_ci(self):
        """Phía 1: Tỷ lệ suy biến <= 5% (bình thường = 0%) -> CI được công bố đầy đủ."""
        a = ["phishing"] * 15 + ["benign"] * 10 + ["insufficient_evidence"] * 5
        b = list(a)

        res = compute_kappa_3x3(a, b, bootstrap_iterations=1000, random_seed=2026, max_degenerate_ratio=0.05)

        assert res.bootstrap_degenerate_ratio <= 0.05
        assert res.ci95_bootstrap is not None
        assert res.bootstrap_warning is None

    def test_degenerate_rate_above_threshold_suppresses_ci(self):
        """Phía 2: Tỷ lệ suy biến > 5% (mẫu cực kỳ mất cân đối: 29 phishing, 1 benign).

        Xác suất bốc toàn phishing trong 30 lần rút: (29/30)^30 ≈ 36.1% > 5%.
        -> Hệ thống từ chối công bố CI (ci95_bootstrap=None) và phát cảnh báo rõ ràng.
        """
        a = ["phishing"] * 29 + ["benign"] * 1
        b = list(a)

        res = compute_kappa_3x3(a, b, bootstrap_iterations=1000, random_seed=2026, max_degenerate_ratio=0.05)

        assert res.bootstrap_degenerate_ratio > 0.05
        assert res.ci95_bootstrap is None
        assert res.bootstrap_warning is not None
        assert "vượt ngưỡng tối đa" in res.bootstrap_warning


class TestIndependentBenchmarkAndReproducibility:
    """Kiểm thử đối chiếu độc lập ma trận N=30 chuẩn benchmark và tính tái lập (Directive 3)."""

    def test_benchmark_matrix_n30_exact_values(self):
        """Kiểm chứng số học đối chiếu bảng liên hợp N=30 trong báo cáo V3.4/V3.5:
        Matrix:
          Row 0 (phishing): [8, 1, 0] (Tổng 9)
          Row 1 (benign): [1, 7, 2] (Tổng 10)
          Row 2 (insufficient_evidence): [0, 1, 10] (Tổng 11)
        """
        a = ["phishing"] * 9 + ["benign"] * 10 + ["insufficient_evidence"] * 11
        b = (
            ["phishing"] * 8 + ["benign"] * 1
            + ["phishing"] * 1 + ["benign"] * 7 + ["insufficient_evidence"] * 2
            + ["benign"] * 1 + ["insufficient_evidence"] * 10
        )

        res = compute_kappa_3x3(a, b, bootstrap_iterations=1000, random_seed=2026)

        assert res.sample_count == 30
        assert res.observed_agreement == pytest.approx(0.8333, abs=1e-4)
        assert res.expected_agreement == pytest.approx(0.3367, abs=1e-4)
        assert res.kappa == pytest.approx(0.7487, abs=1e-4)
        assert res.ci95_bootstrap == (0.5361, 0.9468)
        assert res.bootstrap_degenerate_count == 0
        assert res.bootstrap_degenerate_ratio == 0.0

    def test_deterministic_reproducibility_with_seed(self):
        """Chạy cùng seed 2026 trên cùng dữ liệu cho kết quả CI 95% hoàn toàn đồng nhất 100%."""
        a = ["phishing"] * 9 + ["benign"] * 10 + ["insufficient_evidence"] * 11
        b = (
            ["phishing"] * 8 + ["benign"] * 1
            + ["phishing"] * 1 + ["benign"] * 7 + ["insufficient_evidence"] * 2
            + ["benign"] * 1 + ["insufficient_evidence"] * 10
        )

        run1 = compute_kappa_3x3(a, b, bootstrap_iterations=1000, random_seed=2026)
        run2 = compute_kappa_3x3(a, b, bootstrap_iterations=1000, random_seed=2026)

        assert run1.ci95_bootstrap == run2.ci95_bootstrap
        assert run1.kappa == run2.kappa


class TestRecordsPairingAndBoundaryĐot1:
    """Kiểm thử ranh giới hàm nhận bản ghi Đợt 1 (A có 100 mẫu, B có 30 mẫu) (Directive 4)."""

    def test_records_paired_with_target_sample_ids_filters_a_100_to_b_30(self):
        """A có 100 bản ghi, B có 30 bản ghi: Truyền target_sample_ids lọc đúng 30 mẫu ngẫu nhiên."""
        # A gán 100 mẫu với nhãn đa dạng
        labels_pattern = ["phishing"] * 15 + ["benign"] * 10 + ["insufficient_evidence"] * 5
        recs_a = [
            {"sample_id": f"BLIND-{i:03d}", "class_label": labels_pattern[(i - 1) % len(labels_pattern)]}
            for i in range(1, 101)
        ]
        # B chỉ gán 30 mẫu ngẫu nhiên (ví dụ BLIND-001 đến BLIND-030) khớp hoàn toàn với A
        target_30_ids = [f"BLIND-{i:03d}" for i in range(1, 31)]
        recs_b = [
            {"sample_id": f"BLIND-{i:03d}", "class_label": labels_pattern[(i - 1) % len(labels_pattern)]}
            for i in range(1, 31)
        ]

        res = compute_kappa_3x3_from_records(
            recs_a,
            recs_b,
            target_sample_ids=target_30_ids,
            bootstrap_iterations=500,
            random_seed=2026,
        )

        assert res.sample_count == 30
        assert res.kappa == 1.0
        assert res.zone == "pass"

    def test_records_mismatched_sample_counts_without_target_ids_raises_error(self):
        """Nếu A có 100 mẫu, B có 30 mẫu mà không truyền target_sample_ids thì ném lỗi rõ ràng."""
        recs_a = [{"sample_id": f"BLIND-{i:03d}", "class_label": "phishing"} for i in range(1, 101)]
        recs_b = [{"sample_id": f"BLIND-{i:03d}", "class_label": "phishing"} for i in range(1, 31)]

        with pytest.raises(ValueError, match="Tập hợp sample_id không khớp"):
            compute_kappa_3x3_from_records(recs_a, recs_b)

    def test_records_missing_target_id_raises_error(self):
        """Nếu danh sách target_sample_ids chứa ID không có trong A hoặc B thì ném lỗi."""
        recs_a = [{"sample_id": "BLIND-001", "class_label": "phishing"}]
        recs_b = [{"sample_id": "BLIND-001", "class_label": "phishing"}]

        with pytest.raises(ValueError, match="LỖI GHÉP CẶP PHÂN TẦNG"):
            compute_kappa_3x3_from_records(recs_a, recs_b, target_sample_ids=["BLIND-001", "BLIND-999"])


class TestFormatKappa3x3Report:
    """Kiểm thử định dạng báo cáo Markdown chuẩn ARS (không chứa Fleiss)."""

    def test_report_formatting_without_fleiss(self):
        a = ["phishing"] * 15 + ["benign"] * 10 + ["insufficient_evidence"] * 5
        b = list(a)
        b[0] = "benign"

        res = compute_kappa_3x3(a, b, bootstrap_iterations=500, random_seed=2026)
        report = format_kappa_3x3_report(res)

        assert "BÁO CÁO ĐỒNG THUẬN COHEN'S KAPPA MA TRẬN 3x3" in report
        assert "Quy mô mẫu đối soát ($N$):** 30 mẫu" in report
        assert "VÙNG ĐẠT CHUẨN" in report
        assert "Khoảng tin cậy 95% Paired Bootstrap" in report
        assert "fleiss" not in report.lower(), "Báo cáo tuyệt đối không được chứa thuật ngữ Fleiss!"
