"""Strict canonical JSON for licensed composition presentations."""

from __future__ import annotations

import json
import logging
from typing import NoReturn

from ..claim_composition.types import (
    ClaimCompositionSource,
    ClaimContract,
    CompositionAssessment,
    CompositionLicense,
    CompositionReceipt,
)
from ..status_promotion_types import (
    ClaimDescriptor,
    EvidenceField,
    IndexBinding,
    PremiseArtifact,
    PromotionAuditRequest,
    PromotionSchemaAudit,
    SchemaAuditReport,
    SchemaAuditRow,
)
from .log_boundary import protected_replay_logs
from .public import (
    _preflight_candidate,
    build_licensed_composition_presentation,
    validate_licensed_composition_presentation,
)
from .registry import RULE_ID
from .types import LicensedCompositionPresentation, SourceValidationBinding
from .validation import (
    MAX_JSON_BYTES,
    MAX_STRUCTURAL_NODES,
    P2ClaimAdmissionError,
    capture_authoritative_inputs,
    charge_decoded_with_raw,
    exact_identifier,
    reject,
)

logger = logging.getLogger(__name__)

_TOP_LEVEL_FIELDS = (
    "schema_version",
    "judgment_id",
    "target_contract",
    "source_validator_roots",
    "source_validation_bindings",
    "assumption_roots",
    "license",
    "assessment",
    "receipt",
    "premise",
    "descriptor",
    "request",
    "promotion_schema_audit",
    "schema_audit_report",
    "registry_digest",
    "extension_oracle_digest",
    "truth_established",
    "coherence_established",
    "assumptions_discharged",
    "independence_established",
    "ontology_established",
    "judgment_digest",
    "boundary",
)


def _source_validation_binding_data(value: SourceValidationBinding) -> dict[str, object]:
    """Encode one ordered source-validation authority commitment."""
    logger.debug("_source_validation_binding_data entry")
    result = {
        "local_receipt_digest": value.local_receipt_digest,
        "source_validator_root": value.source_validator_root,
        "authority_class": value.authority_class.value,
        "binding_digest": value.binding_digest,
    }
    logger.debug("_source_validation_binding_data exit")
    return result


def _index_data(value: IndexBinding) -> dict[str, object]:
    """Encode one visible index binding."""
    logger.debug("_index_data entry")
    result = {"name": value.name, "value_digest": value.value_digest}
    logger.debug("_index_data exit")
    return result


def _evidence_data(value: EvidenceField) -> dict[str, object]:
    """Encode one evidence binding."""
    logger.debug("_evidence_data entry")
    result = {"name": value.name, "evidence_digest": value.evidence_digest}
    logger.debug("_evidence_data exit")
    return result


def _premise_data(value: PremiseArtifact) -> dict[str, object]:
    """Encode the exact enriched composition premise."""
    logger.debug("_premise_data entry")
    result = {
        "premise_name": value.premise_name,
        "artifact_kind": value.artifact_kind,
        "artifact_digest": value.artifact_digest,
        "indices": [_index_data(item) for item in value.indices],
        "evidence_fields": [_evidence_data(item) for item in value.evidence_fields],
    }
    logger.debug("_premise_data exit")
    return result


def _descriptor_data(value: ClaimDescriptor) -> dict[str, object]:
    """Encode the exact presentation descriptor."""
    logger.debug("_descriptor_data entry")
    result = {
        "claim_id": value.claim_id,
        "kind": value.kind.value,
        "status": value.status.value,
        "provenance": None if value.provenance is None else value.provenance.value,
        "indices": [_index_data(item) for item in value.indices],
        "descriptor_digest": value.descriptor_digest,
    }
    logger.debug("_descriptor_data exit")
    return result


def _contract_data(value: ClaimContract) -> dict[str, object]:
    """Encode every field of the exact target ClaimContract."""
    logger.debug("_contract_data entry")
    result = {
        "schema_version": value.schema_version,
        "component_contract_digests": list(value.component_contract_digests),
        "claim_roots": list(value.claim_roots),
        "scope_roots": list(value.scope_roots),
        "assumption_roots": list(value.assumption_roots),
        "quantifier": value.quantifier.value,
        "observer_roots": list(value.observer_roots),
        "doctrine_roots": list(value.doctrine_roots),
        "execution_lineage_roots": list(value.execution_lineage_roots),
        "research_lineage_roots": list(value.research_lineage_roots),
        "provenance_roots": list(value.provenance_roots),
        "claim_classes": [item.value for item in value.claim_classes],
        "corroboration": value.corroboration.value,
        "adaptive_capability": value.adaptive_capability.value,
        "public_wording": value.public_wording.value,
        "contract_digest": value.contract_digest,
    }
    logger.debug("_contract_data exit")
    return result


def _receipt_data(value: CompositionReceipt) -> dict[str, object]:
    """Encode the exact unchanged v1 composition receipt."""
    logger.debug("_receipt_data entry")
    result = {
        "schema_version": value.schema_version,
        "source_receipt_digests": list(value.source_receipt_digests),
        "target_contract_digest": value.target_contract_digest,
        "license_digest": value.license_digest,
        "assessment_digest": value.assessment_digest,
        "p2_promotion_established": value.p2_promotion_established,
        "receipt_digest": value.receipt_digest,
        "boundary": value.boundary,
    }
    logger.debug("_receipt_data exit")
    return result


def _license_data(value: CompositionLicense) -> dict[str, object]:
    """Encode the full exact composition license."""
    logger.debug("_license_data entry")
    result = {
        "schema_version": value.schema_version,
        "rule": value.rule.value,
        "sources": [{"receipt_digest": item.receipt_digest, "effect": item.effect.value} for item in value.sources],
        "target_contract_digest": value.target_contract_digest,
        "capability_roots": list(value.capability_roots),
        "license_digest": value.license_digest,
    }
    logger.debug("_license_data exit rows=%d", len(value.sources))
    return result


def _assessment_data(value: CompositionAssessment) -> dict[str, object]:
    """Encode all four independent composition-assessment axes."""
    logger.debug("_assessment_data entry")
    result = {
        "local_receipts_valid": value.local_receipts_valid.value,
        "aggregate_claim_well_formed": value.aggregate_claim_well_formed.value,
        "composition_license_established": value.composition_license_established.value,
        "aggregate_claim_licensed": value.aggregate_claim_licensed.value,
        "source_receipt_digests": list(value.source_receipt_digests),
        "target_contract_digest": value.target_contract_digest,
        "license_digest": value.license_digest,
        "obstructions": list(value.obstructions),
        "assessment_digest": value.assessment_digest,
    }
    logger.debug("_assessment_data exit")
    return result


def _request_data(value: PromotionAuditRequest) -> dict[str, object]:
    """Encode the exact one-premise request and empty P2 assumption DAG."""
    logger.debug("_request_data entry")
    result = {
        "version": value.version,
        "rule_id": value.rule_id,
        "premises": [_premise_data(item) for item in value.premises],
        "assumptions": [],
        "conclusion": _descriptor_data(value.conclusion),
        "request_digest": value.request_digest,
    }
    logger.debug("_request_data exit")
    return result


def _audit_data(value: PromotionSchemaAudit) -> dict[str, object]:
    """Encode the exact meta-only schema audit."""
    logger.debug("_audit_data entry")
    result = {
        "registry_digest": value.registry_digest,
        "rule_digest": value.rule_digest,
        "request_digest": value.request_digest,
        "policy_digest": value.policy_digest,
        "conclusion": _descriptor_data(value.conclusion),
        "premise_artifacts": [_premise_data(item) for item in value.premise_artifacts],
        "assumption_closure": list(value.assumption_closure),
        "nonclaims": list(value.nonclaims),
        "decision": value.decision.value,
        "audit_digest": value.audit_digest,
        "ontological_establishment": value.ontological_establishment.value,
        "scope": value.scope,
    }
    logger.debug("_audit_data exit")
    return result


def _schema_audit_row_data(value: SchemaAuditRow) -> dict[str, object]:
    """Encode one fixed-allowlist schema row."""
    logger.debug("_schema_audit_row_data entry")
    result = {
        "schema_id": value.schema_id,
        "exact_match": value.exact_match,
        "forbidden_fields_absent": value.forbidden_fields_absent,
        "row_digest": value.row_digest,
    }
    logger.debug("_schema_audit_row_data exit")
    return result


def _schema_audit_data(value: SchemaAuditReport) -> dict[str, object]:
    """Encode the dedicated registry-v2 fixed-five schema report."""
    logger.debug("_schema_audit_data entry")
    result = {
        "registry_digest": value.registry_digest,
        "policy_digest": value.policy_digest,
        "rows": [_schema_audit_row_data(item) for item in value.rows],
        "scope": value.scope,
        "nonclaims": list(value.nonclaims),
        "report_digest": value.report_digest,
        "decision": value.decision.value,
        "ontological_establishment": value.ontological_establishment.value,
    }
    logger.debug("_schema_audit_data exit rows=%d", len(value.rows))
    return result


def _presentation_json_data(value: LicensedCompositionPresentation) -> dict[str, object]:
    """Encode every public field in a fixed explicit schema."""
    logger.debug("_presentation_json_data entry")
    result = {
        "schema_version": value.schema_version,
        "judgment_id": value.judgment_id,
        "target_contract": _contract_data(value.target_contract),
        "source_validator_roots": list(value.source_validator_roots),
        "source_validation_bindings": [
            _source_validation_binding_data(item) for item in value.source_validation_bindings
        ],
        "assumption_roots": list(value.assumption_roots),
        "license": _license_data(value.license),
        "assessment": _assessment_data(value.assessment),
        "receipt": _receipt_data(value.receipt),
        "premise": _premise_data(value.premise),
        "descriptor": _descriptor_data(value.descriptor),
        "request": _request_data(value.request),
        "promotion_schema_audit": _audit_data(value.promotion_schema_audit),
        "schema_audit_report": _schema_audit_data(value.schema_audit_report),
        "registry_digest": value.registry_digest,
        "extension_oracle_digest": value.extension_oracle_digest,
        "truth_established": value.truth_established,
        "coherence_established": value.coherence_established,
        "assumptions_discharged": value.assumptions_discharged,
        "independence_established": value.independence_established,
        "ontology_established": value.ontology_established,
        "judgment_digest": value.judgment_digest,
        "boundary": value.boundary,
    }
    logger.debug("_presentation_json_data exit fields=%d", len(result))
    return result


def _canonical_json(value: object) -> str:
    """Render canonical ASCII JSON while enforcing the byte cap incrementally."""
    logger.debug("_canonical_json entry")
    encoder = json.JSONEncoder(
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    )
    chunks: list[str] = []
    total = 0
    for chunk in encoder.iterencode(value):
        total += len(chunk)
        if total > MAX_JSON_BYTES:
            reject("presentation-json-byte-limit")
        chunks.append(chunk)
    result = "".join(chunks)
    logger.debug("_canonical_json exit bytes=%d", len(result))
    return result


def licensed_composition_presentation_json(
    value: LicensedCompositionPresentation,
    sources: tuple[ClaimCompositionSource, ...],
    target: ClaimContract,
    license: CompositionLicense,
    receipt: CompositionReceipt,
) -> str:
    """Verify from raw authority, then emit strict canonical JSON under 1 MiB."""
    logger.debug("licensed_composition_presentation_json entry")
    sources, target, license, receipt, _, raw_nodes, raw_text = capture_authoritative_inputs(
        sources, target, license, receipt, RULE_ID
    )
    value = _preflight_candidate(value, raw_nodes, raw_text)
    with protected_replay_logs():
        if not validate_licensed_composition_presentation(value, sources, target, license, receipt):
            reject("presentation-json-not-authoritative")
        result = _canonical_json(_presentation_json_data(value))
    if len(result) > MAX_JSON_BYTES:
        reject("presentation-json-byte-limit")
    logger.debug("licensed_composition_presentation_json exit bytes=%d", len(result))
    return result


def _reject_number(_: str) -> NoReturn:
    """Reject all numeric JSON tokens; the public schema contains none."""
    logger.debug("_reject_number entry")
    reject("presentation-json-number")


def _reject_constant(_: str) -> NoReturn:
    """Reject NaN and infinity spellings."""
    logger.debug("_reject_constant entry")
    reject("presentation-json-constant")


def _pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    """Reject duplicate object keys during decoding."""
    logger.debug("_pairs entry rows=%d", len(pairs))
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            reject("presentation-json-duplicate-key")
        result[key] = value
    logger.debug("_pairs exit rows=%d", len(result))
    return result


def _decode_payload(payload: object, *, node_allowance: int = MAX_STRUCTURAL_NODES) -> tuple[str, object]:
    """Bound bytes, decode exact UTF-8, and parse with hostile scalar hooks."""
    logger.debug("_decode_payload entry type=%s", type(payload).__name__)
    if type(payload) is bytes:
        encoded = payload
        try:
            text = payload.decode("utf-8", errors="strict")
        except UnicodeError as exc:
            logger.error("_decode_payload rejected type=%s", type(exc).__name__)
            raise P2ClaimAdmissionError("presentation-json-utf8") from exc
    elif type(payload) is str:
        if len(payload) > MAX_JSON_BYTES:
            reject("presentation-json-byte-limit")
        try:
            encoded = payload.encode("utf-8", errors="strict")
        except UnicodeError as exc:
            logger.error("_decode_payload rejected type=%s", type(exc).__name__)
            raise P2ClaimAdmissionError("presentation-json-utf8") from exc
        text = payload
    else:
        reject("presentation-json-type")
    if len(encoded) > MAX_JSON_BYTES:
        reject("presentation-json-byte-limit")
    _preflight_json_shape(text, node_allowance=node_allowance)
    try:
        decoded = json.loads(
            text,
            object_pairs_hook=_pairs,
            parse_int=_reject_number,
            parse_float=_reject_number,
            parse_constant=_reject_constant,
        )
    except P2ClaimAdmissionError:
        raise
    except (json.JSONDecodeError, RecursionError, UnicodeError, ValueError) as exc:
        logger.error("_decode_payload rejected type=%s", type(exc).__name__)
        raise P2ClaimAdmissionError("presentation-json-syntax") from exc
    logger.debug("_decode_payload exit bytes=%d", len(encoded))
    return text, decoded


def _preflight_json_shape(text: str, *, node_allowance: int) -> None:
    """Bound literal JSON nodes/depth before allocating the decoded tree."""
    logger.debug("_preflight_json_shape entry bytes=%d", len(text))
    nodes = 0
    depth = 0
    in_string = False
    escaped = False
    index = 0
    while index < len(text):
        char = text[index]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            index += 1
            continue
        if char == '"':
            in_string = True
            nodes += 1
        elif char in "[{":
            nodes += 1
            depth += 1
            if depth > 128:
                reject("structural-depth-limit")
        elif char in "]}":
            depth -= 1
        elif char in "-0123456789tfn":
            nodes += 1
            while index + 1 < len(text) and text[index + 1] not in " \t\r\n,]}":
                index += 1
        if nodes > node_allowance:
            reject("structural-node-limit")
        index += 1
    logger.debug("_preflight_json_shape exit nodes=%d depth=%d", nodes, depth)


def licensed_composition_presentation_from_json(
    payload: object,
    sources: tuple[ClaimCompositionSource, ...],
    target: ClaimContract,
    license: CompositionLicense,
    receipt: CompositionReceipt,
) -> LicensedCompositionPresentation:
    """Decode only by rebuilding from the same raw authoritative inputs."""
    logger.debug("licensed_composition_presentation_from_json entry")
    sources, target, license, receipt, _, raw_nodes, raw_text = capture_authoritative_inputs(
        sources, target, license, receipt, RULE_ID
    )
    text, decoded = _decode_payload(payload, node_allowance=MAX_STRUCTURAL_NODES - raw_nodes)
    charge_decoded_with_raw(decoded, raw_nodes, raw_text)
    if type(decoded) is not dict or tuple(decoded) != tuple(sorted(_TOP_LEVEL_FIELDS)):
        reject("presentation-json-fields")
    judgment_id = exact_identifier(decoded.get("judgment_id"), "judgment-id")
    if text != _canonical_json(decoded):
        reject("presentation-json-noncanonical")
    with protected_replay_logs():
        expected = build_licensed_composition_presentation(sources, target, license, receipt, judgment_id=judgment_id)
        if decoded != _presentation_json_data(expected):
            reject("presentation-json-authority-mismatch")
    logger.debug("licensed_composition_presentation_from_json exit")
    return expected
