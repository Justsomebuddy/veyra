"""Direct certificate and exact Lean boundary tests for P1-D3."""

from hashlib import sha256
from pathlib import Path
import re

from src.core.all_depth_family import (
    ARTIFACT_NAME, ARTIFACT_SHA256, AXIOM_CLOSURE, LEAN_TCB_DIGEST,
    LEAN_TOOLCHAIN_ID, THEOREM_IDS, check_formal_source,
    periodic_family_formal_source,
)
from src.core.all_depth_family_formal import _compile_captured
from src.core.certify_all_depth_family import certify_all_depth_family_p1d3
from src.core.formal_export_catalog import _strip_lean_comments
import pytest

pytestmark = pytest.mark.requires_lean


def test_direct_level_one_certificate_passes_exact_boundary():
    certificate = certify_all_depth_family_p1d3()
    assert certificate.passed is True and certificate.level == 1
    assert certificate.name == "all_depth_family_p1d3"
    assert certificate.detail == (
        "derived=1 assumed=2 open=1 projections=2 resource=1 unavailable=1 "
        "countermodels=5 promotions=0"
    )


def test_formal_source_digest_theorems_and_axiom_closure_are_exact():
    source = check_formal_source(periodic_family_formal_source())
    payload = Path(ARTIFACT_NAME).read_bytes()
    assert sha256(payload).hexdigest() == ARTIFACT_SHA256 == source.artifact_sha256
    text = payload.decode("utf-8", errors="strict")
    names = tuple(re.findall(
        r"(?m)^[ \t]*(?:theorem|lemma)[ \t]+(THM_D3_[A-Za-z0-9_]+)(?=[ \t\r\n:(])",
        _strip_lean_comments(text),
    ))
    assert names == THEOREM_IDS == source.theorem_ids
    assert AXIOM_CLOSURE == source.axiom_closure == ()
    assert "sorry" not in text and "admit" not in text


def test_captured_compile_rejects_digest_toolchain_and_tcb_drift():
    payload = Path(ARTIFACT_NAME).read_bytes()
    _compile_captured.cache_clear()
    assert _compile_captured(payload, ARTIFACT_SHA256, LEAN_TOOLCHAIN_ID, LEAN_TCB_DIGEST)
    assert not _compile_captured(payload, "0" * 64, LEAN_TOOLCHAIN_ID, LEAN_TCB_DIGEST)
    assert not _compile_captured(payload, ARTIFACT_SHA256, "leanprover/lean4:latest", LEAN_TCB_DIGEST)
    assert not _compile_captured(payload, ARTIFACT_SHA256, LEAN_TOOLCHAIN_ID, "0" * 64)
