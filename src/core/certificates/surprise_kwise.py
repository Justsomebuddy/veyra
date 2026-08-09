"""Certificate for k-wise hidden-correlation surprise rows."""
from __future__ import annotations
import logging
from ..certify_types import Certificate
from ..surprise.kwise import kwise_hidden_correlation_checklist, kwise_hidden_correlation_summary

logger = logging.getLogger(__name__)

def certify_surprise_kwise_s5() -> Certificate:
    """Certify the finite 3-wise-blind / 4-wise parity row."""
    logger.debug("certify_surprise_kwise_s5 entry")
    summary = kwise_hidden_correlation_summary()
    expected = {"rows": 1, "width": 4, "max_blind_order": 3, "baseline_equal": 1, "hidden_splits": 1, "structured_gap": 16, "control_gap": 0, "overclaims": 0}
    passed = summary == expected and len(kwise_hidden_correlation_checklist()) == 5
    detail = f"width={summary['width']} k={summary['max_blind_order']} gap={summary['structured_gap']}"
    result = Certificate("surprise_kwise_s5", "finite 3-wise-blind / 4-wise parity hidden-correlation row", passed, detail, 1)
    logger.debug("certify_surprise_kwise_s5 exit result=%r", result)
    return result
