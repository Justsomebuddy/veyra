from __future__ import annotations

from dataclasses import replace

import pytest

from src.core.observer_discovery_v3.dsl.types import (
    ClosedObserverGrammar,
    ClosedObserverTerm,
)
from src.core.observer_discovery_v3.schema import (
    CanonicalPresentation,
    RepresentationField,
    RepresentationRow,
    RepresentationSchema,
    canonical_presentation,
)
from src.core.observer_discovery_v3.transport import (
    OBSERVER_TRANSPORT_BLOCKED,
    OBSERVER_TRANSPORT_REFUTED,
    OBSERVER_TRANSPORT_VERIFIED,
    CategoryBijection,
    RepresentationTransportSpec,
    apply_representation_transport,
    check_observer_representation_transport,
    validate_observer_transport_result,
)


def presentation() -> CanonicalPresentation:
    schema = RepresentationSchema(
        "observer-transport-source",
        (
            RepresentationField("bit", "binary", (0, 1)),
            RepresentationField("color", "categorical", ("red", "blue")),
        ),
        ("no", "yes"),
    )
    values = ((0, "red", "no"), (1, "blue", "yes"), (0, "blue", "no"), (1, "red", "yes"))
    rows = tuple(
        RepresentationRow(f"r{index}", f"s{index}", f"c{index}", f"g{index}", (bit, color), target)
        for index, (bit, color, target) in enumerate(values)
    )
    return canonical_presentation(schema, rows)


def transport(source: CanonicalPresentation) -> RepresentationTransportSpec:
    return RepresentationTransportSpec(
        "observer-swap-and-invert",
        source.schema_digest,
        source.payload_digest,
        "observer-transport-destination",
        (3, 2, 1, 0),
        (1, 0),
        ("shade", "inverted-bit"),
        (
            CategoryBijection((("red", "violet"), ("blue", "amber"))),
            CategoryBijection(((0, 1), (1, 0))),
        ),
        CategoryBijection((("no", 0), ("yes", 1))),
    )


def grammar(bit_column: int) -> ClosedObserverGrammar:
    return ClosedObserverGrammar("observer-transport-grammar", 2, (bit_column,), ("column",), 1, 0, 1)


def test_closed_observer_commuting_square_verifies_under_declared_response_bijection() -> None:
    source = presentation()
    spec = transport(source)
    applied = apply_representation_transport(source, spec)
    source_term = ClosedObserverTerm("column", (0,))
    destination_term = ClosedObserverTerm("column", (1,))
    response = CategoryBijection(((0, 1), (1, 0)))

    result = check_observer_representation_transport(
        source,
        spec,
        applied,
        grammar(0),
        source_term,
        grammar(1),
        destination_term,
        response,
    )

    assert result.status == OBSERVER_TRANSPORT_VERIFIED
    assert result.receipt is not None
    assert result.receipt.checked_rows == 4
    assert result.receipt.mismatch_count == 0
    assert validate_observer_transport_result(
        result,
        source,
        spec,
        applied,
        grammar(0),
        source_term,
        grammar(1),
        destination_term,
        response,
    )


def test_wrong_destination_observer_is_completed_refutation_not_blocked() -> None:
    source = presentation()
    spec = transport(source)
    applied = apply_representation_transport(source, spec)

    result = check_observer_representation_transport(
        source,
        spec,
        applied,
        grammar(0),
        ClosedObserverTerm("column", (0,)),
        grammar(1),
        ClosedObserverTerm("column", (0,)),
        CategoryBijection(((0, 1), (1, 0))),
    )

    assert result.status == OBSERVER_TRANSPORT_REFUTED
    assert result.receipt is not None
    assert result.receipt.mismatch_count == 4
    assert result.obstructions[0].reason == "commuting-square-failed"


def test_malformed_response_or_transport_blocks_without_receipt() -> None:
    source = presentation()
    spec = transport(source)
    applied = apply_representation_transport(source, spec)
    cases = (
        (
            applied,
            CategoryBijection(((0, 1), (1, 1))),
        ),
        (
            replace(applied, receipt=None),
            CategoryBijection(((0, 1), (1, 0))),
        ),
    )

    for transport_result, response in cases:
        result = check_observer_representation_transport(
            source,
            spec,
            transport_result,
            grammar(0),
            ClosedObserverTerm("column", (0,)),
            grammar(1),
            ClosedObserverTerm("column", (1,)),
            response,
        )
        assert result.status == OBSERVER_TRANSPORT_BLOCKED
        assert result.receipt is None


def test_validator_rejects_forged_completed_receipt() -> None:
    source = presentation()
    spec = transport(source)
    applied = apply_representation_transport(source, spec)
    response = CategoryBijection(((0, 1), (1, 0)))
    result = check_observer_representation_transport(
        source,
        spec,
        applied,
        grammar(0),
        ClosedObserverTerm("column", (0,)),
        grammar(1),
        ClosedObserverTerm("column", (1,)),
        response,
    )
    assert result.receipt is not None
    forged = replace(result, receipt=replace(result.receipt, mismatch_count=1))

    assert not validate_observer_transport_result(
        forged,
        source,
        spec,
        applied,
        grammar(0),
        ClosedObserverTerm("column", (0,)),
        grammar(1),
        ClosedObserverTerm("column", (1,)),
        response,
    )


def test_program_mutation_before_worker_evaluation_blocks_the_square(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import src.core.observer_discovery_v3.transport.observer as observer

    source = presentation()
    spec = transport(source)
    applied = apply_representation_transport(source, spec)
    source_term = ClosedObserverTerm("column", (0,))
    original_worker = observer.run_closed_observers_isolated
    calls = 0

    def mutate_then_run(*args: object, **kwargs: object):
        nonlocal calls
        calls += 1
        if calls == 1:
            object.__setattr__(source_term, "indices", (1,))
        return original_worker(*args, **kwargs)

    monkeypatch.setattr(observer, "run_closed_observers_isolated", mutate_then_run)
    result = check_observer_representation_transport(
        source,
        spec,
        applied,
        grammar(0),
        source_term,
        grammar(1),
        ClosedObserverTerm("column", (1,)),
        CategoryBijection(((0, 1), (1, 0))),
    )

    assert result.status == OBSERVER_TRANSPORT_BLOCKED
    assert result.receipt is None
    assert result.obstructions[0].reason == "worker-blocked"
