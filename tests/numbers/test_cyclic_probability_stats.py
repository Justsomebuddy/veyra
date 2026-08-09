from src.core.cyclic_probability_stats import CyclicPhase, FiniteDistribution, SampleEcho, WeightedOutcome, chord_symmetry_card, cyclic_chord_echo, expectation, mean_balance_card, phase_advance, phase_distance, phase_period_card, probability_complement_card, probability_of, sample_mean, sample_variance
from src.core.ratio import ratio_from_ints, ratio_shadow


def test_cyclic_phase_period_distance_and_chord_symmetry():
    a = CyclicPhase(1, 12)
    b = CyclicPhase(10, 12)
    assert phase_advance(a, 12).index == 1
    assert phase_distance(a, b) == 3
    assert ratio_shadow(cyclic_chord_echo(a, b)) == ratio_shadow(ratio_from_ints(3, 4))
    assert phase_period_card(a).relation == "periodic"
    assert chord_symmetry_card(a, b).relation == "symmetric"


def test_probability_distribution_exact_event_complement_and_expectation():
    dist = FiniteDistribution((WeightedOutcome("a", 1, ratio_from_ints(0)), WeightedOutcome("b", 3, ratio_from_ints(2)), WeightedOutcome("c", 2, ratio_from_ints(5))))
    assert ratio_shadow(probability_of(dist, frozenset({"b", "c"}))) == ratio_shadow(ratio_from_ints(5, 6))
    assert probability_complement_card(dist, frozenset({"a"})).relation == "complete"
    assert ratio_shadow(expectation(dist)) == ratio_shadow(ratio_from_ints(8, 3))


def test_sample_mean_variance_and_balance_card():
    sample = SampleEcho((ratio_from_ints(1), ratio_from_ints(2), ratio_from_ints(3), ratio_from_ints(4)))
    assert ratio_shadow(sample_mean(sample)) == ratio_shadow(ratio_from_ints(5, 2))
    assert ratio_shadow(sample_variance(sample)) == ratio_shadow(ratio_from_ints(5, 4))
    assert mean_balance_card(sample).relation == "balanced"
