"""Fresh hostile-safe result validation for P3-N3/N4."""

from __future__ import annotations

import logging

from .common import exact_digest, exact_shape, reject
from .sources import THEOREM_IDS
from .runtime import (
    local_realization_judgment, scoped_carrier_equality_judgment,
)
from .types import (
    EqualityStatus, FailedBound, FormalFailureKind, N34FormalFailure, N34Open,
    N34Refuted, N34ResourceLimit, N34Status, N3Kind, N3RealizationJudgment,
    N3Request, N3Result, N34_NONCLAIMS, N4EqualityJudgment, N4Kind, N4Request,
    N4Result,
)

logger = logging.getLogger(__name__)


def _digests(raw: dict[str, object], names: tuple[str, ...]) -> None:
    """Validate an exact set of digest fields."""
    logger.debug("_digests entry count=%d", len(names))
    for name in names:
        exact_digest(raw.get(name), name)
    logger.debug("_digests exit")


def _n3_shape(value: N3Result) -> None:
    """Validate the closed N3 result union before fresh replay."""
    logger.debug("_n3_shape entry type=%s", type(value).__name__)
    if type(value) is N3RealizationJudgment:
        raw = exact_shape(value, N3RealizationJudgment, "n3-judgment")
        if (raw["status"] is not N34Status.ESTABLISHED
                or raw["kind"] is not N3Kind.LOCAL_REALIZATION_ESTABLISHED_RELATIVE_TO_EXACT_POMEGA2
                or type(raw["promotions"]) is not int or raw["promotions"] != 0):
            reject("n3-positive-status-or-promotion-invalid")
        theorem_ids, closure, nonclaims = (raw["theorem_ids"],
                                           raw["theorem_axiom_closure"], raw["nonclaims"])
        if (type(theorem_ids) is not tuple or len(theorem_ids) != 2
                or type(closure) is not tuple or len(closure) > 4
                or type(nonclaims) is not tuple or len(nonclaims) > 16):
            reject("n3-theorem-containers-invalid")
        if theorem_ids != THEOREM_IDS[:2] or closure != ("propext",) or nonclaims != N34_NONCLAIMS:
            reject("n3-positive-exact-vocabulary-invalid")
        _digests(raw, ("n1_package_digest", "pomega2_package_digest",
            "theorem_source_digest", "bridge_ledger_digest", "family_term_digest",
            "introduction_evidence_digest", "realized_term_digest",
            "coordinate_evidence_digest", "judgment_digest"))
    elif type(value) is N34ResourceLimit:
        raw = exact_shape(value, N34ResourceLimit, "n34-resource")
        if raw["status"] is not N34Status.RESOURCE_LIMIT:
            reject("n34-resource-status-invalid")
        if (type(raw["failed_bound"]) is not FailedBound
                or type(raw["required"]) is not int or type(raw["allowed"]) is not int
                or not 0 <= raw["allowed"] < raw["required"] <= 16 * 1024 * 1024):
            reject("n34-resource-envelope-invalid")
        _digests(raw, ("request_digest", "refusal_digest"))
    elif type(value) is N34Refuted:
        raw = exact_shape(value, N34Refuted, "n34-refuted")
        if raw["status"] is not N34Status.REFUTED:
            reject("n34-refuted-status-invalid")
        if type(raw["reason"]) is not str or not 1 <= len(raw["reason"]) <= 128:
            reject("n34-refuted-reason-invalid")
        _digests(raw, ("request_digest", "refutation_digest"))
    elif type(value) is N34FormalFailure:
        raw = exact_shape(value, N34FormalFailure, "n34-formal-failure")
        if (type(raw["kind"]) is not FormalFailureKind or type(raw["diagnostic"]) is not str
                or not 1 <= len(raw["diagnostic"]) <= 512):
            reject("n34-formal-failure-envelope-invalid")
        _digests(raw, ("request_digest", "attempt_digest"))
    else:
        reject("n3-result-union-arm-invalid")
    logger.debug("_n3_shape exit")


def _n4_shape(value: N4Result) -> None:
    """Validate the closed N4 result union before fresh replay."""
    logger.debug("_n4_shape entry type=%s", type(value).__name__)
    if type(value) is N4EqualityJudgment:
        raw = exact_shape(value, N4EqualityJudgment, "n4-judgment")
        if (raw["status"] is not N34Status.ESTABLISHED
                or raw["kind"] is not N4Kind.SCOPED_CARRIER_EQUALITY_ESTABLISHED_RELATIVE_TO_LEDGER
                or raw["equality_status"] is not EqualityStatus.ESTABLISHED_RELATIVE_TO_LEDGER
                or type(raw["promotions"]) is not int or raw["promotions"] != 0
                or type(raw["nonclaims"]) is not tuple or len(raw["nonclaims"]) > 16
                or raw["nonclaims"] != N34_NONCLAIMS):
            reject("n4-positive-status-or-promotion-invalid")
        _digests(raw, ("left_realized_term_digest", "right_realized_term_digest",
            "all_depth_source_digest", "theorem_source_digest", "bridge_ledger_digest",
            "equality_evidence_digest", "judgment_digest"))
    elif type(value) is N34Open:
        raw = exact_shape(value, N34Open, "n34-open")
        if (raw["status"] is not N34Status.OPEN
                or raw["equality_status"] is not EqualityStatus.NOT_ESTABLISHED):
            reject("n34-open-status-invalid")
        if type(raw["reason"]) is not str or not 1 <= len(raw["reason"]) <= 128:
            reject("n34-open-reason-invalid")
        _digests(raw, ("request_digest", "open_digest"))
    elif type(value) is N3RealizationJudgment:
        reject("n4-result-cannot-be-n3-positive")
    elif type(value) in (N34ResourceLimit, N34Refuted, N34FormalFailure):
        _n3_shape(value)
    else:
        reject("n4-result-union-arm-invalid")
    logger.debug("_n4_shape exit")


def validate_n3_result(request: N3Request, value: N3Result) -> N3Result:
    """Require a fresh equal-but-distinct N3 replay result."""
    logger.debug("validate_n3_result entry")
    _n3_shape(value)
    expected = local_realization_judgment(request)
    if value != expected or value is expected:
        reject("n3-result-replay-mismatch")
    logger.debug("validate_n3_result exit")
    return expected


def validate_n4_result(request: N4Request, value: N4Result) -> N4Result:
    """Require a fresh equal-but-distinct N4 replay result."""
    logger.debug("validate_n4_result entry")
    _n4_shape(value)
    expected = scoped_carrier_equality_judgment(request)
    if value != expected or value is expected:
        reject("n4-result-replay-mismatch")
    logger.debug("validate_n4_result exit")
    return expected
