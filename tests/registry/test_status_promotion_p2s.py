"""Focused positive tests for the P2-S1--S4 meta-calculus."""

from src.core.certify_status_promotion import certify_status_promotion_p2s
from src.core.status_promotion import (
    CastAttackOutcome, EvidenceStatus as S, JudgmentKind as K,
    LITERAL_ORACLE_DIGEST,
    MetaAuditDecision, MetaOntologicalStatus, PositiveProvenance as P,
    PromotionSchemaAudit, SchemaAuditReport, adjacent_cast_attack_matrix,
    SCHEMA_AUDIT_NONCLAIMS, SCHEMA_AUDIT_SCOPE, audit_allowlisted_schemas,
    audit_promotion_request, audit_registry_against_literal_oracle,
    project_index_existential, project_premise_artifact,
    promotion_registry, validate_index_projection,
    validate_registry, validate_schema_audit_report,
)
from status_promotion_fixture import valid_case

EXPECTED_LITERAL_ORACLE_DIGEST = (
    "2cbe0f2f1f1025696b947c73e32196f230e7748c77c030543d2292a34585875a"
)


def test_registry_exact_matrix_and_d3_pairs() -> None:
    registry = validate_registry(promotion_registry())
    assert LITERAL_ORACLE_DIGEST == EXPECTED_LITERAL_ORACLE_DIGEST
    assert audit_registry_against_literal_oracle(registry) == EXPECTED_LITERAL_ORACLE_DIGEST
    assert len(registry.domains) == 15
    assert len(registry.rules) == 17
    family = next(item for item in registry.domains if item.kind is K.ALL_DEPTH_FAMILY)
    assert {(item.status, item.provenance) for item in family.positive_pairs} == {
        (S.ESTABLISHED_RELATIVE_TO_LEDGER, P.FORMALLY_DERIVED),
        (S.ASSUMED, P.SUPPLIED_HYPOTHESIS),
        (S.ASSUMED, P.ORACLE_DEPENDENT),
    }
    generable = next(item for item in registry.domains if item.kind is K.GENERABLE)
    assert {item.provenance for item in generable.positive_pairs} == {
        P.EXECUTABLE_REPLAY, P.FORMALLY_DERIVED,
    }


def test_named_promotion_and_eliminations_are_meta_only() -> None:
    registry, policy, request = valid_case()
    audit = audit_promotion_request(registry, request, policy)
    assert type(audit) is PromotionSchemaAudit
    assert audit.decision is MetaAuditDecision.SCHEMA_CONFORMANT
    assert audit.ontological_establishment is MetaOntologicalStatus.NOT_CLAIMED
    assert audit.assumption_closure == ("a0", "a1")
    premise = project_premise_artifact(
        registry, request, audit,
        "p2-project-p1-b-finite-generation-v1-seed-v1", policy,
    )
    assert premise.artifact is request.premises[0]
    projected = project_index_existential(
        registry, request.conclusion, "p2-exists-generable-stage-v1",
    )
    assert validate_index_projection(
        projected, registry, "p2-exists-generable-stage-v1",
    ) is projected
    assert projected.hidden_binding.name == "stage"
    assert tuple(item.name for item in projected.retained_indices) == ("doctrine", "scope")


def test_allowlisted_schema_and_attack_matrix() -> None:
    registry, policy, _ = valid_case()
    report = audit_allowlisted_schemas(registry, policy)
    assert type(report) is SchemaAuditReport
    assert validate_schema_audit_report(report, registry, policy) is report
    assert len(report.rows) == 5
    assert report.scope == SCHEMA_AUDIT_SCOPE == "fixed-allowlist-five-only"
    assert report.nonclaims == SCHEMA_AUDIT_NONCLAIMS
    assert "codebase-completeness" in report.nonclaims
    assert "ontology-correctness" in report.nonclaims
    assert all(row.exact_match and row.forbidden_fields_absent for row in report.rows)
    attacks = adjacent_cast_attack_matrix(registry)
    assert len(attacks.rows) == 12
    assert all(row.outcome is CastAttackOutcome.REJECTED for row in attacks.rows)
    assert all(row.matching_rule_count == 0 for row in attacks.rows)


def test_direct_certificate() -> None:
    certificate = certify_status_promotion_p2s()
    assert certificate.passed
    assert "promotions=0 ontology_claims=0" in certificate.detail
    assert f"literal_oracle_digest={EXPECTED_LITERAL_ORACLE_DIGEST}" in certificate.detail
