"""Closed DTOs for P3-C1 ranked generated confluence."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TypeAlias

P3C1_NONCLAIMS = (
    "transport-path-independence",
    "unique-normal-form",
    "church-rosser",
    "unrestricted-confluence",
    "arbitrary-system-termination",
    "observer-independent-identity",
    "physical-persistence",
    "absolute-identity",
    "completed-infinity",
    "foundation-independent-number-system",
    "promotion",
    "incomplete-generated-local-confluence",
    "universal-observer-translation",
    "generic-productive-to-all-depth",
    "no-c1-c3-transport-claim",
)


NO_C1_C3_TRANSPORT_CLAIM = "no-c1-c3-transport-claim"


class CellMode(str, Enum):
    PURE_RELATION_PATH = "pure-same-system-relation-path"


class GeneratedConfluenceStatus(str, Enum):
    GENERATED_FINITE_CONFLUENT_RELATIVE_TO_SYSTEM = "generated-finite-confluent-relative-to-system"
    REFUTED = "refuted"
    OPEN = "open"


class GeneratedFailureKind(str, Enum):
    RESOURCE_LIMIT = "resource-limit"


class FailedBound(str, Enum):
    STATES = "states"
    EDGES = "edges"
    CANONICAL_BYTES = "canonical-bytes"
    LOCAL_CELLS = "local-cells"


@dataclass(frozen=True)
class ContinuationState:
    state_id: str
    kind: str
    payload: bytes
    state_commitment: str


@dataclass(frozen=True)
class ContinuationEdge:
    edge_id: str
    source_id: str
    target_id: str
    rule_kind: str
    rule_payload: bytes
    edge_commitment: str


@dataclass(frozen=True)
class StateRank:
    state_id: str
    rank: int


@dataclass(frozen=True)
class RankedContinuationSystem:
    version: str
    doctrine_fingerprint: str
    source_id: str
    source_version: str
    states: tuple[ContinuationState, ...]
    edges: tuple[ContinuationEdge, ...]
    roots: tuple[str, ...]
    ranks: tuple[StateRank, ...]
    system_digest: str
    scope: str = "finite-ranked-generated-continuation-system"


@dataclass(frozen=True)
class GeneratedLocalPeak:
    peak_id: str
    source_state_id: str
    left_edge_id: str
    right_edge_id: str
    peak_digest: str


@dataclass(frozen=True)
class LocalJoinCell:
    peak_id: str
    left_edge_ids: tuple[str, ...]
    right_edge_ids: tuple[str, ...]
    claimed_join_state_id: str
    mode: CellMode
    system_digest: str
    cell_digest: str


@dataclass(frozen=True)
class BlockedLocalJoinCell:
    peak_id: str
    obstruction: str
    system_digest: str
    cell_digest: str


LocalCell: TypeAlias = LocalJoinCell | BlockedLocalJoinCell


@dataclass(frozen=True)
class LocalPeakRow:
    peak: GeneratedLocalPeak
    cell_digest: str | None
    left_endpoint_id: str | None
    right_endpoint_id: str | None
    status: GeneratedConfluenceStatus
    row_digest: str


@dataclass(frozen=True)
class GeneratedConfluenceTheoremSource:
    version: str
    artifact_path: str
    artifact_sha256: str
    theorem_ids: tuple[str, ...]
    toolchain_id: str
    elan_sha256: str
    lean_sha256: str
    lean_version: str
    tcb_digest: str
    source_digest: str


@dataclass(frozen=True)
class GeneratedFormalPhaseReceipt:
    phase: str
    return_code: int
    output_bytes: int
    output_digest: str


@dataclass(frozen=True)
class GeneratedFiniteConfluence:
    system_digest: str
    reachable_state_ids: tuple[str, ...]
    reachable_edge_ids: tuple[str, ...]
    peaks: tuple[GeneratedLocalPeak, ...]
    rows: tuple[LocalPeakRow, ...]
    theorem_source: GeneratedConfluenceTheoremSource
    theorem_receipt_digest: str
    theorem_phase_receipts: tuple[GeneratedFormalPhaseReceipt, ...]
    status: GeneratedConfluenceStatus
    first_counterexample_peak_id: str | None
    nonclaims: tuple[str, ...]
    result_digest: str


@dataclass(frozen=True)
class GeneratedConfluenceResourceLimit:
    status: GeneratedFailureKind
    failed_bound: FailedBound
    required_value: int
    allowed_value: int
    source_hint_digest: str
    nonclaims: tuple[str, ...]
    refusal_digest: str


GeneratedConfluenceResult: TypeAlias = GeneratedFiniteConfluence | GeneratedConfluenceResourceLimit
