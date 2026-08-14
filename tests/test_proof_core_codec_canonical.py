"""Focused list/tuple boundaries for the proof-core canonical codec."""

from __future__ import annotations

import ast
import logging
from pathlib import Path

import pytest

from src.core.proof_core_codec import canonical_json, digest_data
from src.core.paths import PROJECT_ROOT


logger = logging.getLogger(__name__)


def test_explicit_json_list_keeps_the_recorded_canonical_bytes_and_digest() -> None:
    """List encoding stays byte-for-byte equal to the pre-hardening record."""
    logger.debug("codec list stability test entry")
    payload = {"schema": "codec-list-v1", "items": ["alpha", {"n": 1}]}
    assert canonical_json(payload) == (
        '{"items":["alpha",{"n":1}],"schema":"codec-list-v1"}'
    )
    assert digest_data(payload, "veyra-codec-list-test-v1") == (
        "b68d43021cbefab824f6d7a9caa03a82770e17d74db1dc920e5d18147d9bbcd1"
    )
    logger.debug("codec list stability test exit")


@pytest.mark.parametrize(
    "payload",
    [
        ("alpha", "beta"),
        {"items": ("alpha", "beta")},
        ["alpha", {"nested": (1, 2)}],
    ],
)
def test_raw_tuple_is_rejected_at_every_canonical_depth(payload: object) -> None:
    """A Python tuple cannot collide with an explicitly selected JSON list."""
    logger.debug("codec tuple rejection test entry type=%s", type(payload).__name__)
    with pytest.raises(TypeError, match="noncanonical-json-type:tuple"):
        canonical_json(payload)
    with pytest.raises(TypeError, match="noncanonical-json-type:tuple"):
        digest_data(payload, "veyra-codec-tuple-hostile-v1")
    logger.debug("codec tuple rejection test exit")


def test_direct_canonical_call_payloads_contain_no_literal_tuple() -> None:
    """Keep tuple literals out of every active canonical call expression."""
    logger.debug("codec canonical-call inventory test entry")
    violations: list[str] = []
    files = sorted((PROJECT_ROOT / "src" / "core").rglob("*.py"))
    calls = 0
    for path in files:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            call_name = (
                node.func.id
                if type(node) is ast.Call and type(node.func) is ast.Name
                else node.func.attr
                if type(node) is ast.Call and type(node.func) is ast.Attribute
                else None
            )
            if (
                type(node) is ast.Call
                and call_name in {"canonical_json", "digest_data"}
                and node.args
            ):
                calls += 1
                if any(
                    (
                        type(item) is ast.Tuple
                        and type(item.ctx) is ast.Load
                    )
                    or (
                        type(item) is ast.Call
                        and type(item.func) is ast.Name
                        and item.func.id == "tuple"
                    )
                    for item in ast.walk(node.args[0])
                ):
                    violations.append(f"{path.relative_to(PROJECT_ROOT)}:{node.lineno}")
    assert calls >= 150
    assert violations == []
    logger.debug(
        "codec canonical-call inventory test exit files=%d calls=%d",
        len(files),
        calls,
    )
