"""Cheap hostile-safe result envelope checks before semantic replay."""

from __future__ import annotations

import logging

from ..types import ConfluenceObstruction, ConfluenceStatus
from ...observer.relations.types import LawStatus, LossStatus, RelationClass
from .types import (
    C3TransportMode, TRANSLATED_CONFLUENCE_NONCLAIMS,
    TranslatedConfluenceJudgment, TranslatedConfluenceResourceLimit,
    TranslatedResponseRow, TranslatedResourceBound, TranslatedResourceSource,
    TranslatedTransport2CellArtifact, TranslationDirection,
)
from .validation import hex_digest, reject

logger = logging.getLogger(__name__)


def _get(value: object, names: tuple[str, ...], reason: str) -> tuple[object, ...]:
    """Read exact declared fields without user-defined property dispatch."""
    logger.debug("c3 result shallow get entry reason=%s", reason)
    try:
        result = tuple(object.__getattribute__(value, name) for name in names)
    except AttributeError:
        reject(reason)
    logger.debug("c3 result shallow get exit fields=%d", len(result))
    return result


def _digest(value: object, field: str, *, optional_empty: bool = False) -> None:
    """Validate a digest scalar, optionally admitting the typed empty marker."""
    logger.debug("c3 result shallow digest entry field=%s", field)
    if optional_empty and value == "":
        logger.debug("c3 result shallow digest exit empty field=%s", field)
        return
    hex_digest(value, field)
    logger.debug("c3 result shallow digest exit field=%s", field)


def _nonclaims(value: object) -> None:
    """Validate the canonical bounded nonclaim tuple before replay."""
    logger.debug("c3 result shallow nonclaims entry")
    if (
        type(value) is not tuple or len(value) != len(TRANSLATED_CONFLUENCE_NONCLAIMS)
        or any(type(item) is not str for item in value)
        or value != TRANSLATED_CONFLUENCE_NONCLAIMS
    ):
        reject("translated-result-nonclaims-drift")
    logger.debug("c3 result shallow nonclaims exit")


def _obstruction(value: object, field: str) -> None:
    """Validate one exact optional obstruction without dataclass equality."""
    logger.debug("c3 result shallow obstruction entry field=%s", field)
    if value is None:
        logger.debug("c3 result shallow obstruction exit absent")
        return
    if type(value) is not ConfluenceObstruction:
        reject(f"translated-{field}-must-be-exact")
    row = _get(
        value, ("lane", "occurrence", "observer_id", "outcome"),
        f"translated-{field}-missing-fields",
    )
    if any(type(item) is not str for item in (row[0], row[2], row[3])) or type(row[1]) is not int:
        reject(f"translated-{field}-field-type")
    try:
        state = vars(value)
    except TypeError:
        reject(f"translated-{field}-state")
    if set(state) != {"lane", "occurrence", "observer_id", "outcome"}:
        reject(f"translated-{field}-unexpected-fields")
    logger.debug("c3 result shallow obstruction exit present")


def _row(value: object) -> None:
    """Validate one exact response row's complete scalar shape."""
    logger.debug("c3 result shallow row entry")
    if type(value) is not TranslatedResponseRow:
        reject("translated-response-row-must-be-exact")
    row = _get(value, TranslatedResponseRow.__slots__, "translated-response-row-missing-fields")
    if (
        any(type(row[index]) is not int for index in (0, 1, 2))
        or any(type(row[index]) is not str for index in range(3, 9))
        or type(row[9]) is not ConfluenceStatus or type(row[10]) is not str
        or any(type(row[index]) is not str for index in range(11, 15))
    ):
        reject("translated-response-row-field-type")
    for index in (11, 13, 14):
        _digest(row[index], "translated-response-row-digest")
    _digest(row[12], "translated-response-row-translated-digest", optional_empty=True)
    logger.debug("c3 result shallow row exit")


def _cell(value: object) -> None:
    """Validate cell mode/direction/digests and bounded rows before replay."""
    logger.debug("c3 result shallow cell entry")
    if type(value) is not TranslatedTransport2CellArtifact:
        reject("translated-cell-must-be-exact")
    row = _get(value, TranslatedTransport2CellArtifact.__slots__, "translated-cell-missing-fields")
    if (
        any(type(row[index]) is not str for index in (*range(0, 14), *range(17, 21), 25))
        or type(row[14]) is not TranslationDirection
        or type(row[15]) is not tuple or len(row[15]) != 2
        or any(type(item) is not str for item in row[15])
        or type(row[16]) is not tuple or len(row[16]) > 513
        or type(row[22]) is not int or type(row[23]) is not ConfluenceStatus
        or type(row[24]) is not C3TransportMode
    ):
        reject("translated-cell-field-type-or-length")
    for index in (*range(0, 14), *range(17, 21)):
        _digest(row[index], "translated-cell-digest", optional_empty=index == 8)
    if row[24] is not C3TransportMode.TYPED_TRANSLATION:
        reject("translated-cell-mode-drift")
    _obstruction(row[21], "cell-obstruction")
    for item in row[16]:
        _row(item)
    logger.debug("c3 result shallow cell exit rows=%d", len(row[16]))


def _judgment(value: object) -> None:
    """Validate complete judgment envelope before any fresh semantic replay."""
    logger.debug("c3 result shallow judgment entry")
    if type(value) is not TranslatedConfluenceJudgment:
        reject("translated-judgment-must-be-exact")
    row = _get(value, TranslatedConfluenceJudgment.__slots__, "translated-judgment-missing-fields")
    if (
        any(type(row[index]) is not str for index in (*range(0, 11), 20, 21))
        or type(row[11]) is not LawStatus or type(row[12]) is not LawStatus
        or type(row[13]) is not RelationClass or type(row[14]) is not LossStatus
        or type(row[15]) is not TranslationDirection or type(row[16]) is not ConfluenceStatus
        or (row[17] is not None and type(row[17]) is not TranslatedTransport2CellArtifact)
        or type(row[19]) is not int or type(row[22]) is not C3TransportMode
    ):
        reject("translated-judgment-field-type")
    for index in (*range(0, 11), 20, 21):
        _digest(row[index], "translated-judgment-digest")
    if row[22] is not C3TransportMode.TYPED_TRANSLATION:
        reject("translated-judgment-mode-drift")
    _nonclaims(row[23])
    _obstruction(row[18], "judgment-obstruction")
    if row[17] is not None:
        _cell(row[17])
    logger.debug("c3 result shallow judgment exit")


def _refusal(value: object) -> None:
    """Validate complete payload-free refusal and closed failing bound."""
    logger.debug("c3 result shallow refusal entry")
    if type(value) is not TranslatedConfluenceResourceLimit:
        reject("translated-resource-refusal-must-be-exact")
    row = _get(value, TranslatedConfluenceResourceLimit.__slots__, "translated-resource-refusal-missing-fields")
    if (
        any(type(row[index]) is not str for index in (0, 1, 2, 3, 4, 5, 14, 15))
        or any(type(row[index]) is not int for index in (6, 7, 8, 9, 12, 13))
        or type(row[10]) is not TranslatedResourceBound
        or type(row[11]) is not TranslatedResourceSource
    ):
        reject("translated-resource-refusal-field-type")
    for index in (1, 2, 3, 4, 5, 14):
        _digest(row[index], "translated-resource-refusal-digest")
    if row[15] != "resource-limit":
        reject("translated-resource-refusal-status-drift")
    _nonclaims(row[16])
    logger.debug("c3 result shallow refusal exit")


def shallow_result(value: object) -> None:
    """Apply exact closed-union shallow validation without semantic calls."""
    logger.debug("c3 shallow_result entry type=%s", type(value).__name__)
    if type(value) is TranslatedConfluenceJudgment:
        _judgment(value)
    elif type(value) is TranslatedConfluenceResourceLimit:
        _refusal(value)
    else:
        reject("translated-result-variant-drift")
    logger.debug("c3 shallow_result exit")
