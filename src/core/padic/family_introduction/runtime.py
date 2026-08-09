"""Fail-closed raw-source replay for P3-N1 integer family introduction."""

from __future__ import annotations

import logging

from .common import digest, sha
from .formal import capture_sources, compile_sources, continuity_holds
from .package import first_policy_failure, preflight_charge, snapshot_package
from .sources import AXIOM_CLOSURE, THEOREM_IDS
from .types import (
    N1EvidenceProvenance, N1EvidenceStatus, N1ExecutionFailureKind, N1FamilyJudgment,
    N1FormalFailure, N1IntroductionPackage, N1JudgmentKind, N1_NONCLAIMS,
    N1ResourceLimit, N1Result, N1ResultStatus,
)

logger = logging.getLogger(__name__)


def _rows(name: str, values: tuple[str, ...]) -> tuple[tuple[str, bytes], ...]:
    """Frame an ordered string tuple without unordered normalization."""
    logger.debug("_rows entry name=%s count=%d", name, len(values))
    result = tuple((f"{name}-{i}", value.encode()) for i, value in enumerate(values))
    logger.debug("_rows exit")
    return result


def _run_digest(package: N1IntroductionPackage, captured: tuple[bytes, ...], attestation: str) -> str:
    """Bind the replay to every captured source and expected toolchain identity."""
    logger.debug("_run_digest entry")
    result = digest("veyra.p3n1.run.v1", (
        ("package", package.package_digest.encode()), ("policy", package.policy.policy_digest.encode()),
        *((f"captured-{i}", sha(value).encode()) for i, value in enumerate(captured)),
        ("attestation", attestation.encode()),
    ))
    logger.debug("_run_digest exit")
    return result


def _resource(package, run: str, failure) -> N1ResourceLimit:
    """Construct first-bound refusal with no mathematical payload."""
    logger.debug("_resource entry")
    bound, required, allowed = failure
    value = digest("veyra.p3n1.resource-limit.v1", (
        ("package", package.package_digest.encode()), ("policy", package.policy.policy_digest.encode()),
        ("run", run.encode()), ("bound", bound.value.encode()),
        ("required", required.to_bytes(8, "big")), ("allowed", allowed.to_bytes(8, "big")),
        *_rows("nonclaim", N1_NONCLAIMS),
    ))
    result = N1ResourceLimit(N1ResultStatus.RESOURCE_LIMIT, package.package_digest,
                             package.policy.policy_digest, run, bound, required, allowed,
                             N1_NONCLAIMS, value)
    logger.debug("_resource exit")
    return result


def _failure(package, run: str, outcome) -> N1FormalFailure:
    """Construct sanitized operational failure bound to all phase receipts."""
    logger.debug("_failure entry kind=%s", outcome.kind.value)
    phase_rows = tuple(
        f"{x.phase}|{x.return_code}|{x.output_bytes}|{x.output_digest}|"
        f"{'' if x.failure_kind is None else x.failure_kind.value}"
        for x in outcome.phase_receipts
    )
    attempt = digest("veyra.p3n1.formal-attempt.v1", (
        ("package", package.package_digest.encode()), ("run", run.encode()),
        ("kind", outcome.kind.value.encode()), ("output", sha(outcome.output).encode()),
        *_rows("return-code", tuple(str(x) for x in outcome.return_codes)),
        *_rows("phase", phase_rows),
    ))
    result = N1FormalFailure(outcome.kind, package.package_digest, package.policy.policy_digest,
                             run, attempt, f"formal execution {outcome.kind.value}", N1_NONCLAIMS)
    logger.debug("_failure exit")
    return result


def _positive(package, run: str) -> N1FamilyJudgment:
    """Construct one exact ledger-relative all-depth family judgment."""
    logger.debug("_positive entry")
    family = digest("veyra.p3n1.family-term.v1", (
        ("prime", package.prime.source_digest.encode()),
        ("integer", package.integer.source_digest.encode()),
        ("doctrine", package.doctrine.doctrine_digest.encode()),
        ("family-class", package.doctrine.family_class_id.encode()),
        ("coordinate-definition", package.theorem_source.coordinate_definition_id.encode()),
        ("family-definition", package.theorem_source.family_definition_id.encode()),
    ))
    introduction = digest("veyra.p3n1.introduction-evidence.v1", (
        ("family", family.encode()), ("theorem", package.theorem_source.source_digest.encode()),
        ("ledger", package.ledger.ledger_digest.encode()), ("run", run.encode()),
        *_rows("theorem", THEOREM_IDS), *_rows("axiom", AXIOM_CLOSURE),
    ))
    judgment = digest("veyra.p3n1.judgment.v1", (
        ("kind", N1JudgmentKind.ALL_DEPTH_FAMILY.value.encode()),
        ("status", N1EvidenceStatus.ESTABLISHED.value.encode()),
        ("provenance", N1EvidenceProvenance.FORMALLY_DERIVED.value.encode()),
        ("package", package.package_digest.encode()), ("family", family.encode()),
        ("introduction", introduction.encode()), *_rows("nonclaim", N1_NONCLAIMS),
    ))
    if len({package.theorem_source.source_digest, family, introduction, judgment}) != 4:
        raise RuntimeError("internal N1 digest domain collision")
    yes = N1EvidenceStatus.ESTABLISHED
    result = N1FamilyJudgment(
        N1JudgmentKind.ALL_DEPTH_FAMILY, yes, N1EvidenceProvenance.FORMALLY_DERIVED,
        package.prime.source_digest, package.integer.source_digest,
        package.doctrine.doctrine_digest, package.theorem_source.source_digest,
        package.ledger.ledger_digest, package.package_digest, run, family, introduction,
        THEOREM_IDS, AXIOM_CLOSURE, yes, yes, N1_NONCLAIMS, judgment,
    )
    logger.debug("_positive exit")
    return result


def _judge(raw_package: N1IntroductionPackage) -> N1Result:
    """Replay raw p/z/tower/theorem/ledger only; no previous evidence is accepted."""
    logger.debug("_judge entry type=%s", type(raw_package).__name__)
    package = snapshot_package(raw_package)
    captured = capture_sources(package)
    charge = preflight_charge(package, captured)
    run = _run_digest(package, captured, package.theorem_source.tcb_digest)
    refusal = first_policy_failure(package, charge)
    if refusal is not None:
        return _resource(package, run, refusal)
    outcome = compile_sources(captured, package.policy.compile_timeout_seconds,
                              package.policy.max_output_bytes)
    if outcome.kind is not None:
        return _failure(package, run, outcome)
    if outcome.theorem_axiom_rows != (
        (THEOREM_IDS[0], ()), (THEOREM_IDS[1], AXIOM_CLOSURE),
        (THEOREM_IDS[2], AXIOM_CLOSURE),
    ):
        broken = type(outcome)(N1ExecutionFailureKind.COMPILE_ERROR, outcome.output,
                               outcome.return_codes, (), outcome.attestation_digest,
                               outcome.phase_receipts)
        return _failure(package, run, broken)
    if not continuity_holds(package, captured):
        broken = type(outcome)(N1ExecutionFailureKind.CONTINUITY_DRIFT, outcome.output,
                               outcome.return_codes, (), outcome.attestation_digest,
                               outcome.phase_receipts)
        return _failure(package, run, broken)
    result = _positive(package, run)
    logger.debug("_judge exit positive")
    return result


def introduce_integer_residue_family(raw_package: N1IntroductionPackage) -> N1Result:
    """Expose the sole raw-source P3-N1 introduction lane."""
    logger.debug("introduce_integer_residue_family entry")
    result = _judge(raw_package)
    logger.debug("introduce_integer_residue_family exit type=%s", type(result).__name__)
    return result
