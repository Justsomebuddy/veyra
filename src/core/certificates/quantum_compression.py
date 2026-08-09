"""Certificate for Q9 finite quantum circuit-compression rows."""
from __future__ import annotations
import logging
from ..certify_types import Certificate
from ..quantum.circuit_compression import circuit_compression_checklist, circuit_compression_summary

logger = logging.getLogger(__name__)

def certify_quantum_circuit_compression_q9() -> Certificate:
    """Certify finite peephole/observer circuit-compression rows."""
    logger.debug("certify_quantum_circuit_compression_q9 entry")
    summary = circuit_compression_summary()
    expected = {"rows": 6, "ready": 6, "exact_reductions": 3, "phase_normalizations": 1, "observer_reductions": 2, "saved_gates": 10, "overclaims": 0}
    passed = summary == expected and len(circuit_compression_checklist()) == 6
    detail = f"rows={summary['rows']} exact={summary['exact_reductions']} observer={summary['observer_reductions']} saved={summary['saved_gates']}"
    result = Certificate("quantum_circuit_compression_q9", "finite circuit peephole and observer-preserving compression rows", passed, detail, 1)
    logger.debug("certify_quantum_circuit_compression_q9 exit result=%r", result)
    return result
