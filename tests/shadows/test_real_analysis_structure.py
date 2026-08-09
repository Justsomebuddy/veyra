from src.core.ratio import ratio_from_ints, ratio_shadow
from src.core.real_analysis_structure import (
    area_refinement_certificate,
    derivative_refinement_certificate,
    finite_modulus_certificate,
    identity_rule,
    jump_obstruction_card,
    real_analysis_structure_checklist,
    square_rule,
)


def test_finite_modulus_certificate_for_square_grid():
    grid = tuple(ratio_from_ints(n, 4) for n in range(5))
    row = finite_modulus_certificate("square-grid-modulus", square_rule, grid, ratio_from_ints(1, 4), ratio_from_ints(1, 2))
    assert row.as_dict()["status"] == "stable"
    assert row.checked_pairs == 4
    assert ratio_shadow(row.max_output_drift) == ratio_shadow(ratio_from_ints(7, 16))


def test_derivative_refinement_is_stable_for_square():
    row = derivative_refinement_certificate(square_rule, ratio_from_ints(2), (ratio_from_ints(1), ratio_from_ints(1, 2), ratio_from_ints(1, 4)), ratio_from_ints(0))
    assert row.as_dict()["values"] == ("4", "4", "4")
    assert row.status == "stable"


def test_area_refinement_is_stable_for_identity_midpoints():
    row = area_refinement_certificate(identity_rule, ratio_from_ints(0), ratio_from_ints(1), (2, 4, 8), ratio_from_ints(0))
    assert row.as_dict()["values"] == ("1/2", "1/2", "1/2")
    assert row.status == "stable"


def test_jump_obstruction_is_recorded_as_counterexample():
    card = jump_obstruction_card()
    assert card.name == "analysis-jump-obstruction"
    assert card.relation == "blocked"
    assert card.obstruction == "echo-jump"


def test_real_analysis_structure_checklist():
    assert len(real_analysis_structure_checklist()) == 4
