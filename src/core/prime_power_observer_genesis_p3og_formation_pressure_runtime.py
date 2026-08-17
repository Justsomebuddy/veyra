"""Fresh producer for the non-promoting P3-OG formation-pressure bridge."""

from __future__ import annotations

import logging

from hmac import compare_digest

from .prime_power_observer_genesis_p3og_formation_pressure_codec import (
    formation_pressure_digest,
)
from .prime_power_observer_genesis_p3og_formation_pressure_types import (
    P3OGFormationPressureBinding,
    P3OG_FORMATION_PRESSURE_NONCLAIMS,
)
from .prime_power_observer_genesis_p3og_codec import evidence_bytes
from .prime_power_observer_genesis_p3og_lifecycle_source import (
    validate_formation_source,
)
from .prime_power_observer_genesis_p3og_lifecycle_types import (
    FirstClosureStatus,
    P3OGFirstClosureEvidence,
    P3OGFormationSource,
)
from .prime_power_observer_genesis_p3og_lifecycle_validation import (
    validate_first_closure_evidence,
)
from .prime_power_observer_genesis_p3og_machine_internal import (
    _initial_state_validated,
)
from .prime_power_observer_genesis_p3og_types import (
    P3OGPressureReport,
    P3OGSource,
)
from .prime_power_observer_genesis_p3og_validation import validate_pressure_report

logger = logging.getLogger(__name__)
BINDING_VERSION = "p3og-formation-pressure-binding-v1"


def _same_typed_evidence(left: object, right: object) -> bool:
    """Compare freshly reconstructed typed evidence without caller equality."""
    logger.debug("p3og.binding.same_typed_evidence entry")
    try:
        result = type(left) is type(right) and compare_digest(
            evidence_bytes(left),
            evidence_bytes(right),
        )
    except (AttributeError, RecursionError, TypeError, UnicodeError, ValueError) as exc:
        logger.error("p3og.binding.same_typed_evidence error")
        raise ValueError("p3og-formation-pressure-evidence-shape") from exc
    logger.debug("p3og.binding.same_typed_evidence exit equal=%s", result)
    return result


def _build_binding_validated(
    source: P3OGSource,
    formation_source: P3OGFormationSource,
    evidence: P3OGFirstClosureEvidence,
    report: P3OGPressureReport,
) -> P3OGFormationPressureBinding:
    """Build one bridge after all four caller inputs have been freshly replayed."""
    logger.debug("p3og.binding.build_validated entry")
    if evidence.status is not FirstClosureStatus.WITNESSED:
        logger.error("p3og.binding.build_validated first closure not witnessed")
        raise ValueError("p3og-formation-pressure-first-closure")
    if not _same_typed_evidence(formation_source.selection, report.selection):
        logger.error("p3og.binding.build_validated selection mismatch")
        raise ValueError("p3og-formation-pressure-selection")

    selection = report.selection
    try:
        selected_seed = source.seeds[selection.selected_index]
        selected_result = report.candidates[selection.selected_index]
    except (AttributeError, IndexError, TypeError) as exc:
        logger.error("p3og.binding.build_validated selected row error")
        raise ValueError("p3og-formation-pressure-selection") from exc
    if (
        selected_seed.seed_digest != selection.selected_seed_digest
        or selected_seed.seed_digest != formation_source.selected_seed_digest
    ):
        logger.error("p3og.binding.build_validated selected seed mismatch")
        raise ValueError("p3og-formation-pressure-selected-seed")

    logger.debug("p3og.binding.build_validated reconstructing pressure entry")
    pressure_entry = _initial_state_validated(source, selected_seed)
    if evidence.pressure_entry_state_digest != pressure_entry.state_digest:
        logger.error("p3og.binding.build_validated pressure entry mismatch")
        raise ValueError("p3og-formation-pressure-entry")
    if (
        selected_result.seed_digest != selected_seed.seed_digest
        or report.selected_candidate_result_digest != selected_result.result_digest
    ):
        logger.error("p3og.binding.build_validated selected result mismatch")
        raise ValueError("p3og-formation-pressure-selected-result")
    if (
        selected_result.maintenance_control is None
        or selected_result.active_left is None
        or selected_result.active_right is None
        or selected_result.maintenance_control.enabled_state_digest != pressure_entry.state_digest
        or selected_result.active_left.coupling.before_digest != pressure_entry.state_digest
        or selected_result.active_right.coupling.before_digest != pressure_entry.state_digest
    ):
        logger.error("p3og.binding.build_validated active entry mismatch")
        raise ValueError("p3og-formation-pressure-active-entry")

    fields = (
        BINDING_VERSION,
        source.source_digest,
        formation_source.source_digest,
        evidence.evidence_digest,
        report.report_digest,
        selection.receipt_digest,
        selected_seed.seed_digest,
        pressure_entry.state_digest,
        selected_result.result_digest,
        selected_result.status,
        0,
        P3OG_FORMATION_PRESSURE_NONCLAIMS,
    )
    result = P3OGFormationPressureBinding(
        *fields,
        formation_pressure_digest(*fields),
    )
    logger.debug(
        "p3og.binding.build_validated exit selected_status=%s",
        result.selected_candidate_status.value,
    )
    return result


def build_p3og_formation_pressure_binding(
    source: P3OGSource,
    formation_source: P3OGFormationSource,
    evidence: P3OGFirstClosureEvidence,
    report: P3OGPressureReport,
) -> P3OGFormationPressureBinding:
    """Freshly replay and bind exact witnessed formation to selected pressure."""
    logger.debug("p3og.binding.bind entry")
    try:
        logger.debug("p3og.binding.bind validating formation source")
        source, formation_source = validate_formation_source(
            source,
            formation_source,
        )
        logger.debug("p3og.binding.bind validating first-closure evidence")
        evidence = validate_first_closure_evidence(
            source,
            formation_source,
            evidence,
        )
        logger.debug("p3og.binding.bind validating pressure report")
        report = validate_pressure_report(source, report)
        result = _build_binding_validated(
            source,
            formation_source,
            evidence,
            report,
        )
    except (AttributeError, IndexError, RecursionError, TypeError, UnicodeError, ValueError):
        logger.error("p3og.binding.bind error")
        raise
    logger.debug(
        "p3og.binding.bind exit selected_status=%s",
        result.selected_candidate_status.value,
    )
    return result
