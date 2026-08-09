"""Hard-first generated local-to-global confluence runtime."""

from __future__ import annotations

from dataclasses import replace
import logging

from .common import exact_digest, exact_text, reject
from .digest import (
    blocked_cell_digest,
    join_cell_digest,
    result_digest,
    row_digest,
)
from .formal import (
    check_generated_confluence_theorem,
    generated_confluence_theorem_source,
)
from .paths import (
    branch_targets,
    generated_local_peaks,
    generated_reachable,
    replay_edge_path,
)
from .preflight import resource_preflight
from .source import snapshot_ranked_system
from .types import (
    BlockedLocalJoinCell,
    CellMode,
    GeneratedConfluenceResult,
    GeneratedConfluenceStatus,
    GeneratedFiniteConfluence,
    LocalCell,
    LocalJoinCell,
    LocalPeakRow,
    P3C1_NONCLAIMS,
    RankedContinuationSystem,
)

logger = logging.getLogger(__name__)
ZERO_DIGEST = "0" * 64


def local_join_cell(
    system: RankedContinuationSystem,
    peak_id: str,
    left_edge_ids: tuple[str, ...],
    right_edge_ids: tuple[str, ...],
    claimed_join_state_id: str,
    mode: CellMode = CellMode.PURE_RELATION_PATH,
) -> LocalJoinCell:
    """Bind pure same-relation paths; no C1/C3 transport evidence is minted."""
    logger.debug("local_join_cell entry")
    system = snapshot_ranked_system(system)
    exact_text(peak_id, "peak-id")
    exact_text(claimed_join_state_id, "join-state")
    if type(left_edge_ids) is not tuple or type(right_edge_ids) is not tuple:
        reject("join-cell-path-container-invalid")
    if any(type(item) is not str for item in (*left_edge_ids, *right_edge_ids)):
        reject("join-cell-path-item-type-invalid")
    if type(mode) is not CellMode or mode is not CellMode.PURE_RELATION_PATH:
        reject("join-cell-mode-invalid")
    value = LocalJoinCell(
        peak_id,
        tuple(left_edge_ids),
        tuple(right_edge_ids),
        claimed_join_state_id,
        mode,
        system.system_digest,
        "",
    )
    result = replace(value, cell_digest=join_cell_digest(value))
    logger.debug("local_join_cell exit peak=%s", peak_id)
    return result


def blocked_local_join_cell(system: RankedContinuationSystem, peak_id: str, obstruction: str) -> BlockedLocalJoinCell:
    """Bind one explicit pure-relation domain obstruction."""
    logger.debug("blocked_local_join_cell entry")
    system = snapshot_ranked_system(system)
    exact_text(peak_id, "peak-id")
    exact_text(obstruction, "local-obstruction")
    value = BlockedLocalJoinCell(peak_id, obstruction, system.system_digest, "")
    result = replace(value, cell_digest=blocked_cell_digest(value))
    logger.debug("blocked_local_join_cell exit peak=%s", peak_id)
    return result


def generated_finite_confluence(
    raw_system: RankedContinuationSystem,
    raw_cells: tuple[LocalCell, ...],
) -> GeneratedConfluenceResult:
    """Derive complete peaks and apply TLGC only after hard atomic preflight."""
    logger.debug("generated_finite_confluence entry")
    refusal = resource_preflight(raw_system, raw_cells)
    if refusal is not None:
        logger.debug("generated_finite_confluence exit resource=%s", refusal.failed_bound.value)
        return refusal
    system = snapshot_ranked_system(raw_system)
    cells = _snapshot_cells(system, raw_cells)
    reachable_states, reachable_edges = generated_reachable(system)
    peaks = generated_local_peaks(system)
    peak_ids = {peak.peak_id for peak in peaks}
    if any(cell.peak_id not in peak_ids for cell in cells):
        reject("foreign-local-cell")
    by_peak = {cell.peak_id: cell for cell in cells}
    rows = tuple(_peak_row(system, peak, by_peak.get(peak.peak_id)) for peak in peaks)
    status = _aggregate_status(rows)
    first = next(
        (
            row.peak.peak_id
            for row in rows
            if row.status is status
            and status is not GeneratedConfluenceStatus.GENERATED_FINITE_CONFLUENT_RELATIVE_TO_SYSTEM
        ),
        None,
    )
    theorem_source = generated_confluence_theorem_source()
    if status is GeneratedConfluenceStatus.GENERATED_FINITE_CONFLUENT_RELATIVE_TO_SYSTEM:
        receipt, phases = check_generated_confluence_theorem(theorem_source)
    else:
        receipt, phases = ZERO_DIGEST, ()
    value = GeneratedFiniteConfluence(
        system.system_digest,
        reachable_states,
        reachable_edges,
        peaks,
        rows,
        theorem_source,
        receipt,
        phases,
        status,
        first,
        P3C1_NONCLAIMS,
        "",
    )
    result = replace(value, result_digest=result_digest(value))
    logger.debug("generated_finite_confluence exit status=%s peaks=%d", status.value, len(peaks))
    return result


def _snapshot_cells(system: RankedContinuationSystem, raw_cells: tuple[LocalCell, ...]) -> tuple[LocalCell, ...]:
    logger.debug("_snapshot_cells entry cells=%d", len(raw_cells))
    result = tuple(_snapshot_cell(system, cell) for cell in raw_cells)
    ids = tuple(cell.peak_id for cell in result)
    if len(set(ids)) != len(ids):
        reject("duplicate-local-cell")
    logger.debug("_snapshot_cells exit")
    return result


def _snapshot_cell(system: RankedContinuationSystem, raw: LocalCell) -> LocalCell:
    logger.debug("_snapshot_cell entry")
    if type(raw) is LocalJoinCell:
        for label, value in (("peak-id", raw.peak_id), ("join-state", raw.claimed_join_state_id)):
            exact_text(value, label)
        if type(raw.mode) is not CellMode or raw.mode is not CellMode.PURE_RELATION_PATH:
            reject("join-cell-mode-invalid")
        if type(raw.left_edge_ids) is not tuple or type(raw.right_edge_ids) is not tuple:
            reject("join-cell-shape-invalid")
        if any(type(item) is not str for item in (*raw.left_edge_ids, *raw.right_edge_ids)):
            reject("join-cell-path-item-type-invalid")
        exact_digest(raw.system_digest, "cell-system-digest")
        exact_digest(raw.cell_digest, "cell-digest")
        if raw.system_digest != system.system_digest or join_cell_digest(raw) != raw.cell_digest:
            reject("join-cell-commitment-mismatch")
        result = LocalJoinCell(
            raw.peak_id,
            tuple(raw.left_edge_ids),
            tuple(raw.right_edge_ids),
            raw.claimed_join_state_id,
            raw.mode,
            raw.system_digest,
            raw.cell_digest,
        )
        logger.debug("_snapshot_cell exit type=join")
        return result
    if type(raw) is BlockedLocalJoinCell:
        exact_text(raw.peak_id, "peak-id")
        exact_text(raw.obstruction, "local-obstruction")
        exact_digest(raw.system_digest, "cell-system-digest")
        exact_digest(raw.cell_digest, "cell-digest")
        if raw.system_digest != system.system_digest or blocked_cell_digest(raw) != raw.cell_digest:
            reject("blocked-cell-commitment-mismatch")
        result = BlockedLocalJoinCell(
            raw.peak_id,
            raw.obstruction,
            raw.system_digest,
            raw.cell_digest,
        )
        logger.debug("_snapshot_cell exit type=blocked")
        return result
    reject("local-cell-type-invalid")


def _peak_row(system, peak, cell) -> LocalPeakRow:
    logger.debug("_peak_row entry peak=%s", peak.peak_id)
    if cell is None or type(cell) is BlockedLocalJoinCell:
        value = LocalPeakRow(
            peak, None if cell is None else cell.cell_digest, None, None, GeneratedConfluenceStatus.OPEN, ""
        )
    else:
        left_start, right_start = branch_targets(system, peak)
        left_end = replay_edge_path(system, left_start, cell.left_edge_ids)
        right_end = replay_edge_path(system, right_start, cell.right_edge_ids)
        if cell.claimed_join_state_id not in {state.state_id for state in system.states}:
            reject("claimed-join-state-foreign")
        status = (
            GeneratedConfluenceStatus.GENERATED_FINITE_CONFLUENT_RELATIVE_TO_SYSTEM
            if left_end == right_end == cell.claimed_join_state_id
            else GeneratedConfluenceStatus.REFUTED
        )
        value = LocalPeakRow(peak, cell.cell_digest, left_end, right_end, status, "")
    result = replace(value, row_digest=row_digest(value))
    logger.debug("_peak_row exit status=%s", result.status.value)
    return result


def _aggregate_status(rows: tuple[LocalPeakRow, ...]) -> GeneratedConfluenceStatus:
    logger.debug("_aggregate_status entry rows=%d", len(rows))
    statuses = tuple(row.status for row in rows)
    result = (
        GeneratedConfluenceStatus.REFUTED
        if GeneratedConfluenceStatus.REFUTED in statuses
        else (
            GeneratedConfluenceStatus.OPEN
            if GeneratedConfluenceStatus.OPEN in statuses
            else GeneratedConfluenceStatus.GENERATED_FINITE_CONFLUENT_RELATIVE_TO_SYSTEM
        )
    )
    logger.debug("_aggregate_status exit status=%s", result.value)
    return result
