from dataclasses import replace
from importlib import import_module
import logging
from types import MappingProxyType

import pytest

import src.core.layer_theorem_contracts as contracts_module
import src.core.proof_elaboration_bridge as bridge_module
from src.core.essence import core_layers
from src.core.layer_derivations import layer_derivations
from src.core.layer_theorem_contracts import (
    INTRINSIC_TRANSPORT_CARRIER, R10_LEAN_BRIDGE_ID,
    build_theorem_contract_registry, resolve_layer_theorem,
    theorem_contract_registry,
)
from src.core.layer_theorem_contract_types import TheoremContractCapabilityBlocked
from src.core.proof_elaboration_bridge import proof_elaboration_bridge_report
from src.core.intrinsic_mode_bridge import intrinsic_mode_bridge_report
from src.core.proof_core_resonance import intrinsic_resonance_theorem
from src.platform_capabilities import Capability, CapabilityStatus

derivations_module = import_module("src.core.layer_derivations")
logger = logging.getLogger(__name__)


def _intrinsic_layer():
    return next(layer for layer in core_layers() if layer.name == "intrinsic-resonance")


def _different_contract(base, **changes):
    defaults = {
        "layer": "second-theorem-layer",
        "role": "second exact theorem role",
        "certificate": "second_exact_certificate",
        "theorem_id": "THM-R8-999",
        "statement_digest": "1" * 64,
        "artifact_digest": "2" * 64,
        "proof_rules": ("eq-refl",),
        "native_laws": (),
        "boundary": "second exact boundary",
    }
    defaults.update(changes)
    return replace(base, **defaults)


class _EqualToEverything:
    def __eq__(self, _other):
        return True

    def __hash__(self):
        return hash("intrinsic-resonance")


class _MisleadingLayerName(str):
    def __new__(cls):
        return super().__new__(cls, "intrinsic-resonance")

    def __str__(self):
        return "native-number"


def test_intrinsic_layer_resolves_through_its_exact_contract():
    evidence = resolve_layer_theorem(_intrinsic_layer())
    assert evidence.theorem_id == "THM-R7-004"
    assert evidence.artifact_digest == intrinsic_resonance_theorem().artifact.proof_digest
    assert evidence.proof_digest == intrinsic_resonance_theorem().artifact.proof_digest
    assert evidence.semantic_carrier == INTRINSIC_TRANSPORT_CARRIER
    assert evidence.bridge_id == R10_LEAN_BRIDGE_ID
    assert evidence.bridge_digest == proof_elaboration_bridge_report().binding_digest
    assert len(evidence.statement_digest) == len(evidence.contract_digest) == 64


def test_production_resolution_raises_typed_boundary_before_registry_build(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Missing proof capability cannot trigger bytecode-bound construction."""
    logger.debug("test typed theorem capability boundary entry")
    blocked = CapabilityStatus(
        Capability.THEOREM_PROOF_TOOLCHAIN,
        False,
        "requires-test-toolchain",
    )
    monkeypatch.setattr(
        contracts_module,
        "theorem_contract_capability_status",
        lambda: blocked,
    )

    def reject_registry_build():
        logger.error("test unexpected production theorem registry build")
        raise AssertionError("production theorem registry must remain lazy")

    monkeypatch.setattr(
        contracts_module,
        "_production_theorem_contract_registry",
        reject_registry_build,
    )
    with pytest.raises(TheoremContractCapabilityBlocked) as caught:
        resolve_layer_theorem(_intrinsic_layer())
    assert caught.value.capability == Capability.THEOREM_PROOF_TOOLCHAIN.value
    assert caught.value.detail == "requires-test-toolchain"
    logger.debug("test typed theorem capability boundary exit")


def test_custom_registry_validation_remains_available_without_host_capability(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A caller-supplied registry retains deterministic validation semantics."""
    logger.debug("test custom theorem registry portable validation entry")
    renamed = MappingProxyType(
        {"native-number": contracts_module._INTRINSIC_CONTRACT},
    )
    blocked = CapabilityStatus(
        Capability.THEOREM_PROOF_TOOLCHAIN,
        False,
        "requires-test-toolchain",
    )
    monkeypatch.setattr(
        contracts_module,
        "theorem_contract_capability_status",
        lambda: blocked,
    )
    with pytest.raises(ValueError, match="registry-key-mismatch"):
        resolve_layer_theorem(_intrinsic_layer(), renamed)
    logger.debug("test custom theorem registry portable validation exit")


def test_arbitrary_layer_cannot_inherit_the_only_theorem():
    native_number = next(layer for layer in core_layers() if layer.name == "native-number")
    with pytest.raises(ValueError, match="unbound-theorem-contract"):
        resolve_layer_theorem(native_number)


def test_r9_transport_report_alone_no_longer_authorizes_promotion():
    contract = theorem_contract_registry()["intrinsic-resonance"]
    assert not contract.bridge_verifier(
        contract, intrinsic_mode_bridge_report(), contract.artifact_digest,
    )


def test_registry_mapping_keys_cannot_be_swapped_or_renamed():
    base = theorem_contract_registry()["intrinsic-resonance"]
    renamed = MappingProxyType({"native-number": base})
    with pytest.raises(ValueError, match="registry-key-mismatch"):
        resolve_layer_theorem(_intrinsic_layer(), renamed)


def test_reproduced_old_name_set_promotion_exploit_now_fails(monkeypatch):
    registry = theorem_contract_registry()
    base = registry["intrinsic-resonance"]
    r13 = registry["intrinsic-observer-echo"]
    native = next(layer for layer in core_layers() if layer.name == "native-number")
    reused = replace(base, layer=native.name, role=native.role, certificate=native.certificate)
    injected = MappingProxyType(
        {base.layer: base, reused.layer: reused, r13.layer: r13},
    )
    monkeypatch.setattr(derivations_module, "theorem_contract_registry", lambda: injected)
    monkeypatch.setattr(
        derivations_module, "SHADOW_LAYERS",
        frozenset(name for name in derivations_module.SHADOW_LAYERS if name != native.name),
    )
    with pytest.raises(ValueError, match="duplicate-theorem-contract-theorem-id"):
        derivations_module.layer_derivations()


def test_singleton_contract_transplant_cannot_change_readiness(monkeypatch):
    registry = theorem_contract_registry()
    base = registry["intrinsic-resonance"]
    r13 = registry["intrinsic-observer-echo"]
    native = next(layer for layer in core_layers() if layer.name == "native-number")
    transplanted = replace(
        base, layer=native.name, role=native.role, certificate=native.certificate,
    )
    injected = MappingProxyType({native.name: transplanted, r13.layer: r13})
    with pytest.raises(ValueError, match="trusted-binding-mismatch"):
        build_theorem_contract_registry((transplanted, r13))
    monkeypatch.setattr(derivations_module, "theorem_contract_registry", lambda: injected)
    monkeypatch.setattr(
        derivations_module, "SHADOW_LAYERS",
        frozenset(name for name in derivations_module.SHADOW_LAYERS if name != native.name)
        | {base.layer},
    )
    with pytest.raises(ValueError, match="trusted-binding-mismatch"):
        derivations_module.layer_derivations()


@pytest.mark.parametrize("field,value", [
    ("role", "forged theorem role"),
    ("certificate", "forged_certificate"),
    ("status", "classified"),
])
def test_layer_metadata_drift_blocks_promotion(field, value):
    with pytest.raises(ValueError, match="metadata-mismatch"):
        resolve_layer_theorem(replace(_intrinsic_layer(), **{field: value}))


@pytest.mark.parametrize("field,value", [
    ("name", _EqualToEverything()),
    ("name", _MisleadingLayerName()),
    ("role", _EqualToEverything()),
    ("certificate", _EqualToEverything()),
    ("status", _EqualToEverything()),
])
def test_overloaded_layer_metadata_cannot_bypass_exact_identity(field, value):
    forged = replace(_intrinsic_layer(), **{field: value})
    with pytest.raises(TypeError, match="metadata-type"):
        resolve_layer_theorem(forged)


@pytest.mark.parametrize("field,value", [
    ("layer", "other-layer"),
    ("role", "other-role"),
    ("certificate", "other-cert"),
    ("theorem_id", "THM-R8-FORGED"),
    ("statement_digest", "1" * 64),
    ("artifact_digest", "2" * 64),
    ("proof_rules", ("eq-refl",)),
    ("native_laws", ()),
    ("semantic_carrier", "forged.carrier"),
    ("bridge_id", "forged.bridge"),
    ("boundary", "forged boundary"),
])
def test_every_static_contract_field_is_bound_by_trusted_manifest(field, value):
    base = theorem_contract_registry()["intrinsic-resonance"]
    with pytest.raises(ValueError, match="trusted-binding-mismatch"):
        build_theorem_contract_registry((replace(base, **{field: value}),))


def test_forged_theorem_provider_is_rejected():
    base = theorem_contract_registry()["intrinsic-resonance"]
    forged = replace(intrinsic_resonance_theorem(), boundary="forged")
    with pytest.raises(ValueError, match="handler-mismatch"):
        build_theorem_contract_registry((replace(base, theorem_provider=lambda: forged),))


def test_forged_handler_identity_is_rejected():
    base = theorem_contract_registry()["intrinsic-resonance"]
    with pytest.raises(ValueError, match="handler-id-mismatch"):
        build_theorem_contract_registry((replace(base, handler_id="forged.handler"),))


def test_forged_bridge_provider_is_rejected():
    base = theorem_contract_registry()["intrinsic-resonance"]
    forged = replace(proof_elaboration_bridge_report(), binding_digest="0" * 64)
    with pytest.raises(ValueError, match="handler-mismatch"):
        build_theorem_contract_registry((replace(base, bridge_provider=lambda: forged),))


def test_poisoned_cached_bridge_cannot_promote_or_reach_readiness(monkeypatch):
    report = proof_elaboration_bridge_report()
    forged = replace(
        report, source_digests=(), binding_digest="0" * 64, toolchain="",
        manifest_checked=False, lean_checked=False,
    )
    monkeypatch.setattr(bridge_module, "_cached_default_report", lambda _: forged)
    checked = bridge_module.proof_elaboration_bridge_report()
    assert checked.status == "blocked"
    assert checked.diagnostics == "cached-r10-bridge-integrity-mismatch"
    with pytest.raises(ValueError, match="layer-theorem-bridge-rejected"):
        resolve_layer_theorem(_intrinsic_layer())


@pytest.mark.parametrize("field", ["theorem_verifier", "bridge_verifier"])
def test_fail_open_verifier_replacement_is_rejected(field):
    base = theorem_contract_registry()["intrinsic-resonance"]
    with pytest.raises(ValueError, match="handler-mismatch"):
        build_theorem_contract_registry((replace(base, **{field: lambda *args: True}),))


@pytest.mark.parametrize("field,value,reason", [
    ("role", "", "invalid-theorem-contract-text"),
    ("statement_digest", "short", "invalid-theorem-contract-digest"),
    ("artifact_digest", "z" * 64, "invalid-theorem-contract-digest"),
    ("proof_rules", ["eq-refl"], "invalid-theorem-contract-closure"),
    ("theorem_provider", None, "invalid-theorem-contract-provider"),
])
def test_malformed_contract_shape_is_rejected(field, value, reason):
    base = theorem_contract_registry()["intrinsic-resonance"]
    with pytest.raises(ValueError, match=reason):
        build_theorem_contract_registry((replace(base, **{field: value}),))


def test_duplicate_layer_contract_is_rejected():
    base = theorem_contract_registry()["intrinsic-resonance"]
    with pytest.raises(ValueError, match="duplicate-theorem-contract-layer"):
        build_theorem_contract_registry((base, base))


def test_duplicate_theorem_id_is_rejected_before_dispatch():
    base = theorem_contract_registry()["intrinsic-resonance"]
    duplicate = _different_contract(base, theorem_id=base.theorem_id)
    with pytest.raises(ValueError, match="duplicate-theorem-contract-theorem-id"):
        build_theorem_contract_registry((base, duplicate))


def test_duplicate_artifact_is_rejected_before_dispatch():
    base = theorem_contract_registry()["intrinsic-resonance"]
    duplicate = _different_contract(base, artifact_digest=base.artifact_digest)
    with pytest.raises(ValueError, match="duplicate-theorem-contract-artifact"):
        build_theorem_contract_registry((base, duplicate))


def test_duplicate_contract_digest_is_rejected(monkeypatch):
    base = theorem_contract_registry()["intrinsic-resonance"]
    duplicate = _different_contract(base)
    monkeypatch.setattr(contracts_module, "theorem_contract_digest", lambda _: "0" * 64)
    with pytest.raises(ValueError, match="duplicate-theorem-contract-contract"):
        build_theorem_contract_registry((base, duplicate))


def test_readiness_row_exposes_only_contract_derived_evidence():
    row = next(item for item in layer_derivations() if item.layer == "intrinsic-resonance")
    evidence = resolve_layer_theorem(_intrinsic_layer())
    assert row.statement_digest == evidence.statement_digest
    assert row.semantic_carrier == evidence.semantic_carrier
    assert row.bridge_id == evidence.bridge_id
    assert row.bridge_digest == evidence.bridge_digest
    assert row.contract_digest == evidence.contract_digest
    assert not hasattr(contracts_module, "THEOREM_LAYERS")
