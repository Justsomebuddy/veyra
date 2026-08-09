"""Formal bridge judgment plus separate bounded projection pressure for P3-A1b."""

from __future__ import annotations

import logging

from .common import digest, reject, sha, signed_bytes
from .formal import (
    capture_pressure_sources, capture_sources, compile_pressure_sources, compile_sources,
    continuity_holds,
)
from .package import first_policy_failure, preflight_charge, snapshot_package
from .pressure import (
    PRESSURE_AXIOM_ROWS, canonical_pressure_bytes, snapshot_offset_program,
)
from .sources import AXIOM_ROWS, THEOREM_IDS
from .types import (
    A1B_NONCLAIMS, BoundaryStatus, BridgeEvidenceKind, BridgeFormalFailure,
    BridgeOpen, BridgeProvenance, BridgeRefutation, BridgeResourceLimit,
    BridgeResult, BridgeStatus, FailedBound, FamilyKind, FormalFailureKind,
    ProductiveBridgeJudgment, ProjectionArtifact, ResultStatus, UniformizationRoute,
)

logger = logging.getLogger(__name__)
MAX_RUN_INTEGER_BITS = 4096


def _rows(label: str, values: tuple[str, ...]):
    """Create stable repeated digest rows."""
    logger.debug("_rows entry label=%s count=%d", label, len(values))
    result = tuple((f"{label}-{i}", x.encode()) for i, x in enumerate(values))
    logger.debug("_rows exit")
    return result


def _formal_run(package, captured) -> str:
    """Bind only formal replay bytes; never a projection policy/depth."""
    logger.debug("_formal_run entry")
    result = digest("veyra.p3a1b.formal-run.v1", (
        ("prime", package.prime.source_digest.encode()),
        ("integer", package.integer.source_digest.encode()),
        ("doctrine", package.doctrine.doctrine_digest.encode()),
        ("program", package.program.program_digest.encode()),
        ("n1", package.n1_theorem.source_digest.encode()),
        ("theorem", package.theorem.source_digest.encode()),
        ("ledger", package.ledger.ledger_digest.encode()),
        *((f"source-{i}", sha(x).encode()) for i, x in enumerate(captured)),
        ("tcb", package.theorem.tcb_digest.encode()),
    ))
    logger.debug("_formal_run exit")
    return result


def _resource(package, run: str, failure) -> BridgeResourceLimit:
    """Create a proof-payload-free typed first-bound refusal."""
    logger.debug("_resource entry bound=%s", failure[0].value)
    bound, required, allowed = failure
    value = digest("veyra.p3a1b.resource.v1", (
        ("package", package.package_digest.encode()), ("policy", package.policy.policy_digest.encode()),
        ("run", run.encode()), ("bound", bound.value.encode()),
        ("required", signed_bytes(required, "resource-required", MAX_RUN_INTEGER_BITS)),
        ("allowed", signed_bytes(allowed, "resource-allowed", MAX_RUN_INTEGER_BITS)),
    ))
    result = BridgeResourceLimit(ResultStatus.RESOURCE_LIMIT, bound, required, allowed,
                                 package.package_digest, package.policy.policy_digest, run, value)
    logger.debug("_resource exit")
    return result


def _failure(package, run: str, outcome) -> BridgeFormalFailure:
    """Create sanitized operational failure, never mathematical OPEN/REFUTED."""
    logger.debug("_failure entry kind=%s", outcome.kind.value)
    attempt = digest("veyra.p3a1b.attempt.v1", (
        ("package", package.package_digest.encode()), ("run", run.encode()),
        ("kind", outcome.kind.value.encode()), ("output", sha(outcome.output).encode()),
        *((f"code-{i}", str(x).encode()) for i, x in enumerate(outcome.return_codes)),
    ))
    result = BridgeFormalFailure(outcome.kind, package.package_digest, run,
                                 f"formal execution {outcome.kind.value}", attempt)
    logger.debug("_failure exit")
    return result


def _positive(package) -> ProductiveBridgeJudgment:
    """Construct the nonpromoting relative bridge with six distinct identities."""
    logger.debug("_positive entry")
    family = digest("veyra.p3a1b.family-term.v1", (
        ("prime", package.prime.source_digest.encode()),
        ("integer", package.integer.source_digest.encode()),
        ("n1-theorem", package.n1_theorem.source_digest.encode()),
        ("family-definition", package.n1_theorem.family_definition_id.encode()),
    ))
    productivity = digest("veyra.p3a1b.productivity-evidence.v1", (
        ("program", package.program.program_digest.encode()),
        ("theorem", package.theorem.source_digest.encode()),
        ("ledger", package.ledger.ledger_digest.encode()),
        *_rows("theorem", THEOREM_IDS[:3]),
    ))
    introduction = digest("veyra.p3a1b.family-introduction.v1", (
        ("family", family.encode()), ("n1", package.n1_theorem.source_digest.encode()),
        ("n1-artifact", package.n1_theorem.artifact_sha256.encode()),
    ))
    bridge = digest("veyra.p3a1b.bridge-evidence.v1", (
        ("program", package.program.program_digest.encode()), ("family", family.encode()),
        ("theorem", package.theorem.source_digest.encode()),
        ("commutes", THEOREM_IDS[3].encode()), ("ledger", package.ledger.ledger_digest.encode()),
    ))
    judgment = digest("veyra.p3a1b.judgment.v1", (
        ("kind", BridgeEvidenceKind.PRODUCTIVE_FAMILY_BRIDGE.value.encode()),
        ("status", BridgeStatus.ESTABLISHED_RELATIVE_TO_LEDGER.value.encode()),
        ("provenance", BridgeProvenance.FORMALLY_DERIVED.value.encode()),
        ("route", UniformizationRoute.A1_DEFINITIONAL.value.encode()),
        ("program", package.program.program_digest.encode()), ("family", family.encode()),
        ("productivity", productivity.encode()), ("introduction", introduction.encode()),
        ("bridge", bridge.encode()), *_rows("nonclaim", A1B_NONCLAIMS),
    ))
    identities = {package.program.program_digest, family, productivity, introduction, bridge, judgment}
    if len(identities) != 6:
        raise RuntimeError("internal P3-A1b digest-domain collision")
    yes = BridgeStatus.ESTABLISHED_RELATIVE_TO_LEDGER
    result = ProductiveBridgeJudgment(
        FamilyKind.ALL_DEPTH_FAMILY, BridgeEvidenceKind.PRODUCTIVE_FAMILY_BRIDGE,
        yes, BridgeProvenance.FORMALLY_DERIVED, UniformizationRoute.A1_DEFINITIONAL,
        yes, yes, yes, yes, BoundaryStatus.NOT_ESTABLISHED, BoundaryStatus.OPEN,
        BoundaryStatus.NOT_CLAIMED, 0, package.program.program_digest, family,
        productivity, introduction, bridge, judgment, THEOREM_IDS, AXIOM_ROWS, A1B_NONCLAIMS,
    )
    logger.debug("_positive exit")
    return result


def _judge(raw_package) -> BridgeResult:
    """Replay raw sources; no prior N1/PΩ result is a premise."""
    logger.debug("_judge entry type=%s", type(raw_package).__name__)
    package = snapshot_package(raw_package)
    captured = capture_sources(package)
    charge = preflight_charge(package, captured)
    run = _formal_run(package, captured)
    refusal = first_policy_failure(package, charge)
    if refusal is not None:
        return _resource(package, run, refusal)
    outcome = compile_sources(captured, package.policy.compile_timeout_seconds,
                              package.policy.max_output_bytes)
    if outcome.kind is not None:
        return _failure(package, run, outcome)
    if outcome.theorem_axiom_rows != AXIOM_ROWS:
        broken = type(outcome)(FormalFailureKind.COMPILE_ERROR, outcome.output,
                               outcome.return_codes, (), outcome.attestation_digest,
                               outcome.phase_receipts)
        return _failure(package, run, broken)
    if not continuity_holds(package, captured):
        broken = type(outcome)(FormalFailureKind.CONTINUITY_DRIFT, outcome.output,
                               outcome.return_codes, (), outcome.attestation_digest,
                               outcome.phase_receipts)
        return _failure(package, run, broken)
    result = _positive(package)
    logger.debug("_judge exit positive")
    return result


def establish_productive_family_bridge(raw_package) -> BridgeResult:
    """Expose the sole raw-source formal bridge lane."""
    logger.debug("establish_productive_family_bridge entry")
    result = _judge(raw_package)
    logger.debug("establish_productive_family_bridge exit type=%s", type(result).__name__)
    return result


def project_residue(raw_package, depth: int):
    """Execute separate QA projection; its run digest never enters the judgment."""
    logger.debug("project_residue entry depth_type=%s", type(depth).__name__)
    package = snapshot_package(raw_package)
    captured = capture_sources(package)
    charge = preflight_charge(package, captured, depth)
    refusal = first_policy_failure(package, charge)
    depth_bytes = signed_bytes(depth, "projection-run-depth", MAX_RUN_INTEGER_BITS)
    run = digest("veyra.p3a1b.projection-run.v1", (
        ("package", package.package_digest.encode()), ("policy", package.policy.policy_digest.encode()),
        ("depth", depth_bytes),
    ))
    if refusal is not None:
        return _resource(package, run, refusal)
    exponent = depth + 1
    estimated = (package.prime.p.bit_length() * exponent + 7) // 8
    if estimated > package.policy.max_output_bytes:
        return _resource(package, run, (FailedBound.OUTPUT_BYTES, estimated,
                                        package.policy.max_output_bytes))
    modulus = pow(package.prime.p, exponent)
    residue = package.integer.z % modulus
    result = ProjectionArtifact("established", depth, modulus, residue, "QA_BOUNDED", run)
    logger.debug("project_residue exit residue_bits=%d", residue.bit_length())
    return result


def refute_offset_program(raw_package, raw_pressure_program, depth: int):
    """Formally replay a closed coherent offset program before exact refutation."""
    logger.debug("refute_offset_program entry depth_type=%s", type(depth).__name__)
    package = snapshot_package(raw_package)
    source = snapshot_offset_program(raw_pressure_program)
    if (source.prime_digest != package.prime.source_digest
            or source.integer_digest != package.integer.source_digest):
        reject("pressure-program-p-or-z-binding-mismatch")
    captured = capture_pressure_sources(package, source)
    charge = preflight_charge(package, captured, depth, canonical_pressure_bytes(source), 5)
    refusal = first_policy_failure(package, charge)
    depth_bytes = signed_bytes(depth, "pressure-run-depth", MAX_RUN_INTEGER_BITS)
    run = digest("veyra.p3a1b.pressure-run.v1", (
        ("package", package.package_digest.encode()), ("program", source.program_digest.encode()),
        ("depth", depth_bytes),
    ))
    if refusal is not None:
        return _resource(package, run, refusal)
    exponent = depth + 1
    estimated = (package.prime.p.bit_length() * exponent + 7) // 8
    if estimated > package.policy.max_output_bytes:
        return _resource(package, run, (FailedBound.OUTPUT_BYTES, estimated,
                                        package.policy.max_output_bytes))
    outcome = compile_pressure_sources(captured, package.policy.compile_timeout_seconds,
                                       package.policy.max_output_bytes)
    if outcome.kind is not None:
        return _failure(package, run, outcome)
    if outcome.theorem_axiom_rows != PRESSURE_AXIOM_ROWS:
        broken = type(outcome)(FormalFailureKind.COMPILE_ERROR, outcome.output,
                               outcome.return_codes, (), outcome.attestation_digest,
                               outcome.phase_receipts)
        return _failure(package, run, broken)
    modulus = pow(package.prime.p, depth + 1)
    expected = package.integer.z % modulus
    observed = (package.integer.z + source.offset) % modulus
    if observed == expected:
        reject("pressure-depth-does-not-witness-mismatch")
    value = digest("veyra.p3a1b.refutation.v1", (
        ("package", package.package_digest.encode()), ("program", source.program_digest.encode()),
        ("productivity", source.productivity_evidence_digest.encode()),
        ("coherence", source.coherence_evidence_digest.encode()),
        ("depth", depth.to_bytes(16, "big")),
        ("expected", signed_bytes(expected, "expected-residue")),
        ("observed", signed_bytes(observed, "observed-residue")),
    ))
    result = BridgeRefutation(
        ResultStatus.REFUTED, depth, expected, observed, source.program_digest,
        source.productivity_evidence_digest, source.coherence_evidence_digest, value,
    )
    logger.debug("refute_offset_program exit")
    return result


def report_missing_bridge_evidence(prime, integer, program) -> BridgeOpen:
    """Report admissible raw p/z/program with no theorem as typed OPEN, not error."""
    logger.debug("report_missing_bridge_evidence entry")
    from ...padic.completion.prime import snapshot_prime
    from ...padic.completion.common import PadicCompletionValidationError
    from ...padic.family_introduction.common import PadicFamilyIntroductionValidationError
    from ...padic.family_introduction.sources import snapshot_integer
    from .sources import snapshot_program
    try:
        p = snapshot_prime(prime)
        z = snapshot_integer(integer)
    except (PadicCompletionValidationError, PadicFamilyIntroductionValidationError):
        logger.error("report_missing_bridge_evidence invalid base source")
        reject("open-candidate-base-source-invalid")
    g = snapshot_program(program)
    if g.prime_digest != p.source_digest or g.integer_digest != z.source_digest:
        reject("open-candidate-program-binding-mismatch")
    reason = "missing-admissible-bridge-evidence"
    value = digest("veyra.p3a1b.open.v1", (
        ("prime", p.source_digest.encode()), ("integer", z.source_digest.encode()),
        ("program", g.program_digest.encode()), ("reason", reason.encode()),
    ))
    result = BridgeOpen(ResultStatus.OPEN, reason, p.source_digest,
                        z.source_digest, g.program_digest, value)
    logger.debug("report_missing_bridge_evidence exit")
    return result
