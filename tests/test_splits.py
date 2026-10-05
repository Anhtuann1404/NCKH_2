"""Unit tests kiểm định module grouping, grouped 5-fold CV và temporal split chống rò rỉ dữ liệu."""

from datetime import date, timedelta
import json
from pathlib import Path
import subprocess
import sys
import pytest

from phishing.data.grouping import (
    PSL_SNAPSHOT_SHA256,
    TLDEXTRACT_VERSION,
    extract_group_id,
)
from phishing.data.splits import (
    DEFAULT_SEEDS,
    _validate_and_extract_record,
    assert_no_group_leakage,
    assert_strict_temporal_order,
    generate_grouped_kfold,
    generate_temporal_split,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class TestGrouping:
    """Kiểm tra trích xuất group_id (eTLD+1 & tenant hạ tầng dùng chung)."""

    def test_standard_domains_and_cctlds(self) -> None:
        assert extract_group_id("https://sub.example.com/path") == "domain:example.com"
        assert extract_group_id("https://login.portal.ox.ac.uk/auth") == "domain:ox.ac.uk"
        assert extract_group_id("https://ebank.vcb.com.vn/login") == "domain:vcb.com.vn"
        assert extract_group_id("https://chuyen-tien.techcombank.com.vn/") == "domain:techcombank.com.vn"
        assert extract_group_id("example.org/test") == "domain:example.org"

    def test_ip_addresses(self) -> None:
        assert extract_group_id("http://192.168.1.1:8080/index.php") == "ip:192.168.1.1"
        assert extract_group_id("https://10.0.0.5/") == "ip:10.0.0.5"
        assert extract_group_id("http://[2001:db8::1]:8080/path") == "ip:2001:db8::1"

    def test_sharepoint_tenants(self) -> None:
        assert (
            extract_group_id("https://victimcorp.sharepoint.com/sites/login")
            == "tenant:victimcorp.sharepoint.com"
        )
        assert (
            extract_group_id("https://sec-bank.sharepoint.com/:u:/r/teams/...")
            == "tenant:sec-bank.sharepoint.com"
        )
        assert extract_group_id("https://sharepoint.com/") == "domain:sharepoint.com"

    def test_google_sites(self) -> None:
        assert (
            extract_group_id("https://sites.google.com/view/my-phish-portal/home")
            == "tenant:sites.google.com/view/my-phish-portal"
        )
        assert (
            extract_group_id("https://sites.google.com/site/legacy-site/login")
            == "tenant:sites.google.com/site/legacy-site"
        )
        assert extract_group_id("https://sites.google.com/") == "domain:sites.google.com"

    def test_office_forms(self) -> None:
        assert (
            extract_group_id("https://forms.office.com/Pages/ResponsePage.aspx?id=SecretToken123")
            == "tenant:forms.office.com:id=secrettoken123"
        )
        assert (
            extract_group_id("https://forms.microsoft.com/Pages/ResponsePage.aspx?id=AnotherToken")
            == "tenant:forms.microsoft.com:id=anothertoken"
        )
        assert extract_group_id("https://forms.office.com/r/AbCd12") == "tenant:forms.office.com:r=abcd12"
        assert extract_group_id("https://forms.office.com/") == "domain:forms.office.com"

    def test_s3_bucket_normalization_path_and_virtual_hosted(self) -> None:
        # Cùng một bucket my-bucket qua path-style và virtual-hosted style phải trả về cùng khóa nhóm
        url_path = "https://s3.us-west-2.amazonaws.com/my-bucket/login.html"
        url_vhost = "https://my-bucket.s3.us-west-2.amazonaws.com/login.html"
        assert extract_group_id(url_path) == "tenant:s3:my-bucket"
        assert extract_group_id(url_vhost) == "tenant:s3:my-bucket"
        assert extract_group_id(url_path) == extract_group_id(url_vhost)

        # Các biến thể regional, dualstack, global, website
        assert extract_group_id("https://s3.amazonaws.com/my-bucket/") == "tenant:s3:my-bucket"
        assert extract_group_id("https://my-bucket.s3.amazonaws.com/") == "tenant:s3:my-bucket"
        assert extract_group_id("https://s3.dualstack.us-east-1.amazonaws.com/my-bucket/") == "tenant:s3:my-bucket"
        assert extract_group_id("https://my-bucket.s3.dualstack.us-east-1.amazonaws.com/") == "tenant:s3:my-bucket"
        assert extract_group_id("http://my-bucket.s3-website-us-east-1.amazonaws.com/") == "tenant:s3:my-bucket"
        assert extract_group_id("https://my.dot.bucket.s3.us-west-2.amazonaws.com/p") == "tenant:s3:my.dot.bucket"
        assert extract_group_id("https://s3.us-west-2.amazonaws.com/my.dot.bucket/p") == "tenant:s3:my.dot.bucket"

        # Alias chưa xác minh: xử lý bảo thủ bằng eTLD+1
        assert extract_group_id("https://s3.custom-alias.org/bucket/") == "domain:custom-alias.org"

    def test_cloud_storage_and_app_hosting(self) -> None:
        # Azure Blob (PSL private suffix)
        assert (
            extract_group_id("https://myaccount.blob.core.windows.net/container/login.html")
            == "domain:myaccount.blob.core.windows.net"
        )
        # Firebase / Web.app (PSL private suffix)
        assert extract_group_id("https://my-project.web.app/login") == "domain:my-project.web.app"
        assert extract_group_id("https://my-project.firebaseapp.com/") == "domain:my-project.firebaseapp.com"
        # GitHub Pages (PSL private suffix)
        assert extract_group_id("https://bad-user.github.io/phish/") == "domain:bad-user.github.io"
        # Vercel / Netlify / Pages.dev
        assert extract_group_id("https://login-clone.vercel.app/") == "domain:login-clone.vercel.app"
        assert extract_group_id("https://fake-bank.netlify.app/") == "domain:fake-bank.netlify.app"
        assert extract_group_id("https://my-portal.pages.dev/") == "domain:my-portal.pages.dev"

    def test_invalid_and_empty_urls(self) -> None:
        assert extract_group_id("") == "unknown"
        assert extract_group_id("   ") == "unknown"
        with pytest.raises(TypeError):
            extract_group_id(None)  # type: ignore[arg-type]


class TestGroupedKFold:
    """Kiểm tra thuật toán Grouped 5-Fold Cross Validation và Inner Validation."""

    def test_grouped_kfold_no_leakage_across_seeds(self) -> None:
        # Tạo 30 nhóm tên miền, mỗi nhóm có từ 1 đến 5 mẫu (tổng ~90 mẫu)
        records = []
        sample_id = 1
        for g_idx in range(30):
            group_domain = f"domain{g_idx}.com"
            num_samples = (g_idx % 5) + 1
            for s_idx in range(num_samples):
                records.append({
                    "sample_id": f"SMP-{sample_id:04d}",
                    "url": f"https://login.{group_domain}/page{s_idx}",
                    "class_label": "phishing" if (g_idx + s_idx) % 2 == 0 else "benign",
                })
                sample_id += 1

        splits_by_seed = generate_grouped_kfold(
            records=records,
            n_splits=5,
            seeds=DEFAULT_SEEDS,
        )

        assert set(splits_by_seed.keys()) == set(DEFAULT_SEEDS)

        all_sample_ids = {r["sample_id"] for r in records}

        for seed, fold_list in splits_by_seed.items():
            assert len(fold_list) == 5

            seen_test_samples = set()
            seen_test_groups = set()

            for fold_info in fold_list:
                train_idx = set(fold_info["train_indices"])
                test_idx = set(fold_info["test_indices"])
                train_grp = set(fold_info["train_groups"])
                test_grp = set(fold_info["test_groups"])

                # 1. Zero leakage giữa train và test
                assert_no_group_leakage(train_grp, test_grp, f"Seed {seed} Fold {fold_info['fold']}")
                assert train_idx.isdisjoint(test_idx)

                # 2. Hợp train và test bằng toàn bộ mẫu
                assert train_idx.union(test_idx) == all_sample_ids

                # 3. Test folds không bị trùng lặp mẫu/nhóm qua 5 folds
                assert test_idx.isdisjoint(seen_test_samples)
                assert test_grp.isdisjoint(seen_test_groups)
                seen_test_samples.update(test_idx)
                seen_test_groups.update(test_grp)

                # 4. Kiểm tra inner validation split
                inner_train_idx = set(fold_info["inner_train_indices"])
                inner_val_idx = set(fold_info["inner_val_indices"])
                inner_train_grp = set(fold_info["inner_train_groups"])
                inner_val_grp = set(fold_info["inner_val_groups"])

                assert_no_group_leakage(inner_train_grp, inner_val_grp, f"Seed {seed} Fold {fold_info['fold']} Inner")
                assert inner_train_idx.isdisjoint(inner_val_idx)
                assert inner_train_idx.union(inner_val_idx) == train_idx

    def test_grouped_kfold_deterministic_reproducibility(self) -> None:
        records = [
            {"sample_id": f"S{i}", "url": f"https://corp{i % 10}.com/path", "class_label": "phishing"}
            for i in range(50)
        ]

        run1 = generate_grouped_kfold(records, n_splits=5, seeds=(42,))
        run2 = generate_grouped_kfold(records, n_splits=5, seeds=(42,))

        assert run1[42][0]["train_indices"] == run2[42][0]["train_indices"]
        assert run1[42][0]["test_indices"] == run2[42][0]["test_indices"]
        assert run1[42][0]["train_groups"] == run2[42][0]["train_groups"]

    def test_grouped_kfold_insufficient_groups_raises_error(self) -> None:
        records = [
            {"sample_id": "S1", "url": "https://domain-1.com/1"},
            {"sample_id": "S2", "url": "https://domain-2.com/2"},
            {"sample_id": "S3", "url": "https://domain-3.com/3"},
            {"sample_id": "S4", "url": "https://domain-4.com/4"},
        ]
        with pytest.raises(ValueError, match="Cannot create 5 grouped folds"):
            generate_grouped_kfold(records, n_splits=5)

    def test_duplicate_sample_id_rejected(self) -> None:
        records = [
            {"sample_id": "DUP-001", "url": "https://domain-a.com/page"},
            {"sample_id": "DUP-001", "url": "https://domain-b.com/page"},
            {"sample_id": "SMP-002", "url": "https://domain-c.com/page"},
        ]
        with pytest.raises(ValueError, match="Duplicate sample_id detected.*DUP-001"):
            generate_grouped_kfold(records, n_splits=3)

    def test_missing_id_and_url_rejected(self) -> None:
        # Thiếu sample_id
        with pytest.raises(ValueError, match="missing mandatory ID field"):
            generate_grouped_kfold([{"url": "https://a.com"}], n_splits=3)

        # sample_id rỗng
        with pytest.raises(ValueError, match="empty ID field"):
            generate_grouped_kfold([{"sample_id": "   ", "url": "https://a.com"}], n_splits=3)

        # Thiếu URL và thiếu group_id
        with pytest.raises(ValueError, match="missing valid 'group_id' and has no 'url'"):
            generate_grouped_kfold([{"sample_id": "S1"}], n_splits=3)

        # URL rỗng
        with pytest.raises(ValueError, match="missing valid 'group_id' and has no 'url'"):
            generate_grouped_kfold([{"sample_id": "S1", "url": "   "}], n_splits=3)

        # URL hỏng không thể trích xuất nhóm
        with pytest.raises(ValueError, match="invalid URL"):
            generate_grouped_kfold([{"sample_id": "S1", "url": "http://"}], n_splits=3)

    def test_pre_identified_content_duplicate_component_preserved(self) -> None:
        # Một component trùng nội dung nối 5 tên miền khác nhau
        records = [
            {"sample_id": f"SMP-{i}", "url": f"https://domain-{i}.com/login", "group_id": "component_shared_login"}
            for i in range(5)
        ] + [
            {"sample_id": f"OTHER-{i}", "url": f"https://other-{i}.com/page"}
            for i in range(10)
        ]

        splits = generate_grouped_kfold(records, n_splits=3, seeds=(42,))
        for fold in splits[42]:
            train_ids = set(fold["train_indices"])
            test_ids = set(fold["test_indices"])
            comp_ids = {f"SMP-{i}" for i in range(5)}

            # Toàn bộ component phải ở cùng 1 phía: hoặc tất cả trong train, hoặc tất cả trong test!
            assert comp_ids.issubset(train_ids) or comp_ids.issubset(test_ids)
            assert not (comp_ids.intersection(train_ids) and comp_ids.intersection(test_ids))

    def test_n_splits_minimum_3_enforced(self) -> None:
        records = [
            {"sample_id": f"S{i}", "url": f"https://domain{i}.com/"}
            for i in range(10)
        ]
        with pytest.raises(ValueError, match="n_splits must be at least 3"):
            generate_grouped_kfold(records, n_splits=2)


class TestTemporalSplit:
    """Kiểm tra phân chia mốc thời gian (Temporal Split) 60/20/20."""

    def test_temporal_split_order_and_same_day_atomicity(self) -> None:
        base_date = date(2025, 1, 1)
        records = []
        sample_id = 1

        # Tạo mẫu trong 20 ngày liên tiếp
        for day_offset in range(20):
            cur_date = base_date + timedelta(days=day_offset)
            # Mỗi ngày có 5 mẫu
            for sample_in_day in range(5):
                records.append({
                    "sample_id": f"SMP-{sample_id:04d}",
                    "url": f"https://day{day_offset}-site{sample_in_day}.com/",
                    "collected_at": cur_date.isoformat(),
                    "class_label": "phishing",
                })
                sample_id += 1

        res = generate_temporal_split(
            records=records,
            train_ratio=0.6,
            val_ratio=0.2,
            test_ratio=0.2,
            purge_overlapping_groups=True,
        )

        assert len(res["train_indices"]) > 0
        assert len(res["val_indices"]) > 0
        assert len(res["test_indices"]) > 0

        # Kiểm tra trật tự thời gian
        train_max = date.fromisoformat(res["train_date_range"][1])
        val_min = date.fromisoformat(res["val_date_range"][0])
        val_max = date.fromisoformat(res["val_date_range"][1])
        test_min = date.fromisoformat(res["test_date_range"][0])

        assert train_max < val_min
        assert val_max < test_min

    def test_temporal_split_purges_past_overlapping_groups(self) -> None:
        # Nhóm 'leaking-domain.com' xuất hiện ở Train, Val và Test
        records = [
            {"sample_id": "T1", "url": "https://leaking-domain.com/login", "collected_at": "2025-01-01"},
            {"sample_id": "T2", "url": "https://other-domain-1.com/", "collected_at": "2025-01-02"},
            {"sample_id": "T3", "url": "https://other-domain-2.com/", "collected_at": "2025-01-03"},
            {"sample_id": "V1", "url": "https://leaking-domain.com/step2", "collected_at": "2025-01-10"},
            {"sample_id": "V2", "url": "https://val-domain-clean.com/", "collected_at": "2025-01-11"},
            {"sample_id": "E1", "url": "https://leaking-domain.com/step3", "collected_at": "2025-01-20"},
            {"sample_id": "E2", "url": "https://test-domain-clean.com/", "collected_at": "2025-01-21"},
        ]

        res = generate_temporal_split(
            records=records,
            train_ratio=0.45,
            val_ratio=0.25,
            test_ratio=0.30,
            purge_overlapping_groups=True,
        )

        # V1 và E1 phải bị loại trừ khỏi tập đánh giá sạch do trùng nhóm từ quá khứ
        assert "T1" in res["train_indices"]
        assert "V1" in res["purged_val_indices"]
        assert "V1" not in res["val_indices"]
        assert "E1" in res["purged_test_indices"]
        assert "E1" not in res["test_indices"]

        # V2 và E2 là domain sạch nên được giữ lại
        assert "V2" in res["val_indices"]
        assert "E2" in res["test_indices"]

    def test_temporal_split_ratio_validation(self) -> None:
        records = [
            {"sample_id": f"S{i}", "url": f"https://domain{i}.com/", "collected_at": f"2025-01-{i+1:02d}"}
            for i in range(10)
        ]
        # test_ratio âm
        with pytest.raises(ValueError, match="test_ratio must be a finite positive number"):
            generate_temporal_split(records, train_ratio=0.6, val_ratio=0.2, test_ratio=-99)

        # Tổng khác 1.0
        with pytest.raises(ValueError, match="must sum to 1.0"):
            generate_temporal_split(records, train_ratio=0.6, val_ratio=0.2, test_ratio=0.5)

    def test_temporal_split_not_evaluable_status_on_empty_clean_set(self) -> None:
        # Toàn bộ domain ở test đều trùng với train
        records = [
            {"sample_id": "T1", "url": "https://leak1.com/", "collected_at": "2025-01-01"},
            {"sample_id": "T2", "url": "https://leak2.com/", "collected_at": "2025-01-02"},
            {"sample_id": "V1", "url": "https://val-domain.com/", "collected_at": "2025-01-10"},
            {"sample_id": "E1", "url": "https://leak1.com/", "collected_at": "2025-01-20"},
            {"sample_id": "E2", "url": "https://leak2.com/", "collected_at": "2025-01-21"},
        ]
        res = generate_temporal_split(
            records=records,
            train_ratio=0.4,
            val_ratio=0.2,
            test_ratio=0.4,
            purge_overlapping_groups=True,
        )
        assert len(res["test_indices"]) == 0
        assert res["status"] == "not_evaluable"
        assert res["evaluability"]["test"]["status"] == "not_evaluable"

    def test_temporal_split_insufficient_dates_raises_error(self) -> None:
        records = [
            {"sample_id": "S1", "url": "https://a.com/", "collected_at": "2025-01-01"},
            {"sample_id": "S2", "url": "https://b.com/", "collected_at": "2025-01-01"},
        ]
        with pytest.raises(ValueError, match="Need at least 3 distinct calendar dates"):
            generate_temporal_split(records)


class TestAntiLeakageAssertions:
    """Kiểm tra các hàm assertion phòng vệ chống rò rỉ dữ liệu."""

    def test_assert_no_group_leakage_detects_leak(self) -> None:
        train_groups = ["domain:abc.com", "domain:xyz.com"]
        test_groups = ["domain:foo.com", "domain:abc.com"]

        with pytest.raises(ValueError, match="DATA LEAKAGE DETECTED.*domain:abc.com"):
            assert_no_group_leakage(train_groups, test_groups)

    def test_assert_strict_temporal_order_detects_violation(self) -> None:
        train_dates = [date(2025, 1, 1), date(2025, 1, 5)]
        val_dates = [date(2025, 1, 5), date(2025, 1, 10)]  # trùng ngày 2025-01-05!
        test_dates = [date(2025, 1, 15)]

        with pytest.raises(ValueError, match="Temporal order violated between Train and Val"):
            assert_strict_temporal_order(train_dates, val_dates, test_dates)


class TestLeadDProbesRegression:
    """Kiểm tra hồi quy 6 điểm phản biện và probe của Lead D."""

    def test_probe1_cli_preserves_artifacts_on_failure(self, tmp_path: Path) -> None:
        """Probe 1: Khi input không tồn tại hoặc lỗi, artifacts của run trước phải giữ nguyên 100%."""
        out_dir = tmp_path / "splits_run"
        out_dir.mkdir(parents=True, exist_ok=True)

        old_files = {
            "groups.json": '{"old": "groups_content"}',
            "grouped_5fold_splits.json": '{"old": "splits_content"}',
            "temporal_splits.json": '{"old": "temporal_content"}',
            "manifest.json": '{"old": "manifest_content"}',
        }
        for fname, content in old_files.items():
            (out_dir / fname).write_text(content, encoding="utf-8")

        script = PROJECT_ROOT / "scripts" / "data" / "generate_splits.py"
        cmd = [
            sys.executable,
            str(script),
            "--input",
            str(tmp_path / "non_existent_file.jsonl"),
            "--output-dir",
            str(out_dir),
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", cwd=PROJECT_ROOT)
        assert proc.returncode != 0

        # Cả 4 artifacts cũ phải còn nguyên vẹn, không bị xóa trước khi validate
        for fname, expected_content in old_files.items():
            fpath = out_dir / fname
            assert fpath.is_file(), f"Artifact '{fname}' bị xóa khi CLI gặp lỗi!"
            assert fpath.read_text(encoding="utf-8") == expected_content, f"Artifact '{fname}' bị sửa đổi nội dung!"

    def test_probe1_cli_rejects_overwrite_without_flag(self, tmp_path: Path) -> None:
        """Probe 1: Thư mục đã có artifacts cũ phải từ chối nếu không truyền cờ --overwrite."""
        out_dir = tmp_path / "splits_run"
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "groups.json").write_text("{}", encoding="utf-8")

        in_file = tmp_path / "sample.jsonl"
        recs = [
            {"sample_id": f"S{i}", "url": f"https://domain{i}.com/", "class_label": "phishing" if i % 2 == 0 else "benign", "collected_at": f"2025-01-{i+1:02d}"}
            for i in range(15)
        ]
        in_file.write_text("\n".join(json.dumps(r) for r in recs) + "\n", encoding="utf-8")

        script = PROJECT_ROOT / "scripts" / "data" / "generate_splits.py"
        proc = subprocess.run(
            [sys.executable, str(script), "--input", str(in_file), "--output-dir", str(out_dir)],
            capture_output=True, text=True, encoding="utf-8", cwd=PROJECT_ROOT,
        )
        assert proc.returncode != 0
        assert "--overwrite" in proc.stderr

    def test_probe4_class_sufficiency_insufficient_when_missing_class(self) -> None:
        """Probe 4: Kiểm tra đầy đủ 4 phân vùng; tập chỉ có benign phải báo is_usable=False."""
        records = [
            {"sample_id": f"S{i}", "url": f"https://domain{i}.com/", "class_label": "benign"}
            for i in range(20)
        ]
        res = generate_grouped_kfold(records, n_splits=5, seeds=[42])
        folds = res[42]
        for fold in folds:
            assert fold["is_usable"] is False
            assert "Corpus lacks binary classes" in fold["unusable_reason"]
            assert fold["class_sufficiency"]["status"] == "insufficient_classes"
            assert "phishing" in fold["class_sufficiency"]["missing_in_outer_train"]

    def test_probe4_temporal_split_class_distribution(self) -> None:
        """Probe 4: Temporal split phải kiểm tra phân bố nhãn trên train/val/test."""
        records = [
            {"sample_id": f"S{i}", "url": f"https://domain{i}.com/", "class_label": "benign", "collected_at": f"2025-01-{i+1:02d}"}
            for i in range(10)
        ]
        res = generate_temporal_split(records)
        assert res["status"] == "not_evaluable"
        assert res["evaluability"]["train"]["status"] == "not_evaluable"
        assert res["evaluability"]["validation"]["status"] == "not_evaluable"
        assert res["evaluability"]["test"]["status"] == "not_evaluable"
        assert "Corpus lacks binary classes" in res["evaluability"]["train"]["reason"]

    def test_probe5_invalid_url_and_group_handling(self) -> None:
        """Probe 5: extract_group_id trả về 'unknown' khi URL sai RFC/khoảng trắng; splitter chặn ID/group lỗi."""
        # 1. URL không hợp lệ trả về unknown
        assert extract_group_id("not a valid URL") == "unknown"
        assert extract_group_id("http://invalid host with spaces.com/") == "unknown"
        assert extract_group_id("   ") == "unknown"
        assert extract_group_id("http://") == "unknown"

        # 2. _validate_and_extract_record chặn ID sai kiểu
        with pytest.raises((ValueError, TypeError), match="sample_id"):
            _validate_and_extract_record(0, {"sample_id": 123, "url": "https://example.com/"}, "sample_id", "url", "group_id", "class_label", set())
        with pytest.raises((ValueError, TypeError), match="sample_id"):
            _validate_and_extract_record(0, {"sample_id": True, "url": "https://example.com/"}, "sample_id", "url", "group_id", "class_label", set())
        with pytest.raises(ValueError, match="sample_id"):
            _validate_and_extract_record(0, {"sample_id": "", "url": "https://example.com/"}, "sample_id", "url", "group_id", "class_label", set())
        with pytest.raises((ValueError, TypeError), match="url"):
            _validate_and_extract_record(0, {"sample_id": "S1", "url": None}, "sample_id", "url", "group_id", "class_label", set())

        # 3. _validate_and_extract_record chặn group_id là "unknown" hoặc chứa khoảng trắng
        with pytest.raises(ValueError, match="unknown"):
            _validate_and_extract_record(0, {"sample_id": "S1", "url": "https://example.com/", "group_id": "unknown"}, "sample_id", "url", "group_id", "class_label", set())
        with pytest.raises(ValueError, match="has invalid 'group_id'"):
            _validate_and_extract_record(0, {"sample_id": "S1", "url": "https://example.com/", "group_id": "host:has space"}, "sample_id", "url", "group_id", "class_label", set())

    def test_probe6_empty_seeds_and_provenance_manifest(self, tmp_path: Path) -> None:
        """Probe 6: chặn seeds rỗng/trùng; manifest ghi đầy đủ PSL snapshot hash, tham số CLI và code hash."""
        records = [
            {"sample_id": f"S{i}", "url": f"https://domain{i}.com/", "class_label": "phishing" if i % 2 == 0 else "benign", "collected_at": f"2025-01-{i+1:02d}"}
            for i in range(20)
        ]
        # Seeds rỗng
        with pytest.raises(ValueError, match="seeds list cannot be empty"):
            generate_grouped_kfold(records, seeds=[])
        # Seeds trùng lặp
        with pytest.raises(ValueError, match="Duplicate seeds detected"):
            generate_grouped_kfold(records, seeds=[42, 42])
        # n_splits < 3
        with pytest.raises(ValueError, match="n_splits must be at least 3"):
            generate_grouped_kfold(records, n_splits=2)

        # Chạy generate_splits.py kiểm tra manifest provenance
        in_file = tmp_path / "valid_corpus.jsonl"
        in_file.write_text("\n".join(json.dumps(r) for r in records) + "\n", encoding="utf-8")
        out_dir = tmp_path / "splits_output"

        script = PROJECT_ROOT / "scripts" / "data" / "generate_splits.py"
        proc = subprocess.run(
            [
                sys.executable, str(script),
                "--input", str(in_file),
                "--output-dir", str(out_dir),
                "--seeds", "42,100",
                "-k", "5",
            ],
            capture_output=True, text=True, encoding="utf-8", cwd=PROJECT_ROOT,
        )
        assert proc.returncode == 0, f"Lỗi CLI: {proc.stderr}"

        manifest_data = json.loads((out_dir / "manifest.json").read_text(encoding="utf-8"))
        # Provenance: PSL Snapshot SHA-256
        assert manifest_data["grouping_metadata"]["psl_snapshot_sha256"] == PSL_SNAPSHOT_SHA256
        assert manifest_data["grouping_metadata"]["tldextract_version"] == TLDEXTRACT_VERSION
        # CLI Parameters
        assert manifest_data["run_parameters"]["seeds"] == [42, 100]
        assert manifest_data["run_parameters"]["n_splits"] == 5
        # Code hashes
        assert "code_sha256" in manifest_data
        assert "generate_splits.py" in manifest_data["code_hashes"]
        assert "splits.py" in manifest_data["code_hashes"]
        assert "grouping.py" in manifest_data["code_hashes"]
        assert "date_parser.py" in manifest_data["code_hashes"]

    def test_malware_defacement_labels_fail_binary_class_sufficiency(self) -> None:
        """Lead D probe 5: Tập chỉ chứa malware/defacement không được báo sufficient cho bài toán nhị phân."""
        records = [
            {"sample_id": f"S{i}", "url": f"https://domain{i}.com/", "class_label": "malware" if i % 2 == 0 else "defacement"}
            for i in range(20)
        ]
        res = generate_grouped_kfold(records, n_splits=5, seeds=[42])
        folds = res[42]
        for fold in folds:
            assert fold["is_usable"] is False
            assert fold["class_sufficiency"]["status"] == "insufficient_classes"
            assert "phishing" in fold["class_sufficiency"]["missing_in_outer_train"]
            assert "benign" in fold["class_sufficiency"]["missing_in_outer_train"]

    def test_invalid_url_ports_rejected(self) -> None:
        """Lead D probe 5: URL có port abc hoặc 99999 hoặc 0 phải bị từ chối."""
        from phishing.preprocessing.urls import normalize_url

        # 1. normalize_url
        with pytest.raises(ValueError):
            normalize_url("http://example.com:abc/login")
        with pytest.raises(ValueError):
            normalize_url("http://example.com:99999/login")
        with pytest.raises(ValueError):
            normalize_url("http://example.com:0/login")

        # 2. extract_group_id
        assert extract_group_id("http://example.com:abc/login") == "unknown"
        assert extract_group_id("http://example.com:99999/login") == "unknown"
        assert extract_group_id("http://example.com:0/login") == "unknown"

        # 3. generate_grouped_kfold rejects invalid ports
        invalid_records = [
            {"sample_id": "S1", "url": "http://example.com:99999/login", "class_label": "phishing"}
        ]
        with pytest.raises(ValueError, match="invalid URL"):
            generate_grouped_kfold(invalid_records, n_splits=5, seeds=[42])

    def test_atomic_staging_and_skip_temporal_cleans_stale_artifact(self, tmp_path: Path) -> None:
        """Lead D probe 3: --skip-temporal phải dọn dẹp temporal artifact cũ của run trước."""
        records = [
            {"sample_id": f"S{i}", "url": f"https://domain{i}.com/", "class_label": "phishing" if i % 2 == 0 else "benign", "collected_at": f"2025-01-{i+1:02d}"}
            for i in range(20)
        ]
        in_file = tmp_path / "corpus.jsonl"
        in_file.write_text("\n".join(json.dumps(r) for r in records) + "\n", encoding="utf-8")
        out_dir = tmp_path / "splits_run"

        script = PROJECT_ROOT / "scripts" / "data" / "generate_splits.py"

        # Run 1: có temporal splits
        proc1 = subprocess.run(
            [sys.executable, str(script), "--input", str(in_file), "--output-dir", str(out_dir), "-k", "3", "--seeds", "42"],
            capture_output=True, text=True, encoding="utf-8", cwd=PROJECT_ROOT,
        )
        assert proc1.returncode == 0
        assert (out_dir / "temporal_splits.json").exists()

        # Run 2: với --skip-temporal --overwrite -> temporal_splits.json cũ phải bị dọn dẹp triệt để
        proc2 = subprocess.run(
            [sys.executable, str(script), "--input", str(in_file), "--output-dir", str(out_dir), "-k", "3", "--seeds", "42", "--skip-temporal", "--overwrite"],
            capture_output=True, text=True, encoding="utf-8", cwd=PROJECT_ROOT,
        )
        assert proc2.returncode == 0
        assert not (out_dir / "temporal_splits.json").exists(), "temporal_splits.json cũ không được tồn tại khi --skip-temporal!"

    def test_psl_extractor_no_cache_leakage(self) -> None:
        """Lead D probe 4: Extractor tldextract phải tắt cache (cache_dir=None) và đọc đúng snapshot."""
        from phishing.data.grouping import _EXTRACTOR, _load_psl_snapshot_and_sha256
        assert _EXTRACTOR._cache.enabled is False
        psl_bytes, psl_sha = _load_psl_snapshot_and_sha256()
        assert len(psl_bytes) > 0
        assert len(psl_sha) == 64

