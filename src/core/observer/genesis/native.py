"""Strict primitive AST capture and fresh native replay for P1-E1."""

from __future__ import annotations

import logging
from typing import NoReturn

from ...native_runtime import (
    Breath, Mode, Nod, Rez, Tact, breath as native_breath, mode as native_mode,
    nod as native_nod, rez as native_rez, tact as native_tact,
)
from .digest import genealogy_digest, replayed_mode_digest
from .types import BreathSpec, ModeSpec, NodSpec, RezSpec, TactSpec

logger = logging.getLogger(__name__)
GENEALOGY_VERSION = "p1-e1-native-genealogy-v1"
MAX_IDENTIFIER_BYTES = 128
MAX_GENEALOGY_TACTS = 16


class ObserverGenesisValidationError(ValueError):
    """An exact E1 source, witness, or result contract failed."""


def _reject(reason: str) -> NoReturn:
    logger.error("observer genesis rejected reason=%s", reason)
    raise ObserverGenesisValidationError(reason)


def exact_text(value: str, field: str) -> str:
    """Capture one nonempty bounded exact UTF-8 identifier."""
    logger.debug("exact_text entry field=%s", field)
    try:
        valid = type(value) is str and bool(value) and len(value.encode("utf-8")) <= MAX_IDENTIFIER_BYTES
    except UnicodeError as exc:
        logger.error("exact_text invalid unicode field=%s", field)
        raise ObserverGenesisValidationError(f"invalid-{field}") from exc
    if not valid:
        _reject(f"invalid-{field}")
    logger.debug("exact_text exit field=%s", field)
    return value


def hex_digest(value: str, field: str) -> str:
    """Capture one lowercase SHA-256 hexadecimal digest."""
    logger.debug("hex_digest entry field=%s", field)
    if type(value) is not str or len(value) != 64 or any(ch not in "0123456789abcdef" for ch in value):
        _reject(f"invalid-{field}")
    logger.debug("hex_digest exit field=%s", field)
    return value


def _snapshot_rez(value: RezSpec) -> RezSpec:
    logger.debug("_snapshot_rez entry")
    if type(value) is not RezSpec:
        _reject("rez-spec-must-be-exact")
    try:
        result = RezSpec(exact_text(value.name, "rez-name"))
    except AttributeError:
        _reject("rez-spec-missing-field")
    logger.debug("_snapshot_rez exit")
    return result


def _snapshot_nod(value: NodSpec) -> NodSpec:
    logger.debug("_snapshot_nod entry")
    if type(value) is not NodSpec:
        _reject("nod-spec-must-be-exact")
    try:
        result = NodSpec(_snapshot_rez(value.residue), exact_text(value.mark, "nod-mark"))
    except AttributeError:
        _reject("nod-spec-missing-field")
    logger.debug("_snapshot_nod exit")
    return result


def _snapshot_tact(value: TactSpec) -> TactSpec:
    logger.debug("_snapshot_tact entry")
    if type(value) is not TactSpec:
        _reject("tact-spec-must-be-exact")
    try:
        result = TactSpec(
            _snapshot_nod(value.start), _snapshot_nod(value.end),
            exact_text(value.mark, "tact-mark"),
        )
    except AttributeError:
        _reject("tact-spec-missing-field")
    logger.debug("_snapshot_tact exit")
    return result


def _snapshot_breath(value: BreathSpec) -> BreathSpec:
    logger.debug("_snapshot_breath entry")
    if type(value) is not BreathSpec:
        _reject("breath-spec-must-be-exact")
    try:
        raw = value.tacts
    except AttributeError:
        _reject("breath-spec-missing-field")
    if type(raw) is not tuple or not 1 <= len(raw) <= MAX_GENEALOGY_TACTS:
        _reject("breath-spec-must-be-bounded-nonempty-tuple")
    tacts = tuple(_snapshot_tact(item) for item in raw)
    for left, right in zip(tacts, tacts[1:]):
        if left.end != right.start:
            _reject("breath-spec-noncontiguous")
    if tacts[0].start != tacts[-1].end:
        _reject("mode-spec-not-strictly-closed")
    result = BreathSpec(tacts)
    logger.debug("_snapshot_breath exit count=%d", len(tacts))
    return result


def _replay_native(spec: BreathSpec) -> Mode:
    logger.debug("_replay_native entry tacts=%d", len(spec.tacts))
    replayed: list[Tact] = []
    for item in spec.tacts:
        start_rez = native_rez(item.start.residue.name)
        end_rez = native_rez(item.end.residue.name)
        if type(start_rez) is not Rez or type(end_rez) is not Rez:
            raise RuntimeError("native rez replay returned an unexpected value")
        start, end = native_nod(start_rez, item.start.mark), native_nod(end_rez, item.end.mark)
        if type(start) is not Nod or type(end) is not Nod:
            raise RuntimeError("native nod replay returned an unexpected value")
        row = native_tact(start, end, item.mark)
        if type(row) is not Tact:
            raise RuntimeError("native tact replay returned an unexpected value")
        replayed.append(row)
    replayed_breath = native_breath(*replayed)
    if type(replayed_breath) is not Breath:
        raise ObserverGenesisValidationError("native-breath-replay-obstructed")
    result = native_mode(replayed_breath, None)
    if type(result) is not Mode or result.observer != "native-cycle":
        raise ObserverGenesisValidationError("native-mode-replay-not-exact-cycle")
    if result.breath.tacts[0].start != result.breath.tacts[-1].end:
        raise ObserverGenesisValidationError("native-mode-replay-not-structurally-closed")
    logger.debug("_replay_native exit")
    return result


def build_mode_spec(breath: BreathSpec, version: str = GENEALOGY_VERSION) -> ModeSpec:
    """Build and replay one exact primitive-rooted genealogy."""
    logger.debug("build_mode_spec entry")
    if type(version) is not str or version != GENEALOGY_VERSION:
        _reject("unknown-genealogy-version")
    captured = _snapshot_breath(breath)
    provisional = ModeSpec(version, captured, "0" * 64)
    result = ModeSpec(version, captured, genealogy_digest(provisional))
    _replay_native(captured)
    logger.debug("build_mode_spec exit")
    return result


def snapshot_and_replay_genealogy(value: ModeSpec) -> tuple[ModeSpec, Mode, str]:
    """Deep-capture raw Spec nodes, freshly replay native constructors, and bind both."""
    logger.debug("snapshot_and_replay_genealogy entry")
    if type(value) is not ModeSpec:
        _reject("mode-spec-must-be-exact")
    try:
        expected = build_mode_spec(value.breath, value.version)
        supplied = hex_digest(value.genealogy_digest, "genealogy-digest")
    except AttributeError:
        _reject("mode-spec-missing-field")
    if supplied != expected.genealogy_digest:
        _reject("genealogy-digest-drift")
    replayed = _replay_native(expected.breath)
    native_digest = replayed_mode_digest(replayed)
    logger.debug("snapshot_and_replay_genealogy exit")
    return expected, replayed, native_digest


def origin_mode_spec() -> ModeSpec:
    """Return the exact one-tact origin cycle used by the E1 adapter."""
    logger.debug("origin_mode_spec entry")
    origin = RezSpec("origin")
    node = NodSpec(origin, "origin")
    result = build_mode_spec(BreathSpec((TactSpec(node, node, "cycle"),)))
    logger.debug("origin_mode_spec exit")
    return result
