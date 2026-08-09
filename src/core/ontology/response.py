"""Fresh bounded observation snapshots for positive ontology."""

from __future__ import annotations

import logging

from ..observer_core_semantics import MAX_OBSERVER_DEPTH, MAX_OBSERVER_NODES
from ..observer_core_support import obstruction_data, outcome_data, response_data
from ..observer_core_types import (
    Blocked,
    Mark,
    MarkValue,
    ObstructionCode,
    ObserverObstruction,
    PairValue,
    PathStep,
    Ready,
    RecurrenceValue,
    ResponseValue,
)
from .types import SilenceModality
from .validation import (
    PositiveOntologyValidationError,
    snapshot_recurrence,
)

logger = logging.getLogger(__name__)


def observation_data(observation: Ready | Blocked) -> dict[str, object]:
    """Return canonical data for one freshly rebuilt exact observation."""
    logger.debug("observation_data entry")
    if type(observation) is Ready:
        try:
            source = observation.value
        except AttributeError as exc:
            logger.error("observation_data ready fields missing")
            raise PositiveOntologyValidationError("observation-missing-fields") from exc
        fresh = _snapshot_response(source)
        response_data(fresh)
        result = outcome_data(Ready(fresh))
    elif type(observation) is Blocked:
        try:
            source = observation.obstructions
        except AttributeError as exc:
            logger.error("observation_data blocked fields missing")
            raise PositiveOntologyValidationError("observation-missing-fields") from exc
        if type(source) is not tuple or not 1 <= len(source) <= MAX_OBSERVER_NODES:
            logger.error("observation_data blocked tuple rejected")
            raise PositiveOntologyValidationError("invalid-blocked-obstructions")
        rows: list[ObserverObstruction] = []
        for item in source:
            if type(item) is not ObserverObstruction:
                logger.error("observation_data obstruction exact gate rejected")
                raise PositiveOntologyValidationError("invalid-blocked-obstructions")
            try:
                encoded = obstruction_data(item)
            except (AttributeError, ValueError) as exc:
                logger.error("observation_data obstruction rejected")
                raise PositiveOntologyValidationError("invalid-blocked-obstructions") from exc
            rows.append(
                ObserverObstruction(
                    ObstructionCode(encoded["code"]),
                    tuple(PathStep(step) for step in encoded["path"]),
                )
            )
        try:
            result = outcome_data(Blocked(tuple(rows)))
        except ValueError as exc:
            logger.error("observation_data blocked outcome rejected")
            raise PositiveOntologyValidationError("invalid-blocked-obstructions") from exc
    else:
        logger.error("observation_data exact gate rejected")
        raise PositiveOntologyValidationError("observation-must-be-ready-or-blocked")
    logger.debug("observation_data exit tag=%s", result["tag"])
    return result


def response_modalities(encoded: dict[str, object]) -> tuple[SilenceModality, ...]:
    """Classify only a fresh canonical response-data tree."""
    logger.debug("response_modalities entry")
    if encoded.get("tag") != "ready" or type(encoded.get("value")) is not dict:
        logger.error("response_modalities non-ready data rejected")
        raise PositiveOntologyValidationError("ready-response-data-required")
    stack: list[dict[str, object]] = [encoded["value"]]  # type: ignore[list-item]
    silent = active = False
    nodes = 0
    while stack:
        node = stack.pop()
        nodes += 1
        if nodes > MAX_OBSERVER_NODES:
            logger.error("response_modalities resource limit")
            raise PositiveOntologyValidationError("response-resource-limit")
        tag = node.get("tag")
        if tag == "mark":
            silent |= node.get("mark") == "silent"
            active |= node.get("mark") == "pulse"
        elif tag == "recurrence":
            term = node.get("term")
            if type(term) is not dict:
                logger.error("response_modalities recurrence data rejected")
                raise PositiveOntologyValidationError("invalid-response-data")
            silent |= term.get("tag") == "silence"
            active |= term.get("tag") == "pulse"
        elif tag == "pair":
            left, right = node.get("left"), node.get("right")
            if type(left) is not dict or type(right) is not dict:
                logger.error("response_modalities pair data rejected")
                raise PositiveOntologyValidationError("invalid-response-data")
            stack.extend((right, left))
        else:
            logger.error("response_modalities tag rejected")
            raise PositiveOntologyValidationError("invalid-response-data")
    if silent and active:
        result = (SilenceModality.MIXED,)
    elif silent:
        result = (SilenceModality.RESPONSE,)
    else:
        result = ()
    logger.debug("response_modalities exit count=%d", len(result))
    return result


def _snapshot_response(value: ResponseValue) -> ResponseValue:
    logger.debug("_snapshot_response entry")
    stack: list[tuple[bool, object, int]] = [(False, value, 0)]
    active: set[int] = set()
    values: list[ResponseValue] = []
    nodes = 0
    while stack:
        exiting, node, depth = stack.pop()
        identity = id(node)
        if exiting:
            active.remove(identity)
            right, left = values.pop(), values.pop()
            values.append(PairValue(left, right))
            continue
        nodes += 1
        if nodes > MAX_OBSERVER_NODES or depth > MAX_OBSERVER_DEPTH:
            logger.error("_snapshot_response resource limit")
            raise PositiveOntologyValidationError("response-resource-limit")
        if identity in active:
            logger.error("_snapshot_response cycle rejected")
            raise PositiveOntologyValidationError("circular-response-value")
        if type(node) is RecurrenceValue:
            try:
                recurrence = node.recurrence
            except AttributeError as exc:
                logger.error("_snapshot_response recurrence fields missing")
                raise PositiveOntologyValidationError("response-missing-fields") from exc
            values.append(RecurrenceValue(snapshot_recurrence(recurrence)))
        elif type(node) is MarkValue:
            try:
                mark = node.mark
            except AttributeError as exc:
                logger.error("_snapshot_response mark fields missing")
                raise PositiveOntologyValidationError("response-missing-fields") from exc
            if type(mark) is not Mark:
                logger.error("_snapshot_response mark rejected")
                raise PositiveOntologyValidationError("invalid-mark-value")
            values.append(MarkValue(mark))
        elif type(node) is PairValue:
            try:
                left, right = node.left, node.right
            except AttributeError as exc:
                logger.error("_snapshot_response pair fields missing")
                raise PositiveOntologyValidationError("response-missing-fields") from exc
            active.add(identity)
            stack.extend(((True, node, depth), (False, right, depth + 1), (False, left, depth + 1)))
        else:
            logger.error("_snapshot_response exact gate rejected")
            raise PositiveOntologyValidationError("invalid-response-value")
    if len(values) != 1:
        logger.error("_snapshot_response shape rejected")
        raise PositiveOntologyValidationError("invalid-response-shape")
    logger.debug("_snapshot_response exit nodes=%d", nodes)
    return values[0]
