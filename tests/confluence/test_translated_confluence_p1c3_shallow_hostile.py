"""Equality/property/hollow/huge hostile pressure before C3 traversal or replay."""

from dataclasses import replace

import pytest

from src.core.translated_confluence import (
    ObserverProgramBridgeRow, P0P1AResponseBridgeSource,
    TranslatedConfluenceJudgment, TranslatedConfluenceValidationError,
    TranslatedEchoTransportSpec, translated_confluence_judgment,
    validate_translated_confluence_result,
)

from translated_confluence_fixture import translated_fixture


class EqualityBomb:
    def __eq__(self, other):
        raise AssertionError("hostile equality executed")


class BridgeSubclass(P0P1AResponseBridgeSource):
    @property
    def bridge_digest(self):
        raise AssertionError("hostile property executed")


class SpecSubclass(TranslatedEchoTransportSpec):
    @property
    def spec_digest(self):
        raise AssertionError("hostile property executed")


class JudgmentSubclass(TranslatedConfluenceJudgment):
    @property
    def judgment_digest(self):
        raise AssertionError("hostile property executed")


class TupleSubclass(tuple):
    pass


def test_bridge_equality_bomb_subclass_hollow_and_tuple_subclass_reject_safely():
    fixture = translated_fixture()
    bomb_row = replace(fixture[6].observer_rows[0], p1a_observer_id=EqualityBomb())
    hostile_values = (
        replace(fixture[6], observer_rows=(bomb_row, *fixture[6].observer_rows[1:])),
        object.__new__(P0P1AResponseBridgeSource),
        replace(fixture[6], observer_rows=TupleSubclass(fixture[6].observer_rows)),
    )
    for value in hostile_values:
        with pytest.raises(TranslatedConfluenceValidationError):
            translated_confluence_judgment(*fixture[:6], value, fixture[7], fixture[8])
    with pytest.raises(TranslatedConfluenceValidationError):
        translated_confluence_judgment(
            *fixture[:6], object.__new__(BridgeSubclass), fixture[7], fixture[8],
        )


def test_hollow_bridge_rows_spec_policy_and_property_subclass_are_typed():
    fixture = translated_fixture()
    hollow_row = object.__new__(ObserverProgramBridgeRow)
    hostile_bridge = replace(
        fixture[6], observer_rows=(hollow_row, *fixture[6].observer_rows[1:]),
    )
    with pytest.raises(TranslatedConfluenceValidationError):
        translated_confluence_judgment(*fixture[:6], hostile_bridge, fixture[7], fixture[8])
    for spec in (object.__new__(TranslatedEchoTransportSpec), object.__new__(SpecSubclass)):
        with pytest.raises(TranslatedConfluenceValidationError):
            translated_confluence_judgment(*fixture[:7], spec, fixture[8])
    hollow_policy = object.__new__(type(fixture[8]))
    with pytest.raises(TranslatedConfluenceValidationError):
        translated_confluence_judgment(*fixture[:8], hollow_policy)


def test_hollow_and_huge_result_reject_before_any_semantic_replay(monkeypatch):
    fixture = translated_fixture()
    positive = translated_confluence_judgment(*fixture[:9])
    assert type(positive) is TranslatedConfluenceJudgment
    calls = []

    def forbidden(*args, **kwargs):
        calls.append((args, kwargs))
        raise AssertionError("semantic replay executed")

    monkeypatch.setattr(
        "src.core.translated_confluence_result_validation.translated_confluence_judgment",
        forbidden,
    )
    with pytest.raises(TranslatedConfluenceValidationError):
        validate_translated_confluence_result(*fixture[:9], object.__new__(TranslatedConfluenceJudgment))
    with pytest.raises(TranslatedConfluenceValidationError):
        validate_translated_confluence_result(*fixture[:9], object.__new__(JudgmentSubclass))
    row = positive.transport_cell.response_rows[0]
    huge_cell = replace(positive.transport_cell, response_rows=(row,) * 514)
    with pytest.raises(TranslatedConfluenceValidationError):
        validate_translated_confluence_result(
            *fixture[:9], replace(positive, transport_cell=huge_cell),
        )
    assert calls == []


def test_huge_supplied_bridge_rows_reject_before_semantic_calls(monkeypatch):
    fixture = translated_fixture()
    calls = []

    def forbidden(*args, **kwargs):
        calls.append((args, kwargs))
        raise AssertionError("semantic call executed")

    monkeypatch.setattr("src.core.translated_confluence_runtime.observer_relation_judgment", forbidden)
    huge = replace(fixture[6], observer_rows=(fixture[6].observer_rows[0],) * 65)
    with pytest.raises(TranslatedConfluenceValidationError):
        translated_confluence_judgment(*fixture[:6], huge, fixture[7], fixture[8])
    assert calls == []
