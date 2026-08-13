"""Authoritative runtime for same-doctrine realization transport."""

from __future__ import annotations

import logging

from ..observer_realization import verify_observer_realization_r16
from ..observer_realization_digest import realization_partition_digest, recurrence_commitment
from ..observer_realization_types import ObserverRealizationWitness, RealizationContext
from ..observer_realization_validation import (
    ObserverRealizationValidationError,
    snapshot_context,
    snapshot_realization_doctrine,
)
from ..positive_ontology_types import ObserverDoctrine
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
from .validation import (
    CONTEXT_MORPHISM_VERSION,
    TRANSPORT_RECEIPT_SCHEMA,
    TRANSPORT_SCOPE,
    RealizationTransportValidationError,
    snapshot_morphism,
    snapshot_receipt,
)

logger = logging.getLogger(__name__)


def _normalize_partition(values: tuple[object, ...]) -> tuple[int, ...]:
    """Normalize exact finite labels by first occurrence."""
    logger.debug("transport _normalize_partition entry values=%d", len(values))
    classes: dict[object, int] = {}
    output: list[int] = []
    for value in values:
        if value not in classes:
            classes[value] = len(classes)
        output.append(classes[value])
    result = tuple(output)
    logger.debug("transport _normalize_partition exit classes=%d", len(classes))
    return result


def _join_partition(left: tuple[int, ...], right: tuple[int, ...]) -> tuple[int, ...]:
    """Compute the common refinement of two normalized partitions."""
    logger.debug("transport _join_partition entry states=%d", len(left))
    if len(left) != len(right):
        logger.error("transport _join_partition carrier mismatch")
        raise RealizationTransportValidationError("transport-join-carrier-mismatch")
    result = _normalize_partition(tuple(zip(left, right, strict=True)))
    logger.debug("transport _join_partition exit classes=%d", 1 + max(result))
    return result


def _new_morphism(
    morphism_id: str,
    source_context: RealizationContext,
    target_context: RealizationContext,
    state_index_map: tuple[int, ...],
) -> ContextMorphism:
    """Construct and validate one endpoint-bound total index graph."""
    logger.debug("transport _new_morphism entry")
    if type(morphism_id) is not str or type(state_index_map) is not tuple:
        logger.error("transport _new_morphism raw type rejected")
        raise RealizationTransportValidationError("invalid-context-morphism-input")
    if not morphism_id or len(morphism_id) > 128:
        logger.error("transport _new_morphism identifier length rejected")
        raise RealizationTransportValidationError("invalid-context-morphism-input")
    try:
        morphism_id_bytes = morphism_id.encode("utf-8")
    except UnicodeError as exc:
        logger.error("transport _new_morphism identifier encoding rejected")
        raise RealizationTransportValidationError(
            "invalid-context-morphism-input"
        ) from exc
    if (
        len(morphism_id_bytes) > 128
        or len(state_index_map) != len(source_context.inputs)
        or any(
            type(index) is not int or not 0 <= index < len(target_context.inputs)
            for index in state_index_map
        )
    ):
        logger.error("transport _new_morphism graph or identifier rejected")
        raise RealizationTransportValidationError("invalid-context-morphism-input")
    provisional = ContextMorphism(
        morphism_id,
        source_context.context_digest,
        target_context.context_digest,
        state_index_map,
        CONTEXT_MORPHISM_VERSION,
        context_morphism_digest(
            morphism_id,
            source_context.context_digest,
            target_context.context_digest,
            state_index_map,
            CONTEXT_MORPHISM_VERSION,
        ),
    )
    result = snapshot_morphism(
        provisional,
        source_count=len(source_context.inputs),
        target_count=len(target_context.inputs),
    )
    logger.debug("transport _new_morphism exit edges=%d", len(result.state_index_map))
    return result


def _verified_endpoints(
    doctrine: ObserverDoctrine,
    source_context: RealizationContext,
    target_context: RealizationContext,
    source_witness: ObserverRealizationWitness,
    target_witness: ObserverRealizationWitness,
) -> tuple[
    ObserverDoctrine,
    RealizationContext,
    RealizationContext,
    tuple[bytes, ...],
    tuple[bytes, ...],
    ObserverRealizationWitness,
    ObserverRealizationWitness,
]:
    """Snapshot contexts and authoritatively replay both endpoint witnesses."""
    logger.debug("transport _verified_endpoints entry")
    try:
        trusted_doctrine = snapshot_realization_doctrine(doctrine)
        trusted_source, source_canonical = snapshot_context(source_context, trusted_doctrine)
        trusted_target, target_canonical = snapshot_context(target_context, trusted_doctrine)
        replayed_source = verify_observer_realization_r16(
            trusted_doctrine, trusted_source, source_witness
        )
        replayed_target = verify_observer_realization_r16(
            trusted_doctrine, trusted_target, target_witness
        )
    except ObserverRealizationValidationError as exc:
        logger.error("transport endpoint replay rejected reason=%s", exc)
        raise RealizationTransportValidationError("transport-endpoint-authoritative-replay-failed") from exc
    if (
        trusted_source.response_policy is not trusted_target.response_policy
        or trusted_source.cost_policy is not trusted_target.cost_policy
        or trusted_source.closure_policy is not trusted_target.closure_policy
        or trusted_source.version != trusted_target.version
        or trusted_source.observer_costs != trusted_target.observer_costs
    ):
        logger.error("transport endpoint policy or ordered cost drift")
        raise RealizationTransportValidationError("transport-endpoint-policy-or-cost-drift")
    logger.debug("transport _verified_endpoints exit")
    return (
        trusted_doctrine, trusted_source, trusted_target,
        source_canonical, target_canonical, replayed_source, replayed_target,
    )


def _evaluation_index(
    witness: ObserverRealizationWitness,
) -> dict[tuple[str, int], object]:
    """Index freshly replayed evaluation rows by exact source and state index."""
    logger.debug("transport _evaluation_index entry rows=%d", len(witness.evaluations))
    result = {(row.observer_id, row.state_index): row for row in witness.evaluations}
    if len(result) != len(witness.evaluations):
        logger.error("transport replay produced duplicate evaluation key")
        raise RealizationTransportValidationError("transport-duplicate-evaluation-key")
    logger.debug("transport _evaluation_index exit rows=%d", len(result))
    return result


def _build_receipt(
    doctrine: ObserverDoctrine,
    source_context: RealizationContext,
    target_context: RealizationContext,
    source_canonical: tuple[bytes, ...],
    target_canonical: tuple[bytes, ...],
    source_witness: ObserverRealizationWitness,
    target_witness: ObserverRealizationWitness,
    morphism: ContextMorphism,
) -> RealizationTransportReceipt:
    """Reconstruct every commuting row and algebraic law for one arrow."""
    logger.debug("transport _build_receipt entry edges=%d", len(morphism.state_index_map))
    recurrence_rows: list[RecurrenceCommutingRow] = []
    for source_index, target_index in enumerate(morphism.state_index_map):
        source_bytes = source_canonical[source_index]
        target_bytes = target_canonical[target_index]
        if source_bytes != target_bytes:
            logger.error("transport recurrence square failed source_index=%d target_index=%d", source_index, target_index)
            raise RealizationTransportValidationError("transport-recurrence-square-failed")
        recurrence_rows.append(RecurrenceCommutingRow(
            source_index,
            target_index,
            recurrence_commitment(source_bytes),
            recurrence_commitment(target_bytes),
        ))
    source_evaluations = _evaluation_index(source_witness)
    target_evaluations = _evaluation_index(target_witness)
    evaluation_rows: list[EvaluationCommutingRow] = []
    for member in doctrine.observers:
        for source_index, target_index in enumerate(morphism.state_index_map):
            source_row = source_evaluations.get((member.observer_id, source_index))
            target_row = target_evaluations.get((member.observer_id, target_index))
            if source_row is None or target_row is None:
                logger.error("transport evaluation coverage failed observer=%s", member.observer_id)
                raise RealizationTransportValidationError("transport-evaluation-coverage-failed")
            if (
                source_row.status is not target_row.status
                or source_row.observation_payload != target_row.observation_payload
                or source_row.input_commitment != target_row.input_commitment
            ):
                logger.error(
                    "transport evaluation square failed observer=%s source_index=%d target_index=%d",
                    member.observer_id, source_index, target_index,
                )
                raise RealizationTransportValidationError("transport-evaluation-square-failed")
            evaluation_rows.append(EvaluationCommutingRow(
                member.observer_id, source_index, target_index,
                source_row.status, source_row.payload_digest,
            ))
    source_partitions = {row.partition: index for index, row in enumerate(source_witness.closure)}
    if len(source_partitions) != len(source_witness.closure):
        logger.error("transport source closure extensional duplicate")
        raise RealizationTransportValidationError("transport-source-closure-not-extensional")
    action_rows: list[ClosureActionRow] = []
    cost_rows: list[CostTransportRow] = []
    action_by_target: dict[tuple[int, ...], tuple[int, ...]] = {}
    for target_row in target_witness.closure:
        pulled = _normalize_partition(tuple(target_row.partition[index] for index in morphism.state_index_map))
        source_index = source_partitions.get(pulled)
        if source_index is None:
            logger.error("transport pullback absent from source closure")
            raise RealizationTransportValidationError("transport-pullback-not-admitted")
        source_row = source_witness.closure[source_index]
        if source_row.cost > target_row.cost:
            logger.error("transport cost increased source=%d target=%d", source_row.cost, target_row.cost)
            raise RealizationTransportValidationError("transport-cost-increase")
        source_partition_digest = realization_partition_digest(pulled)
        action_rows.append(ClosureActionRow(
            target_row.partition_digest, pulled, source_partition_digest, source_index
        ))
        cost_rows.append(CostTransportRow(
            target_row.partition_digest,
            source_partition_digest,
            source_row.cost,
            target_row.cost,
            CostTransportStatus.EXACT
            if source_row.cost == target_row.cost
            else CostTransportStatus.NONINCREASING,
        ))
        action_by_target[target_row.partition] = pulled
    target_bottom = tuple(row.partition for row in target_witness.closure if len(set(row.partition)) == 1)
    source_bottom = tuple(row.partition for row in source_witness.closure if len(set(row.partition)) == 1)
    bottom_preserved = (
        len(target_bottom) == 1
        and len(source_bottom) == 1
        and action_by_target.get(target_bottom[0]) == source_bottom[0]
    )
    if not bottom_preserved:
        logger.error("transport bottom law failed")
        raise RealizationTransportValidationError("transport-bottom-law-failed")
    joins_preserved = True
    for left in target_witness.closure:
        for right in target_witness.closure:
            target_join = _join_partition(left.partition, right.partition)
            pulled_join = action_by_target.get(target_join)
            expected_join = _join_partition(
                action_by_target[left.partition], action_by_target[right.partition]
            )
            if pulled_join != expected_join:
                joins_preserved = False
                break
        if not joins_preserved:
            break
    if not joins_preserved:
        logger.error("transport join law failed")
        raise RealizationTransportValidationError("transport-join-law-failed")
    frozen_recurrence = tuple(recurrence_rows)
    frozen_evaluations = tuple(evaluation_rows)
    frozen_action = tuple(action_rows)
    frozen_costs = tuple(cost_rows)
    digest = transport_receipt_digest(
        TRANSPORT_RECEIPT_SCHEMA,
        doctrine.fingerprint,
        source_context.context_digest,
        target_context.context_digest,
        source_witness.witness_digest,
        target_witness.witness_digest,
        morphism,
        frozen_recurrence,
        frozen_evaluations,
        frozen_action,
        frozen_costs,
        bottom_preserved,
        joins_preserved,
        TRANSPORT_SCOPE,
    )
    result = RealizationTransportReceipt(
        TRANSPORT_RECEIPT_SCHEMA,
        doctrine.fingerprint,
        source_context.context_digest,
        target_context.context_digest,
        source_witness.witness_digest,
        target_witness.witness_digest,
        morphism,
        frozen_recurrence,
        frozen_evaluations,
        frozen_action,
        frozen_costs,
        bottom_preserved,
        joins_preserved,
        digest,
        TRANSPORT_SCOPE,
    )
    logger.debug(
        "transport _build_receipt exit evaluations=%d closure=%d digest=%s",
        len(frozen_evaluations), len(frozen_action), digest[:12],
    )
    return result


def realization_context_morphism(
    doctrine: ObserverDoctrine,
    source_context: RealizationContext,
    target_context: RealizationContext,
    morphism_id: str,
    state_index_map: tuple[int, ...],
    source_witness: ObserverRealizationWitness,
    target_witness: ObserverRealizationWitness,
) -> RealizationTransportReceipt:
    """Construct one same-doctrine arrow after authoritative endpoint replay."""
    logger.debug("realization_context_morphism entry")
    (
        trusted_doctrine, trusted_source, trusted_target,
        source_canonical, target_canonical, replayed_source, replayed_target,
    ) = _verified_endpoints(
        doctrine, source_context, target_context, source_witness, target_witness
    )
    morphism = _new_morphism(morphism_id, trusted_source, trusted_target, state_index_map)
    result = _build_receipt(
        trusted_doctrine, trusted_source, trusted_target,
        source_canonical, target_canonical, replayed_source, replayed_target, morphism,
    )
    logger.debug("realization_context_morphism exit digest=%s", result.receipt_digest[:12])
    return result


def verify_realization_transport(
    doctrine: ObserverDoctrine,
    source_context: RealizationContext,
    target_context: RealizationContext,
    morphism: ContextMorphism,
    source_witness: ObserverRealizationWitness,
    target_witness: ObserverRealizationWitness,
    receipt: RealizationTransportReceipt,
) -> RealizationTransportReceipt:
    """Freshly replay endpoints and require exact reconstructed receipt equality."""
    logger.debug("verify_realization_transport entry")
    supplied = snapshot_receipt(receipt)
    (
        trusted_doctrine, trusted_source, trusted_target,
        source_canonical, target_canonical, replayed_source, replayed_target,
    ) = _verified_endpoints(
        doctrine, source_context, target_context, source_witness, target_witness
    )
    trusted_morphism = snapshot_morphism(
        morphism,
        source_count=len(trusted_source.inputs),
        target_count=len(trusted_target.inputs),
    )
    if (
        trusted_morphism.source_context_digest != trusted_source.context_digest
        or trusted_morphism.target_context_digest != trusted_target.context_digest
    ):
        logger.error("verify_realization_transport morphism endpoint mismatch")
        raise RealizationTransportValidationError("transport-morphism-endpoint-mismatch")
    expected = _build_receipt(
        trusted_doctrine, trusted_source, trusted_target,
        source_canonical, target_canonical, replayed_source, replayed_target,
        trusted_morphism,
    )
    if supplied != expected:
        logger.error("verify_realization_transport reconstructed receipt mismatch")
        raise RealizationTransportValidationError("transport-authoritative-reconstruction-mismatch")
    logger.debug("verify_realization_transport exit digest=%s", expected.receipt_digest[:12])
    return expected


def identity_realization_context_morphism(
    doctrine: ObserverDoctrine,
    context: RealizationContext,
    witness: ObserverRealizationWitness,
    morphism_id: str = "identity",
) -> RealizationTransportReceipt:
    """Construct the replayed identity arrow for one realization context."""
    logger.debug("identity_realization_context_morphism entry")
    if type(context) is not RealizationContext:
        logger.error("identity realization context is not exact")
        raise RealizationTransportValidationError("identity-context-must-be-exact")
    try:
        inputs = context.inputs
    except AttributeError as exc:
        logger.error("identity realization context missing inputs")
        raise RealizationTransportValidationError("identity-context-missing-inputs") from exc
    if type(inputs) is not tuple:
        logger.error("identity realization context inputs are not exact")
        raise RealizationTransportValidationError("identity-context-inputs-must-be-exact")
    count = len(inputs)
    result = realization_context_morphism(
        doctrine, context, context, morphism_id, tuple(range(count)), witness, witness
    )
    logger.debug("identity_realization_context_morphism exit")
    return result


def compose_realization_context_morphisms(
    doctrine: ObserverDoctrine,
    source_context: RealizationContext,
    middle_context: RealizationContext,
    target_context: RealizationContext,
    first: ContextMorphism | RealizationTransportReceipt,
    second: ContextMorphism | RealizationTransportReceipt,
    source_witness: ObserverRealizationWitness,
    middle_witness: ObserverRealizationWitness,
    target_witness: ObserverRealizationWitness,
    morphism_id: str,
) -> RealizationTransportReceipt:
    """Validate two endpoint-bound graphs and freshly rebuild their composite."""
    logger.debug("compose_realization_context_morphisms entry")
    (
        trusted_doctrine, trusted_source, trusted_middle,
        source_canonical, middle_canonical, replayed_source, replayed_middle,
    ) = _verified_endpoints(
        doctrine, source_context, middle_context, source_witness, middle_witness
    )
    (
        _, trusted_middle_again, trusted_target,
        middle_canonical_again, target_canonical, replayed_middle_again, replayed_target,
    ) = _verified_endpoints(
        trusted_doctrine, middle_context, target_context, middle_witness, target_witness
    )
    if (
        trusted_middle != trusted_middle_again
        or middle_canonical != middle_canonical_again
        or replayed_middle != replayed_middle_again
    ):
        logger.error("compose realization transport middle replay drift")
        raise RealizationTransportValidationError("transport-composition-middle-replay-drift")
    first_morphism = snapshot_receipt(first).morphism if type(first) is RealizationTransportReceipt else first
    second_morphism = snapshot_receipt(second).morphism if type(second) is RealizationTransportReceipt else second
    verified_first = snapshot_morphism(
        first_morphism,
        source_count=len(trusted_source.inputs),
        target_count=len(trusted_middle.inputs),
    )
    verified_second = snapshot_morphism(
        second_morphism,
        source_count=len(trusted_middle.inputs),
        target_count=len(trusted_target.inputs),
    )
    if (
        verified_first.source_context_digest != trusted_source.context_digest
        or verified_first.target_context_digest != trusted_middle.context_digest
        or verified_second.source_context_digest != trusted_middle.context_digest
        or verified_second.target_context_digest != trusted_target.context_digest
    ):
        logger.error("compose realization transport endpoint mismatch")
        raise RealizationTransportValidationError("transport-composition-endpoint-mismatch")
    expected_first = _build_receipt(
        trusted_doctrine, trusted_source, trusted_middle,
        source_canonical, middle_canonical, replayed_source, replayed_middle,
        verified_first,
    )
    expected_second = _build_receipt(
        trusted_doctrine, trusted_middle, trusted_target,
        middle_canonical, target_canonical, replayed_middle, replayed_target,
        verified_second,
    )
    if type(first) is RealizationTransportReceipt:
        if snapshot_receipt(first) != expected_first:
            logger.error("compose first receipt reconstruction mismatch")
            raise RealizationTransportValidationError("transport-first-receipt-reconstruction-mismatch")
    if type(second) is RealizationTransportReceipt:
        if snapshot_receipt(second) != expected_second:
            logger.error("compose second receipt reconstruction mismatch")
            raise RealizationTransportValidationError("transport-second-receipt-reconstruction-mismatch")
    composite_graph = tuple(
        verified_second.state_index_map[middle_index]
        for middle_index in verified_first.state_index_map
    )
    morphism = _new_morphism(morphism_id, trusted_source, trusted_target, composite_graph)
    result = _build_receipt(
        trusted_doctrine, trusted_source, trusted_target,
        source_canonical, target_canonical, replayed_source, replayed_target, morphism,
    )
    logger.debug("compose_realization_context_morphisms exit edges=%d", len(composite_graph))
    return result
