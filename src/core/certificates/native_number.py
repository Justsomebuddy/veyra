"""Native number-theory certificate hooks for Veyra."""

from __future__ import annotations

import logging

from ..certify_types import Certificate
from ..numbers.compression import CompressionWeights
from ..numbers.modes import Mode
from ..numbers.native_number import compare_spectrum_compression, cycle_divisibility_row, native_number_checklist, native_number_theory_checklist, primitive_count_table, primitive_phase_profile, prime_obstruction_rows, rank_factor_comparison

logger = logging.getLogger(__name__)


def certify_native_resonance_number() -> Certificate:
    """Certify native cycle-echo primitive and rank comparison layer."""
    logger.debug("certify_native_resonance_number entry")
    counts = primitive_count_table(("a", "b"), 3)
    phase = primitive_phase_profile(Mode.from_word("ab"), Mode.from_word("baba"))
    rows = compare_spectrum_compression(Mode.from_word("abac"), [Mode.from_word("ab"), Mode.from_word("ac"), Mode.from_word("cc")], 1)
    ok_counts = [(r.length, r.ordered_primitives, r.cyclic_primitives) for r in counts] == [(1, 2, 2), (2, 2, 1), (3, 6, 2)]
    passed = ok_counts and phase.resonance.cyclic and phase.part_primitive and not phase.whole_primitive and rows[0].part == Mode.from_word("ab") and len(native_number_checklist()) == 6
    detail = f"counts={[(r.ordered_primitives, r.cyclic_primitives) for r in counts]} first={rows[0].part.word}"
    result = Certificate("native_resonance_number", "cycle-echo primitive counts and spectrum/compression comparison", passed, detail, 1)
    logger.debug("certify_native_resonance_number exit result=%r", result)
    return result


def certify_native_number_theory() -> Certificate:
    """Certify Sprint X2 native divisibility/prime/rank-factor layer."""
    logger.debug("certify_native_number_theory entry")
    whole = Mode.from_word("abab")
    div = cycle_divisibility_row(Mode.from_word("ba"), whole)
    bad = cycle_divisibility_row(Mode.from_word("aba"), whole)
    primes = prime_obstruction_rows([Mode.from_word("ab"), Mode.from_word("aa"), Mode.from_word("a")])
    ranks = rank_factor_comparison(whole, [Mode.from_word("ab"), Mode.from_word("ba"), Mode.from_word("aa")], 0, CompressionWeights(defect_weight=1.0))
    passed = div.status == "divides" and div.lift_word == "baba" and bad.obstruction == "length-obstruction" and [r.status for r in primes] == ["variant", "blocked", "blocked"] and [r.factor_status for r in ranks] == ["divides", "divides", "blocked"] and len(native_number_theory_checklist()) == 4
    result = Certificate("native_number_theory_x2", "cycle divisibility, resonance-prime obstructions, factor/lift rank comparison", passed, f"div={div.exponent} ranks={len(ranks)}", 1)
    logger.debug("certify_native_number_theory exit result=%r", result)
    return result
