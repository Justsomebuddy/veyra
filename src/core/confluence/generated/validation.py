"""Fresh hard-envelope/result validation for P3-C1."""

from __future__ import annotations

import logging

from .common import exact_digest, exact_shape, exact_text, reject
from .digest import result_digest, row_digest
from .formal import snapshot_theorem_source
from .runtime import generated_finite_confluence
from .types import (
    FailedBound,
    GeneratedConfluenceResourceLimit,
    GeneratedConfluenceResult,
    GeneratedConfluenceStatus,
    GeneratedFailureKind,
    GeneratedFiniteConfluence,
    GeneratedFormalPhaseReceipt,
    GeneratedLocalPeak,
    LocalCell,
    LocalPeakRow,
    P3C1_NONCLAIMS,
    RankedContinuationSystem,
)

logger = logging.getLogger(__name__)


def validate_generated_confluence_result(
    raw_system: RankedContinuationSystem,
    raw_cells: tuple[LocalCell, ...],
    raw_result: GeneratedConfluenceResult,
) -> GeneratedConfluenceResult:
    """Validate every nested result type before fresh formal/semantic replay."""
    logger.debug("validate_generated_confluence_result entry")
    if type(raw_result) is GeneratedFiniteConfluence:
        _shallow_positive(raw_result)
    elif type(raw_result) is GeneratedConfluenceResourceLimit:
        _shallow_resource(raw_result)
    else:
        reject("generated-result-type-invalid")
    expected = generated_finite_confluence(raw_system, raw_cells)
    if type(expected) is not type(raw_result) or expected != raw_result:
        reject("generated-result-mismatch")
    logger.debug("validate_generated_confluence_result exit type=%s", type(expected).__name__)
    return expected


def _shallow_positive(value: GeneratedFiniteConfluence) -> None:
    logger.debug("_shallow_positive entry")
    exact_shape(value, GeneratedFiniteConfluence, "generated-positive-result")
    for name in (
        "reachable_state_ids",
        "reachable_edge_ids",
        "peaks",
        "rows",
        "theorem_phase_receipts",
        "nonclaims",
    ):
        if type(object.__getattribute__(value, name)) is not tuple:
            reject("generated-result-container-invalid")
    exact_digest(value.system_digest, "result-system-digest")
    exact_digest(value.theorem_receipt_digest, "theorem-receipt-digest")
    exact_digest(value.result_digest, "result-digest")
    if type(value.status) is not GeneratedConfluenceStatus:
        reject("generated-result-status-type-invalid")
    if value.first_counterexample_peak_id is not None:
        exact_text(value.first_counterexample_peak_id, "result-first-counterexample")
    for label, items in (
        ("reachable-state", value.reachable_state_ids),
        ("reachable-edge", value.reachable_edge_ids),
        ("nonclaim", value.nonclaims),
    ):
        for item in items:
            exact_text(item, label)
    snapshot_theorem_source(value.theorem_source)
    for peak in value.peaks:
        _shallow_peak(peak)
    for row in value.rows:
        _shallow_row(row)
    for phase in value.theorem_phase_receipts:
        _shallow_phase(phase)
    if tuple(row.peak for row in value.rows) != value.peaks:
        reject("generated-result-row-peak-order-invalid")
    if value.reachable_state_ids != tuple(sorted(set(value.reachable_state_ids))):
        reject("generated-result-reachable-state-order-invalid")
    if value.reachable_edge_ids != tuple(sorted(set(value.reachable_edge_ids))):
        reject("generated-result-reachable-edge-order-invalid")
    positive = value.status is GeneratedConfluenceStatus.GENERATED_FINITE_CONFLUENT_RELATIVE_TO_SYSTEM
    phase_names = tuple(row.phase for row in value.theorem_phase_receipts)
    if positive:
        if phase_names != ("elan-which", "lean-version", "lean-compile") or value.theorem_receipt_digest == "0" * 64:
            reject("generated-result-positive-formal-receipt-invalid")
    elif phase_names or value.theorem_receipt_digest != "0" * 64:
        reject("generated-result-negative-formal-receipt-invalid")
    if sum(row.output_bytes for row in value.theorem_phase_receipts) > 1_048_576:
        reject("generated-result-formal-output-cap-invalid")
    expected_first = next((row.peak.peak_id for row in value.rows if row.status is value.status and not positive), None)
    if value.first_counterexample_peak_id != expected_first:
        reject("generated-result-first-counterexample-invalid")
    if value.nonclaims != P3C1_NONCLAIMS:
        reject("generated-result-nonclaims-drift")
    if result_digest(value) != value.result_digest:
        reject("generated-result-digest-mismatch")
    logger.debug("_shallow_positive exit")


def _shallow_peak(value: GeneratedLocalPeak) -> None:
    logger.debug("_shallow_peak entry")
    exact_shape(value, GeneratedLocalPeak, "generated-result-peak")
    for name in ("peak_id", "source_state_id", "left_edge_id", "right_edge_id"):
        exact_text(object.__getattribute__(value, name), f"peak-{name}")
    exact_digest(value.peak_digest, "peak-digest")
    if value.peak_id != value.peak_digest:
        reject("generated-result-peak-id-digest-mismatch")
    logger.debug("_shallow_peak exit")


def _shallow_row(value: LocalPeakRow) -> None:
    logger.debug("_shallow_row entry")
    exact_shape(value, LocalPeakRow, "generated-result-row")
    _shallow_peak(value.peak)
    if value.cell_digest is not None:
        exact_digest(value.cell_digest, "result-cell-digest")
    for label, item in (("left-endpoint", value.left_endpoint_id), ("right-endpoint", value.right_endpoint_id)):
        if item is not None:
            exact_text(item, label)
    if type(value.status) is not GeneratedConfluenceStatus:
        reject("generated-result-row-status-type-invalid")
    exact_digest(value.row_digest, "result-row-digest")
    if row_digest(value) != value.row_digest:
        reject("generated-result-row-digest-mismatch")
    logger.debug("_shallow_row exit")


def _shallow_phase(value: GeneratedFormalPhaseReceipt) -> None:
    logger.debug("_shallow_phase entry")
    exact_shape(value, GeneratedFormalPhaseReceipt, "generated-formal-phase")
    exact_text(value.phase, "formal-phase-name")
    if type(value.return_code) is not int or type(value.output_bytes) is not int:
        reject("generated-formal-phase-integer-type-invalid")
    if value.output_bytes < 0 or value.return_code != 0:
        reject("generated-formal-phase-value-invalid")
    exact_digest(value.output_digest, "formal-phase-output-digest")
    logger.debug("_shallow_phase exit")


def _shallow_resource(value: GeneratedConfluenceResourceLimit) -> None:
    logger.debug("_shallow_resource entry")
    exact_shape(value, GeneratedConfluenceResourceLimit, "generated-resource-result")
    if type(value.status) is not GeneratedFailureKind or type(value.failed_bound) is not FailedBound:
        reject("resource-enum-type-invalid")
    exact_digest(value.source_hint_digest, "resource-source-hint")
    exact_digest(value.refusal_digest, "resource-refusal-digest")
    if type(value.required_value) is not int or type(value.allowed_value) is not int:
        reject("resource-count-type-invalid")
    if type(value.nonclaims) is not tuple or any(type(item) is not str for item in value.nonclaims):
        reject("generated-resource-nonclaims-type-invalid")
    if value.nonclaims != P3C1_NONCLAIMS:
        reject("generated-resource-nonclaims-drift")
    logger.debug("_shallow_resource exit")
