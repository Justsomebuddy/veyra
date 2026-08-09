"""Veyra surprise: observer gaps that reveal hidden structure."""

from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Iterable

from ..numbers.compression import CompressionWeights, best_compression
from ..numbers.compression_algebra import edit_resonance_profile
from ..numbers.modes import Mode, enumerate_modes

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class VeyraSurpriseWitness:
    """A mode that becomes structured only after changing observers."""

    mode: Mode
    surface_observer: str
    hidden_observer: str
    part: Mode
    expected: Mode
    edit_distance: int
    surface_saving: float
    hidden_saving: float
    score: float
    obstruction: str
    reason: str

    def as_dict(self) -> dict[str, object]:
        """Return JSON-ready witness row."""
        logger.debug("VeyraSurpriseWitness.as_dict entry mode=%s", self.mode.word)
        result = {
            "mode": self.mode.word,
            "surface_observer": self.surface_observer,
            "hidden_observer": self.hidden_observer,
            "part": self.part.word,
            "expected": self.expected.word,
            "edit_distance": self.edit_distance,
            "surface_saving": self.surface_saving,
            "hidden_saving": self.hidden_saving,
            "score": self.score,
            "obstruction": self.obstruction,
            "reason": self.reason,
        }
        logger.debug("VeyraSurpriseWitness.as_dict exit result=%r", result)
        return result


def _proper_parts(
    mode: Mode, alphabet: Iterable[str], max_part_len: int, min_part_len: int = 2
) -> list[Mode]:
    """Return candidate parts shorter than the mode."""
    logger.debug(
        "_proper_parts entry mode=%s max_part_len=%d min_part_len=%d",
        mode.word,
        max_part_len,
        min_part_len,
    )
    if max_part_len < 1:
        logger.error("_proper_parts invalid max_part_len=%d", max_part_len)
        raise ValueError("max_part_len must be positive")
    if min_part_len < 1:
        logger.error("_proper_parts invalid min_part_len=%d", min_part_len)
        raise ValueError("min_part_len must be positive")
    result = [
        part
        for part in enumerate_modes(
            alphabet, min(max_part_len, max(1, mode.length - 1)), include_silent=False
        )
        if min_part_len <= part.length < mode.length and len(set(part.tacts)) > 1
    ]
    logger.debug("_proper_parts exit count=%d", len(result))
    return result


def surface_exact_saving(mode: Mode, candidates: Iterable[Mode]) -> float:
    """Return best exact-cycle compression saving for a mode."""
    logger.debug("surface_exact_saving entry mode=%s", mode.word)
    best = best_compression(
        mode, candidates, 0, CompressionWeights(defect_weight=2.0, phase_weight=0.25)
    )
    result = 0.0 if best is None else best.saving
    logger.debug("surface_exact_saving exit result=%s", result)
    return result


def best_surprise_for_mode(
    mode: Mode,
    alphabet: Iterable[str],
    max_part_len: int = 3,
    max_edits: int = 1,
    edit_weight: float = 1.0,
    min_part_len: int = 2,
) -> VeyraSurpriseWitness | None:
    """Return best observer-gap witness for one mode, if any."""
    logger.debug(
        "best_surprise_for_mode entry mode=%s max_edits=%d", mode.word, max_edits
    )
    if max_edits < 0:
        logger.error("best_surprise_for_mode invalid max_edits=%d", max_edits)
        raise ValueError("max_edits must be non-negative")
    candidates = _proper_parts(mode, alphabet, max_part_len, min_part_len)
    if not candidates:
        logger.debug("best_surprise_for_mode exit no candidates")
        return None
    surface = surface_exact_saving(mode, candidates)
    rows: list[VeyraSurpriseWitness] = []
    for part in candidates:
        profile = edit_resonance_profile(part, mode, max_edits)
        cost = part.length + edit_weight * profile.distance
        hidden = mode.length - cost
        score = hidden - max(surface, 0.0)
        if profile.resonates and score > 0 and hidden > 0:
            reason = (
                f"surface exact-cycle saves {surface:g}, but edit-lift saves {hidden:g}"
            )
            rows.append(
                VeyraSurpriseWitness(
                    mode,
                    "exact-cycle",
                    "edit-lift",
                    part,
                    profile.expected,
                    profile.distance,
                    surface,
                    hidden,
                    score,
                    profile.obstruction,
                    reason,
                )
            )
    result = (
        None
        if not rows
        else sorted(
            rows,
            key=lambda item: (
                -item.score,
                -item.hidden_saving,
                item.edit_distance,
                item.part.length,
                item.part.word,
            ),
        )[0]
    )
    logger.debug("best_surprise_for_mode exit result=%r", result)
    return result


def find_surprise_witnesses(
    alphabet: Iterable[str] = ("a", "b"),
    max_len: int = 6,
    max_part_len: int = 3,
    max_edits: int = 1,
    limit: int = 5,
    min_part_len: int = 2,
) -> tuple[VeyraSurpriseWitness, ...]:
    """Search finite mode space for observer-gap surprise witnesses."""
    logger.debug("find_surprise_witnesses entry max_len=%d limit=%d", max_len, limit)
    if limit < 0:
        logger.error("find_surprise_witnesses invalid limit=%d", limit)
        raise ValueError("limit must be non-negative")
    witnesses = []
    for mode in enumerate_modes(alphabet, max_len, include_silent=False):
        witness = best_surprise_for_mode(
            mode, alphabet, max_part_len, max_edits, min_part_len=min_part_len
        )
        if witness is not None:
            witnesses.append(witness)
    result = tuple(
        sorted(
            witnesses, key=lambda item: (-item.score, item.mode.length, item.mode.word)
        )[:limit]
    )
    logger.debug("find_surprise_witnesses exit count=%d", len(result))
    return result


def surprise_checklist() -> tuple[str, ...]:
    """Return Veyra surprise-layer capabilities."""
    logger.debug("surprise_checklist entry")
    result = (
        "surface-observer",
        "hidden-observer",
        "observer-gap-score",
        "edit-lift-witness",
        "negative-if-no-gap",
    )
    logger.debug("surprise_checklist exit count=%d", len(result))
    return result
