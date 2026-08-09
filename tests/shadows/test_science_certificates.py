from fractions import Fraction

import pytest

from src.core.ratio import ratio_from_ints, ratio_shadow
from src.core.science_certificates import (
    FlowEdge,
    anti_diffusion_obstruction_card,
    finite_conservation_row,
    finite_diffusion_row,
    finite_flow_balance_row,
    ratio_variation,
    science_certificate_checklist,
)


def test_finite_conservation_row_accepts_transfer():
    row = finite_conservation_row("transfer", (ratio_from_ints(3), ratio_from_ints(1)), (ratio_from_ints(2), ratio_from_ints(2)))
    assert row.status == "conserved"
    assert row.obstruction == "none"
    assert row.as_dict()["before_total"] == "4"
    assert ratio_shadow(row.after_total) == 4


def test_flow_balance_allows_only_declared_boundary_imbalance():
    edges = (FlowEdge("source", "a", ratio_from_ints(3)), FlowEdge("a", "sink", ratio_from_ints(3)), FlowEdge("source", "b", ratio_from_ints(2)), FlowEdge("b", "sink", ratio_from_ints(2)))
    row = finite_flow_balance_row("network", edges, frozenset({"source", "sink"}))
    balances = dict(row.balances)
    assert row.status == "boundary-balanced"
    assert ratio_shadow(balances["a"]) == 0
    assert ratio_shadow(balances["b"]) == 0
    assert ratio_shadow(balances["source"]) == -5
    assert ratio_shadow(balances["sink"]) == 5


def test_diffusion_row_contracts_variation():
    row = finite_diffusion_row("average", (ratio_from_ints(0), ratio_from_ints(1)), (ratio_from_ints(1, 2), ratio_from_ints(1, 2)))
    assert row.status == "smoothed"
    assert ratio_shadow(row.before_variation) == 1
    assert ratio_shadow(row.after_variation) == 0


def test_anti_diffusion_obstruction_card_records_growth():
    card = anti_diffusion_obstruction_card()
    assert card.name == "science-anti-diffusion-obstruction"
    assert card.relation == "blocked"
    assert card.obstruction == "variation-growth"


def test_ratio_variation_rejects_empty_observation():
    with pytest.raises(ValueError):
        ratio_variation(())
    assert ratio_shadow(ratio_variation((ratio_from_ints(1, 3), ratio_from_ints(2, 3)))) == Fraction(1, 3)


def test_science_certificate_checklist_names_finite_scope():
    text = "\n".join(science_certificate_checklist())
    assert "finite" in text
    assert "obstruction" in text
    assert len(science_certificate_checklist()) == 4
