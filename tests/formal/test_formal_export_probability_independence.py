"""Focused X8 coverage for the canonical four-outcome independence count card."""
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


def test_probability_independence_completion_is_fixed_count_product():
    logger.debug("test_probability_independence_completion_is_fixed_count_product entry")
    omega = frozenset({"00", "01", "10", "11"})
    left = frozenset({"10", "11"})
    right = frozenset({"01", "11"})
    counts = (len(left & right), len(omega), len(left), len(right))
    assert counts == (1, 4, 2, 2)
    assert counts[0] * counts[1] == counts[2] * counts[3]
    row = completion.probability_independence_completion_row()
    assert row.theorem_id == "probability-independence"
    assert row.source_hook == "probability.independence"
    assert row.lean_symbol == "THM_P003_probability_independence_counts"
    assert row.proof_path == "proofs/lean/VeyraProbability.lean"
    assert row.export_status == "completed"
    assert row.lean_status == "checked" and row.formalized
    assert "canonical four-outcome" in row.boundary
    assert "no claim about general independence, probability, or measure theory" in row.boundary
    logger.debug("test_probability_independence_completion_is_fixed_count_product exit")


def test_all_probability_rows_share_exact_whole_file_digest():
    logger.debug("test_all_probability_rows_share_exact_whole_file_digest entry")
    specs = {spec.theorem_id: spec for spec in formal_export_specs()}
    rows = tuple(specs[name] for name in (
        "probability-complement", "probability-union", "probability-independence",
    ))
    actual = hashlib.sha256((LEAN_DIR / "VeyraProbability.lean").read_bytes()).hexdigest()
    assert len({row.proof_path for row in rows}) == 1
    assert {row.artifact_sha256 for row in rows} == {actual}
    logger.debug("test_all_probability_rows_share_exact_whole_file_digest exit")


def test_probability_independence_constants_and_public_export_are_exact():
    logger.debug("test_probability_independence_constants_and_public_export_are_exact entry")
    assert completion.PROBABILITY_INDEPENDENCE_ID == "probability-independence"
    assert completion.PROBABILITY_INDEPENDENCE_SYMBOL == "THM_P003_probability_independence_counts"
    assert "probability_independence_completion_row" in completion.__all__
    assert core.probability_independence_completion_row is completion.probability_independence_completion_row
    assert "probability_independence_completion_row" in core.__all__
    logger.debug("test_probability_independence_constants_and_public_export_are_exact exit")


def test_probability_independence_wrong_statement_blocks_before_lean(tmp_path, monkeypatch):
    logger.debug("test_probability_independence_wrong_statement_blocks_before_lean entry")
    path = tmp_path / "WrongIndependence.lean"
    path.write_text("""namespace Veyra
theorem THM_P003_probability_independence_counts : True := by trivial
end Veyra
""")
    spec = next(spec for spec in formal_export_specs() if spec.theorem_id == "probability-independence")

    def forbidden_checker(payload, digest):
        logger.error("forbidden_checker called bytes=%d digest=%s", len(payload), digest)
        raise AssertionError("tampered independence artifact reached Lean")

    monkeypatch.setattr(completion, "check_captured_lean_artifact", forbidden_checker)
    row = completion._completion_row(replace(spec, proof_path=path))
    assert row.lean_status == "blocked"
    assert row.artifact_digest_status == "mismatch"
    assert row.export_status == "blocked" and not row.formalized
    logger.debug("test_probability_independence_wrong_statement_blocks_before_lean exit")
