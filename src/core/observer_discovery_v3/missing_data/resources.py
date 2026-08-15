"""Callback-free input capture and resource accounting."""

from __future__ import annotations

import logging

from ..ingestion.types import HARD_MAX_RECORD_BYTES, HARD_MAX_SPLIT_BYTES
from ..schema import (
    REPRESENTATION_BOUNDARY,
    RepresentationField,
    RepresentationRow,
    RepresentationSchema,
    ThreeWayPresentation,
)
from ..schema.types import (
    HARD_MAX_CATEGORIES,
    HARD_MAX_FIELDS,
    HARD_MAX_INTEGER_BITS,
    HARD_MAX_TEXT_BYTES,
    RepresentationScalar,
)
from .errors import MissingDataProtocolError, reject
from .types import (
    MISSING_BOUNDARY,
    MISSING_NONCLAIMS,
    POLICY_SCHEMA,
    PRESENTATION_SCHEMA,
    MissingDataPolicy,
    MissingFieldRule,
    MissingPolicyMode,
    MissingReplayAuthority,
    MissingWireFormat,
)

logger = logging.getLogger(__name__)

MAX_POLICY_NODES = 16_384
MAX_WRAPPER_NODES = 65_536
MAX_NONPAYLOAD_TEXT_BYTES = 1_048_576
MAX_CODEC_BYTES = 1_048_576


def capture_schema(value: object, reason: str) -> RepresentationSchema:
    """Detach an exact schema without invoking subclass properties or iteration."""
    logger.debug("capture_schema entry code=%s", reason)
    schema_id_raw, version_raw, fields_raw, targets_raw = _schema_parts(value, reason)
    _preflight_schema_parts(schema_id_raw, version_raw, fields_raw, targets_raw, reason)
    schema_id = _text(schema_id_raw, f"{reason}-schema-id")
    version = _text(version_raw, f"{reason}-version")
    if type(fields_raw) is not tuple or type(targets_raw) is not tuple:
        reject(f"{reason}-tuple")
    _charge_schema_text(schema_id, version, fields_raw, targets_raw, reason)
    fields = tuple(_capture_field(item, reason) for item in fields_raw)
    targets = tuple(_scalar(item, f"{reason}-target") for item in targets_raw)
    result = RepresentationSchema(schema_id, fields, targets, version)
    logger.debug("capture_schema exit reason=%s fields=%d", reason, len(fields))
    return result


def capture_rules(value: object) -> tuple[MissingFieldRule, ...]:
    """Detach exact rules and enforce policy-only node/text caps before replay."""
    logger.debug("capture_rules entry")
    if type(value) is not tuple or len(value) > 32:
        reject("policy-rules")
    _preflight_rules(value)
    rules: list[MissingFieldRule] = []
    text_bytes = 0
    nodes = 1
    for item in value:
        if type(item) is not MissingFieldRule:
            reject("policy-rule-type")
        try:
            field_name = _text(object.__getattribute__(item, "field_name"), "policy-field-name")
            mode = object.__getattribute__(item, "mode")
            fallback = object.__getattribute__(item, "fallback")
            derived_name = object.__getattribute__(item, "derived_name")
        except (AttributeError, TypeError) as exc:
            raise MissingDataProtocolError("policy-rule-shape") from exc
        if type(mode) is not MissingPolicyMode:
            reject("policy-mode")
        if fallback is not None:
            fallback = _scalar(fallback, "policy-fallback")
        if derived_name is not None:
            derived_name = _text(derived_name, "policy-derived-name")
        text_bytes += _utf8_len(field_name) + len(mode.value) + (0 if derived_name is None else _utf8_len(derived_name))
        if type(fallback) is str:
            text_bytes += _utf8_len(fallback)
        nodes += 6
        if nodes > MAX_POLICY_NODES or text_bytes > MAX_NONPAYLOAD_TEXT_BYTES:
            reject("policy-resource-limit")
        rules.append(MissingFieldRule(field_name, mode, fallback, derived_name))
    result = tuple(rules)
    logger.debug("capture_rules exit rules=%d nodes=%d text_bytes=%d", len(result), nodes, text_bytes)
    return result


def capture_policy_inputs(
    base_value: object,
    projected_value: object | None,
    rules_value: object,
    *,
    initial_nodes: int = 0,
    initial_text_bytes: int = 0,
) -> tuple[RepresentationSchema, RepresentationSchema | None, tuple[MissingFieldRule, ...]]:
    """Preflight the whole policy graph before any schema or rule detachment."""
    logger.debug("capture_policy_inputs entry")
    if (
        type(initial_nodes) is not int
        or initial_nodes < 0
        or type(initial_text_bytes) is not int
        or initial_text_bytes < 0
    ):
        reject("policy-resource-seed")
    base_parts = _schema_parts(base_value, "base-schema")
    base_nodes, base_text = _preflight_schema_parts(*base_parts, "base-schema")
    projected_nodes = 0
    projected_text = 0
    if projected_value is not None:
        projected_parts = _schema_parts(projected_value, "projected-schema")
        projected_nodes, projected_text = _preflight_schema_parts(*projected_parts, "projected-schema")
    if type(rules_value) is not tuple or len(rules_value) > 32:
        reject("policy-rules")
    rule_nodes, rule_text = _preflight_rules(rules_value)
    if 1 + initial_nodes + base_nodes + projected_nodes + rule_nodes > MAX_POLICY_NODES:
        reject("policy-resource-limit")
    if initial_text_bytes + base_text + projected_text + rule_text > MAX_NONPAYLOAD_TEXT_BYTES:
        reject("policy-resource-limit")
    base = capture_schema(base_value, "base-schema")
    projected = None if projected_value is None else capture_schema(projected_value, "projected-schema")
    rules = capture_rules(rules_value)
    logger.debug("capture_policy_inputs exit rules=%d", len(rules))
    return base, projected, rules


def capture_policy(value: object) -> MissingDataPolicy:
    """Detach one bounded policy graph before exact replay comparison."""
    logger.debug("capture_policy entry")
    if type(value) is not MissingDataPolicy:
        reject("policy-type")
    try:
        schema_version_raw = object.__getattribute__(value, "schema_version")
        base_raw = object.__getattribute__(value, "base_schema")
        base_digest_raw = object.__getattribute__(value, "base_schema_digest")
        projected_raw = object.__getattribute__(value, "projected_schema")
        projected_digest_raw = object.__getattribute__(value, "projected_schema_digest")
        rules_raw = object.__getattribute__(value, "rules")
        projection_root_raw = object.__getattribute__(value, "projection_spec_root")
        policy_digest_raw = object.__getattribute__(value, "policy_digest")
    except (AttributeError, TypeError) as exc:
        raise MissingDataProtocolError("policy-shape") from exc
    texts = (
        schema_version_raw,
        base_digest_raw,
        projected_digest_raw,
        projection_root_raw,
        policy_digest_raw,
    )
    if any(type(item) is not str or len(item) > HARD_MAX_TEXT_BYTES for item in texts):
        reject("policy-text")
    text_bytes = tuple(_preflight_utf8_bytes(item) for item in texts)
    if any(item > HARD_MAX_TEXT_BYTES for item in text_bytes):
        reject("policy-text")
    base, projected_optional, rules = capture_policy_inputs(
        base_raw,
        projected_raw,
        rules_raw,
        initial_nodes=len(texts),
        initial_text_bytes=sum(text_bytes),
    )
    if projected_optional is None:
        reject("policy-projected-schema")
    projected = projected_optional
    detached_texts = tuple(_text(item, "policy-text") for item in texts)
    result = MissingDataPolicy(
        detached_texts[0],
        base,
        detached_texts[1],
        projected,
        detached_texts[2],
        rules,
        detached_texts[3],
        detached_texts[4],
    )
    logger.debug("capture_policy exit rules=%d", len(rules))
    return result


def validated_payload(value: object, split: str) -> bytes:
    """Admit one exact bounded immutable byte payload before parsing."""
    logger.debug("validated_payload entry split=%s", split)
    if type(value) is not bytes:
        reject(f"{split}-bytes-required")
    if not value:
        reject(f"{split}-empty")
    if len(value) > HARD_MAX_SPLIT_BYTES:
        reject(f"{split}-byte-limit")
    if value.startswith(b"\xef\xbb\xbf"):
        reject(f"{split}-bom")
    if b"\x00" in value:
        reject(f"{split}-nul")
    _preflight_physical_records(value)
    try:
        value.decode("utf-8", errors="strict")
    except UnicodeError as exc:
        raise MissingDataProtocolError(f"{split}-utf8") from exc
    result = bytes(value)
    logger.debug("validated_payload exit split=%s bytes=%d", split, len(result))
    return result


def _preflight_physical_records(value: bytes) -> None:
    """Enforce physical CR/LF record caps before whole-payload UTF-8 decode."""
    logger.debug("_preflight_physical_records entry bytes=%d", len(value))
    start = 0
    records = 0
    while start < len(value):
        search_end = min(len(value), start + HARD_MAX_RECORD_BYTES + 1)
        lf = value.find(b"\n", start, search_end)
        cr = value.find(b"\r", start, search_end)
        endings = tuple(item for item in (lf, cr) if item >= 0)
        if endings:
            separator = min(endings)
            end = separator + 1
            if value[separator] == 13 and end < len(value) and value[end] == 10:
                end += 1
        else:
            end = len(value)
        if end - start > HARD_MAX_RECORD_BYTES:
            reject("physical-record-limit")
        start = end
        records += 1
    logger.debug("_preflight_physical_records exit records=%d", records)


class MissingParseBudget:
    """Incrementally charge semantic masks and projected wrapper rows."""

    def __init__(
        self,
        policy: MissingDataPolicy,
        wire_format: MissingWireFormat,
        *,
        authority: MissingReplayAuthority = MissingReplayAuthority.NATIVE_POLICY_REPLAY,
    ) -> None:
        logger.debug("MissingParseBudget entry")
        if (
            type(policy) is not MissingDataPolicy
            or type(wire_format) is not MissingWireFormat
            or type(authority) is not MissingReplayAuthority
        ):
            reject("wrapper-budget-input")
        self._nodes, self._text = _retained_wrapper_seed(policy, wire_format, authority)
        if self._nodes > MAX_WRAPPER_NODES:
            reject("wrapper-node-limit")
        if self._text > MAX_NONPAYLOAD_TEXT_BYTES:
            reject("wrapper-text-limit")
        logger.debug("MissingParseBudget exit nodes=%d text_bytes=%d", self._nodes, self._text)

    def charge(
        self,
        identities: tuple[str, ...],
        cells: tuple[RepresentationScalar | None, ...],
        projected: tuple[RepresentationScalar, ...],
        target: RepresentationScalar,
        rules: tuple[MissingFieldRule, ...],
    ) -> None:
        """Charge one complete row before it enters retained split storage."""
        logger.debug("MissingParseBudget.charge entry cells=%d projected=%d", len(cells), len(projected))
        if len(identities) != 4 or len(cells) != len(rules):
            reject("wrapper-budget-row-shape")
        self._nodes += 16 + len(cells) * 5 + len(projected) * 3
        self._text += _utf8_len(identities[0]) * 3
        self._text += sum(_utf8_len(item) * 2 for item in identities[1:])
        for cell, rule in zip(cells, rules, strict=True):
            if type(cell) is str:
                self._text += _utf8_len(cell) * 3
            elif cell is None and type(rule.fallback) is str:
                self._text += _utf8_len(rule.fallback) * 2
        if type(target) is str:
            self._text += _utf8_len(target) * 2
        if self._nodes > MAX_WRAPPER_NODES:
            reject("wrapper-node-limit")
        if self._text > MAX_NONPAYLOAD_TEXT_BYTES:
            reject("wrapper-text-limit")
        logger.debug("MissingParseBudget.charge exit nodes=%d text_bytes=%d", self._nodes, self._text)

    def charge_projected(
        self,
        identities: tuple[str, ...],
        projected: tuple[RepresentationScalar, ...],
        target: RepresentationScalar,
        rules: tuple[MissingFieldRule, ...],
    ) -> None:
        """Charge one retained projected row without reconstructing source cells."""
        logger.debug("MissingParseBudget.charge_projected entry projected=%d", len(projected))
        if len(identities) != 4:
            reject("wrapper-budget-row-shape")
        cursor = 0
        retained_text = 0
        for rule in rules:
            if cursor >= len(projected):
                reject("wrapper-budget-row-shape")
            value = projected[cursor]
            if rule.mode is MissingPolicyMode.REQUIRED:
                if type(value) is str:
                    retained_text += _utf8_len(value) * 3
                cursor += 1
                continue
            if rule.mode is not MissingPolicyMode.EXPLICIT_MASK or cursor + 1 >= len(projected):
                reject("wrapper-budget-row-shape")
            mask = projected[cursor + 1]
            if type(mask) is not int or mask not in (0, 1):
                reject("wrapper-budget-mask")
            if type(value) is str:
                retained_text += _utf8_len(value) * (2 if mask == 0 else 3)
            cursor += 2
        if cursor != len(projected):
            reject("wrapper-budget-row-shape")
        self._nodes += 16 + len(rules) * 5 + len(projected) * 3
        self._text += _utf8_len(identities[0]) * 3
        self._text += sum(_utf8_len(item) * 2 for item in identities[1:])
        self._text += retained_text
        if type(target) is str:
            self._text += _utf8_len(target) * 2
        if self._nodes > MAX_WRAPPER_NODES:
            reject("wrapper-node-limit")
        if self._text > MAX_NONPAYLOAD_TEXT_BYTES:
            reject("wrapper-text-limit")
        logger.debug(
            "MissingParseBudget.charge_projected exit nodes=%d text_bytes=%d",
            self._nodes,
            self._text,
        )


def precharge_retained_wrapper(
    policy: MissingDataPolicy,
    presentation: ThreeWayPresentation,
    wire_format: MissingWireFormat,
    authority: MissingReplayAuthority,
) -> None:
    """Apply one shared policy-plus-rows ledger to a detached retained wrapper."""
    logger.debug("precharge_retained_wrapper entry")
    if type(policy) is not MissingDataPolicy or type(presentation) is not ThreeWayPresentation:
        reject("wrapper-budget-input")
    budget = MissingParseBudget(policy, wire_format, authority=authority)
    for split in (presentation.train, presentation.validation, presentation.test):
        for row in split.rows:
            budget.charge_projected(
                (row.row_id, row.source_id, row.content_id, row.group_id),
                row.values,
                row.target,
                policy.rules,
            )
    logger.debug("precharge_retained_wrapper exit")


def precharge_policy_inputs(
    base: RepresentationSchema,
    projected: RepresentationSchema | None,
    rules: tuple[MissingFieldRule, ...],
    *,
    initial_nodes: int = 0,
    initial_text_bytes: int = 0,
) -> None:
    """Charge the combined detached policy graph before schema canonicalization."""
    logger.debug("precharge_policy_inputs entry")
    if (
        type(initial_nodes) is not int
        or initial_nodes < 0
        or type(initial_text_bytes) is not int
        or initial_text_bytes < 0
    ):
        reject("policy-resource-seed")
    schemas = (base,) if projected is None else (base, projected)
    nodes = 1 + initial_nodes
    text = initial_text_bytes
    for schema in schemas:
        schema_nodes, schema_text = _detached_schema_usage(schema)
        nodes += schema_nodes
        text += schema_text
    rule_nodes, rule_text = _detached_rules_usage(rules)
    nodes += rule_nodes
    text += rule_text
    if nodes > MAX_POLICY_NODES or text > MAX_NONPAYLOAD_TEXT_BYTES:
        reject("policy-resource-limit")
    logger.debug("precharge_policy_inputs exit nodes=%d text_bytes=%d", nodes, text)


def generated_policy_overhead() -> tuple[int, int]:
    """Return exact fixed node/text overhead for one generated v1 policy."""
    logger.debug("generated_policy_overhead entry")
    result = (5, len(POLICY_SCHEMA) + 4 * 64)
    logger.debug("generated_policy_overhead exit nodes=%d text_bytes=%d", *result)
    return result


def _retained_wrapper_seed(
    policy: MissingDataPolicy,
    wire_format: MissingWireFormat,
    authority: MissingReplayAuthority = MissingReplayAuthority.NATIVE_POLICY_REPLAY,
) -> tuple[int, int]:
    """Seed one shared ledger with retained policy, schemas and receipt overhead."""
    logger.debug("_retained_wrapper_seed entry")
    base_nodes, base_text = _detached_schema_usage(policy.base_schema)
    projected_nodes, projected_text = _detached_schema_usage(policy.projected_schema)
    rule_nodes, rule_text = _detached_rules_usage(policy.rules)
    nodes = 1 + base_nodes + projected_nodes + rule_nodes
    text = base_text + projected_text + rule_text
    policy_texts = (
        policy.schema_version,
        policy.base_schema_digest,
        policy.projected_schema_digest,
        policy.projection_spec_root,
        policy.policy_digest,
    )
    nodes += len(policy_texts)
    text += sum(_utf8_len(item) for item in policy_texts)
    nodes += projected_nodes * 3
    text += projected_text * 3
    fixed_texts = (
        PRESENTATION_SCHEMA,
        wire_format.value,
        authority.value,
        MISSING_BOUNDARY,
        MISSING_BOUNDARY,
        REPRESENTATION_BOUNDARY,
        REPRESENTATION_BOUNDARY,
        REPRESENTATION_BOUNDARY,
        REPRESENTATION_BOUNDARY,
        *MISSING_NONCLAIMS,
    )
    text += sum(_utf8_len(item) for item in fixed_texts)
    # Wrapper/three-way/three presentations/top receipt/three split receipts,
    # plus 28 retained/generated 64-hex digest fields and scalar containers.
    nodes += 96 + 28
    text += 28 * 64
    if nodes > MAX_WRAPPER_NODES or text > MAX_NONPAYLOAD_TEXT_BYTES:
        reject("wrapper-resource-limit")
    logger.debug("_retained_wrapper_seed exit nodes=%d text_bytes=%d", nodes, text)
    return nodes, text


def _detached_schema_usage(schema: RepresentationSchema) -> tuple[int, int]:
    """Count one already detached schema in the shared resource model."""
    logger.debug("_detached_schema_usage entry fields=%d", len(schema.fields))
    nodes = 3 + len(schema.target_categories) * 2
    text = _utf8_len(schema.schema_id) + _utf8_len(schema.version)
    for field in schema.fields:
        nodes += 4 + len(field.categories) * 2
        text += _utf8_len(field.name) + _utf8_len(field.kind)
        text += sum(_utf8_len(item) for item in field.categories if type(item) is str)
    text += sum(_utf8_len(item) for item in schema.target_categories if type(item) is str)
    logger.debug("_detached_schema_usage exit nodes=%d text_bytes=%d", nodes, text)
    return nodes, text


def _detached_rules_usage(rules: tuple[MissingFieldRule, ...]) -> tuple[int, int]:
    """Count already detached rules in the shared resource model."""
    logger.debug("_detached_rules_usage entry rules=%d", len(rules))
    nodes = len(rules) * 6
    text = 0
    for rule in rules:
        text += _utf8_len(rule.field_name) + len(rule.mode.value)
        if type(rule.fallback) is str:
            text += _utf8_len(rule.fallback)
        if rule.derived_name is not None:
            text += _utf8_len(rule.derived_name)
    logger.debug("_detached_rules_usage exit nodes=%d text_bytes=%d", nodes, text)
    return nodes, text


def precharge_projection(*, rows: tuple[RepresentationRow, ...], projected_fields: int) -> None:
    """Charge the complete projected field/cell shape before canonical construction."""
    logger.debug("precharge_projection entry rows=%d fields=%d", len(rows), projected_fields)
    if type(rows) is not tuple or type(projected_fields) is not int or projected_fields < 0:
        reject("projection-charge-type")
    cells = len(rows) * projected_fields
    nodes = 256 + len(rows) * (8 + projected_fields * 2)
    text = 0
    for row in rows:
        if type(row) is not RepresentationRow:
            reject("projection-row-type")
        text += sum(_utf8_len(item) for item in (row.row_id, row.source_id, row.content_id, row.group_id))
        text += sum(_utf8_len(item) for item in row.values if type(item) is str)
        if type(row.target) is str:
            text += _utf8_len(row.target)
    if cells > 262_144:
        reject("projection-cell-limit")
    if nodes > MAX_WRAPPER_NODES:
        reject("wrapper-node-limit")
    if text > MAX_NONPAYLOAD_TEXT_BYTES:
        reject("wrapper-text-limit")
    logger.debug("precharge_projection exit cells=%d nodes=%d text_bytes=%d", cells, nodes, text)


def _capture_field(value: object, reason: str) -> RepresentationField:
    logger.debug("_capture_field entry code=%s", reason)
    if type(value) is not RepresentationField:
        reject(f"{reason}-field-type")
    name = _text(object.__getattribute__(value, "name"), f"{reason}-field-name")
    kind = _text(object.__getattribute__(value, "kind"), f"{reason}-field-kind")
    categories_raw = object.__getattribute__(value, "categories")
    if type(categories_raw) is not tuple:
        reject(f"{reason}-categories-tuple")
    categories = tuple(_scalar(item, f"{reason}-category") for item in categories_raw)
    result = RepresentationField(name, kind, categories)
    logger.debug("_capture_field exit categories=%d", len(categories))
    return result


def _scalar(value: object, reason: str) -> RepresentationScalar:
    logger.debug("_scalar entry code=%s", reason)
    if type(value) is str:
        _utf8_len(value)
        result: RepresentationScalar = str(value)
    elif type(value) is int:
        if int.bit_length(value) > HARD_MAX_INTEGER_BITS:
            reject(f"{reason}-integer-limit")
        result = int(value)
    elif type(value) is bool:
        result = bool(value)
    else:
        reject(reason)
    logger.debug("_scalar exit")
    return result


def _text(value: object, reason: str) -> str:
    logger.debug("_text entry code=%s", reason)
    if type(value) is not str:
        reject(reason)
    if len(value) > HARD_MAX_TEXT_BYTES:
        reject(f"{reason}-text-limit")
    if _utf8_len(value) > HARD_MAX_TEXT_BYTES:
        reject(f"{reason}-text-limit")
    result = str(value)
    logger.debug("_text exit bytes=%d", len(result.encode("utf-8")))
    return result


def _utf8_len(value: str) -> int:
    try:
        return len(value.encode("utf-8", errors="strict"))
    except UnicodeError as exc:
        logger.error("invalid utf8 code=invalid-utf8")
        raise MissingDataProtocolError("invalid-utf8") from exc


def _preflight_schema_parts(
    schema_id: object,
    version: object,
    fields: object,
    targets: object,
    reason: str,
) -> tuple[int, int]:
    """Reject shallow schema resource abuse before copying or UTF-8 encoding."""
    logger.debug("_preflight_schema_parts entry code=%s", reason)
    if type(schema_id) is not str or type(version) is not str:
        reject(f"{reason}-text")
    if len(schema_id) > HARD_MAX_TEXT_BYTES or len(version) > HARD_MAX_TEXT_BYTES:
        reject(f"{reason}-text-limit")
    if type(fields) is not tuple or not 1 <= len(fields) <= HARD_MAX_FIELDS:
        reject(f"{reason}-fields-limit")
    if type(targets) is not tuple or not 2 <= len(targets) <= HARD_MAX_CATEGORIES:
        reject(f"{reason}-targets-limit")
    nodes = 4 + len(fields) * 4 + len(targets) * 2
    text_bytes = _preflight_utf8_bytes(schema_id) + _preflight_utf8_bytes(version)
    for field in fields:
        if type(field) is not RepresentationField:
            reject(f"{reason}-field-type")
        try:
            name = object.__getattribute__(field, "name")
            kind = object.__getattribute__(field, "kind")
            categories = object.__getattribute__(field, "categories")
        except (AttributeError, TypeError) as exc:
            raise MissingDataProtocolError(f"{reason}-field-shape") from exc
        if type(name) is not str or type(kind) is not str:
            reject(f"{reason}-field-text")
        if len(name) > HARD_MAX_TEXT_BYTES or len(kind) > HARD_MAX_TEXT_BYTES:
            reject(f"{reason}-field-text-limit")
        if type(categories) is not tuple or not 2 <= len(categories) <= HARD_MAX_CATEGORIES:
            reject(f"{reason}-categories-limit")
        nodes += len(categories) * 2
        text_bytes += _preflight_utf8_bytes(name) + _preflight_utf8_bytes(kind)
        for item in categories:
            text_bytes += _preflight_scalar(item, f"{reason}-category")
    for item in targets:
        text_bytes += _preflight_scalar(item, f"{reason}-target")
    if nodes > MAX_POLICY_NODES or text_bytes > MAX_NONPAYLOAD_TEXT_BYTES:
        reject("policy-resource-limit")
    logger.debug("_preflight_schema_parts exit nodes=%d text_bytes=%d", nodes, text_bytes)
    return nodes, text_bytes


def _charge_schema_text(
    schema_id: str,
    version: str,
    fields: tuple[RepresentationField, ...],
    targets: tuple[RepresentationScalar, ...],
    reason: str,
) -> None:
    """Charge exact UTF-8 bytes only after the complete shallow preflight."""
    logger.debug("_charge_schema_text entry code=%s", reason)
    text_bytes = _utf8_len(schema_id) + _utf8_len(version)
    for field in fields:
        name = object.__getattribute__(field, "name")
        kind = object.__getattribute__(field, "kind")
        categories = object.__getattribute__(field, "categories")
        text_bytes += _utf8_len(name) + _utf8_len(kind)
        text_bytes += sum(_utf8_len(item) for item in categories if type(item) is str)
    text_bytes += sum(_utf8_len(item) for item in targets if type(item) is str)
    if text_bytes > MAX_NONPAYLOAD_TEXT_BYTES:
        reject("policy-resource-limit")
    logger.debug("_charge_schema_text exit text_bytes=%d", text_bytes)


def _preflight_rules(value: tuple[object, ...]) -> tuple[int, int]:
    """Reject shallow rule resource abuse before copying or UTF-8 encoding."""
    logger.debug("_preflight_rules entry rules=%d", len(value))
    nodes = 1 + len(value) * 6
    text_bytes = 0
    for item in value:
        if type(item) is not MissingFieldRule:
            reject("policy-rule-type")
        try:
            field_name = object.__getattribute__(item, "field_name")
            mode = object.__getattribute__(item, "mode")
            fallback = object.__getattribute__(item, "fallback")
            derived_name = object.__getattribute__(item, "derived_name")
        except (AttributeError, TypeError) as exc:
            raise MissingDataProtocolError("policy-rule-shape") from exc
        if type(field_name) is not str or len(field_name) > HARD_MAX_TEXT_BYTES:
            reject("policy-field-name")
        if type(mode) is not MissingPolicyMode:
            reject("policy-mode")
        if derived_name is not None and (type(derived_name) is not str or len(derived_name) > HARD_MAX_TEXT_BYTES):
            reject("policy-derived-name")
        text_bytes += _preflight_utf8_bytes(field_name) + len(mode.value)
        if derived_name is not None:
            text_bytes += _preflight_utf8_bytes(derived_name)
        if fallback is not None:
            text_bytes += _preflight_scalar(fallback, "policy-fallback")
    if nodes > MAX_POLICY_NODES or text_bytes > MAX_NONPAYLOAD_TEXT_BYTES:
        reject("policy-resource-limit")
    logger.debug("_preflight_rules exit nodes=%d text_bytes=%d", nodes, text_bytes)
    return nodes, text_bytes


def _preflight_scalar(value: object, reason: str) -> int:
    """Return exact string bytes after callback-free scalar and integer gates."""
    logger.debug("_preflight_scalar entry code=%s", reason)
    if type(value) is str:
        if len(value) > HARD_MAX_TEXT_BYTES:
            reject(f"{reason}-text-limit")
        result = _preflight_utf8_bytes(value)
    elif type(value) is int:
        if int.bit_length(value) > HARD_MAX_INTEGER_BITS:
            reject(f"{reason}-integer-limit")
        result = 0
    elif type(value) is bool:
        result = 0
    else:
        reject(reason)
    logger.debug("_preflight_scalar exit text_bytes=%d", result)
    return result


def _preflight_utf8_bytes(value: str) -> int:
    """Count exact UTF-8 bytes for an exact built-in string without allocating encoded bytes."""
    logger.debug("_preflight_utf8_bytes entry chars=%d", len(value))
    total = 0
    for character in value:
        point = ord(character)
        if point <= 0x7F:
            total += 1
        elif point <= 0x7FF:
            total += 2
        elif 0xD800 <= point <= 0xDFFF:
            reject("invalid-utf8")
        elif point <= 0xFFFF:
            total += 3
        else:
            total += 4
    logger.debug("_preflight_utf8_bytes exit bytes=%d", total)
    return total


def _schema_parts(value: object, reason: str) -> tuple[object, object, object, object]:
    """Read four exact schema slots without copying or dynamic type metadata."""
    logger.debug("_schema_parts entry code=%s", reason)
    if type(value) is not RepresentationSchema:
        reject(f"{reason}-type")
    try:
        result = (
            object.__getattribute__(value, "schema_id"),
            object.__getattribute__(value, "version"),
            object.__getattribute__(value, "fields"),
            object.__getattribute__(value, "target_categories"),
        )
    except (AttributeError, TypeError) as exc:
        logger.error("_schema_parts malformed code=%s", reason)
        raise MissingDataProtocolError(f"{reason}-shape") from exc
    logger.debug("_schema_parts exit code=%s", reason)
    return result
