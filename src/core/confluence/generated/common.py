"""Exact primitives for P3-C1 generated confluence."""

from __future__ import annotations

from dataclasses import fields
from hashlib import sha256
import logging

logger = logging.getLogger(__name__)


class GeneratedConfluenceError(ValueError):
    """Fail-closed malformed P3-C1 input."""


def reject(reason: str) -> None:
    """Log and reject one malformed value."""
    logger.error("generated confluence reject reason=%s", reason)
    raise GeneratedConfluenceError(reason)


def exact_shape(value: object, expected: type, label: str) -> None:
    """Require the exact frozen DTO class, never a subclass/proxy."""
    logger.debug("exact_shape entry label=%s", label)
    if type(value) is not expected:
        reject(f"{label}-type-invalid")
    logger.debug("exact_shape exit label=%s", label)


def exact_text(value: object, label: str, *, nonempty: bool = True) -> str:
    """Require a bounded exact UTF-8 string."""
    logger.debug("exact_text entry label=%s", label)
    if type(value) is not str or (nonempty and not value) or len(value.encode("utf-8")) > 4096:
        reject(f"{label}-invalid")
    logger.debug("exact_text exit label=%s", label)
    return value


def exact_digest(value: object, label: str) -> str:
    """Require one lowercase SHA-256 spelling."""
    logger.debug("exact_digest entry label=%s", label)
    text = exact_text(value, label)
    if len(text) != 64 or any(ch not in "0123456789abcdef" for ch in text):
        reject(f"{label}-invalid")
    logger.debug("exact_digest exit label=%s", label)
    return text


def frame(kind: str, payload: bytes) -> bytes:
    """Encode one collision-safe kind-and-length frame."""
    logger.debug("frame entry kind=%s", kind)
    if type(kind) is not str or type(payload) is not bytes:
        reject("frame-input-type-invalid")
    result = len(kind).to_bytes(2, "big") + kind.encode() + len(payload).to_bytes(8, "big") + payload
    logger.debug("frame exit kind=%s bytes=%d", kind, len(result))
    return result


def digest(domain: str, rows: tuple[tuple[str, bytes], ...]) -> str:
    """Hash exact ordered canonical rows."""
    logger.debug("digest entry domain=%s rows=%d", domain, len(rows))
    body = frame("domain", domain.encode()) + b"".join(frame(kind, payload) for kind, payload in rows)
    result = sha256(body).hexdigest()
    logger.debug("digest exit domain=%s", domain)
    return result


def texts(kind: str, values: tuple[str, ...]) -> tuple[tuple[str, bytes], ...]:
    """Encode an ordered exact string tuple."""
    logger.debug("texts entry kind=%s", kind)
    if type(kind) is not str or type(values) is not tuple or any(type(value) is not str for value in values):
        reject("texts-input-type-invalid")
    result = tuple((kind, value.encode()) for value in values)
    logger.debug("texts exit kind=%s rows=%d", kind, len(result))
    return result


def shallow_dataclass_bytes(value: object, label: str) -> int:
    """Measure primitive raw fields without invoking caller code."""
    logger.debug("shallow_dataclass_bytes entry label=%s", label)
    if not hasattr(type(value), "__dataclass_fields__"):
        reject(f"{label}-not-dataclass")
    total = 0
    for field in fields(value):
        item = object.__getattribute__(value, field.name)
        if type(item) is str:
            total += len(item.encode("utf-8"))
        elif type(item) is bytes:
            total += len(item)
        elif type(item) in (int, bool) or item is None:
            total += 8
        elif type(item) is tuple:
            total += 8 * len(item)
        else:
            total += 32
    logger.debug("shallow_dataclass_bytes exit label=%s bytes=%d", label, total)
    return total
