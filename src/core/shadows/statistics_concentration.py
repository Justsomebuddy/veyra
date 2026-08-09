"""Finite concentration and likelihood geometry seeds for Veyra statistics."""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import logging

from .change import ratio_divide
from ..geometry.theorems import TheoremCard
from .ratio import RatioMode, multiply_ratios, ratio_from_fraction, ratio_from_ints, ratio_shadow, subtract_ratios

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ConcentrationBound:
    """Finite concentration row with exact rational evidence."""

    method: str
    samples: int
    radius: RatioMode
    evidence: RatioMode
    relation: str
    obstruction: str

    def as_dict(self) -> dict[str, object]:
        """Return JSON-ready concentration row."""
        logger.debug("ConcentrationBound.as_dict entry method=%s", self.method)
        result = {"method": self.method, "samples": self.samples, "radius": str(ratio_shadow(self.radius)), "evidence": str(ratio_shadow(self.evidence)), "relation": self.relation, "obstruction": self.obstruction}
        logger.debug("ConcentrationBound.as_dict exit result=%r", result)
        return result


@dataclass(frozen=True)
class BernoulliLikelihoodRow:
    """Exact Bernoulli likelihood row for a candidate parameter."""

    successes: int
    trials: int
    p: RatioMode
    likelihood: RatioMode
    relation: str

    def as_dict(self) -> dict[str, object]:
        """Return JSON-ready likelihood row."""
        logger.debug("BernoulliLikelihoodRow.as_dict entry successes=%d trials=%d", self.successes, self.trials)
        result = {"successes": self.successes, "trials": self.trials, "p": str(ratio_shadow(self.p)), "likelihood": str(ratio_shadow(self.likelihood)), "relation": self.relation}
        logger.debug("BernoulliLikelihoodRow.as_dict exit result=%r", result)
        return result


@dataclass(frozen=True)
class DecisionErrorRow:
    """Finite threshold-decision row naming FP/FN outcomes."""

    score: RatioMode
    threshold: RatioMode
    actual_shift: bool
    decision: str
    outcome: str
    obstruction: str

    def as_dict(self) -> dict[str, object]:
        """Return JSON-ready decision-error row."""
        logger.debug("DecisionErrorRow.as_dict entry decision=%s", self.decision)
        result = {"score": str(ratio_shadow(self.score)), "threshold": str(ratio_shadow(self.threshold)), "actual_shift": self.actual_shift, "decision": self.decision, "outcome": self.outcome, "obstruction": self.obstruction}
        logger.debug("DecisionErrorRow.as_dict exit result=%r", result)
        return result


def _ratio_power(base: RatioMode, exponent: int) -> RatioMode:
    """Return exact nonnegative integer power of a ratio."""
    logger.debug("_ratio_power entry base=%s exponent=%d", base.word, exponent)
    if exponent < 0:
        logger.error("_ratio_power negative exponent=%d", exponent)
        raise ValueError("exponent must be nonnegative")
    result = ratio_from_ints(1)
    for _ in range(exponent):
        result = multiply_ratios(result, base)
    logger.debug("_ratio_power exit result=%s", result.word)
    return result


def chebyshev_mean_bound(variance: RatioMode, samples: int, radius: RatioMode) -> ConcentrationBound:
    """Return finite Chebyshev-style bound `variance/(n·radius²)`."""
    logger.debug("chebyshev_mean_bound entry variance=%s samples=%d radius=%s", variance.word, samples, radius.word)
    if samples <= 0 or ratio_shadow(radius) <= 0 or ratio_shadow(variance) < 0:
        logger.error("chebyshev_mean_bound invalid variance=%s samples=%d radius=%s", variance.word, samples, radius.word)
        raise ValueError("variance >= 0, samples > 0, and radius > 0 are required")
    denom = multiply_ratios(ratio_from_ints(samples), multiply_ratios(radius, radius))
    bound = ratio_divide(variance, denom)
    relation = "informative" if ratio_shadow(bound) <= 1 else "loose"
    result = ConcentrationBound("chebyshev", samples, radius, bound, relation, "none" if relation == "informative" else "bound-over-one")
    logger.debug("chebyshev_mean_bound exit relation=%s evidence=%s", result.relation, result.evidence.word)
    return result


def hoeffding_exponent_guard(samples: int, radius: RatioMode, width: RatioMode) -> ConcentrationBound:
    """Return finite Hoeffding-style exponent guard `2n·radius²/width²`."""
    logger.debug("hoeffding_exponent_guard entry samples=%d radius=%s width=%s", samples, radius.word, width.word)
    if samples <= 0 or ratio_shadow(radius) <= 0 or ratio_shadow(width) <= 0:
        logger.error("hoeffding_exponent_guard invalid samples=%d radius=%s width=%s", samples, radius.word, width.word)
        raise ValueError("samples, radius, and width must be positive")
    numerator = multiply_ratios(ratio_from_ints(2 * samples), multiply_ratios(radius, radius))
    exponent = ratio_divide(numerator, multiply_ratios(width, width))
    result = ConcentrationBound("hoeffding-exponent", samples, radius, exponent, "guarded", "tail-exponential-shadow-deferred")
    logger.debug("hoeffding_exponent_guard exit exponent=%s", result.evidence.word)
    return result


def concentration_bound_card(bound: ConcentrationBound) -> TheoremCard:
    """Return theorem card for a finite concentration row."""
    logger.debug("concentration_bound_card entry method=%s", bound.method)
    result = TheoremCard(f"statistics-{bound.method}", "finite", bound.relation, bound.obstruction, (("samples", str(bound.samples)), ("radius", str(ratio_shadow(bound.radius))), ("evidence", str(ratio_shadow(bound.evidence)))))
    logger.debug("concentration_bound_card exit relation=%s", result.relation)
    return result


def bernoulli_likelihood_row(successes: int, trials: int, p: RatioMode) -> BernoulliLikelihoodRow:
    """Return exact Bernoulli likelihood `p^k(1-p)^(n-k)`."""
    logger.debug("bernoulli_likelihood_row entry successes=%d trials=%d p=%s", successes, trials, p.word)
    p_shadow = ratio_shadow(p)
    if trials <= 0 or successes < 0 or successes > trials or not Fraction(0) <= p_shadow <= Fraction(1):
        logger.error("bernoulli_likelihood_row invalid successes=%d trials=%d p=%s", successes, trials, p.word)
        raise ValueError("valid Bernoulli counts and 0 <= p <= 1 are required")
    q = subtract_ratios(ratio_from_ints(1), p)
    likelihood = multiply_ratios(_ratio_power(p, successes), _ratio_power(q, trials - successes))
    result = BernoulliLikelihoodRow(successes, trials, p, likelihood, "finite-shadow")
    logger.debug("bernoulli_likelihood_row exit likelihood=%s", result.likelihood.word)
    return result


def likelihood_ratio_card(left: BernoulliLikelihoodRow, right: BernoulliLikelihoodRow) -> TheoremCard:
    """Compare two finite likelihood rows by exact ratio shadow."""
    logger.debug("likelihood_ratio_card entry left=%s right=%s", left.likelihood.word, right.likelihood.word)
    ratio = ratio_divide(left.likelihood, right.likelihood)
    shadow = ratio_shadow(ratio)
    relation = "left-preferred" if shadow > 1 else "right-preferred" if shadow < 1 else "tie"
    result = TheoremCard("statistics-likelihood-ratio", "finite", relation, "none", (("left_p", str(ratio_shadow(left.p))), ("right_p", str(ratio_shadow(right.p))), ("ratio", str(shadow))))
    logger.debug("likelihood_ratio_card exit relation=%s ratio=%s", relation, shadow)
    return result


def decision_error_row(score: RatioMode, threshold: RatioMode, actual_shift: bool) -> DecisionErrorRow:
    """Classify a finite threshold decision as TP/TN/FP/FN."""
    logger.debug("decision_error_row entry score=%s threshold=%s actual_shift=%s", score.word, threshold.word, actual_shift)
    if ratio_shadow(score) < 0 or ratio_shadow(threshold) < 0:
        logger.error("decision_error_row negative score=%s threshold=%s", score.word, threshold.word)
        raise ValueError("score and threshold must be nonnegative")
    rejects = ratio_shadow(score) >= ratio_shadow(threshold)
    outcome = "true-positive" if rejects and actual_shift else "false-positive" if rejects else "false-negative" if actual_shift else "true-negative"
    result = DecisionErrorRow(score, threshold, actual_shift, "reject" if rejects else "accept", outcome, "decision-mismatch" if outcome.startswith("false") else "none")
    logger.debug("decision_error_row exit outcome=%s", result.outcome)
    return result


def statistics_concentration_checklist() -> tuple[str, ...]:
    """Return D6 statistics concentration and likelihood checklist."""
    logger.debug("statistics_concentration_checklist entry")
    result = ("Chebyshev mean bound card", "Hoeffding exponent guard", "Bernoulli likelihood row", "likelihood ratio card", "false-positive/false-negative rows")
    logger.debug("statistics_concentration_checklist exit count=%d", len(result))
    return result
