"""Focused X8 coverage for the fixed `(1,3,5)` plus-ten variance card."""
import hashlib
import logging
from dataclasses import replace
from pathlib import Path

import src.core as core
import src.core.formal_export_completion as completion
from src.core.formal_export_catalog import formal_export_specs
from src.core.paths import LEAN_DIR
import pytest

pytestmark = pytest.mark.requires_lean

logger = logging.getLogger(__name__)


def test_variance_shift_completion_is_only_two_fixed_numerators():
    logger.debug("test_variance_shift_completion_is_only_two_fixed_numerators entry")
    original = (1, 3, 5)
    shifted = (11, 13, 15)
    assert sum((value - 3) ** 2 for value in original) == 8
    assert sum((value - 13) ** 2 for value in shifted) == 8
    row = completion.variance_shift_completion_row()
    assert row.theorem_id == "variance-shift"
    assert row.source_hook == "statistics.variance_shift"
    assert row.lean_symbol == "THM_S002_variance_shift_1_3_5_plus_10"
    assert row.proof_path == "proofs/lean/VeyraStatistics.lean"
    assert row.export_status == "completed"
    assert row.lean_status == "checked" and row.formalized
    assert "fixed samples (1,3,5) and (11,13,15)" in row.boundary
    assert "no claim about arbitrary shifts or general statistics" in row.boundary
    logger.debug("test_variance_shift_completion_is_only_two_fixed_numerators exit")


def test_statistics_rows_share_exact_whole_file_digest():
    logger.debug("test_statistics_rows_share_exact_whole_file_digest entry")
    specs = {spec.theorem_id: spec for spec in formal_export_specs()}
    mean = specs["mean-balance"]
    variance = specs["variance-shift"]
    payload = (LEAN_DIR / "VeyraStatistics.lean").read_bytes()
    actual = hashlib.sha256(payload).hexdigest()
    assert mean.proof_path == variance.proof_path
    assert mean.artifact_sha256 == variance.artifact_sha256 == actual
    assert len({spec.proof_path for spec in specs.values()}) == 6
    assert "varianceNumerator135 = varianceNumerator111315" in payload.decode()
    logger.debug("test_statistics_rows_share_exact_whole_file_digest exit")


def test_variance_constants_accessor_and_root_api_are_exact():
    logger.debug("test_variance_constants_accessor_and_root_api_are_exact entry")
    assert completion.VARIANCE_SHIFT_ID == "variance-shift"
    assert completion.VARIANCE_SHIFT_SYMBOL == "THM_S002_variance_shift_1_3_5_plus_10"
    assert "variance_shift_completion_row" in completion.__all__
    assert core.variance_shift_completion_row is completion.variance_shift_completion_row
    assert "variance_shift_completion_row" in core.__all__
    logger.debug("test_variance_constants_accessor_and_root_api_are_exact exit")


def test_variance_wrong_statement_blocks_before_lean(tmp_path, monkeypatch):
    logger.debug("test_variance_wrong_statement_blocks_before_lean entry")
    path = tmp_path / "WrongVariance.lean"
    path.write_text("""namespace Veyra
theorem THM_S002_variance_shift_1_3_5_plus_10 : True := by trivial
end Veyra
""")
    spec = next(row for row in formal_export_specs() if row.theorem_id == "variance-shift")

    def forbidden_checker(payload, digest):
        logger.error("forbidden_checker called bytes=%d digest=%s", len(payload), digest)
        raise AssertionError("tampered statistics artifact reached Lean")

    monkeypatch.setattr(completion, "check_captured_lean_artifact", forbidden_checker)
    row = completion._completion_row(replace(spec, proof_path=path))
    assert row.lean_status == "blocked"
    assert row.artifact_digest_status == "mismatch"
    assert row.export_status == "blocked" and not row.formalized
    logger.debug("test_variance_wrong_statement_blocks_before_lean exit")
