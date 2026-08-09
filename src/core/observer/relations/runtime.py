"""Preflight-first P1-A2 relation judgment runtime."""

from __future__ import annotations

from dataclasses import replace
import logging

from ..morphism import ObserverSourceBinding
from .digest import judgment_digest
from .laws import (
    coverage_status, domain_equality_law, information_loss_status,
    preservation_law, reflection_law, relation_classification,
)
from .preflight import (
    preflight, relation_resource_policy, request_cost, snapshot_request,
)
from .replay import replay_pair_rows, replay_stage_rows
from .types import (
    ObserverRelationResult, RelationResourcePolicy,
)
from .triangles import assess_translation
from .types import (
    InvertibilityStatus, LawStatus, ObserverRelationJudgment,
    ObserverRelationScope, RelationEvaluationSource, TranslationInput,
    OBSERVER_RELATION_NONCLAIMS,
)
from ...ontology.types import ObserverDoctrine

logger = logging.getLogger(__name__)


def observer_relation_judgment(
    doctrine: ObserverDoctrine, raw_observer_source: ObserverSourceBinding,
    raw_stage_source: RelationEvaluationSource, raw_scope: ObserverRelationScope,
    forward: TranslationInput | None = None,
    reverse: TranslationInput | None = None,
    policy: RelationResourcePolicy | None = None,
) -> ObserverRelationResult:
    """Replay exact finite relation laws after a no-partial-work preflight."""
    logger.debug("observer_relation_judgment entry")
    selected_policy = relation_resource_policy() if policy is None else policy
    doctrine, request = snapshot_request(
        doctrine, raw_observer_source, raw_stage_source, raw_scope,
        forward, reverse, selected_policy,
    )
    refusal = preflight(request)
    if refusal is not None:
        logger.debug("observer_relation_judgment exit resource-limit")
        return refusal
    stages = replay_stage_rows(doctrine, request)
    pairs = replay_pair_rows(stages)
    preservation, preservation_witness = preservation_law(pairs)
    reflection, reflection_witness = reflection_law(pairs)
    domain_equality, domain_witness = domain_equality_law(
        tuple(item.row for item in stages),
    )
    forward_result = assess_translation(doctrine, request, request.forward, stages)
    reverse_result = assess_translation(doctrine, request, request.reverse, stages)
    classification = relation_classification(
        preservation, reflection, domain_equality,
    )
    loss = information_loss_status(
        forward_result, preservation, reflection, domain_equality,
    )
    provisional = ObserverRelationJudgment(
        request.scope.doctrine_fingerprint, request.scope.observer_source_digest,
        request.scope.stage_source_digest, request.scope.scope_digest,
        tuple(item.row for item in stages), pairs, preservation, reflection,
        domain_equality, preservation_witness, reflection_witness, domain_witness,
        classification, forward_result, reverse_result,
        InvertibilityStatus.NOT_ESTABLISHED, loss,
        coverage_status(tuple(item.row for item in stages)), request_cost(request),
        LawStatus.OPEN, LawStatus.OPEN, OBSERVER_RELATION_NONCLAIMS, "",
    )
    result = replace(provisional, judgment_digest=judgment_digest(provisional))
    logger.debug(
        "observer_relation_judgment exit class=%s", result.classification.value,
    )
    return result


def replay_observer_relation(
    doctrine: ObserverDoctrine, raw_observer_source: ObserverSourceBinding,
    raw_stage_source: RelationEvaluationSource, raw_scope: ObserverRelationScope,
    forward: TranslationInput | None = None,
    reverse: TranslationInput | None = None,
    policy: RelationResourcePolicy | None = None,
) -> ObserverRelationResult:
    """Expose the same raw-only replay boundary without prior artifacts."""
    logger.debug("replay_observer_relation entry")
    result = observer_relation_judgment(
        doctrine, raw_observer_source, raw_stage_source, raw_scope,
        forward, reverse, policy,
    )
    logger.debug("replay_observer_relation exit type=%s", type(result).__name__)
    return result
