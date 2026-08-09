"""Bounded certificate for Veyra observer-descent calculus."""

from __future__ import annotations

import logging

from ..certify_types import Certificate
from ..observer.descent import (
    observer_by_name,
    observer_descent,
    residual_chain_balance,
    validate_doctrine,
    z4_closed_crest_braid,
    z4_doctrine,
    z4_parity_descent,
    z4_reduction_audit,
    z4_shift,
    z4_threshold_descent,
    z4_two_tact_balance,
)

logger = logging.getLogger(__name__)

R16_CERTIFICATE_NAME = "observer_descent_r16"
R16_CERTIFICATE_METHOD = (
    "bounded finite observer-doctrine descent, residual-chain balance, "
    "synergy, and crest-braid audit; not a novelty or universal-calculus claim"
)


def certify_observer_descent_r16() -> Certificate:
    """Certify the finite Z/4 model and all 64 shift-chain balances."""
    logger.debug("certify_observer_descent_r16 entry")
    try:
        doctrine = z4_doctrine()
        validate_doctrine(doctrine)
        parity = z4_parity_descent()
        threshold = z4_threshold_descent()
        synergy = z4_two_tact_balance()
        braid = z4_closed_crest_braid()
        reduction = z4_reduction_audit()
        targets = tuple(
            observer_by_name(doctrine, name)
            for name in ("silence", "parity", "threshold", "phase-pair")
        )
        balances = tuple(
            residual_chain_balance(
                doctrine,
                doctrine,
                z4_shift(first, f"first-{first}"),
                z4_shift(second, f"second-{second}"),
                target,
            )
            for first in range(4)
            for second in range(4)
            for target in targets
        )
        descents = tuple(
            observer_descent(doctrine, z4_shift(shift), target)
            for shift in range(4)
            for target in targets
        )
        passed = (
            parity.descended_observer == "parity"
            and not parity.residual
            and threshold.descended_observer == "silence"
            and len(threshold.residual) == 8
            and synergy.balanced
            and len(synergy.synergy) == 8
            and len(synergy.composite_residual) == 0
            and len(balances) == 64
            and all(row.balanced for row in balances)
            and len(descents) == 16
            and braid.closed
            and len(braid.tacts) == 4
            and braid.endpoint_crest == ()
            and all(tact.crest for tact in braid.tacts)
            and reduction.descents == reduction.exact_best_approximations == 16
            and reduction.composition_rows == reduction.exact_precision_gaps == 64
            and reduction.promotion_status == "reduced-no-novelty-promotion"
        )
        detail = (
            "doctrine=4 shifts=4 descents=16 chains=64 balanced=64 "
            "threshold-residual=8 two-tact-synergy=8 braid=4 endpoint=echo "
            "reduction=best-lower-approximation promotion=rejected "
            "nonclaims=novelty,universality,blocked-response-completion"
        )
    except (KeyError, TypeError, ValueError) as error:
        logger.exception("certify_observer_descent_r16 blocked")
        passed = False
        detail = f"blocked={type(error).__name__}:{error}"
    result = Certificate(
        R16_CERTIFICATE_NAME,
        R16_CERTIFICATE_METHOD,
        passed,
        detail,
        1,
    )
    if not passed:
        logger.error("certify_observer_descent_r16 failed detail=%s", detail)
    logger.debug("certify_observer_descent_r16 exit result=%r", result)
    return result
