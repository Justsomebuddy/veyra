from src.core.surprise_separation import (
    BASELINE_FAMILIES,
    EXPANDED_BASELINE_FAMILIES,
    canonical_surprise_separation_row,
    classical_baseline_signature,
    expanded_baseline_audit_rows,
    expanded_classical_signature,
    surprise_separation_checklist,
    surprise_separation_rows,
    surprise_separation_summary,
)


def test_classical_baseline_signature_matches_canonical_pair():
    left = classical_baseline_signature("aabaabb")
    right = classical_baseline_signature("abbaaab")
    assert left.comparable_key() == right.comparable_key()
    assert left.symbol_counts == (("a", 4), ("b", 3))
    assert left.lag_agreements == (3, 1)
    assert left.lz_phrase_count == 5


def test_canonical_surprise_separation_row_is_finite_and_no_overclaim():
    row = canonical_surprise_separation_row()
    assert row.separation_id == "S1-OGS-001"
    assert row.baseline_family == BASELINE_FAMILIES
    assert row.baseline_equal is True
    assert row.structured_gap == 3.0
    assert row.control_gap == 0.0
    assert row.witness_part == "aab"
    assert row.status == "separated"
    assert "no universal" in row.boundary


def test_expanded_signature_catches_toy_pair_with_stronger_observers():
    left = expanded_classical_signature("aabaabb")
    right = expanded_classical_signature("abbaaab")
    assert left.comparable_key() != right.comparable_key()
    assert left.block_counts[1] == right.block_counts[1]
    assert left.block_counts[2] != right.block_counts[2]
    assert left.lag_agreements != right.lag_agreements
    assert left.cyclic_autocorr != right.cyclic_autocorr
    assert left.compression_counts == (("lz78", 5), ("runs", 4))


def test_expanded_baseline_audit_records_classical_counterpressure():
    rows = expanded_baseline_audit_rows()
    assert len(rows) == 1
    row = rows[0]
    assert row.audit_id == "S2-AUDIT-001"
    assert row.status == "caught"
    assert row.expanded_equal is False
    assert row.catching_observers == (
        "block-frequency entropy-rate proxy",
        "higher-lag autocorrelation",
        "cyclic spectral proxy",
    )
    assert "counterexample pressure" in row.boundary


def test_surprise_separation_rows_and_summary_are_certifiable():
    assert len(surprise_separation_rows()) == 1
    assert len(EXPANDED_BASELINE_FAMILIES) == 7
    assert surprise_separation_summary() == {
        "rows": 1,
        "baseline_blind": 1,
        "separated": 1,
        "baseline_families": 3,
        "expanded_families": 7,
        "audit_rows": 1,
        "caught_by_expanded": 1,
        "overclaims": 0,
    }


def test_surprise_separation_checklist_names_limits_and_counterpressure():
    text = "\n".join(surprise_separation_checklist())
    assert "baseline" in text
    assert "counterexamples" in text
    assert "no universal" in text
