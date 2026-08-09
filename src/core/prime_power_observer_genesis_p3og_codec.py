"""Typed canonical codec and bounded scalar guards for P3-OG."""

from __future__ import annotations

from dataclasses import fields, is_dataclass
from enum import Enum
from hashlib import sha256
import json
import logging
from typing import Any

logger = logging.getLogger(__name__)
DOMAIN = b"veyra-p3og-pressure-v2\0"
MAX_SOURCE_BYTES = 65_536
MAX_EVIDENCE_BYTES = 16 * 1024 * 1024
MAX_CODEC_DEPTH = 24
MAX_CONTAINER_ITEMS = 256
MAX_CODEC_NODES = 100_000
MAX_EVIDENCE_NODES = 2_000_000
EVIDENCE_LABELS = frozenset({"branch-trace", "candidate-result", "pressure-report"})


def bounded_text(value: object, reason: str, maximum: int = 128) -> str:
    """Return a nonempty bounded UTF-8 string or a typed validation error."""
    logger.debug("p3og.bounded_text entry reason=%s", reason)
    try:
        encoded = value.encode("utf-8") if type(value) is str else b""
    except UnicodeEncodeError as exc:
        logger.error("p3og.bounded_text invalid unicode reason=%s", reason)
        raise ValueError(reason) from exc
    if not 1 <= len(encoded) <= maximum:
        logger.error("p3og.bounded_text invalid size reason=%s", reason)
        raise ValueError(reason)
    logger.debug("p3og.bounded_text exit bytes=%d", len(encoded))
    return value  # type: ignore[return-value]


def bounded_int(value: object, reason: str, maximum_bits: int) -> int:
    """Return an exact bounded integer, rejecting bool and foreign numerics."""
    logger.debug("p3og.bounded_int entry reason=%s", reason)
    if type(value) is not int or value.bit_length() > maximum_bits:
        logger.error("p3og.bounded_int invalid reason=%s", reason)
        raise ValueError(reason)
    logger.debug("p3og.bounded_int exit bits=%d", value.bit_length())
    return value


def _typed(value: Any, depth: int, remaining: list[int]) -> Any:
    """Encode Python shape explicitly so tuple/list/enum/string cannot collide."""
    logger.debug("p3og._typed entry type=%s", type(value).__name__)
    if depth > MAX_CODEC_DEPTH or remaining[0] <= 0:
        logger.error("p3og._typed resource bound depth=%d", depth)
        raise ValueError("p3og-codec-resource")
    remaining[0] -= 1
    if value is None:
        result = ["none"]
    elif type(value) is bool:
        result = ["bool", value]
    elif type(value) is int:
        result = ["int", str(value)]
    elif type(value) is str:
        bounded_text(value, "p3og-codec-text", 65_536)
        result = ["str", value]
    elif isinstance(value, Enum):
        enum_type = type(value)
        result = [
            "enum", enum_type.__module__, enum_type.__qualname__,
            _typed(value.value, depth + 1, remaining),
        ]
    elif type(value) is tuple:
        if len(value) > MAX_CONTAINER_ITEMS:
            logger.error("p3og._typed tuple too large items=%d", len(value))
            raise ValueError("p3og-codec-resource")
        result = ["tuple", [_typed(item, depth + 1, remaining) for item in value]]
    elif type(value) is list:
        if len(value) > MAX_CONTAINER_ITEMS:
            logger.error("p3og._typed list too large items=%d", len(value))
            raise ValueError("p3og-codec-resource")
        result = ["list", [_typed(item, depth + 1, remaining) for item in value]]
    elif is_dataclass(value) and not isinstance(value, type):
        value_type = type(value)
        dataclass_fields = fields(value)
        if len(dataclass_fields) > MAX_CONTAINER_ITEMS:
            logger.error("p3og._typed dataclass too large fields=%d", len(dataclass_fields))
            raise ValueError("p3og-codec-resource")
        result = ["dataclass", value_type.__module__, value_type.__qualname__, [
            [field.name, _typed(getattr(value, field.name), depth + 1, remaining)]
            for field in dataclass_fields
        ]]
    else:
        logger.error("p3og._typed unsupported type=%s", type(value).__name__)
        raise ValueError("p3og-codec-type")
    logger.debug("p3og._typed exit type=%s", type(value).__name__)
    return result


def _canonical_bytes(
    values: tuple[Any, ...], maximum_bytes: int, maximum_nodes: int,
) -> bytes:
    """Encode with fixed internal byte and node budgets."""
    logger.debug(
        "p3og._canonical_bytes entry values=%d bytes=%d nodes=%d",
        len(values), maximum_bytes, maximum_nodes,
    )
    try:
        result = json.dumps(
            _typed(values, 0, [maximum_nodes]), ensure_ascii=False, sort_keys=False,
            separators=(",", ":"),
        ).encode("utf-8")
    except UnicodeEncodeError as exc:
        logger.error("p3og.canonical_bytes encoding failure=%s", exc)
        raise ValueError("p3og-canonical-encoding") from exc
    except ValueError:
        logger.error("p3og.canonical_bytes rejected typed value")
        raise
    if len(result) > maximum_bytes:
        logger.error("p3og._canonical_bytes too large bytes=%d", len(result))
        raise ValueError("p3og-canonical-bytes")
    logger.debug("p3og._canonical_bytes exit bytes=%d", len(result))
    return result


def canonical_bytes(*values: Any) -> bytes:
    """Return a source-bounded, type-tagged canonical representation."""
    logger.debug("p3og.canonical_bytes entry values=%d", len(values))
    result = _canonical_bytes(values, MAX_SOURCE_BYTES, MAX_CODEC_NODES)
    logger.debug("p3og.canonical_bytes exit bytes=%d", len(result))
    return result


def evidence_bytes(*values: Any) -> bytes:
    """Return bounded canonical bytes for the maximum accepted execution report."""
    logger.debug("p3og.evidence_bytes entry values=%d", len(values))
    result = _canonical_bytes(values, MAX_EVIDENCE_BYTES, MAX_EVIDENCE_NODES)
    logger.debug("p3og.evidence_bytes exit bytes=%d", len(result))
    return result


def digest(label: str, *values: Any) -> str:
    """Digest typed values under an explicit P3-OG pressure domain."""
    logger.debug("p3og.digest entry label=%s values=%d", label, len(values))
    bounded_text(label, "p3og-digest-label")
    encoder = evidence_bytes if label in EVIDENCE_LABELS else canonical_bytes
    result = sha256(DOMAIN + label.encode() + b"\0" + encoder(*values)).hexdigest()
    logger.debug("p3og.digest exit label=%s digest=%s", label, result[:12])
    return result
