"""Domain-separated digest for the P3-OG formation-pressure bridge."""

from __future__ import annotations

from hashlib import sha256
import logging
from typing import Any

from .prime_power_observer_genesis_p3og_codec import evidence_bytes

logger = logging.getLogger(__name__)
BINDING_DOMAIN = b"veyra-p3og-formation-pressure-binding-v1\0"


def formation_pressure_digest(*values: Any) -> str:
    """Digest bounded typed values under the isolated bridge domain."""
    logger.debug("p3og.binding.digest entry values=%d", len(values))
    try:
        result = sha256(
            BINDING_DOMAIN + b"formation-pressure-binding\0" + evidence_bytes(*values),
        ).hexdigest()
    except (TypeError, UnicodeError, ValueError):
        logger.error("p3og.binding.digest error")
        raise
    logger.debug("p3og.binding.digest exit")
    return result
