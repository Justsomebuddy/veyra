"""Executable theorem cards for Veyra algebra and analysis layers."""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import logging

from .change import AreaCertificate, ContinuityCertificate, DriftQuotient, ratio_distance
from .equation import LinearEquation, solve_linear, solution_satisfies
from ..geometry.theorems import TheoremCard
from .polynomial import Polynomial, eval_polynomial, normalize_polynomial, zero_ratio
from .ratio import RatioMode, add_ratios, ratio_from_ints, ratio_shadow, subtract_ratios

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PolynomialIdentityEvidence:
    """Compact coefficient-level identity evidence."""

    left_degree: int
    right_degree: int
    checked_coefficients: int


def ratio_text(value: RatioMode) -> str:
    """Return exact ratio-shadow text."""
    logger.debug("algebra ratio_text entry value=%s", value.word)
    result = str(ratio_shadow(value))
    logger.debug("algebra ratio_text exit result=%s", result)
    return result


def linear_equation_card(equation: LinearEquation) -> TheoremCard:
    """Return theorem card for a linear equation solution/obstruction."""
    logger.debug("linear_equation_card entry")
    solution = solve_linear(equation)
    if solution.status == "unique" and solution.value is not None:
        ok = solution_satisfies(equation, solution.value)
        relation = "unique" if ok else "blocked"
        obstruction = "none" if ok else "residual-nonzero"
        evidence = (("solution", ratio_text(solution.value)),)
    elif solution.status == "infinite":
        relation = "identity"
        obstruction = "none"
        evidence = (("solution_family", "all-ratio-shadows"),)
    else:
        relation = "blocked"
        obstruction = solution.obstruction
        evidence = (("solution", "none"),)
    result = TheoremCard("linear-equation-solution", "exact", relation, obstruction, evidence)
    logger.debug("linear_equation_card exit relation=%s obstruction=%s", relation, obstruction)
    return result


def polynomial_identity_evidence(left: Polynomial, right: Polynomial) -> PolynomialIdentityEvidence:
    """Return coefficient comparison evidence shape."""
    logger.debug("polynomial_identity_evidence entry")
    a = normalize_polynomial(left)
    b = normalize_polynomial(right)
    result = PolynomialIdentityEvidence(a.degree, b.degree, max(len(a.coefficients), len(b.coefficients)))
    logger.debug("polynomial_identity_evidence exit checked=%d", result.checked_coefficients)
    return result


def coefficient_at(poly: Polynomial, index: int) -> RatioMode:
    """Return coefficient at index or zero."""
    logger.debug("coefficient_at entry index=%d", index)
    result = poly.coefficients[index] if index < len(poly.coefficients) else zero_ratio()
    logger.debug("coefficient_at exit value=%s", result.word)
    return result


def polynomial_identity_card(left: Polynomial, right: Polynomial) -> TheoremCard:
    """Return exact coefficient identity card for two polynomial forms."""
    logger.debug("polynomial_identity_card entry")
    evidence_shape = polynomial_identity_evidence(left, right)
    same = True
    for index in range(evidence_shape.checked_coefficients):
        if ratio_shadow(coefficient_at(left, index)) != ratio_shadow(coefficient_at(right, index)):
            same = False
            break
    relation = "identity" if same else "different"
    obstruction = "none" if same else "coefficient-mismatch"
    evidence = (("left_degree", str(evidence_shape.left_degree)), ("right_degree", str(evidence_shape.right_degree)), ("checked_coefficients", str(evidence_shape.checked_coefficients)))
    result = TheoremCard("polynomial-identity", "exact", relation, obstruction, evidence)
    logger.debug("polynomial_identity_card exit relation=%s", relation)
    return result


def polynomial_evaluation_card(poly: Polynomial, value: RatioMode, expected: RatioMode) -> TheoremCard:
    """Return card for polynomial evaluation at one ratio shadow."""
    logger.debug("polynomial_evaluation_card entry value=%s", value.word)
    observed = eval_polynomial(poly, value)
    relation = "matches" if ratio_shadow(observed) == ratio_shadow(expected) else "different"
    obstruction = "none" if relation == "matches" else "value-mismatch"
    result = TheoremCard("polynomial-evaluation", "exact", relation, obstruction, (("observed", ratio_text(observed)), ("expected", ratio_text(expected))))
    logger.debug("polynomial_evaluation_card exit relation=%s", relation)
    return result


def continuity_card(certificate: ContinuityCertificate) -> TheoremCard:
    """Promote sampled continuity certificate to theorem-card shape."""
    logger.debug("continuity_card entry status=%s", certificate.status)
    relation = "stable" if certificate.status == "stable" else "blocked"
    obstruction = "none" if relation == "stable" else certificate.obstruction
    evidence = (("checked", str(certificate.checked)), ("max_drift", str(certificate.max_drift)))
    result = TheoremCard("sampled-continuity", "finite", relation, obstruction, evidence)
    logger.debug("continuity_card exit relation=%s", relation)
    return result


def drift_stability_card(quotients: tuple[DriftQuotient, ...], tolerance: RatioMode = ratio_from_ints(0)) -> TheoremCard:
    """Return card for drift quotient stability across refinements."""
    logger.debug("drift_stability_card entry count=%d", len(quotients))
    if not quotients:
        logger.error("drift_stability_card empty quotients")
        raise ValueError("at least one quotient required")
    base = quotients[0].value
    max_gap = Fraction(0)
    for quotient in quotients[1:]:
        max_gap = max(max_gap, ratio_distance(base, quotient.value))
    relation = "stable" if max_gap <= ratio_shadow(tolerance) else "unstable"
    obstruction = "none" if relation == "stable" else "drift-jump"
    evidence = (("quotients", str(len(quotients))), ("base", ratio_text(base)), ("max_gap", str(max_gap)))
    result = TheoremCard("drift-stability", "finite", relation, obstruction, evidence)
    logger.debug("drift_stability_card exit relation=%s max_gap=%s", relation, max_gap)
    return result


def area_additivity_card(left: AreaCertificate, right: AreaCertificate, whole: AreaCertificate, tolerance: RatioMode = ratio_from_ints(0)) -> TheoremCard:
    """Return card for finite area additivity over adjacent intervals."""
    logger.debug("area_additivity_card entry")
    if left.value is None or right.value is None or whole.value is None:
        result = TheoremCard("area-additivity", "finite", "blocked", "missing-area-value", ())
        logger.debug("area_additivity_card exit missing")
        return result
    combined = add_ratios(left.value, right.value)
    gap = ratio_shadow(subtract_ratios(combined, whole.value))
    relation = "additive" if abs(gap) <= ratio_shadow(tolerance) else "broken"
    obstruction = "none" if relation == "additive" else "area-gap"
    evidence = (("combined", ratio_text(combined)), ("whole", ratio_text(whole.value)), ("gap", str(gap)))
    result = TheoremCard("area-additivity", "finite", relation, obstruction, evidence)
    logger.debug("area_additivity_card exit relation=%s gap=%s", relation, gap)
    return result
