"""Direct isolated certificate for P3-N2 finite and symbolic lanes."""

from __future__ import annotations

import logging

from ..certify_types import Certificate
from ..prime_power.reduction_network.core import (
    BoundaryStatus, FiniteRelation, N2Open, N2Refutation, N2ResourceLimit,
    PrimePowerReductionJudgment, exact_reduction_network_package,
    path_pressure_candidate, prime_power_reduction_judgment,
    refute_wrong_path_candidate, refute_wrong_square_candidate,
    report_missing_symbolic_evidence, square_pressure_candidate, validate_n2_open,
    validate_n2_refutation, validate_prime_power_reduction_result,
)
from ..prime_power.reduction_network.pressure import required_n2_attacks

logger = logging.getLogger(__name__)


def certify_prime_power_reduction_network() -> Certificate:
    """Certify arithmetic N2-F, all-depth N2-S, boundaries, and 23 attacks."""
    logger.debug("certify_prime_power_reduction_network entry")
    package = exact_reduction_network_package()
    result = prime_power_reduction_judgment(package)
    replay = validate_prime_power_reduction_result(package, result)
    refusal_package = exact_reduction_network_package(max_captured_bytes=1)
    refusal = prime_power_reduction_judgment(refusal_package)
    attacks = required_n2_attacks(package, result, refusal)
    square = square_pressure_candidate(package.finite, "integer:2", 1, 0, 1)
    square_refutation = refute_wrong_square_candidate(package, square)
    path = path_pressure_candidate(package.finite, (2, 1, 0), 3, 0)
    path_refutation = refute_wrong_path_candidate(package, path)
    opened = report_missing_symbolic_evidence(package.finite)
    strict = tuple(x for x in result.finite_arrows
                   if x.relation is FiniteRelation.STRICT_REFINEMENT_ON_EXACT_FINITE_SCOPE)
    passed = (type(result) is PrimePowerReductionJudgment and replay == result
        and replay is not result and len(strict) == 3
        and all(x.separator_family_ids for x in strict)
        and result.completed_carrier is BoundaryStatus.NOT_CLAIMED
        and not result.pomega2_final_judgment_consumed and not result.p3c2_status_consumed
        and result.promotions == 0 and type(refusal) is N2ResourceLimit
        and type(square_refutation) is N2Refutation
        and validate_n2_refutation(package, square, square_refutation) == square_refutation
        and type(path_refutation) is N2Refutation
        and validate_n2_refutation(package, path, path_refutation) == path_refutation
        and type(opened) is N2Open and validate_n2_open(package.finite, opened) == opened
        and len(attacks) == 23 and all(ok for _, ok in attacks))
    detail = (f"finite_arrows={len(result.finite_arrows)} strict={len(strict)} "
        f"symbolic_theorems={len(result.theorem_ids)} attacks={sum(ok for _, ok in attacks)}/23 "
        "refutations=2 open=1 raw_p3t_replay=1 direct_n1=1 "
        "completed_carrier_premise=0 c2_premise=0 promotions=0")
    value = Certificate("prime_power_reduction_network_p3n2",
        "arithmetic-derived finite reductions plus all-depth thin Nat-op coherence",
        passed, detail, 1)
    logger.debug("certify_prime_power_reduction_network exit passed=%s", passed)
    return value


if __name__ == "__main__":
    print(certify_prime_power_reduction_network())
