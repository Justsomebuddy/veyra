"""Exact Ready/Blocked action for P1-A transport v2."""

from __future__ import annotations
import json
import logging

from ..observer_core_semantics import MAX_OBSERVER_DEPTH, MAX_OBSERVER_NODES, validate_closed_recurrence
from ..observer_core_types import (
    Blocked,
    Mark,
    MarkValue,
    ObserverObstruction,
    ObstructionCode,
    PairValue,
    PathStep,
    Ready,
    RecurrenceValue,
)
from ..observer_morphism_runtime import translate_response
from ..observer_morphism_types import ObserverSourceBinding, ProjectionStep, ResponseTranslation
from ..observer_realization_types import ObservationStatus
from ..observer_realization_validation import MAX_REALIZATION_PAYLOAD_BYTES
from ..positive_ontology_types import ObserverDoctrine
from ..proof_core_types import Pulse, Silence
from .digest import payload_digest
from .types import P1AObservationPayloadV2

logger = logging.getLogger(__name__)


class P1AObservationUndefined(ValueError):
    """The selected branch has no outcome derivable from a blocked fine row."""


def _safe_recurrence_data(value: object) -> dict[str, object]:
    """Encode exact Silence/Pulse recurrence without logging its representation."""
    logger.debug("p1a safe recurrence encoding entry")
    try:
        validate_closed_recurrence(value)
    except (TypeError, ValueError, RecursionError) as exc:
        logger.error("p1a safe recurrence validation rejected")
        raise ValueError("p1a-recurrence-invalid") from exc
    pulses = 0
    cursor = value
    while type(cursor) is Pulse:
        pulses += 1
        cursor = cursor.tail
    if type(cursor) is not Silence:
        logger.error("p1a safe recurrence exact type rejected")
        raise ValueError("p1a-recurrence-invalid")
    result: dict[str, object] = {"tag": "silence"}
    for _ in range(pulses):
        result = {"tag": "pulse", "tail": result}
    logger.debug("p1a safe recurrence encoding exit nodes=%d", pulses + 1)
    return result


def _safe_response_data(value: object) -> dict[str, object]:
    """Encode one bounded response without lower-layer repr-bearing codecs."""
    logger.debug("p1a safe response encoding entry type=%s", type(value).__name__)
    stack: list[tuple[bool, object, int]] = [(False, value, 0)]
    active: set[int] = set()
    values: list[dict[str, object]] = []
    nodes = 0
    while stack:
        exiting, node, depth = stack.pop()
        identity = id(node)
        if exiting:
            active.remove(identity)
            if type(node) is RecurrenceValue:
                values.append({"tag": "recurrence", "term": _safe_recurrence_data(node.recurrence)})
            elif type(node) is MarkValue:
                if type(node.mark) is not Mark:
                    logger.error("p1a safe response mark rejected")
                    raise ValueError("p1a-response-invalid")
                values.append({"tag": "mark", "mark": node.mark.value})
            else:
                right, left = values.pop(), values.pop()
                values.append({"tag": "pair", "left": left, "right": right})
            continue
        nodes += 1
        if nodes > MAX_OBSERVER_NODES or depth > MAX_OBSERVER_DEPTH:
            logger.error("p1a safe response resource limit rejected")
            raise ValueError("p1a-response-resource-limit")
        if identity in active or type(node) not in {RecurrenceValue, MarkValue, PairValue}:
            logger.error("p1a safe response shape rejected")
            raise ValueError("p1a-response-invalid")
        active.add(identity)
        stack.append((True, node, depth))
        if type(node) is PairValue:
            stack.append((False, node.right, depth + 1))
            stack.append((False, node.left, depth + 1))
    if len(values) != 1:
        logger.error("p1a safe response cardinality rejected")
        raise ValueError("p1a-response-invalid")
    result = values[0]
    logger.debug("p1a safe response encoding exit nodes=%d tag=%s", nodes, result["tag"])
    return result


def _safe_obstructions_data(value: object) -> list[dict[str, object]]:
    """Encode exact nonempty obstruction paths without logging their contents."""
    logger.debug("p1a safe obstruction encoding entry")
    if type(value) is not tuple or not 1 <= len(value) <= MAX_OBSERVER_NODES:
        logger.error("p1a safe obstruction count rejected")
        raise ValueError("p1a-obstruction-invalid")
    seen: set[tuple[PathStep, ...]] = set()
    result: list[dict[str, object]] = []
    for item in value:
        if (
            type(item) is not ObserverObstruction
            or type(item.code) is not ObstructionCode
            or type(item.path) is not tuple
            or not 1 <= len(item.path) <= MAX_OBSERVER_DEPTH
            or item.path[-1] is not PathStep.APPLY_TAIL
            or any(type(step) is not PathStep for step in item.path)
            or item.path in seen
        ):
            logger.error("p1a safe obstruction shape rejected")
            raise ValueError("p1a-obstruction-invalid")
        seen.add(item.path)
        result.append({"code": item.code.value, "path": [step.value for step in item.path]})
    logger.debug("p1a safe obstruction encoding exit count=%d", len(result))
    return result


def _safe_outcome_data(value: object) -> dict[str, object]:
    """Encode the exact Ready|Blocked sum without disclosing nested values."""
    logger.debug("p1a safe outcome encoding entry type=%s", type(value).__name__)
    if type(value) is Ready:
        result = {"tag": "ready", "value": _safe_response_data(value.value)}
    elif type(value) is Blocked:
        result = {"tag": "blocked", "obstructions": _safe_obstructions_data(value.obstructions)}
    else:
        logger.error("p1a safe outcome exact type rejected")
        raise ValueError("p1a-observation-type")
    logger.debug("p1a safe outcome encoding exit tag=%s", result["tag"])
    return result


def canonical_observation_payload(value: object) -> P1AObservationPayloadV2:
    """Freshly encode one exact R11 sum without decoding caller JSON."""
    logger.debug("canonical_observation_payload entry")
    if type(value) is Ready:
        status = ObservationStatus.READY
    elif type(value) is Blocked:
        status = ObservationStatus.BLOCKED
    else:
        logger.error("canonical observation exact type rejected")
        raise ValueError("p1a-observation-type")
    try:
        payload = json.dumps(
            _safe_outcome_data(value),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        ).encode("ascii")
    except (TypeError, ValueError, UnicodeError, RecursionError) as exc:
        logger.error("canonical observation lower validation rejected")
        raise ValueError("p1a-observation-invalid") from exc
    if len(payload) > MAX_REALIZATION_PAYLOAD_BYTES:
        logger.error("canonical observation payload byte limit rejected")
        raise ValueError("p1a-observation-payload-limit")
    result = P1AObservationPayloadV2(status, payload, payload_digest(payload))
    logger.debug("canonical_observation_payload exit status=%s bytes=%d", status.value, len(payload))
    return result


def transport_observation(
    doctrine: ObserverDoctrine, binding: ObserverSourceBinding, translation: ResponseTranslation, value: object
) -> object:
    """Apply the exact total Ready action or partial Blocked prefix action."""
    logger.debug("transport_observation entry")
    if type(translation) is not ResponseTranslation:
        logger.error("transport_observation translation exact type rejected")
        raise ValueError("p1a-translation-type")
    if type(value) is Ready:
        try:
            result = Ready(translate_response(doctrine, binding, translation, value.value))
        except (TypeError, ValueError, RecursionError) as exc:
            logger.error("transport_observation ready projection rejected")
            raise ValueError("p1a-ready-translation-invalid") from exc
    elif type(value) is Blocked:
        try:
            # Validate the source sum before inspecting any obstruction path.
            _safe_outcome_data(value)
        except (TypeError, ValueError, RecursionError) as exc:
            logger.error("transport_observation blocked source rejected")
            raise ValueError("p1a-blocked-observation-invalid") from exc
        if not translation.projection:
            result = Blocked(tuple(value.obstructions))
        else:
            prefix = tuple(
                PathStep.PAIR_LEFT if s is ProjectionStep.LEFT else PathStep.PAIR_RIGHT for s in translation.projection
            )
            kept = tuple(
                ObserverObstruction(o.code, o.path[len(prefix) :])
                for o in value.obstructions
                if len(o.path) > len(prefix) and o.path[: len(prefix)] == prefix
            )
            if not kept:
                logger.error("transport_observation undefined after prefix filtering")
                raise P1AObservationUndefined("p1a-observation-undefined")
            result = Blocked(kept)
            try:
                _safe_outcome_data(result)
            except (TypeError, ValueError, RecursionError) as exc:
                logger.error("transport_observation projected blocked result rejected")
                raise ValueError("p1a-projected-blocked-invalid") from exc
    else:
        logger.error("transport_observation exact type rejected")
        raise ValueError("p1a-observation-type")
    logger.debug("transport_observation exit status=%s", type(result).__name__)
    return result
