import pytest

from src.core.observer_gap_topology import (
    FiniteDAG,
    base_witness_graphs,
    finite_topological_separation_theorem,
    isolated_extension,
    observer_class_definitions,
    observer_gap_topology_summary,
    topological_baseline_signature,
    topological_order_count,
    topological_order_separation_family,
)


def test_declared_classes_have_an_explicit_factorization_boundary():
    baseline, extended = observer_class_definitions()
    assert baseline.class_id == "S7-degree-factor"
    assert "postprocessor" in baseline.factorization
    assert extended.observables[:-1] == baseline.observables
    assert extended.observables[-1] == "exact topological-order count"
    assert baseline.scope == extended.scope


def test_base_pair_matches_baseline_but_linear_extensions_split():
    connected, split = base_witness_graphs()
    assert topological_baseline_signature(connected) == topological_baseline_signature(split)
    assert topological_order_count(connected) == 1088
    assert topological_order_count(split) == 1120


def test_bounded_isolated_extensions_preserve_every_separation():
    rows = topological_order_separation_family()
    assert [row.isolate_count for row in rows] == list(range(5))
    assert all(row.baseline_equal and row.observer_separates for row in rows)
    base_left, base_right = rows[0].connected_orders, rows[0].split_orders
    for row in rows:
        multiplier = 1
        for value in range(9, 9 + row.isolate_count):
            multiplier *= value
        assert row.connected_orders == base_left * multiplier
        assert row.split_orders == base_right * multiplier


def test_exactly_one_card_states_only_the_bounded_factor_result():
    card = finite_topological_separation_theorem()
    assert card.theorem_id == "THM-S7-001"
    assert card.status == "finite-checked"
    assert len(card.witness_rows) == 5
    assert "0, 1, 2, 3, 4" in card.hypotheses[1]
    assert "no minimality" in card.boundary
    assert "superiority" in card.boundary


def test_summary_is_ready_for_a_small_integration_hook():
    assert observer_gap_topology_summary() == {
        "theorem_id": "THM-S7-001",
        "rows": 5,
        "baseline_equal": 5,
        "observer_separates": 5,
        "status": "finite-checked",
        "bounded": True,
    }


def test_invalid_or_cyclic_graphs_fail_closed():
    with pytest.raises(ValueError, match="unique vertices"):
        topological_order_count(FiniteDAG("duplicate", ("a", "a"), ()))
    with pytest.raises(ValueError, match="acyclic"):
        topological_order_count(FiniteDAG("cycle", ("a", "b"), (("a", "b"), ("b", "a"))))
    with pytest.raises(ValueError, match="between"):
        isolated_extension(base_witness_graphs()[0], 5)
