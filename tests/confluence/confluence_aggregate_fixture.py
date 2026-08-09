"""Shared exact P1-C2 fixture builders."""

from src.core.confluence import (
    diagram_edge, diagram_path, direct_echo_transport, finite_diagram_source,
    fork_join_plan,
)
from src.core.confluence_aggregate import (
    confluence_aggregate_policy, declared_history, finite_confluence_catalog,
    global_path_pair_requirement, identity_history,
    local_critical_fork_requirement,
)
from src.core.confluence_types import AlignmentPoint
from src.core.positive_ontology import ontology_stage
from src.core.positive_ontology_doctrine import p0_observer_doctrine
from src.core.proof_core_types import Pulse, Silence


def aggregate_fixture(*, global_open: bool = False, mismatch: bool = False, policy=None):
    doctrine = p0_observer_doctrine()
    names = ("f", "l", "r", "j", "x", "a", "b", "y", "c", "d")
    stages = tuple(
        ontology_stage(
            name, Silence() if mismatch and name == "r" else Pulse(Silence()),
            doctrine, 1,
        ) for name in names
    )
    edges = (
        diagram_edge("fl", "f", "l", ("crest",)),
        diagram_edge("fr", "f", "r", ("crest",)),
        diagram_edge("lj", "l", "j", ("crest",)),
        diagram_edge("rj", "r", "j", ("crest",)),
        diagram_edge("xa", "x", "a", ("crest",)),
        diagram_edge("xb", "x", "b", ("crest",)),
        diagram_edge("ay", "a", "y", ("crest",)),
        diagram_edge("by", "b", "y", ("crest",)),
        diagram_edge("cd", "c", "d", ("crest",)),
        diagram_edge("dc", "d", "c", ("crest",)),
    )
    paths = (
        diagram_path("lb1", ("fl",), "f", "l"),
        diagram_path("rb1", ("fr",), "f", "r"),
        diagram_path("lj1", ("lj",), "l", "j"),
        diagram_path("rj1", ("rj",), "r", "j"),
        diagram_path("full-left", ("fl", "lj"), "f", "j"),
        diagram_path("full-right", ("fr", "rj"), "f", "j"),
        diagram_path("lb2", ("xa",), "x", "a"),
        diagram_path("rb2", ("xb",), "x", "b"),
        diagram_path("lj2", ("ay",), "a", "y"),
        diagram_path("rj2", ("by",), "b", "y"),
        diagram_path("cycle", ("cd", "dc"), "c", "c"),
    )
    diagram = finite_diagram_source(doctrine, "aggregate-fixture", stages, edges, paths)
    crest = direct_echo_transport(doctrine, ("crest",))
    tail = direct_echo_transport(doctrine, ("tail",))
    alignment = (AlignmentPoint(0, 0), AlignmentPoint(1, 1), AlignmentPoint(2, 2))
    plan1 = fork_join_plan(
        doctrine, diagram, "plan-1", "lb1", "rb1", "lj1", "rj1", alignment, crest,
    )
    plan2 = fork_join_plan(
        doctrine, diagram, "plan-2", "lb2", "rb2", "lj2", "rj2", alignment, crest,
    )
    local = (
        local_critical_fork_requirement(doctrine, diagram, "local-1", plan1, crest),
        local_critical_fork_requirement(doctrine, diagram, "local-2", plan2, crest),
    )
    arbitrary_left = declared_history(doctrine, diagram, "left-full", "full-left")
    arbitrary_right = declared_history(doctrine, diagram, "right-full", "full-right")
    arbitrary = global_path_pair_requirement(
        doctrine, diagram, "arbitrary-pair", arbitrary_left, arbitrary_right,
        alignment, tail if global_open else crest,
    )
    cycle = declared_history(doctrine, diagram, "cycle-history", "cycle")
    identity = identity_history(doctrine, diagram, "identity-history", "c")
    cycle_pair = global_path_pair_requirement(
        doctrine, diagram, "cycle-vs-identity", cycle, identity,
        (AlignmentPoint(0, 0), AlignmentPoint(1, 0), AlignmentPoint(2, 0)), crest,
    )
    selected_policy = confluence_aggregate_policy() if policy is None else policy
    catalog = finite_confluence_catalog(
        doctrine, diagram, local, (arbitrary, cycle_pair), selected_policy,
    )
    return doctrine, diagram, crest, tail, local, (arbitrary, cycle_pair), catalog
