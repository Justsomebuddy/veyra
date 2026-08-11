"""Fail-closed snapshots for the relative P1-to-R16 realization boundary."""

from __future__ import annotations

from hashlib import sha256
import json
import logging
from typing import NoReturn

from .observer_descent_types import FiniteObserver, FiniteObserverDoctrine
from .observer_descent_validation import snapshot_doctrine, snapshot_observer
from .observer_realization_digest import (
    finite_doctrine_digest,
    realization_context_digest,
    realization_partition_digest,
    realization_witness_digest,
)
from .observer_realization_types import (
    ObservationStatus,
    ObserverCost,
    ObserverRealizationWitness,
    RealizationClosurePolicy,
    RealizationClosureRow,
    RealizationContext,
    RealizationCostPolicy,
    RealizationEvaluationRow,
    RealizationInput,
    ResponseTotalization,
)
from .positive_ontology_doctrine import snapshot_observer_doctrine
from .positive_ontology_types import ObserverDoctrine
from .proof_core_types import CoreTerm, Pulse, Silence

logger = logging.getLogger(__name__)

REALIZATION_CONTEXT_VERSION = "p1-r16-context-v1"
OBSERVER_REALIZATION_SCHEMA = "veyra.p1-r16.realization-witness.v1"
REALIZATION_SCOPE = "finite-relative-replayed-no-functoriality"
MAX_REALIZATION_INPUTS = 256
MAX_REALIZATION_SOURCES = 8
MAX_REALIZATION_EVALUATIONS = MAX_REALIZATION_INPUTS * MAX_REALIZATION_SOURCES
MAX_REALIZATION_CLOSURE = 256
MAX_REALIZATION_ID_BYTES = 128
MAX_REALIZATION_PAYLOAD_BYTES = 262_144
MAX_REALIZATION_TOTAL_PAYLOAD_BYTES = 8_388_608
MAX_REALIZATION_COST = (1 << 63) - 1
MAX_REALIZATION_INT_BITS = 4096
MAX_REALIZATION_STATE_NODES = 4096
MAX_REALIZATION_STATE_BYTES = 262_144
MAX_REALIZATION_DOCTRINE_VALUE_NODES = 4_000_000
MAX_REALIZATION_DOCTRINE_VALUE_BYTES = 67_108_864


class ObserverRealizationValidationError(ValueError):
    """One P1-to-R16 representation, binding, or resource rule failed."""


def reject(reason: str) -> NoReturn:
    """Raise the closed realization validation error."""
    logger.error("observer realization rejected reason=%s", reason)
    raise ObserverRealizationValidationError(reason)


def identifier(value: object, field: str) -> str:
    """Capture one exact bounded nonempty UTF-8 identifier."""
    logger.debug("realization identifier entry field=%s", field)
    if type(value) is not str or not value:
        reject(f"invalid-{field}")
    try:
        size = len(value.encode("utf-8"))
    except UnicodeError:
        reject(f"invalid-{field}")
    if size > MAX_REALIZATION_ID_BYTES:
        reject(f"invalid-{field}")
    logger.debug("realization identifier exit field=%s bytes=%d", field, size)
    return value


def digest64(value: object, field: str) -> str:
    """Capture one exact lowercase SHA-256 text digest."""
    logger.debug("realization digest64 entry field=%s", field)
    if (
        type(value) is not str
        or len(value) != 64
        or any(item not in "0123456789abcdef" for item in value)
    ):
        reject(f"invalid-{field}")
    logger.debug("realization digest64 exit field=%s", field)
    return value


def natural(value: object, field: str, maximum: int) -> int:
    """Capture one bounded exact natural number without Boolean coercion."""
    logger.debug("realization natural entry field=%s", field)
    if type(value) is not int or not 0 <= value <= maximum:
        reject(f"invalid-{field}")
    logger.debug("realization natural exit field=%s value=%d", field, value)
    return value


def _precharge_finite_values(
    values: tuple[object, ...], node_limit: int, byte_limit: int
) -> None:
    """Bound full expanded traversal before recursive copy or encoding."""
    logger.debug(
        "_precharge_finite_values entry roots=%d nodes=%d bytes=%d",
        len(values),
        node_limit,
        byte_limit,
    )
    stack = [(value, 0) for value in reversed(values)]
    nodes = 0
    encoded_bytes = 0
    while stack:
        value, depth = stack.pop()
        nodes += 1
        if nodes > node_limit:
            reject("realization-state-node-limit")
        if depth > 8:
            reject("realization-state-depth-limit")
        if value is None:
            encoded_bytes += 1
        elif type(value) is int:
            if value.bit_length() > MAX_REALIZATION_INT_BITS:
                reject("realization-state-integer-limit")
            encoded_bytes += max(1, (abs(value).bit_length() + 7) // 8) + 1
        elif type(value) is str:
            try:
                payload = value.encode("utf-8")
            except UnicodeError:
                reject("realization-state-not-canonical")
            if len(payload) > MAX_REALIZATION_ID_BYTES:
                reject("realization-state-size-limit")
            encoded_bytes += len(payload)
        elif type(value) is bytes:
            if len(value) > MAX_REALIZATION_ID_BYTES:
                reject("realization-state-size-limit")
            encoded_bytes += len(value)
        elif type(value) is tuple and len(value) <= 64:
            encoded_bytes += 8
            stack.extend((item, depth + 1) for item in reversed(value))
        else:
            reject("realization-state-not-canonical")
        if encoded_bytes > byte_limit:
            reject("realization-state-byte-limit")
    logger.debug(
        "_precharge_finite_values exit nodes=%d bytes=%d", nodes, encoded_bytes
    )


def _capture_finite_state(value: object, depth: int) -> object:
    """Recursively copy one already precharged exact finite value."""
    logger.debug("snapshot_finite_state entry depth=%d", depth)
    if value is None:
        result: object = None
    elif type(value) is int:
        result = int(value)
    elif type(value) is str:
        result = value
    elif type(value) is bytes:
        result = memoryview(value).tobytes()
    elif type(value) is tuple:
        result = tuple(_capture_finite_state(item, depth + 1) for item in value)
    else:
        reject("realization-state-not-canonical")
    logger.debug("snapshot_finite_state exit depth=%d", depth)
    return result


def precharge_finite_states(values: tuple[object, ...]) -> None:
    """Bound one complete context carrier traversal before deep capture."""
    logger.debug("precharge_finite_states entry states=%d", len(values))
    _precharge_finite_values(
        values, MAX_REALIZATION_STATE_NODES, MAX_REALIZATION_STATE_BYTES
    )
    logger.debug("precharge_finite_states exit states=%d", len(values))


def snapshot_finite_state(value: object) -> object:
    """Precharge and deep-copy one exact R16 value before hashing/equality."""
    logger.debug("snapshot_finite_state precharge entry")
    precharge_finite_states((value,))
    result = _capture_finite_state(value, 0)
    logger.debug("snapshot_finite_state precharge exit")
    return result


def snapshot_recurrence(value: object) -> tuple[CoreTerm, bytes]:
    """Deep-copy one finite closed Silence/Pulse value and canonical depth bytes."""
    logger.debug("realization snapshot_recurrence entry")
    depth, cursor = 0, value
    active: set[int] = set()
    while type(cursor) is Pulse:
        identity = id(cursor)
        if identity in active:
            reject("circular-realization-recurrence")
        active.add(identity)
        depth += 1
        if depth > 128:
            reject("realization-recurrence-resource-limit")
        try:
            cursor = cursor.tail
        except AttributeError:
            reject("invalid-realization-recurrence")
    if type(cursor) is not Silence:
        reject("invalid-realization-recurrence")
    result: CoreTerm = Silence()
    for _ in range(depth):
        result = Pulse(result)
    canonical = b"VRR1" + depth.to_bytes(2, "big")
    logger.debug("realization snapshot_recurrence exit depth=%d", depth)
    return result, canonical


def snapshot_realization_doctrine(value: object) -> ObserverDoctrine:
    """Normalize the exact P1 doctrine boundary into realization errors."""
    logger.debug("snapshot_realization_doctrine entry")
    try:
        result = snapshot_observer_doctrine(value)  # type: ignore[arg-type]
    except (TypeError, ValueError) as exc:
        logger.error("snapshot_realization_doctrine rejected")
        raise ObserverRealizationValidationError(
            "invalid-realization-source-doctrine"
        ) from exc
    if len(result.observers) > MAX_REALIZATION_SOURCES:
        reject("realization-source-count-limit")
    logger.debug(
        "snapshot_realization_doctrine exit observers=%d", len(result.observers)
    )
    return result


def snapshot_context(
    value: object, doctrine: ObserverDoctrine
) -> tuple[RealizationContext, tuple[bytes, ...]]:
    """Validate and deep-capture every non-canonical realization choice."""
    logger.debug("snapshot_context entry")
    doctrine = snapshot_realization_doctrine(doctrine)
    if type(value) is not RealizationContext:
        reject("realization-context-must-be-exact")
    try:
        realization_id, inputs, costs = (
            value.realization_id,
            value.inputs,
            value.observer_costs,
        )
        response_policy, cost_policy, closure_policy = (
            value.response_policy,
            value.cost_policy,
            value.closure_policy,
        )
        version, supplied_digest = value.version, value.context_digest
    except AttributeError:
        reject("realization-context-missing-fields")
    realization_id = identifier(realization_id, "realization-id")
    if (
        type(inputs) is not tuple
        or not 1 <= len(inputs) <= MAX_REALIZATION_INPUTS
        or type(costs) is not tuple
        or len(costs) != len(doctrine.observers)
        or response_policy is not ResponseTotalization.STRUCTURED_R11
        or cost_policy is not RealizationCostPolicy.MINIMUM_GENERATOR_SUM
        or closure_policy is not RealizationClosurePolicy.FINITE_JOIN_CLOSURE
        or version != REALIZATION_CONTEXT_VERSION
    ):
        reject("invalid-realization-context-policy-or-shape")
    raw_states: list[object] = []
    for input_item in inputs:
        if type(input_item) is not RealizationInput:
            reject("realization-input-must-be-exact")
        try:
            raw_states.append(input_item.state)
        except AttributeError:
            reject("realization-input-missing-fields")
    precharge_finite_states(tuple(raw_states))
    captured_inputs: list[RealizationInput] = []
    canonical_inputs: list[tuple[object, bytes]] = []
    states: list[object] = []
    for input_item in inputs:
        try:
            state, recurrence = input_item.state, input_item.recurrence
        except AttributeError:
            reject("realization-input-missing-fields")
        captured_state = snapshot_finite_state(state)
        captured_recurrence, canonical = snapshot_recurrence(recurrence)
        states.append(captured_state)
        canonical_inputs.append((captured_state, canonical))
        captured_inputs.append(RealizationInput(captured_state, captured_recurrence))
    if len(set(states)) != len(states):
        reject("duplicate-realization-state")
    expected_ids = tuple(item.observer_id for item in doctrine.observers)
    captured_costs: list[ObserverCost] = []
    for cost_item in costs:
        if type(cost_item) is not ObserverCost:
            reject("observer-cost-must-be-exact")
        try:
            observer_id, cost = cost_item.observer_id, cost_item.cost
        except AttributeError:
            reject("observer-cost-missing-fields")
        captured_costs.append(
            ObserverCost(
                identifier(observer_id, "cost-observer-id"),
                natural(cost, "observer-cost", MAX_REALIZATION_COST),
            )
        )
    frozen_costs = tuple(captured_costs)
    if sum(item.cost for item in frozen_costs) > MAX_REALIZATION_COST:
        reject("realization-total-source-cost-limit")
    if tuple(item.observer_id for item in frozen_costs) != expected_ids:
        reject("realization-cost-order-or-coverage-drift")
    expected_digest = realization_context_digest(
        doctrine.fingerprint,
        realization_id,
        tuple(canonical_inputs),
        frozen_costs,
        response_policy.value,
        cost_policy.value,
        closure_policy.value,
        version,
    )
    if supplied_digest != expected_digest:
        reject("realization-context-digest-drift")
    result = RealizationContext(
        realization_id,
        tuple(captured_inputs),
        frozen_costs,
        response_policy,
        cost_policy,
        closure_policy,
        version,
        expected_digest,
    )
    logger.debug("snapshot_context exit inputs=%d", len(result.inputs))
    return result, tuple(item[1] for item in canonical_inputs)


def _snapshot_finite_doctrine(value: object) -> FiniteObserverDoctrine:
    """Deep-capture one exact validated R16 DTO without caller-owned rows."""
    logger.debug("_snapshot_finite_doctrine entry")
    try:
        if type(value) is not FiniteObserverDoctrine:
            reject("invalid-realized-finite-doctrine")
        raw_carrier, raw_observers = value.carrier, value.observers
        if (
            type(raw_carrier) is not tuple
            or not 1 <= len(raw_carrier) <= MAX_REALIZATION_INPUTS
            or type(raw_observers) is not tuple
            or not 1 <= len(raw_observers) <= MAX_REALIZATION_CLOSURE
        ):
            reject("invalid-realized-finite-doctrine-shape")
        raw_values: list[object] = list(raw_carrier)
        for raw_observer in raw_observers:
            if type(raw_observer) is not FiniteObserver:
                reject("invalid-realized-finite-observer")
            raw_responses = raw_observer.responses
            if (
                type(raw_responses) is not tuple
                or len(raw_responses) != len(raw_carrier)
            ):
                reject("invalid-realized-finite-response-count")
            for raw_row in raw_responses:
                if type(raw_row) is not tuple or len(raw_row) != 2:
                    reject("invalid-realized-finite-response-row")
                raw_values.extend(raw_row)
        _precharge_finite_values(
            tuple(raw_values),
            MAX_REALIZATION_DOCTRINE_VALUE_NODES,
            MAX_REALIZATION_DOCTRINE_VALUE_BYTES,
        )
        name, carrier, observers = snapshot_doctrine(value)
        captured_carrier = tuple(snapshot_finite_state(item) for item in carrier)
        captured_observers = []
        for item in observers:
            observer_name, responses, cost = snapshot_observer(item)
            bounded_cost = natural(cost, "finite-observer-cost", MAX_REALIZATION_COST)
            captured_rows = tuple(
                (
                    snapshot_finite_state(state),
                    snapshot_finite_state(response),
                )
                for state, response in responses
            )
            captured_observers.append(
                FiniteObserver(observer_name, captured_rows, bounded_cost)
            )
    except (TypeError, ValueError) as exc:
        logger.error("_snapshot_finite_doctrine rejected")
        raise ObserverRealizationValidationError(
            "invalid-realized-finite-doctrine"
        ) from exc
    result = FiniteObserverDoctrine(
        name, captured_carrier, tuple(captured_observers)
    )
    try:
        from .observer_descent import validate_doctrine

        validate_doctrine(result)
    except (TypeError, ValueError) as exc:
        logger.error("_snapshot_finite_doctrine semantic validation rejected")
        raise ObserverRealizationValidationError(
            "invalid-realized-finite-doctrine-semantics"
        ) from exc
    logger.debug(
        "_snapshot_finite_doctrine exit observers=%d", len(captured_observers)
    )
    return result


def _snapshot_payload(value: object, status: ObservationStatus) -> bytes:
    """Require bounded canonical JSON carrying the declared R11 sum tag."""
    logger.debug("_snapshot_payload entry status=%s", status.value)
    if type(value) is not bytes or len(value) > MAX_REALIZATION_PAYLOAD_BYTES:
        reject("invalid-realization-observation-payload")
    payload = memoryview(value).tobytes()
    try:
        raw = json.loads(payload.decode("ascii"))
        canonical = json.dumps(
            raw, sort_keys=True, separators=(",", ":"), ensure_ascii=True
        ).encode("ascii")
    except (UnicodeError, json.JSONDecodeError, TypeError, ValueError) as exc:
        logger.error("_snapshot_payload invalid JSON")
        raise ObserverRealizationValidationError(
            "invalid-realization-observation-payload"
        ) from exc
    if canonical != payload or type(raw) is not dict or raw.get("tag") != status.value:
        reject("realization-observation-status-or-canonical-drift")
    logger.debug("_snapshot_payload exit bytes=%d", len(payload))
    return payload


def _normalized_partition(value: object, state_count: int) -> tuple[int, ...]:
    """Capture one first-occurrence-normalized partition vector."""
    logger.debug("_normalized_partition entry states=%d", state_count)
    if type(value) is not tuple or len(value) != state_count:
        reject("invalid-realization-partition")
    partition = tuple(
        natural(item, "partition-class", state_count - 1) for item in value
    )
    seen: dict[int, int] = {}
    next_class = 0
    for item in partition:
        if item not in seen:
            if item != next_class:
                reject("noncanonical-realization-partition")
            seen[item] = next_class
            next_class += 1
    logger.debug("_normalized_partition exit classes=%d", next_class)
    return partition


def snapshot_witness(value: object) -> ObserverRealizationWitness:
    """Deep-capture and integrity-check a supplied realization witness."""
    logger.debug("snapshot_witness entry")
    if type(value) is not ObserverRealizationWitness:
        reject("realization-witness-must-be-exact")
    try:
        schema, source_fp, context_digest = (
            value.schema,
            value.source_doctrine_fingerprint,
            value.context_digest,
        )
        evaluations, mapping, closure = (
            value.evaluations,
            value.source_mapping,
            value.closure,
        )
        doctrine, doctrine_digest, witness_digest, scope = (
            value.doctrine,
            value.doctrine_digest,
            value.witness_digest,
            value.scope,
        )
    except AttributeError:
        reject("realization-witness-missing-fields")
    if (
        schema != OBSERVER_REALIZATION_SCHEMA
        or scope != REALIZATION_SCOPE
        or type(evaluations) is not tuple
        or not 1 <= len(evaluations) <= MAX_REALIZATION_EVALUATIONS
        or type(mapping) is not tuple
        or not 1 <= len(mapping) <= MAX_REALIZATION_SOURCES
        or type(closure) is not tuple
        or not 1 <= len(closure) <= MAX_REALIZATION_CLOSURE
    ):
        reject("invalid-realization-witness-shape")
    source_fp = digest64(source_fp, "source-doctrine-fingerprint")
    context_digest = digest64(context_digest, "witness-context-digest")
    captured_evaluations: list[RealizationEvaluationRow] = []
    total_payload = 0
    for evaluation_row in evaluations:
        if type(evaluation_row) is not RealizationEvaluationRow:
            reject("realization-evaluation-row-must-be-exact")
        try:
            observer_id, state_index, state = (
                evaluation_row.observer_id,
                evaluation_row.state_index,
                evaluation_row.state,
            )
            input_commitment, status, response_class = (
                evaluation_row.input_commitment,
                evaluation_row.status,
                evaluation_row.response_class,
            )
            payload, payload_digest = (
                evaluation_row.observation_payload,
                evaluation_row.payload_digest,
            )
        except AttributeError:
            reject("realization-evaluation-row-missing-fields")
        observer_id = identifier(observer_id, "evaluation-observer-id")
        state_index = natural(state_index, "evaluation-state-index", MAX_REALIZATION_INPUTS - 1)
        state = snapshot_finite_state(state)
        input_commitment = digest64(input_commitment, "evaluation-input-commitment")
        if type(status) is not ObservationStatus:
            reject("invalid-realization-observation-status")
        response_class = natural(
            response_class, "evaluation-response-class", MAX_REALIZATION_INPUTS - 1
        )
        payload = _snapshot_payload(payload, status)
        total_payload += len(payload)
        if total_payload > MAX_REALIZATION_TOTAL_PAYLOAD_BYTES:
            reject("realization-total-payload-limit")
        payload_digest = digest64(payload_digest, "evaluation-payload-digest")
        if payload_digest != sha256(payload).hexdigest():
            reject("realization-payload-digest-drift")
        captured_evaluations.append(
            RealizationEvaluationRow(
                observer_id,
                state_index,
                state,
                input_commitment,
                status,
                response_class,
                payload,
                payload_digest,
            )
        )
    captured_mapping: list[tuple[str, str]] = []
    for mapping_row in mapping:
        if type(mapping_row) is not tuple or len(mapping_row) != 2:
            reject("invalid-realization-source-mapping-row")
        captured_mapping.append(
            (
                identifier(mapping_row[0], "mapping-source-observer"),
                identifier(mapping_row[1], "mapping-finite-observer"),
            )
        )
    finite_doctrine = _snapshot_finite_doctrine(doctrine)
    state_count = len(finite_doctrine.carrier)
    captured_closure: list[RealizationClosureRow] = []
    for closure_row in closure:
        if type(closure_row) is not RealizationClosureRow:
            reject("realization-closure-row-must-be-exact")
        try:
            observer_name, generators, partition = (
                closure_row.observer_name,
                closure_row.generator_ids,
                closure_row.partition,
            )
            representatives, partition_digest, cost = (
                closure_row.representative_indices,
                closure_row.partition_digest,
                closure_row.cost,
            )
        except AttributeError:
            reject("realization-closure-row-missing-fields")
        observer_name = identifier(observer_name, "closure-observer-name")
        if type(generators) is not tuple or len(generators) > MAX_REALIZATION_SOURCES:
            reject("invalid-realization-closure-generators")
        captured_generators = tuple(
            identifier(item, "closure-generator-id") for item in generators
        )
        if len(set(captured_generators)) != len(captured_generators):
            reject("duplicate-realization-closure-generator")
        captured_partition = _normalized_partition(partition, state_count)
        class_count = 1 + max(captured_partition)
        if type(representatives) is not tuple or len(representatives) != class_count:
            reject("invalid-realization-class-representatives")
        captured_representatives = tuple(
            natural(item, "class-representative", state_count - 1)
            for item in representatives
        )
        expected_representatives = tuple(
            captured_partition.index(class_id) for class_id in range(class_count)
        )
        if captured_representatives != expected_representatives:
            reject("realization-class-section-drift")
        partition_digest = digest64(partition_digest, "partition-digest")
        if partition_digest != realization_partition_digest(captured_partition):
            reject("realization-partition-digest-drift")
        captured_closure.append(
            RealizationClosureRow(
                observer_name,
                captured_generators,
                captured_partition,
                captured_representatives,
                partition_digest,
                natural(cost, "closure-cost", MAX_REALIZATION_COST),
            )
        )
    doctrine_digest = digest64(doctrine_digest, "finite-doctrine-digest")
    if doctrine_digest != finite_doctrine_digest(finite_doctrine):
        reject("realization-finite-doctrine-digest-drift")
    witness_digest = digest64(witness_digest, "realization-witness-digest")
    captured_eval_tuple = tuple(captured_evaluations)
    captured_mapping_tuple = tuple(captured_mapping)
    captured_closure_tuple = tuple(captured_closure)
    expected_witness = realization_witness_digest(
        source_fp,
        context_digest,
        captured_eval_tuple,
        captured_mapping_tuple,
        captured_closure_tuple,
        doctrine_digest,
        schema,
    )
    if witness_digest != expected_witness:
        reject("realization-witness-digest-drift")
    result = ObserverRealizationWitness(
        schema,
        source_fp,
        context_digest,
        captured_eval_tuple,
        captured_mapping_tuple,
        captured_closure_tuple,
        finite_doctrine,
        doctrine_digest,
        expected_witness,
    )
    logger.debug(
        "snapshot_witness exit evaluations=%d closure=%d",
        len(result.evaluations),
        len(result.closure),
    )
    return result
