"""Exact direct-echo transport and fork/join plan binding for P1-C1."""

from __future__ import annotations

import logging
from typing import NoReturn

from .digest import direct_transport_digest, fork_plan_digest
from .preflight import ConfluenceValidationError
from .types import (
    AlignmentPoint, DirectEchoTransport, FiniteDiagramSource, ForkJoinPlan,
    TransportMode,
)
from .validation import (
    _hex_digest, _identifier, snapshot_confluence_doctrine,
    snapshot_finite_diagram_source,
)
from ..ontology.doctrine import stage_commitment
from ..ontology.types import ObserverDoctrine

logger = logging.getLogger(__name__)
PLAN_VERSION = "p1-c1-plan-v1"
PLAN_SCOPE = "one-declared-fork-direct-echo"


def _reject(reason: str) -> NoReturn:
    logger.error("confluence plan rejected reason=%s", reason)
    raise ConfluenceValidationError(reason)


def _snapshot_alignment(value: tuple[AlignmentPoint, ...]) -> tuple[AlignmentPoint, ...]:
    logger.debug("_snapshot_alignment entry")
    if type(value) is not tuple or len(value) > 513:
        _reject("invalid-alignment")
    rows: list[AlignmentPoint] = []
    for item in value:
        if type(item) is not AlignmentPoint:
            _reject("alignment-point-must-be-exact")
        try:
            left, right = item.left_index, item.right_index
        except AttributeError:
            _reject("alignment-point-missing-fields")
        if type(left) is not int or type(right) is not int or left < 0 or right < 0:
            _reject("invalid-alignment-coordinate")
        rows.append(AlignmentPoint(left, right))
    result = tuple(rows)
    logger.debug("_snapshot_alignment exit points=%d", len(result))
    return result


def build_direct_echo_transport(
    doctrine: ObserverDoctrine, observer_ids: tuple[str, ...],
) -> DirectEchoTransport:
    """Construct the sole C1 transport from exact doctrine members."""
    logger.debug("build_direct_echo_transport entry")
    doctrine = snapshot_confluence_doctrine(doctrine)
    if type(observer_ids) is not tuple or not 1 <= len(observer_ids) <= 64:
        _reject("invalid-direct-transport-observers")
    ids = tuple(_identifier(item, "transport-observer-id") for item in observer_ids)
    if len(set(ids)) != len(ids):
        _reject("duplicate-transport-observer-id")
    admitted = {item.observer_id for item in doctrine.observers}
    if any(item not in admitted for item in ids):
        _reject("transport-observer-not-in-doctrine")
    result = DirectEchoTransport(ids, direct_transport_digest(doctrine.fingerprint, ids))
    logger.debug("build_direct_echo_transport exit observers=%d", len(ids))
    return result


def snapshot_direct_echo_transport(
    value: DirectEchoTransport, doctrine: ObserverDoctrine,
) -> DirectEchoTransport:
    """Rebuild a direct transport and reject translated or forged evidence."""
    logger.debug("snapshot_direct_echo_transport entry")
    doctrine = snapshot_confluence_doctrine(doctrine)
    if type(value) is not DirectEchoTransport:
        _reject("direct-echo-transport-must-be-exact")
    try:
        ids, supplied, mode, scope = (
            value.observer_ids, value.transport_digest, value.mode, value.scope,
        )
    except AttributeError:
        _reject("direct-echo-transport-missing-fields")
    result = build_direct_echo_transport(doctrine, ids)
    if (
        _hex_digest(supplied, "transport-digest") != result.transport_digest
        or type(mode) is not TransportMode or mode is not TransportMode.DIRECT_ECHO
        or type(scope) is not str or scope != "direct-echo-only-no-translation"
    ):
        _reject("direct-echo-transport-drift")
    logger.debug("snapshot_direct_echo_transport exit")
    return result


def _plan_components(
    source: FiniteDiagramSource, plan_id: str, left_branch: str, right_branch: str,
    left_join: str | None, right_join: str | None,
    alignment: tuple[AlignmentPoint, ...], transport: DirectEchoTransport,
) -> tuple[str, str, str | None, tuple[AlignmentPoint, ...], str]:
    logger.debug("_plan_components entry")
    plan_id = _identifier(plan_id, "plan-id")
    left_branch = _identifier(left_branch, "left-branch-path-id")
    right_branch = _identifier(right_branch, "right-branch-path-id")
    if left_branch == right_branch:
        _reject("fork-branches-must-be-distinct")
    paths = {item.path_id: item for item in source.paths}
    commitments = dict(zip((item.path_id for item in source.paths), source.path_commitments, strict=True))
    if left_branch not in paths or right_branch not in paths:
        _reject("unknown-branch-path")
    left, right = paths[left_branch], paths[right_branch]
    if left.edge_ids == right.edge_ids or left.start_stage_id != right.start_stage_id:
        _reject("invalid-fork-branch-history")
    if left.edge_ids[0] == right.edge_ids[0]:
        _reject("fork-first-edges-must-differ")
    stages = {item.stage_id: item for item in source.stages}
    fork = stage_commitment(stages[left.start_stage_id])
    alignment = _snapshot_alignment(alignment)
    join_commitment: str | None = None
    if left_join is None or right_join is None:
        if left_join is not None or right_join is not None or alignment:
            _reject("partial-join-plan")
        path_digests = (commitments[left_branch], commitments[right_branch], None, None)
    else:
        left_join = _identifier(left_join, "left-join-path-id")
        right_join = _identifier(right_join, "right-join-path-id")
        if left_join == right_join or left_join not in paths or right_join not in paths:
            _reject("invalid-separate-join-paths")
        lj, rj = paths[left_join], paths[right_join]
        if left.end_stage_id != lj.start_stage_id or right.end_stage_id != rj.start_stage_id:
            _reject("join-path-not-bound-to-branch")
        if lj.end_stage_id != rj.end_stage_id:
            _reject("join-stage-mismatch")
        join_commitment = stage_commitment(stages[lj.end_stage_id])
        left_last, right_last = len(left.edge_ids) + len(lj.edge_ids), len(right.edge_ids) + len(rj.edge_ids)
        if not alignment or alignment[0] != AlignmentPoint(0, 0) or alignment[-1] != AlignmentPoint(left_last, right_last):
            _reject("alignment-endpoint-drift")
        for previous, current in zip(alignment, alignment[1:]):
            delta = (current.left_index - previous.left_index, current.right_index - previous.right_index)
            if delta not in {(1, 0), (0, 1), (1, 1)}:
                _reject("alignment-not-full-monotone")
        path_digests = (
            commitments[left_branch], commitments[right_branch],
            commitments[left_join], commitments[right_join],
        )
    digest = fork_plan_digest(
        PLAN_VERSION, PLAN_SCOPE, plan_id, source.source_digest, fork,
        path_digests, join_commitment, alignment, transport.transport_digest,
    )
    logger.debug("_plan_components exit joined=%s", join_commitment is not None)
    return plan_id, fork, join_commitment, alignment, digest


def build_fork_join_plan(
    source: FiniteDiagramSource, plan_id: str, left_branch_path_id: str,
    right_branch_path_id: str, left_join_path_id: str | None,
    right_join_path_id: str | None, alignment: tuple[AlignmentPoint, ...],
    transport: DirectEchoTransport, doctrine: ObserverDoctrine,
) -> ForkJoinPlan:
    """Construct a source-bound one-fork plan; absent joins remain valid OPEN input."""
    logger.debug("build_fork_join_plan entry")
    doctrine = snapshot_confluence_doctrine(doctrine)
    source = snapshot_finite_diagram_source(source, doctrine)
    transport = snapshot_direct_echo_transport(transport, doctrine)
    parts = _plan_components(
        source, plan_id, left_branch_path_id, right_branch_path_id,
        left_join_path_id, right_join_path_id, alignment, transport,
    )
    result = ForkJoinPlan(
        parts[0], source.source_digest, parts[1], left_branch_path_id,
        right_branch_path_id, left_join_path_id, right_join_path_id,
        parts[2], parts[3], transport.transport_digest, parts[4],
    )
    logger.debug("build_fork_join_plan exit")
    return result


def snapshot_fork_join_plan(
    value: ForkJoinPlan, source: FiniteDiagramSource,
    transport: DirectEchoTransport, doctrine: ObserverDoctrine,
) -> ForkJoinPlan:
    """Recompute the full plan commitment from raw source and transport."""
    logger.debug("snapshot_fork_join_plan entry")
    doctrine = snapshot_confluence_doctrine(doctrine)
    source = snapshot_finite_diagram_source(source, doctrine)
    transport = snapshot_direct_echo_transport(transport, doctrine)
    if type(value) is not ForkJoinPlan:
        _reject("fork-join-plan-must-be-exact")
    try:
        result = build_fork_join_plan(
            source, value.plan_id, value.left_branch_path_id,
            value.right_branch_path_id, value.left_join_path_id,
            value.right_join_path_id, value.alignment, transport, doctrine,
        )
        supplied = (
            value.diagram_digest, value.fork_stage_commitment,
            value.join_stage_commitment, value.transport_digest, value.plan_digest,
            value.version, value.scope,
        )
    except AttributeError:
        _reject("fork-join-plan-missing-fields")
    diagram, fork, join, transport_digest, plan_digest, version, scope = supplied
    diagram = _hex_digest(diagram, "plan-diagram-digest")
    fork = _hex_digest(fork, "plan-fork-commitment")
    if join is not None:
        join = _hex_digest(join, "plan-join-commitment")
    transport_digest = _hex_digest(transport_digest, "plan-transport-digest")
    plan_digest = _hex_digest(plan_digest, "plan-digest")
    if type(version) is not str or type(scope) is not str:
        _reject("fork-join-plan-drift")
    supplied = (diagram, fork, join, transport_digest, plan_digest, version, scope)
    expected = (
        result.diagram_digest, result.fork_stage_commitment,
        result.join_stage_commitment, result.transport_digest, result.plan_digest,
        result.version, result.scope,
    )
    if supplied != expected:
        _reject("fork-join-plan-drift")
    logger.debug("snapshot_fork_join_plan exit")
    return result


def swap_fork_join_plan(
    doctrine: ObserverDoctrine, source: FiniteDiagramSource, plan: ForkJoinPlan,
    transport: DirectEchoTransport, swapped_plan_id: str,
) -> ForkJoinPlan:
    """Derive an explicit swapped plan, including coordinate-swapped alignment."""
    logger.debug("swap_fork_join_plan entry")
    plan = snapshot_fork_join_plan(plan, source, transport, doctrine)
    alignment = tuple(AlignmentPoint(item.right_index, item.left_index) for item in plan.alignment)
    result = build_fork_join_plan(
        source, swapped_plan_id, plan.right_branch_path_id,
        plan.left_branch_path_id, plan.right_join_path_id,
        plan.left_join_path_id, alignment, transport, doctrine,
    )
    logger.debug("swap_fork_join_plan exit")
    return result
