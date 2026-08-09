"""Shared exact replay budget preflight for P1-C1 through future C4."""

from __future__ import annotations

import logging
from typing import NoReturn

from .types import ConfluencePreflightCharge

logger = logging.getLogger(__name__)
MAX_CONFLUENCE_CHECKS = 4096


class ConfluenceValidationError(ValueError):
    """An exact C1 representation, binding, or resource rule failed."""


def _reject(reason: str) -> NoReturn:
    logger.error("confluence preflight rejected reason=%s", reason)
    raise ConfluenceValidationError(reason)


def preflight_confluence_checks(value: ConfluencePreflightCharge) -> int:
    """Charge every declared lane before any observe/echo/translate call."""
    logger.debug("preflight_confluence_checks entry")
    if type(value) is not ConfluencePreflightCharge:
        _reject("preflight-charge-must-be-exact")
    try:
        fields = (
            value.edge_path_occurrences, value.alignment_points,
            value.transport_observers, value.target_support,
            value.response_g4_rows, value.refinement_checks,
            value.direct_survival_checks,
        )
    except AttributeError:
        _reject("preflight-charge-missing-fields")
    if any(type(item) is not int or item < 0 for item in fields):
        _reject("invalid-preflight-charge")
    total = fields[0] + fields[1] * fields[2] + sum(fields[3:])
    if total > MAX_CONFLUENCE_CHECKS:
        _reject("confluence-check-limit")
    logger.debug("preflight_confluence_checks exit total=%d", total)
    return total
