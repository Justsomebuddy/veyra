"""Replay-derived independent facets for the bounded P0 contract."""

from __future__ import annotations

import logging

from ..observer.patch_atlas import LocalObserverSection, ObserverPatchAtlas
from .core import observer_support_judgment, persistence_judgment
from .boundaries import diagram_coherence_judgment
from .doctrine import (
    require_p0_doctrine,
    snapshot_presentation_commitment,
    stage_commitment,
)
from .types import (
    ObserverSupport,
    FacetStatus,
    ObserverDoctrine,
    OntologyFacetReport,
    OntologyPresentation,
    OntologyStage,
    PresentationCommitment,
    RelationStatus,
    RunStatus,
)
from .validation import (
    PositiveOntologyValidationError,
    snapshot_identifier,
    snapshot_ontology_presentation,
    snapshot_ontology_stage,
)

logger = logging.getLogger(__name__)


def ontology_facet_report(
    stage: OntologyStage,
    doctrine: ObserverDoctrine,
    *,
    presentation: PresentationCommitment | None = None,
    coherence_atlas: ObserverPatchAtlas | None = None,
    coherence_sections: tuple[LocalObserverSection, ...] | None = None,
    persistence_presentation: OntologyPresentation | None = None,
    persistence_path_id: str | None = None,
) -> OntologyFacetReport:
    """Replay sources to classify facets; never accept judgment DTO claims."""
    logger.debug("ontology_facet_report entry")
    stage = snapshot_ontology_stage(stage)
    doctrine = require_p0_doctrine(doctrine)
    _validate_stage_admission(stage, doctrine)
    presentation_row = (
        snapshot_presentation_commitment(presentation, stage)
        if presentation is not None
        else None
    )
    coherent = _replay_coherence(coherence_atlas, coherence_sections)
    persistent = _replay_persistence(
        stage, doctrine, persistence_presentation, persistence_path_id
    )
    support_row = observer_support_judgment(stage)
    constructible = FacetStatus.OPEN
    witnessed = (
        FacetStatus.ESTABLISHED
        if support_row.support is ObserverSupport.SUPPORTED
        else FacetStatus.OPEN
    )
    scoped_object = (
        FacetStatus.REFUTED
        if coherent is FacetStatus.REFUTED or persistent is FacetStatus.REFUTED
        else FacetStatus.OPEN
    )
    result = OntologyFacetReport(
        stage.stage_id,
        FacetStatus.ESTABLISHED,
        FacetStatus.ESTABLISHED,
        FacetStatus.ESTABLISHED
        if any(run.status is RunStatus.READY for run in support_row.runs)
        else FacetStatus.OPEN,
        constructible,
        coherent,
        persistent,
        witnessed,
        scoped_object,
        presentation_row.witness_id if presentation_row else "",
        "object-completion-rule-not-supplied",
    )
    logger.debug(
        "ontology_facet_report exit constructible=%s scoped_object=%s",
        result.constructible.value,
        result.scoped_object.value,
    )
    return result


def _validate_stage_admission(stage: OntologyStage, doctrine: ObserverDoctrine) -> None:
    logger.debug("_validate_stage_admission entry")
    if stage.doctrine_id != doctrine.doctrine_id:
        logger.error("_validate_stage_admission doctrine mismatch")
        raise PositiveOntologyValidationError("stage-doctrine-drift")
    admitted = doctrine.observers[:len(stage.observers)]
    if len(stage.observers) > len(doctrine.observers) or any(
        row.observer_id != target.observer_id
        or row.canonical != target.canonical
        or row.response_kind != target.response_kind
        for row, target in zip(stage.observers, admitted, strict=True)
    ):
        logger.error("_validate_stage_admission prefix rejected")
        raise PositiveOntologyValidationError("observer-family-not-doctrine-prefix")
    logger.debug("_validate_stage_admission exit")


def _replay_coherence(
    atlas: ObserverPatchAtlas | None,
    sections: tuple[LocalObserverSection, ...] | None,
) -> FacetStatus:
    logger.debug("_replay_coherence entry")
    if atlas is None and sections is None:
        result = FacetStatus.NOT_EVALUATED
    elif atlas is None or sections is None:
        logger.error("_replay_coherence incomplete source")
        raise PositiveOntologyValidationError("incomplete-coherence-source")
    else:
        diagram_coherence_judgment(atlas, sections)
        result = FacetStatus.OPEN
    logger.debug("_replay_coherence exit status=%s", result.value)
    return result


def _replay_persistence(
    stage: OntologyStage,
    doctrine: ObserverDoctrine,
    presentation: OntologyPresentation | None,
    path_id: str | None,
) -> FacetStatus:
    logger.debug("_replay_persistence entry")
    if presentation is None and path_id is None:
        result = FacetStatus.NOT_EVALUATED
    elif presentation is None or path_id is None:
        logger.error("_replay_persistence incomplete source")
        raise PositiveOntologyValidationError("incomplete-persistence-source")
    else:
        path_id = snapshot_identifier(path_id, "path-id")
        presentation = snapshot_ontology_presentation(presentation)
        if presentation.doctrine != doctrine:
            logger.error("_replay_persistence doctrine mismatch")
            raise PositiveOntologyValidationError("persistence-doctrine-drift")
        source = next((item for item in presentation.stages if item.stage_id == stage.stage_id), None)
        if source is None or stage_commitment(source) != stage_commitment(stage):
            logger.error("_replay_persistence stage mismatch")
            raise PositiveOntologyValidationError("persistence-stage-drift")
        stages = {item.stage_id: item for item in presentation.stages}
        path = tuple(item for item in presentation.witnesses if item.path_id == path_id)
        path_stage_ids = (
            {path[0].lower_stage, *(witness.upper_stage for witness in path)}
            if path
            else set()
        )
        if stage.stage_id not in path_stage_ids:
            logger.error("_replay_persistence target not on selected path")
            raise PositiveOntologyValidationError("persistence-path-unbound-target")
        row = persistence_judgment(presentation, path_id)
        full_pressure = bool(path) and all(
            witness.preserved_observers
            == tuple(item.observer_id for item in stages[witness.upper_stage].observers)
            for witness in path
        ) and len(stages[path[-1].upper_stage].observers) == len(doctrine.observers)
        if row.status is RelationStatus.ECHO and full_pressure:
            result = FacetStatus.ESTABLISHED
        elif row.status is RelationStatus.ECHO:
            result = FacetStatus.OPEN
        elif row.status is RelationStatus.SPLIT:
            result = FacetStatus.REFUTED
        else:
            result = FacetStatus.OPEN
    logger.debug("_replay_persistence exit status=%s", result.value)
    return result
