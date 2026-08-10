"""Closed DTO grammar for finite P1-E4 historical observer actualization."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TypeAlias

from .construction.finite_builder.types import ConstructionSourceBinding
from .observer_genesis_types import (
    OEPAdmissionRecord, ObserverGenesisDoctrine, ObserverGenesisSource,
    RecurrenceEvidence, WitnessScope,
)
from .positive_ontology_types import ObserverDoctrine, OntologyStage


class ActualizationStatus(str, Enum):
    ESTABLISHED = "established"
    REFUTED = "refuted"
    OPEN = "open"


class HistoricalActualization(str, Enum):
    ESTABLISHED_RELATIVE_TO_HISTORY = "established-relative-to-history"
    OPEN = "open"


class PhysicalInstantiation(str, Enum):
    NOT_ESTABLISHED = "not-established"


class ConsciousnessStatus(str, Enum):
    NOT_CLAIMED = "not-claimed"


class EventKind(str, Enum):
    CONSTRUCTION = "construction"
    OEP = "oep"
    BIRTH = "birth"
    TARGET = "target"
    INTERVENTION = "intervention"
    RESPONSE = "response"
    ORACLE = "oracle"
    EXPECTED_RESPONSE = "expected-response"
    LATER_RESULT = "later-result"
    ACTUALIZATION_JUDGMENT = "actualization-judgment"
    ACTUALIZATION_CERTIFICATE = "actualization-certificate"
    COPIED_BIRTH = "copied-birth"
    OTHER = "other"


class EvidenceAvailability(str, Enum):
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"


class AccessKind(str, Enum):
    DATA_DEPENDENCY = "data-dependency"
    TARGET_READ = "target-read"
    ORACLE_READ = "oracle-read"
    EXPECTED_RESPONSE_READ = "expected-response-read"
    LATER_RESULT_READ = "later-result-read"


class CounterfactualClass(str, Enum):
    PREFIX_TARGET_VARIATION = "prefix-target-variation"
    TARGET_READING_CHOOSER = "target-reading-chooser"
    FOREIGN_PARENT_COPY = "foreign-parent-copy"


class CounterfactualOutcome(str, Enum):
    PASSED = "passed"
    FAILED = "failed"
    OPEN = "open"


class ActualizationOperation(str, Enum):
    SOURCE = "historical-observer-source"
    JUDGMENT = "historical-actualization-judgment"


class ActualizationOperationStatus(str, Enum):
    JUDGED = "judged"
    RESOURCE_LIMIT = "resource-limit"


class ActualizationResourceBound(str, Enum):
    EVENTS = "events"
    PARENT_EDGES = "parent-edges"
    ACCESS_EDGES = "access-edges"
    ASSUMPTIONS = "assumptions"
    COUNTERFACTUALS = "counterfactuals"
    ENCODED_BYTES = "encoded-bytes"


@dataclass(frozen=True)
class HistoryEvent:
    event_id: str
    kind: EventKind
    parent_ids: tuple[str, ...]
    logical_time: int
    payload_digest: str
    lineage_id: str
    availability: EvidenceAvailability = EvidenceAvailability.AVAILABLE


@dataclass(frozen=True)
class AccessEdge:
    provider_event_id: str
    consumer_event_id: str
    kind: AccessKind


@dataclass(frozen=True)
class HistoricalAssumption:
    assumption_id: str
    source_event_id: str
    depends_on: tuple[str, ...]


@dataclass(frozen=True)
class ActualizationCounterfactual:
    case_id: str
    kind: CounterfactualClass
    provider_event_id: str
    consumer_event_id: str
    alternate_target_digest: str
    copied_lineage_id: str
    copied_parent_ids: tuple[str, ...]


@dataclass(frozen=True)
class ActualizationResourcePolicy:
    version: str
    max_events: int
    max_parent_edges: int
    max_access_edges: int
    max_assumptions: int
    max_counterfactuals: int
    max_encoded_bytes: int
    policy_digest: str


@dataclass(frozen=True)
class HistoricalObserverSource:
    version: str
    history_id: str
    lineage_id: str
    events: tuple[HistoryEvent, ...]
    access_edges: tuple[AccessEdge, ...]
    assumptions: tuple[HistoricalAssumption, ...]
    assumption_roots: tuple[str, ...]
    counterfactuals: tuple[ActualizationCounterfactual, ...]
    birth_event_id: str
    construction_event_id: str
    oep_event_id: str
    target_event_id: str
    intervention_event_id: str
    response_event_id: str
    policy: ActualizationResourcePolicy
    p0_doctrine: ObserverDoctrine
    construction_source: ConstructionSourceBinding
    construction_target: OntologyStage
    e1_doctrine: ObserverGenesisDoctrine
    e1_source: ObserverGenesisSource
    e1_witness: WitnessScope
    e1_recurrence: RecurrenceEvidence
    e1_oep: OEPAdmissionRecord
    birth_core_digest: str
    historical_token_id: str
    history_digest: str
    doctrine_digest: str
    scope_digest: str
    source_digest: str


@dataclass(frozen=True)
class CounterfactualEvidence:
    case_id: str
    kind: CounterfactualClass
    outcome: CounterfactualOutcome
    evidence_digest: str


@dataclass(frozen=True)
class HistoricalActualizationJudgment:
    source_digest: str
    birth_core_digest: str
    historical_token_id: str
    history_digest: str
    doctrine_digest: str
    scope_digest: str
    past_event_ids: tuple[str, ...]
    future_event_ids: tuple[str, ...]
    counterfactual_evidence: tuple[CounterfactualEvidence, ...]
    oep_role: ActualizationStatus
    prior_construction: ActualizationStatus
    birth_event: ActualizationStatus
    target_independence: ActualizationStatus
    post_birth_efficacy: ActualizationStatus
    historical_actualization: HistoricalActualization
    actualization_judgment_digest: str
    operation_status: ActualizationOperationStatus = ActualizationOperationStatus.JUDGED
    physical_instantiation: PhysicalInstantiation = PhysicalInstantiation.NOT_ESTABLISHED
    consciousness: ConsciousnessStatus = ConsciousnessStatus.NOT_CLAIMED
    scope: str = "finite-history-relative-observer-actualization-only"


@dataclass(frozen=True)
class ActualizationResourceLimit:
    operation: ActualizationOperation
    failed_bound: ActualizationResourceBound
    required_value: int
    allowed_value: int
    policy_digest: str
    refusal_digest: str
    operation_status: ActualizationOperationStatus = ActualizationOperationStatus.RESOURCE_LIMIT
    physical_instantiation: PhysicalInstantiation = PhysicalInstantiation.NOT_ESTABLISHED
    consciousness: ConsciousnessStatus = ConsciousnessStatus.NOT_CLAIMED
    scope: str = "resource-refusal-no-historical-evidence"


ActualizationSourceResult: TypeAlias = HistoricalObserverSource | ActualizationResourceLimit
ActualizationResult: TypeAlias = HistoricalActualizationJudgment | ActualizationResourceLimit
