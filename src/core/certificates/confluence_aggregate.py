"""Executable level-1 certificate for P1-C2 finite catalog aggregation."""

from __future__ import annotations

import logging

from ..certify_types import Certificate
from ..confluence import (
    diagram_edge, diagram_path, direct_echo_transport, finite_diagram_source,
    fork_join_plan,
)
from ..confluence.aggregate import (
    FiniteConfluenceAggregate, GlobalDeclaredFiniteStatus, LocalFiniteStatus,
    confluence_aggregate_policy, declared_history, finite_confluence_aggregate,
    finite_confluence_catalog, global_path_pair_requirement, identity_history,
    local_critical_fork_requirement, validate_finite_confluence_result,
)
from ..confluence.types import AlignmentPoint, ConfluenceStatus
from ..ontology.core import ontology_stage
from ..ontology.doctrine import p0_observer_doctrine
from ..proof_core_types import Pulse, Silence

logger = logging.getLogger(__name__)


def certify_confluence_aggregate_p1c2() -> Certificate:
    """Certify local and separately declared global finite confluence only."""
    logger.debug("certify_confluence_aggregate_p1c2 entry")
    doctrine = p0_observer_doctrine()
    names = ("fork", "left", "right", "join", "a", "b")
    stages = tuple(
        ontology_stage(name, Pulse(Silence()), doctrine, 1) for name in names
    )
    edges = (
        diagram_edge("fl", "fork", "left", ("crest",)),
        diagram_edge("fr", "fork", "right", ("crest",)),
        diagram_edge("lj", "left", "join", ("crest",)),
        diagram_edge("rj", "right", "join", ("crest",)),
        diagram_edge("ab", "a", "b", ("crest",)),
        diagram_edge("ba", "b", "a", ("crest",)),
    )
    paths = (
        diagram_path("lb", ("fl",), "fork", "left"),
        diagram_path("rb", ("fr",), "fork", "right"),
        diagram_path("ljp", ("lj",), "left", "join"),
        diagram_path("rjp", ("rj",), "right", "join"),
        diagram_path("cycle", ("ab", "ba"), "a", "a"),
    )
    diagram = finite_diagram_source(doctrine, "p1c2-cert", stages, edges, paths)
    transport = direct_echo_transport(doctrine, ("crest",))
    plan = fork_join_plan(
        doctrine, diagram, "local-plan", "lb", "rb", "ljp", "rjp",
        (AlignmentPoint(0, 0), AlignmentPoint(1, 1), AlignmentPoint(2, 2)),
        transport,
    )
    local = local_critical_fork_requirement(doctrine, diagram, "local-1", plan, transport)
    cycle = declared_history(doctrine, diagram, "cycle-history", "cycle")
    identity = identity_history(doctrine, diagram, "identity-history", "a")
    global_ = global_path_pair_requirement(
        doctrine, diagram, "cycle-vs-id", cycle, identity,
        (AlignmentPoint(0, 0), AlignmentPoint(1, 0), AlignmentPoint(2, 0)),
        transport,
    )
    catalog = finite_confluence_catalog(
        doctrine, diagram, (local,), (global_,), confluence_aggregate_policy(),
    )
    first = finite_confluence_aggregate(doctrine, diagram, catalog)
    second = validate_finite_confluence_result(doctrine, diagram, catalog, first)
    passed = (
        type(first) is FiniteConfluenceAggregate
        and type(second) is FiniteConfluenceAggregate
        and first is not second and first.aggregate_digest == second.aggregate_digest
        and first.local_status is LocalFiniteStatus.CONFLUENT
        and first.global_status is GlobalDeclaredFiniteStatus.CONFLUENT
        and len(first.rows) == 2
        and all(row.status is ConfluenceStatus.ESTABLISHED for row in first.rows)
        and first.rows[0].local_judgment_digest is not None
        and first.rows[1].global_history_cell_digest is not None
    )
    method = (
        "P1-C2 exact nonempty local and separately declared global finite catalogs; "
        "cycle-versus-zero-edge identity included; no generated-path universe, "
        "termination, Church-Rosser, object formation, infinity, or promotion claim"
    )
    detail = (
        "atomic source-byte/check preflight, raw C1 replay, arbitrary history 2-cell, "
        "complete ordered coverage, separate local/global statuses, fresh revalidation"
    )
    result = Certificate("confluence_aggregate_p1c2", method, passed, detail, 1)
    logger.debug("certify_confluence_aggregate_p1c2 exit passed=%s", passed)
    return result
