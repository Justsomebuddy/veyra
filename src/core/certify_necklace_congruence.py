"""Executable certificate for the N8 necklace congruence lane."""

from __future__ import annotations

import logging

from .certify_types import Certificate
from .necklace_congruence import (
    fermat_orbit_witness,
    gauss_congruence_witness,
    necklace_congruence_checklist,
    orbit_dichotomy_witness,
)

logger = logging.getLogger(__name__)

_PRIMES = (2, 3, 5, 7)
_ALPHABETS = (("a", "b"), ("a", "b", "c"))
_GAUSS_LENGTHS = tuple(range(1, 11))


def certify_necklace_congruence_n8() -> Certificate:
    """Certify orbit-counting congruences on exact bounded rows."""
    logger.debug("certify_necklace_congruence_n8 entry")
    fermat_ok = all(
        fermat_orbit_witness(alphabet, prime).status == "witnessed"
        for prime in _PRIMES
        for alphabet in _ALPHABETS
    )
    gauss_rows = [
        gauss_congruence_witness(alphabet, length)
        for length in _GAUSS_LENGTHS
        for alphabet in _ALPHABETS
    ]
    gauss_ok = all(row.status == "witnessed" and row.shadow_match for row in gauss_rows)
    composite = orbit_dichotomy_witness(("a", "b"), 4)
    composite_ok = composite.status == "blocked" and composite.obstruction == "nonprime-length" and composite.counterexample != ""
    checklist_ok = len(necklace_congruence_checklist()) == 5
    passed = fermat_ok and gauss_ok and composite_ok and checklist_ok
    detail = (
        "fermat p in {2,3,5,7} x k in {2,3} witnessed; gauss n in 1..10 x k in {2,3} "
        "witnessed with mobius shadow match; composite length 4 blocked with "
        "counterexample; bounded exact rows only, no general theorem"
    )
    result = Certificate(
        "necklace_congruence_n8",
        "orbit-counting congruences: prime-length dichotomy, Fermat partition, Gauss primitive-count divisibility",
        passed,
        detail,
        1,
    )
    if not passed:
        logger.error("certify_necklace_congruence_n8 failed detail=%s", detail)
    logger.debug("certify_necklace_congruence_n8 exit passed=%s", passed)
    return result
