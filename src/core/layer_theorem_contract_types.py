"""Closed data types and canonical serialization for R8 promotion contracts."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import logging
from typing import Protocol

from src.platform_capabilities import CapabilityUnavailableError

from .proof_core_codec import digest_data

logger = logging.getLogger(__name__)
STATEMENT_DOMAIN = "veyra-layer-theorem-statement-v1"
CONTRACT_DOMAIN = "veyra-layer-theorem-contract-v1"


class LayerLike(Protocol):
    """Structural layer fields required by a promotion contract."""

    name: str
    role: str
    certificate: str
    status: str


TheoremProvider = Callable[[], object]
TheoremVerifier = Callable[["LayerTheoremContract", object], bool]
BridgeProvider = Callable[[], object]
BridgeVerifier = Callable[["LayerTheoremContract", object, str], bool]


class TheoremContractCapabilityBlocked(CapabilityUnavailableError):
    """A production theorem contract requires an unavailable exact toolchain."""

    def __init__(self, capability: str, detail: str) -> None:
        logger.debug(
            "TheoremContractCapabilityBlocked.__init__ entry capability=%s",
            capability,
        )
        self.capability = capability
        self.detail = detail
        super().__init__(
            f"theorem-contract-capability-blocked:{capability}:{detail}",
        )
        logger.debug(
            "TheoremContractCapabilityBlocked.__init__ exit capability=%s",
            capability,
        )


@dataclass(frozen=True)
class LayerTheoremContract:
    """Exact static and executable binding for one theorem-derived layer."""

    layer: str
    role: str
    certificate: str
    theorem_id: str
    statement_digest: str
    artifact_digest: str
    proof_rules: tuple[str, ...]
    native_laws: tuple[str, ...]
    handler_id: str
    semantic_carrier: str
    bridge_id: str
    boundary: str
    theorem_provider: TheoremProvider
    theorem_verifier: TheoremVerifier
    bridge_provider: BridgeProvider
    bridge_verifier: BridgeVerifier
    executable_digest: str | None = None


@dataclass(frozen=True)
class VerifiedLayerTheorem:
    """Contract-derived theorem evidence safe to expose in readiness rows."""

    theorem_id: str
    statement_digest: str
    artifact_digest: str
    proof_digest: str
    proof_rules: tuple[str, ...]
    native_laws: tuple[str, ...]
    semantic_carrier: str
    bridge_id: str
    bridge_digest: str
    contract_digest: str
    boundary: str


def contract_data(contract: LayerTheoremContract) -> dict[str, object]:
    """Serialize only the static fields covered by the trusted digest."""
    logger.debug("layer_theorem_contract_types.contract_data entry layer=%s", contract.layer)
    result: dict[str, object] = {
        "layer": contract.layer,
        "role": contract.role,
        "certificate": contract.certificate,
        "theorem_id": contract.theorem_id,
        "statement_digest": contract.statement_digest,
        "artifact_digest": contract.artifact_digest,
        "proof_rules": list(contract.proof_rules),
        "native_laws": list(contract.native_laws),
        "handler_id": contract.handler_id,
        "semantic_carrier": contract.semantic_carrier,
        "bridge_id": contract.bridge_id,
        "boundary": contract.boundary,
    }
    if contract.executable_digest is not None:
        result["executable_digest"] = contract.executable_digest
    logger.debug("layer_theorem_contract_types.contract_data exit layer=%s", contract.layer)
    return result


def theorem_contract_digest(contract: LayerTheoremContract) -> str:
    """Digest static promotion fields, including any executable-manifest pin."""
    logger.debug("layer_theorem_contract_types.theorem_contract_digest entry layer=%s", contract.layer)
    result = digest_data(contract_data(contract), CONTRACT_DOMAIN)
    logger.debug("layer_theorem_contract_types.theorem_contract_digest exit result=%s", result)
    return result
