"""Hostile-safe internal request construction for one P3-N6-W finite depth."""

from __future__ import annotations

import logging
from typing import cast

from ...padic.completion.types import PadicCompletionPackage, PrimeSource
from ...padic.family_introduction.types import N1IntroductionPackage
from .sources import (
    policy,
    snapshot_policy,
    snapshot_theorem_source,
    theorem_source,
)
from .types import (
    N6WPolicyV1,
    N6WTheoremSourceV1,
    N6WWitnessRequestV1,
    N6W_REQUEST_LAYOUT,
)
from ...prime_power_unbounded_common import (
    digest,
    exact_digest,
    exact_nonnegative_int,
    exact_shape,
    freeze_layout,
    reject,
)
from ...prime_power_unbounded_requests import snapshot_w_request, w_request
from ...prime_power_unbounded_sources import policy as n6_policy
from ...prime_power_unbounded_types import N6_W_REQUEST_LAYOUT

logger = logging.getLogger(__name__)

_P2_LAYOUT = freeze_layout(PadicCompletionPackage, (
    "prime", "doctrine", "theorem_source", "ledger", "policy", "package_digest",
))
_PRIME_LAYOUT = freeze_layout(PrimeSource, (
    "version", "p", "witness_algorithm_id", "generated_witness_bytes",
    "generated_witness_sha256", "source_digest",
))


def _digest(
    base_digest: str,
    k: int,
    source_digest: str,
    policy_digest: str,
) -> str:
    """Bind one finite request without accepting any prior result identity."""
    logger.debug("_digest entry k=%d", k)
    result = digest("veyra.p3n6w.request.v1", (
        ("base-request", base_digest.encode()),
        ("k", k.to_bytes(8, "big")),
        ("witness-source", source_digest.encode()),
        ("policy", policy_digest.encode()),
    ))
    logger.debug("_digest exit")
    return cast(str, result)


def witness_request(
    n1_zero: N1IntroductionPackage,
    pomega2: PadicCompletionPackage,
    k: int,
    source: N6WTheoremSourceV1 | None = None,
    run_policy: N6WPolicyV1 | None = None,
    *,
    supplied_result: object | None = None,
) -> N6WWitnessRequestV1:
    """Build one internal request; a supplied N6-W result is always forbidden."""
    logger.debug("witness_request entry k_type=%s", type(k).__name__)
    if supplied_result is not None:
        logger.error("witness_request supplied result rejected")
        reject("n6w-supplied-result-forbidden")
    checked_k = exact_nonnegative_int(k, "n6w-request-k", maximum=2**63 - 1)
    selected_source = theorem_source() if source is None else snapshot_theorem_source(source)
    selected_policy = policy() if run_policy is None else snapshot_policy(run_policy)
    logger.debug("witness_request external-call=w_request state=begin")
    base = w_request(n1_zero, pomega2, None, None, n6_policy())
    logger.debug("witness_request external-call=w_request state=end")
    if base.completed_infinity is not None:
        reject("n6w-base-completed-infinity-forbidden")
    request_digest = _digest(
        base.request_digest, checked_k, selected_source.source_digest,
        selected_policy.policy_digest,
    )
    result = N6WWitnessRequestV1(
        base, checked_k, selected_source, selected_policy, request_digest,
    )
    logger.debug("witness_request exit k=%d", checked_k)
    return result


def snapshot_request(value: N6WWitnessRequestV1) -> N6WWitnessRequestV1:
    """Freshly replay every nested package/source and the exact request digest."""
    logger.debug("snapshot_request entry")
    raw = exact_shape(value, N6W_REQUEST_LAYOUT, "n6w-request")
    checked_k = exact_nonnegative_int(raw["k"], "n6w-request-k", maximum=2**63 - 1)
    logger.debug("snapshot_request external-call=snapshot_w_request state=begin")
    base = snapshot_w_request(raw["base_request"])
    logger.debug("snapshot_request external-call=snapshot_w_request state=end")
    if base.completed_infinity is not None:
        reject("n6w-base-completed-infinity-forbidden")
    source = snapshot_theorem_source(cast(N6WTheoremSourceV1, raw["theorem"]))
    run_policy = snapshot_policy(cast(N6WPolicyV1, raw["policy"]))
    expected_digest = _digest(
        base.request_digest, checked_k, source.source_digest, run_policy.policy_digest,
    )
    if type(raw["request_digest"]) is not str or raw["request_digest"] != expected_digest:
        reject("n6w-request-digest-drift")
    result = N6WWitnessRequestV1(
        base, checked_k, source, run_policy, expected_digest,
    )
    logger.debug("snapshot_request exit k=%d", checked_k)
    return result


def shallow_request_values(
    value: N6WWitnessRequestV1,
) -> tuple[str, int, int, N6WPolicyV1]:
    """Read frozen scalar envelopes needed for refusal before deep replay."""
    logger.debug("shallow_request_values entry")
    raw = exact_shape(value, N6W_REQUEST_LAYOUT, "n6w-shallow-request")
    request_digest = exact_digest(raw["request_digest"], "n6w-shallow-request-digest")
    k = exact_nonnegative_int(raw["k"], "n6w-shallow-k", maximum=2**63 - 1)
    run_policy = snapshot_policy(cast(N6WPolicyV1, raw["policy"]))
    base = exact_shape(raw["base_request"], N6_W_REQUEST_LAYOUT, "n6w-shallow-base")
    if base["completed_infinity"] is not None:
        reject("n6w-shallow-completed-infinity-forbidden")
    pomega2 = exact_shape(base["pomega2"], _P2_LAYOUT, "n6w-shallow-pomega2")
    prime = exact_shape(pomega2["prime"], _PRIME_LAYOUT, "n6w-shallow-prime")
    p = exact_nonnegative_int(prime["p"], "n6w-shallow-p", maximum=65_521)
    result = request_digest, k, p, run_policy
    logger.debug("shallow_request_values exit k=%d p=%d", k, p)
    return result
