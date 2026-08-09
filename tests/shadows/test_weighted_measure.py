from fractions import Fraction

import pytest

from src.core.ratio import ratio_shadow
from src.core.weighted_measure import (
    coverage_row,
    finite_additivity_row,
    mass_of,
    overlap_gap_card,
    pushforward_by_tact,
    weighted_echo_measure,
    weighted_measure_checklist,
)


def test_weighted_echo_measure_normalizes_atom_masses():
    measure = weighted_echo_measure()
    assert measure.total_weight == 6
    assert ratio_shadow(mass_of(measure, frozenset({"alpha"}))) == Fraction(1, 6)
    assert ratio_shadow(mass_of(measure, frozenset({"beta", "gamma"}))) == Fraction(5, 6)


def test_coverage_row_records_complement_mass():
    row = coverage_row(weighted_echo_measure(), "alpha-beta", frozenset({"alpha", "beta"}))
    assert row.as_dict()["mass"] == "1/2"
    assert row.as_dict()["complement"] == "1/2"
    assert row.status == "covered"


def test_disjoint_finite_additivity_is_exact():
    row = finite_additivity_row(weighted_echo_measure(), "partition", frozenset({"alpha"}), frozenset({"beta", "gamma"}))
    assert row.relation == "additive"
    assert row.obstruction == "none"
    assert ratio_shadow(row.union_mass) == 1
    assert ratio_shadow(row.intersection_mass) == 0


def test_overlap_gap_card_blocks_naive_additivity():
    card = overlap_gap_card(weighted_echo_measure())
    assert card.name == "weighted-measure-overlap-gap"
    assert card.relation == "blocked-naive"
    assert card.obstruction == "overlap-mass"


def test_pushforward_by_tact_preserves_group_mass():
    rows = {row.target: row for row in pushforward_by_tact(weighted_echo_measure())}
    assert rows["warm"].source_names == ("alpha",)
    assert rows["cool"].source_names == ("beta", "gamma")
    assert ratio_shadow(rows["warm"].target_mass) == Fraction(1, 6)
    assert ratio_shadow(rows["cool"].target_mass) == Fraction(5, 6)
    assert all(row.status == "preserved" for row in rows.values())


def test_weighted_measure_rejects_unknown_event_names():
    with pytest.raises(ValueError):
        mass_of(weighted_echo_measure(), frozenset({"delta"}))
    assert len(weighted_measure_checklist()) == 4
