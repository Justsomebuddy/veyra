"""Executable certificate for the resonance-arithmetic lane (docs/189)."""

from __future__ import annotations

import logging

from .certify_types import Certificate
from .resonance_arithmetic import (
    default_anchor,
    euclid_escape_witness,
    fermat_phase_witness,
    length,
    phase_congruent,
    resonance_arithmetic_checklist,
    resonance_prime_witness,
    resonates,
    shared_closure,
    shared_echo,
    unary,
)

logger = logging.getLogger(__name__)

_PRIME_PERIODS = (2, 3, 5, 7, 11, 13)
_COMPOSITE_PERIODS = (4, 6, 9)
_ESCAPES = ((2, 3), (2, 3, 5))
_ECHO_PAIRS = ((12, 18, 6, 36), (7, 5, 1, 35), (9, 6, 3, 18), (10, 10, 10, 10))
_CONGRUENCE_ROWS = ((7, 9, 2, True), (7, 9, 3, False), (5, 13, 8, True), (6, 4, 10, True))


def certify_resonance_arithmetic_ra() -> Certificate:
    """Certify the native resonance vocabulary on exact bounded rows."""
    logger.debug("certify_resonance_arithmetic_ra entry")
    anchor = default_anchor()
    echo_ok = all(
        length(shared_echo(unary(anchor, left), unary(anchor, right))) == gcd_value
        and length(shared_closure(unary(anchor, left), unary(anchor, right))) == lcm_value
        and resonates(shared_echo(unary(anchor, left), unary(anchor, right)), unary(anchor, left))
        and resonates(unary(anchor, right), shared_closure(unary(anchor, left), unary(anchor, right)))
        for left, right, gcd_value, lcm_value in _ECHO_PAIRS
    )
    congruence_ok = all(
        phase_congruent(unary(anchor, modulus), unary(anchor, left), unary(anchor, right)) is expected
        for modulus, left, right, expected in _CONGRUENCE_ROWS
    )
    primes_ok = all(resonance_prime_witness(anchor, unary(anchor, value)).prime for value in _PRIME_PERIODS) and all(
        resonance_prime_witness(anchor, unary(anchor, value)).obstruction == "composite-rhythm" for value in _COMPOSITE_PERIODS
    )
    fermat_rows = tuple(fermat_phase_witness(anchor, period) for period in _PRIME_PERIODS)
    blocked_rows = tuple(fermat_phase_witness(anchor, period) for period in _COMPOSITE_PERIODS)
    fermat_ok = all(row.status == "witnessed" and row.returns and row.lagrange and row.cyclic for row in fermat_rows) and all(
        row.status == "blocked" and row.obstruction == "composite-period" and not row.returns for row in blocked_rows
    )
    escape_rows = tuple(euclid_escape_witness(anchor, factors) for factors in _ESCAPES)
    escape_ok = all(row.status == "witnessed" and all(item == 1 for item in row.residual_lengths) for row in escape_rows) and (
        escape_rows[0].new_prime_length == 7 and escape_rows[1].new_prime_length == 31
    )
    checklist_ok = len(resonance_arithmetic_checklist()) == 6
    passed = echo_ok and congruence_ok and primes_ok and fermat_ok and escape_ok and checklist_ok
    detail = (
        "shared echo/closure match on four pairs by structural Euclid; phase congruence on "
        "four rows; native resonance primes 2..13 witnessed and 4, 6, 9 blocked as composite "
        "rhythms; Fermat phase return, Lagrange and generator witnessed natively for periods "
        "2..13 with composites blocked on an exhibited failing unit; product-plus-one escapes "
        "of (2,3) and (2,3,5) leave the unit phase and carry the new resonance primes 7 and "
        "31; no host arithmetic on any decision path (AST-guarded)"
    )
    result = Certificate(
        "resonance_arithmetic_ra",
        "native resonance vocabulary: structural division, phase congruence, indecomposable rhythms, shared echo/closure, Fermat and Euclid rows",
        passed,
        detail,
        1,
    )
    logger.debug("certify_resonance_arithmetic_ra exit passed=%s", passed)
    return result
