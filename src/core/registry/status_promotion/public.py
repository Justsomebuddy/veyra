"""Collision-safe root aliases for the released P2-S meta-validator."""

from __future__ import annotations

from . import core as _p2s

P2S_ASSUMPTION_POLICY_ID = _p2s.ASSUMPTION_POLICY_ID
P2S_DEFAULT_POLICY = _p2s.DEFAULT_POLICY
P2S_FORBIDDEN_CONCLUSION_FIELDS = _p2s.FORBIDDEN_CONCLUSION_FIELDS
P2S_FORBIDDEN_SOURCE_TYPES = _p2s.FORBIDDEN_SOURCE_TYPES
P2S_LITERAL_ORACLE_DIGEST = _p2s.LITERAL_ORACLE_DIGEST
P2S_NONCLAIMS = _p2s.NONCLAIMS
P2S_REGISTRY_VERSION = _p2s.REGISTRY_VERSION
P2S_SCHEMA_AUDIT_NONCLAIMS = _p2s.SCHEMA_AUDIT_NONCLAIMS
P2S_SCHEMA_AUDIT_SCOPE = _p2s.SCHEMA_AUDIT_SCOPE

P2SJudgmentKind = _p2s.JudgmentKind
P2SEvidenceStatus = _p2s.EvidenceStatus
P2SPositiveProvenance = _p2s.PositiveProvenance
P2SMetaAuditDecision = _p2s.MetaAuditDecision
P2SMetaOntologicalStatus = _p2s.MetaOntologicalStatus
P2SResourceBound = _p2s.ResourceBound
P2SCastAttackOutcome = _p2s.CastAttackOutcome
P2SStatusProvenancePair = _p2s.StatusProvenancePair
P2SKindStatusDomain = _p2s.KindStatusDomain
P2SPremiseSignature = _p2s.PremiseSignature
P2SPromotionRule = _p2s.PromotionRule
P2SPremiseProjectionRule = _p2s.PremiseProjectionRule
P2SIndexProjectionRule = _p2s.IndexProjectionRule
P2SSchemaTarget = _p2s.SchemaTarget
P2SPromotionRegistry = _p2s.PromotionRegistry
P2SIndexBinding = _p2s.IndexBinding
P2SEvidenceField = _p2s.EvidenceField
P2SPremiseArtifact = _p2s.PremiseArtifact
P2SAssumptionNode = _p2s.AssumptionNode
P2SClaimDescriptor = _p2s.ClaimDescriptor
P2SPromotionAuditRequest = _p2s.PromotionAuditRequest
P2SPromotionAuditPolicy = _p2s.PromotionAuditPolicy
P2SPromotionSchemaAudit = _p2s.PromotionSchemaAudit
P2SPromotionResourceLimit = _p2s.PromotionResourceLimit
P2SPremiseProjection = _p2s.PremiseProjection
P2SIndexProjection = _p2s.IndexProjection
P2SSchemaAuditRow = _p2s.SchemaAuditRow
P2SSchemaAuditReport = _p2s.SchemaAuditReport
P2SCastAttack = _p2s.CastAttack
P2SCastAttackRow = _p2s.CastAttackRow
P2SCastAttackMatrixReport = _p2s.CastAttackMatrixReport
P2SStatusPromotionValidationError = _p2s.StatusPromotionValidationError

p2s_adjacent_cast_attack_matrix = _p2s.adjacent_cast_attack_matrix
p2s_assumption_node = _p2s.assumption_node
p2s_audit_allowlisted_schemas = _p2s.audit_allowlisted_schemas
p2s_audit_promotion_request = _p2s.audit_promotion_request
p2s_audit_registry_against_literal_oracle = _p2s.audit_registry_against_literal_oracle
p2s_claim_descriptor = _p2s.claim_descriptor
p2s_evidence_field = _p2s.evidence_field
p2s_index_binding = _p2s.index_binding
p2s_premise_artifact = _p2s.premise_artifact
p2s_project_index_existential = _p2s.project_index_existential
p2s_project_premise_artifact = _p2s.project_premise_artifact
p2s_promotion_audit_request = _p2s.promotion_audit_request
p2s_promotion_policy = _p2s.promotion_policy
p2s_promotion_registry = _p2s.promotion_registry
p2s_validate_claim_descriptor = _p2s.validate_claim_descriptor
p2s_validate_index_projection = _p2s.validate_index_projection
p2s_validate_policy = _p2s.validate_policy
p2s_validate_premise_artifact = _p2s.validate_premise_artifact
p2s_validate_registry = _p2s.validate_registry
p2s_validate_request_deep = _p2s.validate_request_deep
p2s_validate_request_shallow = _p2s.validate_request_shallow
p2s_validate_schema_audit = _p2s.validate_schema_audit
p2s_validate_schema_audit_report = _p2s.validate_schema_audit_report

__all__ = (
    "P2S_ASSUMPTION_POLICY_ID", "P2S_DEFAULT_POLICY",
    "P2S_FORBIDDEN_CONCLUSION_FIELDS", "P2S_FORBIDDEN_SOURCE_TYPES",
    "P2S_LITERAL_ORACLE_DIGEST", "P2S_NONCLAIMS", "P2S_REGISTRY_VERSION",
    "P2S_SCHEMA_AUDIT_NONCLAIMS", "P2S_SCHEMA_AUDIT_SCOPE",
    "P2SJudgmentKind", "P2SEvidenceStatus", "P2SPositiveProvenance",
    "P2SMetaAuditDecision", "P2SMetaOntologicalStatus", "P2SResourceBound",
    "P2SCastAttackOutcome", "P2SStatusProvenancePair", "P2SKindStatusDomain",
    "P2SPremiseSignature", "P2SPromotionRule", "P2SPremiseProjectionRule",
    "P2SIndexProjectionRule", "P2SSchemaTarget", "P2SPromotionRegistry",
    "P2SIndexBinding", "P2SEvidenceField", "P2SPremiseArtifact",
    "P2SAssumptionNode", "P2SClaimDescriptor", "P2SPromotionAuditRequest",
    "P2SPromotionAuditPolicy", "P2SPromotionSchemaAudit",
    "P2SPromotionResourceLimit", "P2SPremiseProjection", "P2SIndexProjection",
    "P2SSchemaAuditRow", "P2SSchemaAuditReport", "P2SCastAttack",
    "P2SCastAttackRow", "P2SCastAttackMatrixReport",
    "P2SStatusPromotionValidationError", "p2s_adjacent_cast_attack_matrix",
    "p2s_assumption_node", "p2s_audit_allowlisted_schemas",
    "p2s_audit_promotion_request", "p2s_audit_registry_against_literal_oracle",
    "p2s_claim_descriptor", "p2s_evidence_field", "p2s_index_binding",
    "p2s_premise_artifact", "p2s_project_index_existential",
    "p2s_project_premise_artifact", "p2s_promotion_audit_request",
    "p2s_promotion_policy", "p2s_promotion_registry",
    "p2s_validate_claim_descriptor", "p2s_validate_index_projection",
    "p2s_validate_policy", "p2s_validate_premise_artifact",
    "p2s_validate_registry", "p2s_validate_request_deep",
    "p2s_validate_request_shallow", "p2s_validate_schema_audit",
    "p2s_validate_schema_audit_report",
)
