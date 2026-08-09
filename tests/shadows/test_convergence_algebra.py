from fractions import Fraction

import pytest

from src.core.completion import make_interval
from src.core.convergence_algebra import cauchy_tail_card, cauchy_tail_certificate, convergence_algebra_checklist, majorant_bound, majorant_bound_card, nested_interval_card, nested_interval_certificate, radius_guard, radius_guard_card
from src.core.ratio import ratio_from_ints


def _samples():
    return tuple(ratio_from_ints(n, d) for n, d in ((1, 1), (3, 2), (7, 4), (15, 8), (31, 16)))


def _intervals():
    return (
        make_interval(Fraction(1), Fraction(2), "i0"),
        make_interval(Fraction(5, 4), Fraction(7, 4), "i1"),
        make_interval(Fraction(11, 8), Fraction(13, 8), "i2"),
    )


def test_cauchy_tail_certificate_records_tail_diameter():
    cert = cauchy_tail_certificate(_samples(), ratio_from_ints(1, 2), 3)
    assert cert.as_dict() == {"tolerance": "1/2", "tail": 3, "max_distance": "3/16", "checked_pairs": 3, "status": "stable", "obstruction": "none"}
    assert cauchy_tail_card(_samples(), ratio_from_ints(1, 2), 3).relation == "stable"


def test_majorant_bound_row_and_card():
    row = majorant_bound("tail-majorant", ratio_from_ints(3, 16), ratio_from_ints(1, 4))
    assert row.as_dict() == {"label": "tail-majorant", "observed": "3/16", "bound": "1/4", "status": "bounded", "obstruction": "none"}
    assert majorant_bound_card("tail-majorant", ratio_from_ints(3, 16), ratio_from_ints(1, 4)).relation == "bounded"


def test_nested_interval_certificate_checks_shrinkage():
    cert = nested_interval_certificate("nested-shrink", _intervals())
    assert cert.as_dict() == {"label": "nested-shrink", "intervals": 3, "final_width": "1/4", "status": "nested", "obstruction": "none"}
    assert nested_interval_card("nested-shrink", _intervals()).relation == "nested"


def test_radius_guard_accepts_inside_and_rejects_outside():
    inside = radius_guard("log1p-radius", ratio_from_ints(1, 2), ratio_from_ints(1))
    outside = radius_guard("log1p-radius", ratio_from_ints(3, 2), ratio_from_ints(1))
    assert inside.as_dict()["status"] == "inside"
    assert outside.as_dict()["obstruction"] == "radius-gap"
    assert radius_guard_card("log1p-radius", ratio_from_ints(1, 2), ratio_from_ints(1)).relation == "inside"


def test_convergence_algebra_rejects_invalid_inputs():
    assert len(convergence_algebra_checklist()) == 4
    with pytest.raises(ValueError):
        cauchy_tail_certificate(_samples(), ratio_from_ints(1), 1)
    with pytest.raises(ValueError):
        nested_interval_certificate("one", _intervals()[:1])
