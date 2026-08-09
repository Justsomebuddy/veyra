"""Trigonometry identity theorem-card seeds for Veyra."""

from __future__ import annotations

from dataclasses import dataclass
import logging

from ..geometry.theorems import TheoremCard
from .ratio import RatioMode, add_ratios, multiply_ratios, ratio_from_ints, ratio_shadow, subtract_ratios

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class TrigIdentityVector:
    """Rational cosine/sine shadow for one cyclic phase."""

    cos: RatioMode
    sin: RatioMode
    label: str = "phase"

    def shadow_pair(self) -> tuple[str, str]:
        """Return exact string shadows for cosine and sine."""
        logger.debug("TrigIdentityVector.shadow_pair entry label=%s", self.label)
        result = (str(ratio_shadow(self.cos)), str(ratio_shadow(self.sin)))
        logger.debug("TrigIdentityVector.shadow_pair exit result=%r", result)
        return result


def trig_vector_from_ints(cos_num: int, sin_num: int, denom: int, label: str = "phase") -> TrigIdentityVector:
    """Build rational trig vector from one denominator."""
    logger.debug("trig_vector_from_ints entry cos=%d sin=%d denom=%d label=%s", cos_num, sin_num, denom, label)
    if denom == 0:
        logger.error("trig_vector_from_ints zero denominator")
        raise ValueError("denominator must be nonzero")
    result = TrigIdentityVector(ratio_from_ints(cos_num, denom), ratio_from_ints(sin_num, denom), label)
    logger.debug("trig_vector_from_ints exit pair=%r", result.shadow_pair())
    return result


def unit_identity_gap(vector: TrigIdentityVector) -> RatioMode:
    """Return `cos^2 + sin^2 - 1` for a trig vector."""
    logger.debug("unit_identity_gap entry label=%s", vector.label)
    total = add_ratios(multiply_ratios(vector.cos, vector.cos), multiply_ratios(vector.sin, vector.sin))
    result = subtract_ratios(total, ratio_from_ints(1))
    logger.debug("unit_identity_gap exit result=%s", result.word)
    return result


def pythagorean_identity_card(vector: TrigIdentityVector) -> TheoremCard:
    """Card checking `cos²+sin²=1` for a rational phase shadow."""
    logger.debug("pythagorean_identity_card entry label=%s", vector.label)
    gap = unit_identity_gap(vector)
    coherent = ratio_shadow(gap) == 0
    result = TheoremCard("trig-pythagorean-identity", "exact", "coherent" if coherent else "broken", "none" if coherent else "unit-gap", (("label", vector.label), ("gap", str(ratio_shadow(gap)))))
    logger.debug("pythagorean_identity_card exit relation=%s", result.relation)
    return result


def conjugate_phase(vector: TrigIdentityVector) -> TrigIdentityVector:
    """Return inverse phase shadow `(cos, -sin)`."""
    logger.debug("conjugate_phase entry label=%s", vector.label)
    result = TrigIdentityVector(vector.cos, subtract_ratios(ratio_from_ints(0), vector.sin), f"-{vector.label}")
    logger.debug("conjugate_phase exit pair=%r", result.shadow_pair())
    return result


def compose_phases(left: TrigIdentityVector, right: TrigIdentityVector, label: str = "sum") -> TrigIdentityVector:
    """Compose phase shadows by sum-angle formulas."""
    logger.debug("compose_phases entry left=%s right=%s label=%s", left.label, right.label, label)
    cos_part = subtract_ratios(multiply_ratios(left.cos, right.cos), multiply_ratios(left.sin, right.sin))
    sin_part = add_ratios(multiply_ratios(left.sin, right.cos), multiply_ratios(left.cos, right.sin))
    result = TrigIdentityVector(cos_part, sin_part, label)
    logger.debug("compose_phases exit pair=%r", result.shadow_pair())
    return result


def sum_angle_identity_card(left: TrigIdentityVector, right: TrigIdentityVector) -> TheoremCard:
    """Card checking rational sum-angle composition preserves the unit identity."""
    logger.debug("sum_angle_identity_card entry left=%s right=%s", left.label, right.label)
    result_vector = compose_phases(left, right, f"{left.label}+{right.label}")
    coherent = all(ratio_shadow(unit_identity_gap(item)) == 0 for item in (left, right, result_vector))
    result = TheoremCard("trig-sum-angle", "exact", "coherent" if coherent else "broken", "none" if coherent else "sum-angle-gap", (("cos", str(ratio_shadow(result_vector.cos))), ("sin", str(ratio_shadow(result_vector.sin)))))
    logger.debug("sum_angle_identity_card exit relation=%s", result.relation)
    return result


def double_angle_identity_card(vector: TrigIdentityVector) -> TheoremCard:
    """Card checking double-angle formula against phase self-composition."""
    logger.debug("double_angle_identity_card entry label=%s", vector.label)
    observed = compose_phases(vector, vector, f"2{vector.label}")
    expected_cos = subtract_ratios(multiply_ratios(vector.cos, vector.cos), multiply_ratios(vector.sin, vector.sin))
    expected_sin = multiply_ratios(ratio_from_ints(2), multiply_ratios(vector.sin, vector.cos))
    coherent = ratio_shadow(observed.cos) == ratio_shadow(expected_cos) and ratio_shadow(observed.sin) == ratio_shadow(expected_sin)
    result = TheoremCard("trig-double-angle", "exact", "coherent" if coherent else "broken", "none" if coherent else "double-angle-gap", (("cos", str(ratio_shadow(observed.cos))), ("sin", str(ratio_shadow(observed.sin)))))
    logger.debug("double_angle_identity_card exit relation=%s", result.relation)
    return result


def inverse_phase_identity_card(vector: TrigIdentityVector) -> TheoremCard:
    """Card checking phase plus inverse phase gives identity `(1,0)`."""
    logger.debug("inverse_phase_identity_card entry label=%s", vector.label)
    observed = compose_phases(vector, conjugate_phase(vector), "identity")
    coherent = ratio_shadow(observed.cos) == 1 and ratio_shadow(observed.sin) == 0
    result = TheoremCard("trig-inverse-phase", "exact", "coherent" if coherent else "broken", "none" if coherent else "inverse-gap", (("cos", str(ratio_shadow(observed.cos))), ("sin", str(ratio_shadow(observed.sin)))))
    logger.debug("inverse_phase_identity_card exit relation=%s", result.relation)
    return result


def trigonometry_identity_checklist() -> tuple[str, ...]:
    """Return trigonometry identity acceptance checklist."""
    logger.debug("trigonometry_identity_checklist entry")
    result = ("rational unit phase", "pythagorean identity card", "sum-angle composition card", "double/inverse phase cards")
    logger.debug("trigonometry_identity_checklist exit count=%d", len(result))
    return result
