from pathlib import Path

from src.core.intrinsic_arithmetic import (
    ProductPlusOneObstructionProof,
    StructuralDivisionProof,
    mode_power,
    one,
    product_plus_one_obstruction,
    structural_divide,
    stitch,
    successor,
    weave,
    zero,
)
from src.core.native_runtime import Mode, NativeObstruction


def recurrence_after(seed: Mode, steps: int) -> Mode:
    current = seed
    for _ in range(steps):
        advanced = successor(current)
        assert isinstance(advanced, Mode)
        current = advanced
    return current


def test_zero_one_successor_and_stitch_are_structural():
    silent = zero()
    unit = one()
    two = successor(unit)
    assert isinstance(two, Mode)
    assert stitch(silent, unit) == unit
    assert stitch(unit, silent) == unit
    assert stitch(unit, unit) == two


def test_weave_and_exact_division_reconstruct_the_dividend():
    unit = one()
    two = recurrence_after(unit, 1)
    three = recurrence_after(unit, 2)
    six = weave(two, three)
    assert isinstance(six, Mode)
    proof = structural_divide(six, two)
    assert isinstance(proof, StructuralDivisionProof)
    assert proof.status == "exact"
    assert proof.quotient.breath == three.breath
    assert proof.residual.breath == zero().breath
    assert proof.reconstructs
    assert proof.reconstructed == six


def test_structural_division_preserves_non_silent_residual():
    unit = one()
    two = recurrence_after(unit, 1)
    seven = recurrence_after(unit, 6)
    proof = structural_divide(seven, two)
    assert proof.status == "residual"
    assert proof.residual.breath == unit.breath
    assert proof.reconstructs
    assert proof.reconstructed == seven


def test_zero_divisor_is_a_first_class_obstruction():
    proof = structural_divide(one(), zero())
    assert proof.status == "blocked"
    assert isinstance(proof.obstruction, NativeObstruction)
    assert proof.obstruction.reason == "zero-divisor"
    assert not proof.reconstructs


def test_structural_power_uses_recurrence_iteration():
    unit = one()
    two = recurrence_after(unit, 1)
    three = recurrence_after(unit, 2)
    eight = recurrence_after(unit, 7)
    raised = mode_power(two, three)
    assert isinstance(raised, Mode)
    assert raised.breath == eight.breath
    assert mode_power(two, zero()) == unit


def test_product_plus_one_escape_returns_checked_witnesses():
    unit = one()
    two = recurrence_after(unit, 1)
    three = recurrence_after(unit, 2)
    seven = recurrence_after(unit, 6)
    proof = product_plus_one_obstruction(two, three)
    assert isinstance(proof, ProductPlusOneObstructionProof)
    assert proof.status == "witnessed"
    assert proof.escaped
    assert proof.candidate.breath == seven.breath
    assert all(witness.blocks_resonance for witness in proof.witnesses)
    assert all(witness.division.reconstructs for witness in proof.witnesses)
    assert all(witness.division.residual.breath == unit.breath for witness in proof.witnesses)


def test_intrinsic_arithmetic_source_has_no_school_arithmetic_shortcuts():
    source = Path("src/core/intrinsic_arithmetic.py").read_text(encoding="utf-8")
    forbidden = ("len" + "(", "in" + "t(", "p" + "ow(", "g" + "cd(", chr(37), '"length"', "'length'")
    assert not {token for token in forbidden if token in source}
