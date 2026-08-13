"""Domain-separated encodings for realization transport evidence."""

from __future__ import annotations

from hashlib import sha256
import logging

from .types import (
    ClosureActionRow,
    ContextMorphism,
    CostTransportRow,
    EvaluationCommutingRow,
    RecurrenceCommutingRow,
)

logger = logging.getLogger(__name__)


def _field(tag: str, payload: bytes) -> bytes:
    """Frame a named byte string injectively."""
    logger.debug("transport _field entry tag=%s bytes=%d", tag, len(payload))
    name = tag.encode("ascii")
    result = len(name).to_bytes(2, "big") + name + len(payload).to_bytes(8, "big") + payload
    logger.debug("transport _field exit tag=%s", tag)
    return result


def _sequence(tag: str, rows: tuple[bytes, ...]) -> bytes:
    """Frame an ordered bounded sequence."""
    logger.debug("transport _sequence entry tag=%s rows=%d", tag, len(rows))
    result = _field(tag, len(rows).to_bytes(4, "big") + b"".join(_field("row", row) for row in rows))
    logger.debug("transport _sequence exit tag=%s", tag)
    return result


def _digest(domain: str, *fields: bytes) -> str:
    """Hash one versioned domain and its exact framed fields."""
    logger.debug("transport _digest entry domain=%s fields=%d", domain, len(fields))
    result = sha256(_field("domain", domain.encode("ascii")) + b"".join(fields)).hexdigest()
    logger.debug("transport _digest exit domain=%s", domain)
    return result


def context_morphism_digest(
    morphism_id: str,
    source_context_digest: str,
    target_context_digest: str,
    state_index_map: tuple[int, ...],
    version: str,
) -> str:
    """Commit to a total ordered index graph and both endpoints."""
    logger.debug("context_morphism_digest entry edges=%d", len(state_index_map))
    result = _digest(
        "veyra.p1-r16.context-morphism.v1",
        _field("id", morphism_id.encode("utf-8")),
        _field("source", source_context_digest.encode("ascii")),
        _field("target", target_context_digest.encode("ascii")),
        _sequence("graph", tuple(index.to_bytes(4, "big") for index in state_index_map)),
        _field("version", version.encode("ascii")),
    )
    logger.debug("context_morphism_digest exit")
    return result


def transport_receipt_digest(
    schema: str,
    doctrine_fingerprint: str,
    source_context_digest: str,
    target_context_digest: str,
    source_witness_digest: str,
    target_witness_digest: str,
    morphism: ContextMorphism,
    recurrence_rows: tuple[RecurrenceCommutingRow, ...],
    evaluation_rows: tuple[EvaluationCommutingRow, ...],
    closure_action: tuple[ClosureActionRow, ...],
    cost_rows: tuple[CostTransportRow, ...],
    bottom_preserved: bool,
    joins_preserved: bool,
    scope: str,
) -> str:
    """Commit to every reconstructible field of one transport receipt."""
    logger.debug(
        "transport_receipt_digest entry recurrences=%d evaluations=%d closure=%d",
        len(recurrence_rows), len(evaluation_rows), len(closure_action),
    )
    recurrence_bytes = tuple(
        _field("source-index", row.source_index.to_bytes(4, "big"))
        + _field("target-index", row.target_index.to_bytes(4, "big"))
        + _field("source-input", row.source_input_commitment.encode("ascii"))
        + _field("target-input", row.target_input_commitment.encode("ascii"))
        for row in recurrence_rows
    )
    evaluation_bytes = tuple(
        _field("observer", row.observer_id.encode("utf-8"))
        + _field("source-index", row.source_index.to_bytes(4, "big"))
        + _field("target-index", row.target_index.to_bytes(4, "big"))
        + _field("status", row.status.value.encode("ascii"))
        + _field("payload", row.payload_digest.encode("ascii"))
        for row in evaluation_rows
    )
    action_bytes = tuple(
        _field("target-partition", row.target_partition_digest.encode("ascii"))
        + _sequence("source-partition", tuple(item.to_bytes(4, "big") for item in row.source_partition))
        + _field("source-partition-digest", row.source_partition_digest.encode("ascii"))
        + _field("source-closure-index", row.source_closure_index.to_bytes(4, "big"))
        for row in closure_action
    )
    cost_bytes = tuple(
        _field("target-partition", row.target_partition_digest.encode("ascii"))
        + _field("source-partition", row.source_partition_digest.encode("ascii"))
        + _field("source-cost", row.source_cost.to_bytes(8, "big"))
        + _field("target-cost", row.target_cost.to_bytes(8, "big"))
        + _field("status", row.status.value.encode("ascii"))
        for row in cost_rows
    )
    result = _digest(
        "veyra.p1-r16.realization-transport-receipt.v1",
        _field("schema", schema.encode("ascii")),
        _field("doctrine", doctrine_fingerprint.encode("ascii")),
        _field("source-context", source_context_digest.encode("ascii")),
        _field("target-context", target_context_digest.encode("ascii")),
        _field("source-witness", source_witness_digest.encode("ascii")),
        _field("target-witness", target_witness_digest.encode("ascii")),
        _field("morphism", morphism.morphism_digest.encode("ascii")),
        _sequence("recurrence", recurrence_bytes),
        _sequence("evaluation", evaluation_bytes),
        _sequence("closure-action", action_bytes),
        _sequence("costs", cost_bytes),
        _field("bottom", b"1" if bottom_preserved else b"0"),
        _field("joins", b"1" if joins_preserved else b"0"),
        _field("scope", scope.encode("ascii")),
    )
    logger.debug("transport_receipt_digest exit")
    return result
