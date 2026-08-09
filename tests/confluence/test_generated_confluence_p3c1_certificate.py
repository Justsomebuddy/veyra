"""Direct certificate and private Lean source tests for P3-C1."""

from hashlib import sha256
from pathlib import Path
import pytest

from src.core.certify_generated_confluence import certify_generated_confluence_p3c1
from src.core.generated_confluence import (
    ARTIFACT_PATH,
    ARTIFACT_SHA256,
    THEOREM_IDS,
    check_generated_confluence_theorem,
    generated_confluence_theorem_source,
    local_nonterminating_countermodel,
)

pytestmark = pytest.mark.requires_lean


def test_direct_level_one_certificate_exact_detail():
    cert = certify_generated_confluence_p3c1()
    assert cert.passed is True and cert.level == 1
    assert cert.name == "generated_confluence_p3c1"
    assert cert.detail == "states=5 edges=5 peaks=2 lean=1 countermodels=10 carry_systems=6 promotions=0"


def test_private_lean_source_is_exact_structural_and_no_axiom():
    source = generated_confluence_theorem_source()
    payload = Path(ARTIFACT_PATH).read_bytes()
    assert sha256(payload).hexdigest() == ARTIFACT_SHA256 == source.artifact_sha256
    assert source.theorem_ids == THEOREM_IDS
    text = payload.decode()
    assert all(name in text for name in ("rankY", "rankZ", "rankW", "pathYQ", "pathZR", "pathQT"))
    assert "sorry" not in text and "admit" not in text
    receipt, phases = check_generated_confluence_theorem(source)
    assert receipt != "0" * 64
    assert tuple(row.phase for row in phases) == ("elan-which", "lean-version", "lean-compile")
    assert all(row.return_code == 0 for row in phases)


def test_exact_nonterminating_countermodel_has_local_joins_but_two_normals():
    row = local_nonterminating_countermodel()
    assert row.edges == (("a", "b"), ("a", "c"), ("b", "a"), ("b", "d"))
    assert row.local_peaks_joinable is True
    assert row.distinct_normal_forms == ("c", "d")
    assert row.globally_confluent is False


def test_formal_toolchain_receipts_are_exact_and_compile_is_fresh(monkeypatch):
    import src.core.generated_confluence_formal as formal

    source = formal.generated_confluence_theorem_source()
    assert source.toolchain_id == formal.TOOLCHAIN_ID
    assert source.elan_sha256 == formal.ELAN_SHA256
    assert source.lean_sha256 == formal.LEAN_SHA256
    assert source.lean_version == formal.LEAN_VERSION
    calls = []
    original = formal.capture_phase

    def counted(*args, **kwargs):
        calls.append(args[0])
        return original(*args, **kwargs)

    monkeypatch.setattr(formal, "capture_phase", counted)
    first = formal.check_generated_confluence_theorem(source)
    second = formal.check_generated_confluence_theorem(source)
    assert first == second
    assert calls == ["lean-compile", "lean-compile"]
    assert tuple(row.phase for row in first[1]) == ("elan-which", "lean-version", "lean-compile")


def test_formal_shared_deadline_and_live_combined_output_cap_fail_closed(monkeypatch):
    import src.core.generated_confluence_formal as formal
    from src.core.generated_confluence import GeneratedConfluenceError

    source = formal.generated_confluence_theorem_source()
    monkeypatch.setattr(formal, "MAX_OUTPUT", 1)
    with pytest.raises(GeneratedConfluenceError, match="attestation-output-limit"):
        formal.check_generated_confluence_theorem(source)
    monkeypatch.setattr(formal, "MAX_OUTPUT", 1024 * 1024)
    monkeypatch.setattr(formal, "TIMEOUT", 0)
    with pytest.raises(GeneratedConfluenceError, match="attestation-timeout"):
        formal.check_generated_confluence_theorem(source)
