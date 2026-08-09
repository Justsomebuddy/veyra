"""Canonical framed PΩ2 commitments."""

from __future__ import annotations

from hashlib import sha256
import logging

logger = logging.getLogger(__name__)


def frame(domain: str, fields: tuple[tuple[str, bytes], ...]) -> bytes:
    """Encode one domain-separated length-prefixed record."""
    logger.debug("frame entry domain=%s fields=%d", domain, len(fields))
    out = bytearray(b"VEYRA-POMEGA2\0")
    for tag, value in (("domain", domain.encode()), *fields):
        key = tag.encode()
        out.extend(len(key).to_bytes(4, "big"))
        out.extend(key)
        out.extend(len(value).to_bytes(8, "big"))
        out.extend(value)
    result = bytes(out)
    logger.debug("frame exit bytes=%d", len(result))
    return result


def digest(domain: str, fields: tuple[tuple[str, bytes], ...]) -> str:
    """Hash one canonical record."""
    logger.debug("digest entry domain=%s", domain)
    result = sha256(frame(domain, fields)).hexdigest()
    logger.debug("digest exit domain=%s", domain)
    return result


def texts(tag: str, values: tuple[str, ...]) -> tuple[tuple[str, bytes], ...]:
    """Encode an exact ordered text tuple."""
    logger.debug("texts entry tag=%s count=%d", tag, len(values))
    result = ((f"{tag}-count", len(values).to_bytes(8, "big")),) + tuple(
        (f"{tag}-{index}", value.encode()) for index, value in enumerate(values)
    )
    logger.debug("texts exit tag=%s", tag)
    return result
