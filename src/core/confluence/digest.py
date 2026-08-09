"""Tagged and counted SHA-256 commitments for provisional P1-C1."""

from __future__ import annotations

from hashlib import sha256
import logging

from .types import AlignmentPoint, DiagramEdge, TransportResponseRow

logger = logging.getLogger(__name__)


def _digest(domain: str, fields: tuple[tuple[str, bytes], ...]) -> str:
    """Hash an exact tagged field stream with explicit field count."""
    logger.debug("_digest entry domain=%s fields=%d", domain, len(fields))
    digest = sha256()
    _token(digest, b"domain", domain.encode())
    _token(digest, b"field-count", len(fields).to_bytes(8, "big"))
    for tag, value in fields:
        _token(digest, tag.encode(), value)
    result = digest.hexdigest()
    logger.debug("_digest exit domain=%s", domain)
    return result


def _token(digest: object, tag: bytes, value: bytes) -> None:
    """Write one independently length-prefixed tag/value token."""
    logger.debug("_token entry tag_bytes=%d value_bytes=%d", len(tag), len(value))
    digest.update(len(tag).to_bytes(4, "big"))  # type: ignore[attr-defined]
    digest.update(tag)  # type: ignore[attr-defined]
    digest.update(len(value).to_bytes(8, "big"))  # type: ignore[attr-defined]
    digest.update(value)  # type: ignore[attr-defined]
    logger.debug("_token exit")


def edge_digest(doctrine_fingerprint: str, edge: DiagramEdge) -> str:
    """Commit one edge and its ordered preserved observer family."""
    logger.debug("edge_digest entry observers=%d", len(edge.preserved_observer_ids))
    fields = [
        ("doctrine", doctrine_fingerprint.encode()), ("edge-id", edge.edge_id.encode()),
        ("lower", edge.lower_stage_id.encode()), ("upper", edge.upper_stage_id.encode()),
        ("observer-count", len(edge.preserved_observer_ids).to_bytes(8, "big")),
    ]
    fields.extend((f"observer-{i}", item.encode()) for i, item in enumerate(edge.preserved_observer_ids))
    result = _digest("veyra.p1c1.edge.v1", tuple(fields))
    logger.debug("edge_digest exit")
    return result


def path_digest(
    source_id: str, doctrine_fingerprint: str, path_id: str,
    edge_ids: tuple[str, ...], stage_commitments: tuple[str, ...],
) -> str:
    """Commit ordered path edges and every reconstructed stage occurrence."""
    logger.debug("path_digest entry edges=%d stages=%d", len(edge_ids), len(stage_commitments))
    fields = [
        ("source-id", source_id.encode()), ("doctrine", doctrine_fingerprint.encode()),
        ("path-id", path_id.encode()), ("edge-count", len(edge_ids).to_bytes(8, "big")),
    ]
    fields.extend((f"edge-{i}", item.encode()) for i, item in enumerate(edge_ids))
    fields.append(("stage-count", len(stage_commitments).to_bytes(8, "big")))
    fields.extend((f"stage-{i}", item.encode()) for i, item in enumerate(stage_commitments))
    result = _digest("veyra.p1c1.path.v1", tuple(fields))
    logger.debug("path_digest exit")
    return result


def diagram_digest(
    version: str, scope: str, source_id: str, doctrine_fingerprint: str,
    stage_commitments: tuple[str, ...], edge_commitments: tuple[str, ...],
    path_commitments: tuple[str, ...],
) -> str:
    """Commit the exact ordered generic finite-diagram source."""
    logger.debug("diagram_digest entry stages=%d edges=%d paths=%d", len(stage_commitments), len(edge_commitments), len(path_commitments))
    fields = [
        ("version", version.encode()), ("scope", scope.encode()),
        ("source-id", source_id.encode()), ("doctrine", doctrine_fingerprint.encode()),
        ("stage-count", len(stage_commitments).to_bytes(8, "big")),
    ]
    fields.extend((f"stage-{i}", item.encode()) for i, item in enumerate(stage_commitments))
    fields.append(("edge-count", len(edge_commitments).to_bytes(8, "big")))
    fields.extend((f"edge-{i}", item.encode()) for i, item in enumerate(edge_commitments))
    fields.append(("path-count", len(path_commitments).to_bytes(8, "big")))
    fields.extend((f"path-{i}", item.encode()) for i, item in enumerate(path_commitments))
    result = _digest("veyra.p1c1.diagram.v1", tuple(fields))
    logger.debug("diagram_digest exit")
    return result


def direct_transport_digest(doctrine_fingerprint: str, observer_ids: tuple[str, ...]) -> str:
    """Commit the only C1 transport grammar."""
    logger.debug("direct_transport_digest entry observers=%d", len(observer_ids))
    fields = [
        ("mode", b"direct-echo"), ("doctrine", doctrine_fingerprint.encode()),
        ("observer-count", len(observer_ids).to_bytes(8, "big")),
    ]
    fields.extend((f"observer-{i}", item.encode()) for i, item in enumerate(observer_ids))
    result = _digest("veyra.p1c1.transport.v1", tuple(fields))
    logger.debug("direct_transport_digest exit")
    return result


def fork_plan_digest(
    version: str, scope: str, plan_id: str, diagram: str, fork: str,
    path_commitments: tuple[str, str, str | None, str | None],
    join: str | None, alignment: tuple[AlignmentPoint, ...], transport: str,
) -> str:
    """Commit every fork, join, alignment, and transport plan component."""
    logger.debug("fork_plan_digest entry alignment=%d", len(alignment))
    fields = [
        ("version", version.encode()), ("scope", scope.encode()),
        ("plan-id", plan_id.encode()), ("diagram", diagram.encode()), ("fork", fork.encode()),
        ("left-branch", path_commitments[0].encode()),
        ("right-branch", path_commitments[1].encode()),
        ("joins-present", b"1" if join is not None else b"0"),
        ("left-join", b"" if path_commitments[2] is None else path_commitments[2].encode()),
        ("right-join", b"" if path_commitments[3] is None else path_commitments[3].encode()),
        ("join-stage", b"" if join is None else join.encode()),
        ("alignment-count", len(alignment).to_bytes(8, "big")),
    ]
    fields.extend((f"alignment-{i}", f"{p.left_index}:{p.right_index}".encode()) for i, p in enumerate(alignment))
    fields.append(("transport", transport.encode()))
    result = _digest("veyra.p1c1.plan.v1", tuple(fields))
    logger.debug("fork_plan_digest exit")
    return result


def response_row_digest(fields: tuple[tuple[str, bytes], ...]) -> str:
    """Commit a complete derived response row."""
    logger.debug("response_row_digest entry fields=%d", len(fields))
    result = _digest("veyra.p1c1.response-row.v1", fields)
    logger.debug("response_row_digest exit")
    return result


def trace_digest(side: str, history: str, rows: tuple[TransportResponseRow, ...]) -> str:
    """Commit one ordered joined-history trace."""
    logger.debug("trace_digest entry side=%s rows=%d", side, len(rows))
    fields = [("side", side.encode()), ("history", history.encode()), ("row-count", len(rows).to_bytes(8, "big"))]
    fields.extend((f"row-{i}", row.row_digest.encode()) for i, row in enumerate(rows))
    result = _digest("veyra.p1c1.trace.v1", tuple(fields))
    logger.debug("trace_digest exit side=%s", side)
    return result


def joined_history_digest(side: str, branch: str, join: str, plan: str) -> str:
    """Bind one complete branch-plus-join history before trace hashing."""
    logger.debug("joined_history_digest entry side=%s", side)
    result = _digest(
        "veyra.p1c1.joined-history.v1",
        (("side", side.encode()), ("plan", plan.encode()),
         ("branch", branch.encode()), ("join", join.encode())),
    )
    logger.debug("joined_history_digest exit side=%s", side)
    return result


def cell_trace_digest(left: str, right: str, plan: str) -> str:
    """Bind both directional traces to the exact plan."""
    logger.debug("cell_trace_digest entry")
    result = _digest("veyra.p1c1.cell-trace.v1", (("plan", plan.encode()), ("left", left.encode()), ("right", right.encode())))
    logger.debug("cell_trace_digest exit")
    return result
