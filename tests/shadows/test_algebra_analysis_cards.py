from src.core.algebra_analysis_cards import area_additivity_card, continuity_card, drift_stability_card, linear_equation_card, polynomial_evaluation_card, polynomial_identity_card
from src.core.change import riemann_area, sampled_continuity, symmetric_difference_quotient
from src.core.equation import LinearEquation, constant, variable
from src.core.polynomial import add_polynomials, polynomial_from_ints
from src.core.ratio import ratio_from_ints
from src.core.transformer import affine_transformer, apply_transformer, transformer_from_polynomial


def test_linear_equation_card_unique_identity_blocked():
    assert linear_equation_card(LinearEquation(variable(2, 1), constant(7))).relation == "unique"
    assert linear_equation_card(LinearEquation(variable(1, 0), variable(1, 0))).relation == "identity"
    assert linear_equation_card(LinearEquation(variable(1, 0), variable(1, 1))).obstruction == "parallel-obstruction"


def test_polynomial_identity_and_evaluation_cards():
    left = add_polynomials(polynomial_from_ints([1, 2]), polynomial_from_ints([3, -2]))
    right = polynomial_from_ints([4])
    assert polynomial_identity_card(left, right).relation == "identity"
    assert polynomial_identity_card(left, polynomial_from_ints([5])).obstruction == "coefficient-mismatch"
    assert polynomial_evaluation_card(polynomial_from_ints([1, 0, 1]), ratio_from_ints(3), ratio_from_ints(10)).relation == "matches"


def test_continuity_card_stable_and_blocked():
    rule = affine_transformer(ratio_from_ints(2), ratio_from_ints(0), "double")
    stable = sampled_continuity(lambda x: apply_transformer(rule, x), ratio_from_ints(0), ratio_from_ints(1, 10), ratio_from_ints(1), 2)
    assert continuity_card(stable).relation == "stable"

    def jump(x):
        from src.core.ratio import ratio_shadow
        return ratio_from_ints(0) if ratio_shadow(x) < 0 else ratio_from_ints(1)

    blocked = sampled_continuity(jump, ratio_from_ints(0), ratio_from_ints(1), ratio_from_ints(1, 2), 2)
    assert continuity_card(blocked).obstruction == "echo-jump"


def test_drift_stability_for_square_symmetric_quotients():
    square = transformer_from_polynomial("square", polynomial_from_ints([0, 0, 1]))
    rule = lambda x: apply_transformer(square, x)
    quotients = tuple(symmetric_difference_quotient(rule, ratio_from_ints(3), ratio_from_ints(step)) for step in (1, 2, 3))
    assert drift_stability_card(quotients).relation == "stable"


def test_area_additivity_for_identity_midpoint_sum():
    identity = affine_transformer(ratio_from_ints(1), ratio_from_ints(0), "id")
    rule = lambda x: apply_transformer(identity, x)
    left = riemann_area(rule, ratio_from_ints(0), ratio_from_ints(1), 4, "mid")
    right = riemann_area(rule, ratio_from_ints(1), ratio_from_ints(2), 4, "mid")
    whole = riemann_area(rule, ratio_from_ints(0), ratio_from_ints(2), 8, "mid")
    assert area_additivity_card(left, right, whole).relation == "additive"
