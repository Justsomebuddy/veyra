"""Bounded executable P0 judgments over closed R11 observers."""

from __future__ import annotations

import logging

from ..observer_core_codec import (
    ObserverCodecError,
    canonical_observer_bytes,
    decode_observer,
)
from ..observer_core_semantics import (
    ObserverCoreError,
    echo,
    infer_observer_kind,
    observe,
)
from ..observer_core_types import Blocked, DomainBlocked, Echo, Mismatch, Ready
from .doctrine import (
    snapshot_observer_doctrine,
    stage_commitment,
)
from .response import observation_data, response_modalities
from .observer import snapshot_observer_program
from .types import (
    ContinuationWitness, ObserverSupportJudgment, ObserverSupport,
    FamilyExtensionJudgment, InternalObserver, MetalanguageBoundary,
    ObserverDoctrine, OntologyPresentation, OntologyStage, PersistenceJudgment,
    PresentationCommitment, RelationObstruction,
    RelationStatus, RunJudgment, RunStatus, SilenceModality,
)
from .validation import (
    PositiveOntologyValidationError, snapshot_identifier,
    snapshot_internal_observer, snapshot_ontology_presentation,
    snapshot_ontology_stage, snapshot_recurrence,
)
from ..proof_core_types import CoreTerm, Silence

logger = logging.getLogger(__name__)


def metalanguage_boundary() -> MetalanguageBoundary:
    """State where P0 deliberately relies on metatheoretic identity."""
    logger.debug("metalanguage_boundary entry")
    result = MetalanguageBoundary(
        "observer-indexed echo",
        ("canonical observer bytes", "typed response identity", "control identifiers"),
        False,
        False,
    )
    logger.debug("metalanguage_boundary exit reflection=%s", result.echo_reflects_identity)
    return result


def internal_observer(observer_id: str, program: object) -> InternalObserver:
    """Capture an internally typed closed observer; callables are inadmissible."""
    logger.debug("internal_observer entry")
    observer_id = snapshot_identifier(observer_id, "observer-id")
    try:
        captured = snapshot_observer_program(program)
        canonical = canonical_observer_bytes(captured)
        decoded = decode_observer(canonical)
    except (ObserverCodecError, ObserverCoreError) as exc:
        logger.error("internal_observer invalid program")
        raise PositiveOntologyValidationError("invalid-observer-program") from exc
    result = snapshot_internal_observer(
        InternalObserver(observer_id, canonical, infer_observer_kind(decoded))
    )
    logger.debug("internal_observer exit observer=%s bytes=%d", observer_id, len(canonical))
    return result


def ontology_stage(
    stage_id: str,
    representative: CoreTerm,
    doctrine: ObserverDoctrine,
    observer_count: int,
) -> OntologyStage:
    """Build a stage using exactly one admitted doctrine prefix."""
    logger.debug("ontology_stage entry")
    doctrine = snapshot_observer_doctrine(doctrine)
    if type(observer_count) is not int or not 0 <= observer_count <= len(doctrine.observers):
        logger.error("ontology_stage prefix count rejected")
        raise PositiveOntologyValidationError("invalid-doctrine-prefix-length")
    result = snapshot_ontology_stage(
        OntologyStage(
            stage_id, representative, doctrine.doctrine_id,
            doctrine.observers[:observer_count],
        )
    )
    logger.debug("ontology_stage exit stage=%s observers=%d", result.stage_id, len(result.observers))
    return result


def presentation_commitment(
    witness_id: str, stage: OntologyStage
) -> PresentationCommitment:
    """Commit to a finite stage presentation without proving construction."""
    logger.debug("presentation_commitment entry")
    witness_id = snapshot_identifier(witness_id, "presentation-commitment-id")
    stage = snapshot_ontology_stage(stage)
    result = PresentationCommitment(witness_id, stage.stage_id, stage_commitment(stage))
    logger.debug("presentation_commitment exit stage=%s", stage.stage_id)
    return result


def continuation_witness(
    witness_id: str,
    path_id: str,
    lower_stage: str,
    upper_stage: str,
    preserved_observers: tuple[str, ...],
) -> ContinuationWitness:
    """Build an explicit path-relative preservation claim."""
    logger.debug("continuation_witness entry")
    from .validation import snapshot_continuation_witness
    result = snapshot_continuation_witness(
        ContinuationWitness(
            witness_id, path_id, lower_stage, upper_stage, preserved_observers
        )
    )
    logger.debug("continuation_witness exit witness=%s", result.witness_id)
    return result


def ontology_presentation(
    doctrine: ObserverDoctrine,
    presentation_id: str,
    stages: tuple[OntologyStage, ...],
    witnesses: tuple[ContinuationWitness, ...],
) -> OntologyPresentation:
    """Build a finite doctrine-relative coherent-presentation candidate."""
    logger.debug("ontology_presentation entry")
    result = snapshot_ontology_presentation(
        OntologyPresentation(doctrine, presentation_id, stages, witnesses)
    )
    logger.debug("ontology_presentation exit stages=%d witnesses=%d", len(result.stages), len(result.witnesses))
    return result


def silence_modalities(
    representative: CoreTerm, observation: Ready | Blocked
) -> tuple[SilenceModality, ...]:
    """Classify silence without treating it as nonexistence."""
    logger.debug("silence_modalities entry")
    representative = snapshot_recurrence(representative)
    encoded = observation_data(observation)
    rows: list[SilenceModality] = []
    if type(representative) is Silence:
        rows.append(SilenceModality.INTRINSIC)
    if encoded["tag"] == "blocked":
        rows.extend((SilenceModality.DOMAIN_UNDEFINED, SilenceModality.OBSTRUCTION))
    else:
        rows.extend(response_modalities(encoded))
    if not rows:
        rows.append(SilenceModality.NONE)
    result = tuple(rows)
    logger.debug("silence_modalities exit count=%d", len(result))
    return result


def observer_support_judgment(stage: OntologyStage) -> ObserverSupportJudgment:
    """Return observer support or openness, never an absence verdict."""
    logger.debug("observer_support_judgment entry")
    stage = snapshot_ontology_stage(stage)
    runs: list[RunJudgment] = []
    modalities: list[SilenceModality] = []
    for item in stage.observers:
        program = decode_observer(item.canonical)
        observation = observe(program, stage.representative)
        silence = silence_modalities(stage.representative, observation)
        modalities.extend(silence)
        runs.append(
            RunJudgment(
                stage.stage_id, item.observer_id,
                RunStatus.READY if type(observation) is Ready else RunStatus.BLOCKED,
                item.response_kind, silence,
                0 if type(observation) is Ready else len(observation.obstructions),
            )
        )
    if not runs:
        modalities.append(SilenceModality.NOT_QUERIED)
    support = ObserverSupport.SUPPORTED if any(row.status is RunStatus.READY for row in runs) else ObserverSupport.OPEN
    result = ObserverSupportJudgment(
        stage.stage_id, support, tuple(runs), tuple(dict.fromkeys(modalities))
    )
    logger.debug("observer_support_judgment exit support=%s runs=%d", result.support.value, len(runs))
    return result


def family_extension_judgment(
    presentation: OntologyPresentation, witness_id: str
) -> FamilyExtensionJudgment:
    """Compare inherited persistence with the full admitted doctrine prefix."""
    logger.debug("family_extension_judgment entry")
    presentation = snapshot_ontology_presentation(presentation)
    witness_id = snapshot_identifier(witness_id, "witness-id")
    witness = next((item for item in presentation.witnesses if item.witness_id == witness_id), None)
    if witness is None:
        logger.error("family_extension_judgment unknown witness")
        raise PositiveOntologyValidationError("unknown-witness-id")
    stages = {item.stage_id: item for item in presentation.stages}
    lower, upper = stages[witness.lower_stage], stages[witness.upper_stage]
    inherited = tuple(item.observer_id for item in lower.observers)
    full = tuple(item.observer_id for item in upper.observers)
    inherited_status, inherited_checks, inherited_obstruction = _relation_lane(
        lower, upper, inherited, witness, "inherited"
    )
    full_status, full_checks, full_obstruction = _relation_lane(
        lower, upper, full, witness, "full-family-extension"
    )
    result = FamilyExtensionJudgment(
        witness_id, inherited_checks, full_checks, inherited_status, full_status,
        inherited_obstruction or full_obstruction,
    )
    logger.debug("family_extension_judgment exit inherited=%s full=%s", inherited_status.value, full_status.value)
    return result


def persistence_judgment(
    presentation: OntologyPresentation, path_id: str
) -> PersistenceJudgment:
    """Check a composable explicit path using each witness's named observers."""
    logger.debug("persistence_judgment entry")
    presentation = snapshot_ontology_presentation(presentation)
    path_id = snapshot_identifier(path_id, "path-id")
    path = tuple(item for item in presentation.witnesses if item.path_id == path_id)
    if not path:
        logger.error("persistence_judgment unknown path")
        raise PositiveOntologyValidationError("unknown-path-id")
    stages = {item.stage_id: item for item in presentation.stages}
    checked_observers = 0
    previous_upper: str | None = None
    for index, witness in enumerate(path):
        if previous_upper is not None and witness.lower_stage != previous_upper:
            logger.error("persistence_judgment noncomposable path")
            raise PositiveOntologyValidationError("noncomposable-witness-path")
        lower, upper = stages[witness.lower_stage], stages[witness.upper_stage]
        status, checks, obstruction = _relation_lane(
            lower, upper, witness.preserved_observers, witness, "persistence"
        )
        checked_observers += checks
        if status is not RelationStatus.ECHO:
            result = PersistenceJudgment(path_id, index + 1, checked_observers, status, obstruction)
            logger.debug("persistence_judgment exit status=%s", status.value)
            return result
        previous_upper = witness.upper_stage
    result = PersistenceJudgment(
        path_id, len(path), checked_observers, RelationStatus.ECHO, None
    )
    logger.debug("persistence_judgment exit status=echo witnesses=%d", len(path))
    return result


def _relation_lane(
    lower: OntologyStage,
    upper: OntologyStage,
    observer_ids: tuple[str, ...],
    witness: ContinuationWitness,
    lane: str,
) -> tuple[RelationStatus, int, RelationObstruction | None]:
    logger.debug("_relation_lane entry witness=%s lane=%s observers=%d", witness.witness_id, lane, len(observer_ids))
    if not observer_ids:
        obstruction = RelationObstruction(witness.witness_id, "none", lane, "not-queried")
        logger.debug("_relation_lane exit status=undetermined checks=0")
        return RelationStatus.UNDETERMINED, 0, obstruction
    upper_map = {item.observer_id: item for item in upper.observers}
    for index, observer_id in enumerate(observer_ids, 1):
        outcome = echo(
            decode_observer(upper_map[observer_id].canonical),
            lower.representative,
            upper.representative,
        )
        logger.debug("_relation_lane state witness=%s lane=%s observer=%s", witness.witness_id, lane, observer_id)
        if type(outcome) is Mismatch:
            obstruction = RelationObstruction(witness.witness_id, observer_id, lane, "mismatch")
            return RelationStatus.SPLIT, index, obstruction
        if type(outcome) is DomainBlocked:
            obstruction = RelationObstruction(witness.witness_id, observer_id, lane, "domain-blocked")
            return RelationStatus.UNDETERMINED, index, obstruction
        if type(outcome) is not Echo:
            logger.error("_relation_lane unexpected outcome")
            raise RuntimeError("unexpected echo outcome")
    logger.debug("_relation_lane exit status=echo checks=%d", len(observer_ids))
    return RelationStatus.ECHO, len(observer_ids), None
