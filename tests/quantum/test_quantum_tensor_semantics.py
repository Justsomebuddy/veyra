from fractions import Fraction

import pytest

from src.core.quantum_tensor_semantics import (
    FINITE_BOUNDARY,
    adjoint,
    apply_unitary,
    born_distribution,
    born_total,
    conjugate,
    inner_product,
    is_normalized,
    tensor_gates,
    tensor_modes,
    unitarity_witness,
)
from src.core.quantum_veyra import (
    A0,
    A1,
    AH,
    QGate,
    QMode,
    QAmp,
    R0,
    R1,
    Rad2,
    q_basis_state,
    q_gate_cnot,
    q_gate_h,
    q_gate_i,
    q_gate_x,
)


def test_conjugation_and_inner_product_are_exact():
    imaginary = QAmp(R0, R1)
    imaginary_half_root = QAmp(R0, Rad2(Fraction(0), Fraction(1, 2)))
    state = QMode(("a", "b"), (AH, imaginary_half_root))
    assert conjugate(imaginary) == QAmp(R0, -R1)
    assert inner_product(state, state) == QAmp(state.norm2())


def test_empty_and_three_factor_tensor_modes_are_normalized():
    scalar = tensor_modes(())
    assert scalar == QMode(("",), (A1,))
    assert is_normalized(scalar)

    plus = q_gate_h().apply(q_basis_state("0"))
    state = tensor_modes((plus, q_basis_state("1"), plus))
    assert len(state.basis) == 8
    assert state.basis[0] == "0⊗0⊗0"
    assert state.basis[-1] == "1⊗1⊗1"
    assert is_normalized(state)


def test_tensor_modes_reject_ambiguous_delimited_basis_labels():
    left = QMode(("a", "a⊗b"), (A1, A0))
    right = QMode(("b⊗c", "c"), (A1, A0))
    with pytest.raises(ValueError, match="delimiter-free"):
        tensor_modes((left, right))
    with pytest.raises(ValueError, match="nonempty"):
        tensor_modes((QMode(("",), (A1,)),))


def test_born_rule_is_exact_and_tensor_multiplicative():
    plus = q_gate_h().apply(q_basis_state("0"))
    half = Rad2(Fraction(1, 2))
    assert born_distribution(plus) == (("0", half), ("1", half))
    assert born_total(plus) == R1

    pair = tensor_modes((plus, plus))
    quarter = Rad2(Fraction(1, 4))
    assert born_distribution(pair) == (
        ("0⊗0", quarter),
        ("0⊗1", quarter),
        ("1⊗0", quarter),
        ("1⊗1", quarter),
    )
    assert born_total(pair) == born_total(plus) * born_total(plus)


@pytest.mark.parametrize("gate", [q_gate_i(), q_gate_x(), q_gate_h(), q_gate_cnot()])
def test_full_exact_unitarity_witness(gate: QGate):
    witness = unitarity_witness(gate)
    assert witness.left_identity
    assert witness.right_identity
    assert witness.status == "proved"
    assert witness.dimension == len(gate.matrix)
    assert witness.boundary == FINITE_BOUNDARY


def test_tensor_gate_unitarity_and_empty_scalar_identity():
    scalar = tensor_gates(())
    assert scalar == QGate("1", ((A1,),))
    assert unitarity_witness(scalar).status == "proved"

    gate = tensor_gates((q_gate_h(), q_gate_x(), q_gate_i()))
    witness = unitarity_witness(gate)
    assert witness.dimension == 8
    assert witness.status == "proved"
    assert adjoint(adjoint(gate)).matrix == gate.matrix


def test_tensor_gate_action_matches_factorwise_action():
    left = q_basis_state("0")
    right = q_basis_state("0")
    product_gate = tensor_gates((q_gate_h(), q_gate_x()))
    joint_result = apply_unitary(product_gate, tensor_modes((left, right)))
    factor_result = tensor_modes((apply_unitary(q_gate_h(), left), apply_unitary(q_gate_x(), right)))
    assert joint_result == factor_result


def test_apply_unitary_preserves_an_unnormalized_exact_norm():
    imaginary = QAmp(R0, R1)
    state = QMode(("0", "1"), (A1, imaginary))
    result = apply_unitary(q_gate_h(), state)
    assert born_total(state) == Rad2(Fraction(2))
    assert born_total(result) == born_total(state)


def test_nonunitary_and_invalid_carriers_fail_closed():
    zero_gate = QGate("zero", ((A0, A0), (A0, A0)))
    assert unitarity_witness(zero_gate).status == "refuted"
    with pytest.raises(ValueError, match="unitarity witness"):
        apply_unitary(zero_gate, q_basis_state("0"))
    with pytest.raises(ValueError, match="square"):
        unitarity_witness(QGate("ragged", ((A1, A0),)))
    with pytest.raises(ValueError, match="unique"):
        born_distribution(QMode(("x", "x"), (A1, A0)))
    with pytest.raises(ValueError, match="same ordered basis"):
        inner_product(QMode(("x",), (A1,)), QMode(("y",), (A1,)))


def test_boundary_blocks_apparatus_and_advantage_claims():
    assert "finite exact" in FINITE_BOUNDARY
    assert "no quantum advantage" in FINITE_BOUNDARY
    assert "apparatus claim" in FINITE_BOUNDARY
