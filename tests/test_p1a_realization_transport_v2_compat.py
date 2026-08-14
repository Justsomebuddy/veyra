"""Frozen v1 compatibility and facade-separation tests for RFC 169."""

from __future__ import annotations

from dataclasses import fields
import inspect
import logging

import pytest

import src.core as core_facade
from src.core.p1a_realization_transport_v2 import (
    P1ARealizationTransportValidationError,
    compose_p1a_realization_transport_v2,
    identity_p1a_realization_transport_v2,
    p1a_realization_transport_v2,
    verify_p1a_realization_transport_v2,
)
import src.core.realization_transport as v1
from src.core.realization_transport.validation import (
    CONTEXT_MORPHISM_VERSION,
    TRANSPORT_RECEIPT_SCHEMA,
    TRANSPORT_SCOPE,
)

from p1a_realization_transport_v2_fixture import fixed_p1a_case


logger = logging.getLogger(__name__)

_V1_ALL = (
    "ClosureActionRow",
    "ContextMorphism",
    "CostTransportRow",
    "CostTransportStatus",
    "EvaluationCommutingRow",
    "RealizationTransportReceipt",
    "RealizationTransportValidationError",
    "RecurrenceCommutingRow",
    "compose_realization_context_morphisms",
    "identity_realization_context_morphism",
    "realization_context_morphism",
    "realization_transport_scope_boundary",
    "verify_realization_transport",
)

_V1_FIELDS = {
    v1.ContextMorphism: (
        "morphism_id",
        "source_context_digest",
        "target_context_digest",
        "state_index_map",
        "version",
        "morphism_digest",
    ),
    v1.RecurrenceCommutingRow: (
        "source_index",
        "target_index",
        "source_input_commitment",
        "target_input_commitment",
    ),
    v1.EvaluationCommutingRow: (
        "observer_id",
        "source_index",
        "target_index",
        "status",
        "payload_digest",
    ),
    v1.ClosureActionRow: (
        "target_partition_digest",
        "source_partition",
        "source_partition_digest",
        "source_closure_index",
    ),
    v1.CostTransportRow: (
        "target_partition_digest",
        "source_partition_digest",
        "source_cost",
        "target_cost",
        "status",
    ),
    v1.RealizationTransportReceipt: (
        "schema",
        "doctrine_fingerprint",
        "source_context_digest",
        "target_context_digest",
        "source_witness_digest",
        "target_witness_digest",
        "morphism",
        "recurrence_rows",
        "evaluation_rows",
        "closure_action",
        "cost_rows",
        "bottom_preserved",
        "joins_preserved",
        "receipt_digest",
        "scope",
    ),
}

_V1_SIGNATURES = {
    v1.realization_context_morphism: (
        "(doctrine: 'ObserverDoctrine', source_context: 'RealizationContext', "
        "target_context: 'RealizationContext', morphism_id: 'str', "
        "state_index_map: 'tuple[int, ...]', "
        "source_witness: 'ObserverRealizationWitness', "
        "target_witness: 'ObserverRealizationWitness') -> "
        "'RealizationTransportReceipt'"
    ),
    v1.verify_realization_transport: (
        "(doctrine: 'ObserverDoctrine', source_context: 'RealizationContext', "
        "target_context: 'RealizationContext', morphism: 'ContextMorphism', "
        "source_witness: 'ObserverRealizationWitness', "
        "target_witness: 'ObserverRealizationWitness', "
        "receipt: 'RealizationTransportReceipt') -> 'RealizationTransportReceipt'"
    ),
    v1.identity_realization_context_morphism: (
        "(doctrine: 'ObserverDoctrine', context: 'RealizationContext', "
        "witness: 'ObserverRealizationWitness', morphism_id: 'str' = 'identity') "
        "-> 'RealizationTransportReceipt'"
    ),
    v1.compose_realization_context_morphisms: (
        "(doctrine: 'ObserverDoctrine', source_context: 'RealizationContext', "
        "middle_context: 'RealizationContext', target_context: 'RealizationContext', "
        "first: 'ContextMorphism | RealizationTransportReceipt', "
        "second: 'ContextMorphism | RealizationTransportReceipt', "
        "source_witness: 'ObserverRealizationWitness', "
        "middle_witness: 'ObserverRealizationWitness', "
        "target_witness: 'ObserverRealizationWitness', morphism_id: 'str') -> "
        "'RealizationTransportReceipt'"
    ),
    v1.realization_transport_scope_boundary: "() -> 'tuple[str, ...]'",
}

_V2_FACADE_NAMES = (
    "P1AEndpointPartitionLawV2",
    "P1AEndpointV2",
    "P1AObservationCommutingRowV2",
    "P1AObservationPayloadV2",
    "P1AObservationTransportV2",
    "P1AOutcomeLawV2",
    "P1ARealizationTransportReceiptV2",
    "P1ARealizationTransportValidationError",
    "compose_p1a_realization_transport_v2",
    "identity_p1a_realization_transport_v2",
    "p1a_realization_transport_v2",
    "p1a_realization_transport_v2_scope_boundary",
    "verify_p1a_realization_transport_v2",
)


def test_v1_facade_all_is_byte_for_byte_order_compatible():
    """The sibling v2 package must not alter the ordered v1 public facade."""
    logger.debug("v1 __all__ compatibility test entry")
    assert type(v1.__all__) is list
    assert tuple(v1.__all__) == _V1_ALL
    logger.debug("v1 __all__ compatibility test exit exports=%d", len(v1.__all__))


def test_v1_dataclass_field_order_is_frozen():
    """Serialized v1 field positions and names remain exactly unchanged."""
    logger.debug("v1 dataclass field compatibility test entry")
    observed = {dto: tuple(field.name for field in fields(dto)) for dto in _V1_FIELDS}
    assert observed == _V1_FIELDS
    logger.debug("v1 dataclass field compatibility test exit DTOs=%d", len(observed))


def test_v1_schema_version_and_scope_constants_are_frozen():
    """The new receipt namespace does not version-bump or relabel v1 evidence."""
    logger.debug("v1 constants compatibility test entry")
    assert CONTEXT_MORPHISM_VERSION == "p1-r16-context-morphism-v1"
    assert TRANSPORT_RECEIPT_SCHEMA == "veyra.p1-r16.realization-transport-receipt.v1"
    assert TRANSPORT_SCOPE == ("finite-relative-replayed-single-arrow-no-category-or-functor-claim")
    logger.debug("v1 constants compatibility test exit")


def test_v1_public_signatures_are_exactly_unchanged():
    """Argument order, defaults, annotations, and return types remain frozen."""
    logger.debug("v1 signature compatibility test entry")
    observed = {function: str(inspect.signature(function)) for function in _V1_SIGNATURES}
    assert observed == _V1_SIGNATURES
    logger.debug("v1 signature compatibility test exit functions=%d", len(observed))


def test_v1_deterministic_morphism_and_receipt_digest_pins_are_unchanged():
    """A fixed pre-v2 v1 construction retains its historical digest namespace."""
    logger.debug("v1 digest pin compatibility test entry")
    case = fixed_p1a_case(name="v1-compat-pin")
    assert case.context_transport.morphism.morphism_digest == (
        "dbb5a7db8ded14233c5dba8f4dcabdfd26a7b2a7c8b0c607b6b13936a7b768ad"
    )
    assert case.context_transport.receipt_digest == ("f3d77eca7e8ad3a33d3327fb30853be97e9e5ca4ee8afcde81691560c0f414ca")
    assert type(case.context_transport) is v1.RealizationTransportReceipt
    assert type(case.context_transport.morphism) is v1.ContextMorphism
    logger.debug("v1 digest pin compatibility test exit")


def test_v2_symbols_are_absent_from_root_and_v1_facades():
    """V2 stays opt-in through its sibling module, not the old import surfaces."""
    logger.debug("v2 facade isolation test entry")
    assert all(name not in v1.__all__ for name in _V2_FACADE_NAMES)
    assert all(not hasattr(v1, name) for name in _V2_FACADE_NAMES)
    assert all(name not in core_facade.__all__ for name in _V2_FACADE_NAMES)
    assert all(not hasattr(core_facade, name) for name in _V2_FACADE_NAMES if name != "p1a_realization_transport_v2")
    incidental = getattr(core_facade, "p1a_realization_transport_v2", None)
    assert incidental is None or not callable(incidental)
    logger.debug("v2 facade isolation test exit")


def test_all_argument_taking_v2_public_functions_close_validation_errors():
    """Malformed public inputs never leak a lower-layer validation exception."""
    logger.debug("v2 public error closure test entry")
    case = fixed_p1a_case(name="v2-public-error-closure")
    common = (
        case.doctrine,
        case.binding,
        case.source,
        case.target,
        case.source_witness,
        case.target_witness,
        case.context_transport,
    )
    spec = {
        "transport_id": "error-closure-transport",
        "p1a_morphism_id": "error-closure-p1a",
        "fine_observer_id": "fine-total",
        "coarse_observer_id": "coarse-crest",
        "projection": (),
    }
    operations = (
        lambda: p1a_realization_transport_v2(object(), *common[1:], **spec),
        lambda: verify_p1a_realization_transport_v2(*common, object(), **spec),
        lambda: identity_p1a_realization_transport_v2(
            case.doctrine,
            case.binding,
            object(),
            case.source_witness,
            observer_id="fine-total",
        ),
        lambda: compose_p1a_realization_transport_v2(
            case.doctrine,
            case.binding,
            case.source,
            case.source,
            case.target,
            case.source_witness,
            case.source_witness,
            case.target_witness,
            object(),
            object(),
            transport_id="error-closure-compose",
            p1a_morphism_id="error-closure-compose-p1a",
            context_morphism_id="error-closure-compose-context",
        ),
    )
    for operation in operations:
        with pytest.raises(P1ARealizationTransportValidationError):
            operation()
    logger.debug("v2 public error closure test exit operations=%d", len(operations))
