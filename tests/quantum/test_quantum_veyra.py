from fractions import Fraction

from src.core.quantum_veyra import (
    R1,
    Rad2,
    bell_state,
    compose_gate,
    is_product_factorable_2q,
    observer_distribution,
    q_basis_state,
    q_gate_h,
    q_gate_i,
    q_gate_x,
    qecho,
    quantum_theorem_cards,
    quantum_veyra_summary,
)


def test_exact_rad2_hadamard_involution():
    assert compose_gate(q_gate_h(), q_gate_h()).matrix == q_gate_i().matrix
    assert compose_gate(q_gate_x(), q_gate_x()).matrix == q_gate_i().matrix


def test_qmode_born_distribution_is_exact():
    plus = q_gate_h().apply(q_basis_state("0"))
    assert plus.norm2() == R1
    assert observer_distribution(plus, "Z") == (("0", Rad2(Fraction(1, 2))), ("1", Rad2(Fraction(1, 2))))


def test_observer_echo_is_basis_dependent():
    zero = q_basis_state("0")
    plus = q_gate_h().apply(zero)
    assert not qecho(zero, plus, "Z")
    assert qecho(zero, plus, "X") is False
    assert observer_distribution(zero, "Z") != observer_distribution(zero, "X")


def test_bell_state_has_factorization_obstruction():
    bell = bell_state()
    assert bell.norm2() == R1
    assert is_product_factorable_2q(bell) is False


def test_quantum_theorem_cards_cover_minimal_seed():
    cards = {card.theorem_id: card for card in quantum_theorem_cards()}
    assert set(cards) == {"Q-HH", "Q-XX", "Q-CNOT-NORM", "Q-BELL-NONFACT", "Q-ZX-SHADOW", "Q-NO-CLONE"}
    assert all(card.status == "ready" for card in cards.values())
    assert cards["Q-NO-CLONE"].relation == "obstruction"
    assert "finite" in cards["Q-NO-CLONE"].boundary


def test_quantum_summary_blocks_overclaim():
    assert quantum_veyra_summary() == {
        "cards": 6,
        "ready": 6,
        "obstructions": 2,
        "overclaims": 0,
        "has_born_shadow": True,
        "has_tensor_seed": True,
    }
