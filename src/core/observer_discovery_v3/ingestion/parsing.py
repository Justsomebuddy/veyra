"""Strict bounded parsers for categorical CSV and JSONL byte payloads."""

from __future__ import annotations

import csv
import json
import logging
import re
from typing import NoReturn

from ..schema import RepresentationProtocolError, RepresentationRow, RepresentationSchema
from ..schema.types import HARD_MAX_INTEGER_BITS, HARD_MAX_ROWS_PER_PRESENTATION
from .types import (
    HARD_MAX_RECORD_BYTES,
    HARD_MAX_SPLIT_BYTES,
    IDENTITY_COLUMNS,
    RESERVED_COLUMNS,
    TARGET_COLUMN,
)

logger = logging.getLogger(__name__)

_CANONICAL_DECIMAL = re.compile(r"(?:0|-[1-9][0-9]*|[1-9][0-9]*)\Z")
_MAX_DECIMAL_DIGITS = 78  # 256-bit values have at most 78 decimal digits.


class _BoundedPhysicalBytes:
    """Lazily yield one bounded LF, CRLF, or CR-terminated physical line."""

    def __init__(self, raw: bytes) -> None:
        logger.debug("_BoundedPhysicalBytes entry bytes=%d", len(raw))
        self._raw = raw
        self._index = 0
        logger.debug("_BoundedPhysicalBytes exit")

    def __iter__(self) -> _BoundedPhysicalBytes:
        logger.debug("_BoundedPhysicalBytes.__iter__ entry")
        logger.debug("_BoundedPhysicalBytes.__iter__ exit")
        return self

    def __next__(self) -> bytes:
        logger.debug("_BoundedPhysicalBytes.__next__ entry index=%d", self._index)
        if self._index >= len(self._raw):
            logger.debug("_BoundedPhysicalBytes.__next__ exit eof=true")
            raise StopIteration
        start = self._index
        search_end = min(len(self._raw), start + HARD_MAX_RECORD_BYTES + 1)
        lf = self._raw.find(b"\n", start, search_end)
        cr = self._raw.find(b"\r", start, search_end)
        separators = tuple(index for index in (lf, cr) if index >= 0)
        if separators:
            separator = min(separators)
            end = separator + 1
            if self._raw[separator] == 13 and end < len(self._raw) and self._raw[end] == 10:
                end += 1
        else:
            end = len(self._raw)
        if end - start > HARD_MAX_RECORD_BYTES:
            _reject("resource-limit", "ingestion-physical-record")
        self._index = end
        result = self._raw[start:end]
        logger.debug("_BoundedPhysicalBytes.__next__ exit bytes=%d", len(result))
        return result


class _BoundedCsvLines:
    """Yield decoded physical lines while precharging each logical CSV record."""

    def __init__(self, raw: bytes) -> None:
        logger.debug("_BoundedCsvLines entry bytes=%d", len(raw))
        self._physical = _BoundedPhysicalBytes(raw)
        self._logical_bytes = 0
        logger.debug("_BoundedCsvLines exit")

    def __iter__(self) -> _BoundedCsvLines:
        logger.debug("_BoundedCsvLines.__iter__ entry")
        logger.debug("_BoundedCsvLines.__iter__ exit")
        return self

    def __next__(self) -> str:
        logger.debug("_BoundedCsvLines.__next__ entry")
        raw_line = next(self._physical)
        self._logical_bytes += len(raw_line)
        if self._logical_bytes > HARD_MAX_RECORD_BYTES:
            _reject("resource-limit", "ingestion-logical-record")
        try:
            result = raw_line.decode("utf-8", errors="strict")
        except UnicodeDecodeError:
            _reject("invalid-ingestion", "utf8")
        logger.debug("_BoundedCsvLines.__next__ exit bytes=%d", len(raw_line))
        return result

    def reset_logical_record(self) -> None:
        logger.debug("_BoundedCsvLines.reset_logical_record entry")
        self._logical_bytes = 0
        logger.debug("_BoundedCsvLines.reset_logical_record exit")


def expected_columns(schema: RepresentationSchema) -> tuple[str, ...]:
    """Return the one exact record shape admitted by the adapter."""
    logger.debug("expected_columns entry fields=%d", len(schema.fields))
    if any(field.name in RESERVED_COLUMNS for field in schema.fields):
        _reject("invalid-ingestion-schema", "reserved-field-name")
    result = (*IDENTITY_COLUMNS, *(field.name for field in schema.fields), TARGET_COLUMN)
    logger.debug("expected_columns exit columns=%d", len(result))
    return result


def parse_csv_rows(payload: bytes, schema: RepresentationSchema) -> tuple[RepresentationRow, ...]:
    """Parse one strict tagged CSV split without inferring any field semantics."""
    logger.debug("parse_csv_rows entry payload_type=%s", type(payload).__name__)
    raw = _validated_payload(payload)
    source = _BoundedCsvLines(raw)
    reader = csv.reader(source, delimiter=",", quotechar='"', doublequote=True, strict=True)
    expected = expected_columns(schema)
    try:
        header = next(reader)
        source.reset_logical_record()
    except StopIteration:
        _reject("invalid-ingestion", "csv-header-missing")
    except csv.Error:
        _reject("invalid-ingestion", "csv-syntax")
    if tuple(header) != expected:
        _reject("invalid-ingestion", "csv-header")

    rows: list[RepresentationRow] = []
    try:
        for record in reader:
            source.reset_logical_record()
            if len(rows) >= HARD_MAX_ROWS_PER_PRESENTATION:
                _reject("resource-limit", "ingestion-rows")
            if len(record) != len(expected):
                _reject("invalid-ingestion", "csv-row-width")
            rows.append(_csv_row(record, len(schema.fields)))
    except csv.Error:
        _reject("invalid-ingestion", "csv-syntax")
    if not rows:
        _reject("invalid-ingestion", "split-empty")
    result = tuple(rows)
    logger.debug("parse_csv_rows exit rows=%d", len(result))
    return result


def parse_jsonl_rows(payload: bytes, schema: RepresentationSchema) -> tuple[RepresentationRow, ...]:
    """Parse one strict native-scalar JSONL split without inference or repair."""
    logger.debug("parse_jsonl_rows entry payload_type=%s", type(payload).__name__)
    raw = _validated_payload(payload)
    expected = expected_columns(schema)
    rows: list[RepresentationRow] = []
    for line in _BoundedPhysicalBytes(raw):
        content = _without_line_ending(line)
        if not content:
            _reject("invalid-ingestion", "jsonl-blank-record")
        if len(rows) >= HARD_MAX_ROWS_PER_PRESENTATION:
            _reject("resource-limit", "ingestion-rows")
        try:
            text = content.decode("utf-8", errors="strict")
            value = json.loads(
                text,
                object_pairs_hook=_unique_object,
                parse_int=_bounded_json_integer,
                parse_float=_reject_json_float,
                parse_constant=_reject_json_constant,
            )
        except UnicodeDecodeError:
            _reject("invalid-ingestion", "utf8")
        except (json.JSONDecodeError, RecursionError):
            _reject("invalid-ingestion", "json-syntax")
        if type(value) is not dict:
            _reject("invalid-ingestion", "json-object-required")
        if tuple(value) != expected:
            _reject("invalid-ingestion", "json-keys")
        rows.append(_json_row(value, schema))
    if not rows:
        _reject("invalid-ingestion", "split-empty")
    result = tuple(rows)
    logger.debug("parse_jsonl_rows exit rows=%d", len(result))
    return result


def _validated_payload(payload: bytes) -> bytes:
    logger.debug("_validated_payload entry payload_type=%s", type(payload).__name__)
    if type(payload) is not bytes:
        _reject("invalid-ingestion", "bytes-required")
    if not payload:
        _reject("invalid-ingestion", "split-empty")
    if len(payload) > HARD_MAX_SPLIT_BYTES:
        _reject("resource-limit", "ingestion-split-bytes")
    if payload.startswith(b"\xef\xbb\xbf"):
        _reject("invalid-ingestion", "bom")
    if b"\x00" in payload:
        _reject("invalid-ingestion", "nul")
    try:
        payload.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        _reject("invalid-ingestion", "utf8")
    logger.debug("_validated_payload exit bytes=%d", len(payload))
    return payload


def _csv_row(record: list[str], field_count: int) -> RepresentationRow:
    logger.debug("_csv_row entry columns=%d", len(record))
    identities = tuple(record[: len(IDENTITY_COLUMNS)])
    values = tuple(_tagged_scalar(cell) for cell in record[len(IDENTITY_COLUMNS) : -1])
    if len(values) != field_count:
        _reject("invalid-ingestion", "csv-row-width")
    target = _tagged_scalar(record[-1])
    result = RepresentationRow(*identities, values, target)
    logger.debug("_csv_row exit fields=%d", len(values))
    return result


def _tagged_scalar(cell: str) -> str | int | bool:
    logger.debug("_tagged_scalar entry bytes=%d", len(cell.encode("utf-8")))
    if cell.startswith("s:"):
        result: str | int | bool = cell[2:]
    elif cell.startswith("i:"):
        lexeme = cell[2:]
        if len(lexeme) > _MAX_DECIMAL_DIGITS + 1 or _CANONICAL_DECIMAL.fullmatch(lexeme) is None:
            _reject("invalid-ingestion", "csv-integer")
        result = int(lexeme)
        if result.bit_length() > HARD_MAX_INTEGER_BITS:
            _reject("resource-limit", "ingestion-integer")
    elif cell == "b:true":
        result = True
    elif cell == "b:false":
        result = False
    else:
        _reject("invalid-ingestion", "csv-scalar-tag")
    logger.debug("_tagged_scalar exit type=%s", type(result).__name__)
    return result


def _without_line_ending(line: bytes) -> bytes:
    logger.debug("_without_line_ending entry bytes=%d", len(line))
    if line.endswith(b"\r\n"):
        result = line[:-2]
    elif line.endswith((b"\r", b"\n")):
        result = line[:-1]
    else:
        result = line
    logger.debug("_without_line_ending exit bytes=%d", len(result))
    return result


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    logger.debug("_unique_object entry pairs=%d", len(pairs))
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            _reject("invalid-ingestion", "json-duplicate-key")
        result[key] = value
    logger.debug("_unique_object exit keys=%d", len(result))
    return result


def _bounded_json_integer(lexeme: str) -> int:
    logger.debug("_bounded_json_integer entry digits=%d", len(lexeme))
    if len(lexeme) > _MAX_DECIMAL_DIGITS + 1:
        _reject("resource-limit", "ingestion-integer")
    result = int(lexeme)
    if result.bit_length() > HARD_MAX_INTEGER_BITS:
        _reject("resource-limit", "ingestion-integer")
    logger.debug("_bounded_json_integer exit bits=%d", result.bit_length())
    return result


def _reject_json_float(_lexeme: str) -> NoReturn:
    logger.error("_reject_json_float error code=json-float")
    _reject("invalid-ingestion", "json-float")


def _reject_json_constant(_lexeme: str) -> NoReturn:
    logger.error("_reject_json_constant error code=json-constant")
    _reject("invalid-ingestion", "json-constant")


def _json_row(value: dict[str, object], schema: RepresentationSchema) -> RepresentationRow:
    logger.debug("_json_row entry keys=%d", len(value))
    identities = tuple(value[name] for name in IDENTITY_COLUMNS)
    if any(type(identity) is not str for identity in identities):
        _reject("invalid-ingestion", "json-identity")
    values = tuple(_native_scalar(value[field.name]) for field in schema.fields)
    target = _native_scalar(value[TARGET_COLUMN])
    result = RepresentationRow(*identities, values, target)  # type: ignore[arg-type]
    logger.debug("_json_row exit fields=%d", len(values))
    return result


def _native_scalar(value: object) -> str | int | bool:
    logger.debug("_native_scalar entry type=%s", type(value).__name__)
    if type(value) not in {str, int, bool}:
        _reject("invalid-ingestion", "json-scalar")
    result: str | int | bool = value  # type: ignore[assignment]
    logger.debug("_native_scalar exit type=%s", type(result).__name__)
    return result


def _reject(reason: str, detail: str) -> NoReturn:
    logger.error("categorical ingestion rejected reason=%s detail=%s", reason, detail)
    raise RepresentationProtocolError(reason, detail)
