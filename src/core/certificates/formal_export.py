"""Certificate for X7 formal export preparation rows."""
from __future__ import annotations
import logging
from ..certify_types import Certificate
from ..formal.prep import formal_export_prep_checklist, formal_export_prep_summary, stable_card_export_prep_rows

logger = logging.getLogger(__name__)

def certify_formal_export_prep_x7() -> Certificate:
    """Certify X7 export-prep rows without claiming completed formalization."""
    logger.debug("certify_formal_export_prep_x7 entry")
    rows = stable_card_export_prep_rows()
    summary = formal_export_prep_summary()
    passed = (
        summary["checked_bridges"] == 2 and summary["candidate_rows"] == 19
        and summary["prep_ready"] == 19 and summary["candidate_formalized"] == 0
        and summary["stable_sources"] == 19 and summary["no_completed_claims"]
        and len(formal_export_prep_checklist()) == 4
        and all("no formal proof" in row.boundary for row in rows)
    )
    detail = f"bridges={summary['checked_bridges']} candidates={summary['candidate_rows']} formalized={summary['candidate_formalized']}"
    result = Certificate("formal_export_prep_x7", "stable-card Lean/Coq export-prep rows with no completed-formalization claim", passed, detail, 1)
    logger.debug("certify_formal_export_prep_x7 exit result=%r", result)
    return result
