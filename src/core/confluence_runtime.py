"""Fresh direct-echo replay and deterministic one-fork judgment for P1-C1."""

from __future__ import annotations

import json
import logging

from .confluence_digest import (
    cell_trace_digest, joined_history_digest, response_row_digest, trace_digest,
)
from .confluence_plan import snapshot_direct_echo_transport, snapshot_fork_join_plan
from .confluence_preflight import preflight_confluence_checks
from .confluence_types import (
    ConfluenceObstruction, ConfluencePreflightCharge, ConfluenceStatus,
    DirectEchoTransport, FiniteDiagramSource, ForkConfluenceJudgment,
    ForkJoinPlan, Transport2CellArtifact, TransportResponseRow,
)
from .confluence_validation import (
    snapshot_confluence_doctrine, snapshot_finite_diagram_source,
)
from .observer_core_codec import decode_observer
from .observer_core_semantics import echo
from .observer_core_support import outcome_data
from .observer_core_types import DomainBlocked, Echo, Mismatch
from .positive_ontology_types import ObserverDoctrine, OntologyStage

logger = logging.getLogger(__name__)


def _status(outcome: object) -> ConfluenceStatus:
    logger.debug("_status entry")
    if type(outcome) is Echo:
        result = ConfluenceStatus.ESTABLISHED
    elif type(outcome) is Mismatch:
        result = ConfluenceStatus.REFUTED
    elif type(outcome) is DomainBlocked:
        result = ConfluenceStatus.OPEN
    else:
        logger.error("_status unexpected echo outcome")
        raise RuntimeError("unexpected direct echo outcome")
    logger.debug("_status exit status=%s", result.value)
    return result


def _payload(outcome: object) -> bytes:
    logger.debug("_payload entry")
    encoded = outcome_data(outcome)
    result = json.dumps(encoded, sort_keys=True, separators=(",", ":")).encode()
    logger.debug("_payload exit bytes=%d", len(result))
    return result


def _outcome_name(outcome: object) -> str:
    logger.debug("_outcome_name entry")
    if type(outcome) is Echo:
        result = "echo"
    elif type(outcome) is Mismatch:
        result = "mismatch"
    elif type(outcome) is DomainBlocked:
        result = "domain-blocked"
    else:
        logger.error("_outcome_name unexpected echo outcome")
        raise RuntimeError("unexpected direct echo outcome")
    logger.debug("_outcome_name exit outcome=%s", result)
    return result


def _selected_paths(source: FiniteDiagramSource, plan: ForkJoinPlan) -> tuple[tuple[str, str], ...]:
    logger.debug("_selected_paths entry")
    rows = [
        ("left-branch", plan.left_branch_path_id),
        ("right-branch", plan.right_branch_path_id),
    ]
    if plan.left_join_path_id is not None and plan.right_join_path_id is not None:
        rows.extend((
            ("left-join", plan.left_join_path_id),
            ("right-join", plan.right_join_path_id),
        ))
    result = tuple(rows)
    logger.debug("_selected_paths exit count=%d", len(result))
    return result


def _edge_check_count(source: FiniteDiagramSource, plan: ForkJoinPlan) -> int:
    logger.debug("_edge_check_count entry")
    paths = {item.path_id: item for item in source.paths}
    edges = {item.edge_id: item for item in source.edges}
    result = sum(
        max(1, len(edges[edge_id].preserved_observer_ids))
        for _, path_id in _selected_paths(source, plan)
        for edge_id in paths[path_id].edge_ids
    )
    logger.debug("_edge_check_count exit count=%d", result)
    return result


def _record(
    status: ConfluenceStatus, obstruction: ConfluenceObstruction,
    mismatches: list[ConfluenceObstruction], openings: list[ConfluenceObstruction],
) -> None:
    logger.debug("_record entry status=%s", status.value)
    if status is ConfluenceStatus.REFUTED:
        mismatches.append(obstruction)
    elif status is ConfluenceStatus.OPEN:
        openings.append(obstruction)
    logger.debug("_record exit mismatches=%d openings=%d", len(mismatches), len(openings))


def _check_persistence(
    source: FiniteDiagramSource, plan: ForkJoinPlan,
) -> tuple[list[ConfluenceObstruction], list[ConfluenceObstruction]]:
    logger.debug("_check_persistence entry")
    paths = {item.path_id: item for item in source.paths}
    edges = {item.edge_id: item for item in source.edges}
    stages = {item.stage_id: item for item in source.stages}
    mismatches: list[ConfluenceObstruction] = []
    openings: list[ConfluenceObstruction] = []
    occurrence = 0
    for lane, path_id in _selected_paths(source, plan):
        path = paths[path_id]
        for edge_id in path.edge_ids:
            edge = edges[edge_id]
            if not edge.preserved_observer_ids:
                occurrence += 1
                openings.append(ConfluenceObstruction(lane, occurrence, "none", "not-queried"))
                continue
            upper = {item.observer_id: item for item in stages[edge.upper_stage_id].observers}
            for observer_id in edge.preserved_observer_ids:
                occurrence += 1
                outcome = echo(
                    decode_observer(upper[observer_id].canonical),
                    stages[edge.lower_stage_id].representative,
                    stages[edge.upper_stage_id].representative,
                )
                status = _status(outcome)
                if status is not ConfluenceStatus.ESTABLISHED:
                    _record(
                        status, ConfluenceObstruction(
                            lane, occurrence, observer_id, _outcome_name(outcome)
                        ),
                        mismatches, openings,
                    )
    logger.debug("_check_persistence exit mismatch=%d open=%d", len(mismatches), len(openings))
    return mismatches, openings


def _history_stage_ids(source: FiniteDiagramSource, branch_id: str, join_id: str) -> tuple[str, ...]:
    logger.debug("_history_stage_ids entry")
    paths = {item.path_id: item for item in source.paths}
    edges = {item.edge_id: item for item in source.edges}
    branch, join = paths[branch_id], paths[join_id]
    edge_ids = branch.edge_ids + join.edge_ids
    result = (edges[edge_ids[0]].lower_stage_id, *(edges[item].upper_stage_id for item in edge_ids))
    logger.debug("_history_stage_ids exit stages=%d", len(result))
    return result


def _response_row(
    plan: ForkJoinPlan, point_index: int, left_index: int, right_index: int,
    left: OntologyStage, right: OntologyStage, observer_id: str,
) -> TransportResponseRow:
    logger.debug("_response_row entry point=%d", point_index)
    left_map = {item.observer_id: item for item in left.observers}
    right_map = {item.observer_id: item for item in right.observers}
    if observer_id not in left_map or observer_id not in right_map:
        status = ConfluenceStatus.OPEN
        outcome_name, payload = "observer-unavailable", b'{"tag":"observer-unavailable"}'
    else:
        outcome = echo(
            decode_observer(left_map[observer_id].canonical),
            left.representative, right.representative,
        )
        status, outcome_name, payload = _status(outcome), _outcome_name(outcome), _payload(outcome)
    fields = (
        ("plan", plan.plan_digest.encode()), ("point", point_index.to_bytes(8, "big")),
        ("left-index", left_index.to_bytes(8, "big")),
        ("right-index", right_index.to_bytes(8, "big")),
        ("left-stage", left.stage_id.encode()), ("right-stage", right.stage_id.encode()),
        ("observer", observer_id.encode()), ("status", status.value.encode()),
        ("outcome", outcome_name.encode()), ("payload", payload),
    )
    result = TransportResponseRow(
        point_index, left_index, right_index, left.stage_id, right.stage_id,
        observer_id, status, outcome_name, payload, response_row_digest(fields),
    )
    logger.debug("_response_row exit status=%s", status.value)
    return result


def _transport_cell(
    doctrine: ObserverDoctrine, source: FiniteDiagramSource, plan: ForkJoinPlan,
    transport: DirectEchoTransport,
) -> Transport2CellArtifact:
    logger.debug("_transport_cell entry")
    left_join_id = plan.left_join_path_id
    right_join_id = plan.right_join_path_id
    if left_join_id is None or right_join_id is None:
        logger.error("_transport_cell rejected reason=missing-required-joins")
        raise RuntimeError("transport-cell-requires-complete-separate-joins")
    left_ids = _history_stage_ids(source, plan.left_branch_path_id, left_join_id)
    right_ids = _history_stage_ids(source, plan.right_branch_path_id, right_join_id)
    stages = {item.stage_id: item for item in source.stages}
    rows = tuple(
        _response_row(
            plan, point_index, point.left_index, point.right_index,
            stages[left_ids[point.left_index]], stages[right_ids[point.right_index]], observer_id,
        )
        for point_index, point in enumerate(plan.alignment)
        for observer_id in transport.observer_ids
    )
    bad = tuple(item for item in rows if item.status is ConfluenceStatus.REFUTED)
    open_rows = tuple(item for item in rows if item.status is ConfluenceStatus.OPEN)
    status = ConfluenceStatus.REFUTED if bad else (ConfluenceStatus.OPEN if open_rows else ConfluenceStatus.ESTABLISHED)
    first_row = bad[0] if bad else (open_rows[0] if open_rows else None)
    obstruction = None if first_row is None else ConfluenceObstruction(
        "transport-alignment", first_row.point_index, first_row.observer_id,
        first_row.outcome,
    )
    path_commitments = dict(zip((item.path_id for item in source.paths), source.path_commitments, strict=True))
    left_history = joined_history_digest(
        "left", path_commitments[plan.left_branch_path_id],
        path_commitments[left_join_id], plan.plan_digest,
    )
    right_history = joined_history_digest(
        "right", path_commitments[plan.right_branch_path_id],
        path_commitments[right_join_id], plan.plan_digest,
    )
    left_trace = trace_digest("left", left_history, rows)
    right_trace = trace_digest("right", right_history, rows)
    result = Transport2CellArtifact(
        doctrine.fingerprint, source.source_digest, plan.plan_digest,
        plan.fork_stage_commitment, path_commitments[plan.left_branch_path_id],
        path_commitments[plan.right_branch_path_id],
        path_commitments[left_join_id], path_commitments[right_join_id],
        plan.join_stage_commitment or "", transport.observer_ids, transport.mode,
        transport.transport_digest, rows, left_trace, right_trace,
        cell_trace_digest(left_trace, right_trace, plan.plan_digest), obstruction, status,
    )
    logger.debug("_transport_cell exit status=%s rows=%d", status.value, len(rows))
    return result


def fork_confluence_judgment(
    doctrine: ObserverDoctrine, source: FiniteDiagramSource, plan: ForkJoinPlan,
    transport: DirectEchoTransport,
) -> ForkConfluenceJudgment:
    """Replay raw C1 sources; mismatch outranks missing or blocked evidence."""
    logger.debug("fork_confluence_judgment entry")
    doctrine = snapshot_confluence_doctrine(doctrine)
    source = snapshot_finite_diagram_source(source, doctrine)
    transport = snapshot_direct_echo_transport(transport, doctrine)
    plan = snapshot_fork_join_plan(plan, source, transport, doctrine)
    charged = preflight_confluence_checks(ConfluencePreflightCharge(
        _edge_check_count(source, plan), len(plan.alignment), len(transport.observer_ids)
    ))
    mismatches, openings = _check_persistence(source, plan)
    cell: Transport2CellArtifact | None = None
    if plan.left_join_path_id is None:
        openings.append(ConfluenceObstruction("joins", 0, "none", "missing-required-joins"))
    else:
        cell = _transport_cell(doctrine, source, plan, transport)
        if cell.first_obstruction is not None:
            _record(cell.status, cell.first_obstruction, mismatches, openings)
    status = ConfluenceStatus.REFUTED if mismatches else (
        ConfluenceStatus.OPEN if openings else ConfluenceStatus.ESTABLISHED
    )
    first = mismatches[0] if mismatches else (openings[0] if openings else None)
    result = ForkConfluenceJudgment(plan.plan_id, plan.plan_digest, status, cell, first, charged)
    logger.debug("fork_confluence_judgment exit status=%s checks=%d", status.value, charged)
    return result
