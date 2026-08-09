"""Primitive fail-closed validation helpers for P1-A2."""

from __future__ import annotations

import logging
from typing import NoReturn

from ...observer_core_types import PairKind, ResponseKind
from ..morphism import (
    ObserverMorphismValidationError, ObserverSourceBinding, ProjectionStep,
    response_kind_signature, snapshot_morphism_doctrine, snapshot_projection,
    snapshot_source_binding,
)
from ...ontology.types import ObserverDoctrine
from ...proof_core_types import CoreTerm, Pulse, Silence

logger = logging.getLogger(__name__)
MAX_RELATION_ID_BYTES = 128
MAX_RELATION_STAGES = 32
MAX_RELATION_SOURCE_BYTES = 1_048_576
RELATION_SOURCE_VERSION = "p1a2-source-v1"


class ObserverRelationValidationError(ValueError):
    """An exact P1-A2 representation or binding contract was violated."""


def reject(reason: str) -> NoReturn:
    """Raise the closed P1-A2 validation error."""
    logger.error("observer relation rejected reason=%s", reason)
    raise ObserverRelationValidationError(reason)


def snapshot_relation_doctrine(value: ObserverDoctrine) -> ObserverDoctrine:
    """Normalize lower P1-A doctrine failures into the A2 boundary."""
    logger.debug("snapshot_relation_doctrine entry")
    try:
        result = snapshot_morphism_doctrine(value)
    except ObserverMorphismValidationError as exc:
        logger.error("snapshot_relation_doctrine rejected")
        raise ObserverRelationValidationError("invalid-relation-doctrine") from exc
    logger.debug("snapshot_relation_doctrine exit")
    return result


def snapshot_relation_binding(
    value: ObserverSourceBinding, doctrine: ObserverDoctrine,
) -> ObserverSourceBinding:
    """Snapshot the independent immutable P1-A observer membership binding."""
    logger.debug("snapshot_relation_binding entry")
    try:
        result = snapshot_source_binding(value, doctrine)
    except ObserverMorphismValidationError as exc:
        logger.error("snapshot_relation_binding rejected")
        raise ObserverRelationValidationError("invalid-relation-observer-source") from exc
    logger.debug("snapshot_relation_binding exit members=%d", len(result.observer_ids))
    return result


def identifier(value: str, field: str) -> str:
    """Capture one bounded exact nonempty identifier."""
    logger.debug("relation identifier entry field=%s", field)
    if type(value) is not str or not value or len(value) > MAX_RELATION_ID_BYTES:
        reject(f"invalid-{field}")
    try:
        size = len(value.encode("utf-8"))
    except UnicodeError:
        reject(f"invalid-{field}")
    if size > MAX_RELATION_ID_BYTES:
        reject(f"invalid-{field}")
    logger.debug("relation identifier exit field=%s bytes=%d", field, size)
    return value


def digest64(value: str, field: str) -> str:
    """Capture one exact lowercase SHA-256 text digest."""
    logger.debug("relation digest64 entry field=%s", field)
    if (
        type(value) is not str or len(value) != 64
        or any(item not in "0123456789abcdef" for item in value)
    ):
        reject(f"invalid-{field}")
    logger.debug("relation digest64 exit field=%s", field)
    return value


def natural(value: int, field: str, maximum: int) -> int:
    """Capture one bounded exact natural number."""
    logger.debug("relation natural entry field=%s", field)
    if type(value) is not int or not 0 <= value <= maximum:
        reject(f"invalid-{field}")
    logger.debug("relation natural exit field=%s value=%d", field, value)
    return value


def snapshot_recurrence(value: CoreTerm) -> tuple[CoreTerm, bytes]:
    """Capture one closed Silence/Pulse recurrence in a single bounded pass."""
    logger.debug("relation snapshot_recurrence entry")
    depth, cursor = 0, value
    active: set[int] = set()
    while type(cursor) is Pulse:
        identity = id(cursor)
        if identity in active:
            reject("circular-relation-recurrence")
        active.add(identity)
        depth += 1
        if depth > 128:
            reject("relation-recurrence-resource-limit")
        try:
            cursor = cursor.tail
        except AttributeError:
            reject("invalid-relation-recurrence")
    if type(cursor) is not Silence:
        reject("invalid-relation-recurrence")
    result: CoreTerm = Silence()
    for _ in range(depth):
        result = Pulse(result)
    canonical = b"VRR1" + depth.to_bytes(2, "big")
    logger.debug("relation snapshot_recurrence exit depth=%d", depth)
    return result, canonical


def projection(value: tuple[ProjectionStep, ...]) -> tuple[ProjectionStep, ...]:
    """Snapshot one exact bounded closed P1-A projection."""
    logger.debug("relation projection entry")
    try:
        result = snapshot_projection(value)
    except ObserverMorphismValidationError as exc:
        logger.error("relation projection rejected")
        raise ObserverRelationValidationError("invalid-relation-projection") from exc
    logger.debug("relation projection exit steps=%d", len(result))
    return result


def projected_kind(
    fine_kind: ResponseKind, steps: tuple[ProjectionStep, ...],
) -> ResponseKind:
    """Derive a proposal endpoint kind without claiming observer factorization."""
    logger.debug("projected_kind entry steps=%d", len(steps))
    cursor = fine_kind
    for step in steps:
        if type(cursor) is not PairKind:
            reject("proposal-projection-kind-mismatch")
        cursor = cursor.left if step is ProjectionStep.LEFT else cursor.right
    logger.debug("projected_kind exit")
    return cursor


def kinds_equal(left: ResponseKind, right: ResponseKind) -> bool:
    """Compare exact validated response-kind signatures."""
    logger.debug("relation kinds_equal entry")
    try:
        result = response_kind_signature(left) == response_kind_signature(right)
    except ObserverMorphismValidationError as exc:
        logger.error("relation kinds_equal rejected")
        raise ObserverRelationValidationError("invalid-relation-response-kind") from exc
    logger.debug("relation kinds_equal exit result=%s", result)
    return result
