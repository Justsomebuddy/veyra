"""Certificate for Q8 finite QFT/period-finding rows."""
from __future__ import annotations
import logging
from ..certify_types import Certificate
from ..quantum.qft_period import quantum_qft_period_checklist, quantum_qft_period_summary

logger = logging.getLogger(__name__)

def certify_quantum_qft_period_q8() -> Certificate:
    """Certify finite QFT_4 period-to-frequency shadow rows."""
    logger.debug("certify_quantum_qft_period_q8 entry")
    summary = quantum_qft_period_summary()
    expected = {"period_rows": 3, "ready_period_rows": 3, "offset_echo_rows": 1, "obstruction_rows": 1, "frequency_hits": 3, "overclaims": 0}
    passed = summary == expected and len(quantum_qft_period_checklist()) == 6
    detail = f"periods={summary['period_rows']} hits={summary['frequency_hits']} obstructions={summary['obstruction_rows']}"
    result = Certificate("quantum_qft_period_q8", "finite QFT_4 period-to-frequency observer shadow rows", passed, detail, 1)
    logger.debug("certify_quantum_qft_period_q8 exit result=%r", result)
    return result
