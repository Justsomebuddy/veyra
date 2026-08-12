import logging

import pytest

from src.core.comparative_ledger_types import (
    ComparativeEvidenceRef,
    StructuralSeparationRow,
    StructuralSeparationStatus,
)
from src.core.structural_separation_ledger import (
    STRUCTURAL_SEPARATION_SCHEMA,
    structural_separation_checklist,
    structural_separation_rows,
    structural_separation_summary,
    validate_structural_separation_row,
)

logger = logging.getLogger(__name__)


def test_separation_ledger_proves_existence_is_not_uniqueness():
    logger.debug("test_separation_ledger_proves_existence_is_not_uniqueness entry")
    rows = structural_separation_rows()
    assert len(rows) == 1
    assert rows[0].separation_id == "SEP-G4-001"
    assert rows[0].status is StructuralSeparationStatus.STRICTLY_SEPARATED
    assert "identity and universal" in rows[0].witness
    assert "does not establish Veyra superiority" in rows[0].boundary
    assert structural_separation_summary(rows) == {
        "rows": 1,
        "candidate_separation": 0,
        "strictly_separated": 1,
        "open": 0,
        "unique_ids": True,
        "all_strict_checked": True,
    }
    assert len(structural_separation_checklist()) == 5
    logger.debug("test_separation_ledger_proves_existence_is_not_uniqueness exit")


def test_strict_separation_requires_checked_evidence():
    logger.debug("test_strict_separation_requires_checked_evidence entry")
    source = structural_separation_rows()[0]
    forged = StructuralSeparationRow(
        STRUCTURAL_SEPARATION_SCHEMA,
        source.separation_id,
        source.left_predicate,
        source.right_predicate,
        StructuralSeparationStatus.STRICTLY_SEPARATED,
        source.scope,
        source.witness,
        (ComparativeEvidenceRef("FORGED", "counterexample", "tests/forged.py", False),),
        source.boundary,
    )
    with pytest.raises(ValueError, match="without-evidence"):
        validate_structural_separation_row(forged)
    logger.debug("test_strict_separation_requires_checked_evidence exit")
