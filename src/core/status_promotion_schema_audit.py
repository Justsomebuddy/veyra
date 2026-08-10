"""Bounded allowlisted P2-S2 result-schema audit; no package reflection."""

from __future__ import annotations

from dataclasses import fields
import logging

from .all_depth_family_types import AllDepthFamilyJudgment
from .confluence_aggregate_types import FiniteConfluenceAggregate
from .confluence_types import ForkConfluenceJudgment
from .construction.finite_builder.types import FiniteConstructionJudgment
from .observer_genesis_types import GenesisJudgment
from .status_promotion_common import (
    exact_bool, exact_digest, exact_identifier, exact_shape, exact_tuple, reject,
)
from .status_promotion_digest import digest, text_rows
from .status_promotion_runtime import _resource
from .status_promotion_types import (
    MetaAuditDecision, MetaOntologicalStatus, PromotionAuditPolicy,
    PromotionRegistry, PromotionResourceLimit, ResourceBound, SchemaAuditReport,
    SchemaAuditRow,
)
from .status_promotion_validation import validate_policy, validate_registry

logger = logging.getLogger(__name__)
SCHEMA_AUDIT_SCOPE = "fixed-allowlist-five-only"
SCHEMA_AUDIT_NONCLAIMS = (
    "codebase-completeness", "ontology-correctness", "retroactive-certification",
)

_ALLOWLIST = {
    "finite-construction-judgment": FiniteConstructionJudgment,
    "observer-genesis-judgment": GenesisJudgment,
    "fork-confluence-judgment": ForkConfluenceJudgment,
    "finite-confluence-aggregate": FiniteConfluenceAggregate,
    "all-depth-family-judgment": AllDepthFamilyJudgment,
}
_SCHEMA_REQUEST_DIGEST = digest("veyra.p2s.schema-audit-request.v1", (
    ("allowlist", b"p2-s-fixed-five-v1"),
))


def audit_allowlisted_schemas(
    registry: PromotionRegistry, policy: PromotionAuditPolicy,
) -> SchemaAuditReport | PromotionResourceLimit:
    """Inspect only five direct classes after fixed-count preflight."""
    logger.debug("audit_allowlisted_schemas entry")
    validate_registry(registry)
    validate_policy(policy)
    schema_count = len(registry.schema_targets)
    if schema_count > policy.max_schemas:
        return _resource(
            "schema-audit", _SCHEMA_REQUEST_DIGEST, ResourceBound.SCHEMA_COUNT,
            schema_count, policy.max_schemas, policy,
        )
    field_count = sum(len(item.exact_fields) for item in registry.schema_targets)
    if field_count > policy.max_fields:
        return _resource(
            "schema-audit", _SCHEMA_REQUEST_DIGEST, ResourceBound.FIELD_COUNT,
            field_count, policy.max_fields, policy,
        )
    rows = tuple(_audit_target(target) for target in registry.schema_targets)
    report_digest = digest("veyra.p2s.schema-audit-report.v1", (
        ("registry", registry.registry_digest.encode()),
        ("policy", policy.policy_digest.encode()),
        *text_rows("row", tuple(item.row_digest for item in rows)),
        ("scope", SCHEMA_AUDIT_SCOPE.encode()),
        *text_rows("nonclaim", SCHEMA_AUDIT_NONCLAIMS),
        ("decision", MetaAuditDecision.SCHEMA_CONFORMANT.value.encode()),
        ("ontology", MetaOntologicalStatus.NOT_CLAIMED.value.encode()),
    ))
    result = SchemaAuditReport(
        registry.registry_digest, policy.policy_digest, rows,
        SCHEMA_AUDIT_SCOPE, SCHEMA_AUDIT_NONCLAIMS, report_digest,
        MetaAuditDecision.SCHEMA_CONFORMANT,
    )
    logger.debug("audit_allowlisted_schemas exit rows=%d", len(rows))
    return result


def validate_schema_audit_report(
    value: object, registry: PromotionRegistry, policy: PromotionAuditPolicy,
) -> SchemaAuditReport:
    """Validate the exact scoped meta-report before canonical equality."""
    logger.debug("validate_schema_audit_report entry")
    exact_shape(value, SchemaAuditReport, "schema-audit-report")
    exact_digest(value.registry_digest, "schema-report-registry-digest")
    exact_digest(value.policy_digest, "schema-report-policy-digest")
    exact_tuple(value.rows, "schema-report-rows")
    for row in value.rows:
        exact_shape(row, SchemaAuditRow, "schema-audit-row")
        exact_identifier(row.schema_id, "schema-row-id")
        exact_bool(row.exact_match, "schema-row-exact-match")
        exact_bool(row.forbidden_fields_absent, "schema-row-forbidden-absent")
        exact_digest(row.row_digest, "schema-row-digest")
    exact_identifier(value.scope, "schema-report-scope")
    exact_tuple(value.nonclaims, "schema-report-nonclaims", nonempty=True)
    for nonclaim in value.nonclaims:
        exact_identifier(nonclaim, "schema-report-nonclaim")
    exact_digest(value.report_digest, "schema-report-digest")
    if type(value.decision) is not MetaAuditDecision:
        reject("invalid-schema-report-decision")
    if type(value.ontological_establishment) is not MetaOntologicalStatus:
        reject("invalid-schema-report-ontology-status")
    expected = audit_allowlisted_schemas(registry, policy)
    if type(expected) is not SchemaAuditReport or value != expected:
        reject("schema-audit-report-not-fresh")
    logger.debug("validate_schema_audit_report exit")
    return value


def _audit_target(target) -> SchemaAuditRow:
    logger.debug("_audit_target entry schema=%s", target.schema_id)
    dto_type = _ALLOWLIST.get(target.schema_id)
    if dto_type is None:
        reject("schema-target-not-allowlisted")
    actual = tuple(item.name for item in fields(dto_type))
    exact_match = actual == target.exact_fields
    forbidden_absent = not set(actual).intersection(target.forbidden_positive_fields)
    if not exact_match or not forbidden_absent:
        reject("allowlisted-schema-drift")
    row_digest = digest("veyra.p2s.schema-audit-row.v1", (
        ("schema", target.schema_id.encode()), *text_rows("actual", actual),
        ("exact", b"true"), ("forbidden-absent", b"true"),
    ))
    result = SchemaAuditRow(target.schema_id, True, True, row_digest)
    logger.debug("_audit_target exit schema=%s", target.schema_id)
    return result
