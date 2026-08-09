"""Direct level-1 certificate for P2-S1--S4 meta-validation only."""

from __future__ import annotations

import logging

from ..certify_types import Certificate
from ..registry.status_promotion.core import (
    CastAttackOutcome, EvidenceStatus as S, JudgmentKind as K,
    LITERAL_ORACLE_DIGEST, MetaAuditDecision, MetaOntologicalStatus,
    PositiveProvenance as P, SCHEMA_AUDIT_NONCLAIMS, SCHEMA_AUDIT_SCOPE,
    PromotionSchemaAudit, SchemaAuditReport, adjacent_cast_attack_matrix,
    assumption_node, audit_allowlisted_schemas, audit_promotion_request,
    audit_registry_against_literal_oracle,
    claim_descriptor, evidence_field, index_binding, premise_artifact,
    project_index_existential, project_premise_artifact, promotion_audit_request,
    promotion_policy, promotion_registry, validate_schema_audit_report,
)
from ..registry.status_promotion.core import digest

logger = logging.getLogger(__name__)
EXPECTED_LITERAL_ORACLE_DIGEST = (
    "2cbe0f2f1f1025696b947c73e32196f230e7748c77c030543d2292a34585875a"
)


def _d(label: str) -> str:
    logger.debug("_d entry label=%s", label)
    result = digest("veyra.p2s.certificate-fixture.v1", (("label", label.encode()),))
    logger.debug("_d exit")
    return result


def _valid_generation(registry):
    logger.debug("_valid_generation entry")
    doctrine = index_binding("doctrine", _d("doctrine"))
    scope = index_binding("scope", _d("scope"))
    stage = index_binding("stage", _d("stage"))
    seed = premise_artifact(
        "seed", "seed-source", _d("seed-artifact"), (doctrine,),
        (evidence_field("seed", _d("seed-evidence")),),
    )
    program = premise_artifact(
        "program", "closed-program", _d("program-artifact"), (scope, stage),
        (evidence_field("replay", _d("replay-evidence")),),
    )
    conclusion = claim_descriptor(
        "finite-generation-claim", K.GENERABLE, S.ESTABLISHED_RELATIVE_TO_SCOPE,
        P.EXECUTABLE_REPLAY, (doctrine, scope, stage), registry,
    )
    assumptions = (
        assumption_node("a-source", "source-is-bound", (), _d("a-source")),
        assumption_node("a-replay", "program-replays", ("a-source",), _d("a-replay")),
    )
    result = promotion_audit_request(
        "p1-b-finite-generation-v1", (seed, program), assumptions, conclusion, registry,
    )
    logger.debug("_valid_generation exit")
    return result


def certify_status_promotion_p2s() -> Certificate:
    """Certify registry/audit/projection attacks without certifying ontology."""
    logger.debug("certify_status_promotion_p2s entry")
    registry = promotion_registry()
    oracle_digest = audit_registry_against_literal_oracle(registry)
    policy = promotion_policy()
    request = _valid_generation(registry)
    audit = audit_promotion_request(registry, request, policy)
    schemas = audit_allowlisted_schemas(registry, policy)
    attacks = adjacent_cast_attack_matrix(registry)
    premise_projection = project_premise_artifact(
        registry, request, audit,  # type: ignore[arg-type]
        "p2-project-p1-b-finite-generation-v1-seed-v1", policy,
    )
    index_projection = project_index_existential(
        registry, request.conclusion, "p2-exists-generable-stage-v1",
    )
    family = next(item for item in registry.domains if item.kind is K.ALL_DEPTH_FAMILY)
    d3_pairs = {
        (pair.status, pair.provenance) for pair in family.positive_pairs
    } == {
        (S.ESTABLISHED_RELATIVE_TO_LEDGER, P.FORMALLY_DERIVED),
        (S.ASSUMED, P.SUPPLIED_HYPOTHESIS), (S.ASSUMED, P.ORACLE_DEPENDENT),
    }
    scope = next(item for item in registry.domains if item.kind is K.GENERABLE)
    distinct_execution = {
        pair.provenance for pair in scope.positive_pairs
    } == {P.EXECUTABLE_REPLAY, P.FORMALLY_DERIVED}
    passed = (
        len(registry.domains) == 15 and len(registry.rules) == 17
        and d3_pairs and distinct_execution
        and type(audit) is PromotionSchemaAudit
        and audit.decision is MetaAuditDecision.SCHEMA_CONFORMANT
        and audit.ontological_establishment is MetaOntologicalStatus.NOT_CLAIMED
        and audit.assumption_closure == ("a-source", "a-replay")
        and premise_projection.artifact is request.premises[0]
        and index_projection.existential
        and index_projection.hidden_binding.name == "stage"
        and tuple(item.name for item in index_projection.retained_indices)
        == ("doctrine", "scope")
        and oracle_digest == LITERAL_ORACLE_DIGEST == EXPECTED_LITERAL_ORACLE_DIGEST
        and len(registry.premise_projections) == 40
        and len(registry.index_projections) == 1
        and type(schemas) is SchemaAuditReport
        and validate_schema_audit_report(schemas, registry, policy) is schemas
        and len(schemas.rows) == 5 and schemas.scope == SCHEMA_AUDIT_SCOPE
        and schemas.nonclaims == SCHEMA_AUDIT_NONCLAIMS
        and len(attacks.rows) == 12
        and all(row.outcome is CastAttackOutcome.REJECTED for row in attacks.rows)
        and all(row.matching_rule_count == 0 for row in attacks.rows)
    )
    detail = (
        f"domains={len(registry.domains)}/15 rules={len(registry.rules)}/17 "
        f"schemas={len(schemas.rows) if type(schemas) is SchemaAuditReport else 0}/5 "
        f"cast_attacks={len(attacks.rows)}/12 promotions=0 ontology_claims=0 "
        f"literal_oracle_digest={oracle_digest}"
    )
    result = Certificate(
        "status_promotion_p2s", "P2-S registry and meta-validation boundaries",
        passed, detail, 1,
    )
    logger.debug("certify_status_promotion_p2s exit passed=%s", passed)
    return result
