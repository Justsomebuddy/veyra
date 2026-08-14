"""Normal, law, and small-model tests for restricted context transport."""

from __future__ import annotations

from itertools import product
import logging

import pytest

from src.core.observer_realization import (
    observer_realization_context,
    realize_observer_doctrine_r16,
)
from src.core.positive_ontology_doctrine import p0_observer_doctrine
from src.core.proof_core_types import Pulse, Silence
from src.core.realization_transport import (
    CostTransportStatus,
    compose_realization_context_morphisms,
    identity_realization_context_morphism,
    realization_context_morphism,
    realization_transport_scope_boundary,
    verify_realization_transport,
)
from src.core.realization_transport.runtime import _join_partition
from src.core.realization_transport.validation import RealizationTransportValidationError


logger = logging.getLogger(__name__)


def _pulse(depth: int):
    result = Silence()
    for _ in range(depth):
        result = Pulse(result)
    return result


def _context(doctrine, name: str, depths: tuple[int, ...]):
    return observer_realization_context(
        doctrine,
        name,
        tuple((f"{name}-{index}", _pulse(depth)) for index, depth in enumerate(depths)),
        (("crest", 2), ("tail", 3)),
    )


def _receipt(
    doctrine,
    source_depths: tuple[int, ...],
    target_depths: tuple[int, ...],
    graph: tuple[int, ...],
    name: str = "test-arrow",
):
    source = _context(doctrine, f"{name}-source", source_depths)
    target = _context(doctrine, f"{name}-target", target_depths)
    source_witness = realize_observer_doctrine_r16(doctrine, source)
    target_witness = realize_observer_doctrine_r16(doctrine, target)
    receipt = realization_context_morphism(
        doctrine,
        source,
        target,
        name,
        graph,
        source_witness,
        target_witness,
    )
    return source, target, source_witness, target_witness, receipt


def _normalize(values: tuple[int, ...]) -> tuple[int, ...]:
    classes: dict[int, int] = {}
    output: list[int] = []
    for value in values:
        if value not in classes:
            classes[value] = len(classes)
        output.append(classes[value])
    return tuple(output)


def test_join_partition_normalizes_common_refinement():
    logger.debug("test_join_partition_normalizes_common_refinement entry")
    result = _join_partition((0, 0, 1, 1), (0, 1, 0, 1))
    assert result == (0, 1, 2, 3)
    logger.debug("test_join_partition_normalizes_common_refinement exit")


def test_join_partition_accepts_empty_carrier():
    logger.debug("test_join_partition_accepts_empty_carrier entry")
    result = _join_partition((), ())
    assert result == ()
    logger.debug("test_join_partition_accepts_empty_carrier exit")


def test_join_partition_rejects_carrier_mismatch():
    logger.debug("test_join_partition_rejects_carrier_mismatch entry")
    with pytest.raises(
        RealizationTransportValidationError,
        match="^transport-join-carrier-mismatch$",
    ):
        _join_partition((0,), ())
    logger.debug("test_join_partition_rejects_carrier_mismatch exit")


def test_reorder_receipt_replays_endpoints_and_exact_commuting_rows():
    doctrine = p0_observer_doctrine()
    source, target, source_witness, target_witness, receipt = _receipt(
        doctrine, (2, 0, 1), (0, 1, 2), (2, 0, 1), "reorder"
    )

    assert (
        verify_realization_transport(
            doctrine,
            source,
            target,
            receipt.morphism,
            source_witness,
            target_witness,
            receipt,
        )
        == receipt
    )
    assert tuple(row.target_index for row in receipt.recurrence_rows) == (2, 0, 1)
    assert all(
        row.source_input_commitment == row.target_input_commitment
        for row in receipt.recurrence_rows
    )
    assert len(receipt.evaluation_rows) == len(doctrine.observers) * len(source.inputs)
    assert receipt.bottom_preserved and receipt.joins_preserved


def test_subset_pullback_is_extensional_and_cost_can_strictly_decrease():
    doctrine = p0_observer_doctrine()
    source, target, source_witness, target_witness, receipt = _receipt(
        doctrine, (1,), (0, 1, 2), (1,), "singleton-subset"
    )

    assert len(source_witness.closure) == 1
    assert len(receipt.closure_action) == len(target_witness.closure)
    assert all(row.source_partition == (0,) for row in receipt.closure_action)
    assert any(row.status is CostTransportStatus.NONINCREASING for row in receipt.cost_rows)
    assert all(row.source_cost <= row.target_cost for row in receipt.cost_rows)
    assert verify_realization_transport(
        doctrine,
        source,
        target,
        receipt.morphism,
        source_witness,
        target_witness,
        receipt,
    ) == receipt


def test_duplicate_state_reindexing_is_allowed_when_recurrence_and_payload_commute():
    doctrine = p0_observer_doctrine()
    _, _, _, _, receipt = _receipt(
        doctrine, (1, 1), (0, 1, 2), (1, 1), "duplicate-target"
    )

    assert receipt.morphism.state_index_map == (1, 1)
    assert all(row.source_input_commitment == row.target_input_commitment for row in receipt.recurrence_rows)


def test_identity_builder_has_identity_graph_and_exact_cost_rows():
    doctrine = p0_observer_doctrine()
    context = _context(doctrine, "identity-context", (0, 1, 2))
    witness = realize_observer_doctrine_r16(doctrine, context)
    receipt = identity_realization_context_morphism(doctrine, context, witness)

    assert receipt.morphism.state_index_map == (0, 1, 2)
    assert all(row.status is CostTransportStatus.EXACT for row in receipt.cost_rows)
    assert tuple(row.source_partition for row in receipt.closure_action) == tuple(
        row.partition for row in witness.closure
    )


def test_composition_reconstructs_direct_graph_and_contravariant_action():
    doctrine = p0_observer_doctrine()
    source = _context(doctrine, "composition-source", (2, 0, 1))
    middle = _context(doctrine, "composition-middle", (1, 2, 0))
    target = _context(doctrine, "composition-target", (0, 1, 2))
    source_witness = realize_observer_doctrine_r16(doctrine, source)
    middle_witness = realize_observer_doctrine_r16(doctrine, middle)
    target_witness = realize_observer_doctrine_r16(doctrine, target)
    first = realization_context_morphism(
        doctrine,
        source,
        middle,
        "source-to-middle",
        (1, 2, 0),
        source_witness,
        middle_witness,
    )
    second = realization_context_morphism(
        doctrine,
        middle,
        target,
        "middle-to-target",
        (1, 2, 0),
        middle_witness,
        target_witness,
    )
    composed = compose_realization_context_morphisms(
        doctrine,
        source,
        middle,
        target,
        first,
        second,
        source_witness,
        middle_witness,
        target_witness,
        "composed",
    )
    direct = realization_context_morphism(
        doctrine,
        source,
        target,
        "direct",
        (2, 0, 1),
        source_witness,
        target_witness,
    )

    assert composed.morphism.state_index_map == direct.morphism.state_index_map
    assert tuple(row.source_partition for row in composed.closure_action) == tuple(
        row.source_partition for row in direct.closure_action
    )
    assert tuple((row.source_cost, row.target_cost) for row in composed.cost_rows) == tuple(
        (row.source_cost, row.target_cost) for row in direct.cost_rows
    )


def test_state_graph_composition_is_associative_under_fresh_reconstruction():
    doctrine = p0_observer_doctrine()
    contexts = tuple(
        _context(doctrine, f"associative-{index}", depths)
        for index, depths in enumerate(
            ((0, 1, 2), (2, 0, 1), (1, 2, 0), (0, 1, 2))
        )
    )
    witnesses = tuple(
        realize_observer_doctrine_r16(doctrine, context) for context in contexts
    )
    graph = (1, 2, 0)
    edges = tuple(
        realization_context_morphism(
            doctrine,
            contexts[index],
            contexts[index + 1],
            f"associative-edge-{index}",
            graph,
            witnesses[index],
            witnesses[index + 1],
        )
        for index in range(3)
    )
    source_to_third = compose_realization_context_morphisms(
        doctrine, *contexts[:3], *edges[:2], *witnesses[:3], "left-prefix"
    )
    left = compose_realization_context_morphisms(
        doctrine,
        contexts[0],
        contexts[2],
        contexts[3],
        source_to_third,
        edges[2],
        witnesses[0],
        witnesses[2],
        witnesses[3],
        "left-associated",
    )
    second_to_target = compose_realization_context_morphisms(
        doctrine, *contexts[1:], *edges[1:], *witnesses[1:], "right-suffix"
    )
    right = compose_realization_context_morphisms(
        doctrine,
        *contexts[:2],
        contexts[3],
        edges[0],
        second_to_target,
        *witnesses[:2],
        witnesses[3],
        "right-associated",
    )

    assert left.morphism.state_index_map == right.morphism.state_index_map == (0, 1, 2)
    assert left.closure_action == right.closure_action
    assert left.cost_rows == right.cost_rows
    assert left.evaluation_rows == right.evaluation_rows


def test_exhaustive_small_total_maps_match_independent_partition_pullback():
    doctrine = p0_observer_doctrine()
    target_depths = (0, 1, 2)
    for source_count in range(1, 4):
        for ordinal, graph in enumerate(product(range(3), repeat=source_count)):
            source_depths = tuple(target_depths[index] for index in graph)
            _, _, _, target_witness, receipt = _receipt(
                doctrine,
                source_depths,
                target_depths,
                tuple(graph),
                f"small-{source_count}-{ordinal}",
            )
            expected = tuple(
                _normalize(tuple(row.partition[index] for index in graph))
                for row in target_witness.closure
            )
            assert tuple(row.source_partition for row in receipt.closure_action) == expected


def test_scope_states_single_arrow_and_explicit_nonclaims():
    scope = realization_transport_scope_boundary()

    assert "finite-relative-replayed-single-arrow-no-category-or-functor-claim" in scope
    assert "no-cross-doctrine-transport" in scope
    assert "no-p1a-response-transport" in scope
    assert "no-natural-quotient-section" in scope
    assert "same-exact-p1-doctrine-only" in scope
    assert "no-p1a-cross-doctrine-or-covariant-pushforward-claim" in scope
    assert "local-names-ordinals-generators-and-representatives-do-not-transport" in scope
    assert "single-arrow-identity-and-composition-evidence-not-category-or-functor-proof" in scope
