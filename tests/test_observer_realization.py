"""Contract and adversarial tests for the relative P1-to-R16 bridge."""

from __future__ import annotations

from dataclasses import replace
from hashlib import sha256
import json

import pytest

from src import core
import src.core.observer_realization as realization_module
import src.core.observer_realization_validation as realization_validation
from src.core.observer_core_codec import canonical_observer_bytes
from src.core.observer_core_kernel import tail_observer
from src.core.observer_core_semantics import echo, infer_observer_kind
from src.core.observer_core_types import Apply, DomainBlocked, Input, Pair, PrimitiveId
from src.core.observer_descent_types import FiniteObserver, FiniteObserverDoctrine
from src.core.observer_descent import validate_doctrine
from src.core.observer_realization import (
    observer_realization_context,
    observer_realization_scope_boundary,
    realize_observer_doctrine_r16,
    verify_observer_realization_r16,
)
from src.core.observer_realization_digest import realization_witness_digest
from src.core.observer_realization_digest import finite_doctrine_digest
from src.core.observer_realization_types import (
    ObservationStatus,
    ObserverRealizationWitness,
    RealizationContext,
)
from src.core.observer_realization_validation import (
    ObserverRealizationValidationError,
    snapshot_witness,
)
from src.core.positive_ontology_doctrine import (
    observer_doctrine,
    p0_observer_doctrine,
)
from src.core.positive_ontology_types import InternalObserver
from src.core.proof_core_types import Pulse, Silence


def _pulse(depth: int):
    result = Silence()
    for _ in range(depth):
        result = Pulse(result)
    return result


def _p0_context(
    states: tuple[tuple[object, int], ...] = (("z", 0), ("one", 1), ("two", 2)),
    costs: tuple[tuple[str, int], ...] = (("crest", 2), ("tail", 3)),
):
    doctrine = p0_observer_doctrine()
    context = observer_realization_context(
        doctrine,
        "p0-finite-scope",
        tuple((state, _pulse(depth)) for state, depth in states),
        costs,
    )
    return doctrine, context


def _resign(witness: ObserverRealizationWitness, **changes: object):
    provisional = replace(witness, **changes, witness_digest="0" * 64)
    digest = realization_witness_digest(
        provisional.source_doctrine_fingerprint,
        provisional.context_digest,
        provisional.evaluations,
        provisional.source_mapping,
        provisional.closure,
        provisional.doctrine_digest,
        provisional.schema,
    )
    return replace(provisional, witness_digest=digest)


def test_relative_realization_replays_ready_and_structured_blocked_rows():
    doctrine, context = _p0_context()
    witness = realize_observer_doctrine_r16(doctrine, context)

    assert verify_observer_realization_r16(doctrine, context, witness) == witness
    validate_doctrine(witness.doctrine)
    assert len(witness.evaluations) == 2 * 3
    assert len(witness.closure) == 3
    assert witness.closure[0].observer_name == "bottom"
    assert witness.closure[0].generator_ids == ()
    assert witness.closure[0].cost == 0
    tail_zero = next(
        row
        for row in witness.evaluations
        if row.observer_id == "tail" and row.state == "z"
    )
    assert tail_zero.status is ObservationStatus.BLOCKED
    payload = json.loads(tail_zero.observation_payload)
    assert payload == {
        "obstructions": [
            {"code": "tail-of-silence", "path": ["apply-tail"]}
        ],
        "tag": "blocked",
    }
    target_name = dict(witness.source_mapping)["tail"]
    target = next(item for item in witness.doctrine.observers if item.name == target_name)
    response = dict(target.responses)["z"]
    assert response[0] == "p1-r16-totalized-v1"
    assert ("blocked", tail_zero.response_class) in response[1]
    assert observer_realization_scope_boundary()[0] == "not-canonical-from-p1-alone"


def test_same_p1_doctrine_has_different_context_relative_images():
    doctrine, first = _p0_context((("x0", 1), ("x1", 2)))
    _, second = _p0_context((("x0", 1), ("x1", 1), ("x2", 2)))
    left = realize_observer_doctrine_r16(doctrine, first)
    right = realize_observer_doctrine_r16(doctrine, second)

    assert first.context_digest != second.context_digest
    assert left.doctrine.carrier == ("x0", "x1")
    assert right.doctrine.carrier == ("x0", "x1", "x2")
    assert left.doctrine_digest != right.doctrine_digest
    assert left.witness_digest != right.witness_digest


def test_cost_policy_is_explicit_and_changes_only_relative_cost_evidence():
    doctrine, first = _p0_context()
    _, second = _p0_context(costs=(("crest", 7), ("tail", 11)))
    left = realize_observer_doctrine_r16(doctrine, first)
    right = realize_observer_doctrine_r16(doctrine, second)

    left_partitions = tuple(item.partition for item in left.closure)
    right_partitions = tuple(item.partition for item in right.closure)
    assert left_partitions == right_partitions
    assert tuple(item.cost for item in left.closure) == (0, 2, 3)
    assert tuple(item.cost for item in right.closure) == (0, 7, 11)
    assert left.doctrine_digest != right.doctrine_digest


def test_extensional_source_duplicates_map_to_one_finite_partition():
    programs = (Input(), Pair(Input(), Input()))
    members = tuple(
        InternalObserver(
            observer_id,
            canonical_observer_bytes(program),
            infer_observer_kind(program),
        )
        for observer_id, program in zip(("input", "paired-input"), programs, strict=True)
    )
    doctrine = observer_doctrine(
        "duplicate-image",
        "closed-r11-programs",
        ("relative-realization-test",),
        members,
    )
    context = observer_realization_context(
        doctrine,
        "duplicate-partition-scope",
        (("z", _pulse(0)), ("one", _pulse(1))),
        (("input", 5), ("paired-input", 2)),
    )
    witness = realize_observer_doctrine_r16(doctrine, context)

    assert len(witness.closure) == 2
    mapping = dict(witness.source_mapping)
    assert mapping["input"] == mapping["paired-input"]
    nonbottom = next(item for item in witness.closure if item.observer_name != "bottom")
    assert nonbottom.generator_ids == ("paired-input",)
    assert nonbottom.cost == 2
    assert len(witness.evaluations) == 4


def test_totalized_equal_blockage_is_not_relabelled_as_r11_echo():
    doctrine, context = _p0_context((("left", 0), ("right", 0)))
    witness = realize_observer_doctrine_r16(doctrine, context)
    tail_rows = tuple(row for row in witness.evaluations if row.observer_id == "tail")

    assert tail_rows[0].observation_payload == tail_rows[1].observation_payload
    assert tail_rows[0].response_class == tail_rows[1].response_class
    assert type(echo(tail_observer(), Silence(), Silence())) is DomainBlocked
    assert "structured-blockage-is-totalized-not-r11-echo" in (
        observer_realization_scope_boundary()
    )


def test_nested_blocked_payload_is_retained_beyond_r16_scalar_size():
    tail = Apply(PrimitiveId.TAIL, Input())
    program = Pair(tail, Pair(tail, tail))
    member = InternalObserver(
        "triple-tail",
        canonical_observer_bytes(program),
        infer_observer_kind(program),
    )
    doctrine = observer_doctrine(
        "structured-blockage",
        "closed-r11-programs",
        ("payload-retention-test",),
        (member,),
    )
    context = observer_realization_context(
        doctrine,
        "large-blocked-payload",
        (("z", Silence()),),
        (("triple-tail", 1),),
    )
    witness = realize_observer_doctrine_r16(doctrine, context)
    row = witness.evaluations[0]

    assert row.status is ObservationStatus.BLOCKED
    assert len(row.observation_payload) > 128
    assert len(json.loads(row.observation_payload)["obstructions"]) == 3
    assert verify_observer_realization_r16(doctrine, context, witness) == witness


def test_ready_only_finite_example_is_recorded_as_evidence_not_universal_theorem():
    doctrine, context = _p0_context((("one", 1), ("two", 2), ("three", 3)))
    witness = realize_observer_doctrine_r16(doctrine, context)

    assert len(witness.closure) == 2
    assert tuple(len(set(item.partition)) for item in witness.closure) == (1, 3)
    assert "no-ready-only-image-chain-or-obstruction-basis-theorem" in (
        observer_realization_scope_boundary()
    )


def test_digest_correct_supplied_evaluation_still_requires_authoritative_replay():
    doctrine, context = _p0_context()
    witness = realize_observer_doctrine_r16(doctrine, context)
    first, replacement = witness.evaluations[0], witness.evaluations[1]
    forged_row = replace(
        first,
        status=replacement.status,
        response_class=replacement.response_class,
        observation_payload=replacement.observation_payload,
        payload_digest=sha256(replacement.observation_payload).hexdigest(),
    )
    forged = _resign(
        witness, evaluations=(forged_row,) + witness.evaluations[1:]
    )

    assert snapshot_witness(forged) == forged
    with pytest.raises(
        ObserverRealizationValidationError,
        match="realization-authoritative-replay-mismatch",
    ):
        verify_observer_realization_r16(doctrine, context, forged)


def test_self_consistent_finite_doctrine_forgery_is_rejected_by_reconstruction():
    doctrine, context = _p0_context()
    witness = realize_observer_doctrine_r16(doctrine, context)
    first = witness.doctrine.observers[0]
    forged_first = FiniteObserver(first.name, first.responses, first.cost + 1)
    forged_doctrine = FiniteObserverDoctrine(
        witness.doctrine.name,
        witness.doctrine.carrier,
        (forged_first,) + witness.doctrine.observers[1:],
    )
    doctrine_digest = finite_doctrine_digest(forged_doctrine)
    forged = _resign(
        witness, doctrine=forged_doctrine, doctrine_digest=doctrine_digest
    )

    assert snapshot_witness(forged) == forged
    with pytest.raises(
        ObserverRealizationValidationError,
        match="realization-authoritative-replay-mismatch",
    ):
        verify_observer_realization_r16(doctrine, context, forged)


@pytest.mark.parametrize(
    "states,costs,reason",
    [
        ((("same", 0), ("same", 1)), (("crest", 1), ("tail", 1)), "duplicate-realization-state"),
        (((True, 0),), (("crest", 1), ("tail", 1)), "realization-state-not-canonical"),
        (((1 << 5000, 0),), (("crest", 1), ("tail", 1)), "realization-state-integer-limit"),
        ((("x", 0),), (("tail", 1), ("crest", 1)), "realization-cost-order-or-coverage-drift"),
        ((("x", 0),), (("crest", -1), ("tail", 1)), "invalid-observer-cost"),
    ],
)
def test_context_rejects_ambiguous_or_unbounded_external_choices(states, costs, reason):
    doctrine = p0_observer_doctrine()
    with pytest.raises(ObserverRealizationValidationError, match=reason):
        observer_realization_context(
            doctrine,
            "bad-context",
            tuple((state, _pulse(depth)) for state, depth in states),
            costs,
        )


def test_context_and_witness_require_exact_dtos_and_complete_bindings():
    doctrine, context = _p0_context()
    witness = realize_observer_doctrine_r16(doctrine, context)

    class ContextSubclass(RealizationContext):
        pass

    subclassed = ContextSubclass(
        context.realization_id,
        context.inputs,
        context.observer_costs,
        context.response_policy,
        context.cost_policy,
        context.closure_policy,
        context.version,
        context.context_digest,
    )
    with pytest.raises(
        ObserverRealizationValidationError, match="realization-context-must-be-exact"
    ):
        realize_observer_doctrine_r16(doctrine, subclassed)

    with pytest.raises(
        ObserverRealizationValidationError, match="realization-witness-digest-drift"
    ):
        verify_observer_realization_r16(
            doctrine, context, replace(witness, witness_digest="0" * 64)
        )


def test_join_cost_overflow_and_non_utf8_state_fail_closed():
    doctrine, _ = _p0_context()
    with pytest.raises(
        ObserverRealizationValidationError,
        match="realization-total-source-cost-limit",
    ):
        observer_realization_context(
            doctrine,
            "overflowing-total-source-cost",
            (("z", _pulse(0)), ("two", _pulse(2))),
            (("crest", (1 << 63) - 1), ("tail", (1 << 63) - 1)),
        )

    with pytest.raises(
        ObserverRealizationValidationError, match="realization-state-not-canonical"
    ):
        observer_realization_context(
            doctrine,
            "non-utf8-state",
            ((("\ud800",), _pulse(0)),),
            (("crest", 1), ("tail", 1)),
        )


def test_raw_cost_precharge_and_forged_finite_cost_fail_closed():
    doctrine, context = _p0_context()
    with pytest.raises(
        ObserverRealizationValidationError, match="realization-cost-count-limit"
    ):
        observer_realization_context(
            doctrine,
            "excess-cost-rows",
            (("z", _pulse(0)),),
            tuple((f"observer-{index}", 1) for index in range(9)),
        )

    witness = realize_observer_doctrine_r16(doctrine, context)
    first = witness.doctrine.observers[0]
    forged_first = FiniteObserver(first.name, first.responses, 1 << 80)
    forged_doctrine = FiniteObserverDoctrine(
        witness.doctrine.name,
        witness.doctrine.carrier,
        (forged_first,) + witness.doctrine.observers[1:],
    )
    with pytest.raises(ObserverRealizationValidationError):
        verify_observer_realization_r16(
            doctrine, context, replace(witness, doctrine=forged_doctrine)
        )


def test_shared_state_dag_and_generated_total_payload_fail_before_return(monkeypatch):
    doctrine, context = _p0_context()
    shared: object = 0
    for _ in range(8):
        shared = (shared,) * 64
    with pytest.raises(
        ObserverRealizationValidationError, match="realization-state-node-limit"
    ):
        observer_realization_context(
            doctrine,
            "shared-dag",
            ((shared, _pulse(0)),),
            (("crest", 1), ("tail", 1)),
        )

    baseline = realize_observer_doctrine_r16(doctrine, context)
    row_limit = max(len(row.observation_payload) for row in baseline.evaluations) + 1
    monkeypatch.setattr(
        realization_module, "MAX_REALIZATION_TOTAL_PAYLOAD_BYTES", row_limit
    )
    with pytest.raises(
        ObserverRealizationValidationError, match="realization-total-payload-limit"
    ):
        realize_observer_doctrine_r16(doctrine, context)


def test_supplied_payload_depth_fails_through_closed_validation_boundary():
    doctrine, context = _p0_context()
    witness = realize_observer_doctrine_r16(doctrine, context)
    first = witness.evaluations[0]
    nested_payload = (
        b'{"tag":"ready","value":'
        + (b"[" * 2000)
        + b"0"
        + (b"]" * 2000)
        + b"}"
    )
    forged_row = replace(
        first,
        status=ObservationStatus.READY,
        observation_payload=nested_payload,
        payload_digest=sha256(nested_payload).hexdigest(),
    )
    forged = replace(
        witness, evaluations=(forged_row,) + witness.evaluations[1:]
    )
    with pytest.raises(
        ObserverRealizationValidationError,
        match="invalid-realization-observation-payload",
    ):
        snapshot_witness(forged)


def test_supplied_payload_accepts_bounded_canonical_nesting():
    nested: object = 0
    for _ in range(32):
        nested = [nested]
    payload = json.dumps(
        {"tag": "ready", "value": nested},
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("ascii")

    assert (
        realization_validation._snapshot_payload(
            payload, ObservationStatus.READY
        )
        == payload
    )


def test_supplied_evaluation_states_receive_aggregate_precharge(monkeypatch):
    doctrine, context = _p0_context()
    witness = realize_observer_doctrine_r16(doctrine, context)
    assert snapshot_witness(witness) == witness

    exact_nodes = len(witness.evaluations)
    exact_bytes = sum(
        len(row.state.encode("utf-8")) for row in witness.evaluations
    )
    with monkeypatch.context() as bounded:
        bounded.setattr(
            realization_validation,
            "MAX_REALIZATION_EVALUATION_STATE_NODES",
            exact_nodes,
        )
        bounded.setattr(
            realization_validation,
            "MAX_REALIZATION_EVALUATION_STATE_BYTES",
            exact_bytes,
        )
        assert snapshot_witness(witness) == witness
        bounded.setattr(
            realization_validation,
            "MAX_REALIZATION_EVALUATION_STATE_NODES",
            exact_nodes - 1,
        )
        with pytest.raises(
            ObserverRealizationValidationError,
            match="realization-evaluation-state-node-limit",
        ):
            snapshot_witness(witness)

    with monkeypatch.context() as bounded:
        bounded.setattr(
            realization_validation,
            "MAX_REALIZATION_EVALUATION_STATE_NODES",
            exact_nodes,
        )
        bounded.setattr(
            realization_validation,
            "MAX_REALIZATION_EVALUATION_STATE_BYTES",
            exact_bytes - 1,
        )
        with pytest.raises(
            ObserverRealizationValidationError,
            match="realization-evaluation-state-byte-limit",
        ):
            snapshot_witness(witness)


def test_supplied_shared_evaluation_dag_is_rejected_before_capture(monkeypatch):
    doctrine, context = _p0_context()
    witness = realize_observer_doctrine_r16(doctrine, context)
    shared: object = 0
    for _ in range(3):
        shared = (shared,) * 4
    forged_rows = tuple(
        replace(row, state=shared) for row in witness.evaluations
    )
    forged = replace(witness, evaluations=forged_rows)
    monkeypatch.setattr(
        realization_validation,
        "MAX_REALIZATION_EVALUATION_STATE_NODES",
        100,
    )

    def unexpected_capture(value: object, depth: int) -> object:
        raise AssertionError("aggregate precharge must fail before deep capture")

    monkeypatch.setattr(
        realization_validation, "_capture_finite_state", unexpected_capture
    )
    with pytest.raises(
        ObserverRealizationValidationError,
        match="realization-evaluation-state-node-limit",
    ):
        snapshot_witness(forged)


def test_public_root_exports_are_collision_safe():
    expected = {
        "ObservationStatus": ObservationStatus,
        "ObserverRealizationWitness": ObserverRealizationWitness,
        "RealizationContext": RealizationContext,
        "observer_realization_context": observer_realization_context,
        "observer_realization_scope_boundary": observer_realization_scope_boundary,
        "realize_observer_doctrine_r16": realize_observer_doctrine_r16,
        "verify_observer_realization_r16": verify_observer_realization_r16,
    }
    assert len(core.__all__) == len(set(core.__all__))
    assert all(name in core.__all__ for name in expected)
    assert all(getattr(core, name) is value for name, value in expected.items())
