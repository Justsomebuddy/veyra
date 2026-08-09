"""Adversarial canonical-codec tests for the closed R11 observer AST."""

from __future__ import annotations

import json

import pytest

from src.core.observer_core_codec import (
    MAX_OBSERVER_BYTES,
    SCHEMA_ID,
    ObserverCodecError,
    canonical_observer_bytes,
    decode_observer,
    observer_digest,
)
from src.core.observer_core_types import Apply, Input, Pair, PrimitiveId


def _sample() -> Pair:
    return Pair(Apply(PrimitiveId.CREST, Input()), Apply(PrimitiveId.TAIL, Input()))


def test_canonical_round_trip_and_digest_are_exact():
    observer = _sample()
    encoded = canonical_observer_bytes(observer)
    assert encoded == (
        b'{"observer":{"left":{"child":{"tag":"input"},"primitive":"crest","tag":"apply"},'
        b'"right":{"child":{"tag":"input"},"primitive":"tail","tag":"apply"},"tag":"pair"},'
        b'"schema":"veyra.observer-core.v2"}'
    )
    assert decode_observer(encoded) == observer
    assert len(observer_digest(observer)) == 64
    assert observer_digest(decode_observer(encoded)) == observer_digest(observer)


@pytest.mark.parametrize(
    "mutation",
    [
        lambda raw: raw + b" ",
        lambda raw: b" " + raw,
        lambda raw: raw + b"garbage",
        lambda raw: raw.replace(b'"schema":"veyra.observer-core.v2"', b'"schema":"future"'),
        lambda raw: raw.replace(b'"tag":"input"', b'"tag":"future"', 1),
        lambda raw: raw.replace(b'"primitive":"crest"', b'"primitive":"unknown"'),
        lambda raw: raw.replace(b'"primitive":"crest"', b'"primitive":true'),
        lambda raw: raw.replace(b'"tag":"pair"', b'"extra":null,"tag":"pair"'),
        lambda raw: raw.replace(b'"tag":"input"', b'"extra":null,"tag":"input"', 1),
    ],
)
def test_noncanonical_or_unknown_json_is_rejected(mutation):
    with pytest.raises(ObserverCodecError):
        decode_observer(mutation(canonical_observer_bytes(_sample())))


def test_duplicate_keys_and_envelope_drift_are_rejected():
    duplicate = b'{"observer":{"tag":"input","tag":"input"},"schema":"veyra.observer-core.v2"}'
    extra = b'{"extra":null,"observer":{"tag":"input"},"schema":"veyra.observer-core.v2"}'
    missing = b'{"schema":"veyra.observer-core.v2"}'
    for payload in (duplicate, extra, missing):
        with pytest.raises(ObserverCodecError):
            decode_observer(payload)


def test_non_bytes_subclasses_and_invalid_in_memory_nodes_are_rejected():
    class BytesSubclass(bytes):
        pass

    class InputSubclass(Input):
        pass

    with pytest.raises(ObserverCodecError):
        decode_observer(canonical_observer_bytes(Input()).decode())  # type: ignore[arg-type]
    with pytest.raises(ObserverCodecError):
        decode_observer(BytesSubclass(canonical_observer_bytes(Input())))
    with pytest.raises(ValueError):
        canonical_observer_bytes(InputSubclass())
    with pytest.raises(ValueError):
        canonical_observer_bytes(Apply("tail", Input()))  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="unknown-observer-node"):
        canonical_observer_bytes(lambda value: value)


def test_cycles_and_resource_exhaustion_fail_closed():
    cyclic = Apply(PrimitiveId.TAIL, Input())
    object.__setattr__(cyclic, "child", cyclic)
    with pytest.raises(ValueError, match="circular-observer"):
        canonical_observer_bytes(cyclic)

    deep = Input()
    for _ in range(130):
        deep = Apply(PrimitiveId.TAIL, deep)
    with pytest.raises(ValueError, match="observer-resource-limit"):
        canonical_observer_bytes(deep)

    with pytest.raises(ObserverCodecError, match="observer-byte-limit"):
        decode_observer(b"{" + b" " * MAX_OBSERVER_BYTES)


def test_key_order_and_pretty_json_are_not_alternate_encodings():
    raw = json.loads(canonical_observer_bytes(Input()))
    pretty = json.dumps(raw, indent=2).encode()
    reordered = f'{{"schema":"{SCHEMA_ID}","observer":{{"tag":"input"}}}}'.encode()
    for payload in (pretty, reordered):
        with pytest.raises(ObserverCodecError, match="noncanonical-json"):
            decode_observer(payload)
