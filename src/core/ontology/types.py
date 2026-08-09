"""Closed DTOs for the bounded P0 positive-ontology experiment."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from ..observer_core_types import ResponseKind
from ..proof_core_types import CoreTerm


class RunStatus(str, Enum):
    """Operational observer outcomes, kept separate from ontic claims."""

    READY = "ready"
    BLOCKED = "blocked"
    NOT_QUERIED = "not-queried"


class ObserverSupport(str, Enum):
    """Observer-relative support; deliberately contains no absence verdict."""

    SUPPORTED = "supported"
    OPEN = "open"


class SilenceModality(str, Enum):
    """Non-equivalent meanings commonly hidden under one word, silence."""

    NONE = "none"
    INTRINSIC = "intrinsic-silence"
    RESPONSE = "response-silence"
    NOT_QUERIED = "not-queried"
    OPERATIONAL_ABSENCE = "operational-absence"
    OBSERVER_BLINDNESS = "observer-blindness"
    DOMAIN_UNDEFINED = "domain-undefined"
    OBSTRUCTION = "obstruction"
    EPISTEMIC_OPEN = "epistemic-open"
    RESOURCE_LIMITED = "resource-limited"
    DIVERGENT = "divergent"
    INCONSISTENT = "inconsistent"
    UNRESOLVED_IN_SYSTEM = "unresolved-in-system"
    MIXED = "mixed-response"


class RelationStatus(str, Enum):
    """A scoped echo judgment, not an object-identity verdict."""

    ECHO = "echo"
    SPLIT = "split"
    UNDETERMINED = "undetermined"


class InfinityLevel(str, Enum):
    """Five claims that finite execution must never collapse together."""

    BOUNDED_WINDOW = "bounded-window"
    LOCAL_EXTENSION = "local-extension"
    PRODUCTIVE_PROCESS = "productive-process"
    ALL_DEPTH_HYPOTHESIS = "all-depth-hypothesis"
    COMPLETED_CARRIER = "completed-carrier"


class FacetStatus(str, Enum):
    """Independent conservative status for one ontology-contract facet."""

    ESTABLISHED = "established"
    OPEN = "open"
    REFUTED = "refuted"
    NOT_EVALUATED = "not-evaluated"


@dataclass(frozen=True)
class MetalanguageBoundary:
    """Explicitly locate representation identity outside object language."""

    object_relation: str
    metatheory_identity: tuple[str, ...]
    echo_reflects_identity: bool
    metaphysical_proof: bool


@dataclass(frozen=True)
class SilenceBoundaryJudgment:
    """An explicit non-derived silence/unknown boundary with named evidence."""

    modality: SilenceModality
    evidence_id: str
    derived_from_observation: bool
    boundary: str


@dataclass(frozen=True)
class InternalObserver:
    """A typed, canonical closed R11 observer program."""

    observer_id: str
    canonical: bytes
    response_kind: ResponseKind


@dataclass(frozen=True)
class ObserverDoctrine:
    """Target-independent ordered observer admission doctrine."""

    doctrine_id: str
    admission_rule: str
    metadata: tuple[str, ...]
    observers: tuple[InternalObserver, ...]
    version: str
    fingerprint: str


@dataclass(frozen=True)
class OntologyStage:
    """One presented recurrence and its admitted cumulative observer family."""

    stage_id: str
    representative: CoreTerm
    doctrine_id: str
    observers: tuple[InternalObserver, ...]


@dataclass(frozen=True)
class ContinuationWitness:
    """A path-relative claim that explicitly named responses persist."""

    witness_id: str
    path_id: str
    lower_stage: str
    upper_stage: str
    preserved_observers: tuple[str, ...]


@dataclass(frozen=True)
class OntologyPresentation:
    """Finite doctrine-relative stages and continuation witnesses."""

    doctrine: ObserverDoctrine
    presentation_id: str
    stages: tuple[OntologyStage, ...]
    witnesses: tuple[ContinuationWitness, ...]


@dataclass(frozen=True)
class RunJudgment:
    """One typed run judgment, independent of support and persistence."""

    stage_id: str
    observer_id: str
    status: RunStatus
    response_kind: ResponseKind | None
    silence: tuple[SilenceModality, ...]
    obstruction_count: int


@dataclass(frozen=True)
class ObserverSupportJudgment:
    """Finite observer support for a presented stage; never nonexistence."""

    stage_id: str
    support: ObserverSupport
    runs: tuple[RunJudgment, ...]
    silence: tuple[SilenceModality, ...]
    scope: str = "finite-observer-family"


@dataclass(frozen=True)
class RelationObstruction:
    """First path/family-extension obstruction without identifying presentations."""

    witness_id: str
    observer_id: str
    lane: str
    outcome: str


@dataclass(frozen=True)
class PersistenceJudgment:
    """Echo continuity along one explicit composable witness path."""

    path_id: str
    checked_witnesses: int
    checked_observers: int
    status: RelationStatus
    first_obstruction: RelationObstruction | None
    scope: str = "finite-witness-path"


@dataclass(frozen=True)
class FamilyExtensionJudgment:
    """Separate inherited-family persistence from the full admitted prefix."""

    witness_id: str
    inherited_checks: int
    full_checks: int
    inherited_status: RelationStatus
    full_status: RelationStatus
    first_obstruction: RelationObstruction | None
    scope: str = "finite-declared-family-extension"


@dataclass(frozen=True)
class PresentationCommitment:
    """Canonical commitment to a finite stage presentation, not a construction proof."""

    witness_id: str
    stage_id: str
    stage_commitment: str
    rule: str = "finite-recurrence-presentation"


@dataclass(frozen=True)
class DiagramCoherenceJudgment:
    """Pairwise and global coherence are intentionally independent fields."""

    pairwise_compatible: bool
    global_coherent: bool
    obstruction_count: int
    scope: str = "finite-declared-diagram"


@dataclass(frozen=True)
class InfinityJudgment:
    """One nonpromoting infinity-level judgment with its evidence boundary."""

    level: InfinityLevel
    verified: bool
    maximum_depth: int
    finite_promoted: bool
    boundary: str
    scope: str = "bounded-continuation-evidence"


@dataclass(frozen=True)
class OntologyFacetReport:
    """Independent facets; this record defines no order, join, or lattice."""

    stage_id: str
    presented: FacetStatus
    admissible: FacetStatus
    observable: FacetStatus
    constructible: FacetStatus
    coherent: FacetStatus
    persistent: FacetStatus
    witnessed: FacetStatus
    scoped_object: FacetStatus
    presentation_commitment: str
    object_completion_boundary: str
    scope: str = "independent-facets-no-lattice"
