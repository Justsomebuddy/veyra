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
MAX_CODEC_INT_BITS = 4096
EVIDENCE_LABELS = frozenset({"branch-trace", "candidate-result", "pressure-report"})


def bounded_text(value: object, reason: str, maximum: int = 128) -> str:
    """Return a nonempty bounded UTF-8 string or a typed validation error."""
    logger.debug("p3og.bounded_text entry reason=%s", reason)
    # Bound exact-string character count before encoding so an attacker cannot
    # make validation traverse an arbitrarily large scalar merely to reject it.
    if type(value) is not str or not 1 <= len(value) <= maximum:
        logger.error("p3og.bounded_text invalid size reason=%s", reason)
        raise ValueError(reason)
    try:
        encoded = value.encode("utf-8")
    except UnicodeEncodeError as exc:
        logger.error("p3og.bounded_text invalid unicode reason=%s", reason)
        raise ValueError(reason) from exc
    if len(encoded) > maximum:
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


def _json_string_size(value: str) -> int:
    """Return exact compact-JSON UTF-8 bytes for one already bounded string."""
    size = 2
    for character in value:
        codepoint = ord(character)
        if character in {'"', "\\"} or character in "\b\f\n\r\t":
            size += 2
        elif codepoint < 0x20:
            size += 6
        else:
            size += len(character.encode("utf-8"))
    return size


def _metadata_string_size(value: object) -> int:
    """Bound attacker-created class metadata before JSON sizing or encoding."""
    checked = bounded_text(value, "p3og-codec-resource", 65_536)
    return _json_string_size(checked)


def _charge_bytes(remaining: list[int], amount: int) -> None:
    """Consume an exact prospective JSON byte count before tree allocation."""
    if amount > remaining[0]:
        logger.error("p3og._typed cumulative byte budget exhausted")
        raise ValueError("p3og-codec-resource")
    remaining[0] -= amount


def _typed(
    value: Any, depth: int, remaining_nodes: list[int], remaining_bytes: list[int],
) -> Any:
    """Encode Python shape explicitly so tuple/list/enum/string cannot collide."""
    logger.debug("p3og._typed entry type=%s", type(value).__name__)
    if depth > MAX_CODEC_DEPTH or remaining_nodes[0] <= 0:
        logger.error("p3og._typed resource bound depth=%d", depth)
        raise ValueError("p3og-codec-resource")
    remaining_nodes[0] -= 1
    if value is None:
        _charge_bytes(remaining_bytes, 8)
        result = ["none"]
    elif type(value) is bool:
        _charge_bytes(remaining_bytes, 13 if value else 14)
        result = ["bool", value]
    elif type(value) is int:
        if value.bit_length() > MAX_CODEC_INT_BITS:
            logger.error("p3og._typed integer too large bits=%d", value.bit_length())
            raise ValueError("p3og-codec-resource")
        decimal = str(value)
        _charge_bytes(remaining_bytes, 8 + _json_string_size(decimal))
        result = ["int", decimal]
    elif type(value) is str:
        bounded_text(value, "p3og-codec-text", 65_536)
        _charge_bytes(remaining_bytes, 8 + _json_string_size(value))
        result = ["str", value]
    elif isinstance(value, Enum):
        enum_type = type(value)
        _charge_bytes(
            remaining_bytes,
            11 + _metadata_string_size(enum_type.__module__)
            + _metadata_string_size(enum_type.__qualname__),
        )
        result = [
            "enum", enum_type.__module__, enum_type.__qualname__,
            _typed(value.value, depth + 1, remaining_nodes, remaining_bytes),
        ]
    elif type(value) is tuple:
        if len(value) > MAX_CONTAINER_ITEMS:
            logger.error("p3og._typed tuple too large items=%d", len(value))
            raise ValueError("p3og-codec-resource")
        _charge_bytes(remaining_bytes, 12 + max(len(value) - 1, 0))
        result = ["tuple", [
            _typed(item, depth + 1, remaining_nodes, remaining_bytes)
            for item in value
        ]]
    elif type(value) is list:
        if len(value) > MAX_CONTAINER_ITEMS:
            logger.error("p3og._typed list too large items=%d", len(value))
            raise ValueError("p3og-codec-resource")
        _charge_bytes(remaining_bytes, 11 + max(len(value) - 1, 0))
        result = ["list", [
            _typed(item, depth + 1, remaining_nodes, remaining_bytes)
            for item in value
        ]]
    elif is_dataclass(value) and not isinstance(value, type):
        value_type = type(value)
        raw_fields = getattr(value_type, "__dataclass_fields__", None)
        if type(raw_fields) is not dict or len(raw_fields) > MAX_CONTAINER_ITEMS:
            logger.error("p3og._typed dataclass metadata envelope exceeded")
            raise ValueError("p3og-codec-resource")
        dataclass_fields = fields(value)
        if len(dataclass_fields) > MAX_CONTAINER_ITEMS:
            logger.error("p3og._typed dataclass too large fields=%d", len(dataclass_fields))
            raise ValueError("p3og-codec-resource")
        _charge_bytes(
            remaining_bytes,
            18 + _metadata_string_size(value_type.__module__)
            + _metadata_string_size(value_type.__qualname__)
            + max(len(dataclass_fields) - 1, 0)
            + sum(
                3 + _metadata_string_size(field.name)
                for field in dataclass_fields
            ),
        )
        result = ["dataclass", value_type.__module__, value_type.__qualname__, [
            [field.name, _typed(
                getattr(value, field.name), depth + 1,
                remaining_nodes, remaining_bytes,
            )]
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
        remaining_bytes = [maximum_bytes]
        result = json.dumps(
            _typed(values, 0, [maximum_nodes], remaining_bytes),
            ensure_ascii=False, sort_keys=False,
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
    if len(result) != maximum_bytes - remaining_bytes[0]:
        logger.error("p3og._canonical_bytes preflight accounting drift")
        raise ValueError("p3og-codec-resource")
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
