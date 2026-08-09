"""Certificate for X6 geometry visual regression rows."""
from __future__ import annotations
import logging
from ..certify_types import Certificate
from ..geometry.visual_regression import geometry_visual_regression_checklist, geometry_visual_regression_summary, geometry_visual_snapshots

logger = logging.getLogger(__name__)


def certify_geometry_visual_regression_x6() -> Certificate:
    """Certify reproducible geometry visual snapshot rows."""
    logger.debug("certify_geometry_visual_regression_x6 entry")
    rows = geometry_visual_snapshots()
    summary = geometry_visual_regression_summary(rows)
    passed = summary["scenes"] == summary["snapshots"] == summary["matched"] == 3 and summary["changed"] == 0 and summary["indexed"] and summary["reproducible"] and len(geometry_visual_regression_checklist()) == 4
    detail = f"scenes={summary['scenes']} matched={summary['matched']} changed={summary['changed']} reproducible={summary['reproducible']}"
    result = Certificate("geometry_visual_regression_x6", "reproducible geometry visual scene snapshots", passed, detail, 1)
    logger.debug("certify_geometry_visual_regression_x6 exit result=%r", result)
    return result
