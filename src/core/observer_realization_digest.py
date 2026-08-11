"""Domain-separated canonical digests for P1-to-R16 realization."""

from __future__ import annotations

from hashlib import sha256
import logging

from .observer_descent_validation import snapshot_doctrine, snapshot_observer
from .observer_realization_types import (
    ObserverCost,
    RealizationClosureRow,
    RealizationEvaluationRow,
)

logger = logging.getLogger(__name__)
MAX_CANONICAL_INT_BITS = 4096


def _field(tag: str, payload: bytes) -> bytes:
    """Frame a named byte field without concatenation ambiguity."""
    logger.debug("realization _field entry tag=%s bytes=%d", tag, len(payload))
    encoded = tag.encode("ascii")
    result = (
        len(encoded).to_bytes(2, "big")
        + encoded
        + len(payload).to_bytes(8, "big")
        + payload
    )
    logger.debug("realization _field exit tag=%s", tag)
    return result


def _sequence(tag: str, items: tuple[bytes, ...]) -> bytes:
    """Frame one ordered sequence and its exact item count."""
    logger.debug("realization _sequence entry tag=%s count=%d", tag, len(items))
    payload = len(items).to_bytes(4, "big") + b"".join(
        _field("item", item) for item in items
    )
    result = _field(tag, payload)
    logger.debug("realization _sequence exit tag=%s", tag)
    return result


def _digest(domain: str, *fields: bytes) -> str:
    """Hash one exact versioned domain and ordered framed payload."""
    logger.debug("realization _digest entry domain=%s fields=%d", domain, len(fields))
    result = sha256(_field("domain", domain.encode("ascii")) + b"".join(fields)).hexdigest()
    logger.debug("realization _digest exit domain=%s", domain)
    return result


def canonical_finite_value(value: object) -> bytes:
    """Encode an already validated R16 scalar/tuple value injectively."""
    logger.debug("canonical_finite_value entry")
    if value is None:
        result = _field("none", b"")
    elif type(value) is int:
        magnitude = abs(value)
        if magnitude.bit_length() > MAX_CANONICAL_INT_BITS:
            logger.error("canonical_finite_value integer limit exceeded")
            raise ValueError("realization-finite-integer-limit")
        width = max(1, (magnitude.bit_length() + 7) // 8)
        result = _field("int-sign", b"-" if value < 0 else b"+") + _field(
            "int-magnitude", magnitude.to_bytes(width, "big")
        )
    elif type(value) is str:
        result = _field("text", value.encode("utf-8"))
    elif type(value) is bytes:
        result = _field("bytes", value)
    elif type(value) is tuple:
        result = _sequence(
            "tuple", tuple(canonical_finite_value(item) for item in value)
        )
    else:
        logger.error("canonical_finite_value rejected unsupported exact type")
        raise TypeError("realization-finite-value-not-canonical")
    logger.debug("canonical_finite_value exit bytes=%d", len(result))
    return result


def recurrence_commitment(canonical: bytes) -> str:
    """Commit to one validated canonical recurrence encoding."""
    logger.debug("recurrence_commitment entry bytes=%d", len(canonical))
    result = _digest("veyra.p1-r16.input.v1", _field("recurrence", canonical))
    logger.debug("recurrence_commitment exit")
    return result


def realization_context_digest(
    doctrine_fingerprint: str,
    realization_id: str,
    input_rows: tuple[tuple[object, bytes], ...],
    costs: tuple[ObserverCost, ...],
    response_policy: str,
    cost_policy: str,
    closure_policy: str,
    version: str,
) -> str:
    """Commit to every external choice of one relative realization."""
    logger.debug(
        "realization_context_digest entry inputs=%d costs=%d",
        len(input_rows),
        len(costs),
    )
    inputs = tuple(
        _field("state", canonical_finite_value(state))
        + _field("recurrence", recurrence)
        for state, recurrence in input_rows
    )
    cost_rows = tuple(
        _field("observer-id", item.observer_id.encode("utf-8"))
        + _field("cost", item.cost.to_bytes(8, "big"))
        for item in costs
    )
    result = _digest(
        "veyra.p1-r16.realization-context.v1",
        _field("source-doctrine", doctrine_fingerprint.encode("ascii")),
        _field("realization-id", realization_id.encode("utf-8")),
        _sequence("inputs", inputs),
        _sequence("costs", cost_rows),
        _field("response-policy", response_policy.encode("ascii")),
        _field("cost-policy", cost_policy.encode("ascii")),
        _field("closure-policy", closure_policy.encode("ascii")),
        _field("version", version.encode("ascii")),
    )
    logger.debug("realization_context_digest exit")
    return result


def realization_partition_digest(partition: tuple[int, ...]) -> str:
    """Commit to one normalized ordered finite partition."""
    logger.debug("realization_partition_digest entry states=%d", len(partition))
    rows = tuple(item.to_bytes(4, "big") for item in partition)
    result = _digest(
        "veyra.p1-r16.partition.v1", _sequence("classes", rows)
    )
    logger.debug("realization_partition_digest exit")
    return result


def finite_doctrine_digest(doctrine: object) -> str:
    """Commit to the complete exact R16 doctrine value."""
    logger.debug("finite_doctrine_digest entry")
    name, carrier, observers = snapshot_doctrine(doctrine)
    observer_rows: list[bytes] = []
    for observer in observers:
        observer_name, responses, cost = snapshot_observer(observer)
        response_rows = tuple(
            _field("state", canonical_finite_value(state))
            + _field("response", canonical_finite_value(response))
            for state, response in responses
        )
        observer_rows.append(
            _field("name", observer_name.encode("utf-8"))
            + _sequence("responses", response_rows)
            + _field("cost", cost.to_bytes(8, "big"))
        )
    result = _digest(
        "veyra.p1-r16.finite-doctrine.v1",
        _field("name", name.encode("utf-8")),
        _sequence("carrier", tuple(canonical_finite_value(item) for item in carrier)),
        _sequence("observers", tuple(observer_rows)),
    )
    logger.debug("finite_doctrine_digest exit observers=%d", len(observers))
    return result


def realization_witness_digest(
    source_fingerprint: str,
    context_digest: str,
    evaluations: tuple[RealizationEvaluationRow, ...],
    source_mapping: tuple[tuple[str, str], ...],
    closure: tuple[RealizationClosureRow, ...],
    doctrine_digest: str,
    schema: str,
) -> str:
    """Commit to the complete deterministic typed replay witness."""
    logger.debug(
        "realization_witness_digest entry evaluations=%d closure=%d",
        len(evaluations),
        len(closure),
    )
    evaluation_rows = tuple(
        _field("observer-id", row.observer_id.encode("utf-8"))
        + _field("state-index", row.state_index.to_bytes(4, "big"))
        + _field("state", canonical_finite_value(row.state))
        + _field("input", row.input_commitment.encode("ascii"))
        + _field("status", row.status.value.encode("ascii"))
        + _field("response-class", row.response_class.to_bytes(4, "big"))
        + _field("payload", row.observation_payload)
        + _field("payload-digest", row.payload_digest.encode("ascii"))
        for row in evaluations
    )
    mapping_rows = tuple(
        _field("source", source.encode("utf-8"))
        + _field("finite", finite.encode("utf-8"))
        for source, finite in source_mapping
    )
    closure_rows = tuple(
        _field("observer", row.observer_name.encode("utf-8"))
        + _sequence(
            "generators", tuple(item.encode("utf-8") for item in row.generator_ids)
        )
        + _sequence("partition", tuple(item.to_bytes(4, "big") for item in row.partition))
        + _sequence(
            "representatives",
            tuple(item.to_bytes(4, "big") for item in row.representative_indices),
        )
        + _field("partition-digest", row.partition_digest.encode("ascii"))
        + _field("cost", row.cost.to_bytes(8, "big"))
        for row in closure
    )
    result = _digest(
        "veyra.p1-r16.realization-witness.v1",
        _field("schema", schema.encode("ascii")),
        _field("source-doctrine", source_fingerprint.encode("ascii")),
        _field("context", context_digest.encode("ascii")),
        _sequence("evaluations", evaluation_rows),
        _sequence("source-mapping", mapping_rows),
        _sequence("closure", closure_rows),
        _field("finite-doctrine", doctrine_digest.encode("ascii")),
    )
    logger.debug("realization_witness_digest exit")
    return result
