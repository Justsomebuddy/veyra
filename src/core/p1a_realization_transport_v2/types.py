"""Closed DTOs for same-doctrine all-status P1-A transport v2."""

from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from ..observer_morphism_types import ResponseTranslation
from ..observer_realization_types import (
    ObservationStatus,
    RealizationClosurePolicy,
    RealizationCostPolicy,
    ResponseTotalization,
)
from ..realization_transport.types import RealizationTransportReceipt


class P1AEndpointV2(str, Enum):
    SOURCE = "source"
    TARGET = "target"


class P1AOutcomeLawV2(str, Enum):
    READY_COMMUTES_EXACT = "ready-commutes-exact"
    BLOCKED_COMMUTES_EXACT = "blocked-commutes-exact"


@dataclass(frozen=True, slots=True)
class P1AObservationPayloadV2:
    status: ObservationStatus
    canonical_payload: bytes
    payload_digest: str


@dataclass(frozen=True, slots=True)
class P1AObservationCommutingRowV2:
    source_index: int
    target_index: int
    source_input_commitment: str
    target_input_commitment: str
    source_fine: P1AObservationPayloadV2
    source_transported: P1AObservationPayloadV2
    source_coarse: P1AObservationPayloadV2
    target_fine: P1AObservationPayloadV2
    target_transported: P1AObservationPayloadV2
    target_coarse: P1AObservationPayloadV2
    law: P1AOutcomeLawV2
    row_digest: str


@dataclass(frozen=True, slots=True)
class P1AEndpointPartitionLawV2:
    endpoint: P1AEndpointV2
    fine_partition: tuple[int, ...]
    transported_partition: tuple[int, ...]
    coarse_partition: tuple[int, ...]
    fine_to_coarse_class_map: tuple[int, ...]
    partition_digest: str


@dataclass(frozen=True, slots=True)
class P1AObservationTransportV2:
    transport_id: str
    doctrine_fingerprint: str
    source_binding_digest: str
    strong_judgment_root: str
    translation: ResponseTranslation
    source_context_digest: str
    target_context_digest: str
    source_witness_digest: str
    target_witness_digest: str
    context_morphism_digest: str
    v1_receipt_digest: str
    response_policy: ResponseTotalization
    cost_policy: RealizationCostPolicy
    closure_policy: RealizationClosurePolicy
    version: str
    scope: str
    transport_digest: str


@dataclass(frozen=True, slots=True)
class P1ARealizationTransportReceiptV2:
    schema: str
    transport: P1AObservationTransportV2
    context_transport: RealizationTransportReceipt
    rows: tuple[P1AObservationCommutingRowV2, ...]
    source_partition_law: P1AEndpointPartitionLawV2
    target_partition_law: P1AEndpointPartitionLawV2
    receipt_digest: str
    scope: str
