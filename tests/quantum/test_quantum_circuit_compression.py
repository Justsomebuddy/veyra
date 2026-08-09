from src.core.certify_quantum_compression import certify_quantum_circuit_compression_q9
from src.core.quantum_circuit_compression import (
    circuit_compression_checklist,
    circuit_compression_rows,
    circuit_compression_summary,
)


def test_q9_compression_rows_cover_exact_phase_and_observer_reductions():
    rows = circuit_compression_rows()
    assert [row.row_id for row in rows] == [
        "Q9-REDUCE-HH", "Q9-REDUCE-XX", "Q9-REDUCE-SSSS", "Q9-PHASE-XZ-ZX", "Q9-OBS-S-I-Z0", "Q9-OBS-Z-I-ZPLUS",
    ]
    assert all(row.status == "ready" for row in rows)
    assert sum(row.relation == "exact-reduction" for row in rows) == 3
    assert sum(row.relation == "global-phase-normalization" for row in rows) == 1
    assert sum(row.relation == "observer-preserving-reduction" for row in rows) == 2


def test_q9_exact_reductions_save_gates_without_overclaiming():
    by_id = {row.row_id: row for row in circuit_compression_rows()}
    assert by_id["Q9-REDUCE-HH"].exact_equal is True
    assert by_id["Q9-REDUCE-XX"].saved_gates == 2
    assert by_id["Q9-REDUCE-SSSS"].saved_gates == 4
    assert all("finite" in row.boundary for row in by_id.values())


def test_q9_phase_and_observer_rows_keep_correct_boundaries():
    by_id = {row.row_id: row for row in circuit_compression_rows()}
    assert by_id["Q9-PHASE-XZ-ZX"].exact_equal is False
    assert by_id["Q9-PHASE-XZ-ZX"].phase_equal is True
    assert by_id["Q9-OBS-Z-I-ZPLUS"].exact_equal is False
    assert by_id["Q9-OBS-Z-I-ZPLUS"].phase_equal is False
    assert by_id["Q9-OBS-Z-I-ZPLUS"].observer_echo is True
    assert by_id["Q9-OBS-Z-I-ZPLUS"].input_state == "|+>"


def test_q9_summary_checklist_and_certificate_pass():
    assert circuit_compression_summary() == {
        "rows": 6,
        "ready": 6,
        "exact_reductions": 3,
        "phase_normalizations": 1,
        "observer_reductions": 2,
        "saved_gates": 10,
        "overclaims": 0,
    }
    text = "\n".join(circuit_compression_checklist())
    assert "observer-preserving" in text
    assert "no optimality" in text
    cert = certify_quantum_circuit_compression_q9()
    assert cert.passed is True
    assert "compression" in cert.method
