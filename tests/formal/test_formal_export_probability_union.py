"""Focused X8 regression coverage for the fixed four-outcome union card."""
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


def test_probability_union_completion_is_fixed_count_shadow():
    logger.debug("test_probability_union_completion_is_fixed_count_shadow entry")
    left = frozenset({"10", "11"})
    right = frozenset({"01", "11"})
    assert (len(left | right), len(left & right), len(left), len(right)) == (3, 1, 2, 2)
    row = completion.probability_union_completion_row()
    assert row.theorem_id == "probability-union"
    assert row.source_hook == "probability.union"
    assert row.lean_symbol == "THM_P002_probability_union_counts"
    assert row.proof_path == "proofs/lean/VeyraProbability.lean"
    assert row.export_status == "completed"
    assert row.lean_status == "checked" and row.formalized
    assert "canonical four-outcome" in row.boundary
    assert "no claim about general probability or measure theory" in row.boundary
    logger.debug("test_probability_union_completion_is_fixed_count_shadow exit")


def test_probability_rows_share_exact_whole_file_digest():
    logger.debug("test_probability_rows_share_exact_whole_file_digest entry")
    specs = {spec.theorem_id: spec for spec in formal_export_specs()}
    complement = specs["probability-complement"]
    union = specs["probability-union"]
    actual = hashlib.sha256((LEAN_DIR / "VeyraProbability.lean").read_bytes()).hexdigest()
    assert complement.proof_path == union.proof_path
    assert complement.artifact_sha256 == union.artifact_sha256 == actual
    logger.debug("test_probability_rows_share_exact_whole_file_digest exit")


def test_probability_union_constants_and_public_export_are_exact():
    logger.debug("test_probability_union_constants_and_public_export_are_exact entry")
    assert completion.PROBABILITY_UNION_ID == "probability-union"
    assert completion.PROBABILITY_UNION_SYMBOL == "THM_P002_probability_union_counts"
    assert "probability_union_completion_row" in completion.__all__
    assert core.probability_union_completion_row is completion.probability_union_completion_row
    assert "probability_union_completion_row" in core.__all__
    logger.debug("test_probability_union_constants_and_public_export_are_exact exit")


def test_probability_union_wrong_statement_blocks_before_lean(tmp_path, monkeypatch):
    logger.debug("test_probability_union_wrong_statement_blocks_before_lean entry")
    path = tmp_path / "WrongUnion.lean"
    path.write_text("""namespace Veyra
theorem THM_P002_probability_union_counts : True := by trivial
end Veyra
""")
    spec = next(spec for spec in formal_export_specs() if spec.theorem_id == "probability-union")

    def forbidden_checker(payload, digest):
        logger.error("forbidden_checker called bytes=%d digest=%s", len(payload), digest)
        raise AssertionError("tampered union artifact reached Lean")

    monkeypatch.setattr(completion, "check_captured_lean_artifact", forbidden_checker)
    row = completion._completion_row(replace(spec, proof_path=path))
    assert row.lean_status == "blocked"
    assert row.artifact_digest_status == "mismatch"
    assert row.export_status == "blocked" and not row.formalized
    logger.debug("test_probability_union_wrong_statement_blocks_before_lean exit")
