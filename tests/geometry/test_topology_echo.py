from src.core.topology_echo import (
    deform_shape,
    echo_shape,
    subdivide_corridor,
    topology_echo_checklist,
    topology_echo_shapes,
    topology_echo_summary,
    topology_invariant_rows,
    topology_obstruction_cards,
)


def test_topology_echo_shapes_expose_corridor_and_shell_invariants():
    corridor, corridor_drift, shell, shell_relabel = topology_echo_shapes()
    assert corridor.component_count == corridor_drift.component_count == 1
    assert corridor.boundary_count == corridor_drift.boundary_count == 2
    assert shell.cycle_rank == shell_relabel.cycle_rank == 1
    assert shell.boundary_count == shell_relabel.boundary_count == 0


def test_topology_echo_rows_mark_deformation_invariants():
    rows = topology_invariant_rows()
    assert len(rows) == 4
    assert all(row.status == "invariant" for row in rows)
    assert {row.invariant for row in rows} == {"components", "boundary", "cycle-rank"}


def test_topology_echo_obstruction_cards_mark_non_invariant_deformations():
    cards = topology_obstruction_cards()
    assert [card.status for card in cards] == ["blocked", "blocked"]
    assert [card.obstruction for card in cards] == ["component-split", "cycle-collapse"]
    assert cards[0].before_value == 1 and cards[0].after_value == 2
    assert cards[1].before_value == 1 and cards[1].after_value == 0


def test_topology_echo_summary_and_explicit_deformers():
    shape = echo_shape("line", ("A", "B"), (("A", "B"),))
    drift = subdivide_corridor(shape, ("A", "B"), "X", "line_drift")
    collapsed = deform_shape(shape, {"B": "A"}, "line_collapsed")
    assert drift.boundary_count == 2
    assert collapsed.corridors == ()
    assert topology_echo_summary() == {"shapes": 4, "invariants": 4, "invariant_hits": 4, "obstructions": 2, "blocked": 2, "checklist": 4}
    assert len(topology_echo_checklist()) == 4
