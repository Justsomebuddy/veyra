"""Exact theorem-object and second-contract regressions for R13."""
from __future__ import annotations

from dataclasses import replace

import pytest

from src.core.intrinsic_observer_echo_theorem import (
    EXPECTED_ARTIFACT_DIGEST,
    EXPECTED_STATEMENT_DIGEST,
    IntrinsicObserverEchoTheorem,
    intrinsic_observer_echo_theorem,
    verify_intrinsic_observer_echo_theorem,
)
from src.core.layer_theorem_contract_handlers import (
    R13_HANDLER_ID,
    R13_LEAN_BRIDGE_ID,
    R13_TRANSPORT_CARRIER,
    R13_TRUSTED_CONTRACT_DIGEST,
    normalize_theorem_evidence,
)
from src.core.layer_theorem_contracts import (
    build_theorem_contract_registry,
    theorem_contract_digest,
    theorem_contract_registry,
)

pytestmark = pytest.mark.requires_lean


def test_exact_r13_theorem_replays_and_binds_all_local_evidence() -> None:
    theorem = intrinsic_observer_echo_theorem()
    assert verify_intrinsic_observer_echo_theorem(theorem)
    assert theorem.theorem_id == "THM-R13-003"
    assert theorem.statement_digest == EXPECTED_STATEMENT_DIGEST
    assert theorem.artifact_digest == EXPECTED_ARTIFACT_DIGEST
    assert theorem.proof_rules == (
        "r7-check-sound",
        "r9-intrinsic-image",
        "r11-ready-domain-reflexivity",
        "r12-echo-transport",
    )
    assert theorem.native_laws == ("weave-unit-right",)
    assert "observerBounded(observer)" in theorem.statement
    assert "r11RecurrenceBounded(value)" in theorem.statement
    assert "echoOutcomeBounded(echo(observer,value,value))" in theorem.statement
    assert "observer nodes<=2048/depth<=128" in theorem.boundary


@pytest.mark.parametrize(
    "field,value",
    [
        ("schema", "forged"),
        ("theorem_id", "THM-R13-004"),
        ("statement", "forged"),
        ("statement_digest", "0" * 64),
        ("source_artifact_digest", "0" * 64),
        ("source_proof_digest", "0" * 64),
        ("executable_evidence_digest", "0" * 64),
        ("effect_digest", "0" * 64),
        ("proof_rules", ("r7-check-sound",)),
        ("native_laws", ()),
        ("status", "checked"),
        ("boundary", "forged"),
        ("artifact_digest", "0" * 64),
    ],
)
def test_every_r13_theorem_field_mutation_blocks(field: str, value: object) -> None:
    theorem = intrinsic_observer_echo_theorem()
    assert not verify_intrinsic_observer_echo_theorem(
        replace(theorem, **{field: value}),
    )


def test_hostile_uninitialized_r13_theorem_blocks_without_dereference() -> None:
    hostile = object.__new__(IntrinsicObserverEchoTheorem)
    assert not verify_intrinsic_observer_echo_theorem(hostile)


def test_second_contract_is_exact_and_old_contract_digest_is_unchanged() -> None:
    registry = theorem_contract_registry()
    assert tuple(registry) == ("intrinsic-resonance", "intrinsic-observer-echo")
    old = registry["intrinsic-resonance"]
    new = registry["intrinsic-observer-echo"]
    assert theorem_contract_digest(old) == (
        "484534000ee59a28d0d131b777dcc775d56d24b82c70797954ba82c8570a8eba"
    )
    assert theorem_contract_digest(new) == R13_TRUSTED_CONTRACT_DIGEST
    assert new.handler_id == R13_HANDLER_ID
    assert new.semantic_carrier == R13_TRANSPORT_CARRIER
    assert new.bridge_id == R13_LEAN_BRIDGE_ID
    assert new.artifact_digest == EXPECTED_ARTIFACT_DIGEST
    assert "explicitly bounded" in new.role
    assert new.statement_digest == intrinsic_observer_echo_theorem().statement_digest
    assert all(
        premise in intrinsic_observer_echo_theorem().statement
        for premise in (
            "observerBounded(observer)",
            "r11RecurrenceBounded(value)",
            "echoOutcomeBounded(echo(observer,value,value))",
        )
    )
    normalized = normalize_theorem_evidence(new, intrinsic_observer_echo_theorem())
    assert normalized[2] == theorem_contract_registry()[
        "intrinsic-observer-echo"
    ].artifact_digest
    assert normalized[3] == intrinsic_observer_echo_theorem().source_proof_digest
    assert normalized[2] != normalized[3]


def test_r13_provider_verifier_or_handler_transplant_blocks() -> None:
    contract = theorem_contract_registry()["intrinsic-observer-echo"]
    for field, value in (
        ("theorem_provider", lambda: intrinsic_observer_echo_theorem()),
        ("theorem_verifier", lambda *_: True),
        ("bridge_provider", lambda: object()),
        ("bridge_verifier", lambda *_: True),
        ("handler_id", "veyra.handler.intrinsic-resonance.r10.v1"),
    ):
        with pytest.raises(ValueError):
            build_theorem_contract_registry((replace(contract, **{field: value}),))


def test_handler_selected_normalizer_rejects_cross_contract_theorem() -> None:
    old = theorem_contract_registry()["intrinsic-resonance"]
    with pytest.raises(ValueError, match="normalizer-mismatch"):
        normalize_theorem_evidence(old, intrinsic_observer_echo_theorem())
