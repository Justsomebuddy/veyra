"""Certificate for Q5 observer-indexed QEC echo rows."""
from __future__ import annotations
import logging
from ..certify_types import Certificate
from ..quantum.qec_echo import quantum_qec_echo_checklist, quantum_qec_echo_summary

logger = logging.getLogger(__name__)

def certify_quantum_qec_echo_q5() -> Certificate:
    """Certify finite observer-indexed QEC echo rows."""
    logger.debug("certify_quantum_qec_echo_q5 entry")
    summary = quantum_qec_echo_summary()
    passed = summary == {
        "branches": 14,
        "observer_families": 4,
        "single_error_corrected": 8,
        "double_error_obstructions": 6,
        "split_echo_rows": 4,
        "ambiguity_rows": 6,
        "overclaims": 0,
    } and len(quantum_qec_echo_checklist()) == 6
    detail = (
        f"branches={summary['branches']} splits={summary['split_echo_rows']} "
        f"ambiguities={summary['ambiguity_rows']}"
    )
    result = Certificate(
        "quantum_qec_echo_q5",
        "observer-indexed QEC echo and ambiguity rows",
        passed,
        detail,
        1,
    )
    logger.debug("certify_quantum_qec_echo_q5 exit result=%r", result)
    return result
