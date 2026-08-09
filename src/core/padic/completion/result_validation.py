"""Hostile outer-shape-first independent PΩ2 result replay."""

from __future__ import annotations

from dataclasses import fields
import logging

from .common import exact_digest, exact_shape, reject
from .package import HARD_SOURCE_BYTES, HARD_STATIC_COST
from .runtime import _judge
from .types import (
    POMEGA2_NONCLAIMS, PadicCompletedCarrierStatus, PadicCompletionJudgment,
    PadicCompletionObligations, PadicCompletionPackage, PadicCompletionResourceLimit,
    PadicCompletionResult, PadicExecutionFailureKind, PadicFailedBound,
    PadicFormalExecutionFailure, PadicNotClaimedStatus, PadicNotEstablishedStatus,
    PadicObligationStatus, PadicResultStatus,
)

logger = logging.getLogger(__name__)


def _exact_tuple(value: object, length: int, member: type, label: str) -> None:
    """Reject tuple subclasses and hostile members before replay/equality."""
    logger.debug("_exact_tuple entry label=%s", label)
    if type(value) is not tuple or len(value) != length or any(type(item) is not member for item in value):
        reject(f"{label}-invalid")
    logger.debug("_exact_tuple exit label=%s", label)


def _exact_digests(value: object, names: tuple[str, ...]) -> None:
    """Check selected top-level commitments without nested traversal."""
    logger.debug("_exact_digests entry count=%d", len(names))
    try:
        for name in names:
            exact_digest(getattr(value, name), name)
    except AttributeError:
        reject("padic-result-missing-digest")
    logger.debug("_exact_digests exit")


def _obligations(value: object) -> None:
    """Require the exact DTO and 17 exact established enum members."""
    logger.debug("_obligations entry")
    exact_shape(value, PadicCompletionObligations, "padic-obligations")
    try:
        statuses = tuple(getattr(value, row.name) for row in fields(PadicCompletionObligations))
    except AttributeError:
        reject("padic-obligations-missing-fields")
    if len(statuses) != 17 or any(type(item) is not PadicObligationStatus for item in statuses):
        reject("padic-obligation-status-invalid")
    logger.debug("_obligations exit")


def _positive(value: PadicCompletionJudgment) -> None:
    """Precheck every positive container/scalar lane before fresh semantics."""
    logger.debug("_positive entry")
    exact_shape(value, PadicCompletionJudgment, "padic-completion-judgment")
    _exact_digests(value, (
        "prime_digest", "doctrine_digest", "theorem_source_digest", "ledger_digest",
        "package_digest", "policy_digest", "run_digest", "judgment_digest",
    ))
    if type(value.canonical_ops_id) is not str or type(value.concrete_instance_id) is not str:
        reject("padic-judgment-witness-id-invalid")
    _exact_tuple(value.theorem_ids, 17, str, "padic-judgment-theorems")
    _exact_tuple(value.theorem_axiom_closure, 2, str, "padic-judgment-axioms")
    _exact_tuple(value.nonclaims, len(POMEGA2_NONCLAIMS), str, "padic-judgment-nonclaims")
    _obligations(value.obligations)
    yes = (
        value.tower_formation, value.compatible_family_class,
        value.universal_realization, value.joint_separation, value.ring_closure,
    )
    no = (
        value.categorical_inverse_limit_universal_property,
        value.equivalent_to_mathlib_padic_int, value.topological_completion,
        value.physical_instantiation,
    )
    if any(type(item) is not PadicObligationStatus for item in yes):
        reject("padic-positive-status-type-invalid")
    if type(value.completed_carrier) is not PadicCompletedCarrierStatus:
        reject("padic-completed-carrier-status-type-invalid")
    if any(type(item) is not PadicNotEstablishedStatus for item in no):
        reject("padic-nonestablished-status-type-invalid")
    if type(value.foundation_independent_actuality) is not PadicNotClaimedStatus:
        reject("padic-notclaimed-status-type-invalid")
    logger.debug("_positive exit")


def _refusal(value: PadicCompletionResourceLimit) -> None:
    """Precheck bounded refusal values before replay."""
    logger.debug("_refusal entry")
    exact_shape(value, PadicCompletionResourceLimit, "padic-resource-limit")
    if type(value.status) is not PadicResultStatus or type(value.failed_bound) is not PadicFailedBound:
        reject("padic-refusal-status-invalid")
    if type(value.required_value) is not int or type(value.allowed_value) is not int:
        reject("padic-refusal-bound-type-invalid")
    if value.required_value < 1 or value.allowed_value < 1 or value.required_value <= value.allowed_value:
        reject("padic-refusal-bound-value-invalid")
    maximum = HARD_SOURCE_BYTES if value.failed_bound is PadicFailedBound.CAPTURED_BYTES else HARD_STATIC_COST
    if value.required_value > maximum or value.allowed_value > maximum:
        reject("padic-refusal-bound-maximum-invalid")
    _exact_tuple(value.nonclaims, len(POMEGA2_NONCLAIMS), str, "padic-refusal-nonclaims")
    _exact_digests(value, ("package_digest", "policy_digest", "run_digest", "refusal_digest"))
    logger.debug("_refusal exit")


def _execution(value: PadicFormalExecutionFailure) -> None:
    """Precheck operational provenance and forbid proof/status payloads."""
    logger.debug("_execution entry")
    exact_shape(value, PadicFormalExecutionFailure, "padic-formal-execution-failure")
    if type(value.kind) is not PadicExecutionFailureKind or type(value.diagnostic) is not str:
        reject("padic-execution-scalar-invalid")
    try:
        diagnostic = value.diagnostic.encode("utf-8", errors="strict")
    except UnicodeError:
        reject("padic-execution-diagnostic-invalid-utf8")
    if len(diagnostic) > 256 or value.diagnostic != f"formal execution {value.kind.value}":
        reject("padic-execution-diagnostic-drift")
    _exact_tuple(value.nonclaims, len(POMEGA2_NONCLAIMS), str, "padic-execution-nonclaims")
    _exact_digests(value, ("package_digest", "policy_digest", "run_digest", "attempt_digest"))
    logger.debug("_execution exit")


def validate_padic_completion_result(
    raw_package: PadicCompletionPackage, value: PadicCompletionResult,
) -> PadicCompletionResult:
    """Freshly replay one exact result variant after bounded outer validation."""
    logger.debug("validate_padic_completion_result entry type=%s", type(value).__name__)
    if type(value) is PadicCompletionJudgment:
        _positive(value)
    elif type(value) is PadicCompletionResourceLimit:
        _refusal(value)
    elif type(value) is PadicFormalExecutionFailure:
        _execution(value)
    else:
        reject("padic-result-variant-invalid")
    expected = _judge(raw_package)
    if type(value) is not type(expected) or value != expected:
        reject("padic-result-replay-mismatch")
    logger.debug("validate_padic_completion_result exit")
    return expected
