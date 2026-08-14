"""Public construction facade for strict categorical CSV and JSONL ingestion."""

from __future__ import annotations

import logging
from collections.abc import Callable

from ..schema import (
    RepresentationRow,
    RepresentationSchema,
    ThreeWayPresentation,
    canonical_presentation,
    canonical_representation_schema,
    canonical_three_way_presentation,
)
from .parsing import expected_columns, parse_csv_rows, parse_jsonl_rows

logger = logging.getLogger(__name__)


def categorical_three_way_from_csv(
    schema: RepresentationSchema,
    *,
    train: bytes,
    validation: bytes,
    test: bytes,
) -> ThreeWayPresentation:
    """Build one canonical three-way presentation from strict tagged CSV bytes."""
    logger.debug("categorical_three_way_from_csv entry")
    result = _categorical_three_way(schema, train, validation, test, parse_csv_rows)
    logger.debug("categorical_three_way_from_csv exit")
    return result


def categorical_three_way_from_jsonl(
    schema: RepresentationSchema,
    *,
    train: bytes,
    validation: bytes,
    test: bytes,
) -> ThreeWayPresentation:
    """Build one canonical three-way presentation from strict native JSONL bytes."""
    logger.debug("categorical_three_way_from_jsonl entry")
    result = _categorical_three_way(schema, train, validation, test, parse_jsonl_rows)
    logger.debug("categorical_three_way_from_jsonl exit")
    return result


def _categorical_three_way(
    schema: RepresentationSchema,
    train: bytes,
    validation: bytes,
    test: bytes,
    parser: Callable[[bytes, RepresentationSchema], tuple[RepresentationRow, ...]],
) -> ThreeWayPresentation:
    logger.debug("_categorical_three_way entry parser=%s", parser.__name__)
    canonical_schema = canonical_representation_schema(schema)
    expected_columns(canonical_schema)
    train_presentation = canonical_presentation(canonical_schema, parser(train, canonical_schema))
    validation_presentation = canonical_presentation(canonical_schema, parser(validation, canonical_schema))
    test_presentation = canonical_presentation(canonical_schema, parser(test, canonical_schema))
    result = canonical_three_way_presentation(train_presentation, validation_presentation, test_presentation)
    logger.debug(
        "_categorical_three_way exit rows=%d",
        len(result.train.rows) + len(result.validation.rows) + len(result.test.rows),
    )
    return result
