import pytest

from src.core.certify_quantum_qft import certify_quantum_qft_period_q8
from src.core.quantum_qft_period import (
    expected_period_frequencies,
    observed_frequencies,
    qft_offset_echo_row,
    qft_period_obstruction_row,
    qft_period_row,
    qft_period_rows,
    qft_period_state,
    quantum_qft_period_summary,
)
from src.core.quantum_veyra import R1


def test_q8_period_rows_map_period_to_frequency_shadow():
    rows = qft_period_rows()
    assert [row.period for row in rows] == [1, 2, 4]
    assert [row.observed_frequencies for row in rows] == [("0",), ("0", "2"), ("0", "1", "2", "3")]
    assert all(row.status == "ready" for row in rows)
    assert all("Shor-scale" in row.boundary for row in rows)


def test_q8_period_state_norms_and_expected_frequency_helper():
    assert qft_period_state(1).norm2() == R1
    assert qft_period_state(2).norm2() == R1
    assert qft_period_state(4).norm2() == R1
    assert expected_period_frequencies(2) == ("0", "2")
    with pytest.raises(ValueError):
        qft_period_state(3)


def test_q8_offset_echo_keeps_measurement_but_loses_phase():
    row = qft_offset_echo_row()
    assert row.status == "ready"
    assert row.frequency_echo is True
    assert row.phase_distinct is True
    assert "phase" in row.witness


def test_q8_false_period_obstruction_leaks_to_odd_frequencies():
    row = qft_period_obstruction_row()
    assert row.status == "ready"
    assert row.expected_frequencies == ("0", "2")
    assert row.observed_frequencies == ("0", "1", "3")
    assert observed_frequencies(qft_period_state(2)) == ("0", "2")


def test_q8_summary_and_certificate_pass():
    assert quantum_qft_period_summary() == {
        "period_rows": 3,
        "ready_period_rows": 3,
        "offset_echo_rows": 1,
        "obstruction_rows": 1,
        "frequency_hits": 3,
        "overclaims": 0,
    }
    cert = certify_quantum_qft_period_q8()
    assert cert.passed is True
    assert "QFT_4" in cert.method
