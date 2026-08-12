"""Canonical finite examples for Veyra observer descent."""

from __future__ import annotations

import logging

from .observer_descent import observer_by_name, observer_descent
from .observer_descent_chain import crest_braid, residual_chain_balance
from .observer_descent_types import (
    CrestBraid,
    FiniteObserver,
    FiniteObserverDoctrine,
    FiniteTransition,
    ObserverDescent,
    ResidualChainBalance,
)

logger = logging.getLogger(__name__)

Z4 = (0, 1, 2, 3)


def z4_doctrine() -> FiniteObserverDoctrine:
    """Return the four-observer diamond doctrine on the cyclic four-state breath."""
    logger.debug("z4_doctrine entry")
    result = FiniteObserverDoctrine(
        "z4-phase-doctrine",
        Z4,
        (
            FiniteObserver("silence", tuple((state, 0) for state in Z4), 0),
            FiniteObserver("parity", tuple((state, state % 2) for state in Z4), 1),
            FiniteObserver(
                "threshold",
                tuple((state, int(state >= 2)) for state in Z4),
                1,
            ),
            FiniteObserver(
                "phase-pair",
                tuple((state, (state % 2, int(state >= 2))) for state in Z4),
                2,
            ),
        ),
    )
    logger.debug("z4_doctrine exit observers=%d", len(result.observers))
    return result


def z4_shift(shift: int, name: str | None = None) -> FiniteTransition:
    """Return one exact cyclic shift on the four-state carrier."""
    logger.debug("z4_shift entry shift=%r name=%s", shift, name)
    if type(shift) is not int:
        logger.error("z4_shift invalid shift type=%s", type(shift).__name__)
        raise TypeError("z4-shift-requires-exact-int")
    normalized = shift % len(Z4)
    result = FiniteTransition(
        name or f"shift-{normalized}",
        Z4,
        Z4,
        tuple((state, (state + normalized) % len(Z4)) for state in Z4),
    )
    logger.debug("z4_shift exit name=%s shift=%d", result.name, normalized)
    return result


def z4_successor(name: str = "succ") -> FiniteTransition:
    """Return the exact one-tact cyclic successor on the four-state carrier."""
    logger.debug("z4_successor entry name=%s", name)
    result = z4_shift(1, name)
    logger.debug("z4_successor exit name=%s", result.name)
    return result


def z4_parity_descent() -> ObserverDescent:
    """Return the exact zero-residual parity descent through successor."""
    logger.debug("z4_parity_descent entry")
    doctrine = z4_doctrine()
    result = observer_descent(
        doctrine,
        z4_successor(),
        observer_by_name(doctrine, "parity"),
        target_doctrine=doctrine,
    )
    logger.debug("z4_parity_descent exit residual=%d", len(result.residual))
    return result


def z4_threshold_descent() -> ObserverDescent:
    """Return the lost threshold distinctions under one successor tact."""
    logger.debug("z4_threshold_descent entry")
    doctrine = z4_doctrine()
    result = observer_descent(
        doctrine,
        z4_successor(),
        observer_by_name(doctrine, "threshold"),
        target_doctrine=doctrine,
    )
    logger.debug(
        "z4_threshold_descent exit descended=%s residual=%d",
        result.descended_observer,
        len(result.residual),
    )
    return result


def z4_two_tact_balance() -> ResidualChainBalance:
    """Return the nonzero-synergy chain balance for two successor tacts."""
    logger.debug("z4_two_tact_balance entry")
    doctrine = z4_doctrine()
    result = residual_chain_balance(
        doctrine,
        doctrine,
        z4_successor("succ-1"),
        z4_successor("succ-2"),
        observer_by_name(doctrine, "threshold"),
        target_doctrine=doctrine,
    )
    logger.debug(
        "z4_two_tact_balance exit balanced=%s synergy=%d",
        result.balanced,
        len(result.synergy),
    )
    return result


def z4_closed_crest_braid() -> CrestBraid:
    """Return a closed path whose ordered crests survive endpoint silence."""
    logger.debug("z4_closed_crest_braid entry")
    result = crest_braid(z4_doctrine(), (0, 1, 2, 3, 0))
    logger.debug(
        "z4_closed_crest_braid exit tacts=%d endpoint=%s",
        len(result.tacts),
        result.endpoint_crest,
    )
    return result
