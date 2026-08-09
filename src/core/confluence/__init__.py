"""Public construction surface for provisional P1-C1 confluence."""

from __future__ import annotations

import logging

from .path import compose_diagram_paths, replay_diagram_path
from .plan import (
    build_direct_echo_transport, build_fork_join_plan, swap_fork_join_plan,
)
from .runtime import fork_confluence_judgment
from .types import (
    AlignmentPoint, DiagramEdge, DiagramPath, DirectEchoTransport,
    FiniteDiagramSource, ForkJoinPlan,
)
from .validation import (
    build_finite_diagram_source, snapshot_diagram_edge, snapshot_diagram_path,
)
from ..ontology.types import ObserverDoctrine, OntologyStage

logger = logging.getLogger(__name__)


def diagram_edge(
    edge_id: str, lower_stage_id: str, upper_stage_id: str,
    preserved_observer_ids: tuple[str, ...],
) -> DiagramEdge:
    """Construct one exact generic diagram edge."""
    logger.debug("diagram_edge entry")
    result = snapshot_diagram_edge(
        DiagramEdge(edge_id, lower_stage_id, upper_stage_id, preserved_observer_ids)
    )
    logger.debug("diagram_edge exit")
    return result


def diagram_path(
    path_id: str, edge_ids: tuple[str, ...], start_stage_id: str,
    end_stage_id: str,
) -> DiagramPath:
    """Construct one exact ordered path claim."""
    logger.debug("diagram_path entry")
    result = snapshot_diagram_path(
        DiagramPath(path_id, edge_ids, start_stage_id, end_stage_id)
    )
    logger.debug("diagram_path exit")
    return result


def finite_diagram_source(
    doctrine: ObserverDoctrine, source_id: str, stages: tuple[OntologyStage, ...],
    edges: tuple[DiagramEdge, ...], paths: tuple[DiagramPath, ...],
) -> FiniteDiagramSource:
    """Build a fresh generic doctrine-bound finite diagram source."""
    logger.debug("finite_diagram_source entry")
    result = build_finite_diagram_source(doctrine, source_id, stages, edges, paths)
    logger.debug("finite_diagram_source exit")
    return result


def direct_echo_transport(
    doctrine: ObserverDoctrine, observer_ids: tuple[str, ...],
) -> DirectEchoTransport:
    """Build the sole direct-echo transport available in C1."""
    logger.debug("direct_echo_transport entry")
    result = build_direct_echo_transport(doctrine, observer_ids)
    logger.debug("direct_echo_transport exit")
    return result


def fork_join_plan(
    doctrine: ObserverDoctrine, source: FiniteDiagramSource, plan_id: str,
    left_branch_path_id: str, right_branch_path_id: str,
    left_join_path_id: str | None, right_join_path_id: str | None,
    alignment: tuple[AlignmentPoint, ...], transport: DirectEchoTransport,
) -> ForkJoinPlan:
    """Build a complete or intentionally join-missing exact fork plan."""
    logger.debug("fork_join_plan entry")
    result = build_fork_join_plan(
        source, plan_id, left_branch_path_id, right_branch_path_id,
        left_join_path_id, right_join_path_id, alignment, transport, doctrine,
    )
    logger.debug("fork_join_plan exit")
    return result


__all__ = [
    "compose_diagram_paths", "diagram_edge", "diagram_path",
    "direct_echo_transport", "finite_diagram_source", "fork_confluence_judgment",
    "fork_join_plan", "replay_diagram_path", "swap_fork_join_plan",
]
