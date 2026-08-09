"""Hostile exactness, binding, alignment, and resource pressure for P1-C1."""

from dataclasses import replace

import pytest

import src.core.confluence_runtime as runtime
from src.core.confluence import (
    compose_diagram_paths, diagram_edge, diagram_path, direct_echo_transport,
    finite_diagram_source, fork_confluence_judgment, fork_join_plan,
)
from src.core.confluence_plan import snapshot_direct_echo_transport, snapshot_fork_join_plan
from src.core.confluence_preflight import (
    ConfluenceValidationError, preflight_confluence_checks,
)
from src.core.confluence_types import (
    AlignmentPoint, ConfluencePreflightCharge, DirectEchoTransport,
)
from src.core.positive_ontology import ontology_stage
from src.core.positive_ontology_doctrine import p0_observer_doctrine
from src.core.proof_core_types import Pulse, Silence


def direct_fixture(*, mismatch=False):
    doctrine = p0_observer_doctrine()
    reps = {
        "fork": Pulse(Silence()), "left": Pulse(Silence()),
        "right": Silence() if mismatch else Pulse(Silence()),
        "join": Pulse(Silence()),
    }
    stages = tuple(ontology_stage(name, reps[name], doctrine, 1) for name in reps)
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


class EdgeSubclass(type(diagram_edge("x", "a", "b", ()) )):
    pass


class EqualityTrap:
    def __eq__(self, other):
        raise AssertionError("hostile equality invoked")


def test_duplicate_ids_histories_and_noncomposable_paths_fail_closed():
    doctrine, source, _, _ = direct_fixture()
    with pytest.raises(ConfluenceValidationError, match="duplicate-path-history"):
        finite_diagram_source(
            doctrine, "dup-history", source.stages, source.edges,
            source.paths + (diagram_path("alias", ("fl",), "fork", "left"),),
        )
    with pytest.raises(ConfluenceValidationError, match="duplicate-stage-id"):
        finite_diagram_source(
            doctrine, "dup-stage", source.stages + (
                replace(source.stages[0], representative=Pulse(Pulse(Silence()))),
            ),
            source.edges, source.paths,
        )
    with pytest.raises(ConfluenceValidationError, match="duplicate-edge-id"):
        finite_diagram_source(
            doctrine, "dup-edge", source.stages,
            source.edges + (replace(source.edges[0], upper_stage_id="right"),),
            source.paths,
        )
    bad = diagram_path("bad", ("fl", "rj"), "fork", "join")
    with pytest.raises(ConfluenceValidationError, match="noncomposable"):
        finite_diagram_source(doctrine, "bad-path", source.stages, source.edges, (bad,))


def test_same_join_path_partial_join_and_changed_plan_digest_are_rejected():
    doctrine, source, transport, plan = direct_fixture()
    with pytest.raises(ConfluenceValidationError, match="separate-join"):
        fork_join_plan(
            doctrine, source, "same-join", "lb", "rb", "ljp", "ljp",
            plan.alignment, transport,
        )
    with pytest.raises(ConfluenceValidationError, match="partial-join"):
        fork_join_plan(doctrine, source, "partial", "lb", "rb", "ljp", None, (), transport)
    alien = ontology_stage("alien", Pulse(Silence()), doctrine, 1)
    alien_source = finite_diagram_source(
        doctrine, "alien-join", source.stages + (alien,),
        source.edges + (diagram_edge("ra", "right", "alien", ("crest",)),),
        source.paths + (diagram_path("rap", ("ra",), "right", "alien"),),
    )
    with pytest.raises(ConfluenceValidationError, match="join-stage-mismatch"):
        fork_join_plan(
            doctrine, alien_source, "alien", "lb", "rb", "ljp", "rap",
            plan.alignment, transport,
        )
    forged = replace(plan, alignment=(AlignmentPoint(0, 0),), plan_digest=plan.plan_digest)
    with pytest.raises(ConfluenceValidationError):
        snapshot_fork_join_plan(forged, source, transport, doctrine)
    with pytest.raises(ConfluenceValidationError, match="drift"):
        snapshot_fork_join_plan(plan, source, direct_echo_transport(doctrine, ("tail",)), doctrine)


def test_reordered_paths_reused_source_digest_and_tag_like_ids_do_not_collide():
    doctrine, source, transport, plan = direct_fixture()
    reordered = replace(source, paths=tuple(reversed(source.paths)))
    with pytest.raises(ConfluenceValidationError, match="drift"):
        fork_confluence_judgment(doctrine, reordered, plan, transport)
    renamed = finite_diagram_source(
        doctrine, "field-count|path-0|edge-count", source.stages,
        source.edges, source.paths,
    )
    assert renamed.source_digest != source.source_digest


@pytest.mark.parametrize("alignment", [
    (AlignmentPoint(1, 0), AlignmentPoint(2, 2)),
    (AlignmentPoint(0, 0), AlignmentPoint(0, 0), AlignmentPoint(2, 2)),
    (AlignmentPoint(0, 0), AlignmentPoint(2, 1), AlignmentPoint(2, 2)),
    (AlignmentPoint(0, 0), AlignmentPoint(1, 1)),
])
def test_incomplete_repeated_jump_and_bad_endpoint_alignments_reject(alignment):
    doctrine, source, transport, _ = direct_fixture()
    with pytest.raises(ConfluenceValidationError, match="alignment"):
        fork_join_plan(
            doctrine, source, "bad-alignment", "lb", "rb", "ljp", "rjp",
            alignment, transport,
        )


def test_preserved_observer_must_exist_on_both_edge_endpoints():
    doctrine = p0_observer_doctrine()
    lower = ontology_stage("a", Pulse(Silence()), doctrine, 2)
    upper = ontology_stage("b", Pulse(Silence()), doctrine, 1)
    edge = diagram_edge("ab", "a", "b", ("tail",))
    path = diagram_path("abp", ("ab",), "a", "b")
    with pytest.raises(ConfluenceValidationError, match="both-endpoints"):
        finite_diagram_source(doctrine, "missing-observer", (lower, upper), (edge,), (path,))


def test_foreign_doctrine_source_and_raw_evidence_exact_gates():
    doctrine, source, transport, plan = direct_fixture()
    foreign = replace(doctrine, doctrine_id="foreign")
    with pytest.raises(ConfluenceValidationError):
        fork_confluence_judgment(foreign, source, plan, transport)
    with pytest.raises(ConfluenceValidationError, match="transport-must-be-exact"):
        fork_confluence_judgment(doctrine, source, plan, True)  # type: ignore[arg-type]
    with pytest.raises(ConfluenceValidationError, match="transport-must-be-exact"):
        fork_confluence_judgment(doctrine, source, plan, "0" * 64)  # type: ignore[arg-type]
    row = fork_confluence_judgment(doctrine, source, plan, transport)
    with pytest.raises(ConfluenceValidationError, match="source-must-be-exact"):
        fork_confluence_judgment(doctrine, row, plan, transport)  # type: ignore[arg-type]


def test_exact_type_subclass_cycle_and_post_snapshot_source_mutation_reject():
    doctrine, source, transport, plan = direct_fixture()
    edge = EdgeSubclass("x", "fork", "left", ())
    with pytest.raises(ConfluenceValidationError, match="edge-must-be-exact"):
        finite_diagram_source(doctrine, "subclass", source.stages, (edge,), source.paths[:1])
    cycle = Pulse(Silence())
    object.__setattr__(cycle, "tail", cycle)
    bad_stage = replace(source.stages[0], representative=cycle)
    with pytest.raises(ConfluenceValidationError, match="stage"):
        finite_diagram_source(doctrine, "cycle", (bad_stage,), source.edges[:1], source.paths[:1])
    object.__setattr__(source.paths[0], "edge_ids", ("fr",))
    with pytest.raises(ConfluenceValidationError):
        fork_confluence_judgment(doctrine, source, plan, transport)


def test_hostile_digest_fields_reject_before_equality_hooks():
    doctrine, source, transport, plan = direct_fixture()
    bad_source = replace(source, stage_commitments=(EqualityTrap(),))
    with pytest.raises(ConfluenceValidationError, match="stage-commitment"):
        fork_confluence_judgment(doctrine, bad_source, plan, transport)
    bad_plan = replace(plan, plan_digest=EqualityTrap())
    with pytest.raises(ConfluenceValidationError, match="plan-digest"):
        fork_confluence_judgment(doctrine, source, bad_plan, transport)


def test_preflight_exact_4096_boundary_and_bool_attack():
    assert preflight_confluence_checks(ConfluencePreflightCharge(4096, 0, 0)) == 4096
    assert preflight_confluence_checks(ConfluencePreflightCharge(0, 64, 64)) == 4096
    with pytest.raises(ConfluenceValidationError, match="check-limit"):
        preflight_confluence_checks(ConfluencePreflightCharge(4097, 0, 0))
    with pytest.raises(ConfluenceValidationError, match="invalid-preflight"):
        preflight_confluence_checks(ConfluencePreflightCharge(True, 0, 0))  # type: ignore[arg-type]


def test_exact_declared_structural_bounds_reject_before_replay():
    doctrine, source, _, _ = direct_fixture()
    with pytest.raises(ConfluenceValidationError, match="diagram-stages"):
        finite_diagram_source(doctrine, "many-stages", source.stages * 17, source.edges, source.paths)
    with pytest.raises(ConfluenceValidationError, match="diagram-edges"):
        finite_diagram_source(doctrine, "many-edges", source.stages, source.edges * 33, source.paths)
    with pytest.raises(ConfluenceValidationError, match="path-edges"):
        diagram_path("long", ("fl",) * 129, "fork", "left")
    with pytest.raises(ConfluenceValidationError, match="transport-observers"):
        direct_echo_transport(doctrine, ("crest",) * 65)


def test_transport_reorder_with_stale_digest_is_rejected():
    doctrine, _, _, _ = direct_fixture()
    transport = direct_echo_transport(doctrine, ("crest", "tail"))
    stale = replace(transport, observer_ids=("tail", "crest"))
    with pytest.raises(ConfluenceValidationError, match="drift"):
        snapshot_direct_echo_transport(stale, doctrine)


def test_judgment_preflight_runs_before_any_echo(monkeypatch):
    doctrine, source, transport, plan = direct_fixture()
    calls = 0

    def forbidden_echo(*args):
        nonlocal calls
        calls += 1
        raise AssertionError("echo-ran-before-preflight")

    def over_budget(*args):
        raise ConfluenceValidationError("confluence-check-limit")

    monkeypatch.setattr(runtime, "echo", forbidden_echo)
    monkeypatch.setattr(runtime, "preflight_confluence_checks", over_budget)
    with pytest.raises(ConfluenceValidationError, match="check-limit"):
        fork_confluence_judgment(doctrine, source, plan, transport)
    assert calls == 0


def test_unexpected_echo_exception_propagates_after_valid_preflight(monkeypatch):
    doctrine, source, transport, plan = direct_fixture()
    calls = 0

    def explode(*args):
        nonlocal calls
        calls += 1
        raise RuntimeError("unexpected-internal")

    monkeypatch.setattr(runtime, "echo", explode)
    with pytest.raises(RuntimeError, match="unexpected-internal"):
        fork_confluence_judgment(doctrine, source, plan, transport)
    assert calls == 1


def test_crest_persistence_does_not_hide_tail_transport_split():
    doctrine, _, _, _ = direct_fixture()
    stages = (
        ontology_stage("fork", Pulse(Silence()), doctrine, 2),
        ontology_stage("left", Pulse(Silence()), doctrine, 2),
        ontology_stage("right", Pulse(Pulse(Silence())), doctrine, 2),
        ontology_stage("join", Pulse(Silence()), doctrine, 2),
    )
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
    source = finite_diagram_source(doctrine, "tail-split", stages, edges, paths)
    transport = direct_echo_transport(doctrine, ("tail",))
    plan = fork_join_plan(
        doctrine, source, "tail-plan", "lb", "rb", "ljp", "rjp",
        (AlignmentPoint(0, 0), AlignmentPoint(1, 1), AlignmentPoint(2, 2)), transport,
    )
    row = fork_confluence_judgment(doctrine, source, plan, transport)
    assert row.status.value == "refuted"
    assert row.transport_cell is not None
    assert any(item.status.value == "refuted" for item in row.transport_cell.response_rows)


def test_noncomposable_path_composition_and_untranslated_object_reject():
    doctrine, source, _, _ = direct_fixture()
    with pytest.raises(ConfluenceValidationError, match="noncomposable"):
        compose_diagram_paths(doctrine, source, "lb", "rjp", "bad")
    fake = DirectEchoTransport(("crest",), "0" * 64)
    with pytest.raises(ConfluenceValidationError, match="drift"):
        snapshot_direct_echo_transport(fake, doctrine)
