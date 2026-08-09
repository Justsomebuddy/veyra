"""Hostile raw-source and status-promotion pressure for P1-C4."""

from dataclasses import replace

import pytest

from src.core.observer_relation_types import RelationClass
from src.core.scoped_formation import (
    ScopedFormationJudgment, ScopedFormationStatus,
    ScopedFormationValidationError, formation_refinement_requirement,
    formation_scope, scoped_formation_judgment,
    validate_scoped_formation_result,
)

from scoped_formation_fixture import scoped_formation_fixture


def test_empty_positive_catalogs_and_reordered_g4_are_invalid():
    rule, scope = scoped_formation_fixture()
    with pytest.raises(ScopedFormationValidationError):
        formation_scope(
            rule, scope.scope_id, scope.presentation_id, scope.doctrine,
            scope.construction_source, scope.target, scope.diagram,
            scope.c2_catalog, scope.required_confluence, (), scope.persistence,
            scope.g4_bridge, scope.refinements, scope.policy,
        )
    bridge = replace(scope.g4_bridge, stage_map=scope.g4_bridge.stage_map[::-1])
    with pytest.raises(ScopedFormationValidationError):
        formation_scope(
            rule, scope.scope_id, scope.presentation_id, scope.doctrine,
            scope.construction_source, scope.target, scope.diagram,
            scope.c2_catalog, scope.required_confluence,
            scope.support_observer_ids, scope.persistence, bridge,
            scope.refinements, scope.policy,
        )


def test_p1a_strength_cannot_be_relabelled_as_relation_refinement():
    _, scope = scoped_formation_fixture(include_translated=False)
    old = scope.refinements[0]
    with pytest.raises(ScopedFormationValidationError):
        formation_refinement_requirement(
            "bad", old.a2_doctrine, old.a2_observer_source,
            old.a2_stage_source, old.relation_scope, old.morphism,
            required_class=RelationClass.STRICT_COARSENING_ON_SCOPE,
            required_preservation=old.required_preservation,
            required_reflection=old.required_reflection,
            required_domain_equality=old.required_domain_equality,
            required_loss=old.required_loss, path_ids=old.path_ids,
            survival_mode=old.survival_mode,
            direct_observer_id=old.direct_observer_id,
            direct_bridge=old.direct_bridge,
            relation_policy=old.relation_policy,
        )


def test_mutated_result_is_rejected_and_failed_scope_is_not_nonexistence():
    rule, scope = scoped_formation_fixture()
    result = scoped_formation_judgment(rule, scope)
    hostile = replace(result, first_obstruction="forged")
    with pytest.raises(ScopedFormationValidationError):
        validate_scoped_formation_result(rule, scope, hostile)
    assert "absolute-existence" in result.nonclaims
    assert not hasattr(result, "object_nonexistence")


def test_wrong_or_huge_result_variant_fails_before_nested_traversal():
    rule, scope = scoped_formation_fixture()
    with pytest.raises(ScopedFormationValidationError):
        validate_scoped_formation_result(rule, scope, object())
    good = scoped_formation_judgment(rule, scope)
    huge = replace(good, component_rows=good.component_rows * 1000)
    with pytest.raises(ScopedFormationValidationError):
        validate_scoped_formation_result(rule, scope, huge)


def test_refuted_wins_over_later_open():
    rule, scope = scoped_formation_fixture()
    result = scoped_formation_judgment(rule, scope)
    assert type(result) is ScopedFormationJudgment
    hostile_rows = list(result.component_rows)
    hostile_rows[0] = replace(hostile_rows[0], status=ScopedFormationStatus.REFUTED)
    hostile_rows[-1] = replace(hostile_rows[-1], status=ScopedFormationStatus.OPEN)
    forged = replace(result, component_rows=tuple(hostile_rows), presentation=None, status=ScopedFormationStatus.REFUTED)
    with pytest.raises(ScopedFormationValidationError):
        validate_scoped_formation_result(rule, scope, forged)
