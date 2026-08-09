"""Finite transcendental and limit-algebra seed for Veyra analysis."""

from __future__ import annotations

from dataclasses import dataclass
import logging

from .calculus_depth import scale_polynomial
from ..geometry.theorems import TheoremCard
from .polynomial import Polynomial, derivative_polynomial, eval_polynomial, normalize_polynomial, polynomial_from_ints
from .ratio import RatioMode, ratio_from_ints, ratio_shadow, subtract_ratios

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class FormalSeriesShadow:
    """Finite formal series shadow with an explicit truncation obstruction."""

    name: str
    coefficients: tuple[RatioMode, ...]
    obstruction: str

    @property
    def order(self) -> int:
        """Return the finite truncation order."""
        logger.debug("FormalSeriesShadow.order entry name=%s", self.name)
        result = len(self.coefficients) - 1
        logger.debug("FormalSeriesShadow.order exit result=%d", result)
        return result

    def polynomial(self) -> Polynomial:
        """Return the ratio-polynomial shadow of this finite series."""
        logger.debug("FormalSeriesShadow.polynomial entry name=%s", self.name)
        result = normalize_polynomial(Polynomial(self.coefficients))
        logger.debug("FormalSeriesShadow.polynomial exit degree=%d", result.degree)
        return result


@dataclass(frozen=True)
class LimitEnvelope:
    """Finite interval envelope for a truncated transcendental shadow."""

    label: str
    center: RatioMode
    radius: RatioMode
    status: str
    obstruction: str

    def as_dict(self) -> dict[str, str]:
        """Return JSON-ready envelope row."""
        logger.debug("LimitEnvelope.as_dict entry label=%s", self.label)
        result = {"label": self.label, "center": str(ratio_shadow(self.center)), "radius": str(ratio_shadow(self.radius)), "status": self.status, "obstruction": self.obstruction}
        logger.debug("LimitEnvelope.as_dict exit result=%r", result)
        return result


def factorial_int(value: int) -> int:
    """Return factorial for a nonnegative integer."""
    logger.debug("factorial_int entry value=%d", value)
    if value < 0:
        logger.error("factorial_int negative value=%d", value)
        raise ValueError("value must be nonnegative")
    result = 1
    for item in range(2, value + 1):
        result *= item
    logger.debug("factorial_int exit result=%d", result)
    return result


def exp_series(order: int) -> FormalSeriesShadow:
    """Return finite formal `exp(x)` series through `order`."""
    logger.debug("exp_series entry order=%d", order)
    if order < 0:
        logger.error("exp_series negative order=%d", order)
        raise ValueError("order must be nonnegative")
    result = FormalSeriesShadow("exp", tuple(ratio_from_ints(1, factorial_int(i)) for i in range(order + 1)), "truncated-tail")
    logger.debug("exp_series exit order=%d", result.order)
    return result


def log1p_series(order: int) -> FormalSeriesShadow:
    """Return finite formal `log(1+x)` series through `order`."""
    logger.debug("log1p_series entry order=%d", order)
    if order < 1:
        logger.error("log1p_series invalid order=%d", order)
        raise ValueError("order must be at least one")
    coeffs = [ratio_from_ints(0)]
    for index in range(1, order + 1):
        sign = 1 if index % 2 == 1 else -1
        coeffs.append(ratio_from_ints(sign, index))
    result = FormalSeriesShadow("log1p", tuple(coeffs), "truncated-alternating-tail")
    logger.debug("log1p_series exit order=%d", result.order)
    return result


def geometric_alt_series(order: int) -> Polynomial:
    """Return finite alternating geometric series `1 - x + x^2 ...`."""
    logger.debug("geometric_alt_series entry order=%d", order)
    if order < 0:
        logger.error("geometric_alt_series negative order=%d", order)
        raise ValueError("order must be nonnegative")
    result = normalize_polynomial(Polynomial(tuple(ratio_from_ints(1 if i % 2 == 0 else -1) for i in range(order + 1))))
    logger.debug("geometric_alt_series exit degree=%d", result.degree)
    return result


def series_value(series: FormalSeriesShadow, point: RatioMode) -> RatioMode:
    """Evaluate a finite series polynomial at a ratio point."""
    logger.debug("series_value entry name=%s point=%s", series.name, point.word)
    result = eval_polynomial(series.polynomial(), point)
    logger.debug("series_value exit result=%s", result.word)
    return result


def exp_derivative_card(order: int) -> TheoremCard:
    """Check finite derivative shift `D E_n = E_{n-1}`."""
    logger.debug("exp_derivative_card entry order=%d", order)
    if order < 1:
        logger.error("exp_derivative_card invalid order=%d", order)
        raise ValueError("order must be at least one")
    observed = derivative_polynomial(exp_series(order).polynomial())
    expected = exp_series(order - 1).polynomial()
    ok = tuple(map(ratio_shadow, observed.coefficients)) == tuple(map(ratio_shadow, expected.coefficients))
    result = TheoremCard("transcendental-exp-derivative-shift", "finite-formal", "coherent" if ok else "broken", "none" if ok else "series-derivative-gap", (("order", str(order)),))
    logger.debug("exp_derivative_card exit relation=%s", result.relation)
    return result


def log1p_derivative_card(order: int) -> TheoremCard:
    """Check finite derivative `D L_n = 1 - x + ...` through degree `n-1`."""
    logger.debug("log1p_derivative_card entry order=%d", order)
    if order < 1:
        logger.error("log1p_derivative_card invalid order=%d", order)
        raise ValueError("order must be at least one")
    observed = derivative_polynomial(log1p_series(order).polynomial())
    expected = geometric_alt_series(order - 1)
    ok = tuple(map(ratio_shadow, observed.coefficients)) == tuple(map(ratio_shadow, expected.coefficients))
    result = TheoremCard("transcendental-log1p-derivative-shift", "finite-formal", "coherent" if ok else "broken", "none" if ok else "series-derivative-gap", (("order", str(order)),))
    logger.debug("log1p_derivative_card exit relation=%s", result.relation)
    return result


def alternating_log1p_envelope(order: int, point: RatioMode) -> LimitEnvelope:
    """Return alternating-tail envelope for `log(1+x)` at `0 < x <= 1`."""
    logger.debug("alternating_log1p_envelope entry order=%d point=%s", order, point.word)
    value = ratio_shadow(point)
    if order < 1 or value <= 0 or value > 1:
        logger.error("alternating_log1p_envelope invalid order=%d value=%s", order, value)
        raise ValueError("requires order>=1 and 0 < point <= 1")
    center = series_value(log1p_series(order), point)
    next_poly = scale_polynomial(polynomial_from_ints([0] * (order + 1) + [1]), ratio_from_ints(1, order + 1))
    radius = series_value(FormalSeriesShadow("tail", next_poly.coefficients, "next-term-bound"), point)
    result = LimitEnvelope("log1p-alternating-tail", center, radius, "bounded", "none")
    logger.debug("alternating_log1p_envelope exit result=%r", result.as_dict())
    return result


def envelope_contains_center(envelope: LimitEnvelope) -> bool:
    """Return True iff the envelope radius is nonnegative around its center."""
    logger.debug("envelope_contains_center entry label=%s", envelope.label)
    result = ratio_shadow(subtract_ratios(envelope.center, envelope.center)) <= ratio_shadow(envelope.radius)
    logger.debug("envelope_contains_center exit result=%s", result)
    return result


def alternating_tail_bound_card(order: int, point: RatioMode) -> TheoremCard:
    """Return theorem card for a finite alternating tail envelope."""
    logger.debug("alternating_tail_bound_card entry order=%d point=%s", order, point.word)
    envelope = alternating_log1p_envelope(order, point)
    ok = envelope.status == "bounded" and envelope_contains_center(envelope) and ratio_shadow(envelope.radius) > 0
    result = TheoremCard("transcendental-alternating-tail-bound", "finite-envelope", "bounded" if ok else "broken", "none" if ok else "tail-bound-gap", (("center", str(ratio_shadow(envelope.center))), ("radius", str(ratio_shadow(envelope.radius)))))
    logger.debug("alternating_tail_bound_card exit relation=%s", result.relation)
    return result


def transcendental_limit_checklist() -> tuple[str, ...]:
    """Return bounded transcendental/limit algebra checklist."""
    logger.debug("transcendental_limit_checklist entry")
    result = ("finite exp series", "finite log1p series", "formal derivative shifts", "alternating tail envelope")
    logger.debug("transcendental_limit_checklist exit count=%d", len(result))
    return result
