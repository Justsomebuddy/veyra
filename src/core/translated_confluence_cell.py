"""Occurrence-complete translated response-cell construction for P1-C3."""

from __future__ import annotations

from hashlib import sha256
import logging

from .confluence_runtime import _history_stage_ids
from .confluence_types import ConfluenceObstruction, ConfluenceStatus
from .observer_core_codec import decode_observer
from .observer_core_semantics import observe
from .observer_core_types import Blocked, Ready
from .observer_morphism_runtime import translate_response
from .observer_morphism_types import ResponseTranslation
from .observer_relation_replay import observation_bytes
from .positive_ontology_types import OntologyStage
from .translated_confluence_digest import digest, sequence
from .translated_confluence_preflight import TranslatedConfluenceRequest
from .translated_confluence_types import (
    TranslatedResponseRow, TranslatedTransport2CellArtifact, TranslationDirection,
)
from .translated_confluence_validation import reject

logger = logging.getLogger(__name__)


def _side_ids(
    request: TranslatedConfluenceRequest,
) -> tuple[tuple[str, ...], tuple[str, ...], str, str]:
    """Resolve complete history stage occurrences without deleting repeats."""
    logger.debug("c3 side_ids entry")
    plan, source = request.plan, request.diagram
    left_join_id = plan.left_join_path_id
    right_join_id = plan.right_join_path_id
    if left_join_id is None or right_join_id is None:
        reject("translated-cell-requires-complete-separate-joins")
    left = _history_stage_ids(source, plan.left_branch_path_id, left_join_id)
    right = _history_stage_ids(source, plan.right_branch_path_id, right_join_id)
    logger.debug("c3 side_ids exit left=%d right=%d", len(left), len(right))
    return left, right, left_join_id, right_join_id


def _response_row(
    request: TranslatedConfluenceRequest, translation: ResponseTranslation,
    point_index: int, left_index: int, right_index: int,
    left_stage: OntologyStage, right_stage: OntologyStage,
) -> TranslatedResponseRow:
    """Evaluate both bridged programs and one typed projection at one occurrence."""
    logger.debug("c3 response_row entry point=%d", point_index)
    spec = request.spec
    fine_stage, coarse_stage = (
        (left_stage, right_stage)
        if spec.direction is TranslationDirection.LEFT_FINE_TO_RIGHT_COARSE
        else (right_stage, left_stage)
    )
    p0_members = {row.observer_id: row for row in request.p0_doctrine.observers}
    p1a_members = {row.observer_id: row for row in request.p1a_doctrine.observers}
    p0_fine = observe(
        decode_observer(p0_members[spec.diagram_fine_observer_id].canonical),
        fine_stage.representative,
    )
    p0_coarse = observe(
        decode_observer(p0_members[spec.diagram_coarse_observer_id].canonical),
        coarse_stage.representative,
    )
    fine = observe(
        decode_observer(p1a_members[spec.p1a_fine_observer_id].canonical),
        fine_stage.representative,
    )
    coarse = observe(
        decode_observer(p1a_members[spec.p1a_coarse_observer_id].canonical),
        coarse_stage.representative,
    )
    if observation_bytes(p0_fine) != observation_bytes(fine) or observation_bytes(p0_coarse) != observation_bytes(coarse):
        logger.error("c3 response bridge semantic drift")
        raise RuntimeError("translated-response-bridge-validation-drift")
    fine_digest = sha256(observation_bytes(fine)).hexdigest()
    coarse_digest = sha256(observation_bytes(coarse)).hexdigest()
    translated_digest = ""
    if type(fine) is Blocked or type(coarse) is Blocked:
        status, outcome = ConfluenceStatus.OPEN, "domain-blocked"
    elif type(fine) is Ready and type(coarse) is Ready:
        translated = translate_response(
            request.p1a_doctrine, request.p1a_source, translation, fine.value,
        )
        translated_bytes = observation_bytes(Ready(translated))
        translated_digest = sha256(translated_bytes).hexdigest()
        if translated_bytes == observation_bytes(coarse):
            status, outcome = ConfluenceStatus.ESTABLISHED, "translated-echo"
        else:
            status, outcome = ConfluenceStatus.REFUTED, "translated-mismatch"
    else:
        logger.error("c3 response row malformed observation")
        raise RuntimeError("translated-observation-validation-drift")
    row_digest = digest("p1-c3-response-row-v1", (
        ("run", request.run_digest.encode()),
        ("indices", sequence("index", (
            str(point_index), str(left_index), str(right_index),
        ))),
        ("stages", sequence("stage", (fine_stage.stage_id, coarse_stage.stage_id))),
        ("observers", sequence("observer", (
            spec.diagram_fine_observer_id, spec.diagram_coarse_observer_id,
            spec.p1a_fine_observer_id, spec.p1a_coarse_observer_id,
        ))),
        ("status", status.value.encode()), ("outcome", outcome.encode()),
        ("payloads", sequence("payload", (
            fine_digest, translated_digest, coarse_digest,
        ))),
    ))
    result = TranslatedResponseRow(
        point_index, left_index, right_index, fine_stage.stage_id,
        coarse_stage.stage_id, spec.diagram_fine_observer_id,
        spec.diagram_coarse_observer_id, spec.p1a_fine_observer_id,
        spec.p1a_coarse_observer_id, status, outcome, fine_digest,
        translated_digest, coarse_digest, row_digest,
    )
    logger.debug("c3 response_row exit status=%s", status.value)
    return result


def build_translated_cell(
    request: TranslatedConfluenceRequest, translation: ResponseTranslation,
    a2_digest: str,
) -> TranslatedTransport2CellArtifact:
    """Derive the exact complete translated cell and deterministic obstruction."""
    logger.debug("c3 cell entry")
    left_ids, right_ids, left_join_id, right_join_id = _side_ids(request)
    stages = {row.stage_id: row for row in request.diagram.stages}
    rows = tuple(
        _response_row(
            request, translation, index, point.left_index, point.right_index,
            stages[left_ids[point.left_index]], stages[right_ids[point.right_index]],
        )
        for index, point in enumerate(request.plan.alignment)
    )
    bad = tuple(row for row in rows if row.status is ConfluenceStatus.REFUTED)
    opened = tuple(row for row in rows if row.status is ConfluenceStatus.OPEN)
    status = ConfluenceStatus.REFUTED if bad else (
        ConfluenceStatus.OPEN if opened else ConfluenceStatus.ESTABLISHED
    )
    first = bad[0] if bad else (opened[0] if opened else None)
    obstruction = None if first is None else ConfluenceObstruction(
        "translated-alignment", first.point_index,
        first.diagram_fine_observer_id, first.outcome,
    )
    left_trace = digest("p1-c3-left-trace-v1", (
        ("plan", request.plan.plan_digest.encode()),
        ("rows", sequence("row", tuple(row.row_digest for row in rows))),
    ))
    right_trace = digest("p1-c3-right-trace-v1", (
        ("plan", request.plan.plan_digest.encode()),
        ("rows", sequence("row", tuple(reversed(tuple(row.row_digest for row in rows))))),
    ))
    trace = digest("p1-c3-cell-trace-v1", (
        ("left", left_trace.encode()), ("right", right_trace.encode()),
        ("direction", request.spec.direction.value.encode()),
    ))
    commitments = dict(zip(
        (row.path_id for row in request.diagram.paths),
        request.diagram.path_commitments, strict=True,
    ))
    alignment_digest = digest("p1-c3-alignment-v1", (
        ("points", sequence("point", tuple(
            f"{point.left_index}:{point.right_index}" for point in request.plan.alignment
        ))),
    ))
    history_values = (
        commitments[request.plan.left_branch_path_id],
        commitments[request.plan.right_branch_path_id],
        commitments[left_join_id],
        commitments[right_join_id],
    )
    artifact_digest = digest("p1-c3-cell-artifact-v1", (
        ("run", request.run_digest.encode()), ("a2", a2_digest.encode()),
        ("histories", sequence("history", history_values)),
        ("alignment", alignment_digest.encode()), ("trace", trace.encode()),
        ("status", status.value.encode()),
    ))
    result = TranslatedTransport2CellArtifact(
        request.p0_doctrine.fingerprint, request.diagram.source_digest,
        request.plan.plan_digest, request.plan.fork_stage_commitment,
        *history_values, request.plan.join_stage_commitment or "",
        alignment_digest, request.bridge.bridge_digest,
        request.spec.spec_digest, request.a2_stage_source.source_digest,
        a2_digest, request.spec.direction,
        (request.spec.diagram_fine_observer_id, request.spec.diagram_coarse_observer_id),
        rows, left_trace, right_trace, trace, artifact_digest, obstruction,
        request.required_checks, status,
    )
    logger.debug("c3 cell exit status=%s rows=%d", status.value, len(rows))
    return result
