"""Bounded shallow validation for the P2 claim-admission sibling."""

from __future__ import annotations

import logging
from dataclasses import fields, is_dataclass
from enum import Enum
from typing import Any

from ..claim_composition.types import (
    AdaptiveCapability,
    ClaimClass,
    ClaimCompositionSource,
    ClaimContract,
    ClaimQuantifier,
    CompositionAssessment,
    CompositionLicense,
    CompositionReceipt,
    CompositionRule,
    CompositionSourceBinding,
    CompositionStatus,
    CorroborationStatus,
    LocalClaimReceipt,
    LocalReceiptValidity,
    PublicWording,
    SourceEffect,
)
from ..observer_discovery_v3.dsl.types import ClosedEvaluationReceipt
from ..observer_discovery_v3.ledger.types import (
    OneShotLedgerReceipt,
    OneShotLedgerState,
    OneShotOutcome,
    OneShotReservation,
)
from ..observer_discovery_v3.service.types import GovernedEvaluationResult
from ..status_promotion_types import (
    ClaimDescriptor,
    EvidenceField,
    EvidenceStatus,
    IndexBinding,
    JudgmentKind,
    MetaAuditDecision,
    MetaOntologicalStatus,
    PositiveProvenance,
    PremiseArtifact,
    PromotionAuditRequest,
    PromotionSchemaAudit,
    SchemaAuditReport,
    SchemaAuditRow,
)
from .errors import P2ClaimAdmissionError, reject
from .resource_validation import (
    MAX_DEPTH,
    MAX_IDENTIFIER_BYTES,
    MAX_NONPAYLOAD_TEXT_BYTES,
    MAX_STRUCTURAL_NODES,
    charge_structure,
    charge_text,
    exact_identifier as _bounded_identifier,
)
from .types import LicensedCompositionPresentation, SourceValidationAuthority, SourceValidationBinding

logger = logging.getLogger(__name__)

MAX_JSON_BYTES = 1_048_576
MIN_SOURCES = 2
MAX_SOURCES = 64

_EXACT_DATACLASS_TYPES = frozenset(
    {
        ClaimCompositionSource,
        ClaimContract,
        ClosedEvaluationReceipt,
        CompositionAssessment,
        CompositionLicense,
        CompositionReceipt,
        CompositionSourceBinding,
        GovernedEvaluationResult,
        LicensedCompositionPresentation,
        LocalClaimReceipt,
        OneShotLedgerReceipt,
        OneShotReservation,
        ClaimDescriptor,
        EvidenceField,
        IndexBinding,
        PremiseArtifact,
        PromotionAuditRequest,
        PromotionSchemaAudit,
        SchemaAuditReport,
        SchemaAuditRow,
        SourceValidationBinding,
    }
)
_EXACT_ENUM_TYPES = frozenset(
    {
        AdaptiveCapability,
        ClaimClass,
        ClaimQuantifier,
        CompositionRule,
        CompositionStatus,
        CorroborationStatus,
        EvidenceStatus,
        JudgmentKind,
        LocalReceiptValidity,
        MetaAuditDecision,
        MetaOntologicalStatus,
        OneShotLedgerState,
        OneShotOutcome,
        PositiveProvenance,
        PublicWording,
        SourceEffect,
        SourceValidationAuthority,
    }
)


def exact_identifier(value: object, reason: str) -> str:
    """Validate one nonempty identifier without encoding an unbounded string."""
    logger.debug("exact_identifier entry field=%s", reason)
    if type(value) is not str or not value:
        reject(reason)
    result = _bounded_identifier(value, reason)
    logger.debug("exact_identifier exit field=%s", reason)
    return result


def capture_exact_core_tree(
    value: object,
    *,
    node_allowance: int = MAX_STRUCTURAL_NODES,
    text_allowance: int = MAX_NONPAYLOAD_TEXT_BYTES,
) -> tuple[object, int, int]:
    """Capture one callback-free exact DTO tree under combined resource caps."""
    logger.debug(
        "capture_exact_core_tree entry type=%s node_allowance=%d text_allowance=%d",
        type(value).__name__,
        node_allowance,
        text_allowance,
    )
    if type(node_allowance) is not int or type(text_allowance) is not int or node_allowance < 0 or text_allowance < 0:
        reject("invalid-resource-allowance")
    nodes = 0
    text_bytes = 0

    def capture(node: object, depth: int) -> Any:
        nonlocal nodes, text_bytes
        nodes += 1
        if nodes > node_allowance:
            reject("structural-node-limit")
        if depth > MAX_DEPTH:
            reject("structural-depth-limit")
        node_type = type(node)
        if node is None or node_type in (bool, int, bytes):
            return node
        if node_type is str:
            remaining = text_allowance - text_bytes
            if len(node) > remaining:
                reject("nonpayload-text-limit")
            try:
                size = len(node.encode("utf-8", errors="strict"))
            except UnicodeError as exc:
                logger.error("capture_exact_core_tree rejected type=%s", type(exc).__name__)
                raise P2ClaimAdmissionError("nonpayload-text-invalid") from exc
            if size > remaining:
                reject("nonpayload-text-limit")
            text_bytes += size
            return node
        if node_type in _EXACT_ENUM_TYPES:
            raw_value = object.__getattribute__(node, "_value_")
            if type(raw_value) is not str:
                reject("presentation-nested-enum-value")
            capture(raw_value, depth + 1)
            return node
        if node_type is tuple:
            return tuple(capture(item, depth + 1) for item in node)
        if node_type is list:
            return [capture(item, depth + 1) for item in node]
        if node_type is dict:
            return {capture(key, depth + 1): capture(item, depth + 1) for key, item in node.items()}
        if node_type in _EXACT_DATACLASS_TYPES and is_dataclass(node):
            captured = {
                item.name: capture(object.__getattribute__(node, item.name), depth + 1) for item in fields(node_type)
            }
            return node_type(**captured)
        if isinstance(node, Enum):
            reject("presentation-nested-enum-type")
        reject("presentation-nested-type")

    result = capture(value, 0)
    logger.debug("capture_exact_core_tree exit nodes=%d text=%d", nodes, text_bytes)
    return result, nodes, text_bytes


def validate_exact_core_tree(value: object) -> None:
    """Reject hostile primitive/container subclasses without invoking callbacks."""
    logger.debug("validate_exact_core_tree entry type=%s", type(value).__name__)
    capture_exact_core_tree(value)
    logger.debug("validate_exact_core_tree exit")


def capture_authoritative_inputs(
    sources: object,
    target: object,
    license: object,
    receipt: object,
    judgment_id: object,
) -> tuple[
    tuple[ClaimCompositionSource, ...],
    ClaimContract,
    CompositionLicense,
    CompositionReceipt,
    str,
    int,
    int,
]:
    """Capture one bounded immutable authority snapshot before any deep replay."""
    logger.debug("capture_authoritative_inputs entry")
    if type(sources) is not tuple or not MIN_SOURCES <= len(sources) <= MAX_SOURCES:
        reject("source-count")
    if any(type(item) is not ClaimCompositionSource for item in sources):
        reject("source-type")
    if type(target) is not ClaimContract:
        reject("target-type")
    if type(license) is not CompositionLicense:
        reject("license-type")
    if type(receipt) is not CompositionReceipt:
        reject("receipt-type")
    exact_identifier(judgment_id, "judgment-id")
    captured, nodes, text = capture_exact_core_tree((sources, target, license, receipt, judgment_id))
    captured_sources, captured_target, captured_license, captured_receipt, captured_id = captured
    logger.debug("capture_authoritative_inputs exit nodes=%d text=%d", nodes, text)
    return (
        captured_sources,
        captured_target,
        captured_license,
        captured_receipt,
        captured_id,
        nodes,
        text,
    )


def preflight_authoritative_inputs(
    sources: object,
    target: object,
    license: object,
    receipt: object,
    judgment_id: object,
) -> tuple[int, int]:
    """Reject hostile outer shapes and sibling resources before any replay."""
    logger.debug("preflight_authoritative_inputs entry")
    *_, nodes, text = capture_authoritative_inputs(sources, target, license, receipt, judgment_id)
    logger.debug("preflight_authoritative_inputs exit nodes=%d text=%d", nodes, text)
    return nodes, text


def charge_decoded_with_raw(decoded: object, raw_nodes: int, raw_text: int) -> None:
    """Apply the combined raw-plus-decoded sibling ceilings."""
    logger.debug("charge_decoded_with_raw entry")
    if type(raw_nodes) is not int or type(raw_text) is not int:
        reject("invalid-resource-charge")
    decoded_nodes = charge_structure(decoded, allowance=MAX_STRUCTURAL_NODES - raw_nodes)
    decoded_text = charge_text(decoded, allowance=MAX_NONPAYLOAD_TEXT_BYTES - raw_text)
    logger.debug("charge_decoded_with_raw exit nodes=%d text=%d", raw_nodes + decoded_nodes, raw_text + decoded_text)
