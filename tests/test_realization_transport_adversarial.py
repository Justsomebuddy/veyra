"""Fail-closed and anti-splicing tests for realization-context transport."""

from __future__ import annotations

from dataclasses import replace

import pytest

from src.core.observer_realization import (
    observer_realization_context,
    realize_observer_doctrine_r16,
)
from src.core.positive_ontology_doctrine import p0_observer_doctrine
from src.core.proof_core_types import Pulse, Silence
from src.core.realization_transport import (
    ContextMorphism,
    RealizationTransportValidationError,
    identity_realization_context_morphism,
    realization_context_morphism,
    verify_realization_transport,
)
from src.core.realization_transport.digest import (
    context_morphism_digest,
    transport_receipt_digest,
)


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


def _valid():
    doctrine = p0_observer_doctrine()
    source = _context(doctrine, "adversarial-source", (2, 0, 1))
    target = _context(doctrine, "adversarial-target", (0, 1, 2))
    source_witness = realize_observer_doctrine_r16(doctrine, source)
    target_witness = realize_observer_doctrine_r16(doctrine, target)
    receipt = realization_context_morphism(
        doctrine,
        source,
        target,
        "adversarial-valid",
        (2, 0, 1),
        source_witness,
        target_witness,
    )
    return doctrine, source, target, source_witness, target_witness, receipt


def _resign(receipt, **changes):
    provisional = replace(receipt, **changes, receipt_digest="0" * 64)
    digest = transport_receipt_digest(
        provisional.schema,
        provisional.doctrine_fingerprint,
        provisional.source_context_digest,
        provisional.target_context_digest,
        provisional.source_witness_digest,
        provisional.target_witness_digest,
        provisional.morphism,
        provisional.recurrence_rows,
        provisional.evaluation_rows,
        provisional.closure_action,
        provisional.cost_rows,
        provisional.bottom_preserved,
        provisional.joins_preserved,
        provisional.scope,
    )
    return replace(provisional, receipt_digest=digest)


@pytest.mark.parametrize("graph", [(), (0, 1), (0, 1, 3), (True, 0, 1)])
def test_partial_out_of_range_and_nonexact_graphs_fail_closed(graph):
    doctrine, source, target, source_witness, target_witness, _ = _valid()

    with pytest.raises(RealizationTransportValidationError):
        realization_context_morphism(
            doctrine,
            source,
            target,
            "invalid-graph",
            graph,
            source_witness,
            target_witness,
        )


def test_wrong_recurrence_edge_is_rejected_even_with_valid_endpoint_witnesses():
    doctrine, source, target, source_witness, target_witness, _ = _valid()

    with pytest.raises(RealizationTransportValidationError):
        realization_context_morphism(
            doctrine,
            source,
            target,
            "noncommuting-recurrence",
            (0, 1, 2),
            source_witness,
            target_witness,
        )


def test_ordered_cost_policy_drift_is_rejected_before_transport():
    doctrine, source, _, source_witness, _, _ = _valid()
    target = observer_realization_context(
        doctrine,
        "different-cost-target",
        tuple((f"different-cost-{index}", _pulse(depth)) for index, depth in enumerate((0, 1, 2))),
        (("crest", 7), ("tail", 11)),
    )
    target_witness = realize_observer_doctrine_r16(doctrine, target)

    with pytest.raises(
        RealizationTransportValidationError,
        match="transport-endpoint-policy-or-cost-drift",
    ):
        realization_context_morphism(
            doctrine,
            source,
            target,
            "cost-drift",
            (2, 0, 1),
            source_witness,
            target_witness,
        )


def test_stale_endpoint_witness_is_rejected_by_authoritative_replay():
    doctrine, source, target, source_witness, _, _ = _valid()
    stale_target = _context(doctrine, "stale-target", (0, 1, 2))
    stale_witness = realize_observer_doctrine_r16(doctrine, stale_target)

    with pytest.raises(
        RealizationTransportValidationError,
        match="transport-endpoint-authoritative-replay-failed",
    ):
        realization_context_morphism(
            doctrine,
            source,
            target,
            "stale-witness",
            (2, 0, 1),
            source_witness,
            stale_witness,
        )


def test_morphism_identifier_is_utf8_byte_bounded():
    doctrine, source, target, source_witness, target_witness, _ = _valid()

    with pytest.raises(
        RealizationTransportValidationError,
        match="invalid-context-morphism-input",
    ):
        realization_context_morphism(
            doctrine,
            source,
            target,
            "x" * 10_000,
            (2, 0, 1),
            source_witness,
            target_witness,
        )


def test_morphism_identifier_with_invalid_unicode_fails_closed():
    doctrine, source, target, source_witness, target_witness, _ = _valid()

    with pytest.raises(RealizationTransportValidationError):
        realization_context_morphism(
            doctrine,
            source,
            target,
            "invalid-\ud800",
            (2, 0, 1),
            source_witness,
            target_witness,
        )


class _CallbackBomb:
    def __eq__(self, other):
        raise RuntimeError("callback-executed")

    def __ne__(self, other):
        raise RuntimeError("callback-executed")

    def __len__(self):
        raise RuntimeError("callback-executed")


@pytest.mark.parametrize("field", ("version", "schema", "scope"))
def test_untyped_protocol_fields_reject_without_executing_callbacks(field):
    doctrine, source, target, source_witness, target_witness, receipt = _valid()
    if field == "version":
        supplied_morphism = replace(receipt.morphism, version=_CallbackBomb())
        supplied_receipt = receipt
    else:
        supplied_morphism = receipt.morphism
        supplied_receipt = replace(receipt, **{field: _CallbackBomb()})

    with pytest.raises(RealizationTransportValidationError):
        verify_realization_transport(
            doctrine,
            source,
            target,
            supplied_morphism,
            source_witness,
            target_witness,
            supplied_receipt,
        )


def test_identity_rejects_hostile_inputs_without_calling_len():
    doctrine, source, _, source_witness, _, _ = _valid()
    hostile = replace(source, inputs=_CallbackBomb())

    with pytest.raises(RealizationTransportValidationError):
        identity_realization_context_morphism(doctrine, hostile, source_witness)


def test_digest_correct_forged_evaluation_row_is_rejected_by_reconstruction():
    doctrine, source, target, source_witness, target_witness, receipt = _valid()
    first = receipt.evaluation_rows[0]
    forged_row = replace(first, payload_digest="0" * 64)
    forged = _resign(
        receipt, evaluation_rows=(forged_row,) + receipt.evaluation_rows[1:]
    )

    with pytest.raises(RealizationTransportValidationError):
        verify_realization_transport(
            doctrine,
            source,
            target,
            receipt.morphism,
            source_witness,
            target_witness,
            forged,
        )


def test_digest_correct_forged_closure_action_is_rejected_by_reconstruction():
    doctrine, source, target, source_witness, target_witness, receipt = _valid()
    first = receipt.closure_action[0]
    replacement = receipt.closure_action[-1]
    forged_row = replace(
        first,
        source_partition=replacement.source_partition,
        source_partition_digest=replacement.source_partition_digest,
        source_closure_index=replacement.source_closure_index,
    )
    forged = _resign(receipt, closure_action=(forged_row,) + receipt.closure_action[1:])

    with pytest.raises(RealizationTransportValidationError):
        verify_realization_transport(
            doctrine,
            source,
            target,
            receipt.morphism,
            source_witness,
            target_witness,
            forged,
        )


def test_endpoint_receipt_splicing_is_rejected():
    doctrine, source, target, source_witness, target_witness, receipt = _valid()
    other_target = _context(doctrine, "other-target", (0, 1, 2))
    other_target_witness = realize_observer_doctrine_r16(doctrine, other_target)

    with pytest.raises(RealizationTransportValidationError):
        verify_realization_transport(
            doctrine,
            source,
            other_target,
            receipt.morphism,
            source_witness,
            other_target_witness,
            receipt,
        )


def test_self_consistent_morphism_digest_does_not_override_exact_recurrence():
    doctrine, source, target, source_witness, target_witness, receipt = _valid()
    graph = (0, 1, 2)
    forged_morphism = replace(
        receipt.morphism,
        state_index_map=graph,
        morphism_digest=context_morphism_digest(
            receipt.morphism.morphism_id,
            receipt.morphism.source_context_digest,
            receipt.morphism.target_context_digest,
            graph,
            receipt.morphism.version,
        ),
    )

    with pytest.raises(RealizationTransportValidationError):
        verify_realization_transport(
            doctrine,
            source,
            target,
            forged_morphism,
            source_witness,
            target_witness,
            receipt,
        )


def test_exact_dto_types_are_required():
    doctrine, source, target, source_witness, target_witness, receipt = _valid()

    class MorphismSubclass(ContextMorphism):
        pass

    subclassed = MorphismSubclass(
        receipt.morphism.morphism_id,
        receipt.morphism.source_context_digest,
        receipt.morphism.target_context_digest,
        receipt.morphism.state_index_map,
        receipt.morphism.version,
        receipt.morphism.morphism_digest,
    )
    with pytest.raises(RealizationTransportValidationError):
        verify_realization_transport(
            doctrine,
            source,
            target,
            subclassed,
            source_witness,
            target_witness,
            receipt,
        )
