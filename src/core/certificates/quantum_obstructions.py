"""Certificate for Q7 named finite quantum error obstructions."""
from __future__ import annotations
import logging
from ..certify_types import Certificate
from ..quantum.error_obstructions import quantum_error_obstruction_checklist, quantum_error_obstruction_summary

logger = logging.getLogger(__name__)

def certify_quantum_error_obstruction_q7() -> Certificate:
    """Certify the finite named quantum error-obstruction catalog."""
    logger.debug("certify_quantum_error_obstruction_q7 entry")
    summary = quantum_error_obstruction_summary()
    passed = summary == {
        "rows": 6,
        "ready": 6,
        "families": 6,
        "amplitude_rows": 4,
        "qec_rows": 2,
        "overclaims": 0,
    } and len(quantum_error_obstruction_checklist()) == 6
    detail = f"rows={summary['rows']} families={summary['families']} qec={summary['qec_rows']}"
    result = Certificate("quantum_error_obstruction_q7", "named finite quantum error obstruction characterization", passed, detail, 1)
    logger.debug("certify_quantum_error_obstruction_q7 exit result=%r", result)
    return result
