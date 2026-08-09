from src.core.change import difference_quotient, riemann_area, sampled_continuity, symmetric_difference_quotient
from src.core.polynomial import polynomial_from_ints
from src.core.ratio import ratio_from_ints, ratio_shadow
from src.core.transformer import affine_transformer, apply_transformer, transformer_from_polynomial


def test_affine_sampled_continuity_is_stable():
    rule = affine_transformer(ratio_from_ints(3), ratio_from_ints(1), "triple_shift")
    cert = sampled_continuity(lambda x: apply_transformer(rule, x), ratio_from_ints(2), ratio_from_ints(1, 10), ratio_from_ints(1), 3)
    assert cert.status == "stable"
    assert cert.checked == 7
    assert cert.max_drift <= ratio_shadow(ratio_from_ints(3, 10))


def test_jump_rule_reports_echo_jump():
    def jump(x):
        return ratio_from_ints(0) if ratio_shadow(x) < 0 else ratio_from_ints(1)

    cert = sampled_continuity(jump, ratio_from_ints(0), ratio_from_ints(1), ratio_from_ints(1, 2), 2)
    assert cert.status == "none"
    assert cert.obstruction == "echo-jump"


def test_square_change_quotients():
    square = transformer_from_polynomial("square", polynomial_from_ints([0, 0, 1]))
    rule = lambda x: apply_transformer(square, x)
    forward = difference_quotient(rule, ratio_from_ints(3), ratio_from_ints(1))
    symmetric = symmetric_difference_quotient(rule, ratio_from_ints(3), ratio_from_ints(1))
    assert ratio_shadow(forward.value) == 7
    assert ratio_shadow(symmetric.value) == 6


def test_midpoint_area_for_identity():
    identity = affine_transformer(ratio_from_ints(1), ratio_from_ints(0), "id")
    area = riemann_area(lambda x: apply_transformer(identity, x), ratio_from_ints(0), ratio_from_ints(1), 8, "mid")
    assert area.status == "finite"
    assert ratio_shadow(area.value) == ratio_shadow(ratio_from_ints(1, 2))
