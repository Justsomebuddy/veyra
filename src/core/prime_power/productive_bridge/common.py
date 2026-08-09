"""Exact framing and fail-closed validation for P3-A1b."""

from __future__ import annotations

from dataclasses import fields
from hashlib import sha256
import logging

logger = logging.getLogger(__name__)


class ProductiveBridgeValidationError(ValueError):
    """Typed malformed/foreign/circular source rejection."""


def reject(reason: str) -> None:
    """Log and raise one sanitized validation error."""
    logger.error("P3-A1b rejected reason=%s", reason)
    raise ProductiveBridgeValidationError(reason)


def sha(payload: bytes) -> str:
    """Hash exact bytes."""
    logger.debug("sha entry bytes=%d", len(payload))
    result = sha256(payload).hexdigest()
    logger.debug("sha exit")
    return result


def digest(domain: str, rows: tuple[tuple[str, bytes], ...]) -> str:
    """Hash a length-framed, ordered, domain-separated record."""
    logger.debug("digest entry domain=%s rows=%d", domain, len(rows))
    if type(domain) is not str or type(rows) is not tuple:
        reject("digest-shape-invalid")
    out = bytearray(b"A1B1")
    for item in (domain.encode(),):
        out += len(item).to_bytes(8, "big") + item
    for label, value in rows:
        if type(label) is not str or type(value) is not bytes:
            reject("digest-row-invalid")
        for item in (label.encode(), value):
            out += len(item).to_bytes(8, "big") + item
    result = sha(bytes(out))
    logger.debug("digest exit")
    return result


def exact_shape(value: object, cls: type, label: str) -> dict[str, object]:
    """Return a real exact field dict without invoking hostile equality/callbacks."""
    logger.debug("exact_shape entry label=%s", label)
    if type(value) is not cls:
        reject(f"{label}-shape-invalid")
    try:
        raw = object.__getattribute__(value, "__dict__")
    except (AttributeError, TypeError):
        reject(f"{label}-shape-invalid")
    required = tuple(x.name for x in fields(cls))
    if type(raw) is not dict or tuple(raw) != required:
        reject(f"{label}-shape-invalid")
    logger.debug("exact_shape exit")
    return raw


def exact_digest(value: object, label: str) -> None:
    """Require canonical lowercase SHA-256 text."""
    logger.debug("exact_digest entry label=%s", label)
    if type(value) is not str or len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
        reject(f"{label}-invalid")
    logger.debug("exact_digest exit")


def exact_text(value: object, label: str) -> str:
    """Require a built-in string before any encoding or comparison."""
    logger.debug("exact_text entry label=%s", label)
    if type(value) is not str:
        reject(f"{label}-invalid")
    logger.debug("exact_text exit")
    return value


def exact_int(value: object, label: str) -> int:
    """Require a built-in integer, excluding bool and integer subclasses."""
    logger.debug("exact_int entry label=%s", label)
    if type(value) is not int:
        reject(f"{label}-invalid")
    logger.debug("exact_int exit")
    return value


def signed_bytes(value: object, label: str, max_bits: int | None = None) -> bytes:
    """Encode an exact signed integer without decimal conversion or callbacks."""
    logger.debug("signed_bytes entry label=%s", label)
    number = exact_int(value, label)
    bits = number.bit_length() + 1
    if max_bits is not None and bits > max_bits:
        reject(f"{label}-too-large")
    size = max(1, (bits + 7) // 8)
    result = number.to_bytes(size, "big", signed=True)
    logger.debug("signed_bytes exit bytes=%d", len(result))
    return result
