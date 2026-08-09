"""Tagged count-framed SHA-256 commitments for P1-C3."""

from __future__ import annotations

from hashlib import sha256
import json
import logging

from ...proof_core_codec import canonical_json, term_data

logger = logging.getLogger(__name__)


def frame(tag: str, value: bytes) -> bytes:
    """Frame one tagged byte string without ambiguous concatenation."""
    logger.debug("c3 frame entry tag=%s", tag)
    raw = tag.encode() + b"\0" + len(value).to_bytes(8, "big") + value
    logger.debug("c3 frame exit bytes=%d", len(raw))
    return raw


def digest(tag: str, fields: tuple[tuple[str, bytes], ...]) -> str:
    """Hash one closed ordered field sequence."""
    logger.debug("c3 digest entry tag=%s fields=%d", tag, len(fields))
    h = sha256(frame("domain", tag.encode()))
    for name, value in fields:
        h.update(frame(name, value))
    result = h.hexdigest()
    logger.debug("c3 digest exit tag=%s", tag)
    return result


def sequence(tag: str, values: tuple[str, ...]) -> bytes:
    """Encode one ordered string sequence with an explicit count."""
    logger.debug("c3 sequence entry tag=%s count=%d", tag, len(values))
    result = len(values).to_bytes(8, "big") + b"".join(
        frame(tag, item.encode()) for item in values
    )
    logger.debug("c3 sequence exit bytes=%d", len(result))
    return result


def recurrence_bytes(value: object) -> bytes:
    """Encode one already bounded Core term canonically."""
    logger.debug("c3 recurrence_bytes entry")
    result = canonical_json(term_data(value)).encode()
    logger.debug("c3 recurrence_bytes exit bytes=%d", len(result))
    return result


def kind_bytes(value: object) -> bytes:
    """Encode one closed response-kind tree without repr dependence."""
    logger.debug("c3 kind_bytes entry")
    from ...observer_core_types import LeafKind, PairKind
    if type(value) is LeafKind:
        node = {"leaf": value.value}
    elif type(value) is PairKind:
        node = {"pair": [json.loads(kind_bytes(value.left)), json.loads(kind_bytes(value.right))]}
    else:
        logger.error("c3 kind_bytes invalid kind")
        raise TypeError("invalid-c3-response-kind")
    result = json.dumps(node, sort_keys=True, separators=(",", ":")).encode()
    logger.debug("c3 kind_bytes exit bytes=%d", len(result))
    return result
