"""Exact closed DTOs for P1-D3 all-depth family introduction."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TypeAlias

from ..infinity_prefix import PrefixAlphabet
from ..productivity.types import PeriodicPrefixStage, PeriodicProgram


class FamilyEvidenceStatus(str, Enum):
    OPEN = "open"
    ASSUMED = "assumed"
    ESTABLISHED_RELATIVE_TO_LEDGER = "established-relative-to-ledger"


class FamilyProvenance(str, Enum):
    SUPPLIED_HYPOTHESIS = "supplied-hypothesis"
    FORMALLY_DERIVED = "formally-derived"
    ORACLE_DEPENDENT = "oracle-dependent"


class LawStatus(str, Enum):
    ESTABLISHED = "established"
    ASSUMED = "assumed"
    REFUTED = "refuted"
    OPEN = "open"


class LedgerStatus(str, Enum):
    CLOSED = "closed"


class CompletedCarrierStatus(str, Enum):
    NOT_ESTABLISHED = "not-established"


class HigherStatus(str, Enum):
    OPEN = "open"


class IntroductionKind(str, Enum):
    PERIODIC_DERIVED = "periodic-derived"
    SUPPLIED = "supplied"
    ORACLE = "oracle"


class ProjectionCapability(str, Enum):
    PERIODIC_EXECUTABLE = "periodic-executable"
    SYMBOLIC_ONLY = "symbolic-only"
    ORACLE_INTERFACE = "oracle-interface"


class ProjectionStatus(str, Enum):
    CONSTRUCTED = "constructed"
    RESOURCE_LIMIT = "resource-limit"
    PROJECTION_UNAVAILABLE = "projection-unavailable"


class ProjectionResourceBound(str, Enum):
    DEPTH = "max-depth"
    OUTPUT_BYTES = "max-output-bytes"


class AssumptionKind(str, Enum):
    DEFINITION = "definition"
    FOUNDATION = "foundation"
    HYPOTHESIS = "hypothesis"
    TRUSTED_IMPORT = "trusted-import"


@dataclass(frozen=True)
class AssumptionRow:
    assumption_id: str
    kind: AssumptionKind
    depends_on: tuple[str, ...]


@dataclass(frozen=True)
class AssumptionLedger:
    version: str
    foundation_id: str
    tcb_digest: str
    rows: tuple[AssumptionRow, ...]
    closure: tuple[str, ...]
    ledger_digest: str


@dataclass(frozen=True)
class AllDepthFamilySpec:
    version: str
    doctrine_version: str
    doctrine_fingerprint: str
    alphabet: PrefixAlphabet
    natural_index_id: str
    stage_encoding_id: str
    stage_validator_id: str
    relation_id: str
    restriction_id: str
    relation_law_ids: tuple[str, ...]
    restriction_law_ids: tuple[str, ...]
    family_equivalence_theorem_id: str
    specification_digest: str


@dataclass(frozen=True)
class AlgebraicLawStatus:
    relation_reflexive: LawStatus
    relation_symmetric: LawStatus
    relation_transitive: LawStatus
    restriction_identity: LawStatus
    restriction_composition: LawStatus
    restriction_congruence: LawStatus
    family_equivalence: LawStatus


@dataclass(frozen=True)
class FormalFamilySource:
    version: str
    foundation_id: str
    artifact_name: str
    artifact_sha256: str
    theorem_ids: tuple[str, ...]
    axiom_closure: tuple[str, ...]
    toolchain_id: str
    tcb_digest: str
    formal_source_digest: str


@dataclass(frozen=True)
class FamilyTerm:
    version: str
    constructor_id: str
    program: PeriodicProgram | None
    symbolic_term: bytes
    family_spec_digest: str
    family_term_digest: str


@dataclass(frozen=True)
class FamilyHypothesis:
    version: str
    hypothesis_id: str
    term: FamilyTerm
    coordinate_law_id: str
    compatibility_law_id: str
    ledger: AssumptionLedger
    hypothesis_digest: str


@dataclass(frozen=True)
class OracleFamilyHypothesis:
    version: str
    hypothesis_id: str
    term: FamilyTerm
    oracle_interface_id: str
    totality_hypothesis_id: str
    purity_hypothesis_id: str
    stability_hypothesis_id: str
    trust_identity: str
    ledger: AssumptionLedger
    hypothesis_digest: str


@dataclass(frozen=True)
class FamilyIntroductionSource:
    kind: IntroductionKind
    spec: AllDepthFamilySpec
    term: FamilyTerm
    ledger: AssumptionLedger
    generator_digest: str | None
    formal_source: FormalFamilySource | None
    hypothesis: FamilyHypothesis | OracleFamilyHypothesis | None
    hypothesis_digest: str | None
    introduction_evidence_digest: str
    source_digest: str
    capability: ProjectionCapability


@dataclass(frozen=True)
class AllDepthFamilyJudgment:
    spec: AllDepthFamilySpec
    source: FamilyIntroductionSource | None
    spec_validity: LawStatus
    coordinate_totality: LawStatus
    restriction_compatibility: LawStatus
    algebraic_laws: AlgebraicLawStatus
    evidence_status: FamilyEvidenceStatus
    provenance: FamilyProvenance | None
    ledger_status: LedgerStatus
    ledger_digest: str
    foundation_id: str
    tcb_digest: str
    family_term_digest: str | None
    introduction_evidence_digest: str | None
    judgment_digest: str
    completed_carrier: CompletedCarrierStatus = CompletedCarrierStatus.NOT_ESTABLISHED
    universal_realization: HigherStatus = HigherStatus.OPEN
    observer_separation: HigherStatus = HigherStatus.OPEN
    scope: str = "doctrine-ledger-relative-all-depth-family"


@dataclass(frozen=True)
class FamilyProjectionArtifact:
    source_digest: str
    family_term_digest: str
    introduction_evidence_digest: str
    policy_digest: str
    run_digest: str
    depth: int
    stage: PeriodicPrefixStage
    output_digest: str
    projection_digest: str
    status: ProjectionStatus = ProjectionStatus.CONSTRUCTED
    completed_carrier: CompletedCarrierStatus = CompletedCarrierStatus.NOT_ESTABLISHED
    scope: str = "one-finite-projection-not-universal-proof"


@dataclass(frozen=True)
class FamilyProjectionRefusal:
    source_digest: str
    family_term_digest: str
    introduction_evidence_digest: str
    policy_digest: str
    run_digest: str
    requested_depth: int
    status: ProjectionStatus
    failed_bound: ProjectionResourceBound | None
    required_value: int | None
    allowed_value: int | None
    refusal_digest: str
    completed_carrier: CompletedCarrierStatus = CompletedCarrierStatus.NOT_ESTABLISHED
    scope: str = "operational-refusal-family-status-unchanged"


FamilyProjectionResult: TypeAlias = FamilyProjectionArtifact | FamilyProjectionRefusal
