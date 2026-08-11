"""Finite reduction audit from VODC to best lower approximation."""

from __future__ import annotations

from dataclasses import dataclass
import logging

from .observer_descent import (
    distinction_set,
    observer_by_name,
    observer_descent,
    pullback_observer,
    validate_doctrine,
)
from .observer_descent_chain import residual_chain_balance
from .observer_descent_examples import z4_doctrine, z4_shift
from .observer_descent_types import (
    FiniteObserver,
    FiniteObserverDoctrine,
    FiniteTransition,
    StatePair,
)
from .observer_descent_validation import (
    snapshot_doctrine,
    snapshot_observer,
    snapshot_transition,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class BestLowerApproximation:
    """Greatest admitted distinction relation contained in a concrete one."""

    observer: str
    concrete: frozenset[StatePair]
    abstract: frozenset[StatePair]
    loss: frozenset[StatePair]


@dataclass(frozen=True, slots=True)
class ReductionAudit:
    """Bounded comparison with the independent lower-approximation oracle."""

    descents: int
    exact_best_approximations: int
    composition_rows: int
    exact_precision_gaps: int
    promotion_status: str


def best_lower_approximation(
    doctrine: FiniteObserverDoctrine,
    concrete: frozenset[StatePair],
) -> BestLowerApproximation:
    """Compute the greatest admitted relation below ``concrete`` independently."""
    doctrine_name, carrier, observers = snapshot_doctrine(doctrine)
    logger.debug(
        "best_lower_approximation entry doctrine=%s concrete=%d",
        doctrine_name,
        len(concrete) if type(concrete) is frozenset else -1,
    )
    validate_doctrine(doctrine)
    if type(concrete) is not frozenset:
        logger.error("best_lower_approximation non-frozenset concrete relation")
        raise TypeError("best-lower-concrete-requires-exact-frozenset")
    possible = frozenset(
        (left, right) for left in carrier for right in carrier if left != right
    )
    if not concrete <= possible:
        logger.error("best_lower_approximation relation outside carrier")
        raise ValueError("best-lower-relation-outside-carrier")
    rows = tuple(
        (observer, distinction_set(observer, carrier)) for observer in observers
    )
    candidates = tuple(row for row in rows if row[1] <= concrete)
    greatest = tuple(
        row
        for row in candidates
        if not any(row[1] < other[1] for other in candidates)
    )
    if len(greatest) != 1:
        logger.error("best_lower_approximation ambiguous greatest=%d", len(greatest))
        raise ValueError("best-lower-not-unique")
    observer, abstract = greatest[0]
    result = BestLowerApproximation(
        snapshot_observer(observer)[0],
        concrete,
        abstract,
        concrete - abstract,
    )
    logger.debug(
        "best_lower_approximation exit observer=%s loss=%d",
        result.observer,
        len(result.loss),
    )
    return result


def descent_reduces_to_best_lower(
    doctrine: FiniteObserverDoctrine,
    transition: FiniteTransition,
    target: FiniteObserver,
    *,
    target_doctrine: FiniteObserverDoctrine,
) -> bool:
    """Check one VODC descent against an independently computed best lower row."""
    transition_name, _, _, _ = snapshot_transition(transition)
    target_doctrine_name, _, _ = snapshot_doctrine(target_doctrine)
    target_name, _, _ = snapshot_observer(target)
    logger.debug(
        "descent_reduces_to_best_lower entry transition=%s "
        "target_doctrine=%s target=%s",
        transition_name,
        target_doctrine_name,
        target_name,
    )
    descent = observer_descent(
        doctrine,
        transition,
        target,
        target_doctrine=target_doctrine,
    )
    raw_observer = pullback_observer(transition, target)
    concrete = distinction_set(raw_observer, doctrine.carrier)
    oracle = best_lower_approximation(doctrine, concrete)
    result = (
        descent.descended_observer == oracle.observer
        and descent.raw_distinctions == oracle.concrete
        and descent.admitted_distinctions == oracle.abstract
        and descent.residual == oracle.loss
    )
    if not result:
        logger.error(
            "descent_reduces_to_best_lower mismatch transition=%s target=%s",
            transition_name,
            target_name,
        )
    logger.debug("descent_reduces_to_best_lower exit result=%s", result)
    return result


def z4_reduction_audit() -> ReductionAudit:
    """Audit all Z/4 descents and composition gaps used by the R16 certificate."""
    logger.debug("z4_reduction_audit entry")
    doctrine = z4_doctrine()
    observers = tuple(observer_by_name(doctrine, name) for name in (
        "silence",
        "parity",
        "threshold",
        "phase-pair",
    ))
    descent_rows = tuple(
        descent_reduces_to_best_lower(
            doctrine,
            z4_shift(shift),
            observer,
            target_doctrine=doctrine,
        )
        for shift in range(4)
        for observer in observers
    )
    chain_rows = tuple(
        residual_chain_balance(
            doctrine,
            doctrine,
            z4_shift(first, f"first-{first}"),
            z4_shift(second, f"second-{second}"),
            observer,
            target_doctrine=doctrine,
        )
        for first in range(4)
        for second in range(4)
        for observer in observers
    )
    exact_gaps = sum(
        row.balanced
        and row.synergy
        == (
            (row.composite_residual | row.synergy)
            - row.composite_residual
        )
        for row in chain_rows
    )
    result = ReductionAudit(
        len(descent_rows),
        sum(descent_rows),
        len(chain_rows),
        exact_gaps,
        "reduced-no-novelty-promotion",
    )
    logger.info(
        "z4_reduction_audit state descents=%d/%d gaps=%d/%d promotion=%s",
        result.exact_best_approximations,
        result.descents,
        result.exact_precision_gaps,
        result.composition_rows,
        result.promotion_status,
    )
    logger.debug("z4_reduction_audit exit result=%r", result)
    return result
