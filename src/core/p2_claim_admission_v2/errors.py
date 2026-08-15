"""Stable non-disclosing errors shared by the additive P2 v2 sibling."""

from __future__ import annotations

import logging
from typing import NoReturn

logger = logging.getLogger(__name__)


class P2ClaimAdmissionError(ValueError):
    """Stable fail-closed error for the additive P2 v2 boundary."""

    def __init__(self, reason: str) -> None:
        logger.error("P2ClaimAdmissionError state=blocked reason=%s", reason)
        self.reason = reason
        super().__init__(reason)


def reject(reason: str) -> NoReturn:
    """Raise one bounded non-disclosing sibling error."""
    logger.debug("reject entry reason=%s", reason)
    raise P2ClaimAdmissionError(reason)
