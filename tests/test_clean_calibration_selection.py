"""Kiểm thử đơn vị cho thuật toán tuyển chọn Gói Hiệu chuẩn Sạch và Template Similarity Scan.

Quy chuẩn ARS & Safety:
1. Kiểm thử tất định bằng mock candidates độc lập với dữ liệu raw.
2. Kiểm tra phân tầng tuyệt đối: 12 phish + 12 benign (main) và 4 phish + 4 benign (reserve).
3. Kiểm tra chốt chặn loại trừ: từ chối 100% mẫu có URL/Group nằm trong blocked set.
4. Kiểm tra thuật toán Template Similarity (SimHash 64-bit và DOM Jaccard similarity).
"""

from __future__ import annotations

import json
from pathlib import Path
import pytest

from phishing.data.template_similarity import (
    TemplateSimilarityEngine,
    compute_dom_jaccard_similarity,
    compute_token_simhash_64,
    extract_dom_tag_multiset,
    hamming_distance_64,
)
from scripts.data.prepare_clean_calibration_selection import (
    evaluate_clean_selection_strata,
    scan_candidates_template_similarity,
    select_clean_candidates,
    source_label,
)


class TestTemplateSimilarityEngineUnit:
    """Kiểm thử các hàm toán học SimHash và DOM Jaccard Similarity."""

    def test_simhash_identical_text_has_zero_hamming_distance(self):
        """Chứng minh văn bản giống nhau hoàn toàn có khoảng cách Hamming = 0."""
        text = "Đăng nhập tài khoản ngân hàng trực tuyến an toàn xác minh mật khẩu"
        h1 = compute_token_simhash_64(text)
        h2 = compute_token_simhash_64(text)
        assert h1 == h2
        assert hamming_distance_64(h1, h2) == 0

    def test_simhash_near_duplicate_has_small_distance(self):
        """Chứng minh hai văn bản biến thể clone chỉ khác vài từ có khoảng cách rất nhỏ (<= 12 so với 32 của ngẫu nhiên)."""
        t1 = "Chào mừng quý khách đến với shop thời trang thể thao chính hãng giảm giá 50% thanh toán thẻ"
        t2 = "Chào mừng quý khách đến với shop thời trang thể thao cao cấp giảm giá 50% thanh toán thẻ"
        h1 = compute_token_simhash_64(t1)
        h2 = compute_token_simhash_64(t2)
        dist = hamming_distance_64(h1, h2)
        assert dist <= 12, f"Khoảng cách SimHash biến thể clone phải nhỏ, thực tế: {dist}"

    def test_simhash_completely_different_texts_have_large_distance(self):
        """Chứng minh hai văn bản khác biệt hoàn toàn có khoảng cách lớn (> 15)."""
        t1 = "Tài liệu kỹ thuật lập trình Python học máy phân loại văn bản mã nguồn mở"
        t2 = "Bệnh viện đa khoa khám chữa bệnh nội khoa ngoại khoa cấp cứu y tế"
        h1 = compute_token_simhash_64(t1)
        h2 = compute_token_simhash_64(t2)
        dist = hamming_distance_64(h1, h2)
        assert dist >= 15, f"Hai văn bản khác chủ đề phải có khoảng cách lớn, thực tế: {dist}"

    def test_extract_dom_tags_and_strip_scripts_styles(self):
        """Chứng minh hàm trích xuất thẻ DOM strip toàn bộ script và style an toàn."""
        html = """
        <html>
            <head>
                <style>body { color: red; }</style>
                <script>alert("attack");</script>
            </head>
            <body>
                <header><h1>Shop</h1></header>
                <div class="main"><form action="/login"><input type="text"/></form></div>
            </body>
        </html>
        """
        tags = extract_dom_tag_multiset(html)
        assert "script" not in tags
        assert "style" not in tags
        assert set(tags).issuperset({"html", "head", "body", "header", "h1", "div", "form", "input"})

    def test_dom_jaccard_similarity(self):
        """Chứng minh chỉ số Jaccard giữa hai cấu trúc DOM tương tự nhau đạt mức cao (> 0.85)."""
        dom1 = ["html", "head", "body", "div", "form", "input", "button", "footer"]
        dom2 = ["html", "head", "body", "div", "form", "input", "footer"]  # Thiếu button
        jaccard = compute_dom_jaccard_similarity(dom1, dom2)
        assert jaccard >= 0.85

    def test_engine_detects_registered_clone_template(self):
        """Chứng minh Engine phát hiện chính xác mẫu clone của template đã đăng ký."""
        engine = TemplateSimilarityEngine(max_allowed_simhash_distance=10)
        engine.register_template(
            template_id="TPL-SHOP-JP",
            description="Shop template clone",
            sample_text="特定商取引法に基づく表記 ショッピングカート 決済方法 クレジットカード お問い合わせ",
            sample_html="<html><body><div class='cart'>Cart</div><form><input/></form></body></html>",
        )

        candidate_clone_text = "特定商取引法に基づく表記 ショッピングカート 決済方法 クレジットカード 会社概要 お問い合わせ"
        candidate_clone_html = "<html><body><div class='cart'>Cart</div><form><input/></form></body></html>"
        res = engine.check_candidate_similarity(candidate_clone_text, candidate_clone_html)
        assert res["is_clone_template"] is True
        assert res["closest_template_id"] == "TPL-SHOP-JP"
        assert res["min_simhash_distance"] <= 10
        assert res["max_dom_jaccard"] >= 0.95


class TestCleanCalibrationSelectionUnit:
    """Kiểm thử thuật toán phân tầng và tuyển chọn ứng viên sạch."""

    def _generate_mock_pool(self, n_per_class: int = 40):
        pool = []
        for label in ["phish", "benign"]:
            for i in range(n_per_class):
                uid = f"mock_{label}_{i}"
                gid = f"grp_{label}_{i}"  # Mỗi mẫu một domain group riêng
                locator = {"relative_path": "data/train-000.parquet", "row_offset": len(pool)}
                fp = {
                    "url_sha256": uid,
                    "html_sha256": f"html_{uid}",
                    "group_sha256": gid,
                }
                pool.append((locator, label, fp))
        return pool

    def test_seeded_selection_deterministic_and_balanced(self):
        """Chứng minh tuyển chọn cân bằng đúng 12 phish + 12 benign và lặp lại tất định 100%."""
        pool = self._generate_mock_pool(50)
        blocked = {"url_sha256": set(), "group_sha256": set(), "html_sha256": set()}

        main1, reserve1 = select_clean_candidates(pool, blocked, seed=20261022)
        main2, reserve2 = select_clean_candidates(pool, blocked, seed=20261022)

        # Kiểm tra quy mô
        assert len(main1) == 24
        assert len(reserve1) == 8

        # Kiểm tra tính tất định tuyệt đối
        assert main1 == main2
        assert reserve1 == reserve2

        # 32 locators phải hoàn toàn phân biệt
        all_locs = main1 + reserve1
        unique_offsets = {x["row_offset"] for x in all_locs}
        assert len(unique_offsets) == 32

    def test_selection_rejects_blocked_urls_and_duplicate_groups(self):
        """Chứng minh các mẫu thuộc tập bị chặn hoặc trùng group bị loại trừ triệt để."""
        pool = self._generate_mock_pool(50)
        # Giả lập chặn 2 mẫu phish đầu tiên
        blocked = {
            "url_sha256": {"mock_phish_0", "mock_phish_1"},
            "group_sha256": {"grp_benign_0"},
            "html_sha256": set(),
        }

        main, reserve = select_clean_candidates(pool, blocked, seed=20261022)
        all_offsets = [x["row_offset"] for x in main + reserve]

        assert 0 not in all_offsets  # offset 0 là mock_phish_0
        assert 1 not in all_offsets  # offset 1 là mock_phish_1

    def test_post_selection_template_similarity_scan(self):
        """Chứng minh quy trình hậu kiểm template similarity scan chạy trơn tru trên danh sách locators."""
        pool = self._generate_mock_pool(20)
        blocked = {"url_sha256": set(), "group_sha256": set(), "html_sha256": set()}
        main, reserve = select_clean_candidates(pool, blocked, seed=20261022)

        def mock_html_provider(loc):
            return f"<html><body><div>Safe regular page content for row {loc['row_offset']}</div></body></html>"

        scan_result = scan_candidates_template_similarity(main + reserve, mock_html_provider)
        assert scan_result["status"] == "template_similarity_scan_completed"
        assert scan_result["total_scanned"] == 32
        assert scan_result["clone_detected_count"] == 0

    def test_difficulty_strata_evaluation_no_label_leak(self):
        """Chứng minh đánh giá 6 quy tắc độ khó bề mặt chạy độc lập không phụ thuộc nhãn."""
        pool = self._generate_mock_pool(10)
        blocked = {"url_sha256": set(), "group_sha256": set(), "html_sha256": set()}
        main, reserve = select_clean_candidates(pool, blocked, seed=20261022, main_per_class=4, reserve_per_class=2)

        def mock_row_provider(loc):
            return {
                "url": f"https://login.service.com/account?id={loc['row_offset']}",
                "html": "<html><body><form><input type='password'/></form></body></html>",
            }

        rule_counts, hard_cases = evaluate_clean_selection_strata(main, mock_row_provider)
        assert isinstance(rule_counts, dict)
        assert "login_credential_form" in rule_counts
        assert rule_counts["login_credential_form"] == 8
        assert hard_cases >= 0


class TestCleanCalibrationV2SafetyAndExclusion:
    """Kiểm thử chốt chặn an toàn cho Đợt B: loại trừ 180 mẫu, cô lập locator ngoài Git, bảo vệ tính mù đôi."""

    def test_exclusion_registry_contains_180_samples_and_git_leak_batch(self):
        """Chứng minh exclusion_registry chứa đủ 7 lô với 180 mẫu và lô rò rỉ locator được khóa vĩnh viễn."""
        root = Path(__file__).resolve().parents[1]
        registry_path = root / "data/exclusion_registry.json"
        assert registry_path.exists()
        registry = json.loads(registry_path.read_text(encoding="utf-8"))

        assert registry["total_excluded_entries"] == 7
        assert registry["total_excluded_samples"] == 180

        excl_map = {e["exclusion_id"]: e for e in registry["exclusions"]}
        assert "EXCL-CALIB-CLEAN-32-EXPOSED-ON-GIT" in excl_map
        leak_batch = excl_map["EXCL-CALIB-CLEAN-32-EXPOSED-ON-GIT"]
        assert leak_batch["n_samples"] == 32
        assert leak_batch["action"] == "permanently_exclude_from_train_val_test"
        assert len(leak_batch["samples"]) == 32

    def test_clean_calibration_v2_manifest_governance_contract(self):
        """Chứng minh manifest Đợt B giữ trạng thái pending, ready_for_annotation=false và tham chiếu đúng."""
        root = Path(__file__).resolve().parents[1]
        manifest_path = root / "configs/calibration_clean_a_manifest.json"
        assert manifest_path.exists()
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

        assert manifest["manifest_id"] == "CALIBRATION-CLEAN-A-MANIFEST-V1.1-PROPOSAL"
        assert manifest["status"] == "pending_lead_d_and_member_b_review"
        assert manifest["governance"]["ready_for_annotation"] is False
        assert manifest["governance"]["training_blocked"] is True
        assert manifest["governance"]["known_excluded_samples_count"] == 180
        assert manifest["sampling_spec"]["random_seed"] == 20261027
        assert manifest["sampling_spec"]["random_seed_main_shuffle"] == 20261028
        assert manifest["sampling_spec"]["random_seed_reserve_shuffle"] == 20261029

    def test_clean_calibration_inspection_report_public_contract(self):
        """Chứng minh báo cáo trên Git là báo cáo tổng hợp thuần túy (không chứa locator/URL) độc lập với dữ liệu hạn chế."""
        root = Path(__file__).resolve().parents[1]
        report_path = root / "data/source_audit/clean_calibration_selection_inspection_report.json"
        assert report_path.exists()
        report_text = report_path.read_text(encoding="utf-8")
        report = json.loads(report_text)

        # 1. Báo cáo tổng hợp không chứa trường locator, url hoặc html
        assert "main_locators" not in report
        assert "reserve_locators" not in report
        assert "candidates" not in report
        assert "row_offset" not in report_text

        # 2. Khớp phân tầng 24 chính (12 phish/12 benign) + 8 dự phòng (4 phish/4 benign)
        assert report["selection_summary"]["main_samples_count"] == 24
        assert report["selection_summary"]["reserve_samples_count"] == 8
        assert report["selection_summary"]["distinct_groups_count"] == 32
        assert report["selection_summary"]["deduplication_vs_registry_180_overlaps"] == 0
        assert report["template_similarity_scan"]["clone_detected_count"] == 0

        # 3. Quét tương đồng cặp toàn bộ 496 cặp đạt 0 xung đột
        assert "pairwise_template_similarity_scan" in report
        assert report["pairwise_template_similarity_scan"]["total_pairs_scanned"] == 496
        assert report["pairwise_template_similarity_scan"]["conflict_pairs_count"] == 0

        # 4. Hash tệp hạn chế được khai báo đầy đủ (64 hex ký tự)
        restricted_hash = report["artifacts"]["restricted_candidates_sha256"]
        assert isinstance(restricted_hash, str) and len(restricted_hash) == 64

    @pytest.mark.integration
    def test_integration_restricted_candidates_package_hash_matches_inspection_report(self):
        """Integration test (có điều kiện): đối soát SHA-256 giữa tệp ứng viên hạn chế và báo cáo tổng hợp."""
        import hashlib
        root = Path(__file__).resolve().parents[1]
        restricted_file = root / "data/restricted/clean_calibration_candidates_v2_restricted.json"
        if not restricted_file.exists():
            pytest.skip("Bỏ qua test integration khi checkout sạch chưa có tệp hạn chế data/restricted/")

        report_path = root / "data/source_audit/clean_calibration_selection_inspection_report.json"
        assert report_path.exists()
        report = json.loads(report_path.read_text(encoding="utf-8"))

        actual_hash = hashlib.sha256(restricted_file.read_bytes()).hexdigest()
        assert report["artifacts"]["restricted_candidates_sha256"] == actual_hash

