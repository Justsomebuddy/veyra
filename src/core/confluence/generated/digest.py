"""Canonical commitments for P3-C1 generated confluence."""

from __future__ import annotations

import logging

from .common import digest, texts
from .types import (
    BlockedLocalJoinCell,
    GeneratedConfluenceTheoremSource,
    LocalJoinCell,
    LocalPeakRow,
    RankedContinuationSystem,
)

logger = logging.getLogger(__name__)


def state_digest(state_id: str, kind: str, payload: bytes) -> str:
    logger.debug("state_digest entry id=%s", state_id)
    result = digest("veyra.p3c1.state.v1", (("id", state_id.encode()), ("kind", kind.encode()), ("payload", payload)))
    logger.debug("state_digest exit id=%s", state_id)
    return result


def edge_digest(edge_id: str, source: str, target: str, kind: str, payload: bytes) -> str:
    logger.debug("edge_digest entry id=%s", edge_id)
    result = digest(
        "veyra.p3c1.edge.v1",
        (
            ("id", edge_id.encode()),
            ("source", source.encode()),
            ("target", target.encode()),
            ("kind", kind.encode()),
            ("payload", payload),
        ),
    )
    logger.debug("edge_digest exit id=%s", edge_id)
    return result


def system_digest(value: RankedContinuationSystem) -> str:
    logger.debug("system_digest entry")
    rows = (
        ("version", value.version.encode()),
        ("doctrine", value.doctrine_fingerprint.encode()),
        ("source", value.source_id.encode()),
        ("source-version", value.source_version.encode()),
        *texts("state", tuple(item.state_commitment for item in value.states)),
        *texts("edge", tuple(item.edge_commitment for item in value.edges)),
        *texts("root", value.roots),
        *tuple(("rank", f"{item.state_id}:{item.rank}".encode()) for item in value.ranks),
        ("scope", value.scope.encode()),
    )
    result = digest("veyra.p3c1.system.v1", rows)
    logger.debug("system_digest exit")
    return result


def peak_digest(system: str, source: str, left: str, right: str) -> str:
    logger.debug("peak_digest entry source=%s", source)
    result = digest(
        "veyra.p3c1.peak.v1",
        (
            ("system", system.encode()),
            ("source", source.encode()),
            ("left", left.encode()),
            ("right", right.encode()),
        ),
    )
    logger.debug("peak_digest exit source=%s", source)
    return result


def join_cell_digest(value: LocalJoinCell) -> str:
    logger.debug("join_cell_digest entry peak=%s", value.peak_id)
    result = digest(
        "veyra.p3c1.join-cell.v1",
        (
            ("peak", value.peak_id.encode()),
            *texts("left-edge", value.left_edge_ids),
            *texts("right-edge", value.right_edge_ids),
            ("join", value.claimed_join_state_id.encode()),
            ("mode", value.mode.value.encode()),
            ("system", value.system_digest.encode()),
        ),
    )
    logger.debug("join_cell_digest exit peak=%s", value.peak_id)
    return result


def blocked_cell_digest(value: BlockedLocalJoinCell) -> str:
    logger.debug("blocked_cell_digest entry peak=%s", value.peak_id)
    result = digest(
        "veyra.p3c1.blocked-cell.v1",
        (
            ("peak", value.peak_id.encode()),
            ("obstruction", value.obstruction.encode()),
            ("system", value.system_digest.encode()),
        ),
    )
    logger.debug("blocked_cell_digest exit peak=%s", value.peak_id)
    return result


def row_digest(value: LocalPeakRow) -> str:
    logger.debug("row_digest entry peak=%s", value.peak.peak_id)
    result = digest(
        "veyra.p3c1.row.v1",
        (
            ("peak", value.peak.peak_digest.encode()),
            ("cell", (value.cell_digest or "").encode()),
            ("left-end", (value.left_endpoint_id or "").encode()),
            ("right-end", (value.right_endpoint_id or "").encode()),
            ("status", value.status.value.encode()),
        ),
    )
    logger.debug("row_digest exit peak=%s", value.peak.peak_id)
    return result


def theorem_source_digest(value: GeneratedConfluenceTheoremSource) -> str:
    logger.debug("theorem_source_digest entry")
    result = digest(
        "veyra.p3c1.formal-source.v1",
        (
            ("version", value.version.encode()),
            ("path", value.artifact_path.encode()),
            ("sha", value.artifact_sha256.encode()),
            *texts("theorem", value.theorem_ids),
            ("toolchain", value.toolchain_id.encode()),
            ("elan", value.elan_sha256.encode()),
            ("lean", value.lean_sha256.encode()),
            ("lean-version", value.lean_version.encode()),
            ("tcb", value.tcb_digest.encode()),
        ),
    )
    logger.debug("theorem_source_digest exit")
    return result


def result_digest(value) -> str:
    """Bind one exact P3-C1 semantic result."""
    logger.debug("result_digest entry")
    result = digest(
        "veyra.p3c1.result.v1",
        (
            ("system", value.system_digest.encode()),
            *texts("reachable-state", value.reachable_state_ids),
            *texts("reachable-edge", value.reachable_edge_ids),
            *texts("peak", tuple(item.peak_digest for item in value.peaks)),
            *texts("row", tuple(item.row_digest for item in value.rows)),
            ("formal-source", value.theorem_source.source_digest.encode()),
            ("formal-receipt", value.theorem_receipt_digest.encode()),
            *tuple(
                ("formal-phase", f"{row.phase}:{row.return_code}:{row.output_bytes}:{row.output_digest}".encode())
                for row in value.theorem_phase_receipts
            ),
            ("status", value.status.value.encode()),
            ("first", (value.first_counterexample_peak_id or "").encode()),
            *texts("nonclaim", value.nonclaims),
        ),
    )
    logger.debug("result_digest exit")
    return result
