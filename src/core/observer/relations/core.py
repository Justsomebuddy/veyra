"""Public P1-A2.1/A2.2 exact finite observer-relation API."""

from __future__ import annotations

import logging

from .preflight import relation_resource_policy
from .request import (
    observer_relation_scope, relation_evaluation_source, translation_proposal,
)
from .types import (
    ObserverRelationResult, RelationOperation, RelationResourceLimit,
    RelationResourcePolicy, RelationResultStatus,
)
from .result_validation import validate_observer_relation_result
from .runtime import (
    observer_relation_judgment, replay_observer_relation,
)
from .translation import morphism_replay_spec
from .types import (
    ComparisonMode, CoverageStatus, DomainWitness, InvertibilityStatus,
    LawStatus, LossStatus, MorphismEvidenceStatus, MorphismReplaySpec,
    ObserverRelationJudgment, ObserverRelationScope, PairOutcome,
    ProposalStatus, RelationClass, RelationEvaluationSource, RelationPairRow,
    RelationRunStatus, RelationStage, RelationWitness, StageObservationRow,
    TranslationAssessment, TranslationProposal, TranslationTriangleRow,
    TranslationInputKind,
    OBSERVER_RELATION_NONCLAIMS,
)
from .validation import ObserverRelationValidationError

logger = logging.getLogger(__name__)

__all__ = [
    "ComparisonMode", "CoverageStatus", "DomainWitness", "InvertibilityStatus",
    "LawStatus", "LossStatus", "MorphismEvidenceStatus", "MorphismReplaySpec",
    "ObserverRelationJudgment", "ObserverRelationResult", "ObserverRelationScope",
    "ObserverRelationValidationError", "PairOutcome", "ProposalStatus",
    "RelationClass", "RelationEvaluationSource", "RelationOperation",
    "RelationPairRow", "RelationResourceLimit", "RelationResourcePolicy",
    "RelationResultStatus", "RelationRunStatus", "RelationStage",
    "RelationWitness", "StageObservationRow", "TranslationAssessment",
    "TranslationProposal", "TranslationTriangleRow", "morphism_replay_spec",
    "TranslationInputKind",
    "OBSERVER_RELATION_NONCLAIMS",
    "observer_relation_judgment", "observer_relation_scope",
    "observer_relations_scope_boundary",
    "relation_evaluation_source", "relation_resource_policy",
    "replay_observer_relation", "translation_proposal",
    "validate_observer_relation_result",
]


def observer_relations_scope_boundary() -> tuple[str, ...]:
    """Expose permanent A2.1/A2.2 nonclaims without promoting them."""
    logger.debug("observer_relations_scope_boundary entry")
    result = OBSERVER_RELATION_NONCLAIMS
    logger.debug("observer_relations_scope_boundary exit rows=%d", len(result))
    return result
