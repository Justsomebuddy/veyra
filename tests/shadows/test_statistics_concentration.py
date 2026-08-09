import pytest

from src.core.ratio import ratio_from_ints, ratio_shadow
from src.core.statistics_concentration import bernoulli_likelihood_row, chebyshev_mean_bound, concentration_bound_card, decision_error_row, hoeffding_exponent_guard, likelihood_ratio_card, statistics_concentration_checklist


def test_chebyshev_bound_card_is_exact_and_informative():
    bound = chebyshev_mean_bound(ratio_from_ints(3, 16), 4, ratio_from_ints(1, 2))
    card = concentration_bound_card(bound)
    assert ratio_shadow(bound.evidence) == ratio_shadow(ratio_from_ints(3, 16))
    assert bound.as_dict()["relation"] == "informative"
    assert card.relation == "informative"


def test_hoeffding_exponent_guard_records_deferred_tail_shadow():
    guard = hoeffding_exponent_guard(4, ratio_from_ints(1, 2), ratio_from_ints(1))
    card = concentration_bound_card(guard)
    assert ratio_shadow(guard.evidence) == 2
    assert guard.obstruction == "tail-exponential-shadow-deferred"
    assert card.relation == "guarded"


def test_bernoulli_likelihood_rows_and_ratio_card():
    likely = bernoulli_likelihood_row(3, 4, ratio_from_ints(3, 4))
    baseline = bernoulli_likelihood_row(3, 4, ratio_from_ints(1, 2))
    card = likelihood_ratio_card(likely, baseline)
    assert ratio_shadow(likely.likelihood) == ratio_shadow(ratio_from_ints(27, 256))
    assert baseline.as_dict()["likelihood"] == "1/16"
    assert card.relation == "left-preferred"


def test_decision_rows_name_false_positive_and_false_negative():
    fp = decision_error_row(ratio_from_ints(3, 4), ratio_from_ints(1, 2), False)
    fn = decision_error_row(ratio_from_ints(1, 4), ratio_from_ints(1, 2), True)
    assert fp.decision == "reject" and fp.outcome == "false-positive"
    assert fn.decision == "accept" and fn.outcome == "false-negative"
    assert fp.as_dict()["obstruction"] == "decision-mismatch"


def test_statistics_concentration_validates_bad_inputs_and_checklist():
    assert len(statistics_concentration_checklist()) == 5
    with pytest.raises(ValueError):
        chebyshev_mean_bound(ratio_from_ints(1), 0, ratio_from_ints(1))
    with pytest.raises(ValueError):
        bernoulli_likelihood_row(5, 4, ratio_from_ints(1, 2))
    with pytest.raises(ValueError):
        decision_error_row(ratio_from_ints(-1), ratio_from_ints(1), False)
