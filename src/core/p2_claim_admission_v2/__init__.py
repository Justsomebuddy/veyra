"""Additive non-root P2 v2 licensed-composition registry API."""

from .errors import P2ClaimAdmissionError
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
from .resource_validation import (
    MAX_DEPTH,
    MAX_IDENTIFIER_BYTES,
    MAX_NONPAYLOAD_TEXT_BYTES,
    MAX_STRUCTURAL_NODES,
)

__all__ = (
    "EVIDENCE_FIELDS",
    "EXTENSION_ORACLE_DIGEST",
    "MAX_DEPTH",
    "MAX_IDENTIFIER_BYTES",
    "MAX_NONPAYLOAD_TEXT_BYTES",
    "MAX_STRUCTURAL_NODES",
    "P2ClaimAdmissionError",
    "PERMANENT_NONCLAIMS",
    "PREMISE_KIND",
    "PREMISE_NAME",
    "PROJECTION_ID",
    "REGISTRY_DIGEST",
    "REGISTRY_VERSION",
    "RULE_ID",
    "VISIBLE_INDICES",
    "audit_registry_v2_against_literal_oracle",
    "promotion_registry_v2",
    "validate_registry_v2",
)
