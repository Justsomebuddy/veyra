"""Pinned source/toolchain/output/continuity tests for PΩ2."""

from hashlib import sha256
from pathlib import Path
import re
from dataclasses import replace

from src.core.formal_export_catalog import _strip_lean_comments
from src.core.padic_completion import ARTIFACT_PATH, ARTIFACT_SHA256, THEOREM_IDS
from src.core.padic_completion_formal import (
    ELAN_SHA256, LEAN_BINARY_SHA256, LEAN_VERSION, TOOLCHAIN_ID,
    _parse_axiom_rows, capture_generic_source, compile_captured_sources, continuity_holds,
    padic_completion_theorem_source,
)
from src.core.padic_completion_ledger import AXIOM_CLOSURE, compiler_axiom_closure

from padic_completion_fixture import exact_padic_package
from src.core.paths import TMP_DIR
import pytest

pytestmark = pytest.mark.requires_lean

ORACLE_THEOREMS = (
    "THM_POMEGA2_001_prime_lower_bound",
    "THM_POMEGA2_002_stage_modulus_divisibility",
    "THM_POMEGA2_003_reduction_well_formed_congruence",
    "THM_POMEGA2_004_reduction_identity",
    "THM_POMEGA2_005_reduction_composition",
    "THM_POMEGA2_006_carrier_presentation_compatible",
    "THM_POMEGA2_007_universal_realization",
    "THM_POMEGA2_008_coordinate_agreement",
    "THM_POMEGA2_009_joint_separation",
    "THM_POMEGA2_010_relative_uniqueness",
    "THM_POMEGA2_011_zero_family_nonvacuity",
    "THM_POMEGA2_012_one_family_formation",
    "THM_POMEGA2_013_addition_closure",
    "THM_POMEGA2_014_negation_additive_inverse",
    "THM_POMEGA2_015_multiplication_closure",
    "THM_POMEGA2_016_full_commutative_ring",
    "THM_POMEGA2_017_ppcp_introduction",
)
ORACLE_ARTIFACT_SHA256 = "28052d0260b1535e484ddd8e70f97fea945ca3ff9a23c358bb45d209a071a18f"
ORACLE_AXIOMS = (
    (), ("propext",), (), ("propext",), ("propext",), (), (), (),
    ("Quot.sound",), ("Quot.sound",), (), (), (), ("Quot.sound",), (),
    ("Quot.sound",), ("Quot.sound", "propext"),
)


def test_generic_artifact_has_exact_digest_symbols_and_no_placeholders():
    source = padic_completion_theorem_source()
    payload = capture_generic_source(source)
    assert sha256(payload).hexdigest() == ORACLE_ARTIFACT_SHA256
    assert ARTIFACT_SHA256 == ORACLE_ARTIFACT_SHA256 == source.artifact_sha256
    clean = _strip_lean_comments(payload.decode())
    found = tuple(re.findall(
        r"(?m)^[ \t]*(?:theorem|lemma)[ \t]+(THM_POMEGA2_[A-Za-z0-9_]+)(?=[ \t\r\n:(])",
        clean,
    ))
    assert found == ORACLE_THEOREMS == THEOREM_IDS
    assert "sorry" not in clean and "admit" not in clean
    assert "def VeyraCompatibleFamily" in clean and "structure VeyraCompatibleFamily" not in clean
    assert "{a : (n : Nat) -> VeyraZMod hp n //" in clean
    assert "def veyraCanonicalStageRingLaws" in clean
    assert "THM_POMEGA2_017_ppcp_introduction {p : Nat} (hp" in clean
    assert "(ops : VeyraStageRingLaws hp) : VeyraPPCPBundle" not in clean
    assert Path(ARTIFACT_PATH).read_bytes() == payload


def test_toolchain_and_binary_identity_are_literal_pins():
    assert TOOLCHAIN_ID == "leanprover/lean4:v4.30.0-rc2"
    assert LEAN_VERSION == (
        "Lean (version 4.30.0-rc2, x86_64-unknown-linux-gnu, "
        "commit 3dc1a088b6d2d8eafe25a7cd7ec7b58d731bd7cc, Release)\n"
    )
    assert ELAN_SHA256 == "19d38963260cfb376f1aab0f0fbcf4e80ec25c8bd0ba3b1797d95141d56ec55a"
    assert LEAN_BINARY_SHA256 == "3e0d0d3d801675359f2d4cf9815bfdb417b20b92fdd9d48b3b14c95bbae28bbf"


def test_private_compile_has_four_phases_exact_rows_and_axiom_closure():
    package = exact_padic_package()
    generic = capture_generic_source(package.theorem_source)
    before = set(TMP_DIR.glob("pomega2-*"))
    outcome = compile_captured_sources(
        generic, package.prime.generated_witness_bytes, 120, 1024 * 1024,
    )
    after = set(TMP_DIR.glob("pomega2-*"))
    assert outcome.kind is None and outcome.return_codes == (0, 0, 0, 0)
    assert tuple(row.phase for row in outcome.phase_receipts) == (
        "elan-which", "lean-version", "generic-compile", "prime-compile",
    )
    assert outcome.theorem_axiom_rows == tuple(zip(ORACLE_THEOREMS, ORACLE_AXIOMS, strict=True))
    assert outcome.output.count(b"'pomega2PrimeWitness' does not depend on any axioms") == 1
    assert outcome.output.count(b"'veyraCanonicalStageRingLaws' depends on axioms: [propext]") == 1
    assert outcome.output.count(
        b"'pomega2ConcreteCompletion' depends on axioms: [propext, Quot.sound]"
    ) == 1
    assert tuple(sorted({axiom for _, row in outcome.theorem_axiom_rows for axiom in row})) == AXIOM_CLOSURE
    assert compiler_axiom_closure(package.ledger, outcome.theorem_axiom_rows) == AXIOM_CLOSURE
    assert before == after


def test_parser_rejects_duplicate_missing_extra_and_bad_axiom_id():
    package = exact_padic_package()
    generic = capture_generic_source(package.theorem_source)
    outcome = compile_captured_sources(
        generic, package.prime.generated_witness_bytes, 120, 1024 * 1024,
    )
    lines = [line for line in outcome.output.splitlines(keepends=True) if line.startswith(b"'THM_POMEGA2_")]
    assert len(lines) == 17
    assert _parse_axiom_rows(outcome.output + lines[0]) is None
    assert _parse_axiom_rows(outcome.output.replace(lines[0], b"", 1)) is None
    assert _parse_axiom_rows(outcome.output + b"'THM_POMEGA2_999_extra' does not depend on any axioms\n") is None
    assert _parse_axiom_rows(outcome.output.replace(b"[propext]", b"[bad axiom]", 1)) is None


def test_live_combined_output_cap_retains_exact_prefix_and_phase_receipt():
    package = exact_padic_package()
    generic = capture_generic_source(package.theorem_source)
    full = compile_captured_sources(
        generic, package.prime.generated_witness_bytes, 120, 1024 * 1024,
    )
    cap = sum(row.output_bytes for row in full.phase_receipts[:3]) + 1
    limited = compile_captured_sources(generic, package.prime.generated_witness_bytes, 120, cap)
    assert limited.kind.value == "output-limit" and len(limited.output) == cap
    assert sum(row.output_bytes for row in limited.phase_receipts) == cap
    assert limited.phase_receipts[-1].output_digest == sha256(limited.output[-1:]).hexdigest()


def test_tiny_caps_and_tampered_prime_witness_fail_closed():
    package = exact_padic_package()
    generic = capture_generic_source(package.theorem_source)
    for cap in (0, 1, 2, 8):
        outcome = compile_captured_sources(generic, package.prime.generated_witness_bytes, 120, cap)
        assert outcome.kind.value == "output-limit" and len(outcome.output) == cap
    tampered = package.prime.generated_witness_bytes.replace(b"VeyraPrimeWitness 5", b"VeyraPrimeWitness 4")
    outcome = compile_captured_sources(generic, tampered, 120, 1024 * 1024)
    assert outcome.kind.value == "compile-error"


def test_attested_binary_drift_and_shared_deadline_fail_closed(monkeypatch):
    package = exact_padic_package()
    generic = capture_generic_source(package.theorem_source)
    monkeypatch.setattr(
        "src.core.stream_completion_formal_attestation.file_sha", lambda _path: "0" * 64,
    )
    drift = compile_captured_sources(
        generic, package.prime.generated_witness_bytes, 120, 1024 * 1024,
    )
    assert drift.kind.value == "compile-error" and drift.return_codes == ()
    monkeypatch.undo()
    timed = compile_captured_sources(
        generic, package.prime.generated_witness_bytes, 0, 1024 * 1024,
    )
    assert timed.kind.value == "timeout"
    assert timed.phase_receipts == () and timed.return_codes == ()


def test_continuity_binds_generic_and_regenerated_prime_witness():
    package = exact_padic_package()
    generic = capture_generic_source(package.theorem_source)
    assert continuity_holds(generic, package.prime)
    changed = replace(package.prime, generated_witness_bytes=b"foreign")
    assert not continuity_holds(generic, changed)
