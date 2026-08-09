"""Outer-envelope-first replay for hostile P3-A1b result objects."""

from __future__ import annotations

import logging

from .common import exact_digest, exact_shape, reject
from .runtime import (
    _judge, project_residue, refute_offset_program, report_missing_bridge_evidence,
)
from .sources import AXIOM_ROWS, THEOREM_IDS
from .types import (
    A1B_NONCLAIMS, BoundaryStatus, BridgeEvidenceKind, BridgeFormalFailure,
    BridgeOpen, BridgeProvenance, BridgeRefutation, BridgeResourceLimit, BridgeStatus,
    FailedBound, FamilyKind, FormalFailureKind, ProductiveBridgeJudgment,
    ProjectionArtifact, ResultStatus, UniformizationRoute,
)

logger = logging.getLogger(__name__)


def _tuple(value: object, expected: tuple, label: str) -> None:
    """Require exact built-in tuple before any value equality."""
    logger.debug("_tuple entry label=%s", label)
    if type(value) is not tuple or len(value) != len(expected):
        reject(f"{label}-shape-invalid")
    for actual, wanted in zip(value, expected, strict=True):
        if type(wanted) is tuple:
            _tuple(actual, wanted, label)
        elif type(actual) is not type(wanted):
            reject(f"{label}-shape-invalid")
    if value != expected:
        reject(f"{label}-value-invalid")
    logger.debug("_tuple exit")


def _positive(value: ProductiveBridgeJudgment) -> None:
    """Validate all outer fields and six digest domains before replay."""
    logger.debug("_positive entry")
    exact_shape(value, ProductiveBridgeJudgment, "bridge-judgment")
    enums = (
        (value.family_kind, FamilyKind, FamilyKind.ALL_DEPTH_FAMILY),
        (value.bridge_evidence_kind, BridgeEvidenceKind, BridgeEvidenceKind.PRODUCTIVE_FAMILY_BRIDGE),
        (value.bridge_status, BridgeStatus, BridgeStatus.ESTABLISHED_RELATIVE_TO_LEDGER),
        (value.bridge_provenance, BridgeProvenance, BridgeProvenance.FORMALLY_DERIVED),
        (value.uniformization_route, UniformizationRoute, UniformizationRoute.A1_DEFINITIONAL),
        (value.completed_carrier, BoundaryStatus, BoundaryStatus.NOT_ESTABLISHED),
        (value.universal_completion, BoundaryStatus, BoundaryStatus.OPEN),
        (value.physical_or_foundation_independent_infinity, BoundaryStatus, BoundaryStatus.NOT_CLAIMED),
    )
    if any(type(x) is not cls or x is not expected for x, cls, expected in enums):
        reject("bridge-judgment-enum-invalid")
    statuses = (value.productivity_status, value.determinism_status,
                value.process_coherence_status, value.family_introduction_status)
    if any(type(x) is not BridgeStatus or x is not BridgeStatus.ESTABLISHED_RELATIVE_TO_LEDGER for x in statuses):
        reject("bridge-component-status-invalid")
    if type(value.promotions) is not int or value.promotions != 0:
        reject("bridge-promotions-must-be-zero")
    names = ("program_digest", "family_term_digest", "productivity_evidence_digest",
             "family_introduction_digest", "bridge_evidence_digest", "judgment_digest")
    for name in names:
        exact_digest(getattr(value, name), name)
    if len({getattr(value, name) for name in names}) != 6:
        reject("bridge-digest-domains-not-distinct")
    _tuple(value.theorem_ids, THEOREM_IDS, "bridge-theorem-ids")
    _tuple(value.theorem_axiom_rows, AXIOM_ROWS, "bridge-axiom-rows")
    _tuple(value.nonclaims, A1B_NONCLAIMS, "bridge-nonclaims")
    logger.debug("_positive exit")


def _resource(value: BridgeResourceLimit) -> None:
    """Validate proof-payload-free resource refusal."""
    logger.debug("_resource entry")
    exact_shape(value, BridgeResourceLimit, "bridge-resource")
    if type(value.status) is not ResultStatus or value.status is not ResultStatus.RESOURCE_LIMIT:
        reject("resource-status-invalid")
    if type(value.failed_bound) is not FailedBound:
        reject("resource-bound-invalid")
    if type(value.required_value) is not int or type(value.allowed_value) is not int:
        reject("resource-scalars-invalid")
    if value.required_value <= value.allowed_value or value.allowed_value < 1:
        reject("resource-order-invalid")
    for name in ("package_digest", "policy_digest", "run_digest", "refusal_digest"):
        exact_digest(getattr(value, name), name)
    logger.debug("_resource exit")


def _failure(value: BridgeFormalFailure) -> None:
    """Validate sanitized operational result with no ontological status."""
    logger.debug("_failure entry")
    exact_shape(value, BridgeFormalFailure, "bridge-formal-failure")
    if type(value.kind) is not FormalFailureKind or type(value.diagnostic) is not str:
        reject("formal-failure-fields-invalid")
    if value.diagnostic != f"formal execution {value.kind.value}":
        reject("formal-failure-diagnostic-invalid")
    for name in ("package_digest", "run_digest", "attempt_digest"):
        exact_digest(getattr(value, name), name)
    logger.debug("_failure exit")


def validate_productive_bridge_result(raw_package, value):
    """Freshly replay only after hostile outer validation."""
    logger.debug("validate_productive_bridge_result entry type=%s", type(value).__name__)
    if type(value) is ProductiveBridgeJudgment:
        _positive(value)
    elif type(value) is BridgeResourceLimit:
        _resource(value)
    elif type(value) is BridgeFormalFailure:
        _failure(value)
    else:
        reject("bridge-result-variant-invalid")
    expected = _judge(raw_package)
    if type(value) is not type(expected) or value != expected:
        reject("bridge-result-replay-mismatch")
    logger.debug("validate_productive_bridge_result exit")
    return expected


def _projection(value: ProjectionArtifact) -> None:
    """Validate the complete bounded projection envelope before replay."""
    logger.debug("_projection entry")
    raw = exact_shape(value, ProjectionArtifact, "projection-artifact")
    if type(raw["status"]) is not str or raw["status"] != "established":
        reject("projection-status-invalid")
    if any(type(raw[name]) is not int for name in ("depth", "modulus", "residue")):
        reject("projection-scalars-invalid")
    if raw["depth"] < 0 or raw["modulus"] < 2 or not 0 <= raw["residue"] < raw["modulus"]:
        reject("projection-values-invalid")
    if type(raw["qa_scope"]) is not str or raw["qa_scope"] != "QA_BOUNDED":
        reject("projection-scope-invalid")
    exact_digest(raw["projection_run_digest"], "projection-run-digest")
    logger.debug("_projection exit")


def validate_projection_result(raw_package, depth: int, value):
    """Reject hostile projection envelopes, then execute a fresh replay."""
    logger.debug("validate_projection_result entry")
    if type(value) is ProjectionArtifact:
        _projection(value)
    elif type(value) is BridgeResourceLimit:
        _resource(value)
    else:
        reject("projection-result-variant-invalid")
    expected = project_residue(raw_package, depth)
    if type(value) is not type(expected) or value != expected:
        reject("projection-result-replay-mismatch")
    logger.debug("validate_projection_result exit")
    return expected


def _refutation(value: BridgeRefutation) -> None:
    """Validate exact pressure evidence and mismatch fields before replay."""
    logger.debug("_refutation entry")
    raw = exact_shape(value, BridgeRefutation, "bridge-refutation")
    if type(raw["status"]) is not ResultStatus or raw["status"] is not ResultStatus.REFUTED:
        reject("refutation-status-invalid")
    names = ("mismatch_depth", "expected_residue", "observed_residue")
    if any(type(raw[name]) is not int for name in names):
        reject("refutation-scalars-invalid")
    if raw["mismatch_depth"] < 0 or raw["expected_residue"] == raw["observed_residue"]:
        reject("refutation-values-invalid")
    for name in ("pressure_program_digest", "productivity_evidence_digest",
                 "coherence_evidence_digest", "refutation_digest"):
        exact_digest(raw[name], name)
    logger.debug("_refutation exit")


def validate_offset_refutation_result(raw_package, raw_pressure_program, depth: int, value):
    """Reject hostile refutations, then replay formal pressure and mismatch."""
    logger.debug("validate_offset_refutation_result entry")
    if type(value) is BridgeRefutation:
        _refutation(value)
    elif type(value) is BridgeResourceLimit:
        _resource(value)
    elif type(value) is BridgeFormalFailure:
        _failure(value)
    else:
        reject("refutation-result-variant-invalid")
    expected = refute_offset_program(raw_package, raw_pressure_program, depth)
    if type(value) is not type(expected) or value != expected:
        reject("refutation-result-replay-mismatch")
    logger.debug("validate_offset_refutation_result exit")
    return expected


def _open(value: BridgeOpen) -> None:
    """Validate a proof-free missing-evidence envelope before replay."""
    logger.debug("_open entry")
    raw = exact_shape(value, BridgeOpen, "bridge-open")
    if type(raw["status"]) is not ResultStatus or raw["status"] is not ResultStatus.OPEN:
        reject("open-status-invalid")
    if type(raw["reason"]) is not str or raw["reason"] != "missing-admissible-bridge-evidence":
        reject("open-reason-invalid")
    for name in ("prime_digest", "integer_digest", "program_digest", "open_digest"):
        exact_digest(raw[name], name)
    logger.debug("_open exit")


def validate_open_result(prime, integer, program, value):
    """Reject hostile OPEN values and reconstruct the same admissible absence."""
    logger.debug("validate_open_result entry")
    _open(value)
    expected = report_missing_bridge_evidence(prime, integer, program)
    if type(expected) is not BridgeOpen or value != expected:
        reject("open-result-replay-mismatch")
    logger.debug("validate_open_result exit")
    return expected
