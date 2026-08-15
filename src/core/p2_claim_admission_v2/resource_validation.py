"""Dependency-light structural resource gates for P2 v2 artifacts."""

from __future__ import annotations

from dataclasses import fields, is_dataclass
from enum import Enum
import logging

from .errors import P2ClaimAdmissionError, reject

logger = logging.getLogger(__name__)

MAX_NONPAYLOAD_TEXT_BYTES = 1_048_576
MAX_STRUCTURAL_NODES = 65_536
MAX_DEPTH = 128
MAX_IDENTIFIER_BYTES = 128
_HEX = frozenset("0123456789abcdef")


def exact_digest(value: object, reason: str) -> str:
    """Validate one lowercase SHA-256 spelling."""
    logger.debug("exact_digest entry field=%s", reason)
    if type(value) is not str or len(value) != 64 or any(ch not in _HEX for ch in value):
        reject(reason)
    logger.debug("exact_digest exit field=%s", reason)
    return value


def exact_identifier(value: object, reason: str) -> str:
    """Validate one exact string within the fixed UTF-8 identifier ceiling."""
    logger.debug("exact_identifier entry field=%s", reason)
    if type(value) is not str or len(value) > MAX_IDENTIFIER_BYTES:
        reject(reason)
    try:
        encoded = value.encode("utf-8", errors="strict")
    except UnicodeError as exc:
        logger.error("exact_identifier rejected field=%s type=%s", reason, type(exc).__name__)
        raise P2ClaimAdmissionError(reason) from exc
    if len(encoded) > MAX_IDENTIFIER_BYTES:
        reject(reason)
    logger.debug("exact_identifier exit field=%s bytes=%d", reason, len(encoded))
    return value


def _children(value: object) -> tuple[object, ...]:
    """Return structural children without invoking user iteration hooks."""
    logger.debug("_children entry type=%s", type(value).__name__)
    if type(value) in (tuple, list):
        result = tuple(value)
    elif type(value) is dict:
        result = tuple(part for item in value.items() for part in item)
    elif is_dataclass(value) and type(value).__module__.startswith("src.core"):
        result = tuple(getattr(value, item.name) for item in fields(value))
    else:
        result = ()
    logger.debug("_children exit rows=%d", len(result))
    return result


def charge_structure(value: object, *, allowance: int = MAX_STRUCTURAL_NODES) -> int:
    """Count occurrence-expanded nodes with a fixed depth ceiling."""
    logger.debug("charge_structure entry allowance=%d", allowance)
    if type(allowance) is not int or type(allowance) is bool or allowance < 0:
        reject("invalid-node-allowance")
    count = 0
    stack: list[tuple[object, int]] = [(value, 0)]
    while stack:
        node, depth = stack.pop()
        count += 1
        if count > allowance:
            reject("structural-node-limit")
        if depth > MAX_DEPTH:
            reject("structural-depth-limit")
        children = _children(node)
        stack.extend((child, depth + 1) for child in reversed(children))
    logger.debug("charge_structure exit nodes=%d", count)
    return count


def charge_text(value: object, *, allowance: int = MAX_NONPAYLOAD_TEXT_BYTES) -> int:
    """Charge aggregate UTF-8 text before authoritative replay."""
    logger.debug("charge_text entry allowance=%d", allowance)
    if type(allowance) is not int or type(allowance) is bool or allowance < 0:
        reject("invalid-text-allowance")
    total = 0
    stack: list[object] = [value]
    while stack:
        node = stack.pop()
        text = node.value if isinstance(node, Enum) else node
        if type(text) is str:
            remaining = allowance - total
            if len(text) > remaining:
                reject("nonpayload-text-limit")
            try:
                size = len(text.encode("utf-8", errors="strict"))
            except UnicodeError as exc:
                logger.error("charge_text rejected type=%s", type(exc).__name__)
                raise P2ClaimAdmissionError("nonpayload-text-invalid") from exc
            if size > remaining:
                reject("nonpayload-text-limit")
            total += size
        else:
            stack.extend(reversed(_children(node)))
    logger.debug("charge_text exit bytes=%d", total)
    return total
