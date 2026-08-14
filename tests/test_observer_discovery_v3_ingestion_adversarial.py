"""Hostile input and resource coverage for strict v3 categorical ingestion."""

from __future__ import annotations

import inspect
import json
import logging

import pytest

from src.core.observer_discovery_v3.ingestion import (
    categorical_three_way_from_csv,
    categorical_three_way_from_jsonl,
)
from src.core.observer_discovery_v3.ingestion import parsing
from src.core.observer_discovery_v3.schema import (
    RepresentationField,
    RepresentationProtocolError,
    RepresentationSchema,
)

logger = logging.getLogger(__name__)

HEADER = b"row_id,source_id,content_id,group_id,value,target\n"
CSV_ROWS = b"r1,s1,c1,g1,s:a,s:yes\nr2,s2,c2,g2,s:b,s:no\n"


def _schema(field_name: str = "value") -> RepresentationSchema:
    logger.debug("_schema entry")
    result = RepresentationSchema(
        "hostile-v1",
        (RepresentationField(field_name, "categorical", ("a", "b")),),
        ("yes", "no"),
    )
    logger.debug("_schema exit")
    return result


def _valid_csv(prefix: str) -> bytes:
    logger.debug("_valid_csv entry")
    result = (
        HEADER
        + (
            f"{prefix}r1,{prefix}s1,{prefix}c1,{prefix}g1,s:a,s:yes\n"
            f"{prefix}r2,{prefix}s2,{prefix}c2,{prefix}g2,s:b,s:no\n"
        ).encode()
    )
    logger.debug("_valid_csv exit bytes=%d", len(result))
    return result


def _call_csv(payload: object, schema: RepresentationSchema | None = None):
    logger.debug("_call_csv entry")
    value = categorical_three_way_from_csv(
        schema or _schema(), train=payload, validation=_valid_csv("v"), test=_valid_csv("t")
    )
    logger.debug("_call_csv exit")
    return value


def _json_record(prefix: str, **updates: object) -> bytes:
    logger.debug("_json_record entry")
    records = []
    for suffix, value, target in (("1", "a", "yes"), ("2", "b", "no")):
        record: dict[str, object] = {
            "row_id": f"{prefix}r{suffix}",
            "source_id": f"{prefix}s{suffix}",
            "content_id": f"{prefix}c{suffix}",
            "group_id": f"{prefix}g{suffix}",
            "value": value,
            "target": target,
        }
        record.update(updates)
        records.append(json.dumps(record, separators=(",", ":")).encode() + b"\n")
    result = b"".join(records)
    logger.debug("_json_record exit bytes=%d", len(result))
    return result


def _call_json(payload: object, schema: RepresentationSchema | None = None):
    logger.debug("_call_json entry")
    value = categorical_three_way_from_jsonl(
        schema or _schema(), train=payload, validation=_json_record("v"), test=_json_record("t")
    )
    logger.debug("_call_json exit")
    return value


@pytest.mark.parametrize(
    ("payload", "error"),
    (
        (bytearray(HEADER + CSV_ROWS), "invalid-ingestion:bytes-required"),
        (b"", "invalid-ingestion:split-empty"),
        (b"\xef\xbb\xbf" + HEADER + CSV_ROWS, "invalid-ingestion:bom"),
        (HEADER + b"r1,s1,c1,g1,s:a,s:yes\x00\n", "invalid-ingestion:nul"),
        (HEADER + b"\xff\n", "invalid-ingestion:utf8"),
        (b"source_id,row_id,content_id,group_id,value,target\n" + CSV_ROWS, "invalid-ingestion:csv-header"),
        (HEADER + b"r1,s1,c1,g1,s:a\n", "invalid-ingestion:csv-row-width"),
        (HEADER, "invalid-ingestion:split-empty"),
        (HEADER + b'r1,s1,c1,g1,"s:a,s:yes\n', "invalid-ingestion:csv-syntax"),
        (HEADER + b"r1,s1,c1,g1,x:a,s:yes\nr2,s2,c2,g2,s:b,s:no\n", "invalid-ingestion:csv-scalar-tag"),
    ),
)
def test_csv_rejects_malformed_envelopes(payload, error):
    logger.debug("test malformed CSV entry")
    with pytest.raises(RepresentationProtocolError, match=rf"^{error}$"):
        _call_csv(payload)
    logger.debug("test malformed CSV exit")


@pytest.mark.parametrize("lexeme", ("+1", "01", "-0", "1.0", "true", ""))
def test_csv_integer_tag_requires_canonical_decimal(lexeme):
    logger.debug("test CSV integer grammar entry")
    schema = RepresentationSchema(
        "integer-v1",
        (RepresentationField("value", "categorical", (0, 1)),),
        (0, 1),
    )
    payload = HEADER + f"r1,s1,c1,g1,i:{lexeme},i:0\nr2,s2,c2,g2,i:1,i:1\n".encode()
    with pytest.raises(RepresentationProtocolError, match=r"^invalid-ingestion:csv-integer$"):
        _call_csv(payload, schema)
    logger.debug("test CSV integer grammar exit")


def test_csv_and_json_integer_resource_bounds_precede_canonical_construction():
    logger.debug("test integer resource entry")
    schema = RepresentationSchema(
        "integer-v1",
        (RepresentationField("value", "categorical", (0, 1)),),
        (0, 1),
    )
    huge = "9" * 79
    csv_payload = HEADER + f"r1,s1,c1,g1,i:{huge},i:0\nr2,s2,c2,g2,i:1,i:1\n".encode()
    with pytest.raises(RepresentationProtocolError, match=r"^resource-limit:ingestion-integer$"):
        _call_csv(csv_payload, schema)
    json_payload = (
        b'{"row_id":"r1","source_id":"s1","content_id":"c1","group_id":"g1","value":'
        + huge.encode()
        + b',"target":0}\n'
    )
    with pytest.raises(RepresentationProtocolError, match=r"^resource-limit:ingestion-integer$"):
        _call_json(json_payload, schema)
    logger.debug("test integer resource exit")


@pytest.mark.parametrize(
    ("payload", "error"),
    (
        (bytearray(b"{}\n"), "invalid-ingestion:bytes-required"),
        (b"", "invalid-ingestion:split-empty"),
        (b"\xef\xbb\xbf{}\n", "invalid-ingestion:bom"),
        (b"{}\x00\n", "invalid-ingestion:nul"),
        (b"\xff\n", "invalid-ingestion:utf8"),
        (b"\n", "invalid-ingestion:jsonl-blank-record"),
        (b"[]\n", "invalid-ingestion:json-object-required"),
        (b'{"row_id":"r"}\n', "invalid-ingestion:json-keys"),
        (
            b'{"row_id":"r","row_id":"x","source_id":"s","content_id":"c","group_id":"g","value":"a","target":"yes"}\n',
            "invalid-ingestion:json-duplicate-key",
        ),
        (
            b'{"row_id":1,"source_id":"s","content_id":"c","group_id":"g","value":"a","target":"yes"}\n',
            "invalid-ingestion:json-identity",
        ),
        (
            b'{"row_id":"r","source_id":"s","content_id":"c","group_id":"g","value":null,"target":"yes"}\n',
            "invalid-ingestion:json-scalar",
        ),
        (
            b'{"row_id":"r","source_id":"s","content_id":"c","group_id":"g","value":1.5,"target":"yes"}\n',
            "invalid-ingestion:json-float",
        ),
        (
            b'{"row_id":"r","source_id":"s","content_id":"c","group_id":"g","value":NaN,"target":"yes"}\n',
            "invalid-ingestion:json-constant",
        ),
    ),
)
def test_jsonl_rejects_malformed_or_inferred_values(payload, error):
    logger.debug("test malformed JSONL entry")
    with pytest.raises(RepresentationProtocolError, match=rf"^{error}$"):
        _call_json(payload)
    logger.debug("test malformed JSONL exit")


def test_jsonl_rejects_deep_nesting_with_a_sanitized_error():
    logger.debug("test deep JSON entry")
    depth = 1_500
    nested = ("[" * depth + "0" + "]" * depth).encode()
    payload = b'{"row_id":"r","source_id":"s","content_id":"c","group_id":"g","value":' + nested + b',"target":"yes"}\n'
    with pytest.raises(RepresentationProtocolError, match=r"^invalid-ingestion:json-syntax$"):
        _call_json(payload)
    logger.debug("test deep JSON exit")


def test_jsonl_requires_exact_declared_key_order():
    logger.debug("test JSON key order entry")
    payload = b'{"target":"yes","value":"a","group_id":"g1","content_id":"c1","source_id":"s1","row_id":"r1"}\n'
    with pytest.raises(RepresentationProtocolError, match=r"^invalid-ingestion:json-keys$"):
        _call_json(payload)
    logger.debug("test JSON key order exit")


@pytest.mark.parametrize("field_name", ("row_id", "source_id", "content_id", "group_id", "target"))
@pytest.mark.parametrize(
    "builder,payload",
    ((categorical_three_way_from_csv, HEADER + CSV_ROWS), (categorical_three_way_from_jsonl, _json_record("r"))),
)
def test_reserved_schema_fields_are_rejected(field_name, builder, payload):
    logger.debug("test reserved fields entry")
    schema = _schema(field_name)
    with pytest.raises(RepresentationProtocolError, match=r"^invalid-ingestion-schema:reserved-field-name$"):
        builder(schema, train=payload, validation=payload, test=payload)
    logger.debug("test reserved fields exit")


def test_reserved_schema_collision_precedes_payload_validation():
    logger.debug("test schema precedence entry")
    with pytest.raises(RepresentationProtocolError, match=r"^invalid-ingestion-schema:reserved-field-name$"):
        categorical_three_way_from_csv(_schema("row_id"), train=None, validation=None, test=None)
    logger.debug("test schema precedence exit")


def test_split_physical_logical_and_row_limits_are_fail_closed(monkeypatch):
    logger.debug("test resource limits entry")
    monkeypatch.setattr(parsing, "HARD_MAX_SPLIT_BYTES", 50)
    with pytest.raises(RepresentationProtocolError, match=r"^resource-limit:ingestion-split-bytes$"):
        _call_csv(HEADER + CSV_ROWS)

    monkeypatch.setattr(parsing, "HARD_MAX_SPLIT_BYTES", 10_000)
    monkeypatch.setattr(parsing, "HARD_MAX_RECORD_BYTES", 60)
    with pytest.raises(RepresentationProtocolError, match=r"^resource-limit:ingestion-physical-record$"):
        _call_json(_json_record("r"))

    monkeypatch.setattr(parsing, "HARD_MAX_RECORD_BYTES", 70)
    multiline = HEADER + b'r1,s1,c1,g1,"s:' + b"x\n" * 40 + b'",s:yes\n'
    with pytest.raises(RepresentationProtocolError, match=r"^resource-limit:ingestion-logical-record$"):
        _call_csv(multiline)

    monkeypatch.setattr(parsing, "HARD_MAX_RECORD_BYTES", 32 * 1024)
    monkeypatch.setattr(parsing, "HARD_MAX_ROWS_PER_PRESENTATION", 1)
    with pytest.raises(RepresentationProtocolError, match=r"^resource-limit:ingestion-rows$"):
        _call_csv(HEADER + CSV_ROWS)
    logger.debug("test resource limits exit")


def test_line_scanning_is_lazy_and_does_not_materialize_splitlines(monkeypatch):
    logger.debug("test lazy line scan entry")
    monkeypatch.setattr(parsing, "HARD_MAX_ROWS_PER_PRESENTATION", 1)
    newline_heavy = HEADER + CSV_ROWS + (b"\n" * 1_000_000)
    with pytest.raises(RepresentationProtocolError, match=r"^resource-limit:ingestion-rows$"):
        _call_csv(newline_heavy)
    assert ".splitlines(" not in inspect.getsource(parsing)
    logger.debug("test lazy line scan exit")


def test_failure_logs_do_not_expose_payload_values(caplog):
    logger.debug("test logging secrecy entry")
    canary = "DO_NOT_LOG_PAYLOAD_7d125d"
    payload = HEADER + f"{canary},s1,c1,g1,x:a,s:yes\n".encode()
    with caplog.at_level(logging.DEBUG), pytest.raises(RepresentationProtocolError):
        _call_csv(payload)
    assert canary not in caplog.text
    assert "x:a" not in caplog.text
    logger.debug("test logging secrecy exit")


def test_failure_logs_do_not_expose_schema_field_names(caplog):
    logger.debug("test schema logging secrecy entry")
    canary = "DO_NOT_LOG_FIELD_1c804f"
    schema = _schema(canary)
    header = f"row_id,source_id,content_id,group_id,{canary},target\n".encode()
    payload = header + b"r1,s1,c1,g1,x:a,s:yes\n"
    with caplog.at_level(logging.DEBUG), pytest.raises(RepresentationProtocolError):
        _call_csv(payload, schema)
    assert canary not in caplog.text
    logger.debug("test schema logging secrecy exit")
