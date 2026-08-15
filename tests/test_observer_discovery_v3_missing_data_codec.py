"""Canonical codec and authority-boundary coverage for RFC 172."""

from __future__ import annotations

from hashlib import sha256
import json
import logging
from pathlib import Path

import pytest

import src.core.observer_discovery_v3.missing_data.codec as missing_codec
from src.core.observer_discovery_v3.missing_data import (
    MissingDataProtocolError,
    MissingReplayAuthority,
    MissingWireFormat,
    external_binding,
    missingness_presentation_from_json,
    missingness_presentation_json,
    native_missingness_presentation_from_json,
    native_missingness_presentation_json,
)
from test_observer_discovery_v3_missing_data import _build_csv

logger = logging.getLogger(__name__)

_CODEC_SHALLOW_SIZE_CASES = (
    b" " * (1024 * 1024 + 1),
    b"\xff" * (1024 * 1024 + 1),
    " " * (1024 * 1024 + 1),
    "\ud800" * (1024 * 1024 + 1),
)
_CODEC_SHALLOW_SIZE_CASE_IDS = (
    "bytes-ascii-oversize",
    "bytes-invalid-oversize",
    "text-ascii-oversize",
    "text-surrogate-oversize",
)


def test_external_codec_roundtrip_is_exact_and_never_upgrades_authority():
    logger.debug("test external codec entry")
    _, _, _, _, native = _build_csv()
    external = external_binding(native)
    encoded = missingness_presentation_json(external)
    decoded = missingness_presentation_from_json(encoded)
    assert decoded == external
    assert decoded.receipt.authority is MissingReplayAuthority.EXTERNAL_BINDING_ONLY
    assert missingness_presentation_json(decoded) == encoded
    logger.debug("test external codec exit")


def test_native_codec_requires_complete_matching_source_replay():
    logger.debug("test native codec replay entry")
    base, projected, policy, raws, native = _build_csv()
    with pytest.raises(MissingDataProtocolError, match="^codec-value-invalid$"):
        missingness_presentation_json(native)
    encoded = native_missingness_presentation_json(
        native,
        policy,
        base,
        projected,
        wire_format=MissingWireFormat.CSV,
        train=raws[0],
        validation=raws[1],
        test=raws[2],
    )
    with pytest.raises(MissingDataProtocolError, match="^codec-native-requires-source-replay$"):
        missingness_presentation_from_json(encoded)
    assert (
        native_missingness_presentation_from_json(
            encoded,
            policy,
            base,
            projected,
            wire_format=MissingWireFormat.CSV,
            train=raws[0],
            validation=raws[1],
            test=raws[2],
        )
        == native
    )
    with pytest.raises(MissingDataProtocolError, match="^codec-native-authority-mismatch$"):
        native_missingness_presentation_from_json(
            encoded,
            policy,
            base,
            projected,
            wire_format=MissingWireFormat.CSV,
            train=raws[0].replace(b"\n", b"\r\n"),
            validation=raws[1],
            test=raws[2],
        )
    logger.debug("test native codec replay exit")


@pytest.mark.parametrize(
    ("mutation", "reason"),
    (
        (lambda text: " " + text, "codec-noncanonical"),
        (lambda text: text.replace('"boundary":', '"boundary":"duplicate","boundary":', 1), "codec-duplicate-key"),
        (
            lambda text: text.replace('"authority":"EXTERNAL_BINDING_ONLY"', '"authority":"NATIVE_POLICY_REPLAY"'),
            "codec-native-requires-source-replay",
        ),
        (lambda text: text.replace('"row_count":4', '"row_count":true', 1), "codec-split-receipt-types"),
    ),
)
def test_malformed_or_authority_forged_codec_payloads_fail_closed(mutation, reason):
    logger.debug("test hostile codec entry reason=%s", reason)
    _, _, _, _, native = _build_csv()
    encoded = missingness_presentation_json(external_binding(native))
    with pytest.raises(MissingDataProtocolError, match=rf"^{reason}$"):
        missingness_presentation_from_json(mutation(encoded))
    logger.debug("test hostile codec exit")


def test_codec_preserves_typed_bool_and_integer_scalars():
    logger.debug("test codec scalar identity entry")
    _, _, _, _, native = _build_csv()
    encoded = missingness_presentation_json(external_binding(native))
    decoded = missingness_presentation_from_json(encoded)
    values = decoded.presentation.train.rows
    assert type(values[0].values[2]) is int
    assert type(values[1].values[2]) is bool
    parsed = json.loads(encoded)
    assert parsed["presentation"]["train"]["rows"][0]["values"][2] == {"type": "int", "value": 1}
    assert parsed["presentation"]["train"]["rows"][1]["values"][2] == {"type": "bool", "value": True}
    logger.debug("test codec scalar identity exit")


def test_codec_rejects_duplicate_nested_keys_and_oversize_before_construction():
    logger.debug("test codec resource entry")
    _, _, _, _, native = _build_csv()
    encoded = missingness_presentation_json(external_binding(native))
    duplicate = encoded.replace('"policy_digest":', '"policy_digest":"0","policy_digest":', 1)
    with pytest.raises(MissingDataProtocolError, match="^codec-duplicate-key$"):
        missingness_presentation_from_json(duplicate)
    with pytest.raises(MissingDataProtocolError, match="^codec-byte-limit$"):
        missingness_presentation_from_json(b" " * (1024 * 1024 + 1))
    logger.debug("test codec resource exit")


@pytest.mark.parametrize(
    "payload",
    _CODEC_SHALLOW_SIZE_CASES,
    ids=_CODEC_SHALLOW_SIZE_CASE_IDS,
)
def test_codec_shallow_size_gate_precedes_transcoding_and_parser(monkeypatch, payload):
    logger.debug("test codec shallow size gate entry")

    def forbidden_parser(*_args, **_kwargs):
        raise AssertionError("JSON parser reached before shallow size rejection")

    monkeypatch.setattr(missing_codec, "_preflight_json", forbidden_parser)
    monkeypatch.setattr(missing_codec.json, "loads", forbidden_parser)
    with pytest.raises(MissingDataProtocolError, match="^codec-byte-limit$"):
        missingness_presentation_from_json(payload)
    logger.debug("test codec shallow size gate exit")


def test_codec_shallow_size_case_ids_are_windows_environment_safe():
    logger.debug("test codec shallow IDs entry")
    assert _CODEC_SHALLOW_SIZE_CASE_IDS == (
        "bytes-ascii-oversize",
        "bytes-invalid-oversize",
        "text-ascii-oversize",
        "text-surrogate-oversize",
    )
    assert max(map(len, _CODEC_SHALLOW_SIZE_CASE_IDS)) <= 32
    assert all(identifier.isascii() for identifier in _CODEC_SHALLOW_SIZE_CASE_IDS)
    collected_nodeids = tuple(
        f"{Path(__file__).name}::test_codec_shallow_size_gate_precedes_transcoding_and_parser[{identifier}]"
        for identifier in _CODEC_SHALLOW_SIZE_CASE_IDS
    )
    assert max(len(nodeid.encode("ascii")) for nodeid in collected_nodeids) <= 256
    logger.debug("test codec shallow IDs exit")


def test_external_codec_serializes_validated_detached_snapshot(monkeypatch):
    logger.debug("test external codec snapshot entry")
    _, _, _, _, native = _build_csv()
    external = external_binding(native)
    expected = missingness_presentation_json(external)
    original_validate = missing_codec._validate_detached_missingness_presentation

    def mutate_after_validation(value, *, allow_native):
        valid = original_validate(value, allow_native=allow_native)
        object.__setattr__(external, "boundary", "caller-mutated-after-validation")
        return valid

    monkeypatch.setattr(missing_codec, "_validate_detached_missingness_presentation", mutate_after_validation)
    assert missingness_presentation_json(external) == expected
    logger.debug("test external codec snapshot exit")


def test_native_codec_serializes_fresh_replay_after_caller_mutation(monkeypatch):
    logger.debug("test native codec snapshot entry")
    base, projected, policy, raws, native = _build_csv()
    expected = native_missingness_presentation_json(
        native,
        policy,
        base,
        projected,
        wire_format=MissingWireFormat.CSV,
        train=raws[0],
        validation=raws[1],
        test=raws[2],
    )
    original_compare = missing_codec.exact_data_equal

    def mutate_after_comparison(left, right):
        valid = original_compare(left, right)
        object.__setattr__(native, "boundary", "caller-mutated-after-validation")
        return valid

    monkeypatch.setattr(missing_codec, "exact_data_equal", mutate_after_comparison)
    assert (
        native_missingness_presentation_json(
            native,
            policy,
            base,
            projected,
            wire_format=MissingWireFormat.CSV,
            train=raws[0],
            validation=raws[1],
            test=raws[2],
        )
        == expected
    )
    logger.debug("test native codec snapshot exit")


def test_v1_canonical_external_json_bytes_are_exactly_pinned():
    logger.debug("test missing v1 JSON pin entry")
    _, _, _, _, native = _build_csv()
    actual = missingness_presentation_json(external_binding(native)).encode("ascii")
    expected = (Path(__file__).parent / "fixtures" / "observer_missing_data_v1_external.json").read_bytes()
    assert sha256(expected).hexdigest() == "73a8f2870602b9f4e446f16379a10aaf677dfd4c76b063c5e4678cef773da0b4"
    assert actual == expected
    assert not actual.endswith(b"\n")
    logger.debug("test missing v1 JSON pin exit bytes=%d", len(actual))
