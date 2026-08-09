"""Atomic hard-first raw charging for P3-C1."""

from __future__ import annotations

from hashlib import sha256
import logging

from .common import exact_shape, reject
from .source import MAX_CANONICAL_BYTES, MAX_EDGES, MAX_STATES
from .types import (
    BlockedLocalJoinCell,
    CellMode,
    ContinuationEdge,
    ContinuationState,
    FailedBound,
    GeneratedConfluenceResourceLimit,
    GeneratedFailureKind,
    LocalCell,
    LocalJoinCell,
    P3C1_NONCLAIMS,
    RankedContinuationSystem,
    StateRank,
)

logger = logging.getLogger(__name__)
MAX_LOCAL_CELLS = 16_384


def resource_preflight(
    raw_system: RankedContinuationSystem,
    raw_cells: tuple[LocalCell, ...],
) -> GeneratedConfluenceResourceLimit | None:
    """Charge all raw nested bytes/types before any digest or semantic replay."""
    logger.debug("resource_preflight entry")
    exact_shape(raw_system, RankedContinuationSystem, "ranked-system")
    for name in ("states", "edges", "roots", "ranks"):
        if type(object.__getattribute__(raw_system, name)) is not tuple:
            reject("ranked-system-container-type-invalid")
    if type(raw_cells) is not tuple:
        reject("local-cells-container-type-invalid")
    limits = (
        (FailedBound.STATES, len(raw_system.states), MAX_STATES),
        (FailedBound.EDGES, len(raw_system.edges), MAX_EDGES),
        (FailedBound.LOCAL_CELLS, len(raw_cells), MAX_LOCAL_CELLS),
    )
    failed = next((row for row in limits if row[1] > row[2]), None)
    if failed is not None:
        result = _resource_result(failed, raw_system, raw_cells, 0)
        logger.debug("resource_preflight exit failed=%s", result.failed_bound.value)
        return result
    size = _raw_byte_size(raw_system, raw_cells)
    if size > MAX_CANONICAL_BYTES:
        failed = (FailedBound.CANONICAL_BYTES, size, MAX_CANONICAL_BYTES)
        result = _resource_result(failed, raw_system, raw_cells, size)
        logger.debug("resource_preflight exit failed=%s", result.failed_bound.value)
        return result
    logger.debug("resource_preflight exit ok bytes=%d", size)
    return None


def _resource_result(failed, system, cells, size) -> GeneratedConfluenceResourceLimit:
    logger.debug("_resource_result entry")
    bound, required, allowed = failed
    hint = sha256(f"p3c1:{len(system.states)}:{len(system.edges)}:{len(cells)}:{size}".encode()).hexdigest()
    refusal = sha256(f"p3c1-refusal:{bound.value}:{required}:{allowed}:{hint}".encode()).hexdigest()
    result = GeneratedConfluenceResourceLimit(
        GeneratedFailureKind.RESOURCE_LIMIT,
        bound,
        required,
        allowed,
        hint,
        P3C1_NONCLAIMS,
        refusal,
    )
    logger.debug("_resource_result exit failed=%s", bound.value)
    return result


def _raw_byte_size(system: RankedContinuationSystem, cells: tuple[LocalCell, ...]) -> int:
    logger.debug("_raw_byte_size entry")
    total = sum(
        _text(object.__getattribute__(system, name), f"system-{name}")
        for name in (
            "version",
            "doctrine_fingerprint",
            "source_id",
            "source_version",
            "system_digest",
            "scope",
        )
    )
    for state in system.states:
        exact_shape(state, ContinuationState, "preflight-state")
        total += _text(state.state_id, "state-id") + _text(state.kind, "state-kind")
        total += _bytes(state.payload, "state-payload") + _text(state.state_commitment, "state-commitment")
    for edge in system.edges:
        exact_shape(edge, ContinuationEdge, "preflight-edge")
        for name in ("edge_id", "source_id", "target_id", "rule_kind", "edge_commitment"):
            total += _text(object.__getattribute__(edge, name), f"edge-{name}")
        total += _bytes(edge.rule_payload, "edge-rule-payload")
    for root in system.roots:
        total += _text(root, "root-item")
    for rank in system.ranks:
        exact_shape(rank, StateRank, "preflight-rank")
        total += _text(rank.state_id, "rank-state-id") + _integer(rank.rank, "rank-value")
    for cell in cells:
        total += _cell_bytes(cell)
    logger.debug("_raw_byte_size exit bytes=%d", total)
    return total


def _cell_bytes(cell: LocalCell) -> int:
    logger.debug("_cell_bytes entry")
    if type(cell) is LocalJoinCell:
        total = sum(
            _text(object.__getattribute__(cell, name), f"cell-{name}")
            for name in (
                "peak_id",
                "claimed_join_state_id",
                "system_digest",
                "cell_digest",
            )
        )
        if type(cell.mode) is not CellMode:
            reject("cell-mode-type-invalid")
        total += _text(cell.mode.value, "cell-mode")
        for name in ("left_edge_ids", "right_edge_ids"):
            path = object.__getattribute__(cell, name)
            if type(path) is not tuple:
                reject("cell-path-container-type-invalid")
            total += sum(_text(item, "cell-path-item") for item in path)
        logger.debug("_cell_bytes exit type=join bytes=%d", total)
        return total
    if type(cell) is BlockedLocalJoinCell:
        total = sum(
            _text(object.__getattribute__(cell, name), f"blocked-{name}")
            for name in (
                "peak_id",
                "obstruction",
                "system_digest",
                "cell_digest",
            )
        )
        logger.debug("_cell_bytes exit type=blocked bytes=%d", total)
        return total
    reject("preflight-cell-type-invalid")


def _text(value: object, label: str) -> int:
    logger.debug("_text entry label=%s", label)
    if type(value) is not str:
        reject(f"{label}-type-invalid")
    try:
        result = len(value.encode("utf-8"))
    except UnicodeError:
        reject(f"{label}-utf8-invalid")
    logger.debug("_text exit label=%s bytes=%d", label, result)
    return result


def _bytes(value: object, label: str) -> int:
    logger.debug("_bytes entry label=%s", label)
    if type(value) is not bytes:
        reject(f"{label}-type-invalid")
    result = len(value)
    logger.debug("_bytes exit label=%s bytes=%d", label, result)
    return result


def _integer(value: object, label: str) -> int:
    logger.debug("_integer entry label=%s", label)
    if type(value) is not int:
        reject(f"{label}-type-invalid")
    logger.debug("_integer exit label=%s", label)
    return 8
