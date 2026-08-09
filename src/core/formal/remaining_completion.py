"""Explicit public X8 completion accessors for the final four fixed cards."""
from __future__ import annotations

import logging

from .completion import FormalExportCompletionRow, _named_completion_row
from .remaining_data import (
    AREA_ADDITIVITY_ID, AREA_ADDITIVITY_SYMBOL,
    CHORD_SYMMETRY_ID, CHORD_SYMMETRY_SYMBOL,
    DRIFT_STABILITY_ID, DRIFT_STABILITY_SYMBOL,
    SAMPLED_CONTINUITY_ID, SAMPLED_CONTINUITY_SYMBOL,
)

logger = logging.getLogger(__name__)

__all__ = (
    "AREA_ADDITIVITY_ID", "AREA_ADDITIVITY_SYMBOL",
    "CHORD_SYMMETRY_ID", "CHORD_SYMMETRY_SYMBOL",
    "DRIFT_STABILITY_ID", "DRIFT_STABILITY_SYMBOL",
    "SAMPLED_CONTINUITY_ID", "SAMPLED_CONTINUITY_SYMBOL",
    "area_additivity_completion_row", "chord_symmetry_completion_row",
    "drift_stability_completion_row", "sampled_continuity_completion_row",
)


def sampled_continuity_completion_row() -> FormalExportCompletionRow:
    """Return the fixed five-point double-map completion row."""
    logger.debug("sampled_continuity_completion_row entry")
    result = _named_completion_row(SAMPLED_CONTINUITY_ID)
    logger.debug("sampled_continuity_completion_row exit status=%s", result.export_status)
    return result


def drift_stability_completion_row() -> FormalExportCompletionRow:
    """Return the fixed square-map three-step drift completion row."""
    logger.debug("drift_stability_completion_row entry")
    result = _named_completion_row(DRIFT_STABILITY_ID)
    logger.debug("drift_stability_completion_row exit status=%s", result.export_status)
    return result


def area_additivity_completion_row() -> FormalExportCompletionRow:
    """Return the fixed identity-midpoint area completion row."""
    logger.debug("area_additivity_completion_row entry")
    result = _named_completion_row(AREA_ADDITIVITY_ID)
    logger.debug("area_additivity_completion_row exit status=%s", result.export_status)
    return result


def chord_symmetry_completion_row() -> FormalExportCompletionRow:
    """Return the fixed mod-12 chord-mirror completion row."""
    logger.debug("chord_symmetry_completion_row entry")
    result = _named_completion_row(CHORD_SYMMETRY_ID)
    logger.debug("chord_symmetry_completion_row exit status=%s", result.export_status)
    return result
