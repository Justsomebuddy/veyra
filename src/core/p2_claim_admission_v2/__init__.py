"""Additive non-root P2 v2 licensed-composition presentation API."""

from .codec import (
    licensed_composition_presentation_from_json,
    licensed_composition_presentation_json,
)
from .public import (
    build_licensed_composition_presentation,
    validate_licensed_composition_presentation,
)
from .registry import (
    EVIDENCE_FIELDS,
    EXTENSION_ORACLE_DIGEST,
    PERMANENT_NONCLAIMS,
    PREMISE_KIND,
    PREMISE_NAME,
    PROJECTION_ID,
    REGISTRY_DIGEST,
    REGISTRY_VERSION,
    RULE_ID,
    VISIBLE_INDICES,
    audit_registry_v2_against_literal_oracle,
    promotion_registry_v2,
    validate_registry_v2,
)
from .replay import (
    build_composition_presentation_premise,
    build_presentation_schema_audit,
    validate_composition_presentation_premise,
    validate_presentation_schema_audit,
)
from .schema_audit import (
    SCHEMA_AUDIT_NONCLAIMS_V2,
    SCHEMA_AUDIT_SCOPE_V2,
    build_presentation_schema_audit_report_v2,
    validate_presentation_schema_audit_report_v2,
)
from .types import (
    JUDGMENT_BOUNDARY,
    JUDGMENT_SCHEMA,
    P2_CLAIM_ADMISSION_VERSION,
    LicensedCompositionPresentation,
    SourceValidationAuthority,
    SourceValidationBinding,
)
from .validation import (
    MAX_DEPTH,
    MAX_IDENTIFIER_BYTES,
    MAX_JSON_BYTES,
    MAX_NONPAYLOAD_TEXT_BYTES,
    MAX_STRUCTURAL_NODES,
    P2ClaimAdmissionError,
)

__all__ = (
    "EVIDENCE_FIELDS",
    "EXTENSION_ORACLE_DIGEST",
    "JUDGMENT_BOUNDARY",
    "JUDGMENT_SCHEMA",
    "LicensedCompositionPresentation",
    "MAX_DEPTH",
    "MAX_IDENTIFIER_BYTES",
    "MAX_JSON_BYTES",
    "MAX_NONPAYLOAD_TEXT_BYTES",
    "MAX_STRUCTURAL_NODES",
    "P2ClaimAdmissionError",
    "P2_CLAIM_ADMISSION_VERSION",
    "PERMANENT_NONCLAIMS",
    "PREMISE_KIND",
    "PREMISE_NAME",
    "PROJECTION_ID",
    "REGISTRY_DIGEST",
    "REGISTRY_VERSION",
    "RULE_ID",
    "SCHEMA_AUDIT_NONCLAIMS_V2",
    "SCHEMA_AUDIT_SCOPE_V2",
    "SourceValidationAuthority",
    "SourceValidationBinding",
    "VISIBLE_INDICES",
    "audit_registry_v2_against_literal_oracle",
    "build_composition_presentation_premise",
    "build_licensed_composition_presentation",
    "build_presentation_schema_audit",
    "build_presentation_schema_audit_report_v2",
    "licensed_composition_presentation_from_json",
    "licensed_composition_presentation_json",
    "promotion_registry_v2",
    "validate_composition_presentation_premise",
    "validate_licensed_composition_presentation",
    "validate_presentation_schema_audit",
    "validate_presentation_schema_audit_report_v2",
    "validate_registry_v2",
)
