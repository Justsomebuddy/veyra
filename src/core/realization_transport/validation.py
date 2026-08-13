"""Fail-closed validation for bounded realization transport values."""

from __future__ import annotations

import logging
from typing import NoReturn

from ..observer_realization_types import ObservationStatus
from ..observer_realization_validation import (
    MAX_REALIZATION_CLOSURE,
    MAX_REALIZATION_COST,
    MAX_REALIZATION_EVALUATIONS,
    MAX_REALIZATION_ID_BYTES,
    MAX_REALIZATION_INPUTS,
)
from .digest import context_morphism_digest, transport_receipt_digest
from .types import (
    ClosureActionRow,
    ContextMorphism,
    CostTransportRow,
    CostTransportStatus,
    EvaluationCommutingRow,
    RealizationTransportReceipt,
    RecurrenceCommutingRow,
)

logger = logging.getLogger(__name__)

CONTEXT_MORPHISM_VERSION = "p1-r16-context-morphism-v1"
TRANSPORT_RECEIPT_SCHEMA = "veyra.p1-r16.realization-transport-receipt.v1"
TRANSPORT_SCOPE = "finite-relative-replayed-single-arrow-no-category-or-functor-claim"
MAX_TRANSPORT_RECEIPT_NODES = 131_072
MAX_TRANSPORT_RECEIPT_BYTES = 16_777_216


class RealizationTransportValidationError(ValueError):
    """A context arrow, replay, law, or resource invariant failed."""


def reject(reason: str) -> NoReturn:
    """Raise the single closed transport validation error."""
    logger.error("realization transport rejected reason=%s", reason)
    raise RealizationTransportValidationError(reason)


def _identifier(value: object, field: str) -> str:
    """Capture an exact bounded nonempty UTF-8 identifier."""
    logger.debug("transport identifier entry field=%s", field)
    if type(value) is not str or not value or len(value) > MAX_REALIZATION_ID_BYTES:
        reject(f"invalid-{field}")
    try:
        size = len(value.encode("utf-8"))
    except UnicodeError:
        reject(f"invalid-{field}")
    if size > MAX_REALIZATION_ID_BYTES:
        reject(f"invalid-{field}")
    logger.debug("transport identifier exit field=%s bytes=%d", field, size)
    return value


def _digest64(value: object, field: str) -> str:
    """Capture exact lowercase SHA-256 text."""
    logger.debug("transport digest entry field=%s", field)
    if type(value) is not str or len(value) != 64 or any(ch not in "0123456789abcdef" for ch in value):
        reject(f"invalid-{field}")
    logger.debug("transport digest exit field=%s", field)
    return value


def _natural(value: object, field: str, maximum: int) -> int:
    """Capture an exact bounded natural without Boolean coercion."""
    logger.debug("transport natural entry field=%s", field)
    if type(value) is not int or not 0 <= value <= maximum:
        reject(f"invalid-{field}")
    logger.debug("transport natural exit field=%s value=%d", field, value)
    return value


def normalized_partition(value: object, state_count: int) -> tuple[int, ...]:
    """Capture a first-occurrence-normalized partition."""
    logger.debug("transport normalized_partition entry states=%d", state_count)
    if type(value) is not tuple or len(value) != state_count or not value:
        reject("invalid-transport-partition")
    result = tuple(_natural(item, "transport-partition-class", state_count - 1) for item in value)
    next_class = 0
    seen: set[int] = set()
    for item in result:
        if item not in seen:
            if item != next_class:
                reject("noncanonical-transport-partition")
            seen.add(item)
            next_class += 1
    logger.debug("transport normalized_partition exit classes=%d", next_class)
    return result


def _precharge_receipt_rows(
    recurrence: tuple[object, ...],
    evaluations: tuple[object, ...],
    action: tuple[object, ...],
    costs: tuple[object, ...],
) -> None:
    """Bound aggregate row expansion before any row-by-row snapshot work."""
    logger.debug(
        "transport receipt precharge entry recurrence=%d evaluations=%d action=%d costs=%d",
        len(recurrence), len(evaluations), len(action), len(costs),
    )
    nodes = len(recurrence) * 5 + len(evaluations) * 6 + len(costs) * 6
    byte_count = 0
    for row in recurrence:
        if type(row) is not RecurrenceCommutingRow:
            reject("transport-recurrence-row-must-be-exact")
        for value in (row.source_input_commitment, row.target_input_commitment):
            if type(value) is not str:
                reject("invalid-transport-input-commitment")
            byte_count += len(value)
    for row in evaluations:
        if type(row) is not EvaluationCommutingRow:
            reject("transport-evaluation-row-must-be-exact")
        if type(row.observer_id) is not str or type(row.payload_digest) is not str:
            reject("invalid-transport-evaluation-text")
        if len(row.observer_id) > MAX_REALIZATION_ID_BYTES:
            reject("invalid-transport-evaluation-text")
        try:
            byte_count += len(row.observer_id.encode("utf-8")) + len(row.payload_digest)
        except UnicodeError:
            reject("invalid-transport-evaluation-text")
    for row in action:
        if type(row) is not ClosureActionRow or type(row.source_partition) is not tuple:
            reject("transport-closure-row-must-be-exact")
        nodes += len(row.source_partition) + 5
        if type(row.target_partition_digest) is not str or type(row.source_partition_digest) is not str:
            reject("invalid-transport-closure-digest")
        byte_count += len(row.target_partition_digest) + len(row.source_partition_digest)
    for row in costs:
        if type(row) is not CostTransportRow:
            reject("transport-cost-row-must-be-exact")
        if type(row.target_partition_digest) is not str or type(row.source_partition_digest) is not str:
            reject("invalid-transport-cost-digest")
        byte_count += len(row.target_partition_digest) + len(row.source_partition_digest)
    if nodes > MAX_TRANSPORT_RECEIPT_NODES:
        reject("transport-receipt-node-limit")
    if byte_count > MAX_TRANSPORT_RECEIPT_BYTES:
        reject("transport-receipt-byte-limit")
    logger.debug("transport receipt precharge exit nodes=%d bytes=%d", nodes, byte_count)


def snapshot_morphism(
    value: object,
    *,
    source_count: int | None = None,
    target_count: int | None = None,
) -> ContextMorphism:
    """Deep-capture one exact total finite index graph."""
    logger.debug("snapshot_morphism entry")
    if type(value) is not ContextMorphism:
        reject("context-morphism-must-be-exact")
    try:
        morphism_id = _identifier(value.morphism_id, "morphism-id")
        source_digest = _digest64(value.source_context_digest, "morphism-source-context")
        target_digest = _digest64(value.target_context_digest, "morphism-target-context")
        graph = value.state_index_map
        version = value.version
        supplied_digest = value.morphism_digest
    except AttributeError:
        reject("context-morphism-missing-fields")
    if type(graph) is not tuple or not 1 <= len(graph) <= MAX_REALIZATION_INPUTS:
        reject("invalid-context-morphism-graph")
    if source_count is not None and len(graph) != source_count:
        reject("context-morphism-not-total")
    maximum = MAX_REALIZATION_INPUTS - 1 if target_count is None else target_count - 1
    captured_graph = tuple(_natural(index, "morphism-target-index", maximum) for index in graph)
    if type(version) is not str or version != CONTEXT_MORPHISM_VERSION:
        reject("context-morphism-version-drift")
    supplied_digest = _digest64(supplied_digest, "context-morphism-digest")
    expected_digest = context_morphism_digest(
        morphism_id, source_digest, target_digest, captured_graph, version
    )
    if supplied_digest != expected_digest:
        reject("context-morphism-digest-drift")
    result = ContextMorphism(
        morphism_id, source_digest, target_digest, captured_graph, version, expected_digest
    )
    logger.debug("snapshot_morphism exit edges=%d", len(captured_graph))
    return result


def snapshot_receipt(value: object) -> RealizationTransportReceipt:
    """Deep-capture and integrity-check a supplied transport receipt."""
    logger.debug("snapshot_receipt entry")
    if type(value) is not RealizationTransportReceipt:
        reject("transport-receipt-must-be-exact")
    try:
        schema, doctrine = value.schema, value.doctrine_fingerprint
        source_context, target_context = value.source_context_digest, value.target_context_digest
        source_witness, target_witness = value.source_witness_digest, value.target_witness_digest
        morphism = value.morphism
        recurrence, evaluations = value.recurrence_rows, value.evaluation_rows
        action, costs = value.closure_action, value.cost_rows
        bottom, joins = value.bottom_preserved, value.joins_preserved
        receipt_digest, scope = value.receipt_digest, value.scope
    except AttributeError:
        reject("transport-receipt-missing-fields")
    if (
        type(schema) is not str
        or type(scope) is not str
        or schema != TRANSPORT_RECEIPT_SCHEMA
        or scope != TRANSPORT_SCOPE
    ):
        reject("transport-receipt-schema-or-scope-drift")
    doctrine = _digest64(doctrine, "transport-doctrine")
    source_context = _digest64(source_context, "transport-source-context")
    target_context = _digest64(target_context, "transport-target-context")
    source_witness = _digest64(source_witness, "transport-source-witness")
    target_witness = _digest64(target_witness, "transport-target-witness")
    trusted_morphism = snapshot_morphism(morphism)
    if trusted_morphism.source_context_digest != source_context or trusted_morphism.target_context_digest != target_context:
        reject("transport-morphism-endpoint-drift")
    if type(recurrence) is not tuple or not 1 <= len(recurrence) <= MAX_REALIZATION_INPUTS:
        reject("invalid-transport-recurrence-rows")
    if type(evaluations) is not tuple or not 1 <= len(evaluations) <= MAX_REALIZATION_EVALUATIONS:
        reject("invalid-transport-evaluation-rows")
    if type(action) is not tuple or not 1 <= len(action) <= MAX_REALIZATION_CLOSURE:
        reject("invalid-transport-closure-action")
    if type(costs) is not tuple or len(costs) != len(action):
        reject("invalid-transport-cost-rows")
    _precharge_receipt_rows(recurrence, evaluations, action, costs)
    recurrence_rows: list[RecurrenceCommutingRow] = []
    for row in recurrence:
        if type(row) is not RecurrenceCommutingRow:
            reject("transport-recurrence-row-must-be-exact")
        recurrence_rows.append(RecurrenceCommutingRow(
            _natural(row.source_index, "transport-source-index", MAX_REALIZATION_INPUTS - 1),
            _natural(row.target_index, "transport-target-index", MAX_REALIZATION_INPUTS - 1),
            _digest64(row.source_input_commitment, "transport-source-input"),
            _digest64(row.target_input_commitment, "transport-target-input"),
        ))
    evaluation_rows: list[EvaluationCommutingRow] = []
    for row in evaluations:
        if type(row) is not EvaluationCommutingRow or type(row.status) is not ObservationStatus:
            reject("transport-evaluation-row-must-be-exact")
        evaluation_rows.append(EvaluationCommutingRow(
            _identifier(row.observer_id, "transport-observer-id"),
            _natural(row.source_index, "transport-source-index", MAX_REALIZATION_INPUTS - 1),
            _natural(row.target_index, "transport-target-index", MAX_REALIZATION_INPUTS - 1),
            row.status,
            _digest64(row.payload_digest, "transport-payload"),
        ))
    action_rows: list[ClosureActionRow] = []
    for row in action:
        if type(row) is not ClosureActionRow:
            reject("transport-closure-row-must-be-exact")
        partition = normalized_partition(row.source_partition, len(trusted_morphism.state_index_map))
        action_rows.append(ClosureActionRow(
            _digest64(row.target_partition_digest, "transport-target-partition"),
            partition,
            _digest64(row.source_partition_digest, "transport-source-partition"),
            _natural(row.source_closure_index, "transport-source-closure-index", MAX_REALIZATION_CLOSURE - 1),
        ))
    cost_rows: list[CostTransportRow] = []
    for row in costs:
        if type(row) is not CostTransportRow or type(row.status) is not CostTransportStatus:
            reject("transport-cost-row-must-be-exact")
        source_cost = _natural(row.source_cost, "transport-source-cost", MAX_REALIZATION_COST)
        target_cost = _natural(row.target_cost, "transport-target-cost", MAX_REALIZATION_COST)
        if source_cost > target_cost:
            reject("transport-cost-increase")
        expected_status = CostTransportStatus.EXACT if source_cost == target_cost else CostTransportStatus.NONINCREASING
        if row.status is not expected_status:
            reject("transport-cost-status-drift")
        cost_rows.append(CostTransportRow(
            _digest64(row.target_partition_digest, "transport-target-partition"),
            _digest64(row.source_partition_digest, "transport-source-partition"),
            source_cost, target_cost, row.status,
        ))
    if type(bottom) is not bool or type(joins) is not bool or not bottom or not joins:
        reject("transport-algebra-law-failed")
    supplied = _digest64(receipt_digest, "transport-receipt-digest")
    frozen_recurrence = tuple(recurrence_rows)
    frozen_evaluations = tuple(evaluation_rows)
    frozen_action = tuple(action_rows)
    frozen_costs = tuple(cost_rows)
    expected = transport_receipt_digest(
        schema, doctrine, source_context, target_context, source_witness, target_witness,
        trusted_morphism, frozen_recurrence, frozen_evaluations, frozen_action, frozen_costs,
        bottom, joins, scope,
    )
    if supplied != expected:
        reject("transport-receipt-digest-drift")
    result = RealizationTransportReceipt(
        schema, doctrine, source_context, target_context, source_witness, target_witness,
        trusted_morphism, frozen_recurrence, frozen_evaluations, frozen_action, frozen_costs,
        bottom, joins, expected, scope,
    )
    logger.debug("snapshot_receipt exit edges=%d closure=%d", len(frozen_recurrence), len(frozen_action))
    return result
