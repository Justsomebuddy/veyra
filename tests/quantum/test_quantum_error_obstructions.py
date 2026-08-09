from src.core.quantum_error_obstructions import (
    branch_distinguishability_row,
    interference_loss_row,
    leakage_row,
    nonunitarity_row,
    phase_break_row,
    quantum_error_obstruction_rows,
    quantum_error_obstruction_summary,
    syndrome_ambiguity_row,
)


def test_q7_obstruction_rows_cover_six_named_families():
    rows = quantum_error_obstruction_rows()
    assert [row.obstruction_id for row in rows] == [
        "Q7-PHASE-BREAK",
        "Q7-INTERFERENCE-LOSS",
        "Q7-LEAKAGE",
        "Q7-NON-UNITARITY",
        "Q7-SYNDROME-AMBIGUITY",
        "Q7-BRANCH-DISTINGUISHABLE",
    ]
    assert {row.family for row in rows} == {
        "phase-break",
        "interference-loss",
        "leakage",
        "non-unitarity",
        "syndrome-ambiguity",
        "branch-distinguishability",
    }
    assert all(row.status == "ready" and "finite" in row.boundary for row in rows)


def test_q7_amplitude_debug_rows_are_specific_not_binary():
    assert phase_break_row().observed_shadow == "S≠Z"
    assert "split" in interference_loss_row().observed_shadow
    assert "leak_mass" in leakage_row().observed_shadow
    assert nonunitarity_row().observer == "norm"


def test_q7_qec_rows_reuse_observer_indexed_ambiguity():
    assert syndrome_ambiguity_row().family == "syndrome-ambiguity"
    assert branch_distinguishability_row().family == "branch-distinguishability"
    assert "non-binary" in syndrome_ambiguity_row().witness
    assert "observer-indexed" in branch_distinguishability_row().witness


def test_q7_summary_blocks_overclaim():
    assert quantum_error_obstruction_summary() == {
        "rows": 6,
        "ready": 6,
        "families": 6,
        "amplitude_rows": 4,
        "qec_rows": 2,
        "overclaims": 0,
    }
