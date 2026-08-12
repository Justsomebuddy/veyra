"""Authoritative relative realization from P1 observers into finite R16."""

from __future__ import annotations

from hashlib import sha256
import json
import logging

from .observer_core_codec import decode_observer
from .observer_core_semantics import observe
from .observer_core_support import outcome_data
from .observer_core_types import Blocked, Ready
from .observer_descent import validate_doctrine
from .observer_descent_types import FiniteObserver, FiniteObserverDoctrine
from .observer_realization_digest import (
    finite_doctrine_digest,
    realization_context_digest,
    realization_partition_digest,
    realization_witness_digest,
    recurrence_commitment,
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
from .observer_realization_validation import (
    MAX_REALIZATION_CLOSURE,
    MAX_REALIZATION_COST,
    MAX_REALIZATION_INPUTS,
    MAX_REALIZATION_PAYLOAD_BYTES,
    MAX_REALIZATION_TOTAL_PAYLOAD_BYTES,
    OBSERVER_REALIZATION_SCHEMA,
    REALIZATION_CONTEXT_VERSION,
    ObserverRealizationValidationError,
    identifier,
    natural,
    precharge_finite_states,
    reject,
    snapshot_context,
    snapshot_finite_state,
    snapshot_realization_doctrine,
    snapshot_recurrence,
    snapshot_witness,
)
from .positive_ontology_types import ObserverDoctrine
from .proof_core_types import CoreTerm

logger = logging.getLogger(__name__)


def observer_realization_context(
    doctrine: ObserverDoctrine,
    realization_id: str,
    state_inputs: tuple[tuple[object, CoreTerm], ...],
    observer_costs: tuple[tuple[str, int], ...],
) -> RealizationContext:
    """Construct one digest-bound external P1-to-R16 realization context."""
    logger.debug("observer_realization_context entry")
    doctrine = snapshot_realization_doctrine(doctrine)
    if type(state_inputs) is not tuple or type(observer_costs) is not tuple:
        reject("realization-context-raw-tuples-required")
    realization_id = identifier(realization_id, "realization-id")
    if not 1 <= len(state_inputs) <= MAX_REALIZATION_INPUTS:
        reject("realization-input-count-limit")
    if len(observer_costs) != len(doctrine.observers):
        reject("realization-cost-count-limit")
    for row in state_inputs:
        if type(row) is not tuple or len(row) != 2:
            reject("invalid-realization-input-row")
    precharge_finite_states(tuple(row[0] for row in state_inputs))
    inputs: list[RealizationInput] = []
    canonical_inputs: list[tuple[object, bytes]] = []
    for row in state_inputs:
        state = snapshot_finite_state(row[0])
        recurrence, canonical = snapshot_recurrence(row[1])
        inputs.append(RealizationInput(state, recurrence))
        canonical_inputs.append((state, canonical))
    costs: list[ObserverCost] = []
    for row in observer_costs:
        if type(row) is not tuple or len(row) != 2:
            reject("invalid-realization-cost-row")
        costs.append(
            ObserverCost(
                identifier(row[0], "cost-observer-id"),
                natural(row[1], "observer-cost", MAX_REALIZATION_COST),
            )
        )
    expected_ids = tuple(item.observer_id for item in doctrine.observers)
    if sum(item.cost for item in costs) > MAX_REALIZATION_COST:
        reject("realization-total-source-cost-limit")
    if tuple(item.observer_id for item in costs) != expected_ids:
        reject("realization-cost-order-or-coverage-drift")
    response_policy = ResponseTotalization.STRUCTURED_R11
    cost_policy = RealizationCostPolicy.MINIMUM_GENERATOR_SUM
    closure_policy = RealizationClosurePolicy.FINITE_JOIN_CLOSURE
    digest = realization_context_digest(
        doctrine.fingerprint,
        realization_id,
        tuple(canonical_inputs),
        tuple(costs),
        response_policy.value,
        cost_policy.value,
        closure_policy.value,
        REALIZATION_CONTEXT_VERSION,
    )
    provisional = RealizationContext(
        realization_id,
        tuple(inputs),
        tuple(costs),
        response_policy,
        cost_policy,
        closure_policy,
        REALIZATION_CONTEXT_VERSION,
        digest,
    )
    result, _ = snapshot_context(provisional, doctrine)
    logger.debug("observer_realization_context exit inputs=%d", len(result.inputs))
    return result


def _observation_payload(value: object) -> tuple[ObservationStatus, bytes]:
    """Encode one freshly replayed exact Ready/Blocked result losslessly."""
    logger.debug("_observation_payload entry type=%s", type(value).__name__)
    if type(value) is Ready:
        status = ObservationStatus.READY
    elif type(value) is Blocked:
        status = ObservationStatus.BLOCKED
    else:
        reject("invalid-replayed-realization-observation")
    data = outcome_data(value)
    payload = json.dumps(
        data, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("ascii")
    if len(payload) > MAX_REALIZATION_PAYLOAD_BYTES:
        reject("realization-observation-payload-limit")
    logger.debug(
        "_observation_payload exit status=%s bytes=%d", status.value, len(payload)
    )
    return status, payload


def _normalize_partition(values: tuple[object, ...]) -> tuple[int, ...]:
    """Replace exact response values by first-occurrence class ordinals."""
    logger.debug("_normalize_partition entry values=%d", len(values))
    classes: dict[object, int] = {}
    output: list[int] = []
    for value in values:
        if value not in classes:
            classes[value] = len(classes)
        output.append(classes[value])
    result = tuple(output)
    logger.debug("_normalize_partition exit classes=%d", len(classes))
    return result


def _join_partitions(
    partitions: tuple[tuple[int, ...], ...], state_count: int
) -> tuple[int, ...]:
    """Compute the exact common refinement of ordered normalized partitions."""
    logger.debug(
        "_join_partitions entry partitions=%d states=%d",
        len(partitions),
        state_count,
    )
    if not partitions:
        result = (0,) * state_count
    else:
        result = _normalize_partition(
            tuple(tuple(partition[index] for partition in partitions) for index in range(state_count))
        )
    logger.debug("_join_partitions exit classes=%d", 1 + max(result))
    return result


def _closure_candidates(
    observer_ids: tuple[str, ...],
    partitions: tuple[tuple[int, ...], ...],
    costs: tuple[int, ...],
    state_count: int,
) -> dict[tuple[int, ...], tuple[int, tuple[str, ...], tuple[int, ...]]]:
    """Enumerate the bounded finite join closure and cheapest generators."""
    logger.debug("_closure_candidates entry sources=%d", len(observer_ids))
    candidates: dict[
        tuple[int, ...], tuple[int, tuple[str, ...], tuple[int, ...]]
    ] = {}
    for mask in range(1 << len(observer_ids)):
        indices = tuple(
            index for index in range(len(observer_ids)) if mask & (1 << index)
        )
        partition = _join_partitions(
            tuple(partitions[index] for index in indices), state_count
        )
        generator_ids = tuple(observer_ids[index] for index in indices)
        cost = sum(costs[index] for index in indices)
        if cost > MAX_REALIZATION_COST:
            reject("realization-closure-cost-limit")
        candidate = (cost, generator_ids, indices)
        current = candidates.get(partition)
        if current is None or (cost, indices) < (current[0], current[2]):
            candidates[partition] = candidate
        if len(candidates) > MAX_REALIZATION_CLOSURE:
            reject("realization-join-closure-limit")
    logger.debug("_closure_candidates exit closure=%d", len(candidates))
    return candidates


def _response_label(
    generator_indices: tuple[int, ...],
    per_source_rows: tuple[tuple[RealizationEvaluationRow, ...], ...],
    state_index: int,
) -> tuple[object, ...]:
    """Create a total tagged class reference into structured replay rows."""
    logger.debug(
        "_response_label entry generators=%d state=%d",
        len(generator_indices),
        state_index,
    )
    components = tuple(
        (
            per_source_rows[index][state_index].status.value,
            per_source_rows[index][state_index].response_class,
        )
        for index in generator_indices
    )
    result: tuple[object, ...] = ("p1-r16-totalized-v1", components)
    logger.debug("_response_label exit components=%d", len(components))
    return result


def _realize(
    doctrine: ObserverDoctrine,
    context: RealizationContext,
    canonical_inputs: tuple[bytes, ...],
) -> ObserverRealizationWitness:
    """Replay one already snapshotted source/context and build its finite completion."""
    logger.debug("_realize entry observers=%d inputs=%d", len(doctrine.observers), len(context.inputs))
    input_commitments = tuple(
        recurrence_commitment(item) for item in canonical_inputs
    )
    all_rows: list[RealizationEvaluationRow] = []
    total_payload = 0
    per_source_rows: list[tuple[RealizationEvaluationRow, ...]] = []
    source_partitions: list[tuple[int, ...]] = []
    for member in doctrine.observers:
        program = decode_observer(member.canonical)
        provisional: list[tuple[ObservationStatus, bytes]] = []
        for item in context.inputs:
            observation = _observation_payload(observe(program, item.recurrence))
            total_payload += len(observation[1])
            if total_payload > MAX_REALIZATION_TOTAL_PAYLOAD_BYTES:
                reject("realization-total-payload-limit")
            provisional.append(observation)
        payload_partition = _normalize_partition(
            tuple((status.value, payload) for status, payload in provisional)
        )
        rows = tuple(
            RealizationEvaluationRow(
                member.observer_id,
                index,
                context.inputs[index].state,
                input_commitments[index],
                status,
                payload_partition[index],
                payload,
                sha256(payload).hexdigest(),
            )
            for index, (status, payload) in enumerate(provisional)
        )
        all_rows.extend(rows)
        per_source_rows.append(rows)
        source_partitions.append(payload_partition)
    observer_ids = tuple(item.observer_id for item in doctrine.observers)
    base_costs = tuple(item.cost for item in context.observer_costs)
    candidates = _closure_candidates(
        observer_ids,
        tuple(source_partitions),
        base_costs,
        len(context.inputs),
    )
    ordered_partitions = tuple(
        sorted(candidates, key=lambda item: (1 + max(item), item))
    )
    names = {
        partition: (
            "bottom"
            if len(set(partition)) == 1
            else f"realized-{realization_partition_digest(partition)}"
        )
        for partition in ordered_partitions
    }
    finite_observers: list[FiniteObserver] = []
    closure_rows: list[RealizationClosureRow] = []
    frozen_source_rows = tuple(per_source_rows)
    for partition in ordered_partitions:
        cost, generator_ids, generator_indices = candidates[partition]
        observer_name = names[partition]
        responses = tuple(
            (
                item.state,
                _response_label(generator_indices, frozen_source_rows, state_index),
            )
            for state_index, item in enumerate(context.inputs)
        )
        finite_observers.append(FiniteObserver(observer_name, responses, cost))
        class_count = 1 + max(partition)
        representatives = tuple(
            partition.index(class_id) for class_id in range(class_count)
        )
        closure_rows.append(
            RealizationClosureRow(
                observer_name,
                generator_ids,
                partition,
                representatives,
                realization_partition_digest(partition),
                cost,
            )
        )
    finite_doctrine = FiniteObserverDoctrine(
        f"realization-{context.context_digest[:32]}",
        tuple(item.state for item in context.inputs),
        tuple(finite_observers),
    )
    try:
        validate_doctrine(finite_doctrine)
    except (TypeError, ValueError) as exc:
        logger.exception("_realize generated invalid finite doctrine")
        raise ObserverRealizationValidationError(
            "generated-realization-doctrine-invalid"
        ) from exc
    source_mapping = tuple(
        (observer_id, names[partition])
        for observer_id, partition in zip(
            observer_ids, source_partitions, strict=True
        )
    )
    doctrine_digest = finite_doctrine_digest(finite_doctrine)
    evaluations = tuple(all_rows)
    closure = tuple(closure_rows)
    witness_digest = realization_witness_digest(
        doctrine.fingerprint,
        context.context_digest,
        evaluations,
        source_mapping,
        closure,
        doctrine_digest,
        OBSERVER_REALIZATION_SCHEMA,
    )
    result = ObserverRealizationWitness(
        OBSERVER_REALIZATION_SCHEMA,
        doctrine.fingerprint,
        context.context_digest,
        evaluations,
        source_mapping,
        closure,
        finite_doctrine,
        doctrine_digest,
        witness_digest,
    )
    logger.debug(
        "_realize exit evaluations=%d closure=%d",
        len(evaluations),
        len(closure),
    )
    return result


def realize_observer_doctrine_r16(
    doctrine: ObserverDoctrine, context: RealizationContext
) -> ObserverRealizationWitness:
    """Authoritatively replay and finitely join-complete one relative P1 image."""
    logger.debug("realize_observer_doctrine_r16 entry")
    trusted_doctrine = snapshot_realization_doctrine(doctrine)
    trusted_context, canonical_inputs = snapshot_context(context, trusted_doctrine)
    result = _realize(trusted_doctrine, trusted_context, canonical_inputs)
    logger.debug("realize_observer_doctrine_r16 exit")
    return result


def verify_observer_realization_r16(
    doctrine: ObserverDoctrine,
    context: RealizationContext,
    witness: ObserverRealizationWitness,
) -> ObserverRealizationWitness:
    """Replay R11 on every bound input and require complete witness equality."""
    logger.debug("verify_observer_realization_r16 entry")
    trusted_doctrine = snapshot_realization_doctrine(doctrine)
    trusted_context, canonical_inputs = snapshot_context(context, trusted_doctrine)
    supplied = snapshot_witness(witness)
    expected = _realize(trusted_doctrine, trusted_context, canonical_inputs)
    if supplied != expected:
        logger.error("verify_observer_realization_r16 replay mismatch")
        raise ObserverRealizationValidationError("realization-authoritative-replay-mismatch")
    logger.debug("verify_observer_realization_r16 exit")
    return expected


def observer_realization_scope_boundary() -> tuple[str, ...]:
    """Return the fixed nonclaims of the first relative realization slice."""
    logger.debug("observer_realization_scope_boundary entry")
    result = (
        "not-canonical-from-p1-alone",
        "structured-blockage-is-totalized-not-r11-echo",
        "generated-joins-are-derived-r16-observers-not-p1-programs",
        "no-identity-composition-functoriality-or-naturality",
        "ordered-local-section-not-canonical-quotient-transport",
        "digests-bind-integrity-not-authentication",
        "no-ready-only-image-chain-or-obstruction-basis-theorem",
        "finite-relative-executable-evidence-not-promotion",
    )
    logger.debug("observer_realization_scope_boundary exit items=%d", len(result))
    return result
