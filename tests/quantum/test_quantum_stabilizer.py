from src.core.quantum_stabilizer import (
    apply_x,
    logical_observer,
    logical_obstruction_rows,
    pauli_x_rows,
    stabilizer_echo_rows,
    syndrome,
    syndrome_rows,
    quantum_stabilizer_summary,
)


def test_pauli_x_rows_are_involutions():
    rows = pauli_x_rows()
    assert len(rows) == 3
    assert all(row.status == "ready" and row.roundtrip_bits == row.input_bits for row in rows)


def test_syndrome_identifies_single_bit_errors_for_both_logicals():
    rows = syndrome_rows()
    assert len(rows) == 8
    assert all(row.status == "ready" for row in rows)
    assert {(row.error, row.syndrome, row.correction) for row in rows if row.logical == 0} == {
        ("I", (1, 1), "I"), ("X0", (-1, 1), "X0"), ("X1", (-1, -1), "X1"), ("X2", (1, -1), "X2")
    }


def test_syndrome_echo_differs_from_logical_observer():
    rows = stabilizer_echo_rows()
    assert len(rows) == 4
    assert all(row.syndrome_echo and not row.logical_echo and row.status == "ready" for row in rows)


def test_double_errors_are_logical_obstructions():
    rows = logical_obstruction_rows()
    assert len(rows) == 3
    assert all(row.status == "ready" and row.logical_before == 0 and row.logical_after == 1 for row in rows)


def test_low_level_observers_are_deterministic():
    assert syndrome(apply_x("000", (1,))) == (-1, -1)
    assert logical_observer("110") == 1


def test_quantum_stabilizer_summary_blocks_overclaim():
    assert quantum_stabilizer_summary() == {
        "pauli_rows": 3,
        "syndrome_rows": 8,
        "single_error_corrected": 8,
        "echo_split_rows": 4,
        "logical_obstructions": 3,
        "overclaims": 0,
    }
