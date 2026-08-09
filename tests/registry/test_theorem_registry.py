from src.core.geometry import TremorCorridor, event_from_ints
from src.core.geometry_theorems import line_shell_intersections, pythagorean_card, sas_card
from src.core.ratio import ratio_from_ints
from src.core.theorem_registry import GEOMETRY_KNOWN_DEFS, check_card, dependency_edges, geometry_theorem_specs, missing_dependencies, registry_summary


def test_geometry_registry_summary_and_edges():
    specs = geometry_theorem_specs()
    summary = registry_summary(specs)
    assert summary.total == 5
    assert summary.dependency_edges == len(dependency_edges(specs))
    assert summary.sage_ready == 5
    assert ("pythagorean-separation", "DEF-088") in dependency_edges(specs)


def test_ready_pythagorean_card_against_dependencies():
    spec = geometry_theorem_specs()["pythagorean-separation"]
    card = pythagorean_card(event_from_ints((0, 0)), event_from_ints((3, 0)), event_from_ints((0, 4)))
    result = check_card(spec, card)
    assert result.status == "ready"
    assert result.missing_dependencies == ()


def test_missing_dependency_blocks_registry_check():
    spec = geometry_theorem_specs()["sas-triangle"]
    left = (event_from_ints((0, 0)), event_from_ints((3, 0)), event_from_ints((0, 4)))
    card = sas_card(left, left)
    known = GEOMETRY_KNOWN_DEFS - {"DEF-087"}
    assert missing_dependencies(spec, known) == ("DEF-087",)
    assert check_card(spec, card, known).obstruction == "missing-dependencies"


def test_card_obstruction_blocks_even_with_dependencies():
    spec = geometry_theorem_specs()["pythagorean-separation"]
    card = pythagorean_card(event_from_ints((0, 0)), event_from_ints((3, 0)), event_from_ints((1, 1)))
    result = check_card(spec, card)
    assert result.status == "blocked"
    assert result.obstruction == "non-right-apex"


def test_line_shell_intersection_registry_ready_for_tangent():
    spec = geometry_theorem_specs()["line-shell-intersection"]
    corridor = TremorCorridor(event_from_ints((5, -1)), event_from_ints((5, 1)), "tangent")
    card = line_shell_intersections(corridor, event_from_ints((0, 0)), ratio_from_ints(25))
    result = check_card(spec, card)
    assert result.status == "ready"
    assert result.relation == "tangent"

from src.core.algebra_analysis_cards import linear_equation_card, polynomial_identity_card
from src.core.equation import LinearEquation, constant, variable
from src.core.polynomial import add_polynomials, polynomial_from_ints
from src.core.theorem_registry import algebra_analysis_theorem_specs, all_theorem_specs


def test_algebra_analysis_registry_specs_join_global_map():
    specs = algebra_analysis_theorem_specs()
    assert "linear-equation-solution" in specs
    assert "area-additivity" in specs
    assert len(all_theorem_specs()) >= len(geometry_theorem_specs()) + len(specs)


def test_linear_and_polynomial_cards_ready_in_registry():
    specs = all_theorem_specs()
    linear = linear_equation_card(LinearEquation(variable(2, 1), constant(7)))
    assert check_card(specs["linear-equation-solution"], linear).status == "ready"
    poly = polynomial_identity_card(add_polynomials(polynomial_from_ints([1, 2]), polynomial_from_ints([3, -2])), polynomial_from_ints([4]))
    assert check_card(specs["polynomial-identity"], poly).status == "ready"

from src.core.cyclic_probability_stats import CyclicPhase, FiniteDistribution, SampleEcho, WeightedOutcome, chord_symmetry_card, mean_balance_card, probability_complement_card
from src.core.theorem_registry import cyclic_probability_statistics_theorem_specs, depth_pack_theorem_specs


def test_cyclic_probability_statistics_specs_join_global_map():
    specs = cyclic_probability_statistics_theorem_specs()
    assert set(specs) == {"cyclic-period", "chord-symmetry", "probability-complement", "mean-balance"}
    assert len(all_theorem_specs()) >= len(geometry_theorem_specs()) + len(algebra_analysis_theorem_specs()) + len(specs)


def test_cyclic_probability_statistics_cards_ready_in_registry():
    specs = all_theorem_specs()
    assert check_card(specs["chord-symmetry"], chord_symmetry_card(CyclicPhase(0, 12), CyclicPhase(3, 12))).status == "ready"
    dist = FiniteDistribution((WeightedOutcome("a", 1, ratio_from_ints(0)), WeightedOutcome("b", 1, ratio_from_ints(1))))
    assert check_card(specs["probability-complement"], probability_complement_card(dist, frozenset({"a"}))).status == "ready"
    assert check_card(specs["mean-balance"], mean_balance_card(SampleEcho((ratio_from_ints(1), ratio_from_ints(3))))).status == "ready"


from src.core.depth_packs import binomial_symmetry_card, independence_card, probability_union_card, variance_shift_card


def test_depth_pack_specs_join_global_map_and_cards_ready():
    specs = all_theorem_specs()
    depth = depth_pack_theorem_specs()
    assert set(depth) == {"binomial-symmetry", "probability-union", "probability-independence", "variance-shift"}
    assert check_card(specs["binomial-symmetry"], binomial_symmetry_card(6, 2)).status == "ready"
    dist = FiniteDistribution(tuple(WeightedOutcome(name, 1, ratio_from_ints(0)) for name in ("00", "01", "10", "11")))
    a = frozenset({"10", "11"})
    b = frozenset({"01", "11"})
    assert check_card(specs["probability-union"], probability_union_card(dist, a, b)).status == "ready"
    assert check_card(specs["probability-independence"], independence_card(dist, a, b)).status == "ready"
    assert check_card(specs["variance-shift"], variance_shift_card(SampleEcho((ratio_from_ints(1), ratio_from_ints(3))), ratio_from_ints(10))).status == "ready"
