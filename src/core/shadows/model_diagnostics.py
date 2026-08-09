"""Finite model diagnostic certificates for Veyra science rows."""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import logging

from ..geometry.theorems import TheoremCard
from .ratio import RatioMode, add_ratios, ratio_from_fraction, ratio_from_ints, ratio_shadow, subtract_ratios

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ModelObservation:
    """One observed/predicted exact model point."""

    label: str
    observed: RatioMode
    predicted: RatioMode

    def __post_init__(self) -> None:
        """Validate nonempty observation label."""
        logger.debug("ModelObservation.__post_init__ entry label=%s", self.label)
        if not self.label:
            logger.error("ModelObservation empty label")
            raise ValueError("observation label must be nonempty")
        logger.debug("ModelObservation.__post_init__ exit observed=%s predicted=%s", self.observed.word, self.predicted.word)


@dataclass(frozen=True)
class ResidualRow:
    """Finite residual row against an explicit tolerance."""

    label: str
    residual: RatioMode
    absolute_residual: RatioMode
    tolerance: RatioMode
    status: str
    obstruction: str

    def as_dict(self) -> dict[str, object]:
        """Return JSON-ready residual row."""
        logger.debug("ResidualRow.as_dict entry label=%s", self.label)
        result = {"label": self.label, "residual": str(ratio_shadow(self.residual)), "absolute_residual": str(ratio_shadow(self.absolute_residual)), "tolerance": str(ratio_shadow(self.tolerance)), "status": self.status, "obstruction": self.obstruction}
        logger.debug("ResidualRow.as_dict exit result=%r", result)
        return result


@dataclass(frozen=True)
class ModelFitReport:
    """Finite model-fit report with residual aggregates."""

    label: str
    rows: tuple[ResidualRow, ...]
    total_absolute_error: RatioMode
    max_absolute_error: RatioMode
    tolerance: RatioMode
    status: str
    obstruction: str

    def as_dict(self) -> dict[str, object]:
        """Return JSON-ready model-fit report."""
        logger.debug("ModelFitReport.as_dict entry label=%s", self.label)
        result = {"label": self.label, "rows": len(self.rows), "total_absolute_error": str(ratio_shadow(self.total_absolute_error)), "max_absolute_error": str(ratio_shadow(self.max_absolute_error)), "tolerance": str(ratio_shadow(self.tolerance)), "status": self.status, "obstruction": self.obstruction}
        logger.debug("ModelFitReport.as_dict exit result=%r", result)
        return result


@dataclass(frozen=True)
class ModelComparisonRow:
    """Finite comparison between candidate and baseline model fits."""

    label: str
    candidate_error: RatioMode
    baseline_error: RatioMode
    status: str
    obstruction: str

    def as_dict(self) -> dict[str, object]:
        """Return JSON-ready model comparison row."""
        logger.debug("ModelComparisonRow.as_dict entry label=%s", self.label)
        result = {"label": self.label, "candidate_error": str(ratio_shadow(self.candidate_error)), "baseline_error": str(ratio_shadow(self.baseline_error)), "status": self.status, "obstruction": self.obstruction}
        logger.debug("ModelComparisonRow.as_dict exit result=%r", result)
        return result


def absolute_ratio(value: RatioMode) -> RatioMode:
    """Return absolute value of a ratio shadow."""
    logger.debug("absolute_ratio entry value=%s", value.word)
    result = ratio_from_fraction(abs(ratio_shadow(value)))
    logger.debug("absolute_ratio exit result=%s", result.word)
    return result


def residual_row(observation: ModelObservation, tolerance: RatioMode) -> ResidualRow:
    """Return residual diagnostics for one observation."""
    logger.debug("residual_row entry label=%s", observation.label)
    residual = subtract_ratios(observation.observed, observation.predicted)
    absolute = absolute_ratio(residual)
    ok = ratio_shadow(absolute) <= ratio_shadow(tolerance)
    result = ResidualRow(observation.label, residual, absolute, tolerance, "within-band" if ok else "outlier", "none" if ok else "residual-outlier")
    logger.debug("residual_row exit result=%r", result.as_dict())
    return result


def model_fit_report(label: str, observations: tuple[ModelObservation, ...], tolerance: RatioMode) -> ModelFitReport:
    """Build finite residual aggregate report."""
    logger.debug("model_fit_report entry label=%s count=%d", label, len(observations))
    if not observations:
        logger.error("model_fit_report empty observations")
        raise ValueError("model fit needs observations")
    rows = tuple(residual_row(item, tolerance) for item in observations)
    total = ratio_from_ints(0)
    for row in rows:
        total = add_ratios(total, row.absolute_residual)
    max_error = ratio_from_fraction(max((ratio_shadow(row.absolute_residual) for row in rows), default=Fraction(0)))
    ok = all(row.status == "within-band" for row in rows)
    result = ModelFitReport(label, rows, total, max_error, tolerance, "fit" if ok else "blocked", "none" if ok else "residual-outlier")
    logger.debug("model_fit_report exit result=%r", result.as_dict())
    return result


def compare_model_reports(label: str, candidate: ModelFitReport, baseline: ModelFitReport) -> ModelComparisonRow:
    """Compare finite model reports by total absolute error."""
    logger.debug("compare_model_reports entry label=%s", label)
    improved = ratio_shadow(candidate.total_absolute_error) < ratio_shadow(baseline.total_absolute_error)
    result = ModelComparisonRow(label, candidate.total_absolute_error, baseline.total_absolute_error, "improved" if improved else "not-improved", "none" if improved else "no-error-drop")
    logger.debug("compare_model_reports exit result=%r", result.as_dict())
    return result


def canonical_model_observations() -> tuple[ModelObservation, ...]:
    """Return canonical finite candidate-model fixture."""
    logger.debug("canonical_model_observations entry")
    result = (ModelObservation("p0", ratio_from_ints(1), ratio_from_ints(1)), ModelObservation("p1", ratio_from_ints(9, 4), ratio_from_ints(2)), ModelObservation("p2", ratio_from_ints(11, 4), ratio_from_ints(3)))
    logger.debug("canonical_model_observations exit count=%d", len(result))
    return result


def baseline_model_observations() -> tuple[ModelObservation, ...]:
    """Return rough baseline fixture for model comparison."""
    logger.debug("baseline_model_observations entry")
    result = (ModelObservation("p0", ratio_from_ints(1), ratio_from_ints(0)), ModelObservation("p1", ratio_from_ints(9, 4), ratio_from_ints(2)), ModelObservation("p2", ratio_from_ints(11, 4), ratio_from_ints(4)))
    logger.debug("baseline_model_observations exit count=%d", len(result))
    return result


def anomaly_obstruction_card() -> TheoremCard:
    """Return finite residual outlier obstruction card."""
    logger.debug("anomaly_obstruction_card entry")
    row = residual_row(ModelObservation("spike", ratio_from_ints(5), ratio_from_ints(2)), ratio_from_ints(1))
    result = TheoremCard("model-anomaly-obstruction", "finite", "blocked" if row.status == "outlier" else "unexpected", row.obstruction, (("residual", str(ratio_shadow(row.residual))), ("tolerance", str(ratio_shadow(row.tolerance)))))
    logger.debug("anomaly_obstruction_card exit relation=%s", result.relation)
    return result


def model_diagnostics_checklist() -> tuple[str, ...]:
    """Return finite model-diagnostics checklist."""
    logger.debug("model_diagnostics_checklist entry")
    result = ("finite residual rows", "aggregate fit report", "baseline model comparison", "anomaly obstruction card")
    logger.debug("model_diagnostics_checklist exit count=%d", len(result))
    return result
