"""Focused X8 coverage for the fixed `choose 6 2 = choose 6 4 = 15` card."""
import hashlib
import logging
from dataclasses import replace
from pathlib import Path

import src.core as core
import src.core.formal_export_completion as completion
from src.core.formal_export_catalog import declares_lean_theorem, formal_export_specs
from src.core.paths import LEAN_DIR
import pytest

pytestmark = pytest.mark.requires_lean

logger = logging.getLogger(__name__)


def test_binomial_symmetry_completion_is_only_the_fixed_card():
    logger.debug("test_binomial_symmetry_completion_is_only_the_fixed_card entry")
    row = completion.binomial_symmetry_completion_row()
    assert row.theorem_id == "binomial-symmetry"
    assert row.source_hook == "combinatorics.binomial_symmetry"
    assert row.lean_symbol == "THM_B001_binomial_symmetry_6_2"
    assert row.proof_path == "proofs/lean/VeyraCombinatorics.lean"
    assert row.export_status == "completed"
    assert row.lean_status == "checked" and row.formalized
    assert "choose 6 2 = choose 6 4 = 15" in row.boundary
    assert "no claim about general binomial symmetry or combinatorics" in row.boundary
    logger.debug("test_binomial_symmetry_completion_is_only_the_fixed_card exit")


def test_binomial_artifact_has_unique_actual_digest_and_recursive_source():
    logger.debug("test_binomial_artifact_has_unique_actual_digest_and_recursive_source entry")
    specs = formal_export_specs()
    spec = next(row for row in specs if row.theorem_id == "binomial-symmetry")
    payload = spec.proof_path.read_bytes()
    text = payload.decode()
    actual = hashlib.sha256(payload).hexdigest()
    assert spec.artifact_sha256 == actual
    assert sum(row.proof_path == spec.proof_path for row in specs) == 1
    assert len({row.proof_path for row in specs}) == 6
    assert "def choose : Nat → Nat → Nat" in text
    assert "| n + 1, k + 1 => choose n k + choose n (k + 1)" in text
    assert declares_lean_theorem(text, spec.lean_symbol)
    logger.debug("test_binomial_artifact_has_unique_actual_digest_and_recursive_source exit")


def test_binomial_constants_path_accessor_and_legacy_dict_are_compatible():
    logger.debug("test_binomial_constants_path_accessor_and_legacy_dict_are_compatible entry")
    assert completion.BINOMIAL_SYMMETRY_ID == "binomial-symmetry"
    assert completion.BINOMIAL_SYMMETRY_SYMBOL == "THM_B001_binomial_symmetry_6_2"
    assert completion.lean_combinatorics_export_path() == LEAN_DIR / "VeyraCombinatorics.lean"
    assert "binomial_symmetry_completion_row" in completion.__all__
    assert core.binomial_symmetry_completion_row is completion.binomial_symmetry_completion_row
    assert core.lean_combinatorics_export_path is completion.lean_combinatorics_export_path
    assert "binomial_symmetry_completion_row" in core.__all__
    row = completion.FormalExportCompletionRow(
        "legacy", "Legacy", "legacy.source", "Lean", "legacy.lean", "LEGACY", (),
        "blocked", "blocked", False, "legacy boundary",
    )
    assert tuple(row.as_dict()) == (
        "theorem_id", "title", "source_hook", "backend", "proof_path", "lean_symbol",
        "artifact_sha256", "artifact_digest_status", "dependencies", "export_status",
        "lean_status", "formalized", "boundary",
    )
    logger.debug("test_binomial_constants_path_accessor_and_legacy_dict_are_compatible exit")


def test_binomial_wrong_statement_blocks_before_lean(tmp_path, monkeypatch):
    logger.debug("test_binomial_wrong_statement_blocks_before_lean entry")
    path = tmp_path / "WrongBinomial.lean"
    path.write_text("""namespace Veyra
theorem THM_B001_binomial_symmetry_6_2 : True := by trivial
end Veyra
""")
    spec = next(row for row in formal_export_specs() if row.theorem_id == "binomial-symmetry")

    def forbidden_checker(payload, digest):
        logger.error("forbidden_checker called bytes=%d digest=%s", len(payload), digest)
        raise AssertionError("tampered combinatorics artifact reached Lean")

    monkeypatch.setattr(completion, "check_captured_lean_artifact", forbidden_checker)
    row = completion._completion_row(replace(spec, proof_path=path))
    assert row.lean_status == "blocked"
    assert row.artifact_digest_status == "mismatch"
    assert row.export_status == "blocked" and not row.formalized
    logger.debug("test_binomial_wrong_statement_blocks_before_lean exit")
