"""Finite prefix windows and their coherence for the bounded I1 experiment.

One concept end to end: the immutable prefix DTOs, the hostile-input gates that
admit them, and the executable window logic — construction, restriction,
periodic streams, and the first restriction conflict. Coherence is reported only
across the declared finite window; nothing here claims a completed tower.
"""

from __future__ import annotations

from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

MAX_PREFIX_DEPTH = 128
MAX_PREFIX_ALPHABET = 64
MAX_PREFIX_SYMBOL_BYTES = 128


@dataclass(frozen=True)
class PrefixAlphabet:
    """A finite exact alphabet used by prefix observers."""

    symbols: tuple[str, ...]


@dataclass(frozen=True)
class PrefixStage:
    """The declared finite observation at one exact depth."""

    depth: int
    symbols: tuple[str, ...]


@dataclass(frozen=True)
class PrefixTowerWindow:
    """A bounded candidate window; coherence is checked separately."""

    alphabet: PrefixAlphabet
    stages: tuple[PrefixStage, ...]


@dataclass(frozen=True)
class PrefixRestrictionObstruction:
    """The first witnessed failure of a longer prefix to restrict."""

    lower_depth: int
    upper_depth: int
    mismatch_index: int
    lower_symbol: str
    projected_symbol: str


@dataclass(frozen=True)
class PrefixCoherenceReport:
    """Finite-only coherence status for one captured prefix window."""

    maximum_depth: int
    checked_links: int
    coherent: bool
    first_obstruction: PrefixRestrictionObstruction | None
    scope: str = "finite-window"


class InfinityPrefixValidationError(ValueError):
    """A prefix DTO failed exact finite-shape validation."""


def snapshot_prefix_alphabet(value: PrefixAlphabet) -> PrefixAlphabet:
    """Capture and validate an exact immutable finite alphabet."""
    logger.debug("snapshot_prefix_alphabet entry")
    if type(value) is not PrefixAlphabet:
        logger.error("snapshot_prefix_alphabet invalid container type")
        raise InfinityPrefixValidationError("alphabet must be an exact PrefixAlphabet")
    try:
        symbols = value.symbols
    except AttributeError as exc:
        logger.error("snapshot_prefix_alphabet missing field")
        raise InfinityPrefixValidationError("alphabet is missing required fields") from exc
    if type(symbols) is not tuple or not 1 <= len(symbols) <= MAX_PREFIX_ALPHABET:
        logger.error("snapshot_prefix_alphabet invalid symbol container")
        raise InfinityPrefixValidationError("alphabet symbols must be a bounded nonempty exact tuple")
    captured: list[str] = []
    for symbol in symbols:
        if type(symbol) is not str:
            logger.error("snapshot_prefix_alphabet invalid symbol type")
            raise InfinityPrefixValidationError("alphabet symbols must be exact strings")
        if not symbol or len(symbol) > MAX_PREFIX_SYMBOL_BYTES:
            logger.error("snapshot_prefix_alphabet invalid symbol character bound")
            raise InfinityPrefixValidationError("alphabet symbols must be nonempty and bounded")
        encoded_bytes = len(symbol.encode("utf-8"))
        if encoded_bytes > MAX_PREFIX_SYMBOL_BYTES:
            logger.error("snapshot_prefix_alphabet invalid symbol bytes=%d", encoded_bytes)
            raise InfinityPrefixValidationError("alphabet symbols must be nonempty and bounded")
        captured.append(symbol)
    result = PrefixAlphabet(tuple(captured))
    if len(frozenset(result.symbols)) != len(result.symbols):
        logger.error("snapshot_prefix_alphabet duplicate symbols")
        raise InfinityPrefixValidationError("alphabet symbols must be unique")
    logger.debug("snapshot_prefix_alphabet exit symbols=%d", len(result.symbols))
    return result


def snapshot_prefix_stage(value: PrefixStage, alphabet: PrefixAlphabet) -> PrefixStage:
    """Capture one exact stage without imposing cross-stage coherence."""
    logger.debug("snapshot_prefix_stage entry")
    alphabet = snapshot_prefix_alphabet(alphabet)
    result = snapshot_unbound_prefix_stage(value)
    allowed = frozenset(alphabet.symbols)
    if any(symbol not in allowed for symbol in result.symbols):
        logger.error("snapshot_prefix_stage foreign symbol")
        raise InfinityPrefixValidationError("stage contains a foreign symbol")
    logger.debug("snapshot_prefix_stage exit depth=%d", result.depth)
    return result


def snapshot_unbound_prefix_stage(value: PrefixStage) -> PrefixStage:
    """Capture exact stage structure where no alphabet parameter is available."""
    logger.debug("snapshot_unbound_prefix_stage entry")
    if type(value) is not PrefixStage:
        logger.error("snapshot_unbound_prefix_stage invalid container type")
        raise InfinityPrefixValidationError("stage must be an exact PrefixStage")
    try:
        depth, symbols = value.depth, value.symbols
    except AttributeError as exc:
        logger.error("snapshot_unbound_prefix_stage missing field")
        raise InfinityPrefixValidationError("stage is missing required fields") from exc
    if type(depth) is not int or not 0 <= depth <= MAX_PREFIX_DEPTH:
        logger.error("snapshot_unbound_prefix_stage invalid depth")
        raise InfinityPrefixValidationError("stage depth must be a bounded exact integer")
    if type(symbols) is not tuple or len(symbols) != depth:
        logger.error("snapshot_unbound_prefix_stage invalid length depth=%d", depth)
        raise InfinityPrefixValidationError("stage symbols must be an exact tuple matching its depth")
    captured: list[str] = []
    for symbol in symbols:
        if type(symbol) is not str:
            logger.error("snapshot_unbound_prefix_stage nonexact symbol")
            raise InfinityPrefixValidationError("stage contains a nonexact symbol")
        if not symbol or len(symbol) > MAX_PREFIX_SYMBOL_BYTES:
            logger.error("snapshot_unbound_prefix_stage invalid symbol character bound")
            raise InfinityPrefixValidationError("stage contains an empty or unbounded symbol")
        if len(symbol.encode("utf-8")) > MAX_PREFIX_SYMBOL_BYTES:
            logger.error("snapshot_unbound_prefix_stage unbounded symbol")
            raise InfinityPrefixValidationError("stage contains an empty or unbounded symbol")
        captured.append(symbol)
    result = PrefixStage(depth, tuple(captured))
    logger.debug("snapshot_unbound_prefix_stage exit depth=%d", result.depth)
    return result


def snapshot_prefix_window(value: PrefixTowerWindow) -> PrefixTowerWindow:
    """Deep-capture a structurally valid finite candidate window."""
    logger.debug("snapshot_prefix_window entry")
    if type(value) is not PrefixTowerWindow:
        logger.error("snapshot_prefix_window invalid container type")
        raise InfinityPrefixValidationError("window must be an exact PrefixTowerWindow")
    try:
        source_alphabet, source_stages = value.alphabet, value.stages
    except AttributeError as exc:
        logger.error("snapshot_prefix_window missing field")
        raise InfinityPrefixValidationError("window is missing required fields") from exc
    alphabet = snapshot_prefix_alphabet(source_alphabet)
    if type(source_stages) is not tuple or not 1 <= len(source_stages) <= MAX_PREFIX_DEPTH + 1:
        logger.error("snapshot_prefix_window invalid stages container")
        raise InfinityPrefixValidationError("window stages must be a bounded nonempty exact tuple")
    stages = tuple(snapshot_prefix_stage(stage, alphabet) for stage in source_stages)
    if tuple(stage.depth for stage in stages) != tuple(range(len(stages))):
        logger.error("snapshot_prefix_window noncontiguous depths")
        raise InfinityPrefixValidationError("window stages must cover each depth from zero")
    result = PrefixTowerWindow(alphabet, stages)
    logger.debug("snapshot_prefix_window exit depth=%d", len(stages) - 1)
    return result


def prefix_alphabet(symbols: tuple[str, ...]) -> PrefixAlphabet:
    """Build an exact bounded prefix alphabet."""
    logger.debug("prefix_alphabet entry")
    result = snapshot_prefix_alphabet(PrefixAlphabet(symbols))
    logger.debug("prefix_alphabet exit symbols=%d", len(result.symbols))
    return result


def prefix_tower_window(
    alphabet: PrefixAlphabet, rows: tuple[tuple[str, ...], ...]
) -> PrefixTowerWindow:
    """Build a structurally valid candidate, including incoherent candidates."""
    logger.debug("prefix_tower_window entry")
    alphabet = snapshot_prefix_alphabet(alphabet)
    if type(rows) is not tuple or not 1 <= len(rows) <= MAX_PREFIX_DEPTH + 1:
        logger.error("prefix_tower_window invalid row container")
        raise InfinityPrefixValidationError("rows must be a bounded nonempty exact tuple")
    stages: list[PrefixStage] = []
    for depth, row in enumerate(rows):
        if type(row) is not tuple:
            logger.error("prefix_tower_window invalid row type depth=%d", depth)
            raise InfinityPrefixValidationError("each prefix row must be an exact tuple")
        stages.append(PrefixStage(depth, row))
    result = snapshot_prefix_window(PrefixTowerWindow(alphabet, tuple(stages)))
    logger.debug("prefix_tower_window exit depth=%d", len(result.stages) - 1)
    return result


def prefix_stage(
    alphabet: PrefixAlphabet, depth: int, symbols: tuple[str, ...]
) -> PrefixStage:
    """Build one canonical finite stage at its explicit observer depth."""
    logger.debug("prefix_stage entry")
    alphabet = snapshot_prefix_alphabet(alphabet)
    if type(depth) is not int:
        logger.error("prefix_stage invalid depth type")
        raise InfinityPrefixValidationError("stage depth must be an exact integer")
    if type(symbols) is not tuple:
        logger.error("prefix_stage invalid symbols container")
        raise InfinityPrefixValidationError("stage symbols must be an exact tuple")
    result = snapshot_prefix_stage(PrefixStage(depth, symbols), alphabet)
    logger.debug("prefix_stage exit depth=%d", result.depth)
    return result


def restrict_prefix(
    stage: PrefixStage, target_depth: int
) -> PrefixStage:
    """Project one finite prefix stage to an explicitly smaller depth."""
    logger.debug("restrict_prefix entry")
    stage = snapshot_unbound_prefix_stage(stage)
    if type(target_depth) is not int or not 0 <= target_depth <= stage.depth:
        logger.error("restrict_prefix invalid target depth")
        raise InfinityPrefixValidationError("restriction depth must be an exact in-range integer")
    result = PrefixStage(target_depth, stage.symbols[:target_depth])
    logger.debug("restrict_prefix exit depth=%d", result.depth)
    return result


def periodic_prefix_window(
    alphabet: PrefixAlphabet, period: tuple[str, ...], depth: int
) -> PrefixTowerWindow:
    """Construct all finite prefixes of one periodic stream through depth."""
    logger.debug("periodic_prefix_window entry")
    alphabet = snapshot_prefix_alphabet(alphabet)
    if type(depth) is not int or not 0 <= depth <= MAX_PREFIX_DEPTH:
        logger.error("periodic_prefix_window invalid depth")
        raise InfinityPrefixValidationError("depth must be a bounded exact integer")
    if type(period) is not tuple or not period:
        logger.error("periodic_prefix_window invalid period container")
        raise InfinityPrefixValidationError("period must be a nonempty exact tuple")
    allowed = frozenset(alphabet.symbols)
    if any(type(symbol) is not str or symbol not in allowed for symbol in period):
        logger.error("periodic_prefix_window foreign or nonexact period symbol")
        raise InfinityPrefixValidationError("period contains a foreign or nonexact symbol")
    stream = tuple(period[index % len(period)] for index in range(depth))
    rows = tuple(stream[:stage_depth] for stage_depth in range(depth + 1))
    result = prefix_tower_window(alphabet, rows)
    logger.debug("periodic_prefix_window exit depth=%d", depth)
    return result


def first_prefix_obstruction(
    window: PrefixTowerWindow,
) -> PrefixRestrictionObstruction | None:
    """Return the first finite restriction conflict, if one is witnessed."""
    logger.debug("first_prefix_obstruction entry")
    window = snapshot_prefix_window(window)
    for upper_depth in range(1, len(window.stages)):
        lower = window.stages[upper_depth - 1]
        upper = window.stages[upper_depth]
        for index, lower_symbol in enumerate(lower.symbols):
            projected_symbol = upper.symbols[index]
            if projected_symbol != lower_symbol:
                result = PrefixRestrictionObstruction(
                    lower.depth, upper.depth, index, lower_symbol, projected_symbol
                )
                logger.debug("first_prefix_obstruction exit result=%r", result)
                return result
    logger.debug("first_prefix_obstruction exit result=None")
    return None


def prefix_coherence_report(window: PrefixTowerWindow) -> PrefixCoherenceReport:
    """Report only the declared finite window's restriction coherence."""
    logger.debug("prefix_coherence_report entry")
    window = snapshot_prefix_window(window)
    obstruction = first_prefix_obstruction(window)
    depth = len(window.stages) - 1
    checked_links = depth if obstruction is None else obstruction.upper_depth
    result = PrefixCoherenceReport(
        depth, checked_links, obstruction is None, obstruction
    )
    logger.debug("prefix_coherence_report exit coherent=%s", result.coherent)
    return result
