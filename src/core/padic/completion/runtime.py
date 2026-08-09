"""Fail-closed PΩ2 replay from exact sources to relative PPCP judgment."""

from __future__ import annotations

import logging

from .common import sha
from .digest import digest, texts
from .formal import (
    THEOREM_IDS, capture_generic_source, compile_captured_sources,
    continuity_holds, validate_captured_sources,
)
from .ledger import compiler_axiom_closure
from .package import snapshot_package
from .preflight import first_policy_failure, preflight_charge
from .types import (
    POMEGA2_NONCLAIMS, PadicCompletedCarrierStatus, PadicCompletionJudgment,
    PadicCompletionObligations, PadicCompletionPackage, PadicCompletionResourceLimit,
    PadicCompletionResult, PadicExecutionFailureKind, PadicFormalExecutionFailure,
    PadicNotClaimedStatus, PadicNotEstablishedStatus, PadicObligationStatus,
    PadicResultStatus,
)

logger = logging.getLogger(__name__)


def _run_digest(package: PadicCompletionPackage, generic: bytes, toolchain: str) -> str:
    """Bind one run to both captured sources, policy, and attested toolchain."""
    logger.debug("_run_digest entry")
    result = digest("veyra.pomega2.run.v1", (
        ("package", package.package_digest.encode()),
        ("policy", package.policy.policy_digest.encode()),
        ("generic-sha", sha(generic).encode()),
        ("prime-witness-sha", package.prime.generated_witness_sha256.encode()),
        ("canonical-ops", package.theorem_source.canonical_ops_id.encode()),
        ("concrete-instance", package.theorem_source.concrete_instance_id.encode()),
        ("toolchain", toolchain.encode()),
    ))
    logger.debug("_run_digest exit")
    return result


def _resource_limit(package, run: str, failure) -> PadicCompletionResourceLimit:
    """Construct the first-bound payload-free refusal."""
    logger.debug("_resource_limit entry")
    bound, required, allowed = failure
    value = digest("veyra.pomega2.resource-limit.v1", (
        ("package", package.package_digest.encode()),
        ("policy", package.policy.policy_digest.encode()), ("run", run.encode()),
        ("bound", bound.value.encode()), ("required", required.to_bytes(8, "big")),
        ("allowed", allowed.to_bytes(8, "big")), *texts("nonclaim", POMEGA2_NONCLAIMS),
    ))
    result = PadicCompletionResourceLimit(
        PadicResultStatus.RESOURCE_LIMIT, package.package_digest,
        package.policy.policy_digest, run, bound, required, allowed,
        POMEGA2_NONCLAIMS, value,
    )
    logger.debug("_resource_limit exit bound=%s", bound.value)
    return result


def _execution_failure(package, run: str, outcome) -> PadicFormalExecutionFailure:
    """Construct sanitized provenance-only operational failure evidence."""
    logger.debug("_execution_failure entry kind=%s", outcome.kind.value)
    phases = tuple(
        f"{row.phase}|{row.return_code}|{row.output_bytes}|{row.output_digest}|"
        f"{'' if row.failure_kind is None else row.failure_kind.value}"
        for row in outcome.phase_receipts
    )
    attempt = digest("veyra.pomega2.compile-attempt.v1", (
        ("package", package.package_digest.encode()), ("run", run.encode()),
        ("kind", outcome.kind.value.encode()), ("output-sha", sha(outcome.output).encode()),
        *texts("return-code", tuple(str(code) for code in outcome.return_codes)),
        *texts("phase", phases),
    ))
    result = PadicFormalExecutionFailure(
        outcome.kind, package.package_digest, package.policy.policy_digest, run,
        attempt, f"formal execution {outcome.kind.value}", POMEGA2_NONCLAIMS,
    )
    logger.debug("_execution_failure exit")
    return result


def _obligations() -> PadicCompletionObligations:
    """Construct exactly 17 independently named established statuses."""
    logger.debug("_obligations entry")
    result = PadicCompletionObligations(*((PadicObligationStatus.ESTABLISHED,) * 17))
    logger.debug("_obligations exit")
    return result


def _positive(package, run: str, closure: tuple[str, ...]) -> PadicCompletionJudgment:
    """Construct the exact ledger-relative positive PPCP result."""
    logger.debug("_positive entry")
    obligations = _obligations()
    value = digest("veyra.pomega2.judgment.v1", (
        ("prime", package.prime.source_digest.encode()),
        ("doctrine", package.doctrine.doctrine_digest.encode()),
        ("theorem", package.theorem_source.source_digest.encode()),
        ("ledger", package.ledger.ledger_digest.encode()),
        ("package", package.package_digest.encode()),
        ("policy", package.policy.policy_digest.encode()), ("run", run.encode()),
        ("canonical-ops", package.theorem_source.canonical_ops_id.encode()),
        ("concrete-instance", package.theorem_source.concrete_instance_id.encode()),
        *texts("theorem-id", THEOREM_IDS), *texts("axiom", closure),
        *texts("obligation", tuple(x.value for x in obligations.__dict__.values())),
        *texts("nonclaim", POMEGA2_NONCLAIMS),
    ))
    yes = PadicObligationStatus.ESTABLISHED
    no = PadicNotEstablishedStatus.NOT_ESTABLISHED
    result = PadicCompletionJudgment(
        package.prime.source_digest, package.doctrine.doctrine_digest,
        package.theorem_source.source_digest, package.ledger.ledger_digest,
        package.package_digest, package.policy.policy_digest, run,
        package.theorem_source.canonical_ops_id,
        package.theorem_source.concrete_instance_id, THEOREM_IDS, closure,
        obligations, yes, yes, yes, yes, yes,
        PadicCompletedCarrierStatus.ESTABLISHED_RELATIVE_TO_LEDGER,
        no, no, no, no, PadicNotClaimedStatus.NOT_CLAIMED,
        POMEGA2_NONCLAIMS, value,
    )
    logger.debug("_positive exit")
    return result


def _judge(raw_package: PadicCompletionPackage) -> PadicCompletionResult:
    """Freshly replay exact source, policy, formal output, closure, and continuity."""
    logger.debug("_judge entry type=%s", type(raw_package).__name__)
    package = snapshot_package(raw_package)
    generic = capture_generic_source(package.theorem_source)
    validate_captured_sources(generic, package.prime)
    charge = preflight_charge(package, generic)
    failure = first_policy_failure(package, charge)
    if failure is not None:
        run = _run_digest(package, generic, package.theorem_source.tcb_digest)
        result = _resource_limit(package, run, failure)
        logger.debug("_judge exit resource-limit")
        return result
    outcome = compile_captured_sources(
        generic, package.prime.generated_witness_bytes,
        package.policy.compile_timeout_seconds, package.policy.max_output_bytes,
    )
    run = _run_digest(package, generic, outcome.attestation_digest)
    if outcome.kind is not None:
        result = _execution_failure(package, run, outcome)
        logger.debug("_judge exit execution-failure")
        return result
    closure = compiler_axiom_closure(package.ledger, outcome.theorem_axiom_rows)
    if closure is None:
        broken = type(outcome)(
            PadicExecutionFailureKind.COMPILE_ERROR, outcome.output,
            outcome.return_codes, (), outcome.attestation_digest, outcome.phase_receipts,
        )
        return _execution_failure(package, run, broken)
    if not continuity_holds(generic, package.prime):
        broken = type(outcome)(
            PadicExecutionFailureKind.CONTINUITY_DRIFT, outcome.output,
            outcome.return_codes, (), outcome.attestation_digest, outcome.phase_receipts,
        )
        return _execution_failure(package, run, broken)
    result = _positive(package, run, closure)
    logger.debug("_judge exit positive")
    return result


def padic_completion_judgment(raw_package: PadicCompletionPackage) -> PadicCompletionResult:
    """Expose only exact fresh PΩ2 source replay, never a family adapter."""
    logger.debug("padic_completion_judgment entry")
    result = _judge(raw_package)
    logger.debug("padic_completion_judgment exit type=%s", type(result).__name__)
    return result
