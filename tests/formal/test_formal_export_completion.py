import logging
from pathlib import Path

import src.core.formal_export_completion as completion
from src.core.formal_export_catalog import formal_export_specs
from src.core.formal_export_completion import (
    _mean_balance_completion_row_at,
    completed_formal_export_rows,
    formal_export_completion_summary,
    mean_balance_completion_row,
)
from src.core.formal_export_prep import stable_card_export_prep_rows
from src.core.paths import LEAN_DIR
import pytest

pytestmark = pytest.mark.requires_lean

logger = logging.getLogger(__name__)


def test_completion_row_legacy_positional_constructor_stays_compatible():
    logger.debug("test_completion_row_legacy_positional_constructor_stays_compatible entry")
    row = completion.FormalExportCompletionRow(
        "legacy", "Legacy", "legacy.source", "Lean", "legacy.lean", "LEGACY", (),
        "blocked", "blocked", False, "legacy boundary",
    )
    assert row.boundary == "legacy boundary"
    assert row.artifact_sha256 == ""
    assert row.artifact_digest_status == "unbound"
    logger.debug("test_completion_row_legacy_positional_constructor_stays_compatible exit")


def test_formal_export_catalog_has_unique_stable_order():
    logger.debug("test_formal_export_catalog_has_unique_stable_order entry")
    specs = formal_export_specs()
    ids = tuple(spec.theorem_id for spec in specs)
    symbols = tuple(spec.lean_symbol for spec in specs)
    assert ids == (
        "cyclic-period",
        "pythagorean-separation",
        "polynomial-identity",
        "polynomial-evaluation",
        "linear-equation-solution",
        "probability-complement",
        "probability-union",
        "probability-independence",
        "mean-balance",
        "binomial-symmetry",
        "variance-shift",
        "sss-triangle",
        "sas-triangle",
        "line-shell-intersection",
        "plane-relabel-composition",
        "sampled-continuity",
        "drift-stability",
        "area-additivity",
        "chord-symmetry",
    )
    assert len(set(ids)) == len(ids)
    assert len(set(symbols)) == len(symbols)
    assert len({spec.artifact_sha256 for spec in specs}) == 6
    assert all(len(spec.artifact_sha256) == 64 for spec in specs)
    assert all(spec.theorem_id in {row.theorem_id for row in stable_card_export_prep_rows()} for spec in specs)
    logger.debug("test_formal_export_catalog_has_unique_stable_order exit")


def test_pre_refactor_id_symbol_constants_remain_import_compatible():
    logger.debug("test_pre_refactor_id_symbol_constants_remain_import_compatible entry")
    assert completion.CYCLIC_PERIOD_ID == "cyclic-period"
    assert completion.CYCLIC_PERIOD_SYMBOL == "THM_C001_cyclic_period"
    assert completion.PYTHAGOREAN_SEPARATION_ID == "pythagorean-separation"
    assert completion.PYTHAGOREAN_SEPARATION_SYMBOL == "THM_G001_pythagorean_3_4_5"
    assert completion.POLYNOMIAL_IDENTITY_ID == "polynomial-identity"
    assert completion.POLYNOMIAL_IDENTITY_SYMBOL == "THM_A001_polynomial_identity_coeffs"
    assert completion.POLYNOMIAL_EVALUATION_ID == "polynomial-evaluation"
    assert completion.POLYNOMIAL_EVALUATION_SYMBOL == "THM_A002_polynomial_eval_at_3"
    assert completion.LINEAR_EQUATION_ID == "linear-equation-solution"
    assert completion.LINEAR_EQUATION_SYMBOL == "THM_A003_linear_equation_unique_solution"
    assert completion.PROBABILITY_COMPLEMENT_ID == "probability-complement"
    assert completion.PROBABILITY_COMPLEMENT_SYMBOL == "THM_P001_probability_complement_counts"
    logger.debug("test_pre_refactor_id_symbol_constants_remain_import_compatible exit")


def test_cyclic_period_completion_promotes_existing_prep_candidate():
    prep_ids = {row.theorem_id for row in stable_card_export_prep_rows()}
    rows = {row.theorem_id: row for row in completed_formal_export_rows()}
    row = rows["cyclic-period"]
    assert row.theorem_id == "cyclic-period"
    assert row.theorem_id in prep_ids
    assert row.export_status == "completed"
    assert row.lean_status == "checked"
    assert row.formalized is True
    assert "VeyraCyclic.lean" in row.proof_path
    assert "no claim" in row.boundary


def test_pythagorean_completion_promotes_geometry_prep_candidate():
    prep_ids = {row.theorem_id for row in stable_card_export_prep_rows()}
    rows = {row.theorem_id: row for row in completed_formal_export_rows()}
    row = rows["pythagorean-separation"]
    assert row.theorem_id in prep_ids
    assert row.source_hook == "geometry.pythagorean"
    assert row.export_status == "completed"
    assert row.lean_status == "checked"
    assert row.formalized is True
    assert row.lean_symbol == "THM_G001_pythagorean_3_4_5"
    assert "VeyraGeometry.lean" in row.proof_path
    assert "no claim" in row.boundary


def test_polynomial_completion_promotes_algebra_prep_candidates():
    prep_ids = {row.theorem_id for row in stable_card_export_prep_rows()}
    rows = {row.theorem_id: row for row in completed_formal_export_rows()}
    identity = rows["polynomial-identity"]
    evaluation = rows["polynomial-evaluation"]
    assert identity.theorem_id in prep_ids
    assert evaluation.theorem_id in prep_ids
    assert identity.source_hook == "algebra.polynomial_identity"
    assert evaluation.source_hook == "algebra.polynomial_eval"
    assert identity.export_status == evaluation.export_status == "completed"
    assert identity.lean_status == evaluation.lean_status == "checked"
    assert identity.formalized and evaluation.formalized
    assert identity.lean_symbol == "THM_A001_polynomial_identity_coeffs"
    assert evaluation.lean_symbol == "THM_A002_polynomial_eval_at_3"
    assert "VeyraAlgebra.lean" in identity.proof_path
    assert "VeyraAlgebra.lean" in evaluation.proof_path
    assert "no claim" in identity.boundary
    assert "no claim" in evaluation.boundary


def test_linear_equation_completion_promotes_algebra_prep_candidate():
    prep_ids = {row.theorem_id for row in stable_card_export_prep_rows()}
    rows = {row.theorem_id: row for row in completed_formal_export_rows()}
    row = rows["linear-equation-solution"]
    assert row.theorem_id in prep_ids
    assert row.source_hook == "algebra.linear_solution"
    assert row.export_status == "completed"
    assert row.lean_status == "checked"
    assert row.formalized is True
    assert row.lean_symbol == "THM_A003_linear_equation_unique_solution"
    assert "VeyraAlgebra.lean" in row.proof_path
    assert "no claim" in row.boundary


def test_probability_complement_completion_promotes_probability_candidate():
    prep_ids = {row.theorem_id for row in stable_card_export_prep_rows()}
    rows = {row.theorem_id: row for row in completed_formal_export_rows()}
    row = rows["probability-complement"]
    assert row.theorem_id in prep_ids
    assert row.source_hook == "probability.complement"
    assert row.export_status == "completed"
    assert row.lean_status == "checked"
    assert row.formalized is True
    assert row.lean_symbol == "THM_P001_probability_complement_counts"
    assert "VeyraProbability.lean" in row.proof_path
    assert "no claim" in row.boundary


def test_formal_export_completion_summary_keeps_remaining_boundary():
    logger.debug("test_formal_export_completion_summary_keeps_remaining_boundary entry")
    summary = formal_export_completion_summary()
    assert summary == {
        "candidate_total": 19,
        "completed_candidates": 19,
        "checked_lean_files": 6,
        "formalized_candidates": 19,
        "remaining_prep_ready": 0,
        "overclaims": 0,
    }
    logger.debug("test_formal_export_completion_summary_keeps_remaining_boundary exit")


def test_mean_balance_completion_is_exact_fixed_sample_card():
    logger.debug("test_mean_balance_completion_is_exact_fixed_sample_card entry")
    row = mean_balance_completion_row()
    assert row.theorem_id == "mean-balance"
    assert row.source_hook == "statistics.mean_balance"
    assert row.export_status == "completed"
    assert row.lean_status == "checked"
    assert row.formalized is True
    assert row.lean_symbol == "THM_S001_mean_balance_1_3_5"
    assert row.artifact_digest_status == "matched"
    assert row.proof_path == "proofs/lean/VeyraStatistics.lean"
    assert "fixed finite sample (1,3,5)" in row.boundary
    assert "no claim about general statistics" in row.boundary
    logger.debug("test_mean_balance_completion_is_exact_fixed_sample_card exit")


def test_mean_balance_completion_rejects_comment_only_marker(tmp_path):
    logger.debug("test_mean_balance_completion_rejects_comment_only_marker entry")
    path = tmp_path / "CommentOnly.lean"
    path.write_text("""namespace Veyra
-- theorem THM_S001_mean_balance_1_3_5 : True := by trivial
/- nested comment
/- theorem-like text stays a comment -/
theorem THM_S001_mean_balance_1_3_5 : True := by trivial
-/
end Veyra
""")
    row = _mean_balance_completion_row_at(path)
    assert row.lean_status == "blocked"
    assert row.export_status == "blocked"
    assert row.formalized is False
    logger.debug("test_mean_balance_completion_rejects_comment_only_marker exit")


def test_mean_balance_completion_fails_closed_for_missing_file(tmp_path):
    logger.debug("test_mean_balance_completion_fails_closed_for_missing_file entry")
    row = _mean_balance_completion_row_at(tmp_path / "missing.lean")
    assert row.lean_status == "blocked"
    assert row.export_status == "blocked"
    assert row.formalized is False
    logger.debug("test_mean_balance_completion_fails_closed_for_missing_file exit")


def test_mean_balance_completion_rejects_wrong_statement_before_checker(tmp_path, monkeypatch):
    logger.debug("test_mean_balance_completion_rejects_wrong_statement_with_exact_symbol entry")
    path = tmp_path / "WrongStatement.lean"
    path.write_text("""namespace Veyra
theorem THM_S001_mean_balance_1_3_5 : True := by trivial
end Veyra
""")
    def forbidden_checker(payload, digest):
        logger.error("forbidden_checker called bytes=%d digest=%s", len(payload), digest)
        raise AssertionError("digest-mismatched payload reached Lean checker")

    monkeypatch.setattr(completion, "check_captured_lean_artifact", forbidden_checker)
    row = _mean_balance_completion_row_at(path)
    assert row.lean_status == "blocked"
    assert row.artifact_digest_status == "mismatch"
    assert row.export_status == "blocked"
    assert row.formalized is False
    logger.debug("test_mean_balance_completion_rejects_wrong_statement_with_exact_symbol exit")


def test_mean_balance_swap_compiles_capture_but_blocks_canonical_drift(tmp_path, monkeypatch):
    logger.debug("test_mean_balance_swap_compiles_capture_but_blocks_canonical_drift entry")
    canonical = tmp_path / "SwapTarget.lean"
    canonical.write_bytes((LEAN_DIR / "VeyraStatistics.lean").read_bytes())
    original_check = completion.check_captured_lean_artifact

    def swap_then_check(payload, digest):
        logger.debug("swap_then_check entry bytes=%d digest=%s", len(payload), digest)
        canonical.write_text("""namespace Veyra
theorem THM_S001_mean_balance_1_3_5 : True := by trivial
end Veyra
""")
        result = original_check(payload, digest)
        logger.debug("swap_then_check exit status=%s", result)
        return result

    monkeypatch.setattr(completion, "check_captured_lean_artifact", swap_then_check)
    row = _mean_balance_completion_row_at(canonical)
    assert row.proof_path == str(canonical)
    assert row.lean_status == "checked"
    assert row.artifact_digest_status == "drift"
    assert row.export_status == "blocked"
    assert row.formalized is False
    logger.debug("test_mean_balance_swap_compiles_capture_but_blocks_canonical_drift exit")
