"""Normal and compatibility coverage for RFC 172 missing-data replay."""

from __future__ import annotations

import csv
from io import StringIO
import json
import logging

import src.core as core_root
import src.core.observer_discovery_v3 as v3_root
import src.core.observer_discovery_v3.ingestion as ingestion
import src.core.observer_discovery_v3.missing_data as missing
from src.core.observer_discovery_v3.missing_data import (
    MissingFieldRule,
    MissingPolicyMode,
    MissingReplayAuthority,
    MissingSplitReceipt,
    MissingWireFormat,
    canonical_missing_data_policy,
    external_binding,
    missingness_from_csv,
    missingness_from_jsonl,
    projected_schema_for_missing_policy,
    validate_native_missingness_presentation,
)
from src.core.observer_discovery_v3.missing_data.parsing import _parse_csv, parse_missing_split
from src.core.observer_discovery_v3.schema import RepresentationField, RepresentationSchema
from src.core.observer_discovery_v3.schema.phase2_compat import discovery_split_from_three_way

logger = logging.getLogger(__name__)


def _contract(fallback: str = "red"):
    logger.debug("missing fixture contract entry")
    base = RepresentationSchema(
        "missing-test-base-v1",
        (
            RepresentationField("label", "categorical", ("red", "blue")),
            RepresentationField("typed", "categorical", (1, True, "1")),
            RepresentationField("flag", "binary", (0, 1)),
        ),
        ("allow", "deny"),
    )
    rules = (
        MissingFieldRule("label", MissingPolicyMode.EXPLICIT_MASK, fallback, "label__present_v1"),
        MissingFieldRule("typed", MissingPolicyMode.REQUIRED),
        MissingFieldRule("flag", MissingPolicyMode.REQUIRED),
    )
    projected = projected_schema_for_missing_policy(base, rules)
    policy = canonical_missing_data_policy(base, projected, rules)
    logger.debug("missing fixture contract exit")
    return base, projected, policy


def _records(prefix: str, *, missing_first: bool = False) -> list[dict[str, object]]:
    labels = (None if missing_first else "red", "blue", "red", "blue")
    groups = ("a", "a", "b", "b")
    targets = ("allow", "allow", "deny", "deny")
    return [
        {
            "row_id": f"{prefix}-r{index}",
            "source_id": f"{prefix}-s{index}",
            "content_id": f"{prefix}-c{index}",
            "group_id": f"{prefix}-{groups[index]}",
            "label": labels[index],
            "typed": 1 if index % 2 == 0 else True,
            "flag": index % 2,
            "target": targets[index],
        }
        for index in range(4)
    ]


def _jsonl(prefix: str, *, missing_first: bool = False) -> bytes:
    return b"".join(
        json.dumps(row, ensure_ascii=False, separators=(",", ":")).encode() + b"\n"
        for row in _records(prefix, missing_first=missing_first)
    )


def _csv(prefix: str, *, missing_first: bool = False) -> bytes:
    output = StringIO(newline="")
    writer = csv.writer(output, lineterminator="\n")
    writer.writerow(("row_id", "source_id", "content_id", "group_id", "label", "typed", "flag", "target"))
    for row in _records(prefix, missing_first=missing_first):
        typed = "i:1" if type(row["typed"]) is int else "b:true"
        writer.writerow(
            (
                row["row_id"],
                row["source_id"],
                row["content_id"],
                row["group_id"],
                "m:" if row["label"] is None else f"s:{row['label']}",
                typed,
                f"i:{row['flag']}",
                f"s:{row['target']}",
            )
        )
    return output.getvalue().encode()


def _build_csv(fallback: str = "red", *, missing_first: bool = True):
    base, projected, policy = _contract(fallback)
    raws = (_csv("train", missing_first=missing_first), _csv("validation"), _csv("test"))
    value = missingness_from_csv(policy, base, projected, train=raws[0], validation=raws[1], test=raws[2])
    return base, projected, policy, raws, value


def test_csv_and_jsonl_preserve_projection_and_distinguish_wire_identity():
    logger.debug("test missing CSV/JSONL parity entry")
    base, projected, policy = _contract()
    csv_raw = (_csv("train", missing_first=True), _csv("validation"), _csv("test"))
    json_raw = (_jsonl("train", missing_first=True), _jsonl("validation"), _jsonl("test"))
    csv_value = missingness_from_csv(policy, base, projected, train=csv_raw[0], validation=csv_raw[1], test=csv_raw[2])
    json_value = missingness_from_jsonl(
        policy, base, projected, train=json_raw[0], validation=json_raw[1], test=json_raw[2]
    )
    assert csv_value.presentation == json_value.presentation
    assert csv_value.receipt.train.semantic_mask_digest == json_value.receipt.train.semantic_mask_digest
    assert csv_value.receipt.train.projection_digest == json_value.receipt.train.projection_digest
    assert csv_value.receipt.train.raw_digest != json_value.receipt.train.raw_digest
    assert csv_value.receipt.wire_format is MissingWireFormat.CSV
    assert json_value.receipt.wire_format is MissingWireFormat.JSONL
    assert csv_value.receipt.receipt_digest != json_value.receipt.receipt_digest
    logger.debug("test missing CSV/JSONL parity exit")


def test_missing_and_observed_fallback_are_distinct_and_types_remain_exact():
    logger.debug("test missing fallback distinction entry")
    _, _, _, _, value = _build_csv()
    rows = value.presentation.train.rows
    assert rows[0].values[:2] == ("red", 0)
    assert rows[2].values[:2] == ("red", 1)
    assert type(rows[0].values[2]) is int
    assert type(rows[1].values[2]) is bool
    assert value.receipt.authority is MissingReplayAuthority.NATIVE_POLICY_REPLAY
    logger.debug("test missing fallback distinction exit")


def test_issue_55_equal_legacy_split_cannot_recover_native_policy_authority():
    logger.debug("test issue 55 authority erasure entry")
    red = _build_csv("red", missing_first=False)
    blue = _build_csv("blue", missing_first=False)
    assert red[4].presentation.protocol_digest != blue[4].presentation.protocol_digest
    assert discovery_split_from_three_way(red[4].presentation) == discovery_split_from_three_way(blue[4].presentation)
    detached = external_binding(red[4])
    assert detached.receipt.authority is MissingReplayAuthority.EXTERNAL_BINDING_ONLY
    assert not validate_native_missingness_presentation(
        detached,
        red[2],
        red[0],
        red[1],
        wire_format=MissingWireFormat.CSV,
        train=red[3][0],
        validation=red[3][1],
        test=red[3][2],
    )
    logger.debug("test issue 55 authority erasure exit")


def test_new_runtime_is_non_root_and_old_ingestion_exports_stay_exact():
    logger.debug("test missing non-root exports entry")
    assert ingestion.__all__ == (
        "categorical_three_way_from_csv",
        "categorical_three_way_from_jsonl",
    )
    assert missing.__all__ == (
        "MISSING_BOUNDARY",
        "MISSING_NONCLAIMS",
        "POLICY_SCHEMA",
        "PRESENTATION_SCHEMA",
        "MissingDataPolicy",
        "MissingDataProtocolError",
        "MissingFieldRule",
        "MissingPolicyMode",
        "MissingReplayAuthority",
        "MissingSplitReceipt",
        "MissingWireFormat",
        "MissingnessPresentation",
        "MissingnessReceipt",
        "canonical_missing_data_policy",
        "external_binding",
        "missingness_from_csv",
        "missingness_from_jsonl",
        "missingness_presentation_from_json",
        "missingness_presentation_json",
        "native_missingness_presentation_from_json",
        "native_missingness_presentation_json",
        "projected_schema_for_missing_policy",
        "replay_missingness_from_sources",
        "validate_missing_data_policy",
        "validate_native_missingness_presentation",
        "validate_structural_missingness_presentation",
    )
    for name in missing.__all__:
        assert not hasattr(v3_root, name)
        assert not hasattr(core_root, name)
    logger.debug("test missing non-root exports exit")


def test_parser_callable_retains_its_public_docstring():
    logger.debug("test missing parser docstring entry")
    assert parse_missing_split.__doc__ == "Parse one split using only this sibling's explicit grammar."
    assert _parse_csv.__doc__ == "Parse one bounded CSV split."
    logger.debug("test missing parser docstring exit")


def test_v1_policy_projection_split_and_top_receipts_are_exactly_pinned():
    logger.debug("test missing v1 digest pins entry")
    _, _, policy, _, native = _build_csv()
    external = external_binding(native)
    assert policy.projection_spec_root == "5601f96b27a415070733110f8a489417ea37a79f61223c8b309b34c3eef33ce9"
    assert policy.projected_schema_digest == "aa683cc269d6994aacbea836e64a35c9a7c8663f8a939c12e88125b1386f4bd6"
    assert policy.policy_digest == "921c634df909527896234bbdfeb6d08da3ce854bf56ca362099ae4212356f014"
    assert native.receipt.train == MissingSplitReceipt(
        raw_digest="2e86be06ec1fd7a94fbcaec8bf43f8f7247178b3350346af2e359680dab006ae",
        semantic_mask_digest="32f602cacddc619438b3d3d2f4a996624714867ea91d503bfc47cfcafe3a1fe8",
        projection_digest="f1e24ca7ff0ce0fa3c01676707381887c493c85796e27219eecbfe41c8d339c4",
        output_payload_digest="b8c761bf02ff150db1aa0b7383fdccc524c9087ac6a123b3305ce041545ae122",
        row_count=4,
        receipt_digest="09f3a332e5cb243137aa2f121a5abd485af582591f1db90ff9521c8512320439",
    )
    assert native.receipt.receipt_digest == "8eb5554c3494d77fff9aebf7982c6cdfef22f29dfe93dac3c1af32a1e0a909ec"
    assert external.receipt.receipt_digest == "3305c5b79bf18f59bd98cb55e3885a0098a32ef9cf9e2dd921ea54cdb5cde408"
    logger.debug("test missing v1 digest pins exit")
