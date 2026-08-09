"""Closed DTOs for the isolated P3-N0 arithmetic-history experiment."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TypeAlias

from ...observer.network.types import NetworkResourcePolicy, ObserverNetworkSource
from ...padic.family_introduction.types import N1IntroductionPackage, N1Result
from ..reduction_network.types import (
    FiniteFamilySource, N2Result, PrimePowerReductionPackage,
)


@dataclass(frozen=True)
class N0TheoremSource:
    version: str
    artifact_path: str
    artifact_sha256: str
    toolchain_id: str
    theorem_ids: tuple[str, ...]
    axiom_rows: tuple[tuple[str, tuple[str, ...]], ...]
    source_digest: str


@dataclass(frozen=True)
class N0PhaseReceipt:
    phase_index: int
    artifact_name: str
    captured_sha256: str
    return_code: int
    output_sha256: str
    receipt_digest: str


@dataclass(frozen=True)
class N0FormalAttestation:
    theorem_source_digest: str
    captured_hashes: tuple[str, str, str, str]
    receipts: tuple[N0PhaseReceipt, N0PhaseReceipt, N0PhaseReceipt, N0PhaseReceipt]
    attestation_digest: str


@dataclass(frozen=True)
class N0ReplayEvidence:
    selector: str
    package_digest: str
    network_source_digest: str
    network_judgment_digest: str
    n2_judgment_digest: str
    arrow_judgment_digest: str
    producer_digests: tuple[str, ...]
    outcome_digest: str


@dataclass(frozen=True)
class N0BoundPostbirthLedger:
    row_payloads: tuple[tuple[str, str], tuple[str, str], tuple[str, str]]
    strict_outcome_digest: str
    open_outcome_digest: str
    strict_efficacy_digest: str
    open_efficacy_digest: str
    ledger_digest: str


N0_NONCLAIMS = (
    "necessary-observer-criterion", "generic-e4-bridge", "physical-birth",
    "consciousness", "absolute-observerhood", "carrier-or-object-formation",
    "SCAP-or-A-SFP-object-adoption", "finite-to-infinite-promotion",
)
class PremiseStatus(str, Enum):
    ESTABLISHED = "established"
    REFUTED = "refuted"
    OPEN = "open"
class DoctrineAdmission(str, Enum):
    ADMITTED = "admitted"
    NOT_ADMITTED = "not-admitted"
class RoleStatus(str, Enum):
    ESTABLISHED_RELATIVE_TO_DOCTRINE = "established-relative-to-doctrine"
    OPEN = "open"

class ActualizationStatus(str, Enum):
    ESTABLISHED_RELATIVE_TO_FINITE_ARITHMETIC_HISTORY = (
        "established-relative-to-finite-arithmetic-history"
    )
    OPEN = "open"
class BoundaryStatus(str, Enum):
    OPEN = "open"
    NOT_ESTABLISHED = "not-established"
    NOT_CLAIMED = "not-claimed"
class SuffixSelector(str, Enum):
    STRICT_SUFFIX = "strict-suffix"
    OPEN_SUFFIX = "open-suffix"

class FormalFailureKind(str, Enum):
    TIMEOUT = "timeout"
    OUTPUT_LIMIT = "output-limit"
    COMPILE_ERROR = "compile-error"
    CONTINUITY_DRIFT = "continuity-drift"
class FailedBound(str, Enum):
    DEPTH = "depth"
    INTEGER_BITS = "integer-bits"
    EXPONENT = "exponent"
    MODULUS_BITS = "modulus-bits"
    EVENTS = "events"
    EDGES = "edges"
    ACCESS_EDGES = "access-edges"
    EVALUATIONS = "evaluations"
    FAMILIES = "families"
    FINITE_ROWS = "finite-rows"
    REDUCTIONS = "reductions"
    ASSUMPTIONS = "assumptions"
    LEDGER_BYTES = "ledger-bytes"
    CAPTURED_BYTES = "captured-bytes"
    OUTPUT_BYTES = "output-bytes"
    STATIC_COST = "static-cost"

@dataclass(frozen=True)
class PrimePowerObserverDoctrine:
    version: str
    principle_family_id: str
    principle_id: str
    admission: DoctrineAdmission
    prime_kind: str
    tower_kind: str
    family_domain_kind: str
    premises: tuple[str, ...]
    doctrine_digest: str

@dataclass(frozen=True)
class N0Policy:
    version: str
    max_depth: int
    max_integer_bits: int
    max_exponent: int
    max_modulus_bits: int
    max_events: int
    max_parent_edges: int
    max_access_edges: int
    max_evaluations: int
    max_families: int
    max_finite_rows: int
    max_reductions: int
    max_assumptions: int
    max_ledger_bytes: int
    max_captured_bytes: int
    max_output_bytes: int
    timeout_seconds: int
    policy_digest: str

@dataclass(frozen=True)
class N0FamilyBridgeRow:
    family_id: str
    package_digest: str
    family_term_digest: str
    finite_family: FiniteFamilySource
    row_digest: str

@dataclass(frozen=True)
class N0FamilyFiniteBridgeSource:
    version: str
    depths: tuple[int, int]
    rows: tuple[N0FamilyBridgeRow, ...]
    bridge_digest: str

@dataclass(frozen=True)
class UnavailableFamilyFiniteBridgeEvidence:
    version: str
    reason: str
    evidence_digest: str

@dataclass(frozen=True)
class N2FPackage:
    selector: SuffixSelector
    raw_package: PrimePowerReductionPackage
    network_source: ObserverNetworkSource
    network_policy: NetworkResourcePolicy
    wrapper_digest: str

@dataclass(frozen=True)
class RhoObserverScope:
    family_ids: tuple[str, ...]
    package_digests: tuple[str, str]
    allowed_selectors: tuple[SuffixSelector, SuffixSelector]
    depths: tuple[int, int]
    arrow: tuple[int, int]
    scope_digest: str

@dataclass(frozen=True)
class PreTokenKey:
    lineage_id: str
    rho_structural_id: str
    doctrine_digest: str
    strict_past_scope_digest: str
    key_digest: str

@dataclass(frozen=True)
class N0Ledger:
    version: str
    ordered_rows: tuple[str, ...]
    direct_edges: tuple[tuple[str, str], ...]
    roots: tuple[str, ...]
    imports: tuple[str, ...]
    axioms: tuple[str, ...]
    provenance: str
    ledger_digest: str

@dataclass(frozen=True)
class N0Event:
    event_id: str
    kind: str
    parents: tuple[str, ...]
    token_id: str | None
    lineage_id: str
    scope_digest: str
    payload_digest: str
    event_digest: str

@dataclass(frozen=True)
class N0AccessEdge:
    consumer_id: str
    producer_id: str
    token_id: str
    lineage_id: str
    scope_digest: str
    edge_digest: str

@dataclass(frozen=True)
class N0History:
    selector: SuffixSelector
    events: tuple[N0Event, ...]
    access_edges: tuple[N0AccessEdge, ...]
    strict_past_digest: str
    birth_event_digest: str
    birth_core_digest: str
    historical_token_id: str
    replay_evidence: N0ReplayEvidence
    outcome_digest: str
    efficacy_digest: str
    history_digest: str

@dataclass(frozen=True)
class N0Source:
    prime: int
    depth: int
    lineage_id: str
    doctrine: PrimePowerObserverDoctrine
    policy: N0Policy
    theorem_source: N0TheoremSource
    n1_packages: tuple[N1IntroductionPackage, N1IntroductionPackage, N1IntroductionPackage]
    bridge: N0FamilyFiniteBridgeSource | UnavailableFamilyFiniteBridgeEvidence
    strict_package: N2FPackage
    open_package: N2FPackage
    scope: RhoObserverScope
    prebirth_ledger: N0Ledger
    postbirth_ledger: N0Ledger
    history_ledger: N0Ledger
    source_digest: str

@dataclass(frozen=True)
class N0DiscriminationPressureCandidate:
    package_digest: str
    bridge_digest: str
    token_id: str
    scope_digest: str
    family_ids: tuple[str, str]
    claimed_residues: tuple[int, int]
    claimed_distinct: bool
    candidate_digest: str

@dataclass(frozen=True)
class N0SeparatorPressureCandidate:
    package_digest: str
    bridge_digest: str
    token_id: str
    scope_digest: str
    claimed_fine_residues: tuple[int, int]
    claimed_equal_at_fine: bool
    candidate_digest: str

@dataclass(frozen=True)
class N0Premises:
    genealogy: PremiseStatus
    discrimination: PremiseStatus
    persistence: PremiseStatus
    first_birth: PremiseStatus
    target_independence: PremiseStatus
    token_identity: PremiseStatus
    post_birth_efficacy: PremiseStatus

@dataclass(frozen=True)
class PrimePowerObserverActualizationJudgment:
    premises: N0Premises
    role: RoleStatus
    actualization: ActualizationStatus
    strict_relation: str
    open_relation: str
    run_digest: str
    rho_structural_id: str
    scope_digest: str
    birth_core_digest: str
    historical_token_id: str
    strict_history_digest: str
    open_history_digest: str
    strict_outcome_digest: str
    open_outcome_digest: str
    strict_efficacy_digest: str
    open_efficacy_digest: str
    postbirth_evidence_ledger: N0BoundPostbirthLedger
    formal_attestation: N0FormalAttestation
    n1_results: tuple[N1Result, N1Result, N1Result]
    n2_results: tuple[N2Result, N2Result]
    generic_e4_bridge: BoundaryStatus
    physical_instantiation: BoundaryStatus
    consciousness: BoundaryStatus
    absolute_observerhood: BoundaryStatus
    promotions: int
    nonclaims: tuple[str, ...]
    judgment_digest: str

@dataclass(frozen=True)
class N0ResourceLimit:
    failed_bound: FailedBound
    required: int
    allowed: int
    source_digest: str
    run_digest: str
    nested_result: N1Result | N2Result | None
    refusal_digest: str

@dataclass(frozen=True)
class N0FormalFailure:
    kind: FormalFailureKind
    source_digest: str
    run_digest: str
    nested_result: N1Result | N2Result | None
    diagnostic: str
    attempt_digest: str


@dataclass(frozen=True)
class N0DoctrineOpen:
    source_digest: str
    run_digest: str
    doctrine_digest: str
    genealogy: PremiseStatus
    role: RoleStatus
    actualization: ActualizationStatus
    result_digest: str


@dataclass(frozen=True)
class N0UnavailableSource:
    prime: int
    depth: int
    lineage_id: str
    doctrine: PrimePowerObserverDoctrine
    policy: N0Policy
    theorem_source: N0TheoremSource
    bridge_evidence: UnavailableFamilyFiniteBridgeEvidence
    source_digest: str


@dataclass(frozen=True)
class N0UnavailableBridgeRequest:
    source: N0UnavailableSource
    reason: str
    evidence_digest: str
    request_digest: str


@dataclass(frozen=True)
class N0GenealogyUnavailable:
    source_digest: str
    request_digest: str
    run_digest: str
    evidence_digest: str
    genealogy: PremiseStatus
    role: RoleStatus
    actualization: ActualizationStatus
    result_digest: str


N0Result: TypeAlias = (
    PrimePowerObserverActualizationJudgment | N0DoctrineOpen | N0GenealogyUnavailable
    | N0ResourceLimit | N0FormalFailure
)
