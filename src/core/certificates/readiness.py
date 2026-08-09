"""Focused proof-discipline and Essence readiness certificates."""
from __future__ import annotations

import logging

from ..certify_types import Certificate
from ..kernel.essence import essence_report
from ..registry.proof_discipline import proof_discipline_checklist, proof_discipline_summary

logger = logging.getLogger(__name__)


def certify_proof_discipline() -> Certificate:
    """Certify Sprint F proof-discipline coverage."""
    logger.debug("certify_proof_discipline entry")
    summary = proof_discipline_summary()
    passed = (
        summary["rules"] >= 7 and summary["steps"] >= 28
        and summary["blocked_rules"] >= 1 and summary["domains"] == 7
        and summary["domain_certs"] == 7 and summary["models"] >= 10
        and summary["exports"] == 19 and len(proof_discipline_checklist()) == 4
    )
    detail = f"rules={summary['rules']} domains={summary['domains']} exports={summary['exports']}"
    result = Certificate(
        "proof_discipline", "rule/source-span/domain/model/stable-export coverage",
        passed, detail, 1,
    )
    logger.debug("certify_proof_discipline exit result=%r", result)
    return result


def certify_essence_core() -> Certificate:
    """Certify the executable Essence/Core readiness contract."""
    logger.debug("certify_essence_core entry")
    summary = essence_report().summary()
    expected = {
        "axioms": 9, "layers": 36, "executable_layers": 36, "missing": 0,
        "checklist": 6, "core_ready": True, "execution_ready": True,
        "proof_complete": False, "theorem_derived": 2, "witness_only": 4,
        "shadow": 25, "meta": 5,
    }
    passed = summary == expected
    detail = f"axioms={summary['axioms']} layers={summary['layers']} ready={summary['core_ready']}"
    result = Certificate(
        "essence_core", "axiom/layer/checklist readiness contract", passed, detail, 1,
    )
    logger.debug("certify_essence_core exit result=%r", result)
    return result
