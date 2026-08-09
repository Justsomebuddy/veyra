"""Approximate bounded-defect resonance for Veyra mode shadows."""

from __future__ import annotations

from dataclasses import dataclass
import logging

from .modes import Mode, repeat_mode
from .resonance import rotate_mode

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Defect:
    """One position where expected and actual tacts differ."""

    index: int
    expected: str
    actual: str


@dataclass(frozen=True)
class ApproxPhaseMatch:
    """Approximate phase match for one whole rotation."""

    offset: int
    rotated: Mode
    expected: Mode
    defects: tuple[Defect, ...]

    @property
    def defect_count(self) -> int:
        """Return number of defects in this phase match."""
        logger.debug("ApproxPhaseMatch.defect_count entry offset=%d", self.offset)
        result = len(self.defects)
        logger.debug("ApproxPhaseMatch.defect_count exit result=%d", result)
        return result


@dataclass(frozen=True)
class ApproxResonanceProfile:
    """Best bounded-defect resonance profile for a part/whole pair."""

    part: Mode
    whole: Mode
    max_defects: int
    resonates: bool
    obstruction: str
    best: ApproxPhaseMatch | None


def defect_list(expected: Mode, actual: Mode) -> tuple[Defect, ...]:
    """Return position-wise tact mismatches for equal-length modes."""
    logger.debug("defect_list entry expected=%s actual=%s", expected.word, actual.word)
    if expected.length != actual.length:
        logger.error("defect_list length mismatch expected=%d actual=%d", expected.length, actual.length)
        raise ValueError("defect_list requires equal-length modes")
    result = tuple(
        Defect(index, left, right)
        for index, (left, right) in enumerate(zip(expected.tacts, actual.tacts, strict=True))
        if left != right
    )
    logger.debug("defect_list exit count=%d", len(result))
    return result


def approximate_phase_matches(part: Mode, whole: Mode) -> tuple[ApproxPhaseMatch, ...]:
    """Return all phase matches with defect lists, if lengths tile."""
    logger.debug("approximate_phase_matches entry part=%s whole=%s", part.word, whole.word)
    if part.length == 0:
        logger.debug("approximate_phase_matches exit empty silent_part")
        return ()
    if whole.length % part.length != 0:
        logger.debug("approximate_phase_matches exit empty length_obstruction")
        return ()
    expected = repeat_mode(part, whole.length // part.length)
    matches: list[ApproxPhaseMatch] = []
    for offset in range(whole.length if whole.length else 1):
        rotated = rotate_mode(whole, offset)
        matches.append(ApproxPhaseMatch(offset, rotated, expected, defect_list(expected, rotated)))
    result = tuple(sorted(matches, key=lambda item: (item.defect_count, item.offset)))
    logger.debug("approximate_phase_matches exit count=%d", len(result))
    return result


def approximate_resonance_profile(part: Mode, whole: Mode, max_defects: int) -> ApproxResonanceProfile:
    """Return best approximate cyclic resonance profile under a defect budget."""
    logger.debug(
        "approximate_resonance_profile entry part=%s whole=%s max_defects=%d",
        part.word,
        whole.word,
        max_defects,
    )
    if max_defects < 0:
        logger.error("approximate_resonance_profile invalid max_defects=%d", max_defects)
        raise ValueError("max_defects must be non-negative")
    if part.length == 0:
        result = ApproxResonanceProfile(part, whole, max_defects, False, "silent-part", None)
        logger.debug("approximate_resonance_profile exit result=%r", result)
        return result
    if whole.length % part.length != 0:
        result = ApproxResonanceProfile(part, whole, max_defects, False, "length-obstruction", None)
        logger.debug("approximate_resonance_profile exit result=%r", result)
        return result
    matches = approximate_phase_matches(part, whole)
    best = matches[0] if matches else None
    if best is None:
        result = ApproxResonanceProfile(part, whole, max_defects, False, "pattern-obstruction", None)
    elif best.defect_count == 0:
        result = ApproxResonanceProfile(part, whole, max_defects, True, "none", best)
    elif best.defect_count <= max_defects:
        result = ApproxResonanceProfile(part, whole, max_defects, True, "bounded-defect", best)
    else:
        result = ApproxResonanceProfile(part, whole, max_defects, False, "over-budget", best)
    logger.debug("approximate_resonance_profile exit result=%r", result)
    return result


def approximate_cyclic_resonates(part: Mode, whole: Mode, max_defects: int) -> bool:
    """Return True iff part approximately tiles a rotation of whole within budget."""
    logger.debug(
        "approximate_cyclic_resonates entry part=%s whole=%s max_defects=%d",
        part.word,
        whole.word,
        max_defects,
    )
    result = approximate_resonance_profile(part, whole, max_defects).resonates
    logger.debug("approximate_cyclic_resonates exit result=%s", result)
    return result
