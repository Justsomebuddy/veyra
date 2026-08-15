"""Authoritative source-backed licensed-composition presentation producer."""

from __future__ import annotations

from dataclasses import replace
import logging

from ..claim_composition.types import (
    ClaimCompositionSource,
    ClaimContract,
    CompositionAssessment,
    CompositionLicense,
    CompositionReceipt,
)
from ..proof_core_codec import digest_data
from ..status_promotion_types import (
    ClaimDescriptor,
    PremiseArtifact,
    PromotionAuditRequest,
    PromotionSchemaAudit,
    SchemaAuditReport,
)
from .log_boundary import protected_replay_logs
from .registry import (
    EXTENSION_ORACLE_DIGEST,
    audit_registry_v2_against_literal_oracle,
    promotion_registry_v2,
)
from .replay import (
    _authoritative_replay,
    _build_premise_from_replay,
    build_presentation_descriptor,
    build_presentation_request,
    build_presentation_schema_audit,
)
from .schema_audit import build_presentation_schema_audit_report_v2
from .types import (
    JUDGMENT_BOUNDARY,
    JUDGMENT_SCHEMA,
    LicensedCompositionPresentation,
    SourceValidationAuthority,
    SourceValidationBinding,
)
from .validation import (
    MAX_NONPAYLOAD_TEXT_BYTES,
    MAX_STRUCTURAL_NODES,
    P2ClaimAdmissionError,
    capture_authoritative_inputs,
    capture_exact_core_tree,
)

logger = logging.getLogger(__name__)


def _presentation_data(value: LicensedCompositionPresentation) -> dict[str, object]:
    """Return the fixed digest commitment surface without encoding raw payloads."""
    logger.debug("_presentation_data entry")
    result = {
        "schema_version": value.schema_version,
        "judgment_id": value.judgment_id,
        "target_contract_digest": value.target_contract.contract_digest,
        "source_validator_roots": list(value.source_validator_roots),
        "source_validation_bindings": [
            {
                "local_receipt_digest": item.local_receipt_digest,
                "source_validator_root": item.source_validator_root,
                "authority_class": item.authority_class.value,
                "binding_digest": item.binding_digest,
            }
            for item in value.source_validation_bindings
        ],
        "assumption_roots": list(value.assumption_roots),
        "license_digest": value.license.license_digest,
        "assessment_digest": value.assessment.assessment_digest,
        "receipt_digest": value.receipt.receipt_digest,
        "premise_digest": value.premise.artifact_digest,
        "descriptor_digest": value.descriptor.descriptor_digest,
        "request_digest": value.request.request_digest,
        "promotion_schema_audit_digest": value.promotion_schema_audit.audit_digest,
        "schema_audit_report_digest": value.schema_audit_report.report_digest,
        "registry_digest": value.registry_digest,
        "extension_oracle_digest": value.extension_oracle_digest,
        "truth_established": value.truth_established,
        "coherence_established": value.coherence_established,
        "assumptions_discharged": value.assumptions_discharged,
        "independence_established": value.independence_established,
        "ontology_established": value.ontology_established,
        "boundary": value.boundary,
    }
    logger.debug("_presentation_data exit fields=%d", len(result))
    return result


def build_licensed_composition_presentation(
    sources: tuple[ClaimCompositionSource, ...],
    target: ClaimContract,
    license: CompositionLicense,
    receipt: CompositionReceipt,
    *,
    judgment_id: str,
) -> LicensedCompositionPresentation:
    """Freshly replay every authority-bearing input and issue one presentation."""
    logger.debug("build_licensed_composition_presentation entry")
    sources, target, license, receipt, judgment_id, raw_nodes, raw_text = capture_authoritative_inputs(
        sources, target, license, receipt, judgment_id
    )
    with protected_replay_logs():
        registry = promotion_registry_v2()
        oracle_digest = audit_registry_v2_against_literal_oracle(registry)
        if oracle_digest != EXTENSION_ORACLE_DIGEST:
            raise P2ClaimAdmissionError("registry-v2-oracle-drift")
        replay = _authoritative_replay(sources, target, license, receipt)
        premise = _build_premise_from_replay(replay, target, license, receipt)
        descriptor = build_presentation_descriptor(judgment_id, premise, registry)
        request = build_presentation_request(premise, descriptor, registry)
        promotion_schema_audit = build_presentation_schema_audit(request, registry)
        schema_audit_report = build_presentation_schema_audit_report_v2(registry)
        draft = LicensedCompositionPresentation(
            schema_version=JUDGMENT_SCHEMA,
            judgment_id=judgment_id,
            target_contract=target,
            source_validator_roots=tuple(item.source_validator_root for item in replay.source_validation_bindings),
            source_validation_bindings=replay.source_validation_bindings,
            assumption_roots=target.assumption_roots,
            license=license,
            assessment=replay.assessment,
            receipt=receipt,
            premise=premise,
            descriptor=descriptor,
            request=request,
            promotion_schema_audit=promotion_schema_audit,
            schema_audit_report=schema_audit_report,
            registry_digest=registry.registry_digest,
            extension_oracle_digest=oracle_digest,
            truth_established=False,
            coherence_established=False,
            assumptions_discharged=False,
            independence_established=False,
            ontology_established=False,
            judgment_digest="",
            boundary=JUDGMENT_BOUNDARY,
        )
        result = replace(
            draft,
            judgment_digest=digest_data(_presentation_data(draft), "veyra.p2-claim-admission.public-presentation.v2"),
        )
        result = _preflight_candidate(result, raw_nodes, raw_text)
    logger.info(
        "build_licensed_composition_presentation state=PRESENTED status=ESTABLISHED "
        "provenance=SUPPLIED_PRESENTATION truth=false coherence=false assumptions=false "
        "independence=false ontology=false"
    )
    logger.debug("build_licensed_composition_presentation exit")
    return result


def _preflight_candidate(
    value: object,
    raw_nodes: int,
    raw_text: int,
) -> LicensedCompositionPresentation:
    """Bound a candidate before exact equality or nested field access."""
    logger.debug("_preflight_candidate entry type=%s", type(value).__name__)
    if (
        type(raw_nodes) is not int
        or type(raw_text) is not int
        or raw_nodes < 0
        or raw_text < 0
        or raw_nodes > MAX_STRUCTURAL_NODES
        or raw_text > MAX_NONPAYLOAD_TEXT_BYTES
    ):
        raise P2ClaimAdmissionError("invalid-resource-charge")
    if type(value) is not LicensedCompositionPresentation:
        raise P2ClaimAdmissionError("presentation-type")
    captured, _, _ = capture_exact_core_tree(
        value,
        node_allowance=MAX_STRUCTURAL_NODES - raw_nodes,
        text_allowance=MAX_NONPAYLOAD_TEXT_BYTES - raw_text,
    )
    if type(captured) is not LicensedCompositionPresentation:
        raise P2ClaimAdmissionError("presentation-type")
    value = captured
    if (
        type(value.schema_version) is not str
        or type(value.judgment_id) is not str
        or type(value.target_contract) is not ClaimContract
        or type(value.source_validator_roots) is not tuple
        or type(value.source_validation_bindings) is not tuple
        or not 2 <= len(value.source_validation_bindings) <= 64
        or any(type(item) is not str for item in value.source_validator_roots)
        or any(type(item) is not SourceValidationBinding for item in value.source_validation_bindings)
        or any(
            type(item.local_receipt_digest) is not str
            or type(item.source_validator_root) is not str
            or type(item.authority_class) is not SourceValidationAuthority
            or type(item.binding_digest) is not str
            for item in value.source_validation_bindings
        )
        or len(value.source_validator_roots) != len(value.source_validation_bindings)
        or tuple(item.source_validator_root for item in value.source_validation_bindings)
        != value.source_validator_roots
        or type(value.assumption_roots) is not tuple
        or any(type(item) is not str for item in value.assumption_roots)
        or type(value.license) is not CompositionLicense
        or type(value.assessment) is not CompositionAssessment
        or type(value.receipt) is not CompositionReceipt
        or type(value.premise) is not PremiseArtifact
        or type(value.descriptor) is not ClaimDescriptor
        or type(value.request) is not PromotionAuditRequest
        or type(value.promotion_schema_audit) is not PromotionSchemaAudit
        or type(value.schema_audit_report) is not SchemaAuditReport
        or type(value.registry_digest) is not str
        or type(value.extension_oracle_digest) is not str
        or any(
            type(flag) is not bool
            for flag in (
                value.truth_established,
                value.coherence_established,
                value.assumptions_discharged,
                value.independence_established,
                value.ontology_established,
            )
        )
        or type(value.judgment_digest) is not str
        or type(value.boundary) is not str
    ):
        raise P2ClaimAdmissionError("presentation-source-binding-shape")
    logger.debug("_preflight_candidate exit")
    return captured


def validate_licensed_composition_presentation(
    value: object,
    sources: tuple[ClaimCompositionSource, ...],
    target: ClaimContract,
    license: CompositionLicense,
    receipt: CompositionReceipt,
) -> bool:
    """Reconstruct from raw authority and exact-compare; supplied audits are inert."""
    logger.debug("validate_licensed_composition_presentation entry type=%s", type(value).__name__)
    try:
        if type(value) is not LicensedCompositionPresentation:
            raise P2ClaimAdmissionError("presentation-type")
        sources, target, license, receipt, _, raw_nodes, raw_text = capture_authoritative_inputs(
            sources,
            target,
            license,
            receipt,
            value.judgment_id,
        )
        captured = _preflight_candidate(value, raw_nodes, raw_text)
        with protected_replay_logs():
            expected = build_licensed_composition_presentation(
                sources, target, license, receipt, judgment_id=captured.judgment_id
            )
            valid = captured == expected
    except (AttributeError, P2ClaimAdmissionError, TypeError, UnicodeError, ValueError):
        logger.error("validate_licensed_composition_presentation rejected")
        valid = False
    logger.debug("validate_licensed_composition_presentation exit valid=%s", valid)
    return valid
