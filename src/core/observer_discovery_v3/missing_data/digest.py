"""Canonical domain-separated digests for missing-data artifacts."""

from __future__ import annotations

from hashlib import sha256
import logging
from typing import cast

from ...proof_core_codec import digest_data
from ..schema import (
    CanonicalPresentation,
    RepresentationField,
    RepresentationRow,
    RepresentationSchema,
    ThreeWayPresentation,
)
from ..schema.types import RepresentationScalar
from .errors import reject
from .types import (
    MissingDataPolicy,
    MissingFieldRule,
    MissingSplitReceipt,
    MissingnessPresentation,
    MissingnessReceipt,
)

logger = logging.getLogger(__name__)

PROJECTION_SPEC_DOMAIN = "veyra.observer-discovery.v3.missing-projection-spec-root.v1"
POLICY_DOMAIN = "veyra.observer-discovery.v3.missing-policy-root.v1"
RAW_SPLIT_DOMAIN = "veyra.observer-discovery.v3.missing-raw-split.v1"
SEMANTIC_MASK_DOMAIN = "veyra.observer-discovery.v3.missing-semantic-mask.v1"
PROJECTION_DOMAIN = "veyra.observer-discovery.v3.missing-projection.v1"
SPLIT_RECEIPT_DOMAIN = "veyra.observer-discovery.v3.missing-split-receipt.v1"
RECEIPT_DOMAIN = "veyra.observer-discovery.v3.missing-receipt.v1"
NONCLAIMS_DOMAIN = "veyra.observer-discovery.v3.missing-nonclaims.v1"


def scalar_data(value: RepresentationScalar) -> dict[str, object]:
    """Preserve exact bool/int/string identity in all policy commitments."""
    logger.debug("missing scalar_data entry")
    if type(value) is str:
        kind = "str"
    elif type(value) is int:
        kind = "int"
    elif type(value) is bool:
        kind = "bool"
    else:
        reject("digest-scalar-type")
    result: dict[str, object] = {"type": kind, "value": value}
    logger.debug("missing scalar_data exit")
    return result


def field_data(value: RepresentationField) -> dict[str, object]:
    """Encode one exact canonical field."""
    logger.debug("missing field_data entry")
    result: dict[str, object] = {
        "name": value.name,
        "kind": value.kind,
        "categories": [scalar_data(item) for item in value.categories],
    }
    logger.debug("missing field_data exit")
    return result


def schema_data(value: RepresentationSchema) -> dict[str, object]:
    """Encode one exact canonical representation schema."""
    logger.debug("missing schema_data entry fields=%d", len(value.fields))
    result: dict[str, object] = {
        "version": value.version,
        "schema_id": value.schema_id,
        "fields": [field_data(item) for item in value.fields],
        "target_categories": [scalar_data(item) for item in value.target_categories],
    }
    logger.debug("missing schema_data exit")
    return result


def rule_data(value: MissingFieldRule) -> dict[str, object]:
    """Encode one canonical ordered policy rule."""
    logger.debug("missing rule_data entry mode=%s", value.mode.value)
    result: dict[str, object] = {
        "field_name": value.field_name,
        "mode": value.mode.value,
        "fallback": None if value.fallback is None else scalar_data(value.fallback),
        "derived_name": value.derived_name,
    }
    logger.debug("missing rule_data exit")
    return result


def row_data(value: RepresentationRow) -> dict[str, object]:
    """Encode one projected row without relying on private schema helpers."""
    logger.debug("missing row_data entry values=%d", len(value.values))
    result: dict[str, object] = {
        "row_id": value.row_id,
        "source_id": value.source_id,
        "content_id": value.content_id,
        "group_id": value.group_id,
        "values": [scalar_data(item) for item in value.values],
        "target": scalar_data(value.target),
    }
    logger.debug("missing row_data exit")
    return result


def raw_split_digest(payload: bytes) -> str:
    """Hash exact source bytes as SHA256(domain_utf8 || NUL || bytes)."""
    logger.debug("raw_split_digest entry bytes=%d", len(payload))
    result = sha256(RAW_SPLIT_DOMAIN.encode("utf-8") + b"\0" + payload).hexdigest()
    logger.debug("raw_split_digest exit")
    return result


def split_receipt_data(value: MissingSplitReceipt, *, include_digest: bool = True) -> dict[str, object]:
    """Encode a split receipt in fixed field form."""
    logger.debug("missing split_receipt_data entry include_field=%s", include_digest)
    result: dict[str, object] = {
        "raw_digest": value.raw_digest,
        "semantic_mask_digest": value.semantic_mask_digest,
        "projection_digest": value.projection_digest,
        "output_payload_digest": value.output_payload_digest,
        "row_count": value.row_count,
    }
    if include_digest:
        result["receipt_digest"] = value.receipt_digest
    logger.debug("missing split_receipt_data exit")
    return result


def policy_data(value: MissingDataPolicy) -> dict[str, object]:
    """Encode one complete retained policy in fixed field form."""
    logger.debug("missing policy_data entry rules=%d", len(value.rules))
    result: dict[str, object] = {
        "schema_version": value.schema_version,
        "base_schema": schema_data(value.base_schema),
        "base_schema_digest": value.base_schema_digest,
        "projected_schema": schema_data(value.projected_schema),
        "projected_schema_digest": value.projected_schema_digest,
        "rules": [rule_data(item) for item in value.rules],
        "projection_spec_root": value.projection_spec_root,
        "policy_digest": value.policy_digest,
    }
    logger.debug("missing policy_data exit")
    return result


def canonical_presentation_data(value: CanonicalPresentation) -> dict[str, object]:
    """Encode one complete canonical presentation in fixed field form."""
    logger.debug("missing canonical_presentation_data entry rows=%d", len(value.rows))
    result: dict[str, object] = {
        "schema": schema_data(value.schema),
        "schema_digest": value.schema_digest,
        "rows": [row_data(item) for item in value.rows],
        "payload_digest": value.payload_digest,
        "boundary": value.boundary,
    }
    logger.debug("missing canonical_presentation_data exit")
    return result


def presentation_data(value: ThreeWayPresentation) -> dict[str, object]:
    """Encode one complete retained three-way presentation."""
    logger.debug("missing presentation_data entry")
    result: dict[str, object] = {
        "train": canonical_presentation_data(value.train),
        "validation": canonical_presentation_data(value.validation),
        "test": canonical_presentation_data(value.test),
        "protocol_digest": value.protocol_digest,
        "boundary": value.boundary,
    }
    logger.debug("missing presentation_data exit")
    return result


def receipt_data(value: MissingnessReceipt) -> dict[str, object]:
    """Encode one complete retained top receipt."""
    logger.debug("missing receipt_data entry")
    result: dict[str, object] = {
        "schema_version": value.schema_version,
        "wire_format": value.wire_format.value,
        "authority": value.authority.value,
        "base_schema_digest": value.base_schema_digest,
        "projected_schema_digest": value.projected_schema_digest,
        "policy_digest": value.policy_digest,
        "train": split_receipt_data(value.train),
        "validation": split_receipt_data(value.validation),
        "test": split_receipt_data(value.test),
        "protocol_digest": value.protocol_digest,
        "nonclaims_digest": value.nonclaims_digest,
        "receipt_digest": value.receipt_digest,
        "boundary": value.boundary,
    }
    logger.debug("missing receipt_data exit")
    return result


def missingness_data(value: MissingnessPresentation) -> dict[str, object]:
    """Encode a complete retained wrapper for exact type-aware comparison."""
    logger.debug("missing missingness_data entry")
    result: dict[str, object] = {
        "boundary": value.boundary,
        "policy": policy_data(value.policy),
        "presentation": presentation_data(value.presentation),
        "receipt": receipt_data(value.receipt),
    }
    logger.debug("missing missingness_data exit")
    return result


def exact_data_equal(left: object, right: object) -> bool:
    """Compare bounded canonical data without Python bool/int equality collapse."""
    logger.debug("missing exact_data_equal entry")
    pending = [(left, right)]
    valid = True
    while pending and valid:
        left_item, right_item = pending.pop()
        if type(left_item) is not type(right_item):
            valid = False
        elif type(left_item) is dict:
            left_dict = cast(dict[object, object], left_item)
            right_dict = cast(dict[object, object], right_item)
            left_keys = tuple(left_dict)
            right_keys = tuple(right_dict)
            if left_keys != right_keys or any(type(key) is not str for key in left_keys):
                valid = False
            else:
                pending.extend((left_dict[key], right_dict[key]) for key in left_keys)
        elif type(left_item) is list or type(left_item) is tuple:
            left_sequence = cast(list[object] | tuple[object, ...], left_item)
            right_sequence = cast(list[object] | tuple[object, ...], right_item)
            if len(left_sequence) != len(right_sequence):
                valid = False
            else:
                pending.extend(zip(left_sequence, right_sequence, strict=True))
        elif type(left_item) is str or type(left_item) is int or type(left_item) is bool or left_item is None:
            valid = left_item == right_item
        else:
            valid = False
    logger.debug("missing exact_data_equal exit valid=%s", valid)
    return valid


__all__ = (
    "NONCLAIMS_DOMAIN",
    "POLICY_DOMAIN",
    "PROJECTION_DOMAIN",
    "PROJECTION_SPEC_DOMAIN",
    "RAW_SPLIT_DOMAIN",
    "RECEIPT_DOMAIN",
    "SEMANTIC_MASK_DOMAIN",
    "SPLIT_RECEIPT_DOMAIN",
    "digest_data",
    "canonical_presentation_data",
    "exact_data_equal",
    "field_data",
    "missingness_data",
    "policy_data",
    "presentation_data",
    "raw_split_digest",
    "receipt_data",
    "row_data",
    "rule_data",
    "scalar_data",
    "schema_data",
    "split_receipt_data",
)
