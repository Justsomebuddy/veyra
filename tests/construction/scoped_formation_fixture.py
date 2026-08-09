"""Reusable exact positive P1-C4 raw-source fixture."""

from src.core.confluence_aggregate import (
    confluence_aggregate_policy, declared_history, finite_confluence_catalog,
    global_path_pair_requirement, local_critical_fork_requirement,
)
from src.core.confluence import (
    diagram_edge, diagram_path, direct_echo_transport, finite_diagram_source,
    fork_join_plan,
)
from src.core.confluence_types import AlignmentPoint
from src.core.finite_builder_types import PulseStep, SeedRef
from src.core.finite_construction import (
    construction_source_binding, finite_builder_program, finite_recurrence_seed,
)
from src.core.observer_patch_atlas import observer_patch, observer_patch_atlas
from src.core.observer_relation_types import LawStatus
from src.core.positive_ontology_doctrine import stage_commitment
from src.core.proof_core_types import Silence
from src.core.scoped_formation import (
    RequiredConfluenceLevel, SurvivalMode, bound_g4_bridge_source,
    bound_patch_requirement, finite_scoped_formation_rule_source,
    formation_persistence_requirement, formation_policy,
    formation_refinement_requirement, formation_scope, g4_bridge_mappings,
    stage_map_row,
)
from src.core.translated_confluence import (
    p0_p1a_response_bridge, translated_echo_transport_spec,
)

# the only fixture shared across test packages, so it is addressed in full
from tests.confluence.translated_confluence_fixture import translated_fixture


def scoped_formation_fixture(
    *, include_translated: bool = True, policy=None,
    variant: str = "strict", padding_observers: int = 0,
):
    """Build one positive scope containing direct and optionally translated survival."""
    p0, old_diagram, old_plan, p1a, binding, a2_source, _, old_spec, c3_policy, placeholder = translated_fixture(
        variant=variant, padding_observers=padding_observers,
    )
    translated_edges = tuple(
        diagram_edge(
            f"t{x.edge_id}", x.lower_stage_id, x.upper_stage_id,
            ("diagram-fine", "diagram-coarse")
            if x.edge_id in {"fl", "lj"} else ("diagram-coarse",),
        ) for x in old_diagram.edges
    )
    g4_edge = diagram_edge("gfr", "fork", "right", ("diagram-fine",))
    diagram = finite_diagram_source(
        p0, "c4-diagram", old_diagram.stages,
        old_diagram.edges + translated_edges + (g4_edge,),
        old_diagram.paths + (
            diagram_path("full-left", ("fl", "lj"), "fork", "join"),
            diagram_path("full-right", ("fr", "rj"), "fork", "join"),
            diagram_path("tlb", ("tfl",), "fork", "left"),
            diagram_path("trb", ("tfr",), "fork", "right"),
            diagram_path("tljp", ("tlj",), "left", "join"),
            diagram_path("trjp", ("trj",), "right", "join"),
            diagram_path("grb", ("gfr",), "fork", "right"),
        ),
    )
    plan = fork_join_plan(
        p0, diagram, "c4-translated-plan", "tlb", "trb", "tljp", "trjp",
        old_plan.alignment, placeholder,
    )
    bridge = p0_p1a_response_bridge(p0, diagram, p1a, binding, a2_source)
    spec = translated_echo_transport_spec(
        p0, diagram, plan, p1a, binding, a2_source, bridge, "c4-spec",
        old_spec.direction, old_spec.diagram_fine_observer_id,
        old_spec.diagram_coarse_observer_id, old_spec.morphism,
        old_spec.relation_scope, old_spec.relation_policy,
        old_spec.required_class, old_spec.required_loss,
    )
    coarse = direct_echo_transport(p0, ("diagram-coarse",))
    stages = {x.stage_id: x for x in diagram.stages}
    seed = finite_recurrence_seed("formation-seed", Silence())
    program = finite_builder_program(
        "formation-builder", "join", tuple(x.observer_id for x in p0.observers),
        PulseStep(SeedRef("formation-seed")),
    )
    construction = construction_source_binding(
        p0, "formation-construction", program, (seed,),
    )
    local_plan = fork_join_plan(
        p0, diagram, "formation-local-plan", "lb", "rb", "ljp", "rjp",
        plan.alignment, coarse,
    )
    local = local_critical_fork_requirement(
        p0, diagram, "formation-local", local_plan, coarse,
    )
    left = declared_history(p0, diagram, "formation-left", "full-left")
    right = declared_history(p0, diagram, "formation-right", "full-right")
    global_ = global_path_pair_requirement(
        p0, diagram, "formation-global", left, right,
        (AlignmentPoint(0, 0), AlignmentPoint(1, 1), AlignmentPoint(2, 2)), coarse,
    )
    catalog = finite_confluence_catalog(
        p0, diagram, (local,), (global_,), confluence_aggregate_policy(),
    )
    atlas = observer_patch_atlas(
        ("fork", "left", "right", "join"),
        (
            observer_patch("left-patch", ("fork", "left", "join")),
            observer_patch("right-patch", ("fork", "right", "join")),
        ),
    )
    stage_map = tuple(
        stage_map_row(name, name, stage_commitment(stages[name]))
        for name in atlas.universe
    )
    patch_requirements = (
        bound_patch_requirement(
            "left-patch", ("lb", "ljp"), ("diagram-coarse",),
            ("fork", "left", "join"),
        ),
        bound_patch_requirement(
            "right-patch", ("rb", "rjp"), ("diagram-coarse",),
            ("fork", "right", "join"),
        ),
    )
    g4 = bound_g4_bridge_source(
        atlas, p0, diagram, g4_bridge_mappings(stage_map, patch_requirements),
    )
    persistence = tuple(
        formation_persistence_requirement("diagram-coarse", path)
        for path in ("lb", "rb", "ljp", "rjp")
    )
    laws = dict(
        required_class=spec.required_class,
        required_preservation=LawStatus.ESTABLISHED,
        required_reflection=LawStatus.REFUTED,
        required_domain_equality=LawStatus.ESTABLISHED,
        required_loss=spec.required_loss,
        path_ids=("tlb", "trb", "tljp", "trjp"),
        relation_policy=spec.relation_policy,
    )
    refinements = [formation_refinement_requirement(
        "direct-refinement", p1a, binding, a2_source, spec.relation_scope,
        spec.morphism, survival_mode=SurvivalMode.DIRECT,
        direct_observer_id="diagram-coarse", direct_bridge=bridge, **laws,
    )]
    if include_translated:
        refinements.append(formation_refinement_requirement(
            "translated-refinement", p1a, binding, a2_source,
            spec.relation_scope, spec.morphism,
            survival_mode=SurvivalMode.TRANSLATED, translated_plan=plan,
            translated_bridge=bridge, translated_spec=spec,
            translated_policy=c3_policy, **laws,
        ))
    rule = finite_scoped_formation_rule_source(p0)
    scope = formation_scope(
        rule, "formation-scope", "finite-object-presentation", p0,
        construction, stages["join"], diagram, catalog,
        RequiredConfluenceLevel.GLOBAL_DECLARED_FINITE,
        ("diagram-coarse",), persistence, g4, tuple(refinements),
        formation_policy() if policy is None else policy,
    )
    return rule, scope
