"""Evidence-backed bounded-coordinate OPEN/REFUTED runtime for P3-N4."""

from __future__ import annotations

import logging

from ..completion.package import snapshot_package as snapshot_p2
from ..family_introduction.package import snapshot_package as snapshot_n1
from .types import (
    BoundedCoordinateEqualitySource, BoundedCoordinateRow, BoundedEqualityRequest,
    BoundedEqualityResult,
)
from .common import digest, exact_digest, exact_shape, reject
from .sources import VERSION, _family_digest, policy
from .types import (
    EqualityStatus, FailedBound, N34Open, N34Policy, N34Refuted,
    N34ResourceLimit, N34Status,
)

logger = logging.getLogger(__name__)
MAX_BOUNDED_DEPTH = 1024
_POLICY_FIELDS = ("max_captured_bytes", "max_static_cost", "max_ledger_rows",
                  "max_ledger_edges", "timeout_seconds", "max_output_bytes")


def _exact_policy(value: N34Policy | None) -> N34Policy:
    """Rebuild one exact bounded-run policy."""
    logger.debug("_exact_policy entry")
    if value is None:
        result = policy()
    else:
        raw = exact_shape(value, N34Policy, "bounded-policy")
        result = policy(*(raw[name] for name in _POLICY_FIELDS))
        if value != result:
            reject("bounded-policy-drift")
    logger.debug("_exact_policy exit")
    return result


def _row(p: int, left_z: int, right_z: int, depth: int) -> BoundedCoordinateRow:
    """Derive one exact finite coordinate comparison row."""
    logger.debug("_row entry depth=%d", depth)
    modulus = p ** (depth + 1)
    left, right = left_z % modulus, right_z % modulus
    value = digest("veyra.p3n4.bounded-row.v1", (
        ("depth", depth.to_bytes(4, "big")), ("modulus", str(modulus).encode()),
        ("left", str(left).encode()), ("right", str(right).encode())))
    result = BoundedCoordinateRow(depth, modulus, left, right, value)
    logger.debug("_row exit equal=%s", left == right)
    return result


def bounded_coordinate_equality_source(left_n1, right_n1, pomega2,
                                       depth: int) -> BoundedCoordinateEqualitySource:
    """Capture exact coordinate values at every index ``0..depth``."""
    logger.debug("bounded_coordinate_equality_source entry depth=%r", depth)
    if type(depth) is not int or not 0 <= depth <= MAX_BOUNDED_DEPTH:
        reject("bounded-depth-invalid")
    left, right, p2 = snapshot_n1(left_n1), snapshot_n1(right_n1), snapshot_p2(pomega2)
    if left.prime != p2.prime or right.prime != p2.prime:
        reject("bounded-package-endpoint-mismatch")
    rows = tuple(_row(p2.prime.p, left.integer.z, right.integer.z, n)
                 for n in range(depth + 1))
    left_family, right_family = _family_digest(left), _family_digest(right)
    value = digest("veyra.p3n4.bounded-source.v1", (
        ("depth", depth.to_bytes(4, "big")), ("p2", p2.package_digest.encode()),
        ("left-family", left_family.encode()), ("right-family", right_family.encode()),
        *((f"row-{i}", row.row_digest.encode()) for i, row in enumerate(rows))))
    result = BoundedCoordinateEqualitySource(VERSION, depth, p2.package_digest,
        left_family, right_family, rows, value)
    logger.debug("bounded_coordinate_equality_source exit rows=%d", len(rows))
    return result


def bounded_equality_request(left_n1, right_n1, pomega2,
                             source: BoundedCoordinateEqualitySource,
                             execution_policy: N34Policy | None = None
                             ) -> BoundedEqualityRequest:
    """Build one exact bounded comparison request with owned evidence."""
    logger.debug("bounded_equality_request entry")
    left, right, p2 = snapshot_n1(left_n1), snapshot_n1(right_n1), snapshot_p2(pomega2)
    exact_shape(source, BoundedCoordinateEqualitySource, "bounded-source")
    if source != bounded_coordinate_equality_source(left, right, p2, source.depth):
        reject("bounded-source-drift-or-transplant")
    execution_policy = _exact_policy(execution_policy)
    value = digest("veyra.p3n4.bounded-request.v1", (
        ("left", left.package_digest.encode()), ("right", right.package_digest.encode()),
        ("p2", p2.package_digest.encode()), ("source", source.source_digest.encode()),
        ("policy", execution_policy.policy_digest.encode())))
    result = BoundedEqualityRequest(left, right, p2, source, execution_policy, value)
    logger.debug("bounded_equality_request exit")
    return result


def _raw_preflight(value: BoundedEqualityRequest) -> tuple[dict[str, object], tuple | None]:
    """Inspect only the bounded outer envelope and charge before semantic replay."""
    logger.debug("_raw_preflight entry")
    raw = exact_shape(value, BoundedEqualityRequest, "bounded-request")
    source = exact_shape(raw["source"], BoundedCoordinateEqualitySource, "bounded-source")
    execution = _exact_policy(raw["policy"])
    exact_digest(raw["request_digest"], "bounded-request-digest")
    rows, depth = source["rows"], source["depth"]
    if type(rows) is not tuple or type(depth) is not int or depth < 0:
        reject("bounded-source-envelope-invalid")
    required_rows = depth + 1
    static = 1024 + 256 * required_rows
    failure = None
    if depth > MAX_BOUNDED_DEPTH or len(rows) != required_rows:
        failure = (FailedBound.STATIC_COST, static, execution.max_static_cost)
    elif static > execution.max_static_cost:
        failure = (FailedBound.STATIC_COST, static, execution.max_static_cost)
    logger.debug("_raw_preflight exit failure=%s", failure is not None)
    return raw, failure


def _resource(request_digest: str, failure: tuple) -> N34ResourceLimit:
    """Construct one first-bound bounded refusal."""
    logger.debug("_resource entry")
    kind, required, allowed = failure
    value = digest("veyra.p3n3n4.resource.v1", (("request", request_digest.encode()),
        ("bound", kind.value.encode()), ("required", str(required).encode()),
        ("allowed", str(allowed).encode())))
    result = N34ResourceLimit(N34Status.RESOURCE_LIMIT, kind, required, allowed,
                              request_digest, value)
    logger.debug("_resource exit")
    return result


def bounded_coordinate_equality_judgment(raw_request: BoundedEqualityRequest
                                         ) -> BoundedEqualityResult:
    """Freshly replay all coordinates; mismatch is REFUTED, agreement stays OPEN."""
    logger.debug("bounded_coordinate_equality_judgment entry")
    raw, failure = _raw_preflight(raw_request)
    request_digest = raw["request_digest"]
    if failure is not None:
        return _resource(request_digest, failure)
    source = raw["source"]
    request = bounded_equality_request(raw["left_n1"], raw["right_n1"], raw["pomega2"],
                                       source, raw["policy"])
    for row in request.source.rows:
        expected = _row(request.pomega2.prime.p, request.left_n1.integer.z,
                        request.right_n1.integer.z, row.depth)
        if row != expected:
            reject("bounded-row-replay-drift")
        if row.left_residue != row.right_residue:
            reason = f"bounded-coordinate-mismatch-at-depth-{row.depth}"
            value = digest("veyra.p3n3n4.refuted.v1", (("request", request.request_digest.encode()),
                ("reason", reason.encode())))
            logger.debug("bounded_coordinate_equality_judgment exit refuted")
            return N34Refuted(N34Status.REFUTED, reason, request.request_digest, value)
    reason = "exact-finite-coordinate-agreement-is-not-all-depth-evidence"
    value = digest("veyra.p3n4.open.v1", (("request", request.request_digest.encode()),
        ("reason", reason.encode())))
    result = N34Open(N34Status.OPEN, EqualityStatus.NOT_ESTABLISHED,
                     reason, request.request_digest, value)
    logger.debug("bounded_coordinate_equality_judgment exit open")
    return result


def validate_bounded_result(request: BoundedEqualityRequest,
                            value: BoundedEqualityResult) -> BoundedEqualityResult:
    """Bound the result envelope, then require an equal-but-distinct fresh replay."""
    logger.debug("validate_bounded_result entry")
    if type(value) is N34Open:
        raw = exact_shape(value, N34Open, "bounded-open")
        if raw["status"] is not N34Status.OPEN or raw["equality_status"] is not EqualityStatus.NOT_ESTABLISHED:
            reject("bounded-open-status-invalid")
        if type(raw["reason"]) is not str or not 1 <= len(raw["reason"]) <= 128:
            reject("bounded-open-reason-invalid")
        exact_digest(raw["request_digest"], "bounded-open-request")
        exact_digest(raw["open_digest"], "bounded-open-digest")
    elif type(value) is N34Refuted:
        raw = exact_shape(value, N34Refuted, "bounded-refuted")
        if (raw["status"] is not N34Status.REFUTED or type(raw["reason"]) is not str
                or not 1 <= len(raw["reason"]) <= 128):
            reject("bounded-refuted-envelope-invalid")
        exact_digest(raw["request_digest"], "bounded-refuted-request")
        exact_digest(raw["refutation_digest"], "bounded-refuted-digest")
    elif type(value) is N34ResourceLimit:
        raw = exact_shape(value, N34ResourceLimit, "bounded-resource")
        if (raw["status"] is not N34Status.RESOURCE_LIMIT
                or type(raw["failed_bound"]) is not FailedBound
                or type(raw["required"]) is not int or type(raw["allowed"]) is not int
                or not 0 <= raw["allowed"] < raw["required"] <= 16 * 1024 * 1024):
            reject("bounded-resource-status-invalid")
        exact_digest(raw["request_digest"], "bounded-resource-request")
        exact_digest(raw["refusal_digest"], "bounded-resource-digest")
    else:
        reject("bounded-result-union-arm-invalid")
    expected = bounded_coordinate_equality_judgment(request)
    if value != expected or value is expected:
        reject("bounded-result-replay-mismatch")
    logger.debug("validate_bounded_result exit")
    return expected
