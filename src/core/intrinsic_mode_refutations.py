"""Executable counterexamples delimiting intrinsic transport from word resonance."""
from __future__ import annotations

from dataclasses import dataclass
import logging

from .intrinsic_mode_transport import recurrence_digest, recurrence_equal
from .numbers.modes import Mode as WordMode
from .proof_core_types import CoreTerm, Pulse, Silence
from .numbers.resonance import cyclic_resonates_inside, phase_offsets

logger = logging.getLogger(__name__)
BOUNDARY = (
    "label erasure preserves only unary recurrence shape; it neither reflects "
    "general cyclic resonance nor recovers phase offsets"
)


@dataclass(frozen=True)
class ErasureBoundaryRow:
    """One checked non-equivalence row at the word/intrinsic carrier boundary."""

    row_id: str
    erased_left_digest: str
    erased_right_digest: str
    intrinsic_echo: bool
    cyclic_resonance: bool
    phase_offsets: tuple[int, ...]
    separated: bool
    finding: str
    boundary: str = BOUNDARY


def erase_word_mode(value: WordMode) -> CoreTerm:
    """Forget labels and retain only structural pulse succession."""
    logger.debug("erase_word_mode entry word=%s", value.word)
    result: CoreTerm = Silence()
    for _ in reversed(value.tacts):
        result = Pulse(result)
    logger.debug("erase_word_mode exit digest=%s", recurrence_digest(result))
    return result


def _pair_row(row_id: str, left: WordMode, right: WordMode) -> ErasureBoundaryRow:
    logger.debug("_pair_row entry row=%s", row_id)
    erased_left, erased_right = erase_word_mode(left), erase_word_mode(right)
    intrinsic_echo = recurrence_equal(erased_left, erased_right)
    cyclic = cyclic_resonates_inside(left, right)
    offsets = phase_offsets(left, right)
    separated = intrinsic_echo and not cyclic
    result = ErasureBoundaryRow(
        row_id, recurrence_digest(erased_left), recurrence_digest(erased_right),
        intrinsic_echo, cyclic, offsets, separated,
        "same unary recurrence image but different labeled cyclic behavior",
    )
    logger.debug("_pair_row exit separated=%s", result.separated)
    return result


def erasure_boundary_rows() -> tuple[ErasureBoundaryRow, ...]:
    """Return the required label, phase, and silent-boundary counterexamples."""
    logger.debug("erasure_boundary_rows entry")
    label = _pair_row("R9-REFUTE-LABEL", WordMode.from_word("ab"), WordMode.from_word("aa"))

    part = WordMode.from_word("ab")
    first, second = WordMode.from_word("abab"), WordMode.from_word("baba")
    erased_first, erased_second = erase_word_mode(first), erase_word_mode(second)
    first_offsets, second_offsets = phase_offsets(part, first), phase_offsets(part, second)
    phase_echo = recurrence_equal(erased_first, erased_second)
    phase_cyclic = cyclic_resonates_inside(part, first) and cyclic_resonates_inside(part, second)
    phase = ErasureBoundaryRow(
        "R9-REFUTE-PHASE", recurrence_digest(erased_first), recurrence_digest(erased_second),
        phase_echo, phase_cyclic, second_offsets,
        phase_echo and phase_cyclic and first_offsets != second_offsets,
        f"same erased pair lengths; labeled offsets differ {first_offsets} vs {second_offsets}",
    )

    silent_word = WordMode.from_word("")
    silent = erase_word_mode(silent_word)
    silent_cyclic = cyclic_resonates_inside(silent_word, silent_word)
    silent_echo = recurrence_equal(silent, silent)
    silent_row = ErasureBoundaryRow(
        "R9-REFUTE-SILENT", recurrence_digest(silent), recurrence_digest(silent),
        silent_echo, silent_cyclic, phase_offsets(silent_word, silent_word),
        silent_echo and not silent_cyclic,
        "intrinsic silence reflexivity is outside word cyclic resonance",
    )
    result = (label, phase, silent_row)
    logger.debug("erasure_boundary_rows exit rows=%d", len(result))
    return result
