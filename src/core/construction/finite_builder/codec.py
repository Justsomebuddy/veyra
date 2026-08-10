"""Canonical bounded codec for closed P1-B builder syntax and recurrences."""

from __future__ import annotations

import logging

from .types import FiniteBuilderExpr, PulseStep, SeedRef
from ...positive_ontology_validation import (
    PositiveOntologyValidationError, snapshot_recurrence,
)
from ...proof_core_types import CoreTerm, Pulse, Silence

_LEGACY_MODULE = "src.core.finite_builder_codec"
logger = logging.getLogger(_LEGACY_MODULE)
BUILDER_MAGIC = b"VFB1"
RECURRENCE_MAGIC = b"VFR1"
MAX_FINITE_BUILDER_NODES = 128


class FiniteBuilderCodecError(ValueError):
    """Canonical finite-builder encoding was invalid or exceeded its bound."""


def _canonical_builder_bytes(value: FiniteBuilderExpr) -> bytes:
    """Encode exact unary builder syntax without recursion or hostile repr."""
    logger.debug("_canonical_builder_bytes entry")
    output = bytearray(BUILDER_MAGIC)
    cursor: object = value
    active: set[int] = set()
    nodes = 0
    while type(cursor) is PulseStep:
        identity = id(cursor)
        if identity in active:
            logger.error("_canonical_builder_bytes cycle rejected")
            raise FiniteBuilderCodecError("circular-builder-program")
        active.add(identity)
        nodes += 1
        if nodes > MAX_FINITE_BUILDER_NODES:
            logger.error("_canonical_builder_bytes resource limit")
            raise FiniteBuilderCodecError("builder-resource-limit")
        output.extend(b"P")
        try:
            cursor = cursor.child
        except AttributeError as exc:
            logger.error("_canonical_builder_bytes missing child")
            raise FiniteBuilderCodecError("invalid-builder-program") from exc
    nodes += 1
    if nodes > MAX_FINITE_BUILDER_NODES or type(cursor) is not SeedRef:
        logger.error("_canonical_builder_bytes leaf rejected")
        raise FiniteBuilderCodecError("invalid-builder-program")
    try:
        seed_id = cursor.seed_id
    except AttributeError as exc:
        logger.error("_canonical_builder_bytes missing seed")
        raise FiniteBuilderCodecError("invalid-builder-program") from exc
    if type(seed_id) is not str or not seed_id:
        logger.error("_canonical_builder_bytes seed rejected")
        raise FiniteBuilderCodecError("invalid-builder-seed-id")
    try:
        encoded = seed_id.encode("utf-8")
    except UnicodeError as exc:
        logger.error("_canonical_builder_bytes seed encoding rejected")
        raise FiniteBuilderCodecError("invalid-builder-seed-id") from exc
    if len(encoded) > 128:
        logger.error("_canonical_builder_bytes seed limit")
        raise FiniteBuilderCodecError("invalid-builder-seed-id")
    output.extend(b"S" + len(encoded).to_bytes(2, "big") + encoded)
    result = bytes(output)
    logger.debug("_canonical_builder_bytes exit nodes=%d", nodes)
    return result


def _decode_builder(value: bytes) -> FiniteBuilderExpr:
    """Decode one canonical bounded builder into fresh exact nodes."""
    logger.debug("_decode_builder entry")
    if type(value) is not bytes or not value.startswith(BUILDER_MAGIC):
        logger.error("_decode_builder header rejected")
        raise FiniteBuilderCodecError("invalid-builder-canonical")
    data = memoryview(value)
    offset, pulses = len(BUILDER_MAGIC), 0
    while offset < len(data) and data[offset] == ord("P"):
        pulses += 1
        offset += 1
        if pulses + 1 > MAX_FINITE_BUILDER_NODES:
            logger.error("_decode_builder resource limit")
            raise FiniteBuilderCodecError("builder-resource-limit")
    if offset >= len(data) or data[offset] != ord("S") or offset + 3 > len(data):
        logger.error("_decode_builder seed tag rejected")
        raise FiniteBuilderCodecError("invalid-builder-canonical")
    size = int.from_bytes(data[offset + 1:offset + 3], "big")
    start, end = offset + 3, offset + 3 + size
    if not 0 < size <= 128 or end != len(data):
        logger.error("_decode_builder seed length rejected")
        raise FiniteBuilderCodecError("invalid-builder-canonical")
    try:
        seed_id = bytes(data[start:end]).decode("utf-8")
    except UnicodeError as exc:
        logger.error("_decode_builder seed encoding rejected")
        raise FiniteBuilderCodecError("invalid-builder-canonical") from exc
    result: FiniteBuilderExpr = SeedRef(seed_id)
    for _ in range(pulses):
        result = PulseStep(result)
    if _canonical_builder_bytes(result) != value:
        logger.error("_decode_builder noncanonical bytes")
        raise FiniteBuilderCodecError("noncanonical-builder")
    logger.debug("_decode_builder exit nodes=%d", pulses + 1)
    return result


def _canonical_recurrence_bytes(value: CoreTerm) -> bytes:
    """Encode one exact finite Silence/Pulse recurrence by its depth."""
    logger.debug("_canonical_recurrence_bytes entry")
    try:
        captured = snapshot_recurrence(value)
    except PositiveOntologyValidationError as exc:
        logger.error("_canonical_recurrence_bytes recurrence rejected")
        raise FiniteBuilderCodecError("invalid-finite-recurrence") from exc
    depth, cursor = 0, captured
    while type(cursor) is Pulse:
        depth += 1
        cursor = cursor.tail
    result = RECURRENCE_MAGIC + depth.to_bytes(2, "big")
    logger.debug("_canonical_recurrence_bytes exit depth=%d", depth)
    return result


def _decode_recurrence(value: bytes) -> CoreTerm:
    """Decode one canonical finite recurrence into fresh exact nodes."""
    logger.debug("_decode_recurrence entry")
    if type(value) is not bytes or len(value) != 6 or not value.startswith(RECURRENCE_MAGIC):
        logger.error("_decode_recurrence canonical rejected")
        raise FiniteBuilderCodecError("invalid-recurrence-canonical")
    depth = int.from_bytes(value[4:6], "big")
    if depth > 128:
        logger.error("_decode_recurrence resource limit")
        raise FiniteBuilderCodecError("recurrence-resource-limit")
    result: CoreTerm = Silence()
    for _ in range(depth):
        result = Pulse(result)
    logger.debug("_decode_recurrence exit depth=%d", depth)
    return result


for _legacy_object in (
    FiniteBuilderCodecError,
    _canonical_builder_bytes,
    _decode_builder,
    _canonical_recurrence_bytes,
    _decode_recurrence,
):
    _legacy_object.__module__ = _LEGACY_MODULE
del _legacy_object, _LEGACY_MODULE
