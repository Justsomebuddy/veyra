"""Resource, G4 contradiction, and hostile-result pressure for P1-C4."""

from dataclasses import replace

import pytest

from src.core.observer_patch_atlas import observer_patch, observer_patch_atlas
from src.core.positive_ontology_doctrine import stage_commitment
from src.core.scoped_formation import (
    FormationFailedBound, ScopedFormationJudgment,
    ScopedFormationResourceLimit, ScopedFormationStatus,
    ScopedFormationValidationError, SurvivalMode, bound_g4_bridge_source,
    bound_patch_requirement, formation_policy, formation_refinement_requirement,
    formation_scope, g4_bridge_mappings, scoped_formation_judgment,
    stage_map_row, validate_scoped_formation_result,
)

from scoped_formation_fixture import scoped_formation_fixture


def _with(scope, rule, *, bridge=None, refinements=None, policy=None):
    return formation_scope(
        rule, scope.scope_id, scope.presentation_id, scope.doctrine,
        scope.construction_source, scope.target, scope.diagram,
        scope.c2_catalog, scope.required_confluence,
        scope.support_observer_ids, scope.persistence,
        scope.g4_bridge if bridge is None else bridge,
        scope.refinements if refinements is None else refinements,
        scope.policy if policy is None else policy,
    )


def test_outer_preflight_refuses_atomically_before_any_semantics(monkeypatch):
    rule, scope = scoped_formation_fixture()
    limited = _with(scope, rule, policy=formation_policy(max_checks=1))

    def forbidden(*_args, **_kwargs):
        raise AssertionError("semantic replay occurred after preflight refusal")

    monkeypatch.setattr("src.core.scoped_formation_components.observe", forbidden)
    monkeypatch.setattr("src.core.scoped_formation_components.echo", forbidden)
    monkeypatch.setattr("src.core.scoped_formation_g4.echo", forbidden)
    result = scoped_formation_judgment(rule, limited)
    assert type(result) is ScopedFormationResourceLimit
    assert result.failed_bound is FormationFailedBound.CHECKS
    assert not hasattr(result, "presentation")
    assert not hasattr(result, "component_rows")


def test_bytes_refusal_precedes_checks_refusal():
    rule, scope = scoped_formation_fixture()
    limited = _with(
        scope, rule, policy=formation_policy(max_checks=1, max_bytes=1),
    )
    result = scoped_formation_judgment(rule, limited)
    assert type(result) is ScopedFormationResourceLimit
    assert result.failed_bound is FormationFailedBound.BYTES


def test_response_derived_triangle_contradiction_refutes_formation():
    rule, scope = scoped_formation_fixture()
    stages = {x.stage_id: x for x in scope.diagram.stages}
    atlas = observer_patch_atlas(
        ("fork", "left", "right"),
        (
            observer_patch("ab", ("fork", "left")),
            observer_patch("bc", ("left", "right")),
            observer_patch("ca", ("right", "fork")),
        ),
    )
    mappings = g4_bridge_mappings(
        tuple(
            stage_map_row(x, x, stage_commitment(stages[x]))
            for x in atlas.universe
        ),
        (
            bound_patch_requirement("ab", ("lb",), ("diagram-coarse",), ("fork", "left")),
            bound_patch_requirement("bc", ("lb", "rb"), ("diagram-coarse",), ("left", "right")),
            bound_patch_requirement("ca", ("grb",), ("diagram-fine",), ("right", "fork")),
        ),
    )
    bridge = bound_g4_bridge_source(atlas, scope.doctrine, scope.diagram, mappings)
    changed = _with(scope, rule, bridge=bridge)
    result = scoped_formation_judgment(rule, changed)
    assert type(result) is ScopedFormationJudgment
    assert result.status is ScopedFormationStatus.REFUTED
    assert result.presentation is None
    assert result.g4.contradiction_rows
    assert result.g4.first_contradiction == result.g4.contradiction_rows[0]
    assert result.g4.first_obstruction == result.g4.contradiction_rows[0].contradiction_digest


def test_direct_translated_field_swap_is_invalid():
    _, scope = scoped_formation_fixture()
    translated = scope.refinements[1]
    with pytest.raises(ScopedFormationValidationError):
        formation_refinement_requirement(
            "swapped", translated.a2_doctrine,
            translated.a2_observer_source, translated.a2_stage_source,
            translated.relation_scope, translated.morphism,
            required_class=translated.required_class,
            required_preservation=translated.required_preservation,
            required_reflection=translated.required_reflection,
            required_domain_equality=translated.required_domain_equality,
            required_loss=translated.required_loss,
            path_ids=translated.path_ids, survival_mode=SurvivalMode.DIRECT,
            direct_observer_id="diagram-coarse",
            direct_bridge=translated.translated_bridge,
            translated_plan=translated.translated_plan,
            translated_bridge=translated.translated_bridge,
            translated_spec=translated.translated_spec,
            translated_policy=translated.translated_policy,
            relation_policy=translated.relation_policy,
        )


def test_huge_nested_result_is_rejected_before_full_replay(monkeypatch):
    rule, scope = scoped_formation_fixture()
    result = scoped_formation_judgment(rule, scope)
    hostile_g4 = replace(
        result.g4,
        section_digests=("x" * (5 * 1024 * 1024),) + result.g4.section_digests[1:],
    )
    hostile = replace(result, g4=hostile_g4)

    def forbidden(*_args, **_kwargs):
        raise AssertionError("semantic replay occurred before hostile shallow rejection")

    monkeypatch.setattr("src.core.scoped_formation_components.observe", forbidden)
    with pytest.raises(ScopedFormationValidationError):
        validate_scoped_formation_result(rule, scope, hostile)


def test_unexpected_semantic_fault_propagates(monkeypatch):
    rule, scope = scoped_formation_fixture()

    def explode(*_args, **_kwargs):
        raise RuntimeError("injected-observer-fault")

    monkeypatch.setattr("src.core.scoped_formation_components.observe", explode)
    with pytest.raises(RuntimeError, match="injected-observer-fault"):
        scoped_formation_judgment(rule, scope)
