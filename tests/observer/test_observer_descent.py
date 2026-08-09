from __future__ import annotations

import pytest

from src.core.certify_observer_descent import certify_observer_descent_r16
from src.core.observer_descent import (
    distinction_set,
    observer_by_name,
    observer_descent,
    transition_map,
    validate_doctrine,
)
from src.core.observer_descent_chain import (
    crest_braid,
    residual_chain_balance,
    response_trace,
)
from src.core.observer_descent_examples import (
    Z4,
    z4_closed_crest_braid,
    z4_doctrine,
    z4_parity_descent,
    z4_shift,
    z4_threshold_descent,
    z4_two_tact_balance,
)
from src.core.observer_descent_types import (
    FiniteObserver,
    FiniteObserverDoctrine,
    FiniteTransition,
)


def test_z4_doctrine_is_a_finite_extensional_join_semilattice():
    doctrine = z4_doctrine()
    validate_doctrine(doctrine)
    counts = {
        observer.name: len(distinction_set(observer, doctrine.carrier))
        for observer in doctrine.observers
    }
    assert counts == {"silence": 0, "parity": 8, "threshold": 8, "phase-pair": 12}


def test_parity_descends_exactly_but_threshold_leaves_typed_residual():
    parity = z4_parity_descent()
    threshold = z4_threshold_descent()
    assert (parity.descended_observer, len(parity.residual)) == ("parity", 0)
    assert (threshold.descended_observer, len(threshold.residual)) == ("silence", 8)
    assert threshold.raw_distinctions == threshold.residual


def test_two_successor_tacts_have_nonzero_synergy_and_zero_composite_residual():
    row = z4_two_tact_balance()
    assert row.balanced is True
    assert len(row.pulled_second_residual) == 8
    assert len(row.first_residual) == 0
    assert len(row.composite_residual) == 0
    assert len(row.synergy) == 8


@pytest.mark.parametrize("first", range(4))
@pytest.mark.parametrize("second", range(4))
@pytest.mark.parametrize("target_name", ("silence", "parity", "threshold", "phase-pair"))
def test_residual_chain_balance_for_all_z4_shift_pairs(first, second, target_name):
    doctrine = z4_doctrine()
    row = residual_chain_balance(
        doctrine,
        doctrine,
        z4_shift(first, f"f-{first}"),
        z4_shift(second, f"g-{second}"),
        observer_by_name(doctrine, target_name),
    )
    assert row.balanced is True
    assert row.pulled_second_residual.isdisjoint(row.first_residual)
    assert row.composite_residual.isdisjoint(row.synergy)
    assert (
        row.pulled_second_residual | row.first_residual
        == row.composite_residual | row.synergy
    )


def test_closed_crest_braid_retains_order_erased_by_endpoint_echo():
    braid = z4_closed_crest_braid()
    assert braid.closed is True
    assert braid.endpoint_crest == ()
    assert tuple(tact.crest for tact in braid.tacts) == (
        ("parity",),
        ("parity", "threshold"),
        ("parity",),
        ("parity", "threshold"),
    )


def test_response_trace_is_an_exact_finite_receipt():
    doctrine = z4_doctrine()
    parity = observer_by_name(doctrine, "parity")
    assert response_trace(parity, (0, 1, 2, 3, 0)) == (0, 1, 0, 1, 0)
    with pytest.raises(ValueError, match="response-trace-state-outside-carrier"):
        response_trace(parity, (0, 4))


def test_invalid_doctrines_and_transitions_fail_closed():
    silence = FiniteObserver("silence", tuple((state, 0) for state in Z4), 0)
    parity = FiniteObserver("parity", tuple((state, state % 2) for state in Z4), 1)
    threshold = FiniteObserver(
        "threshold",
        tuple((state, int(state >= 2)) for state in Z4),
        1,
    )
    with pytest.raises(ValueError, match="not-join-semilattice"):
        validate_doctrine(FiniteObserverDoctrine("no-join", Z4, (silence, parity, threshold)))
    duplicate = FiniteObserver("duplicate", silence.responses, 2)
    with pytest.raises(ValueError, match="invalid-extensional-order"):
        validate_doctrine(FiniteObserverDoctrine("duplicate", Z4, (silence, duplicate)))
    broken = FiniteTransition("broken", Z4, Z4, ((0, 1),))
    with pytest.raises(ValueError, match="transition-not-total"):
        transition_map(broken)
    with pytest.raises(TypeError, match="exact-int"):
        z4_shift(True)


def test_wrong_carrier_and_short_paths_are_obstructions():
    doctrine = z4_doctrine()
    wrong = FiniteTransition("wrong", (0, 1), Z4, ((0, 1), (1, 2)))
    with pytest.raises(ValueError, match="descent-source-carrier-mismatch"):
        observer_descent(doctrine, wrong, observer_by_name(doctrine, "parity"))
    with pytest.raises(ValueError, match="crest-path-too-short"):
        crest_braid(doctrine, (0,))


def test_r16_certificate_is_bounded_and_nonclaiming():
    certificate = certify_observer_descent_r16()
    assert certificate.passed is True
    assert certificate.level == 1
    assert "chains=64 balanced=64" in certificate.detail
    assert "not a novelty or universal-calculus claim" in certificate.method
