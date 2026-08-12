"""Canonical complete disclosure and source-backed replay for composition artifacts."""

from __future__ import annotations

import json
import logging
from typing import NoReturn

from ..proof_core_codec import canonical_json, digest_data, exact_keys, load_canonical
from .protocol import (
    ClaimCompositionError,
    assess_claim_composition,
    build_claim_contract,
    validate_claim_contract,
    validate_composition_assessment,
    validate_composition_license_shape,
    validate_composition_receipt,
)
from .types import (
    COMPOSITION_BOUNDARY,
    COMPOSITION_EXPORT_BOUNDARY,
    COMPOSITION_EXPORT_SCHEMA,
    COMPOSITION_SCHEMA,
    AdaptiveCapability,
    ClaimClass,
    ClaimCompositionSource,
    ClaimContract,
    ClaimQuantifier,
    CompositionAssessment,
    CompositionLicense,
    CompositionPublicExport,
    CompositionReceipt,
    CompositionRule,
    CompositionSourceBinding,
    CompositionStatus,
    CorroborationStatus,
    PublicWording,
    SourceEffect,
)

logger = logging.getLogger(__name__)

MAX_COMPOSITION_EXPORT_BYTES = 1_000_000
_EXPORT_DOMAIN = "veyra.claim-composition.public-export-payload.v1"


def build_composition_public_export(
    receipt: CompositionReceipt,
    sources: tuple[ClaimCompositionSource, ...],
    target: ClaimContract,
    license: CompositionLicense,
) -> CompositionPublicExport:
    """Build a complete export only after fresh source-backed semantic replay."""
    logger.debug("build_composition_public_export entry")
    if not validate_composition_receipt(receipt, sources, target, license):
        _reject("public-export-unlicensed")
    assessment = assess_claim_composition(sources, target, license)
    draft = CompositionPublicExport(
        COMPOSITION_EXPORT_SCHEMA,
        target,
        license,
        assessment,
        receipt,
        "",
        COMPOSITION_EXPORT_BOUNDARY,
    )
    result = CompositionPublicExport(
        draft.schema_version,
        draft.target_contract,
        draft.license,
        draft.assessment,
        draft.receipt,
        digest_data(_export_payload_data(draft), _EXPORT_DOMAIN),
        draft.boundary,
    )
    logger.info("build_composition_public_export state=REPLAYED p2_promotion=False")
    logger.debug("build_composition_public_export exit digest=%s", result.payload_digest[:12])
    return result


def validate_composition_public_export(
    value: object,
    sources: tuple[ClaimCompositionSource, ...],
) -> bool:
    """Validate the complete export by replaying its exact original local sources."""
    logger.debug("validate_composition_public_export entry type=%s", type(value).__name__)
    try:
        valid = (
            type(value) is CompositionPublicExport
            and value.schema_version == COMPOSITION_EXPORT_SCHEMA
            and value.boundary == COMPOSITION_EXPORT_BOUNDARY
            and validate_claim_contract(value.target_contract)
            and validate_composition_license_shape(value.license)
            and validate_composition_assessment(
                value.assessment,
                sources,
                value.target_contract,
                value.license,
            )
            and validate_composition_receipt(
                value.receipt,
                sources,
                value.target_contract,
                value.license,
            )
            and value.payload_digest == digest_data(_export_payload_data(value), _EXPORT_DOMAIN)
        )
    except (AttributeError, ClaimCompositionError, TypeError, UnicodeError, ValueError):
        logger.error("validate_composition_public_export rejected")
        valid = False
    logger.debug("validate_composition_public_export exit valid=%s", valid)
    return valid


def composition_public_export_json(
    value: CompositionPublicExport,
    sources: tuple[ClaimCompositionSource, ...],
) -> str:
    """Serialize a complete export only after fresh source-backed validation."""
    logger.debug("composition_public_export_json entry")
    if not validate_composition_public_export(value, sources):
        _reject("public-export-invalid")
    result = canonical_json(_export_data(value))
    if len(result.encode("utf-8")) > MAX_COMPOSITION_EXPORT_BYTES:
        _reject("public-export-size")
    logger.debug("composition_public_export_json exit bytes=%d", len(result.encode("utf-8")))
    return result


def composition_public_export_from_json(
    text: str,
    sources: tuple[ClaimCompositionSource, ...],
) -> CompositionPublicExport:
    """Decode canonical JSON and accept it only after replay against original sources."""
    logger.debug("composition_public_export_from_json entry type=%s", type(text).__name__)
    if type(text) is not str or len(text) > MAX_COMPOSITION_EXPORT_BYTES:
        _reject("public-export-size")
    try:
        encoded = text.encode("utf-8")
    except UnicodeError as exc:
        raise ClaimCompositionError("public-export-format") from exc
    if len(encoded) > MAX_COMPOSITION_EXPORT_BYTES:
        _reject("public-export-size")
    try:
        data = load_canonical(text)
        result = _export_from_data(data)
    except (json.JSONDecodeError, KeyError, RecursionError, TypeError, UnicodeError, ValueError) as exc:
        logger.error("composition_public_export_from_json rejected type=%s", type(exc).__name__)
        raise ClaimCompositionError("public-export-format") from exc
    if not validate_composition_public_export(result, sources):
        _reject("public-export-replay")
    logger.debug("composition_public_export_from_json exit")
    return result


def composition_disclosure_json(
    receipt: CompositionReceipt,
    sources: tuple[ClaimCompositionSource, ...],
    target: ClaimContract,
    license: CompositionLicense,
) -> str:
    """Build and serialize the complete licensed, permanently nonpromoting export."""
    logger.debug("composition_disclosure_json entry")
    export = build_composition_public_export(receipt, sources, target, license)
    result = composition_public_export_json(export, sources)
    logger.info("composition_disclosure_json state=EXPORTED p2_promotion=False")
    logger.debug("composition_disclosure_json exit bytes=%d", len(result.encode("utf-8")))
    return result


def _export_from_data(data: object) -> CompositionPublicExport:
    logger.debug("_export_from_data entry")
    row = exact_keys(
        data,
        {
            "schema_version",
            "target_contract",
            "license",
            "assessment",
            "receipt",
            "payload_digest",
            "boundary",
        },
    )
    result = CompositionPublicExport(
        row["schema_version"],
        _contract_from_data(row["target_contract"]),
        _license_from_data(row["license"]),
        _assessment_from_data(row["assessment"]),
        _receipt_from_data(row["receipt"]),
        row["payload_digest"],
        row["boundary"],
    )
    logger.debug("_export_from_data exit")
    return result


def _contract_from_data(data: object) -> ClaimContract:
    logger.debug("_contract_from_data entry")
    row = exact_keys(
        data,
        {
            "schema_version",
            "component_contract_digests",
            "claim_roots",
            "scope_roots",
            "assumption_roots",
            "quantifier",
            "observer_roots",
            "doctrine_roots",
            "execution_lineage_roots",
            "research_lineage_roots",
            "provenance_roots",
            "claim_classes",
            "corroboration",
            "adaptive_capability",
            "public_wording",
            "contract_digest",
        },
    )
    if row["schema_version"] != COMPOSITION_SCHEMA:
        _reject("public-export-contract-schema")
    result = build_claim_contract(
        _string_tuple(row["claim_roots"]),
        _string_tuple(row["scope_roots"]),
        _string_tuple(row["assumption_roots"]),
        ClaimQuantifier(row["quantifier"]),
        _string_tuple(row["observer_roots"]),
        _string_tuple(row["doctrine_roots"]),
        _string_tuple(row["execution_lineage_roots"]),
        _string_tuple(row["research_lineage_roots"]),
        _string_tuple(row["provenance_roots"]),
        tuple(ClaimClass(item) for item in _string_list(row["claim_classes"])),
        CorroborationStatus(row["corroboration"]),
        AdaptiveCapability(row["adaptive_capability"]),
        PublicWording(row["public_wording"]),
        component_contract_digests=_string_tuple(row["component_contract_digests"]),
    )
    if result.contract_digest != row["contract_digest"]:
        _reject("public-export-contract-digest")
    logger.debug("_contract_from_data exit")
    return result


def _license_from_data(data: object) -> CompositionLicense:
    logger.debug("_license_from_data entry")
    row = exact_keys(
        data,
        {
            "schema_version",
            "rule",
            "sources",
            "target_contract_digest",
            "capability_roots",
            "license_digest",
        },
    )
    if type(row["sources"]) is not list:
        _reject("public-export-license-sources")
    sources = tuple(
        CompositionSourceBinding(
            exact_keys(item, {"receipt_digest", "effect"})["receipt_digest"],
            SourceEffect(exact_keys(item, {"receipt_digest", "effect"})["effect"]),
        )
        for item in row["sources"]
    )
    result = CompositionLicense(
        row["schema_version"],
        CompositionRule(row["rule"]),
        sources,
        row["target_contract_digest"],
        _string_tuple(row["capability_roots"]),
        row["license_digest"],
    )
    if not validate_composition_license_shape(result):
        _reject("public-export-license")
    logger.debug("_license_from_data exit")
    return result


def _assessment_from_data(data: object) -> CompositionAssessment:
    logger.debug("_assessment_from_data entry")
    row = exact_keys(
        data,
        {
            "local_receipts_valid",
            "aggregate_claim_well_formed",
            "composition_license_established",
            "aggregate_claim_licensed",
            "source_receipt_digests",
            "target_contract_digest",
            "license_digest",
            "obstructions",
            "assessment_digest",
        },
    )
    result = CompositionAssessment(
        CompositionStatus(row["local_receipts_valid"]),
        CompositionStatus(row["aggregate_claim_well_formed"]),
        CompositionStatus(row["composition_license_established"]),
        CompositionStatus(row["aggregate_claim_licensed"]),
        _string_tuple(row["source_receipt_digests"]),
        row["target_contract_digest"],
        row["license_digest"],
        _string_tuple(row["obstructions"]),
        row["assessment_digest"],
    )
    logger.debug("_assessment_from_data exit")
    return result


def _receipt_from_data(data: object) -> CompositionReceipt:
    logger.debug("_receipt_from_data entry")
    row = exact_keys(
        data,
        {
            "schema_version",
            "source_receipt_digests",
            "target_contract_digest",
            "license_digest",
            "assessment_digest",
            "p2_promotion_established",
            "receipt_digest",
            "boundary",
        },
    )
    result = CompositionReceipt(
        row["schema_version"],
        _string_tuple(row["source_receipt_digests"]),
        row["target_contract_digest"],
        row["license_digest"],
        row["assessment_digest"],
        row["p2_promotion_established"],
        row["receipt_digest"],
        row["boundary"],
    )
    logger.debug("_receipt_from_data exit")
    return result


def _export_data(value: CompositionPublicExport) -> dict[str, object]:
    logger.debug("_export_data entry")
    result = {**_export_payload_data(value), "payload_digest": value.payload_digest}
    logger.debug("_export_data exit")
    return result


def _export_payload_data(value: CompositionPublicExport) -> dict[str, object]:
    logger.debug("_export_payload_data entry")
    result: dict[str, object] = {
        "schema_version": value.schema_version,
        "target_contract": _contract_data(value.target_contract),
        "license": _license_data(value.license),
        "assessment": _assessment_data(value.assessment),
        "receipt": _receipt_data(value.receipt),
        "boundary": value.boundary,
    }
    logger.debug("_export_payload_data exit")
    return result


def _contract_data(value: ClaimContract) -> dict[str, object]:
    logger.debug("export._contract_data entry")
    result: dict[str, object] = {
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
    logger.debug("export._contract_data exit")
    return result


def _license_data(value: CompositionLicense) -> dict[str, object]:
    logger.debug("export._license_data entry")
    result: dict[str, object] = {
        "schema_version": value.schema_version,
        "rule": value.rule.value,
        "sources": [
            {"receipt_digest": item.receipt_digest, "effect": item.effect.value}
            for item in value.sources
        ],
        "target_contract_digest": value.target_contract_digest,
        "capability_roots": list(value.capability_roots),
        "license_digest": value.license_digest,
    }
    logger.debug("export._license_data exit")
    return result


def _assessment_data(value: CompositionAssessment) -> dict[str, object]:
    logger.debug("export._assessment_data entry")
    result: dict[str, object] = {
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
    logger.debug("export._assessment_data exit")
    return result


def _receipt_data(value: CompositionReceipt) -> dict[str, object]:
    logger.debug("export._receipt_data entry")
    result: dict[str, object] = {
        "schema_version": value.schema_version,
        "source_receipt_digests": list(value.source_receipt_digests),
        "target_contract_digest": value.target_contract_digest,
        "license_digest": value.license_digest,
        "assessment_digest": value.assessment_digest,
        "p2_promotion_established": value.p2_promotion_established,
        "receipt_digest": value.receipt_digest,
        "boundary": value.boundary,
    }
    logger.debug("export._receipt_data exit")
    return result


def _string_list(value: object) -> list[str]:
    logger.debug("_string_list entry type=%s", type(value).__name__)
    if type(value) is not list or any(type(item) is not str for item in value):
        _reject("public-export-string-list")
    logger.debug("_string_list exit count=%d", len(value))
    return value


def _string_tuple(value: object) -> tuple[str, ...]:
    logger.debug("_string_tuple entry")
    result = tuple(_string_list(value))
    logger.debug("_string_tuple exit count=%d", len(result))
    return result


def _reject(reason: str) -> NoReturn:
    logger.error("composition export rejected reason=%s", reason)
    raise ClaimCompositionError(reason)
