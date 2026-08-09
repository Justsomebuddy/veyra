import pytest

from src.core.ratio import ratio_from_ints, ratio_shadow
from src.core.transcendental_limit import alternating_log1p_envelope, alternating_tail_bound_card, exp_derivative_card, exp_series, log1p_derivative_card, log1p_series, series_value, transcendental_limit_checklist


def test_exp_series_coefficients_and_derivative_shift():
    series = exp_series(4)
    assert [str(ratio_shadow(c)) for c in series.coefficients] == ["1", "1", "1/2", "1/6", "1/24"]
    assert series.order == 4
    assert exp_derivative_card(4).relation == "coherent"


def test_log1p_series_derivative_shift_and_value():
    series = log1p_series(4)
    assert [str(ratio_shadow(c)) for c in series.coefficients] == ["0", "1", "-1/2", "1/3", "-1/4"]
    assert log1p_derivative_card(4).relation == "coherent"
    assert str(ratio_shadow(series_value(series, ratio_from_ints(1, 2)))) == "77/192"


def test_alternating_log1p_envelope_records_tail_bound():
    envelope = alternating_log1p_envelope(4, ratio_from_ints(1, 2))
    assert envelope.as_dict() == {"label": "log1p-alternating-tail", "center": "77/192", "radius": "1/160", "status": "bounded", "obstruction": "none"}
    card = alternating_tail_bound_card(4, ratio_from_ints(1, 2))
    assert card.relation == "bounded"
    assert card.obstruction == "none"


def test_transcendental_limit_rejects_invalid_claims():
    assert len(transcendental_limit_checklist()) == 4
    with pytest.raises(ValueError):
        exp_series(-1)
    with pytest.raises(ValueError):
        alternating_log1p_envelope(4, ratio_from_ints(3, 2))
