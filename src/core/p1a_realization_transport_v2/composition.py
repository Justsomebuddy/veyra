"""Identity and direct fresh composition for P1-A transport v2."""

from __future__ import annotations
import logging
from ..observer_morphism_types import ObserverSourceBinding
from ..observer_realization_types import ObserverRealizationWitness, RealizationContext
from ..observer_realization_validation import snapshot_context
from ..positive_ontology_types import ObserverDoctrine
from ..realization_transport import compose_realization_context_morphisms, identity_realization_context_morphism
from .runtime import p1a_realization_transport_v2, verify_p1a_realization_transport_v2
from .log_boundary import protected_replay_logs
from .types import P1ARealizationTransportReceiptV2
from .validation import P1ARealizationTransportValidationError, _id, snapshot_receipt

logger = logging.getLogger(__name__)


def _identity_p1a_realization_transport_v2(
    doctrine: ObserverDoctrine,
    binding: ObserverSourceBinding,
    context: RealizationContext,
    witness: ObserverRealizationWitness,
    *,
    observer_id: str,
    transport_id: str = "identity",
    p1a_morphism_id: str = "identity",
    context_morphism_id: str = "identity",
) -> P1ARealizationTransportReceiptV2:
    logger.debug("p1a v2 internal identity entry")
    v1 = identity_realization_context_morphism(doctrine, context, witness, context_morphism_id)
    result = p1a_realization_transport_v2(
        doctrine,
        binding,
        context,
        context,
        witness,
        witness,
        v1,
        transport_id=transport_id,
        p1a_morphism_id=p1a_morphism_id,
        fine_observer_id=observer_id,
        coarse_observer_id=observer_id,
        projection=(),
    )
    logger.debug("p1a v2 internal identity exit digest=%s", result.receipt_digest[:12])
    return result


def identity_p1a_realization_transport_v2(
    doctrine: ObserverDoctrine,
    binding: ObserverSourceBinding,
    context: RealizationContext,
    witness: ObserverRealizationWitness,
    *,
    observer_id: str,
    transport_id: str = "identity",
    p1a_morphism_id: str = "identity",
    context_morphism_id: str = "identity",
) -> P1ARealizationTransportReceiptV2:
    """Construct identity while closing all lower validation exceptions."""
    logger.debug("identity_p1a_realization_transport_v2 entry")
    with protected_replay_logs():
        try:
            _id(observer_id, "p1a-observer-id")
            _id(transport_id, "p1a-transport-id")
            _id(p1a_morphism_id, "p1a-morphism-id")
            _id(context_morphism_id, "p1a-context-morphism-id")
            result = _identity_p1a_realization_transport_v2(
                doctrine,
                binding,
                context,
                witness,
                observer_id=observer_id,
                transport_id=transport_id,
                p1a_morphism_id=p1a_morphism_id,
                context_morphism_id=context_morphism_id,
            )
        except P1ARealizationTransportValidationError:
            logger.error("identity_p1a_realization_transport_v2 rejected")
            raise
        except (TypeError, ValueError, KeyError, OverflowError, RecursionError) as exc:
            logger.error("identity_p1a_realization_transport_v2 lower failure normalized")
            raise P1ARealizationTransportValidationError("p1a-identity-failed") from exc
    logger.debug(
        "identity_p1a_realization_transport_v2 exit digest=%s",
        result.receipt_digest[:12],
    )
    return result


def _verify_child(doctrine, binding, source, target, source_witness, target_witness, receipt):
    """Snapshot a child before reading its embedded translation specification."""
    logger.debug("p1a v2 composition child verification entry")
    if type(receipt) is not P1ARealizationTransportReceiptV2:
        raise P1ARealizationTransportValidationError("p1a-composition-child-must-be-exact")
    trusted_source, _ = snapshot_context(source, doctrine)
    trusted_target, _ = snapshot_context(target, doctrine)
    trusted = snapshot_receipt(
        receipt,
        doctrine,
        binding,
        source_count=len(trusted_source.inputs),
        target_count=len(trusted_target.inputs),
    )
    translation = trusted.transport.translation
    result = verify_p1a_realization_transport_v2(
        doctrine,
        binding,
        source,
        target,
        source_witness,
        target_witness,
        trusted.context_transport,
        trusted,
        transport_id=trusted.transport.transport_id,
        p1a_morphism_id=translation.translation_id,
        fine_observer_id=translation.fine_observer_id,
        coarse_observer_id=translation.coarse_observer_id,
        projection=translation.projection,
    )
    logger.debug("p1a v2 composition child verification exit")
    return result


def _compose_p1a_realization_transport_v2(
    doctrine: ObserverDoctrine,
    binding: ObserverSourceBinding,
    source_context: RealizationContext,
    middle_context: RealizationContext,
    target_context: RealizationContext,
    source_witness: ObserverRealizationWitness,
    middle_witness: ObserverRealizationWitness,
    target_witness: ObserverRealizationWitness,
    first: P1ARealizationTransportReceiptV2,
    second: P1ARealizationTransportReceiptV2,
    *,
    transport_id: str,
    p1a_morphism_id: str,
    context_morphism_id: str,
) -> P1ARealizationTransportReceiptV2:
    logger.debug("p1a v2 internal composition entry")
    trusted_first = _verify_child(
        doctrine, binding, source_context, middle_context, source_witness, middle_witness, first
    )
    trusted_second = _verify_child(
        doctrine, binding, middle_context, target_context, middle_witness, target_witness, second
    )
    first_t = trusted_first.transport.translation
    second_t = trusted_second.transport.translation
    if first_t.coarse_observer_id != second_t.fine_observer_id:
        logger.error("p1a v2 composition middle observer mismatch")
        raise P1ARealizationTransportValidationError("p1a-composition-middle-observer-mismatch")
    v1 = compose_realization_context_morphisms(
        doctrine,
        source_context,
        middle_context,
        target_context,
        trusted_first.context_transport,
        trusted_second.context_transport,
        source_witness,
        middle_witness,
        target_witness,
        context_morphism_id,
    )
    result = p1a_realization_transport_v2(
        doctrine,
        binding,
        source_context,
        target_context,
        source_witness,
        target_witness,
        v1,
        transport_id=transport_id,
        p1a_morphism_id=p1a_morphism_id,
        fine_observer_id=first_t.fine_observer_id,
        coarse_observer_id=second_t.coarse_observer_id,
        projection=first_t.projection + second_t.projection,
    )
    logger.debug("p1a v2 internal composition exit digest=%s", result.receipt_digest[:12])
    return result


def compose_p1a_realization_transport_v2(
    doctrine: ObserverDoctrine,
    binding: ObserverSourceBinding,
    source_context: RealizationContext,
    middle_context: RealizationContext,
    target_context: RealizationContext,
    source_witness: ObserverRealizationWitness,
    middle_witness: ObserverRealizationWitness,
    target_witness: ObserverRealizationWitness,
    first: P1ARealizationTransportReceiptV2,
    second: P1ARealizationTransportReceiptV2,
    *,
    transport_id: str,
    p1a_morphism_id: str,
    context_morphism_id: str,
) -> P1ARealizationTransportReceiptV2:
    """Compose direct endpoints while closing all lower validation failures."""
    logger.debug("compose_p1a_realization_transport_v2 entry")
    with protected_replay_logs():
        try:
            _id(transport_id, "p1a-transport-id")
            _id(p1a_morphism_id, "p1a-morphism-id")
            _id(context_morphism_id, "p1a-context-morphism-id")
            result = _compose_p1a_realization_transport_v2(
                doctrine,
                binding,
                source_context,
                middle_context,
                target_context,
                source_witness,
                middle_witness,
                target_witness,
                first,
                second,
                transport_id=transport_id,
                p1a_morphism_id=p1a_morphism_id,
                context_morphism_id=context_morphism_id,
            )
        except P1ARealizationTransportValidationError:
            logger.error("compose_p1a_realization_transport_v2 rejected")
            raise
        except (TypeError, ValueError, KeyError, IndexError, OverflowError, RecursionError) as exc:
            logger.error("compose_p1a_realization_transport_v2 lower failure normalized")
            raise P1ARealizationTransportValidationError("p1a-composition-failed") from exc
    logger.debug(
        "compose_p1a_realization_transport_v2 exit digest=%s",
        result.receipt_digest[:12],
    )
    return result
