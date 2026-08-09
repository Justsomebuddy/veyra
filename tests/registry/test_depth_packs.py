from src.core.curriculum_map import sage_export_rows, school_curriculum_nodes
from src.core.cyclic_probability_stats import FiniteDistribution, SampleEcho, WeightedOutcome
from src.core.depth_packs import binomial_symmetry_card, choose_echo, curriculum_sage_export_rows, factorial_echo, independence_card, probability_union_card, theorem_sage_export_rows, variance_shift_card
from src.core.ratio import ratio_from_ints, ratio_shadow
from src.core.theorem_registry import all_theorem_specs


def test_combinatorics_factorial_choose_and_symmetry_card():
    assert ratio_shadow(factorial_echo(5)) == 120
    assert ratio_shadow(choose_echo(6, 2)) == 15
    assert binomial_symmetry_card(6, 2).relation == "symmetric"


def test_probability_union_and_independence_cards():
    dist = FiniteDistribution(tuple(WeightedOutcome(name, 1, ratio_from_ints(0)) for name in ("00", "01", "10", "11")))
    left = frozenset({"10", "11"})
    right = frozenset({"01", "11"})
    assert probability_union_card(dist, left, right).relation == "additive"
    assert independence_card(dist, left, right).relation == "independent"


def test_variance_shift_card():
    sample = SampleEcho((ratio_from_ints(1), ratio_from_ints(3), ratio_from_ints(5)))
    assert variance_shift_card(sample, ratio_from_ints(10)).relation == "invariant"


def test_sage_export_adapters_are_json_ready_rows():
    specs = all_theorem_specs()
    theorem_rows = theorem_sage_export_rows(specs)
    curriculum_rows = curriculum_sage_export_rows(sage_export_rows(school_curriculum_nodes(), specs))
    assert len(theorem_rows) == len(specs)
    assert any(row.name == "pythagorean-separation" and row.domain == "geometry" for row in theorem_rows)
    assert any(row.row_type == "curriculum" and row.hook == "probability.complement" for row in curriculum_rows)
