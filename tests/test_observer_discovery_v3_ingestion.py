"""Behavioral coverage for strict v3 categorical CSV/JSONL ingestion."""

from __future__ import annotations

import csv
from io import StringIO
import json
import logging

import pytest

import src.core.observer_discovery_v3 as v3_root
import src.core.observer_discovery_v3.ingestion as ingestion
import src.core.observer_discovery_v3.schema as schema_facade
from src.core.observer_discovery_v3.ingestion import (
    categorical_three_way_from_csv,
    categorical_three_way_from_jsonl,
)
from src.core.observer_discovery_v3.schema import (
    RepresentationField,
    RepresentationProtocolError,
    RepresentationRow,
    RepresentationSchema,
    canonical_presentation,
    canonical_three_way_presentation,
    validate_three_way_presentation,
)

logger = logging.getLogger(__name__)


def _schema() -> RepresentationSchema:
    logger.debug("_schema entry")
    result = RepresentationSchema(
        "ingestion-test-v1",
        (
            RepresentationField("label", "categorical", ("red", "blue", "1")),
            RepresentationField("count", "categorical", (1, 2)),
            RepresentationField("flag", "categorical", (True, False)),
        ),
        ("allow", "deny"),
    )
    logger.debug("_schema exit")
    return result


def _records(prefix: str) -> list[dict[str, object]]:
    logger.debug("_records entry")
    result = [
        {
            "row_id": f"{prefix}-r1",
            "source_id": f"{prefix}-s1",
            "content_id": f"{prefix}-c1",
            "group_id": f"{prefix}-g1",
            "label": "red",
            "count": 1,
            "flag": True,
            "target": "allow",
        },
        {
            "row_id": f"{prefix}-r2",
            "source_id": f"{prefix}-s2",
            "content_id": f"{prefix}-c2",
            "group_id": f"{prefix}-g2",
            "label": "1",
            "count": 2,
            "flag": False,
            "target": "deny",
        },
    ]
    logger.debug("_records exit rows=%d", len(result))
    return result


def _jsonl_records(records: list[dict[str, object]]) -> bytes:
    logger.debug("_jsonl_records entry")
    result = b"".join(
        json.dumps(record, separators=(",", ":"), ensure_ascii=False).encode("utf-8") + b"\n" for record in records
    )
    logger.debug("_jsonl_records exit bytes=%d", len(result))
    return result


def _jsonl(prefix: str) -> bytes:
    logger.debug("_jsonl entry")
    result = _jsonl_records(_records(prefix))
    logger.debug("_jsonl exit bytes=%d", len(result))
    return result


def _csv_records(records: list[dict[str, object]]) -> bytes:
    logger.debug("_csv_records entry")
    output = StringIO(newline="")
    writer = csv.writer(output, lineterminator="\n")
    writer.writerow(("row_id", "source_id", "content_id", "group_id", "label", "count", "flag", "target"))
    for record in records:
        writer.writerow(
            (
                record["row_id"],
                record["source_id"],
                record["content_id"],
                record["group_id"],
                f"s:{record['label']}",
                f"i:{record['count']}",
                f"b:{str(record['flag']).lower()}",
                f"s:{record['target']}",
            )
        )
    result = output.getvalue().encode("utf-8")
    logger.debug("_csv_records exit bytes=%d", len(result))
    return result


def _csv(prefix: str) -> bytes:
    logger.debug("_csv entry")
    result = _csv_records(_records(prefix))
    logger.debug("_csv exit bytes=%d", len(result))
    return result


def _expected() -> object:
    logger.debug("_expected entry")
    schema = _schema()
    presentations = []
    for prefix in ("train", "validation", "test"):
        rows = tuple(
            RepresentationRow(
                record["row_id"],
                record["source_id"],
                record["content_id"],
                record["group_id"],
                (record["label"], record["count"], record["flag"]),
                record["target"],
            )
            for record in _records(prefix)
        )
        presentations.append(canonical_presentation(schema, rows))
    result = canonical_three_way_presentation(*presentations)
    logger.debug("_expected exit")
    return result


@pytest.mark.parametrize(
    ("builder", "payload"),
    (
        (categorical_three_way_from_csv, _csv),
        (categorical_three_way_from_jsonl, _jsonl),
    ),
)
def test_categorical_ingestion_matches_existing_canonical_contract(builder, payload):
    logger.debug("test canonical ingestion entry")
    result = builder(
        _schema(),
        train=payload("train"),
        validation=payload("validation"),
        test=payload("test"),
    )
    assert result == _expected()
    assert validate_three_way_presentation(result)
    assert result.train.schema_digest == "d42e8500d9ebc85082c79a98adc1a1f8d73ab7cffb8724e31311e78f596fcb2e"
    assert result.train.payload_digest == "7aa79b6bef37899967e46b68aec6651de256901ee9ecc51bbd4a26084457097a"
    assert result.validation.payload_digest == "38137753a110489085db6e805348a44f234e3fe868309f21d43a94c69859ab49"
    assert result.test.payload_digest == "bb36865915e69edd987a7126bfb914679cdc2c8e0bf7b5817c94ce8a37e05b8d"
    assert result.protocol_digest == "c2bf2795f7b5008622242582f25227c59abc7415a8ae30a9f75f1995b3d6b0d1"
    assert tuple(row.row_id for row in result.train.rows) == ("train-r1", "train-r2")
    assert tuple(type(value) for value in result.train.rows[1].values) == (str, int, bool)
    logger.debug("test canonical ingestion exit")


def test_csv_and_jsonl_have_identical_semantic_digest():
    logger.debug("test format semantic parity entry")
    csv_value = categorical_three_way_from_csv(
        _schema(), train=_csv("train"), validation=_csv("validation"), test=_csv("test")
    )
    jsonl_value = categorical_three_way_from_jsonl(
        _schema(), train=_jsonl("train"), validation=_jsonl("validation"), test=_jsonl("test")
    )
    assert csv_value == jsonl_value
    assert csv_value.protocol_digest == jsonl_value.protocol_digest
    logger.debug("test format semantic parity exit")


def test_csv_preserves_quoted_text_and_record_order():
    logger.debug("test quoted CSV entry")
    schema = RepresentationSchema(
        "quoted-v1",
        (RepresentationField("label", "categorical", ("a,b", "line\nbreak")),),
        (0, 1),
    )

    def payload(prefix: str) -> bytes:
        logger.debug("quoted payload entry")
        output = StringIO(newline="")
        writer = csv.writer(output, lineterminator="\n")
        writer.writerow(("row_id", "source_id", "content_id", "group_id", "label", "target"))
        writer.writerow((f"{prefix}-r1", f"{prefix}-s1", f"{prefix}-c1", f"{prefix}-g1", "s:a,b", "i:0"))
        writer.writerow((f"{prefix}-r2", f"{prefix}-s2", f"{prefix}-c2", f"{prefix}-g2", "s:line\nbreak", "i:1"))
        result = output.getvalue().encode()
        logger.debug("quoted payload exit bytes=%d", len(result))
        return result

    result = categorical_three_way_from_csv(
        schema, train=payload("train"), validation=payload("validation"), test=payload("test")
    )
    assert tuple(row.values[0] for row in result.train.rows) == ("a,b", "line\nbreak")
    logger.debug("test quoted CSV exit")


def test_ingestion_exports_are_exact_and_non_root():
    logger.debug("test ingestion exports entry")
    assert ingestion.__all__ == (
        "categorical_three_way_from_csv",
        "categorical_three_way_from_jsonl",
    )
    for name in ingestion.__all__:
        assert getattr(ingestion, name).__module__ == "src.core.observer_discovery_v3.ingestion.runtime"
        assert not hasattr(v3_root, name)
        assert not hasattr(schema_facade, name)
    logger.debug("test ingestion exports exit")


@pytest.mark.parametrize(
    ("builder", "serialize"),
    (
        (categorical_three_way_from_csv, _csv_records),
        (categorical_three_way_from_jsonl, _jsonl_records),
    ),
)
@pytest.mark.parametrize("attribute", ("row_id", "source_id", "content_id", "group_id"))
def test_existing_three_way_lineage_validator_remains_authoritative(builder, serialize, attribute):
    logger.debug("test canonical lineage authority entry")
    train_records = _records("train")
    validation_records = _records("validation")
    for index in range(len(validation_records)):
        validation_records[index][attribute] = train_records[index][attribute]
    with pytest.raises(RepresentationProtocolError, match=rf"^split-leakage:three-way-{attribute}-overlap$"):
        builder(
            _schema(),
            train=serialize(train_records),
            validation=serialize(validation_records),
            test=serialize(_records("test")),
        )
    logger.debug("test canonical lineage authority exit")
