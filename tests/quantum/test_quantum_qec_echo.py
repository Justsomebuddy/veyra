from src.core.quantum_qec_echo import (
    branch_shadow,
    qec_ambiguity_rows,
    qec_branch,
    qec_branch_rows,
    qec_echo,
    qec_observer_family_rows,
    qec_split_echo_rows,
    quantum_qec_echo_summary,
)


def test_qec_branch_rows_cover_logicals_and_error_weights():
    rows = qec_branch_rows()
    assert len(rows) == 14
    assert {row.logical for row in rows} == {0, 1}
    assert {row.weight for row in rows} == {0, 1, 2}
    assert sum(row.correctable for row in rows) == 8


def test_qec_observer_shadows_are_named_and_deterministic():
    row = qec_branch(0, "X1")
    assert branch_shadow(row, "syndrome") == (-1, -1)
    assert branch_shadow(row, "correction") == "X1"
    assert branch_shadow(row, "logical-after") == 0


def test_qec_echo_is_indexed_by_observer_family():
    left = qec_branch(0, "X2")
    right = qec_branch(0, "X0X1")
    assert qec_echo(left, right, ("syndrome", "correction"))
    assert not qec_echo(left, right, ("logical-after", "correctable"))


def test_qec_observer_families_make_echo_classes_first_class():
    rows = qec_observer_family_rows()
    assert [row.name for row in rows] == ["syndrome", "recovery", "logical", "diagnostic"]
    diagnostic = rows[-1]
    assert diagnostic.distinguishes_logical
    assert diagnostic.distinguishes_correctability
    assert all(row.status == "ready" for row in rows)


def test_qec_syndrome_echo_splits_under_logical_observer():
    rows = qec_split_echo_rows()
    assert len(rows) == 4
    assert all(row.syndrome_correction_echo for row in rows)
    assert all(not row.logical_echo and row.status == "ready" for row in rows)


def test_qec_ambiguity_rows_name_double_error_obstructions():
    rows = qec_ambiguity_rows()
    assert len(rows) == 6
    assert all(row.single_correctable and not row.double_correctable for row in rows)
    assert all(row.logical_distinct_after and row.status == "ready" for row in rows)


def test_quantum_qec_echo_summary_blocks_overclaim():
    assert quantum_qec_echo_summary() == {
        "branches": 14,
        "observer_families": 4,
        "single_error_corrected": 8,
        "double_error_obstructions": 6,
        "split_echo_rows": 4,
        "ambiguity_rows": 6,
        "overclaims": 0,
    }
