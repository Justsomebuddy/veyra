"""Parse explicit missing markers from bounded CSV/JSONL source bytes."""

from __future__ import annotations

from dataclasses import dataclass
import csv
import json
import logging
import re
from typing import NoReturn

from ..ingestion.types import HARD_MAX_RECORD_BYTES, IDENTITY_COLUMNS, TARGET_COLUMN
from ..schema import RepresentationRow, RepresentationSchema
from ..schema.types import HARD_MAX_INTEGER_BITS, HARD_MAX_ROWS_PER_PRESENTATION, RepresentationScalar
from .digest import scalar_data
from .errors import MissingDataProtocolError, reject
from .resources import MissingParseBudget
from .types import MissingDataPolicy, MissingPolicyMode, MissingWireFormat

logger = logging.getLogger(__name__)

_CANONICAL_DECIMAL = re.compile(r"(?:0|-[1-9][0-9]*|[1-9][0-9]*)\Z")
_MAX_DECIMAL_DIGITS = 78


@dataclass(frozen=True, slots=True)
class ParsedMissingSplit:
    """Projected rows plus exact ordered semantic/mask digest material."""

    rows: tuple[RepresentationRow, ...]
    semantic_mask_data: tuple[dict[str, object], ...]
    projection_data: tuple[dict[str, object], ...]


class _BoundedPhysicalBytes:
    def __init__(self, raw: bytes) -> None:
        logger.debug("missing physical bytes entry bytes=%d", len(raw))
        self._raw = raw
        self._index = 0

    def __iter__(self) -> _BoundedPhysicalBytes:
        logger.debug("missing physical __iter__ entry")
        logger.debug("missing physical __iter__ exit")
        return self

    def __next__(self) -> bytes:
        logger.debug("missing physical __next__ entry index=%d", self._index)
        if self._index >= len(self._raw):
            logger.debug("missing physical __next__ exit eof=true")
            raise StopIteration
        start = self._index
        search_end = min(len(self._raw), start + HARD_MAX_RECORD_BYTES + 1)
        lf = self._raw.find(b"\n", start, search_end)
        cr = self._raw.find(b"\r", start, search_end)
        endings = tuple(item for item in (lf, cr) if item >= 0)
        if endings:
            separator = min(endings)
            end = separator + 1
            if self._raw[separator] == 13 and end < len(self._raw) and self._raw[end] == 10:
                end += 1
        else:
            end = len(self._raw)
        if end - start > HARD_MAX_RECORD_BYTES:
            reject("physical-record-limit")
        self._index = end
        result = self._raw[start:end]
        logger.debug("missing physical __next__ exit bytes=%d", len(result))
        return result


class _BoundedCsvLines:
    def __init__(self, raw: bytes) -> None:
        logger.debug("missing csv lines entry bytes=%d", len(raw))
        self._physical = _BoundedPhysicalBytes(raw)
        self._logical_bytes = 0
        logger.debug("missing csv lines exit")

    def __iter__(self) -> _BoundedCsvLines:
        logger.debug("missing csv lines __iter__ entry")
        logger.debug("missing csv lines __iter__ exit")
        return self

    def __next__(self) -> str:
        logger.debug("missing csv lines __next__ entry")
        line = next(self._physical)
        self._logical_bytes += len(line)
        if self._logical_bytes > HARD_MAX_RECORD_BYTES:
            reject("logical-record-limit")
        try:
            result = line.decode("utf-8", errors="strict")
        except UnicodeError as exc:
            raise MissingDataProtocolError("source-utf8") from exc
        logger.debug("missing csv lines __next__ exit bytes=%d", len(line))
        return result

    def reset(self) -> None:
        logger.debug("missing csv lines reset entry")
        self._logical_bytes = 0
        logger.debug("missing csv lines reset exit")


def parse_missing_split(
    raw: bytes,
    base_schema: RepresentationSchema,
    policy: MissingDataPolicy,
    wire_format: MissingWireFormat,
    budget: MissingParseBudget,
) -> ParsedMissingSplit:
    """Parse one split using only this sibling's explicit grammar."""
    logger.debug("parse_missing_split entry format=%s bytes=%d", wire_format.value, len(raw))
    if wire_format is MissingWireFormat.CSV:
        result = _parse_csv(raw, base_schema, policy, budget)
    elif wire_format is MissingWireFormat.JSONL:
        result = _parse_jsonl(raw, base_schema, policy, budget)
    else:
        reject("wire-format")
    logger.debug("parse_missing_split exit format=%s rows=%d", wire_format.value, len(result.rows))
    return result


def _parse_csv(
    raw: bytes,
    schema: RepresentationSchema,
    policy: MissingDataPolicy,
    budget: MissingParseBudget,
) -> ParsedMissingSplit:
    """Parse one bounded CSV split."""
    source = _BoundedCsvLines(raw)
    reader = csv.reader(source, delimiter=",", quotechar='"', doublequote=True, strict=True)
    expected = (*IDENTITY_COLUMNS, *(field.name for field in schema.fields), TARGET_COLUMN)
    try:
        header = next(reader)
        source.reset()
    except StopIteration:
        reject("csv-header-missing")
    except csv.Error as exc:
        raise MissingDataProtocolError("csv-syntax") from exc
    if tuple(header) != expected:
        reject("csv-header")
    output: list[tuple[RepresentationRow, dict[str, object], dict[str, object]]] = []
    try:
        for record in reader:
            source.reset()
            if len(output) >= HARD_MAX_ROWS_PER_PRESENTATION:
                reject("row-limit")
            if len(record) != len(expected):
                reject("csv-row-width")
            identities = tuple(record[: len(IDENTITY_COLUMNS)])
            if any(item == "m:" for item in identities):
                reject("identity-missing")
            cells: list[RepresentationScalar | None] = []
            for index, cell in enumerate(record[len(IDENTITY_COLUMNS) : -1]):
                if cell == "m:":
                    if policy.rules[index].mode is not MissingPolicyMode.EXPLICIT_MASK:
                        reject("required-feature-missing")
                    cells.append(None)
                else:
                    cells.append(_tagged_scalar(cell))
            if record[-1] == "m:":
                reject("target-missing")
            target = _tagged_scalar(record[-1])
            output.append(_project_row(identities, tuple(cells), target, policy, budget))
    except csv.Error as exc:
        raise MissingDataProtocolError("csv-syntax") from exc
    result = _finish(output)
    logger.debug("_parse_csv exit rows=%d", len(result.rows))
    return result


def _parse_jsonl(
    raw: bytes,
    schema: RepresentationSchema,
    policy: MissingDataPolicy,
    budget: MissingParseBudget,
) -> ParsedMissingSplit:
    logger.debug("_parse_jsonl entry bytes=%d", len(raw))
    expected = (*IDENTITY_COLUMNS, *(field.name for field in schema.fields), TARGET_COLUMN)
    output: list[tuple[RepresentationRow, dict[str, object], dict[str, object]]] = []
    for line in _BoundedPhysicalBytes(raw):
        content = _strip_ending(line)
        if not content:
            reject("jsonl-blank-record")
        if len(output) >= HARD_MAX_ROWS_PER_PRESENTATION:
            reject("row-limit")
        try:
            decoded = json.loads(
                content.decode("utf-8", errors="strict"),
                object_pairs_hook=_unique_object,
                parse_int=_bounded_integer,
                parse_float=_reject_float,
                parse_constant=_reject_constant,
            )
        except MissingDataProtocolError:
            raise
        except UnicodeError as exc:
            raise MissingDataProtocolError("source-utf8") from exc
        except (json.JSONDecodeError, RecursionError, ValueError) as exc:
            raise MissingDataProtocolError("json-syntax") from exc
        if type(decoded) is not dict or tuple(decoded) != expected:
            reject("json-keys")
        identities_raw = tuple(decoded[name] for name in IDENTITY_COLUMNS)
        if any(type(item) is not str for item in identities_raw):
            reject("identity-type")
        cells: list[RepresentationScalar | None] = []
        for index, field in enumerate(schema.fields):
            cell = decoded[field.name]
            if cell is None:
                if policy.rules[index].mode is not MissingPolicyMode.EXPLICIT_MASK:
                    reject("required-feature-missing")
                cells.append(None)
            else:
                cells.append(_native_scalar(cell, "feature-type"))
        if decoded[TARGET_COLUMN] is None:
            reject("target-missing")
        target = _native_scalar(decoded[TARGET_COLUMN], "target-type")
        output.append(_project_row(identities_raw, tuple(cells), target, policy, budget))
    result = _finish(output)
    logger.debug("_parse_jsonl exit rows=%d", len(result.rows))
    return result


def _project_row(
    identities: tuple[str, ...],
    cells: tuple[RepresentationScalar | None, ...],
    target: RepresentationScalar,
    policy: MissingDataPolicy,
    budget: MissingParseBudget,
) -> tuple[RepresentationRow, dict[str, object], dict[str, object]]:
    logger.debug("_project_row entry fields=%d", len(cells))
    values: list[RepresentationScalar] = []
    semantic: list[object] = []
    mask: list[int] = []
    for cell, rule in zip(cells, policy.rules, strict=True):
        if cell is None:
            values.extend((rule.fallback, 0))  # type: ignore[arg-type]
            semantic.append({"missing": True})
            mask.append(0)
        else:
            values.append(cell)
            semantic.append({"missing": False, "scalar": scalar_data(cell)})
            mask.append(1)
            if rule.mode is MissingPolicyMode.EXPLICIT_MASK:
                values.append(1)
    row = RepresentationRow(identities[0], identities[1], identities[2], identities[3], tuple(values), target)
    budget.charge(identities, cells, tuple(values), target, policy.rules)
    semantic_data = {
        "identities": list(identities),
        "features": semantic,
        "missing_mask": mask,
        "target": scalar_data(target),
    }
    projection_data: dict[str, object] = {
        "row_id": identities[0],
        "assigned_values": [scalar_data(item) for item in values],
    }
    logger.debug("_project_row exit projected_fields=%d", len(values))
    return row, semantic_data, projection_data


def _finish(
    output: list[tuple[RepresentationRow, dict[str, object], dict[str, object]]],
) -> ParsedMissingSplit:
    logger.debug("_finish entry rows=%d", len(output))
    if not output:
        reject("split-empty")
    rows, semantic, projection = zip(*output, strict=True)
    result = ParsedMissingSplit(tuple(rows), tuple(semantic), tuple(projection))
    logger.debug("_finish exit rows=%d", len(result.rows))
    return result


def _tagged_scalar(cell: str) -> RepresentationScalar:
    logger.debug("_tagged_scalar entry bytes=%d", len(cell.encode("utf-8")))
    if cell.startswith("s:"):
        result: RepresentationScalar = cell[2:]
    elif cell.startswith("i:"):
        lexeme = cell[2:]
        if len(lexeme) > _MAX_DECIMAL_DIGITS + 1 or _CANONICAL_DECIMAL.fullmatch(lexeme) is None:
            reject("csv-integer")
        result = int(lexeme)
        if result.bit_length() > HARD_MAX_INTEGER_BITS:
            reject("integer-limit")
    elif cell == "b:true":
        result = True
    elif cell == "b:false":
        result = False
    else:
        reject("csv-scalar-tag")
    logger.debug("_tagged_scalar exit")
    return result


def _native_scalar(value: object, reason: str) -> RepresentationScalar:
    logger.debug("_native_scalar entry")
    if type(value) is not str and type(value) is not int and type(value) is not bool:
        reject(reason)
    result: RepresentationScalar = value
    logger.debug("_native_scalar exit")
    return result


def _bounded_integer(lexeme: str) -> int:
    logger.debug("_bounded_integer entry digits=%d", len(lexeme))
    if len(lexeme) > _MAX_DECIMAL_DIGITS + 1:
        reject("integer-limit")
    result = int(lexeme)
    if result.bit_length() > HARD_MAX_INTEGER_BITS:
        reject("integer-limit")
    logger.debug("_bounded_integer exit bits=%d", result.bit_length())
    return result


def _reject_float(_lexeme: str) -> NoReturn:
    logger.error("_reject_float error reason=json-float")
    reject("json-float")


def _reject_constant(_lexeme: str) -> NoReturn:
    logger.error("_reject_constant error reason=json-constant")
    reject("json-constant")


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    logger.debug("_unique_object entry pairs=%d", len(pairs))
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            reject("json-duplicate-key")
        result[key] = value
    logger.debug("_unique_object exit keys=%d", len(result))
    return result


def _strip_ending(line: bytes) -> bytes:
    logger.debug("_strip_ending entry bytes=%d", len(line))
    if line.endswith(b"\r\n"):
        result = line[:-2]
    elif line.endswith((b"\r", b"\n")):
        result = line[:-1]
    else:
        result = line
    logger.debug("_strip_ending exit bytes=%d", len(result))
    return result


__all__ = ("ParsedMissingSplit", "parse_missing_split")
