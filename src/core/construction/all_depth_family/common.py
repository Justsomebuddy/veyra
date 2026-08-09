"""Hostile-safe scalar and dataclass guards for P1-D3."""

from __future__ import annotations

import logging
from typing import NoReturn

logger = logging.getLogger(__name__)
MAX_IDENTIFIER_BYTES = 128
MAX_SYMBOLIC_TERM_BYTES = 4096


class AllDepthFamilyValidationError(ValueError):
    """A D3 source, representation, proof binding, or result was invalid."""


def reject(reason: str) -> NoReturn:
    logger.error("all-depth family rejected reason=%s", reason)
    raise AllDepthFamilyValidationError(reason)


def exact_shape(value: object, expected_type: type, field: str) -> None:
    logger.debug("exact_shape entry field=%s", field)
    if type(value) is not expected_type:
        reject(f"{field}-must-be-exact")
    if set(vars(value)) != set(expected_type.__dataclass_fields__):
        reject(f"{field}-shape-drift")
    logger.debug("exact_shape exit field=%s", field)


def exact_identifier(value: object, field: str) -> str:
    logger.debug("exact_identifier entry field=%s", field)
    if type(value) is not str or not value:
        reject(f"invalid-{field}")
    try:
        size = len(value.encode("utf-8", errors="strict"))
    except UnicodeError:
        reject(f"invalid-{field}")
    if size > MAX_IDENTIFIER_BYTES:
        reject(f"invalid-{field}")
    logger.debug("exact_identifier exit field=%s bytes=%d", field, size)
    return value


def exact_digest(value: object, field: str) -> str:
    logger.debug("exact_digest entry field=%s", field)
    if (
        type(value) is not str or len(value) != 64
        or any(ch not in "0123456789abcdef" for ch in value)
    ):
        reject(f"invalid-{field}")
    logger.debug("exact_digest exit field=%s", field)
    return value


def exact_natural(value: object, field: str, maximum: int = 1_000_000) -> int:
    logger.debug("exact_natural entry field=%s", field)
    if type(value) is not int or not 0 <= value <= maximum:
        reject(f"invalid-{field}")
    logger.debug("exact_natural exit field=%s", field)
    return value


def exact_bytes(value: object, field: str, *, nonempty: bool = True) -> bytes:
    logger.debug("exact_bytes entry field=%s", field)
    if type(value) is not bytes or (nonempty and not value) or len(value) > MAX_SYMBOLIC_TERM_BYTES:
        reject(f"invalid-{field}")
    result = bytes(bytearray(value))
    logger.debug("exact_bytes exit field=%s bytes=%d", field, len(result))
    return result
