"""Hostile outer-shape-first independent result replay for PΩ1."""

from __future__ import annotations

from dataclasses import fields
import logging

from .common import exact_digest, exact_shape, reject
from .package import HARD_SOURCE_BYTES, HARD_STATIC_COST
from .runtime import _judge
from .types import (
    CompletedCarrierStatus, CompletionFailedBound, CompletionObligationStatuses,
    CompletionResultStatus, FormalExecutionFailure, FormalExecutionFailureKind,
    MetaphysicalTotalityStatus, ObligationStatus, POMEGA1_NONCLAIMS,
    PhysicalInstantiationStatus, StreamCompletionJudgment, StreamCompletionPackage,
    StreamCompletionResourceLimit, StreamCompletionResult,
)

logger = logging.getLogger(__name__)


def _exact_tuple(value: object, length: int, member: type, label: str) -> None:
    """Reject tuple subclasses and hostile members before hashing/equality."""
    logger.debug("_exact_tuple entry label=%s", label)
    if type(value) is not tuple or len(value) != length or any(type(x) is not member for x in value):
        reject(f"{label}-invalid")
    logger.debug("_exact_tuple exit label=%s", label)


def _exact_digests(value: object, names: tuple[str, ...]) -> None:
    """Check selected top-level provenance digests without nested traversal."""
    logger.debug("_exact_digests entry count=%d", len(names))
    try:
        for name in names:
            exact_digest(getattr(value, name), name.replace("_", "-"))
    except AttributeError:
        reject("stream-result-missing-digest")
    logger.debug("_exact_digests exit")


def _validate_obligations(value: object) -> None:
    """Require exact DTO shape and exactly eleven ESTABLISHED enum members."""
    logger.debug("_validate_obligations entry")
    exact_shape(value, CompletionObligationStatuses, "completion-obligations")
    try:
        statuses = tuple(getattr(value, field.name) for field in fields(CompletionObligationStatuses))
    except AttributeError:
        reject("completion-obligations-missing-fields")
    if len(statuses) != 11 or any(type(status) is not ObligationStatus for status in statuses):
        reject("completion-obligation-status-invalid")
    logger.debug("_validate_obligations exit")


def _outer_positive(value: StreamCompletionJudgment) -> None:
    """Precheck all positive scalar/container lanes before replay or equality."""
    logger.debug("_outer_positive entry")
    exact_shape(value, StreamCompletionJudgment, "stream-completion-judgment")
    _exact_digests(value, (
        "doctrine_digest", "alphabet_digest", "presentation_digest",
        "theorem_source_digest", "ledger_digest", "package_digest",
        "policy_digest", "run_digest", "judgment_digest",
    ))
    _exact_tuple(value.theorem_ids, 15, str, "judgment-theorem-ids")
    _exact_tuple(value.theorem_axiom_closure, 1, str, "judgment-axiom-closure")
    _exact_tuple(value.nonclaims, len(POMEGA1_NONCLAIMS), str, "judgment-nonclaims")
    _validate_obligations(value.obligations)
    enums = (
        (value.formal_carrier_presentation, ObligationStatus),
        (value.universal_realization, ObligationStatus),
        (value.joint_separation, ObligationStatus),
        (value.completed_carrier, CompletedCarrierStatus),
        (value.physical_instantiation, PhysicalInstantiationStatus),
        (value.observer_independent_metaphysical_totality, MetaphysicalTotalityStatus),
    )
    if any(type(item) is not cls for item, cls in enums):
        reject("judgment-status-type-invalid")
    logger.debug("_outer_positive exit")


def _outer_refusal(value: StreamCompletionResourceLimit) -> None:
    """Precheck small bound values before any supplied digest comparison."""
    logger.debug("_outer_refusal entry")
    exact_shape(value, StreamCompletionResourceLimit, "stream-completion-refusal")
    if type(value.status) is not CompletionResultStatus or type(value.failed_bound) is not CompletionFailedBound:
        reject("stream-refusal-status-invalid")
    if type(value.required_value) is not int or type(value.allowed_value) is not int:
        reject("stream-refusal-bound-type-invalid")
    if value.required_value < 1 or value.allowed_value < 1 or value.required_value <= value.allowed_value:
        reject("stream-refusal-bound-value-invalid")
    maximum = (
        HARD_SOURCE_BYTES
        if value.failed_bound is CompletionFailedBound.CAPTURED_BYTES
        else HARD_STATIC_COST
    )
    if value.required_value > maximum or value.allowed_value > maximum:
        reject("stream-refusal-bound-maximum-invalid")
    _exact_tuple(value.nonclaims, len(POMEGA1_NONCLAIMS), str, "refusal-nonclaims")
    _exact_digests(value, ("package_digest", "policy_digest", "run_digest", "refusal_digest"))
    logger.debug("_outer_refusal exit")


def _outer_execution(value: FormalExecutionFailure) -> None:
    """Precheck operational failure provenance and forbid proof payloads."""
    logger.debug("_outer_execution entry")
    exact_shape(value, FormalExecutionFailure, "formal-execution-failure")
    if type(value.kind) is not FormalExecutionFailureKind or type(value.diagnostic) is not str:
        reject("formal-execution-failure-scalar-invalid")
    try:
        diagnostic = value.diagnostic.encode("utf-8", errors="strict")
    except UnicodeError:
        reject("formal-execution-diagnostic-invalid-utf8")
    if len(diagnostic) > 256:
        reject("formal-execution-diagnostic-too-large")
    if value.diagnostic != f"formal execution {value.kind.value}":
        reject("formal-execution-diagnostic-drift")
    enums = (
        (value.physical_instantiation, PhysicalInstantiationStatus),
        (value.observer_independent_metaphysical_totality, MetaphysicalTotalityStatus),
    )
    if any(type(item) is not cls for item, cls in enums):
        reject("formal-execution-nonclaim-status-invalid")
    _exact_tuple(value.nonclaims, len(POMEGA1_NONCLAIMS), str, "execution-nonclaims")
    _exact_digests(value, ("package_digest", "policy_digest", "run_digest", "attempt_digest"))
    logger.debug("_outer_execution exit")


def validate_stream_completion_result(
    raw_package: StreamCompletionPackage, result: StreamCompletionResult,
) -> StreamCompletionResult:
    """Derive one fresh variant, then compare every exact field and commitment."""
    logger.debug("validate_stream_completion_result entry type=%s", type(result).__name__)
    if type(result) is StreamCompletionJudgment:
        _outer_positive(result)
    elif type(result) is StreamCompletionResourceLimit:
        _outer_refusal(result)
    elif type(result) is FormalExecutionFailure:
        _outer_execution(result)
    else:
        reject("stream-result-variant-invalid")
    expected = _judge(raw_package)
    if type(result) is not type(expected) or result != expected:
        reject("stream-result-replay-mismatch")
    logger.debug("validate_stream_completion_result exit")
    return expected
