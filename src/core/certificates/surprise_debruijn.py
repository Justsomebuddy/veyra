"""Certificate for S6 de Bruijn hidden-trail surprise rows."""
from __future__ import annotations
import logging
from ..certify_types import Certificate
from ..surprise.debruijn import debruijn_hidden_checklist, debruijn_hidden_summary

logger = logging.getLogger(__name__)

def certify_surprise_debruijn_s6() -> Certificate:
    """Certify the S6 order-3-window-blind de Bruijn trail row."""
    logger.debug("certify_surprise_debruijn_s6 entry")
    summary = debruijn_hidden_summary()
    checklist = debruijn_hidden_checklist()
    passed = summary == {"rows": 1, "baseline_equal": 1, "hidden_splits": 1, "common_transitions": 4, "divergent_transitions": 8, "overclaims": 0} and len(checklist) == 5
    detail = f"common={summary['common_transitions']} divergent={summary['divergent_transitions']}"
    result = Certificate("surprise_debruijn_s6", "finite order-3-window-blind de Bruijn trail-adjacency row", passed, detail, 1)
    logger.debug("certify_surprise_debruijn_s6 exit result=%r", result)
    return result
