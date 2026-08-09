"""Fail-closed PΩ1 replay: hard checks, preflight, compile, continuity, judgment."""

from __future__ import annotations

import logging

from .common import sha
from .digest import digest, texts
from .formal import (
    THEOREM_IDS, capture_generic_source, compile_captured_sources,
    continuity_holds, validate_captured_sources,
)
from .formal_process import FormalPhaseReceipt
from .ledger import compiler_axiom_closure
from .package import snapshot_package
from .preflight import first_policy_failure, preflight_charge
from .types import (
    CompletedCarrierStatus, CompletionObligationStatuses, CompletionResultStatus,
    FormalExecutionFailure, FormalExecutionFailureKind, MetaphysicalTotalityStatus, ObligationStatus,
    POMEGA1_NONCLAIMS, PhysicalInstantiationStatus, StreamCompletionJudgment,
    StreamCompletionPackage, StreamCompletionResourceLimit, StreamCompletionResult,
)

logger = logging.getLogger(__name__)


def _run_digest(package: StreamCompletionPackage, generic: bytes, toolchain_identity: str) -> str:
    """Bind replay to sources, policy, and attested/planned toolchain identity."""
    logger.debug("_run_digest entry")
    result = digest("veyra.pomega1.run.v1", (
        ("package", package.package_digest.encode()),
        ("policy", package.policy.policy_digest.encode()),
        ("generic-sha", sha(generic).encode()),
        ("instance-sha", package.alphabet_presentation.generated_instance_sha256.encode()),
        ("toolchain-identity", toolchain_identity.encode()),
    ))
    logger.debug("_run_digest exit")
    return result


def _resource_limit(
    package: StreamCompletionPackage, run: str, failure: tuple,
) -> StreamCompletionResourceLimit:
    """Construct a payload-free first-bound refusal."""
    logger.debug("_resource_limit entry")
    bound, required, allowed = failure
    value = digest("veyra.pomega1.resource-limit.v1", (
        ("package", package.package_digest.encode()),
        ("policy", package.policy.policy_digest.encode()), ("run", run.encode()),
        ("bound", bound.value.encode()), ("required", required.to_bytes(8, "big")),
        ("allowed", allowed.to_bytes(8, "big")), *texts("nonclaim", POMEGA1_NONCLAIMS),
    ))
    result = StreamCompletionResourceLimit(
        CompletionResultStatus.RESOURCE_LIMIT, package.package_digest,
        package.policy.policy_digest, run, bound, required, allowed,
        POMEGA1_NONCLAIMS, value,
    )
    logger.debug("_resource_limit exit bound=%s", bound.value)
    return result


def _execution_failure(
    package: StreamCompletionPackage, run: str, kind, output: bytes,
    codes: tuple[int, ...], phases: tuple[FormalPhaseReceipt, ...],
) -> FormalExecutionFailure:
    """Construct sanitized provenance-only operational failure evidence."""
    logger.debug("_execution_failure entry kind=%s", kind.value)
    attempt = digest("veyra.pomega1.compile-attempt.v1", (
        ("package", package.package_digest.encode()), ("run", run.encode()),
        ("kind", kind.value.encode()), ("output-sha", sha(output).encode()),
        *texts("return-code", tuple(str(code) for code in codes)),
        *texts("phase", tuple(
            f"{row.phase}|{row.return_code}|{row.output_bytes}|{row.output_digest}|"
            f"{'' if row.failure_kind is None else row.failure_kind.value}"
            for row in phases
        )),
    ))
    result = FormalExecutionFailure(
        kind, package.package_digest, package.policy.policy_digest, run, attempt,
        f"formal execution {kind.value}",
        PhysicalInstantiationStatus.NOT_ESTABLISHED,
        MetaphysicalTotalityStatus.NOT_CLAIMED, POMEGA1_NONCLAIMS,
    )
    logger.debug("_execution_failure exit")
    return result


def _obligations() -> CompletionObligationStatuses:
    """Construct the exact eleven independently named positive statuses."""
    logger.debug("_obligations entry")
    established = ObligationStatus.ESTABLISHED
    result = CompletionObligationStatuses(*((established,) * 11))
    logger.debug("_obligations exit")
    return result


def _positive(
    package: StreamCompletionPackage, run: str, axiom_closure: tuple[str, ...],
) -> StreamCompletionJudgment:
    """Construct the doctrine/ledger-relative positive result after all gates."""
    logger.debug("_positive entry")
    obligations = _obligations()
    value = digest("veyra.pomega1.judgment.v1", (
        ("doctrine", package.doctrine.doctrine_digest.encode()),
        ("alphabet", package.alphabet.alphabet_digest.encode()),
        ("presentation", package.alphabet_presentation.presentation_digest.encode()),
        ("theorem", package.theorem_source.source_digest.encode()),
        ("ledger", package.ledger.ledger_digest.encode()),
        ("package", package.package_digest.encode()),
        ("policy", package.policy.policy_digest.encode()), ("run", run.encode()),
        *texts("theorem-id", THEOREM_IDS), *texts("axiom", axiom_closure),
        *texts("obligation", tuple(status.value for status in obligations.__dict__.values())),
        *texts("nonclaim", POMEGA1_NONCLAIMS),
    ))
    result = StreamCompletionJudgment(
        package.doctrine.doctrine_digest, package.alphabet.alphabet_digest,
        package.alphabet_presentation.presentation_digest,
        package.theorem_source.source_digest, package.ledger.ledger_digest,
        package.package_digest, package.policy.policy_digest, run, THEOREM_IDS,
        axiom_closure, obligations, ObligationStatus.ESTABLISHED,
        ObligationStatus.ESTABLISHED, ObligationStatus.ESTABLISHED,
        CompletedCarrierStatus.ESTABLISHED_RELATIVE_TO_LEDGER,
        PhysicalInstantiationStatus.NOT_ESTABLISHED,
        MetaphysicalTotalityStatus.NOT_CLAIMED, POMEGA1_NONCLAIMS, value,
    )
    logger.debug("_positive exit")
    return result


def _judge(raw_package: StreamCompletionPackage) -> StreamCompletionResult:
    """Internal fresh replay used by construction and independent revalidation."""
    logger.debug("_judge entry type=%s", type(raw_package).__name__)
    package = snapshot_package(raw_package)
    generic = capture_generic_source(package.theorem_source)
    validate_captured_sources(generic, package.alphabet_presentation)
    charge = preflight_charge(package, generic)
    failure = first_policy_failure(package, charge)
    if failure is not None:
        run = _run_digest(package, generic, package.theorem_source.tcb_digest)
        result = _resource_limit(package, run, failure)
        logger.debug("_judge exit resource-limit")
        return result
    outcome = compile_captured_sources(
        generic, package.alphabet_presentation.generated_instance_bytes,
        package.policy.compile_timeout_seconds, package.policy.max_output_bytes,
    )
    run = _run_digest(package, generic, outcome.attestation_digest)
    if outcome.kind is not None:
        result = _execution_failure(
            package, run, outcome.kind, outcome.output,
            outcome.return_codes, outcome.phase_receipts,
        )
        logger.debug("_judge exit execution-failure kind=%s", outcome.kind.value)
        return result
    closure = compiler_axiom_closure(package.ledger, outcome.theorem_axiom_rows)
    if closure is None:
        result = _execution_failure(
            package, run, FormalExecutionFailureKind.COMPILE_ERROR,
            outcome.output, outcome.return_codes,
            outcome.phase_receipts,
        )
        logger.debug("_judge exit compiler-closure-mismatch")
        return result
    if not continuity_holds(generic):
        result = _execution_failure(
            package, run, FormalExecutionFailureKind.CONTINUITY_DRIFT,
            outcome.output, outcome.return_codes, outcome.phase_receipts,
        )
        logger.debug("_judge exit continuity-drift")
        return result
    result = _positive(package, run, closure)
    logger.debug("_judge exit positive")
    return result


def stream_completion_judgment(
    raw_package: StreamCompletionPackage,
) -> StreamCompletionResult:
    """Replay only an exact raw source package; prior results prove nothing."""
    logger.debug("stream_completion_judgment entry")
    result = _judge(raw_package)
    logger.debug("stream_completion_judgment exit variant=%s", type(result).__name__)
    return result
