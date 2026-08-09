import pytest

from src.core.certify_surprise_debruijn import certify_surprise_debruijn_s6
from src.core.surprise_debruijn import (
    cyclic_window_count_signature,
    cyclic_windows,
    debruijn_baseline_signature,
    debruijn_hidden_checklist,
    debruijn_hidden_summary,
    debruijn_trail_adjacencies,
    debruijn_trail_hidden_row,
)


def test_debruijn_row_is_window_blind_but_trail_visible():
    row = debruijn_trail_hidden_row()
    assert row.row_id == "S6-DEBRUIJN-001"
    assert row.structured_word == "00010111"
    assert row.control_word == "00011101"
    assert row.baseline_equal is True
    assert row.common_transitions == 4
    assert row.divergent_transitions == 8
    assert row.status == "window-blind-trail-split"
    assert "not a universal" in row.boundary


def test_cyclic_window_baseline_matches_order_1_to_3():
    left = debruijn_baseline_signature("left", "00010111")
    right = debruijn_baseline_signature("right", "00011101")
    assert left.comparable_key() == right.comparable_key()
    assert cyclic_window_count_signature("00010111") == cyclic_window_count_signature("00011101")
    assert cyclic_windows("00010111", 3) == ("000", "001", "010", "101", "011", "111", "110", "100")


def test_trail_adjacency_is_the_hidden_order_observer():
    left = debruijn_trail_adjacencies("00010111")
    right = debruijn_trail_adjacencies("00011101")
    assert left != right
    assert ("001", "010") in left
    assert ("001", "011") in right
    assert set(cyclic_windows("00010111", 4)) != set(cyclic_windows("00011101", 4))


def test_debruijn_summary_checklist_and_certificate_are_stable():
    assert debruijn_hidden_summary() == {
        "rows": 1,
        "baseline_equal": 1,
        "hidden_splits": 1,
        "common_transitions": 4,
        "divergent_transitions": 8,
        "overclaims": 0,
    }
    assert "trail adjacency" in "\n".join(debruijn_hidden_checklist())
    cert = certify_surprise_debruijn_s6()
    assert cert.passed is True
    assert "de Bruijn" in cert.method


def test_debruijn_helpers_reject_bad_inputs():
    with pytest.raises(ValueError):
        cyclic_windows("", 1)
    with pytest.raises(ValueError):
        cyclic_windows("0102", 2)
    with pytest.raises(ValueError):
        cyclic_window_count_signature("0101", max_window=4)
