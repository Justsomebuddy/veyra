from src.core.calculus_depth import chain_rule_card, compose_polynomials, integral_coherence, integral_coherence_card, linearization_error, local_linearization, product_rule_card
from src.core.polynomial import derivative_polynomial, eval_polynomial, polynomial_from_ints
from src.core.ratio import ratio_from_ints, ratio_shadow


def test_local_linearization_of_square_records_tangent_and_error():
    square = polynomial_from_ints([0, 0, 1])
    linear = local_linearization(square, ratio_from_ints(3))
    assert ratio_shadow(linear.value) == 9
    assert ratio_shadow(linear.slope) == 6
    assert [ratio_shadow(c) for c in linear.tangent.coefficients] == [-9, 6]
    assert ratio_shadow(linearization_error(square, ratio_from_ints(3), ratio_from_ints(4))) == 1


def test_product_rule_card_for_polynomial_shadows():
    left = polynomial_from_ints([0, 0, 1])
    right = polynomial_from_ints([1, 1])
    card = product_rule_card(left, right)
    assert card.name == "calculus-product-rule"
    assert card.relation == "coherent"
    assert card.obstruction == "none"


def test_chain_rule_card_and_composition_shadow():
    outer = polynomial_from_ints([0, 0, 1])
    inner = polynomial_from_ints([1, 1])
    composed = compose_polynomials(outer, inner)
    derivative = derivative_polynomial(composed)
    assert [ratio_shadow(c) for c in composed.coefficients] == [1, 2, 1]
    assert ratio_shadow(eval_polynomial(derivative, ratio_from_ints(3))) == 8
    assert chain_rule_card(outer, inner).relation == "coherent"


def test_integral_coherence_card_for_linear_polynomial():
    linear = polynomial_from_ints([0, 2])
    cert = integral_coherence(linear, ratio_from_ints(0), ratio_from_ints(3))
    assert ratio_shadow(cert.value) == 9
    card = integral_coherence_card(linear, ratio_from_ints(0), ratio_from_ints(3), ratio_from_ints(9))
    assert card.relation == "coherent"
    assert card.obstruction == "none"
