"""Executable level-1 certificate for P1-C4 scoped formation."""

from __future__ import annotations

import logging

from .certify_translated_confluence import _fixture as c3_fixture
from .certify_types import Certificate
from .confluence import (
    diagram_edge, diagram_path, direct_echo_transport, finite_diagram_source,
    fork_join_plan,
)
from .confluence_aggregate import (
    confluence_aggregate_policy, declared_history, finite_confluence_catalog,
    global_path_pair_requirement, local_critical_fork_requirement,
)
from .confluence_types import AlignmentPoint
from .construction.finite_builder.types import PulseStep, SeedRef
from .finite_construction import (
    construction_source_binding, finite_builder_program, finite_recurrence_seed,
)
from .observer_patch_atlas import observer_patch, observer_patch_atlas
from .observer_relation_types import LawStatus, LossStatus, RelationClass
from .positive_ontology_doctrine import stage_commitment
from .proof_core_types import Silence
from .scoped_formation_runtime import scoped_formation_judgment
from .scoped_formation_result_validation import validate_scoped_formation_result
from .scoped_formation_refinement_source import formation_refinement_requirement
from .scoped_formation_scope import formation_scope
from .scoped_formation_sources import (
    bound_g4_bridge_source, bound_patch_requirement,
    finite_scoped_formation_rule_source, formation_persistence_requirement,
    formation_policy, g4_bridge_mappings, stage_map_row,
)
from .scoped_formation_types import (
    RequiredConfluenceLevel, ScopedFormationJudgment,
    ScopedFormationResourceLimit, ScopedFormationStatus, SurvivalMode,
)
from .translated_confluence import translated_confluence_policy
from .translated_confluence import (
    p0_p1a_response_bridge, translated_echo_transport_spec,
)

logger = logging.getLogger(__name__)


def _formation_fixture():
    """Build one raw positive witness without importing test artifacts."""
    logger.debug("c4 certificate fixture entry")
    p0, old_diagram, old_plan, p1a, binding, source, _, old_spec = c3_fixture()
    translated_edges = tuple(
        diagram_edge(
            f"t{x.edge_id}", x.lower_stage_id, x.upper_stage_id,
            ("diagram-fine", "diagram-coarse")
            if x.edge_id in {"fl", "lj"} else ("diagram-coarse",),
        ) for x in old_diagram.edges
    )
    g4_edge = diagram_edge("gfr", "fork", "right", ("diagram-fine",))
    diagram = finite_diagram_source(
        p0, "c4-certificate-diagram", old_diagram.stages,
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
    translated_transport = direct_echo_transport(
        p0, ("diagram-fine", "diagram-coarse"),
    )
    plan = fork_join_plan(
        p0, diagram, "c4-certificate-translated-plan", "tlb", "trb", "tljp", "trjp",
        old_plan.alignment, translated_transport,
    )
    bridge = p0_p1a_response_bridge(p0, diagram, p1a, binding, source)
    spec = translated_echo_transport_spec(
        p0, diagram, plan, p1a, binding, source, bridge,
        "c4-certificate-spec", old_spec.direction,
        old_spec.diagram_fine_observer_id, old_spec.diagram_coarse_observer_id,
        old_spec.morphism, old_spec.relation_scope, old_spec.relation_policy,
        old_spec.required_class, old_spec.required_loss,
    )
    stages = {x.stage_id: x for x in diagram.stages}
    seed = finite_recurrence_seed("c4-seed", Silence())
    program = finite_builder_program(
        "c4-builder", "join", ("diagram-fine", "diagram-coarse"),
        PulseStep(SeedRef("c4-seed")),
    )
    construction = construction_source_binding(
        p0, "c4-construction", program, (seed,),
    )
    coarse = direct_echo_transport(p0, ("diagram-coarse",))
    local_plan = fork_join_plan(
        p0, diagram, "c4-local-plan", "lb", "rb", "ljp", "rjp",
        plan.alignment, coarse,
    )
    local = local_critical_fork_requirement(
        p0, diagram, "c4-local", local_plan, coarse,
    )
    left = declared_history(p0, diagram, "c4-left", "full-left")
    right = declared_history(p0, diagram, "c4-right", "full-right")
    global_ = global_path_pair_requirement(
        p0, diagram, "c4-global", left, right,
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
    mappings = g4_bridge_mappings(
        tuple(stage_map_row(x, x, stage_commitment(stages[x])) for x in atlas.universe),
        (
            bound_patch_requirement("left-patch", ("lb", "ljp"), ("diagram-coarse",), ("fork", "left", "join")),
            bound_patch_requirement("right-patch", ("rb", "rjp"), ("diagram-coarse",), ("fork", "right", "join")),
        ),
    )
    g4 = bound_g4_bridge_source(atlas, p0, diagram, mappings)
    persistence = tuple(
        formation_persistence_requirement("diagram-coarse", x)
        for x in ("lb", "rb", "ljp", "rjp")
    )
    relation_policy = spec.relation_policy
    common = dict(
        required_class=RelationClass.STRICT_REFINEMENT_ON_SCOPE,
        required_preservation=LawStatus.ESTABLISHED,
        required_reflection=LawStatus.REFUTED,
        required_domain_equality=LawStatus.ESTABLISHED,
        required_loss=LossStatus.LOSSY_ON_SCOPE,
        path_ids=("tlb", "trb", "tljp", "trjp"),
        relation_policy=relation_policy,
    )
    refinements = (
        formation_refinement_requirement(
            "c4-direct", p1a, binding, source, spec.relation_scope,
            spec.morphism, survival_mode=SurvivalMode.DIRECT,
            direct_observer_id="diagram-coarse", direct_bridge=bridge, **common,
        ),
        formation_refinement_requirement(
            "c4-translated", p1a, binding, source, spec.relation_scope,
            spec.morphism, survival_mode=SurvivalMode.TRANSLATED,
            translated_plan=plan, translated_bridge=bridge,
            translated_spec=spec, translated_policy=translated_confluence_policy(),
            **common,
        ),
    )
    rule = finite_scoped_formation_rule_source(p0)
    scope = formation_scope(
        rule, "c4-certificate-scope", "c4-certificate-presentation", p0,
        construction, stages["join"], diagram, catalog,
        RequiredConfluenceLevel.GLOBAL_DECLARED_FINITE,
        ("diagram-coarse",), persistence, g4, refinements, formation_policy(),
    )
    logger.debug("c4 certificate fixture exit")
    return rule, scope


def certify_scoped_formation() -> Certificate:
    """Certify one exact finite doctrine-relative SFP presentation."""
    logger.debug("certify_scoped_formation entry")
    rule, scope = _formation_fixture()
    value = scoped_formation_judgment(rule, scope)
    validated = validate_scoped_formation_result(rule, scope, value)
    refused_scope = formation_scope(
        rule, scope.scope_id, scope.presentation_id, scope.doctrine,
        scope.construction_source, scope.target, scope.diagram, scope.c2_catalog,
        scope.required_confluence, scope.support_observer_ids, scope.persistence,
        scope.g4_bridge, scope.refinements,
        formation_policy(max_checks=1, max_bytes=1),
    )
    refused = scoped_formation_judgment(rule, refused_scope)
    passed = (
        type(value) is ScopedFormationJudgment
        and type(validated) is ScopedFormationJudgment
        and validated is not value
        and validated.judgment_digest == value.judgment_digest
        and value.status is ScopedFormationStatus.ESTABLISHED_RELATIVE_TO_FORMATION_SCOPE
        and value.presentation is not None
        and all(x.status is ScopedFormationStatus.ESTABLISHED_RELATIVE_TO_FORMATION_SCOPE for x in value.component_rows)
        and type(refused) is ScopedFormationResourceLimit
        and not hasattr(refused, "presentation")
    )
    method = (
        "raw P1-B/G4/C2/A2/C3 replay, exact response-derived gluing, "
        "direct and translated survival, and atomic hard-first preflight"
    )
    detail = (
        "one finite presentation relative to SFP and scope only; no ontic genesis, "
        "absolute existence, universal refinement, productivity, or completed infinity"
    )
    result = Certificate("scoped_formation_p1c4", method, passed, detail, 1)
    logger.debug("certify_scoped_formation exit passed=%s", passed)
    return result


if __name__ == "__main__":
    print(certify_scoped_formation())
