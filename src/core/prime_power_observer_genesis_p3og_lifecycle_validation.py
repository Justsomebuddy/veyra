"""Fresh exact replay validation for P3-OG first-closure evidence."""

from __future__ import annotations

from dataclasses import fields, is_dataclass
from hmac import compare_digest
import logging

from .prime_power_observer_genesis_p3og_codec import evidence_bytes
from .prime_power_observer_genesis_p3og_lifecycle_runtime import (
    _run_p3og_first_closure_validated,
)
from .prime_power_observer_genesis_p3og_lifecycle_source import (
    validate_formation_source,
)
from .prime_power_observer_genesis_p3og_lifecycle_types import (
    P3OGFirstClosureEvidence,
    P3OGFormationSource,
)
from .prime_power_observer_genesis_p3og_types import P3OGSource

logger = logging.getLogger(__name__)


def _require_exact_lifecycle_shape(
    value: object,
    expected: object,
    depth: int = 0,
) -> None:
    """Reject foreign nested values before canonical byte comparison."""
    logger.debug("p3og.lifecycle.require_shape entry depth=%d", depth)
    if depth > 24 or type(value) is not type(expected):
        logger.error("p3og.lifecycle.require_shape type/depth mismatch")
        raise ValueError("p3og-first-closure-evidence-shape")
    if type(expected) is tuple:
        if len(value) != len(expected):  # type: ignore[arg-type]
            logger.error("p3og.lifecycle.require_shape tuple length mismatch")
            raise ValueError("p3og-first-closure-evidence-shape")
        for actual_item, expected_item in zip(value, expected, strict=True):  # type: ignore[arg-type]
            _require_exact_lifecycle_shape(actual_item, expected_item, depth + 1)
    elif is_dataclass(expected) and not isinstance(expected, type):
        for field in fields(expected):
            _require_exact_lifecycle_shape(
                getattr(value, field.name),
                getattr(expected, field.name),
                depth + 1,
            )
    logger.debug("p3og.lifecycle.require_shape exit depth=%d", depth)


def validate_first_closure_evidence(
    source: P3OGSource,
    formation_source: P3OGFormationSource,
    evidence: P3OGFirstClosureEvidence,
) -> P3OGFirstClosureEvidence:
    """Freshly reconstruct evidence; this grants no historical authority."""
    logger.debug("p3og.lifecycle.validate_evidence entry")
    source, formation_source = validate_formation_source(source, formation_source)
    if type(evidence) is not P3OGFirstClosureEvidence:
        logger.error("p3og.lifecycle.validate_evidence wrong outer type")
        raise ValueError("p3og-first-closure-evidence-type")
    try:
        expected = _run_p3og_first_closure_validated(source, formation_source)
        _require_exact_lifecycle_shape(evidence, expected)
        equal = compare_digest(
            evidence_bytes(evidence),
            evidence_bytes(expected),
        )
    except (AttributeError, RecursionError, TypeError, UnicodeError, ValueError) as exc:
        logger.error(
            "p3og.lifecycle.validate_evidence malformed type=%s",
            type(exc).__name__,
        )
        raise ValueError("p3og-first-closure-evidence-malformed") from exc
    if not equal:
        logger.error("p3og.lifecycle.validate_evidence evidence drift")
        raise ValueError("p3og-first-closure-evidence-drift")
    logger.debug("p3og.lifecycle.validate_evidence exit status=%s", expected.status.value)
    return expected
