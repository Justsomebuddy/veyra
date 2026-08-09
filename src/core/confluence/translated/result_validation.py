"""Hostile-safe fresh result validation for P1-C3."""

from __future__ import annotations

from dataclasses import fields
from enum import Enum
import logging

from ..types import ConfluenceObstruction
from .runtime import translated_confluence_judgment
from .result_shallow import shallow_result
from .types import (
    TranslatedConfluenceJudgment, TranslatedConfluencePolicy,
    TranslatedConfluenceResourceLimit, TranslatedConfluenceResult,
    TranslatedEchoTransportSpec, TranslatedResponseRow,
    TranslatedTransport2CellArtifact,
)
from .validation import reject

logger = logging.getLogger(__name__)


def _declared(value: object, kind: type, field: str) -> None:
    """Require exact type, every field, and no dynamic extra instance state."""
    logger.debug("c3 result declared entry field=%s", field)
    if type(value) is not kind:
        reject(f"translated-{field}-must-be-exact")
    names = {item.name for item in fields(kind)}
    try:
        for name in names:
            object.__getattribute__(value, name)
        state = vars(value) if hasattr(value, "__dict__") else {}
    except (AttributeError, TypeError):
        reject(f"translated-{field}-missing-fields")
    if state and set(state) != names:
        reject(f"translated-{field}-unexpected-fields")
    logger.debug("c3 result declared exit field=%s", field)


def _primitive(raw: object, expected: object, names: tuple[str, ...], field: str) -> None:
    """Compare already declared primitive and enum fields without DTO equality."""
    logger.debug("c3 result primitive entry field=%s", field)
    for name in names:
        supplied, wanted = object.__getattribute__(raw, name), object.__getattribute__(expected, name)
        if type(supplied) is not type(wanted):
            reject(f"translated-{field}-drift")
        if isinstance(wanted, Enum):
            if supplied is not wanted:
                reject(f"translated-{field}-drift")
        elif supplied != wanted:
            reject(f"translated-{field}-drift")
    logger.debug("c3 result primitive exit field=%s", field)


def _nonclaims(raw: object, expected: tuple[str, ...], field: str) -> None:
    """Require the exact permanent nonclaim tuple."""
    logger.debug("c3 result nonclaims entry")
    if (
        type(raw) is not tuple or len(raw) != len(expected)
        or any(type(item) is not str for item in raw) or raw != expected
    ):
        reject(f"translated-{field}-drift")
    logger.debug("c3 result nonclaims exit")


def _obstruction(raw: object, expected: object, field: str) -> None:
    """Validate one exact optional C1 obstruction field-by-field."""
    logger.debug("c3 result obstruction entry field=%s", field)
    if expected is None:
        if raw is not None:
            reject(f"translated-{field}-drift")
    else:
        _declared(raw, ConfluenceObstruction, field)
        _primitive(raw, expected, ("lane", "occurrence", "observer_id", "outcome"), field)
    logger.debug("c3 result obstruction exit field=%s", field)


def _row(raw: object, expected: TranslatedResponseRow, index: int) -> None:
    """Validate one occurrence row after the enclosing count is fixed."""
    logger.debug("c3 result row entry index=%d", index)
    _declared(raw, TranslatedResponseRow, "response-row")
    _primitive(raw, expected, tuple(item.name for item in fields(TranslatedResponseRow)), "response-row")
    logger.debug("c3 result row exit index=%d", index)


def _cell(raw: object, expected: object) -> None:
    """Validate optional cell outer shape before bounded row traversal."""
    logger.debug("c3 result cell entry")
    if expected is None:
        if raw is not None:
            reject("translated-cell-drift")
        logger.debug("c3 result cell exit absent")
        return
    _declared(raw, TranslatedTransport2CellArtifact, "cell")
    try:
        rows, pair = raw.response_rows, raw.observer_pair
    except AttributeError:
        reject("translated-cell-missing-fields")
    if (
        type(rows) is not tuple or len(rows) != len(expected.response_rows)
        or type(pair) is not tuple or len(pair) != 2
        or any(type(item) is not str for item in pair)
    ):
        reject("translated-cell-outer-precheck")
    excluded = {"response_rows", "observer_pair", "first_obstruction"}
    names = tuple(item.name for item in fields(TranslatedTransport2CellArtifact) if item.name not in excluded)
    _primitive(raw, expected, names, "cell")
    if pair != expected.observer_pair:
        reject("translated-cell-pair-drift")
    _obstruction(raw.first_obstruction, expected.first_obstruction, "cell-obstruction")
    for index, (supplied, wanted) in enumerate(zip(rows, expected.response_rows, strict=True)):
        _row(supplied, wanted, index)
    logger.debug("c3 result cell exit rows=%d", len(rows))


def _judgment(raw: object, expected: TranslatedConfluenceJudgment) -> None:
    """Validate a judgment's scalar envelope before its cell."""
    logger.debug("c3 result judgment entry")
    _declared(raw, TranslatedConfluenceJudgment, "judgment")
    excluded = {"transport_cell", "first_obstruction", "nonclaims"}
    names = tuple(item.name for item in fields(TranslatedConfluenceJudgment) if item.name not in excluded)
    _primitive(raw, expected, names, "judgment")
    _nonclaims(raw.nonclaims, expected.nonclaims, "judgment-nonclaims")
    _obstruction(raw.first_obstruction, expected.first_obstruction, "judgment-obstruction")
    _cell(raw.transport_cell, expected.transport_cell)
    logger.debug("c3 result judgment exit")


def _refusal(raw: object, expected: TranslatedConfluenceResourceLimit) -> None:
    """Validate a payload-free refusal without nested semantic fields."""
    logger.debug("c3 result refusal entry")
    _declared(raw, TranslatedConfluenceResourceLimit, "resource-refusal")
    names = tuple(item.name for item in fields(TranslatedConfluenceResourceLimit) if item.name != "nonclaims")
    _primitive(raw, expected, names, "resource-refusal")
    _nonclaims(raw.nonclaims, expected.nonclaims, "resource-refusal-nonclaims")
    logger.debug("c3 result refusal exit")


def validate_translated_confluence_result(
    p0_doctrine, diagram, plan, p1a_doctrine, p1a_source, a2_stage_source,
    bridge, transport: TranslatedEchoTransportSpec,
    policy: TranslatedConfluencePolicy, value: TranslatedConfluenceResult,
) -> TranslatedConfluenceResult:
    """Recompute from raw sources and return a fresh exact expected result."""
    logger.debug("validate_translated_confluence_result entry")
    shallow_result(value)
    expected = translated_confluence_judgment(
        p0_doctrine, diagram, plan, p1a_doctrine, p1a_source,
        a2_stage_source, bridge, transport, policy,
    )
    if type(value) is not type(expected):
        reject("translated-result-variant-drift")
    if type(expected) is TranslatedConfluenceJudgment:
        _judgment(value, expected)
    elif type(expected) is TranslatedConfluenceResourceLimit:
        _refusal(value, expected)
    else:
        reject("translated-result-unknown-variant")
    logger.debug("validate_translated_confluence_result exit type=%s", type(expected).__name__)
    return expected
