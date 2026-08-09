from src.core.native_geometry_derivations import native_axis_breath, native_geometry_derivation_rows, native_geometry_derivation_summary, native_right_corner_row
from src.core.native_runtime import Breath, NativeObstruction, observe_native


def test_native_axis_breath_derives_length_by_observer():
    row = native_axis_breath("x", 3)
    assert isinstance(row, Breath)
    assert observe_native(row, "length") == 3


def test_native_axis_breath_blocks_nonpositive_lengths():
    row = native_axis_breath("x", 0)
    assert isinstance(row, NativeObstruction)
    assert row.reason == "nonpositive-length"


def test_native_right_corner_row_derives_3_4_5():
    row = native_right_corner_row(3, 4)
    assert row.status == "derived"
    assert row.leg_lengths == (3, 4)
    assert row.hypotenuse == 5
    assert row.leg_square_sum == 25
    assert row.hyp_square == 25
    assert "not a full geometry theorem" in row.boundary


def test_native_geometry_derivation_summary_counts_finite_rows():
    rows = native_geometry_derivation_rows()
    assert [row.hypotenuse for row in rows] == [5, 13, 17]
    assert native_geometry_derivation_summary() == {"rows": 3, "derived": 3, "finite_only": True}
