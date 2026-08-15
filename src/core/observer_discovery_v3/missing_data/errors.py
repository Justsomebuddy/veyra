"""Closed error surface for the optional missing-data policy runtime."""

from __future__ import annotations

import logging
from typing import NoReturn

logger = logging.getLogger(__name__)


class MissingDataProtocolError(ValueError):
    """Bounded machine-readable failure without caller-controlled text."""

    def __init__(self, reason: str) -> None:
        logger.error("missing-data protocol error")
        self.reason = reason
        super().__init__(reason)


def reject(reason: str) -> NoReturn:
    """Raise the one public protocol failure type."""
    logger.error("missing-data rejected")
    raise MissingDataProtocolError(reason)
