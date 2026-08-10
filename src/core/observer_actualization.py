"""Public isolated facade for finite P1-E4 historical actualization."""

from __future__ import annotations

import logging

from .construction.finite_builder.types import ConstructionSourceBinding
from .observer_actualization_graph import ObserverActualizationValidationError
from .observer_actualization_result_validation import validate_actualization_result
from .observer_actualization_runtime import historical_actualization_judgment
from .observer_actualization_types import (
    AccessEdge, AccessKind, ActualizationCounterfactual, ActualizationOperation,
    ActualizationOperationStatus, ActualizationResourceBound,
    ActualizationResourceLimit, ActualizationResourcePolicy, ActualizationResult,
    ActualizationSourceResult, ActualizationStatus, ConsciousnessStatus,
    CounterfactualClass, CounterfactualEvidence, CounterfactualOutcome,
    EventKind, EvidenceAvailability, HistoricalActualization,
    HistoricalActualizationJudgment, HistoricalAssumption,
    HistoricalObserverSource, HistoryEvent, PhysicalInstantiation,
)
from .observer_actualization_validation import build_policy, build_source
from .observer_genesis_types import (
    OEPAdmissionRecord, ObserverGenesisDoctrine, ObserverGenesisSource,
    RecurrenceEvidence, WitnessScope,
)
from .positive_ontology_types import ObserverDoctrine, OntologyStage

logger = logging.getLogger(__name__)


def actualization_resource_policy(
    max_events: int = 64, max_parent_edges: int = 256,
    max_access_edges: int = 256, max_assumptions: int = 128,
    max_counterfactuals: int = 3, max_encoded_bytes: int = 65_536,
) -> ActualizationResourcePolicy:  # noqa: F405
    """Build the explicit E4 graph/resource envelope."""
    logger.debug("actualization_resource_policy entry")
    result = build_policy(
        max_events, max_parent_edges, max_access_edges, max_assumptions,
        max_counterfactuals, max_encoded_bytes,
    )
    logger.debug("actualization_resource_policy exit")
    return result


def history_event(
    event_id: str, kind: EventKind, parent_ids: tuple[str, ...],  # noqa: F405
    logical_time: int, payload_digest: str, lineage_id: str,
    availability: EvidenceAvailability = EvidenceAvailability.AVAILABLE,  # noqa: F405
) -> HistoryEvent:  # noqa: F405
    """Create one raw event; source construction performs exact validation."""
    logger.debug("history_event entry event=%s", event_id)
    result = HistoryEvent(  # noqa: F405
        event_id, kind, parent_ids, logical_time, payload_digest, lineage_id,
        availability,
    )
    logger.debug("history_event exit event=%s", event_id)
    return result


def access_edge(
    provider_event_id: str, consumer_event_id: str, kind: AccessKind,  # noqa: F405
) -> AccessEdge:  # noqa: F405
    """Create one typed information-flow edge."""
    logger.debug("access_edge entry")
    result = AccessEdge(provider_event_id, consumer_event_id, kind)  # noqa: F405
    logger.debug("access_edge exit")
    return result


def historical_assumption(
    assumption_id: str, source_event_id: str, depends_on: tuple[str, ...],
) -> HistoricalAssumption:  # noqa: F405
    """Create one named assumption-DAG node bound to a source event."""
    logger.debug("historical_assumption entry")
    result = HistoricalAssumption(  # noqa: F405
        assumption_id, source_event_id, depends_on,
    )
    logger.debug("historical_assumption exit")
    return result


def actualization_counterfactual(
    case_id: str, kind: CounterfactualClass,  # noqa: F405
    provider_event_id: str, consumer_event_id: str,
    alternate_target_digest: str, copied_lineage_id: str,
    copied_parent_ids: tuple[str, ...],
) -> ActualizationCounterfactual:  # noqa: F405
    """Create one closed counterfactual mutation descriptor."""
    logger.debug("actualization_counterfactual entry kind=%s", kind.value)
    result = ActualizationCounterfactual(  # noqa: F405
        case_id, kind, provider_event_id, consumer_event_id,
        alternate_target_digest, copied_lineage_id, copied_parent_ids,
    )
    logger.debug("actualization_counterfactual exit kind=%s", kind.value)
    return result


def historical_observer_source(
    policy: ActualizationResourcePolicy, history_id: str, lineage_id: str,  # noqa: F405
    events: tuple[HistoryEvent, ...], access_edges: tuple[AccessEdge, ...],  # noqa: F405
    assumptions: tuple[HistoricalAssumption, ...],  # noqa: F405
    assumption_roots: tuple[str, ...],
    counterfactuals: tuple[ActualizationCounterfactual, ...],  # noqa: F405
    birth_event_id: str, construction_event_id: str, oep_event_id: str,
    target_event_id: str, intervention_event_id: str, response_event_id: str,
    p0_doctrine: ObserverDoctrine, construction_source: ConstructionSourceBinding,
    construction_target: OntologyStage, e1_doctrine: ObserverGenesisDoctrine,
    e1_source: ObserverGenesisSource, e1_witness: WitnessScope,
    e1_recurrence: RecurrenceEvidence, e1_oep: OEPAdmissionRecord,
) -> ActualizationSourceResult:  # noqa: F405
    """Bind one finite event DAG to raw P1-B and E1 evidence."""
    logger.debug("historical_observer_source entry")
    result = build_source(
        policy, history_id, lineage_id, events, access_edges, assumptions,
        assumption_roots, counterfactuals, birth_event_id, construction_event_id,
        oep_event_id, target_event_id, intervention_event_id, response_event_id,
        p0_doctrine, construction_source, construction_target, e1_doctrine,
        e1_source, e1_witness, e1_recurrence, e1_oep,
    )
    logger.debug("historical_observer_source exit type=%s", type(result).__name__)
    return result


__all__ = (
    "ObserverActualizationValidationError", "actualization_resource_policy",
    "history_event", "access_edge", "historical_assumption",
    "actualization_counterfactual", "historical_observer_source",
    "historical_actualization_judgment", "validate_actualization_result",
    "ActualizationStatus", "HistoricalActualization", "PhysicalInstantiation",
    "ConsciousnessStatus", "EventKind", "EvidenceAvailability", "AccessKind",
    "CounterfactualClass", "CounterfactualOutcome", "ActualizationOperation",
    "ActualizationOperationStatus", "ActualizationResourceBound",
    "HistoryEvent", "AccessEdge", "HistoricalAssumption",
    "ActualizationCounterfactual", "ActualizationResourcePolicy",
    "HistoricalObserverSource", "CounterfactualEvidence",
    "HistoricalActualizationJudgment", "ActualizationResourceLimit",
    "ActualizationSourceResult", "ActualizationResult",
)
