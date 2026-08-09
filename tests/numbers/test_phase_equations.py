import pytest

from src.core.phase_equations import default_phase_basis, inverse_phase_obstruction_card, phase_coordinate_row, phase_equation_checklist, phase_equation_normal_form_card, phase_pair_row
from src.core.ratio import ratio_from_ints


def test_coordinate_rows_resolve_rational_phase_matches():
    basis = default_phase_basis()
    cos_row = phase_coordinate_row("cos", ratio_from_ints(3, 5), basis)
    sin_row = phase_coordinate_row("sin", ratio_from_ints(4, 5), basis)
    assert cos_row.matches == ("a", "-a")
    assert sin_row.matches == ("a",)
    assert cos_row.as_dict()["relation"] == "resolved"


def test_phase_pair_rows_are_exact_normal_forms():
    basis = default_phase_basis()
    assert phase_pair_row(ratio_from_ints(3, 5), ratio_from_ints(4, 5), basis).matches == ("a",)
    assert phase_pair_row(ratio_from_ints(3, 5), ratio_from_ints(-4, 5), basis).matches == ("-a",)
    assert phase_equation_normal_form_card(ratio_from_ints(3, 5), ratio_from_ints(4, 5), basis).relation == "resolved"


def test_inverse_phase_obstruction_cards_name_finite_rejections():
    basis = default_phase_basis()
    accepted = inverse_phase_obstruction_card(ratio_from_ints(3, 5), ratio_from_ints(4, 5), basis)
    non_unit = inverse_phase_obstruction_card(ratio_from_ints(2), ratio_from_ints(0), basis)
    missing_basis = inverse_phase_obstruction_card(ratio_from_ints(0), ratio_from_ints(1), basis)
    assert accepted.relation == "available" and accepted.obstruction == "none"
    assert non_unit.relation == "blocked" and non_unit.obstruction == "unit-gap"
    assert missing_basis.relation == "blocked" and missing_basis.obstruction == "basis-gap"


def test_phase_equation_checklist_and_invalid_target():
    assert len(phase_equation_checklist()) == 4
    with pytest.raises(ValueError):
        phase_coordinate_row("tan", ratio_from_ints(1))
