import pytest

from src.core.ratio import ratio_from_ints, ratio_shadow
from src.core.statistics_inference import bernoulli_family, hypothesis_mean_card, interval_contains_shadow, mean_interval, sample_echo_from_ints, standard_error_shadow, statistics_inference_checklist


def test_bernoulli_family_parameters_are_exact():
    family = bernoulli_family(3, 4)
    assert family.status == "finite-shadow"
    assert family.parameter_shadow("p") == "3/4"
    assert family.parameter_shadow("variance") == "3/16"


def test_mean_interval_contains_center_and_rejects_outside():
    sample = sample_echo_from_ints([1, 2, 3])
    interval = mean_interval(sample, ratio_from_ints(1, 2))
    assert ratio_shadow(interval.center) == 2
    assert interval_contains_shadow(interval, ratio_from_ints(2))
    assert not interval_contains_shadow(interval, ratio_from_ints(3))


def test_hypothesis_and_uncertainty_seed():
    sample = sample_echo_from_ints([1, 2, 3])
    accepted = hypothesis_mean_card(sample, ratio_from_ints(2), ratio_from_ints(0))
    rejected = hypothesis_mean_card(sample, ratio_from_ints(5), ratio_from_ints(1))
    assert accepted.relation == "accepted"
    assert rejected.obstruction == "mean-shift"
    assert ratio_shadow(standard_error_shadow(ratio_from_ints(3, 16), 4)) == ratio_shadow(ratio_from_ints(3, 64))
    assert len(statistics_inference_checklist()) == 4


def test_statistics_seed_validates_bad_inputs():
    with pytest.raises(ValueError):
        bernoulli_family(5, 4)
    with pytest.raises(ValueError):
        sample_echo_from_ints([])
