"""Finite observer-descent calculus: types, kernel, chain laws, and audit.

One concept end to end: the exact finite observer doctrine, the fail-closed
snapshots that admit it, the descent kernel, the compositional residual-chain
laws, the canonical Z/4 examples, and the independent best-lower-approximation
oracle that the R16 certificate audits descent against.
"""

from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Hashable, TypeAlias

logger = logging.getLogger(__name__)

State = Hashable
Response = Hashable
StatePair = tuple[State, State]


@dataclass(frozen=True, slots=True)
class FiniteObserver:
    """A named total response table on one finite carrier."""

    name: str
    responses: tuple[tuple[State, Response], ...]
    cost: int


@dataclass(frozen=True, slots=True)
class FiniteObserverDoctrine:
    """A finite admitted observer join-semilattice."""

    name: str
    carrier: tuple[State, ...]
    observers: tuple[FiniteObserver, ...]


@dataclass(frozen=True, slots=True)
class FiniteTransition:
    """A total finite transformation encoded without dynamic callables."""

    name: str
    source: tuple[State, ...]
    target: tuple[State, ...]
    graph: tuple[tuple[State, State], ...]


@dataclass(frozen=True, slots=True)
class ObserverDescent:
    """Unique greatest admitted observer below one exact pullback."""

    transition: str
    target_observer: str
    descended_observer: str
    raw_distinctions: frozenset[StatePair]
    admitted_distinctions: frozenset[StatePair]
    residual: frozenset[StatePair]


@dataclass(frozen=True, slots=True)
class ResidualChainBalance:
    """Two exact decompositions of one compositional distinction debt."""

    first_transition: str
    second_transition: str
    target_observer: str
    pulled_second_residual: frozenset[StatePair]
    first_residual: frozenset[StatePair]
    composite_residual: frozenset[StatePair]
    synergy: frozenset[StatePair]
    balanced: bool


@dataclass(frozen=True, slots=True)
class CrestTact:
    """Minimal observer distinctions retained for one path tact."""

    source: State
    target: State
    crest: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class CrestBraid:
    """Ordered finite crest history, including an endpoint receipt."""

    doctrine: str
    tacts: tuple[CrestTact, ...]
    endpoint_crest: tuple[str, ...]
    closed: bool


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


OBSERVER_DOCTRINE_SCHEMA = "veyra.observer-doctrine.r16.v1"
OBSERVER_DESCENT_SCHEMA = "veyra.observer-descent.r16.v1"
OBSERVER_BALANCE_SCHEMA = "veyra.observer-descent-balance.r16.v1"
CREST_BRAID_SCHEMA = "veyra.crest-braid.r16.v1"

ObserverSnapshot: TypeAlias = tuple[
    str,
    tuple[tuple[State, Response], ...],
    int,
]
DoctrineSnapshot: TypeAlias = tuple[
    str,
    tuple[State, ...],
    tuple[FiniteObserver, ...],
]
TransitionSnapshot: TypeAlias = tuple[
    str,
    tuple[State, ...],
    tuple[State, ...],
    tuple[tuple[State, State], ...],
]

MAX_CARRIER = 256
MAX_OBSERVERS = 256
MAX_NAME_BYTES = 128
MAX_VALUE_DEPTH = 8
MAX_VALUE_WIDTH = 64

Z4 = (0, 1, 2, 3)


def _exact_value(value: object, depth: int = 0) -> bool:
    """Accept only bounded canonical scalar/tuple values, never subclasses."""
    logger.debug("_exact_value entry type=%s depth=%d", type(value).__name__, depth)
    if depth > MAX_VALUE_DEPTH:
        logger.error("_exact_value depth exceeded depth=%d", depth)
        return False
    if type(value) in (type(None), int, str, bytes):
        result = not (
            type(value) in (str, bytes)
            and len(value) > MAX_NAME_BYTES
        )
        logger.debug("_exact_value exit scalar result=%s", result)
        return result
    if type(value) is tuple and len(value) <= MAX_VALUE_WIDTH:
        result = all(_exact_value(item, depth + 1) for item in value)
        logger.debug("_exact_value exit tuple result=%s", result)
        return result
    logger.error("_exact_value rejected type=%s", type(value).__name__)
    return False


def snapshot_observer(observer: object) -> ObserverSnapshot:
    """Read one exact slotted observer once and validate its closed payload."""
    logger.debug("snapshot_observer entry type=%s", type(observer).__name__)
    if type(observer) is not FiniteObserver:
        logger.error("snapshot_observer wrong type=%s", type(observer).__name__)
        raise TypeError("observer-requires-exact-dto")
    try:
        name, responses, cost = observer.name, observer.responses, observer.cost
    except AttributeError as error:
        logger.exception("snapshot_observer missing slot")
        raise TypeError("observer-requires-complete-slots") from error
    if (
        type(name) is not str
        or not name
        or len(name.encode("utf-8")) > MAX_NAME_BYTES
        or type(responses) is not tuple
        or type(cost) is not int
        or cost < 0
    ):
        logger.error("snapshot_observer invalid scalar fields name=%r cost=%r", name, cost)
        raise ValueError("observer-invalid-fields")
    for row in responses:
        if (
            type(row) is not tuple
            or len(row) != 2
            or not _exact_value(row[0])
            or not _exact_value(row[1])
        ):
            logger.error("snapshot_observer invalid response row")
            raise ValueError("observer-invalid-response-row")
    result = (name, responses, cost)
    logger.debug("snapshot_observer exit name=%s rows=%d", name, len(responses))
    return result


def snapshot_doctrine(doctrine: object) -> DoctrineSnapshot:
    """Read one exact doctrine once and enforce bounded canonical carriers."""
    logger.debug("snapshot_doctrine entry type=%s", type(doctrine).__name__)
    if type(doctrine) is not FiniteObserverDoctrine:
        logger.error("snapshot_doctrine wrong type=%s", type(doctrine).__name__)
        raise TypeError("doctrine-requires-exact-dto")
    try:
        name, carrier, observers = doctrine.name, doctrine.carrier, doctrine.observers
    except AttributeError as error:
        logger.exception("snapshot_doctrine missing slot")
        raise TypeError("doctrine-requires-complete-slots") from error
    if (
        type(name) is not str
        or not name
        or len(name.encode("utf-8")) > MAX_NAME_BYTES
        or type(carrier) is not tuple
        or not 0 < len(carrier) <= MAX_CARRIER
        or type(observers) is not tuple
        or not 0 < len(observers) <= MAX_OBSERVERS
        or any(not _exact_value(state) for state in carrier)
    ):
        logger.error("snapshot_doctrine invalid fields")
        raise ValueError("doctrine-invalid-fields")
    for observer in observers:
        snapshot_observer(observer)
    result = (name, carrier, observers)
    logger.debug(
        "snapshot_doctrine exit name=%s carrier=%d observers=%d",
        name,
        len(carrier),
        len(observers),
    )
    return result


def snapshot_transition(transition: object) -> TransitionSnapshot:
    """Read one exact finite transition once and validate closed graph rows."""
    logger.debug("snapshot_transition entry type=%s", type(transition).__name__)
    if type(transition) is not FiniteTransition:
        logger.error("snapshot_transition wrong type=%s", type(transition).__name__)
        raise TypeError("transition-requires-exact-dto")
    try:
        name = transition.name
        source = transition.source
        target = transition.target
        graph = transition.graph
    except AttributeError as error:
        logger.exception("snapshot_transition missing slot")
        raise TypeError("transition-requires-complete-slots") from error
    if (
        type(name) is not str
        or not name
        or len(name.encode("utf-8")) > MAX_NAME_BYTES
        or type(source) is not tuple
        or not 0 < len(source) <= MAX_CARRIER
        or type(target) is not tuple
        or not 0 < len(target) <= MAX_CARRIER
        or type(graph) is not tuple
        or len(graph) > MAX_CARRIER
        or any(not _exact_value(state) for state in source + target)
    ):
        logger.error("snapshot_transition invalid fields")
        raise ValueError("transition-invalid-fields")
    for row in graph:
        if (
            type(row) is not tuple
            or len(row) != 2
            or not _exact_value(row[0])
            or not _exact_value(row[1])
        ):
            logger.error("snapshot_transition invalid graph row")
            raise ValueError("transition-invalid-graph-row")
    result = (name, source, target, graph)
    logger.debug("snapshot_transition exit name=%s graph=%d", name, len(graph))
    return result


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
    """Pull a total observer response backward through a transition."""
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


def observer_descent(
    source_doctrine: FiniteObserverDoctrine,
    transition: FiniteTransition,
    target_observer: FiniteObserver,
) -> ObserverDescent:
    """Compute a unique greatest admitted source observer, or fail closed."""
    doctrine_name, carrier, observers = snapshot_doctrine(source_doctrine)
    transition_name, source, _, _ = snapshot_transition(transition)
    target_name, _, _ = snapshot_observer(target_observer)
    logger.debug(
        "observer_descent entry doctrine=%s transition=%s target=%s",
        doctrine_name,
        transition_name,
        target_name,
    )
    validate_doctrine(source_doctrine)
    if source != carrier:
        logger.error("observer_descent source carrier mismatch")
        raise ValueError("descent-source-carrier-mismatch")
    raw_observer = pullback_observer(transition, target_observer)
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
) -> ResidualChainBalance:
    """Evaluate the exact VODC residual-chain balance with synergy."""
    _, middle_carrier, _ = snapshot_doctrine(middle_doctrine)
    first_name, _, first_target, _ = snapshot_transition(first)
    second_name, second_source, _, _ = snapshot_transition(second)
    target_name, _, _ = snapshot_observer(target_observer)
    logger.debug(
        "residual_chain_balance entry first=%s second=%s target=%s",
        first_name,
        second_name,
        target_name,
    )
    if first_target != middle_carrier or second_source != middle_carrier:
        logger.error("residual_chain_balance middle carrier mismatch")
        raise ValueError("chain-middle-carrier-mismatch")
    second_descent = observer_descent(middle_doctrine, second, target_observer)
    middle_observer = observer_by_name(
        middle_doctrine,
        second_descent.descended_observer,
    )
    first_descent = observer_descent(source_doctrine, first, middle_observer)
    composite = compose_transitions(first, second)
    composite_descent = observer_descent(source_doctrine, composite, target_observer)
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
) -> bool:
    """Check one VODC descent against an independently computed best lower row."""
    logger.debug(
        "descent_reduces_to_best_lower entry transition=%s target=%s",
        transition.name,
        target.name,
    )
    raw_observer = pullback_observer(transition, target)
    concrete = distinction_set(raw_observer, doctrine.carrier)
    oracle = best_lower_approximation(doctrine, concrete)
    descent = observer_descent(doctrine, transition, target)
    result = (
        descent.descended_observer == oracle.observer
        and descent.raw_distinctions == oracle.concrete
        and descent.admitted_distinctions == oracle.abstract
        and descent.residual == oracle.loss
    )
    if not result:
        logger.error(
            "descent_reduces_to_best_lower mismatch transition=%s target=%s",
            transition.name,
            target.name,
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
        descent_reduces_to_best_lower(doctrine, z4_shift(shift), observer)
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
