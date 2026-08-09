"""Veyra Core-0 mode shadows.

This module is deliberately small. It models a mode shadow as a finite tact word
so early Veyra definitions can be tested against examples and counterexamples.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from itertools import product
import logging
from typing import Callable, Iterable

logger = logging.getLogger(__name__)

Observer = Callable[["Mode"], object]


@dataclass(frozen=True, order=True)
class Mode:
    """Finite tact-word shadow of a closed Veyra breath."""

    tacts: tuple[str, ...]

    @classmethod
    def from_word(cls, word: str | Iterable[str]) -> "Mode":
        """Create a mode from a string or iterable of tact labels."""
        logger.debug("Mode.from_word entry word=%r", word)
        try:
            if isinstance(word, str):
                mode = cls(tuple(word))
            else:
                mode = cls(tuple(word))
            logger.debug("Mode.from_word exit mode=%s", mode.word)
            return mode
        except Exception:
            logger.exception("Mode.from_word error word=%r", word)
            raise

    @property
    def word(self) -> str:
        """Return compact word representation; epsilon for the silent mode."""
        logger.debug("Mode.word entry tacts=%r", self.tacts)
        result = "".join(self.tacts) if self.tacts else "ε"
        logger.debug("Mode.word exit result=%s", result)
        return result

    @property
    def length(self) -> int:
        """Return tact count."""
        logger.debug("Mode.length entry mode=%s", self.word)
        result = len(self.tacts)
        logger.debug("Mode.length exit result=%d", result)
        return result

    def stitch(self, other: "Mode") -> "Mode":
        """Stitch two closed mode shadows by concatenating tact words."""
        logger.debug("Mode.stitch entry left=%s right=%s", self.word, other.word)
        result = Mode(self.tacts + other.tacts)
        logger.debug("Mode.stitch exit result=%s", result.word)
        return result


def enumerate_modes(alphabet: Iterable[str], max_len: int, include_silent: bool = True) -> list[Mode]:
    """Enumerate all mode shadows over alphabet up to max_len."""
    logger.debug(
        "enumerate_modes entry alphabet=%r max_len=%d include_silent=%s",
        alphabet,
        max_len,
        include_silent,
    )
    if max_len < 0:
        logger.error("enumerate_modes invalid max_len=%d", max_len)
        raise ValueError("max_len must be non-negative")
    symbols = tuple(alphabet)
    if not symbols and max_len > 0:
        logger.error("enumerate_modes empty alphabet with max_len=%d", max_len)
        raise ValueError("alphabet must be non-empty when max_len > 0")
    modes: list[Mode] = [Mode(())] if include_silent else []
    for length in range(1, max_len + 1):
        modes.extend(Mode(tuple(word)) for word in product(symbols, repeat=length))
    logger.debug("enumerate_modes exit count=%d", len(modes))
    return modes


def length_observer(mode: Mode) -> int:
    """Observe only tact count."""
    logger.debug("length_observer entry mode=%s", mode.word)
    result = mode.length
    logger.debug("length_observer exit result=%d", result)
    return result


def parikh_observer(mode: Mode) -> tuple[tuple[str, int], ...]:
    """Observe unordered tact multiplicities."""
    logger.debug("parikh_observer entry mode=%s", mode.word)
    result = tuple(sorted(Counter(mode.tacts).items()))
    logger.debug("parikh_observer exit result=%r", result)
    return result


def word_observer(mode: Mode) -> tuple[str, ...]:
    """Observe exact tact sequence."""
    logger.debug("word_observer entry mode=%s", mode.word)
    result = mode.tacts
    logger.debug("word_observer exit result=%r", result)
    return result


def cyclic_observer(mode: Mode) -> tuple[str, ...]:
    """Observe canonical rotation class of a closed tact word."""
    logger.debug("cyclic_observer entry mode=%s", mode.word)
    if not mode.tacts:
        logger.debug("cyclic_observer exit silent")
        return ()
    rotations = [mode.tacts[i:] + mode.tacts[:i] for i in range(len(mode.tacts))]
    result = min(rotations)
    logger.debug("cyclic_observer exit result=%r", result)
    return result


TEST_FAMILIES: dict[str, tuple[Observer, ...]] = {
    "length": (length_observer,),
    "bag": (parikh_observer,),
    "ordered": (word_observer,),
    "cycle": (cyclic_observer,),
}


def echo_key(mode: Mode, tests: Iterable[Observer]) -> tuple[object, ...]:
    """Return all observer responses for mode under tests."""
    logger.debug("echo_key entry mode=%s", mode.word)
    result = tuple(test(mode) for test in tests)
    logger.debug("echo_key exit result=%r", result)
    return result


def echo_equivalent(left: Mode, right: Mode, tests: Iterable[Observer]) -> bool:
    """Return True iff left and right are echo-equivalent under tests."""
    logger.debug("echo_equivalent entry left=%s right=%s", left.word, right.word)
    result = echo_key(left, tests) == echo_key(right, tests)
    logger.debug("echo_equivalent exit result=%s", result)
    return result


def primitive_root(mode: Mode) -> tuple[Mode, int]:
    """Return shortest repeated root and exponent for an ordered word mode."""
    logger.debug("primitive_root entry mode=%s", mode.word)
    n = mode.length
    if n == 0:
        result = (mode, 1)
        logger.debug("primitive_root exit silent result=%s exponent=1", mode.word)
        return result
    for size in range(1, n + 1):
        if n % size != 0:
            continue
        root = mode.tacts[:size]
        if root * (n // size) == mode.tacts:
            result = (Mode(root), n // size)
            logger.debug("primitive_root exit root=%s exponent=%d", result[0].word, result[1])
            return result
    logger.error("primitive_root unreachable mode=%s", mode.word)
    raise RuntimeError("primitive root search failed")


def is_ordered_primitive(mode: Mode) -> bool:
    """Return True for non-silent modes not made by repeating a shorter word."""
    logger.debug("is_ordered_primitive entry mode=%s", mode.word)
    if mode.length == 0:
        logger.debug("is_ordered_primitive exit result=False silent")
        return False
    root, exponent = primitive_root(mode)
    result = root == mode and exponent == 1
    logger.debug("is_ordered_primitive exit result=%s", result)
    return result


def ordered_resonates_inside(part: Mode, whole: Mode) -> bool:
    """Return True iff whole is an exact repetition of non-silent part."""
    logger.debug("ordered_resonates_inside entry part=%s whole=%s", part.word, whole.word)
    if part.length == 0:
        result = whole.length == 0
        logger.debug("ordered_resonates_inside exit result=%s silent_part", result)
        return result
    if whole.length % part.length != 0:
        logger.debug("ordered_resonates_inside exit result=False bad_length")
        return False
    result = part.tacts * (whole.length // part.length) == whole.tacts
    logger.debug("ordered_resonates_inside exit result=%s", result)
    return result


def repeat_mode(mode: Mode, times: int) -> Mode:
    """Repeat a mode by stitching it to itself times times."""
    logger.debug("repeat_mode entry mode=%s times=%d", mode.word, times)
    if times < 0:
        logger.error("repeat_mode invalid times=%d", times)
        raise ValueError("times must be non-negative")
    result = Mode(mode.tacts * times)
    logger.debug("repeat_mode exit result=%s", result.word)
    return result


def substitute_mode(driver: Mode, mapping: dict[str, Mode]) -> Mode:
    """Weave by replacing each driver tact with the mapped mode."""
    logger.debug("substitute_mode entry driver=%s keys=%r", driver.word, sorted(mapping))
    pieces: list[str] = []
    try:
        for tact in driver.tacts:
            pieces.extend(mapping[tact].tacts)
    except KeyError:
        logger.exception("substitute_mode missing tact for driver=%s", driver.word)
        raise
    result = Mode(tuple(pieces))
    logger.debug("substitute_mode exit result=%s", result.word)
    return result


def weave_by_length(filler: Mode, driver: Mode) -> Mode:
    """Binary Core-0 length-weave: repeat filler once per driver tact."""
    logger.debug("weave_by_length entry filler=%s driver=%s", filler.word, driver.word)
    result = repeat_mode(filler, driver.length)
    logger.debug("weave_by_length exit result=%s", result.word)
    return result


def natural_mode(value: int, tact: str = "τ") -> Mode:
    """Return the one-tact mode shadow tau^value."""
    logger.debug("natural_mode entry value=%d tact=%r", value, tact)
    if value < 0:
        logger.error("natural_mode invalid value=%d", value)
        raise ValueError("value must be non-negative")
    if not tact:
        logger.error("natural_mode empty tact")
        raise ValueError("tact must be non-empty")
    result = Mode((tact,) * value)
    logger.debug("natural_mode exit result=%s", result.word)
    return result


def natural_shadow(mode: Mode, tact: str = "τ") -> int:
    """Map a one-tact mode shadow to its natural-number length."""
    logger.debug("natural_shadow entry mode=%s tact=%r", mode.word, tact)
    if any(item != tact for item in mode.tacts):
        logger.error("natural_shadow non one-tact mode=%s tact=%r", mode.word, tact)
        raise ValueError("mode is not in the selected one-tact shadow")
    result = mode.length
    logger.debug("natural_shadow exit result=%d", result)
    return result
