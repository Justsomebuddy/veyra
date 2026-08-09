"""Positive and three-valued P1-C4 formation pressure."""

from dataclasses import replace

import pytest

from src.core.scoped_formation import (
    SCOPED_FORMATION_NONCLAIMS, ScopedFormationJudgment,
    ScopedFormationStatus, ScopedFormationValidationError,
    finite_scoped_formation_rule,
    scoped_formation_judgment, validate_scoped_formation_result,
)

from scoped_formation_fixture import scoped_formation_fixture


def test_positive_scope_forms_only_relative_finite_presentation():
    rule, scope = scoped_formation_fixture()
    result = scoped_formation_judgment(rule, scope)
    assert type(result) is ScopedFormationJudgment
    assert result.status is ScopedFormationStatus.ESTABLISHED_RELATIVE_TO_FORMATION_SCOPE
    assert result.presentation is not None
    assert result.presentation.status is ScopedFormationStatus.ESTABLISHED_RELATIVE_TO_FORMATION_SCOPE
    assert result.presentation.target_stage_id == "join"
    assert result.presentation.target_stage is not scope.target
    assert result.nonclaims == SCOPED_FORMATION_NONCLAIMS
    assert "absolute-existence" in result.nonclaims
    assert "completed-carrier" in result.nonclaims
    membership = next(x for x in result.component_rows if x.component == "target-membership")
    assert membership.evidence_digest != scope.expected_target_commitment


def test_named_rule_and_validator_freshly_replay():
    rule, scope = scoped_formation_fixture()
    first = finite_scoped_formation_rule(rule, scope)
    second = validate_scoped_formation_result(rule, scope, first)
    assert second == first
    assert second is not first
    assert second.presentation is not first.presentation


def test_alien_target_is_rejected_before_runtime():
    rule, scope = scoped_formation_fixture()
    mismatched = replace(
        scope.target, representative=scope.diagram.stages[2].representative,
    )
    from src.core.scoped_formation import formation_scope
    for alien in (mismatched, replace(scope.target, stage_id="alien-stage")):
        with pytest.raises(
            ScopedFormationValidationError,
            match="formation-target-not-exact-diagram-stage",
        ):
            formation_scope(
                rule, scope.scope_id, scope.presentation_id, scope.doctrine,
                scope.construction_source, alien, scope.diagram,
                scope.c2_catalog, scope.required_confluence,
                scope.support_observer_ids, scope.persistence,
                scope.g4_bridge, scope.refinements, scope.policy,
            )


def test_complete_component_order_includes_both_survival_modes():
    rule, scope = scoped_formation_fixture()
    result = scoped_formation_judgment(rule, scope)
    components = tuple(row.component for row in result.component_rows)
    assert components[:4] == (
        "construction", "target-membership", "support", "g4",
    )
    assert components.count("a2-refinement") == 2
    assert components.count("survival") == 2
    assert all(row.status is ScopedFormationStatus.ESTABLISHED_RELATIVE_TO_FORMATION_SCOPE for row in result.component_rows)
