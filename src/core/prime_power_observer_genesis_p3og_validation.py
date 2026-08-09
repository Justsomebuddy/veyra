"""Deterministic replay drift check for P3-OG pressure reports."""

from __future__ import annotations

from dataclasses import fields, is_dataclass
from hmac import compare_digest
import logging

from .prime_power_observer_genesis_p3og_codec import evidence_bytes
from .prime_power_observer_genesis_p3og_runtime import _run_p3og_pressure_validated
from .prime_power_observer_genesis_p3og_source import validate_source
from .prime_power_observer_genesis_p3og_types import P3OGPressureReport, P3OGSource

logger = logging.getLogger(__name__)


def _require_exact_shape(value: object, expected: object, depth: int = 0) -> None:
    """Reject foreign nested values without invoking attacker-defined equality."""
    logger.debug("p3og._require_exact_shape entry depth=%d", depth)
    if depth > 24 or type(value) is not type(expected):
        logger.error("p3og._require_exact_shape type/depth mismatch depth=%d", depth)
        raise ValueError("p3og-report-shape")
    if type(expected) is tuple:
        if len(value) != len(expected):  # type: ignore[arg-type]
            logger.error("p3og._require_exact_shape tuple length mismatch")
            raise ValueError("p3og-report-shape")
        for actual_item, expected_item in zip(value, expected, strict=True):  # type: ignore[arg-type]
            _require_exact_shape(actual_item, expected_item, depth + 1)
    elif is_dataclass(expected) and not isinstance(expected, type):
        for field in fields(expected):
            _require_exact_shape(
                getattr(value, field.name), getattr(expected, field.name), depth + 1,
            )
    logger.debug("p3og._require_exact_shape exit depth=%d", depth)


def validate_pressure_report(
    source: P3OGSource, report: P3OGPressureReport,
) -> P3OGPressureReport:
    """Recompute deterministic checks; this is not historical authentication."""
    logger.debug("p3og.validate_pressure_report entry")
    source = validate_source(source)
    if type(report) is not P3OGPressureReport:
        logger.error("p3og.validate_pressure_report wrong report type")
        raise ValueError("p3og-report-type")
    try:
        expected = _run_p3og_pressure_validated(source)
        _require_exact_shape(report, expected)
        equal = compare_digest(evidence_bytes(report), evidence_bytes(expected))
    except (AttributeError, RecursionError, TypeError, UnicodeError, ValueError) as exc:
        logger.error("p3og.validate_pressure_report malformed report=%s", exc)
        raise ValueError("p3og-report-malformed") from exc
    if not equal:
        logger.error("p3og.validate_pressure_report report drift")
        raise ValueError("p3og-report-drift")
    logger.debug("p3og.validate_pressure_report exit status=%s", expected.status.value)
    return expected
