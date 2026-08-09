"""Hostile-safe framing helpers for P3-C2."""

from __future__ import annotations
from dataclasses import fields
from hashlib import sha256
import logging

logger = logging.getLogger(__name__)


class TransportCoherenceError(ValueError):
    """Typed P3-C2 validation error."""


def reject(reason: str) -> None:
    """Log and raise one sanitized rejection."""
    logger.debug("reject entry")
    logger.error("P3-C2 rejected reason=%s", reason)
    raise TransportCoherenceError(reason)


def exact_shape(value: object, cls: type, label: str) -> None:
    """Require exact DTO type and exact field sequence."""
    logger.debug("exact_shape entry label=%s", label)
    if type(value) is not cls:
        reject(f"{label}-shape-invalid")
    namespace = object.__getattribute__(value, "__dict__")
    if type(namespace) is not dict or tuple(dict.keys(namespace)) != tuple(x.name for x in fields(cls)):
        reject(f"{label}-shape-invalid")
    logger.debug("exact_shape exit label=%s", label)


def exact_text(value: object, label: str) -> str:
    """Require one bounded nonempty plain string."""
    logger.debug("exact_text entry label=%s", label)
    if type(value) is not str or not value or len(value.encode("utf-8")) > 4096:
        reject(f"{label}-invalid")
    logger.debug("exact_text exit label=%s", label)
    return value


def exact_digest(value: object, label: str) -> str:
    """Require canonical lowercase SHA-256 text."""
    logger.debug("exact_digest entry label=%s", label)
    if type(value) is not str or len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
        reject(f"{label}-invalid")
    logger.debug("exact_digest exit label=%s", label)
    return value


def frame(domain: str, rows: tuple[tuple[str, bytes], ...]) -> bytes:
    """Encode ordered domain-separated length-framed rows."""
    logger.debug("frame entry domain=%s rows=%d", domain, len(rows))
    exact_text(domain, "frame-domain")
    if type(rows) is not tuple:
        reject("frame-rows-invalid")
    out = bytearray(b"P3C2F1")
    for item in (domain.encode(),):
        out += len(item).to_bytes(8, "big") + item
    for label, value in rows:
        if type(label) is not str or type(value) is not bytes:
            reject("frame-row-invalid")
        for item in (label.encode(), value):
            out += len(item).to_bytes(8, "big") + item
    result = bytes(out)
    logger.debug("frame exit bytes=%d", len(result))
    return result


def digest(domain: str, rows: tuple[tuple[str, bytes], ...]) -> str:
    """Hash one exact framed record."""
    logger.debug("digest entry domain=%s", domain)
    result = sha256(frame(domain, rows)).hexdigest()
    logger.debug("digest exit")
    return result
