"""Finite convergence algebra seed for Veyra analysis."""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import logging

from .completion import CompletionInterval, interval_refines
from ..geometry.theorems import TheoremCard
from .ratio import RatioMode, ratio_from_fraction, ratio_from_ints, ratio_shadow, subtract_ratios

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CauchyTailCertificate:
    """Finite tail certificate under one rational tolerance observer."""

    tolerance: RatioMode
    tail: int
    max_distance: RatioMode
    checked_pairs: int
    status: str
    obstruction: str

    def as_dict(self) -> dict[str, object]:
        """Return JSON-ready Cauchy tail row."""
        logger.debug("CauchyTailCertificate.as_dict entry tail=%d", self.tail)
        result = {"tolerance": str(ratio_shadow(self.tolerance)), "tail": self.tail, "max_distance": str(ratio_shadow(self.max_distance)), "checked_pairs": self.checked_pairs, "status": self.status, "obstruction": self.obstruction}
        logger.debug("CauchyTailCertificate.as_dict exit result=%r", result)
        return result


@dataclass(frozen=True)
class MajorantBound:
    """Finite observed-vs-majorant bound row."""

    label: str
    observed: RatioMode
    bound: RatioMode
    status: str
    obstruction: str

    def as_dict(self) -> dict[str, str]:
        """Return JSON-ready majorant row."""
        logger.debug("MajorantBound.as_dict entry label=%s", self.label)
        result = {"label": self.label, "observed": str(ratio_shadow(self.observed)), "bound": str(ratio_shadow(self.bound)), "status": self.status, "obstruction": self.obstruction}
        logger.debug("MajorantBound.as_dict exit result=%r", result)
        return result


@dataclass(frozen=True)
class NestedIntervalCertificate:
    """Finite nested interval and width-shrink row."""

    label: str
    intervals: int
    final_width: RatioMode
    status: str
    obstruction: str

    def as_dict(self) -> dict[str, object]:
        """Return JSON-ready nested interval row."""
        logger.debug("NestedIntervalCertificate.as_dict entry label=%s", self.label)
        result = {"label": self.label, "intervals": self.intervals, "final_width": str(ratio_shadow(self.final_width)), "status": self.status, "obstruction": self.obstruction}
        logger.debug("NestedIntervalCertificate.as_dict exit result=%r", result)
        return result


@dataclass(frozen=True)
class RadiusGuard:
    """Finite radius/domain guard for a series point."""

    label: str
    point: RatioMode
    radius: RatioMode
    status: str
    obstruction: str

    def as_dict(self) -> dict[str, str]:
        """Return JSON-ready radius guard row."""
        logger.debug("RadiusGuard.as_dict entry label=%s", self.label)
        result = {"label": self.label, "point": str(ratio_shadow(self.point)), "radius": str(ratio_shadow(self.radius)), "status": self.status, "obstruction": self.obstruction}
        logger.debug("RadiusGuard.as_dict exit result=%r", result)
        return result


def ratio_abs_distance(left: RatioMode, right: RatioMode) -> RatioMode:
    """Return exact absolute distance between two ratio shadows."""
    logger.debug("ratio_abs_distance entry left=%s right=%s", left.word, right.word)
    result = ratio_from_fraction(abs(ratio_shadow(subtract_ratios(left, right))))
    logger.debug("ratio_abs_distance exit result=%s", result.word)
    return result


def cauchy_tail_certificate(samples: tuple[RatioMode, ...], tolerance: RatioMode, tail: int) -> CauchyTailCertificate:
    """Certify that all pair distances in a finite tail fit the tolerance."""
    logger.debug("cauchy_tail_certificate entry samples=%d tail=%d", len(samples), tail)
    if tail <= 1 or tail > len(samples):
        logger.error("cauchy_tail_certificate invalid tail=%d", tail)
        raise ValueError("tail must be between 2 and len(samples)")
    max_distance = ratio_from_ints(0)
    checked = 0
    tail_items = samples[-tail:]
    for index, left in enumerate(tail_items):
        for right in tail_items[index + 1:]:
            checked += 1
            distance = ratio_abs_distance(left, right)
            if ratio_shadow(distance) > ratio_shadow(max_distance):
                max_distance = distance
    ok = ratio_shadow(max_distance) <= ratio_shadow(tolerance)
    result = CauchyTailCertificate(tolerance, tail, max_distance, checked, "stable" if ok else "blocked", "none" if ok else "tail-diameter")
    logger.debug("cauchy_tail_certificate exit result=%r", result.as_dict())
    return result


def majorant_bound(label: str, observed: RatioMode, bound: RatioMode) -> MajorantBound:
    """Return finite majorant bound row."""
    logger.debug("majorant_bound entry label=%s", label)
    ok = ratio_shadow(observed) <= ratio_shadow(bound)
    result = MajorantBound(label, observed, bound, "bounded" if ok else "blocked", "none" if ok else "majorant-gap")
    logger.debug("majorant_bound exit result=%r", result.as_dict())
    return result


def nested_interval_certificate(label: str, intervals: tuple[CompletionInterval, ...]) -> NestedIntervalCertificate:
    """Certify finite nested intervals with nonincreasing widths."""
    logger.debug("nested_interval_certificate entry label=%s count=%d", label, len(intervals))
    if len(intervals) < 2:
        logger.error("nested_interval_certificate too few intervals")
        raise ValueError("at least two intervals required")
    nested = all(interval_refines(prev, cur) for prev, cur in zip(intervals, intervals[1:]))
    widths = tuple(item.width for item in intervals)
    shrinking = all(left >= right for left, right in zip(widths, widths[1:]))
    final_width = ratio_from_fraction(widths[-1])
    ok = nested and shrinking
    obstruction = "none" if ok else "not-nested" if not nested else "width-increase"
    result = NestedIntervalCertificate(label, len(intervals), final_width, "nested" if ok else "blocked", obstruction)
    logger.debug("nested_interval_certificate exit result=%r", result.as_dict())
    return result


def radius_guard(label: str, point: RatioMode, radius: RatioMode, strict: bool = True) -> RadiusGuard:
    """Return finite radius/domain guard for a series point."""
    logger.debug("radius_guard entry label=%s strict=%s", label, strict)
    value = abs(ratio_shadow(point))
    bound = ratio_shadow(radius)
    ok = value < bound if strict else value <= bound
    result = RadiusGuard(label, point, radius, "inside" if ok else "outside", "none" if ok else "radius-gap")
    logger.debug("radius_guard exit result=%r", result.as_dict())
    return result


def cauchy_tail_card(samples: tuple[RatioMode, ...], tolerance: RatioMode, tail: int) -> TheoremCard:
    """Return theorem card for finite Cauchy-tail stability."""
    logger.debug("cauchy_tail_card entry")
    cert = cauchy_tail_certificate(samples, tolerance, tail)
    result = TheoremCard("convergence-cauchy-tail", "finite", cert.status, cert.obstruction, (("max_distance", str(ratio_shadow(cert.max_distance))), ("tolerance", str(ratio_shadow(tolerance)))))
    logger.debug("cauchy_tail_card exit relation=%s", result.relation)
    return result


def majorant_bound_card(label: str, observed: RatioMode, bound: RatioMode) -> TheoremCard:
    """Return theorem card for finite majorant bound."""
    logger.debug("majorant_bound_card entry label=%s", label)
    row = majorant_bound(label, observed, bound)
    result = TheoremCard("convergence-majorant-bound", "finite", row.status, row.obstruction, (("observed", str(ratio_shadow(observed))), ("bound", str(ratio_shadow(bound)))))
    logger.debug("majorant_bound_card exit relation=%s", result.relation)
    return result


def nested_interval_card(label: str, intervals: tuple[CompletionInterval, ...]) -> TheoremCard:
    """Return theorem card for nested interval shrinkage."""
    logger.debug("nested_interval_card entry label=%s", label)
    cert = nested_interval_certificate(label, intervals)
    result = TheoremCard("convergence-nested-intervals", "finite", cert.status, cert.obstruction, (("intervals", str(cert.intervals)), ("final_width", str(ratio_shadow(cert.final_width)))))
    logger.debug("nested_interval_card exit relation=%s", result.relation)
    return result


def radius_guard_card(label: str, point: RatioMode, radius: RatioMode) -> TheoremCard:
    """Return theorem card for finite series radius guard."""
    logger.debug("radius_guard_card entry label=%s", label)
    guard = radius_guard(label, point, radius)
    result = TheoremCard("convergence-radius-guard", "finite", guard.status, guard.obstruction, (("point", str(ratio_shadow(point))), ("radius", str(ratio_shadow(radius)))))
    logger.debug("radius_guard_card exit relation=%s", result.relation)
    return result


def convergence_algebra_checklist() -> tuple[str, ...]:
    """Return convergence algebra acceptance checklist."""
    logger.debug("convergence_algebra_checklist entry")
    result = ("Cauchy tail certificate", "majorant bound row", "nested interval shrinkage", "series radius guard")
    logger.debug("convergence_algebra_checklist exit count=%d", len(result))
    return result
