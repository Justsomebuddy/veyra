"""Resonance spectra for Veyra mode shadows."""

from __future__ import annotations

from dataclasses import dataclass
from math import inf
import logging
from typing import Iterable

from .approx_resonance import ApproxResonanceProfile, approximate_resonance_profile
from .modes import Mode, enumerate_modes

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SpectrumEntry:
    """One candidate part and its approximate resonance profile against a whole."""

    part: Mode
    profile: ApproxResonanceProfile

    @property
    def defect_count(self) -> int | None:
        """Return best defect count, if a best phase exists."""
        logger.debug("SpectrumEntry.defect_count entry part=%s", self.part.word)
        result = None if self.profile.best is None else self.profile.best.defect_count
        logger.debug("SpectrumEntry.defect_count exit result=%r", result)
        return result

    @property
    def best_offset(self) -> int | None:
        """Return best phase offset, if available."""
        logger.debug("SpectrumEntry.best_offset entry part=%s", self.part.word)
        result = None if self.profile.best is None else self.profile.best.offset
        logger.debug("SpectrumEntry.best_offset exit result=%r", result)
        return result

    @property
    def exact(self) -> bool:
        """Return True iff the best profile has zero defects and resonates."""
        logger.debug("SpectrumEntry.exact entry part=%s", self.part.word)
        result = self.profile.resonates and self.defect_count == 0
        logger.debug("SpectrumEntry.exact exit result=%s", result)
        return result


def candidate_parts(alphabet: Iterable[str], max_len: int, min_len: int = 1) -> list[Mode]:
    """Enumerate non-silent candidate parts within length bounds."""
    logger.debug("candidate_parts entry alphabet=%r max_len=%d min_len=%d", alphabet, max_len, min_len)
    if min_len < 1:
        logger.error("candidate_parts invalid min_len=%d", min_len)
        raise ValueError("min_len must be at least 1")
    if max_len < min_len:
        logger.error("candidate_parts invalid max_len=%d min_len=%d", max_len, min_len)
        raise ValueError("max_len must be >= min_len")
    result = [mode for mode in enumerate_modes(alphabet, max_len, include_silent=False) if mode.length >= min_len]
    logger.debug("candidate_parts exit count=%d", len(result))
    return result


def spectrum_rank_key(entry: SpectrumEntry) -> tuple[object, ...]:
    """Return deterministic ranking key for spectrum entries."""
    logger.debug("spectrum_rank_key entry part=%s", entry.part.word)
    defect_count = inf if entry.defect_count is None else entry.defect_count
    obstruction_rank = {
        "none": 0,
        "bounded-defect": 1,
        "over-budget": 2,
        "pattern-obstruction": 3,
        "length-obstruction": 4,
        "silent-part": 5,
    }.get(entry.profile.obstruction, 9)
    result = (
        not entry.profile.resonates,
        defect_count,
        obstruction_rank,
        entry.part.length,
        entry.part.word,
    )
    logger.debug("spectrum_rank_key exit result=%r", result)
    return result


def resonance_spectrum(
    whole: Mode,
    candidates: Iterable[Mode],
    max_defects: int,
    include_nonresonant: bool = True,
) -> list[SpectrumEntry]:
    """Return ranked approximate resonance spectrum for whole over candidates."""
    logger.debug(
        "resonance_spectrum entry whole=%s max_defects=%d include_nonresonant=%s",
        whole.word,
        max_defects,
        include_nonresonant,
    )
    entries: list[SpectrumEntry] = []
    for part in candidates:
        profile = approximate_resonance_profile(part, whole, max_defects)
        if profile.resonates or include_nonresonant:
            entries.append(SpectrumEntry(part, profile))
    result = sorted(entries, key=spectrum_rank_key)
    logger.debug("resonance_spectrum exit count=%d", len(result))
    return result


def top_resonances(whole: Mode, candidates: Iterable[Mode], max_defects: int, limit: int) -> list[SpectrumEntry]:
    """Return top spectrum entries, excluding non-resonating candidates."""
    logger.debug("top_resonances entry whole=%s max_defects=%d limit=%d", whole.word, max_defects, limit)
    if limit < 0:
        logger.error("top_resonances invalid limit=%d", limit)
        raise ValueError("limit must be non-negative")
    result = resonance_spectrum(whole, candidates, max_defects, include_nonresonant=False)[:limit]
    logger.debug("top_resonances exit count=%d", len(result))
    return result
