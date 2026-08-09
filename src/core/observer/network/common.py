"""Exact validation helpers for P3-T."""

from __future__ import annotations

from dataclasses import fields
import logging

logger = logging.getLogger(__name__)


class ObserverNetworkError(ValueError):
    """Typed malformed-source or resource refusal."""


def reject(code: str) -> None:
    """Raise one stable typed validation error."""
    logger.error("observer network reject code=%s", code)
    raise ObserverNetworkError(code)


def exact_text(
    value: object, label: str, *, max_codepoints: int = 4096, max_bytes: int = 4096
) -> str:
    """Accept only nonempty exact strings."""
    logger.debug("exact_text entry label=%s", label)
    if type(value) is not str or not value or len(value) > max_codepoints:
        reject(f"{label}-invalid")
    try:
        encoded = value.encode("utf-8")
    except UnicodeError:
        reject(f"{label}-invalid")
    if len(encoded) > max_bytes:
        reject(f"{label}-invalid")
    logger.debug("exact_text exit label=%s", label)
    return value


def exact_digest(value: object, label: str) -> str:
    """Accept only lowercase SHA-256 text."""
    logger.debug("exact_digest entry label=%s", label)
    if type(value) is not str or len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
        reject(f"{label}-invalid")
    logger.debug("exact_digest exit label=%s", label)
    return value


def exact_shape(value: object, expected: type, label: str) -> None:
    """Require an exact dataclass with one ordinary, exact field dictionary."""
    logger.debug("exact_shape entry label=%s", label)
    if type(value) is not expected:
        reject(f"{label}-type-invalid")
    try:
        instance_dict = object.__getattribute__(value, "__dict__")
    except AttributeError:
        reject(f"{label}-shape-invalid")
    if type(instance_dict) is not dict:
        reject(f"{label}-shape-invalid")
    required = tuple(item.name for item in fields(expected))
    if set(dict.keys(instance_dict)) != set(required):
        reject(f"{label}-shape-invalid")
    logger.debug("exact_shape exit label=%s", label)
