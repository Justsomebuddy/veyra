"""Fail-closed theorem-promotion contracts for Essence/Core layers."""
from __future__ import annotations

from collections.abc import Iterable, Mapping
import logging
from types import MappingProxyType
from typing import NoReturn

from .layer_theorem_contract_handlers import (
    INTRINSIC_TRANSPORT_CARRIER,
    R10_HANDLER_ID,
    R10_LEAN_BRIDGE_ID,
    R13_HANDLER_ID,
    R13_LEAN_BRIDGE_ID,
    R13_TRANSPORT_CARRIER,
    normalize_theorem_evidence,
    validate_contract_handlers,
    verify_intrinsic_contract,
    verify_r10_bridge,
    verify_r13_bridge,
    verify_r13_contract,
)
from .layer_theorem_contract_types import (
    LayerLike,
    LayerTheoremContract,
    TheoremContractCapabilityBlocked,
    VerifiedLayerTheorem,
    theorem_contract_digest,
)
from .proof_elaboration_bridge import proof_elaboration_bridge_report
from .intrinsic_observer_echo_formal_bridge import (
    intrinsic_observer_echo_contract_bridge_report,
)
from .intrinsic_observer_echo_theorem import (
    BOUNDARY as R13_BOUNDARY,
    EXPECTED_ARTIFACT_DIGEST as R13_ARTIFACT_DIGEST,
    EXPECTED_STATEMENT_DIGEST as R13_STATEMENT_DIGEST,
    NATIVE_LAWS as R13_NATIVE_LAWS,
    PROOF_RULES as R13_PROOF_RULES,
    THEOREM_ID as R13_THEOREM_ID,
    intrinsic_observer_echo_theorem,
)
from .proof_core_resonance import (
    BOUNDARY,
    intrinsic_resonance_theorem,
)
from src.platform_capabilities import Capability, capability_status

logger = logging.getLogger(__name__)


def _reject(reason: str) -> NoReturn:
    logger.error("layer_theorem_contracts rejected reason=%s", reason)
    raise ValueError(reason)


def _reject_type(reason: str) -> NoReturn:
    logger.error("layer_theorem_contracts type rejected reason=%s", reason)
    raise TypeError(reason)


def _validate_contract_shape(contract: LayerTheoremContract) -> None:
    logger.debug("layer_theorem_contracts._validate_contract_shape entry layer=%r", contract.layer)
    text_fields = (
        contract.layer, contract.role, contract.certificate, contract.theorem_id,
        contract.handler_id, contract.semantic_carrier, contract.bridge_id, contract.boundary,
    )
    digests = (contract.statement_digest, contract.artifact_digest)
    closures = (contract.proof_rules, contract.native_laws)
    providers = (
        contract.theorem_provider, contract.theorem_verifier,
        contract.bridge_provider, contract.bridge_verifier,
    )
    if any(type(item) is not str or not item for item in text_fields):
        _reject("invalid-theorem-contract-text")
    if any(
        type(item) is not str or len(item) != 64
        or any(char not in "0123456789abcdef" for char in item)
        for item in digests
    ):
        _reject("invalid-theorem-contract-digest")
    if contract.executable_digest is not None and (
        type(contract.executable_digest) is not str
        or len(contract.executable_digest) != 64
        or any(char not in "0123456789abcdef" for char in contract.executable_digest)
    ):
        _reject("invalid-theorem-contract-executable-digest")
    if any(type(items) is not tuple or any(type(item) is not str for item in items) for items in closures):
        _reject("invalid-theorem-contract-closure")
    if any(not callable(item) for item in providers):
        _reject("invalid-theorem-contract-provider")
    logger.debug("layer_theorem_contracts._validate_contract_shape exit layer=%s", contract.layer)


def build_theorem_contract_registry(
    contracts: Iterable[LayerTheoremContract],
) -> Mapping[str, LayerTheoremContract]:
    """Build an immutable registry and reject every ambiguous reuse surface."""
    logger.debug("build_theorem_contract_registry entry")
    rows = tuple(contracts)
    for contract in rows:
        if type(contract) is not LayerTheoremContract:
            _reject_type("theorem-contract-type")
        _validate_contract_shape(contract)
    uniqueness = {
        "layer": [item.layer for item in rows],
        "theorem-id": [item.theorem_id for item in rows],
        "artifact": [item.artifact_digest for item in rows],
        "contract": [theorem_contract_digest(item) for item in rows],
    }
    for field, values in uniqueness.items():
        if len(values) != len(set(values)):
            logger.error("build_theorem_contract_registry duplicate field=%s", field)
            _reject(f"duplicate-theorem-contract-{field}")
    for contract in rows:
        validate_contract_handlers(contract, theorem_contract_digest)
    result = MappingProxyType({item.layer: item for item in rows})
    logger.debug("build_theorem_contract_registry exit count=%d", len(result))
    return result


_INTRINSIC_CONTRACT = LayerTheoremContract(
    layer="intrinsic-resonance",
    role="proof-carrying intrinsic recurrence weave witness",
    certificate="proof_carrying_core_r7",
    theorem_id="THM-R7-004",
    statement_digest="2c8cf08aa670cdcd3ddac628b303d6f48be2bcac63f76761daaf7d0d7f91e145",
    artifact_digest="aca33a6a76af8b0f9958e722a11133dc851876ba718dce59c2486fba8232e362",
    proof_rules=("forall-intro", "native-law", "resonance-intro"),
    native_laws=("weave-unit-right",),
    handler_id=R10_HANDLER_ID,
    semantic_carrier=INTRINSIC_TRANSPORT_CARRIER,
    bridge_id=R10_LEAN_BRIDGE_ID,
    boundary=BOUNDARY,
    theorem_provider=intrinsic_resonance_theorem,
    theorem_verifier=verify_intrinsic_contract,
    bridge_provider=proof_elaboration_bridge_report,
    bridge_verifier=verify_r10_bridge,
)
_INTRINSIC_OBSERVER_ECHO_CONTRACT = LayerTheoremContract(
    layer="intrinsic-observer-echo",
    role="proof-carrying explicitly bounded readiness-conditioned intrinsic observer echo",
    certificate="intrinsic_observer_echo_r13",
    theorem_id=R13_THEOREM_ID,
    statement_digest=R13_STATEMENT_DIGEST,
    artifact_digest=R13_ARTIFACT_DIGEST,
    proof_rules=R13_PROOF_RULES,
    native_laws=R13_NATIVE_LAWS,
    handler_id=R13_HANDLER_ID,
    semantic_carrier=R13_TRANSPORT_CARRIER,
    bridge_id=R13_LEAN_BRIDGE_ID,
    boundary=R13_BOUNDARY,
    theorem_provider=intrinsic_observer_echo_theorem,
    theorem_verifier=verify_r13_contract,
    bridge_provider=intrinsic_observer_echo_contract_bridge_report,
    bridge_verifier=verify_r13_bridge,
    executable_digest="ee12d603d86b0a1387bcba3e9c6a76fbba983940908e5ec07a0b5d856a9d5673",
)
_THEOREM_CONTRACTS: Mapping[str, LayerTheoremContract] | None = None


def _theorem_contracts() -> Mapping[str, LayerTheoremContract]:
    """Build the immutable registry once, lazily.

    Building at import time made every ``import src.core`` fail closed on any
    interpreter whose bytecode did not match the pinned executable digests.
    Validation still runs exactly once before first use, so the fail-closed
    property is preserved; it just no longer poisons unrelated imports.
    """
    global _THEOREM_CONTRACTS
    if _THEOREM_CONTRACTS is None:
        logger.debug("layer_theorem_contracts registry lazy build entry")
        _THEOREM_CONTRACTS = build_theorem_contract_registry(
            (_INTRINSIC_CONTRACT, _INTRINSIC_OBSERVER_ECHO_CONTRACT),
        )
        logger.debug(
            "layer_theorem_contracts registry lazy build exit count=%d",
            len(_THEOREM_CONTRACTS),
        )
    return _THEOREM_CONTRACTS


def theorem_contract_registry() -> Mapping[str, LayerTheoremContract]:
    """Return the immutable production theorem-promotion registry."""
    logger.debug("theorem_contract_registry entry")
    result = _theorem_contracts()
    logger.debug("theorem_contract_registry exit count=%d", len(result))
    return result


def resolve_layer_theorem(
    layer: LayerLike, registry: Mapping[str, LayerTheoremContract] | None = None,
) -> VerifiedLayerTheorem:
    """Resolve only the requested layer's exact contract, with no fallback."""
    logger.debug("resolve_layer_theorem entry type=%s", type(layer).__name__)
    if not capability_status(Capability.LEAN_TOOLCHAIN_CANDIDATE).available:
        logger.debug("resolve_layer_theorem blocked missing lean candidate capability")
        raise TheoremContractCapabilityBlocked(
            "theorem-contract-capability-blocked:"
            "lean-toolchain-candidate-required",
        )
    actual_layer = (layer.name, layer.role, layer.certificate, layer.status)
    if any(type(item) is not str for item in actual_layer):
        _reject_type("layer-theorem-contract-metadata-type")
    logger.debug("resolve_layer_theorem metadata layer=%s", actual_layer[0])
    contracts = theorem_contract_registry() if registry is None else registry
    validated = build_theorem_contract_registry(contracts.values())
    if set(contracts) != set(validated):
        _reject("theorem-contract-registry-key-mismatch")
    contract = validated.get(actual_layer[0])
    if contract is None:
        logger.error("resolve_layer_theorem unbound layer=%s", actual_layer[0])
        _reject("unbound-theorem-contract")
    expected_layer = (contract.layer, contract.role, contract.certificate, "ready")
    if actual_layer != expected_layer:
        logger.error("resolve_layer_theorem layer metadata mismatch actual=%r", actual_layer)
        _reject("layer-theorem-contract-metadata-mismatch")
    theorem = contract.theorem_provider()
    if not contract.theorem_verifier(contract, theorem):
        _reject("layer-theorem-provider-rejected")
    actual_theorem = normalize_theorem_evidence(contract, theorem)
    actual_contract_fields = (
        *actual_theorem[:3],
        *actual_theorem[4:],
    )
    expected_contract_fields = (
        contract.theorem_id, contract.statement_digest, contract.artifact_digest,
        contract.proof_rules, contract.native_laws, contract.boundary,
    )
    if actual_contract_fields != expected_contract_fields:
        logger.error(
            "resolve_layer_theorem theorem metadata mismatch theorem=%s",
            actual_theorem[0],
        )
        _reject("layer-theorem-contract-evidence-mismatch")
    bridge = contract.bridge_provider()
    if not contract.bridge_verifier(contract, bridge, contract.artifact_digest):
        _reject("layer-theorem-bridge-rejected")
    bridge_digest = getattr(bridge, "binding_digest", None)
    if type(bridge_digest) is not str or len(bridge_digest) != 64:
        _reject("layer-theorem-bridge-digest-invalid")
    result = VerifiedLayerTheorem(
        contract.theorem_id, contract.statement_digest, contract.artifact_digest,
        actual_theorem[3], contract.proof_rules, contract.native_laws,
        contract.semantic_carrier, contract.bridge_id, bridge_digest,
        theorem_contract_digest(contract), contract.boundary,
    )
    logger.debug("resolve_layer_theorem exit theorem=%s", result.theorem_id)
    return result
