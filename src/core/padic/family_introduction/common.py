"""Exact validation and framing helpers for P3-N1."""

from __future__ import annotations

from dataclasses import fields
from hashlib import sha256
import logging

logger = logging.getLogger(__name__)


class PadicFamilyIntroductionValidationError(ValueError):
    """Typed fail-closed P3-N1 validation error."""


def reject(reason: str) -> None:
    """Log and raise one sanitized validation error."""
    logger.error("P3-N1 rejected reason=%s", reason)
    raise PadicFamilyIntroductionValidationError(reason)


def sha(payload: bytes) -> str:
    """Return SHA-256 for exact captured bytes."""
    logger.debug("sha entry bytes=%d", len(payload))
    result = sha256(payload).hexdigest()
    logger.debug("sha exit")
    return result


def frame(domain: str, rows: tuple[tuple[str, bytes], ...]) -> bytes:
    """Encode one ordered duplicate-safe domain-separated record."""
    logger.debug("frame entry domain=%s rows=%d", domain, len(rows))
    if type(domain) is not str or type(rows) is not tuple:
        reject("frame-shape-invalid")
    output = bytearray(b"N1F1")
    for value in (domain.encode(),):
        output += len(value).to_bytes(8, "big") + value
    for label, value in rows:
        if type(label) is not str or type(value) is not bytes:
            reject("frame-row-invalid")
        for item in (label.encode(), value):
            output += len(item).to_bytes(8, "big") + item
    result = bytes(output)
    logger.debug("frame exit bytes=%d", len(result))
    return result


def digest(domain: str, rows: tuple[tuple[str, bytes], ...]) -> str:
    """Digest one exact framed record."""
    logger.debug("digest entry domain=%s", domain)
    result = sha(frame(domain, rows))
    logger.debug("digest exit")
    return result


def exact_shape(value: object, cls: type, label: str) -> None:
    """Reject subclasses, extra attributes, or missing DTO fields."""
    logger.debug("exact_shape entry label=%s", label)
    if type(value) is not cls or tuple(value.__dict__) != tuple(row.name for row in fields(cls)):
        reject(f"{label}-shape-invalid")
    logger.debug("exact_shape exit label=%s", label)


def exact_digest(value: object, label: str) -> None:
    """Reject noncanonical digest strings without coercion."""
    logger.debug("exact_digest entry label=%s", label)
    if type(value) is not str or len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
        reject(f"{label}-invalid")
    logger.debug("exact_digest exit label=%s", label)
