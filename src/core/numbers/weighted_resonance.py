"""Weighted tact-specific defect resonance for Veyra mode shadows."""

from __future__ import annotations

from dataclasses import dataclass
import logging

from .modes import Mode, repeat_mode
from .resonance import rotate_mode

logger = logging.getLogger(__name__)

CostMap = dict[tuple[str, str], float]


@dataclass(frozen=True)
class WeightedDefect:
    """One directed tact mismatch with a nonnegative cost."""

    index: int
    expected: str
    actual: str
    cost: float


@dataclass(frozen=True)
class WeightedPhaseMatch:
    """Weighted phase match between expected repetition and rotated whole."""

    offset: int
    rotated: Mode
    expected: Mode
    defects: tuple[WeightedDefect, ...]
    total_cost: float

    @property
    def defect_count(self) -> int:
        """Return number of mismatched positions."""
        logger.debug("WeightedPhaseMatch.defect_count entry offset=%d", self.offset)
        result = len(self.defects)
        logger.debug("WeightedPhaseMatch.defect_count exit result=%d", result)
        return result


@dataclass(frozen=True)
class WeightedResonanceProfile:
    """Best weighted approximate resonance profile."""

    part: Mode
    whole: Mode
    budget: float
    resonates: bool
    obstruction: str
    best: WeightedPhaseMatch | None


def tact_cost(expected: str, actual: str, costs: CostMap, default_cost: float = 1.0) -> float:
    """Return directed mismatch cost, with zero cost for exact match."""
    logger.debug("tact_cost entry expected=%r actual=%r default=%s", expected, actual, default_cost)
    if default_cost < 0:
        logger.error("tact_cost invalid default_cost=%s", default_cost)
        raise ValueError("default_cost must be nonnegative")
    if expected == actual:
        logger.debug("tact_cost exit exact=0")
        return 0.0
    result = costs.get((expected, actual), default_cost)
    if result < 0:
        logger.error("tact_cost negative result=%s pair=%r", result, (expected, actual))
        raise ValueError("costs must be nonnegative")
    logger.debug("tact_cost exit result=%s", result)
    return result


def weighted_defects(expected: Mode, actual: Mode, costs: CostMap, default_cost: float = 1.0) -> tuple[WeightedDefect, ...]:
    """Return weighted defects between equal-length modes."""
    logger.debug("weighted_defects entry expected=%s actual=%s", expected.word, actual.word)
    if expected.length != actual.length:
        logger.error("weighted_defects length mismatch expected=%d actual=%d", expected.length, actual.length)
        raise ValueError("weighted_defects requires equal-length modes")
    result = tuple(
        WeightedDefect(index, left, right, tact_cost(left, right, costs, default_cost))
        for index, (left, right) in enumerate(zip(expected.tacts, actual.tacts, strict=True))
        if left != right
    )
    logger.debug("weighted_defects exit count=%d", len(result))
    return result


def weighted_phase_matches(part: Mode, whole: Mode, costs: CostMap, default_cost: float = 1.0) -> tuple[WeightedPhaseMatch, ...]:
    """Return all weighted phase matches if part length tiles whole length."""
    logger.debug("weighted_phase_matches entry part=%s whole=%s", part.word, whole.word)
    if part.length == 0 or whole.length % part.length != 0:
        logger.debug("weighted_phase_matches exit empty")
        return ()
    expected = repeat_mode(part, whole.length // part.length)
    matches: list[WeightedPhaseMatch] = []
    for offset in range(whole.length if whole.length else 1):
        rotated = rotate_mode(whole, offset)
        defects = weighted_defects(expected, rotated, costs, default_cost)
        matches.append(WeightedPhaseMatch(offset, rotated, expected, defects, sum(item.cost for item in defects)))
    result = tuple(sorted(matches, key=lambda item: (item.total_cost, item.defect_count, item.offset)))
    logger.debug("weighted_phase_matches exit count=%d", len(result))
    return result


def weighted_resonance_profile(part: Mode, whole: Mode, budget: float, costs: CostMap, default_cost: float = 1.0) -> WeightedResonanceProfile:
    """Return best weighted approximate cyclic resonance profile."""
    logger.debug("weighted_resonance_profile entry part=%s whole=%s budget=%s", part.word, whole.word, budget)
    if budget < 0:
        logger.error("weighted_resonance_profile invalid budget=%s", budget)
        raise ValueError("budget must be nonnegative")
    if part.length == 0:
        return WeightedResonanceProfile(part, whole, budget, False, "silent-part", None)
    if whole.length % part.length != 0:
        return WeightedResonanceProfile(part, whole, budget, False, "length-obstruction", None)
    matches = weighted_phase_matches(part, whole, costs, default_cost)
    best = matches[0] if matches else None
    if best is None:
        result = WeightedResonanceProfile(part, whole, budget, False, "pattern-obstruction", None)
    elif best.total_cost == 0:
        result = WeightedResonanceProfile(part, whole, budget, True, "none", best)
    elif best.total_cost <= budget:
        result = WeightedResonanceProfile(part, whole, budget, True, "weighted-defect", best)
    else:
        result = WeightedResonanceProfile(part, whole, budget, False, "over-budget", best)
    logger.debug("weighted_resonance_profile exit result=%r", result)
    return result


def weighted_cyclic_resonates(part: Mode, whole: Mode, budget: float, costs: CostMap, default_cost: float = 1.0) -> bool:
    """Return True iff weighted defect cost fits budget."""
    logger.debug("weighted_cyclic_resonates entry part=%s whole=%s budget=%s", part.word, whole.word, budget)
    result = weighted_resonance_profile(part, whole, budget, costs, default_cost).resonates
    logger.debug("weighted_cyclic_resonates exit result=%s", result)
    return result
