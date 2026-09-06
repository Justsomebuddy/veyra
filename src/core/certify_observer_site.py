"""Executable certificate for the observer-site internal logic (docs/190)."""

from __future__ import annotations

import logging

from .certify_types import Certificate
from .observer_site import (
    LENGTH,
    WORD,
    PairStatus,
    bounded_reader,
    cotransitivity_failures,
    forces_decided,
    internal_equal,
    observer_site_checklist,
    prime_monotonicity_violations,
    prime_table,
    primitive_at,
    restriction,
    site_law_report,
    standard_site,
    substages,
    undecided_pairs,
    words_up_to,
)

logger = logging.getLogger(__name__)

_ALPHABET = ("a", "b")
_AB, _BA, _ABA = ("a", "b"), ("b", "a"), ("a", "b", "a")


def certify_observer_site_os() -> Certificate:
    """Certify the finite observer site laws on words over {a, b} up to length 3."""
    logger.debug("certify_observer_site_os entry")
    site = standard_site()
    words = words_up_to(_ALPHABET, 3)
    nonempty = words[1:]
    laws = site_law_report(site, words)
    laws_ok = laws.passed and laws.silent_pairs == 0 and laws.stages == 16
    undecided = undecided_pairs(site, (LENGTH,), words)
    split_ok = any(
        row.left == _AB
        and row.right == _BA
        and row.status_at_stage is PairStatus.ECHO
        and row.splitting_observers == ("word",)
        for row in undecided
    ) and not forces_decided(site, (LENGTH,), _AB, _BA)
    complete_ok = all(forces_decided(site, site, left, right) for left in words for right in words)
    partial = (bounded_reader(1),)
    silence_rows = cotransitivity_failures(partial, (("a",), _AB, ("b",)))
    silence_ok = (
        (("a",), _AB, ("b",)) in silence_rows
        and internal_equal(partial, ("a",), _AB)
        and internal_equal(partial, _AB, ("b",))
        and not internal_equal(partial, ("a",), ("b",))
    )
    total_ok = not cotransitivity_failures(site, words) and site_law_report((LENGTH, partial[0]), words).passed
    restriction_ok = all(
        restriction(coarse, fine, words) is not None
        for coarse in substages(site)
        for fine in substages(site)
        if all(o.name in {p.name for p in fine} for o in coarse)
    )
    table = prime_table(site, nonempty, _ALPHABET)
    prime_ok = (
        prime_monotonicity_violations(site, nonempty, _ALPHABET) == 0
        and not primitive_at((LENGTH,), _ABA, _ALPHABET)
        and primitive_at((WORD,), _ABA, _ALPHABET)
        and table["{length}"] == (("a",), ("b",))
        and _AB in table["{word}"]
        and ("a", "b", "a", "b") not in table["{word}"]
    )
    checklist_ok = len(observer_site_checklist()) == 19
    passed = (
        laws_ok
        and split_ok
        and complete_ok
        and silence_ok
        and total_ok
        and restriction_ok
        and prime_ok
        and checklist_ok
    )
    detail = (
        "persistence, retraction and trichotomy hold on all 16 stages of the length/bag/cycle/word "
        "site over 15 words (225 pairs, no silence with total observers); ab/ba echo at {length} and "
        "are split only by word, so neither ab = ba nor ab # ba is forced there while the complete "
        "stage decides every pair; the bounded reader (silent beyond one letter) breaks cotransitivity "
        "and transitivity of internal equality on (a, ab, b) while the three stage laws still hold; "
        "echo classes restrict along every refinement; stage-primitivity is monotone on the lattice, "
        "only one-letter words are primitive at {length}, and aba is composite at {length} but "
        "primitive at {word}; 19 Lean cards mirrored"
    )
    result = Certificate(
        "observer_site_os",
        "finite observer site: apartness persists, echo retracts, excluded middle for equality fails at incomplete stages, silence breaks cotransitivity, stage-primitivity is monotone",
        passed,
        detail,
        1,
    )
    logger.debug("certify_observer_site_os exit passed=%s", passed)
    return result
