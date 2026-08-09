"""Collision-safe root aliases for released finite P3-T observer networks."""

from __future__ import annotations

from . import core as _p3t

P3T_NETWORK_VERSION = _p3t.NETWORK_VERSION
P3T_NONCLAIMS = _p3t.NONCLAIMS
P3TObserverNetworkError = _p3t.ObserverNetworkError
P3TObserverSourceBinding = _p3t.ObserverSourceBinding
P3TProjectionStep = _p3t.ProjectionStep
P3TPairOutcome = _p3t.PairOutcome
P3TRelationEvaluationSource = _p3t.RelationEvaluationSource
P3TObserverDoctrine = _p3t.ObserverDoctrine
P3TResponseStatus = _p3t.ResponseStatus
P3TLawStatus = _p3t.LawStatus
P3TRefinementStatus = _p3t.RefinementStatus
P3TTriangleStatus = _p3t.TriangleStatus
P3TNetworkResourcePolicy = _p3t.NetworkResourcePolicy
P3TRawObserverPairSource = _p3t.RawObserverPairSource
P3TInputSnapshot = _p3t.InputSnapshot
P3TTypedValue = _p3t.TypedValue
P3TResponse = _p3t.Response
P3TObservationRow = _p3t.ObservationRow
P3TGrammarDescriptor = _p3t.GrammarDescriptor
P3TObserverSource = _p3t.ObserverSource
P3TTranslationRow = _p3t.TranslationRow
P3TTranslationSource = _p3t.TranslationSource
P3TTriangleDemand = _p3t.TriangleDemand
P3TObserverNetworkSource = _p3t.ObserverNetworkSource
P3TPartialMap = _p3t.PartialMap
P3TEvaluationDomainJudgment = _p3t.EvaluationDomainJudgment
P3TRelationReplayRow = _p3t.RelationReplayRow
P3TEdgeJudgment = _p3t.EdgeJudgment
P3TIsomorphismJudgment = _p3t.IsomorphismJudgment
P3TCompositionJudgment = _p3t.CompositionJudgment
P3TIdentityLawJudgment = _p3t.IdentityLawJudgment
P3TObserverPairJudgment = _p3t.ObserverPairJudgment
P3TAssociativityJudgment = _p3t.AssociativityJudgment
P3TTriangleJudgment = _p3t.TriangleJudgment
P3TObserverNetworkJudgment = _p3t.ObserverNetworkJudgment

p3t_example_observer_network = _p3t.example_observer_network
p3t_network_resource_policy = _p3t.network_resource_policy
p3t_validate_observer_network_result = _p3t.validate_observer_network_result
p3t_observer_network_judgment = _p3t.observer_network_judgment
p3t_blocked = _p3t.blocked
p3t_grammar_descriptor = _p3t.grammar_descriptor
p3t_input_snapshot = _p3t.input_snapshot
p3t_observation_row = _p3t.observation_row
p3t_observer_network_source = _p3t.observer_network_source
p3t_observer_source = _p3t.observer_source
p3t_raw_observer_pair_source = _p3t.raw_observer_pair_source
p3t_ready = _p3t.ready
p3t_silent = _p3t.silent
p3t_translation_row = _p3t.translation_row
p3t_translation_source = _p3t.translation_source
p3t_triangle_demand = _p3t.triangle_demand
p3t_typed_value = _p3t.typed_value
p3t_snapshot_network_source = _p3t.snapshot_network_source

__all__ = (
    "P3T_NETWORK_VERSION", "P3T_NONCLAIMS", "P3TObserverNetworkError",
    "P3TObserverSourceBinding", "P3TProjectionStep", "P3TPairOutcome",
    "P3TRelationEvaluationSource", "P3TObserverDoctrine", "P3TResponseStatus",
    "P3TLawStatus", "P3TRefinementStatus", "P3TTriangleStatus",
    "P3TNetworkResourcePolicy", "P3TRawObserverPairSource", "P3TInputSnapshot",
    "P3TTypedValue", "P3TResponse", "P3TObservationRow", "P3TGrammarDescriptor",
    "P3TObserverSource", "P3TTranslationRow", "P3TTranslationSource",
    "P3TTriangleDemand", "P3TObserverNetworkSource", "P3TPartialMap",
    "P3TEvaluationDomainJudgment", "P3TRelationReplayRow", "P3TEdgeJudgment",
    "P3TIsomorphismJudgment", "P3TCompositionJudgment", "P3TIdentityLawJudgment",
    "P3TObserverPairJudgment", "P3TAssociativityJudgment", "P3TTriangleJudgment",
    "P3TObserverNetworkJudgment", "p3t_example_observer_network",
    "p3t_network_resource_policy", "p3t_validate_observer_network_result",
    "p3t_observer_network_judgment", "p3t_blocked", "p3t_grammar_descriptor",
    "p3t_input_snapshot", "p3t_observation_row", "p3t_observer_network_source",
    "p3t_observer_source", "p3t_raw_observer_pair_source", "p3t_ready",
    "p3t_silent", "p3t_translation_row", "p3t_translation_source",
    "p3t_triangle_demand", "p3t_typed_value", "p3t_snapshot_network_source",
)
