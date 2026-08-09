"""Certificate for explicit deduction-chain ledger."""
from __future__ import annotations
import logging
from ..certify_types import Certificate
from ..formal.deduction_chain import deduction_chain_checklist, deduction_chain_summary, deduction_links

logger = logging.getLogger(__name__)

def certify_deduction_chain_f6() -> Certificate:
    """Certify that derivation boundaries are explicit, not overclaimed."""
    logger.debug("certify_deduction_chain_f6 entry")
    links = deduction_links()
    summary = deduction_chain_summary(links)
    anchors = {anchor for row in links for anchor in row.anchors}
    passed = (
        summary["links"] == 5 and summary["verified"] == 5 and summary["derived"] >= 5
        and summary["observer-derived"] == 0 and summary["shadow-dependent"] == 0 and summary["blocked"] == 0
        and summary["all_derived"]
        and "THM-F001" in anchors and "THM-R3-001" in anchors
        and len(deduction_chain_checklist()) == 5
    )
    detail = f"links={summary['links']} verified={summary['verified']} derived={summary['derived']} observer={summary['observer-derived']} shadow={summary['shadow-dependent']} blocked={summary['blocked']}"
    result = Certificate(
        "deduction_chain_f6", "executable deduction-chain proof rows with explicit non-derivation boundaries",
        passed, detail, 1,
    )
    logger.debug("certify_deduction_chain_f6 exit result=%r", result)
    return result
