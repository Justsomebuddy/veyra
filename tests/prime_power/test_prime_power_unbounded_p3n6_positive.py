"""Focused hostile checks for the first checked P3-N6-E positive slice."""

from __future__ import annotations

from dataclasses import replace
import logging
from pathlib import Path
import tempfile

import pytest

from src.core.padic_completion import (
    padic_completion_ledger,
    padic_completion_package,
    padic_completion_policy,
    padic_completion_theorem_source,
    padic_tower_doctrine,
    prime_source,
)
from src.core.padic_family_introduction import (
    integer_source,
    n1_assumption_ledger,
    n1_introduction_package,
    n1_policy,
    n1_theorem_source,
)
from src.core.prime_power_unbounded_capture import capture_fixed_source
from src.core.prime_power_unbounded_capture import project_tmp_path
from src.core.prime_power_unbounded_common import P3N6ValidationError
from src.core.prime_power_unbounded_common import sha
from src.core.prime_power_unbounded_execution_continuity import (
    runtime_file_unchanged,
    snapshot_runtime_file,
)
from src.core.prime_power_unbounded_failure_validation import validate_e_result
from src.core import prime_power_unbounded_formal as formal
from src.core.prime_power_unbounded_formal import _axioms
from src.core.prime_power_unbounded_ledger import (
    EQUALITY_ADAPTER_THEOREM_ID,
    INJECTION_THEOREM_IDS,
)
from src.core.prime_power_unbounded_requests import e_request, e_result
from src.core.prime_power_unbounded_results import (
    PowerInjectionEvidenceV1,
    PowerInjectionJudgmentV1,
    _evidence_digest,
    _judgment_digest,
)
from src.core.prime_power_unbounded_types import N6Status
from src.core.prime_power_unbounded_types import N6FormalFailureKind
from src.core.stream_completion_formal_process import CapturedPhase, FormalPhaseReceipt

pytestmark = pytest.mark.requires_lean

logger = logging.getLogger(__name__)


def _packages(p: int = 5):
    """Build one exact shared-prime N1-zero/PΩ2 pair."""
    logger.debug("_packages entry p=%d", p)
    prime = prime_source(p)
    doctrine = padic_tower_doctrine()
    pomega2 = padic_completion_package(
        prime, doctrine, padic_completion_theorem_source(),
        padic_completion_ledger(), padic_completion_policy(),
    )
    n1 = n1_introduction_package(
        prime, integer_source(0), doctrine, n1_theorem_source(),
        n1_assumption_ledger(), n1_policy(),
    )
    logger.debug("_packages exit")
    return n1, pomega2


def test_checked_n6e_derivation_and_fresh_validation() -> None:
    """Only fresh dependency/source/Lean/ledger replay yields ESTABLISHED."""
    logger.debug("test_checked_n6e_derivation_and_fresh_validation entry")
    request = e_request(*_packages())
    result = e_result(request)
    assert type(result) is PowerInjectionJudgmentV1
    assert result.status is N6Status.ESTABLISHED
    assert result.raw.request_digest == request.request_digest
    assert result.raw.map_domain == "Nat"
    assert result.raw.map_definition_id == "veyraPowerCarrier"
    assert result.evidence.raw.proof_ids == INJECTION_THEOREM_IDS
    assert result.evidence.adapter.raw.proof_id == EQUALITY_ADAPTER_THEOREM_ID
    assert result.evidence.raw.pomega2_package_digest == request.pomega2.package_digest
    assert result.evidence.raw.n1_zero_package_digest == request.n1_zero.package_digest
    assert len(result.evidence.raw.launcher_attestation_digest) == 64
    assert len(result.evidence.raw.formal_run_digest) == 64
    replayed = validate_e_result(result, request)
    assert type(replayed) is PowerInjectionJudgmentV1
    assert replayed.raw.judgment_digest == result.raw.judgment_digest
    forged_evidence_raw = replace(
        result.evidence.raw, formal_run_digest="f" * 64, evidence_digest="0" * 64,
    )
    forged_evidence_raw = replace(
        forged_evidence_raw, evidence_digest=_evidence_digest(forged_evidence_raw),
    )
    forged_judgment_raw = replace(
        result.raw, evidence=forged_evidence_raw, judgment_digest="0" * 64,
    )
    forged_judgment_raw = replace(
        forged_judgment_raw, judgment_digest=_judgment_digest(forged_judgment_raw),
    )
    forged_evidence = object.__new__(PowerInjectionEvidenceV1)
    object.__setattr__(forged_evidence, "raw", forged_evidence_raw)
    object.__setattr__(forged_evidence, "adapter", result.evidence.adapter)
    forged = object.__new__(PowerInjectionJudgmentV1)
    object.__setattr__(forged, "status", N6Status.ESTABLISHED)
    object.__setattr__(forged, "raw", forged_judgment_raw)
    object.__setattr__(forged, "evidence", forged_evidence)
    with pytest.raises(P3N6ValidationError, match="positive-replay-mismatch"):
        validate_e_result(forged, request)
    other_request = e_request(*_packages(7))
    with pytest.raises(P3N6ValidationError, match="request-context-mismatch"):
        validate_e_result(result, other_request)
    logger.debug("test_checked_n6e_derivation_and_fresh_validation exit")


def test_cross_prime_and_doctrine_endpoints_reject_before_positive() -> None:
    """Individually valid but incompatible package endpoints are malformed."""
    logger.debug("test_cross_prime_and_doctrine_endpoints_reject_before_positive entry")
    n1, _ = _packages(5)
    _, pomega2 = _packages(7)
    with pytest.raises(P3N6ValidationError, match="endpoint-mismatch"):
        e_request(n1, pomega2)
    drifted = replace(n1, doctrine=replace(n1.doctrine, equality_id="alien-equality"))
    with pytest.raises(P3N6ValidationError):
        e_request(drifted, _packages(5)[1])
    logger.debug("test_cross_prime_and_doctrine_endpoints_reject_before_positive exit")


def test_partial_owned_positive_and_detached_raw_constructor_stay_closed() -> None:
    """A partial exact-class shell cannot bypass expected-request replay."""
    logger.debug("test_partial_owned_positive_and_detached_raw_constructor_stay_closed entry")
    request = e_request(*_packages())
    forged = object.__new__(PowerInjectionJudgmentV1)
    with pytest.raises(P3N6ValidationError, match="fields-missing"):
        validate_e_result(forged, request)
    with pytest.raises(P3N6ValidationError, match="constructor-forbidden"):
        PowerInjectionJudgmentV1(object())
    logger.debug("test_partial_owned_positive_and_detached_raw_constructor_stay_closed exit")


def test_duplicate_axiom_rows_and_parent_traversal_fail_closed() -> None:
    """Duplicate formal reports and path traversal never authenticate."""
    logger.debug("test_duplicate_axiom_rows_and_parent_traversal_fail_closed entry")
    rows = b"\n".join((
        b"'THM_P3N6_003_power_carrier_injective' depends on axioms: [propext]",
        b"'THM_P3N6_004_power_carrier_eqc_injective' depends on axioms: [propext]",
        b"'THM_P3N6_005_carrier_equality_adapter' does not depend on any axioms",
        b"'THM_P3N6_005_carrier_equality_adapter' does not depend on any axioms",
    ))
    assert _axioms(rows) is None
    with pytest.raises(P3N6ValidationError, match="path-invalid"):
        capture_fixed_source("../proofs/lean/VeyraPrimePowerUnbounded.lean", "0" * 64)
    logger.debug("test_duplicate_axiom_rows_and_parent_traversal_fail_closed exit")


def test_nonrestored_runtime_file_and_private_phase_mutation_are_detected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Persistent path/byte mutation fails local continuity and the formal run."""
    logger.debug("test_nonrestored_runtime_file_and_private_phase_mutation entry")
    with tempfile.TemporaryDirectory(prefix="p3n6-continuity-", dir=project_tmp_path()) as root:
        path = Path(root) / "runtime.bin"
        path.write_bytes(b"trusted-runtime")
        snapshot = snapshot_runtime_file(path, sha(b"trusted-runtime"))
        assert snapshot is not None
        path.write_bytes(b"mutated-runtime")
        assert runtime_file_unchanged(snapshot) is False
    request = e_request(*_packages())
    captured = formal.capture_e_sources(request.theorem)

    def mutate_phase(
        phase: str, command: list[str], cwd: Path | None, deadline: float,
        cap: int, env: dict[str, str] | None = None,
    ) -> CapturedPhase:
        logger.debug("mutate_phase entry phase=%s", phase)
        assert cwd is not None
        target = cwd / "VeyraPadicCompletion.lean"
        target.chmod(0o600)
        target.write_bytes(b"persistent-private-source-mutation")
        receipt = FormalPhaseReceipt(phase, 0, 0, sha(b""), None)
        logger.debug("mutate_phase exit phase=%s", phase)
        return CapturedPhase(None, 0, b"", receipt)

    monkeypatch.setattr(formal, "capture_phase", mutate_phase)
    outcome = formal.compile_e_sources(request.theorem, request.policy, captured)
    assert outcome.kind is N6FormalFailureKind.CONTINUITY_DRIFT
    logger.debug("test_nonrestored_runtime_file_and_private_phase_mutation exit")


def test_external_runtime_tcb_boundary_is_explicit_and_closed() -> None:
    """The candidate never relabels its still-open dynamic runtime as attested."""
    logger.debug("test_external_runtime_tcb_boundary_is_explicit_and_closed entry")
    assert formal.EXTERNAL_RUNTIME_TCB_BOUNDARIES == (
        "lean-owned-dynamic-shared-objects",
        "lean-init-std-olean-import-closure",
        "system-dynamic-loader-and-libraries",
        "active-same-uid-restored-compiler-path-swap",
    )
    logger.debug("test_external_runtime_tcb_boundary_is_explicit_and_closed exit")
