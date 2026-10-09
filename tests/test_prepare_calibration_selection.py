"""Calibration proposal must stay balanced, deterministic and group-disjoint."""

import pytest

from scripts.data.prepare_calibration_selection import select, source_label


def _candidates():
    result = []
    for label in ("phish", "benign"):
        for idx in range(20):
            key = f"{label}-{idx}"
            result.append(({"relative_path": "data/train-000.parquet", "row_offset": len(result)},
                           label, {"url_sha256": key, "group_sha256": key}))
    return result


def test_seeded_selection_is_balanced_and_repeatable():
    blocked = {"url_sha256": set(), "group_sha256": set()}
    main, reserve = select(_candidates(), blocked)
    assert len(main) == 24 and len(reserve) == 8
    assert len({(x["relative_path"], x["row_offset"]) for x in main + reserve}) == 32
    assert (main, reserve) == select(_candidates(), blocked)
    assert all(set(x) == {"relative_path", "row_offset"} for x in main + reserve)


def test_selection_rejects_blocked_and_duplicate_groups():
    candidates = _candidates()
    blocked = {"url_sha256": {"phish-0"}, "group_sha256": set()}
    main, reserve = select(candidates, blocked)
    assert 0 not in [x["row_offset"] for x in main + reserve]
    for index in range(10):
        candidates[index][2]["group_sha256"] = "same-group"
    with pytest.raises(ValueError, match="Không đủ"):
        select(candidates, blocked)


def test_source_label_does_not_turn_unknown_into_benign():
    assert source_label("phishing") == "phish"
    assert source_label(0) == "benign"
    assert source_label("malware") is None
    assert source_label(None) is None


def test_difficulty_strata_integration():
    from phishing.data.difficulty_strata import DIFFICULTY_RULES
    assert len(DIFFICULTY_RULES) == 6
    assert isinstance(DIFFICULTY_RULES, tuple)

