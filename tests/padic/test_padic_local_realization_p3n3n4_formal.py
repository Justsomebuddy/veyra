"""Pinned private Lean tests for P3-N3/N4."""

from padic_local_realization_fixture import exact_n34_packages
from src.core.padic_local_realization_formal import (
    capture_sources, compile_sources, continuity_holds,
)
import pytest

pytestmark = pytest.mark.requires_lean


def test_private_n3_and_n4_sources_compile_with_exact_axioms():
    _, _, n3, n4 = exact_n34_packages()
    captured3 = capture_sources(n3)
    outcome3 = compile_sources(n3, captured3)
    assert outcome3.kind is None and continuity_holds(n3, captured3)
    assert dict(outcome3.axiom_rows)["THM_P3N3_001_realize_integer_family"] == ("propext",)
    captured4 = capture_sources(n4)
    outcome4 = compile_sources(n4, captured4)
    assert outcome4.kind is None and continuity_holds(n4, captured4)
    rows = dict(outcome4.axiom_rows)
    assert rows["THM_P3N4_001_scoped_joint_separation"] == ("Quot.sound",)
    assert rows["THM_P3N4_PREMISE_001_same_integer_coordinates"] == ("propext",)
