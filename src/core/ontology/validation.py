"""Fail-closed snapshots for the bounded P0 executable contract."""

from __future__ import annotations

import logging
from typing import NoReturn

from ..observer_core_codec import (
    ObserverCodecError,
    canonical_observer_bytes,
    decode_observer,
)
from ..observer_core_semantics import ObserverCoreError, infer_observer_kind
from ..observer_core_types import LeafKind, PairKind, ResponseKind
from .types import (
    ContinuationWitness,
    InternalObserver,
    OntologyPresentation,
    OntologyStage,
)
from ..proof_core_types import CoreTerm, Pulse, Silence

logger = logging.getLogger(__name__)

MAX_P0_ID_BYTES = 128
MAX_P0_STAGES = 64
MAX_P0_OBSERVERS = 64
MAX_P0_WITNESSES = 128
MAX_P0_CHECKS = 4096


class PositiveOntologyValidationError(ValueError):
    """An exact P0 representation or resource contract was violated."""


def _reject(reason: str) -> NoReturn:
    logger.error("positive ontology rejected reason=%s", reason)
    raise PositiveOntologyValidationError(reason)


def snapshot_identifier(value: str, field: str) -> str:
    """Capture one bounded exact identifier without invoking hostile repr."""
    logger.debug("snapshot_identifier entry field=%s", field)
    if type(value) is not str or not value or len(value) > MAX_P0_ID_BYTES:
        _reject(f"invalid-{field}")
    try:
        byte_count = len(value.encode("utf-8"))
    except UnicodeError:
        _reject(f"invalid-{field}")
    if byte_count > MAX_P0_ID_BYTES:
        _reject(f"invalid-{field}")
    logger.debug("snapshot_identifier exit field=%s bytes=%d", field, byte_count)
    return value


def snapshot_recurrence(value: CoreTerm) -> CoreTerm:
    """Capture one recurrence in a single bounded, cycle-safe pass."""
    logger.debug("snapshot_recurrence entry")
    depth = 0
    cursor: object = value
    active: set[int] = set()
    while type(cursor) is Pulse:
        identity = id(cursor)
        if identity in active:
            _reject("circular-recurrence")
        active.add(identity)
        depth += 1
        if depth > 128:
            _reject("recurrence-resource-limit")
        try:
            cursor = cursor.tail
        except AttributeError:
            _reject("invalid-recurrence")
    if type(cursor) is not Silence:
        _reject("invalid-recurrence")
    result: CoreTerm = Silence()
    for _ in range(depth):
        result = Pulse(result)
    logger.debug("snapshot_recurrence exit depth=%d", depth)
    return result


def snapshot_internal_observer(value: InternalObserver) -> InternalObserver:
    """Re-decode canonical observer bytes and recompute the trusted kind."""
    logger.debug("snapshot_internal_observer entry")
    if type(value) is not InternalObserver:
        _reject("observer-must-be-exact")
    try:
        source_id, source_bytes, source_kind = (
            value.observer_id, value.canonical, value.response_kind
        )
    except AttributeError:
        _reject("observer-missing-fields")
    observer_id = snapshot_identifier(source_id, "observer-id")
    if type(source_bytes) is not bytes:
        _reject("observer-canonical-must-be-bytes")
    canonical = memoryview(source_bytes).tobytes()
    try:
        program = decode_observer(canonical)
        kind = infer_observer_kind(program)
    except (ObserverCodecError, ObserverCoreError) as exc:
        logger.error("snapshot_internal_observer invalid canonical program")
        raise PositiveOntologyValidationError("invalid-observer-program") from exc
    if _response_kind_signature(source_kind) != _response_kind_signature(kind):
        _reject("observer-kind-or-canonical-drift")
    if canonical_observer_bytes(program) != canonical:
        _reject("observer-kind-or-canonical-drift")
    result = InternalObserver(observer_id, canonical, kind)
    logger.debug("snapshot_internal_observer exit observer=%s", observer_id)
    return result


def _response_kind_signature(value: ResponseKind) -> tuple[str, ...]:
    logger.debug("_response_kind_signature entry")
    stack: list[tuple[bool, object]] = [(False, value)]
    active: set[int] = set()
    output: list[str] = []
    nodes = 0
    while stack:
        closing, node = stack.pop()
        if closing:
            active.discard(id(node))
            output.append("pair-close")
            continue
        nodes += 1
        if nodes > 256:
            _reject("response-kind-resource-limit")
        if type(node) is LeafKind:
            output.append(node.value)
            continue
        if type(node) is not PairKind or id(node) in active:
            _reject("invalid-response-kind")
        try:
            left, right = node.left, node.right
        except AttributeError:
            _reject("response-kind-missing-fields")
        active.add(id(node))
        output.append("pair-open")
        stack.extend(((True, node), (False, right), (False, left)))
    result = tuple(output)
    logger.debug("_response_kind_signature exit nodes=%d", nodes)
    return result


def snapshot_ontology_stage(value: OntologyStage) -> OntologyStage:
    """Deep-capture one stage without interpreting its observations."""
    logger.debug("snapshot_ontology_stage entry")
    if type(value) is not OntologyStage:
        _reject("stage-must-be-exact")
    try:
        source_id, source_recurrence, source_doctrine, source_observers = (
            value.stage_id, value.representative, value.doctrine_id, value.observers
        )
    except AttributeError:
        _reject("stage-missing-fields")
    stage_id = snapshot_identifier(source_id, "stage-id")
    representative = snapshot_recurrence(source_recurrence)
    doctrine_id = snapshot_identifier(source_doctrine, "doctrine-id")
    if type(source_observers) is not tuple or len(source_observers) > MAX_P0_OBSERVERS:
        _reject("invalid-stage-observers")
    observers = tuple(snapshot_internal_observer(item) for item in source_observers)
    ids = tuple(item.observer_id for item in observers)
    if len(frozenset(ids)) != len(ids):
        _reject("duplicate-observer-id")
    result = OntologyStage(stage_id, representative, doctrine_id, observers)
    logger.debug("snapshot_ontology_stage exit stage=%s observers=%d", stage_id, len(observers))
    return result


def snapshot_continuation_witness(value: ContinuationWitness) -> ContinuationWitness:
    """Capture one path-relative continuation claim."""
    logger.debug("snapshot_continuation_witness entry")
    if type(value) is not ContinuationWitness:
        _reject("witness-must-be-exact")
    try:
        fields = (
            value.witness_id, value.path_id, value.lower_stage,
            value.upper_stage, value.preserved_observers,
        )
    except AttributeError:
        _reject("witness-missing-fields")
    witness_id = snapshot_identifier(fields[0], "witness-id")
    path_id = snapshot_identifier(fields[1], "path-id")
    lower = snapshot_identifier(fields[2], "lower-stage")
    upper = snapshot_identifier(fields[3], "upper-stage")
    preserved_source = fields[4]
    if type(preserved_source) is not tuple or len(preserved_source) > MAX_P0_OBSERVERS:
        _reject("invalid-preserved-observers")
    preserved = tuple(snapshot_identifier(item, "preserved-observer") for item in preserved_source)
    if len(frozenset(preserved)) != len(preserved) or lower == upper:
        _reject("invalid-witness-shape")
    result = ContinuationWitness(witness_id, path_id, lower, upper, preserved)
    logger.debug("snapshot_continuation_witness exit witness=%s observers=%d", witness_id, len(preserved))
    return result


def snapshot_ontology_presentation(value: OntologyPresentation) -> OntologyPresentation:
    """Deep-capture stages and verify admitted cumulative family extensions."""
    logger.debug("snapshot_ontology_presentation entry")
    if type(value) is not OntologyPresentation:
        _reject("presentation-must-be-exact")
    try:
        doctrine_source, presentation_source, stages_source, witnesses_source = (
            value.doctrine, value.presentation_id, value.stages, value.witnesses
        )
    except AttributeError:
        _reject("presentation-missing-fields")
    from .doctrine import require_p0_doctrine
    doctrine = require_p0_doctrine(doctrine_source)
    presentation = snapshot_identifier(presentation_source, "presentation-id")
    if type(stages_source) is not tuple or not 1 <= len(stages_source) <= MAX_P0_STAGES:
        _reject("invalid-presentation-stages")
    if type(witnesses_source) is not tuple or len(witnesses_source) > MAX_P0_WITNESSES:
        _reject("invalid-presentation-witnesses")
    stages = tuple(snapshot_ontology_stage(item) for item in stages_source)
    witnesses = tuple(snapshot_continuation_witness(item) for item in witnesses_source)
    stage_map = {item.stage_id: item for item in stages}
    if len(stage_map) != len(stages):
        _reject("duplicate-stage-id")
    witness_ids = tuple(item.witness_id for item in witnesses)
    if len(frozenset(witness_ids)) != len(witness_ids):
        _reject("duplicate-witness-id")
    total_checks = 0
    doctrine_ids = tuple(item.observer_id for item in doctrine.observers)
    doctrine_map = {item.observer_id: item for item in doctrine.observers}
    for stage in stages:
        stage_ids = tuple(item.observer_id for item in stage.observers)
        if stage.doctrine_id != doctrine.doctrine_id:
            _reject("stage-doctrine-drift")
        if stage_ids != doctrine_ids[:len(stage_ids)]:
            _reject("observer-family-not-doctrine-prefix")
        for observer in stage.observers:
            admitted = doctrine_map[observer.observer_id]
            if observer.canonical != admitted.canonical or observer.response_kind != admitted.response_kind:
                _reject("doctrine-observer-drift")
    for witness in witnesses:
        if witness.lower_stage not in stage_map or witness.upper_stage not in stage_map:
            _reject("unknown-witness-stage")
        lower = stage_map[witness.lower_stage]
        upper = stage_map[witness.upper_stage]
        lower_map = {item.observer_id: item for item in lower.observers}
        upper_map = {item.observer_id: item for item in upper.observers}
        if tuple(lower_map) != tuple(upper_map)[:len(lower_map)]:
            _reject("observer-family-not-cumulative")
        if any(item not in lower_map for item in witness.preserved_observers):
            _reject("unavailable-preserved-observer")
        total_checks += len(upper.observers)
        if total_checks > MAX_P0_CHECKS:
            _reject("presentation-check-limit")
    result = OntologyPresentation(doctrine, presentation, stages, witnesses)
    logger.debug(
        "snapshot_ontology_presentation exit stages=%d witnesses=%d checks=%d",
        len(stages), len(witnesses), total_checks,
    )
    return result
