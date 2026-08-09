"""Raw P1-A replay and typed proposal validation for P1-A2."""

from __future__ import annotations

import logging

from ..morphism import ObserverSourceBinding
from .digest import proposal_digest
from .types import (
    ComparisonMode, MorphismReplaySpec, ObserverRelationScope,
    TranslationInput, TranslationProposal,
)
from ...ontology.types import ObserverDoctrine
from .validation import (
    digest64, identifier, kinds_equal, projected_kind, projection, reject,
    snapshot_relation_binding, snapshot_relation_doctrine,
)

logger = logging.getLogger(__name__)


def morphism_replay_spec(
    morphism_id: str, fine_observer_id: str, coarse_observer_id: str,
    steps: tuple,
) -> MorphismReplaySpec:
    """Construct one exact raw P1-A replay request."""
    logger.debug("morphism_replay_spec entry")
    result = MorphismReplaySpec(
        identifier(morphism_id, "morphism-id"),
        identifier(fine_observer_id, "fine-observer-id"),
        identifier(coarse_observer_id, "coarse-observer-id"), projection(steps),
    )
    logger.debug("morphism_replay_spec exit steps=%d", len(result.projection))
    return result


def snapshot_translation_input(
    value: TranslationInput | None, expected_fine: str, expected_coarse: str,
    doctrine: ObserverDoctrine, binding: ObserverSourceBinding,
) -> TranslationInput | None:
    """Validate one exact direction-bound raw replay spec or proposal."""
    logger.debug("snapshot_translation_input entry")
    doctrine = snapshot_relation_doctrine(doctrine)
    binding = snapshot_relation_binding(binding, doctrine)
    if value is None:
        logger.debug("snapshot_translation_input exit absent")
        return None
    if type(value) is MorphismReplaySpec:
        result: TranslationInput = _snapshot_morphism(value)
    elif type(value) is TranslationProposal:
        result = _snapshot_proposal(value, doctrine, binding)
    else:
        reject("translation-input-must-be-exact")
    if result.fine_observer_id != expected_fine or result.coarse_observer_id != expected_coarse:
        reject("translation-direction-drift")
    logger.debug("snapshot_translation_input exit type=%s", type(result).__name__)
    return result


def validate_translation_kinds(
    value: TranslationInput | None, doctrine: ObserverDoctrine,
    binding: ObserverSourceBinding,
) -> None:
    """Validate endpoint response kinds after aggregate projection preflight."""
    logger.debug("validate_translation_kinds entry type=%s", type(value).__name__)
    if value is None:
        logger.debug("validate_translation_kinds exit absent")
        return
    _validate_endpoint_kinds(value, doctrine, binding)
    logger.debug("validate_translation_kinds exit")


def _validate_endpoint_kinds(
    value: TranslationInput, doctrine: ObserverDoctrine,
    binding: ObserverSourceBinding,
) -> None:
    """Reject source-unbound or response-kind-invalid translation syntax."""
    logger.debug("validate_endpoint_kinds entry")
    members = {item.observer_id: item for item in doctrine.observers}
    if (
        value.fine_observer_id not in binding.observer_ids
        or value.coarse_observer_id not in binding.observer_ids
    ):
        reject("translation-observer-source-unbound")
    endpoint = projected_kind(
        members[value.fine_observer_id].response_kind, value.projection,
    )
    if not kinds_equal(endpoint, members[value.coarse_observer_id].response_kind):
        reason = (
            "morphism-replay-endpoint-kind-mismatch"
            if type(value) is MorphismReplaySpec
            else "proposal-endpoint-kind-mismatch"
        )
        reject(reason)
    logger.debug("validate_endpoint_kinds exit")


def validate_translation_mode(
    scope: ObserverRelationScope, forward: TranslationInput | None,
    reverse: TranslationInput | None,
) -> None:
    """Keep extensional, proposal, and theorem-replay modes disjoint."""
    logger.debug("validate_translation_mode entry mode=%s", scope.mode.value)
    values = tuple(item for item in (forward, reverse) if item is not None)
    if scope.mode is ComparisonMode.EXTENSIONAL_ONLY and values:
        reject("extensional-mode-rejects-translations")
    if scope.mode is ComparisonMode.WITH_PROPOSALS and any(
        type(item) is not TranslationProposal for item in values
    ):
        reject("proposal-mode-requires-proposals")
    if scope.mode is ComparisonMode.WITH_P1A_REPLAY and any(
        type(item) is not MorphismReplaySpec for item in values
    ):
        reject("p1a-mode-requires-raw-replay-specs")
    logger.debug("validate_translation_mode exit count=%d", len(values))


def _snapshot_morphism(value: MorphismReplaySpec) -> MorphismReplaySpec:
    """Snapshot exact raw P1-A syntax without accepting a prior judgment."""
    logger.debug("snapshot_morphism_replay entry")
    try:
        result = MorphismReplaySpec(
            identifier(value.morphism_id, "morphism-id"),
            identifier(value.fine_observer_id, "fine-observer-id"),
            identifier(value.coarse_observer_id, "coarse-observer-id"),
            projection(value.projection),
        )
    except AttributeError:
        reject("morphism-replay-spec-missing-fields")
    logger.debug("snapshot_morphism_replay exit steps=%d", len(result.projection))
    return result


def _snapshot_proposal(
    value: TranslationProposal, doctrine: ObserverDoctrine,
    binding: ObserverSourceBinding,
) -> TranslationProposal:
    """Revalidate exact source binding, kind endpoint, and proposal digest."""
    logger.debug("snapshot_relation_proposal entry")
    try:
        proposal_id = identifier(value.proposal_id, "proposal-id")
        fine_id = identifier(value.fine_observer_id, "fine-observer-id")
        coarse_id = identifier(value.coarse_observer_id, "coarse-observer-id")
        steps = projection(value.projection)
        doctrine_fp, source_fp, supplied = (
            value.doctrine_fingerprint, value.observer_source_digest,
            value.proposal_digest,
        )
    except AttributeError:
        reject("translation-proposal-missing-fields")
    if fine_id not in binding.observer_ids or coarse_id not in binding.observer_ids:
        reject("proposal-observer-source-unbound")
    doctrine_fp = digest64(doctrine_fp, "proposal-doctrine")
    source_fp = digest64(source_fp, "proposal-observer-source")
    supplied = digest64(supplied, "proposal-digest")
    if doctrine_fp != doctrine.fingerprint or source_fp != binding.membership_digest:
        reject("proposal-source-transplant")
    expected = proposal_digest(
        proposal_id, doctrine.fingerprint, binding.membership_digest,
        fine_id, coarse_id, tuple(item.value for item in steps),
    )
    if supplied != expected:
        reject("proposal-digest-drift")
    result = TranslationProposal(
        proposal_id, fine_id, coarse_id, steps, doctrine.fingerprint,
        binding.membership_digest, expected,
    )
    logger.debug("snapshot_relation_proposal exit steps=%d", len(steps))
    return result
