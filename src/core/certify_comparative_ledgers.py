"""Level-1 certificate for the sibling bridge and separation ledgers."""

from __future__ import annotations

import logging

from .certify_types import Certificate
from .comparative_bridge_ledger import (
    comparative_bridge_checklist,
    comparative_bridge_rows,
    comparative_bridge_summary,
)
from .comparative_ledger_types import ComparativeBridgeStatus, StructuralSeparationStatus
from .structural_separation_ledger import (
    structural_separation_checklist,
    structural_separation_rows,
    structural_separation_summary,
)

logger = logging.getLogger(__name__)


def certify_comparative_bridge_separation_ledgers() -> Certificate:
    """Certify exact row catalogs, checked statuses, and nonclaim boundaries."""
    logger.debug("certify_comparative_bridge_separation_ledgers entry")
    bridges = comparative_bridge_rows()
    separations = structural_separation_rows()
    bridge_summary = comparative_bridge_summary(bridges)
    separation_summary = structural_separation_summary(separations)
    passed = (
        tuple(row.bridge_id for row in bridges) == ("CB-ECHO-001", "CB-PROCESS-001", "CB-G4-001")
        and bridges[-1].status is ComparativeBridgeStatus.REDUCED
        and separations[0].separation_id == "SEP-G4-001"
        and separations[0].status is StructuralSeparationStatus.STRICTLY_SEPARATED
        and bridge_summary["unique_ids"]
        and bridge_summary["all_checked_reductions"]
        and separation_summary["unique_ids"]
        and separation_summary["all_strict_checked"]
        and len(comparative_bridge_checklist()) == 5
        and len(structural_separation_checklist()) == 5
        and all(
            any(
                term in row.boundary
                for term in ("superiority", "analogy is not", "no general sheaf", "no functor")
            )
            for row in bridges
        )
        and "superiority" in separations[0].boundary
    )
    detail = (
        f"bridges={bridge_summary['rows']} reduced={bridge_summary['reduced']} "
        f"open={bridge_summary['open']} separations={separation_summary['rows']} "
        f"strict={separation_summary['strictly_separated']} promotions=0"
    )
    result = Certificate(
        "comparative_bridge_separation_ledgers",
        "finite structural bridge reduction and predicate separation truth maintenance",
        bool(passed),
        detail,
        1,
    )
    logger.debug("certify_comparative_bridge_separation_ledgers exit result=%r", result)
    return result
