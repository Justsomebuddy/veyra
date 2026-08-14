"""Domain-separated digests for bounded P3-OG lifecycle evidence."""

from __future__ import annotations

from hashlib import sha256
import logging
from typing import Any

from .prime_power_observer_genesis_p3og_codec import (
    bounded_text,
    canonical_bytes,
    evidence_bytes,
)

logger = logging.getLogger(__name__)
LIFECYCLE_DOMAIN = b"veyra-p3og-lifecycle-v1\0"
_LIFECYCLE_EVIDENCE_LABELS = frozenset(
    {"formation-genealogy", "first-closure-evidence"},
)


def lifecycle_digest(label: str, *values: Any) -> str:
    """Digest typed values under the isolated lifecycle domain."""
    logger.debug(
        "p3og.lifecycle.digest entry label=%s values=%d",
        label,
        len(values),
    )
    try:
        label = bounded_text(label, "p3og-lifecycle-digest-label")
        encoder = evidence_bytes if label in _LIFECYCLE_EVIDENCE_LABELS else canonical_bytes
        encoded = encoder(*values)
        result = sha256(
            LIFECYCLE_DOMAIN + label.encode("ascii") + b"\0" + encoded,
        ).hexdigest()
    except (TypeError, UnicodeError, ValueError) as exc:
        logger.error(
            "p3og.lifecycle.digest error label=%r type=%s",
            label if type(label) is str and len(label) <= 128 else "<invalid>",
            type(exc).__name__,
        )
        raise
    logger.debug(
        "p3og.lifecycle.digest exit label=%s digest=%s",
        label,
        result[:12],
    )
    return result
