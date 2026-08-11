"""Regression tests for the exact R16 target-admission boundary."""

from __future__ import annotations

from dataclasses import replace
import logging

import pytest

import src.core.certify_observer_descent as certificate_module
from src.core.observer_descent import (
    observer_by_name,
    observer_descent,
    pullback_observer,
)
from src.core.observer_descent_chain import residual_chain_balance
from src.core.observer_descent_examples import Z4, z4_doctrine, z4_shift
from src.core.observer_descent_types import (
    FiniteObserver,
    FiniteObserverDoctrine,
    FiniteTransition,
)

logger = logging.getLogger(__name__)


def _bottom_doctrine(
    name: str,
    carrier: tuple[int, ...],
) -> FiniteObserverDoctrine:
    logger.debug("_bottom_doctrine entry name=%s carrier=%d", name, len(carrier))
    bottom = FiniteObserver(
        "bottom",
        tuple((state, 0) for state in carrier),
        0,
    )
    result = FiniteObserverDoctrine(name, carrier, (bottom,))
    logger.debug("_bottom_doctrine exit name=%s", name)
    return result


def _identity(carrier: tuple[int, ...]) -> FiniteTransition:
    logger.debug("_identity entry carrier=%d", len(carrier))
    result = FiniteTransition(
        "identity",
        carrier,
        carrier,
        tuple((state, state) for state in carrier),
    )
    logger.debug("_identity exit rows=%d", len(result.graph))
    return result


def test_issue_10_external_target_is_not_admitted_by_name_or_totality():
    logger.debug("issue-10 external-target rejection test entry")
    source = _bottom_doctrine("source-bottom-only", Z4)
    target = _bottom_doctrine("target-bottom-only", Z4)
    external = FiniteObserver(
        "external-top",
        tuple((state, state) for state in Z4),
        0,
    )

    with pytest.raises(ValueError, match="descent-target-observer-not-admitted"):
        observer_descent(
            source,
            _identity(Z4),
            external,
            target_doctrine=target,
        )
    logger.debug("issue-10 external-target rejection observed; test exit")


def test_exact_detached_observer_value_is_admitted_without_object_identity():
    logger.debug("detached exact target admission test entry")
    doctrine = z4_doctrine()
    canonical = observer_by_name(doctrine, "parity")
    detached = FiniteObserver(
        canonical.name,
        tuple(canonical.responses),
        canonical.cost,
    )

    result = observer_descent(
        doctrine,
        z4_shift(1),
        detached,
        target_doctrine=doctrine,
    )

    assert detached is not canonical
    assert result.descended_observer == "parity"
    assert result.residual == frozenset()
    logger.debug("detached exact target admission test exit")


@pytest.mark.parametrize(
    "drift_kind",
    (
        "name",
        "cost",
        "row-order",
        "response",
        "same-distinction-relabel",
    ),
)
def test_name_cost_order_or_response_drift_does_not_launder_membership(
    drift_kind: str,
):
    logger.debug("target membership drift test entry kind=%s", drift_kind)
    doctrine = z4_doctrine()
    observer = observer_by_name(doctrine, "parity")
    if drift_kind == "name":
        changed = replace(observer, name="renamed-parity")
    elif drift_kind == "cost":
        changed = replace(observer, cost=observer.cost + 1)
    elif drift_kind == "row-order":
        changed = replace(observer, responses=tuple(reversed(observer.responses)))
    elif drift_kind == "response":
        changed = replace(observer, responses=((0, 1),) + observer.responses[1:])
    else:
        changed = replace(
            observer,
            responses=tuple(
                (state, 1 - response) for state, response in observer.responses
            ),
        )

    with pytest.raises(ValueError, match="descent-target-observer-not-admitted"):
        observer_descent(
            doctrine,
            z4_shift(0),
            changed,
            target_doctrine=doctrine,
        )
    logger.debug("target membership drift rejected kind=%s; test exit", drift_kind)


def test_invalid_target_doctrine_fails_before_it_can_admit_a_target():
    logger.debug("invalid target doctrine test entry")
    bottom = FiniteObserver("bottom", ((0, 0), (1, 0)), 0)
    duplicate = FiniteObserver("duplicate", bottom.responses, 1)
    invalid = FiniteObserverDoctrine("invalid-target", (0, 1), (bottom, duplicate))

    with pytest.raises(ValueError, match="invalid-extensional-order"):
        observer_descent(
            _bottom_doctrine("source", (0, 1)),
            _identity((0, 1)),
            bottom,
            target_doctrine=invalid,
        )
    logger.debug("invalid target doctrine rejected; test exit")


def test_transition_target_must_equal_target_doctrine_carrier_in_order():
    logger.debug("target doctrine ordered-carrier test entry")
    source = _bottom_doctrine("source", (0, 1))
    target = _bottom_doctrine("reordered-target", (1, 0))
    admitted = target.observers[0]

    with pytest.raises(ValueError, match="target-doctrine-carrier-mismatch"):
        observer_descent(
            source,
            _identity((0, 1)),
            admitted,
            target_doctrine=target,
        )
    logger.debug("target doctrine ordered-carrier mismatch rejected; test exit")


def test_chain_balance_propagates_final_target_admission():
    logger.debug("chain target admission test entry")
    doctrine = _bottom_doctrine("bottom-only", (0, 1))
    external = FiniteObserver("external", ((0, 0), (1, 1)), 0)

    with pytest.raises(ValueError, match="descent-target-observer-not-admitted"):
        residual_chain_balance(
            doctrine,
            doctrine,
            _identity((0, 1)),
            _identity((0, 1)),
            external,
            target_doctrine=doctrine,
        )
    logger.debug("chain target admission rejection observed; test exit")


def test_legacy_three_argument_descent_fails_closed_without_target_doctrine():
    logger.debug("required keyword-only target doctrine test entry")
    doctrine = z4_doctrine()
    parity = observer_by_name(doctrine, "parity")

    with pytest.raises(TypeError, match="target_doctrine"):
        observer_descent(doctrine, z4_shift(0), parity)

    with pytest.raises(TypeError):
        observer_descent(doctrine, z4_shift(0), parity, doctrine)  # type: ignore[misc]
    logger.debug("missing/positional target doctrine rejected; test exit")


def test_raw_pullback_remains_ambient_and_is_not_membership_evidence():
    logger.debug("ambient raw pullback test entry")
    external = FiniteObserver(
        "external-top",
        tuple((state, state) for state in Z4),
        0,
    )

    raw = pullback_observer(_identity(Z4), external)

    assert raw.responses == external.responses
    assert raw.name == "identity^sharp(external-top)"
    logger.debug("ambient raw pullback test exit")


def test_certificate_reports_actual_failed_admission_attack_count(monkeypatch):
    """A failed attack gate must never retain a hard-coded passing detail."""
    logger.debug("certificate admission attack honesty test entry")
    original = certificate_module.observer_descent

    def allow_one_external_target(
        source_doctrine,
        transition,
        target_observer,
        *,
        target_doctrine,
    ):
        logger.debug(
            "allow_one_external_target entry target=%s",
            target_observer.name,
        )
        if target_observer.name == "external-parity":
            target_observer = observer_by_name(target_doctrine, "parity")
        try:
            result = original(
                source_doctrine,
                transition,
                target_observer,
                target_doctrine=target_doctrine,
            )
        except Exception:
            logger.debug("allow_one_external_target propagating rejection")
            raise
        logger.debug(
            "allow_one_external_target exit descended=%s",
            result.descended_observer,
        )
        return result

    monkeypatch.setattr(
        certificate_module,
        "observer_descent",
        allow_one_external_target,
    )

    certificate = certificate_module.certify_observer_descent_r16()

    assert certificate.passed is False
    assert "attacks=3/4" in certificate.detail
    assert "attacks=4/4" not in certificate.detail
    logger.debug("certificate admission attack honesty test exit")
