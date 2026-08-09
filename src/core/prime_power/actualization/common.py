"""Canonical primitives and hostile-input rejection for P3-N0."""

from __future__ import annotations

import hashlib
import logging
from dataclasses import fields

logger = logging.getLogger(__name__)


class N0ValidationError(ValueError):
    """Malformed or identity-drifting P3-N0 input."""


def reject(reason: str) -> None:
    """Log and raise the sole malformed-input exception."""
    logger.debug("reject entry reason=%s", reason)
    logger.debug("reject state=terminal-error")
    logger.error("P3-N0 validation rejection reason=%s", reason)
    raise N0ValidationError(reason)


def digest(domain: str, rows: tuple[tuple[str, bytes], ...]) -> str:
    """Hash ordered, length-prefixed rows without ambiguous concatenation."""
    logger.debug("digest entry domain=%s rows=%d", domain, len(rows))
    h = hashlib.sha256()
    for value in (domain.encode(), *(k.encode() + b"\0" + v for k, v in rows)):
        h.update(len(value).to_bytes(8, "big"))
        h.update(value)
    result = h.hexdigest()
    logger.debug("digest exit domain=%s", domain)
    return result


def indexed(label: str, values) -> tuple[tuple[str, bytes], ...]:
    """Encode an already-bounded sequence as ordered digest rows."""
    logger.debug("indexed entry label=%s", label)
    try:
        result = tuple((f"{label}-{i}", str(v).encode("utf-8"))
                       for i, v in enumerate(values))
    except (UnicodeError, TypeError):
        reject(f"{label}-indexed-encoding-invalid")
    logger.debug("indexed exit label=%s count=%d", label, len(result))
    return result


def exact_int(value, label: str, *, minimum: int = 0, maximum: int) -> int:
    """Accept exact bounded integers and reject Python's Boolean subtype."""
    logger.debug("exact_int entry label=%s type=%s", label, type(value).__name__)
    if type(value) is not int:
        reject(f"{label}-exact-int-required")
    if value < minimum or value > maximum:
        reject(f"{label}-out-of-envelope")
    logger.debug("exact_int exit label=%s", label)
    return value


def exact_text(value, label: str, *, maximum: int = 256) -> str:
    """Accept a nonempty bounded plain string."""
    logger.debug("exact_text entry label=%s", label)
    if type(value) is not str or not value:
        reject(f"{label}-text-invalid")
    try:
        encoded = value.encode("utf-8")
    except UnicodeError:
        reject(f"{label}-text-invalid")
    if len(encoded) > maximum:
        reject(f"{label}-text-invalid")
    logger.debug("exact_text exit label=%s", label)
    return value


def exact_shape(value, cls, label: str) -> dict:
    """Reject subclasses, proxies, missing slots, and extra state."""
    logger.debug("exact_shape entry label=%s", label)
    if type(value) is not cls:
        reject(f"{label}-exact-type-required")
    names = tuple(field.name for field in fields(cls))
    try:
        raw = {name: object.__getattribute__(value, name) for name in names}
        state = object.__getattribute__(value, "__dict__")
    except (AttributeError, TypeError):
        reject(f"{label}-malformed")
    if tuple(state) != names:
        reject(f"{label}-shape-invalid")
    logger.debug("exact_shape exit label=%s", label)
    return raw


def exact_hex(value, label: str) -> str:
    """Validate one lowercase SHA-256 identity."""
    logger.debug("exact_hex entry label=%s", label)
    if (type(value) is not str or len(value) != 64
            or any(c not in "0123456789abcdef" for c in value)):
        reject(f"{label}-digest-invalid")
    logger.debug("exact_hex exit label=%s", label)
    return value
