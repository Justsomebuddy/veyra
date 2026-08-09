from __future__ import annotations

import pytest

from src.core.observer_descent_reduction import (
    best_lower_approximation,
    descent_reduces_to_best_lower,
    z4_reduction_audit,
)
from src.core.observer_descent_examples import z4_doctrine, z4_shift
from src.core.observer_descent import observer_by_name
from src.core.observer_descent import observer_descent, validate_doctrine
from src.core.observer_descent_types import (
    FiniteObserver,
    FiniteObserverDoctrine,
    FiniteTransition,
)


@pytest.mark.parametrize("shift", range(4))
@pytest.mark.parametrize(
    "target_name",
    ("silence", "parity", "threshold", "phase-pair"),
)
def test_each_z4_descent_is_the_best_admitted_lower_approximation(
    shift: int,
    target_name: str,
):
    doctrine = z4_doctrine()
    assert descent_reduces_to_best_lower(
        doctrine,
        z4_shift(shift),
        observer_by_name(doctrine, target_name),
    )


def test_best_lower_rejects_relations_outside_the_carrier():
    doctrine = z4_doctrine()
    with pytest.raises(ValueError, match="relation-outside-carrier"):
        best_lower_approximation(doctrine, frozenset({(0, 99)}))
    with pytest.raises(TypeError, match="exact-frozenset"):
        best_lower_approximation(doctrine, {(0, 1)})  # type: ignore[arg-type]


def test_r16_finite_audit_rejects_novelty_promotion_after_reduction():
    report = z4_reduction_audit()
    assert (report.descents, report.exact_best_approximations) == (16, 16)
    assert (report.composition_rows, report.exact_precision_gaps) == (64, 64)
    assert report.promotion_status == "reduced-no-novelty-promotion"


def test_internal_join_semilattice_does_not_make_descent_total():
    carrier = (0, 1, 2, 3, 4)

    def observer(name: str, labels: tuple[int, ...]) -> FiniteObserver:
        return FiniteObserver(name, tuple(zip(carrier, labels, strict=True)), 0)

    doctrine = FiniteObserverDoctrine(
        "internal-diamond",
        carrier,
        (
            observer("bottom", (0, 0, 0, 0, 0)),
            observer("a", (0, 0, 1, 1, 1)),
            observer("b", (0, 1, 0, 1, 1)),
            observer("top", carrier),
        ),
    )
    raw_ambient_join = observer("ambient-join", (0, 1, 2, 3, 3))
    identity = FiniteTransition(
        "id",
        carrier,
        carrier,
        tuple(zip(carrier, carrier, strict=True)),
    )
    validate_doctrine(doctrine)
    with pytest.raises(ValueError, match="descent-not-unique"):
        observer_descent(doctrine, identity, raw_ambient_join)
