"""Certificate for finite observer-gap surprise separation rows."""
from __future__ import annotations
import logging
from ..certify_types import Certificate
from ..surprise.separation import surprise_separation_checklist, surprise_separation_summary

logger = logging.getLogger(__name__)

def certify_surprise_separation_s1() -> Certificate:
    """Certify the finite observer-gap separation and baseline-pressure ledger."""
    logger.debug("certify_surprise_separation_s1 entry")
    summary = surprise_separation_summary()
    expected = {
        "rows": 1,
        "baseline_blind": 1,
        "separated": 1,
        "baseline_families": 3,
        "expanded_families": 7,
        "audit_rows": 1,
        "caught_by_expanded": 1,
        "overclaims": 0,
    }
    passed = summary == expected and len(surprise_separation_checklist()) == 5
    detail = f"rows={summary['rows']} expanded={summary['expanded_families']} caught={summary['caught_by_expanded']}"
    result = Certificate("surprise_separation_s1", "finite observer-gap separation against named classical baselines", passed, detail, 1)
    logger.debug("certify_surprise_separation_s1 exit result=%r", result)
    return result
