import pytest

from src.core.ratio import ratio_shadow
from src.core.trigonometry_identities import compose_phases, conjugate_phase, double_angle_identity_card, inverse_phase_identity_card, pythagorean_identity_card, sum_angle_identity_card, trig_vector_from_ints, trigonometry_identity_checklist, unit_identity_gap


def test_rational_unit_phase_and_pythagorean_card():
    phase = trig_vector_from_ints(3, 4, 5, "a")
    assert phase.shadow_pair() == ("3/5", "4/5")
    assert ratio_shadow(unit_identity_gap(phase)) == 0
    assert pythagorean_identity_card(phase).relation == "coherent"


def test_sum_angle_composition_is_exact():
    first = trig_vector_from_ints(3, 4, 5, "a")
    second = trig_vector_from_ints(5, 12, 13, "b")
    combined = compose_phases(first, second)
    card = sum_angle_identity_card(first, second)
    assert combined.shadow_pair() == ("-33/65", "56/65")
    assert ratio_shadow(unit_identity_gap(combined)) == 0
    assert card.relation == "coherent"


def test_double_and_inverse_phase_cards():
    phase = trig_vector_from_ints(3, 4, 5, "a")
    inverse = conjugate_phase(phase)
    assert inverse.shadow_pair() == ("3/5", "-4/5")
    assert double_angle_identity_card(phase).relation == "coherent"
    assert inverse_phase_identity_card(phase).relation == "coherent"
    assert len(trigonometry_identity_checklist()) == 4


def test_trig_vector_rejects_zero_denominator():
    with pytest.raises(ValueError):
        trig_vector_from_ints(1, 0, 0)
