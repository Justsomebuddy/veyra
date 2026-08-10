"""Bounded bijective representation transports with exact round-trip receipts."""

from __future__ import annotations

import logging
from typing import NoReturn

from ..schema.canonical import (
    canonical_presentation,
    validate_canonical_presentation,
)
from ..schema.types import (
    HARD_MAX_INTEGER_BITS,
    HARD_MAX_TEXT_BYTES,
    CanonicalPresentation,
    RepresentationField,
    RepresentationProtocolError,
    RepresentationRow,
    RepresentationScalar,
    RepresentationSchema,
)
from .types import (
    HARD_MAX_OBSTRUCTIONS,
    TRANSPORT_APPLIED,
    TRANSPORT_BLOCKED,
    TRANSPORT_BOUNDARY,
    TRANSPORT_VERSION,
    CategoryBijection,
    RepresentationObstruction,
    RepresentationTransportReceipt,
    RepresentationTransportResult,
    RepresentationTransportSpec,
)
from ...proof_core_codec import digest_data

logger = logging.getLogger(__name__)


def apply_representation_transport(
    source: CanonicalPresentation,
    spec: RepresentationTransportSpec,
) -> RepresentationTransportResult:
    """Apply one exact finite bijection or return a terminal blocked result."""
    logger.debug("apply_representation_transport entry source_type=%s", type(source).__name__)
    try:
        if not validate_canonical_presentation(source):
            _reject("invalid-presentation", "canonical-source-required")
        canonical_spec = _canonical_transport_spec(source, spec)
        destination = _apply_validated_transport(source, canonical_spec)
        inverse = _inverse_transport_spec(source, destination, canonical_spec)
        restored = _apply_validated_transport(destination, _canonical_transport_spec(destination, inverse))
        if restored != source:
            _reject("transport-failure", "roundtrip-mismatch")
        lineage_preserved = _lineage(source) == _lineage(destination)
        if not lineage_preserved:
            _reject("transport-failure", "lineage-mismatch")
        spec_digest = digest_data(_spec_data(canonical_spec), TRANSPORT_VERSION)
        receipt = _bind_receipt(
            RepresentationTransportReceipt(
                canonical_spec.transport_id,
                source.schema_digest,
                source.payload_digest,
                destination.schema_digest,
                destination.payload_digest,
                spec_digest,
                len(source.rows),
                len(source.schema.fields),
                True,
                True,
                "",
                TRANSPORT_BOUNDARY,
            )
        )
        result = RepresentationTransportResult(
            TRANSPORT_APPLIED,
            destination,
            receipt,
            (),
            TRANSPORT_BOUNDARY,
        )
    except RepresentationProtocolError as exc:
        logger.error("apply_representation_transport blocked reason=%s detail=%s", exc.reason, exc.detail)
        result = _blocked(exc.reason, exc.detail)
    except (AttributeError, TypeError, ValueError, OverflowError) as exc:
        logger.error("apply_representation_transport malformed type=%s", type(exc).__name__)
        result = _blocked("invalid-transport", f"malformed-{type(exc).__name__}")
    logger.debug("apply_representation_transport exit status=%s", result.status)
    return result


def validate_representation_transport_result(
    result: object,
    source: CanonicalPresentation,
    spec: RepresentationTransportSpec,
) -> bool:
    """Replay a transport and require byte-for-byte equivalent terminal evidence."""
    logger.debug("validate_representation_transport_result entry type=%s", type(result).__name__)
    try:
        if (
            type(result) is not RepresentationTransportResult
            or result.status not in {TRANSPORT_APPLIED, TRANSPORT_BLOCKED}
            or result.boundary != TRANSPORT_BOUNDARY
            or type(result.obstructions) is not tuple
            or len(result.obstructions) > HARD_MAX_OBSTRUCTIONS
            or any(type(row) is not RepresentationObstruction for row in result.obstructions)
        ):
            logger.error("validate_representation_transport_result invalid shape")
            return False
        expected = apply_representation_transport(source, spec)
        valid = result == expected
        if result.status == TRANSPORT_APPLIED:
            valid = (
                valid
                and result.destination is not None
                and result.receipt is not None
                and not result.obstructions
                and _receipt_valid(result.receipt)
            )
        else:
            valid = valid and result.destination is None and result.receipt is None and bool(result.obstructions)
    except (AttributeError, TypeError, ValueError, OverflowError, RepresentationProtocolError):
        logger.error("validate_representation_transport_result malformed")
        valid = False
    logger.debug("validate_representation_transport_result exit valid=%s", valid)
    return valid


def _canonical_transport_spec(
    source: CanonicalPresentation,
    spec: RepresentationTransportSpec,
) -> RepresentationTransportSpec:
    logger.debug("_canonical_transport_spec entry type=%s", type(spec).__name__)
    if type(spec) is not RepresentationTransportSpec:
        _reject("invalid-transport", "immutable-spec-required")
    if spec.version != TRANSPORT_VERSION:
        _reject("invalid-transport", "transport-version")
    if not _bounded_text(spec.transport_id) or not _bounded_text(spec.destination_schema_id):
        _reject("invalid-transport", "transport-identity")
    if spec.source_schema_digest != source.schema_digest or spec.source_payload_digest != source.payload_digest:
        _reject("transport-transplant", "source-root-mismatch")
    if not _is_digest(spec.source_schema_digest) or not _is_digest(spec.source_payload_digest):
        _reject("invalid-transport", "source-digest")
    row_count = len(source.rows)
    field_count = len(source.schema.fields)
    row_order = _canonical_permutation(spec.row_order, row_count, "row-order")
    field_order = _canonical_permutation(spec.field_order, field_count, "field-order")
    if (
        type(spec.destination_field_names) is not tuple
        or len(spec.destination_field_names) != field_count
        or any(not _bounded_text(name) for name in spec.destination_field_names)
        or len(set(spec.destination_field_names)) != field_count
    ):
        _reject("invalid-transport", "destination-field-names")
    if type(spec.category_bijections) is not tuple or len(spec.category_bijections) != field_count:
        _reject("invalid-transport", "category-bijections")
    bijections = []
    for destination_index, source_index in enumerate(field_order):
        field = source.schema.fields[source_index]
        bijections.append(
            _canonical_bijection(
                spec.category_bijections[destination_index],
                field.categories,
                binary=field.kind == "binary",
                domain="field-bijection",
            )
        )
    target = _canonical_bijection(
        spec.target_bijection,
        source.schema.target_categories,
        binary=False,
        domain="target-bijection",
    )
    result = RepresentationTransportSpec(
        str(spec.transport_id),
        str(spec.source_schema_digest),
        str(spec.source_payload_digest),
        str(spec.destination_schema_id),
        row_order,
        field_order,
        tuple(str(name) for name in spec.destination_field_names),
        tuple(bijections),
        target,
        TRANSPORT_VERSION,
    )
    logger.debug("_canonical_transport_spec exit rows=%d fields=%d", row_count, field_count)
    return result


def _canonical_permutation(value: tuple[int, ...], size: int, domain: str) -> tuple[int, ...]:
    logger.debug("_canonical_permutation entry domain=%s size=%d", domain, size)
    if (
        type(value) is not tuple
        or len(value) != size
        or any(type(index) is not int for index in value)
        or set(value) != set(range(size))
    ):
        _reject("invalid-transport", domain)
    result = tuple(int(index) for index in value)
    logger.debug("_canonical_permutation exit domain=%s", domain)
    return result


def _canonical_bijection(
    value: CategoryBijection,
    source_categories: tuple[RepresentationScalar, ...],
    *,
    binary: bool,
    domain: str,
) -> CategoryBijection:
    logger.debug("_canonical_bijection entry domain=%s", domain)
    if type(value) is not CategoryBijection or type(value.entries) is not tuple:
        _reject("invalid-transport", domain)
    if len(value.entries) != len(source_categories):
        _reject("invalid-transport", f"{domain}-domain-size")
    entries = []
    for index, pair in enumerate(value.entries):
        if type(pair) is not tuple or len(pair) != 2:
            _reject("invalid-transport", f"{domain}-entry")
        left = _transport_scalar(pair[0], f"{domain}-source")
        right = _transport_scalar(pair[1], f"{domain}-destination")
        if _scalar_key(left) != _scalar_key(source_categories[index]):
            _reject("invalid-transport", f"{domain}-source-order")
        entries.append((left, right))
    destination_keys = tuple(_scalar_key(right) for _, right in entries)
    if len(set(destination_keys)) != len(destination_keys):
        _reject("invalid-transport", f"{domain}-not-injective")
    if binary and set(destination_keys) != {("int", 0), ("int", 1)}:
        _reject("invalid-transport", f"{domain}-binary-codomain")
    result = CategoryBijection(tuple(entries))
    logger.debug("_canonical_bijection exit domain=%s entries=%d", domain, len(entries))
    return result


def _apply_validated_transport(
    source: CanonicalPresentation,
    spec: RepresentationTransportSpec,
) -> CanonicalPresentation:
    logger.debug("_apply_validated_transport entry rows=%d", len(source.rows))
    fields = []
    maps = []
    for destination_index, source_index in enumerate(spec.field_order):
        source_field = source.schema.fields[source_index]
        entries = spec.category_bijections[destination_index].entries
        mapping = {_scalar_key(left): right for left, right in entries}
        maps.append(mapping)
        categories = (0, 1) if source_field.kind == "binary" else tuple(right for _, right in entries)
        fields.append(
            RepresentationField(
                spec.destination_field_names[destination_index],
                source_field.kind,
                categories,
            )
        )
    target_map = {_scalar_key(left): right for left, right in spec.target_bijection.entries}
    target_categories = tuple(right for _, right in spec.target_bijection.entries)
    schema = RepresentationSchema(spec.destination_schema_id, tuple(fields), target_categories)
    rows = []
    for source_row_index in spec.row_order:
        source_row = source.rows[source_row_index]
        values = tuple(
            maps[destination_index][_scalar_key(source_row.values[source_index])]
            for destination_index, source_index in enumerate(spec.field_order)
        )
        rows.append(
            RepresentationRow(
                source_row.row_id,
                source_row.source_id,
                source_row.content_id,
                source_row.group_id,
                values,
                target_map[_scalar_key(source_row.target)],
            )
        )
    result = canonical_presentation(schema, tuple(rows))
    logger.debug("_apply_validated_transport exit digest=%s", result.payload_digest[:12])
    return result


def _inverse_transport_spec(
    original: CanonicalPresentation,
    destination: CanonicalPresentation,
    spec: RepresentationTransportSpec,
) -> RepresentationTransportSpec:
    logger.debug("_inverse_transport_spec entry")
    inverse_rows = _inverse_permutation(spec.row_order)
    inverse_fields = _inverse_permutation(spec.field_order)
    bijections = []
    for original_index, destination_source_index in enumerate(inverse_fields):
        forward = spec.category_bijections[destination_source_index].entries
        inverse_map = {_scalar_key(right): left for left, right in forward}
        current_categories = destination.schema.fields[destination_source_index].categories
        bijections.append(
            CategoryBijection(tuple((category, inverse_map[_scalar_key(category)]) for category in current_categories))
        )
    target_inverse = {_scalar_key(right): left for left, right in spec.target_bijection.entries}
    target = CategoryBijection(
        tuple((category, target_inverse[_scalar_key(category)]) for category in destination.schema.target_categories)
    )
    result = RepresentationTransportSpec(
        f"inverse:{digest_data({'transport_id': spec.transport_id}, TRANSPORT_VERSION)[:32]}",
        destination.schema_digest,
        destination.payload_digest,
        original.schema.schema_id,
        inverse_rows,
        inverse_fields,
        tuple(field.name for field in original.schema.fields),
        tuple(bijections),
        target,
        TRANSPORT_VERSION,
    )
    logger.debug("_inverse_transport_spec exit")
    return result


def _inverse_permutation(permutation: tuple[int, ...]) -> tuple[int, ...]:
    logger.debug("_inverse_permutation entry size=%d", len(permutation))
    inverse = [0] * len(permutation)
    for destination_index, source_index in enumerate(permutation):
        inverse[source_index] = destination_index
    result = tuple(inverse)
    logger.debug("_inverse_permutation exit size=%d", len(result))
    return result


def _lineage(presentation: CanonicalPresentation) -> frozenset[tuple[str, str, str, str]]:
    logger.debug("_lineage entry rows=%d", len(presentation.rows))
    result = frozenset((row.row_id, row.source_id, row.content_id, row.group_id) for row in presentation.rows)
    logger.debug("_lineage exit rows=%d", len(result))
    return result


def _bind_receipt(receipt: RepresentationTransportReceipt) -> RepresentationTransportReceipt:
    logger.debug("_bind_receipt entry")
    from dataclasses import replace

    blank = replace(receipt, receipt_digest="")
    digest = digest_data(
        _receipt_data(blank),
        "veyra.observer-discovery.v3.transport-receipt.v1",
    )
    result = replace(blank, receipt_digest=digest)
    logger.debug("_bind_receipt exit digest=%s", digest[:12])
    return result


def _receipt_valid(receipt: RepresentationTransportReceipt) -> bool:
    logger.debug("_receipt_valid entry type=%s", type(receipt).__name__)
    if type(receipt) is not RepresentationTransportReceipt:
        logger.error("_receipt_valid invalid type")
        return False
    from dataclasses import replace

    valid = (
        receipt.boundary == TRANSPORT_BOUNDARY
        and all(
            _is_digest(value)
            for value in (
                receipt.source_schema_digest,
                receipt.source_payload_digest,
                receipt.destination_schema_digest,
                receipt.destination_payload_digest,
                receipt.spec_digest,
                receipt.receipt_digest,
            )
        )
        and type(receipt.row_count) is int
        and receipt.row_count > 0
        and type(receipt.field_count) is int
        and receipt.field_count > 0
        and receipt.lineage_preserved is True
        and receipt.roundtrip_verified is True
        and _bind_receipt(replace(receipt, receipt_digest="")) == receipt
    )
    logger.debug("_receipt_valid exit valid=%s", valid)
    return valid


def _spec_data(spec: RepresentationTransportSpec) -> dict[str, object]:
    logger.debug("_spec_data entry")
    result = {
        "version": spec.version,
        "transport_id": spec.transport_id,
        "source_schema": spec.source_schema_digest,
        "source_payload": spec.source_payload_digest,
        "destination_schema_id": spec.destination_schema_id,
        "row_order": list(spec.row_order),
        "field_order": list(spec.field_order),
        "destination_field_names": list(spec.destination_field_names),
        "category_bijections": [_bijection_data(row) for row in spec.category_bijections],
        "target_bijection": _bijection_data(spec.target_bijection),
    }
    logger.debug("_spec_data exit")
    return result


def _bijection_data(value: CategoryBijection) -> list[dict[str, object]]:
    logger.debug("_bijection_data entry entries=%d", len(value.entries))
    result = [{"source": _scalar_data(left), "destination": _scalar_data(right)} for left, right in value.entries]
    logger.debug("_bijection_data exit entries=%d", len(result))
    return result


def _receipt_data(receipt: RepresentationTransportReceipt) -> dict[str, object]:
    logger.debug("_receipt_data entry")
    result = {
        "transport_id": receipt.transport_id,
        "source_schema": receipt.source_schema_digest,
        "source_payload": receipt.source_payload_digest,
        "destination_schema": receipt.destination_schema_digest,
        "destination_payload": receipt.destination_payload_digest,
        "spec": receipt.spec_digest,
        "row_count": receipt.row_count,
        "field_count": receipt.field_count,
        "lineage_preserved": receipt.lineage_preserved,
        "roundtrip_verified": receipt.roundtrip_verified,
        "boundary": receipt.boundary,
    }
    logger.debug("_receipt_data exit")
    return result


def _scalar_data(value: RepresentationScalar) -> dict[str, object]:
    logger.debug("_scalar_data entry type=%s", type(value).__name__)
    result = {"type": type(value).__name__, "value": value}
    logger.debug("_scalar_data exit")
    return result


def _scalar_key(value: RepresentationScalar) -> tuple[str, object]:
    logger.debug("_scalar_key entry type=%s", type(value).__name__)
    result = (type(value).__name__, value)
    logger.debug("_scalar_key exit")
    return result


def _transport_scalar(value: object, domain: str) -> RepresentationScalar:
    logger.debug("_transport_scalar entry domain=%s type=%s", domain, type(value).__name__)
    if type(value) is str:
        try:
            byte_length = len(value.encode("utf-8")) if len(value) <= HARD_MAX_TEXT_BYTES else 0
        except UnicodeEncodeError:
            _reject("invalid-transport", f"{domain}-string-encoding")
        if len(value) > HARD_MAX_TEXT_BYTES or byte_length > HARD_MAX_TEXT_BYTES:
            _reject("resource-limit", f"{domain}-string")
        result: RepresentationScalar = str(value)
    elif type(value) is int:
        if value.bit_length() > HARD_MAX_INTEGER_BITS:
            _reject("resource-limit", f"{domain}-integer")
        result = int(value)
    elif type(value) is bool:
        result = bool(value)
    else:
        _reject("invalid-transport", f"{domain}-scalar")
    logger.debug("_transport_scalar exit domain=%s", domain)
    return result


def _bounded_text(value: object) -> bool:
    logger.debug("_bounded_text entry type=%s", type(value).__name__)
    try:
        byte_length = len(value.encode("utf-8")) if type(value) is str and len(value) <= HARD_MAX_TEXT_BYTES else 0
    except UnicodeEncodeError:
        logger.error("_bounded_text invalid utf8")
        byte_length = HARD_MAX_TEXT_BYTES + 1
    result = (
        type(value) is str and bool(value) and len(value) <= HARD_MAX_TEXT_BYTES and byte_length <= HARD_MAX_TEXT_BYTES
    )
    logger.debug("_bounded_text exit valid=%s", result)
    return result


def _is_digest(value: object) -> bool:
    logger.debug("_is_digest entry type=%s", type(value).__name__)
    result = type(value) is str and len(value) == 64 and all(character in "0123456789abcdef" for character in value)
    logger.debug("_is_digest exit valid=%s", result)
    return result


def _blocked(reason: str, detail: str) -> RepresentationTransportResult:
    logger.debug("_blocked entry reason=%s detail=%s", reason, detail)
    result = RepresentationTransportResult(
        TRANSPORT_BLOCKED,
        None,
        None,
        (RepresentationObstruction(reason, detail),),
        TRANSPORT_BOUNDARY,
    )
    logger.debug("_blocked exit")
    return result


def _reject(reason: str, detail: str) -> NoReturn:
    logger.error("transport rejected reason=%s detail=%s", reason, detail)
    raise RepresentationProtocolError(reason, detail)
