"""Compression scoring for Veyra resonance spectrum entries."""

from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Iterable

from .modes import Mode
from .spectrum import SpectrumEntry, resonance_spectrum

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CompressionWeights:
    """Weights for the first Veyra explanation-cost model."""

    defect_weight: float = 2.0
    phase_weight: float = 0.25


@dataclass(frozen=True)
class CompressionEntry:
    """Compression score attached to one resonance spectrum entry."""

    spectrum_entry: SpectrumEntry
    cost: float
    saving: float
    ratio: float

    @property
    def part(self) -> Mode:
        """Return candidate part mode."""
        logger.debug("CompressionEntry.part entry")
        result = self.spectrum_entry.part
        logger.debug("CompressionEntry.part exit result=%s", result.word)
        return result


def phase_penalty(offset: int | None) -> float:
    """Return first simple phase penalty: zero offset is free, shifted phase costs 1."""
    logger.debug("phase_penalty entry offset=%r", offset)
    result = 0.0 if offset in (None, 0) else 1.0
    logger.debug("phase_penalty exit result=%s", result)
    return result


def explanation_cost(entry: SpectrumEntry, weights: CompressionWeights = CompressionWeights()) -> float:
    """Compute explanation cost for a resonating spectrum entry."""
    logger.debug("explanation_cost entry part=%s weights=%r", entry.part.word, weights)
    if not entry.profile.resonates or entry.profile.best is None:
        logger.error("explanation_cost non-resonating entry part=%s", entry.part.word)
        raise ValueError("compression cost requires a resonating entry with a best match")
    defects = entry.profile.best.defect_count
    result = entry.part.length + weights.defect_weight * defects + weights.phase_weight * phase_penalty(entry.profile.best.offset)
    logger.debug("explanation_cost exit result=%s", result)
    return result


def compression_entry(entry: SpectrumEntry, weights: CompressionWeights = CompressionWeights()) -> CompressionEntry:
    """Attach cost, saving, and ratio to a resonating spectrum entry."""
    logger.debug("compression_entry entry part=%s", entry.part.word)
    cost = explanation_cost(entry, weights)
    whole_len = entry.profile.whole.length
    saving = whole_len - cost
    ratio = 0.0 if whole_len == 0 else saving / whole_len
    result = CompressionEntry(entry, cost, saving, ratio)
    logger.debug("compression_entry exit result=%r", result)
    return result


def compression_rank_key(entry: CompressionEntry) -> tuple[object, ...]:
    """Rank compression entries by best explanation first."""
    logger.debug("compression_rank_key entry part=%s", entry.part.word)
    best = entry.spectrum_entry.profile.best
    defect_count = 10**9 if best is None else best.defect_count
    offset = 10**9 if best is None else best.offset
    result = (-entry.saving, defect_count, entry.part.length, offset, entry.part.word)
    logger.debug("compression_rank_key exit result=%r", result)
    return result


def compression_scores(
    whole: Mode,
    candidates: Iterable[Mode],
    max_defects: int,
    weights: CompressionWeights = CompressionWeights(),
) -> list[CompressionEntry]:
    """Return ranked compression scores for resonating candidate parts."""
    logger.debug("compression_scores entry whole=%s max_defects=%d weights=%r", whole.word, max_defects, weights)
    spectrum = resonance_spectrum(whole, candidates, max_defects, include_nonresonant=False)
    entries = [compression_entry(entry, weights) for entry in spectrum]
    result = sorted(entries, key=compression_rank_key)
    logger.debug("compression_scores exit count=%d", len(result))
    return result


def best_compression(
    whole: Mode,
    candidates: Iterable[Mode],
    max_defects: int,
    weights: CompressionWeights = CompressionWeights(),
) -> CompressionEntry | None:
    """Return best compression entry, or None if nothing resonates."""
    logger.debug("best_compression entry whole=%s max_defects=%d", whole.word, max_defects)
    scores = compression_scores(whole, candidates, max_defects, weights)
    result = scores[0] if scores else None
    logger.debug("best_compression exit result=%r", result)
    return result
