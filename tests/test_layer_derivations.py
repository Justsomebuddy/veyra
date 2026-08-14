from dataclasses import replace
from importlib import import_module
import logging

import pytest

from src.core.essence import core_layers
from src.core.layer_derivations import layer_derivation_report, layer_derivations
from src.core.layer_theorem_contract_types import TheoremContractCapabilityBlocked
from src.core.semantic_kernel import axiom_closure, verify_receipts
from src.platform_capabilities import Capability

derivations_module = import_module("src.core.layer_derivations")
logger = logging.getLogger(__name__)


def test_every_current_core_layer_is_explicitly_classified_without_fallback():
    logger.debug("test complete layer classification entry")
    layers = core_layers()
    rows = layer_derivations()
    assert len(rows) == len(layers) == 36
    assert [row.layer for row in rows] == [layer.name for layer in layers]
    assert {row.classification for row in rows} == {"theorem-derived", "receipt-backed-witness", "shadow", "meta"}
    assert layer_derivation_report().summary() == {
        "layers": 36, "theorem_derived": 2, "theorem_blocked": 0,
        "witness_backed": 4, "shadow": 25, "meta": 5,
        "receipt_backed": 4, "complete": True,
    }
    logger.debug("test complete layer classification exit")


def test_only_witness_backed_rows_receive_checked_receipts_and_axioms():
    for row in layer_derivations():
        if row.classification == "receipt-backed-witness":
            assert row.status == "ready"
            assert row.receipts and verify_receipts(row.receipts).ok
            assert row.axioms == axiom_closure(row.receipts)
            assert "not the whole named layer" in row.boundary
        elif row.classification != "theorem-derived":
            assert row.receipts == ()
            assert row.axioms == ()
            assert "no " in row.boundary


def test_exact_two_intrinsic_layers_are_theorem_derived():
    rows = [row for row in layer_derivations() if row.classification == "theorem-derived"]
    assert [row.layer for row in rows] == [
        "intrinsic-resonance",
        "intrinsic-observer-echo",
    ]
    row = rows[0]
    assert row.layer == "intrinsic-resonance"
    assert row.theorem_id == "THM-R7-004"
    assert len(row.proof_digest) == 64
    assert row.proof_rules == ("forall-intro", "native-law", "resonance-intro")
    assert row.native_laws == ("weave-unit-right",)
    assert row.semantic_carrier == "veyra.proof.recurrence-equiv-strict-intrinsic-mode.v1"
    assert row.bridge_id == "veyra.lean.r10.proof-elaboration-tcb.v1"
    assert all(len(value) == 64 for value in (
        row.statement_digest, row.proof_digest, row.bridge_digest, row.contract_digest,
    ))
    assert next(item for item in layer_derivations() if item.layer == "resonance").classification == "shadow"
    echo = rows[1]
    assert echo.theorem_id == "THM-R13-003"
    assert echo.proof_rules == (
        "r7-check-sound",
        "r9-intrinsic-image",
        "r11-ready-domain-reflexivity",
        "r12-echo-transport",
    )
    assert echo.native_laws == ("weave-unit-right",)


def test_registry_drift_is_rejected_instead_of_getting_default_axioms():
    layers = list(core_layers())
    layers[0] = replace(layers[0], name="new-unclassified-layer")
    with pytest.raises(ValueError, match="registry drift"):
        layer_derivations(layers)


def test_missing_toolchain_blocks_theorem_rows_without_building_registry(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Portable readiness remains truthful and never touches executable handlers."""
    logger.debug("test blocked portable theorem rows entry")

    def reject_registry_build():
        logger.debug("test blocked theorem registry attempt")
        raise TheoremContractCapabilityBlocked(
            Capability.THEOREM_PROOF_TOOLCHAIN.value,
            "requires-test-toolchain",
        )

    monkeypatch.setattr(
        derivations_module,
        "theorem_contract_registry",
        reject_registry_build,
    )
    rows = layer_derivations()
    theorem_rows = tuple(
        row for row in rows if row.classification == "theorem-derived"
    )
    assert len(theorem_rows) == 2
    assert all(row.status == "blocked" for row in theorem_rows)
    assert all(
        not row.theorem_id
        and not row.proof_digest
        and not row.statement_digest
        and not row.bridge_digest
        and not row.contract_digest
        for row in theorem_rows
    )
    assert all("no theorem handler" in row.boundary for row in theorem_rows)
    summary = layer_derivation_report().summary()
    assert summary["theorem_blocked"] == 2
    assert summary["complete"] is False
    logger.debug("test blocked portable theorem rows exit")


def test_layer_derivations_uses_one_authoritative_registry_attempt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """No preflight probe can flap before the authoritative blocked attempt."""
    logger.debug("test single theorem registry attempt entry")
    assert not hasattr(
        derivations_module,
        "theorem_contract_capability_status",
    )
    registry_calls = 0

    def blocked_registry_attempt():
        nonlocal registry_calls
        registry_calls += 1
        raise TheoremContractCapabilityBlocked(
            Capability.THEOREM_PROOF_TOOLCHAIN.value,
            "single-attempt-blocked",
        )

    monkeypatch.setattr(
        derivations_module,
        "theorem_contract_registry",
        blocked_registry_attempt,
    )
    rows = layer_derivations()
    theorem_rows = tuple(
        row for row in rows if row.classification == "theorem-derived"
    )
    assert registry_calls == 1
    assert all(row.status == "blocked" for row in theorem_rows)
    assert all("single-attempt-blocked" in row.boundary for row in theorem_rows)
    logger.debug(
        "test single theorem registry attempt exit registry_calls=%d",
        registry_calls,
    )


def test_missing_toolchain_does_not_hide_theorem_metadata_drift(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Static theorem identity remains fail-closed without executable tooling."""
    logger.debug("test blocked theorem metadata drift entry")

    def reject_registry_build():
        logger.debug("test blocked drift theorem registry attempt")
        raise TheoremContractCapabilityBlocked(
            Capability.THEOREM_PROOF_TOOLCHAIN.value,
            "requires-test-toolchain",
        )

    monkeypatch.setattr(
        derivations_module,
        "theorem_contract_registry",
        reject_registry_build,
    )
    layers = list(core_layers())
    index = next(
        index
        for index, layer in enumerate(layers)
        if layer.name == "intrinsic-resonance"
    )
    layers[index] = replace(layers[index], role="forged theorem role")
    with pytest.raises(ValueError, match="metadata-mismatch"):
        layer_derivations(layers)
    logger.debug("test blocked theorem metadata drift exit")
