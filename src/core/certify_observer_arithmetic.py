"""Executable certificate for arithmetic as a variable object over the observer site (docs/191)."""

from __future__ import annotations

import logging

from .certify_types import Certificate
from .observer_arithmetic import (
    bag_primitivity_agreement,
    canonical_cut_associativity_failures,
    descends,
    law_table,
    length_divides,
    literal_laws_hold,
    nat_shadow,
    observer_arithmetic_checklist,
    resonates_at,
    restriction_commutes,
    standard_stages,
    weave_respects_cycle_violations,
)
from .observer_site import BAG, CYCLE, LENGTH, WORD, words_up_to

logger = logging.getLogger(__name__)

_ALPHABET = ("a", "b")
_A, _B, _AB, _BA = ("a",), ("b",), ("a", "b"), ("b", "a")
_EXPECTED_LAWS = {
    "{length}": (True, True, True, True, True),
    "{bag}": (True, True, True, False, True),
    "{cycle}": (False, True, True, False, False),
    "{word}": (True, True, False, False, False),
}


def certify_observer_arithmetic_va() -> Certificate:
    """Certify descent, restriction, the length fibre, the laws table and the AX-005 countermodel."""
    logger.debug("certify_observer_arithmetic_va entry")
    words = words_up_to(_ALPHABET, 3)
    rows = {row.stage: row for row in law_table(standard_stages(), words)}
    laws_ok = (
        all(
            (
                row.stitch_descends,
                row.weave_descends,
                row.stitch_commutative,
                row.weave_commutative,
                row.left_distributive,
            )
            == _EXPECTED_LAWS[stage]
            for stage, row in rows.items()
        )
        and len(rows) == 4
    )
    cycle_report = descends((CYCLE,), "stitch", words)
    cycle_ok = (_AB, _BA, _AB, _AB) in cycle_report.violations and weave_respects_cycle_violations(words, 2) == 0
    restriction_ok = all(
        restriction_commutes(coarse, fine, operation, words)
        for coarse, fine in (
            ((LENGTH,), (LENGTH, BAG)),
            ((LENGTH,), (LENGTH, WORD)),
            ((BAG,), (BAG, WORD)),
            ((LENGTH,), (LENGTH, BAG, WORD)),
        )
        for operation in ("stitch", "weave")
    ) and all(restriction_commutes((LENGTH,), (LENGTH, CYCLE), "weave", words) for _ in (0,))
    shadow = nat_shadow(words)
    nat_ok = shadow.lengths == (0, 1, 2, 3) and shadow.stitch_is_addition and shadow.weave_is_multiplication
    checked, disagreements = bag_primitivity_agreement(words_up_to(_ALPHABET, 6), _ALPHABET)
    parikh_ok = checked == 126 and disagreements == 0
    failures = canonical_cut_associativity_failures(words)
    cut_ok = (_A, _B, _AB) in failures and literal_laws_hold(words)
    nonempty = [word for word in words if word]
    resonance_ok = all(
        resonates_at((LENGTH,), factor, carrier) == length_divides(factor, carrier)
        for factor in nonempty
        for carrier in nonempty
    ) and all(
        not resonates_at((LENGTH, WORD), factor, carrier) or resonates_at((LENGTH,), factor, carrier)
        for factor in nonempty
        for carrier in nonempty
    )
    checklist_ok = len(observer_arithmetic_checklist()) == 14
    passed = (
        laws_ok and cycle_ok and restriction_ok and nat_ok and parikh_ok and cut_ok and resonance_ok and checklist_ok
    )
    detail = (
        "over 15 words up to length 3: stitch descends at {length}, {bag}, {word} and not at {cycle} "
        "(ab~ba, abab vs baab), weave descends at all four stages and respects cyclic echo; commutativity "
        "of stitch holds at {length}, {bag}, {cycle} and fails at {word}, commutativity of weave holds only "
        "at {length}, left distributivity holds at {length}, {bag} and fails at {cycle}, {word}; right "
        "distributivity and associativity are literal; restriction commutes with both operations on four "
        "refinements; the length fibre is 0..3 with stitch as + and weave as ×; native bag-stage "
        f"primitivity agrees with the coprime-counts shadow on {checked} words; the canonical-cut stitch of "
        "closed modes is not associative on (a, b, ab); 14 Lean cards mirrored"
    )
    result = Certificate(
        "observer_arithmetic_va",
        "arithmetic as a variable object: stitch/weave descend to congruence stages and commute with restriction, the natural numbers are the length fibre, commutativity and distributivity are stage properties, AX-005 fails for canonical-cut stitching of closed modes",
        passed,
        detail,
        1,
    )
    logger.debug("certify_observer_arithmetic_va exit passed=%s", passed)
    return result
