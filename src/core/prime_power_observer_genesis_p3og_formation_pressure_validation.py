"""Fresh exact validation for P3-OG formation-pressure bindings."""

from __future__ import annotations

from dataclasses import fields, is_dataclass
from hmac import compare_digest
import logging
from typing import cast

from .prime_power_observer_genesis_p3og_formation_pressure_runtime import (
    build_p3og_formation_pressure_binding,
)
from .prime_power_observer_genesis_p3og_formation_pressure_types import (
    P3OGFormationPressureBinding,
)
from .prime_power_observer_genesis_p3og_codec import evidence_bytes
from .prime_power_observer_genesis_p3og_lifecycle_types import (
    P3OGFirstClosureEvidence,
    P3OGFormationSource,
)
from .prime_power_observer_genesis_p3og_types import P3OGPressureReport, P3OGSource

logger = logging.getLogger(__name__)


def _require_exact_binding_shape(
    value: object,
    expected: object,
    depth: int = 0,
) -> None:
    """Reject foreign nested bridge values before canonical comparison."""
    logger.debug("p3og.binding.require_shape entry depth=%d", depth)
    if depth > 24 or type(value) is not type(expected):
        logger.error("p3og.binding.require_shape type/depth mismatch")
        raise ValueError("p3og-formation-pressure-binding-shape")
    if type(expected) is tuple:
        actual_tuple = cast(tuple[object, ...], value)
        if len(actual_tuple) != len(expected):
            logger.error("p3og.binding.require_shape tuple length mismatch")
            raise ValueError("p3og-formation-pressure-binding-shape")
        for actual_item, expected_item in zip(
            actual_tuple,
            expected,
            strict=True,
        ):
            _require_exact_binding_shape(actual_item, expected_item, depth + 1)
    elif is_dataclass(expected) and not isinstance(expected, type):
        for field in fields(expected):
            _require_exact_binding_shape(
                getattr(value, field.name),
                getattr(expected, field.name),
                depth + 1,
            )
    logger.debug("p3og.binding.require_shape exit depth=%d", depth)


def validate_p3og_formation_pressure_binding(
    source: P3OGSource,
    formation_source: P3OGFormationSource,
    evidence: P3OGFirstClosureEvidence,
    report: P3OGPressureReport,
    binding: P3OGFormationPressureBinding,
) -> P3OGFormationPressureBinding:
    """Freshly reconstruct the exact bridge without granting authority."""
    logger.debug("p3og.binding.validate entry")
    if type(binding) is not P3OGFormationPressureBinding:
        logger.error("p3og.binding.validate wrong outer type")
        raise ValueError("p3og-formation-pressure-binding-type")
    logger.debug("p3og.binding.validate reconstructing expected binding")
    expected = build_p3og_formation_pressure_binding(
        source,
        formation_source,
        evidence,
        report,
    )
    try:
        _require_exact_binding_shape(binding, expected)
        equal = compare_digest(
            evidence_bytes(binding),
            evidence_bytes(expected),
        )
    except (AttributeError, RecursionError, TypeError, UnicodeError, ValueError) as exc:
        logger.error("p3og.binding.validate malformed")
        raise ValueError("p3og-formation-pressure-binding-malformed") from exc
    if not equal:
        logger.error("p3og.binding.validate binding drift")
        raise ValueError("p3og-formation-pressure-binding-drift")
    logger.debug(
        "p3og.binding.validate exit selected_status=%s",
        expected.selected_candidate_status.value,
    )
    return expected
