"""Explicit logical-only projections from strict v3 data into Phase-II records."""

from __future__ import annotations

import logging

from ...observer_discovery_types import DiscoveryRow, DiscoverySplit
from .canonical import validate_three_way_presentation
from .types import (
    CanonicalPresentation,
    RepresentationProtocolError,
    ThreeWayPresentation,
)

logger = logging.getLogger(__name__)

PHASE2_COMPAT_BOUNDARY = (
    "logical compatibility projection into Phase-II in-memory records only; it exports detached row data, "
    "provides no locked-test custody, access control, process isolation, observer admission, E4 robustness, "
    "and no claim promotion"
)


def discovery_split_from_three_way(value: ThreeWayPresentation) -> DiscoverySplit:
    """Project train/validation into Phase-II without accessing the declared test rows."""
    logger.debug("discovery_split_from_three_way entry")
    if not validate_three_way_presentation(value):
        _reject("invalid-presentation", "three-way-required")
    result = DiscoverySplit(_discovery_rows(value.train), _discovery_rows(value.validation))
    logger.debug(
        "discovery_split_from_three_way exit train=%d validation=%d boundary=%s",
        len(result.train),
        len(result.holdout),
        PHASE2_COMPAT_BOUNDARY,
    )
    return result


def declared_test_rows_from_three_way(value: ThreeWayPresentation) -> tuple[DiscoveryRow, ...]:
    """Export a detached Phase-II copy, explicitly forfeiting any custody assertion."""
    logger.debug("declared_test_rows_from_three_way entry")
    if not validate_three_way_presentation(value):
        _reject("invalid-presentation", "three-way-required")
    result = _discovery_rows(value.test)
    logger.debug(
        "declared_test_rows_from_three_way exit rows=%d boundary=%s",
        len(result),
        PHASE2_COMPAT_BOUNDARY,
    )
    return result


def _discovery_rows(presentation: CanonicalPresentation) -> tuple[DiscoveryRow, ...]:
    logger.debug("_discovery_rows entry rows=%d", len(presentation.rows))
    result = tuple(
        DiscoveryRow(
            row.row_id,
            row.source_id,
            row.content_id,
            row.group_id,
            tuple(row.values),
            row.target,
        )
        for row in presentation.rows
    )
    logger.debug("_discovery_rows exit rows=%d", len(result))
    return result


def _reject(reason: str, detail: str) -> None:
    logger.error("phase2 compatibility projection rejected reason=%s detail=%s", reason, detail)
    raise RepresentationProtocolError(reason, detail)
