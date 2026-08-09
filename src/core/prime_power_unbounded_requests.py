"""Public closed E/W request constructors for candidate P3-N6."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, cast

from .padic.completion.types import PadicCompletionPackage
from .padic.family_introduction.types import N1IntroductionPackage
from .prime_power_unbounded_common import digest, exact_digest, exact_shape, exact_text, reject, sha
from .prime_power_unbounded_dispatch import dispatch_e_request
from .prime_power_unbounded_sources import (
    policy as _policy,
    snapshot_policy as _snapshot_policy,
    snapshot_theorem_source as _snapshot_theorem_source,
    theorem_source as _theorem_source,
)
from .prime_power_unbounded_types import (
    CompletedInfinityReceiptV1, N6DiagnosticCode,
    N6ERawRequestV1, N6ERequestV1, N6FormalFailureKind, N6GoalID, N6Lane,
    N6PolicyV1, N6Status, N6TheoremSourceV1, N6WOpenReason, N6WRequestV1,
    N6_CI_RECEIPT_LAYOUT, N6_E_REQUEST_LAYOUT, N6_W_REQUEST_LAYOUT,
)

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from .prime_power_unbounded_failures import N6EResultV1, N6WResultV1


def raw_e_request(
    n1_zero: N1IntroductionPackage,
    pomega2: PadicCompletionPackage,
    theorem: N6TheoremSourceV1 | None = None,
    run_policy: N6PolicyV1 | None = None,
    *,
    supplied_request_digest: str | None = None,
) -> N6ERawRequestV1:
    """Assemble inert direct fields without defaults, recursion or hashing."""
    logger.debug("raw_e_request entry")
    result = N6ERawRequestV1(
        n1_zero, pomega2, theorem, run_policy, supplied_request_digest
    )
    logger.debug("raw_e_request state=inert-assembled")
    logger.debug("raw_e_request exit")
    return result


def e_request(
    n1_zero: N1IntroductionPackage,
    pomega2: PadicCompletionPackage,
    theorem: N6TheoremSourceV1 | None = None,
    run_policy: N6PolicyV1 | None = None,
) -> N6ERequestV1:
    """Run the sole public source-pinned E dispatcher."""
    logger.debug("e_request entry")
    result = dispatch_e_request(
        raw_e_request(n1_zero, pomega2, theorem, run_policy)
    )
    logger.debug("e_request exit")
    return result


def snapshot_e_request(value: N6ERequestV1) -> N6ERequestV1:
    """Freshly replay a deep E request through the sole dispatcher."""
    logger.debug("snapshot_e_request entry")
    raw = exact_shape(value, N6_E_REQUEST_LAYOUT, "n6-e-request")
    result = dispatch_e_request(raw_e_request(
        cast(N1IntroductionPackage, raw["n1_zero"]),
        cast(PadicCompletionPackage, raw["pomega2"]),
        cast(N6TheoremSourceV1, raw["theorem"]),
        cast(N6PolicyV1, raw["policy"]),
        supplied_request_digest=cast(str, raw["request_digest"]),
    ))
    logger.debug("snapshot_e_request exit")
    return result


def w_request(
    n1_zero: N1IntroductionPackage,
    pomega2: PadicCompletionPackage,
    completed_infinity: CompletedInfinityReceiptV1 | None = None,
    theorem: N6TheoremSourceV1 | None = None,
    run_policy: N6PolicyV1 | None = None,
) -> N6WRequestV1:
    """Build W NONE/SOME request; SOME remains non-authoritative in Python."""
    logger.debug("w_request entry")
    receipt = (
        None
        if completed_infinity is None
        else snapshot_ci_receipt(completed_infinity)
    )
    source = (
        _theorem_source(N6Lane.W_INFORMATION_GROWTH)
        if theorem is None
        else _snapshot_theorem_source(theorem, N6Lane.W_INFORMATION_GROWTH)
    )
    selected_policy = _policy() if run_policy is None else _snapshot_policy(run_policy)
    common = e_request(n1_zero, pomega2, None, selected_policy)
    receipt_binding = b"missing" if receipt is None else receipt.receipt_digest.encode()
    request_digest = digest("veyra.p3n6.w-request.v1", (
        ("n1-zero-package", common.n1_zero.package_digest.encode()),
        ("pomega2-package", common.pomega2.package_digest.encode()),
        ("completed-infinity", receipt_binding),
        ("theorem-source", source.source_digest.encode()),
        ("policy", common.policy.policy_digest.encode()),
    ))
    result = N6WRequestV1(
        common.n1_zero, common.pomega2, receipt, source, common.policy,
        request_digest,
    )
    logger.debug(
        "w_request exit state=%s",
        "missing-completed-infinity" if receipt is None else "typed-untrusted",
    )
    return result


def snapshot_w_request(value: N6WRequestV1) -> N6WRequestV1:
    """Freshly replay the missing-CI W request and its exact digest."""
    logger.debug("snapshot_w_request entry")
    raw = exact_shape(value, N6_W_REQUEST_LAYOUT, "n6-w-request")
    result = w_request(
        cast(N1IntroductionPackage, raw["n1_zero"]),
        cast(PadicCompletionPackage, raw["pomega2"]),
        cast(CompletedInfinityReceiptV1 | None, raw["completed_infinity"]),
        cast(N6TheoremSourceV1, raw["theorem"]),
        cast(N6PolicyV1, raw["policy"]),
    )
    if type(raw["request_digest"]) is not str or raw["request_digest"] != result.request_digest:
        reject("n6-w-request-drift")
    logger.debug("snapshot_w_request exit")
    return result


def snapshot_ci_receipt(value: CompletedInfinityReceiptV1) -> CompletedInfinityReceiptV1:
    """Reconstruct a typed SOME receipt without treating metadata as admission."""
    logger.debug("snapshot_ci_receipt entry")
    raw = exact_shape(value, N6_CI_RECEIPT_LAYOUT, "n6-ci-receipt")
    for name in ("doctrine_digest", "package_digest", "source_digest", "receipt_digest"):
        exact_digest(raw[name], f"n6-ci-{name}")
    for name in ("index_id", "foundation_id"):
        exact_text(raw[name], f"n6-ci-{name}")
    expected = digest("veyra.p3n6.ci-receipt.v1", (
        ("doctrine", cast(str, raw["doctrine_digest"]).encode()),
        ("index", cast(str, raw["index_id"]).encode()),
        ("foundation", cast(str, raw["foundation_id"]).encode()),
        ("package", cast(str, raw["package_digest"]).encode()),
        ("source", cast(str, raw["source_digest"]).encode()),
    ))
    if raw["receipt_digest"] != expected:
        reject("n6-ci-receipt-digest-drift")
    result = CompletedInfinityReceiptV1(
        cast(str, raw["doctrine_digest"]),
        cast(str, raw["index_id"]),
        cast(str, raw["foundation_id"]),
        cast(str, raw["package_digest"]),
        cast(str, raw["source_digest"]),
        cast(str, raw["receipt_digest"]),
    )
    logger.debug("snapshot_ci_receipt exit state=typed-untrusted")
    return result


def e_result(value: N6ERequestV1) -> N6EResultV1:
    """Run the fresh checked E derivation; no supplied positive is accepted."""
    logger.debug("e_result entry")
    request = snapshot_e_request(value)
    from .prime_power_unbounded_runtime import derive_power_injection

    result = derive_power_injection(request)
    logger.debug("e_result exit type=%s", type(result).__name__)
    return result


def w_result(value: N6WRequestV1) -> N6WResultV1:
    """Closed W dispatcher: NONE is OPEN; SOME is operationally unverified."""
    logger.debug("w_result entry")
    request = snapshot_w_request(value)
    from .prime_power_unbounded_failures import N6WOpenV1
    from .prime_power_unbounded_formal_failures import (
        N6SanitizedDiagnosticV1,
        N6WFormalFailureV1,
    )
    from .prime_power_unbounded_result_digests import formal_attempt_digest, open_result_digest

    if request.completed_infinity is not None:
        output_digest = sha(b"")
        detail_digest = sha(b"python-runtime-is-not-positive-derivation-authority")
        diagnostic = N6SanitizedDiagnosticV1(
            N6DiagnosticCode.DEPENDENCY_REPLAY_FAILURE, detail_digest
        )
        attempt = formal_attempt_digest(
            N6Lane.W_INFORMATION_GROWTH,
            N6FormalFailureKind.DEPENDENCY_REPLAY_FAILURE,
            request.request_digest, request.theorem.source_digest,
            "leanprover/lean4:v4.30.0-rc2",
            request.policy.policy_digest, output_digest, diagnostic.code.value,
            diagnostic.detail_digest,
        )
        failure_result = N6WFormalFailureV1(
            N6FormalFailureKind.DEPENDENCY_REPLAY_FAILURE, request.request_digest,
            request.theorem.source_digest, "leanprover/lean4:v4.30.0-rc2",
            request.policy.policy_digest,
            output_digest, attempt, diagnostic,
        )
        logger.debug("w_result exit state=formal-failure kind=%s", failure_result.kind.value)
        return failure_result
    open_digest = open_result_digest(
        N6Lane.W_INFORMATION_GROWTH,
        N6WOpenReason.MISSING_COMPLETED_INFINITY_ADMISSION.value,
        N6GoalID.COMPLETED_INFINITY_ADMISSION,
        request.request_digest,
    )
    result = N6WOpenV1(
        N6Status.OPEN, N6WOpenReason.MISSING_COMPLETED_INFINITY_ADMISSION,
        N6GoalID.COMPLETED_INFINITY_ADMISSION, request.request_digest,
        open_digest,
    )
    logger.debug("w_result exit status=open")
    return result
