"""Context-derived tact similarity and defect costs for Veyra modes."""

from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Iterable

from .modes import Mode
from .weighted_resonance import CostMap

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class TactAura:
    """External shadow of a tact by surrounding cyclic context marks."""

    tact: str
    marks: frozenset[str]


@dataclass(frozen=True)
class AuraMark:
    """Structured aura mark before external string rendering."""

    side: str
    distance: int
    tact: str

    def text(self) -> str:
        """Return legacy text shadow for this structured mark."""
        logger.debug("AuraMark.text entry mark=%r", self)
        result = f"{self.side}{self.distance}:{self.tact}"
        logger.debug("AuraMark.text exit result=%s", result)
        return result


@dataclass(frozen=True)
class TactAuraEcho:
    """Internal tact aura echo object with structured context marks."""

    tact: str
    marks: frozenset[AuraMark]

    def text_marks(self) -> frozenset[str]:
        """Return legacy string-mark shadow of the aura echo."""
        logger.debug("TactAuraEcho.text_marks entry tact=%s", self.tact)
        result = frozenset(mark.text() for mark in self.marks)
        logger.debug("TactAuraEcho.text_marks exit count=%d", len(result))
        return result


def cyclic_tact_aura_echoes(modes: Iterable[Mode], alphabet: Iterable[str] = (), radius: int = 1) -> dict[str, TactAuraEcho]:
    """Build internal tact aura echoes from cyclic left/right neighborhoods."""
    logger.debug("cyclic_tact_aura_echoes entry radius=%d", radius)
    if radius < 1:
        logger.error("cyclic_tact_aura_echoes invalid radius=%d", radius)
        raise ValueError("radius must be positive")
    marks: dict[str, set[AuraMark]] = {tact: set() for tact in alphabet}
    for mode in modes:
        if mode.length == 0:
            continue
        for index, tact in enumerate(mode.tacts):
            tact_marks = marks.setdefault(tact, set())
            for step in range(1, radius + 1):
                tact_marks.add(AuraMark("L", step, mode.tacts[(index - step) % mode.length]))
                tact_marks.add(AuraMark("R", step, mode.tacts[(index + step) % mode.length]))
    result = {tact: TactAuraEcho(tact, frozenset(values)) for tact, values in sorted(marks.items())}
    logger.debug("cyclic_tact_aura_echoes exit count=%d", len(result))
    return result


def cyclic_tact_auras(modes: Iterable[Mode], alphabet: Iterable[str] = (), radius: int = 1) -> dict[str, TactAura]:
    """Build legacy string-shadow tact auras from internal aura echoes."""
    logger.debug("cyclic_tact_auras entry radius=%d", radius)
    echoes = cyclic_tact_aura_echoes(modes, alphabet, radius)
    result = {tact: TactAura(tact, echo.text_marks()) for tact, echo in echoes.items()}
    logger.debug("cyclic_tact_auras exit count=%d", len(result))
    return result


def jaccard_similarity(left: TactAura, right: TactAura) -> float:
    """Return Jaccard similarity of two tact auras."""
    logger.debug("jaccard_similarity entry left=%s right=%s", left.tact, right.tact)
    if left.tact == right.tact:
        logger.debug("jaccard_similarity exit exact=1")
        return 1.0
    union = left.marks | right.marks
    if not union:
        logger.debug("jaccard_similarity exit empty=0")
        return 0.0
    result = len(left.marks & right.marks) / len(union)
    logger.debug("jaccard_similarity exit result=%s", result)
    return result


def aura_cost(left: TactAura, right: TactAura, min_mismatch_cost: float = 0.25, max_mismatch_cost: float = 1.0) -> float:
    """Convert aura similarity into a nonnegative directed mismatch cost."""
    logger.debug("aura_cost entry left=%s right=%s", left.tact, right.tact)
    if min_mismatch_cost < 0 or max_mismatch_cost < min_mismatch_cost:
        logger.error("aura_cost invalid bounds min=%s max=%s", min_mismatch_cost, max_mismatch_cost)
        raise ValueError("cost bounds must satisfy 0 <= min <= max")
    if left.tact == right.tact:
        logger.debug("aura_cost exit exact=0")
        return 0.0
    raw = 1.0 - jaccard_similarity(left, right)
    result = max(min_mismatch_cost, min(max_mismatch_cost, raw))
    logger.debug("aura_cost exit result=%s", result)
    return result


def aura_cost_map(modes: Iterable[Mode], alphabet: Iterable[str] = (), radius: int = 1, min_mismatch_cost: float = 0.25, max_mismatch_cost: float = 1.0) -> CostMap:
    """Derive a complete directed mismatch cost map from cyclic tact auras."""
    logger.debug("aura_cost_map entry radius=%d", radius)
    auras = cyclic_tact_auras(modes, alphabet, radius)
    costs: CostMap = {}
    for expected in auras.values():
        for actual in auras.values():
            if expected.tact != actual.tact:
                costs[(expected.tact, actual.tact)] = aura_cost(expected, actual, min_mismatch_cost, max_mismatch_cost)
    logger.debug("aura_cost_map exit count=%d", len(costs))
    return costs


def tact_aura_cost_rows(modes: Iterable[Mode], alphabet: Iterable[str] = (), radius: int = 1, min_mismatch_cost: float = 0.25, max_mismatch_cost: float = 1.0) -> list[dict[str, object]]:
    """Build CSV-ready aura similarity/cost rows."""
    logger.debug("tact_aura_cost_rows entry radius=%d", radius)
    auras = cyclic_tact_auras(modes, alphabet, radius)
    rows: list[dict[str, object]] = []
    for expected in auras.values():
        for actual in auras.values():
            if expected.tact == actual.tact:
                continue
            rows.append({
                "expected": expected.tact,
                "actual": actual.tact,
                "similarity": jaccard_similarity(expected, actual),
                "cost": aura_cost(expected, actual, min_mismatch_cost, max_mismatch_cost),
                "expected_aura": "|".join(sorted(expected.marks)),
                "actual_aura": "|".join(sorted(actual.marks)),
            })
    logger.debug("tact_aura_cost_rows exit rows=%d", len(rows))
    return rows
