"""Certificate gate for fail-closed R8 theorem-layer promotion contracts."""
from __future__ import annotations

import logging
from types import MappingProxyType

from ..certify_types import Certificate
from ..kernel.essence import core_layers
from ..layer_theorem_contracts import (
    INTRINSIC_TRANSPORT_CARRIER, R10_LEAN_BRIDGE_ID, resolve_layer_theorem,
    theorem_contract_digest, theorem_contract_registry,
)

logger = logging.getLogger(__name__)


def certify_theorem_promotion_contract_r8() -> Certificate:
    """Gate exact layer/theorem/carrier/bridge dispatch and exposed evidence."""
    logger.debug("certify_theorem_promotion_contract_r8 entry")
    registry = theorem_contract_registry()
    layer = next(item for item in core_layers() if item.name == "intrinsic-resonance")
    contract = registry[layer.name]
    evidence = resolve_layer_theorem(layer, registry)
    immutable = type(registry) is type(MappingProxyType({}))
    passed = (
        immutable
        and tuple(registry) == ("intrinsic-resonance", "intrinsic-observer-echo")
        and contract.layer == layer.name and contract.role == layer.role
        and contract.certificate == layer.certificate
        and evidence.theorem_id == "THM-R7-004"
        and evidence.semantic_carrier == INTRINSIC_TRANSPORT_CARRIER
        and evidence.bridge_id == R10_LEAN_BRIDGE_ID
        and evidence.contract_digest == theorem_contract_digest(contract)
        and all(len(value) == 64 for value in (
            evidence.statement_digest, evidence.proof_digest,
            evidence.bridge_digest, evidence.contract_digest,
        ))
        and "cyclic phase" in evidence.boundary
    )
    detail = (
        f"contracts={len(registry)} theorem={evidence.theorem_id} "
        f"carrier={evidence.semantic_carrier} contract={evidence.contract_digest[:16]}"
    )
    result = Certificate(
        "theorem_promotion_contract_r8",
        "exact immutable layer-to-theorem/carrier/Lean-bridge promotion contract",
        passed, detail, 2,
    )
    if not passed:
        logger.error("certify_theorem_promotion_contract_r8 blocked detail=%s", detail)
    logger.debug("certify_theorem_promotion_contract_r8 exit result=%r", result)
    return result
