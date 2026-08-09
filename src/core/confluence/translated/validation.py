"""Shared exact validation primitives for P1-C3."""

from __future__ import annotations

import logging
from typing import NoReturn

logger = logging.getLogger(__name__)


class TranslatedConfluenceValidationError(ValueError):
    """Malformed C3 input or returned artifact."""


def reject(reason: str) -> NoReturn:
    """Raise the one public validation error without payload logging."""
    logger.error("translated confluence rejected reason=%s", reason)
    raise TranslatedConfluenceValidationError(reason)


def identifier(value: object, field: str) -> str:
    """Validate one compact identifier."""
    logger.debug("c3 identifier entry field=%s", field)
    if (
        type(value) is not str or not 1 <= len(value) <= 128
        or any(ord(ch) < 32 or ord(ch) > 126 for ch in value)
    ):
        reject(f"invalid-{field}")
    logger.debug("c3 identifier exit field=%s", field)
    return value


def hex_digest(value: object, field: str) -> str:
    """Validate one lowercase SHA-256 hex digest."""
    logger.debug("c3 hex_digest entry field=%s", field)
    if (
        type(value) is not str or len(value) != 64
        or any(ch not in "0123456789abcdef" for ch in value)
    ):
        reject(f"invalid-{field}")
    logger.debug("c3 hex_digest exit field=%s", field)
    return value


def exact_tuple(value: object, field: str, *, minimum: int = 0, maximum: int = 4096) -> tuple:
    """Validate a bounded built-in tuple before traversal."""
    logger.debug("c3 exact_tuple entry field=%s", field)
    if type(value) is not tuple or not minimum <= len(value) <= maximum:
        reject(f"invalid-{field}")
    logger.debug("c3 exact_tuple exit field=%s count=%d", field, len(value))
    return value
