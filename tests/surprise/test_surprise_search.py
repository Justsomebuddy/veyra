import pytest

from src.core.certify_surprise_search import certify_surprise_search_s3
from src.core.surprise_search import (
    expanded_baseline_search_row,
    hidden_correlation_rows,
    pairwise_baseline_signature,
    surprise_search_checklist,
    surprise_search_summary,
    xor_hidden_correlation_row,
)


def test_expanded_baseline_search_row_records_negative_bounded_result():
    row = expanded_baseline_search_row()
    assert row.search_id == "S3-SEARCH-001"
    assert row.min_len == 4
    assert row.max_len == 8
    assert row.scanned_words == 496
    assert row.signature_groups == 464
    assert row.colliding_signature_groups == 32
    assert row.split_signature_groups == 0
    assert row.robust_pairs == 0
    assert row.status == "no-expanded-blind-surprise-split"
    assert "not impossibility" in row.boundary


def test_surprise_search_summary_and_checklist_are_certifiable():
    assert surprise_search_summary() == {
        "search_rows": 1,
        "scanned_words": 496,
        "signature_groups": 464,
        "colliding_signature_groups": 32,
        "split_signature_groups": 0,
        "robust_pairs": 0,
        "hidden_correlation_rows": 1,
        "pairwise_blind_hidden_splits": 1,
        "overclaims": 0,
    }
    text = "\n".join(surprise_search_checklist())
    assert "finite corpus" in text
    assert "baseline" in text
    assert "hidden-correlation" in text
    assert "bounded" in text


def test_surprise_search_certificate_passes():
    cert = certify_surprise_search_s3()
    assert cert.name == "surprise_search_s3"
    assert cert.passed is True
    assert "expanded-baseline" in cert.method


def test_expanded_baseline_search_rejects_non_binary_alphabet():
    with pytest.raises(ValueError):
        expanded_baseline_search_row(alphabet=("a", "b", "c"))


def test_xor_hidden_correlation_is_pairwise_blind_but_parity_visible():
    row = xor_hidden_correlation_row()
    assert row.correlation_id == "S4-XOR-001"
    assert row.baseline_equal is True
    assert row.structured_parity_counts == (("even", 8), ("odd", 0))
    assert row.control_parity_counts == (("even", 4), ("odd", 4))
    assert row.structured_gap == 8
    assert row.control_gap == 0
    assert row.hidden_observer == "triple parity observer"
    assert row.status == "pairwise-blind-hidden-correlation"
    assert "not a universal" in row.boundary


def test_pairwise_baseline_signature_matches_xor_and_full_cube_control():
    row = hidden_correlation_rows()[0]
    left = pairwise_baseline_signature("left", row.structured_table)
    right = pairwise_baseline_signature("right", row.control_table)
    assert left.comparable_key() == right.comparable_key()
    assert left.row_count == 8
    assert left.marginals == ((0, 4, 4), (1, 4, 4), (2, 4, 4))
    assert left.pairwise_counts[0][1] == (("00", 2), ("01", 2), ("10", 2), ("11", 2))
