import pytest

from src.core.quantum_surprise import (
    BASIS_SPECS,
    BELL_PHI_PLUS,
    PRODUCT_00,
    PRODUCT_0_PLUS,
    PRODUCT_PLUS_0,
    PRODUCT_PLUS_PLUS,
    PRODUCT_STATES,
    basis_rotation,
    basis_shadow,
    blind_menu_obstruction_rows,
    correlation_gap_labels,
    marginal_distribution,
    menu_detects_gap,
    menu_shadow,
    named_two_qubit_state,
    product_of_marginals,
    quantum_surprise_baseline_rows,
    quantum_surprise_checklist,
    quantum_surprise_summary,
    surprise_witness_row,
    surprise_witness_rows,
)
from src.core.quantum_veyra import (
    bell_state,
    is_product_factorable_2q,
    observer_distribution,
    q_basis_state,
    qecho,
)


def test_limited_menus_detect_bell_correlation_without_full_tomography():
    rows = surprise_witness_rows()
    assert [row.row_id for row in rows] == [
        "QS-ZZ-BELL", "QS-XX-BELL", "QS-ZZXX-BELL",
        "QS-ZZ-PRODUCT-00", "QS-ZZ-PRODUCT-PP", "QS-XX-PRODUCT-PP",
    ]
    bell_rows = [row for row in rows if row.state_name == BELL_PHI_PLUS]
    assert len(bell_rows) == 3
    assert all(row.detects_hidden_correlation for row in bell_rows)
    assert all(row.status == "ready" for row in rows)
    assert all(len(row.menu) <= 2 for row in rows)  # strictly less access than full tomography
    zz_row, xx_row, joint_row = bell_rows
    assert zz_row.gap_specs == ("ZZ",) and zz_row.blind_specs == ()
    assert xx_row.gap_specs == ("XX",) and xx_row.blind_specs == ()
    assert joint_row.gap_specs == ("ZZ", "XX") and joint_row.blind_specs == ()


def test_witness_shadows_are_consistent_with_qecho():
    bell = bell_state()
    for spec in BASIS_SPECS:
        rotated = basis_rotation(spec).apply(bell)
        assert basis_shadow(bell, spec) == observer_distribution(rotated, "Z")
        assert qecho(rotated, rotated, "Z") is True
    # ZZ-menu gap is consistent with qecho: Bell and |00> differ under the Z observer.
    assert correlation_gap_labels(basis_shadow(bell, "ZZ")) != ()
    assert qecho(bell, q_basis_state("00"), "Z") is False
    # Product-factor baseline consistency: Bell non-factorable, every seed product factorable.
    assert is_product_factorable_2q(bell) is False
    assert all(is_product_factorable_2q(named_two_qubit_state(name)) for name in PRODUCT_STATES)


def test_product_states_are_never_flagged_by_any_menu():
    for name in PRODUCT_STATES:
        state = named_two_qubit_state(name)
        for spec in BASIS_SPECS:
            assert correlation_gap_labels(basis_shadow(state, spec)) == ()
        assert menu_detects_gap(state, BASIS_SPECS) is False
    product_rows = [row for row in surprise_witness_rows() if row.state_name != BELL_PHI_PLUS]
    assert [row.state_name for row in product_rows] == [PRODUCT_00, PRODUCT_PLUS_PLUS, PRODUCT_PLUS_PLUS]
    assert all(not row.detects_hidden_correlation for row in product_rows)
    assert all(row.gap_specs == () for row in product_rows)


def test_blind_menu_obstruction_rows_fire_on_mixed_menus():
    rows = blind_menu_obstruction_rows()
    assert [row.row_id for row in rows] == ["QS-BLIND-ZX", "QS-BLIND-XZ"]
    assert all(row.status == "ready" for row in rows)
    assert all(row.menu_echo and not row.gaps_detected for row in rows)
    bell = bell_state()
    # The ZX menu is blind: Bell and |+0> both give the uniform shadow and qecho agrees.
    assert rows[0].left_state == BELL_PHI_PLUS and rows[0].right_state == PRODUCT_PLUS_0
    assert basis_shadow(bell, "ZX") == basis_shadow(named_two_qubit_state(PRODUCT_PLUS_0), "ZX")
    assert qecho(basis_rotation("ZX").apply(bell), basis_rotation("ZX").apply(named_two_qubit_state(PRODUCT_PLUS_0)), "Z")
    # The XZ menu is blind: Bell and |0+> echo.
    assert rows[1].left_state == BELL_PHI_PLUS and rows[1].right_state == PRODUCT_0_PLUS
    assert basis_shadow(bell, "XZ") == basis_shadow(named_two_qubit_state(PRODUCT_0_PLUS), "XZ")
    # Widening a blind menu with ZZ separates Bell from products again.
    assert menu_detects_gap(bell, ("ZZ", "ZX")) is True
    assert menu_detects_gap(named_two_qubit_state(PRODUCT_PLUS_0), ("ZZ", "ZX")) is False


def test_marginal_product_reconstruction_is_exact():
    dist = basis_shadow(bell_state(), "ZZ")
    assert marginal_distribution(dist, 0) == marginal_distribution(dist, 1)
    joint, surface = dict(dist), dict(product_of_marginals(dist))
    assert tuple(joint) == tuple(surface) == ("00", "01", "10", "11")
    assert joint["00"] != surface["00"]  # 1/2 joint vs 1/4 independent coupling
    assert correlation_gap_labels(dist) == ("00", "01", "10", "11")


def test_baseline_ledger_names_product_factor_and_tomography_reference():
    rows = quantum_surprise_baseline_rows()
    assert [row.result_id for row in rows] == ["QS-BASE-PRODUCT-FACTOR", "QS-BASE-TOMOGRAPHY", "QS-BASE-CLASSICAL-CORR"]
    assert {row.baseline_family for row in rows} == {"tensor-product", "full-tomography", "classical-correlation"}
    assert all(row.status == "benchmarked" and not row.stronger_claim for row in rows)
    tomography = rows[1]
    assert tomography.verdict == "baseline-stronger-reference"
    assert "stronger reference" in tomography.boundary
    assert "do not replace tomography" in tomography.boundary


def test_summary_counts_and_overclaim_guard():
    assert quantum_surprise_summary() == {
        "witness_rows": 6,
        "bell_detected": 3,
        "products_flagged": 0,
        "obstruction_rows": 2,
        "ready_obstructions": 2,
        "baseline_rows": 3,
        "stronger_claims": 0,
        "overclaims": 0,
    }
    text = "\n".join(quantum_surprise_checklist())
    assert "full-tomography stronger reference" in text
    assert "no quantum-advantage" in text


def test_builders_are_deterministic():
    assert surprise_witness_rows() == surprise_witness_rows()
    assert blind_menu_obstruction_rows() == blind_menu_obstruction_rows()
    assert quantum_surprise_baseline_rows() == quantum_surprise_baseline_rows()
    assert quantum_surprise_summary() == quantum_surprise_summary()
    canonical = surprise_witness_row("QS-ZZ-BELL", BELL_PHI_PLUS, ("ZZ",))
    assert canonical == surprise_witness_rows()[0]
    assert canonical.as_dict() == surprise_witness_rows()[0].as_dict()


def test_invalid_inputs_raise_value_error():
    with pytest.raises(ValueError):
        named_two_qubit_state("not-a-state")
    with pytest.raises(ValueError):
        basis_rotation("ZY")
    with pytest.raises(ValueError):
        basis_rotation("Z")
    with pytest.raises(ValueError):
        menu_shadow(bell_state(), ())
    with pytest.raises(ValueError):
        marginal_distribution(basis_shadow(bell_state(), "ZZ"), 2)
