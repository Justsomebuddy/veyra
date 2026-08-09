"""Exact source, scope, translation, and policy snapshots for P1-A2."""

from __future__ import annotations

import logging

from ..morphism import ObserverSourceBinding
from .digest import (
    proposal_digest, scope_digest, source_digest, stage_commitment,
)
from .types import (
    ComparisonMode, ObserverRelationScope, PairKey,
    RelationEvaluationSource, RelationStage, StageKey, TranslationProposal,
)
from ...ontology.types import ObserverDoctrine
from ...proof_core_types import CoreTerm
from .validation import (
    MAX_RELATION_STAGES, RELATION_SOURCE_VERSION,
    digest64, identifier, kinds_equal,
    projected_kind, projection, reject, snapshot_recurrence,
    snapshot_relation_binding, snapshot_relation_doctrine,
)

logger = logging.getLogger(__name__)


def relation_evaluation_source(
    doctrine: ObserverDoctrine, binding: ObserverSourceBinding,
    stages: tuple[tuple[str, CoreTerm], ...],
    *, version: str = RELATION_SOURCE_VERSION,
) -> RelationEvaluationSource:
    """Construct an exact ordered stage source from raw recurrences."""
    logger.debug("relation_evaluation_source entry")
    doctrine = snapshot_relation_doctrine(doctrine)
    binding = snapshot_relation_binding(binding, doctrine)
    version = identifier(version, "relation-source-version")
    if version != RELATION_SOURCE_VERSION or type(stages) is not tuple:
        reject("invalid-relation-stage-source")
    if not 1 <= len(stages) <= MAX_RELATION_STAGES:
        reject("relation-stage-count-limit")
    captured: list[RelationStage] = []
    for item in stages:
        if type(item) is not tuple or len(item) != 2:
            reject("invalid-relation-stage-entry")
        stage_id = identifier(item[0], "relation-stage-id")
        recurrence, canonical = snapshot_recurrence(item[1])
        commitment = stage_commitment(version, stage_id, canonical)
        captured.append(RelationStage(stage_id, recurrence, commitment))
    if len({item.stage_id for item in captured}) != len(captured):
        reject("duplicate-relation-stage-id")
    commitments = tuple(item.commitment for item in captured)
    if len(set(commitments)) != len(commitments):
        reject("duplicate-relation-stage-commitment")
    frozen = tuple(captured)
    digest = source_digest(
        doctrine.fingerprint, binding.membership_digest, version, frozen,
    )
    result = RelationEvaluationSource(
        doctrine.fingerprint, frozen, commitments, binding.membership_digest,
        version, digest,
    )
    logger.debug("relation_evaluation_source exit stages=%d", len(frozen))
    return result


def snapshot_stage_source(
    value: RelationEvaluationSource, doctrine: ObserverDoctrine,
    binding: ObserverSourceBinding,
) -> RelationEvaluationSource:
    """Rebuild an exact stage source and reject mutation or transplant."""
    logger.debug("snapshot_stage_source entry")
    doctrine = snapshot_relation_doctrine(doctrine)
    binding = snapshot_relation_binding(binding, doctrine)
    if type(value) is not RelationEvaluationSource:
        reject("relation-stage-source-must-be-exact")
    try:
        doctrine_fp, stages, commitments = (
            value.doctrine_fingerprint, value.stages, value.ordered_commitments,
        )
        observer_digest, version, supplied = (
            value.observer_source_digest, value.version, value.source_digest,
        )
    except AttributeError:
        reject("relation-stage-source-missing-fields")
    if (
        type(stages) is not tuple or not 1 <= len(stages) <= MAX_RELATION_STAGES
        or type(commitments) is not tuple or len(commitments) != len(stages)
        or type(doctrine_fp) is not str or type(observer_digest) is not str
        or type(version) is not str or type(supplied) is not str
        or doctrine_fp != doctrine.fingerprint
        or observer_digest != binding.membership_digest
        or version != RELATION_SOURCE_VERSION
    ):
        reject("relation-stage-source-binding-drift")
    rebuilt: list[RelationStage] = []
    for index, item in enumerate(stages):
        if type(item) is not RelationStage:
            reject("relation-stage-must-be-exact")
        try:
            stage_id, recurrence, commitment = (
                item.stage_id, item.recurrence, item.commitment,
            )
        except AttributeError:
            reject("relation-stage-missing-fields")
        stage_id = identifier(stage_id, "relation-stage-id")
        recurrence, canonical = snapshot_recurrence(recurrence)
        expected = stage_commitment(version, stage_id, canonical)
        commitment = digest64(commitment, "stage-commitment")
        ordered = digest64(commitments[index], "ordered-stage-commitment")
        if commitment != expected or ordered != expected:
            reject("relation-stage-commitment-drift")
        rebuilt.append(RelationStage(stage_id, recurrence, expected))
    frozen = tuple(rebuilt)
    if (
        len({item.stage_id for item in frozen}) != len(frozen)
        or len({item.commitment for item in frozen}) != len(frozen)
    ):
        reject("duplicate-relation-stage")
    expected_digest = source_digest(
        doctrine.fingerprint, binding.membership_digest, version, frozen,
    )
    if supplied != expected_digest:
        reject("relation-stage-source-digest-drift")
    result = RelationEvaluationSource(
        doctrine.fingerprint, frozen, tuple(item.commitment for item in frozen),
        binding.membership_digest, version, expected_digest,
    )
    logger.debug("snapshot_stage_source exit stages=%d", len(frozen))
    return result


def observer_relation_scope(
    doctrine: ObserverDoctrine, binding: ObserverSourceBinding,
    source: RelationEvaluationSource, fine_observer_id: str,
    coarse_observer_id: str, stages: tuple[StageKey, ...],
    mode: ComparisonMode,
) -> ObserverRelationScope:
    """Construct the exact full ordered Cartesian relation scope."""
    logger.debug("observer_relation_scope entry")
    doctrine = snapshot_relation_doctrine(doctrine)
    binding = snapshot_relation_binding(binding, doctrine)
    source = snapshot_stage_source(source, doctrine, binding)
    fine_id = identifier(fine_observer_id, "fine-observer-id")
    coarse_id = identifier(coarse_observer_id, "coarse-observer-id")
    if fine_id == coarse_id or fine_id not in binding.observer_ids or coarse_id not in binding.observer_ids:
        reject("invalid-relation-observer-pair")
    available = tuple((item.stage_id, item.commitment) for item in source.stages)
    captured = _stage_keys(stages)
    positions = {item: index for index, item in enumerate(available)}
    if (
        any(item not in positions for item in captured)
        or tuple(positions[item] for item in captured)
        != tuple(sorted(positions[item] for item in captured))
        or len(set(captured)) != len(captured)
        or type(mode) is not ComparisonMode
    ):
        reject("relation-scope-stage-order-or-mode-drift")
    pairs = _cartesian(captured)
    digest = scope_digest(
        doctrine.fingerprint, binding.membership_digest, source.source_digest,
        fine_id, coarse_id, captured, mode,
    )
    result = ObserverRelationScope(
        doctrine.fingerprint, binding.membership_digest, source.source_digest,
        fine_id, coarse_id, captured, pairs, mode, digest,
    )
    logger.debug("observer_relation_scope exit pairs=%d", len(pairs))
    return result


def snapshot_scope(
    value: ObserverRelationScope, doctrine: ObserverDoctrine,
    binding: ObserverSourceBinding, source: RelationEvaluationSource,
) -> ObserverRelationScope:
    """Reconstruct and compare an exact relation scope including all pairs."""
    logger.debug("snapshot_scope entry")
    if type(value) is not ObserverRelationScope:
        reject("relation-scope-must-be-exact")
    try:
        result = observer_relation_scope(
            doctrine, binding, source, value.fine_observer_id,
            value.coarse_observer_id, value.stages, value.mode,
        )
        supplied_pairs, supplied_digest = value.ordered_pairs, value.scope_digest
        outer = (
            value.doctrine_fingerprint, value.observer_source_digest,
            value.stage_source_digest,
        )
    except AttributeError:
        reject("relation-scope-missing-fields")
    if type(supplied_pairs) is not tuple or len(supplied_pairs) != len(result.ordered_pairs):
        reject("relation-scope-drift-or-incomplete-pairs")
    captured_pairs = _pair_keys(supplied_pairs)
    expected_outer = (
        result.doctrine_fingerprint, result.observer_source_digest,
        result.stage_source_digest,
    )
    if (
        any(type(item) is not str for item in (*outer, supplied_digest))
        or outer != expected_outer or captured_pairs != result.ordered_pairs
        or supplied_digest != result.scope_digest
    ):
        reject("relation-scope-drift-or-incomplete-pairs")
    logger.debug("snapshot_scope exit pairs=%d", len(result.ordered_pairs))
    return result


def translation_proposal(
    doctrine: ObserverDoctrine, binding: ObserverSourceBinding, proposal_id: str,
    fine_id: str, coarse_id: str, steps: tuple,
) -> TranslationProposal:
    """Construct one response-kind-correct proposal without factorization."""
    logger.debug("translation_proposal entry")
    doctrine = snapshot_relation_doctrine(doctrine)
    binding = snapshot_relation_binding(binding, doctrine)
    proposal_id = identifier(proposal_id, "proposal-id")
    fine_id, coarse_id = identifier(fine_id, "fine-observer-id"), identifier(coarse_id, "coarse-observer-id")
    steps = projection(steps)
    members = {item.observer_id: item for item in doctrine.observers}
    if fine_id not in binding.observer_ids or coarse_id not in binding.observer_ids:
        reject("proposal-observer-source-unbound")
    if not kinds_equal(projected_kind(members[fine_id].response_kind, steps), members[coarse_id].response_kind):
        reject("proposal-endpoint-kind-mismatch")
    digest = proposal_digest(
        proposal_id, doctrine.fingerprint, binding.membership_digest,
        fine_id, coarse_id, tuple(item.value for item in steps),
    )
    result = TranslationProposal(
        proposal_id, fine_id, coarse_id, steps, doctrine.fingerprint,
        binding.membership_digest, digest,
    )
    logger.debug("translation_proposal exit steps=%d", len(steps))
    return result


def _stage_keys(value: tuple[StageKey, ...]) -> tuple[StageKey, ...]:
    """Capture exact ordered source keys without accepting duck tuples."""
    logger.debug("relation stage_keys entry")
    if type(value) is not tuple or not 1 <= len(value) <= MAX_RELATION_STAGES:
        reject("invalid-relation-stage-keys")
    result: list[StageKey] = []
    for item in value:
        if type(item) is not tuple or len(item) != 2:
            reject("invalid-relation-stage-key")
        result.append((identifier(item[0], "relation-stage-id"), digest64(item[1], "stage-commitment")))
    frozen = tuple(result)
    logger.debug("relation stage_keys exit count=%d", len(frozen))
    return frozen


def _cartesian(stages: tuple[StageKey, ...]) -> tuple[PairKey, ...]:
    """Derive the complete ordered Cartesian pair universe including diagonal."""
    logger.debug("relation cartesian entry stages=%d", len(stages))
    result = tuple((left, right) for left in stages for right in stages)
    logger.debug("relation cartesian exit pairs=%d", len(result))
    return result


def _pair_keys(value: tuple[PairKey, ...]) -> tuple[PairKey, ...]:
    """Capture a bounded exact pair universe without trusting nested equality."""
    logger.debug("relation pair_keys entry")
    if type(value) is not tuple or len(value) > MAX_RELATION_STAGES**2:
        reject("invalid-relation-pair-keys")
    result: list[PairKey] = []
    for item in value:
        if type(item) is not tuple or len(item) != 2:
            reject("invalid-relation-pair-key")
        left = _stage_keys((item[0],))[0]
        right = _stage_keys((item[1],))[0]
        result.append((left, right))
    frozen = tuple(result)
    logger.debug("relation pair_keys exit count=%d", len(frozen))
    return frozen
