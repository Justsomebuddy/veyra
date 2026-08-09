"""Closed DTOs for the isolated two-lane P3-N2 reduction network."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TypeAlias

from ...observer.network.types import ObserverNetworkSource
from ...padic.completion.types import PadicTowerDoctrine, PrimeSource
from ...padic.family_introduction.types import N1TheoremSource

N2_NONCLAIMS = (
    "completed-carrier", "pomega2-final-judgment", "coarse-to-fine-inverse",
    "caller-supplied-map", "generic-p3t", "generic-p3c2", "carry-normalization",
    "observer-free-identity", "ontic-history-identity", "p2s-promotion",
    "physical-metaphysical-or-foundation-independent-objectivity",
)


class RelativeStatus(str, Enum):
    ESTABLISHED_RELATIVE_TO_LEDGER = "established-relative-to-ledger"


class FiniteRelation(str, Enum):
    TRANSLATION_ISOMORPHIC_ON_EXACT_FINITE_SCOPE = "translation-isomorphic-on-exact-finite-scope"
    STRICT_REFINEMENT_ON_EXACT_FINITE_SCOPE = "strict-refinement-on-exact-finite-scope"
    OPEN = "open"


class SymbolicKind(str, Enum):
    THIN_REDUCTION_PATH_COHERENT_RELATIVE_TO_TOWER = "thin-reduction-path-coherent-relative-to-tower"


class BoundaryStatus(str, Enum):
    NOT_CLAIMED = "not-claimed"
    NOT_ESTABLISHED = "not-established"


class ResultStatus(str, Enum):
    RESOURCE_LIMIT = "resource-limit"
    OPEN = "open"
    REFUTED = "refuted"


class N2PressureKind(str, Enum):
    WRONG_SQUARE = "wrong-square"
    WRONG_PATH = "wrong-path"


class FailedBound(str, Enum):
    CAPTURED_BYTES = "captured-bytes"
    STATIC_COST = "static-cost"
    DEPTHS = "depths"
    ARROWS = "arrows"
    TABLE_ROWS = "table-rows"
    OUTPUT_BYTES = "output-bytes"


class FormalFailureKind(str, Enum):
    TIMEOUT = "timeout"
    OUTPUT_LIMIT = "output-limit"
    COMPILE_ERROR = "compile-error"
    CONTINUITY_DRIFT = "continuity-drift"


@dataclass(frozen=True)
class DepthNode:
    depth: int
    modulus: int
    node_digest: str


@dataclass(frozen=True)
class FamilyCoordinate:
    depth: int
    residue: int
    coordinate_digest: str


@dataclass(frozen=True)
class FiniteFamilySource:
    family_id: str
    integer: int
    coordinates: tuple[FamilyCoordinate, ...]
    family_digest: str


@dataclass(frozen=True)
class ReductionRow:
    source_residue: int
    target_residue: int
    row_digest: str


@dataclass(frozen=True)
class ReductionArrowSource:
    fine_depth: int
    coarse_depth: int
    rows: tuple[ReductionRow, ...]
    arrow_digest: str


@dataclass(frozen=True)
class FiniteReductionSource:
    version: str
    prime_digest: str
    doctrine_digest: str
    p3t_version: str
    p3t_raw_source: ObserverNetworkSource
    depths: tuple[DepthNode, ...]
    families: tuple[FiniteFamilySource, ...]
    arrows: tuple[ReductionArrowSource, ...]
    source_digest: str


@dataclass(frozen=True)
class N2TheoremSource:
    version: str
    pomega2_path: str
    pomega2_sha256: str
    n1_path: str
    n1_sha256: str
    artifact_path: str
    artifact_sha256: str
    theorem_ids: tuple[str, ...]
    toolchain_id: str
    tcb_digest: str
    source_digest: str


@dataclass(frozen=True)
class N2Ledger:
    version: str
    ordered_rows: tuple[str, ...]
    direct_edges: tuple[tuple[str, str], ...]
    axiom_rows: tuple[tuple[str, tuple[str, ...]], ...]
    ledger_digest: str


@dataclass(frozen=True)
class N2Policy:
    version: str
    max_captured_bytes: int
    max_static_cost: int
    max_depths: int
    max_arrows: int
    max_table_rows: int
    max_output_bytes: int
    timeout_seconds: int
    policy_digest: str


@dataclass(frozen=True)
class PrimePowerReductionPackage:
    prime: PrimeSource
    doctrine: PadicTowerDoctrine
    finite: FiniteReductionSource
    n1_theorem: N1TheoremSource
    theorem: N2TheoremSource
    ledger: N2Ledger
    policy: N2Policy
    package_digest: str


@dataclass(frozen=True)
class FiniteArrowJudgment:
    fine_depth: int
    coarse_depth: int
    total: bool
    square_commutes: bool
    preservation: bool
    relation: FiniteRelation
    separator_family_ids: tuple[str, str] | None
    map_digest: str
    judgment_digest: str


@dataclass(frozen=True)
class PrimePowerReductionJudgment:
    finite_status: RelativeStatus
    symbolic_status: RelativeStatus
    symbolic_kind: SymbolicKind
    finite_arrows: tuple[FiniteArrowJudgment, ...]
    p3t_source_digest: str
    p3t_replay_digest: str
    theorem_source_digest: str
    ledger_digest: str
    identity: RelativeStatus
    composition: RelativeStatus
    rho_square: RelativeStatus
    proof_witness_independence: RelativeStatus
    completed_carrier: BoundaryStatus
    pomega2_final_judgment_consumed: bool
    p3c2_status_consumed: bool
    promotions: int
    theorem_ids: tuple[str, ...]
    axiom_rows: tuple[tuple[str, tuple[str, ...]], ...]
    nonclaims: tuple[str, ...]
    judgment_digest: str


@dataclass(frozen=True)
class N2ResourceLimit:
    status: ResultStatus
    failed_bound: FailedBound
    required: int
    allowed: int
    package_digest: str
    refusal_digest: str


@dataclass(frozen=True)
class N2FormalFailure:
    kind: FormalFailureKind
    package_digest: str
    diagnostic: str
    attempt_digest: str


@dataclass(frozen=True)
class N2PressureCandidate:
    version: str
    kind: N2PressureKind
    finite_source_digest: str
    family_id: str | None
    path_depths: tuple[int, ...]
    source_residue: int
    claimed_target_residue: int
    candidate_digest: str


@dataclass(frozen=True)
class N2Refutation:
    status: ResultStatus
    kind: N2PressureKind
    family_id: str | None
    path_depths: tuple[int, ...]
    source_residue: int
    expected_target_residue: int
    claimed_target_residue: int
    finite_source_digest: str
    package_digest: str
    candidate_digest: str
    witness_digest: str
    refutation_digest: str


@dataclass(frozen=True)
class N2Open:
    status: ResultStatus
    reason: str
    prime_digest: str
    doctrine_digest: str
    source_digest: str
    p3t_source_digest: str
    open_digest: str


N2Result: TypeAlias = (
    PrimePowerReductionJudgment | N2ResourceLimit | N2FormalFailure
    | N2Refutation | N2Open
)
