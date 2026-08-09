"""Hostile-safe primitives for isolated P3-N3/N4."""

from __future__ import annotations

import hashlib
import logging

logger = logging.getLogger(__name__)


class P3N3N4ValidationError(ValueError):
    """Malformed input at the N3/N4 trust boundary."""


def reject(message: str) -> None:
    """Log and reject one malformed boundary value."""
    logger.error("P3-N3/N4 validation failed reason=%s", message)
    raise P3N3N4ValidationError(message)


def sha(payload: bytes) -> str:
    """Hash exact captured bytes."""
    logger.debug("sha entry bytes=%d", len(payload))
    result = hashlib.sha256(payload).hexdigest()
    logger.debug("sha exit")
    return result


def frame(domain: str, rows: tuple[tuple[str, bytes], ...]) -> bytes:
    """Encode an ordered domain-separated transcript."""
    logger.debug("frame entry domain=%s rows=%d", domain, len(rows))
    if type(domain) is not str or type(rows) is not tuple:
        reject("frame-shape-invalid")
    output = bytearray(domain.encode() + b"\0")
    for label, value in rows:
        if type(label) is not str or type(value) is not bytes:
            reject("frame-row-invalid")
        for item in (label.encode(), value):
            output.extend(len(item).to_bytes(8, "big"))
            output.extend(item)
    result = bytes(output)
    logger.debug("frame exit bytes=%d", len(result))
    return result


def digest(domain: str, rows: tuple[tuple[str, bytes], ...]) -> str:
    """Hash one ordered transcript."""
    logger.debug("digest entry domain=%s", domain)
    result = sha(frame(domain, rows))
    logger.debug("digest exit")
    return result


def exact_shape(value: object, expected: type, label: str) -> dict[str, object]:
    """Reject subclasses/extra keys and read frozen fields without hostile hooks."""
    logger.debug("exact_shape entry label=%s", label)
    if type(value) is not expected:
        reject(f"{label}-exact-type-required")
    try:
        names = tuple(expected.__dataclass_fields__)
        namespace = object.__getattribute__(value, "__dict__")
        if type(namespace) is not dict or tuple(namespace) != names:
            reject(f"{label}-exact-keys-required")
        result = {name: object.__getattribute__(value, name) for name in names}
    except (AttributeError, TypeError):
        reject(f"{label}-fields-missing")
    logger.debug("exact_shape exit label=%s", label)
    return result


def exact_digest(value: object, label: str) -> str:
    """Require one lowercase SHA-256 identity."""
    logger.debug("exact_digest entry label=%s", label)
    if (type(value) is not str or len(value) != 64
            or any(c not in "0123456789abcdef" for c in value)):
        reject(f"{label}-invalid")
    logger.debug("exact_digest exit label=%s", label)
    return value


def realized_digest(family: str, carrier: str, theorem: str, ledger: str) -> str:
    """Derive one N3 term independently of N4 evidence."""
    logger.debug("realized_digest entry")
    result = digest("veyra.p3n3.realized-term.v1", (("family", family.encode()),
        ("carrier", carrier.encode()), ("thm007", theorem.encode()),
        ("ledger", ledger.encode())))
    logger.debug("realized_digest exit")
    return result


def role_term_digest(base: str, role: str) -> str:
    """Bind one N4 term reference to an independently derived N3 term."""
    logger.debug("role_term_digest entry role=%s", role)
    result = digest(f"veyra.p3n4.{role}-term-reference.v1", (
        ("n3-realized", base.encode()), ("role", role.encode())))
    logger.debug("role_term_digest exit")
    return result
