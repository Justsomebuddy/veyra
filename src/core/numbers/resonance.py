"""Resonance relations for Veyra mode shadows."""

from __future__ import annotations

from dataclasses import dataclass
import logging

from .modes import Mode, ordered_resonates_inside, repeat_mode
from .weave import cyclic_representative

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ResonanceProfile:
    """Ordered and cyclic resonance facts for one part/whole pair."""

    part: Mode
    whole: Mode
    ordered: bool
    cyclic: bool
    phase_offsets: tuple[int, ...]
    obstruction: str


def rotate_mode(mode: Mode, offset: int) -> Mode:
    """Rotate mode tacts left by offset positions."""
    logger.debug("rotate_mode entry mode=%s offset=%d", mode.word, offset)
    if mode.length == 0:
        logger.debug("rotate_mode exit silent")
        return mode
    real_offset = offset % mode.length
    result = Mode(mode.tacts[real_offset:] + mode.tacts[:real_offset])
    logger.debug("rotate_mode exit result=%s", result.word)
    return result


def phase_offsets(part: Mode, whole: Mode) -> tuple[int, ...]:
    """Return offsets where rotating whole becomes an exact power of part."""
    logger.debug("phase_offsets entry part=%s whole=%s", part.word, whole.word)
    if part.length == 0:
        logger.debug("phase_offsets exit empty silent_part")
        return ()
    if whole.length % part.length != 0:
        logger.debug("phase_offsets exit empty length_obstruction")
        return ()
    target = repeat_mode(part, whole.length // part.length)
    offsets: list[int] = []
    for offset in range(whole.length if whole.length else 1):
        if rotate_mode(whole, offset) == target:
            offsets.append(offset)
    result = tuple(offsets)
    logger.debug("phase_offsets exit result=%r", result)
    return result


def cyclic_resonates_inside(part: Mode, whole: Mode) -> bool:
    """Return True iff part tiles some rotation of whole."""
    logger.debug("cyclic_resonates_inside entry part=%s whole=%s", part.word, whole.word)
    result = bool(phase_offsets(part, whole))
    logger.debug("cyclic_resonates_inside exit result=%s", result)
    return result


def resonance_obstruction(part: Mode, whole: Mode) -> str:
    """Classify the first obstruction to cyclic resonance."""
    logger.debug("resonance_obstruction entry part=%s whole=%s", part.word, whole.word)
    if part.length == 0:
        result = "silent-part"
    elif whole.length % part.length != 0:
        result = "length-obstruction"
    elif cyclic_resonates_inside(part, whole):
        result = "none"
    else:
        result = "pattern-obstruction"
    logger.debug("resonance_obstruction exit result=%s", result)
    return result


def cyclic_power(mode: Mode, exponent: int) -> Mode:
    """Return canonical cyclic representative of a repeated mode."""
    logger.debug("cyclic_power entry mode=%s exponent=%d", mode.word, exponent)
    result = cyclic_representative(repeat_mode(mode, exponent))
    logger.debug("cyclic_power exit result=%s", result.word)
    return result


def resonance_profile(part: Mode, whole: Mode) -> ResonanceProfile:
    """Return ordered/cyclic resonance profile for part and whole."""
    logger.debug("resonance_profile entry part=%s whole=%s", part.word, whole.word)
    offsets = phase_offsets(part, whole)
    result = ResonanceProfile(
        part=part,
        whole=whole,
        ordered=ordered_resonates_inside(part, whole),
        cyclic=bool(offsets),
        phase_offsets=offsets,
        obstruction=resonance_obstruction(part, whole),
    )
    logger.debug("resonance_profile exit result=%r", result)
    return result
