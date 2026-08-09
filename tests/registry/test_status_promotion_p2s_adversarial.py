"""Hostile DTO, anti-circularity, and no-cast pressure for P2-S."""

from dataclasses import replace

import pytest

from src.core.status_promotion import (
    EvidenceStatus as S, JudgmentKind as K, PositiveProvenance as P,
    PromotionAuditRequest, PromotionResourceLimit,
    LITERAL_ORACLE_DIGEST, ResourceBound, SchemaAuditReport,
    StatusPromotionValidationError, assumption_node,
    audit_allowlisted_schemas, audit_promotion_request,
    audit_registry_against_literal_oracle, claim_descriptor, evidence_field,
    project_index_existential, project_premise_artifact,
    promotion_audit_request, promotion_policy, validate_registry,
    validate_schema_audit_report,
)
from src.core.status_promotion_digest import digest
from src.core.status_promotion_projection_commitment import premise_projection_digest
from status_promotion_fixture import valid_case


def _d(label: str) -> str:
    return digest("test.p2s.hostile.v1", (("label", label.encode()),))


def test_rejects_str_enum_bool_int_and_subclass_shapes() -> None:
    registry, _, request = valid_case()
    with pytest.raises(StatusPromotionValidationError):
        claim_descriptor(
            "bad", K.GENERABLE.value, S.ESTABLISHED_RELATIVE_TO_SCOPE,
            P.EXECUTABLE_REPLAY, request.conclusion.indices, registry,
        )
    with pytest.raises(StatusPromotionValidationError):
        promotion_policy(max_premises=True)

    class RegistrySubclass(type(registry)):
        pass

    hostile = RegistrySubclass(*tuple(vars(registry).values()))
    with pytest.raises(StatusPromotionValidationError):
        validate_registry(hostile)


def test_open_and_refuted_cannot_carry_positive_provenance() -> None:
    registry, _, request = valid_case()
    with pytest.raises(StatusPromotionValidationError):
        claim_descriptor(
            "open", K.GENERABLE, S.OPEN, P.EXECUTABLE_REPLAY,
            request.conclusion.indices, registry,
        )
    with pytest.raises(StatusPromotionValidationError):
        claim_descriptor(
            "refuted", K.GENERABLE, S.REFUTED, P.FORMALLY_DERIVED,
            request.conclusion.indices, registry,
        )


@pytest.mark.parametrize(
    "artifact_kind", ["bool", "digest-only", "old-certificate", "old-judgment"],
)
def test_forbidden_sources_cannot_promote(artifact_kind: str) -> None:
    registry, policy, request = valid_case()
    bad_seed = replace(request.premises[0], artifact_kind=artifact_kind)
    bad_request = promotion_audit_request(
        request.rule_id, (bad_seed, request.premises[1]), request.assumptions,
        request.conclusion, registry,
    )
    with pytest.raises(StatusPromotionValidationError, match="forbidden-promotion-source"):
        audit_promotion_request(registry, bad_request, policy)


def test_exact_premise_fields_and_indices_prevent_silent_drop() -> None:
    registry, policy, request = valid_case()
    seed = request.premises[0]
    extra = replace(
        seed,
        evidence_fields=seed.evidence_fields + (evidence_field("extra", _d("extra")),),
    )
    bad = promotion_audit_request(
        request.rule_id, (extra, request.premises[1]), request.assumptions,
        request.conclusion, registry,
    )
    with pytest.raises(StatusPromotionValidationError, match="evidence-fields-not-exact"):
        audit_promotion_request(registry, bad, policy)
    reordered = replace(
        request.conclusion,
        indices=(request.conclusion.indices[1], request.conclusion.indices[0],
                 request.conclusion.indices[2]),
    )
    with pytest.raises(StatusPromotionValidationError):
        project_index_existential(registry, reordered, "p2-exists-generable-stage-v1")


def test_assumption_cycle_missing_dependency_and_own_conclusion_rejected() -> None:
    registry, policy, request = valid_case()
    cases = (
        (
            assumption_node("x", "x-claim", ("y",), _d("x")),
            assumption_node("y", "y-claim", ("x",), _d("y")),
        ),
        (assumption_node("x", "x-claim", ("missing",), _d("x")),),
        (assumption_node("x", request.conclusion.claim_id, (), _d("x")),),
    )
    for assumptions in cases:
        candidate = promotion_audit_request(
            request.rule_id, request.premises, assumptions, request.conclusion, registry,
        )
        with pytest.raises(StatusPromotionValidationError):
            audit_promotion_request(registry, candidate, policy)


def test_preflight_refuses_without_traversing_hostile_premise() -> None:
    registry, _, request = valid_case()

    class Trap:
        def __getattribute__(self, name):
            raise AssertionError(f"traversed:{name}")

    policy = promotion_policy(max_premises=1)
    hostile = PromotionAuditRequest(
        request.version, request.rule_id, (Trap(), Trap()), (),
        request.conclusion, request.request_digest,
    )
    result = audit_promotion_request(registry, hostile, policy)
    assert type(result) is PromotionResourceLimit
    assert result.failed_bound is ResourceBound.PREMISE_COUNT


def test_bare_status_or_audit_cannot_replace_premise_artifact() -> None:
    registry, policy, request = valid_case()
    with pytest.raises(StatusPromotionValidationError):
        project_premise_artifact(
            registry, request, request.conclusion,  # type: ignore[arg-type]
            "p2-project-p1-b-finite-generation-v1-seed-v1", policy,
        )
    fake = replace(request, premises=(request.conclusion, request.premises[1]))
    with pytest.raises(StatusPromotionValidationError):
        audit_promotion_request(registry, fake, policy)


def test_hostile_audit_enum_is_rejected_before_equality() -> None:
    registry, policy, request = valid_case()
    audit = audit_promotion_request(registry, request, policy)
    hostile = replace(audit, decision="schema-conformant")
    with pytest.raises(StatusPromotionValidationError, match="invalid-audit-decision"):
        project_premise_artifact(
            registry, request, hostile,  # type: ignore[arg-type]
            "p2-project-p1-b-finite-generation-v1-seed-v1", policy,
        )


def test_schema_count_has_typed_preflight_refusal() -> None:
    registry, _, _ = valid_case()
    result = audit_allowlisted_schemas(registry, promotion_policy(max_schemas=4))
    assert type(result) is PromotionResourceLimit
    assert result.failed_bound is ResourceBound.SCHEMA_COUNT


def test_schema_report_scope_and_nonclaims_are_exactly_bound() -> None:
    registry, policy, _ = valid_case()
    report = audit_allowlisted_schemas(registry, policy)
    assert type(report) is SchemaAuditReport
    for hostile in (
        replace(report, scope="all-public-dtos"),
        replace(report, nonclaims=("codebase-completeness",)),
    ):
        with pytest.raises(StatusPromotionValidationError):
            validate_schema_audit_report(hostile, registry, policy)


def test_literal_oracle_defeats_self_consistent_generator_drift(monkeypatch) -> None:
    registry, _, _ = valid_case()
    first = replace(registry.domains[0], allowed_statuses=(S.ESTABLISHED,))
    drifted = replace(registry, domains=(first,) + registry.domains[1:])
    import src.core.status_promotion_validation as validation
    monkeypatch.setattr(validation, "promotion_registry", lambda: drifted)
    with pytest.raises(StatusPromotionValidationError, match="domain-oracle-mismatch"):
        audit_registry_against_literal_oracle(drifted)
    assert len(LITERAL_ORACLE_DIGEST) == 64


def test_literal_oracle_pins_rule_forbidden_tuple_and_assumption_policy(monkeypatch) -> None:
    registry, _, _ = valid_case()
    first = registry.rules[0]
    hostile_rules = (
        replace(first, forbidden_source_types=first.forbidden_source_types + ("new-source",)),
        replace(first, assumption_policy_id="self-consistent-but-wrong-policy"),
    )
    import src.core.status_promotion_validation as validation
    for hostile_rule in hostile_rules:
        drifted = replace(registry, rules=(hostile_rule,) + registry.rules[1:])
        monkeypatch.setattr(validation, "promotion_registry", lambda value=drifted: value)
        with pytest.raises(StatusPromotionValidationError, match="rule-oracle-mismatch"):
            audit_registry_against_literal_oracle(drifted)


def test_projection_rename_changes_digest_and_literal_oracle_rejects(monkeypatch) -> None:
    registry, _, _ = valid_case()
    original = registry.premise_projections[0]
    renamed_id = original.projection_id + "-renamed"
    renamed_digest = premise_projection_digest(
        renamed_id, original.source_rule_id, original.premise_name,
    )
    assert renamed_digest != original.projection_digest
    renamed = replace(
        original, projection_id=renamed_id, projection_digest=renamed_digest,
    )
    drifted = replace(
        registry, premise_projections=(renamed,) + registry.premise_projections[1:],
    )
    import src.core.status_promotion_validation as validation
    monkeypatch.setattr(validation, "promotion_registry", lambda: drifted)
    with pytest.raises(StatusPromotionValidationError, match="projection-oracle-mismatch"):
        audit_registry_against_literal_oracle(drifted)
