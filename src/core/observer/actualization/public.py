"""Collision-safe root aliases for released P1-E4 historical actualization."""

from __future__ import annotations

from . import core as _e4

E4ObserverActualizationValidationError = _e4.ObserverActualizationValidationError
E4ActualizationStatus = _e4.ActualizationStatus
E4HistoricalActualization = _e4.HistoricalActualization
E4PhysicalInstantiation = _e4.PhysicalInstantiation
E4ConsciousnessStatus = _e4.ConsciousnessStatus
E4EventKind = _e4.EventKind
E4EvidenceAvailability = _e4.EvidenceAvailability
E4AccessKind = _e4.AccessKind
E4CounterfactualClass = _e4.CounterfactualClass
E4CounterfactualOutcome = _e4.CounterfactualOutcome
E4ActualizationOperation = _e4.ActualizationOperation
E4ActualizationOperationStatus = _e4.ActualizationOperationStatus
E4ActualizationResourceBound = _e4.ActualizationResourceBound
E4HistoryEvent = _e4.HistoryEvent
E4AccessEdge = _e4.AccessEdge
E4HistoricalAssumption = _e4.HistoricalAssumption
E4ActualizationCounterfactual = _e4.ActualizationCounterfactual
E4ActualizationResourcePolicy = _e4.ActualizationResourcePolicy
E4HistoricalObserverSource = _e4.HistoricalObserverSource
E4CounterfactualEvidence = _e4.CounterfactualEvidence
E4HistoricalActualizationJudgment = _e4.HistoricalActualizationJudgment
E4ActualizationResourceLimit = _e4.ActualizationResourceLimit
E4ActualizationSourceResult = _e4.ActualizationSourceResult
E4ActualizationResult = _e4.ActualizationResult

e4_actualization_resource_policy = _e4.actualization_resource_policy
e4_history_event = _e4.history_event
e4_access_edge = _e4.access_edge
e4_historical_assumption = _e4.historical_assumption
e4_actualization_counterfactual = _e4.actualization_counterfactual
e4_historical_observer_source = _e4.historical_observer_source
e4_historical_actualization_judgment = _e4.historical_actualization_judgment
e4_validate_actualization_result = _e4.validate_actualization_result

__all__ = (
    "E4ObserverActualizationValidationError", "E4ActualizationStatus",
    "E4HistoricalActualization", "E4PhysicalInstantiation",
    "E4ConsciousnessStatus", "E4EventKind", "E4EvidenceAvailability",
    "E4AccessKind", "E4CounterfactualClass", "E4CounterfactualOutcome",
    "E4ActualizationOperation", "E4ActualizationOperationStatus",
    "E4ActualizationResourceBound", "E4HistoryEvent", "E4AccessEdge",
    "E4HistoricalAssumption", "E4ActualizationCounterfactual",
    "E4ActualizationResourcePolicy", "E4HistoricalObserverSource",
    "E4CounterfactualEvidence", "E4HistoricalActualizationJudgment",
    "E4ActualizationResourceLimit", "E4ActualizationSourceResult",
    "E4ActualizationResult", "e4_actualization_resource_policy",
    "e4_history_event", "e4_access_edge", "e4_historical_assumption",
    "e4_actualization_counterfactual", "e4_historical_observer_source",
    "e4_historical_actualization_judgment",
    "e4_validate_actualization_result",
)
