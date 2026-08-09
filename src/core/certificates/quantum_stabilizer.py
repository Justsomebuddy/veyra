"""Certificate for Q2 finite stabilizer/QEC observer rows."""
from __future__ import annotations
import logging
from ..certify_types import Certificate
from ..quantum.stabilizer import quantum_stabilizer_checklist, quantum_stabilizer_summary

logger = logging.getLogger(__name__)

def certify_quantum_stabilizer_q2() -> Certificate:
    """Certify finite syndrome/logical observer split rows."""
    logger.debug("certify_quantum_stabilizer_q2 entry")
    summary = quantum_stabilizer_summary()
    passed = summary == {"pauli_rows": 3, "syndrome_rows": 8, "single_error_corrected": 8, "echo_split_rows": 4, "logical_obstructions": 3, "overclaims": 0} and len(quantum_stabilizer_checklist()) == 6
    detail = f"syndrome={summary['syndrome_rows']} corrected={summary['single_error_corrected']} obstructions={summary['logical_obstructions']}"
    result = Certificate("quantum_stabilizer_q2", "finite stabilizer syndrome/logical observer split rows", passed, detail, 1)
    logger.debug("certify_quantum_stabilizer_q2 exit result=%r", result)
    return result
