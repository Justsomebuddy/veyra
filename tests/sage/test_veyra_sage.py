from fractions import Fraction
import doctest

import pytest

import veyra_sage.examples as sage_examples
from veyra_sage.all import VeyraBalances, VeyraModes, VeyraPolynomials, VeyraRatios, sage_certificate_suite

pytestmark = pytest.mark.requires_lean


def test_veyra_modes_parent_constructs_elements():
    parent = VeyraModes("ab")
    ab = parent("ab")
    ba = parent("ba")
    assert ab.word == "ab"
    assert ba.echo_key("cycle") == ab.echo_key("cycle")


def test_veyra_mode_resonance_methods():
    parent = VeyraModes("abc")
    assert parent("ab").cyclic_resonates(parent("baba"))
    assert parent("ab").weighted_resonates(parent("abac"), budget=0.5)


def test_sage_certificate_suite_summary():
    summary = sage_certificate_suite()
    assert summary["failed"] == []
    assert summary["sage_parent_passed"]
    assert summary["sage_balance_passed"]
    assert summary["sage_ratio_passed"]
    assert summary["sage_polynomial_passed"]
    assert summary["sage_school_passed"]
    assert summary["sage_school_summary"]["theorem_specs"] == 19
    assert summary["sage_proof_graph_passed"]
    assert summary["sage_proof_graph_summary"]["curriculum_edges"] == 12
    assert summary["sage_notebook_passed"]
    assert summary["sage_notebook_summary"]["cells"] == 8
    assert summary["sage_domain_notebooks_passed"]
    assert summary["sage_domain_notebook_summary"]["domains"] == 7
    assert summary["sage_card_examples_passed"]
    assert summary["sage_card_examples_summary"]["examples"] == 19
    assert summary["sage_refutations_passed"]
    assert summary["sage_refutations_summary"]["blocked"] == 7
    assert summary["sage_refutation_search_passed"]
    assert summary["sage_refutation_search_summary"]["tried"] == 10
    assert summary["sage_language_passed"]
    assert summary["sage_language_summary"]["mutation_cases"] == 10
    assert summary["sage_language_summary"]["family_cases"] == 20
    assert summary["sage_language_summary"]["property_cases"] == 24
    assert summary["sage_language_summary"]["property_shrunk"] == 24
    assert summary["sage_language_summary"]["coverage_cases"] == 54
    assert summary["sage_language_summary"]["coverage_missed"] == 0
    assert summary["sage_language_summary"]["span_diag_cases"] == 7
    assert summary["sage_language_summary"]["span_diag_missed"] == 0
    assert summary["sage_calculus_depth_passed"]
    assert summary["sage_calculus_depth_summary"]["cards"] == 3
    assert summary["sage_calculus_depth_notebook_summary"]["cells"] == 5
    assert summary["sage_trigonometry_identities_passed"]
    assert summary["sage_trigonometry_identities_summary"]["all_coherent"]
    assert summary["sage_trigonometry_identities_notebook_summary"]["cells"] == 5
    assert summary["sage_linear_algebra_seed_passed"]
    assert summary["sage_linear_algebra_seed_summary"]["determinant_ready"]
    assert summary["sage_linear_algebra_seed_notebook_summary"]["cells"] == 5
    assert summary["sage_statistics_inference_passed"]
    assert summary["sage_statistics_inference_summary"]["uncertainty"] == "3/64"
    assert summary["sage_statistics_inference_notebook_summary"]["cells"] == 5
    assert summary["sage_geometry_theorem_cards_passed"]
    assert summary["sage_geometry_theorem_cards_summary"]["stable_exports"] == 5
    assert summary["sage_geometry_theorem_cards_notebook_summary"]["cells"] == 6
    assert summary["sage_essence_passed"]
    assert summary["sage_essence_summary"]["core_ready"]
    assert summary["sage_essence_summary"]["layers"] == 36
    assert summary["sage_essence_notebook_summary"]["cells"] == 5
    assert summary["sage_proof_discipline_passed"]
    assert summary["sage_proof_discipline_summary"]["exports"] == 19
    assert summary["sage_proof_discipline_notebook_summary"]["cells"] == 5
    assert summary["sage_number_theory_passed"]
    assert summary["sage_number_theory_summary"]["factor_hits"] == 2
    assert summary["sage_number_theory_notebook_summary"]["cells"] == 5
    assert summary["sage_category_like_passed"]
    assert summary["sage_category_like_summary"]["blocked"] == 1
    assert summary["sage_category_like_notebook_summary"]["cells"] == 5
    assert summary["sage_topology_echo_passed"]
    assert summary["sage_topology_echo_summary"]["blocked"] == 2
    assert summary["sage_topology_echo_notebook_summary"]["cells"] == 5
    assert summary["sage_likelihood_geometry_passed"]
    assert summary["sage_likelihood_geometry_summary"]["blocked_domains"] == 1
    assert summary["sage_likelihood_geometry_notebook_summary"]["cells"] == 5
    assert summary["sage_notebook_artifacts_passed"]
    assert summary["sage_notebook_artifacts_summary"]["notebooks"] == 41
    assert summary["sage_intrinsic_vam_passed"]
    assert summary["sage_intrinsic_vam_summary"]["theorems"] == 9
    assert summary["sage_intrinsic_vam_summary"]["lanes"] == 4
    assert summary["sage_intrinsic_vam_summary"]["vami_frames"] == 4
    assert summary["sage_intrinsic_vam_summary"]["presentation_only"] is True
    assert summary["sage_intrinsic_vam_summary"]["evidence_accepted"] is False
    assert summary["sage_intrinsic_vam_summary"]["promotion_ready"] is False
    assert summary["sage_intrinsic_vam_summary"]["taxonomy_changed"] is False
    assert summary["sage_intrinsic_observer_echo_passed"]
    assert summary["sage_intrinsic_observer_echo_summary"]["theorem"] == "THM-R13-003"
    assert summary["sage_intrinsic_observer_echo_summary"]["contract_promoted"] is True
    assert summary["sage_intrinsic_observer_echo_summary"]["presentation_only"] is True
    assert summary["sage_observer_synthesis_v2_passed"]
    assert summary["sage_observer_synthesis_v2_summary"]["subjects"] == 5
    assert summary["sage_observer_synthesis_v2_summary"]["receipt_rows"] == 10
    assert summary["sage_observer_synthesis_v2_summary"]["presentation_only"] is True
    assert summary["sage_observer_synthesis_v2_summary"]["semantic_replay"] is False
    assert "Veyra modes" in summary["sage_parent"]


def test_veyra_balance_parent_signed_arithmetic():
    balances = VeyraBalances("τ")
    total = balances(3) + balances(-2)
    assert total.net_length() == 1
    assert (balances(3) - balances(5)).net_length() == -2
    assert total.opposite().net_length() == -1
    assert total.echo_key("length") == 1
    with pytest.raises(ValueError):
        VeyraBalances("")


def test_veyra_ratio_parent_arithmetic_and_raw_forms():
    ratios = VeyraRatios("τ")
    half = ratios(1, 2)
    third = ratios(Fraction(1, 3))
    raw = half.raw_add(third)
    assert (half + third).shadow() == Fraction(5, 6)
    assert (half - third).shadow() == Fraction(1, 6)
    assert (half * third).shadow() == Fraction(1, 6)
    assert raw.ratio.scale.length == 6
    assert raw.shadow() == Fraction(5, 6)
    assert third.inverse().shadow() == Fraction(3, 1)
    with pytest.raises(ValueError):
        ratios(1, 0)


def test_veyra_polynomial_parent_algebra_and_derivative():
    polys = VeyraPolynomials("τ", "x")
    product = polys([1, 1]) * polys([-1, 1])
    assert product.coefficient_shadows() == [-1, 0, 1]
    assert product.degree() == 2
    assert product.evaluate(3).shadow() == 8
    assert product.derivative().coefficient_shadows() == [0, 2]
    assert product.derivative().evaluate(Fraction(3, 2)).shadow() == 3
    assert (polys([1, 2]) + polys([-1, 3, 0])).coefficient_shadows() == [0, 5]


def test_veyra_sage_examples_doctest():
    result = doctest.testmod(sage_examples, verbose=False)
    assert result.failed == 0
    assert result.attempted >= 10
