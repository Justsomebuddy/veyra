"""Finite likelihood geometry and residual-family certificates for Veyra."""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import logging

from .model_diagnostics import ModelFitReport, ModelObservation, canonical_model_observations, model_fit_report
from .ratio import RatioMode, ratio_from_fraction, ratio_from_ints, ratio_shadow, subtract_ratios
from .statistics_concentration import bernoulli_likelihood_row

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class LikelihoodPoint:
    """One exact point on a finite likelihood grid."""

    label: str
    parameter: RatioMode
    likelihood: RatioMode

    def as_dict(self) -> dict[str, str]:
        """Return JSON-ready likelihood point."""
        logger.debug("LikelihoodPoint.as_dict entry label=%s", self.label)
        result = {"label": self.label, "parameter": str(ratio_shadow(self.parameter)), "likelihood": str(ratio_shadow(self.likelihood))}
        logger.debug("LikelihoodPoint.as_dict exit result=%r", result)
        return result


@dataclass(frozen=True)
class LikelihoodSegment:
    """Adjacent finite likelihood-grid segment with exact slope shadow."""

    left: str
    right: str
    parameter_gap: RatioMode
    likelihood_gap: RatioMode
    slope: RatioMode
    relation: str

    def as_dict(self) -> dict[str, str]:
        """Return JSON-ready likelihood segment."""
        logger.debug("LikelihoodSegment.as_dict entry left=%s right=%s", self.left, self.right)
        result = {"left": self.left, "right": self.right, "parameter_gap": str(ratio_shadow(self.parameter_gap)), "likelihood_gap": str(ratio_shadow(self.likelihood_gap)), "slope": str(ratio_shadow(self.slope)), "relation": self.relation}
        logger.debug("LikelihoodSegment.as_dict exit result=%r", result)
        return result


@dataclass(frozen=True)
class LikelihoodPeakCard:
    """Finite peak candidate for a likelihood grid."""

    label: str
    parameter: RatioMode
    likelihood: RatioMode
    status: str
    obstruction: str

    def as_dict(self) -> dict[str, str]:
        """Return JSON-ready peak card."""
        logger.debug("LikelihoodPeakCard.as_dict entry label=%s", self.label)
        result = {"label": self.label, "parameter": str(ratio_shadow(self.parameter)), "likelihood": str(ratio_shadow(self.likelihood)), "status": self.status, "obstruction": self.obstruction}
        logger.debug("LikelihoodPeakCard.as_dict exit result=%r", result)
        return result


@dataclass(frozen=True)
class DomainResidualCertificate:
    """Domain-specific residual-family certificate over a finite model report."""

    domain: str
    report: ModelFitReport
    status: str
    obstruction: str

    def as_dict(self) -> dict[str, object]:
        """Return JSON-ready domain residual certificate."""
        logger.debug("DomainResidualCertificate.as_dict entry domain=%s", self.domain)
        result = {"domain": self.domain, "rows": len(self.report.rows), "total_absolute_error": str(ratio_shadow(self.report.total_absolute_error)), "max_absolute_error": str(ratio_shadow(self.report.max_absolute_error)), "tolerance": str(ratio_shadow(self.report.tolerance)), "status": self.status, "obstruction": self.obstruction}
        logger.debug("DomainResidualCertificate.as_dict exit result=%r", result)
        return result


def likelihood_point(successes: int, trials: int, parameter: RatioMode, label: str | None = None) -> LikelihoodPoint:
    """Return one finite Bernoulli likelihood point."""
    logger.debug("likelihood_point entry successes=%d trials=%d parameter=%s", successes, trials, parameter.word)
    row = bernoulli_likelihood_row(successes, trials, parameter)
    name = label or f"p={ratio_shadow(parameter)}"
    result = LikelihoodPoint(name, parameter, row.likelihood)
    logger.debug("likelihood_point exit result=%r", result.as_dict())
    return result


def likelihood_grid(successes: int = 3, trials: int = 4, candidates: tuple[RatioMode, ...] | None = None) -> tuple[LikelihoodPoint, ...]:
    """Return a sorted finite likelihood grid."""
    logger.debug("likelihood_grid entry successes=%d trials=%d", successes, trials)
    params = candidates or (ratio_from_ints(1, 4), ratio_from_ints(1, 2), ratio_from_ints(3, 4))
    if not params:
        logger.error("likelihood_grid empty candidates")
        raise ValueError("likelihood grid needs candidates")
    ordered = tuple(sorted(params, key=ratio_shadow))
    result = tuple(likelihood_point(successes, trials, item) for item in ordered)
    logger.debug("likelihood_grid exit count=%d", len(result))
    return result


def finite_likelihood_segments(points: tuple[LikelihoodPoint, ...]) -> tuple[LikelihoodSegment, ...]:
    """Return exact adjacent segments on a finite likelihood grid."""
    logger.debug("finite_likelihood_segments entry count=%d", len(points))
    if len(points) < 2:
        logger.error("finite_likelihood_segments too few points=%d", len(points))
        raise ValueError("at least two likelihood points are required")
    segments: list[LikelihoodSegment] = []
    for left, right in zip(points, points[1:]):
        parameter_gap = subtract_ratios(right.parameter, left.parameter)
        gap = ratio_shadow(parameter_gap)
        if gap <= 0:
            logger.error("finite_likelihood_segments non-increasing parameter gap=%s", gap)
            raise ValueError("likelihood parameters must strictly increase")
        likelihood_gap = subtract_ratios(right.likelihood, left.likelihood)
        slope = ratio_from_fraction(ratio_shadow(likelihood_gap) / gap)
        relation = "rising" if ratio_shadow(likelihood_gap) > 0 else "falling" if ratio_shadow(likelihood_gap) < 0 else "flat"
        segments.append(LikelihoodSegment(left.label, right.label, parameter_gap, likelihood_gap, slope, relation))
    result = tuple(segments)
    logger.debug("finite_likelihood_segments exit count=%d", len(result))
    return result


def likelihood_peak_card(points: tuple[LikelihoodPoint, ...]) -> LikelihoodPeakCard:
    """Return finite likelihood peak card."""
    logger.debug("likelihood_peak_card entry count=%d", len(points))
    if not points:
        logger.error("likelihood_peak_card empty points")
        raise ValueError("peak card needs likelihood points")
    best_value = max(ratio_shadow(point.likelihood) for point in points)
    winners = tuple(point for point in points if ratio_shadow(point.likelihood) == best_value)
    winner = winners[0]
    status = "unique-peak" if len(winners) == 1 else "peak-tie"
    result = LikelihoodPeakCard(winner.label, winner.parameter, winner.likelihood, status, "none" if status == "unique-peak" else "peak-tie")
    logger.debug("likelihood_peak_card exit result=%r", result.as_dict())
    return result


def domain_residual_certificate(domain: str, observations: tuple[ModelObservation, ...], tolerance: RatioMode) -> DomainResidualCertificate:
    """Return one domain-specific finite residual-family certificate."""
    logger.debug("domain_residual_certificate entry domain=%s observations=%d", domain, len(observations))
    if not domain:
        logger.error("domain_residual_certificate empty domain")
        raise ValueError("domain must be nonempty")
    report = model_fit_report(f"{domain}-residual-family", observations, tolerance)
    status = "certified" if report.status == "fit" else "blocked"
    result = DomainResidualCertificate(domain, report, status, "none" if status == "certified" else report.obstruction)
    logger.debug("domain_residual_certificate exit result=%r", result.as_dict())
    return result


def residual_family_certificates() -> tuple[DomainResidualCertificate, ...]:
    """Return canonical domain residual-family certificates."""
    logger.debug("residual_family_certificates entry")
    motion = domain_residual_certificate("linear-motion", canonical_model_observations(), ratio_from_ints(1))
    sensor = domain_residual_certificate("sensor-spike", (ModelObservation("s0", ratio_from_ints(1), ratio_from_ints(1)), ModelObservation("s1", ratio_from_ints(2), ratio_from_ints(2)), ModelObservation("s2", ratio_from_ints(5), ratio_from_ints(2))), ratio_from_ints(1))
    result = (motion, sensor)
    logger.debug("residual_family_certificates exit count=%d", len(result))
    return result


def likelihood_geometry_checklist() -> tuple[str, ...]:
    """Return Sprint X5 acceptance checklist."""
    logger.debug("likelihood_geometry_checklist entry")
    result = ("likelihood geometry is a finite parameter grid", "adjacent grid segments carry exact slope shadows", "peak candidates are finite cards", "domain residual families certify or block model diagnostics")
    logger.debug("likelihood_geometry_checklist exit count=%d", len(result))
    return result


def likelihood_geometry_summary() -> dict[str, int]:
    """Return compact X5 likelihood/residual summary."""
    logger.debug("likelihood_geometry_summary entry")
    points = likelihood_grid(); segments = finite_likelihood_segments(points); certs = residual_family_certificates()
    result = {"likelihood_points": len(points), "segments": len(segments), "rising_segments": sum(item.relation == "rising" for item in segments), "residual_certificates": len(certs), "fit_domains": sum(item.status == "certified" for item in certs), "blocked_domains": sum(item.status == "blocked" for item in certs), "checklist": len(likelihood_geometry_checklist())}
    logger.debug("likelihood_geometry_summary exit result=%r", result)
    return result
