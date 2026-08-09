"""Hostile-safe raw request builders for P3-N3/N4."""

from __future__ import annotations

import logging

from ..completion.package import snapshot_package as snapshot_p2
from ..family_introduction.package import snapshot_package as snapshot_n1
from .common import digest, exact_shape, reject
from .sources import all_depth_source, policy, theorem_source
from .types import (
    AllDepthCoordinateEqualitySource, N34Policy, N34TheoremSource, N3Request,
    N4Request,
)

logger = logging.getLogger(__name__)
_POLICY_FIELDS = ("max_captured_bytes", "max_static_cost", "max_ledger_rows",
                  "max_ledger_edges", "timeout_seconds", "max_output_bytes")


def _policy(value: N34Policy | None) -> N34Policy:
    """Reconstruct one exact policy without hostile attribute dispatch."""
    logger.debug("_policy entry")
    if value is None:
        result = policy()
    else:
        raw = exact_shape(value, N34Policy, "n34-policy")
        values = tuple(raw[name] for name in _POLICY_FIELDS)
        result = policy(*values)
        if value != result:
            reject("n34-policy-drift")
    logger.debug("_policy exit")
    return result


def _theorem(value: N34TheoremSource | None) -> N34TheoremSource:
    """Reconstruct the sole exact theorem source."""
    logger.debug("_theorem entry")
    result = theorem_source()
    if value is not None:
        exact_shape(value, N34TheoremSource, "n34-theorem-source")
        if value != result:
            reject("n34-theorem-source-drift")
    logger.debug("_theorem exit")
    return result


def n3_request(n1, pomega2, theorem: N34TheoremSource | None = None,
               execution_policy: N34Policy | None = None) -> N3Request:
    """Build one source-only N3 request."""
    logger.debug("n3_request entry")
    n1, pomega2 = snapshot_n1(n1), snapshot_p2(pomega2)
    theorem, execution_policy = _theorem(theorem), _policy(execution_policy)
    value = digest("veyra.p3n3.request.v1", (("n1", n1.package_digest.encode()),
        ("p2", pomega2.package_digest.encode()), ("theorem", theorem.source_digest.encode()),
        ("policy", execution_policy.policy_digest.encode())))
    result = N3Request(n1, pomega2, theorem, execution_policy, value)
    logger.debug("n3_request exit")
    return result


def n4_request(left, right, pomega2, premise, theorem: N34TheoremSource | None = None,
               execution_policy: N34Policy | None = None) -> N4Request:
    """Build one source-only N4 request without accepting N3 judgments."""
    logger.debug("n4_request entry")
    left, right, pomega2 = snapshot_n1(left), snapshot_n1(right), snapshot_p2(pomega2)
    theorem, execution_policy = _theorem(theorem), _policy(execution_policy)
    exact_shape(premise, AllDepthCoordinateEqualitySource, "all-depth-source")
    if premise != all_depth_source(left, right, pomega2):
        reject("all-depth-source-drift-or-transplant")
    value = digest("veyra.p3n4.request.v1", (("left", left.package_digest.encode()),
        ("right", right.package_digest.encode()), ("p2", pomega2.package_digest.encode()),
        ("theorem", theorem.source_digest.encode()), ("premise", premise.source_digest.encode()),
        ("policy", execution_policy.policy_digest.encode())))
    result = N4Request(left, right, pomega2, theorem, premise, execution_policy, value)
    logger.debug("n4_request exit")
    return result
