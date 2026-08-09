"""Closed DTOs for isolated P3-C2 generated transport coherence."""

from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import TypeAlias
from ..confluence.generated.types import RankedContinuationSystem

P3C2_NONCLAIMS = (
    "higher-cell-structure-coherence-not-implemented",
    "no-admitted-source-bound-3cell-universe",
    "unique-normal-form",
    "history-equality",
    "church-rosser",
    "unrestricted-higher-confluence",
    "p3t-adapter-gated-unreleased",
    "partial-transport-coherence",
    "symbolic-natop-from-finite-tlgc",
    "universal-observer-translation",
    "physical-persistence",
    "absolute-identity",
    "generic-objecthood",
    "completed-infinity",
    "foundation-independent-mathematics",
    "promotion",
)


class TransportCoherenceStatus(str, Enum):
    GENERATED_TRANSPORT_COHERENT_RELATIVE_TO_SYSTEM = "generated-transport-coherent-relative-to-system"
    REFUTED = "refuted"
    OPEN = "open"


class HigherCellStructureStatus(str, Enum):
    NOT_IMPLEMENTED = "not-implemented"


class TransportFailureKind(str, Enum):
    RESOURCE_LIMIT = "resource-limit"
    FORMAL_FAILURE = "formal-failure"


class TransportFailedBound(str, Enum):
    VALUES = "values"
    MAP_ENTRIES = "map-entries"
    LOCAL_FILLERS = "local-fillers"
    GENERATED_PATHS = "generated-paths"
    SEMANTIC_WORK = "semantic-work"
    CANONICAL_BYTES = "canonical-bytes"


class FormalFailureKind(str, Enum):
    TIMEOUT = "timeout"
    OUTPUT_LIMIT = "output-limit"
    COMPILE_ERROR = "compile-error"
    CONTINUITY_DRIFT = "continuity-drift"


@dataclass(frozen=True)
class TransportValue:
    state_id: str
    value_id: str
    payload: bytes
    value_commitment: str


@dataclass(frozen=True)
class SetoidClassRow:
    value_id: str
    class_id: str


@dataclass(frozen=True)
class StateSetoidCarrier:
    state_id: str
    state_commitment: str
    values: tuple[TransportValue, ...]
    classes: tuple[SetoidClassRow, ...]
    carrier_digest: str


@dataclass(frozen=True)
class TransportMapEntry:
    source_value_id: str
    target_value_id: str


@dataclass(frozen=True)
class EdgeTransportMap:
    edge_id: str
    edge_commitment: str
    source_carrier_digest: str
    target_carrier_digest: str
    entries: tuple[TransportMapEntry, ...]
    map_digest: str


@dataclass(frozen=True)
class TotalTransportDoctrine:
    version: str
    doctrine_id: str
    system_digest: str
    carriers: tuple[StateSetoidCarrier, ...]
    edge_maps: tuple[EdgeTransportMap, ...]
    identity_law_id: str
    composition_law_id: str
    setoid_respect_law_id: str
    p3t_adapter_status: str
    doctrine_digest: str


@dataclass(frozen=True)
class LocalCommutingFiller:
    peak_id: str
    left_path: tuple[str, ...]
    right_path: tuple[str, ...]
    target_state_id: str
    system_digest: str
    doctrine_digest: str
    filler_digest: str


@dataclass(frozen=True)
class GeneratedTransportFiller:
    root_state_id: str
    left_boundary: tuple[str, ...]
    right_boundary: tuple[str, ...]
    target_state_id: str
    left_postpath: tuple[str, ...]
    right_postpath: tuple[str, ...]
    filler_digest: str


@dataclass(frozen=True)
class CofinalBoundaryReconciliation:
    boundary_digest: str
    first_target_state_id: str
    second_target_state_id: str
    postjoin_state_id: str
    first_postpath: tuple[str, ...]
    second_postpath: tuple[str, ...]
    first_filler_digest: str
    second_filler_digest: str
    system_digest: str
    doctrine_digest: str
    reconciliation_digest: str


@dataclass(frozen=True)
class TransportTheoremSource:
    version: str
    artifact_path: str
    artifact_sha256: str
    theorem_ids: tuple[str, ...]
    toolchain_id: str
    tcb_digest: str
    source_digest: str


@dataclass(frozen=True)
class TransportAssumptionLedger:
    version: str
    ordered_rows: tuple[str, ...]
    direct_edges: tuple[tuple[str, str], ...]
    theorem_axiom_closure: tuple[str, ...]
    ledger_digest: str


@dataclass(frozen=True)
class TransportPolicy:
    max_values: int
    max_map_entries: int
    max_local_fillers: int
    max_generated_paths: int
    max_semantic_work: int
    max_canonical_bytes: int
    compile_timeout_seconds: int
    max_output_bytes: int
    policy_digest: str


@dataclass(frozen=True)
class GeneratedTransportCoherence:
    system_digest: str
    doctrine_digest: str
    theorem_source_digest: str
    assumption_ledger_digest: str
    formal_receipt_digest: str
    formal_phase_count: int
    local_filler_digests: tuple[str, ...]
    global_fillers: tuple[GeneratedTransportFiller, ...]
    local_square_count: int
    global_boundary_count: int
    semantic_work: int
    finite_tlgc_scope: str
    symbolic_natop_scope: str
    status: TransportCoherenceStatus
    higher_cell_structure: HigherCellStructureStatus
    nonclaims: tuple[str, ...]
    result_digest: str


@dataclass(frozen=True)
class TransportResourceLimit:
    status: TransportFailureKind
    failed_bound: TransportFailedBound
    required_value: int
    allowed_value: int
    source_hint_digest: str
    nonclaims: tuple[str, ...]
    refusal_digest: str


@dataclass(frozen=True)
class TransportFormalFailure:
    status: TransportFailureKind
    kind: FormalFailureKind
    diagnostic: str
    attempt_digest: str
    nonclaims: tuple[str, ...]


TransportResult: TypeAlias = GeneratedTransportCoherence | TransportResourceLimit | TransportFormalFailure


@dataclass(frozen=True)
class TransportPackage:
    system: RankedContinuationSystem
    doctrine: TotalTransportDoctrine
    local_fillers: tuple[LocalCommutingFiller, ...]
    theorem_source: TransportTheoremSource
    assumption_ledger: TransportAssumptionLedger
    policy: TransportPolicy
    package_digest: str
