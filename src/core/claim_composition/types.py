"""Immutable contracts for bounded receipt-family composition."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from ..observer_discovery_v3.service.types import GovernedEvaluationResult


COMPOSITION_SCHEMA = "veyra.claim-composition.v1"
COMPOSITION_BOUNDARY = (
    "bounded semantic aggregation immediately upstream of P2-S; local validity is relative to each "
    "bound source-validator root, exact conjunction preserves every declared contract dimension, and "
    "neither a composition receipt nor its public export establishes a P2 promotion, theorem, "
    "assumption discharge, provenance independence, adaptive validity, or population claim"
)


class ClaimQuantifier(str, Enum):
    """Closed quantifier shapes carried by one claim contract."""

    LOCAL = "LOCAL"
    EXISTENTIAL = "EXISTENTIAL"
    FINITE_CONJUNCTION = "FINITE_CONJUNCTION"
    UNIVERSAL = "UNIVERSAL"


class ClaimClass(str, Enum):
    """Semantic roles that may not be silently reinterpreted by aggregation."""

    STRUCTURAL = "STRUCTURAL"
    EMPIRICAL = "EMPIRICAL"
    EPISTEMIC = "EPISTEMIC"
    OBJECTIVITY = "OBJECTIVITY"


class CorroborationStatus(str, Enum):
    """What the contract says about agreement and provenance independence."""

    SINGLE_LOCAL_RECEIPT = "SINGLE_LOCAL_RECEIPT"
    MULTIPLE_LOCAL_RECEIPTS = "MULTIPLE_LOCAL_RECEIPTS"
    AGREEMENT = "AGREEMENT"
    INDEPENDENT_CORROBORATION = "INDEPENDENT_CORROBORATION"


class AdaptiveCapability(str, Enum):
    """Family/adaptive capability carried by a claim contract."""

    LOCAL_ONLY = "LOCAL_ONLY"
    FAMILY_VALID = "FAMILY_VALID"
    ADAPTIVE_VALID = "ADAPTIVE_VALID"


class PublicWording(str, Enum):
    """Closed public-wording classes; they are not a numeric strength lattice."""

    EXPLORATORY = "EXPLORATORY"
    EVALUATION_COMPLETION = "EVALUATION_COMPLETION"
    BOUNDED_LOCAL = "BOUNDED_LOCAL"
    CONJUNCTIVE_SUMMARY = "CONJUNCTIVE_SUMMARY"
    SIGNIFICANCE = "SIGNIFICANCE"
    FAMILY_INFERENCE = "FAMILY_INFERENCE"
    POPULATION = "POPULATION"


class LocalReceiptValidity(str, Enum):
    """Validity status asserted under the receipt's exact source-validator root."""

    ESTABLISHED = "ESTABLISHED"
    NOT_ESTABLISHED = "NOT_ESTABLISHED"


class SourceEffect(str, Enum):
    """How a source receipt is proposed to affect an aggregate claim."""

    COUNTEREVIDENCE = "COUNTEREVIDENCE"
    DIAGNOSTIC_ONLY = "DIAGNOSTIC_ONLY"
    INCLUDE_LOCAL_CLAIM = "INCLUDE_LOCAL_CLAIM"


class CompositionRule(str, Enum):
    """Closed rule registry for the first composition slice."""

    EXACT_CONJUNCTION = "EXACT_CONJUNCTION"


class CompositionStatus(str, Enum):
    """Fail-closed status for each independent composition predicate."""

    ESTABLISHED = "ESTABLISHED"
    NOT_ESTABLISHED = "NOT_ESTABLISHED"


@dataclass(frozen=True, slots=True)
class ClaimContract:
    """Canonical semantic contract for one local or aggregate claim."""

    schema_version: str
    component_contract_digests: tuple[str, ...]
    claim_roots: tuple[str, ...]
    scope_roots: tuple[str, ...]
    assumption_roots: tuple[str, ...]
    quantifier: ClaimQuantifier
    observer_roots: tuple[str, ...]
    doctrine_roots: tuple[str, ...]
    execution_lineage_roots: tuple[str, ...]
    research_lineage_roots: tuple[str, ...]
    provenance_roots: tuple[str, ...]
    claim_classes: tuple[ClaimClass, ...]
    corroboration: CorroborationStatus
    adaptive_capability: AdaptiveCapability
    public_wording: PublicWording
    contract_digest: str


@dataclass(frozen=True, slots=True)
class LocalClaimReceipt:
    """One local receipt bound to its contract and external validator identity."""

    contract: ClaimContract
    source_receipt_root: str
    source_validator_root: str
    validity: LocalReceiptValidity
    receipt_digest: str


@dataclass(frozen=True, slots=True)
class ClaimCompositionSource:
    """One replayable governed or externally validated local receipt and effect."""

    governed_result: GovernedEvaluationResult | None
    receipt: LocalClaimReceipt
    effect: SourceEffect


@dataclass(frozen=True, slots=True)
class CompositionSourceBinding:
    """Canonical license binding for one input receipt and effect."""

    receipt_digest: str
    effect: SourceEffect


@dataclass(frozen=True, slots=True)
class CompositionLicense:
    """Named rule witness from exact source contracts to one target contract."""

    schema_version: str
    rule: CompositionRule
    sources: tuple[CompositionSourceBinding, ...]
    target_contract_digest: str
    capability_roots: tuple[str, ...]
    license_digest: str


@dataclass(frozen=True, slots=True)
class CompositionAssessment:
    """Four independent statuses required before an aggregate can be exported."""

    local_receipts_valid: CompositionStatus
    aggregate_claim_well_formed: CompositionStatus
    composition_license_established: CompositionStatus
    aggregate_claim_licensed: CompositionStatus
    source_receipt_digests: tuple[str, ...]
    target_contract_digest: str
    license_digest: str
    obstructions: tuple[str, ...]
    assessment_digest: str


@dataclass(frozen=True, slots=True)
class CompositionReceipt:
    """Successful replay-bound composition artifact immediately upstream of P2-S."""

    schema_version: str
    source_receipt_digests: tuple[str, ...]
    target_contract_digest: str
    license_digest: str
    assessment_digest: str
    p2_promotion_established: bool
    receipt_digest: str
    boundary: str = COMPOSITION_BOUNDARY


COMPOSITION_EXPORT_SCHEMA = "veyra.claim-composition.public-export.v1"
COMPOSITION_EXPORT_BOUNDARY = (
    "canonical composition disclosure whose semantic replay requires the exact bound local sources; "
    "it is not a self-contained proof of source validity, a P2 promotion, or claim truth"
)


@dataclass(frozen=True, slots=True)
class CompositionPublicExport:
    """Canonical disclosure of the complete target, license, assessment, and receipt."""

    schema_version: str
    target_contract: ClaimContract
    license: CompositionLicense
    assessment: CompositionAssessment
    receipt: CompositionReceipt
    payload_digest: str
    boundary: str = COMPOSITION_EXPORT_BOUNDARY


class CompositionAuthentication(str, Enum):
    """Authentication profiles for a composition-export envelope."""

    HMAC_SHA256 = "HMAC-SHA256-v1"
    ED25519 = "Ed25519-v1"


COMPOSITION_AUTH_SCHEMA = "veyra.claim-composition.authenticated-export.v1"
COMPOSITION_AUTH_BOUNDARY = (
    "authentication binds exact composition export bytes and roots, not source-validator trust, "
    "P2 promotion, theorem status, or claim truth; signer identity and trust remain external"
)


@dataclass(frozen=True, slots=True)
class AuthenticatedCompositionExport:
    """HMAC-authenticated or Ed25519-signed binding for one public export."""

    schema_version: str
    export_payload_digest: str
    composition_receipt_digest: str
    license_digest: str
    assessment_digest: str
    signer_id: str
    authentication: CompositionAuthentication
    envelope_digest: str
    authentication_tag: str
    boundary: str = COMPOSITION_AUTH_BOUNDARY
