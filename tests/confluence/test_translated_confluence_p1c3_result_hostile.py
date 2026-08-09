"""Exact result-shape pressure for P1-C3 hostile revalidation."""

from dataclasses import replace

import pytest

from src.core.translated_confluence import (
    TranslatedConfluenceJudgment, TranslatedConfluenceValidationError,
    translated_confluence_judgment, validate_translated_confluence_result,
)

from translated_confluence_fixture import translated_fixture


def validate(fixture, value):
    return validate_translated_confluence_result(*fixture[:9], value)


def test_hollow_exact_judgment_and_row_are_typed_rejections():
    fixture = translated_fixture()
    result = translated_confluence_judgment(*fixture[:9])
    hollow = object.__new__(TranslatedConfluenceJudgment)
    with pytest.raises(TranslatedConfluenceValidationError):
        validate(fixture, hollow)
    hollow_row = object.__new__(type(result.transport_cell.response_rows[0]))
    forged_cell = replace(
        result.transport_cell,
        response_rows=(hollow_row, *result.transport_cell.response_rows[1:]),
    )
    with pytest.raises(TranslatedConfluenceValidationError):
        validate(fixture, replace(result, transport_cell=forged_cell))


def test_tuple_subclass_and_digest_transplant_are_rejected():
    fixture = translated_fixture()
    result = translated_confluence_judgment(*fixture[:9])

    class EvilTuple(tuple):
        pass

    forged = replace(
        result.transport_cell,
        response_rows=EvilTuple(result.transport_cell.response_rows),
    )
    with pytest.raises(TranslatedConfluenceValidationError):
        validate(fixture, replace(result, transport_cell=forged))
    with pytest.raises(TranslatedConfluenceValidationError):
        validate(fixture, replace(result, bridge_digest="0" * 64))


def test_wrong_exact_variant_and_nested_scalar_drift_are_rejected():
    fixture = translated_fixture()
    result = translated_confluence_judgment(*fixture[:9])
    with pytest.raises(TranslatedConfluenceValidationError):
        validate(fixture, object())
    row = replace(result.transport_cell.response_rows[0], point_index=99)
    cell = replace(result.transport_cell, response_rows=(row, *result.transport_cell.response_rows[1:]))
    with pytest.raises(TranslatedConfluenceValidationError):
        validate(fixture, replace(result, transport_cell=cell))
