from src.core.native_number_theorems import (
    euclid_escape_row,
    lean_euclid_bridge_ready,
    native_euclid_mode_row,
    native_euclid_mode_rows,
    native_euclid_rows,
    native_fermat_obstruction_rows,
    native_fermat_phase_row,
    native_fermat_phase_rows,
    native_number_theorem_gaps,
    native_number_theorem_summary,
)


def test_euclid_escape_row_has_remainder_one_for_each_source_prime():
    row = euclid_escape_row((2, 3, 5, 7))
    assert row.status == "certified-shadow"
    assert row.witness == 211
    assert row.remainders == (1, 1, 1, 1)
    assert "not full native prime infinitude" in row.boundary


def test_euclid_escape_blocks_invalid_prime_observer_list():
    row = euclid_escape_row((1, 2))
    assert row.status == "blocked"
    assert row.remainders == ()


def test_native_number_theorem_summary_keeps_gaps_visible():
    summary = native_number_theorem_summary()
    assert summary["rows"] == 3
    assert summary["certified"] == 3
    assert summary["native_rows"] == 3
    assert summary["native_derived"] == 3
    assert summary["fermat_rows"] == 4
    assert summary["fermat_derived"] == 4
    assert summary["fermat_units"] == 13
    assert summary["fermat_blocked"] == 3
    assert summary["open_gaps"] == 3
    assert summary["lean_f002"] is True
    assert "unbounded native Fermat" in "\n".join(native_number_theorem_gaps())
    assert lean_euclid_bridge_ready() is True


def test_native_euclid_rows_are_json_ready():
    rows = native_euclid_rows()
    assert len(rows) == 3
    assert all(row.as_dict()["theorem_id"] == "THM-F002" for row in rows)


def test_native_euclid_mode_rows_derive_lengths_from_modes():
    row = native_euclid_mode_row((2, 3, 5))
    assert row.status == "derived"
    assert row.mode_lengths == (2, 3, 5)
    assert row.witness == 31
    assert row.remainders == (1, 1, 1)
    assert len(native_euclid_mode_rows()) == 3


def test_native_fermat_phase_row_covers_all_units_for_prime_period():
    row = native_fermat_phase_row(5)
    assert row.status == "derived"
    assert row.mode_length == 5
    assert row.unit_lengths == (1, 2, 3, 4)
    assert row.residues == (1, 1, 1, 1)
    assert row.coverage == row.unit_lengths
    assert row.orbit_lengths == (1, 4, 4, 2)
    assert "not unbounded native Fermat" in row.boundary


def test_native_fermat_phase_rows_include_blocked_composite_obstructions():
    rows = native_fermat_phase_rows()
    blocked = native_fermat_obstruction_rows()
    assert [row.period for row in rows] == [2, 3, 5, 7]
    assert all(row.status == "derived" for row in rows)
    assert [row.period for row in blocked] == [1, 4, 6]
    assert all(row.status == "blocked" for row in blocked)


def test_composite_period_rows_exhibit_an_actual_fermat_failure():
    for period, unit, residue in ((4, 2, 0), (6, 2, 2), (9, 2, 4), (561, 3, 375)):
        row = native_fermat_phase_row(period)
        assert row.status == "blocked"
        assert row.unit_lengths == tuple(range(1, period))
        assert row.residues[unit - 1] == residue
        assert f"fails at unit {unit} (residue {residue})" in row.boundary
    assert native_fermat_phase_row(1).boundary == "requires a native closed Mode with period at least 2"


def test_prime_period_rows_carry_lagrange_and_cyclicity_pressure():
    for period in (2, 3, 5, 7, 11, 13):
        row = native_fermat_phase_row(period)
        assert row.status == "derived"
        assert all((period - 1) % length == 0 for length in row.orbit_lengths)
        assert (period - 1) in row.orbit_lengths
