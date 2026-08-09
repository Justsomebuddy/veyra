"""Executable level-1 certificate for provisional P1-C1 confluence."""

from __future__ import annotations

import logging

from ..certify_types import Certificate
from ..confluence import (
    compose_diagram_paths, diagram_edge, diagram_path, direct_echo_transport,
    finite_diagram_source, fork_confluence_judgment, fork_join_plan,
    replay_diagram_path, swap_fork_join_plan,
)
from ..confluence.types import (
    AlignmentPoint, ConfluenceStatus, HigherConfluence, ScopedFormation,
)
from ..ontology.core import ontology_stage
from ..ontology.doctrine import p0_observer_doctrine
from ..proof_core_types import Pulse, Silence

logger = logging.getLogger(__name__)


def certify_confluence_p1c1() -> Certificate:
    """Certify one exact direct-echo fork without any higher promotion."""
    logger.debug("certify_confluence_p1c1 entry")
    doctrine = p0_observer_doctrine()
    stages = tuple(
        ontology_stage(name, Pulse(Silence()), doctrine, 1)
        for name in ("fork", "left", "right", "join")
    )
    edges = (
        diagram_edge("fork-left", "fork", "left", ("crest",)),
        diagram_edge("fork-right", "fork", "right", ("crest",)),
        diagram_edge("left-join", "left", "join", ("crest",)),
        diagram_edge("right-join", "right", "join", ("crest",)),
    )
    paths = (
        diagram_path("left-branch", ("fork-left",), "fork", "left"),
        diagram_path("right-branch", ("fork-right",), "fork", "right"),
        diagram_path("left-join-path", ("left-join",), "left", "join"),
        diagram_path("right-join-path", ("right-join",), "right", "join"),
    )
    source = finite_diagram_source(doctrine, "certificate-diagram", stages, edges, paths)
    transport = direct_echo_transport(doctrine, ("crest",))
    alignment = (AlignmentPoint(0, 0), AlignmentPoint(1, 1), AlignmentPoint(2, 2))
    plan = fork_join_plan(
        doctrine, source, "certificate-fork", "left-branch", "right-branch",
        "left-join-path", "right-join-path", alignment, transport,
    )
    first = fork_confluence_judgment(doctrine, source, plan, transport)
    second = fork_confluence_judgment(doctrine, source, plan, transport)
    swapped = swap_fork_join_plan(doctrine, source, plan, transport, "certificate-swapped")
    swap_row = fork_confluence_judgment(doctrine, source, swapped, transport)
    left = replay_diagram_path(doctrine, source, "left-branch")
    composed = compose_diagram_paths(
        doctrine, source, "left-branch", "left-join-path", "left-complete"
    )
    fresh = (
        first is not second and first.transport_cell is not second.transport_cell
        and first.plan_digest == second.plan_digest
        and first.transport_cell is not None and second.transport_cell is not None
        and first.transport_cell.trace_digest == second.transport_cell.trace_digest
        and first.transport_cell.response_rows is not second.transport_cell.response_rows
        and left.stages[0] is not source.stages[0]
    )
    nonclaims = all(
        row.local_finite_confluence is HigherConfluence.OPEN
        and row.global_confluence is HigherConfluence.OPEN
        and row.scoped_formation is ScopedFormation.OPEN
        for row in (first, second, swap_row)
    )
    passed = (
        first.status is second.status is swap_row.status is ConfluenceStatus.ESTABLISHED
        and first.transport_cell is not None
        and len(first.transport_cell.response_rows) == 3
        and first.charged_checks == 7
        and composed.edge_ids == ("fork-left", "left-join")
        and composed.stage_commitments[0] == left.stage_commitments[0]
        and composed.stage_commitments[-1] != composed.stage_commitments[0]
        and swapped.plan_digest != plan.plan_digest and fresh and nonclaims
    )
    method = (
        "provisional P1-C1 exact doctrine-bound direct-echo one-fork replay; "
        "no aggregation, finite/global/Church-Rosser promotion, translated mode, "
        "G4, scoped formation, termination, infinity, PΩ, R8, layer, or Sage claim"
    )
    detail = (
        "distinct branches and joins, full monotone alignment, derived fresh 2-cell, "
        "deterministic commitments, explicit swapped replay, higher claims open"
    )
    result = Certificate("confluence_p1c1", method, passed, detail, 1)
    logger.debug("certify_confluence_p1c1 exit result=%r", result)
    return result
