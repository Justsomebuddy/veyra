"""Closed DTOs for the isolated P3-A1b productive-process bridge."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TypeAlias

from ...padic.completion.types import PadicTowerDoctrine, PrimeSource
from ...padic.family_introduction.types import IntegerSource, N1TheoremSource

A1B_NONCLAIMS = (
    "completed-carrier", "universal-completion", "generic-uaip",
    "selector-from-prop", "finite-prefix-to-infinity", "p2s-promotion",
    "physical-or-foundation-independent-infinity",
)


class BridgeEvidenceKind(str, Enum):
    PRODUCTIVE_FAMILY_BRIDGE = "productive-family-bridge"


class BridgeStatus(str, Enum):
    ESTABLISHED_RELATIVE_TO_LEDGER = "established-relative-to-ledger"


class BridgeProvenance(str, Enum):
    FORMALLY_DERIVED = "formally-derived"


class FamilyKind(str, Enum):
    ALL_DEPTH_FAMILY = "all-depth-family"


class UniformizationRoute(str, Enum):
    A1_DEFINITIONAL = "a1-definitional"


class BoundaryStatus(str, Enum):
    NOT_ESTABLISHED = "not-established"
    OPEN = "open"
    NOT_CLAIMED = "not-claimed"


class ResultStatus(str, Enum):
    RESOURCE_LIMIT = "resource-limit"
    REFUTED = "refuted"
    OPEN = "open"


class FailedBound(str, Enum):
    CAPTURED_BYTES = "captured-bytes"
    STATIC_COST = "static-cost"
    REQUESTED_DEPTH = "requested-depth"
    OUTPUT_BYTES = "output-bytes"


class FormalFailureKind(str, Enum):
    TIMEOUT = "timeout"
    OUTPUT_LIMIT = "output-limit"
    COMPILE_ERROR = "compile-error"
    CONTINUITY_DRIFT = "continuity-drift"


@dataclass(frozen=True)
class ResidueProgramSource:
    version: str
    constructor: str
    grammar_id: str
    prime_digest: str
    integer_digest: str
    program_digest: str


@dataclass(frozen=True)
class OffsetResidueProgramSource:
    version: str
    constructor: str
    grammar_id: str
    prime_digest: str
    integer_digest: str
    offset: int
    artifact_path_id: str
    artifact_sha256: str
    theorem_ids: tuple[str, ...]
    toolchain_id: str
    program_digest: str
    productivity_evidence_digest: str
    coherence_evidence_digest: str


@dataclass(frozen=True)
class BridgeTheoremSource:
    version: str
    artifact_path_id: str
    artifact_sha256: str
    n1_artifact_path_id: str
    n1_artifact_sha256: str
    pomega2_artifact_path_id: str
    pomega2_artifact_sha256: str
    theorem_ids: tuple[str, ...]
    toolchain_id: str
    tcb_digest: str
    source_digest: str


@dataclass(frozen=True)
class BridgeLedger:
    version: str
    ordered_rows: tuple[str, ...]
    direct_edges: tuple[tuple[str, str], ...]
    theorem_axiom_rows: tuple[tuple[str, tuple[str, ...]], ...]
    ledger_digest: str


@dataclass(frozen=True)
class BridgePolicy:
    version: str
    max_captured_bytes: int
    max_static_cost: int
    max_depth: int
    max_output_bytes: int
    compile_timeout_seconds: int
    policy_digest: str


@dataclass(frozen=True)
class ProductiveBridgePackage:
    prime: PrimeSource
    integer: IntegerSource
    doctrine: PadicTowerDoctrine
    program: ResidueProgramSource
    n1_theorem: N1TheoremSource
    theorem: BridgeTheoremSource
    ledger: BridgeLedger
    policy: BridgePolicy
    package_digest: str


@dataclass(frozen=True)
class ProductiveBridgeJudgment:
    family_kind: FamilyKind
    bridge_evidence_kind: BridgeEvidenceKind
    bridge_status: BridgeStatus
    bridge_provenance: BridgeProvenance
    uniformization_route: UniformizationRoute
    productivity_status: BridgeStatus
    determinism_status: BridgeStatus
    process_coherence_status: BridgeStatus
    family_introduction_status: BridgeStatus
    completed_carrier: BoundaryStatus
    universal_completion: BoundaryStatus
    physical_or_foundation_independent_infinity: BoundaryStatus
    promotions: int
    program_digest: str
    family_term_digest: str
    productivity_evidence_digest: str
    family_introduction_digest: str
    bridge_evidence_digest: str
    judgment_digest: str
    theorem_ids: tuple[str, ...]
    theorem_axiom_rows: tuple[tuple[str, tuple[str, ...]], ...]
    nonclaims: tuple[str, ...]


@dataclass(frozen=True)
class ProjectionArtifact:
    status: str
    depth: int
    modulus: int
    residue: int
    qa_scope: str
    projection_run_digest: str


@dataclass(frozen=True)
class BridgeResourceLimit:
    status: ResultStatus
    failed_bound: FailedBound
    required_value: int
    allowed_value: int
    package_digest: str
    policy_digest: str
    run_digest: str
    refusal_digest: str


@dataclass(frozen=True)
class BridgeRefutation:
    status: ResultStatus
    mismatch_depth: int
    expected_residue: int
    observed_residue: int
    pressure_program_digest: str
    productivity_evidence_digest: str
    coherence_evidence_digest: str
    refutation_digest: str


@dataclass(frozen=True)
class BridgeOpen:
    status: ResultStatus
    reason: str
    prime_digest: str
    integer_digest: str
    program_digest: str
    open_digest: str


@dataclass(frozen=True)
class BridgeFormalFailure:
    kind: FormalFailureKind
    package_digest: str
    run_digest: str
    diagnostic: str
    attempt_digest: str


BridgeResult: TypeAlias = ProductiveBridgeJudgment | BridgeResourceLimit | BridgeFormalFailure
