"""Fresh authoritative construction and verification of P1-A transport v2."""

from __future__ import annotations
from dataclasses import replace
import logging
from ..observer_core_codec import decode_observer
from ..observer_core_semantics import observe
from ..observer_morphism import observer_morphism_judgment
from ..observer_morphism_types import MorphismStatus, ObserverSourceBinding, ProjectionStep
from ..observer_morphism_validation import (
    ObserverMorphismValidationError,
    snapshot_morphism_doctrine,
    snapshot_source_binding,
)
from ..observer_realization import verify_observer_realization_r16
from ..observer_realization_types import (
    ObservationStatus,
    ObserverRealizationWitness,
    RealizationContext,
)
from ..observer_realization_validation import ObserverRealizationValidationError, snapshot_context
from ..positive_ontology_types import ObserverDoctrine
from ..realization_transport import (
    RealizationTransportReceipt,
    RealizationTransportValidationError,
    verify_realization_transport,
)
from ..realization_transport.validation import snapshot_receipt as snapshot_v1_receipt
from .digest import judgment_root, receipt_digest, row_digest, transport_digest
from .log_boundary import protected_replay_logs
from .observation import P1AObservationUndefined, canonical_observation_payload, transport_observation
from .partitions import endpoint_partition_law
from .types import (
    P1AEndpointV2,
    P1AObservationCommutingRowV2,
    P1AObservationPayloadV2,
    P1AObservationTransportV2,
    P1AOutcomeLawV2,
    P1ARealizationTransportReceiptV2,
)
from .validation import (
    MAX_P1A_V2_ROWS,
    MAX_P1A_V2_SIX_STREAM_BYTES,
    MAX_P1A_V2_TRANSPORTED_ENDPOINT_BYTES,
    P1A_RECEIPT_SCHEMA,
    P1A_TRANSPORT_SCOPE,
    P1A_TRANSPORT_VERSION,
    P1ARealizationTransportValidationError,
    _id,
    snapshot_receipt,
)

logger = logging.getLogger(__name__)


def _fail(reason: str) -> P1ARealizationTransportValidationError:
    logger.error("p1a v2 runtime rejected reason=%s", reason)
    return P1ARealizationTransportValidationError(reason)


def _normalize_partition_labels(values: tuple[int, ...]) -> tuple[int, ...]:
    """Normalize finite class labels by first occurrence."""
    logger.debug("p1a runtime partition normalization entry items=%d", len(values))
    classes: dict[int, int] = {}
    result: list[int] = []
    for item in values:
        if item not in classes:
            classes[item] = len(classes)
        result.append(classes[item])
    frozen = tuple(result)
    logger.debug("p1a runtime partition normalization exit classes=%d", len(classes))
    return frozen


def _precharge_retained_streams(
    graph: tuple[int, ...],
    source_fine: tuple[P1AObservationPayloadV2, ...],
    source_transported: tuple[P1AObservationPayloadV2, ...],
    source_coarse: tuple[P1AObservationPayloadV2, ...],
    target_fine: tuple[P1AObservationPayloadV2, ...],
    target_transported: tuple[P1AObservationPayloadV2, ...],
    target_coarse: tuple[P1AObservationPayloadV2, ...],
) -> int:
    """Charge the six retained row streams before receipt construction."""
    logger.debug("p1a six-stream precharge entry rows=%d", len(graph))
    if not 1 <= len(graph) <= MAX_P1A_V2_ROWS:
        logger.error("p1a six-stream row bound rejected")
        raise _fail("invalid-p1a-rows")
    total = 0
    try:
        for source_index, target_index in enumerate(graph):
            payloads = (
                source_fine[source_index],
                source_transported[source_index],
                source_coarse[source_index],
                target_fine[target_index],
                target_transported[target_index],
                target_coarse[target_index],
            )
            total += sum(len(item.canonical_payload) for item in payloads)
            if total > MAX_P1A_V2_SIX_STREAM_BYTES:
                logger.error("p1a six-stream precharge byte limit rejected")
                raise _fail("p1a-six-stream-byte-limit")
    except (IndexError, TypeError, AttributeError) as exc:
        logger.error("p1a six-stream precharge graph rejected")
        raise _fail("p1a-six-stream-graph-invalid") from exc
    logger.debug("p1a six-stream precharge exit bytes=%d", total)
    return total


def _evaluation_index(witness: ObserverRealizationWitness) -> dict[tuple[str, int], object]:
    """Index exact replay rows without invoking caller equality hooks."""
    logger.debug("p1a v2 evaluation index entry")
    result = {(row.observer_id, row.state_index): row for row in witness.evaluations}
    if len(result) != len(witness.evaluations):
        logger.error("p1a v2 evaluation index duplicate rejected")
        raise _fail("p1a-duplicate-endpoint-evaluation")
    logger.debug("p1a v2 evaluation index exit rows=%d", len(result))
    return result


def _fresh_endpoint(
    doctrine: ObserverDoctrine,
    context: RealizationContext,
    witness: ObserverRealizationWitness,
    fine_id: str,
    coarse_id: str,
    translation,
    binding: ObserverSourceBinding,
) -> tuple[
    tuple[P1AObservationPayloadV2, ...],
    tuple[P1AObservationPayloadV2, ...],
    tuple[P1AObservationPayloadV2, ...],
    ObserverRealizationWitness,
    RealizationContext,
]:
    logger.debug(
        "p1a v2 fresh endpoint entry states=%d",
        len(context.inputs) if type(context) is RealizationContext and type(context.inputs) is tuple else -1,
    )
    trusted_context, _ = snapshot_context(context, doctrine)
    replayed = verify_observer_realization_r16(doctrine, trusted_context, witness)
    index = _evaluation_index(replayed)
    members = {m.observer_id: m for m in doctrine.observers}
    fine_program = decode_observer(members[fine_id].canonical)
    coarse_program = decode_observer(members[coarse_id].canonical)
    fine_payload = []
    transported = []
    coarse = []
    transported_bytes = 0
    for state_index, item in enumerate(trusted_context.inputs):
        f = observe(fine_program, item.recurrence)
        c = observe(coarse_program, item.recurrence)
        fp = canonical_observation_payload(f)
        cp = canonical_observation_payload(c)
        fine_row = index.get((fine_id, state_index))
        coarse_row = index.get((coarse_id, state_index))
        if (
            fine_row is None
            or coarse_row is None
            or fp.canonical_payload != fine_row.observation_payload
            or cp.canonical_payload != coarse_row.observation_payload
        ):
            raise _fail("p1a-fresh-witness-payload-mismatch")
        try:
            transported_out = transport_observation(doctrine, binding, translation, f)
        except P1AObservationUndefined as exc:
            raise _fail("p1a-observation-undefined") from exc
        tp = canonical_observation_payload(transported_out)
        transported_bytes += len(tp.canonical_payload)
        if tp != cp:
            raise _fail("p1a-vertical-observation-square-failed")
        fine_payload.append(fp)
        transported.append(tp)
        coarse.append(cp)
    if transported_bytes > MAX_P1A_V2_TRANSPORTED_ENDPOINT_BYTES:
        raise _fail("p1a-transported-endpoint-byte-limit")
    logger.debug(
        "p1a v2 fresh endpoint exit states=%d transported_bytes=%d",
        len(fine_payload),
        transported_bytes,
    )
    return (
        tuple(fine_payload),
        tuple(transported),
        tuple(coarse),
        replayed,
        trusted_context,
    )


def _build_p1a_realization_transport_v2(
    doctrine: ObserverDoctrine,
    binding: ObserverSourceBinding,
    source_context: RealizationContext,
    target_context: RealizationContext,
    source_witness: ObserverRealizationWitness,
    target_witness: ObserverRealizationWitness,
    context_transport: RealizationTransportReceipt,
    *,
    transport_id: str,
    p1a_morphism_id: str,
    fine_observer_id: str,
    coarse_observer_id: str,
    projection: tuple[ProjectionStep, ...],
) -> P1ARealizationTransportReceiptV2:
    """Build one all-status square only from fresh STRONG and endpoint replay."""
    logger.debug("p1a v2 internal build entry")
    try:
        trusted_doctrine = snapshot_morphism_doctrine(doctrine)
        trusted_binding = snapshot_source_binding(binding, trusted_doctrine)
        judgment = observer_morphism_judgment(
            trusted_doctrine, trusted_binding, p1a_morphism_id, fine_observer_id, coarse_observer_id, projection
        )
        if (
            judgment.status is not MorphismStatus.STRONG
            or judgment.translation is None
            or judgment.obstruction
            or not judgment.information_factorizes_on_comparison
            or not judgment.coarse_domain_in_fine_domain
            or not judgment.witness_checked
        ):
            raise _fail("p1a-strong-judgment-required")
        if type(context_transport) is not RealizationTransportReceipt:
            raise _fail("p1a-v1-receipt-must-be-exact")
        trusted_v1 = snapshot_v1_receipt(context_transport)
        verified_v1 = verify_realization_transport(
            trusted_doctrine,
            source_context,
            target_context,
            trusted_v1.morphism,
            source_witness,
            target_witness,
            trusted_v1,
        )
        source_fine, source_transported, source_coarse, replayed_source, trusted_source = _fresh_endpoint(
            trusted_doctrine,
            source_context,
            source_witness,
            judgment.fine_observer_id,
            judgment.coarse_observer_id,
            judgment.translation,
            trusted_binding,
        )
        target_fine, target_transported, target_coarse, replayed_target, trusted_target = _fresh_endpoint(
            trusted_doctrine,
            target_context,
            target_witness,
            judgment.fine_observer_id,
            judgment.coarse_observer_id,
            judgment.translation,
            trusted_binding,
        )
    except P1ARealizationTransportValidationError:
        raise
    except (
        ObserverMorphismValidationError,
        ObserverRealizationValidationError,
        RealizationTransportValidationError,
        KeyError,
        TypeError,
        ValueError,
    ) as exc:
        raise _fail("p1a-authoritative-replay-failed") from exc
    graph = verified_v1.morphism.state_index_map
    _precharge_retained_streams(
        graph,
        source_fine,
        source_transported,
        source_coarse,
        target_fine,
        target_transported,
        target_coarse,
    )
    source_index = _evaluation_index(replayed_source)
    target_index = _evaluation_index(replayed_target)
    rows = []
    for si, ti in enumerate(graph):
        if source_fine[si] != target_fine[ti] or source_coarse[si] != target_coarse[ti]:
            raise _fail("p1a-horizontal-observation-square-failed")
        six = (
            source_fine[si],
            source_transported[si],
            source_coarse[si],
            target_fine[ti],
            target_transported[ti],
            target_coarse[ti],
        )
        statuses = {x.status for x in six}
        law = (
            P1AOutcomeLawV2.READY_COMMUTES_EXACT
            if statuses == {ObservationStatus.READY}
            else P1AOutcomeLawV2.BLOCKED_COMMUTES_EXACT
            if statuses == {ObservationStatus.BLOCKED}
            else None
        )
        if law is None:
            raise _fail("p1a-row-status-law-drift")
        sfrow = source_index[(judgment.fine_observer_id, si)]
        tfrow = target_index[(judgment.fine_observer_id, ti)]
        provisional = P1AObservationCommutingRowV2(
            si, ti, sfrow.input_commitment, tfrow.input_commitment, *six, law, "0" * 64
        )
        rows.append(replace(provisional, row_digest=row_digest(provisional)))
    source_law = endpoint_partition_law(P1AEndpointV2.SOURCE, source_fine, source_transported, source_coarse)
    target_law = endpoint_partition_law(P1AEndpointV2.TARGET, target_fine, target_transported, target_coarse)
    expected_fine = tuple(target_law.fine_partition[i] for i in graph)
    expected_coarse = tuple(target_law.coarse_partition[i] for i in graph)

    if source_law.fine_partition != _normalize_partition_labels(
        expected_fine
    ) or source_law.coarse_partition != _normalize_partition_labels(expected_coarse):
        raise _fail("p1a-horizontal-partition-law-failed")
    provisional_transport = P1AObservationTransportV2(
        transport_id,
        trusted_doctrine.fingerprint,
        trusted_binding.membership_digest,
        judgment_root(judgment),
        judgment.translation,
        trusted_source.context_digest,
        trusted_target.context_digest,
        replayed_source.witness_digest,
        replayed_target.witness_digest,
        verified_v1.morphism.morphism_digest,
        verified_v1.receipt_digest,
        trusted_source.response_policy,
        trusted_source.cost_policy,
        trusted_source.closure_policy,
        P1A_TRANSPORT_VERSION,
        P1A_TRANSPORT_SCOPE,
        "0" * 64,
    )
    transport = replace(provisional_transport, transport_digest=transport_digest(provisional_transport))
    frozen = tuple(rows)
    provisional = P1ARealizationTransportReceiptV2(
        P1A_RECEIPT_SCHEMA, transport, verified_v1, frozen, source_law, target_law, "0" * 64, P1A_TRANSPORT_SCOPE
    )
    result = replace(
        provisional,
        receipt_digest=receipt_digest(
            P1A_RECEIPT_SCHEMA, transport, frozen, source_law, target_law, P1A_TRANSPORT_SCOPE
        ),
    )
    result = snapshot_receipt(
        result,
        trusted_doctrine,
        trusted_binding,
        source_count=len(trusted_source.inputs),
        target_count=len(trusted_target.inputs),
    )
    logger.debug(
        "p1a v2 internal build exit rows=%d digest=%s",
        len(result.rows),
        result.receipt_digest[:12],
    )
    return result


def p1a_realization_transport_v2(
    doctrine: ObserverDoctrine,
    binding: ObserverSourceBinding,
    source_context: RealizationContext,
    target_context: RealizationContext,
    source_witness: ObserverRealizationWitness,
    target_witness: ObserverRealizationWitness,
    context_transport: RealizationTransportReceipt,
    *,
    transport_id: str,
    p1a_morphism_id: str,
    fine_observer_id: str,
    coarse_observer_id: str,
    projection: tuple[ProjectionStep, ...],
) -> P1ARealizationTransportReceiptV2:
    """Build one all-status square with a normalized public failure boundary."""
    logger.debug("p1a_realization_transport_v2 entry")
    with protected_replay_logs():
        try:
            checked_transport_id = _id(transport_id, "p1a-transport-id")
            result = _build_p1a_realization_transport_v2(
                doctrine,
                binding,
                source_context,
                target_context,
                source_witness,
                target_witness,
                context_transport,
                transport_id=checked_transport_id,
                p1a_morphism_id=p1a_morphism_id,
                fine_observer_id=fine_observer_id,
                coarse_observer_id=coarse_observer_id,
                projection=projection,
            )
        except P1ARealizationTransportValidationError:
            logger.error("p1a_realization_transport_v2 rejected")
            raise
        except (TypeError, ValueError, KeyError, IndexError, OverflowError, RecursionError) as exc:
            logger.error("p1a_realization_transport_v2 lower failure normalized")
            raise _fail("p1a-authoritative-replay-failed") from exc
    logger.debug(
        "p1a_realization_transport_v2 exit rows=%d digest=%s",
        len(result.rows),
        result.receipt_digest[:12],
    )
    return result


def _verify_p1a_realization_transport_v2(
    doctrine,
    binding,
    source_context,
    target_context,
    source_witness,
    target_witness,
    context_transport,
    receipt,
    *,
    transport_id,
    p1a_morphism_id,
    fine_observer_id,
    coarse_observer_id,
    projection,
):
    """Require exact equality with a wholly reconstructed receipt."""
    logger.debug("p1a v2 internal verify entry")
    trusted_doctrine = snapshot_morphism_doctrine(doctrine)
    trusted_binding = snapshot_source_binding(binding, trusted_doctrine)
    trusted_source, _ = snapshot_context(source_context, trusted_doctrine)
    trusted_target, _ = snapshot_context(target_context, trusted_doctrine)
    supplied = snapshot_receipt(
        receipt,
        trusted_doctrine,
        trusted_binding,
        source_count=len(trusted_source.inputs),
        target_count=len(trusted_target.inputs),
    )
    expected = p1a_realization_transport_v2(
        doctrine,
        binding,
        source_context,
        target_context,
        source_witness,
        target_witness,
        context_transport,
        transport_id=transport_id,
        p1a_morphism_id=p1a_morphism_id,
        fine_observer_id=fine_observer_id,
        coarse_observer_id=coarse_observer_id,
        projection=projection,
    )
    if supplied != expected:
        raise _fail("p1a-authoritative-reconstruction-mismatch")
    logger.debug("p1a v2 internal verify exit digest=%s", expected.receipt_digest[:12])
    return expected


def verify_p1a_realization_transport_v2(
    doctrine,
    binding,
    source_context,
    target_context,
    source_witness,
    target_witness,
    context_transport,
    receipt,
    *,
    transport_id,
    p1a_morphism_id,
    fine_observer_id,
    coarse_observer_id,
    projection,
):
    """Verify by reconstruction while normalizing every lower-layer failure."""
    logger.debug("verify_p1a_realization_transport_v2 entry")
    with protected_replay_logs():
        try:
            _id(transport_id, "p1a-transport-id")
            result = _verify_p1a_realization_transport_v2(
                doctrine,
                binding,
                source_context,
                target_context,
                source_witness,
                target_witness,
                context_transport,
                receipt,
                transport_id=transport_id,
                p1a_morphism_id=p1a_morphism_id,
                fine_observer_id=fine_observer_id,
                coarse_observer_id=coarse_observer_id,
                projection=projection,
            )
        except P1ARealizationTransportValidationError:
            logger.error("verify_p1a_realization_transport_v2 rejected")
            raise
        except (TypeError, ValueError, KeyError, IndexError, OverflowError, RecursionError) as exc:
            logger.error("verify_p1a_realization_transport_v2 lower failure normalized")
            raise _fail("p1a-authoritative-replay-failed") from exc
    logger.debug(
        "verify_p1a_realization_transport_v2 exit digest=%s",
        result.receipt_digest[:12],
    )
    return result
