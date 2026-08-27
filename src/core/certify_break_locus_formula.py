"""Executable certificate for the TR-2/3 break-locus resolution."""

from __future__ import annotations

import logging

from .break_locus import (
    achieved_floor_check,
    break_locus,
    first_slice,
    forced_pairs,
    forcing_report,
    formula_agreement_sweep,
    locus_formula,
    refutation_witness,
)
from .certify_types import Certificate

logger = logging.getLogger(__name__)

AB = ("a", "b")
ABC = ("a", "b", "c")


def certify_break_locus_formula_tr2c() -> Certificate:
    """Certify Achievability, the closed-form locus, and the refutation witness."""
    logger.debug("certify_break_locus_formula_tr2c entry")
    achieved_ok = (
        first_slice(tuple("aabbcc"), ABC, 2) == tuple("abc")
        and all(
            achieved_floor_check(word, alphabet, exponent).attained
            for word, alphabet, exponent in (
                (tuple("aabb"), AB, 2), (tuple("aabbcc"), ABC, 2),
                (tuple("aaabbb"), AB, 3),
                (tuple("aabbab" * 2), AB, 2), (tuple("aabbab" * 2), AB, 3),
            )
        )
        and achieved_floor_check(tuple("aab"), AB, 2).obstruction == "invalid-exponent"
    )
    word, alphabet = refutation_witness()
    locus = break_locus(word, alphabet)
    witness_ok = (
        forced_pairs(word, alphabet, 2) == (("a", "c"), ("b", "c"))
        and forced_pairs(word, alphabet, 3) == (("a", "b"), ("b", "c"))
        and locus.status == "witnessed" and not locus.principal
        and locus.minimal_deltas == ((("a", "b"), ("b", "c")), (("a", "c"), ("b", "c")))
        and locus_formula(word, alphabet) == locus.minimal_deltas
        and forcing_report(word, alphabet).lemma_a_respected
        and achieved_floor_check(word, alphabet, 2).attained
        and achieved_floor_check(word, alphabet, 3).attained
    )
    agreement_ok = True
    agreement_total = 0
    for shape_alphabet, counts, checked in (
        (AB, (3, 3), 20), (AB, (4, 2), 15),
        (ABC, (2, 2, 2), 90), (("a", "b", "c", "d"), (2, 2, 2, 2), 2520),
    ):
        report = formula_agreement_sweep(shape_alphabet, counts)
        agreement_total += report.words_checked
        agreement_ok = agreement_ok and (
            report.status == "witnessed" and report.words_checked == checked
            and report.formula_mismatches == () and report.unachieved_floors == ()
        )
    passed = achieved_ok and witness_ok and agreement_ok
    detail = (
        "firstSlice attains the floor on known cells and on both witness "
        "exponents; the refutation witness aaccabbbaccaaccbbb has "
        "incomparable prime floors and a two-element minimal locus, with "
        "formula == enumeration; agreement and attainment hold on %d "
        "in-certificate exhaustive words (6285 pinned in tests) with zero "
        "failures; single-prime principality is thereby derived and the "
        "general conjecture refuted - statuses recorded in the registry, "
        "prose assembly not promoted beyond its W-001-style rung"
        % agreement_total
    )
    result = Certificate(
        "break_locus_formula_tr2c",
        "break-locus resolution: constructive Achievability, closed-form locus, machine-verified refutation witness",
        passed,
        detail,
        1,
    )
    if not passed:
        logger.error("certify_break_locus_formula_tr2c failed detail=%s", detail)
    logger.debug("certify_break_locus_formula_tr2c exit passed=%s", passed)
    return result
