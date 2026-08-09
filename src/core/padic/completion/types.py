"""Closed DTOs for the ledger-relative PΩ2 prime-power completion."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TypeAlias

POMEGA2_NONCLAIMS = (
    "categorical-inverse-limit-universal-property",
    "mathlib-padic-int-equivalence",
    "topological-completion",
    "physical-instantiation",
    "foundation-independent-actuality",
    "generic-completion",
    "generic-inverse-limits",
    "all-depth-family-introduction",
    "digit-stream-equivalence",
    "field-structure",
)


class PadicLedgerRowClass(str, Enum):
    FOUNDATION = "foundation"
    DEFINITION = "definition"
    AXIOM = "axiom"
    TRUSTED_BOUNDARY = "trusted-boundary"
    NOT_USED = "not-used"


class PadicObligationStatus(str, Enum):
    ESTABLISHED = "established"


class PadicCompletedCarrierStatus(str, Enum):
    ESTABLISHED_RELATIVE_TO_LEDGER = "established-relative-to-ledger"


class PadicNotEstablishedStatus(str, Enum):
    NOT_ESTABLISHED = "not-established"


class PadicNotClaimedStatus(str, Enum):
    NOT_CLAIMED = "not-claimed"


class PadicResultStatus(str, Enum):
    RESOURCE_LIMIT = "resource-limit"


class PadicFailedBound(str, Enum):
    CAPTURED_BYTES = "captured-bytes"
    STATIC_COST = "static-cost"


class PadicExecutionFailureKind(str, Enum):
    TIMEOUT = "timeout"
    OUTPUT_LIMIT = "output-limit"
    COMPILE_ERROR = "compile-error"
    CONTINUITY_DRIFT = "continuity-drift"


@dataclass(frozen=True)
class PrimeSource:
    version: str
    p: int
    witness_algorithm_id: str
    generated_witness_bytes: bytes
    generated_witness_sha256: str
    source_digest: str


@dataclass(frozen=True)
class PadicTowerDoctrine:
    version: str
    doctrine_id: str
    index_id: str
    stage_id: str
    modulus_id: str
    reduction_id: str
    family_class_id: str
    carrier_id: str
    equality_id: str
    ring_id: str
    ppcp_rule_id: str
    doctrine_digest: str


@dataclass(frozen=True)
class PadicCompletionTheoremSource:
    version: str
    artifact_path_id: str
    artifact_sha256: str
    theorem_ids: tuple[str, ...]
    representation_id: str
    canonical_ops_id: str
    concrete_instance_id: str
    toolchain_id: str
    tcb_digest: str
    source_digest: str


@dataclass(frozen=True)
class PadicCompletionLedgerRow:
    row_id: str
    row_class: PadicLedgerRowClass
    direct_dependencies: tuple[str, ...]
    use: str
    source_digest: str
    axiom_closure: tuple[str, ...]


@dataclass(frozen=True)
class PadicCompletionLedger:
    version: str
    rows: tuple[PadicCompletionLedgerRow, ...]
    theorem_axiom_closure: tuple[str, ...]
    ledger_digest: str


@dataclass(frozen=True)
class PadicCompletionPolicy:
    version: str
    max_captured_bytes: int
    max_static_cost: int
    compile_timeout_seconds: int
    max_output_bytes: int
    policy_digest: str


@dataclass(frozen=True)
class PadicCompletionPackage:
    prime: PrimeSource
    doctrine: PadicTowerDoctrine
    theorem_source: PadicCompletionTheoremSource
    ledger: PadicCompletionLedger
    policy: PadicCompletionPolicy
    package_digest: str


@dataclass(frozen=True)
class PadicCompletionObligations:
    prime_lower_bound: PadicObligationStatus
    stage_modulus_divisibility: PadicObligationStatus
    reduction_well_formed_congruence: PadicObligationStatus
    reduction_identity: PadicObligationStatus
    reduction_composition: PadicObligationStatus
    carrier_presentation_compatible: PadicObligationStatus
    universal_realization: PadicObligationStatus
    coordinate_agreement: PadicObligationStatus
    joint_separation: PadicObligationStatus
    relative_uniqueness: PadicObligationStatus
    zero_family_nonvacuity: PadicObligationStatus
    one_family_formation: PadicObligationStatus
    addition_closure: PadicObligationStatus
    negation_additive_inverse: PadicObligationStatus
    multiplication_closure: PadicObligationStatus
    full_commutative_ring: PadicObligationStatus
    ppcp_introduction: PadicObligationStatus


@dataclass(frozen=True)
class PadicCompletionJudgment:
    prime_digest: str
    doctrine_digest: str
    theorem_source_digest: str
    ledger_digest: str
    package_digest: str
    policy_digest: str
    run_digest: str
    canonical_ops_id: str
    concrete_instance_id: str
    theorem_ids: tuple[str, ...]
    theorem_axiom_closure: tuple[str, ...]
    obligations: PadicCompletionObligations
    tower_formation: PadicObligationStatus
    compatible_family_class: PadicObligationStatus
    universal_realization: PadicObligationStatus
    joint_separation: PadicObligationStatus
    ring_closure: PadicObligationStatus
    completed_carrier: PadicCompletedCarrierStatus
    categorical_inverse_limit_universal_property: PadicNotEstablishedStatus
    equivalent_to_mathlib_padic_int: PadicNotEstablishedStatus
    topological_completion: PadicNotEstablishedStatus
    physical_instantiation: PadicNotEstablishedStatus
    foundation_independent_actuality: PadicNotClaimedStatus
    nonclaims: tuple[str, ...]
    judgment_digest: str


@dataclass(frozen=True)
class PadicCompletionResourceLimit:
    status: PadicResultStatus
    package_digest: str
    policy_digest: str
    run_digest: str
    failed_bound: PadicFailedBound
    required_value: int
    allowed_value: int
    nonclaims: tuple[str, ...]
    refusal_digest: str


@dataclass(frozen=True)
class PadicFormalExecutionFailure:
    kind: PadicExecutionFailureKind
    package_digest: str
    policy_digest: str
    run_digest: str
    attempt_digest: str
    diagnostic: str
    nonclaims: tuple[str, ...]


PadicCompletionResult: TypeAlias = (
    PadicCompletionJudgment | PadicCompletionResourceLimit | PadicFormalExecutionFailure
)


@dataclass(frozen=True)
class BoundedPadicShadow:
    p: int
    depth: int
    zero: tuple[int, ...]
    one: tuple[int, ...]
    minus_one: tuple[int, ...]
    add_inverse_checks: tuple[bool, ...]
    restriction_checks: int
    strict_refinement_witnesses: int
    incompatible_first_failure: tuple[int, int] | None
    scope: str
    shadow_digest: str
