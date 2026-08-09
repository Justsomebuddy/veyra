"""Fresh internal derivation of the exact request-bound P3-N6-W witness pair."""

from __future__ import annotations
import logging
from typing import cast
from ...padic.completion.runtime import padic_completion_judgment
from ...padic.completion.types import PadicCompletionJudgment
from ...padic.family_introduction.package import n1_introduction_package
from ...padic.family_introduction.runtime import introduce_integer_residue_family
from ...padic.family_introduction.sources import integer_source
from ...padic.family_introduction.types import N1FamilyJudgment, N1IntroductionPackage
from .builders import build_basis, build_witness
from .formal import (
    capture_sources,
    continuity_holds,
    formal_run_digest,
)
from .formal_runner import compile_sources
from .request import shallow_request_values, snapshot_request
from .types import (
    N6WExecutionFailureV1,
    N6WFailedBound,
    N6WResourceLimitV1,
    N6WRuntimeResultV1,
    N6WStatus,
    N6WWitnessRequestV1,
)
from ...prime_power_unbounded_common import digest, sha
from ...prime_power_unbounded_sources import policy as n6_policy
from ...prime_power_unbounded_types import N6FormalFailureKind

logger = logging.getLogger(__name__)
def _rows(name: str, values: tuple[str, ...]) -> tuple[tuple[str, bytes], ...]:
    """Frame one ordered string tuple for result commitments."""
    logger.debug("_rows entry name=%s count=%d", name, len(values))
    result = tuple((f"{name}-{index}", value.encode()) for index, value in enumerate(values))
    logger.debug("_rows exit name=%s", name)
    return result


def _resource(
    request_digest: str,
    bound: N6WFailedBound,
    required: int,
    allowed: int,
) -> N6WResourceLimitV1:
    """Build the first hard-bound refusal with no positive witness fields."""
    logger.debug("_resource entry bound=%s", bound.value)
    nonclaims = (
        "completed-index-admission", "information-unboundedness-internalization",
        "carrier-cardinality-or-uncountability", "omegan-or-omegaa-adoption",
        "public-export-certificate-registry-or-promotion",
        "generic-physical-absolute-or-foundation-independent-infinity",
    )
    refusal = digest("veyra.p3n6w.resource-limit.v1", (
        ("request", request_digest.encode()),
        ("bound", bound.value.encode()),
        ("required", required.to_bytes(8, "big")),
        ("allowed", allowed.to_bytes(8, "big")),
        *_rows("nonclaim", nonclaims),
    ))
    result = N6WResourceLimitV1(
        N6WStatus.RESOURCE_LIMIT, request_digest, bound, required,
        allowed, nonclaims, refusal,
    )
    logger.debug("_resource exit bound=%s", bound.value)
    return result


def _preflight_value(
    request: N6WWitnessRequestV1,
) -> tuple[str, int] | N6WResourceLimitV1:
    """Apply depth, prefix-row, then exact-integer-bit limits before dependencies."""
    logger.debug("_preflight_value entry")
    request_digest, k, p, run_policy = shallow_request_values(request)
    if k > run_policy.max_requested_depth:
        result = _resource(
            request_digest, N6WFailedBound.REQUESTED_DEPTH, k,
            run_policy.max_requested_depth,
        )
        logger.debug("_preflight_value exit state=resource bound=requested-depth")
        return result
    rows = k + 1
    if rows > run_policy.max_prefix_rows:
        result = _resource(
            request_digest, N6WFailedBound.PREFIX_ROWS, rows,
            run_policy.max_prefix_rows,
        )
        logger.debug("_preflight_value exit state=resource bound=prefix-rows")
        return result
    right = p ** (k + 1)
    bits = right.bit_length()
    if bits > run_policy.max_integer_bits:
        result = _resource(
            request_digest, N6WFailedBound.INTEGER_BITS, bits,
            run_policy.max_integer_bits,
        )
        logger.debug("_preflight_value exit state=resource bound=integer-bits")
        return result
    logger.debug("_preflight_value exit bits=%d", bits)
    return request_digest, right


def _late_package(request: N6WWitnessRequestV1, right: int) -> N1IntroductionPackage:
    """Construct the exact p^(k+1) N1 package from the zero package identities."""
    logger.debug("_late_package entry bits=%d", right.bit_length())
    zero = request.base_request.n1_zero
    pomega2 = request.base_request.pomega2
    logger.debug("_late_package external-call=integer_source state=begin")
    integer = integer_source(right)
    logger.debug("_late_package external-call=integer_source state=end")
    result = n1_introduction_package(
        pomega2.prime, integer, pomega2.doctrine, zero.theorem_source,
        zero.ledger, zero.policy,
    )
    logger.debug("_late_package exit")
    return result


def _dependencies(
    request: N6WWitnessRequestV1,
    right: int,
) -> tuple[N1FamilyJudgment, N1FamilyJudgment, PadicCompletionJudgment] | None:
    """Freshly replay zero/late N1 and the exact PΩ2 package before formal W."""
    logger.debug("_dependencies entry")
    late = _late_package(request, right)
    logger.debug("_dependencies external-call=introduce-zero state=begin")
    zero_judgment = introduce_integer_residue_family(request.base_request.n1_zero)
    logger.debug("_dependencies external-call=introduce-zero state=end")
    logger.debug("_dependencies external-call=introduce-late state=begin")
    late_judgment = introduce_integer_residue_family(late)
    logger.debug("_dependencies external-call=introduce-late state=end")
    logger.debug("_dependencies external-call=padic-completion state=begin")
    completion = padic_completion_judgment(request.base_request.pomega2)
    logger.debug("_dependencies external-call=padic-completion state=end")
    valid = (
        type(zero_judgment) is N1FamilyJudgment
        and type(late_judgment) is N1FamilyJudgment
        and type(completion) is PadicCompletionJudgment
        and zero_judgment.package_digest == request.base_request.n1_zero.package_digest
        and late_judgment.package_digest == late.package_digest
        and zero_judgment.prime_digest == late_judgment.prime_digest == completion.prime_digest
        and zero_judgment.doctrine_digest
        == late_judgment.doctrine_digest
        == completion.doctrine_digest
        and completion.package_digest == request.base_request.pomega2.package_digest
    )
    result = (zero_judgment, late_judgment, completion) if valid else None
    logger.debug("_dependencies exit established=%s", valid)
    return result


def _failure(
    request: N6WWitnessRequestV1,
    kind: N6FormalFailureKind,
    output: bytes,
    detail: bytes,
) -> N6WExecutionFailureV1:
    """Build one sanitized operational failure bound to both exact sources."""
    logger.debug("_failure entry kind=%s", kind.value)
    output_digest = sha(output)
    diagnostic = sha(detail)
    attempt = digest("veyra.p3n6w.execution-failure.v1", (
        ("kind", kind.value.encode()),
        ("request", request.request_digest.encode()),
        ("arithmetic-source", request.base_request.theorem.source_digest.encode()),
        ("witness-source", request.theorem.source_digest.encode()),
        ("policy", request.policy.policy_digest.encode()),
        ("output", output_digest.encode()),
        ("diagnostic", diagnostic.encode()),
    ))
    result = N6WExecutionFailureV1(
        kind, request.request_digest, request.base_request.theorem.source_digest,
        request.theorem.source_digest, request.policy.policy_digest,
        output_digest, diagnostic, attempt,
    )
    logger.debug("_failure exit kind=%s", kind.value)
    return result


def derive_witnesses(request: N6WWitnessRequestV1) -> N6WRuntimeResultV1:
    """Return the exact witness+basis pair or the first typed nonpositive arm."""
    logger.debug("derive_witnesses entry")
    preflight = _preflight_value(request)
    if type(preflight) is N6WResourceLimitV1:
        logger.debug("derive_witnesses exit state=resource bound=%s", preflight.failed_bound.value)
        return preflight
    shallow_digest, right = cast(tuple[str, int], preflight)
    checked = snapshot_request(request)
    if checked.request_digest != shallow_digest:
        raise RuntimeError("internal N6-W shallow/deep request drift")
    dependencies = _dependencies(checked, right)
    if dependencies is None:
        result_failure = _failure(
            checked, N6FormalFailureKind.DEPENDENCY_REPLAY_FAILURE, b"",
            b"n6w-dependency-replay-failed",
        )
        logger.debug("derive_witnesses exit state=failure kind=%s", result_failure.kind.value)
        return result_failure
    logger.debug("derive_witnesses external-call=capture_sources state=begin")
    captured = capture_sources(checked.theorem)
    logger.debug("derive_witnesses external-call=capture_sources state=end")
    logger.debug("derive_witnesses external-call=compile_sources state=begin")
    outcome = compile_sources(checked.theorem, n6_policy(), captured)
    logger.debug("derive_witnesses external-call=compile_sources state=end")
    if outcome.kind is not None:
        result_failure = _failure(
            checked, outcome.kind, outcome.output,
            f"n6w-formal-{outcome.kind.value}".encode(),
        )
        logger.debug("derive_witnesses exit state=failure kind=%s", result_failure.kind.value)
        return result_failure
    if outcome.theorem_axiom_rows != checked.theorem.theorem_axiom_rows:
        result_failure = _failure(
            checked, N6FormalFailureKind.COMPILE_ERROR, outcome.output,
            b"n6w-axiom-row-drift",
        )
        logger.debug("derive_witnesses exit state=failure kind=%s", result_failure.kind.value)
        return result_failure
    if not continuity_holds(checked.theorem, captured):
        result_failure = _failure(
            checked, N6FormalFailureKind.CONTINUITY_DRIFT, outcome.output,
            b"n6w-post-run-continuity-drift",
        )
        logger.debug("derive_witnesses exit state=failure kind=%s", result_failure.kind.value)
        return result_failure
    basis = build_basis(checked, dependencies[2], formal_run_digest(outcome))
    witness = build_witness(checked, right, dependencies, basis)
    result = (witness, basis)
    logger.debug("derive_witnesses exit state=established rows=%d", len(witness.prefix_rows))
    return result
