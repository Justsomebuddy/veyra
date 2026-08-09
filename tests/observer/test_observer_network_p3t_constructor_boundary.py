"""Exact hostile-child regressions for every exported P3-T constructor layer."""

from dataclasses import replace

import pytest

from observer_network_fixture import network_source
from src.core.observer_network import (
    ObserverNetworkError,
    observation_row,
    observer_network_source,
    observer_source,
    raw_observer_pair_source,
    ready,
    translation_row,
    translation_source,
)


class BombDict(dict):
    """A mapping subclass whose virtual operations must never run."""

    calls = 0

    def keys(self):
        type(self).calls += 1
        raise AssertionError("hostile keys")

    def __iter__(self):
        type(self).calls += 1
        raise AssertionError("hostile iteration")

    def __contains__(self, key):
        type(self).calls += 1
        raise AssertionError("hostile contains")


def test_absent_projection_refuses_hostile_morphism_scalar_before_digesting():
    class BombScalar:
        calls = 0

        def __str__(self):
            type(self).calls += 1
            raise AssertionError("hostile string conversion")

        def encode(self, *args, **kwargs):
            type(self).calls += 1
            raise AssertionError("hostile encode")

    with pytest.raises(ObserverNetworkError, match="raw-pair-morphism-invalid"):
        raw_observer_pair_source("pair", "left", "right", BombScalar(), None)
    assert BombScalar.calls == 0

def _constructor_case(source, case):
    """Return one direct child, deleted field, and constructor callback."""
    observer = source.observers[0]
    edge = source.translations[0]
    response = observer.rows[0].response
    value = response.value
    cases = {
        "ready": (value, "value_digest", lambda bad: ready(bad)),
        "observation-input": (
            source.inputs[0],
            "commitment",
            lambda bad: observation_row(bad, response),
        ),
        "observation-response": (
            response,
            "response_digest",
            lambda bad: observation_row(source.inputs[0], bad),
        ),
        "observer-descriptor": (
            observer.grammar_descriptor,
            "grammar_id",
            lambda bad: observer_source(observer.observer_id, observer.input_type_id, bad, observer.rows),
        ),
        "observer-row": (
            observer.rows[0],
            "row_digest",
            lambda bad: observer_source(
                observer.observer_id,
                observer.input_type_id,
                observer.grammar_descriptor,
                (bad,) + observer.rows[1:],
            ),
        ),
        "translation-value": (
            edge.rows[0].source_value,
            "value_digest",
            lambda bad: translation_row(bad, edge.rows[0].target_value),
        ),
        "translation-row": (
            edge.rows[0],
            "row_digest",
            lambda bad: translation_source(
                edge.edge_id,
                edge.source_observer_id,
                edge.target_observer_id,
                edge.declared_domain,
                (bad,) + edge.rows[1:],
                edge.dependency_ids,
            ),
        ),
        "aggregate-input": (
            source.inputs[0],
            "commitment",
            lambda bad: observer_network_source(
                source.doctrine_id,
                source.source_id,
                source.source_version,
                (bad,) + source.inputs[1:],
                source.observers,
                source.translations,
                source.triangles,
                source.p1a_doctrine,
                source.p1a_binding,
                source.p1a_stage_source,
                source.raw_pairs,
            ),
        ),
    }
    return cases[case]


@pytest.mark.parametrize(
    "case",
    (
        "ready",
        "observation-input",
        "observation-response",
        "observer-descriptor",
        "observer-row",
        "translation-value",
        "translation-row",
        "aggregate-input",
    ),
)
def test_exported_constructors_refuse_deleted_extra_hostile_dict_and_subclass(case):
    source = network_source()
    child, deleted_field, operation = _constructor_case(source, case)

    deleted = replace(child)
    object.__delattr__(deleted, deleted_field)
    with pytest.raises(ObserverNetworkError):
        operation(deleted)

    extra = replace(child)
    object.__setattr__(extra, "unexpected", "metadata")
    with pytest.raises(ObserverNetworkError):
        operation(extra)

    BombDict.calls = 0
    hostile_dict = replace(child)
    object.__setattr__(
        hostile_dict,
        "__dict__",
        BombDict(object.__getattribute__(hostile_dict, "__dict__")),
    )
    with pytest.raises(ObserverNetworkError):
        operation(hostile_dict)
    assert BombDict.calls == 0

    calls = [0]

    def hostile_getattribute(self, name):
        calls[0] += 1
        raise AssertionError("hostile field read")

    hostile_type = type("HostileChild", (type(child),), {"__getattribute__": hostile_getattribute})
    hostile_subclass = object.__new__(hostile_type)
    object.__setattr__(hostile_subclass, "__dict__", dict(object.__getattribute__(child, "__dict__")))
    with pytest.raises(ObserverNetworkError):
        operation(hostile_subclass)
    assert calls == [0]
