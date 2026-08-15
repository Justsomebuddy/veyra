"""Canonical categorical schemas and three-way discovery presentations."""

from __future__ import annotations

from collections import Counter, defaultdict
import logging
from typing import NoReturn

from .types import (
    HARD_MAX_CATEGORIES,
    HARD_MAX_FIELDS,
    HARD_MAX_INTEGER_BITS,
    HARD_MAX_ROWS_PER_PRESENTATION,
    HARD_MAX_TEXT_BYTES,
    HARD_MAX_TOTAL_CELLS,
    REPRESENTATION_BOUNDARY,
    SCHEMA_VERSION,
    THREE_WAY_VERSION,
    CanonicalPresentation,
    RepresentationField,
    RepresentationProtocolError,
    RepresentationRow,
    RepresentationScalar,
    RepresentationSchema,
    ThreeWayPresentation,
)
from ...proof_core_codec import digest_data

logger = logging.getLogger(__name__)


def canonical_representation_schema(schema: RepresentationSchema) -> RepresentationSchema:
    """Validate and detach one exact finite categorical schema."""
    logger.debug("canonical_representation_schema entry type=%s", type(schema).__name__)
    if type(schema) is not RepresentationSchema:
        _reject("invalid-schema", "immutable-schema-required")
    if schema.version != SCHEMA_VERSION:
        _reject("invalid-schema", "schema-version")
    if not _bounded_text(schema.schema_id):
        _reject("invalid-schema", "schema-id")
    if type(schema.fields) is not tuple or not 1 <= len(schema.fields) <= HARD_MAX_FIELDS:
        _reject("resource-limit", "schema-fields")
    fields = tuple(_canonical_field(field) for field in schema.fields)
    if len({field.name for field in fields}) != len(fields):
        _reject("invalid-schema", "duplicate-field-name")
    targets = _canonical_categories(schema.target_categories, "target", binary=False)
    result = RepresentationSchema(str(schema.schema_id), fields, targets, SCHEMA_VERSION)
    logger.debug("canonical_representation_schema exit fields=%d", len(result.fields))
    return result


def representation_schema_digest(schema: RepresentationSchema) -> str:
    """Return the domain-separated identity of one valid detached schema."""
    logger.debug("representation_schema_digest entry")
    canonical = canonical_representation_schema(schema)
    result = digest_data(_schema_data(canonical), SCHEMA_VERSION)
    logger.debug("representation_schema_digest exit")
    return result


def canonical_presentation(
    schema: RepresentationSchema,
    rows: tuple[RepresentationRow, ...],
) -> CanonicalPresentation:
    """Validate and detach one ordered finite presentation."""
    logger.debug("canonical_presentation entry rows_type=%s", type(rows).__name__)
    canonical_schema = canonical_representation_schema(schema)
    canonical_rows = _canonical_rows(canonical_schema, rows)
    schema_digest = digest_data(_schema_data(canonical_schema), SCHEMA_VERSION)
    payload_digest = digest_data(
        {
            "schema": schema_digest,
            "rows": [_row_data(row) for row in canonical_rows],
        },
        "veyra.observer-discovery.v3.presentation.v1",
    )
    result = CanonicalPresentation(
        canonical_schema,
        canonical_rows,
        schema_digest,
        payload_digest,
        REPRESENTATION_BOUNDARY,
    )
    logger.debug("canonical_presentation exit rows=%d", len(canonical_rows))
    return result


def validate_canonical_presentation(value: object) -> bool:
    """Recompute every canonical presentation field without trusting its roots."""
    logger.debug("validate_canonical_presentation entry type=%s", type(value).__name__)
    try:
        valid = (
            type(value) is CanonicalPresentation
            and value.boundary == REPRESENTATION_BOUNDARY
            and canonical_presentation(value.schema, value.rows) == value
        )
    except (RepresentationProtocolError, AttributeError, TypeError, ValueError, OverflowError):
        logger.error("validate_canonical_presentation malformed")
        valid = False
    logger.debug("validate_canonical_presentation exit valid=%s", valid)
    return valid


def canonical_three_way_presentation(
    train: CanonicalPresentation,
    validation: CanonicalPresentation,
    test: CanonicalPresentation,
) -> ThreeWayPresentation:
    """Bind caller-declared train, validation, and test presentations fail closed."""
    logger.debug("canonical_three_way_presentation entry")
    presentations = (train, validation, test)
    if any(not validate_canonical_presentation(item) for item in presentations):
        _reject("invalid-presentation", "canonical-input-required")
    if len({item.schema_digest for item in presentations}) != 1:
        _reject("schema-mismatch", "three-way-schema")
    total_cells = sum(len(item.rows) * len(item.schema.fields) for item in presentations)
    if total_cells > HARD_MAX_TOTAL_CELLS:
        _reject("resource-limit", "three-way-cells")
    _validate_three_way_lineage(presentations)
    protocol = digest_data(
        {
            "version": THREE_WAY_VERSION,
            "schema": train.schema_digest,
            "train": train.payload_digest,
            "validation": validation.payload_digest,
            "test": test.payload_digest,
            "boundary": REPRESENTATION_BOUNDARY,
        },
        THREE_WAY_VERSION,
    )
    result = ThreeWayPresentation(train, validation, test, protocol, REPRESENTATION_BOUNDARY)
    logger.debug("canonical_three_way_presentation exit")
    return result


def validate_three_way_presentation(value: object) -> bool:
    """Replay the complete three-way schema, data, and lineage contract."""
    logger.debug("validate_three_way_presentation entry type=%s", type(value).__name__)
    try:
        valid = (
            type(value) is ThreeWayPresentation
            and value.boundary == REPRESENTATION_BOUNDARY
            and canonical_three_way_presentation(value.train, value.validation, value.test) == value
        )
    except (RepresentationProtocolError, AttributeError, TypeError, ValueError, OverflowError):
        logger.error("validate_three_way_presentation malformed")
        valid = False
    logger.debug("validate_three_way_presentation exit valid=%s", valid)
    return valid


def _canonical_field(field: RepresentationField) -> RepresentationField:
    logger.debug("_canonical_field entry type=%s", type(field).__name__)
    if type(field) is not RepresentationField:
        _reject("invalid-schema", "immutable-field-required")
    if not _bounded_text(field.name):
        _reject("invalid-schema", "field-name")
    if field.kind not in {"binary", "categorical"}:
        _reject("invalid-schema", "field-kind")
    categories = _canonical_categories(field.categories, "field", binary=field.kind == "binary")
    result = RepresentationField(str(field.name), str(field.kind), categories)
    logger.debug("_canonical_field exit categories=%d", len(categories))
    return result


def _canonical_categories(
    categories: tuple[RepresentationScalar, ...],
    domain: str,
    *,
    binary: bool,
) -> tuple[RepresentationScalar, ...]:
    logger.debug("_canonical_categories entry domain=%s", domain)
    if type(categories) is not tuple or not 2 <= len(categories) <= HARD_MAX_CATEGORIES:
        _reject("resource-limit", f"{domain}-categories")
    result = tuple(_detached_scalar(value, f"{domain}-category") for value in categories)
    keys = tuple((type(value).__name__, value) for value in result)
    if len(set(keys)) != len(keys):
        _reject("invalid-schema", f"{domain}-duplicate-category")
    if binary and keys != (("int", 0), ("int", 1)):
        _reject("invalid-schema", "binary-domain-must-be-int-zero-one")
    logger.debug("_canonical_categories exit domain=%s count=%d", domain, len(result))
    return result


def _canonical_rows(
    schema: RepresentationSchema,
    rows: tuple[RepresentationRow, ...],
) -> tuple[RepresentationRow, ...]:
    logger.debug("_canonical_rows entry type=%s", type(rows).__name__)
    if type(rows) is not tuple or not 1 <= len(rows) <= HARD_MAX_ROWS_PER_PRESENTATION:
        _reject("resource-limit", "presentation-rows")
    if len(rows) * len(schema.fields) > HARD_MAX_TOTAL_CELLS:
        _reject("resource-limit", "presentation-cells")
    field_domains = tuple({(type(value).__name__, value) for value in field.categories} for field in schema.fields)
    target_domain = {(type(value).__name__, value) for value in schema.target_categories}
    result: list[RepresentationRow] = []
    group_targets: dict[str, set[tuple[str, object]]] = defaultdict(set)
    source_groups: dict[str, set[str]] = defaultdict(set)
    content_groups: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        if type(row) is not RepresentationRow:
            _reject("invalid-presentation", "immutable-row-required")
        identities = (row.row_id, row.source_id, row.content_id, row.group_id)
        if any(not _bounded_text(value) for value in identities):
            _reject("invalid-presentation", "row-identity")
        if type(row.values) is not tuple or len(row.values) != len(schema.fields):
            _reject("invalid-presentation", "row-width")
        values = tuple(_detached_scalar(value, "feature-value") for value in row.values)
        for index, value in enumerate(values):
            if (type(value).__name__, value) not in field_domains[index]:
                _reject("invalid-presentation", "feature-outside-domain")
        target = _detached_scalar(row.target, "target-value")
        target_key = (type(target).__name__, target)
        if target_key not in target_domain:
            _reject("invalid-presentation", "target-outside-domain")
        detached = RepresentationRow(*(str(value) for value in identities), values, target)
        result.append(detached)
        group_targets[detached.group_id].add(target_key)
        source_groups[detached.source_id].add(detached.group_id)
        content_groups[detached.content_id].add(detached.group_id)
    if len({row.row_id for row in result}) != len(result):
        _reject("invalid-presentation", "duplicate-row-id")
    if any(len(targets) != 1 for targets in group_targets.values()):
        _reject("invalid-presentation", "one-target-per-group-required")
    if len(group_targets) < 2:
        _reject("insufficient-calibration", "needs-two-groups")
    group_sizes = Counter(row.group_id for row in result)
    if len(set(group_sizes.values())) != 1:
        _reject("invalid-presentation", "unequal-group-sizes")
    if any(len(groups) != 1 for groups in (*source_groups.values(), *content_groups.values())):
        _reject("invalid-presentation", "lineage-crosses-groups")
    output = tuple(result)
    logger.debug("_canonical_rows exit rows=%d groups=%d", len(output), len(group_targets))
    return output


def _validate_three_way_lineage(
    presentations: tuple[CanonicalPresentation, CanonicalPresentation, CanonicalPresentation],
) -> None:
    logger.debug("_validate_three_way_lineage entry")
    for attribute in ("row_id", "source_id", "content_id", "group_id"):
        sets = tuple({getattr(row, attribute) for row in item.rows} for item in presentations)
        if any(sets[left] & sets[right] for left, right in ((0, 1), (0, 2), (1, 2))):
            _reject("split-leakage", f"three-way-{attribute}-overlap")
    logger.debug("_validate_three_way_lineage exit")


def _detached_scalar(value: object, domain: str) -> RepresentationScalar:
    logger.debug("_detached_scalar entry domain=%s type=%s", domain, type(value).__name__)
    if type(value) is str:
        try:
            byte_length = len(value.encode("utf-8")) if len(value) <= HARD_MAX_TEXT_BYTES else 0
        except UnicodeEncodeError:
            _reject("invalid-presentation", f"{domain}-string-encoding")
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
        _reject("invalid-presentation", f"{domain}-scalar")
    logger.debug("_detached_scalar exit domain=%s", domain)
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


def _schema_data(schema: RepresentationSchema) -> dict[str, object]:
    logger.debug("_schema_data entry fields=%d", len(schema.fields))
    result = {
        "version": schema.version,
        "schema_id": schema.schema_id,
        "fields": [
            {
                "name": field.name,
                "kind": field.kind,
                "categories": [_scalar_data(value) for value in field.categories],
            }
            for field in schema.fields
        ],
        "target_categories": [_scalar_data(value) for value in schema.target_categories],
    }
    logger.debug("_schema_data exit")
    return result


def _row_data(row: RepresentationRow) -> dict[str, object]:
    logger.debug("_row_data entry")
    result = {
        "row_id": row.row_id,
        "source_id": row.source_id,
        "content_id": row.content_id,
        "group_id": row.group_id,
        "values": [_scalar_data(value) for value in row.values],
        "target": _scalar_data(row.target),
    }
    logger.debug("_row_data exit")
    return result


def _scalar_data(value: RepresentationScalar) -> dict[str, object]:
    logger.debug("_scalar_data entry type=%s", type(value).__name__)
    result = {"type": type(value).__name__, "value": value}
    logger.debug("_scalar_data exit")
    return result


def _reject(reason: str, detail: str) -> NoReturn:
    logger.error("representation rejected reason=%s detail=%s", reason, detail)
    raise RepresentationProtocolError(reason, detail)
