"""Fresh P1-A replay and independent proposal-triangle checks for P1-A2."""

from __future__ import annotations

from dataclasses import replace
import logging

from ...observer_core_types import Blocked, PairValue, Ready, ResponseValue
from ..morphism import (
    MorphismStatus, ResponseTranslation, observer_morphism_judgment,
    translate_response,
)
from .digest import (
    assessment_digest, response_payload_digest, translation_input_commitment,
    triangle_row_digest,
)
from .replay import StageReplay, observation_bytes
from .types import RelationRequest
from .types import (
    MorphismEvidenceStatus, MorphismReplaySpec, ProposalStatus,
    TranslationAssessment, TranslationInput, TranslationInputKind, TranslationProposal,
    TranslationTriangleRow,
)
from ...ontology.response import _snapshot_response
from ...ontology.types import ObserverDoctrine
from .validation import reject

logger = logging.getLogger(__name__)


def assess_translation(
    doctrine: ObserverDoctrine, request: RelationRequest,
    value: TranslationInput | None, stages: tuple[StageReplay, ...],
) -> TranslationAssessment:
    """Replay raw structural evidence or check a typed proposal independently."""
    logger.debug("assess_translation entry type=%s", type(value).__name__)
    input_kind, input_commitment = _input_provenance(request, value)
    if value is None:
        provisional = TranslationAssessment(
            input_kind, input_commitment, MorphismEvidenceStatus.ABSENT,
            ProposalStatus.ABSENT, (), None, "",
        )
        result = replace(provisional, translation_digest=assessment_digest(provisional))
        logger.debug("assess_translation exit absent")
        return result
    translation: ResponseTranslation | None = None
    morphism_status = MorphismEvidenceStatus.ABSENT
    if type(value) is MorphismReplaySpec:
        replayed = observer_morphism_judgment(
            doctrine, request.binding, value.morphism_id,
            value.fine_observer_id, value.coarse_observer_id, value.projection,
        )
        if (
            replayed.status in {MorphismStatus.STRONG, MorphismStatus.INFORMATION_ONLY}
            and replayed.information_factorizes_on_comparison
            and replayed.translation is not None
        ):
            morphism_status = MorphismEvidenceStatus.P1A_ESTABLISHED
            translation = replayed.translation
        else:
            provisional = TranslationAssessment(
                input_kind, input_commitment, MorphismEvidenceStatus.ABSENT,
                ProposalStatus.ABSENT, (), None, "",
            )
            result = replace(
                provisional, translation_digest=assessment_digest(provisional),
            )
            logger.debug("assess_translation exit replay-not-established")
            return result
    rows = _triangle_rows(doctrine, request, value, translation, stages)
    conflict = next(
        (item for item in rows if item.status is ProposalStatus.CONFLICT_ON_SCOPE), None,
    )
    if conflict is not None:
        status = ProposalStatus.CONFLICT_ON_SCOPE
    elif any(item.status is ProposalStatus.OPEN for item in rows):
        status = ProposalStatus.OPEN
    else:
        status = ProposalStatus.COMMUTES_ON_SCOPE
    provisional = TranslationAssessment(
        input_kind, input_commitment, morphism_status, status, rows, conflict, "",
    )
    result = replace(provisional, translation_digest=assessment_digest(provisional))
    logger.debug("assess_translation exit status=%s", status.value)
    return result


def _input_provenance(
    request: RelationRequest, value: TranslationInput | None,
) -> tuple[TranslationInputKind, str]:
    """Bind the exact raw translation variant and full source-relative identity."""
    logger.debug("relation input_provenance entry type=%s", type(value).__name__)
    if value is None:
        kind, identity, fine, coarse, steps, proposal_source = (
            TranslationInputKind.ABSENT, "", "", "", (), "",
        )
    elif type(value) is MorphismReplaySpec:
        kind, identity, fine, coarse, steps, proposal_source = (
            TranslationInputKind.P1A_REPLAY, value.morphism_id,
            value.fine_observer_id, value.coarse_observer_id,
            tuple(item.value for item in value.projection), "",
        )
    elif type(value) is TranslationProposal:
        kind, identity, fine, coarse, steps, proposal_source = (
            TranslationInputKind.PROPOSAL, value.proposal_id,
            value.fine_observer_id, value.coarse_observer_id,
            tuple(item.value for item in value.projection), value.proposal_digest,
        )
    else:
        reject("unknown-translation-input-provenance")
    commitment = translation_input_commitment(
        kind, request.scope.doctrine_fingerprint,
        request.scope.observer_source_digest, identity, fine, coarse,
        steps, proposal_source,
    )
    logger.debug("relation input_provenance exit kind=%s", kind.value)
    return kind, commitment


def _triangle_rows(
    doctrine: ObserverDoctrine, request: RelationRequest,
    value: TranslationInput, translation: ResponseTranslation | None,
    stages: tuple[StageReplay, ...],
) -> tuple[TranslationTriangleRow, ...]:
    """Check every exact in-scope response triangle in source order."""
    logger.debug("relation triangle_rows entry stages=%d", len(stages))
    forward = value.fine_observer_id == request.scope.fine_observer_id
    output: list[TranslationTriangleRow] = []
    for index, stage in enumerate(stages):
        fine = stage.fine if forward else stage.coarse
        coarse = stage.coarse if forward else stage.fine
        fine_digest = (
            stage.row.fine_payload_digest if forward else stage.row.coarse_payload_digest
        )
        coarse_digest = (
            stage.row.coarse_payload_digest if forward else stage.row.fine_payload_digest
        )
        translated_digest = ""
        if type(fine) is Blocked or type(coarse) is Blocked:
            status = ProposalStatus.OPEN
        elif type(fine) is Ready and type(coarse) is Ready:
            translated = (
                translate_response(doctrine, request.binding, translation, fine.value)
                if translation is not None
                else _project_value(fine.value, value)
            )
            translated_bytes = observation_bytes(Ready(translated))
            translated_digest = response_payload_digest(translated_bytes)
            status = (
                ProposalStatus.COMMUTES_ON_SCOPE
                if translated_bytes == observation_bytes(coarse)
                else ProposalStatus.CONFLICT_ON_SCOPE
            )
        else:
            reject("malformed-relation-triangle-observation")
        provisional = TranslationTriangleRow(
            index, stage.row.stage, status, fine_digest, translated_digest,
            coarse_digest, "",
        )
        output.append(replace(provisional, row_digest=triangle_row_digest(provisional)))
    result = tuple(output)
    logger.debug("relation triangle_rows exit rows=%d", len(result))
    return result


def _project_value(value: ResponseValue, proposal: TranslationProposal) -> ResponseValue:
    """Apply only the already kind-checked closed proposal projection."""
    logger.debug("relation project_value entry steps=%d", len(proposal.projection))
    cursor = _snapshot_response(value)
    for step in proposal.projection:
        if type(cursor) is not PairValue:
            reject("proposal-runtime-shape-mismatch")
        cursor = cursor.left if step.value == "left" else cursor.right
    result = _snapshot_response(cursor)
    logger.debug("relation project_value exit")
    return result
