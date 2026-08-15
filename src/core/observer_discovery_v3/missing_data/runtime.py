"""Source-backed construction and replay for missing-data presentations."""

from __future__ import annotations

from dataclasses import replace
import logging

from ..schema import (
    CanonicalPresentation,
    RepresentationField,
    RepresentationProtocolError,
    RepresentationRow,
    RepresentationSchema,
    ThreeWayPresentation,
    canonical_presentation,
    canonical_three_way_presentation,
)
from ..schema.types import HARD_MAX_INTEGER_BITS, HARD_MAX_TEXT_BYTES
from .digest import (
    NONCLAIMS_DOMAIN,
    PROJECTION_DOMAIN,
    RECEIPT_DOMAIN,
    SEMANTIC_MASK_DOMAIN,
    SPLIT_RECEIPT_DOMAIN,
    digest_data,
    exact_data_equal,
    missingness_data,
    policy_data,
    presentation_data,
    raw_split_digest,
    receipt_data,
    split_receipt_data,
)
from .errors import MissingDataProtocolError, reject
from .parsing import ParsedMissingSplit, parse_missing_split
from .policy import canonical_missing_data_policy
from .resources import (
    MissingParseBudget,
    capture_policy,
    capture_policy_inputs,
    capture_schema,
    precharge_projection,
    precharge_retained_wrapper,
    validated_payload,
)
from .types import (
    MISSING_BOUNDARY,
    MISSING_NONCLAIMS,
    PRESENTATION_SCHEMA,
    MissingDataPolicy,
    MissingFieldRule,
    MissingPolicyMode,
    MissingReplayAuthority,
    MissingSplitReceipt,
    MissingWireFormat,
    MissingnessPresentation,
    MissingnessReceipt,
)

logger = logging.getLogger(__name__)


def missingness_from_csv(
    policy: MissingDataPolicy,
    base_schema: RepresentationSchema,
    projected_schema: RepresentationSchema,
    *,
    train: bytes,
    validation: bytes,
    test: bytes,
) -> MissingnessPresentation:
    """Freshly replay exact CSV sources into one native-authority wrapper."""
    logger.debug("missingness_from_csv entry")
    result = replay_missingness_from_sources(
        policy,
        base_schema,
        projected_schema,
        wire_format=MissingWireFormat.CSV,
        train=train,
        validation=validation,
        test=test,
    )
    logger.debug("missingness_from_csv exit rows=%d", _row_count(result))
    return result


def missingness_from_jsonl(
    policy: MissingDataPolicy,
    base_schema: RepresentationSchema,
    projected_schema: RepresentationSchema,
    *,
    train: bytes,
    validation: bytes,
    test: bytes,
) -> MissingnessPresentation:
    """Freshly replay exact JSONL sources into one native-authority wrapper."""
    logger.debug("missingness_from_jsonl entry")
    result = replay_missingness_from_sources(
        policy,
        base_schema,
        projected_schema,
        wire_format=MissingWireFormat.JSONL,
        train=train,
        validation=validation,
        test=test,
    )
    logger.debug("missingness_from_jsonl exit rows=%d", _row_count(result))
    return result


def replay_missingness_from_sources(
    policy: MissingDataPolicy,
    base_schema: RepresentationSchema,
    projected_schema: RepresentationSchema,
    *,
    wire_format: MissingWireFormat,
    train: bytes,
    validation: bytes,
    test: bytes,
) -> MissingnessPresentation:
    """Sole native authority constructor: capture and replay all fresh sources."""
    logger.debug("replay_missingness_from_sources entry")
    if type(wire_format) is not MissingWireFormat:
        reject("wire-format-type")
    captured_policy = capture_policy(policy)
    base, projected_optional, _ = capture_policy_inputs(base_schema, projected_schema, captured_policy.rules)
    if projected_optional is None:
        reject("projected-schema-required")
    projected = projected_optional
    try:
        expected_policy = canonical_missing_data_policy(base, projected, captured_policy.rules)
    except (AttributeError, TypeError) as exc:
        raise MissingDataProtocolError("policy-shape") from exc
    if not exact_data_equal(policy_data(captured_policy), policy_data(expected_policy)):
        reject("policy-mismatch")
    raw_splits = (
        validated_payload(train, "train"),
        validated_payload(validation, "validation"),
        validated_payload(test, "test"),
    )
    logger.debug("replay_missingness_from_sources external-call parser format=%s", wire_format.value)
    budget = MissingParseBudget(expected_policy, wire_format)
    parsed = tuple(parse_missing_split(raw, base, expected_policy, wire_format, budget) for raw in raw_splits)
    precharge_projection(
        rows=tuple(row for item in parsed for row in item.rows),
        projected_fields=len(projected.fields),
    )
    try:
        presentations = tuple(canonical_presentation(projected, item.rows) for item in parsed)
        three_way = canonical_three_way_presentation(*presentations)
    except RepresentationProtocolError as exc:
        logger.error("projected canonicalization rejected code=projected-presentation-invalid")
        raise MissingDataProtocolError("projected-presentation-invalid") from exc
    split_receipts_raw = tuple(
        _split_receipt(raw, parsed_split, presentation.payload_digest, expected_policy.policy_digest)
        for raw, parsed_split, presentation in zip(raw_splits, parsed, presentations, strict=True)
    )
    split_receipts = (split_receipts_raw[0], split_receipts_raw[1], split_receipts_raw[2])
    receipt = _top_receipt(
        wire_format,
        MissingReplayAuthority.NATIVE_POLICY_REPLAY,
        expected_policy,
        split_receipts,
        three_way.protocol_digest,
    )
    result = MissingnessPresentation(expected_policy, three_way, receipt, MISSING_BOUNDARY)
    logger.debug("replay_missingness_from_sources exit rows=%d", _row_count(result))
    return result


def validate_native_missingness_presentation(
    value: object,
    policy: MissingDataPolicy,
    base_schema: RepresentationSchema,
    projected_schema: RepresentationSchema,
    *,
    wire_format: MissingWireFormat,
    train: bytes,
    validation: bytes,
    test: bytes,
) -> bool:
    """Return true only for equality with complete fresh source-backed replay."""
    logger.debug("validate_native_missingness_presentation entry")
    try:
        captured = _snapshot_retained_missingness_presentation(value)
        expected = replay_missingness_from_sources(
            policy,
            base_schema,
            projected_schema,
            wire_format=wire_format,
            train=train,
            validation=validation,
            test=test,
        )
        valid = exact_data_equal(missingness_data(captured), missingness_data(expected))
    except (MissingDataProtocolError, AttributeError, TypeError, ValueError, OverflowError):
        logger.error("validate_native_missingness_presentation replay-failed")
        valid = False
    logger.debug("validate_native_missingness_presentation exit valid=%s", valid)
    return valid


def external_binding(value: MissingnessPresentation) -> MissingnessPresentation:
    """Downgrade a structurally valid wrapper; never upgrade authority."""
    logger.debug("external_binding entry")
    captured = _snapshot_retained_missingness_presentation(value)
    if not _validate_detached_missingness_presentation(captured, allow_native=True):
        reject("external-binding-invalid")
    receipt = _top_receipt(
        captured.receipt.wire_format,
        MissingReplayAuthority.EXTERNAL_BINDING_ONLY,
        captured.policy,
        (captured.receipt.train, captured.receipt.validation, captured.receipt.test),
        captured.presentation.protocol_digest,
    )
    result = MissingnessPresentation(captured.policy, captured.presentation, receipt, MISSING_BOUNDARY)
    precharge_retained_wrapper(result.policy, result.presentation, receipt.wire_format, receipt.authority)
    logger.debug("external_binding exit")
    return result


def validate_structural_missingness_presentation(value: object) -> bool:
    """Validate only an external retained structure; native always requires replay."""
    logger.debug("validate_structural_missingness_presentation entry")
    valid = _validate_retained_missingness_presentation(value, allow_native=False)
    logger.debug("validate_structural_missingness_presentation exit valid=%s", valid)
    return valid


def _validate_retained_missingness_presentation(value: object, *, allow_native: bool) -> bool:
    """Internal structural replay used before downgrade or source-backed comparison."""
    logger.debug("_validate_retained_missingness_presentation entry")
    try:
        captured = _snapshot_retained_missingness_presentation(value)
        valid = _validate_detached_missingness_presentation(captured, allow_native=allow_native)
    except (
        MissingDataProtocolError,
        RepresentationProtocolError,
        AttributeError,
        TypeError,
        ValueError,
        OverflowError,
    ):
        logger.error("validate_structural_missingness_presentation malformed")
        valid = False
    logger.debug("_validate_retained_missingness_presentation exit valid=%s", valid)
    return valid


def _validate_detached_missingness_presentation(
    value: MissingnessPresentation,
    *,
    allow_native: bool,
) -> bool:
    """Replay one detached wrapper with exact type-aware identity checks."""
    logger.debug("_validate_detached_missingness_presentation entry")
    try:
        if value.boundary != MISSING_BOUNDARY:
            return False
        policy = value.policy
        canonical_policy = canonical_missing_data_policy(policy.base_schema, policy.projected_schema, policy.rules)
        if not exact_data_equal(policy_data(policy), policy_data(canonical_policy)):
            return False
        splits = (value.presentation.train, value.presentation.validation, value.presentation.test)
        canonical_splits = tuple(canonical_presentation(policy.projected_schema, item.rows) for item in splits)
        canonical_three_way = canonical_three_way_presentation(*canonical_splits)
        if not exact_data_equal(presentation_data(value.presentation), presentation_data(canonical_three_way)):
            return False
        receipt = value.receipt
        if receipt.authority is MissingReplayAuthority.NATIVE_POLICY_REPLAY and not allow_native:
            return False
        expected_receipt = _top_receipt(
            receipt.wire_format,
            receipt.authority,
            policy,
            (receipt.train, receipt.validation, receipt.test),
            value.presentation.protocol_digest,
        )
        valid = exact_data_equal(receipt_data(receipt), receipt_data(expected_receipt))
        valid = valid and tuple(
            item.output_payload_digest for item in (receipt.train, receipt.validation, receipt.test)
        ) == tuple(item.payload_digest for item in splits)
        valid = valid and tuple(item.row_count for item in (receipt.train, receipt.validation, receipt.test)) == tuple(
            len(item.rows) for item in splits
        )
    except (
        MissingDataProtocolError,
        RepresentationProtocolError,
        AttributeError,
        TypeError,
        ValueError,
        OverflowError,
    ):
        logger.error("_validate_detached_missingness_presentation malformed")
        valid = False
    logger.debug("_validate_detached_missingness_presentation exit valid=%s", valid)
    return valid


def _snapshot_retained_missingness_presentation(value: object) -> MissingnessPresentation:
    """Capture a bounded detached wrapper before validation or serialization."""
    logger.debug("_snapshot_retained_missingness_presentation entry")
    if type(value) is not MissingnessPresentation or not _safe_structural_shape(value):
        reject("wrapper-shape")
    policy = capture_policy(object.__getattribute__(value, "policy"))
    presentation = _snapshot_three_way(object.__getattribute__(value, "presentation"))
    receipt = _snapshot_receipt(object.__getattribute__(value, "receipt"))
    boundary = object.__getattribute__(value, "boundary")
    if type(boundary) is not str:
        reject("wrapper-boundary-type")
    result = MissingnessPresentation(policy, presentation, receipt, _snapshot_text(boundary, "wrapper-boundary"))
    precharge_retained_wrapper(policy, presentation, receipt.wire_format, receipt.authority)
    logger.debug("_snapshot_retained_missingness_presentation exit")
    return result


def _snapshot_three_way(value: object) -> ThreeWayPresentation:
    """Capture one exact three-way graph without retaining caller containers."""
    logger.debug("_snapshot_three_way entry")
    if type(value) is not ThreeWayPresentation:
        reject("wrapper-presentation-type")
    train = _snapshot_canonical(object.__getattribute__(value, "train"))
    validation = _snapshot_canonical(object.__getattribute__(value, "validation"))
    test = _snapshot_canonical(object.__getattribute__(value, "test"))
    protocol_digest = object.__getattribute__(value, "protocol_digest")
    boundary = object.__getattribute__(value, "boundary")
    if type(protocol_digest) is not str or type(boundary) is not str:
        reject("wrapper-presentation-text")
    all_rows = tuple(row for item in (train, validation, test) for row in item.rows)
    precharge_projection(rows=all_rows, projected_fields=len(train.schema.fields))
    result = ThreeWayPresentation(
        train,
        validation,
        test,
        _snapshot_text(protocol_digest, "wrapper-protocol-digest"),
        _snapshot_text(boundary, "wrapper-presentation-boundary"),
    )
    logger.debug("_snapshot_three_way exit rows=%d", len(all_rows))
    return result


def _snapshot_canonical(value: object) -> CanonicalPresentation:
    """Capture one exact canonical split without retaining caller containers."""
    logger.debug("_snapshot_canonical entry")
    if type(value) is not CanonicalPresentation:
        reject("wrapper-split-type")
    schema = capture_schema(object.__getattribute__(value, "schema"), "wrapper-schema")
    rows_raw = object.__getattribute__(value, "rows")
    schema_digest = object.__getattribute__(value, "schema_digest")
    payload_digest = object.__getattribute__(value, "payload_digest")
    boundary = object.__getattribute__(value, "boundary")
    if type(rows_raw) is not tuple or not 1 <= len(rows_raw) <= 8192:
        reject("wrapper-rows-limit")
    if any(type(item) is not RepresentationRow for item in rows_raw):
        reject("wrapper-row-type")
    if any(type(item) is not str for item in (schema_digest, payload_digest, boundary)):
        reject("wrapper-split-text")
    rows = tuple(_snapshot_row(item) for item in rows_raw)
    result = CanonicalPresentation(
        schema,
        rows,
        _snapshot_text(schema_digest, "wrapper-schema-digest"),
        _snapshot_text(payload_digest, "wrapper-payload-digest"),
        _snapshot_text(boundary, "wrapper-split-boundary"),
    )
    logger.debug("_snapshot_canonical exit rows=%d", len(rows))
    return result


def _snapshot_row(value: RepresentationRow) -> RepresentationRow:
    """Capture one exact bounded row and preserve scalar runtime types."""
    logger.debug("_snapshot_row entry")
    identities = tuple(
        object.__getattribute__(value, name) for name in ("row_id", "source_id", "content_id", "group_id")
    )
    values_raw = object.__getattribute__(value, "values")
    target_raw = object.__getattribute__(value, "target")
    if any(type(item) is not str for item in identities) or type(values_raw) is not tuple:
        reject("wrapper-row-shape")
    if len(values_raw) > 32:
        reject("wrapper-row-width")
    detached_identities = tuple(_snapshot_text(item, "wrapper-row-identity") for item in identities)
    values = tuple(_snapshot_scalar(item) for item in values_raw)
    target = _snapshot_scalar(target_raw)
    result = RepresentationRow(
        detached_identities[0],
        detached_identities[1],
        detached_identities[2],
        detached_identities[3],
        values,
        target,
    )
    logger.debug("_snapshot_row exit values=%d", len(values))
    return result


def _snapshot_scalar(value: object) -> str | int | bool:
    """Detach one exact scalar without dynamic type metadata access."""
    logger.debug("_snapshot_scalar entry")
    if type(value) is str:
        result: str | int | bool = _snapshot_text(value, "wrapper-scalar")
    elif type(value) is int:
        if int.bit_length(value) > HARD_MAX_INTEGER_BITS:
            reject("wrapper-scalar-integer-limit")
        result = int(value)
    elif type(value) is bool:
        result = bool(value)
    else:
        reject("wrapper-scalar-type")
    logger.debug("_snapshot_scalar exit")
    return result


def _snapshot_text(value: object, reason: str) -> str:
    """Detach exact bounded UTF-8 text after a shallow character cap."""
    logger.debug("_snapshot_text entry code=%s", reason)
    if type(value) is not str:
        reject(f"{reason}-type")
    if len(value) > HARD_MAX_TEXT_BYTES:
        reject(f"{reason}-text-limit")
    try:
        encoded = value.encode("utf-8", errors="strict")
    except UnicodeError as exc:
        raise MissingDataProtocolError(f"{reason}-utf8") from exc
    if len(encoded) > HARD_MAX_TEXT_BYTES:
        reject(f"{reason}-text-limit")
    result = str(value)
    logger.debug("_snapshot_text exit bytes=%d", len(encoded))
    return result


def _snapshot_receipt(value: object) -> MissingnessReceipt:
    """Capture one exact receipt graph without retaining caller objects."""
    logger.debug("_snapshot_receipt entry")
    if type(value) is not MissingnessReceipt:
        reject("wrapper-receipt-type")
    wire_format = object.__getattribute__(value, "wire_format")
    authority = object.__getattribute__(value, "authority")
    if type(wire_format) is not MissingWireFormat or type(authority) is not MissingReplayAuthority:
        reject("wrapper-receipt-enum")
    text_names = (
        "schema_version",
        "base_schema_digest",
        "projected_schema_digest",
        "policy_digest",
        "protocol_digest",
        "nonclaims_digest",
        "receipt_digest",
        "boundary",
    )
    texts = tuple(object.__getattribute__(value, name) for name in text_names)
    if any(type(item) is not str for item in texts):
        reject("wrapper-receipt-text")
    splits = tuple(
        _snapshot_split_receipt(object.__getattribute__(value, name)) for name in ("train", "validation", "test")
    )
    detached_texts = tuple(_snapshot_text(item, "wrapper-receipt-text") for item in texts)
    result = MissingnessReceipt(
        detached_texts[0],
        wire_format,
        authority,
        detached_texts[1],
        detached_texts[2],
        detached_texts[3],
        splits[0],
        splits[1],
        splits[2],
        detached_texts[4],
        detached_texts[5],
        detached_texts[6],
        detached_texts[7],
    )
    logger.debug("_snapshot_receipt exit")
    return result


def _snapshot_split_receipt(value: object) -> MissingSplitReceipt:
    """Capture one exact split receipt without caller-owned references."""
    logger.debug("_snapshot_split_receipt entry")
    if type(value) is not MissingSplitReceipt:
        reject("wrapper-split-receipt-type")
    text_names = (
        "raw_digest",
        "semantic_mask_digest",
        "projection_digest",
        "output_payload_digest",
        "receipt_digest",
    )
    texts = tuple(object.__getattribute__(value, name) for name in text_names)
    row_count = object.__getattribute__(value, "row_count")
    if any(type(item) is not str for item in texts) or type(row_count) is not int:
        reject("wrapper-split-receipt-shape")
    detached_texts = tuple(_snapshot_text(item, "wrapper-split-receipt-text") for item in texts)
    result = MissingSplitReceipt(
        detached_texts[0],
        detached_texts[1],
        detached_texts[2],
        detached_texts[3],
        int(row_count),
        detached_texts[4],
    )
    logger.debug("_snapshot_split_receipt exit rows=%d", row_count)
    return result


def _split_receipt(
    raw: bytes,
    parsed: ParsedMissingSplit,
    output_payload_digest: str,
    policy_digest: str,
) -> MissingSplitReceipt:
    logger.debug("_split_receipt entry rows=%d bytes=%d", len(parsed.rows), len(raw))
    semantic = digest_data(
        {"policy_digest": policy_digest, "rows": list(parsed.semantic_mask_data)},
        SEMANTIC_MASK_DOMAIN,
    )
    projection = digest_data(
        {"policy_digest": policy_digest, "rows": list(parsed.projection_data)},
        PROJECTION_DOMAIN,
    )
    partial = MissingSplitReceipt(
        raw_split_digest(raw), semantic, projection, output_payload_digest, len(parsed.rows), ""
    )
    result = replace(
        partial, receipt_digest=digest_data(split_receipt_data(partial, include_digest=False), SPLIT_RECEIPT_DOMAIN)
    )
    logger.debug("_split_receipt exit")
    return result


def _top_receipt(
    wire_format: MissingWireFormat,
    authority: MissingReplayAuthority,
    policy: MissingDataPolicy,
    splits: tuple[MissingSplitReceipt, MissingSplitReceipt, MissingSplitReceipt],
    protocol_digest: str,
) -> MissingnessReceipt:
    if type(wire_format) is not MissingWireFormat or type(authority) is not MissingReplayAuthority:
        reject("receipt-enum-type")
    logger.debug("_top_receipt entry format=%s authority=%s", wire_format.value, authority.value)
    if type(splits) is not tuple or len(splits) != 3:
        reject("receipt-splits")
    for split in splits:
        _validate_split_receipt(split)
    _exact_digest(protocol_digest, "protocol-digest")
    nonclaims = digest_data({"boundary": MISSING_BOUNDARY, "nonclaims": list(MISSING_NONCLAIMS)}, NONCLAIMS_DOMAIN)
    partial = MissingnessReceipt(
        PRESENTATION_SCHEMA,
        wire_format,
        authority,
        policy.base_schema_digest,
        policy.projected_schema_digest,
        policy.policy_digest,
        *splits,
        protocol_digest,
        nonclaims,
        "",
        MISSING_BOUNDARY,
    )
    data = {
        "schema_version": partial.schema_version,
        "wire_format": partial.wire_format.value,
        "authority": partial.authority.value,
        "base_schema_digest": partial.base_schema_digest,
        "projected_schema_digest": partial.projected_schema_digest,
        "policy_digest": partial.policy_digest,
        "train": split_receipt_data(partial.train),
        "validation": split_receipt_data(partial.validation),
        "test": split_receipt_data(partial.test),
        "protocol_digest": partial.protocol_digest,
        "nonclaims_digest": partial.nonclaims_digest,
        "boundary": partial.boundary,
    }
    result = replace(partial, receipt_digest=digest_data(data, RECEIPT_DOMAIN))
    logger.debug("_top_receipt exit")
    return result


def _validate_split_receipt(value: object) -> None:
    logger.debug("_validate_split_receipt entry")
    if type(value) is not MissingSplitReceipt:
        reject("split-receipt-type")
    _exact_digest(value.raw_digest, "raw-digest")
    _exact_digest(value.semantic_mask_digest, "semantic-mask-digest")
    _exact_digest(value.projection_digest, "projection-digest")
    _exact_digest(value.output_payload_digest, "output-payload-digest")
    if type(value.row_count) is not int or type(value.row_count) is bool or not 1 <= value.row_count <= 8192:
        reject("split-row-count")
    expected = digest_data(split_receipt_data(value, include_digest=False), SPLIT_RECEIPT_DOMAIN)
    if value.receipt_digest != expected:
        reject("split-receipt-digest")
    logger.debug("_validate_split_receipt exit rows=%d", value.row_count)


def _exact_digest(value: object, reason: str) -> str:
    logger.debug("_exact_digest entry field=%s", reason)
    if type(value) is not str or len(value) != 64 or any(ch not in "0123456789abcdef" for ch in value):
        reject(reason)
    logger.debug("_exact_digest exit field=%s", reason)
    return value


def _row_count(value: MissingnessPresentation) -> int:
    logger.debug("_row_count entry")
    result = sum(
        len(item.rows) for item in (value.presentation.train, value.presentation.validation, value.presentation.test)
    )
    logger.debug("_row_count exit rows=%d", result)
    return result


def _safe_structural_shape(value: object) -> bool:
    """Reject hostile nested objects before equality, iteration, or lower replay."""
    logger.debug("_safe_structural_shape entry")
    if type(value) is not MissingnessPresentation or not _safe_shallow_text(value.boundary):
        logger.debug("_safe_structural_shape exit valid=false layer=wrapper")
        return False
    policy = value.policy
    if type(policy) is not MissingDataPolicy or any(
        not _safe_shallow_text(item)
        for item in (
            policy.schema_version,
            policy.base_schema_digest,
            policy.projected_schema_digest,
            policy.projection_spec_root,
            policy.policy_digest,
        )
    ):
        logger.debug("_safe_structural_shape exit valid=false layer=policy")
        return False
    rules = policy.rules
    if type(rules) is not tuple or len(rules) > 32:
        logger.debug("_safe_structural_shape exit valid=false layer=rules-cap")
        return False
    if not _safe_schema_shape(policy.base_schema) or not _safe_schema_shape(policy.projected_schema):
        return False
    if any(not _safe_rule_shape(item) for item in rules):
        return False
    if not _safe_three_way_shape(value.presentation):
        return False
    if not _safe_receipt_shape(value.receipt):
        return False
    logger.debug("_safe_structural_shape exit valid=true")
    return True


def _safe_schema_shape(value: object) -> bool:
    logger.debug("_safe_schema_shape entry")
    valid = (
        type(value) is RepresentationSchema
        and type(value.schema_id) is str
        and type(value.version) is str
        and type(value.fields) is tuple
        and 1 <= len(value.fields) <= 32
        and type(value.target_categories) is tuple
        and 2 <= len(value.target_categories) <= 128
        and all(
            type(field) is RepresentationField
            and type(field.name) is str
            and type(field.kind) is str
            and type(field.categories) is tuple
            and 2 <= len(field.categories) <= 128
            and all(_safe_scalar_shape(item) for item in field.categories)
            for field in value.fields
        )
        and all(_safe_scalar_shape(item) for item in value.target_categories)
    )
    logger.debug("_safe_schema_shape exit valid=%s", valid)
    return valid


def _safe_rule_shape(value: object) -> bool:
    logger.debug("_safe_rule_shape entry")
    valid = (
        type(value) is MissingFieldRule
        and type(value.field_name) is str
        and type(value.mode) is MissingPolicyMode
        and (value.fallback is None or _safe_scalar_shape(value.fallback))
        and (value.derived_name is None or type(value.derived_name) is str)
    )
    logger.debug("_safe_rule_shape exit valid=%s", valid)
    return valid


def _safe_three_way_shape(value: object) -> bool:
    logger.debug("_safe_three_way_shape entry")
    if type(value) is not ThreeWayPresentation:
        logger.debug("_safe_three_way_shape exit valid=false")
        return False
    splits = (value.train, value.validation, value.test)
    shallow: list[tuple[CanonicalPresentation, tuple[RepresentationRow, ...], tuple[RepresentationField, ...]]] = []
    for item in splits:
        if type(item) is not CanonicalPresentation:
            logger.debug("_safe_three_way_shape exit valid=false layer=splits")
            return False
        rows = item.rows
        schema = item.schema
        if type(rows) is not tuple or not 1 <= len(rows) <= 8192 or type(schema) is not RepresentationSchema:
            logger.debug("_safe_three_way_shape exit valid=false layer=splits")
            return False
        fields = schema.fields
        if type(fields) is not tuple or not 1 <= len(fields) <= 32:
            logger.debug("_safe_three_way_shape exit valid=false layer=fields")
            return False
        shallow.append((item, rows, fields))
    row_count = sum(len(rows) for _, rows, _ in shallow)
    if row_count > 24_576:
        logger.debug("_safe_three_way_shape exit valid=false layer=rows")
        return False
    nodes = 1_024 + sum(len(rows) * (8 + len(fields) * 3) for _, rows, fields in shallow)
    if nodes > 65_536:
        logger.debug("_safe_three_way_shape exit valid=false layer=nodes")
        return False
    valid = (
        type(value.protocol_digest) is str
        and type(value.boundary) is str
        and all(_safe_canonical_shape(item) for item, _, _ in shallow)
    )
    logger.debug("_safe_three_way_shape exit valid=%s", valid)
    return valid


def _safe_canonical_shape(value: object) -> bool:
    logger.debug("_safe_canonical_shape entry")
    valid = (
        type(value) is CanonicalPresentation
        and _safe_schema_shape(value.schema)
        and type(value.rows) is tuple
        and 1 <= len(value.rows) <= 8192
        and all(_safe_row_shape(item) for item in value.rows)
        and type(value.schema_digest) is str
        and type(value.payload_digest) is str
        and type(value.boundary) is str
    )
    logger.debug("_safe_canonical_shape exit valid=%s", valid)
    return valid


def _safe_row_shape(value: object) -> bool:
    logger.debug("_safe_row_shape entry")
    valid = (
        type(value) is RepresentationRow
        and all(type(item) is str for item in (value.row_id, value.source_id, value.content_id, value.group_id))
        and all(
            len(item) <= HARD_MAX_TEXT_BYTES
            for item in (value.row_id, value.source_id, value.content_id, value.group_id)
        )
        and type(value.values) is tuple
        and len(value.values) <= 32
        and all(_safe_scalar_shape(item) for item in value.values)
        and _safe_scalar_shape(value.target)
    )
    logger.debug("_safe_row_shape exit valid=%s", valid)
    return valid


def _safe_receipt_shape(value: object) -> bool:
    logger.debug("_safe_receipt_shape entry")
    valid = (
        type(value) is MissingnessReceipt
        and type(value.wire_format) is MissingWireFormat
        and type(value.authority) is MissingReplayAuthority
        and all(
            type(item) is str
            for item in (
                value.schema_version,
                value.base_schema_digest,
                value.projected_schema_digest,
                value.policy_digest,
                value.protocol_digest,
                value.nonclaims_digest,
                value.receipt_digest,
                value.boundary,
            )
        )
        and all(_safe_split_shape(item) for item in (value.train, value.validation, value.test))
    )
    logger.debug("_safe_receipt_shape exit valid=%s", valid)
    return valid


def _safe_split_shape(value: object) -> bool:
    logger.debug("_safe_split_shape entry")
    valid = (
        type(value) is MissingSplitReceipt
        and all(
            type(item) is str
            for item in (
                value.raw_digest,
                value.semantic_mask_digest,
                value.projection_digest,
                value.output_payload_digest,
                value.receipt_digest,
            )
        )
        and type(value.row_count) is int
    )
    logger.debug("_safe_split_shape exit valid=%s", valid)
    return valid


def _safe_scalar_shape(value: object) -> bool:
    """Apply exact scalar text/integer bounds before any detached copy."""
    logger.debug("_safe_scalar_shape entry")
    if type(value) is str:
        valid = len(value) <= HARD_MAX_TEXT_BYTES
    elif type(value) is int:
        valid = int.bit_length(value) <= HARD_MAX_INTEGER_BITS
    else:
        valid = type(value) is bool
    logger.debug("_safe_scalar_shape exit valid=%s", valid)
    return valid


def _safe_shallow_text(value: object) -> bool:
    """Bound exact UTF-8 text before any nested structural traversal."""
    logger.debug("_safe_shallow_text entry")
    if type(value) is not str or len(value) > HARD_MAX_TEXT_BYTES:
        valid = False
    else:
        try:
            valid = len(value.encode("utf-8", errors="strict")) <= HARD_MAX_TEXT_BYTES
        except UnicodeError:
            valid = False
    logger.debug("_safe_shallow_text exit valid=%s", valid)
    return valid


__all__ = (
    "external_binding",
    "missingness_from_csv",
    "missingness_from_jsonl",
    "replay_missingness_from_sources",
    "validate_native_missingness_presentation",
    "validate_structural_missingness_presentation",
)
