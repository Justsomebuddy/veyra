"""Versioned resource policy and pre-semantic preflight for P1-A2."""

from __future__ import annotations

from dataclasses import replace
import logging

from ..morphism import ObserverSourceBinding
from .digest import policy_digest, refusal_digest
from .request import snapshot_scope, snapshot_stage_source
from .types import (
    RelationOperation, RelationRequest, RelationResourceLimit,
    RelationResourcePolicy, RelationResultStatus,
)
from .translation import (
    snapshot_translation_input, validate_translation_kinds,
    validate_translation_mode,
)
from .types import (
    LawStatus, MorphismReplaySpec, ObserverRelationScope,
    RelationEvaluationSource, TranslationInput, TranslationProposal,
    OBSERVER_RELATION_NONCLAIMS,
)
from ...ontology.types import ObserverDoctrine
from .validation import (
    MAX_RELATION_SOURCE_BYTES, digest64, natural, reject, snapshot_recurrence,
    snapshot_relation_binding, snapshot_relation_doctrine,
)

logger = logging.getLogger(__name__)
POLICY_VERSION = "p1a2-policy-v1"


def relation_resource_policy(
    *, max_cost: int = 2048, max_encoded_bytes: int = MAX_RELATION_SOURCE_BYTES,
) -> RelationResourcePolicy:
    """Construct one exact versioned and digest-bound policy."""
    logger.debug("relation_resource_policy entry")
    max_cost = natural(max_cost, "relation-max-cost", 1_000_000)
    max_encoded_bytes = natural(
        max_encoded_bytes, "relation-max-encoded-bytes", MAX_RELATION_SOURCE_BYTES,
    )
    digest = policy_digest(POLICY_VERSION, max_cost, max_encoded_bytes)
    result = RelationResourcePolicy(
        POLICY_VERSION, max_cost, max_encoded_bytes, digest,
    )
    logger.debug("relation_resource_policy exit")
    return result


def snapshot_policy(value: RelationResourcePolicy) -> RelationResourcePolicy:
    """Recompute the exact policy digest instead of trusting dataclass defaults."""
    logger.debug("snapshot_relation_policy entry")
    if type(value) is not RelationResourcePolicy:
        reject("relation-policy-must-be-exact")
    try:
        version, max_cost, max_bytes, supplied = (
            value.version, value.max_cost, value.max_encoded_bytes,
            value.policy_digest,
        )
    except AttributeError:
        reject("relation-policy-missing-fields")
    if type(version) is not str or version != POLICY_VERSION:
        reject("relation-policy-version-drift")
    max_cost = natural(max_cost, "relation-max-cost", 1_000_000)
    max_bytes = natural(
        max_bytes, "relation-max-encoded-bytes", MAX_RELATION_SOURCE_BYTES,
    )
    supplied = digest64(supplied, "relation-policy-digest")
    expected = policy_digest(version, max_cost, max_bytes)
    if supplied != expected:
        reject("relation-policy-digest-drift")
    result = RelationResourcePolicy(version, max_cost, max_bytes, expected)
    logger.debug("snapshot_relation_policy exit")
    return result


def snapshot_request(
    doctrine: ObserverDoctrine, binding: ObserverSourceBinding,
    raw_source: RelationEvaluationSource, raw_scope: ObserverRelationScope,
    forward: TranslationInput | None, reverse: TranslationInput | None,
    policy: RelationResourcePolicy,
) -> tuple[ObserverDoctrine, RelationRequest]:
    """Snapshot every structural input before any R11 or P1-A semantic call."""
    logger.debug("snapshot_relation_request entry")
    doctrine = snapshot_relation_doctrine(doctrine)
    binding = snapshot_relation_binding(binding, doctrine)
    source = snapshot_stage_source(raw_source, doctrine, binding)
    scope = snapshot_scope(raw_scope, doctrine, binding, source)
    forward = snapshot_translation_input(
        forward, scope.fine_observer_id, scope.coarse_observer_id,
        doctrine, binding,
    )
    reverse = snapshot_translation_input(
        reverse, scope.coarse_observer_id, scope.fine_observer_id,
        doctrine, binding,
    )
    if sum(
        len(item.projection) for item in (forward, reverse) if item is not None
    ) > 128:
        reject("relation-total-projection-step-limit")
    validate_translation_kinds(forward, doctrine, binding)
    validate_translation_kinds(reverse, doctrine, binding)
    validate_translation_mode(scope, forward, reverse)
    policy = snapshot_policy(policy)
    result = RelationRequest(binding, source, scope, forward, reverse, policy)
    logger.debug("snapshot_relation_request exit")
    return doctrine, result


def preflight(request: RelationRequest) -> RelationResourceLimit | None:
    """Charge the closed worst-case formula before any observer evaluation."""
    logger.debug("relation preflight entry")
    required_cost = request_cost(request)
    required_bytes = encoded_request_bytes(request)
    if (
        required_cost <= request.policy.max_cost
        and required_bytes <= request.policy.max_encoded_bytes
    ):
        logger.debug("relation preflight exit allowed cost=%d", required_cost)
        return None
    provisional = RelationResourceLimit(
        RelationOperation.JUDGE, RelationResultStatus.RESOURCE_LIMIT,
        request.policy.version, request.policy.policy_digest,
        request.scope.doctrine_fingerprint, request.scope.observer_source_digest,
        request.scope.stage_source_digest, request.scope.scope_digest,
        required_cost, request.policy.max_cost, required_bytes,
        request.policy.max_encoded_bytes, LawStatus.OPEN, LawStatus.OPEN,
        OBSERVER_RELATION_NONCLAIMS, "",
    )
    result = replace(provisional, refusal_digest=refusal_digest(provisional))
    logger.debug("relation preflight exit refused cost=%d", required_cost)
    return result


def request_cost(request: RelationRequest) -> int:
    """Compute the closed overflow-safe A2 cost formula."""
    logger.debug("relation request_cost entry")
    n = len(request.scope.stages)
    values = tuple(item for item in (request.forward, request.reverse) if item is not None)
    morphisms = sum(type(item) is MorphismReplaySpec for item in values)
    proposals = sum(type(item) is TranslationProposal for item in values)
    steps = sum(len(item.projection) for item in values)
    result = 2 * n + 2 * n * n + 6 * morphisms + (morphisms + proposals) * n + steps
    logger.debug("relation request_cost exit cost=%d", result)
    return result


def encoded_request_bytes(request: RelationRequest) -> int:
    """Compute the exact count-framed structural request envelope size."""
    logger.debug("encoded_request_bytes entry")
    tokens: list[bytes] = [
        request.scope.doctrine_fingerprint.encode(),
        request.scope.observer_source_digest.encode(),
        request.scope.stage_source_digest.encode(), request.scope.scope_digest.encode(),
        request.scope.fine_observer_id.encode(), request.scope.coarse_observer_id.encode(),
        request.scope.mode.value.encode(), request.policy.version.encode(),
        request.policy.policy_digest.encode(),
    ]
    for stage in request.source.stages:
        _, canonical = snapshot_recurrence(stage.recurrence)
        tokens.extend((stage.stage_id.encode(), stage.commitment.encode(), canonical))
    for stage_id, commitment in request.scope.stages:
        tokens.extend((stage_id.encode(), commitment.encode()))
    for item in (request.forward, request.reverse):
        if item is None:
            tokens.append(b"absent")
            continue
        identity = item.morphism_id if type(item) is MorphismReplaySpec else item.proposal_id
        tokens.extend((
            identity.encode(), item.fine_observer_id.encode(),
            item.coarse_observer_id.encode(),
            *(step.value.encode() for step in item.projection),
        ))
    result = 4 + sum(8 + len(item) for item in tokens)
    logger.debug("encoded_request_bytes exit bytes=%d", result)
    return result
