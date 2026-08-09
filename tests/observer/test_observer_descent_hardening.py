from __future__ import annotations

import pytest

from src.core.observer_descent import (
    observer_by_name,
    observer_descent,
    observer_response_map,
    transition_map,
    validate_doctrine,
)
from src.core.observer_descent_chain import crest_braid, pullback_pairs
from src.core.observer_descent_examples import Z4, z4_doctrine, z4_shift
from src.core.observer_descent_types import (
    FiniteObserver,
    FiniteObserverDoctrine,
    FiniteTransition,
)
from src.core.observer_descent_validation import (
    snapshot_doctrine,
    snapshot_observer,
    snapshot_transition,
)


class Hostile:
    def __hash__(self):
        raise AssertionError("hostile hash must never run")

    def __eq__(self, other):
        raise AssertionError("hostile equality must never run")


class ObserverSubclass(FiniteObserver):
    pass


class DoctrineSubclass(FiniteObserverDoctrine):
    pass


class TransitionSubclass(FiniteTransition):
    pass


def test_exact_dto_branding_rejects_subclasses():
    observer = FiniteObserver("silence", ((0, 0),), 0)
    doctrine = FiniteObserverDoctrine("one", (0,), (observer,))
    transition = FiniteTransition("identity", (0,), (0,), ((0, 0),))
    with pytest.raises(TypeError, match="observer-requires-exact-dto"):
        snapshot_observer(ObserverSubclass("silence", ((0, 0),), 0))
    with pytest.raises(TypeError, match="doctrine-requires-exact-dto"):
        snapshot_doctrine(DoctrineSubclass("one", (0,), (observer,)))
    with pytest.raises(TypeError, match="transition-requires-exact-dto"):
        snapshot_transition(TransitionSubclass("identity", (0,), (0,), ((0, 0),)))
    validate_doctrine(doctrine)
    assert transition_map(transition) == {0: 0}


@pytest.mark.parametrize("cost", (True, 1.0, -1))
def test_cost_bool_float_and_negative_values_fail_closed(cost):
    observer = FiniteObserver("bad", ((0, 0),), cost)
    with pytest.raises(ValueError, match="observer-invalid-fields"):
        snapshot_observer(observer)


def test_hostile_payload_is_rejected_before_hash_or_equality():
    observer = FiniteObserver("hostile", ((Hostile(), 0),), 0)
    doctrine = FiniteObserverDoctrine("hostile", (Hostile(),), (observer,))
    transition = FiniteTransition("hostile", (Hostile(),), (0,), ((Hostile(), 0),))
    with pytest.raises(ValueError, match="observer-invalid-response-row"):
        observer_response_map(observer)
    with pytest.raises(ValueError, match="doctrine-invalid-fields"):
        validate_doctrine(doctrine)
    with pytest.raises(ValueError, match="transition-invalid-fields"):
        transition_map(transition)


def test_deleted_slots_fail_closed_without_partial_evidence():
    observer = FiniteObserver("silence", ((0, 0),), 0)
    doctrine = FiniteObserverDoctrine("one", (0,), (observer,))
    transition = FiniteTransition("identity", (0,), (0,), ((0, 0),))
    object.__delattr__(observer, "cost")
    object.__delattr__(doctrine, "observers")
    object.__delattr__(transition, "graph")
    with pytest.raises(TypeError, match="observer-requires-complete-slots"):
        snapshot_observer(observer)
    with pytest.raises(TypeError, match="doctrine-requires-complete-slots"):
        snapshot_doctrine(doctrine)
    with pytest.raises(TypeError, match="transition-requires-complete-slots"):
        snapshot_transition(transition)


def test_dynamic_containers_and_relations_are_not_laundered():
    doctrine = z4_doctrine()
    parity = observer_by_name(doctrine, "parity")
    with pytest.raises(TypeError, match="crest-path-requires-exact-tuple"):
        crest_braid(doctrine, [0, 1])
    with pytest.raises(TypeError, match="pullback-pairs-requires-exact-frozenset"):
        pullback_pairs(z4_shift(1), {(0, 1)})
    with pytest.raises(TypeError, match="observer-name-requires-exact-string"):
        observer_by_name(doctrine, 1)
    assert observer_descent(doctrine, z4_shift(1), parity).residual == frozenset()


def test_duplicate_graph_sources_and_images_outside_target_fail_closed():
    duplicate = FiniteTransition(
        "duplicate",
        (0, 1),
        (0, 1),
        ((0, 0), (0, 1)),
    )
    outside = FiniteTransition(
        "outside",
        (0, 1),
        (0, 1),
        ((0, 0), (1, 2)),
    )
    with pytest.raises(ValueError, match="transition-duplicate-source"):
        transition_map(duplicate)
    with pytest.raises(ValueError, match="transition-image-outside-target"):
        transition_map(outside)


def test_bounded_payload_and_carrier_limits_are_enforced():
    too_deep: object = 0
    for _ in range(10):
        too_deep = (too_deep,)
    deep = FiniteObserver("deep", ((0, too_deep),), 0)
    huge = tuple(range(257))
    with pytest.raises(ValueError, match="observer-invalid-response-row"):
        snapshot_observer(deep)
    with pytest.raises(ValueError, match="doctrine-invalid-fields"):
        snapshot_doctrine(FiniteObserverDoctrine("huge", huge, ()))


def test_canonical_z4_payloads_remain_exact_after_hardening():
    doctrine = z4_doctrine()
    validate_doctrine(doctrine)
    for observer in doctrine.observers:
        name, responses, cost = snapshot_observer(observer)
        assert name == observer.name
        assert responses == observer.responses
        assert type(cost) is int
    assert tuple(state for state in doctrine.carrier) == Z4
