"""Certificate for the R15 comparative benchmark evidence ledger."""
from __future__ import annotations
import logging
from ..shadows.benchmark_evidence import benchmark_evidence_checklist, benchmark_evidence_summary, validate_benchmark_evidence
from ..certify_types import Certificate

logger = logging.getLogger(__name__)

def certify_benchmark_evidence_r15() -> Certificate:
    """Certify complete scoped evidence over the benchmark registry."""
    logger.debug("certify_benchmark_evidence_r15 entry")
    summary = benchmark_evidence_summary()
    expected = {
        "benchmarks": 8,
        "evidence_rows": 8,
        "obstructions": 0,
        "complete": True,
        "stronger_rows": 1,
        "scoped_stronger": 1,
        "global_superiority_claims": 0,
        "carrier_finite_shadow": 4,
        "carrier_witness": 2,
        "carrier_theorem_derived": 2,
    }
    passed = summary == expected and validate_benchmark_evidence() == () and len(benchmark_evidence_checklist()) == 8
    detail = f"benchmarks={summary['benchmarks']} complete={summary['complete']} scoped_stronger={summary['scoped_stronger']} superiority_claims={summary['global_superiority_claims']}"
    result = Certificate("benchmark_evidence_r15", "scoped benchmark evidence ledger, no superiority claim", passed, detail, 1)
    logger.debug("certify_benchmark_evidence_r15 exit result=%r", result)
    return result
