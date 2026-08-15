"""Additive P2 registry-v2 snapshot and independent extension oracle."""

from __future__ import annotations

from hashlib import sha256
import json
import logging

from ..status_promotion_catalog import promotion_registry
from ..status_promotion_digest import digest, frame, nested_rows, text_rows
from ..status_promotion_oracle import LITERAL_ORACLE_DIGEST, audit_registry_against_literal_oracle
from ..status_promotion_projection_commitment import premise_projection_digest
from ..status_promotion_types import (
    EvidenceStatus,
    IndexProjectionRule,
    JudgmentKind,
    KindStatusDomain,
    PositiveProvenance,
    PremiseProjectionRule,
    PremiseSignature,
    PromotionRegistry,
    PromotionRule,
    SchemaTarget,
    StatusProvenancePair,
)
from .errors import reject
from .resource_validation import (
    MAX_STRUCTURAL_NODES,
    charge_structure,
    charge_text,
    exact_digest,
    exact_identifier,
)

logger = logging.getLogger(__name__)

REGISTRY_VERSION = "p2-s-promotion-registry-v2"
RULE_ID = "composition-licensed-presentation-v2"
PREMISE_NAME = "composition"
PREMISE_KIND = "claim-composition-presentation-v2"
EVIDENCE_FIELDS = (
    "target-contract",
    "claim-set",
    "scope-set",
    "assumption-set",
    "doctrine-set",
    "source-validator-family",
    "source-family",
    "composition-license",
    "composition-assessment",
    "nonpromotion",
)
VISIBLE_INDICES = (
    "contract",
    "claims",
    "scope",
    "assumptions",
    "doctrine",
    "source-validators",
    "composition",
)
PERMANENT_NONCLAIMS = (
    "source-truth",
    "external-validator-trust",
    "logical-consistency",
    "logical-coherence",
    "assumption-discharge",
    "unconditionalization",
    "independence",
    "corroboration",
    "adaptive-validity",
    "family-validity",
    "statistical-validity",
    "population-validity",
    "universalization",
    "existential-upgrade",
    "objectivity",
    "observer-independence",
    "theorem",
    "certificate",
    "formal-proof",
    "ontology",
    "object",
    "history",
    "lifecycle",
    "empirical-instantiation",
    "physical-instantiation",
    "authentication",
    "custody",
    "chronology",
    "audit-as-truth",
)
PROJECTION_ID = "p2-project-composition-licensed-presentation-v2-composition-v2"
_V1_REGISTRY_DIGEST = "375f1654807b462c3a9ebd9a112a75ee28fc96a4029cf767acae1fd591a60e9d"
_LITERAL_STATEMENT_DIGEST = "a6f3b6742f3f3adbf9bd27b08034d4043575bf2ce07df532cb90c6d0b7cbe7f6"
_LITERAL_RULE_DIGEST = "b5e6bbff4bd0831e495fcd22f3846441b2a5bc2c0db37f00217322e03e0fe372"
_LITERAL_PROJECTION_DIGEST = "bad46ba3246b4ca5ade758902daa5bbfdf500d556988b6d07ff57fe636176441"
_LITERAL_FORBIDDEN_SOURCE_TYPES = (
    "bool",
    "digest-only",
    "old-certificate",
    "old-judgment",
    "finite-sample-table",
)
_LITERAL_FORBIDDEN_CONCLUSION_FIELDS = (
    "exists",
    "global_exists",
    "metaphysically_exists",
    "proof_complete",
    "observer_independent",
    "physical_exists",
)
_LITERAL_ASSUMPTION_POLICY_ID = "p2-s-acyclic-no-own-conclusion-v1"
REGISTRY_DIGEST = "ba6020151518faf5eb2fa2eb22943af4c7d0abd88b393b1388f848e63dbc3eb4"
EXTENSION_ORACLE_DIGEST = "ee55fcb02a6c69b8915e54ceee0ac7d0e2b741452198be6c49e9f14ae37488d3"


def _new_rule() -> PromotionRule:
    """Build the sole literal additive rule without mutating the v1 catalog."""
    logger.debug("_new_rule entry")
    base = promotion_registry()
    premise = PremiseSignature(PREMISE_NAME, PREMISE_KIND, EVIDENCE_FIELDS, VISIBLE_INDICES)
    statement = digest(
        "veyra.p2s.rule-statement.v2",
        (("rule-id", RULE_ID.encode()), ("statement", b"named-introduction:composition-licensed-presentation-v2")),
    )
    premise_frame = frame(
        "veyra.p2s.premise-signature.v2",
        (
            ("name", PREMISE_NAME.encode()),
            ("artifact-kind", PREMISE_KIND.encode()),
            *text_rows("evidence", EVIDENCE_FIELDS),
            *text_rows("index", VISIBLE_INDICES),
        ),
    )
    inherited = base.rules[0]
    value = digest(
        "veyra.p2s.promotion-rule.v2",
        (
            ("rule-id", RULE_ID.encode()),
            ("statement", statement.encode()),
            *nested_rows("premise", (premise_frame,)),
            ("output-kind", JudgmentKind.PRESENTED.value.encode()),
            ("output-status", EvidenceStatus.ESTABLISHED.value.encode()),
            ("output-provenance", PositiveProvenance.SUPPLIED_PRESENTATION.value.encode()),
            *text_rows("output-index", VISIBLE_INDICES),
            *text_rows("forbidden-source", inherited.forbidden_source_types),
            *text_rows("forbidden-conclusion", inherited.forbidden_conclusion_fields),
            ("assumption-policy", inherited.assumption_policy_id.encode()),
            *text_rows("nonclaim", PERMANENT_NONCLAIMS),
        ),
    )
    result = PromotionRule(
        RULE_ID,
        statement,
        (premise,),
        JudgmentKind.PRESENTED,
        EvidenceStatus.ESTABLISHED,
        PositiveProvenance.SUPPLIED_PRESENTATION,
        VISIBLE_INDICES,
        inherited.forbidden_source_types,
        inherited.forbidden_conclusion_fields,
        inherited.assumption_policy_id,
        PERMANENT_NONCLAIMS,
        value,
    )
    logger.debug("_new_rule exit")
    return result


def _new_projection() -> PremiseProjectionRule:
    """Build the one additive premise projection; no index projection is added."""
    logger.debug("_new_projection entry")
    result = PremiseProjectionRule(
        PROJECTION_ID,
        RULE_ID,
        PREMISE_NAME,
        premise_projection_digest(PROJECTION_ID, RULE_ID, PREMISE_NAME),
    )
    logger.debug("_new_projection exit")
    return result


def promotion_registry_v2() -> PromotionRegistry:
    """Return the full exact v1 snapshot plus exactly one rule and projection."""
    logger.debug("promotion_registry_v2 entry")
    base = promotion_registry()
    rule = _new_rule()
    projection = _new_projection()
    rules = base.rules + (rule,)
    projections = base.premise_projections + (projection,)
    value = digest(
        "veyra.p2s.registry.v2",
        (
            ("version", REGISTRY_VERSION.encode()),
            *text_rows("domain", tuple(item.domain_digest for item in base.domains)),
            *text_rows("rule", tuple(item.rule_digest for item in rules)),
            *text_rows("premise-projection", tuple(item.projection_digest for item in projections)),
            *text_rows("index-projection", tuple(item.projection_digest for item in base.index_projections)),
            *text_rows("schema", tuple(item.schema_digest for item in base.schema_targets)),
        ),
    )
    result = PromotionRegistry(
        REGISTRY_VERSION,
        base.domains,
        rules,
        projections,
        base.index_projections,
        base.schema_targets,
        value,
    )
    logger.debug("promotion_registry_v2 exit counts=15/18/41/1/5")
    return result


def compute_extension_oracle_digest() -> str:
    """Commit handwritten v1 pins and the complete literal extension row."""
    logger.debug("compute_extension_oracle_digest entry")
    payload = {
        "v1_registry_digest": _V1_REGISTRY_DIGEST,
        "v1_literal_oracle_digest": LITERAL_ORACLE_DIGEST,
        "rule": {
            "rule_id": RULE_ID,
            "statement_digest": _LITERAL_STATEMENT_DIGEST,
            "premise": [PREMISE_NAME, PREMISE_KIND, list(EVIDENCE_FIELDS), list(VISIBLE_INDICES)],
            "output": ["presented", "established", "supplied-presentation"],
            "output_indices": list(VISIBLE_INDICES),
            "forbidden_source_types": list(_LITERAL_FORBIDDEN_SOURCE_TYPES),
            "forbidden_conclusion_fields": list(_LITERAL_FORBIDDEN_CONCLUSION_FIELDS),
            "assumption_policy_id": _LITERAL_ASSUMPTION_POLICY_ID,
            "permanent_nonclaims": list(PERMANENT_NONCLAIMS),
            "rule_digest": _LITERAL_RULE_DIGEST,
        },
        "projection": [
            PROJECTION_ID,
            RULE_ID,
            PREMISE_NAME,
            _LITERAL_PROJECTION_DIGEST,
        ],
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")
    result = sha256(encoded).hexdigest()
    logger.debug("compute_extension_oracle_digest exit")
    return result


def _charge_exact_tuple(value: object, scanned: int) -> int:
    """Bound one exact tuple before any iteration or nested callback can run."""
    logger.debug("_charge_exact_tuple entry scanned=%d type=%s", scanned, type(value).__name__)
    if type(value) is not tuple:
        reject("registry-v2-nested-type")
    result = scanned + 1 + len(value)
    if result > MAX_STRUCTURAL_NODES:
        reject("structural-node-limit")
    logger.debug("_charge_exact_tuple exit scanned=%d", result)
    return result


def _validate_registry_v2_shallow(value: PromotionRegistry) -> None:
    """Run a callback-free, node-bounded exact-type scan before deep work."""
    logger.debug("_validate_registry_v2_shallow entry")
    if type(value.version) is not str or type(value.registry_digest) is not str:
        reject("registry-v2-nested-type")
    scanned = 0
    for container in (
        value.domains,
        value.rules,
        value.premise_projections,
        value.index_projections,
        value.schema_targets,
    ):
        scanned = _charge_exact_tuple(container, scanned)
    if (
        len(value.domains) != 15
        or len(value.rules) != 18
        or len(value.premise_projections) != 41
        or len(value.index_projections) != 1
        or len(value.schema_targets) != 5
    ):
        reject("registry-v2-cardinality")
    for domain in value.domains:
        if type(domain) is not KindStatusDomain:
            reject("registry-v2-nested-type")
        scanned = _charge_exact_tuple(domain.allowed_statuses, scanned)
        scanned = _charge_exact_tuple(domain.positive_pairs, scanned)
        if (
            type(domain.kind) is not JudgmentKind
            or any(type(item) is not EvidenceStatus for item in domain.allowed_statuses)
            or any(
                type(item) is not StatusProvenancePair
                or type(item.status) is not EvidenceStatus
                or type(item.provenance) is not PositiveProvenance
                for item in domain.positive_pairs
            )
            or type(domain.domain_digest) is not str
        ):
            reject("registry-v2-nested-type")
    for rule in value.rules:
        if type(rule) is not PromotionRule:
            reject("registry-v2-nested-type")
        scanned = _charge_exact_tuple(rule.premise_signatures, scanned)
        scanned = _charge_exact_tuple(rule.output_indices, scanned)
        scanned = _charge_exact_tuple(rule.forbidden_source_types, scanned)
        scanned = _charge_exact_tuple(rule.forbidden_conclusion_fields, scanned)
        scanned = _charge_exact_tuple(rule.permanent_nonclaims, scanned)
        for item in rule.premise_signatures:
            if type(item) is not PremiseSignature:
                reject("registry-v2-nested-type")
            scanned = _charge_exact_tuple(item.required_evidence_fields, scanned)
            scanned = _charge_exact_tuple(item.required_indices, scanned)
        if (
            type(rule.rule_id) is not str
            or type(rule.statement_digest) is not str
            or any(
                type(item.premise_name) is not str
                or type(item.artifact_kind) is not str
                or any(type(field) is not str for field in item.required_evidence_fields)
                or any(type(index) is not str for index in item.required_indices)
                for item in rule.premise_signatures
            )
            or type(rule.output_kind) is not JudgmentKind
            or type(rule.output_status) is not EvidenceStatus
            or type(rule.output_provenance) is not PositiveProvenance
            or any(type(item) is not str for item in rule.output_indices)
            or any(type(item) is not str for item in rule.forbidden_source_types)
            or any(type(item) is not str for item in rule.forbidden_conclusion_fields)
            or type(rule.assumption_policy_id) is not str
            or any(type(item) is not str for item in rule.permanent_nonclaims)
            or type(rule.rule_digest) is not str
        ):
            reject("registry-v2-nested-type")
    for projection in value.premise_projections:
        if (
            type(projection) is not PremiseProjectionRule
            or type(projection.projection_id) is not str
            or type(projection.source_rule_id) is not str
            or type(projection.premise_name) is not str
            or type(projection.projection_digest) is not str
        ):
            reject("registry-v2-nested-type")
    for projection in value.index_projections:
        if type(projection) is not IndexProjectionRule:
            reject("registry-v2-nested-type")
        scanned = _charge_exact_tuple(projection.input_indices, scanned)
        scanned = _charge_exact_tuple(projection.retained_indices, scanned)
        if (
            type(projection.projection_id) is not str
            or type(projection.kind) is not JudgmentKind
            or any(type(item) is not str for item in projection.input_indices)
            or type(projection.hidden_index) is not str
            or any(type(item) is not str for item in projection.retained_indices)
            or type(projection.projection_digest) is not str
        ):
            reject("registry-v2-nested-type")
    for schema in value.schema_targets:
        if type(schema) is not SchemaTarget:
            reject("registry-v2-nested-type")
        scanned = _charge_exact_tuple(schema.exact_fields, scanned)
        scanned = _charge_exact_tuple(schema.forbidden_positive_fields, scanned)
        if (
            type(schema.schema_id) is not str
            or any(type(item) is not str for item in schema.exact_fields)
            or any(type(item) is not str for item in schema.forbidden_positive_fields)
            or type(schema.schema_digest) is not str
        ):
            reject("registry-v2-nested-type")
    logger.debug("_validate_registry_v2_shallow exit scanned=%d", scanned)


def _validate_registry_v2_identifiers(value: PromotionRegistry) -> None:
    """Enforce the 128-byte UTF-8 ceiling on every registry identifier."""
    logger.debug("_validate_registry_v2_identifiers entry")
    exact_identifier(value.version, "registry-v2-identifier-limit")
    for rule in value.rules:
        exact_identifier(rule.rule_id, "registry-v2-identifier-limit")
        for premise in rule.premise_signatures:
            exact_identifier(premise.premise_name, "registry-v2-identifier-limit")
            exact_identifier(premise.artifact_kind, "registry-v2-identifier-limit")
            for item in premise.required_evidence_fields + premise.required_indices:
                exact_identifier(item, "registry-v2-identifier-limit")
        for item in (
            *rule.output_indices,
            *rule.forbidden_source_types,
            *rule.forbidden_conclusion_fields,
            rule.assumption_policy_id,
            *rule.permanent_nonclaims,
        ):
            exact_identifier(item, "registry-v2-identifier-limit")
    for projection in value.premise_projections:
        for item in (projection.projection_id, projection.source_rule_id, projection.premise_name):
            exact_identifier(item, "registry-v2-identifier-limit")
    for projection in value.index_projections:
        for item in (
            projection.projection_id,
            *projection.input_indices,
            projection.hidden_index,
            *projection.retained_indices,
        ):
            exact_identifier(item, "registry-v2-identifier-limit")
    for schema in value.schema_targets:
        for item in (schema.schema_id, *schema.exact_fields, *schema.forbidden_positive_fields):
            exact_identifier(item, "registry-v2-identifier-limit")
    logger.debug("_validate_registry_v2_identifiers exit")


def validate_registry_v2(value: object) -> PromotionRegistry:
    """Reject every nonliteral additive snapshot, including v1-prefix drift."""
    logger.debug("validate_registry_v2 entry")
    if type(value) is not PromotionRegistry:
        reject("registry-v2-not-canonical")
    _validate_registry_v2_shallow(value)
    charge_structure(value)
    _validate_registry_v2_identifiers(value)
    charge_text(value)
    expected = promotion_registry_v2()
    if value != expected:
        reject("registry-v2-not-canonical")
    value = expected
    if value.registry_digest != REGISTRY_DIGEST:
        reject("registry-v2-digest-drift")
    base = promotion_registry()
    if (
        base.registry_digest != _V1_REGISTRY_DIGEST
        or value.domains != base.domains
        or value.rules[:-1] != base.rules
        or value.premise_projections[:-1] != base.premise_projections
        or value.index_projections != base.index_projections
        or value.schema_targets != base.schema_targets
    ):
        reject("registry-v1-prefix-drift")
    rule = value.rules[-1]
    projection = value.premise_projections[-1]
    literal_rule = (
        RULE_ID,
        _LITERAL_STATEMENT_DIGEST,
        ((PREMISE_NAME, PREMISE_KIND, EVIDENCE_FIELDS, VISIBLE_INDICES),),
        JudgmentKind.PRESENTED,
        EvidenceStatus.ESTABLISHED,
        PositiveProvenance.SUPPLIED_PRESENTATION,
        VISIBLE_INDICES,
        _LITERAL_FORBIDDEN_SOURCE_TYPES,
        _LITERAL_FORBIDDEN_CONCLUSION_FIELDS,
        _LITERAL_ASSUMPTION_POLICY_ID,
        PERMANENT_NONCLAIMS,
        _LITERAL_RULE_DIGEST,
    )
    actual_rule = (
        rule.rule_id,
        rule.statement_digest,
        tuple(
            (
                item.premise_name,
                item.artifact_kind,
                item.required_evidence_fields,
                item.required_indices,
            )
            for item in rule.premise_signatures
        ),
        rule.output_kind,
        rule.output_status,
        rule.output_provenance,
        rule.output_indices,
        rule.forbidden_source_types,
        rule.forbidden_conclusion_fields,
        rule.assumption_policy_id,
        rule.permanent_nonclaims,
        rule.rule_digest,
    )
    if actual_rule != literal_rule:
        reject("registry-v2-rule-oracle-mismatch")
    if (
        projection.projection_id,
        projection.source_rule_id,
        projection.premise_name,
        projection.projection_digest,
    ) != (PROJECTION_ID, RULE_ID, PREMISE_NAME, _LITERAL_PROJECTION_DIGEST):
        reject("registry-v2-projection-oracle-mismatch")
    audit_registry_against_literal_oracle(base)
    exact_digest(value.registry_digest, "registry-v2-digest")
    logger.debug("validate_registry_v2 exit")
    return value


def audit_registry_v2_against_literal_oracle(value: object) -> str:
    """Bind the exact generated snapshot to the separately pinned extension oracle."""
    logger.debug("audit_registry_v2_against_literal_oracle entry")
    validate_registry_v2(value)
    actual = compute_extension_oracle_digest()
    if actual != EXTENSION_ORACLE_DIGEST:
        reject("extension-oracle-digest-drift")
    logger.debug("audit_registry_v2_against_literal_oracle exit")
    return EXTENSION_ORACLE_DIGEST
