"""Executable certificate for the TR-2/4 tightness and type-spectrum slice."""

from __future__ import annotations

import logging

from .break_locus import (
    break_locus,
    forced_pairs,
    locus_formula,
    tightness_witness,
    type_spectrum_sweep,
    verify_tightness,
)
from .certify_types import Certificate

logger = logging.getLogger(__name__)


def certify_locus_tightness_tr2d() -> Certificate:
    """Certify the star tightness witnesses and full small-shape type spectrum."""
    logger.debug("certify_locus_tightness_tr2d entry")
    sizes_ok = True
    for primes, expected in (((2,), 1), ((2, 3), 2), ((2, 3, 5), 3)):
        report = verify_tightness(primes)
        sizes_ok = sizes_ok and (
            report.status == "witnessed" and report.locus_size == expected
            and report.special_pattern_ok and report.pairwise_incomparable
        )
    word, alphabet = tightness_witness((2, 3))
    r2_ok = (
        "".join(word) == "aaabbzzbbzaaazbbzz"
        and forced_pairs(word, alphabet, 2) == (("a", "b"), ("b", "z"))
        and forced_pairs(word, alphabet, 3) == (("a", "b"), ("a", "z"))
        and locus_formula(word, alphabet) == break_locus(word, alphabet).minimal_deltas
    )
    spectrum = type_spectrum_sweep(("a", "b", "c"), (2, 2, 2), 2)
    spectrum_ok = (
        spectrum.status == "witnessed" and spectrum.words_scanned == 90
        and len(spectrum.realized_vectors) == 8
    )
    invalid_ok = tightness_witness((4,)) == ("invalid-primes",)
    passed = sizes_ok and r2_ok and spectrum_ok and invalid_ok
    detail = (
        "star witnesses achieve |B| = 1, 2, 3 for prime sets {2}, {2,3}, "
        "{2,3,5} with the special-pair membership pattern and pairwise "
        "incomparable floors - the primes(gcd) bound is tight, "
        "constructively; the r=2 witness floors are exact and the formula "
        "agrees with candidate enumeration; all 8 pair power-type vectors "
        "are realized on the exhaustive a2b2c2 shape at q=2; invalid prime "
        "sets are blocked; general type-matrix realizability remains OPEN"
    )
    result = Certificate(
        "locus_tightness_tr2d",
        "tightness of the prime-count bound via star witnesses, plus full small-shape type-vector spectrum",
        passed,
        detail,
        1,
    )
    if not passed:
        logger.error("certify_locus_tightness_tr2d failed detail=%s", detail)
    logger.debug("certify_locus_tightness_tr2d exit passed=%s", passed)
    return result
