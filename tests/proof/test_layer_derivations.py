from dataclasses import replace

import pytest

from src.core.essence import core_layers
from src.core.layer_derivations import layer_derivation_report, layer_derivations
from src.core.semantic_kernel import axiom_closure, verify_receipts

pytestmark = pytest.mark.requires_lean


def test_every_current_core_layer_is_explicitly_classified_without_fallback():
    layers = core_layers()
    rows = layer_derivations()
    assert len(rows) == len(layers) == 36
    assert [row.layer for row in rows] == [layer.name for layer in layers]
    assert {row.classification for row in rows} == {"theorem-derived", "receipt-backed-witness", "shadow", "meta"}
    assert layer_derivation_report().summary() == {
        "layers": 36, "theorem_derived": 2, "witness_backed": 4, "shadow": 25, "meta": 5,
        "receipt_backed": 4, "complete": True,
    }


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
