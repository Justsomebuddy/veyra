"""Fresh checked derivation for the isolated P3-N6 E power-injection slice."""

from __future__ import annotations

import logging

from .padic.completion.runtime import padic_completion_judgment
from .padic.completion.types import PadicCompletionJudgment
from .padic.family_introduction.runtime import introduce_integer_residue_family
from .padic.family_introduction.types import N1FamilyJudgment
from .prime_power_unbounded_common import sha
from .prime_power_unbounded_formal import (
    N6ECompileOutcome,
    capture_e_sources,
    compile_e_sources,
    continuity_holds,
    formal_run_digest,
)
from .prime_power_unbounded_formal_failures import (
    N6EFormalFailureV1,
    N6SanitizedDiagnosticV1,
)
from .prime_power_unbounded_ledger import (
    EQUALITY_ADAPTER_THEOREM_ID,
    E_AXIOM_CLOSURE,
    INJECTION_THEOREM_IDS,
    checked_axiom_closure,
    n6e_dependency_ledger,
    snapshot_n6e_ledger,
)
from .prime_power_unbounded_result_digests import formal_attempt_digest
from .prime_power_unbounded_results import (
    PPEqualityAdapterRawV1,
    PPEqualityAdapterV1,
    PowerInjectionEvidenceRawV1,
    PowerInjectionEvidenceV1,
    PowerInjectionJudgmentRawV1,
    PowerInjectionJudgmentV1,
    _adapter_digest,
    _evidence_digest,
    _judgment_digest,
    _validate_adapter,
    _validate_evidence,
    _validate_judgment,
)
from .prime_power_unbounded_types import (
    N6DiagnosticCode,
    N6ERequestV1,
    N6FormalFailureKind,
    N6Kind,
    N6Lane,
    N6Status,
    N6_NONCLAIMS,
)

logger = logging.getLogger(__name__)
TOOLCHAIN_ID = "leanprover/lean4:v4.30.0-rc2"


def _failure(
    request: N6ERequestV1,
    kind: N6FormalFailureKind,
    output: bytes,
    detail: bytes,
) -> N6EFormalFailureV1:
    """Build a sanitized execution failure bound to the exact E request."""
    logger.debug("_failure entry kind=%s", kind.value)
    code = N6DiagnosticCode(kind.value)
    output_digest = sha(output)
    diagnostic = N6SanitizedDiagnosticV1(code, sha(detail))
    attempt = formal_attempt_digest(
        N6Lane.E_POWER_INJECTION, kind, request.request_digest,
        request.theorem.source_digest, TOOLCHAIN_ID,
        request.policy.policy_digest, output_digest, code.value,
        diagnostic.detail_digest,
    )
    result = N6EFormalFailureV1(
        kind, request.request_digest, request.theorem.source_digest,
        TOOLCHAIN_ID, request.policy.policy_digest, output_digest, attempt,
        diagnostic,
    )
    logger.debug("_failure exit kind=%s", kind.value)
    return result


def _adapter(request: N6ERequestV1) -> PPEqualityAdapterRawV1:
    """Construct the adapter only from exact PΩ2 endpoints and THM005."""
    logger.debug("_adapter entry")
    package = request.pomega2
    raw = PPEqualityAdapterRawV1(
        package.package_digest,
        package.doctrine.doctrine_digest,
        package.doctrine.carrier_id,
        package.doctrine.equality_id,
        request.theorem.equality_definition_id,
        request.theorem.source_digest,
        EQUALITY_ADAPTER_THEOREM_ID,
        "0" * 64,
    )
    result = PPEqualityAdapterRawV1(
        raw.pomega2_package_digest, raw.doctrine_digest, raw.carrier_id,
        raw.equality_id, raw.equality_definition_id,
        raw.theorem_source_digest, raw.proof_id, _adapter_digest(raw),
    )
    _validate_adapter(result)
    logger.debug("_adapter exit")
    return result


def _evidence(
    request: N6ERequestV1,
    adapter: PPEqualityAdapterRawV1,
    ledger_digest: str,
    n1: N1FamilyJudgment,
    pomega2: PadicCompletionJudgment,
    outcome: N6ECompileOutcome,
) -> PowerInjectionEvidenceRawV1:
    """Bind the checked theorem closure, map, adapter, and source packages."""
    logger.debug("_evidence entry")
    raw = PowerInjectionEvidenceRawV1(
        request.pomega2.prime.source_digest,
        request.pomega2.package_digest,
        request.n1_zero.package_digest,
        pomega2.judgment_digest,
        n1.judgment_digest,
        request.pomega2.theorem_source.source_digest,
        request.n1_zero.theorem_source.source_digest,
        request.pomega2.doctrine.doctrine_digest,
        request.pomega2.doctrine.carrier_id,
        request.pomega2.doctrine.equality_id,
        request.theorem.source_digest,
        ledger_digest,
        outcome.attestation_digest,
        formal_run_digest(outcome),
        adapter.adapter_digest,
        request.theorem.power_map_definition_id,
        INJECTION_THEOREM_IDS,
        E_AXIOM_CLOSURE,
        "0" * 64,
    )
    result = PowerInjectionEvidenceRawV1(
        raw.prime_digest, raw.pomega2_package_digest,
        raw.n1_zero_package_digest, raw.pomega2_judgment_digest,
        raw.n1_zero_judgment_digest,
        raw.pomega2_theorem_source_digest, raw.n1_theorem_source_digest,
        raw.doctrine_digest, raw.carrier_id, raw.equality_id,
        raw.theorem_source_digest, raw.ledger_digest,
        raw.launcher_attestation_digest, raw.formal_run_digest,
        raw.equality_adapter_digest,
        raw.power_map_definition_id, raw.proof_ids,
        raw.theorem_axiom_closure, _evidence_digest(raw),
    )
    _validate_evidence(result)
    logger.debug("_evidence exit")
    return result


def _judgment(
    request: N6ERequestV1,
    evidence: PowerInjectionEvidenceRawV1,
) -> PowerInjectionJudgmentRawV1:
    """Construct the exact nonpromoting power-injection judgment payload."""
    logger.debug("_judgment entry")
    doctrine = request.pomega2.doctrine
    raw = PowerInjectionJudgmentRawV1(
        N6Kind.POWER_INJECTION_RELATIVE_TO_EXACT_POMEGA2,
        request.request_digest, evidence, "Nat",
        request.theorem.power_map_definition_id, doctrine.carrier_id,
        doctrine.equality_id, 0, N6_NONCLAIMS, "0" * 64,
    )
    result = PowerInjectionJudgmentRawV1(
        raw.kind, raw.request_digest, raw.evidence, raw.map_domain,
        raw.map_definition_id, raw.carrier_id, raw.equality_id,
        raw.promotions, raw.nonclaims, _judgment_digest(raw),
    )
    _validate_judgment(result, evidence)
    logger.debug("_judgment exit")
    return result


def _dependency_check(
    request: N6ERequestV1,
) -> tuple[N1FamilyJudgment, PadicCompletionJudgment] | None:
    """Freshly replay the released N1-zero and PΩ2 positive dependencies."""
    logger.debug("_dependency_check entry")
    n1 = introduce_integer_residue_family(request.n1_zero)
    pomega2 = padic_completion_judgment(request.pomega2)
    established = (
        type(n1) is N1FamilyJudgment
        and type(pomega2) is PadicCompletionJudgment
        and n1.prime_digest == pomega2.prime_digest
        and n1.doctrine_digest == pomega2.doctrine_digest
        and n1.package_digest == request.n1_zero.package_digest
        and pomega2.package_digest == request.pomega2.package_digest
    )
    result = (n1, pomega2) if established else None
    logger.debug("_dependency_check exit established=%s", established)
    return result


def derive_power_injection(
    request: N6ERequestV1,
) -> PowerInjectionJudgmentV1 | N6EFormalFailureV1:
    """Derive N6-E only after dependency, source, Lean, ledger, and continuity checks."""
    logger.debug("derive_power_injection entry")
    from .prime_power_unbounded_requests import snapshot_e_request

    request = snapshot_e_request(request)
    dependencies = _dependency_check(request)
    if dependencies is None:
        result_failure = _failure(
            request, N6FormalFailureKind.DEPENDENCY_REPLAY_FAILURE, b"",
            b"n6-e-dependency-replay-failed",
        )
        logger.debug("derive_power_injection exit status=formal-failure kind=%s",
                     result_failure.kind.value)
        return result_failure
    ledger = snapshot_n6e_ledger(n6e_dependency_ledger())
    captured = capture_e_sources(request.theorem)
    outcome = compile_e_sources(request.theorem, request.policy, captured)
    if outcome.kind is not None:
        logger.error("derive_power_injection formal failure kind=%s", outcome.kind.value)
        result_failure = _failure(
            request, outcome.kind, outcome.output,
            f"n6-e-formal-{outcome.kind.value}".encode(),
        )
        logger.debug("derive_power_injection exit status=formal-failure kind=%s",
                     result_failure.kind.value)
        return result_failure
    closure = checked_axiom_closure(ledger, outcome.theorem_axiom_rows)
    if closure != E_AXIOM_CLOSURE:
        result_failure = _failure(
            request, N6FormalFailureKind.COMPILE_ERROR, outcome.output,
            b"n6-e-axiom-ledger-mismatch",
        )
        logger.debug("derive_power_injection exit status=formal-failure kind=%s",
                     result_failure.kind.value)
        return result_failure
    if not continuity_holds(request.theorem, captured):
        result_failure = _failure(
            request, N6FormalFailureKind.CONTINUITY_DRIFT, outcome.output,
            b"n6-e-source-continuity-drift",
        )
        logger.debug("derive_power_injection exit status=formal-failure kind=%s",
                     result_failure.kind.value)
        return result_failure
    adapter = _adapter(request)
    n1, pomega2 = dependencies
    evidence = _evidence(request, adapter, ledger.ledger_digest, n1, pomega2, outcome)
    judgment = _judgment(request, evidence)
    _validate_adapter(adapter)
    _validate_evidence(evidence)
    _validate_judgment(judgment, evidence)
    owned_adapter = object.__new__(PPEqualityAdapterV1)
    object.__setattr__(owned_adapter, "raw", adapter)
    owned_evidence = object.__new__(PowerInjectionEvidenceV1)
    object.__setattr__(owned_evidence, "raw", evidence)
    object.__setattr__(owned_evidence, "adapter", owned_adapter)
    result = object.__new__(PowerInjectionJudgmentV1)
    object.__setattr__(result, "status", N6Status.ESTABLISHED)
    object.__setattr__(result, "raw", judgment)
    object.__setattr__(result, "evidence", owned_evidence)
    logger.debug("derive_power_injection exit status=established")
    return result
