import logging

import pytest

from src.core.comparative_bridge_ledger import (
    COMPARATIVE_BRIDGE_SCHEMA,
    comparative_bridge_checklist,
    comparative_bridge_rows,
    comparative_bridge_summary,
    validate_comparative_bridge_row,
)
from src.core.comparative_ledger_types import ComparativeBridgeRow, ComparativeBridgeStatus

logger = logging.getLogger(__name__)


def test_bridge_ledger_keeps_finite_reduction_and_open_candidate_distinct():
    logger.debug("test_bridge_ledger_keeps_finite_reduction_and_open_candidate_distinct entry")
    rows = comparative_bridge_rows()
    assert tuple(row.bridge_id for row in rows) == ("CB-ECHO-001", "CB-PROCESS-001", "CB-G4-001")
    assert tuple(row.status for row in rows) == (
        ComparativeBridgeStatus.KNOWN_ANALOGUE,
        ComparativeBridgeStatus.OPEN,
        ComparativeBridgeStatus.REDUCED,
    )
    g4 = rows[-1]
    assert "EqRel" in g4.comparison_formalism
    assert "finite existence/effectivity fragment only" in g4.boundary
    assert all(item.checked for item in g4.evidence)
    assert comparative_bridge_summary(rows) == {
        "rows": 3,
        "known_analogue": 1,
        "candidate_bridge": 0,
        "reduced": 1,
        "open": 1,
        "unique_ids": True,
        "all_checked_reductions": True,
    }
    assert len(comparative_bridge_checklist()) == 5
    logger.debug("test_bridge_ledger_keeps_finite_reduction_and_open_candidate_distinct exit")


def test_bridge_validator_rejects_unsupported_reduction_and_subclass():
    logger.debug("test_bridge_validator_rejects_unsupported_reduction_and_subclass entry")
    source = comparative_bridge_rows()[1]
    unsupported = ComparativeBridgeRow(
        COMPARATIVE_BRIDGE_SCHEMA,
        source.bridge_id,
        source.veyra_construct,
        source.comparison_formalism,
        ComparativeBridgeStatus.REDUCED,
        source.scope,
        (),
        source.preservation,
        source.reflection,
        source.extra_structure,
        source.evidence,
        source.boundary,
    )
    with pytest.raises(ValueError, match="reduced-without-evidence"):
        validate_comparative_bridge_row(unsupported)

    class Forged(ComparativeBridgeRow):
        pass

    with pytest.raises(ValueError, match="must-be-exact"):
        validate_comparative_bridge_row(Forged(*source.__getstate__()))
    surrogate = ComparativeBridgeRow(
        source.schema,
        "\ud800",
        source.veyra_construct,
        source.comparison_formalism,
        source.status,
        source.scope,
        source.correspondence,
        source.preservation,
        source.reflection,
        source.extra_structure,
        source.evidence,
        source.boundary,
    )
    with pytest.raises(ValueError, match="invalid-comparative-bridge-row"):
        validate_comparative_bridge_row(surrogate)
    logger.debug("test_bridge_validator_rejects_unsupported_reduction_and_subclass exit")
