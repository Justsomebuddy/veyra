"""Focused certificate and captured-Lean regressions for finite G4 atlases."""
import hashlib
import logging
from pathlib import Path

import src.core as core
import src.core.certify_observer_patch_atlas as certificate

logger = logging.getLogger(__name__)


def test_g4_lean_evidence_binds_full_bytes_registered_symbols_and_helpers():
    logger.debug("test_g4_lean_evidence_binds_full_bytes_registered_symbols_and_helpers entry")
    evidence = certificate.observer_patch_atlas_lean_evidence()
    actual = hashlib.sha256(certificate.lean_observer_patch_atlas_path().read_bytes()).hexdigest()
    assert evidence.expected_sha256 == evidence.actual_sha256 == actual == certificate.G4_LEAN_SHA256
    assert evidence.digest_status == "matched"
    assert evidence.lean_status == "checked"
    assert evidence.symbols == certificate.G4_LEAN_SYMBOLS
    assert len(evidence.symbols) == 3 and evidence.symbols_exact
    assert evidence.helper_symbols == certificate.G4_LEAN_HELPER_SYMBOLS
    assert len(evidence.helper_symbols) == 2 and evidence.helpers_exact and evidence.continuous
    logger.debug("test_g4_lean_evidence_binds_full_bytes_registered_symbols_and_helpers exit")


def test_g4_certificate_combines_valid_gluing_triangle_and_lean():
    logger.debug("test_g4_certificate_combines_valid_gluing_triangle_and_lean entry")
    result = certificate.certify_observer_patch_atlas_g4()
    assert result.name == "observer_patch_atlas_g4"
    assert result.passed and result.level == 1
    assert "exact gluing" in result.method and "triangle" in result.method
    assert result.detail == "valid_gluing=True triangle_obstructions=1 nonunique=2 lean=3/3 helpers=2/2"
    logger.debug("test_g4_certificate_combines_valid_gluing_triangle_and_lean exit")


def test_g4_digest_tamper_blocks_before_lean(tmp_path, monkeypatch):
    logger.debug("test_g4_digest_tamper_blocks_before_lean entry")
    path = tmp_path / "TamperedG4.lean"
    path.write_bytes(certificate.lean_observer_patch_atlas_path().read_bytes() + b"\n-- tamper\n")

    def forbidden_checker(payload: bytes, digest: str) -> str:
        logger.error("forbidden_checker called bytes=%d digest=%s", len(payload), digest)
        raise AssertionError("digest-mismatched G4 bytes reached Lean")

    monkeypatch.setattr(certificate, "check_captured_lean_artifact", forbidden_checker)
    evidence = certificate._observer_patch_lean_evidence_at(path)
    assert evidence.digest_status == "mismatch"
    assert evidence.lean_status == "blocked"
    assert not evidence.symbols_exact and not evidence.helpers_exact and not evidence.continuous
    logger.debug("test_g4_digest_tamper_blocks_before_lean exit")


def test_g4_reread_continuity_blocks_post_capture_swap(tmp_path, monkeypatch):
    logger.debug("test_g4_reread_continuity_blocks_post_capture_swap entry")
    path = tmp_path / "SwappedG4.lean"
    path.write_bytes(certificate.lean_observer_patch_atlas_path().read_bytes())

    def swap_after_capture(payload: bytes, digest: str) -> str:
        logger.debug("swap_after_capture bytes=%d digest=%s", len(payload), digest)
        path.write_bytes(payload + b"\n-- swapped after capture\n")
        return "checked"

    monkeypatch.setattr(certificate, "check_captured_lean_artifact", swap_after_capture)
    evidence = certificate._observer_patch_lean_evidence_at(path)
    assert evidence.digest_status == "matched"
    assert evidence.symbols_exact
    assert evidence.helpers_exact
    assert evidence.lean_status == "blocked" and not evidence.continuous
    logger.debug("test_g4_reread_continuity_blocks_post_capture_swap exit")


def test_g4_public_api_exports_exact_atlas_surface():
    logger.debug("test_g4_public_api_exports_exact_atlas_surface entry")
    expected = {
        "ObserverPatch", "ObserverPatchAtlas", "LocalObserverSection",
        "ExactGluingCriterion", "TriangleCounterexample", "observer_patch",
        "observer_patch_atlas", "local_observer_section", "local_echo_relation",
        "generated_echo_closure", "pairwise_overlap_rows", "local_contradictions",
        "exact_gluing_relation", "exact_gluing_criterion", "triangle_counterexample",
    }
    assert expected <= set(core.__all__)
    for name in expected:
        assert getattr(core, name) is getattr(__import__("src.core.observer_patch_atlas", fromlist=[name]), name)
    logger.debug("test_g4_public_api_exports_exact_atlas_surface exit")


def test_g4_canonical_path_is_project_relative():
    logger.debug("test_g4_canonical_path_is_project_relative entry")
    assert certificate.lean_observer_patch_atlas_path() == Path(
        "proofs/lean/VeyraObserverPatchAtlas.lean"
    )
    logger.debug("test_g4_canonical_path_is_project_relative exit")
