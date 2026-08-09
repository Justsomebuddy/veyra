"""Integration coverage for the final four fixed X8 completion rows."""
import hashlib
import logging
import pickle
from dataclasses import replace
from pathlib import Path

import src.core as core
import src.core.formal_export_completion as completion
import src.core.formal_export_remaining_completion as remaining
from src.core.formal_export_catalog import formal_export_specs
from src.core.formal_export_remaining_data import (
    ANALYSIS_ARTIFACT_SHA256, CYCLIC_ARTIFACT_SHA256,
)
from src.core.paths import LEAN_DIR
import pytest

pytestmark = pytest.mark.requires_lean

logger = logging.getLogger(__name__)

IDS = ("sampled-continuity", "drift-stability", "area-additivity", "chord-symmetry")
SYMBOLS = (
    "THM_A004_sampled_continuity_double_0_five_points",
    "THM_A005_square_symmetric_drift_3_steps_1_2_3",
    "THM_A006_identity_midpoint_area_4_4_8",
    "THM_C002_chord_symmetry_12_0_3_9",
)
ACCESSORS = (
    remaining.sampled_continuity_completion_row,
    remaining.drift_stability_completion_row,
    remaining.area_additivity_completion_row,
    remaining.chord_symmetry_completion_row,
)


def test_final_four_append_after_exact_fifteen_row_prefix():
    logger.debug("test_final_four_append_after_exact_fifteen_row_prefix entry")
    ids = tuple(spec.theorem_id for spec in formal_export_specs())
    assert len(ids) == len(set(ids)) == 19
    assert ids[-4:] == IDS
    assert ids[:15] == (
        "cyclic-period", "pythagorean-separation", "polynomial-identity",
        "polynomial-evaluation", "linear-equation-solution", "probability-complement",
        "probability-union", "probability-independence", "mean-balance",
        "binomial-symmetry", "variance-shift", "sss-triangle", "sas-triangle",
        "line-shell-intersection", "plane-relabel-composition",
    )
    logger.debug("test_final_four_append_after_exact_fifteen_row_prefix exit")


def test_existing_and_final_rows_share_actual_rebound_artifact_hashes():
    logger.debug("test_existing_and_final_rows_share_actual_rebound_artifact_hashes entry")
    specs = {spec.theorem_id: spec for spec in formal_export_specs()}
    algebra_ids = (
        "polynomial-identity", "polynomial-evaluation", "linear-equation-solution",
        "sampled-continuity", "drift-stability", "area-additivity",
    )
    cyclic_ids = ("cyclic-period", "chord-symmetry")
    assert {specs[name].artifact_sha256 for name in algebra_ids} == {ANALYSIS_ARTIFACT_SHA256}
    assert {specs[name].artifact_sha256 for name in cyclic_ids} == {CYCLIC_ARTIFACT_SHA256}
    assert hashlib.sha256((LEAN_DIR / "VeyraAlgebra.lean").read_bytes()).hexdigest() == ANALYSIS_ARTIFACT_SHA256
    assert hashlib.sha256((LEAN_DIR / "VeyraCyclic.lean").read_bytes()).hexdigest() == CYCLIC_ARTIFACT_SHA256
    assert len({spec.proof_path for spec in specs.values()}) == 6
    logger.debug("test_existing_and_final_rows_share_actual_rebound_artifact_hashes exit")


def test_final_four_wrappers_preserve_row_runtime_and_public_api():
    logger.debug("test_final_four_wrappers_preserve_row_runtime_and_public_api entry")
    rows = tuple(accessor() for accessor in ACCESSORS)
    assert tuple(row.theorem_id for row in rows) == IDS
    assert tuple(row.lean_symbol for row in rows) == SYMBOLS
    assert tuple((row.source_hook, row.dependencies, row.proof_path) for row in rows) == (
        ("analysis.sampled_continuity", ("DEF-072", "DEF-073", "DEF-086"), "proofs/lean/VeyraAlgebra.lean"),
        ("analysis.drift_stability", ("DEF-074", "DEF-086"), "proofs/lean/VeyraAlgebra.lean"),
        ("analysis.area_additivity", ("DEF-075", "DEF-086"), "proofs/lean/VeyraAlgebra.lean"),
        ("trig.chord_symmetry", ("DEF-106", "DEF-108", "DEF-086"), "proofs/lean/VeyraCyclic.lean"),
    )
    assert all("formalizes only" in row.boundary and "no claim about general" in row.boundary for row in rows)
    assert all(type(row) is completion.FormalExportCompletionRow for row in rows)
    assert all(row.export_status == "completed" and row.lean_status == "checked" for row in rows)
    assert all(row.formalized and row.artifact_digest_status == "matched" for row in rows)
    assert pickle.loads(pickle.dumps(rows[0])) == rows[0]
    assert tuple(rows[0].as_dict()) == (
        "theorem_id", "title", "source_hook", "backend", "proof_path", "lean_symbol",
        "artifact_sha256", "artifact_digest_status", "dependencies", "export_status",
        "lean_status", "formalized", "boundary",
    )
    names = tuple(accessor.__name__ for accessor in ACCESSORS)
    assert all(name in remaining.__all__ and name in core.__all__ for name in names)
    assert all(getattr(core, name) is getattr(remaining, name) for name in names)
    constant_names = tuple(name for stem in (
        "SAMPLED_CONTINUITY", "DRIFT_STABILITY", "AREA_ADDITIVITY", "CHORD_SYMMETRY",
    ) for name in (f"{stem}_ID", f"{stem}_SYMBOL"))
    assert all(name in remaining.__all__ and name in core.__all__ for name in constant_names)
    assert all(getattr(core, name) == getattr(remaining, name) for name in constant_names)
    logger.debug("test_final_four_wrappers_preserve_row_runtime_and_public_api exit")


def test_final_wrapper_forwards_live_completion_checker(monkeypatch):
    logger.debug("test_final_wrapper_forwards_live_completion_checker entry")
    calls: list[str] = []

    def blocking_checker(payload, digest):
        logger.debug("blocking_checker entry bytes=%d digest=%s", len(payload), digest)
        calls.append(digest)
        logger.debug("blocking_checker exit status=blocked")
        return "blocked"

    monkeypatch.setattr(completion, "check_captured_lean_artifact", blocking_checker)
    row = remaining.sampled_continuity_completion_row()
    assert calls == [ANALYSIS_ARTIFACT_SHA256]
    assert row.lean_status == row.export_status == "blocked" and not row.formalized
    logger.debug("test_final_wrapper_forwards_live_completion_checker exit")


def test_final_tamper_blocks_before_lean(tmp_path, monkeypatch):
    logger.debug("test_final_tamper_blocks_before_lean entry")
    path = tmp_path / "WrongRemaining.lean"
    path.write_text("namespace Veyra\ntheorem THM_A006_identity_midpoint_area_4_4_8 : True := by trivial\nend Veyra\n")
    spec = next(spec for spec in formal_export_specs() if spec.theorem_id == "area-additivity")

    def forbidden_checker(payload, digest):
        logger.error("forbidden_checker called bytes=%d digest=%s", len(payload), digest)
        raise AssertionError("tampered final artifact reached Lean")

    monkeypatch.setattr(completion, "check_captured_lean_artifact", forbidden_checker)
    row = completion._completion_row(replace(spec, proof_path=path))
    assert row.artifact_digest_status == "mismatch"
    assert row.lean_status == row.export_status == "blocked" and not row.formalized
    logger.debug("test_final_tamper_blocks_before_lean exit")
