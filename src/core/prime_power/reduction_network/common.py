"""Hostile-safe scalar checks and domain-separated hashing for P3-N2."""

from __future__ import annotations

from dataclasses import fields
import hashlib
import logging

logger = logging.getLogger(__name__)


class PrimePowerReductionValidationError(ValueError):
    """Malformed or forged P3-N2 raw evidence."""


def reject(reason: str):
    """Reject malformed evidence without normalizing it to OPEN."""
    logger.error("P3-N2 reject reason=%s", reason)
    raise PrimePowerReductionValidationError(reason)


def digest(domain: str, rows) -> str:
    """Hash length-delimited byte rows under one exact domain."""
    logger.debug("digest entry domain=%s", domain)
    h = hashlib.sha256(domain.encode() + b"\0")
    for label, payload in rows:
        if type(label) is not str or type(payload) is not bytes:
            reject("digest-row-invalid")
        for value in (label.encode(), payload):
            h.update(len(value).to_bytes(8, "big"))
            h.update(value)
    result = h.hexdigest()
    logger.debug("digest exit domain=%s", domain)
    return result


def sha(payload: bytes) -> str:
    """Hash exact captured bytes."""
    logger.debug("sha entry")
    if type(payload) is not bytes:
        reject("sha-input-not-bytes")
    result = hashlib.sha256(payload).hexdigest()
    logger.debug("sha exit")
    return result


def exact_shape(value, cls, label: str) -> dict:
    """Reject subclasses/proxies and read only declared dataclass fields."""
    logger.debug("exact_shape entry label=%s", label)
    if type(value) is not cls:
        reject(f"{label}-exact-type-required")
    try:
        result = {f.name: object.__getattribute__(value, f.name) for f in fields(cls)}
    except (AttributeError, TypeError):
        reject(f"{label}-fields-invalid")
    logger.debug("exact_shape exit label=%s", label)
    return result


def exact_int(value, label: str, *, minimum=0, maximum=2**31 - 1) -> int:
    """Accept a bounded exact integer, never Bool."""
    logger.debug("exact_int entry label=%s", label)
    if type(value) is not int or not minimum <= value <= maximum:
        reject(f"{label}-integer-invalid")
    logger.debug("exact_int exit label=%s", label)
    return value


def exact_text(value, label: str) -> str:
    """Accept one short nonempty exact string."""
    logger.debug("exact_text entry label=%s", label)
    if type(value) is not str or not value or len(value.encode()) > 4096:
        reject(f"{label}-text-invalid")
    logger.debug("exact_text exit label=%s", label)
    return value


def exact_digest(value, label: str) -> str:
    """Accept one lowercase SHA-256 rendering."""
    logger.debug("exact_digest entry label=%s", label)
    if type(value) is not str or len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
        reject(f"{label}-digest-invalid")
    logger.debug("exact_digest exit label=%s", label)
    return value
