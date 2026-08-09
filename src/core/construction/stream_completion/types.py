"""Closed DTOs for PΩ1 completed finite-alphabet stream carriers."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TypeAlias

POMEGA1_NONCLAIMS = (
    "physical-infinity", "foundation-independent-existence",
    "observer-independent-metaphysical-identity", "generic-inverse-limits",
    "p-adics", "generic-compactness", "generic-completion", "choice",
    "novelty", "r8-promotion", "layer-promotion", "sage-promotion",
)


class LedgerRowClass(str, Enum):
    FOUNDATION = "foundation"
    DEFINITION = "definition"
    AXIOM = "axiom"
    TRUSTED_BOUNDARY = "trusted-boundary"
    NOT_USED = "not-used"


class ObligationStatus(str, Enum):
    ESTABLISHED = "established"


class CompletedCarrierStatus(str, Enum):
    ESTABLISHED_RELATIVE_TO_LEDGER = "established-relative-to-ledger"


class PhysicalInstantiationStatus(str, Enum):
    NOT_ESTABLISHED = "not-established"


class MetaphysicalTotalityStatus(str, Enum):
    NOT_CLAIMED = "not-claimed"


class CompletionResultStatus(str, Enum):
    RESOURCE_LIMIT = "resource-limit"


class CompletionFailedBound(str, Enum):
    CAPTURED_BYTES = "captured-bytes"
    STATIC_COST = "static-cost"


class FormalExecutionFailureKind(str, Enum):
    TIMEOUT = "timeout"
    OUTPUT_LIMIT = "output-limit"
    COMPILE_ERROR = "compile-error"
    CONTINUITY_DRIFT = "continuity-drift"


@dataclass(frozen=True)
class StreamAlphabetSource:
    version: str
    symbols: tuple[str, ...]
    alphabet_digest: str


@dataclass(frozen=True)
class FormalAlphabetPresentation:
    alphabet_digest: str
    cardinality: int
    generated_instance_bytes: bytes
    generated_instance_sha256: str
    index_to_symbol: tuple[str, ...]
    symbol_to_index: tuple[tuple[str, int], ...]
    inhabitant_index: int
    inhabitant_symbol: str
    theorem_ids: tuple[str, ...]
    generic_source_digest: str
    template_digest: str
    presentation_digest: str


@dataclass(frozen=True)
class StreamCompletionTheoremSource:
    version: str
    artifact_path_id: str
    artifact_sha256: str
    theorem_ids: tuple[str, ...]
    representation_id: str
    toolchain_id: str
    tcb_digest: str
    source_digest: str


@dataclass(frozen=True)
class StreamCompletionDoctrine:
    version: str
    doctrine_id: str
    index_id: str
    prefix_id: str
    family_class_id: str
    carrier_id: str
    restriction_id: str
    equality_id: str
    scp_rule_id: str
    doctrine_digest: str


@dataclass(frozen=True)
class StreamCompletionLedgerRow:
    row_id: str
    row_class: LedgerRowClass
    direct_dependencies: tuple[str, ...]
    use: str
    source_digest: str
    axiom_closure: tuple[str, ...]


@dataclass(frozen=True)
class StreamCompletionLedger:
    version: str
    rows: tuple[StreamCompletionLedgerRow, ...]
    theorem_axiom_closure: tuple[str, ...]
    ledger_digest: str


@dataclass(frozen=True)
class StreamCompletionPolicy:
    version: str
    max_captured_bytes: int
    max_static_cost: int
    compile_timeout_seconds: int
    max_output_bytes: int
    policy_digest: str


@dataclass(frozen=True)
class StreamCompletionPackage:
    doctrine: StreamCompletionDoctrine
    alphabet: StreamAlphabetSource
    alphabet_presentation: FormalAlphabetPresentation
    family_class_id: str
    carrier_id: str
    restriction_id: str
    theorem_source: StreamCompletionTheoremSource
    ledger: StreamCompletionLedger
    policy: StreamCompletionPolicy
    package_digest: str


@dataclass(frozen=True)
class CompletionObligationStatuses:
    truncation_identity: ObligationStatus
    truncation_composition: ObligationStatus
    restriction_formation_congruence: ObligationStatus
    restriction_compatibility: ObligationStatus
    diagonal_realization: ObligationStatus
    universal_realization: ObligationStatus
    coordinate_agreement: ObligationStatus
    joint_separation: ObligationStatus
    relative_uniqueness: ObligationStatus
    nonvacuity_inhabitance: ObligationStatus
    scp_introduction: ObligationStatus


@dataclass(frozen=True)
class StreamCompletionJudgment:
    doctrine_digest: str
    alphabet_digest: str
    presentation_digest: str
    theorem_source_digest: str
    ledger_digest: str
    package_digest: str
    policy_digest: str
    run_digest: str
    theorem_ids: tuple[str, ...]
    theorem_axiom_closure: tuple[str, ...]
    obligations: CompletionObligationStatuses
    formal_carrier_presentation: ObligationStatus
    universal_realization: ObligationStatus
    joint_separation: ObligationStatus
    completed_carrier: CompletedCarrierStatus
    physical_instantiation: PhysicalInstantiationStatus
    observer_independent_metaphysical_totality: MetaphysicalTotalityStatus
    nonclaims: tuple[str, ...]
    judgment_digest: str


@dataclass(frozen=True)
class StreamCompletionResourceLimit:
    status: CompletionResultStatus
    package_digest: str
    policy_digest: str
    run_digest: str
    failed_bound: CompletionFailedBound
    required_value: int
    allowed_value: int
    nonclaims: tuple[str, ...]
    refusal_digest: str


@dataclass(frozen=True)
class FormalExecutionFailure:
    kind: FormalExecutionFailureKind
    package_digest: str
    policy_digest: str
    run_digest: str
    attempt_digest: str
    diagnostic: str
    physical_instantiation: PhysicalInstantiationStatus
    observer_independent_metaphysical_totality: MetaphysicalTotalityStatus
    nonclaims: tuple[str, ...]


StreamCompletionResult: TypeAlias = (
    StreamCompletionJudgment | StreamCompletionResourceLimit | FormalExecutionFailure
)


@dataclass(frozen=True)
class BoundedStreamShadow:
    alphabet_digest: str
    depth: int
    finite_stream: tuple[str, ...]
    restrictions: tuple[tuple[str, ...], ...]
    diagonal: tuple[str, ...]
    shadow_digest: str
    scope: str = "finite-pressure-not-completed-carrier-evidence"
