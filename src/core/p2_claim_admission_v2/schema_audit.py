"""Dedicated fixed-five schema audit for the additive P2 registry-v2."""

from __future__ import annotations

from dataclasses import fields
import logging

from ..all_depth_family_types import AllDepthFamilyJudgment
from ..confluence_aggregate_types import FiniteConfluenceAggregate
from ..confluence_types import ForkConfluenceJudgment
from ..construction.finite_builder.types import FiniteConstructionJudgment
from ..observer_genesis_types import GenesisJudgment
from ..status_promotion_digest import digest, text_rows
from ..status_promotion_types import (
    MetaAuditDecision,
    MetaOntologicalStatus,
    PromotionRegistry,
    SchemaAuditReport,
    SchemaAuditRow,
    SchemaTarget,
)
from ..status_promotion_validation import promotion_policy
from .errors import P2ClaimAdmissionError, reject
from .registry import (
    PERMANENT_NONCLAIMS,
    audit_registry_v2_against_literal_oracle,
    promotion_registry_v2,
    validate_registry_v2,
)
from .validation import capture_exact_core_tree

logger = logging.getLogger(__name__)

SCHEMA_AUDIT_SCOPE_V2 = "p2-claim-admission-v2-fixed-five-schema-meta-only"
SCHEMA_AUDIT_NONCLAIMS_V2 = (
    "codebase-completeness",
    "ontology-correctness",
    "retroactive-certification",
    *PERMANENT_NONCLAIMS,
)
_SCHEMA_ALLOWLIST = (
    ("finite-construction-judgment", FiniteConstructionJudgment),
    ("observer-genesis-judgment", GenesisJudgment),
    ("fork-confluence-judgment", ForkConfluenceJudgment),
    ("finite-confluence-aggregate", FiniteConfluenceAggregate),
    ("all-depth-family-judgment", AllDepthFamilyJudgment),
)


def _audit_schema_target_v2(target: SchemaTarget, expected_id: str, dto_type: type) -> SchemaAuditRow:
    """Audit one exact ordered target and bind its registry target digest."""
    logger.debug("_audit_schema_target_v2 entry schema=%s", expected_id)
    if type(target) is not SchemaTarget or target.schema_id != expected_id:
        reject("schema-audit-target-order")
    actual = tuple(item.name for item in fields(dto_type))
    if actual != target.exact_fields or set(actual).intersection(target.forbidden_positive_fields):
        reject("allowlisted-schema-drift")
    row_digest = digest(
        "veyra.p2-claim-admission.schema-audit-row.v2",
        (
            ("schema", expected_id.encode()),
            ("target", target.schema_digest.encode()),
            *text_rows("actual", actual),
            ("exact", b"true"),
            ("forbidden-absent", b"true"),
        ),
    )
    result = SchemaAuditRow(expected_id, True, True, row_digest)
    logger.debug("_audit_schema_target_v2 exit schema=%s", expected_id)
    return result


def build_presentation_schema_audit_report_v2(registry: PromotionRegistry) -> SchemaAuditReport:
    """Audit exactly the five frozen schema targets in registry-v2 order."""
    logger.debug("build_presentation_schema_audit_report_v2 entry")
    validate_registry_v2(registry)
    registry = promotion_registry_v2()
    audit_registry_v2_against_literal_oracle(registry)
    policy = promotion_policy()
    targets = registry.schema_targets
    if type(targets) is not tuple or len(targets) != len(_SCHEMA_ALLOWLIST):
        reject("schema-audit-target-count")
    if len(targets) > policy.max_schemas:
        reject("schema-audit-target-resource")
    field_count = sum(len(target.exact_fields) for target in targets)
    if field_count > policy.max_fields:
        reject("schema-audit-field-resource")
    rows = tuple(
        _audit_schema_target_v2(target, schema_id, dto_type)
        for target, (schema_id, dto_type) in zip(targets, _SCHEMA_ALLOWLIST, strict=True)
    )
    report_digest = digest(
        "veyra.p2-claim-admission.schema-audit-report.v2",
        (
            ("registry", registry.registry_digest.encode()),
            ("policy", policy.policy_digest.encode()),
            *text_rows("row", tuple(item.row_digest for item in rows)),
            ("scope", SCHEMA_AUDIT_SCOPE_V2.encode()),
            *text_rows("nonclaim", SCHEMA_AUDIT_NONCLAIMS_V2),
            ("decision", MetaAuditDecision.SCHEMA_CONFORMANT.value.encode()),
            ("ontology", MetaOntologicalStatus.NOT_CLAIMED.value.encode()),
        ),
    )
    result = SchemaAuditReport(
        registry.registry_digest,
        policy.policy_digest,
        rows,
        SCHEMA_AUDIT_SCOPE_V2,
        SCHEMA_AUDIT_NONCLAIMS_V2,
        report_digest,
        MetaAuditDecision.SCHEMA_CONFORMANT,
    )
    logger.info("build_presentation_schema_audit_report_v2 state=SCHEMA_CONFORMANT rows=5")
    logger.debug("build_presentation_schema_audit_report_v2 exit")
    return result


def validate_presentation_schema_audit_report_v2(
    value: object,
    registry: PromotionRegistry,
) -> bool:
    """Bound, reconstruct, and exact-compare the registry-v2 fixed-five report."""
    logger.debug("validate_presentation_schema_audit_report_v2 entry type=%s", type(value).__name__)
    try:
        if type(value) is not SchemaAuditReport:
            reject("schema-audit-report-type")
        value, _, _ = capture_exact_core_tree(value)
        if type(value) is not SchemaAuditReport:
            reject("schema-audit-report-type")
        if type(value.rows) is not tuple or len(value.rows) != 5:
            reject("schema-audit-report-rows")
        if any(type(row) is not SchemaAuditRow for row in value.rows):
            reject("schema-audit-report-row-type")
        valid = value == build_presentation_schema_audit_report_v2(registry)
    except (AttributeError, P2ClaimAdmissionError, TypeError, UnicodeError, ValueError):
        logger.error("validate_presentation_schema_audit_report_v2 rejected")
        valid = False
    logger.debug("validate_presentation_schema_audit_report_v2 exit valid=%s", valid)
    return valid
