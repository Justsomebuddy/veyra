"""Closed DTOs for ledger-relative P3-N3 realization and N4 identity."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TypeAlias

from ..completion.types import PadicCompletionPackage
from ..family_introduction.types import N1IntroductionPackage

N34_NONCLAIMS = (
    "generic-or-categorical-completion", "completion-from-concrete-family",
    "family-from-completion", "bounded-to-all-depth-promotion",
    "integer-or-observer-free-identity", "topology-metric-q_p-or-field",
    "mathlib-padic-equivalence", "physical-or-foundation-independent-infinity",
)


class N34Status(str, Enum):
    ESTABLISHED = "established"
    OPEN = "open"
    REFUTED = "refuted"
    RESOURCE_LIMIT = "resource-limit"


class N3Kind(str, Enum):
    LOCAL_REALIZATION_ESTABLISHED_RELATIVE_TO_EXACT_POMEGA2 = (
        "local-realization-established-relative-to-exact-pomega2")


class N4Kind(str, Enum):
    SCOPED_CARRIER_EQUALITY_ESTABLISHED_RELATIVE_TO_LEDGER = (
        "scoped-carrier-equality-established-relative-to-ledger")


class EqualityStatus(str, Enum):
    ESTABLISHED_RELATIVE_TO_LEDGER = "established-relative-to-ledger"
    NOT_ESTABLISHED = "not-established"


class FailedBound(str, Enum):
    CAPTURED_BYTES = "captured-bytes"
    STATIC_COST = "static-cost"
    LEDGER_ROWS = "ledger-rows"
    LEDGER_EDGES = "ledger-edges"
    OUTPUT_BYTES = "output-bytes"


class FormalFailureKind(str, Enum):
    TIMEOUT = "timeout"
    OUTPUT_LIMIT = "output-limit"
    COMPILE_ERROR = "compile-error"
    CONTINUITY_DRIFT = "continuity-drift"
    DEPENDENCY_REPLAY_FAILURE = "dependency-replay-failure"


@dataclass(frozen=True)
class N34Policy:
    version: str
    max_captured_bytes: int
    max_static_cost: int
    max_ledger_rows: int
    max_ledger_edges: int
    timeout_seconds: int
    max_output_bytes: int
    policy_digest: str


@dataclass(frozen=True)
class N34TheoremSource:
    version: str
    artifact_path: str
    artifact_sha256: str
    theorem_ids: tuple[str, ...]
    imports: tuple[tuple[str, str], ...]
    toolchain_id: str
    tcb_digest: str
    source_digest: str


@dataclass(frozen=True)
class BridgeDependencyRow:
    row_id: str
    direct_dependencies: tuple[str, ...]
    source_digest: str
    axiom_closure: tuple[str, ...]


@dataclass(frozen=True)
class BridgeDependencyUnion:
    version: str
    ordered_rows: tuple[BridgeDependencyRow, ...]
    theorem_axiom_closure: tuple[str, ...]
    ledger_digest: str


@dataclass(frozen=True)
class AllDepthCoordinateEqualitySource:
    version: str
    artifact_path: str
    artifact_sha256: str
    theorem_ids: tuple[str, ...]
    imports: tuple[tuple[str, str], ...]
    toolchain_id: str
    tcb_digest: str
    pomega2_package_digest: str
    left_family_source_digest: str
    right_family_source_digest: str
    left_realized_term_digest: str
    right_realized_term_digest: str
    rho_definition_id: str
    ordered_rows: tuple[BridgeDependencyRow, ...]
    theorem_axiom_closure: tuple[str, ...]
    ledger_digest: str
    source_digest: str


@dataclass(frozen=True)
class N3Request:
    n1: N1IntroductionPackage
    pomega2: PadicCompletionPackage
    theorem: N34TheoremSource
    policy: N34Policy
    request_digest: str


@dataclass(frozen=True)
class N4Request:
    left_n1: N1IntroductionPackage
    right_n1: N1IntroductionPackage
    pomega2: PadicCompletionPackage
    theorem: N34TheoremSource
    all_depth: AllDepthCoordinateEqualitySource
    policy: N34Policy
    request_digest: str


@dataclass(frozen=True)
class N3RealizationJudgment:
    status: N34Status
    kind: N3Kind
    n1_package_digest: str
    pomega2_package_digest: str
    theorem_source_digest: str
    bridge_ledger_digest: str
    family_term_digest: str
    introduction_evidence_digest: str
    realized_term_digest: str
    coordinate_evidence_digest: str
    theorem_ids: tuple[str, ...]
    theorem_axiom_closure: tuple[str, ...]
    promotions: int
    nonclaims: tuple[str, ...]
    judgment_digest: str


@dataclass(frozen=True)
class N4EqualityJudgment:
    status: N34Status
    kind: N4Kind
    equality_status: EqualityStatus
    left_realized_term_digest: str
    right_realized_term_digest: str
    all_depth_source_digest: str
    theorem_source_digest: str
    bridge_ledger_digest: str
    equality_evidence_digest: str
    promotions: int
    nonclaims: tuple[str, ...]
    judgment_digest: str


@dataclass(frozen=True)
class N34Open:
    status: N34Status
    equality_status: EqualityStatus
    reason: str
    request_digest: str
    open_digest: str


@dataclass(frozen=True)
class N34Refuted:
    status: N34Status
    reason: str
    request_digest: str
    refutation_digest: str


@dataclass(frozen=True)
class N34ResourceLimit:
    status: N34Status
    failed_bound: FailedBound
    required: int
    allowed: int
    request_digest: str
    refusal_digest: str


@dataclass(frozen=True)
class N34FormalFailure:
    kind: FormalFailureKind
    request_digest: str
    attempt_digest: str
    diagnostic: str


N3Result: TypeAlias = N3RealizationJudgment | N34Refuted | N34ResourceLimit | N34FormalFailure
N4Result: TypeAlias = (
    N4EqualityJudgment | N34Open | N34Refuted | N34ResourceLimit | N34FormalFailure
)


@dataclass(frozen=True)
class BoundedCoordinateRow:
    depth: int
    modulus: int
    left_residue: int
    right_residue: int
    row_digest: str


@dataclass(frozen=True)
class BoundedCoordinateEqualitySource:
    version: str
    depth: int
    pomega2_package_digest: str
    left_family_source_digest: str
    right_family_source_digest: str
    rows: tuple[BoundedCoordinateRow, ...]
    source_digest: str


@dataclass(frozen=True)
class BoundedEqualityRequest:
    left_n1: N1IntroductionPackage
    right_n1: N1IntroductionPackage
    pomega2: PadicCompletionPackage
    source: BoundedCoordinateEqualitySource
    policy: N34Policy
    request_digest: str


BoundedEqualityResult: TypeAlias = N34Open | N34Refuted | N34ResourceLimit
