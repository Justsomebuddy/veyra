"""Collision-safe tagged digests for P3-T artifacts."""

from __future__ import annotations

from hashlib import sha256
import logging

logger = logging.getLogger(__name__)


def field(tag: str, payload: bytes) -> bytes:
    """Length-frame a digest field."""
    logger.debug("network field entry tag=%s bytes=%d", tag, len(payload))
    name = tag.encode("ascii")
    result = len(name).to_bytes(2, "big") + name + len(payload).to_bytes(8, "big") + payload
    logger.debug("network field exit tag=%s", tag)
    return result


def text(tag: str, value: str) -> bytes:
    """Frame UTF-8 text."""
    logger.debug("network text entry tag=%s", tag)
    result = field(tag, value.encode("utf-8"))
    logger.debug("network text exit tag=%s", tag)
    return result


def seq(tag: str, values: tuple[bytes, ...]) -> bytes:
    """Count-bind ordered framed entries."""
    logger.debug("network seq entry tag=%s count=%d", tag, len(values))
    result = field(tag, len(values).to_bytes(4, "big") + b"".join(field("item", v) for v in values))
    logger.debug("network seq exit tag=%s", tag)
    return result


def digest(domain: str, *values: bytes) -> str:
    """Hash under one distinct semantic domain."""
    logger.debug("network digest entry domain=%s", domain)
    result = sha256(field("domain", domain.encode("ascii")) + b"".join(values)).hexdigest()
    logger.debug("network digest exit domain=%s", domain)
    return result


def input_digest(input_id: str, type_id: str, payload: bytes) -> str:
    """Commit one input occurrence."""
    logger.debug("input_digest entry id=%s", input_id)
    result = digest("p3t-input-v1", text("id", input_id), text("type", type_id), field("payload", payload))
    logger.debug("input_digest exit id=%s", input_id)
    return result


def value_digest(grammar: str, kind: str, payload: bytes) -> str:
    """Commit one exact typed ready value."""
    logger.debug("value_digest entry")
    result = digest("p3t-value-v1", text("grammar", grammar), text("kind", kind), field("payload", payload))
    logger.debug("value_digest exit")
    return result


def response_digest(status: str, value: str, reason: str) -> str:
    """Commit one tagged response."""
    logger.debug("response_digest entry status=%s", status)
    result = digest("p3t-response-v1", text("status", status), text("value", value), text("reason", reason))
    logger.debug("response_digest exit status=%s", status)
    return result


def records_digest(domain: str, identity: tuple[str, ...], records: tuple[str, ...]) -> str:
    """Commit identities and ordered child commitments."""
    logger.debug("records_digest entry domain=%s records=%d", domain, len(records))
    result = digest(
        domain,
        seq("identity", tuple(text("id", x) for x in identity)),
        seq("records", tuple(text("digest", x) for x in records)),
    )
    logger.debug("records_digest exit domain=%s", domain)
    return result


def map_digest(path: tuple[str, ...], source: str, target: str, rows: tuple[tuple[str, str], ...]) -> str:
    """Commit one derived partial map and exact domain order."""
    logger.debug("map_digest entry edges=%d rows=%d", len(path), len(rows))
    encoded = tuple(text("source-value", a) + text("target-value", b) for a, b in rows)
    result = digest(
        "p3t-partial-map-v1",
        seq("path", tuple(text("edge", e) for e in path)),
        text("source", source),
        text("target", target),
        seq("rows", encoded),
    )
    logger.debug("map_digest exit")
    return result
