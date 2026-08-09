"""Immutable DTOs for P1-A2 finite observer-relation classification."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TypeAlias

from ..morphism import ObserverSourceBinding, ProjectionStep
from ...proof_core_types import CoreTerm

OBSERVER_RELATION_NONCLAIMS = (
    "observer-independent-identity",
    "universal-refinement",
    "off-scope-equivalence",
    "chronology",
    "ontic-observer-genesis",
    "confluence",
    "scoped-object-formation",
    "all-depth-existence",
    "completed-infinity",
    "consciousness",
    "physical-instantiation",
    "novelty",
    "r8-promotion",
    "layer-promotion",
    "sage-promotion",
)


class ComparisonMode(str, Enum):
    """Which independently bound translation evidence is requested."""

    EXTENSIONAL_ONLY = "extensional-only"
    WITH_PROPOSALS = "with-proposals"
    WITH_P1A_REPLAY = "with-p1a-replay"


class LawStatus(str, Enum):
    """Three-way exact finite law status."""

    ESTABLISHED = "established"
    REFUTED = "refuted"
    OPEN = "open"


class PairOutcome(str, Enum):
    """One observer's relation outcome for an ordered pair."""

    ECHO = "echo"
    MISMATCH = "mismatch"
    BLOCKED = "blocked"


class RelationClass(str, Enum):
    """Deterministic classification derived from independent laws."""

    EQUIVALENT_ON_SCOPE = "equivalent-on-scope"
    STRICT_REFINEMENT_ON_SCOPE = "strict-refinement-on-scope"
    STRICT_COARSENING_ON_SCOPE = "strict-coarsening-on-scope"
    INCOMPARABLE_ON_SCOPE = "incomparable-on-scope"
    OPEN = "open"


class MorphismEvidenceStatus(str, Enum):
    """Whether raw P1-A replay established a structural translation."""

    ABSENT = "absent"
    P1A_ESTABLISHED = "p1a-established"


class TranslationInputKind(str, Enum):
    """Exact provenance variant for a translation assessment."""

    ABSENT = "absent"
    P1A_REPLAY = "p1a-replay"
    PROPOSAL = "proposal"


class ProposalStatus(str, Enum):
    """Finite triangle outcome for a typed non-theorem proposal."""

    ABSENT = "absent"
    COMMUTES_ON_SCOPE = "commutes-on-scope"
    CONFLICT_ON_SCOPE = "conflict-on-scope"
    OPEN = "open"


class InvertibilityStatus(str, Enum):
    """A2.1/A2.2 cannot establish reversible translations."""

    NOT_ESTABLISHED = "not-established"


class LossStatus(str, Enum):
    """Information-loss status requiring established P1-A replay."""

    NOT_ESTABLISHED = "not-established"
    LOSSY_ON_SCOPE = "lossy-on-scope"
    LOSSLESS_ON_SCOPE = "lossless-on-scope"


class CoverageStatus(str, Enum):
    """Whether every stage response was ready."""

    COMPLETE = "complete"
    PARTIAL_BLOCKED = "partial-blocked"


class RelationRunStatus(str, Enum):
    """Fresh stage observation status."""

    READY = "ready"
    BLOCKED = "blocked"


@dataclass(frozen=True)
class RelationStage:
    """One exact recurrence and its commitment."""

    stage_id: str
    recurrence: CoreTerm
    commitment: str


@dataclass(frozen=True)
class RelationEvaluationSource:
    """Ordered, doctrine-bound finite recurrence source."""

    doctrine_fingerprint: str
    stages: tuple[RelationStage, ...]
    ordered_commitments: tuple[str, ...]
    observer_source_digest: str
    version: str
    source_digest: str


StageKey: TypeAlias = tuple[str, str]
PairKey: TypeAlias = tuple[StageKey, StageKey]


@dataclass(frozen=True)
class ObserverRelationScope:
    """Exact ordered scope including the complete Cartesian pair universe."""

    doctrine_fingerprint: str
    observer_source_digest: str
    stage_source_digest: str
    fine_observer_id: str
    coarse_observer_id: str
    stages: tuple[StageKey, ...]
    ordered_pairs: tuple[PairKey, ...]
    mode: ComparisonMode
    scope_digest: str


@dataclass(frozen=True)
class MorphismReplaySpec:
    """Raw P1-A replay request; never a prior judgment."""

    morphism_id: str
    fine_observer_id: str
    coarse_observer_id: str
    projection: tuple[ProjectionStep, ...]


@dataclass(frozen=True)
class TranslationProposal:
    """Typed closed projection proposal without a factorization claim."""

    proposal_id: str
    fine_observer_id: str
    coarse_observer_id: str
    projection: tuple[ProjectionStep, ...]
    doctrine_fingerprint: str
    observer_source_digest: str
    proposal_digest: str


TranslationInput: TypeAlias = MorphismReplaySpec | TranslationProposal


@dataclass(frozen=True)
class StageObservationRow:
    """Fresh response or blocked marker for both observers at one stage."""

    stage: StageKey
    fine_status: RelationRunStatus
    coarse_status: RelationRunStatus
    fine_payload_digest: str
    coarse_payload_digest: str
    row_digest: str


@dataclass(frozen=True)
class RelationPairRow:
    """One exact ordered pair relation comparison."""

    pair_index: int
    left: StageKey
    right: StageKey
    fine_outcome: PairOutcome
    coarse_outcome: PairOutcome
    fine_left_payload: str
    fine_right_payload: str
    coarse_left_payload: str
    coarse_right_payload: str
    row_digest: str


@dataclass(frozen=True)
class RelationWitness:
    """First exact row refuting one implication."""

    pair_index: int
    row_digest: str
    left: StageKey
    right: StageKey


@dataclass(frozen=True)
class DomainWitness:
    """First stage on which exactly one observer is ready."""

    stage_index: int
    stage: StageKey
    fine_status: RelationRunStatus
    coarse_status: RelationRunStatus
    row_digest: str


@dataclass(frozen=True)
class TranslationTriangleRow:
    """One freshly checked response triangle."""

    stage_index: int
    stage: StageKey
    status: ProposalStatus
    fine_payload_digest: str
    translated_payload_digest: str
    coarse_payload_digest: str
    row_digest: str


@dataclass(frozen=True)
class TranslationAssessment:
    """Separate structural/proposal result and its first conflict."""

    input_kind: TranslationInputKind
    input_commitment: str
    morphism_status: MorphismEvidenceStatus
    proposal_status: ProposalStatus
    triangles: tuple[TranslationTriangleRow, ...]
    conflict: TranslationTriangleRow | None
    translation_digest: str


@dataclass(frozen=True)
class ObserverRelationJudgment:
    """Closed P1-A2.1/A2.2 finite relation artifact."""

    doctrine_fingerprint: str
    observer_source_digest: str
    stage_source_digest: str
    scope_digest: str
    observations: tuple[StageObservationRow, ...]
    pairs: tuple[RelationPairRow, ...]
    preservation: LawStatus
    reflection: LawStatus
    domain_equality: LawStatus
    preservation_witness: RelationWitness | None
    reflection_witness: RelationWitness | None
    domain_witness: DomainWitness | None
    classification: RelationClass
    forward: TranslationAssessment
    reverse: TranslationAssessment
    structural_invertibility: InvertibilityStatus
    information_loss: LossStatus
    coverage: CoverageStatus
    charged_checks: int
    observer_independent_identity: LawStatus
    universal_refinement: LawStatus
    nonclaims: tuple[str, ...]
    judgment_digest: str


class RelationOperation(str, Enum):
    """Typed operation marker for resource refusal."""

    JUDGE = "observer-relation-judgment"


class RelationResultStatus(str, Enum):
    """Typed refusal run status."""

    RESOURCE_LIMIT = "resource-limit"


@dataclass(frozen=True)
class RelationResourcePolicy:
    """Versioned and digest-bound work policy."""

    version: str
    max_cost: int
    max_encoded_bytes: int
    policy_digest: str


@dataclass(frozen=True)
class RelationResourceLimit:
    """Typed refusal emitted before any semantic observation."""

    operation: RelationOperation
    status: RelationResultStatus
    policy_version: str
    policy_digest: str
    doctrine_fingerprint: str
    observer_source_digest: str
    stage_source_digest: str
    scope_digest: str
    required_cost: int
    allowed_cost: int
    required_encoded_bytes: int
    allowed_encoded_bytes: int
    observer_independent_identity: LawStatus
    universal_refinement: LawStatus
    nonclaims: tuple[str, ...]
    refusal_digest: str


ObserverRelationResult: TypeAlias = ObserverRelationJudgment | RelationResourceLimit


@dataclass(frozen=True)
class RelationRequest:
    """Validated request envelope used by preflight and runtime."""

    binding: ObserverSourceBinding
    source: RelationEvaluationSource
    scope: ObserverRelationScope
    forward: TranslationInput | None
    reverse: TranslationInput | None
    policy: RelationResourcePolicy
