"""Finite executable kernel for Veyra observer descent."""

from __future__ import annotations

import logging

from .observer_descent_types import (
    FiniteObserver,
    FiniteObserverDoctrine,
    FiniteTransition,
    ObserverDescent,
    Response,
    State,
    StatePair,
)
from .observer_descent_validation import (
    snapshot_doctrine,
    snapshot_observer,
    snapshot_transition,
)

logger = logging.getLogger(__name__)


def observer_response_map(observer: FiniteObserver) -> dict[State, Response]:
    """Decode an observer table while rejecting duplicate states."""
    logger.debug("observer_response_map entry type=%s", type(observer).__name__)
    name, rows, _ = snapshot_observer(observer)
    result: dict[State, Response] = {}
    for state, response in rows:
        if state in result:
            logger.error("observer_response_map duplicate state observer=%s", name)
            raise ValueError("observer-response-duplicate-state")
        result[state] = response
    logger.debug("observer_response_map exit observer=%s rows=%d", name, len(result))
    return result


def transition_map(transition: FiniteTransition) -> dict[State, State]:
    """Decode and validate one total finite transition graph."""
    logger.debug("transition_map entry type=%s", type(transition).__name__)
    name, source, target_rows, graph = snapshot_transition(transition)
    result: dict[State, State] = {}
    target = set(target_rows)
    for state, image in graph:
        if state in result:
            logger.error("transition_map duplicate source transition=%s", name)
            raise ValueError("transition-duplicate-source")
        if image not in target:
            logger.error("transition_map image outside target transition=%s", name)
            raise ValueError("transition-image-outside-target")
        result[state] = image
    if set(result) != set(source) or len(result) != len(source):
        logger.error("transition_map non-total transition=%s", name)
        raise ValueError("transition-not-total")
    logger.debug("transition_map exit transition=%s rows=%d", name, len(result))
    return result


def distinction_set(
    observer: FiniteObserver,
    carrier: tuple[State, ...],
) -> frozenset[StatePair]:
    """Return the ordered pairs distinguished by a total observer."""
    name, _, _ = snapshot_observer(observer)
    if type(carrier) is not tuple:
        logger.error("distinction_set carrier is not exact tuple")
        raise TypeError("distinction-carrier-requires-exact-tuple")
    logger.debug("distinction_set entry observer=%s carrier=%d", name, len(carrier))
    responses = observer_response_map(observer)
    if set(responses) != set(carrier) or len(responses) != len(carrier):
        logger.error("distinction_set carrier mismatch observer=%s", name)
        raise ValueError("observer-carrier-mismatch")
    result = frozenset(
        (left, right)
        for left in carrier
        for right in carrier
        if left != right and responses[left] != responses[right]
    )
    logger.debug("distinction_set exit observer=%s pairs=%d", name, len(result))
    return result


def _unique_join(
    left: frozenset[StatePair],
    right: frozenset[StatePair],
    admitted: tuple[frozenset[StatePair], ...],
) -> frozenset[StatePair]:
    """Return the unique least admitted upper bound of two distinction sets."""
    logger.debug("_unique_join entry left=%d right=%d", len(left), len(right))
    upper = tuple(item for item in admitted if left <= item and right <= item)
    minimal = tuple(item for item in upper if not any(other < item for other in upper))
    if len(minimal) != 1:
        logger.error("_unique_join missing or ambiguous count=%d", len(minimal))
        raise ValueError("observer-doctrine-not-join-semilattice")
    logger.debug("_unique_join exit pairs=%d", len(minimal[0]))
    return minimal[0]


def validate_doctrine(doctrine: FiniteObserverDoctrine) -> None:
    """Require a nonempty finite doctrine with unique internal joins.

    This does not make descent total for arbitrary external pullbacks: an
    internal admitted join can overshoot the concrete relation.  Descent
    therefore remains a fail-closed partial operation unless a greatest
    admitted lower approximation exists for the particular pullback.
    """
    name, carrier, observers = snapshot_doctrine(doctrine)
    logger.debug("validate_doctrine entry doctrine=%s", name)
    if len(set(carrier)) != len(carrier):
        logger.error("validate_doctrine invalid carrier doctrine=%s", name)
        raise ValueError("observer-doctrine-invalid-carrier")
    names = tuple(snapshot_observer(observer)[0] for observer in observers)
    if not names or len(set(names)) != len(names):
        logger.error("validate_doctrine invalid names doctrine=%s", name)
        raise ValueError("observer-doctrine-invalid-names")
    admitted = tuple(distinction_set(observer, carrier) for observer in observers)
    if len(set(admitted)) != len(admitted) or frozenset() not in admitted:
        logger.error("validate_doctrine extensional duplicate or no bottom doctrine=%s", name)
        raise ValueError("observer-doctrine-invalid-extensional-order")
    for left in admitted:
        for right in admitted:
            _unique_join(left, right, admitted)
    logger.debug("validate_doctrine exit doctrine=%s observers=%d", name, len(admitted))


def observer_by_name(doctrine: FiniteObserverDoctrine, name: str) -> FiniteObserver:
    """Select exactly one admitted observer by stable name."""
    doctrine_name, _, observers = snapshot_doctrine(doctrine)
    if type(name) is not str:
        logger.error("observer_by_name invalid name type=%s", type(name).__name__)
        raise TypeError("observer-name-requires-exact-string")
    logger.debug("observer_by_name entry doctrine=%s name=%s", doctrine_name, name)
    matches = tuple(
        observer
        for observer in observers
        if snapshot_observer(observer)[0] == name
    )
    if len(matches) != 1:
        logger.error("observer_by_name invalid match count=%d name=%s", len(matches), name)
        raise ValueError("observer-name-not-unique")
    logger.debug("observer_by_name exit name=%s", name)
    return matches[0]


def pullback_observer(
    transition: FiniteTransition,
    target_observer: FiniteObserver,
) -> FiniteObserver:
    """Pull a total observer backward without asserting doctrine admission.

    This is the deliberately ambient, lower-level operation.  The public R16
    descent boundary is :func:`observer_descent`, which additionally requires
    and validates the target doctrine containing ``target_observer``.
    """
    transition_name, source, target, _ = snapshot_transition(transition)
    observer_name, _, observer_cost = snapshot_observer(target_observer)
    logger.debug(
        "pullback_observer entry transition=%s observer=%s",
        transition_name,
        observer_name,
    )
    graph = transition_map(transition)
    target_responses = observer_response_map(target_observer)
    if set(target_responses) != set(target):
        logger.error("pullback_observer target carrier mismatch")
        raise ValueError("pullback-target-carrier-mismatch")
    result = FiniteObserver(
        f"{transition_name}^sharp({observer_name})",
        tuple((state, target_responses[graph[state]]) for state in source),
        observer_cost,
    )
    logger.debug("pullback_observer exit observer=%s", result.name)
    return result


def _admitted_target_observer(
    target_doctrine: FiniteObserverDoctrine,
    target_observer: FiniteObserver,
) -> tuple[str, tuple[State, ...], FiniteObserver]:
    """Return a detached exact target only when its doctrine admits it."""
    doctrine_name, carrier, observers = snapshot_doctrine(target_doctrine)
    target_snapshot = snapshot_observer(target_observer)
    logger.debug(
        "_admitted_target_observer entry doctrine=%s observer=%s",
        doctrine_name,
        target_snapshot[0],
    )
    validate_doctrine(target_doctrine)
    admitted = tuple(snapshot_observer(observer) for observer in observers)
    matches = tuple(candidate for candidate in admitted if candidate == target_snapshot)
    if len(matches) != 1:
        logger.error(
            "_admitted_target_observer rejected doctrine=%s observer=%s matches=%d",
            doctrine_name,
            target_snapshot[0],
            len(matches),
        )
        raise ValueError("descent-target-observer-not-admitted")
    result = FiniteObserver(*target_snapshot)
    logger.debug(
        "_admitted_target_observer exit doctrine=%s observer=%s",
        doctrine_name,
        result.name,
    )
    return doctrine_name, carrier, result


def observer_descent(
    source_doctrine: FiniteObserverDoctrine,
    transition: FiniteTransition,
    target_observer: FiniteObserver,
    *,
    target_doctrine: FiniteObserverDoctrine,
) -> ObserverDescent:
    """Descend one target admitted by its exact finite doctrine.

    Membership compares the complete canonical value (name, responses, cost),
    not Python object identity.  The admitted value is detached before the
    computation, so reconstructed validated DTOs remain usable without
    trusting caller-owned state after admission.
    """
    doctrine_name, carrier, observers = snapshot_doctrine(source_doctrine)
    transition_name, source, transition_target, _ = snapshot_transition(transition)
    target_name, _, _ = snapshot_observer(target_observer)
    target_doctrine_name, target_carrier, admitted_target = (
        _admitted_target_observer(target_doctrine, target_observer)
    )
    logger.debug(
        "observer_descent entry source_doctrine=%s target_doctrine=%s "
        "transition=%s target=%s",
        doctrine_name,
        target_doctrine_name,
        transition_name,
        target_name,
    )
    validate_doctrine(source_doctrine)
    if source != carrier:
        logger.error("observer_descent source carrier mismatch")
        raise ValueError("descent-source-carrier-mismatch")
    if transition_target != target_carrier:
        logger.error("observer_descent target doctrine carrier mismatch")
        raise ValueError("descent-target-doctrine-carrier-mismatch")
    raw_observer = pullback_observer(transition, admitted_target)
    raw = distinction_set(raw_observer, source)
    rows = tuple(
        (observer, distinction_set(observer, carrier))
        for observer in observers
    )
    candidates = tuple((observer, marks) for observer, marks in rows if marks <= raw)
    greatest = tuple(
        item
        for item in candidates
        if not any(item[1] < other[1] for other in candidates)
    )
    if len(greatest) != 1:
        logger.error("observer_descent greatest observer count=%d", len(greatest))
        raise ValueError("descent-not-unique")
    observer, admitted = greatest[0]
    result = ObserverDescent(
        transition_name,
        target_name,
        snapshot_observer(observer)[0],
        raw,
        admitted,
        raw - admitted,
    )
    logger.debug(
        "observer_descent exit descended=%s residual=%d",
        result.descended_observer,
        len(result.residual),
    )
    return result


def compose_transitions(
    first: FiniteTransition,
    second: FiniteTransition,
) -> FiniteTransition:
    """Compose `first` then `second` as an exact finite graph."""
    first_name, first_source, first_target, _ = snapshot_transition(first)
    second_name, second_source, second_target, _ = snapshot_transition(second)
    logger.debug("compose_transitions entry first=%s second=%s", first_name, second_name)
    if first_target != second_source:
        logger.error("compose_transitions carrier mismatch")
        raise ValueError("transition-composition-carrier-mismatch")
    first_map = transition_map(first)
    second_map = transition_map(second)
    result = FiniteTransition(
        f"{second_name}∘{first_name}",
        first_source,
        second_target,
        tuple((state, second_map[first_map[state]]) for state in first_source),
    )
    logger.debug("compose_transitions exit transition=%s", result.name)
    return result
