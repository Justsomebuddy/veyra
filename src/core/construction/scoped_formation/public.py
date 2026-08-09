"""Collision-safe root aliases for released P1-C4 scoped formation."""

from __future__ import annotations

from . import core as _c4
from . import types as _types

C4_SCOPED_FORMATION_NONCLAIMS = _types.SCOPED_FORMATION_NONCLAIMS
C4ScopedFormationStatus = _types.ScopedFormationStatus
C4RequiredConfluenceLevel = _types.RequiredConfluenceLevel
C4SurvivalMode = _types.SurvivalMode
C4FormationFailedBound = _types.FormationFailedBound
C4FormationLimitSource = _types.FormationLimitSource
C4FormationPolicy = _types.FormationPolicy
C4FiniteScopedFormationRuleSource = _types.FiniteScopedFormationRuleSource
C4StageMapRow = _types.StageMapRow
C4BoundPatchRequirement = _types.BoundPatchRequirement
C4G4BridgeMappings = _types.G4BridgeMappings
C4BoundG4BridgeSource = _types.BoundG4BridgeSource
C4FormationPersistenceRequirement = _types.FormationPersistenceRequirement
C4FormationRefinementRequirement = _types.FormationRefinementRequirement
C4FormationScope = _types.FormationScope
C4FormationComponentRow = _types.FormationComponentRow
C4G4ResponseRow = _types.G4ResponseRow
C4G4ContradictionRow = _types.G4ContradictionRow
C4BoundG4BridgeJudgment = _types.BoundG4BridgeJudgment
C4FiniteScopedObjectPresentation = _types.FiniteScopedObjectPresentation
C4ScopedFormationJudgment = _types.ScopedFormationJudgment
C4ScopedFormationResourceLimit = _types.ScopedFormationResourceLimit
C4ScopedFormationResult = _types.ScopedFormationResult
C4ScopedFormationValidationError = _c4.ScopedFormationValidationError

c4_bound_g4_bridge_source = _c4.bound_g4_bridge_source
c4_bound_patch_requirement = _c4.bound_patch_requirement
c4_finite_scoped_formation_rule = _c4.finite_scoped_formation_rule
c4_finite_scoped_formation_rule_source = _c4.finite_scoped_formation_rule_source
c4_formation_persistence_requirement = _c4.formation_persistence_requirement
c4_formation_policy = _c4.formation_policy
c4_formation_refinement_requirement = _c4.formation_refinement_requirement
c4_formation_scope = _c4.formation_scope
c4_g4_bridge_mappings = _c4.g4_bridge_mappings
c4_scoped_formation_judgment = _c4.scoped_formation_judgment
c4_scoped_formation_scope_boundary = _c4.scoped_formation_scope_boundary
c4_snapshot_formation_scope = _c4.snapshot_formation_scope
c4_stage_map_row = _c4.stage_map_row
c4_validate_scoped_formation_result = _c4.validate_scoped_formation_result

__all__ = (
    "C4_SCOPED_FORMATION_NONCLAIMS", "C4ScopedFormationStatus",
    "C4RequiredConfluenceLevel", "C4SurvivalMode", "C4FormationFailedBound",
    "C4FormationLimitSource", "C4FormationPolicy",
    "C4FiniteScopedFormationRuleSource", "C4StageMapRow",
    "C4BoundPatchRequirement", "C4G4BridgeMappings", "C4BoundG4BridgeSource",
    "C4FormationPersistenceRequirement", "C4FormationRefinementRequirement",
    "C4FormationScope", "C4FormationComponentRow", "C4G4ResponseRow",
    "C4G4ContradictionRow", "C4BoundG4BridgeJudgment",
    "C4FiniteScopedObjectPresentation", "C4ScopedFormationJudgment",
    "C4ScopedFormationResourceLimit", "C4ScopedFormationResult",
    "C4ScopedFormationValidationError", "c4_bound_g4_bridge_source",
    "c4_bound_patch_requirement", "c4_finite_scoped_formation_rule",
    "c4_finite_scoped_formation_rule_source",
    "c4_formation_persistence_requirement", "c4_formation_policy",
    "c4_formation_refinement_requirement", "c4_formation_scope",
    "c4_g4_bridge_mappings", "c4_scoped_formation_judgment",
    "c4_scoped_formation_scope_boundary", "c4_snapshot_formation_scope",
    "c4_stage_map_row", "c4_validate_scoped_formation_result",
)
