from fractions import Fraction

from src.core.ratio import ratio_from_ints, ratio_shadow
from src.core.transformer import (
    affine_transformer,
    apply_transformer,
    compose_transformers,
    fixed_point_shadow,
    graph_shadow,
    identity_transformer,
    inverse_affine_transformer,
    transformer_echo_equivalent,
)


def test_affine_transformer_application():
    transform = affine_transformer(ratio_from_ints(2), ratio_from_ints(3), "f")
    assert ratio_shadow(apply_transformer(transform, ratio_from_ints(5))) == 13


def test_transformer_composition():
    outer = affine_transformer(ratio_from_ints(2), ratio_from_ints(3), "f")
    inner = affine_transformer(ratio_from_ints(1), ratio_from_ints(-1), "g")
    composed = compose_transformers(outer, inner)
    assert ratio_shadow(apply_transformer(composed, ratio_from_ints(5))) == 11


def test_inverse_affine_transformer():
    transform = affine_transformer(ratio_from_ints(2), ratio_from_ints(3), "f")
    inverse = inverse_affine_transformer(transform)
    value = apply_transformer(inverse, apply_transformer(transform, ratio_from_ints(5)))
    assert ratio_shadow(value) == 5


def test_fixed_point_shadow():
    transform = affine_transformer(ratio_from_ints(2), ratio_from_ints(3), "f")
    status, value = fixed_point_shadow(transform)
    assert status == "unique"
    assert value is not None
    assert ratio_shadow(value) == -3


def test_graph_shadow_and_echo_equivalence():
    samples = (ratio_from_ints(0), ratio_from_ints(1), ratio_from_ints(1, 2))
    ident = identity_transformer()
    same = affine_transformer(ratio_from_ints(1), ratio_from_ints(0), "same")
    graph = graph_shadow(ident, samples)
    assert graph[-1] == (Fraction(1, 2), Fraction(1, 2))
    assert transformer_echo_equivalent(ident, same, samples)
