"""Level-1 executable certificate for P1-A2.1/A2.2 observer relations."""

from __future__ import annotations

import logging

from ..certify_types import Certificate
from ..observer.morphism import (
    ProjectionStep, observer_source_binding, p1a_observer_morphism_doctrine,
)
from ..observer.relations.core import (
    ComparisonMode, InvertibilityStatus, LawStatus, LossStatus,
    MorphismEvidenceStatus, ObserverRelationJudgment, ProposalStatus,
    RelationClass, RelationResourceLimit, morphism_replay_spec,
    observer_relation_judgment, observer_relation_scope,
    relation_evaluation_source, relation_resource_policy,
    validate_observer_relation_result,
)
from ..proof_core_types import Pulse, Silence

logger = logging.getLogger(__name__)


def _recurrence(depth: int):
    """Construct one exact finite certificate recurrence."""
    logger.debug("observer relation certificate recurrence entry depth=%d", depth)
    value = Silence()
    for _ in range(depth):
        value = Pulse(value)
    logger.debug("observer relation certificate recurrence exit depth=%d", depth)
    return value


def _fixture(fine: str, coarse: str, mode: ComparisonMode):
    """Build one fixed doctrine/source/scope certificate fixture."""
    logger.debug("observer relation certificate fixture entry")
    doctrine = p1a_observer_morphism_doctrine()
    binding = observer_source_binding(
        doctrine, "p1a2-certificate-source",
        tuple(item.observer_id for item in doctrine.observers),
    )
    source = relation_evaluation_source(
        doctrine, binding,
        (("d0", _recurrence(0)), ("d1", _recurrence(1)), ("d2", _recurrence(2))),
    )
    keys = tuple((item.stage_id, item.commitment) for item in source.stages)
    scope = observer_relation_scope(
        doctrine, binding, source, fine, coarse, keys, mode,
    )
    logger.debug("observer relation certificate fixture exit")
    return doctrine, binding, source, scope


def certify_observer_relations_p1a2() -> Certificate:
    """Certify finite law replay, classification, loss separation, and refusal."""
    logger.debug("certify_observer_relations_p1a2 entry")
    doctrine, binding, source, scope = _fixture(
        "fine-total", "coarse-crest", ComparisonMode.WITH_P1A_REPLAY,
    )
    forward = morphism_replay_spec(
        "certificate-projection", "fine-total", "coarse-crest",
        (ProjectionStep.LEFT,),
    )
    refinement = observer_relation_judgment(
        doctrine, binding, source, scope, forward,
    )
    reverse_fixture = _fixture(
        "coarse-crest", "fine-total", ComparisonMode.EXTENSIONAL_ONLY,
    )
    coarsening = observer_relation_judgment(*reverse_fixture)
    equivalent_fixture = _fixture(
        "fine-total", "fine-nested", ComparisonMode.EXTENSIONAL_ONLY,
    )
    equivalent = observer_relation_judgment(*equivalent_fixture)
    policy = relation_resource_policy(max_cost=0)
    refusal = observer_relation_judgment(
        doctrine, binding, source, scope, forward, policy=policy,
    )
    fresh = validate_observer_relation_result(
        doctrine, binding, source, scope, forward, None,
        relation_resource_policy(), refinement,
    )
    passed = (
        isinstance(refinement, ObserverRelationJudgment)
        and refinement.preservation is LawStatus.ESTABLISHED
        and refinement.reflection is LawStatus.REFUTED
        and refinement.domain_equality is LawStatus.ESTABLISHED
        and refinement.classification is RelationClass.STRICT_REFINEMENT_ON_SCOPE
        and refinement.forward.morphism_status is MorphismEvidenceStatus.P1A_ESTABLISHED
        and refinement.forward.proposal_status is ProposalStatus.COMMUTES_ON_SCOPE
        and refinement.information_loss is LossStatus.LOSSY_ON_SCOPE
        and refinement.structural_invertibility is InvertibilityStatus.NOT_ESTABLISHED
        and len(refinement.pairs) == 9
        and isinstance(coarsening, ObserverRelationJudgment)
        and coarsening.classification is RelationClass.STRICT_COARSENING_ON_SCOPE
        and isinstance(equivalent, ObserverRelationJudgment)
        and equivalent.classification is RelationClass.EQUIVALENT_ON_SCOPE
        and equivalent.information_loss is LossStatus.NOT_ESTABLISHED
        and isinstance(refusal, RelationResourceLimit)
        and refusal.observer_independent_identity is LawStatus.OPEN
        and refusal.universal_refinement is LawStatus.OPEN
        and fresh == refinement and fresh is not refinement
    )
    method = (
        "exact finite source/scope binding, complete ordered Cartesian replay, "
        "independent preservation/reflection/domain laws, raw P1-A triangles, "
        "proposal-conflict separation, preflight refusal, and fresh revalidation; "
        "no universal order, off-scope equivalence, chronology, inverse law, "
        "completed infinity, consciousness, physical realization, R8, layer, or Sage promotion"
    )
    detail = (
        "strict refinement/coarsening/equivalence separated; structural loss requires "
        "freshly replayed P1-A evidence; invertibility remains NOT_ESTABLISHED"
    )
    result = Certificate("observer_relations_p1a2", method, passed, detail, 1)
    logger.debug("certify_observer_relations_p1a2 exit result=%r", result)
    return result
