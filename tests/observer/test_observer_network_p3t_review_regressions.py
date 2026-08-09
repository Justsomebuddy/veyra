"""Exact regressions for the second strict P3-T review."""

from dataclasses import replace

import pytest

from observer_network_fixture import network_source
from src.core.observer_network import (
    ObserverNetworkError,
    input_snapshot,
    observation_row,
    observer_network_judgment,
    observer_network_source,
    observer_source,
    snapshot_network_source,
    validate_observer_network_result,
)
from src.core.observer_network_preflight import network_resource_policy
from src.core.observer_network_work import network_evaluation_charge, network_work_charge


def _rebuild(source, *, inputs=None, observers=None):
    """Rebuild one exact source with explicit unchanged raw P1 roots."""
    return observer_network_source(
        source.doctrine_id,
        source.source_id,
        source.source_version,
        source.inputs if inputs is None else inputs,
        source.observers if observers is None else observers,
        source.translations,
        source.triangles,
        source.p1a_doctrine,
        source.p1a_binding,
        source.p1a_stage_source,
        source.raw_pairs,
    )


def test_input_payload_is_canonically_bound_into_source_and_judgment_identity():
    source = network_source()
    old = source.inputs[0]
    with pytest.raises(ObserverNetworkError, match="input-canonical-commitment-mismatch"):
        snapshot_network_source(replace(source, inputs=(replace(old, payload=b"mutated"),) + source.inputs[1:]))
    changed_input = input_snapshot(old.input_id, old.type_id, b"mutated", old.stage_commitment)
    changed_inputs = (changed_input,) + source.inputs[1:]
    changed_observers = []
    for observer in source.observers:
        rows = (
            observation_row(changed_input, observer.rows[0].response),
        ) + observer.rows[1:]
        changed_observers.append(observer_source(observer.observer_id, observer.input_type_id, observer.grammar_descriptor, rows))
    changed = _rebuild(source, inputs=changed_inputs, observers=tuple(changed_observers))
    first, second = observer_network_judgment(source), observer_network_judgment(changed)
    assert old.commitment != changed_input.commitment
    assert source.network_digest != changed.network_digest
    assert first.source_digest != second.source_digest
    assert first.judgment_digest != second.judgment_digest


def test_instance_dataclass_metadata_is_refused_without_invoking_it():
    source = network_source()
    result = observer_network_judgment(source)

    class BombFields(dict):
        calls = 0

        def __iter__(self):
            type(self).calls += 1
            raise AssertionError("hostile metadata")

    object.__setattr__(result, "__dataclass_fields__", BombFields())
    with pytest.raises(ObserverNetworkError, match="result-instance-metadata-invalid"):
        validate_observer_network_result(source, result)
    assert BombFields.calls == 0


def test_public_constructors_refuse_hostile_scalars_before_encode_or_hash():
    source = network_source()

    class BombStr(str):
        calls = 0

        def encode(self, *args, **kwargs):
            type(self).calls += 1
            raise AssertionError("hostile encode")

    bad_input = replace(source.inputs[0], commitment=BombStr(source.inputs[0].commitment))
    with pytest.raises(ObserverNetworkError, match="observation-input-commitment-invalid"):
        observation_row(bad_input, source.observers[0].rows[0].response)
    bad_observer = replace(source.observers[0], observer_digest=BombStr(source.observers[0].observer_digest))
    with pytest.raises(ObserverNetworkError, match="canonical-byte-value-invalid"):
        _rebuild(source, observers=(bad_observer,) + source.observers[1:])
    assert BombStr.calls == 0


def test_authoritative_work_cap_covers_all_608_actual_a2_rows_and_refuses_minus_one():
    source = network_source()
    required = network_evaluation_charge(source)
    total, charged_a2_rows = network_work_charge(source)
    assert total == required and charged_a2_rows == 608
    tiny = replace(network_resource_policy(), max_evaluations=required - 1)
    with pytest.raises(ObserverNetworkError, match="network-hard-work-limit"):
        snapshot_network_source(source, tiny)
    assert snapshot_network_source(source, replace(tiny, max_evaluations=required)) == source


def test_result_primitive_byte_cap_precedes_semantic_equality():
    source = network_source()
    result = observer_network_judgment(source)
    forged = replace(result, nonclaims=("x" * 4096,))
    tiny = replace(network_resource_policy(), max_result_bytes=1024)
    with pytest.raises(ObserverNetworkError, match="result-byte-hard-limit"):
        validate_observer_network_result(source, forged, tiny)


def test_reverse_and_truth_nonclaims_are_explicit():
    result = observer_network_judgment(network_source())
    assert "guaranteed-reverse-translation" in result.nonclaims
    assert "observer-free-truth" in result.nonclaims
