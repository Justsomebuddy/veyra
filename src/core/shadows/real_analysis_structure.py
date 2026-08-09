"""Finite real-analysis structure certificates for Veyra."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from fractions import Fraction
import logging

from .change import AreaCertificate, DriftQuotient, riemann_area, sampled_continuity, symmetric_difference_quotient
from ..geometry.theorems import TheoremCard
from .ratio import RatioMode, ratio_from_fraction, ratio_from_ints, ratio_shadow, subtract_ratios

logger = logging.getLogger(__name__)
Rule = Callable[[RatioMode], RatioMode]


@dataclass(frozen=True)
class FiniteModulusCertificate:
    """Finite grid certificate for an epsilon/modulus observer."""

    label: str
    checked_pairs: int
    input_radius: RatioMode
    output_tolerance: RatioMode
    max_output_drift: RatioMode
    status: str
    obstruction: str

    def as_dict(self) -> dict[str, object]:
        """Return JSON-ready finite-modulus row."""
        logger.debug("FiniteModulusCertificate.as_dict entry label=%s", self.label)
        result = {"label": self.label, "checked_pairs": self.checked_pairs, "input_radius": str(ratio_shadow(self.input_radius)), "output_tolerance": str(ratio_shadow(self.output_tolerance)), "max_output_drift": str(ratio_shadow(self.max_output_drift)), "status": self.status, "obstruction": self.obstruction}
        logger.debug("FiniteModulusCertificate.as_dict exit result=%r", result)
        return result


@dataclass(frozen=True)
class RefinementStabilityCertificate:
    """Certificate that refinement rows remain stable under a tolerance."""

    label: str
    values: tuple[RatioMode, ...]
    max_gap: RatioMode
    status: str
    obstruction: str

    def as_dict(self) -> dict[str, object]:
        """Return JSON-ready refinement-stability row."""
        logger.debug("RefinementStabilityCertificate.as_dict entry label=%s", self.label)
        result = {"label": self.label, "values": tuple(str(ratio_shadow(item)) for item in self.values), "max_gap": str(ratio_shadow(self.max_gap)), "status": self.status, "obstruction": self.obstruction}
        logger.debug("RefinementStabilityCertificate.as_dict exit result=%r", result)
        return result


def square_rule(value: RatioMode) -> RatioMode:
    """Return exact square rule on ratio shadows."""
    logger.debug("square_rule entry value=%s", value.word)
    v = ratio_shadow(value)
    result = ratio_from_fraction(v * v)
    logger.debug("square_rule exit result=%s", result.word)
    return result


def identity_rule(value: RatioMode) -> RatioMode:
    """Return identity rule for analysis rows."""
    logger.debug("identity_rule entry value=%s", value.word)
    logger.debug("identity_rule exit result=%s", value.word)
    return value


def jump_rule(value: RatioMode) -> RatioMode:
    """Return toy jump rule: 0 below zero, 1 otherwise."""
    logger.debug("jump_rule entry value=%s", value.word)
    result = ratio_from_ints(0) if ratio_shadow(value) < 0 else ratio_from_ints(1)
    logger.debug("jump_rule exit result=%s", result.word)
    return result


def finite_modulus_certificate(label: str, rule: Rule, grid: tuple[RatioMode, ...], input_radius: RatioMode, output_tolerance: RatioMode) -> FiniteModulusCertificate:
    """Check finite grid pairs whose input distance fits a radius."""
    logger.debug("finite_modulus_certificate entry label=%s grid=%d", label, len(grid))
    max_drift = ratio_from_ints(0)
    checked = 0
    for index, left in enumerate(grid):
        for right in grid[index + 1:]:
            if abs(ratio_shadow(subtract_ratios(left, right))) <= ratio_shadow(input_radius):
                checked += 1
                drift = ratio_from_fraction(abs(ratio_shadow(subtract_ratios(rule(left), rule(right)))))
                if ratio_shadow(drift) > ratio_shadow(max_drift):
                    max_drift = drift
    ok = checked > 0 and ratio_shadow(max_drift) <= ratio_shadow(output_tolerance)
    result = FiniteModulusCertificate(label, checked, input_radius, output_tolerance, max_drift, "stable" if ok else "blocked", "none" if ok else "modulus-gap")
    logger.debug("finite_modulus_certificate exit result=%r", result.as_dict())
    return result


def derivative_refinement_certificate(rule: Rule, anchor: RatioMode, steps: tuple[RatioMode, ...], tolerance: RatioMode) -> RefinementStabilityCertificate:
    """Check symmetric difference quotients across step refinements."""
    logger.debug("derivative_refinement_certificate entry steps=%d", len(steps))
    quotients = tuple(symmetric_difference_quotient(rule, anchor, step).value for step in steps)
    result = _stability_row("derivative-refinement", quotients, tolerance)
    logger.debug("derivative_refinement_certificate exit result=%r", result.as_dict())
    return result


def area_refinement_certificate(rule: Rule, lower: RatioMode, upper: RatioMode, slices: tuple[int, ...], tolerance: RatioMode) -> RefinementStabilityCertificate:
    """Check midpoint Riemann rows across slice refinements."""
    logger.debug("area_refinement_certificate entry slices=%r", slices)
    values = tuple(_area_value(riemann_area(rule, lower, upper, count, "mid")) for count in slices)
    result = _stability_row("area-refinement", values, tolerance)
    logger.debug("area_refinement_certificate exit result=%r", result.as_dict())
    return result


def jump_obstruction_card() -> TheoremCard:
    """Return finite sampled jump obstruction card."""
    logger.debug("jump_obstruction_card entry")
    cert = sampled_continuity(jump_rule, ratio_from_ints(0), ratio_from_ints(1), ratio_from_ints(0), 2)
    result = TheoremCard("analysis-jump-obstruction", "finite", "blocked" if cert.status == "none" else "stable", cert.obstruction, (("checked", str(cert.checked)), ("max_drift", str(cert.max_drift))))
    logger.debug("jump_obstruction_card exit relation=%s", result.relation)
    return result


def real_analysis_structure_checklist() -> tuple[str, ...]:
    """Return finite real-analysis structure checklist."""
    logger.debug("real_analysis_structure_checklist entry")
    result = ("finite modulus grid", "derivative refinement stability", "area refinement stability", "jump obstruction counterexample")
    logger.debug("real_analysis_structure_checklist exit count=%d", len(result))
    return result


def _stability_row(label: str, values: tuple[RatioMode, ...], tolerance: RatioMode) -> RefinementStabilityCertificate:
    """Build a generic refinement stability row."""
    logger.debug("_stability_row entry label=%s count=%d", label, len(values))
    if len(values) < 2:
        logger.error("_stability_row too few values")
        raise ValueError("at least two values required")
    gaps = [abs(ratio_shadow(subtract_ratios(left, right))) for left, right in zip(values, values[1:])]
    max_gap = ratio_from_fraction(max(gaps, default=Fraction(0)))
    ok = ratio_shadow(max_gap) <= ratio_shadow(tolerance)
    result = RefinementStabilityCertificate(label, values, max_gap, "stable" if ok else "blocked", "none" if ok else "refinement-gap")
    logger.debug("_stability_row exit result=%r", result.as_dict())
    return result


def _area_value(cert: AreaCertificate) -> RatioMode:
    """Extract area value from a finite area certificate."""
    logger.debug("_area_value entry status=%s", cert.status)
    if cert.value is None:
        logger.error("_area_value missing value obstruction=%s", cert.obstruction)
        raise ValueError("area certificate has no value")
    logger.debug("_area_value exit result=%s", cert.value.word)
    return cert.value
