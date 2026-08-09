"""Digest, Lean, and suite-binding regressions for bounded I1."""

import hashlib
import logging
from pathlib import Path

import src.core.certify_infinity_i1 as certificate
from src.core.paths import LEAN_DIR
import pytest

pytestmark = pytest.mark.requires_lean

logger = logging.getLogger(__name__)


def test_i1_lean_evidence_binds_full_sha_ordered_symbols_and_compile():
    logger.debug("test_i1_lean_evidence_binds_full_sha_ordered_symbols_and_compile entry")
    evidence = certificate.observer_infinity_lean_evidence()
    actual = hashlib.sha256(certificate.lean_coherent_towers_path().read_bytes()).hexdigest()
    assert evidence.expected_sha256 == evidence.actual_sha256 == actual
    assert actual == certificate.I1_LEAN_SHA256
    assert evidence.digest_status == "matched" and evidence.lean_status == "checked"
    assert evidence.symbols == certificate.I1_LEAN_SYMBOLS
    assert len(evidence.symbols) == 4 and evidence.symbols_exact and evidence.continuous
    logger.debug("test_i1_lean_evidence_binds_full_sha_ordered_symbols_and_compile exit")


def test_i1_certificate_has_exact_finite_rows_and_four_lean_theorems():
    logger.debug("test_i1_certificate_has_exact_finite_rows_and_four_lean_theorems entry")
    result = certificate.certify_observer_infinity_i1()
    assert result.name == "observer_infinity_i1"
    assert result.level == 1 and result.passed
    assert "finite prefix coherence" in result.method
    assert "classical p-adic residue shadows" in result.method
    assert "all-depth Lean hypothesis" in result.method
    assert result.detail == "prefix_depth=6 p5_levels=4 obstructions=2 lean=4/4"
    logger.debug("test_i1_certificate_has_exact_finite_rows_and_four_lean_theorems exit")


def test_i1_digest_tamper_blocks_before_captured_compiler(tmp_path, monkeypatch):
    logger.debug("test_i1_digest_tamper_blocks_before_captured_compiler entry")
    path = tmp_path / "TamperedI1.lean"
    path.write_bytes(certificate.lean_coherent_towers_path().read_bytes() + b"\n-- tamper\n")

    def forbidden_checker(payload: bytes, digest: str) -> str:
        logger.error("forbidden_checker called bytes=%d digest=%s", len(payload), digest)
        raise AssertionError("digest-mismatched I1 bytes reached Lean")

    monkeypatch.setattr(certificate, "check_captured_lean_artifact", forbidden_checker)
    evidence = certificate._observer_infinity_lean_evidence_at(path)
    assert evidence.digest_status == "mismatch" and evidence.lean_status == "blocked"
    assert not evidence.symbols_exact and not evidence.continuous
    logger.debug("test_i1_digest_tamper_blocks_before_captured_compiler exit")


def test_i1_symbol_substitution_blocks_before_captured_compiler(tmp_path, monkeypatch):
    logger.debug("test_i1_symbol_substitution_blocks_before_captured_compiler entry")
    payload = certificate.lean_coherent_towers_path().read_bytes().replace(
        certificate.I1_LEAN_SYMBOLS[2].encode(), b"THM_I1_003_substituted", 1
    )
    path = tmp_path / "SubstitutedI1.lean"
    path.write_bytes(payload)
    digest = hashlib.sha256(payload).hexdigest()

    def forbidden_checker(compiled_payload: bytes, expected: str) -> str:
        logger.error("forbidden_checker called bytes=%d digest=%s", len(compiled_payload), expected)
        raise AssertionError("symbol-substituted I1 bytes reached Lean")

    monkeypatch.setattr(certificate, "check_captured_lean_artifact", forbidden_checker)
    evidence = certificate._observer_infinity_lean_evidence_at(path, digest)
    assert evidence.digest_status == "matched" and evidence.lean_status == "blocked"
    assert not evidence.symbols_exact and not evidence.continuous
    logger.debug("test_i1_symbol_substitution_blocks_before_captured_compiler exit")


def test_i1_extra_symbol_blocks_before_captured_compiler(tmp_path, monkeypatch):
    logger.debug("test_i1_extra_symbol_blocks_before_captured_compiler entry")
    payload = certificate.lean_coherent_towers_path().read_bytes() + (
        b"\ntheorem THM_I1_999_extra : True := by trivial\n"
    )
    path = tmp_path / "ExtraSymbolI1.lean"
    path.write_bytes(payload)

    def forbidden_checker(compiled_payload: bytes, expected: str) -> str:
        logger.error("forbidden_checker called bytes=%d digest=%s", len(compiled_payload), expected)
        raise AssertionError("extra-symbol I1 bytes reached Lean")

    monkeypatch.setattr(certificate, "check_captured_lean_artifact", forbidden_checker)
    evidence = certificate._observer_infinity_lean_evidence_at(
        path, hashlib.sha256(payload).hexdigest()
    )
    assert evidence.digest_status == "matched" and evidence.lean_status == "blocked"
    assert not evidence.symbols_exact
    logger.debug("test_i1_extra_symbol_blocks_before_captured_compiler exit")


def test_i1_reread_continuity_blocks_post_capture_swap(tmp_path, monkeypatch):
    logger.debug("test_i1_reread_continuity_blocks_post_capture_swap entry")
    path = tmp_path / "SwappedI1.lean"
    path.write_bytes(certificate.lean_coherent_towers_path().read_bytes())

    def swap_after_capture(payload: bytes, digest: str) -> str:
        logger.debug("swap_after_capture bytes=%d digest=%s", len(payload), digest)
        path.write_bytes(payload + b"\n-- swapped after capture\n")
        return "checked"

    monkeypatch.setattr(certificate, "check_captured_lean_artifact", swap_after_capture)
    evidence = certificate._observer_infinity_lean_evidence_at(path)
    assert evidence.digest_status == "matched" and evidence.symbols_exact
    assert evidence.lean_status == "blocked" and not evidence.continuous
    logger.debug("test_i1_reread_continuity_blocks_post_capture_swap exit")


def test_i1_lean_separates_arbitrary_tower_from_coherence_hypothesis():
    logger.debug("test_i1_lean_separates_arbitrary_tower_from_coherence_hypothesis entry")
    source = (LEAN_DIR / "VeyraCoherentTowers.lean").read_text(encoding="utf-8")
    assert "abbrev PrefixTower" in source and "def PrefixCoherent" in source
    assert "structure PrefixTower" not in source
    assert "(coherent : PrefixCoherent tower)" in source
    assert "(tower : PrefixTower α) (conflict : PrefixConflict tower)" in source
    assert "Nat.mod_mod_of_dvd" in source
    logger.debug("test_i1_lean_separates_arbitrary_tower_from_coherence_hypothesis exit")
