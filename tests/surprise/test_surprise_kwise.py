import pytest

from src.core.certify_surprise_kwise import certify_surprise_kwise_s5
from src.core.surprise_kwise import (
    bit_words,
    global_parity_counts,
    kwise_baseline_signature,
    kwise_hidden_correlation_checklist,
    kwise_hidden_correlation_summary,
    kwise_parity_hidden_correlation_row,
)


def test_kwise_parity_row_is_3wise_blind_but_4wise_visible():
    row = kwise_parity_hidden_correlation_row()
    assert row.correlation_id == "S5-KWISE-001"
    assert row.width == 4
    assert row.max_blind_order == 3
    assert row.baseline_equal is True
    assert row.structured_parity_counts == (("even", 16), ("odd", 0))
    assert row.control_parity_counts == (("even", 8), ("odd", 8))
    assert row.structured_gap == 16
    assert row.control_gap == 0
    assert row.status == "3-wise-blind-hidden-correlation"
    assert "not a universal" in row.boundary


def test_kwise_baseline_signature_matches_even_parity_and_full_cube():
    row = kwise_parity_hidden_correlation_row()
    left = kwise_baseline_signature("left", row.structured_table)
    right = kwise_baseline_signature("right", row.control_table)
    assert left.comparable_key() == right.comparable_key()
    assert left.row_count == 16
    assert len(left.joint_counts) == 14
    assert left.joint_counts[-1][1] == tuple((bits, 2) for bits in bit_words(3))


def test_kwise_summary_checklist_and_certificate_are_stable():
    assert kwise_hidden_correlation_summary() == {
        "rows": 1,
        "width": 4,
        "max_blind_order": 3,
        "baseline_equal": 1,
        "hidden_splits": 1,
        "structured_gap": 16,
        "control_gap": 0,
        "overclaims": 0,
    }
    assert "global parity" in "\n".join(kwise_hidden_correlation_checklist())
    cert = certify_surprise_kwise_s5()
    assert cert.passed is True
    assert "3-wise" in cert.method


def test_kwise_helpers_reject_bad_inputs():
    with pytest.raises(ValueError):
        bit_words(0)
    with pytest.raises(ValueError):
        global_parity_counts(("01",), width=4)
    with pytest.raises(ValueError):
        kwise_baseline_signature("bad", ("0000",), max_order=4)
