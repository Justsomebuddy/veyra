"""Bounded canonical JSON codec with authority-preserving decode separation."""

from __future__ import annotations

import json
import logging
from typing import NoReturn, cast

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
from ..schema.types import RepresentationScalar
from .digest import exact_data_equal, missingness_data, rule_data, scalar_data, schema_data, split_receipt_data
from .errors import MissingDataProtocolError, reject
from .policy import canonical_missing_data_policy
from .resources import MAX_CODEC_BYTES, MAX_WRAPPER_NODES
from .runtime import (
    _snapshot_retained_missingness_presentation,
    _validate_detached_missingness_presentation,
    _validate_retained_missingness_presentation,
    replay_missingness_from_sources,
)
from .types import (
    MISSING_BOUNDARY,
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

_TOP_FIELDS = ("boundary", "policy", "presentation", "receipt")


def missingness_presentation_json(value: MissingnessPresentation) -> str:
    """Encode a structurally valid external wrapper canonically."""
    logger.debug("missingness_presentation_json entry")
    captured = _snapshot_retained_missingness_presentation(value)
    if not _validate_detached_missingness_presentation(captured, allow_native=False):
        reject("codec-value-invalid")
    result = _canonical_json(_wrapper_data(captured))
    logger.debug("missingness_presentation_json exit bytes=%d", len(result))
    return result


def native_missingness_presentation_json(
    value: MissingnessPresentation,
    policy: MissingDataPolicy,
    base_schema: RepresentationSchema,
    projected_schema: RepresentationSchema,
    *,
    wire_format: MissingWireFormat,
    train: bytes,
    validation: bytes,
    test: bytes,
) -> str:
    """Encode native authority only after complete fresh source-backed replay."""
    logger.debug("native_missingness_presentation_json entry")
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
    if not exact_data_equal(missingness_data(captured), missingness_data(expected)):
        reject("codec-native-not-authoritative")
    result = _canonical_json(_wrapper_data(expected))
    logger.debug("native_missingness_presentation_json exit bytes=%d", len(result))
    return result


def missingness_presentation_from_json(payload: object) -> MissingnessPresentation:
    """Structurally decode only an EXTERNAL_BINDING_ONLY wrapper."""
    logger.debug("missingness_presentation_from_json entry")
    result = _decode_wrapper(payload, allow_native=False)
    logger.debug("missingness_presentation_from_json exit authority=%s", result.receipt.authority.value)
    return result


def native_missingness_presentation_from_json(
    payload: object,
    policy: MissingDataPolicy,
    base_schema: RepresentationSchema,
    projected_schema: RepresentationSchema,
    *,
    wire_format: MissingWireFormat,
    train: bytes,
    validation: bytes,
    test: bytes,
) -> MissingnessPresentation:
    """Decode native bytes only by equality with complete fresh source replay."""
    logger.debug("native_missingness_presentation_from_json entry")
    decoded = _decode_wrapper(payload, allow_native=True)
    expected = replay_missingness_from_sources(
        policy,
        base_schema,
        projected_schema,
        wire_format=wire_format,
        train=train,
        validation=validation,
        test=test,
    )
    if not exact_data_equal(missingness_data(decoded), missingness_data(expected)):
        reject("codec-native-authority-mismatch")
    logger.debug("native_missingness_presentation_from_json exit authority=%s", expected.receipt.authority.value)
    return expected


def _wrapper_data(value: MissingnessPresentation) -> dict[str, object]:
    logger.debug("_wrapper_data entry")
    result: dict[str, object] = {
        "boundary": value.boundary,
        "policy": _policy_data(value.policy),
        "presentation": _presentation_data(value),
        "receipt": _receipt_data(value.receipt),
    }
    logger.debug("_wrapper_data exit")
    return result


def _policy_data(value: MissingDataPolicy) -> dict[str, object]:
    logger.debug("_policy_data entry rules=%d", len(value.rules))
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
    logger.debug("_policy_data exit")
    return result


def _presentation_data(value: MissingnessPresentation) -> dict[str, object]:
    logger.debug("_presentation_data entry")
    presentation = value.presentation
    result: dict[str, object] = {
        "train": _canonical_presentation_data(presentation.train),
        "validation": _canonical_presentation_data(presentation.validation),
        "test": _canonical_presentation_data(presentation.test),
        "protocol_digest": presentation.protocol_digest,
        "boundary": presentation.boundary,
    }
    logger.debug("_presentation_data exit")
    return result


def _canonical_presentation_data(value: CanonicalPresentation) -> dict[str, object]:
    logger.debug("_canonical_presentation_data entry rows=%d", len(value.rows))
    result: dict[str, object] = {
        "schema_digest": value.schema_digest,
        "rows": [_row_data(item) for item in value.rows],
        "payload_digest": value.payload_digest,
        "boundary": value.boundary,
    }
    logger.debug("_canonical_presentation_data exit")
    return result


def _row_data(value: RepresentationRow) -> dict[str, object]:
    logger.debug("_row_data entry values=%d", len(value.values))
    result: dict[str, object] = {
        "row_id": value.row_id,
        "source_id": value.source_id,
        "content_id": value.content_id,
        "group_id": value.group_id,
        "values": [scalar_data(item) for item in value.values],
        "target": scalar_data(value.target),
    }
    logger.debug("_row_data exit")
    return result


def _receipt_data(value: MissingnessReceipt) -> dict[str, object]:
    logger.debug("_receipt_data entry authority=%s", value.authority.value)
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
    logger.debug("_receipt_data exit")
    return result


def _canonical_json(value: object) -> str:
    logger.debug("missing codec canonical-json entry")
    encoder = json.JSONEncoder(sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)
    chunks: list[str] = []
    total = 0
    for chunk in encoder.iterencode(value):
        total += len(chunk)
        if total > MAX_CODEC_BYTES:
            reject("codec-byte-limit")
        chunks.append(chunk)
    result = "".join(chunks)
    logger.debug("missing codec canonical-json exit bytes=%d", total)
    return result


def _decode_wrapper(payload: object, *, allow_native: bool) -> MissingnessPresentation:
    logger.debug("_decode_wrapper entry allow_native=%s", allow_native)
    text, decoded = _decode_payload(payload)
    top = _exact_object(decoded, _TOP_FIELDS, "codec-top-fields")
    if top["boundary"] != MISSING_BOUNDARY:
        reject("codec-boundary")
    policy = _decode_policy(top["policy"])
    presentation = _decode_presentation(top["presentation"], policy.projected_schema)
    receipt = _decode_receipt(top["receipt"])
    if receipt.authority is MissingReplayAuthority.NATIVE_POLICY_REPLAY and not allow_native:
        reject("codec-native-requires-source-replay")
    result = MissingnessPresentation(policy, presentation, receipt, MISSING_BOUNDARY)
    if not _validate_retained_missingness_presentation(result, allow_native=allow_native):
        reject("codec-structure-invalid")
    if text != _canonical_json(_wrapper_data(result)):
        reject("codec-noncanonical")
    logger.debug("_decode_wrapper exit authority=%s", result.receipt.authority.value)
    return result


def _decode_policy(value: object) -> MissingDataPolicy:
    logger.debug("_decode_policy entry")
    row = _exact_object(
        value,
        (
            "schema_version",
            "base_schema",
            "base_schema_digest",
            "projected_schema",
            "projected_schema_digest",
            "rules",
            "projection_spec_root",
            "policy_digest",
        ),
        "codec-policy-fields",
    )
    rules_raw = _exact_list(row["rules"], "codec-rules", maximum=32)
    base = _decode_schema(row["base_schema"])
    projected = _decode_schema(row["projected_schema"])
    rules = tuple(_decode_rule(item) for item in rules_raw)
    expected = canonical_missing_data_policy(base, projected, rules)
    if row != _policy_data(expected):
        reject("codec-policy-mismatch")
    logger.debug("_decode_policy exit rules=%d", len(expected.rules))
    return expected


def _decode_schema(value: object) -> RepresentationSchema:
    logger.debug("_decode_schema entry")
    row = _exact_object(value, ("version", "schema_id", "fields", "target_categories"), "codec-schema-fields")
    fields_raw = _exact_list(row["fields"], "codec-fields", minimum=1, maximum=32)
    targets_raw = _exact_list(row["target_categories"], "codec-targets", minimum=2, maximum=128)
    fields = tuple(_decode_field(item) for item in fields_raw)
    targets = tuple(_decode_scalar(item) for item in targets_raw)
    if type(row["version"]) is not str or type(row["schema_id"]) is not str:
        reject("codec-schema-text")
    result = RepresentationSchema(row["schema_id"], fields, targets, row["version"])
    logger.debug("_decode_schema exit fields=%d", len(fields))
    return result


def _decode_field(value: object) -> RepresentationField:
    logger.debug("_decode_field entry")
    row = _exact_object(value, ("name", "kind", "categories"), "codec-field-fields")
    if type(row["name"]) is not str or type(row["kind"]) is not str:
        reject("codec-field-text")
    categories = tuple(
        _decode_scalar(item) for item in _exact_list(row["categories"], "codec-categories", minimum=2, maximum=128)
    )
    result = RepresentationField(row["name"], row["kind"], categories)
    logger.debug("_decode_field exit categories=%d", len(categories))
    return result


def _decode_rule(value: object) -> MissingFieldRule:
    logger.debug("_decode_rule entry")
    row = _exact_object(value, ("field_name", "mode", "fallback", "derived_name"), "codec-rule-fields")
    if type(row["field_name"]) is not str or type(row["mode"]) is not str:
        reject("codec-rule-text")
    if row["derived_name"] is not None and type(row["derived_name"]) is not str:
        reject("codec-rule-derived")
    try:
        mode = MissingPolicyMode(row["mode"])
    except ValueError as exc:
        raise MissingDataProtocolError("codec-rule-mode") from exc
    fallback = None if row["fallback"] is None else _decode_scalar(row["fallback"])
    result = MissingFieldRule(row["field_name"], mode, fallback, row["derived_name"])
    logger.debug("_decode_rule exit mode=%s", mode.value)
    return result


def _decode_presentation(value: object, schema: RepresentationSchema) -> ThreeWayPresentation:
    logger.debug("_decode_presentation entry")
    row = _exact_object(
        value, ("train", "validation", "test", "protocol_digest", "boundary"), "codec-presentation-fields"
    )
    total_rows = 0
    for name in ("train", "validation", "test"):
        split = _exact_object(row[name], ("schema_digest", "rows", "payload_digest", "boundary"), "codec-split-fields")
        total_rows += len(_exact_list(split["rows"], "codec-rows", minimum=1, maximum=8192))
    if total_rows > 24_576:
        reject("codec-total-rows-limit")
    splits = tuple(_decode_canonical_presentation(row[name], schema) for name in ("train", "validation", "test"))
    try:
        expected = canonical_three_way_presentation(*splits)
    except RepresentationProtocolError as exc:
        raise MissingDataProtocolError("codec-presentation-invalid") from exc
    if row != {
        "train": _canonical_presentation_data(expected.train),
        "validation": _canonical_presentation_data(expected.validation),
        "test": _canonical_presentation_data(expected.test),
        "protocol_digest": expected.protocol_digest,
        "boundary": expected.boundary,
    }:
        reject("codec-presentation-mismatch")
    logger.debug("_decode_presentation exit")
    return expected


def _decode_canonical_presentation(value: object, schema: RepresentationSchema) -> CanonicalPresentation:
    logger.debug("_decode_canonical_presentation entry")
    row = _exact_object(value, ("schema_digest", "rows", "payload_digest", "boundary"), "codec-split-fields")
    rows = tuple(_decode_row(item) for item in _exact_list(row["rows"], "codec-rows", minimum=1, maximum=8192))
    try:
        expected = canonical_presentation(schema, rows)
    except RepresentationProtocolError as exc:
        raise MissingDataProtocolError("codec-split-invalid") from exc
    if row != _canonical_presentation_data(expected):
        reject("codec-split-mismatch")
    logger.debug("_decode_canonical_presentation exit rows=%d", len(expected.rows))
    return expected


def _decode_row(value: object) -> RepresentationRow:
    logger.debug("_decode_row entry")
    row = _exact_object(
        value,
        ("row_id", "source_id", "content_id", "group_id", "values", "target"),
        "codec-row-fields",
    )
    identities = tuple(row[name] for name in ("row_id", "source_id", "content_id", "group_id"))
    if any(type(item) is not str for item in identities):
        reject("codec-row-identity")
    values = tuple(_decode_scalar(item) for item in _exact_list(row["values"], "codec-row-values", maximum=32))
    result = RepresentationRow(
        cast(str, identities[0]),
        cast(str, identities[1]),
        cast(str, identities[2]),
        cast(str, identities[3]),
        values,
        _decode_scalar(row["target"]),
    )
    logger.debug("_decode_row exit values=%d", len(values))
    return result


def _decode_scalar(value: object) -> RepresentationScalar:
    logger.debug("_decode_scalar entry")
    row = _exact_object(value, ("type", "value"), "codec-scalar-fields")
    kind = row["type"]
    scalar = row["value"]
    if kind == "str" and type(scalar) is str:
        result: RepresentationScalar = scalar
    elif kind == "int" and type(scalar) is int:
        result = scalar
    elif kind == "bool" and type(scalar) is bool:
        result = scalar
    else:
        reject("codec-scalar-type")
    logger.debug("_decode_scalar exit")
    return result


def _decode_receipt(value: object) -> MissingnessReceipt:
    logger.debug("_decode_receipt entry")
    fields = (
        "schema_version",
        "wire_format",
        "authority",
        "base_schema_digest",
        "projected_schema_digest",
        "policy_digest",
        "train",
        "validation",
        "test",
        "protocol_digest",
        "nonclaims_digest",
        "receipt_digest",
        "boundary",
    )
    row = _exact_object(value, fields, "codec-receipt-fields")
    try:
        wire_format = MissingWireFormat(row["wire_format"])
        authority = MissingReplayAuthority(row["authority"])
    except (TypeError, ValueError) as exc:
        raise MissingDataProtocolError("codec-receipt-enum") from exc
    text_fields = (
        "schema_version",
        "base_schema_digest",
        "projected_schema_digest",
        "policy_digest",
        "protocol_digest",
        "nonclaims_digest",
        "receipt_digest",
        "boundary",
    )
    if any(type(row[name]) is not str for name in text_fields):
        reject("codec-receipt-text")
    result = MissingnessReceipt(
        cast(str, row["schema_version"]),
        wire_format,
        authority,
        cast(str, row["base_schema_digest"]),
        cast(str, row["projected_schema_digest"]),
        cast(str, row["policy_digest"]),
        _decode_split_receipt(row["train"]),
        _decode_split_receipt(row["validation"]),
        _decode_split_receipt(row["test"]),
        cast(str, row["protocol_digest"]),
        cast(str, row["nonclaims_digest"]),
        cast(str, row["receipt_digest"]),
        cast(str, row["boundary"]),
    )
    logger.debug("_decode_receipt exit authority=%s", result.authority.value)
    return result


def _decode_split_receipt(value: object) -> MissingSplitReceipt:
    logger.debug("_decode_split_receipt entry")
    row = _exact_object(
        value,
        (
            "raw_digest",
            "semantic_mask_digest",
            "projection_digest",
            "output_payload_digest",
            "row_count",
            "receipt_digest",
        ),
        "codec-split-receipt-fields",
    )
    digest_fields = (
        "raw_digest",
        "semantic_mask_digest",
        "projection_digest",
        "output_payload_digest",
        "receipt_digest",
    )
    if any(type(row[name]) is not str for name in digest_fields) or type(row["row_count"]) is not int:
        reject("codec-split-receipt-types")
    result = MissingSplitReceipt(
        cast(str, row["raw_digest"]),
        cast(str, row["semantic_mask_digest"]),
        cast(str, row["projection_digest"]),
        cast(str, row["output_payload_digest"]),
        row["row_count"],
        cast(str, row["receipt_digest"]),
    )
    logger.debug("_decode_split_receipt exit rows=%d", result.row_count)
    return result


def _decode_payload(payload: object) -> tuple[str, object]:
    logger.debug("missing codec decode external-call json")
    if type(payload) is not bytes and type(payload) is not str:
        reject("codec-payload-type")
    if len(payload) > MAX_CODEC_BYTES:
        reject("codec-byte-limit")
    if type(payload) is bytes:
        encoded = payload
        try:
            text = payload.decode("utf-8", errors="strict")
        except UnicodeError as exc:
            raise MissingDataProtocolError("codec-utf8") from exc
    elif type(payload) is str:
        try:
            encoded = payload.encode("utf-8", errors="strict")
        except UnicodeError as exc:
            raise MissingDataProtocolError("codec-utf8") from exc
        text = payload
    if len(encoded) > MAX_CODEC_BYTES:
        reject("codec-byte-limit")
    _preflight_json(text)
    try:
        decoded = json.loads(
            text,
            object_pairs_hook=_unique_object,
            parse_int=_bounded_json_integer,
            parse_float=_reject_json_float,
            parse_constant=_reject_json_constant,
        )
    except MissingDataProtocolError:
        raise
    except (json.JSONDecodeError, RecursionError, UnicodeError, ValueError) as exc:
        raise MissingDataProtocolError("codec-syntax") from exc
    return text, decoded


def _preflight_json(text: str) -> None:
    logger.debug("_preflight_json entry bytes=%d", len(text))
    nodes = 0
    depth = 0
    in_string = False
    escaped = False
    for char in text:
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
            nodes += 1
        elif char in "[{":
            nodes += 1
            depth += 1
            if depth > 128:
                reject("codec-depth-limit")
        elif char in "]}":
            depth -= 1
            if depth < 0:
                reject("codec-syntax")
        elif char in "-0123456789tfn":
            nodes += 1
        if nodes > MAX_WRAPPER_NODES:
            reject("codec-node-limit")
    logger.debug("_preflight_json exit nodes=%d depth=%d", nodes, depth)


def _bounded_json_integer(lexeme: str) -> int:
    logger.debug("_bounded_json_integer entry digits=%d", len(lexeme))
    if len(lexeme) > 79:
        reject("codec-integer-limit")
    result = int(lexeme)
    if result.bit_length() > 256:
        reject("codec-integer-limit")
    logger.debug("_bounded_json_integer exit bits=%d", result.bit_length())
    return result


def _reject_json_float(_value: str) -> NoReturn:
    logger.error("_reject_json_float error reason=codec-float")
    reject("codec-float")


def _reject_json_constant(_value: str) -> NoReturn:
    logger.error("_reject_json_constant error reason=codec-constant")
    reject("codec-constant")


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    logger.debug("codec _unique_object entry pairs=%d", len(pairs))
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            reject("codec-duplicate-key")
        result[key] = value
    logger.debug("codec _unique_object exit keys=%d", len(result))
    return result


def _exact_object(value: object, fields: tuple[str, ...], reason: str) -> dict[str, object]:
    logger.debug("_exact_object entry code=%s", reason)
    if type(value) is not dict or tuple(value) != tuple(sorted(fields)):
        reject(reason)
    logger.debug("_exact_object exit reason=%s", reason)
    return value


def _exact_list(
    value: object,
    reason: str,
    *,
    minimum: int = 0,
    maximum: int,
) -> list[object]:
    logger.debug("_exact_list entry code=%s", reason)
    if type(value) is not list:
        reject(reason)
    if not minimum <= len(value) <= maximum:
        reject(f"{reason}-limit")
    logger.debug("_exact_list exit reason=%s rows=%d", reason, len(value))
    return value


__all__ = (
    "missingness_presentation_from_json",
    "missingness_presentation_json",
    "native_missingness_presentation_from_json",
    "native_missingness_presentation_json",
)
