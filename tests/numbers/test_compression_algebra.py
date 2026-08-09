from fractions import Fraction

from src.core.compression_algebra import (
    compare_cost_strategies,
    compression_algebra_checklist,
    divide_by_linear_root,
    edit_distance,
    edit_resonance_profile,
    hierarchical_compression_tree,
    polynomial_factor_search,
)
from src.core.compression import CompressionWeights
from src.core.modes import Mode
from src.core.polynomial import polynomial_from_ints
from src.core.ratio import ratio_shadow


def coeffs(poly):
    return [ratio_shadow(item) for item in poly.coefficients]


def test_edit_distance_detects_insert_delete_drift():
    assert edit_distance(tuple("abab"), tuple("abxab")) == 1
    profile = edit_resonance_profile(Mode.from_word("ab"), Mode.from_word("abxab"), max_edits=1)
    assert profile.resonates
    assert profile.obstruction == "edit-drift"
    assert profile.distance == 1
    assert profile.exponent == 2


def test_hierarchical_compression_tree_splits_positive_saving():
    tree = hierarchical_compression_tree(Mode.from_word("ababab"), max_depth=2, max_defects=0)
    assert tree.status == "split"
    assert tree.part == Mode.from_word("ab")
    assert tree.repeats == 3
    assert tree.saving == 4.0
    assert tree.children[0].mode == Mode.from_word("ab")


def test_hierarchical_compression_tree_respects_no_positive_saving():
    tree = hierarchical_compression_tree(Mode.from_word("abac"), max_depth=2, max_defects=1, weights=CompressionWeights(defect_weight=2.0))
    assert tree.status == "leaf"


def test_polynomial_factor_search_finds_native_linear_hits():
    poly = polynomial_from_ints([-1, 0, 1])
    hits = polynomial_factor_search(poly, [Fraction(-1), Fraction(0), Fraction(1)])
    assert [ratio_shadow(hit.root) for hit in hits] == [Fraction(-1), Fraction(1)]
    assert coeffs(hits[0].factor) == [1, 1]
    assert coeffs(hits[1].factor) == [-1, 1]
    assert coeffs(divide_by_linear_root(poly, hits[1].root)) == [1, 1]


def test_compare_cost_strategies_separates_uniform_manual_aura():
    rows = compare_cost_strategies(
        Mode.from_word("ab"),
        Mode.from_word("abac"),
        budget=0.5,
        context=[Mode.from_word("abac")],
        alphabet=("a", "b", "c"),
        manual={("b", "c"): 0.25},
    )
    assert [row.strategy for row in rows] == ["uniform", "manual", "aura"]
    assert [row.profile.resonates for row in rows] == [False, True, True]
    assert [row.best_cost for row in rows] == [1.0, 0.25, 0.25]


def test_compression_algebra_checklist_covers_sprint_b():
    text = "\n".join(compression_algebra_checklist())
    assert "edit insert/delete" in text
    assert "hierarchical compression" in text
    assert "polynomial root/factor" in text
    assert "aura/manual/uniform" in text
