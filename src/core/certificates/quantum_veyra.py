"""Certificate for Q1 finite Q-Veyra seed layer."""
from __future__ import annotations
import logging
from ..certify_types import Certificate
from ..quantum.veyra import quantum_theorem_cards, quantum_veyra_checklist, quantum_veyra_summary

logger = logging.getLogger(__name__)

def certify_quantum_veyra_q1() -> Certificate:
    """Certify finite observer-indexed quantum theorem-card seed rows."""
    logger.debug("certify_quantum_veyra_q1 entry")
    cards = quantum_theorem_cards()
    summary = quantum_veyra_summary()
    passed = (
        summary["cards"] == 6 and summary["ready"] == 6 and summary["obstructions"] == 2
        and summary["overclaims"] == 0 and summary["has_born_shadow"] and summary["has_tensor_seed"]
        and {card.theorem_id for card in cards} == {"Q-HH", "Q-XX", "Q-CNOT-NORM", "Q-BELL-NONFACT", "Q-ZX-SHADOW", "Q-NO-CLONE"}
        and len(quantum_veyra_checklist()) == 6
    )
    detail = f"cards={summary['cards']} ready={summary['ready']} obstructions={summary['obstructions']}"
    result = Certificate("quantum_veyra_q1", "finite observer-indexed Q-Veyra theorem-card seed", passed, detail, 1)
    logger.debug("certify_quantum_veyra_q1 exit result=%r", result)
    return result
