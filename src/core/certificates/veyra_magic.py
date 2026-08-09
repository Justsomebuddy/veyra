"""Certificate for the current Veyra magic audit."""
from __future__ import annotations
import logging
from ..certify_types import Certificate
from ..surprise.veyra_magic import VEYRA_MAGIC_THESIS, magic_audit_checklist, magic_audit_summary
from ..observer.synthesis import observer_synthesis_summary, strict_observer_class_certificate

logger = logging.getLogger(__name__)

def certify_veyra_magic_m1() -> Certificate:
    """Certify the bounded M1 observer-synthesis magic thesis."""
    logger.debug("certify_veyra_magic_m1 entry")
    summary = magic_audit_summary()
    checklist = magic_audit_checklist()
    expected = {"rows": 5, "strongest_candidates": 1, "active_candidates": 2, "truth_maintenance": 1, "blocked_claims": 1, "overclaims": 0}
    synthesis = observer_synthesis_summary(); strength = strict_observer_class_certificate()
    passed = summary == expected and synthesis["status"] == "validated" and synthesis["winner"] == "histogram(xor-rows(input))" and strength.strictly_stronger and len(checklist) == 6 and "observer synthesis" in VEYRA_MAGIC_THESIS
    detail = f"rows={summary['rows']} synthesis={synthesis['status']} winner={synthesis['winner']} scoped_stronger={strength.strictly_stronger} overclaims={summary['overclaims']}"
    result = Certificate("veyra_magic_m1", "bounded typed observer-synthesis engine with locked holdout and scoped strength", passed, detail, 1)
    logger.debug("certify_veyra_magic_m1 exit result=%r", result)
    return result
