"""Exact hostile-safe helpers for PΩ2."""

from __future__ import annotations

from dataclasses import fields
from hashlib import sha256
import logging
import re

logger = logging.getLogger(__name__)
_DIGEST = re.compile(r"[0-9a-f]{64}")
_IDENT = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:/+\-|]{0,191}")


class PadicCompletionValidationError(ValueError):
    """Invalid caller-controlled PΩ2 source or result."""


def reject(reason: str) -> None:
    """Log and raise one stable validation error."""
    logger.error("padic completion validation failed reason=%s", reason)
    raise PadicCompletionValidationError(reason)


def exact_shape(value: object, cls: type, label: str) -> None:
    """Require the exact dataclass and declared instance field set."""
    logger.debug("exact_shape entry label=%s", label)
    if type(value) is not cls:
        reject(f"{label}-must-be-exact")
    if set(getattr(value, "__dict__", {})) != {row.name for row in fields(cls)}:
        reject(f"{label}-field-shape-invalid")
    logger.debug("exact_shape exit label=%s", label)


def exact_digest(value: object, label: str) -> str:
    """Require canonical lowercase SHA-256 text."""
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


def sha(payload: bytes) -> str:
    """Hash exact bytes."""
    logger.debug("sha entry bytes=%d", len(payload))
    result = sha256(payload).hexdigest()
    logger.debug("sha exit")
    return result
