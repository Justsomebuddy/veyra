"""Composition laws and path invariants derived from observer descent."""

from __future__ import annotations

import logging

from .observer_descent import (
    compose_transitions,
    distinction_set,
    observer_by_name,
    observer_descent,
    observer_response_map,
    transition_map,
    validate_doctrine,
)
from .observer_descent_validation import (
    snapshot_doctrine,
    snapshot_observer,
    snapshot_transition,
)
from .observer_descent_types import (
    CrestBraid,
    CrestTact,
    FiniteObserver,
    FiniteObserverDoctrine,
    FiniteTransition,
    ResidualChainBalance,
    State,
    StatePair,
)

logger = logging.getLogger(__name__)


def pullback_pairs(
    transition: FiniteTransition,
    pairs: frozenset[StatePair],
) -> frozenset[StatePair]:
    """Pull a relation on the target carrier back along both coordinates."""
    name, source, _, _ = snapshot_transition(transition)
    if type(pairs) is not frozenset:
        logger.error("pullback_pairs relation is not exact frozenset")
        raise TypeError("pullback-pairs-requires-exact-frozenset")
    logger.debug("pullback_pairs entry transition=%s pairs=%d", name, len(pairs))
    graph = transition_map(transition)
    result = frozenset(
        (left, right)
        for left in source
        for right in source
        if left != right and (graph[left], graph[right]) in pairs
    )
    logger.debug("pullback_pairs exit transition=%s pairs=%d", name, len(result))
    return result


def residual_chain_balance(
    source_doctrine: FiniteObserverDoctrine,
    middle_doctrine: FiniteObserverDoctrine,
    first: FiniteTransition,
    second: FiniteTransition,
    target_observer: FiniteObserver,
    *,
    target_doctrine: FiniteObserverDoctrine,
) -> ResidualChainBalance:
    """Evaluate the exact typed VODC residual-chain balance with synergy."""
    _, middle_carrier, _ = snapshot_doctrine(middle_doctrine)
    target_doctrine_name, _, _ = snapshot_doctrine(target_doctrine)
    first_name, _, first_target, _ = snapshot_transition(first)
    second_name, second_source, _, _ = snapshot_transition(second)
    target_name, _, _ = snapshot_observer(target_observer)
    logger.debug(
        "residual_chain_balance entry first=%s second=%s "
        "target_doctrine=%s target=%s",
        first_name,
        second_name,
        target_doctrine_name,
        target_name,
    )
    if first_target != middle_carrier or second_source != middle_carrier:
        logger.error("residual_chain_balance middle carrier mismatch")
        raise ValueError("chain-middle-carrier-mismatch")
    second_descent = observer_descent(
        middle_doctrine,
        second,
        target_observer,
        target_doctrine=target_doctrine,
    )
    middle_observer = observer_by_name(
        middle_doctrine,
        second_descent.descended_observer,
    )
    first_descent = observer_descent(
        source_doctrine,
        first,
        middle_observer,
        target_doctrine=middle_doctrine,
    )
    composite = compose_transitions(first, second)
    composite_descent = observer_descent(
        source_doctrine,
        composite,
        target_observer,
        target_doctrine=target_doctrine,
    )
    pulled = pullback_pairs(first, second_descent.residual)
    synergy = (
        composite_descent.admitted_distinctions
        - first_descent.admitted_distinctions
    )
    left = pulled | first_descent.residual
    right = composite_descent.residual | synergy
    balanced = (
        pulled.isdisjoint(first_descent.residual)
        and composite_descent.residual.isdisjoint(synergy)
        and left == right
    )
    result = ResidualChainBalance(
        first_name,
        second_name,
        target_name,
        pulled,
        first_descent.residual,
        composite_descent.residual,
        synergy,
        balanced,
    )
    logger.debug(
        "residual_chain_balance exit balanced=%s left=%d synergy=%d",
        balanced,
        len(left),
        len(synergy),
    )
    return result


def minimal_distinguishers(
    doctrine: FiniteObserverDoctrine,
    left: State,
    right: State,
) -> tuple[str, ...]:
    """Return the least admitted observers that distinguish one ordered pair."""
    doctrine_name, carrier, observers = snapshot_doctrine(doctrine)
    logger.debug(
        "minimal_distinguishers entry doctrine=%s left=%r right=%r",
        doctrine_name,
        left,
        right,
    )
    validate_doctrine(doctrine)
    if left not in carrier or right not in carrier:
        logger.error("minimal_distinguishers state outside carrier")
        raise ValueError("crest-state-outside-carrier")
    rows = tuple(
        (observer, distinction_set(observer, carrier))
        for observer in observers
    )
    distinguishing = tuple((observer, marks) for observer, marks in rows if (left, right) in marks)
    minimal = tuple(
        observer
        for observer, marks in distinguishing
        if not any(other_marks < marks for _, other_marks in distinguishing)
    )
    result = tuple(sorted(snapshot_observer(observer)[0] for observer in minimal))
    logger.debug("minimal_distinguishers exit crest=%s", result)
    return result


def crest_braid(
    doctrine: FiniteObserverDoctrine,
    path: tuple[State, ...],
) -> CrestBraid:
    """Build the ordered finite crest history of a path."""
    doctrine_name, _, _ = snapshot_doctrine(doctrine)
    if type(path) is not tuple:
        logger.error("crest_braid path is not exact tuple")
        raise TypeError("crest-path-requires-exact-tuple")
    logger.debug("crest_braid entry doctrine=%s path=%d", doctrine_name, len(path))
    if len(path) < 2:
        logger.error("crest_braid path too short")
        raise ValueError("crest-path-too-short")
    tacts = tuple(
        CrestTact(left, right, minimal_distinguishers(doctrine, left, right))
        for left, right in zip(path, path[1:])
    )
    result = CrestBraid(
        doctrine_name,
        tacts,
        minimal_distinguishers(doctrine, path[0], path[-1]),
        path[0] == path[-1],
    )
    logger.debug(
        "crest_braid exit closed=%s tacts=%d endpoint_crest=%s",
        result.closed,
        len(result.tacts),
        result.endpoint_crest,
    )
    return result


def response_trace(
    observer: FiniteObserver,
    path: tuple[State, ...],
) -> tuple[object, ...]:
    """Expose an exact finite response receipt for a path observer."""
    observer_name, _, _ = snapshot_observer(observer)
    if type(path) is not tuple:
        logger.error("response_trace path is not exact tuple")
        raise TypeError("response-trace-requires-exact-tuple")
    logger.debug("response_trace entry observer=%s path=%d", observer_name, len(path))
    responses = observer_response_map(observer)
    try:
        result = tuple(responses[state] for state in path)
    except KeyError as error:
        logger.exception("response_trace state outside observer carrier")
        raise ValueError("response-trace-state-outside-carrier") from error
    logger.debug("response_trace exit observer=%s rows=%d", observer_name, len(result))
    return result
