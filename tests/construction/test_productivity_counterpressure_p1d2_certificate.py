"""Direct certificate and exact Lean-source boundary tests for P1-D2."""

from dataclasses import replace
from hashlib import sha256
from pathlib import Path
import re

import pytest

import src.core.certify_productivity_counterpressure as certifier
from src.core.certify_productivity_counterpressure import (
    certify_productivity_counterpressure,
)
from src.core.formal_export_catalog import _strip_lean_comments
from src.core.productivity_counterpressure import (
    ARTIFACT_NAME, ARTIFACT_SHA256, LEAN_TCB_DIGEST, LEAN_TOOLCHAIN_ID,
    THEOREM_IDS, CounterpressureValidationError, check_basis_source,
    counterpressure_basis_source,
)
from src.core.productivity_counterpressure_basis import _compile_captured
from src.core.productivity_counterpressure_types import (
    CounterpressureCertificate, CounterpressureInference,
)

pytestmark = pytest.mark.requires_lean


def test_direct_level_one_certificate_passes_with_exact_counts():
    certificate = certify_productivity_counterpressure()
    assert certificate.passed is True
    assert certificate.level == 1
    assert certificate.name == "productivity_counterpressure_p1d2"
    assert "rows=5/5" in certificate.detail
    assert "insufficiency=2/2" in certificate.detail
    assert "countermodels=3/3" in certificate.detail
    assert "lean_countermodels=2/2" in certificate.detail
    assert "structural_chooser=1/1" in certificate.detail
    assert "promotions=0" in certificate.detail


def test_duplicate_inference_id_with_same_counts_fails_exact_catalog(monkeypatch):
    original = certifier.counterpressure_result

    def forged_result(request):
        result = original(request)
        if (
            type(result) is CounterpressureCertificate
            and result.inference_id is CounterpressureInference.POSTHOC_INDEPENDENCE
        ):
            return replace(result, inference_id=CounterpressureInference.FINITE_DEPTH_BRANCH)
        return result

    monkeypatch.setattr(certifier, "counterpressure_result", forged_result)
    certificate = certifier.certify_productivity_counterpressure()
    assert certificate.passed is False


def test_production_lean_file_digest_and_theorem_set_are_exact():
    payload = Path(ARTIFACT_NAME).read_bytes()
    assert sha256(payload).hexdigest() == ARTIFACT_SHA256
    text = payload.decode("utf-8", errors="strict")
    declared = tuple(re.findall(
        r"(?m)^[ \t]*(?:theorem|lemma)[ \t]+(THM_D2_[A-Za-z0-9_]+)(?=[ \t:(])",
        _strip_lean_comments(text),
    ))
    assert declared == THEOREM_IDS
    assert "sorry" not in text and "admit" not in text


def test_captured_compile_rejects_wrong_digest_toolchain_and_tcb():
    payload = Path(ARTIFACT_NAME).read_bytes()
    _compile_captured.cache_clear()
    assert _compile_captured(payload, ARTIFACT_SHA256, LEAN_TOOLCHAIN_ID, LEAN_TCB_DIGEST)
    assert not _compile_captured(payload, "0" * 64, LEAN_TOOLCHAIN_ID, LEAN_TCB_DIGEST)
    assert not _compile_captured(payload, ARTIFACT_SHA256, "leanprover/lean4:latest", LEAN_TCB_DIGEST)
    assert not _compile_captured(payload, ARTIFACT_SHA256, LEAN_TOOLCHAIN_ID, "0" * 64)


def test_theorem_name_lookalike_and_source_digest_drift_reject():
    source = counterpressure_basis_source()
    lookalike = replace(
        source,
        theorem_ids=("THM_D2_LEAN_001_finite_strict_descent_lookalike", *source.theorem_ids[1:]),
    )
    with pytest.raises(CounterpressureValidationError, match="basis-source-drift"):
        check_basis_source(lookalike)
    changed = replace(source, artifact_sha256="0" * 64)
    with pytest.raises(CounterpressureValidationError, match="basis-source-drift"):
        check_basis_source(changed)
