"""Positive laws and narrow claim boundaries for provisional P1-C1."""

from dataclasses import replace
import inspect

from src.core.confluence import (
    compose_diagram_paths, diagram_edge, diagram_path, direct_echo_transport,
    finite_diagram_source, fork_confluence_judgment, fork_join_plan,
    replay_diagram_path, swap_fork_join_plan,
)
from src.core.confluence_types import (
    AlignmentPoint, ConfluenceStatus, HigherConfluence, ScopedFormation,
    TransportMode,
)
from src.core.positive_ontology import ontology_stage
from src.core.positive_ontology_doctrine import p0_observer_doctrine
from src.core.proof_core_types import Pulse, Silence


def direct_fixture(*, mismatch=False, two_observers=False):
    doctrine = p0_observer_doctrine()
    count = 2 if two_observers else 1
    reps = {
        "fork": Pulse(Silence()), "left": Pulse(Silence()),
        "right": Silence() if mismatch else Pulse(Silence()),
        "join": Pulse(Silence()),
    }
    stages = tuple(ontology_stage(name, reps[name], doctrine, count) for name in reps)
    edges = (
        diagram_edge("fl", "fork", "left", ("crest",)),
        diagram_edge("fr", "fork", "right", ("crest",)),
        diagram_edge("lj", "left", "join", ("crest",)),
        diagram_edge("rj", "right", "join", ("crest",)),
    )
    paths = (
        diagram_path("lb", ("fl",), "fork", "left"),
        diagram_path("rb", ("fr",), "fork", "right"),
        diagram_path("ljp", ("lj",), "left", "join"),
        diagram_path("rjp", ("rj",), "right", "join"),
    )
    source = finite_diagram_source(doctrine, "diagram", stages, edges, paths)
    transport = direct_echo_transport(doctrine, ("crest",))
    alignment = (AlignmentPoint(0, 0), AlignmentPoint(1, 1), AlignmentPoint(2, 2))
    plan = fork_join_plan(
        doctrine, source, "fork-plan", "lb", "rb", "ljp", "rjp", alignment, transport
    )
    return doctrine, source, transport, plan


def test_direct_echo_positive_is_exact_fresh_and_nonpromoting():
    doctrine, source, transport, plan = direct_fixture()
    first = fork_confluence_judgment(doctrine, source, plan, transport)
    second = fork_confluence_judgment(doctrine, source, plan, transport)
    assert first.status is second.status is ConfluenceStatus.ESTABLISHED
    assert first.charged_checks == 7
    assert first.transport_cell is not None and second.transport_cell is not None
    assert first.transport_cell.status is ConfluenceStatus.ESTABLISHED
    assert first.transport_cell.trace_digest == second.transport_cell.trace_digest
    assert first.transport_cell.response_rows == second.transport_cell.response_rows
    assert first.transport_cell is not second.transport_cell
    assert first.transport_cell.response_rows is not second.transport_cell.response_rows
    assert first.local_finite_confluence is HigherConfluence.OPEN
    assert first.global_confluence is HigherConfluence.OPEN
    assert first.scoped_formation is ScopedFormation.OPEN


def test_path_reconstruction_composition_order_and_freshness():
    doctrine, source, _, _ = direct_fixture()
    left = replay_diagram_path(doctrine, source, "lb")
    again = replay_diagram_path(doctrine, source, "lb")
    complete = compose_diagram_paths(doctrine, source, "lb", "ljp", "left-full")
    assert left.edge_ids == ("fl",) and complete.edge_ids == ("fl", "lj")
    assert complete.source_path_ids == ("lb", "ljp")
    assert left.history_digest == again.history_digest
    assert left.stages[0] is not again.stages[0]
    assert left.stages[0] is not source.stages[0]


def test_explicit_swap_derives_distinct_plan_and_two_cell():
    doctrine, source, transport, plan = direct_fixture()
    swapped = swap_fork_join_plan(doctrine, source, plan, transport, "swapped")
    assert swapped.left_branch_path_id == plan.right_branch_path_id
    assert swapped.alignment == tuple(
        AlignmentPoint(item.right_index, item.left_index) for item in plan.alignment
    )
    assert swapped.plan_digest != plan.plan_digest
    row = fork_confluence_judgment(doctrine, source, swapped, transport)
    assert row.status is ConfluenceStatus.ESTABLISHED
    assert row.transport_cell is not None
    assert row.transport_cell.plan_digest == swapped.plan_digest


def test_missing_joins_are_open_but_mismatch_has_precedence_in_both_orders():
    doctrine, source, transport, _ = direct_fixture(mismatch=True)
    empty = fork_join_plan(doctrine, source, "open", "lb", "rb", None, None, (), transport)
    swapped = fork_join_plan(doctrine, source, "open-swap", "rb", "lb", None, None, (), transport)
    left = fork_confluence_judgment(doctrine, source, empty, transport)
    right = fork_confluence_judgment(doctrine, source, swapped, transport)
    assert left.status is right.status is ConfluenceStatus.REFUTED
    assert left.transport_cell is right.transport_cell is None
    assert left.first_obstruction is not None and right.first_obstruction is not None


def test_valid_missing_joins_are_open_and_no_cell_is_forged():
    doctrine, source, transport, _ = direct_fixture()
    plan = fork_join_plan(doctrine, source, "open", "lb", "rb", None, None, (), transport)
    row = fork_confluence_judgment(doctrine, source, plan, transport)
    assert row.status is ConfluenceStatus.OPEN
    assert row.transport_cell is None
    assert row.first_obstruction is not None
    assert row.first_obstruction.outcome == "missing-required-joins"


def test_transport_is_closed_to_direct_echo_and_target_has_no_role():
    doctrine, _, transport, _ = direct_fixture()
    assert transport.mode is TransportMode.DIRECT_ECHO
    assert tuple(TransportMode) == (TransportMode.DIRECT_ECHO,)
    assert set(inspect.signature(fork_confluence_judgment).parameters) == {
        "doctrine", "source", "plan", "transport"
    }
    assert direct_echo_transport(doctrine, ("crest",)).transport_digest == transport.transport_digest


def test_output_alias_mutation_cannot_change_fresh_replay():
    doctrine, source, transport, plan = direct_fixture()
    first = fork_confluence_judgment(doctrine, source, plan, transport)
    assert first.transport_cell is not None
    object.__setattr__(first.transport_cell.response_rows[0], "outcome_payload", b"forged")
    second = fork_confluence_judgment(doctrine, source, plan, transport)
    assert second.status is ConfluenceStatus.ESTABLISHED
    assert second.transport_cell is not None
    assert second.transport_cell.response_rows[0].outcome_payload != b"forged"
    assert second.transport_cell.trace_digest != "forged"


def test_plan_digest_binds_alignment_and_transport_order():
    doctrine, source, transport, plan = direct_fixture(two_observers=True)
    two = direct_echo_transport(doctrine, ("crest", "tail"))
    changed = fork_join_plan(
        doctrine, source, "fork-plan-two", "lb", "rb", "ljp", "rjp",
        plan.alignment, two,
    )
    assert changed.transport_digest != transport.transport_digest
    assert changed.plan_digest != plan.plan_digest
    assert replace(plan, plan_digest="0" * 64) != plan


def test_finite_cycle_is_valid_syntax_but_receives_no_global_claim():
    doctrine = p0_observer_doctrine()
    stages = tuple(
        ontology_stage(name, Pulse(Silence()), doctrine, 1) for name in ("a", "b")
    )
    edges = (
        diagram_edge("ab", "a", "b", ("crest",)),
        diagram_edge("ba", "b", "a", ("crest",)),
    )
    paths = (diagram_path("cycle", ("ab", "ba"), "a", "a"),)
    source = finite_diagram_source(doctrine, "cycle-source", stages, edges, paths)
    replay = replay_diagram_path(doctrine, source, "cycle")
    assert replay.stages[0].stage_id == replay.stages[-1].stage_id == "a"
    assert replay.stages[0] is not replay.stages[-1]
    assert HigherConfluence.OPEN.value == "open"


def test_actual_r11_domain_blocked_is_typed_open_not_refuted():
    doctrine = p0_observer_doctrine()
    stages = tuple(ontology_stage(name, Silence(), doctrine, 2) for name in ("f", "l", "r", "j"))
    edges = (
        diagram_edge("fl", "f", "l", ("tail",)),
        diagram_edge("fr", "f", "r", ("tail",)),
        diagram_edge("lj", "l", "j", ("tail",)),
        diagram_edge("rj", "r", "j", ("tail",)),
    )
    paths = (
        diagram_path("lb", ("fl",), "f", "l"), diagram_path("rb", ("fr",), "f", "r"),
        diagram_path("ljp", ("lj",), "l", "j"), diagram_path("rjp", ("rj",), "r", "j"),
    )
    source = finite_diagram_source(doctrine, "blocked", stages, edges, paths)
    transport = direct_echo_transport(doctrine, ("tail",))
    alignment = (AlignmentPoint(0, 0), AlignmentPoint(1, 1), AlignmentPoint(2, 2))
    plan = fork_join_plan(doctrine, source, "blocked-plan", "lb", "rb", "ljp", "rjp", alignment, transport)
    row = fork_confluence_judgment(doctrine, source, plan, transport)
    assert row.status is ConfluenceStatus.OPEN
    assert row.first_obstruction is not None and row.first_obstruction.outcome == "domain-blocked"
    assert row.transport_cell is not None and row.transport_cell.status is ConfluenceStatus.OPEN
    assert {item.outcome for item in row.transport_cell.response_rows} == {"domain-blocked"}
