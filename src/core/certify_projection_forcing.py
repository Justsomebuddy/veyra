"""Executable certificate for the TR-2/2 projection-forcing structure."""

from __future__ import annotations

import logging

from .break_locus import (
    forced_law_sweep,
    forced_pairs,
    forcing_report,
    is_k_power,
    two_prime_probe,
)
from .certify_types import Certificate

logger = logging.getLogger(__name__)

AB = ("a", "b")
ABC = ("a", "b", "c")


def certify_projection_forcing_tr2b() -> Certificate:
    """Certify the forcing floor, the forced-locus law, and the two-prime probe."""
    logger.debug("certify_projection_forcing_tr2b entry")
    cells_ok = (
        is_k_power(tuple("abab"), 2) and not is_k_power(tuple("aabb"), 2)
        and forced_pairs(tuple("aabb"), AB, 2) == (("a", "b"),)
        and forced_pairs(tuple("aabbcc"), ABC, 2) == (("a", "b"), ("a", "c"), ("b", "c"))
    )
    floors = forcing_report(tuple("aabbab" * 2), AB)
    floors_ok = (
        floors.prime_exponents == (2, 3)
        and dict(floors.forced_by_prime)[2] == ()
        and dict(floors.forced_by_prime)[3] == (("a", "b"),)
        and floors.lemma_a_respected
    )
    law_ok = True
    law_total = 0
    for alphabet, counts, checked in (
        (AB, (3, 3), 20), (AB, (4, 2), 15),
        (ABC, (2, 2, 2), 90), (("a", "b", "c", "d"), (2, 2, 2, 2), 2520),
    ):
        sweep = forced_law_sweep(alphabet, counts)
        law_total += sweep.words_checked
        law_ok = law_ok and (
            sweep.status == "witnessed" and sweep.words_checked == checked
            and sweep.lemma_a_violations == () and sweep.law_mismatches == ()
        )
    probe = two_prime_probe(ABC, (6, 6, 6), samples=300)
    probe_ok = (
        probe.status == "witnessed" and probe.samples == 300
        and probe.nonprincipal_words == () and probe.max_locus_size == 1
        and probe.forced_floor_respected
    )
    passed = cells_ok and floors_ok and law_ok and probe_ok
    detail = (
        "forcing floor exact on known cells; two-prime floors incomparable in "
        "principle (F2=(), F3={ab}) with Lemma A respected; forced-locus law "
        "B(w)=={F_q} holds on %d in-certificate exhaustive words (6285 pinned "
        "in tests) with zero Lemma-A violations; seeded (6,6,6) probe: 300 "
        "in-certificate samples (1200 pinned) all principal with the floor "
        "respected - SAMPLED evidence, not exhaustive; conjecture remains "
        "CONJECTURE, nothing promoted" % law_total
    )
    result = Certificate(
        "projection_forcing_tr2b",
        "forcing structure of the break locus: Lean-anchored floor, prime reduction, forced-locus law, two-prime probe",
        passed,
        detail,
        1,
    )
    if not passed:
        logger.error("certify_projection_forcing_tr2b failed detail=%s", detail)
    logger.debug("certify_projection_forcing_tr2b exit passed=%s", passed)
    return result
