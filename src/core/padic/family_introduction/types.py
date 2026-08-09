"""Closed DTOs for P3-N1 integer residue-family introduction."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TypeAlias

from ..completion.types import PadicTowerDoctrine, PrimeSource

N1_NONCLAIMS = (
    "universal-pomega2-completion", "local-carrier-realization",
    "categorical-inverse-limit", "finite-prefix-promotion",
    "d1-productivity-cast", "d3-family-cast", "oracle-or-callback-family",
    "physical-or-foundation-independent-infinity",
)


class N1EvidenceStatus(str, Enum):
    ESTABLISHED = "established"


class N1EvidenceProvenance(str, Enum):
    FORMALLY_DERIVED = "formally-derived"


class N1JudgmentKind(str, Enum):
    ALL_DEPTH_FAMILY = "all-depth-family"


class N1ResultStatus(str, Enum):
    RESOURCE_LIMIT = "resource-limit"


class N1FailedBound(str, Enum):
    CAPTURED_BYTES = "captured-bytes"
    STATIC_COST = "static-cost"


class N1ExecutionFailureKind(str, Enum):
    TIMEOUT = "timeout"
    OUTPUT_LIMIT = "output-limit"
    COMPILE_ERROR = "compile-error"
    CONTINUITY_DRIFT = "continuity-drift"


@dataclass(frozen=True)
class IntegerSource:
    version: str
    z: int
    representation_id: str
    source_digest: str


@dataclass(frozen=True)
class N1TheoremSource:
    version: str
    artifact_path_id: str
    artifact_sha256: str
    pomega2_artifact_path_id: str
    pomega2_artifact_sha256: str
    theorem_ids: tuple[str, ...]
    family_definition_id: str
    coordinate_definition_id: str
    toolchain_id: str
    tcb_digest: str
    source_digest: str


@dataclass(frozen=True)
class N1AssumptionLedger:
    version: str
    ordered_rows: tuple[str, ...]
    direct_edges: tuple[tuple[str, str], ...]
    theorem_axiom_closure: tuple[str, ...]
    ledger_digest: str


@dataclass(frozen=True)
class N1Policy:
    version: str
    max_captured_bytes: int
    max_static_cost: int
    compile_timeout_seconds: int
    max_output_bytes: int
    policy_digest: str


@dataclass(frozen=True)
class N1IntroductionPackage:
    prime: PrimeSource
    integer: IntegerSource
    doctrine: PadicTowerDoctrine
    theorem_source: N1TheoremSource
    ledger: N1AssumptionLedger
    policy: N1Policy
    package_digest: str


@dataclass(frozen=True)
class N1FamilyJudgment:
    kind: N1JudgmentKind
    status: N1EvidenceStatus
    provenance: N1EvidenceProvenance
    prime_digest: str
    integer_digest: str
    doctrine_digest: str
    theorem_source_digest: str
    ledger_digest: str
    package_digest: str
    run_digest: str
    family_term_digest: str
    introduction_evidence_digest: str
    theorem_ids: tuple[str, ...]
    theorem_axiom_closure: tuple[str, ...]
    coordinate_totality: N1EvidenceStatus
    all_reductions_compatible: N1EvidenceStatus
    nonclaims: tuple[str, ...]
    judgment_digest: str


@dataclass(frozen=True)
class N1ResourceLimit:
    status: N1ResultStatus
    package_digest: str
    policy_digest: str
    run_digest: str
    failed_bound: N1FailedBound
    required_value: int
    allowed_value: int
    nonclaims: tuple[str, ...]
    refusal_digest: str


@dataclass(frozen=True)
class N1FormalFailure:
    kind: N1ExecutionFailureKind
    package_digest: str
    policy_digest: str
    run_digest: str
    attempt_digest: str
    diagnostic: str
    nonclaims: tuple[str, ...]


N1Result: TypeAlias = N1FamilyJudgment | N1ResourceLimit | N1FormalFailure
