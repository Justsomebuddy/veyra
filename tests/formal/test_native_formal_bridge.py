from pathlib import Path

from src.core.native_formal_bridge import intrinsic_arithmetic_lean_status, native_formal_bridge_report
from src.core.semantic_kernel import evaluate_native
from src.core.paths import LEAN_DIR
import pytest

pytestmark = pytest.mark.requires_lean


def test_native_semantics_are_checked_generally_in_lean():
    report = native_formal_bridge_report()
    assert report.status == "checked"
    assert report.theorem_ids == tuple(f"THM-R4-{index:03d}" for index in range(1, 8))
    assert "Rez/Nod/Tact/Breath/Mode syntax" in report.semantic_scope
    assert "breath contiguity" in report.semantic_scope
    assert "anchored silence" in report.semantic_scope
    assert "echo mismatch obstruction" in report.semantic_scope
    assert "general over labels and tact lists" in report.boundary
    assert "not a proof of every shadow module" in report.boundary
    assert intrinsic_arithmetic_lean_status() == "checked"
    native_source = Path(report.path).read_text(encoding="utf-8")
    arithmetic_source = (LEAN_DIR / "VeyraNativeArithmetic.lean").read_text(encoding="utf-8")
    assert all(f"theorem THM_R4_{index:03d}" in native_source for index in range(1, 8))
    assert all(f"theorem THM_R3_{index:03d}" in arithmetic_source for index in range(1, 3))


def test_python_echo_mismatch_matches_the_named_lean_obstruction_law():
    source = "echo(mode(breath(tact(nod:a,nod:a))),mode(breath(tact(nod:b,nod:b))),observer:boundary)"
    result = evaluate_native(source)
    lean_source = (LEAN_DIR / "VeyraNativeSemantics.lean").read_text(encoding="utf-8")
    assert result.status == "blocked" and result.obstruction == "echo mismatch"
    assert 'blocked "echo mismatch"' in lean_source
    assert "theorem THM_R4_006_boundary_mismatch_blocks" in lean_source
