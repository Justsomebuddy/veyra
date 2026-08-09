"""Focused same-identity executable-binding attacks for the R13 contract."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace

import pytest

import src.core.layer_theorem_contract_handlers as handlers
from src.core.layer_theorem_contract_executable import handler_executable_digest
from src.core.layer_theorem_contracts import (
    build_theorem_contract_registry,
    theorem_contract_digest,
    theorem_contract_registry,
)


R13_EXECUTABLE_SLOTS = (
    "theorem_provider",
    "theorem_verifier",
    "bridge_provider",
    "bridge_verifier",
    "evidence_normalizer",
)


def _r13_handler_rows() -> tuple[tuple[str, Callable[..., object]], ...]:
    contract = theorem_contract_registry()["intrinsic-observer-echo"]
    return (
        ("theorem_provider", contract.theorem_provider),
        ("theorem_verifier", contract.theorem_verifier),
        ("bridge_provider", contract.bridge_provider),
        ("bridge_verifier", contract.bridge_verifier),
        ("evidence_normalizer", handlers.normalize_theorem_evidence),
    )


def _must_not_execute(*_args: object, **_kwargs: object) -> object:
    raise AssertionError("mutated handler executed before promotion rejection")


def test_r13_contract_binds_exact_handler_executable_manifest() -> None:
    contract = theorem_contract_registry()["intrinsic-observer-echo"]
    assert contract.executable_digest == handlers.R13_TRUSTED_EXECUTABLE_DIGEST
    assert handler_executable_digest(
        contract.handler_id,
        _r13_handler_rows(),
    ) == handlers.R13_TRUSTED_EXECUTABLE_DIGEST
    assert theorem_contract_digest(contract) == handlers.R13_TRUSTED_CONTRACT_DIGEST


@pytest.mark.parametrize("slot", R13_EXECUTABLE_SLOTS)
def test_same_identity_code_replacement_fails_before_promotion(slot: str) -> None:
    contract = theorem_contract_registry()["intrinsic-observer-echo"]
    target = dict(_r13_handler_rows())[slot]
    original_code = target.__code__
    original_identity = id(target)
    try:
        target.__code__ = _must_not_execute.__code__
        assert id(target) == original_identity
        with pytest.raises(
            ValueError,
            match="theorem-contract-handler-executable-mismatch",
        ):
            build_theorem_contract_registry((contract,))
    finally:
        target.__code__ = original_code


def test_r13_executable_pin_drift_blocks_at_static_contract_gate() -> None:
    contract = theorem_contract_registry()["intrinsic-observer-echo"]
    forged = replace(contract, executable_digest="0" * 64)
    with pytest.raises(
        ValueError,
        match="theorem-contract-trusted-binding-mismatch",
    ):
        build_theorem_contract_registry((forged,))


@pytest.mark.parametrize("value", ["short", "z" * 64])
def test_malformed_r13_executable_pin_fails_shape_gate(value: str) -> None:
    contract = theorem_contract_registry()["intrinsic-observer-echo"]
    forged = replace(contract, executable_digest=value)
    with pytest.raises(
        ValueError,
        match="invalid-theorem-contract-executable-digest",
    ):
        build_theorem_contract_registry((forged,))
