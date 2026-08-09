"""Fail-closed exact-value helpers for PΩ1."""

from __future__ import annotations

from dataclasses import fields
from hashlib import sha256
import logging
import re

logger = logging.getLogger(__name__)
_DIGEST = re.compile(r"[0-9a-f]{64}")
_IDENT = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:/+\-|]{0,191}")


class StreamCompletionValidationError(ValueError):
    """Invalid caller-controlled PΩ1 source or result."""


def reject(reason: str) -> None:
    """Log and raise one stable validation error."""
    logger.error("stream completion validation failed reason=%s", reason)
    raise StreamCompletionValidationError(reason)


def exact_shape(value: object, cls: type, label: str) -> None:
    """Require an exact class and exact declared instance field set."""
    logger.debug("exact_shape entry label=%s", label)
    if type(value) is not cls:
        reject(f"{label}-must-be-exact")
    expected = {field.name for field in fields(cls)}
    actual = set(getattr(value, "__dict__", {}))
    if actual != expected:
        reject(f"{label}-field-shape-invalid")
    logger.debug("exact_shape exit label=%s", label)


def exact_digest(value: object, label: str) -> str:
    """Require a lowercase SHA-256 text digest."""
    logger.debug("exact_digest entry label=%s", label)
    if type(value) is not str or _DIGEST.fullmatch(value) is None:
        reject(f"{label}-must-be-sha256")
    logger.debug("exact_digest exit label=%s", label)
    return value


def exact_identifier(value: object, label: str) -> str:
    """Require a bounded exact identifier."""
    logger.debug("exact_identifier entry label=%s", label)
    if type(value) is not str or _IDENT.fullmatch(value) is None:
        reject(f"{label}-invalid")
    logger.debug("exact_identifier exit label=%s", label)
    return value


def sha(data: bytes) -> str:
    """Return SHA-256 with trace logging."""
    logger.debug("sha entry bytes=%d", len(data))
    result = sha256(data).hexdigest()
    logger.debug("sha exit")
    return result
