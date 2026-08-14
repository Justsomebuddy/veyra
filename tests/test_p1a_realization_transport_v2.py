"""Normal, all-status, partition, identity, and composition tests for RFC 169."""

from __future__ import annotations

import json
import logging

import pytest

from src.core.observer_morphism_types import ProjectionStep
from src.core.observer_realization import realize_observer_doctrine_r16
from src.core.p1a_realization_transport_v2 import (
    P1AEndpointV2,
    P1AEndpointPartitionLawV2,
    P1AObservationCommutingRowV2,
    P1AObservationPayloadV2,
    P1AObservationTransportV2,
    P1AOutcomeLawV2,
    P1ARealizationTransportReceiptV2,
    P1ARealizationTransportValidationError,
    compose_p1a_realization_transport_v2,
    identity_p1a_realization_transport_v2,
    p1a_realization_transport_v2,
    verify_p1a_realization_transport_v2,
)
from src.core.realization_transport import (
    identity_realization_context_morphism,
    realization_context_morphism,
)

from p1a_realization_transport_v2_fixture import (
    P1ATransportCase,
    all_observer_costs,
    fixed_p1a_case,
    mixed_projection_case,
    non_surjective_fixed_case,
    pulse,
    realization_context,
)


logger = logging.getLogger(__name__)


def _build(
    case: P1ATransportCase,
    *,
    transport_id: str,
    p1a_morphism_id: str,
    fine_observer_id: str,
    coarse_observer_id: str,
    projection: tuple[ProjectionStep, ...],
):
    """Construct one sibling receipt through the frozen public API."""
    logger.debug(
        "test helper build entry transport=%s fine=%s coarse=%s",
        transport_id,
        fine_observer_id,
        coarse_observer_id,
    )
    result = p1a_realization_transport_v2(
        case.doctrine,
        case.binding,
        case.source,
        case.target,
        case.source_witness,
        case.target_witness,
        case.context_transport,
        transport_id=transport_id,
        p1a_morphism_id=p1a_morphism_id,
        fine_observer_id=fine_observer_id,
        coarse_observer_id=coarse_observer_id,
        projection=projection,
    )
    logger.debug("test helper build exit rows=%d", len(result.rows))
    return result


def _verify(
    case: P1ATransportCase,
    receipt,
    *,
    transport_id: str,
    p1a_morphism_id: str,
    fine_observer_id: str,
    coarse_observer_id: str,
    projection: tuple[ProjectionStep, ...],
):
    """Verify one receipt with the same raw spec used for reconstruction."""
    logger.debug("test helper verify entry transport=%s", transport_id)
    result = verify_p1a_realization_transport_v2(
        case.doctrine,
        case.binding,
        case.source,
        case.target,
        case.source_witness,
        case.target_witness,
        case.context_transport,
        receipt,
        transport_id=transport_id,
        p1a_morphism_id=p1a_morphism_id,
        fine_observer_id=fine_observer_id,
        coarse_observer_id=coarse_observer_id,
        projection=projection,
    )
    logger.debug("test helper verify exit rows=%d", len(result.rows))
    return result


def _payloads(row) -> tuple[object, ...]:
    """Return all six payload envelopes in the contract's fixed order."""
    logger.debug("test helper payloads entry source=%d", row.source_index)
    result = (
        row.source_fine,
        row.source_transported,
        row.source_coarse,
        row.target_fine,
        row.target_transported,
        row.target_coarse,
    )
    logger.debug("test helper payloads exit count=%d", len(result))
    return result


def test_ready_left_reconstructs_all_six_payloads_and_refinement_partitions():
    """A lossy strong left projection retains the complete four-vertex square."""
    logger.debug("test_ready_left entry")
    case = fixed_p1a_case(name="ready-left")
    receipt = _build(
        case,
        transport_id="ready-left-transport",
        p1a_morphism_id="ready-left-p1a",
        fine_observer_id="fine-total",
        coarse_observer_id="coarse-crest",
        projection=(ProjectionStep.LEFT,),
    )

    assert (
        _verify(
            case,
            receipt,
            transport_id="ready-left-transport",
            p1a_morphism_id="ready-left-p1a",
            fine_observer_id="fine-total",
            coarse_observer_id="coarse-crest",
            projection=(ProjectionStep.LEFT,),
        )
        == receipt
    )
    assert type(receipt) is P1ARealizationTransportReceiptV2
    assert type(receipt.transport) is P1AObservationTransportV2
    assert type(receipt.source_partition_law) is P1AEndpointPartitionLawV2
    assert type(receipt.target_partition_law) is P1AEndpointPartitionLawV2
    assert all(type(row) is P1AObservationCommutingRowV2 for row in receipt.rows)
    assert all(type(payload) is P1AObservationPayloadV2 for row in receipt.rows for payload in _payloads(row))
    assert len(receipt.rows) == len(case.source.inputs)
    assert tuple(row.target_index for row in receipt.rows) == (2, 0, 1)
    for row in receipt.rows:
        assert row.law is P1AOutcomeLawV2.READY_COMMUTES_EXACT
        assert all(payload.status.value == "ready" for payload in _payloads(row))
        assert row.source_input_commitment == row.target_input_commitment
        assert row.source_fine.canonical_payload == row.target_fine.canonical_payload
        assert row.source_coarse.canonical_payload == row.target_coarse.canonical_payload
        assert row.source_transported.canonical_payload == row.source_coarse.canonical_payload
        assert row.target_transported.canonical_payload == row.target_coarse.canonical_payload
        assert len({payload.payload_digest for payload in _payloads(row)}) >= 2

    source = receipt.source_partition_law
    target = receipt.target_partition_law
    assert source.endpoint is P1AEndpointV2.SOURCE
    assert target.endpoint is P1AEndpointV2.TARGET
    assert source.transported_partition == source.coarse_partition
    assert target.transported_partition == target.coarse_partition
    assert source.fine_partition == (0, 1, 2)
    assert source.coarse_partition == (0, 1, 0)
    assert source.fine_to_coarse_class_map == (0, 1, 0)
    assert target.fine_partition == (0, 1, 2)
    assert target.coarse_partition == (0, 1, 1)
    assert target.fine_to_coarse_class_map == (0, 1, 1)
    logger.debug("test_ready_left exit")


@pytest.mark.parametrize(
    ("fine", "projection"),
    (
        ("fine-right-total", (ProjectionStep.RIGHT,)),
        (
            "fine-right-nested",
            (ProjectionStep.RIGHT, ProjectionStep.RIGHT),
        ),
    ),
)
def test_ready_right_and_nested_strong_projections(fine, projection):
    """A mirrored bounded doctrine exercises right and nested structural paths."""
    logger.debug("test_ready_right_nested entry fine=%s", fine)
    case = mixed_projection_case(name=f"ready-{fine}")
    receipt = _build(
        case,
        transport_id=f"ready-{fine}-transport",
        p1a_morphism_id=f"ready-{fine}-p1a",
        fine_observer_id=fine,
        coarse_observer_id="coarse-crest",
        projection=projection,
    )

    assert all(row.law is P1AOutcomeLawV2.READY_COMMUTES_EXACT for row in receipt.rows)
    assert receipt.transport.translation.projection == projection
    assert receipt.source_partition_law.transported_partition == (receipt.source_partition_law.coarse_partition)
    assert receipt.target_partition_law.transported_partition == (receipt.target_partition_law.coarse_partition)
    logger.debug("test_ready_right_nested exit fine=%s", fine)


def test_fixed_doctrine_right_projection_is_not_upgraded_from_incomparable():
    """Finite ready rows never upgrade a structurally false fixed-doctrine path."""
    logger.debug("test_fixed_right_rejection entry")
    case = fixed_p1a_case(name="fixed-right-rejection")
    with pytest.raises(P1ARealizationTransportValidationError):
        _build(
            case,
            transport_id="fixed-right-transport",
            p1a_morphism_id="fixed-right-p1a",
            fine_observer_id="fine-total",
            coarse_observer_id="coarse-crest",
            projection=(ProjectionStep.RIGHT,),
        )
    logger.debug("test_fixed_right_rejection exit")


def test_blocked_identity_preserves_exact_payload_at_both_endpoints():
    """The empty structural projection copies Blocked bytes without relabeling."""
    logger.debug("test_blocked_identity entry")
    case = fixed_p1a_case(name="blocked-identity")
    receipt = identity_p1a_realization_transport_v2(
        case.doctrine,
        case.binding,
        case.source,
        case.source_witness,
        observer_id="fine-domain-hole",
        transport_id="blocked-identity-transport",
        p1a_morphism_id="blocked-identity-p1a",
        context_morphism_id="blocked-identity-context",
    )

    blocked = next(row for row in receipt.rows if row.law is P1AOutcomeLawV2.BLOCKED_COMMUTES_EXACT)
    assert len({payload.canonical_payload for payload in _payloads(blocked)}) == 1
    assert json.loads(blocked.source_fine.canonical_payload) == {
        "obstructions": [
            {
                "code": "tail-of-silence",
                "path": ["pair-right", "apply-tail"],
            }
        ],
        "tag": "blocked",
    }
    assert receipt.transport.translation.projection == ()
    source_law = receipt.source_partition_law
    target_law = receipt.target_partition_law
    assert source_law.endpoint is P1AEndpointV2.SOURCE
    assert target_law.endpoint is P1AEndpointV2.TARGET
    assert source_law.fine_partition == target_law.fine_partition
    assert source_law.transported_partition == target_law.transported_partition
    assert source_law.coarse_partition == target_law.coarse_partition
    assert source_law.fine_to_coarse_class_map == target_law.fine_to_coarse_class_map
    logger.debug("test_blocked_identity exit")


@pytest.mark.parametrize("projection", ((ProjectionStep.LEFT,), (ProjectionStep.RIGHT,)))
def test_blocked_projection_filters_mixed_paths_without_reorder(projection):
    """Only the selected obstruction prefix survives a strong pair projection."""
    logger.debug("test_blocked_projection entry side=%s", projection[0].value)
    case = mixed_projection_case(name=f"blocked-{projection[0].value}")
    receipt = _build(
        case,
        transport_id=f"blocked-{projection[0].value}-transport",
        p1a_morphism_id=f"blocked-{projection[0].value}-p1a",
        fine_observer_id="fine-both-tail",
        coarse_observer_id="coarse-tail",
        projection=projection,
    )
    row = next(item for item in receipt.rows if item.source_index == 0)

    assert row.law is P1AOutcomeLawV2.BLOCKED_COMMUTES_EXACT
    fine = json.loads(row.source_fine.canonical_payload)
    transported = json.loads(row.source_transported.canonical_payload)
    assert [item["path"] for item in fine["obstructions"]] == [
        ["pair-left", "apply-tail"],
        ["pair-right", "apply-tail"],
    ]
    assert transported == {
        "obstructions": [{"code": "tail-of-silence", "path": ["apply-tail"]}],
        "tag": "blocked",
    }
    assert row.source_transported.canonical_payload == row.source_coarse.canonical_payload
    assert row.target_transported.canonical_payload == row.target_coarse.canonical_payload
    assert receipt.source_partition_law.fine_to_coarse_class_map == (0, 1, 2)
    logger.debug("test_blocked_projection exit side=%s", projection[0].value)


def test_duplicate_non_surjective_map_covers_full_target_vertical_partition():
    """Target-only states remain present in target partition/refinement evidence."""
    logger.debug("test_non_surjective_target_coverage entry")
    case = non_surjective_fixed_case()
    receipt = _build(
        case,
        transport_id="non-surjective-transport",
        p1a_morphism_id="non-surjective-p1a",
        fine_observer_id="fine-total",
        coarse_observer_id="coarse-crest",
        projection=(ProjectionStep.LEFT,),
    )

    assert tuple(row.target_index for row in receipt.rows) == (0, 2, 2)
    assert len(receipt.source_partition_law.fine_partition) == 3
    assert len(receipt.target_partition_law.fine_partition) == 4
    assert receipt.target_partition_law.fine_partition == (0, 1, 2, 3)
    assert receipt.target_partition_law.transported_partition == (0, 1, 1, 1)
    assert receipt.target_partition_law.coarse_partition == (0, 1, 1, 1)
    assert receipt.target_partition_law.fine_to_coarse_class_map == (0, 1, 1, 1)
    duplicate_rows = tuple(row for row in receipt.rows if row.target_index == 2)
    assert len(duplicate_rows) == 2
    assert duplicate_rows[0].target_fine == duplicate_rows[1].target_fine
    logger.debug("test_non_surjective_target_coverage exit")


def test_identity_builder_equals_direct_reconstruction():
    """The identity helper is exact direct construction, not row splicing."""
    logger.debug("test_identity_direct_equality entry")
    case = fixed_p1a_case(name="identity-direct")
    helper = identity_p1a_realization_transport_v2(
        case.doctrine,
        case.binding,
        case.source,
        case.source_witness,
        observer_id="fine-domain-hole",
        transport_id="identity-direct-transport",
        p1a_morphism_id="identity-direct-p1a",
        context_morphism_id="identity-direct-context",
    )
    context_transport = identity_realization_context_morphism(
        case.doctrine,
        case.source,
        case.source_witness,
        "identity-direct-context",
    )
    direct = p1a_realization_transport_v2(
        case.doctrine,
        case.binding,
        case.source,
        case.source,
        case.source_witness,
        case.source_witness,
        context_transport,
        transport_id="identity-direct-transport",
        p1a_morphism_id="identity-direct-p1a",
        fine_observer_id="fine-domain-hole",
        coarse_observer_id="fine-domain-hole",
        projection=(),
    )

    assert helper == direct
    logger.debug("test_identity_direct_equality exit")


def test_composition_equals_fresh_direct_two_step_projection():
    """Composed observer/state paths rebuild exactly the direct endpoint receipt."""
    logger.debug("test_composition_direct_equality entry")
    base = fixed_p1a_case(name="composition-base")
    doctrine, binding = base.doctrine, base.binding
    source = realization_context(doctrine, "composition-source", (2, 0, 1))
    middle = realization_context(doctrine, "composition-middle", (0, 1, 2))
    target = realization_context(doctrine, "composition-target", (2, 0, 1))
    source_witness = realize_observer_doctrine_r16(doctrine, source)
    middle_witness = realize_observer_doctrine_r16(doctrine, middle)
    target_witness = realize_observer_doctrine_r16(doctrine, target)
    first_v1 = realization_context_morphism(
        doctrine,
        source,
        middle,
        "composition-first-context",
        (2, 0, 1),
        source_witness,
        middle_witness,
    )
    second_v1 = realization_context_morphism(
        doctrine,
        middle,
        target,
        "composition-second-context",
        (1, 2, 0),
        middle_witness,
        target_witness,
    )
    first = p1a_realization_transport_v2(
        doctrine,
        binding,
        source,
        middle,
        source_witness,
        middle_witness,
        first_v1,
        transport_id="composition-first-transport",
        p1a_morphism_id="composition-first-p1a",
        fine_observer_id="fine-nested",
        coarse_observer_id="fine-total",
        projection=(ProjectionStep.LEFT,),
    )
    second = p1a_realization_transport_v2(
        doctrine,
        binding,
        middle,
        target,
        middle_witness,
        target_witness,
        second_v1,
        transport_id="composition-second-transport",
        p1a_morphism_id="composition-second-p1a",
        fine_observer_id="fine-total",
        coarse_observer_id="coarse-crest",
        projection=(ProjectionStep.LEFT,),
    )
    composed = compose_p1a_realization_transport_v2(
        doctrine,
        binding,
        source,
        middle,
        target,
        source_witness,
        middle_witness,
        target_witness,
        first,
        second,
        transport_id="composition-direct-transport",
        p1a_morphism_id="composition-direct-p1a",
        context_morphism_id="composition-direct-context",
    )
    direct_v1 = realization_context_morphism(
        doctrine,
        source,
        target,
        "composition-direct-context",
        (0, 1, 2),
        source_witness,
        target_witness,
    )
    direct = p1a_realization_transport_v2(
        doctrine,
        binding,
        source,
        target,
        source_witness,
        target_witness,
        direct_v1,
        transport_id="composition-direct-transport",
        p1a_morphism_id="composition-direct-p1a",
        fine_observer_id="fine-nested",
        coarse_observer_id="coarse-crest",
        projection=(ProjectionStep.LEFT, ProjectionStep.LEFT),
    )

    assert composed == direct
    assert composed.transport.translation.projection == (
        ProjectionStep.LEFT,
        ProjectionStep.LEFT,
    )
    logger.debug("test_composition_direct_equality exit")


def test_fixed_context_fixture_covers_all_five_observer_costs():
    """Every context used by the contract binds all five doctrine costs in order."""
    logger.debug("test_all_five_costs entry")
    case = fixed_p1a_case(name="all-five-costs")
    expected = tuple(member.observer_id for member in case.doctrine.observers)

    assert len(expected) == 5
    assert tuple(item.observer_id for item in case.source.observer_costs) == expected
    assert tuple(item.observer_id for item in case.target.observer_costs) == expected
    assert all_observer_costs(case.doctrine) == tuple(
        (observer_id, index + 1) for index, observer_id in enumerate(expected)
    )
    assert pulse(0) == case.target.inputs[0].recurrence
    logger.debug("test_all_five_costs exit")
