"""Native-to-outer operational resource labels for P3-N0."""

from __future__ import annotations

import logging

from .types import FailedBound

logger = logging.getLogger(__name__)


def nested_resource_bound(nested) -> FailedBound:
    """Map only the outer label while preserving the complete native refusal DTO."""
    logger.debug("nested_resource_bound entry")
    value = nested.failed_bound.value
    result = {
        "captured-bytes": FailedBound.CAPTURED_BYTES,
        "static-cost": FailedBound.STATIC_COST, "depths": FailedBound.DEPTH,
        "arrows": FailedBound.REDUCTIONS, "table-rows": FailedBound.FINITE_ROWS,
        "output-bytes": FailedBound.OUTPUT_BYTES,
    }.get(value, FailedBound.EVALUATIONS)
    logger.debug("nested_resource_bound exit bound=%s", result.value)
    return result
