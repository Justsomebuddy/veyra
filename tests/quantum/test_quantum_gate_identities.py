from src.core.quantum_gate_identities import (
    cnot_conjugation_rows,
    gate_identity_baseline_rows,
    gate_identity_rows,
    gate_phase_equal,
    gate_word,
    q_gate_i2,
    q_gate_s,
    q_gate_z,
    quantum_gate_identity_summary,
)
from src.core.quantum_veyra import AM1, compose_gate, q_gate_cnot, q_gate_i, q_gate_x, tensor_gate


def test_one_qubit_gate_word_identities_are_exact():
    assert gate_word(("H", "H")).matrix == q_gate_i().matrix
    assert gate_word(("X", "X")).matrix == q_gate_i().matrix
    assert gate_word(("Z", "Z")).matrix == q_gate_i().matrix
    assert gate_word(("S", "S")).matrix == q_gate_z().matrix
    assert gate_word(("S", "S", "S", "S")).matrix == q_gate_i().matrix


def test_basis_change_and_anticommutation_rows_are_ready():
    rows = {row.identity_id: row for row in gate_identity_rows()}
    assert rows["QID-HXH-Z"].exact_equal
    assert rows["QID-HZH-X"].exact_equal
    assert not rows["QID-XZ-ANTI"].exact_equal
    assert rows["QID-XZ-ANTI"].phase_equal
    assert gate_phase_equal(compose_gate(q_gate_x(), q_gate_z()), compose_gate(q_gate_z(), q_gate_x()), AM1)


def test_cnot_rows_cover_involution_and_pauli_propagation():
    rows = {row.identity_id: row for row in cnot_conjugation_rows()}
    assert set(rows) == {"QID-CNOT-CNOT", "QID-CNOT-XC", "QID-CNOT-XT"}
    assert all(row.exact_equal and row.status == "ready" for row in rows.values())
    cnot = q_gate_cnot()
    assert compose_gate(cnot, cnot).matrix == q_gate_i2().matrix
    assert rows["QID-CNOT-XC"].right_word == ("X⊗X",)
    assert rows["QID-CNOT-XT"].right_word == ("I⊗X",)


def test_gate_identity_catalog_has_compiler_baselines():
    baselines = gate_identity_baseline_rows()
    assert len(baselines) == 3
    assert all(row.covered_rows == 11 and not row.stronger_claim for row in baselines)
    assert {row.family for row in baselines} == {"classical-matrix-algebra", "clifford-tableau", "compiler-peephole"}


def test_quantum_gate_identity_summary_blocks_overclaim():
    assert quantum_gate_identity_summary() == {
        "rows": 11,
        "ready": 11,
        "exact_identities": 10,
        "phase_identities": 1,
        "cnot_rows": 3,
        "baseline_rows": 3,
        "stronger_claims": 0,
        "overclaims": 0,
    }
