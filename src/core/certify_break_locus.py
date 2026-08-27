"""Executable certificate for the TR-2/1 break-locus lane."""

from __future__ import annotations

import logging

from .break_locus import (
    break_locus,
    break_locus_checklist,
    cross_check_full_lattice,
    nonprincipal_sweep,
)
from .certify_types import Certificate

logger = logging.getLogger(__name__)


def certify_break_locus_tr2() -> Certificate:
    """Certify locus computation, the classical-bridge cross-check, and sweeps."""
    logger.debug("certify_break_locus_tr2 entry")
    aabb = break_locus(tuple("aabb"), ("a", "b"))
    aabbcc = break_locus(tuple("aabbcc"), ("a", "b", "c"))
    abab = break_locus(tuple("abab"), ("a", "b"))
    known_ok = (
        aabb.minimal_deltas == ((("a", "b"),),)
        and aabbcc.minimal_deltas == ((("a", "b"), ("a", "c"), ("b", "c")),)
        and abab.literal_power and abab.minimal_deltas == ((),)
    )
    checks_ok = True
    for word, alphabet in (
        (tuple("aabb"), ("a", "b")), (tuple("abab"), ("a", "b")),
        (tuple("aabbcc"), ("a", "b", "c")), (tuple("aabc"), ("a", "b", "c")),
        (tuple("abc"), ("a", "b", "c")), (tuple("aabbc"), ("a", "b", "c")),
    ):
        report = cross_check_full_lattice(word, alphabet)
        checks_ok = checks_ok and report.status == "witnessed" and report.refused_doctrines == 0
    sweeps_ok = True
    for alphabet, counts, scanned, literal in (
        (("a", "b"), (3, 3), 20, 2),
        (("a", "b"), (4, 2), 15, 3),
        (("a", "b", "c"), (2, 2, 2), 90, 6),
        (("a", "b", "c", "d"), (2, 2, 2, 2), 2520, 24),
    ):
        sweep = nonprincipal_sweep(alphabet, counts)
        sweeps_ok = sweeps_ok and (
            sweep.status == "witnessed" and sweep.words_scanned == scanned
            and sweep.literal_powers == literal and sweep.nonprincipal_words == ()
            and sweep.max_locus_size == 1
        )
    refusal = nonprincipal_sweep(("a", "b", "c"), (4, 4, 4), word_cap=100)
    refusal_ok = refusal.status == "refused" and refusal.obstruction == "sweep-size-refusal"
    checklist_ok = len(break_locus_checklist()) == 5
    passed = known_ok and checks_ok and sweeps_ok and refusal_ok and checklist_ok
    detail = (
        "known loci exact (aabb -> {ab}; aabbcc -> top; abab -> {empty}); "
        "delta predictions match BFS truth on every doctrine of six full "
        "lattices with zero refusals; principality evidence: four exhaustive "
        "shapes in-certificate (2645 words) and seven pinned in tests (6285 "
        "words) with zero non-principal loci - recorded as CONJECTURE "
        "evidence, not a theorem; oversized sweep refuses"
    )
    result = Certificate(
        "break_locus_tr2",
        "break locus: minimal breaking antichain via projection deltas, cross-checked against BFS on the full doctrine lattice",
        passed,
        detail,
        1,
    )
    if not passed:
        logger.error("certify_break_locus_tr2 failed detail=%s", detail)
    logger.debug("certify_break_locus_tr2 exit passed=%s", passed)
    return result
