"""Native cycle-echo number-theory probes for Veyra resonance."""

from __future__ import annotations

from dataclasses import dataclass
from math import inf
import logging
from typing import Iterable

from .compression import CompressionEntry, CompressionWeights, compression_scores
from .modes import Mode, enumerate_modes, is_ordered_primitive, repeat_mode, substitute_mode
from .primes import PrimeProfile, prime_profile
from .resonance import ResonanceProfile, resonance_profile, rotate_mode
from .spectrum import SpectrumEntry, resonance_spectrum

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CycleEcho:
    """Internal cyclic echo object: the whole rotation orbit, not one chosen cut."""

    orbit: frozenset[tuple[str, ...]]

    @property
    def length(self) -> int:
        """Return common orbit word length."""
        logger.debug("CycleEcho.length entry orbit_size=%d", len(self.orbit))
        result = len(next(iter(self.orbit))) if self.orbit else 0
        logger.debug("CycleEcho.length exit result=%d", result)
        return result

    @property
    def orbit_size(self) -> int:
        """Return number of distinct cuts in the cycle."""
        logger.debug("CycleEcho.orbit_size entry")
        result = len(self.orbit)
        logger.debug("CycleEcho.orbit_size exit result=%d", result)
        return result

    @property
    def words(self) -> tuple[str, ...]:
        """Return deterministic external display words for the orbit."""
        logger.debug("CycleEcho.words entry")
        result = tuple(sorted("".join(item) if item else "ε" for item in self.orbit))
        logger.debug("CycleEcho.words exit result=%r", result)
        return result

    def contains(self, mode: Mode) -> bool:
        """Return whether a mode presentation belongs to this cycle echo."""
        logger.debug("CycleEcho.contains entry mode=%s", mode.word)
        result = mode.tacts in self.orbit
        logger.debug("CycleEcho.contains exit result=%s", result)
        return result


def cycle_echo(mode: Mode) -> CycleEcho:
    """Return rotation-orbit echo object for a mode without picking a canonical cut."""
    logger.debug("cycle_echo entry mode=%s", mode.word)
    if mode.length == 0:
        result = CycleEcho(frozenset({()}))
    else:
        result = CycleEcho(frozenset(rotate_mode(mode, offset).tacts for offset in range(mode.length)))
    logger.debug("cycle_echo exit orbit_size=%d words=%r", result.orbit_size, result.words)
    return result


def cycle_equivalent(left: Mode, right: Mode) -> bool:
    """Return True iff two mode presentations have the same cycle echo."""
    logger.debug("cycle_equivalent entry left=%s right=%s", left.word, right.word)
    result = cycle_echo(left) == cycle_echo(right)
    logger.debug("cycle_equivalent exit result=%s", result)
    return result


def cyclic_weave_echo(driver: Mode, mapping: dict[str, Mode]) -> CycleEcho:
    """Return cyclic weave as an internal cycle-echo object, not a chosen word."""
    logger.debug("cyclic_weave_echo entry driver=%s keys=%r", driver.word, sorted(mapping))
    result = cycle_echo(substitute_mode(driver, mapping))
    logger.debug("cyclic_weave_echo exit words=%r", result.words)
    return result


@dataclass(frozen=True)
class PrimitiveCountRow:
    """Ordered primitive count versus cyclic primitive echo count for one length."""

    length: int
    ordered_primitives: int
    cyclic_primitives: int
    collapse: int


def primitive_count_table(alphabet: Iterable[str], max_len: int, min_len: int = 1) -> tuple[PrimitiveCountRow, ...]:
    """Compare ordered primitive words with unique primitive cycle echoes by length."""
    logger.debug("primitive_count_table entry max_len=%d min_len=%d", max_len, min_len)
    if min_len < 1 or max_len < min_len:
        logger.error("primitive_count_table invalid bounds min=%d max=%d", min_len, max_len)
        raise ValueError("bounds must satisfy 1 <= min_len <= max_len")
    symbols = tuple(alphabet)
    rows: list[PrimitiveCountRow] = []
    for length in range(min_len, max_len + 1):
        modes = [item for item in enumerate_modes(symbols, length, include_silent=False) if item.length == length]
        ordered = [item for item in modes if is_ordered_primitive(item)]
        cyclic = {cycle_echo(item) for item in ordered}
        rows.append(PrimitiveCountRow(length, len(ordered), len(cyclic), len(ordered) - len(cyclic)))
    result = tuple(rows)
    logger.debug("primitive_count_table exit rows=%r", result)
    return result


@dataclass(frozen=True)
class PrimitivePhaseProfile:
    """Bridge between phase resonance and cyclic primitive structure."""

    part: Mode
    whole: Mode
    part_echo: CycleEcho
    whole_echo: CycleEcho
    part_primitive: bool
    whole_primitive: bool
    exponent: int
    resonance: ResonanceProfile


def primitive_phase_profile(part: Mode, whole: Mode) -> PrimitivePhaseProfile:
    """Return resonance profile enriched with primitive cycle-echo facts."""
    logger.debug("primitive_phase_profile entry part=%s whole=%s", part.word, whole.word)
    resonance = resonance_profile(part, whole)
    exponent = 0 if part.length == 0 or whole.length % part.length else whole.length // part.length
    result = PrimitivePhaseProfile(part, whole, cycle_echo(part), cycle_echo(whole), is_ordered_primitive(part), is_ordered_primitive(whole), exponent, resonance)
    logger.debug("primitive_phase_profile exit result=%r", result)
    return result


@dataclass(frozen=True)
class SpectrumCompressionRow:
    """One candidate compared under spectrum rank and compression rank."""

    part: Mode
    spectrum_rank: int
    compression_rank: int | None
    defect_count: int | None
    saving: float | None
    exact: bool
    obstruction: str


def compare_spectrum_compression(whole: Mode, candidates: Iterable[Mode], max_defects: int, weights: CompressionWeights = CompressionWeights()) -> tuple[SpectrumCompressionRow, ...]:
    """Compare resonance-spectrum order with compression-score order."""
    logger.debug("compare_spectrum_compression entry whole=%s max_defects=%d", whole.word, max_defects)
    spectrum = resonance_spectrum(whole, candidates, max_defects, include_nonresonant=True)
    scores = compression_scores(whole, [entry.part for entry in spectrum], max_defects, weights)
    score_by_part: dict[Mode, tuple[int, CompressionEntry]] = {item.part: (rank, item) for rank, item in enumerate(scores)}
    rows = []
    for rank, entry in enumerate(spectrum):
        score = score_by_part.get(entry.part)
        rows.append(SpectrumCompressionRow(entry.part, rank, None if score is None else score[0], entry.defect_count, None if score is None else score[1].saving, entry.exact, entry.profile.obstruction))
    result = tuple(sorted(rows, key=lambda item: (item.spectrum_rank, inf if item.compression_rank is None else item.compression_rank)))
    logger.debug("compare_spectrum_compression exit rows=%d", len(result))
    return result


@dataclass(frozen=True)
class CycleDivisibilityRow:
    """Cycle-echo divisibility attempt with explicit obstruction."""

    part: Mode
    whole: Mode
    exponent: int
    lift_word: str
    status: str
    obstruction: str


@dataclass(frozen=True)
class PrimeObstructionRow:
    """Resonance-prime variant row with school-prime shadow kept separate."""

    mode: Mode
    profile: PrimeProfile
    status: str
    obstruction: str


@dataclass(frozen=True)
class RankFactorRow:
    """Spectrum/compression row enriched with native factor-lift status."""

    part: Mode
    spectrum_rank: int
    compression_rank: int | None
    factor_status: str
    lift_word: str
    obstruction: str


def cycle_divisibility_row(part: Mode, whole: Mode) -> CycleDivisibilityRow:
    """Return whether repeated part reconstructs whole up to cycle echo."""
    logger.debug("cycle_divisibility_row entry part=%s whole=%s", part.word, whole.word)
    if part.length == 0:
        result = CycleDivisibilityRow(part, whole, 0, "ε", "blocked", "silent-part")
    elif whole.length % part.length:
        result = CycleDivisibilityRow(part, whole, 0, "ε", "blocked", "length-obstruction")
    else:
        exponent = whole.length // part.length
        lift = repeat_mode(part, exponent)
        ok = cycle_equivalent(lift, whole)
        result = CycleDivisibilityRow(part, whole, exponent, lift.word, "divides" if ok else "blocked", "none" if ok else "cycle-mismatch")
    logger.debug("cycle_divisibility_row exit result=%r", result)
    return result


def prime_obstruction_rows(modes: Iterable[Mode]) -> tuple[PrimeObstructionRow, ...]:
    """Classify native resonance-prime candidates and their obstructions."""
    logger.debug("prime_obstruction_rows entry")
    rows = []
    for mode in modes:
        profile = prime_profile(mode)
        status = "variant" if mode.length > 1 and profile.cyclic_primitive else "blocked"
        obstruction = "none" if status == "variant" else "unit-or-silent" if mode.length <= 1 else "cycle-power"
        rows.append(PrimeObstructionRow(mode, profile, status, obstruction))
    result = tuple(rows)
    logger.debug("prime_obstruction_rows exit count=%d", len(result))
    return result


def rank_factor_comparison(whole: Mode, candidates: Iterable[Mode], max_defects: int, weights: CompressionWeights = CompressionWeights()) -> tuple[RankFactorRow, ...]:
    """Compare resonance/compression ranks with native factor-lift shadows."""
    logger.debug("rank_factor_comparison entry whole=%s max_defects=%d", whole.word, max_defects)
    rows = []
    for row in compare_spectrum_compression(whole, candidates, max_defects, weights):
        div = cycle_divisibility_row(row.part, whole)
        rows.append(RankFactorRow(row.part, row.spectrum_rank, row.compression_rank, div.status, div.lift_word, div.obstruction))
    result = tuple(rows)
    logger.debug("rank_factor_comparison exit count=%d", len(result))
    return result


def native_number_theory_checklist() -> tuple[str, ...]:
    """Return Sprint X2 native number-theory acceptance checklist."""
    logger.debug("native_number_theory_checklist entry")
    result = ("cycle-echo divisibility uses repeated lifts and orbit equality", "prime variants report native obstruction rows", "rank comparisons keep spectrum/compression/factor-lift surfaces separate", "school numeric-prime facts remain profile shadows only")
    logger.debug("native_number_theory_checklist exit count=%d", len(result))
    return result


def native_number_checklist() -> tuple[str, ...]:
    """Return native resonance-number layer checklist."""
    logger.debug("native_number_checklist entry")
    result = (
        "cycle echo stores the full rotation orbit, not a lexicographic cut",
        "ordered primitive counts are compared with cyclic primitive echo counts",
        "phase resonance is paired with primitive/exponent facts",
        "spectrum rank and compression rank can be compared candidate-by-candidate",
        "legacy cyclic representatives remain only display/convenience shadows",
        "aura echoes can promote context marks into structured objects",
    )
    logger.debug("native_number_checklist exit count=%d", len(result))
    return result
