"""Focused X8 coverage for the four fixed closed-arithmetic geometry cards."""
import hashlib
import logging
from dataclasses import replace
from pathlib import Path

import src.core as core
import src.core.formal_export_completion as completion
from src.core.formal_export_catalog import formal_export_specs
from src.core.formal_export_geometry_data import GEOMETRY_FORMAL_EXPORT_ROWS
from src.core.paths import LEAN_DIR
import pytest

pytestmark = pytest.mark.requires_lean

logger = logging.getLogger(__name__)

IDS = (
    "sss-triangle", "sas-triangle", "line-shell-intersection", "plane-relabel-composition",
)
SYMBOLS = (
    "THM_G002_sss_side_squares_shift_10",
    "THM_G003_sas_anchor_3_4_dot_0",
    "THM_G004_diameter_shell_scaled_roots",
    "THM_G005_quarter_turn_after_translation",
)


def test_geometry_wave_rows_have_exact_hooks_dependencies_and_boundaries():
    logger.debug("test_geometry_wave_rows_have_exact_hooks_dependencies_and_boundaries entry")
    accessors = (
        completion.sss_triangle_completion_row,
        completion.sas_triangle_completion_row,
        completion.line_shell_intersection_completion_row,
        completion.plane_relabel_composition_completion_row,
    )
    expected = (
        ("geometry.sss", ("DEF-076", "DEF-079", "DEF-082", "DEF-086")),
        ("geometry.sas", ("DEF-076", "DEF-078", "DEF-079", "DEF-086", "DEF-087")),
        ("geometry.line_shell", ("DEF-077", "DEF-083", "DEF-086", "DEF-089")),
        ("geometry.relabel_compose", ("DEF-076", "DEF-085", "DEF-086", "DEF-090")),
    )
    rows = tuple(accessor() for accessor in accessors)
    assert tuple(row.theorem_id for row in rows) == IDS
    assert tuple(row.lean_symbol for row in rows) == SYMBOLS
    assert tuple((row.source_hook, row.dependencies) for row in rows) == expected
    assert all(row.proof_path == "proofs/lean/VeyraGeometry.lean" for row in rows)
    assert all(row.export_status == "completed" and row.lean_status == "checked" for row in rows)
    assert all(row.formalized and "formalizes only" in row.boundary and "no claim" in row.boundary for row in rows)
    logger.debug("test_geometry_wave_rows_have_exact_hooks_dependencies_and_boundaries exit")


def test_geometry_source_pins_exact_fixed_literals_without_variables():
    logger.debug("test_geometry_source_pins_exact_fixed_literals_without_variables entry")
    text = (LEAN_DIR / "VeyraGeometry.lean").read_text()
    assert "((0 : Int) - 3) * (0 - 3)" in text
    assert "((10 : Int) - 13) * (10 - 13)" in text
    assert "(13 - 10) * (10 - 10) + (10 - 10) * (14 - 10) = 0" in text
    assert "t=1/4 and t=3/4" in text
    assert "(-10 : Int) * 4 + 20 * 1 = (-5) * 4" in text
    assert "(-10 : Int) * 4 + 20 * 3 = 5 * 4" in text
    assert "(-((3 : Int) - 2), 2 + 1) = (-1, 3)" in text
    assert all(f"theorem {symbol} :" in text for symbol in SYMBOLS)
    assert all("∀" not in line and "forall" not in line for line in text.splitlines())
    logger.debug("test_geometry_source_pins_exact_fixed_literals_without_variables exit")


def test_g001_through_g005_share_one_actual_whole_file_digest():
    logger.debug("test_g001_through_g005_share_one_actual_whole_file_digest entry")
    specs = {spec.theorem_id: spec for spec in formal_export_specs()}
    rows = (specs["pythagorean-separation"], *(specs[name] for name in IDS))
    payload = (LEAN_DIR / "VeyraGeometry.lean").read_bytes()
    actual = hashlib.sha256(payload).hexdigest()
    assert len({row.proof_path for row in rows}) == 1
    assert {row.artifact_sha256 for row in rows} == {actual}
    assert tuple(item[0] for item in GEOMETRY_FORMAL_EXPORT_ROWS) == IDS
    logger.debug("test_g001_through_g005_share_one_actual_whole_file_digest exit")


def test_geometry_constants_accessors_and_root_api_are_explicit():
    logger.debug("test_geometry_constants_accessors_and_root_api_are_explicit entry")
    constant_pairs = (
        (completion.SSS_TRIANGLE_ID, completion.SSS_TRIANGLE_SYMBOL),
        (completion.SAS_TRIANGLE_ID, completion.SAS_TRIANGLE_SYMBOL),
        (completion.LINE_SHELL_INTERSECTION_ID, completion.LINE_SHELL_INTERSECTION_SYMBOL),
        (completion.PLANE_RELABEL_COMPOSITION_ID, completion.PLANE_RELABEL_COMPOSITION_SYMBOL),
    )
    names = (
        "sss_triangle_completion_row", "sas_triangle_completion_row",
        "line_shell_intersection_completion_row", "plane_relabel_composition_completion_row",
    )
    assert constant_pairs == tuple(zip(IDS, SYMBOLS, strict=True))
    assert all(name in completion.__all__ and name in core.__all__ for name in names)
    assert all(getattr(core, name) is getattr(completion, name) for name in names)
    logger.debug("test_geometry_constants_accessors_and_root_api_are_explicit exit")


def test_geometry_wrong_statement_blocks_before_lean(tmp_path, monkeypatch):
    logger.debug("test_geometry_wrong_statement_blocks_before_lean entry")
    path = tmp_path / "WrongGeometry.lean"
    path.write_text("""namespace Veyra
theorem THM_G004_diameter_shell_scaled_roots : True := by trivial
end Veyra
""")
    spec = next(row for row in formal_export_specs() if row.theorem_id == "line-shell-intersection")

    def forbidden_checker(payload, digest):
        logger.error("forbidden_checker called bytes=%d digest=%s", len(payload), digest)
        raise AssertionError("tampered geometry artifact reached Lean")

    monkeypatch.setattr(completion, "check_captured_lean_artifact", forbidden_checker)
    row = completion._completion_row(replace(spec, proof_path=path))
    assert row.lean_status == "blocked"
    assert row.artifact_digest_status == "mismatch"
    assert row.export_status == "blocked" and not row.formalized
    logger.debug("test_geometry_wrong_statement_blocks_before_lean exit")
