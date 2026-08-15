"""Exact composition replay into the one named P2 v2 presentation rule."""

from __future__ import annotations

from dataclasses import dataclass
import logging

from ..claim_composition import (
    assess_claim_composition,
    canonical_composition_sources,
    validate_composition_receipt,
)
from ..claim_composition.types import (
    ClaimCompositionSource,
    ClaimContract,
    CompositionAssessment,
    CompositionLicense,
    CompositionReceipt,
)
from ..observer_discovery_v3.service.types import GovernedEvaluationResult
from ..proof_core_codec import digest_data
from ..status_promotion_digest import digest, text_rows
from ..status_promotion_request import claim_descriptor, promotion_audit_request, validate_request_deep
from ..status_promotion_types import (
    ClaimDescriptor,
    EvidenceStatus,
    MetaAuditDecision,
    MetaOntologicalStatus,
    PositiveProvenance,
    PremiseArtifact,
    PromotionAuditRequest,
    PromotionRegistry,
    PromotionSchemaAudit,
)
from ..status_promotion_validation import evidence_field, index_binding, premise_artifact, promotion_policy
from .log_boundary import protected_replay_logs
from .registry import (
    EVIDENCE_FIELDS,
    PERMANENT_NONCLAIMS,
    PREMISE_KIND,
    PREMISE_NAME,
    RULE_ID,
    VISIBLE_INDICES,
    audit_registry_v2_against_literal_oracle,
    promotion_registry_v2,
    validate_registry_v2,
)
from .types import SourceValidationAuthority, SourceValidationBinding
from .validation import (
    P2ClaimAdmissionError,
    capture_authoritative_inputs,
    capture_exact_core_tree,
    reject,
)

logger = logging.getLogger(__name__)

_SET_DOMAINS = {
    "claims": "veyra.p2-claim-admission.claim-set.v2",
    "scope": "veyra.p2-claim-admission.scope-set.v2",
    "assumptions": "veyra.p2-claim-admission.assumption-set.v2",
    "doctrine": "veyra.p2-claim-admission.doctrine-set.v2",
    "source-validators": "veyra.p2-claim-admission.source-validator-family.v2",
    "source-family": "veyra.p2-claim-admission.source-family.v2",
}
_AUTHORITY_BINDING_DOMAIN = "veyra.p2-claim-admission.source-validator-binding.v2"
PROMOTION_SCHEMA_AUDIT_SCOPE_V2 = "p2-claim-admission-v2-named-rule-schema-meta-only"


@dataclass(frozen=True, slots=True)
class _AuthoritativeReplay:
    """One immutable result of replay used throughout a public build."""

    sources: tuple[ClaimCompositionSource, ...]
    assessment: CompositionAssessment
    source_validation_bindings: tuple[SourceValidationBinding, ...]


def _root_family_digest(name: str, roots: tuple[str, ...]) -> str:
    """Commit one exact ordered opaque-root family."""
    logger.debug("_root_family_digest entry family=%s rows=%d", name, len(roots))
    domain = _SET_DOMAINS.get(name)
    if domain is None:
        reject("unknown-root-family")
    result = digest_data({"roots": list(roots)}, domain)
    logger.debug("_root_family_digest exit family=%s", name)
    return result


def _source_validation_bindings(
    sources: tuple[ClaimCompositionSource, ...],
) -> tuple[SourceValidationBinding, ...]:
    """Commit ordered receipt/validator/fresh-authority triples."""
    logger.debug("_source_validation_bindings entry rows=%d", len(sources))
    rows: list[SourceValidationBinding] = []
    for source in sources:
        authority = (
            SourceValidationAuthority.NATIVE_GOVERNED_REPLAY
            if type(source.governed_result) is GovernedEvaluationResult
            else SourceValidationAuthority.EXTERNAL_BINDING_ONLY
        )
        data = {
            "local_receipt_digest": source.receipt.receipt_digest,
            "source_validator_root": source.receipt.source_validator_root,
            "authority_class": authority.value,
        }
        rows.append(
            SourceValidationBinding(
                source.receipt.receipt_digest,
                source.receipt.source_validator_root,
                authority,
                digest_data(data, _AUTHORITY_BINDING_DOMAIN),
            )
        )
    result = tuple(rows)
    logger.debug("_source_validation_bindings exit rows=%d", len(result))
    return result


def _source_receipt_roots(sources: tuple[ClaimCompositionSource, ...]) -> tuple[str, ...]:
    """Retain local-receipt identities in exact canonical source order."""
    logger.debug("_source_receipt_roots entry rows=%d", len(sources))
    result = tuple(source.receipt.receipt_digest for source in sources)
    logger.debug("_source_receipt_roots exit rows=%d", len(result))
    return result


def _nonpromotion_digest(receipt: CompositionReceipt) -> str:
    """Commit the unchanged composition-v1 false promotion boundary."""
    logger.debug("_nonpromotion_digest entry")
    result = digest_data(
        {
            "p2_promotion_established": receipt.p2_promotion_established,
            "boundary": receipt.boundary,
        },
        "veyra.p2-claim-admission.nonpromotion.v2",
    )
    logger.debug("_nonpromotion_digest exit")
    return result


def _premise_bindings(
    replay: _AuthoritativeReplay,
    target: ClaimContract,
    license: CompositionLicense,
    receipt: CompositionReceipt,
) -> tuple[tuple, tuple]:
    """Build the exact visible indices and evidence rows in frozen order."""
    logger.debug("_premise_bindings entry rows=%d", len(replay.sources))
    claims = _root_family_digest("claims", target.claim_roots)
    scope = _root_family_digest("scope", target.scope_roots)
    assumptions = _root_family_digest("assumptions", target.assumption_roots)
    doctrine = _root_family_digest("doctrine", target.doctrine_roots)
    validators = _root_family_digest(
        "source-validators",
        tuple(item.binding_digest for item in replay.source_validation_bindings),
    )
    source_family = _root_family_digest("source-family", _source_receipt_roots(replay.sources))
    indices = tuple(
        index_binding(name, value)
        for name, value in zip(
            VISIBLE_INDICES,
            (
                target.contract_digest,
                claims,
                scope,
                assumptions,
                doctrine,
                validators,
                receipt.receipt_digest,
            ),
            strict=True,
        )
    )
    evidence = tuple(
        evidence_field(name, value)
        for name, value in zip(
            EVIDENCE_FIELDS,
            (
                target.contract_digest,
                claims,
                scope,
                assumptions,
                doctrine,
                validators,
                source_family,
                license.license_digest,
                receipt.assessment_digest,
                _nonpromotion_digest(receipt),
            ),
            strict=True,
        )
    )
    logger.debug("_premise_bindings exit indices=%d evidence=%d", len(indices), len(evidence))
    return indices, evidence


def _authoritative_replay(
    sources: tuple[ClaimCompositionSource, ...],
    target: ClaimContract,
    license: CompositionLicense,
    receipt: CompositionReceipt,
) -> _AuthoritativeReplay:
    """Freshly replay the full v1 source/target/license/assessment/receipt chain."""
    logger.debug("_authoritative_replay entry rows=%d", len(sources))
    try:
        checked = canonical_composition_sources(sources)
        if checked != sources:
            reject("authoritative-source-order")
        if not validate_composition_receipt(receipt, checked, target, license):
            reject("authoritative-composition-replay")
        assessment = assess_claim_composition(checked, target, license)
        if assessment.assessment_digest != receipt.assessment_digest:
            reject("authoritative-assessment-replay")
        bindings = _source_validation_bindings(checked)
    except P2ClaimAdmissionError:
        raise
    except (AttributeError, TypeError, UnicodeError, ValueError) as exc:
        logger.error("_authoritative_replay rejected type=%s", type(exc).__name__)
        raise P2ClaimAdmissionError("authoritative-composition-replay") from exc
    logger.info("_authoritative_replay state=licensed p2_v1_promotion=false")
    logger.debug("_authoritative_replay exit")
    return _AuthoritativeReplay(checked, assessment, bindings)


def _build_premise_from_replay(
    replay: _AuthoritativeReplay,
    target: ClaimContract,
    license: CompositionLicense,
    receipt: CompositionReceipt,
) -> PremiseArtifact:
    """Build one premise from the already replayed immutable snapshot."""
    logger.debug("_build_premise_from_replay entry rows=%d", len(replay.sources))
    indices, evidence = _premise_bindings(replay, target, license, receipt)
    artifact_digest = digest_data(
        {
            "receipt_digest": receipt.receipt_digest,
            "indices": [[item.name, item.value_digest] for item in indices],
            "evidence": [[item.name, item.evidence_digest] for item in evidence],
        },
        "veyra.p2-claim-admission.premise.v2",
    )
    result = premise_artifact(PREMISE_NAME, PREMISE_KIND, artifact_digest, indices, evidence)
    logger.debug("_build_premise_from_replay exit")
    return result


def build_composition_presentation_premise(
    sources: tuple[ClaimCompositionSource, ...],
    target: ClaimContract,
    license: CompositionLicense,
    receipt: CompositionReceipt,
) -> PremiseArtifact:
    """Issue the sole v2 premise only after fresh authoritative composition replay."""
    logger.debug("build_composition_presentation_premise entry")
    sources, target, license, receipt, _, _, _ = capture_authoritative_inputs(
        sources, target, license, receipt, RULE_ID
    )
    with protected_replay_logs():
        replay = _authoritative_replay(sources, target, license, receipt)
        result = _build_premise_from_replay(replay, target, license, receipt)
    logger.info("build_composition_presentation_premise state=source-backed-presentation")
    logger.debug("build_composition_presentation_premise exit")
    return result


def validate_composition_presentation_premise(
    value: object,
    sources: tuple[ClaimCompositionSource, ...],
    target: ClaimContract,
    license: CompositionLicense,
    receipt: CompositionReceipt,
) -> bool:
    """Freshly reconstruct and exact-compare one v2 composition premise."""
    logger.debug("validate_composition_presentation_premise entry type=%s", type(value).__name__)
    try:
        if type(value) is not PremiseArtifact:
            reject("presentation-premise-type")
        captured, _, _ = capture_exact_core_tree(value)
        valid = captured == build_composition_presentation_premise(sources, target, license, receipt)
    except (AttributeError, P2ClaimAdmissionError, TypeError, UnicodeError, ValueError):
        logger.error("validate_composition_presentation_premise rejected")
        valid = False
    logger.debug("validate_composition_presentation_premise exit valid=%s", valid)
    return valid


def build_presentation_descriptor(
    judgment_id: str,
    premise: PremiseArtifact,
    registry: PromotionRegistry,
) -> ClaimDescriptor:
    """Build only PRESENTED/ESTABLISHED/SUPPLIED_PRESENTATION with exact indices."""
    logger.debug("build_presentation_descriptor entry")
    premise, _, _ = capture_exact_core_tree(premise)
    if type(premise) is not PremiseArtifact:
        reject("presentation-premise-type")
    validate_registry_v2(registry)
    registry = promotion_registry_v2()
    result = claim_descriptor(
        judgment_id,
        registry.rules[-1].output_kind,
        registry.rules[-1].output_status,
        registry.rules[-1].output_provenance,
        premise.indices,
        registry,
    )
    logger.debug("build_presentation_descriptor exit")
    return result


def build_presentation_request(
    premise: PremiseArtifact,
    descriptor: ClaimDescriptor,
    registry: PromotionRegistry,
) -> PromotionAuditRequest:
    """Construct the exact one-premise, zero-P2-assumption request."""
    logger.debug("build_presentation_request entry")
    premise, _, _ = capture_exact_core_tree(premise)
    descriptor, _, _ = capture_exact_core_tree(descriptor)
    if type(premise) is not PremiseArtifact or type(descriptor) is not ClaimDescriptor:
        reject("presentation-request-input-type")
    validate_registry_v2(registry)
    registry = promotion_registry_v2()
    result = promotion_audit_request(RULE_ID, (premise,), (), descriptor, registry)
    logger.debug("build_presentation_request exit")
    return result


def build_presentation_schema_audit(
    request: PromotionAuditRequest,
    registry: PromotionRegistry,
) -> PromotionSchemaAudit:
    """Audit named-rule syntax only; the result is never conclusion authority."""
    logger.debug("build_presentation_schema_audit entry")
    validate_registry_v2(registry)
    registry = promotion_registry_v2()
    audit_registry_v2_against_literal_oracle(registry)
    if (
        type(request) is not PromotionAuditRequest
        or type(request.premises) is not tuple
        or len(request.premises) != 1
        or type(request.assumptions) is not tuple
        or request.assumptions != ()
    ):
        reject("named-rule-request-shape")
    request, _, _ = capture_exact_core_tree(request)
    if type(request) is not PromotionAuditRequest:
        reject("named-rule-request-shape")
    try:
        validate_request_deep(request, registry)
    except (AttributeError, TypeError, UnicodeError, ValueError) as exc:
        logger.error("build_presentation_schema_audit rejected type=%s", type(exc).__name__)
        raise P2ClaimAdmissionError("named-rule-request-replay") from exc
    rule = registry.rules[-1]
    if (
        request.rule_id != RULE_ID
        or request.premises[0].premise_name != PREMISE_NAME
        or request.premises[0].artifact_kind != PREMISE_KIND
        or tuple(item.name for item in request.premises[0].indices) != VISIBLE_INDICES
        or tuple(item.name for item in request.premises[0].evidence_fields) != EVIDENCE_FIELDS
        or request.assumptions != ()
        or request.conclusion.kind is not rule.output_kind
        or request.conclusion.status is not rule.output_status
        or request.conclusion.provenance is not rule.output_provenance
        or tuple(item.name for item in request.conclusion.indices) != VISIBLE_INDICES
    ):
        reject("named-rule-schema-mismatch")
    policy = promotion_policy()
    value = digest(
        "veyra.p2-claim-admission.promotion-schema-audit.v2",
        (
            ("registry", registry.registry_digest.encode()),
            ("rule", rule.rule_digest.encode()),
            ("request", request.request_digest.encode()),
            ("policy", policy.policy_digest.encode()),
            ("conclusion", request.conclusion.descriptor_digest.encode()),
            *text_rows("premise", (request.premises[0].artifact_digest,)),
            *text_rows("assumption", ()),
            *text_rows("nonclaim", rule.permanent_nonclaims),
            ("scope", PROMOTION_SCHEMA_AUDIT_SCOPE_V2.encode()),
            ("decision", MetaAuditDecision.SCHEMA_CONFORMANT.value.encode()),
            ("ontology", MetaOntologicalStatus.NOT_CLAIMED.value.encode()),
        ),
    )
    result = PromotionSchemaAudit(
        registry_digest=registry.registry_digest,
        rule_digest=rule.rule_digest,
        request_digest=request.request_digest,
        policy_digest=policy.policy_digest,
        conclusion=request.conclusion,
        premise_artifacts=request.premises,
        assumption_closure=(),
        nonclaims=rule.permanent_nonclaims,
        decision=MetaAuditDecision.SCHEMA_CONFORMANT,
        audit_digest=value,
        ontological_establishment=MetaOntologicalStatus.NOT_CLAIMED,
        scope=PROMOTION_SCHEMA_AUDIT_SCOPE_V2,
    )
    logger.info("build_presentation_schema_audit state=SCHEMA_CONFORMANT ontology=NOT_CLAIMED")
    logger.debug("build_presentation_schema_audit exit")
    return result


def validate_presentation_schema_audit(
    value: object,
    request: PromotionAuditRequest,
    registry: PromotionRegistry,
) -> bool:
    """Rebuild and exact-compare the named-rule v2 meta-only audit."""
    logger.debug("validate_presentation_schema_audit entry type=%s", type(value).__name__)
    try:
        if type(value) is not PromotionSchemaAudit:
            reject("promotion-schema-audit-type")
        captured, _, _ = capture_exact_core_tree(value)
        valid = captured == build_presentation_schema_audit(request, registry)
    except (AttributeError, P2ClaimAdmissionError, TypeError, UnicodeError, ValueError):
        logger.error("validate_presentation_schema_audit rejected")
        valid = False
    logger.debug("validate_presentation_schema_audit exit valid=%s", valid)
    return valid
