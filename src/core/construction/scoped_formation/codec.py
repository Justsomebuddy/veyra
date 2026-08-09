"""Canonical framing and exact primitive validation for P1-C4."""

from __future__ import annotations

from dataclasses import fields, is_dataclass
from enum import Enum
from hashlib import sha256
import logging

logger = logging.getLogger(__name__)


class ScopedFormationValidationError(ValueError):
    """Fail-closed C4 source error."""


def identifier(value: object, field: str) -> str:
    """Capture one bounded nonempty control identifier."""
    logger.debug("identifier entry field=%s", field)
    if type(value) is not str or not value or len(value.encode()) > 128:
        logger.error("identifier rejected field=%s", field)
        raise ScopedFormationValidationError(f"invalid-{field}")
    logger.debug("identifier exit field=%s", field)
    return value


def hex_digest(value: object, field: str) -> str:
    """Require one exact lowercase SHA-256 hexadecimal digest."""
    logger.debug("hex_digest entry field=%s", field)
    if type(value) is not str or len(value) != 64:
        logger.error("hex_digest rejected field=%s", field)
        raise ScopedFormationValidationError(f"invalid-{field}")
    if any(ch not in "0123456789abcdef" for ch in value):
        logger.error("hex_digest alphabet rejected field=%s", field)
        raise ScopedFormationValidationError(f"invalid-{field}")
    logger.debug("hex_digest exit field=%s", field)
    return value


def bounded_int(value: object, field: str, minimum: int, maximum: int) -> int:
    """Require one exact bounded integer before decimal conversion or encoding."""
    logger.debug("bounded_int entry field=%s", field)
    if type(value) is not int or not minimum <= value <= maximum:
        logger.error("bounded_int rejected field=%s", field)
        raise ScopedFormationValidationError(f"invalid-{field}")
    logger.debug("bounded_int exit field=%s", field)
    return value


def canonical_bytes(value: object) -> bytes:
    """Encode a closed immutable DTO tree with tagged/count framing."""
    logger.debug("canonical_bytes entry type=%s", type(value).__name__)
    result = _encode(value)
    logger.debug("canonical_bytes exit bytes=%d", len(result))
    return result


def digest(tag: str, *values: object) -> str:
    """Digest a domain tag and canonical framed values."""
    logger.debug("digest entry tag=%s values=%d", tag, len(values))
    result = sha256(_frame(b"domain", tag.encode()) + _encode(values)).hexdigest()
    logger.debug("digest exit tag=%s", tag)
    return result


def exact_tuple(value: object, field: str, minimum: int, maximum: int) -> tuple:
    """Require an exact tuple inside a closed count interval."""
    logger.debug("exact_tuple entry field=%s", field)
    if type(value) is not tuple or not minimum <= len(value) <= maximum:
        logger.error("exact_tuple rejected field=%s", field)
        raise ScopedFormationValidationError(f"invalid-{field}")
    logger.debug("exact_tuple exit field=%s count=%d", field, len(value))
    return value


def unique(values: tuple[str, ...], field: str) -> None:
    """Reject duplicate ordered catalog keys."""
    logger.debug("unique entry field=%s count=%d", field, len(values))
    if len(set(values)) != len(values):
        logger.error("unique rejected field=%s", field)
        raise ScopedFormationValidationError(f"duplicate-{field}")
    logger.debug("unique exit field=%s", field)


def _frame(tag: bytes, payload: bytes) -> bytes:
    """Return one unambiguous tagged length frame."""
    logger.debug("_frame entry tag=%r bytes=%d", tag, len(payload))
    result = len(tag).to_bytes(2, "big") + tag + len(payload).to_bytes(8, "big") + payload
    logger.debug("_frame exit bytes=%d", len(result))
    return result


def _encode(value: object) -> bytes:
    """Recursively encode only the closed C4 raw-source value language."""
    logger.debug("_encode entry type=%s", type(value).__name__)
    if value is None:
        result = _frame(b"none", b"")
    elif type(value) is bool:
        result = _frame(b"bool", b"1" if value else b"0")
    elif type(value) is int:
        if value.bit_length() > 63:
            logger.error("_encode rejected oversized integer")
            raise ScopedFormationValidationError("noncanonical-integer-range")
        result = _frame(b"int", str(value).encode())
    elif type(value) is str:
        result = _frame(b"str", value.encode())
    elif type(value) is bytes:
        result = _frame(b"bytes", value)
    elif isinstance(value, Enum):
        result = _frame(b"enum:" + type(value).__name__.encode(), _encode(value.value))
    elif type(value) is tuple:
        result = _frame(b"tuple", len(value).to_bytes(8, "big") + b"".join(_encode(x) for x in value))
    elif is_dataclass(value) and type(value).__module__.startswith("src.core"):
        payload = len(fields(value)).to_bytes(4, "big")
        for item in fields(value):
            payload += _frame(b"field", item.name.encode()) + _encode(getattr(value, item.name))
        result = _frame(b"dto:" + type(value).__name__.encode(), payload)
    else:
        logger.error("_encode rejected type=%s", type(value).__name__)
        raise ScopedFormationValidationError("noncanonical-raw-source-value")
    logger.debug("_encode exit type=%s bytes=%d", type(value).__name__, len(result))
    return result
