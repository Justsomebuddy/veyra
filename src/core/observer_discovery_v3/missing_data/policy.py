"""Canonical construction and validation of missing-data policies."""

from __future__ import annotations

import logging

from ..ingestion.types import RESERVED_COLUMNS
from ..schema import (
    RepresentationField,
    RepresentationProtocolError,
    RepresentationSchema,
    canonical_representation_schema,
    representation_schema_digest,
)
from .digest import (
    POLICY_DOMAIN,
    PROJECTION_SPEC_DOMAIN,
    digest_data,
    exact_data_equal,
    policy_data,
    rule_data,
    schema_data,
)
from .errors import MissingDataProtocolError, reject
from .resources import capture_policy, capture_policy_inputs, generated_policy_overhead, precharge_policy_inputs
from .types import MissingDataPolicy, MissingFieldRule, MissingPolicyMode, POLICY_SCHEMA

logger = logging.getLogger(__name__)


def projected_schema_for_missing_policy(
    base_schema: RepresentationSchema,
    rules: tuple[MissingFieldRule, ...],
) -> RepresentationSchema:
    """Return the uniquely required projected schema for explicit caller review."""
    logger.debug("projected_schema_for_missing_policy entry")
    base_input, projected_input, canonical_rules = capture_policy_inputs(base_schema, None, rules)
    if projected_input is not None:
        reject("projected-schema-unexpected")
    precharge_policy_inputs(base_input, None, canonical_rules)
    try:
        base = canonical_representation_schema(base_input)
    except RepresentationProtocolError as exc:
        raise MissingDataProtocolError("base-schema-invalid") from exc
    if len(canonical_rules) != len(base.fields):
        reject("policy-cardinality")
    if tuple(rule.field_name for rule in canonical_rules) != tuple(field.name for field in base.fields):
        reject("policy-field-order")
    _validate_rules(base, canonical_rules)
    base_digest = representation_schema_digest(base)
    spec = digest_data(
        {"base_schema_digest": base_digest, "rules": [rule_data(item) for item in canonical_rules]},
        PROJECTION_SPEC_DOMAIN,
    )
    try:
        result = canonical_representation_schema(_expected_projected(base, canonical_rules, spec))
    except RepresentationProtocolError as exc:
        raise MissingDataProtocolError("projected-schema-invalid") from exc
    logger.debug("projected_schema_for_missing_policy exit fields=%d", len(result.fields))
    return result


def canonical_missing_data_policy(
    base_schema: RepresentationSchema,
    projected_schema: RepresentationSchema,
    rules: tuple[MissingFieldRule, ...],
) -> MissingDataPolicy:
    """Build the one exact policy expansion without trusting caller DTO identity."""
    logger.debug("canonical_missing_data_policy entry")
    reserved_nodes, reserved_text = generated_policy_overhead()
    base_input, projected_input_optional, canonical_rules = capture_policy_inputs(
        base_schema,
        projected_schema,
        rules,
        initial_nodes=reserved_nodes,
        initial_text_bytes=reserved_text,
    )
    if projected_input_optional is None:
        reject("projected-schema-required")
    projected_input = projected_input_optional
    precharge_policy_inputs(
        base_input,
        projected_input,
        canonical_rules,
        initial_nodes=reserved_nodes,
        initial_text_bytes=reserved_text,
    )
    try:
        base = canonical_representation_schema(base_input)
    except RepresentationProtocolError as exc:
        logger.error("base schema rejected code=base-schema-invalid")
        raise MissingDataProtocolError("base-schema-invalid") from exc
    if len(canonical_rules) != len(base.fields):
        reject("policy-cardinality")
    if tuple(rule.field_name for rule in canonical_rules) != tuple(field.name for field in base.fields):
        reject("policy-field-order")
    _validate_rules(base, canonical_rules)
    base_digest = representation_schema_digest(base)
    spec = digest_data(
        {
            "base_schema_digest": base_digest,
            "rules": [rule_data(item) for item in canonical_rules],
        },
        PROJECTION_SPEC_DOMAIN,
    )
    expected = _expected_projected(base, canonical_rules, spec)
    try:
        projected = canonical_representation_schema(projected_input)
    except RepresentationProtocolError as exc:
        logger.error("projected schema rejected code=projected-schema-invalid")
        raise MissingDataProtocolError("projected-schema-invalid") from exc
    if not exact_data_equal(schema_data(projected), schema_data(expected)):
        reject("projected-schema-mismatch")
    projected_digest = representation_schema_digest(projected)
    policy_digest = digest_data(
        {
            "schema_version": POLICY_SCHEMA,
            "base_schema_digest": base_digest,
            "projection_spec_root": spec,
            "projected_schema_digest": projected_digest,
            "rules": [rule_data(item) for item in canonical_rules],
        },
        POLICY_DOMAIN,
    )
    result = MissingDataPolicy(
        POLICY_SCHEMA,
        base,
        base_digest,
        projected,
        projected_digest,
        canonical_rules,
        spec,
        policy_digest,
    )
    logger.debug("canonical_missing_data_policy exit rules=%d", len(canonical_rules))
    return result


def validate_missing_data_policy(value: object, base_schema: RepresentationSchema) -> bool:
    """Replay a policy from its complete schemas and ordered rules."""
    logger.debug("validate_missing_data_policy entry")
    try:
        captured = capture_policy(value)
        expected = canonical_missing_data_policy(base_schema, captured.projected_schema, captured.rules)
        valid = exact_data_equal(policy_data(captured), policy_data(expected))
    except (MissingDataProtocolError, AttributeError, TypeError, ValueError, OverflowError):
        logger.error("validate_missing_data_policy malformed")
        valid = False
    logger.debug("validate_missing_data_policy exit valid=%s", valid)
    return valid


def _validate_rules(base: RepresentationSchema, rules: tuple[MissingFieldRule, ...]) -> None:
    logger.debug("_validate_rules entry rules=%d", len(rules))
    occupied = set(RESERVED_COLUMNS) | {field.name for field in base.fields}
    if any(field.name in RESERVED_COLUMNS for field in base.fields):
        reject("reserved-field-name")
    for field, rule in zip(base.fields, rules, strict=True):
        if rule.mode is MissingPolicyMode.REQUIRED:
            if rule.fallback is not None or rule.derived_name is not None:
                reject("required-rule-shape")
            continue
        if rule.mode is not MissingPolicyMode.EXPLICIT_MASK or field.kind != "categorical":
            reject("mask-categorical-only")
        expected_name = f"{field.name}__present_v1"
        if rule.derived_name != expected_name:
            reject("derived-name")
        try:
            encoded = expected_name.encode("utf-8", errors="strict")
        except UnicodeError as exc:
            raise MissingDataProtocolError("derived-name-utf8") from exc
        if not expected_name or len(encoded) > 512 or expected_name in occupied:
            reject("derived-name-collision-or-limit")
        if rule.fallback is None:
            reject("fallback-outside-domain")
        key = _scalar_key(rule.fallback)
        domain = {_scalar_key(item) for item in field.categories}
        if key not in domain:
            reject("fallback-outside-domain")
        occupied.add(expected_name)
    logger.debug("_validate_rules exit")


def _expected_projected(
    base: RepresentationSchema,
    rules: tuple[MissingFieldRule, ...],
    projection_spec_root: str,
) -> RepresentationSchema:
    logger.debug("_expected_projected entry")
    fields: list[RepresentationField] = []
    for field, rule in zip(base.fields, rules, strict=True):
        fields.append(field)
        if rule.mode is MissingPolicyMode.EXPLICIT_MASK:
            fields.append(RepresentationField(rule.derived_name or "", "binary", (0, 1)))
    result = RepresentationSchema(
        f"missing-v1:{projection_spec_root}",
        tuple(fields),
        base.target_categories,
        base.version,
    )
    logger.debug("_expected_projected exit fields=%d", len(fields))
    return result


def _scalar_key(value: object) -> tuple[str, object]:
    """Return an exact scalar identity key without dynamic type metadata."""
    logger.debug("_scalar_key entry")
    if type(value) is str:
        kind = "str"
    elif type(value) is int:
        kind = "int"
    elif type(value) is bool:
        kind = "bool"
    else:
        reject("policy-scalar-type")
    result = (kind, value)
    logger.debug("_scalar_key exit")
    return result


__all__ = (
    "canonical_missing_data_policy",
    "projected_schema_for_missing_policy",
    "validate_missing_data_policy",
)
