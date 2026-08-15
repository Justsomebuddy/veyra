"""Immutable public DTO for source-backed P2 presentation admission."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from ..claim_composition.types import (
    ClaimContract,
    CompositionAssessment,
    CompositionLicense,
    CompositionReceipt,
)
from ..status_promotion_types import (
    ClaimDescriptor,
    PremiseArtifact,
    PromotionAuditRequest,
    PromotionSchemaAudit,
    SchemaAuditReport,
)


P2_CLAIM_ADMISSION_VERSION = "p2-r17-claim-admission-v2"
JUDGMENT_SCHEMA = "veyra.p2-claim-admission-judgment.v2"
JUDGMENT_BOUNDARY = (
    "source-backed licensed-composition presentation only; schema conformity is meta-only and "
    "does not establish truth, coherence, assumption discharge, independence, ontology, "
    "objectivity, theorem status, lifecycle status, or physical instantiation"
)


class SourceValidationAuthority(str, Enum):
    """How one local source was freshly validated for this v2 judgment."""

    NATIVE_GOVERNED_REPLAY = "NATIVE_GOVERNED_REPLAY"
    EXTERNAL_BINDING_ONLY = "EXTERNAL_BINDING_ONLY"


@dataclass(frozen=True, slots=True)
class SourceValidationBinding:
    """Ordered receipt, validator, and fresh replay-authority commitment."""

    local_receipt_digest: str
    source_validator_root: str
    authority_class: SourceValidationAuthority
    binding_digest: str


@dataclass(frozen=True, slots=True)
class LicensedCompositionPresentation:
    """A replay-backed presentation whose permanent nonclaims remain explicit."""

    schema_version: str
    judgment_id: str
    target_contract: ClaimContract
    source_validator_roots: tuple[str, ...]
    source_validation_bindings: tuple[SourceValidationBinding, ...]
    assumption_roots: tuple[str, ...]
    license: CompositionLicense
    assessment: CompositionAssessment
    receipt: CompositionReceipt
    premise: PremiseArtifact
    descriptor: ClaimDescriptor
    request: PromotionAuditRequest
    promotion_schema_audit: PromotionSchemaAudit
    schema_audit_report: SchemaAuditReport
    registry_digest: str
    extension_oracle_digest: str
    truth_established: bool
    coherence_established: bool
    assumptions_discharged: bool
    independence_established: bool
    ontology_established: bool
    judgment_digest: str
    boundary: str = JUDGMENT_BOUNDARY
