"""Topology echo certificate hooks for Veyra."""

from __future__ import annotations

import logging

from ..certify_types import Certificate
from ..geometry.topology_echo import topology_echo_checklist, topology_echo_summary, topology_invariant_rows, topology_obstruction_cards

logger = logging.getLogger(__name__)


def certify_topology_echo_x4() -> Certificate:
    """Certify Sprint X4 finite deformation-invariant echo layer."""
    logger.debug("certify_topology_echo_x4 entry")
    summary = topology_echo_summary()
    rows = topology_invariant_rows()
    cards = topology_obstruction_cards()
    expected = {"shapes": 4, "invariants": 4, "invariant_hits": 4, "obstructions": 2, "blocked": 2, "checklist": 4}
    passed = summary == expected and all(row.status == "invariant" for row in rows) and [card.obstruction for card in cards] == ["component-split", "cycle-collapse"] and len(topology_echo_checklist()) == 4
    result = Certificate("topology_echo_x4", "finite deformation-invariant corridor/shell echo tests", passed, f"shapes={summary['shapes']} blocked={summary['blocked']}", 1)
    logger.debug("certify_topology_echo_x4 exit result=%r", result)
    return result
