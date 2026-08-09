"""Statistics inference shadow seeds for Veyra."""

from __future__ import annotations

from dataclasses import dataclass
import logging

from .change import ratio_divide
from ..numbers.cyclic_probability_stats import SampleEcho, sample_mean
from ..geometry.theorems import TheoremCard
from .order import ratio_between
from .ratio import RatioMode, add_ratios, multiply_ratios, ratio_from_ints, ratio_shadow, subtract_ratios

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DistributionFamily:
    """Named finite distribution family with ratio parameters."""

    name: str
    parameters: tuple[tuple[str, RatioMode], ...]
    status: str

    def parameter_shadow(self, name: str) -> str:
        """Return exact string shadow for a named parameter."""
        logger.debug("DistributionFamily.parameter_shadow entry family=%s name=%s", self.name, name)
        for key, value in self.parameters:
            if key == name:
                result = str(ratio_shadow(value))
                logger.debug("DistributionFamily.parameter_shadow exit result=%s", result)
                return result
        logger.error("DistributionFamily.parameter_shadow missing name=%s", name)
        raise KeyError(name)


@dataclass(frozen=True)
class IntervalEstimate:
    """Finite interval estimate around a sample statistic."""

    center: RatioMode
    lower: RatioMode
    upper: RatioMode
    radius: RatioMode
    samples: int
    status: str


def sample_echo_from_ints(values: list[int]) -> SampleEcho:
    """Build nonempty sample echo from integer values."""
    logger.debug("sample_echo_from_ints entry values=%r", values)
    result = SampleEcho(tuple(ratio_from_ints(value) for value in values))
    logger.debug("sample_echo_from_ints exit count=%d", len(result.values))
    return result


def bernoulli_family(successes: int, trials: int) -> DistributionFamily:
    """Return Bernoulli/binomial one-parameter family shadow."""
    logger.debug("bernoulli_family entry successes=%d trials=%d", successes, trials)
    if trials <= 0 or successes < 0 or successes > trials:
        logger.error("bernoulli_family invalid successes=%d trials=%d", successes, trials)
        raise ValueError("successes must satisfy 0 <= successes <= trials and trials > 0")
    p = ratio_from_ints(successes, trials)
    variance = multiply_ratios(p, subtract_ratios(ratio_from_ints(1), p))
    result = DistributionFamily("bernoulli", (("p", p), ("variance", variance)), "finite-shadow")
    logger.debug("bernoulli_family exit p=%s variance=%s", p.word, variance.word)
    return result


def mean_interval(sample: SampleEcho, radius: RatioMode) -> IntervalEstimate:
    """Return sample-mean interval estimate with explicit radius."""
    logger.debug("mean_interval entry samples=%d radius=%s", len(sample.values), radius.word)
    if ratio_shadow(radius) < 0:
        logger.error("mean_interval negative radius=%s", radius.word)
        raise ValueError("radius must be nonnegative")
    center = sample_mean(sample)
    result = IntervalEstimate(center, subtract_ratios(center, radius), add_ratios(center, radius), radius, len(sample.values), "finite-shadow")
    logger.debug("mean_interval exit center=%s lower=%s upper=%s", center.word, result.lower.word, result.upper.word)
    return result


def interval_contains_shadow(interval: IntervalEstimate, value: RatioMode) -> bool:
    """Return whether a ratio shadow lies inside the estimate interval."""
    logger.debug("interval_contains_shadow entry samples=%d value=%s", interval.samples, value.word)
    result = ratio_between(value, interval.lower, interval.upper)
    logger.debug("interval_contains_shadow exit result=%s", result)
    return result


def hypothesis_mean_card(sample: SampleEcho, null_mean: RatioMode, tolerance: RatioMode) -> TheoremCard:
    """Check a finite sample-mean hypothesis with explicit tolerance."""
    logger.debug("hypothesis_mean_card entry samples=%d null=%s tolerance=%s", len(sample.values), null_mean.word, tolerance.word)
    if ratio_shadow(tolerance) < 0:
        logger.error("hypothesis_mean_card negative tolerance=%s", tolerance.word)
        raise ValueError("tolerance must be nonnegative")
    mean = sample_mean(sample)
    delta = subtract_ratios(mean, null_mean)
    magnitude = ratio_from_ints(abs(ratio_shadow(delta).numerator), abs(ratio_shadow(delta).denominator))
    accepted = ratio_shadow(magnitude) <= ratio_shadow(tolerance)
    result = TheoremCard("statistics-mean-hypothesis", "finite", "accepted" if accepted else "rejected", "none" if accepted else "mean-shift", (("mean", str(ratio_shadow(mean))), ("null", str(ratio_shadow(null_mean))), ("delta", str(ratio_shadow(delta)))))
    logger.debug("hypothesis_mean_card exit relation=%s", result.relation)
    return result


def standard_error_shadow(variance: RatioMode, samples: int) -> RatioMode:
    """Return variance/n seed used before completing square-root uncertainty."""
    logger.debug("standard_error_shadow entry variance=%s samples=%d", variance.word, samples)
    if samples <= 0:
        logger.error("standard_error_shadow invalid samples=%d", samples)
        raise ValueError("samples must be positive")
    result = ratio_divide(variance, ratio_from_ints(samples))
    logger.debug("standard_error_shadow exit result=%s", result.word)
    return result


def statistics_inference_checklist() -> tuple[str, ...]:
    """Return acceptance checklist for statistics inference seeds."""
    logger.debug("statistics_inference_checklist entry")
    result = ("distribution-family parameter", "mean interval estimate", "finite hypothesis card", "variance-per-sample uncertainty seed")
    logger.debug("statistics_inference_checklist exit count=%d", len(result))
    return result
