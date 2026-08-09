"""Hostile outer-envelope-first independent P3-N1 result replay."""

from __future__ import annotations

import logging

from .common import exact_digest, exact_shape, reject
from .package import HARD_SOURCE_BYTES, HARD_STATIC_COST
from .runtime import _judge
from .sources import AXIOM_CLOSURE, THEOREM_IDS
from .types import (
    N1EvidenceProvenance, N1EvidenceStatus, N1ExecutionFailureKind, N1FamilyJudgment,
    N1FailedBound, N1FormalFailure, N1IntroductionPackage, N1JudgmentKind,
    N1_NONCLAIMS, N1ResourceLimit, N1Result, N1ResultStatus,
)

logger = logging.getLogger(__name__)


def _tuple(value: object, expected: tuple[str, ...], label: str) -> None:
    """Require exact tuple/type/value without invoking hostile equality first."""
    logger.debug("_tuple entry label=%s", label)
    if type(value) is not tuple or len(value) != len(expected) or any(type(x) is not str for x in value):
        reject(f"{label}-shape-invalid")
    if value != expected:
        reject(f"{label}-value-invalid")
    logger.debug("_tuple exit label=%s", label)


def _digests(value: object, names: tuple[str, ...]) -> None:
    """Validate top-level digest syntax before nested replay/equality."""
    logger.debug("_digests entry count=%d", len(names))
    try:
        for name in names:
            exact_digest(getattr(value, name), name)
    except AttributeError:
        reject("n1-result-missing-digest")
    logger.debug("_digests exit")


def _positive(value: N1FamilyJudgment) -> None:
    """Precheck every positive lane and permanent nonclaim before semantics."""
    logger.debug("_positive entry")
    exact_shape(value, N1FamilyJudgment, "n1-family-judgment")
    if type(value.kind) is not N1JudgmentKind or value.kind is not N1JudgmentKind.ALL_DEPTH_FAMILY:
        reject("n1-result-kind-invalid")
    if type(value.status) is not N1EvidenceStatus or value.status is not N1EvidenceStatus.ESTABLISHED:
        reject("n1-result-status-invalid")
    if type(value.provenance) is not N1EvidenceProvenance or value.provenance is not N1EvidenceProvenance.FORMALLY_DERIVED:
        reject("n1-result-provenance-invalid")
    if type(value.coordinate_totality) is not N1EvidenceStatus or type(value.all_reductions_compatible) is not N1EvidenceStatus:
        reject("n1-result-law-status-invalid")
    _digests(value, (
        "prime_digest", "integer_digest", "doctrine_digest", "theorem_source_digest",
        "ledger_digest", "package_digest", "run_digest", "family_term_digest",
        "introduction_evidence_digest", "judgment_digest",
    ))
    _tuple(value.theorem_ids, THEOREM_IDS, "n1-result-theorems")
    _tuple(value.theorem_axiom_closure, AXIOM_CLOSURE, "n1-result-axioms")
    _tuple(value.nonclaims, N1_NONCLAIMS, "n1-result-nonclaims")
    if len({value.theorem_source_digest, value.family_term_digest,
            value.introduction_evidence_digest, value.judgment_digest}) != 4:
        reject("n1-result-distinct-digests-required")
    logger.debug("_positive exit")


def _resource(value: N1ResourceLimit) -> None:
    """Precheck a payload-free first-bound resource refusal."""
    logger.debug("_resource entry")
    exact_shape(value, N1ResourceLimit, "n1-resource-limit")
    if type(value.status) is not N1ResultStatus or type(value.failed_bound) is not N1FailedBound:
        reject("n1-resource-enum-invalid")
    if type(value.required_value) is not int or type(value.allowed_value) is not int:
        reject("n1-resource-value-type-invalid")
    if value.required_value <= value.allowed_value or value.allowed_value < 1:
        reject("n1-resource-value-invalid")
    maximum = HARD_SOURCE_BYTES if value.failed_bound is N1FailedBound.CAPTURED_BYTES else HARD_STATIC_COST
    if value.required_value > maximum or value.allowed_value > maximum:
        reject("n1-resource-value-exceeds-hard-limit")
    _digests(value, ("package_digest", "policy_digest", "run_digest", "refusal_digest"))
    _tuple(value.nonclaims, N1_NONCLAIMS, "n1-resource-nonclaims")
    logger.debug("_resource exit")


def _failure(value: N1FormalFailure) -> None:
    """Precheck sanitized operational evidence with no mathematical status."""
    logger.debug("_failure entry")
    exact_shape(value, N1FormalFailure, "n1-formal-failure")
    if type(value.kind) is not N1ExecutionFailureKind or type(value.diagnostic) is not str:
        reject("n1-failure-scalar-invalid")
    if value.diagnostic != f"formal execution {value.kind.value}" or len(value.diagnostic.encode()) > 128:
        reject("n1-failure-diagnostic-invalid")
    _digests(value, ("package_digest", "policy_digest", "run_digest", "attempt_digest"))
    _tuple(value.nonclaims, N1_NONCLAIMS, "n1-failure-nonclaims")
    logger.debug("_failure exit")


def validate_n1_result(raw_package: N1IntroductionPackage, value: N1Result) -> N1Result:
    """Freshly replay one exact result only after safe outer validation."""
    logger.debug("validate_n1_result entry type=%s", type(value).__name__)
    if type(value) is N1FamilyJudgment:
        _positive(value)
    elif type(value) is N1ResourceLimit:
        _resource(value)
    elif type(value) is N1FormalFailure:
        _failure(value)
    else:
        reject("n1-result-variant-invalid")
    expected = _judge(raw_package)
    if type(value) is not type(expected) or value != expected:
        reject("n1-result-replay-mismatch")
    logger.debug("validate_n1_result exit")
    return expected
