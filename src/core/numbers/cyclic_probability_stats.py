"""Cyclic, probability, and statistics seeds for Veyra school coverage."""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import logging

from ..shadows.change import ratio_divide
from ..geometry.theorems import TheoremCard
from ..shadows.ratio import RatioMode, add_ratios, multiply_ratios, ratio_from_fraction, ratio_from_ints, ratio_shadow, subtract_ratios

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CyclicPhase:
    """Finite cyclic phase event with exact integer modulus."""

    index: int
    modulus: int
    label: str = "phase"

    def __post_init__(self) -> None:
        """Validate and canonicalize phase."""
        logger.debug("CyclicPhase.__post_init__ entry index=%d modulus=%d", self.index, self.modulus)
        if self.modulus <= 0:
            logger.error("CyclicPhase invalid modulus=%d", self.modulus)
            raise ValueError("modulus must be positive")
        object.__setattr__(self, "index", self.index % self.modulus)
        logger.debug("CyclicPhase.__post_init__ exit index=%d", self.index)


@dataclass(frozen=True)
class WeightedOutcome:
    """Finite observer outcome with integer weight and ratio score."""

    name: str
    weight: int
    score: RatioMode


@dataclass(frozen=True)
class FiniteDistribution:
    """Finite weighted observer distribution."""

    outcomes: tuple[WeightedOutcome, ...]

    def __post_init__(self) -> None:
        """Validate nonempty nonnegative finite distribution."""
        logger.debug("FiniteDistribution.__post_init__ entry count=%d", len(self.outcomes))
        if not self.outcomes or any(item.weight < 0 for item in self.outcomes) or self.total_weight <= 0:
            logger.error("FiniteDistribution invalid distribution")
            raise ValueError("distribution needs nonnegative weights and positive total")
        logger.debug("FiniteDistribution.__post_init__ exit total=%d", self.total_weight)

    @property
    def total_weight(self) -> int:
        """Return total outcome weight."""
        logger.debug("FiniteDistribution.total_weight entry")
        result = sum(item.weight for item in self.outcomes)
        logger.debug("FiniteDistribution.total_weight exit result=%d", result)
        return result


@dataclass(frozen=True)
class SampleEcho:
    """Finite statistical sample as ratio echoes."""

    values: tuple[RatioMode, ...]

    def __post_init__(self) -> None:
        """Validate nonempty sample."""
        logger.debug("SampleEcho.__post_init__ entry count=%d", len(self.values))
        if not self.values:
            logger.error("SampleEcho empty")
            raise ValueError("sample must be nonempty")
        logger.debug("SampleEcho.__post_init__ exit")


def phase_advance(phase: CyclicPhase, step: int) -> CyclicPhase:
    """Advance phase by integer cyclic steps."""
    logger.debug("phase_advance entry phase=%d/%d step=%d", phase.index, phase.modulus, step)
    result = CyclicPhase(phase.index + step, phase.modulus, phase.label)
    logger.debug("phase_advance exit index=%d", result.index)
    return result


def phase_distance(left: CyclicPhase, right: CyclicPhase) -> int:
    """Return shortest cyclic step distance."""
    logger.debug("phase_distance entry left=%d right=%d", left.index, right.index)
    if left.modulus != right.modulus:
        logger.error("phase_distance modulus mismatch")
        raise ValueError("phases must share modulus")
    raw = abs(left.index - right.index)
    result = min(raw, left.modulus - raw)
    logger.debug("phase_distance exit result=%d", result)
    return result


def cyclic_chord_echo(left: CyclicPhase, right: CyclicPhase) -> RatioMode:
    """Return rational cyclic shell echo symmetric under phase complement."""
    logger.debug("cyclic_chord_echo entry")
    d = phase_distance(left, right)
    n = left.modulus
    result = ratio_from_fraction(Fraction(4 * d * (n - d), n * n))
    logger.debug("cyclic_chord_echo exit result=%s", result.word)
    return result


def phase_period_card(phase: CyclicPhase) -> TheoremCard:
    """Card proving one full cycle returns to same phase."""
    logger.debug("phase_period_card entry phase=%d/%d", phase.index, phase.modulus)
    returned = phase_advance(phase, phase.modulus)
    relation = "periodic" if returned.index == phase.index else "broken"
    result = TheoremCard("cyclic-period", "exact", relation, "none" if relation == "periodic" else "phase-mismatch", (("phase", str(phase.index)), ("modulus", str(phase.modulus))))
    logger.debug("phase_period_card exit relation=%s", relation)
    return result


def chord_symmetry_card(anchor: CyclicPhase, phase: CyclicPhase) -> TheoremCard:
    """Card proving chord echo symmetry around an anchor phase."""
    logger.debug("chord_symmetry_card entry")
    mirror = phase_advance(anchor, -phase_distance(anchor, phase))
    left = cyclic_chord_echo(anchor, phase)
    right = cyclic_chord_echo(anchor, mirror)
    relation = "symmetric" if ratio_shadow(left) == ratio_shadow(right) else "broken"
    result = TheoremCard("chord-symmetry", "exact", relation, "none" if relation == "symmetric" else "chord-mismatch", (("left", str(ratio_shadow(left))), ("right", str(ratio_shadow(right)))))
    logger.debug("chord_symmetry_card exit relation=%s", relation)
    return result


def probability_of(distribution: FiniteDistribution, names: frozenset[str]) -> RatioMode:
    """Return exact probability of named outcomes."""
    logger.debug("probability_of entry names=%r", sorted(names))
    known = {item.name for item in distribution.outcomes}
    if not names <= known:
        logger.error("probability_of unknown outcomes=%r", sorted(names - known))
        raise ValueError("unknown outcome name")
    weight = sum(item.weight for item in distribution.outcomes if item.name in names)
    result = ratio_from_ints(weight, distribution.total_weight)
    logger.debug("probability_of exit result=%s", result.word)
    return result


def expectation(distribution: FiniteDistribution) -> RatioMode:
    """Return exact weighted expectation of outcome scores."""
    logger.debug("expectation entry")
    total = ratio_from_ints(0)
    for item in distribution.outcomes:
        total = add_ratios(total, multiply_ratios(item.score, ratio_from_ints(item.weight)))
    result = ratio_divide(total, ratio_from_ints(distribution.total_weight))
    logger.debug("expectation exit result=%s", result.word)
    return result


def probability_complement_card(distribution: FiniteDistribution, names: frozenset[str]) -> TheoremCard:
    """Card proving event and complement probabilities sum to one."""
    logger.debug("probability_complement_card entry")
    known = frozenset(item.name for item in distribution.outcomes)
    event = probability_of(distribution, names)
    complement = probability_of(distribution, known - names)
    total = add_ratios(event, complement)
    relation = "complete" if ratio_shadow(total) == 1 else "broken"
    result = TheoremCard("probability-complement", "exact", relation, "none" if relation == "complete" else "mass-gap", (("event", str(ratio_shadow(event))), ("complement", str(ratio_shadow(complement)))))
    logger.debug("probability_complement_card exit relation=%s", relation)
    return result


def sample_mean(sample: SampleEcho) -> RatioMode:
    """Return exact sample mean."""
    logger.debug("sample_mean entry count=%d", len(sample.values))
    total = ratio_from_ints(0)
    for value in sample.values:
        total = add_ratios(total, value)
    result = ratio_divide(total, ratio_from_ints(len(sample.values)))
    logger.debug("sample_mean exit result=%s", result.word)
    return result


def sample_variance(sample: SampleEcho) -> RatioMode:
    """Return exact population variance echo."""
    logger.debug("sample_variance entry")
    mean = sample_mean(sample)
    total = ratio_from_ints(0)
    for value in sample.values:
        delta = subtract_ratios(value, mean)
        total = add_ratios(total, multiply_ratios(delta, delta))
    result = ratio_divide(total, ratio_from_ints(len(sample.values)))
    logger.debug("sample_variance exit result=%s", result.word)
    return result


def mean_balance_card(sample: SampleEcho) -> TheoremCard:
    """Card proving deviations from sample mean sum to zero."""
    logger.debug("mean_balance_card entry")
    mean = sample_mean(sample)
    total = ratio_from_ints(0)
    for value in sample.values:
        total = add_ratios(total, subtract_ratios(value, mean))
    relation = "balanced" if ratio_shadow(total) == 0 else "broken"
    result = TheoremCard("mean-balance", "exact", relation, "none" if relation == "balanced" else "deviation-gap", (("mean", str(ratio_shadow(mean))), ("deviation_sum", str(ratio_shadow(total)))))
    logger.debug("mean_balance_card exit relation=%s", relation)
    return result
