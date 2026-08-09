"""Exact stage-prefix and edge-preservation checks for P1-C4 observers."""

from __future__ import annotations

import logging

from .codec import ScopedFormationValidationError

logger = logging.getLogger(__name__)


def require_observer_at_stage(doctrine, stage, observer_id: str, lane: str) -> None:
    """Require one unique occurrence identical to its doctrine member."""
    logger.debug("require_observer_at_stage entry lane=%s stage=%s", lane, stage.stage_id)
    doctrine_rows = tuple(x for x in doctrine.observers if x.observer_id == observer_id)
    stage_rows = tuple(x for x in stage.observers if x.observer_id == observer_id)
    if len(doctrine_rows) != 1 or len(stage_rows) != 1:
        logger.error("observer occurrence missing/ambiguous lane=%s stage=%s observer=%s", lane, stage.stage_id, observer_id)
        raise ScopedFormationValidationError(f"{lane}-observer-occurrence-not-exact")
    expected, actual = doctrine_rows[0], stage_rows[0]
    if (
        type(actual) is not type(expected)
        or actual.canonical != expected.canonical
        or type(actual.response_kind) is not type(expected.response_kind)
        or actual.response_kind != expected.response_kind
    ):
        logger.error("observer occurrence drift lane=%s stage=%s observer=%s", lane, stage.stage_id, observer_id)
        raise ScopedFormationValidationError(f"{lane}-observer-occurrence-drift")
    logger.debug("require_observer_at_stage exit lane=%s", lane)


def require_observer_on_path(doctrine, diagram, path_id: str, observer_id: str, lane: str) -> None:
    """Require exact occurrence at every stage and declared preservation on every edge."""
    logger.debug("require_observer_on_path entry lane=%s path=%s", lane, path_id)
    paths = tuple(x for x in diagram.paths if x.path_id == path_id)
    if len(paths) != 1:
        logger.error("observer path missing/ambiguous lane=%s path=%s", lane, path_id)
        raise ScopedFormationValidationError(f"{lane}-path-not-exact")
    stages = {x.stage_id: x for x in diagram.stages}
    edges = {x.edge_id: x for x in diagram.edges}
    path = paths[0]
    stage_ids = [path.start_stage_id]
    for edge_id in path.edge_ids:
        edge = edges[edge_id]
        if observer_id not in edge.preserved_observer_ids:
            logger.error("observer not preserved lane=%s path=%s edge=%s observer=%s", lane, path_id, edge_id, observer_id)
            raise ScopedFormationValidationError(f"{lane}-observer-not-preserved")
        stage_ids.append(edge.upper_stage_id)
    for stage_id in stage_ids:
        require_observer_at_stage(doctrine, stages[stage_id], observer_id, lane)
    logger.debug("require_observer_on_path exit lane=%s path=%s", lane, path_id)
