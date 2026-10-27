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
    """Kiểm thử chốt chặn an toàn cho Đợt B: loại trừ 214 mẫu (gồm 182 mẫu cũ + 32 mẫu sạch Runway A), cô lập locator ngoài Git, bảo vệ tính mù đôi."""

    def test_exclusion_registry_contains_214_samples_and_git_leak_batches(self):
        """Chứng minh exclusion_registry chứa đủ 9 lô với 214 mẫu và 2 lô rò rỉ locator được khóa vĩnh viễn cùng 32 mẫu sạch Runway A."""
        root = Path(__file__).resolve().parents[1]
        registry_path = root / "data/exclusion_registry.json"
        assert registry_path.exists()
        registry = json.loads(registry_path.read_text(encoding="utf-8"))

        assert registry["total_excluded_entries"] == 9
        assert registry["total_excluded_samples"] == 214

        excl_map = {e["exclusion_id"]: e for e in registry["exclusions"]}
        assert "EXCL-CALIB-CLEAN-32-EXPOSED-ON-GIT" in excl_map
        leak_batch_32 = excl_map["EXCL-CALIB-CLEAN-32-EXPOSED-ON-GIT"]
        assert leak_batch_32["n_samples"] == 32
        assert leak_batch_32["action"] == "permanently_exclude_from_train_val_test"

        assert "EXCL-CALIB-CLEAN-02-PAIRWISE-RESOLUTION-LOCATOR-EXPOSED" in excl_map
        leak_batch_02 = excl_map["EXCL-CALIB-CLEAN-02-PAIRWISE-RESOLUTION-LOCATOR-EXPOSED"]
        assert leak_batch_02["n_samples"] == 2
        assert leak_batch_02["action"] == "permanently_exclude_from_train_val_test"
        assert len(leak_batch_02["samples"]) == 2

        assert "EXCL-CALIBRATION-CLEAN-RUNWAY-32" in excl_map
        clean_runway_batch = excl_map["EXCL-CALIBRATION-CLEAN-RUNWAY-32"]
        assert clean_runway_batch["n_samples"] == 32
        assert clean_runway_batch["action"] == "permanently_exclude_from_train_val_test"
        assert len(clean_runway_batch["samples"]) == 32

    def test_tripartite_exclusion_consistency(self):
        """Chứng minh tính nhất quán trực tiếp ba bên: exclusion_registry, audit_report và manifest (chỉ đạo Lead D)."""
        import hashlib
        root = Path(__file__).resolve().parents[1]

        registry_path = root / "data/exclusion_registry.json"
        audit_path = root / "data/source_audit/clean_calibration_exclusion_audit_report.json"
        git_leak_path = root / "data/source_audit/clean_calibration_git_leak_audit.json"
        manifest_path = root / "configs/calibration_clean_a_manifest.json"

        assert registry_path.exists(), "Thiếu data/exclusion_registry.json"
        assert audit_path.exists(), "Thiếu data/source_audit/clean_calibration_exclusion_audit_report.json"
        assert git_leak_path.exists(), "Thiếu data/source_audit/clean_calibration_git_leak_audit.json"
        assert manifest_path.exists(), "Thiếu configs/calibration_clean_a_manifest.json"

        registry_bytes = registry_path.read_bytes()
        audit_bytes = audit_path.read_bytes()
        git_leak_bytes = git_leak_path.read_bytes()

        registry_sha256 = hashlib.sha256(registry_bytes).hexdigest()
        audit_sha256 = hashlib.sha256(audit_bytes).hexdigest()
        git_leak_sha256 = hashlib.sha256(git_leak_bytes).hexdigest()

        registry = json.loads(registry_bytes.decode("utf-8"))
        audit = json.loads(audit_bytes.decode("utf-8"))
        git_leak = json.loads(git_leak_bytes.decode("utf-8"))
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

        # 1. Trụ 1: Registry kiểm đếm mẫu và lô
        reg_entries = registry["total_excluded_entries"]
        reg_samples = registry["total_excluded_samples"]
        assert reg_entries == 9, f"Registry phải có 9 lô, thực tế: {reg_entries}"
        assert reg_samples == 214, f"Registry phải có 214 mẫu, thực tế: {reg_samples}"
        assert len(registry["exclusions"]) == 9
        counted_samples = sum(e.get("n_samples", len(e.get("samples", []))) for e in registry["exclusions"])
        assert counted_samples == 214

        # 2. Trụ 2: Báo cáo kiểm kê loại trừ đối soát trực tiếp registry
        assert audit["governance"]["registry_sha256"] == registry_sha256
        assert audit["governance"]["total_excluded_entries_in_registry"] == 9
        assert audit["governance"]["total_excluded_samples_in_registry"] == 214
        assert audit["inventory"]["total_batches_count"] == 9
        assert audit["inventory"]["total_samples_count"] == 214
        assert len(audit["inventory"]["batches"]) == 9
        audit_batch_sum = sum(b["sample_count"] for b in audit["inventory"]["batches"])
        assert audit_batch_sum == 214

        # 3. Trụ 3: Manifest liên kết mã băm cryptographic và số lượng chốt chặn
        manifest_gov = manifest["governance"]
        assert manifest_gov["exclusion_registry_sha256"] == registry_sha256
        assert manifest_gov["exclusion_audit_sha256"] == audit_sha256
        assert manifest_gov["git_leak_audit_sha256"] == git_leak_sha256
        assert manifest_gov["known_excluded_samples_count"] == 214
        assert manifest_gov["ready_for_annotation"] is False
        assert manifest_gov["training_blocked"] is True

        # 4. Đối soát ba bên chéo (Tripartite Cross-Check)
        assert reg_samples == audit["inventory"]["total_samples_count"] == manifest_gov["known_excluded_samples_count"] == 214
        assert reg_entries == audit["inventory"]["total_batches_count"] == 9

        # 5. Hồ sơ kiểm toán sự cố Git leak ghi nhận đủ cả 2 sự cố và 34 locator
        assert git_leak["governance"]["total_incidents_recorded"] == 2
        assert git_leak["governance"]["total_exposed_locators_remediated"] == 34
        assert len(git_leak["incidents"]) == 2
        assert git_leak["governance"]["total_samples_in_exclusion_registry"] == 182

    def test_clean_calibration_v2_manifest_governance_contract(self):
        """Chứng minh manifest Đợt B giữ trạng thái pending, ready_for_annotation=false và tham chiếu đúng."""
        root = Path(__file__).resolve().parents[1]
        manifest_path = root / "configs/calibration_clean_a_manifest.json"
        assert manifest_path.exists()
        manifest_text = manifest_path.read_text(encoding="utf-8")
        manifest = json.loads(manifest_text)

        assert manifest["manifest_id"] == "CALIBRATION-CLEAN-A-MANIFEST-V1.1-PROPOSAL"
        assert manifest["status"] == "pending_lead_d_and_member_b_review"
        assert manifest["governance"]["ready_for_annotation"] is False
        assert manifest["governance"]["training_blocked"] is True
        assert manifest["governance"]["known_excluded_samples_count"] == 214
        assert manifest["sampling_spec"]["total_samples"] == 32
        assert manifest["sampling_spec"]["main_samples_count"] == 24
        assert manifest["sampling_spec"]["reserve_samples_count"] == 8
        assert manifest["sampling_spec"]["random_seed"] in (20261027, 20261035)
        assert manifest["sampling_spec"]["random_seed_main_shuffle"] in (20261028, 20261036)
        assert manifest["sampling_spec"]["random_seed_reserve_shuffle"] in (20261029, 20261037)

        # Chốt chặn mù nhãn nguồn: Manifest dành cho annotator KHÔNG được công bố trước tỷ lệ nhãn
        assert "stratification" not in manifest["sampling_spec"], "Manifest không được chứa trường stratification tiết lộ nhãn"
        assert "main_phish_count" not in manifest_text, "Manifest không được chứa main_phish_count"
        assert "main_benign_count" not in manifest_text, "Manifest không được chứa main_benign_count"
        assert "reserve_phish_count" not in manifest_text, "Manifest không được chứa reserve_phish_count"
        assert "reserve_benign_count" not in manifest_text, "Manifest không được chứa reserve_benign_count"

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
        assert report["selection_summary"]["deduplication_vs_registry_182_overlaps"] == 0
        assert report["template_similarity_scan"]["clone_detected_count"] == 0

        # 3. Quét tương đồng cặp toàn bộ 496 cặp đạt 0 xung đột theo cả 2 quy tắc
        assert "pairwise_template_similarity_scan" in report
        assert report["pairwise_template_similarity_scan"]["total_pairs_scanned"] == 496
        assert report["pairwise_template_similarity_scan"]["conflict_pairs_count"] == 0
        assert report["pairwise_template_similarity_scan"]["engine_rule_conflict_pairs_count"] == 0
        assert report["pairwise_template_similarity_scan"]["conjunction_rule_conflict_pairs_count"] == 0
        assert report["pairwise_template_similarity_scan"]["min_pairwise_simhash_distance"] >= 10

        # 4. Hash tệp hạn chế được khai báo đầy đủ (64 hex ký tự)
        restricted_hash = report["artifacts"]["restricted_candidates_sha256"]
        assert isinstance(restricted_hash, str) and len(restricted_hash) == 64

    def test_regression_public_report_zero_locator_leak(self):
        """Regression test nghiêm ngặt (theo chỉ đạo Lead D): đảm bảo báo cáo công khai không chứa vết locator/shard/row."""
        import re
        root = Path(__file__).resolve().parents[1]
        report_path = root / "data/source_audit/clean_calibration_selection_inspection_report.json"
        assert report_path.exists()
        report_text = report_path.read_text(encoding="utf-8")
        report = json.loads(report_text)

        # 1. Không chứa pattern locator như row 123 hoặc row_offset
        assert not re.search(r"row[_\s]+\d+", report_text, re.IGNORECASE), "Báo cáo công khai không được chứa chỉ số dòng (row offset)"
        assert not re.search(r"https?://", report_text), "Báo cáo công khai không được chứa URL thô"

        # 2. resolution_summary không chứa tên shard hoặc row
        res_summary = report.get("pairwise_template_similarity_scan", {}).get("resolution_summary", "")
        assert "train-" not in res_summary, "resolution_summary không được chứa tên shard"
        assert "row" not in res_summary.lower(), "resolution_summary không được chứa từ khóa row"
        assert "parquet" not in res_summary.lower(), "resolution_summary không được chứa đuôi tệp parquet"

    def test_member_b_qa_package_zero_leak_and_boundary(self):
        """Chứng minh ranh giới bàn giao gói QA cho Member B: 100% không rò rỉ dữ liệu và tách biệt với Lead D."""
        import zipfile
        root = Path(__file__).resolve().parents[1]
        zip_b_path = root / "GOI_QA_MEMBER_B_CALIBRATION_CLEAN_32.zip"
        zip_d_path = root / "GOI_RA_SOAT_HAN_CHE_CALIBRATION_CLEAN_32_V2.zip"

        if not zip_b_path.exists() or not zip_d_path.exists():
            from scripts.data.create_restricted_review_package import create_lead_d_package, create_member_b_qa_package
            create_lead_d_package()
            create_member_b_qa_package()

        assert zip_b_path.exists(), "Thiếu tệp GOI_QA_MEMBER_B_CALIBRATION_CLEAN_32.zip"
        assert zip_d_path.exists(), "Thiếu tệp GOI_RA_SOAT_HAN_CHE_CALIBRATION_CLEAN_32_V2.zip"

        # 1. Kiểm tra gói Lead D: chứa tệp hạn chế và mô tả dành riêng cho D
        with zipfile.ZipFile(zip_d_path, "r") as z_d:
            d_files = z_d.namelist()
            assert "candidates_restricted.json" in d_files
            assert "clean_calibration_git_leak_audit.json" in d_files
            assert "MANIFEST_RESTRICTED.json" in d_files

            manifest_d = json.loads(z_d.read("MANIFEST_RESTRICTED.json").decode("utf-8"))
            assert "Lead D" in manifest_d["recipient"]
            assert "dành cho Member B" not in manifest_d["purpose"]
            assert manifest_d["governance"]["contains_raw_locators"] is True

        # 2. Kiểm tra gói Member B: cấm tuyệt đối locator và tệp nhạy cảm
        with zipfile.ZipFile(zip_b_path, "r") as z_b:
            b_files = z_b.namelist()
            assert "candidates_restricted.json" not in b_files, "LỖI: Gói B chứa candidates_restricted.json"
            assert "clean_calibration_git_leak_audit.json" not in b_files, "LỖI: Gói B chứa clean_calibration_git_leak_audit.json"
            assert "MANIFEST_QA_MEMBER_B.json" in b_files
            assert "verify_member_b_qa.py" in b_files

            manifest_b = json.loads(z_b.read("MANIFEST_QA_MEMBER_B.json").decode("utf-8"))
            assert "Member B" in manifest_b["recipient"]
            assert manifest_b["governance"]["contains_raw_locators"] is False
            assert manifest_b["governance"]["contains_source_labels"] is False
            assert manifest_b["governance"]["ready_for_annotation"] is False
            assert manifest_b["governance"]["training_blocked"] is True

        # 3. Chạy công cụ kiểm tra tự động verify_member_b_package
        from scripts.data.verify_member_b_qa import verify_member_b_package
        qa_result = verify_member_b_package(zip_b_path)
        assert qa_result["zero_leak_verified"] is True
        assert qa_result["hash_integrity_verified"] is True
        assert qa_result["status"] == "QA_PASSED_READY_FOR_LEAD_D_SIGN_OFF"

    def test_regression_zero_source_label_ratio_leak_in_annotator_artifacts(self):
        """Regression test nghiêm ngặt (chỉ đạo Lead D): tài liệu annotator (Member B) không được công bố trước tỷ lệ nhãn."""
        import re
        import zipfile
        root = Path(__file__).resolve().parents[1]

        # 1. calibration_clean_a_manifest.json không chứa tỷ lệ nhãn
        manifest_path = root / "configs/calibration_clean_a_manifest.json"
        manifest_text = manifest_path.read_text(encoding="utf-8")
        assert not re.search(r"(?:main|reserve)_(?:phish|benign)_count", manifest_text), "Manifest không được chứa trường đếm nhãn nguồn"
        assert not re.search(r"\b12\s*(?:phish|benign)", manifest_text, re.IGNORECASE), "Manifest không được chứa 12 phish/benign"
        assert not re.search(r"\b4\s*(?:phish|benign)", manifest_text, re.IGNORECASE), "Manifest không được chứa 4 phish/benign"

        # 2. clean_calibration_selection_inspection_report.json không chứa nhãn phân loại hay tỷ lệ
        report_path = root / "data/source_audit/clean_calibration_selection_inspection_report.json"
        report_text = report_path.read_text(encoding="utf-8")
        assert not re.search(r"\bphish\b", report_text, re.IGNORECASE), "Báo cáo công khai không được chứa nhãn phish"
        assert not re.search(r"\bbenign\b", report_text, re.IGNORECASE), "Báo cáo công khai không được chứa nhãn benign"
        assert not re.search(r"\b12/12\b", report_text), "Báo cáo công khai không được chứa 12/12"
        assert not re.search(r"\b4/4\b", report_text), "Báo cáo công khai không được chứa 4/4"

        # 3. verify_member_b_qa.py không chứa 12/12 hoặc 4/4
        verify_tool_path = root / "scripts/data/verify_member_b_qa.py"
        verify_tool_text = verify_tool_path.read_text(encoding="utf-8")
        assert "12/12" not in verify_tool_text, "verify_member_b_qa.py không được in hoặc chứa tỷ lệ 12/12"
        assert "4/4" not in verify_tool_text, "verify_member_b_qa.py không được in hoặc chứa tỷ lệ 4/4"

        # 4. Toàn bộ tệp trong GOI_QA_MEMBER_B_CALIBRATION_CLEAN_32.zip không chứa tỷ lệ nhãn
        zip_b_path = root / "GOI_QA_MEMBER_B_CALIBRATION_CLEAN_32.zip"
        if zip_b_path.exists():
            with zipfile.ZipFile(zip_b_path, "r") as z_b:
                for fname in z_b.namelist():
                    if fname.endswith(".json"):
                        content = z_b.read(fname).decode("utf-8")
                        assert not re.search(r"(?:main|reserve)_(?:phish|benign)_count", content), f"Tệp {fname} trong gói B chứa trường đếm nhãn"
                        assert not re.search(r"\b12\s*(?:phish|benign)", content, re.IGNORECASE), f"Tệp {fname} trong gói B chứa 12 phish/benign"
                        assert not re.search(r"\b12/12\b", content), f"Tệp {fname} trong gói B chứa 12/12"

        # 5. Hồ sơ hạn chế data/restricted/ (chỉ D xem) lưu giữ đầy đủ cân bằng lớp để D tự nghiệm thu
        restricted_file = root / "data/restricted/clean_calibration_candidates_v2_restricted.json"
        if restricted_file.exists():
            restr_data = json.loads(restricted_file.read_text(encoding="utf-8"))
            assert "source_class_balance" in restr_data, "Hồ sơ hạn chế của D phải lưu trữ source_class_balance"
            balance = restr_data["source_class_balance"]
            assert balance["main_strata"]["phish"] == 12
            assert balance["main_strata"]["benign"] == 12
            assert balance["reserve_strata"]["phish"] == 4
            assert balance["reserve_strata"]["benign"] == 4

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

