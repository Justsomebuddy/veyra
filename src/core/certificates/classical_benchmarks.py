"""Certificate for F5 classical benchmark ledger."""
from __future__ import annotations
import logging
from ..certify_types import Certificate
from ..shadows.classical_benchmarks import classical_benchmark_cards, classical_benchmark_checklist, classical_benchmark_summary

logger = logging.getLogger(__name__)

def certify_classical_benchmark_f5() -> Certificate:
    """Certify paired classical-vs-Veyra benchmark cards."""
    logger.debug("certify_classical_benchmark_f5 entry")
    cards = classical_benchmark_cards()
    summary = classical_benchmark_summary(cards)
    ids = tuple(row.benchmark_id for row in cards)
    expected = tuple(f"BM-F{idx:03d}" for idx in range(1, 8)) + ("BM-F009",)
    passed = ids == expected and summary["cards"] == 8 and summary["all_status"] and summary["equivalent"] == 1 and summary["weaker"] == 4 and summary["clearer"] == 2 and summary["stronger"] == 1 and summary["unsupported_stronger"] == 0 and summary["overclaims"] == 0 and summary["scoped_claims"] and len(classical_benchmark_checklist()) == 7
    detail = f"cards={summary['cards']} eq={summary['equivalent']} weaker={summary['weaker']} clearer={summary['clearer']} stronger={summary['stronger']} unsupported={summary['unsupported_stronger']}"
    result = Certificate("classical_benchmark_f5", "scoped classical-vs-Veyra benchmark ledger with certified observer-class strength", passed, detail, 1)
    logger.debug("certify_classical_benchmark_f5 exit result=%r", result)
    return result
