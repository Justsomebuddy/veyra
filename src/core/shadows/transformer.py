"""Mode transformers: Veyra shadow for school functions."""

from __future__ import annotations

from dataclasses import dataclass
import logging

from .equation import LinearEquation, LinearForm, solve_linear
from .polynomial import Polynomial, add_polynomials, eval_polynomial, multiply_polynomials, normalize_polynomial, polynomial_from_ints, zero_ratio
from .ratio import RatioMode, add_ratios, inverse_ratio, multiply_ratios, ratio_from_ints, ratio_shadow, subtract_ratios

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ModeTransformer:
    """A one-input ratio transformer backed by a polynomial schema."""

    name: str
    polynomial: Polynomial
    observer: str = "ratio-length"

    @property
    def degree(self) -> int:
        """Return transformer degree."""
        logger.debug("ModeTransformer.degree entry name=%s", self.name)
        result = self.polynomial.degree
        logger.debug("ModeTransformer.degree exit result=%d", result)
        return result


def transformer_from_polynomial(name: str, polynomial: Polynomial) -> ModeTransformer:
    """Create a normalized polynomial-backed transformer."""
    logger.debug("transformer_from_polynomial entry name=%s", name)
    result = ModeTransformer(name, normalize_polynomial(polynomial))
    logger.debug("transformer_from_polynomial exit degree=%d", result.degree)
    return result


def identity_transformer() -> ModeTransformer:
    """Return identity transformer x -> x."""
    logger.debug("identity_transformer entry")
    result = transformer_from_polynomial("id", polynomial_from_ints([0, 1]))
    logger.debug("identity_transformer exit")
    return result


def constant_transformer(value: RatioMode, name: str = "const") -> ModeTransformer:
    """Return constant transformer x -> value."""
    logger.debug("constant_transformer entry value=%s", value.word)
    result = transformer_from_polynomial(name, Polynomial((value,)))
    logger.debug("constant_transformer exit")
    return result


def affine_transformer(slope: RatioMode, offset: RatioMode, name: str = "affine") -> ModeTransformer:
    """Return affine transformer x -> slope*x + offset."""
    logger.debug("affine_transformer entry slope=%s offset=%s", slope.word, offset.word)
    result = transformer_from_polynomial(name, Polynomial((offset, slope)))
    logger.debug("affine_transformer exit")
    return result


def apply_transformer(transformer: ModeTransformer, value: RatioMode) -> RatioMode:
    """Apply transformer to a ratio value."""
    logger.debug("apply_transformer entry name=%s value=%s", transformer.name, value.word)
    result = eval_polynomial(transformer.polynomial, value)
    logger.debug("apply_transformer exit result=%s", result.word)
    return result


def scale_polynomial(poly: Polynomial, scalar: RatioMode) -> Polynomial:
    """Multiply every polynomial coefficient by a scalar ratio."""
    logger.debug("scale_polynomial entry degree=%d scalar=%s", poly.degree, scalar.word)
    result = normalize_polynomial(Polynomial(tuple(multiply_ratios(coeff, scalar) for coeff in poly.coefficients)))
    logger.debug("scale_polynomial exit degree=%d", result.degree)
    return result


def compose_polynomials(outer: Polynomial, inner: Polynomial) -> Polynomial:
    """Return outer(inner(x)) by polynomial Horner-like expansion."""
    logger.debug("compose_polynomials entry outer=%d inner=%d", outer.degree, inner.degree)
    result = Polynomial((zero_ratio(),))
    power = polynomial_from_ints([1])
    for coeff in outer.coefficients:
        result = add_polynomials(result, scale_polynomial(power, coeff))
        power = multiply_polynomials(power, inner)
    result = normalize_polynomial(result)
    logger.debug("compose_polynomials exit degree=%d", result.degree)
    return result


def compose_transformers(outer: ModeTransformer, inner: ModeTransformer, name: str | None = None) -> ModeTransformer:
    """Compose two transformers as outer(inner(x))."""
    logger.debug("compose_transformers entry outer=%s inner=%s", outer.name, inner.name)
    result = transformer_from_polynomial(name or f"{outer.name}∘{inner.name}", compose_polynomials(outer.polynomial, inner.polynomial))
    logger.debug("compose_transformers exit degree=%d", result.degree)
    return result


def inverse_affine_transformer(transformer: ModeTransformer) -> ModeTransformer:
    """Return inverse of nonconstant affine transformer."""
    logger.debug("inverse_affine_transformer entry name=%s", transformer.name)
    if transformer.degree != 1:
        logger.error("inverse_affine_transformer non-affine degree=%d", transformer.degree)
        raise ValueError("only degree-1 affine transformers are invertible here")
    offset, slope = transformer.polynomial.coefficients[:2]
    if ratio_shadow(slope) == 0:
        logger.error("inverse_affine_transformer zero slope")
        raise ValueError("constant transformer has no inverse")
    inv_slope = inverse_ratio(slope)
    inv_offset = multiply_ratios(subtract_ratios(ratio_from_ints(0), offset), inv_slope)
    result = affine_transformer(inv_slope, inv_offset, f"{transformer.name}⁻¹")
    logger.debug("inverse_affine_transformer exit")
    return result


def fixed_point_equation(transformer: ModeTransformer) -> LinearEquation:
    """Build linear fixed-point equation T(x)=x for affine transformers."""
    logger.debug("fixed_point_equation entry name=%s", transformer.name)
    if transformer.degree > 1:
        logger.error("fixed_point_equation nonlinear degree=%d", transformer.degree)
        raise ValueError("only affine fixed points are implemented")
    coeffs = transformer.polynomial.coefficients
    offset = coeffs[0] if coeffs else zero_ratio()
    slope = coeffs[1] if len(coeffs) > 1 else zero_ratio()
    result = LinearEquation(LinearForm(slope, offset), LinearForm(ratio_from_ints(1), ratio_from_ints(0)))
    logger.debug("fixed_point_equation exit")
    return result


def fixed_point_shadow(transformer: ModeTransformer) -> tuple[str, RatioMode | None]:
    """Solve affine fixed-point shadow T(x)=x."""
    logger.debug("fixed_point_shadow entry name=%s", transformer.name)
    solution = solve_linear(fixed_point_equation(transformer))
    result = (solution.status, solution.value)
    logger.debug("fixed_point_shadow exit status=%s", solution.status)
    return result


def graph_shadow(transformer: ModeTransformer, samples: tuple[RatioMode, ...]) -> tuple[tuple[object, object], ...]:
    """Return observer graph as rational shadow pairs."""
    logger.debug("graph_shadow entry name=%s samples=%d", transformer.name, len(samples))
    result = tuple((ratio_shadow(x), ratio_shadow(apply_transformer(transformer, x))) for x in samples)
    logger.debug("graph_shadow exit count=%d", len(result))
    return result


def transformer_echo_equivalent(left: ModeTransformer, right: ModeTransformer, samples: tuple[RatioMode, ...]) -> bool:
    """Compare transformers by finite graph shadows over samples."""
    logger.debug("transformer_echo_equivalent entry left=%s right=%s", left.name, right.name)
    result = graph_shadow(left, samples) == graph_shadow(right, samples)
    logger.debug("transformer_echo_equivalent exit result=%s", result)
    return result
