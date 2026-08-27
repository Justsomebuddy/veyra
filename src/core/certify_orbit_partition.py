"""Executable certificate for the DI-2 orbit-partition candidate lane."""

from __future__ import annotations

import logging

from .certify_types import Certificate
from .doctrinal_induction import InductionDoctrine, license_all_depth
from .native_runtime import nod, rez
from .necklace_congruence import fermat_orbit_witness
from .orbit_partition import (
    fermat_family_contract,
    orbit_partition_checklist,
    partition_evidence,
    tally_bomb_contract,
)

logger = logging.getLogger(__name__)

_DOCTRINE = InductionDoctrine("di2.cert.v1", "alphabet-extension")


def certify_orbit_partition_di2() -> Certificate:
    """Certify the DI-2 partition licenses with both adversarial controls."""
    logger.debug("certify_orbit_partition_di2 entry")
    anchor = nod(rez("di2-cert"), "di2-cert")
    three = license_all_depth(_DOCTRINE, fermat_family_contract(3), anchor, (1, 2, 3, 4))
    five = license_all_depth(_DOCTRINE, fermat_family_contract(5), anchor, (1, 2, 3))
    positive_ok = (
        three.status == "licensed" and five.status == "licensed"
        and all(row.valid for row in three.probes)
        and all(row.valid for row in five.probes)
    )
    composite = license_all_depth(_DOCTRINE, fermat_family_contract(4), anchor, (1, 2))
    composite_ok = composite.status == "blocked" and composite.obstruction == "composite-length"
    bomb = license_all_depth(_DOCTRINE, tally_bomb_contract(3, 3), anchor, (1, 2, 3, 4))
    bomb_ok = bomb.status == "blocked" and bomb.obstruction == "step-invalid-at-depth:3"
    ties_ok = True
    for length, depth, alphabet in ((3, 2, ("a", "b")), (5, 3, ("a", "b", "c"))):
        cell = partition_evidence(anchor, length, depth)
        n8 = fermat_orbit_witness(alphabet, length)
        ties_ok = ties_ok and (
            cell.status == "witnessed" and n8.status == "witnessed"
            and len(cell.full_mode.breath.tacts) == n8.full_orbit_count
            and len(cell.tally_mode.breath.tacts) == n8.nonconstant_count
        )
    checklist_ok = len(orbit_partition_checklist()) == 5
    passed = positive_ok and composite_ok and bomb_ok and ties_ok and checklist_ok
    detail = (
        "fermat partition families licensed for lengths 3 (depths 1..4) and 5 "
        "(depths 1..3) with native primality and woven congruence; composite "
        "length 4 blocked by the divisor witness; tally bomb blocked at "
        "exactly 3; full-orbit and tally counts echo the N8 instances; "
        "one licensed family statement, no completed carrier, no promotion"
    )
    result = Certificate(
        "orbit_partition_di2",
        "orbit-partition rule: dichotomy from period plus divisor witness, congruence as woven reconstruction, DI-1 family over alphabet depth",
        passed,
        detail,
        1,
    )
    if not passed:
        logger.error("certify_orbit_partition_di2 failed detail=%s", detail)
    logger.debug("certify_orbit_partition_di2 exit passed=%s", passed)
    return result
