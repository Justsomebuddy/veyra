"""Fresh exact finite-path replay and composition for P1-C1."""

from __future__ import annotations

import logging

from .digest import path_digest
from .preflight import ConfluenceValidationError
from .types import DiagramPathReplay, FiniteDiagramSource
from .validation import (
    _identifier, _snapshot_stage, reconstruct_path, snapshot_confluence_doctrine,
    snapshot_finite_diagram_source,
)
from ..ontology.types import ObserverDoctrine

logger = logging.getLogger(__name__)


def replay_diagram_path(
    doctrine: ObserverDoctrine, source: FiniteDiagramSource, path_id: str,
) -> DiagramPathReplay:
    """Reconstruct one declared path into fresh stage snapshots."""
    logger.debug("replay_diagram_path entry")
    doctrine = snapshot_confluence_doctrine(doctrine)
    source = snapshot_finite_diagram_source(source, doctrine)
    path_id = _identifier(path_id, "path-id")
    path_map = {item.path_id: item for item in source.paths}
    path = path_map.get(path_id)
    if path is None:
        logger.error("replay_diagram_path unknown path")
        raise ConfluenceValidationError("unknown-path-id")
    edge_map = {item.edge_id: item for item in source.edges}
    stage_map = {item.stage_id: item for item in source.stages}
    stage_ids, commitments, digest = reconstruct_path(
        source.source_id, doctrine.fingerprint, path, edge_map, stage_map
    )
    result = DiagramPathReplay(
        (path_id,), path.edge_ids, tuple(_snapshot_stage(stage_map[item]) for item in stage_ids),
        commitments, digest,
    )
    logger.debug("replay_diagram_path exit stages=%d", len(result.stages))
    return result


def compose_diagram_paths(
    doctrine: ObserverDoctrine, source: FiniteDiagramSource,
    left_path_id: str, right_path_id: str, composed_path_id: str,
) -> DiagramPathReplay:
    """Compose two declared fresh replays when their exact endpoints agree."""
    logger.debug("compose_diagram_paths entry")
    doctrine = snapshot_confluence_doctrine(doctrine)
    source = snapshot_finite_diagram_source(source, doctrine)
    left = replay_diagram_path(doctrine, source, left_path_id)
    right = replay_diagram_path(doctrine, source, right_path_id)
    composed_path_id = _identifier(composed_path_id, "composed-path-id")
    if left.stage_commitments[-1] != right.stage_commitments[0]:
        logger.error("compose_diagram_paths noncomposable")
        raise ConfluenceValidationError("noncomposable-path-replays")
    stages = left.stages + right.stages[1:]
    commitments = left.stage_commitments + right.stage_commitments[1:]
    edges = left.edge_ids + right.edge_ids
    digest = path_digest(source.source_id, doctrine.fingerprint, composed_path_id, edges, commitments)
    result = DiagramPathReplay(
        left.source_path_ids + right.source_path_ids, edges, stages, commitments, digest
    )
    logger.debug("compose_diagram_paths exit stages=%d", len(stages))
    return result
