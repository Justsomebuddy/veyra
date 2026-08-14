"""Receipt-backed classification of every Essence/Core layer."""
from __future__ import annotations

from dataclasses import dataclass
import logging
from collections.abc import Collection, Iterable, Mapping

from src.platform_capabilities import Capability, CapabilityStatus

from .essence import VeyraCoreLayer, core_layers
from .layer_theorem_contracts import (
    LayerTheoremContract,
    resolve_layer_theorem,
    theorem_contract_layers,
    theorem_contract_registry,
    validate_production_theorem_layer_metadata,
)
from .layer_theorem_contract_types import TheoremContractCapabilityBlocked
from .semantic_kernel import DerivationReceipt, axiom_closure, evaluate_native, replay_receipts

logger = logging.getLogger(__name__)

# Sources are executable witnesses, not hand-authored axiom dependency tuples.
WITNESS_SOURCES = {
    "echo": "echo(nod:a,nod:b,observer:kind)",
    "language": "echo(mode(breath(tact(nod:a,nod:a))),mode(breath(tact(nod:b,nod:b))),observer:length)",
    "foundational-kernel": "echo(mode(breath(tact(nod:a,nod:a))),mode(breath(tact(nod:a,nod:a))),observer:trace)",
    "native-runtime": "mode(breath(tact(nod:a,nod:a)))",
}
SHADOW_LAYERS = frozenset({
    "resonance", "native-number", "aura-weight", "balance", "ratio-order", "equation", "polynomial",
    "calculus-depth", "trigonometry-identities", "phase-equations", "linear-algebra", "statistics-inference",
    "statistics-concentration", "transcendental-limit", "convergence-algebra", "real-analysis-structure",
    "weighted-echo-measure", "science-domain-certificates", "model-diagnostics", "scale-memory-log",
    "compression-algebra", "category-like", "topology-echo", "likelihood-geometry", "native-number-theorem",
})
META_LAYERS = frozenset({"proof-pressure", "diagnostics", "proof-discipline", "classical-benchmark", "deduction-chain"})


@dataclass(frozen=True)
class LayerDerivation:
    """One explicitly classified layer and any checked semantic proof graph."""
    layer: str
    certificate: str
    classification: str
    status: str
    source: str
    receipts: tuple[DerivationReceipt, ...]
    axioms: tuple[str, ...]
    boundary: str
    theorem_id: str = ""
    proof_digest: str = ""
    proof_rules: tuple[str, ...] = ()
    native_laws: tuple[str, ...] = ()
    statement_digest: str = ""
    semantic_carrier: str = ""
    bridge_id: str = ""
    bridge_digest: str = ""
    contract_digest: str = ""


@dataclass(frozen=True)
class LayerDerivationReport:
    """Coverage report for the exact current core-layer registry."""
    rows: tuple[LayerDerivation, ...]

    def summary(self) -> dict[str, int | bool]:
        """Return compact classification and receipt counters."""
        logger.debug("LayerDerivationReport.summary entry rows=%d", len(self.rows))
        theorem_blocked = sum(
            row.classification == "theorem-derived" and row.status == "blocked"
            for row in self.rows
        )
        theorem_ready = all(
            row.status == "ready"
            for row in self.rows
            if row.classification == "theorem-derived"
        )
        classifications_complete = all(
            row.classification
            in {"theorem-derived", "receipt-backed-witness", "shadow", "meta"}
            for row in self.rows
        )
        result: dict[str, int | bool] = {
            "layers": len(self.rows),
            "theorem_derived": sum(row.classification == "theorem-derived" for row in self.rows),
            "theorem_blocked": theorem_blocked,
            "witness_backed": sum(row.classification == "receipt-backed-witness" for row in self.rows),
            "shadow": sum(row.classification == "shadow" for row in self.rows),
            "meta": sum(row.classification == "meta" for row in self.rows),
            "receipt_backed": sum(bool(row.receipts) for row in self.rows),
            "complete": classifications_complete and theorem_ready,
        }
        logger.debug("LayerDerivationReport.summary exit result=%r", result)
        return result


def _registry_names(
    theorem_layers: Collection[str],
) -> frozenset[str]:
    logger.debug("_registry_names entry")
    result = frozenset(theorem_layers) | frozenset(WITNESS_SOURCES) | SHADOW_LAYERS | META_LAYERS
    logger.debug("_registry_names exit count=%d", len(result))
    return result


def _validate_registry(
    layers: tuple[VeyraCoreLayer, ...],
    theorem_layers: Collection[str],
) -> None:
    logger.debug("_validate_registry entry layers=%d", len(layers))
    groups = (frozenset(theorem_layers), frozenset(WITNESS_SOURCES), SHADOW_LAYERS, META_LAYERS)
    overlap = frozenset(item for index, group in enumerate(groups) for other in groups[index + 1:] for item in group & other)
    actual = frozenset(layer.name for layer in layers)
    expected = _registry_names(theorem_layers)
    errors = []
    if overlap:
        errors.append("overlap=" + ",".join(sorted(overlap)))
    if actual - expected:
        errors.append("unclassified=" + ",".join(sorted(actual - expected)))
    if expected - actual:
        errors.append("stale=" + ",".join(sorted(expected - actual)))
    if len(actual) != len(layers):
        errors.append("duplicate-layer-name")
    if errors:
        logger.error("_validate_registry failure errors=%r", errors)
        raise ValueError("layer classification registry drift: " + ";".join(errors))
    logger.debug("_validate_registry exit valid")


def _witness_row(layer: VeyraCoreLayer) -> LayerDerivation:
    logger.debug("_witness_row entry layer=%s", layer.name)
    source = WITNESS_SOURCES[layer.name]
    semantic = evaluate_native(source)
    checked = replay_receipts(source, semantic.receipts)
    if semantic.status != "ready" or not checked.ok:
        logger.error("_witness_row invalid layer=%s status=%s errors=%r", layer.name, semantic.status, checked.errors)
        raise ValueError(f"invalid proof witness for {layer.name}")
    result = LayerDerivation(layer.name, layer.certificate, "receipt-backed-witness", semantic.status, source,
                             semantic.receipts, axiom_closure(semantic.receipts),
                             "axioms derive only from this replayed native witness, not the whole named layer/certificate")
    logger.debug("_witness_row exit layer=%s receipts=%d axioms=%r", layer.name, len(result.receipts), result.axioms)
    return result


def _theorem_row(
    layer: VeyraCoreLayer,
    theorem_contracts: Mapping[str, LayerTheoremContract],
) -> LayerDerivation:
    logger.debug("_theorem_row entry layer=%s", layer.name)
    theorem = resolve_layer_theorem(layer, theorem_contracts)
    result = LayerDerivation(
        layer.name, layer.certificate, "theorem-derived", "ready", "", (), (),
        theorem.boundary, theorem.theorem_id, theorem.proof_digest,
        theorem.proof_rules, theorem.native_laws, theorem.statement_digest,
        theorem.semantic_carrier, theorem.bridge_id, theorem.bridge_digest,
        theorem.contract_digest,
    )
    logger.debug("_theorem_row exit theorem=%s digest=%s", result.theorem_id, result.proof_digest)
    return result


def _blocked_theorem_row(
    layer: VeyraCoreLayer,
    capability: CapabilityStatus,
) -> LayerDerivation:
    """Expose truthful non-readiness without constructing executable contracts."""
    logger.debug(
        "_blocked_theorem_row entry layer=%s capability=%s",
        layer.name,
        capability.capability.value,
    )
    validate_production_theorem_layer_metadata(layer)
    result = LayerDerivation(
        layer.name,
        layer.certificate,
        "theorem-derived",
        "blocked",
        "",
        (),
        (),
        "production theorem evidence unavailable: "
        f"{capability.capability.value}:{capability.detail}; "
        "no theorem handler, bridge, or bytecode-bound registry was resolved",
    )
    logger.debug("_blocked_theorem_row exit layer=%s", layer.name)
    return result


def _nonproof_row(layer: VeyraCoreLayer, classification: str) -> LayerDerivation:
    logger.debug("_nonproof_row entry layer=%s class=%s", layer.name, classification)
    boundary = ("finite external/shadow artifact; no kernel derivation or axiom use claimed"
                if classification == "shadow" else
                "ledger, diagnostic, or orchestration metadata; no theorem axioms claimed")
    result = LayerDerivation(layer.name, layer.certificate, classification, "classified", "", (), (), boundary)
    logger.debug("_nonproof_row exit layer=%s", layer.name)
    return result


def layer_derivations(layers: Iterable[VeyraCoreLayer] | None = None) -> tuple[LayerDerivation, ...]:
    """Classify exactly all current layers, refusing registry drift or fallback."""
    logger.debug("layer_derivations entry custom=%s", layers is not None)
    current = tuple(core_layers() if layers is None else layers)
    theorem_layers = theorem_contract_layers()
    capability = None
    try:
        contracts = theorem_contract_registry()
    except TheoremContractCapabilityBlocked as blocked:
        capability = CapabilityStatus(
            Capability(blocked.capability),
            False,
            blocked.detail,
        )
        contracts = None
        logger.warning(
            "layer_derivations theorem registry blocked capability=%s detail=%s",
            capability.capability.value,
            capability.detail,
        )
    _validate_registry(current, theorem_layers if contracts is None else contracts)
    rows = []
    for layer in current:
        if layer.name in theorem_layers:
            if contracts is not None:
                rows.append(_theorem_row(layer, contracts))
            elif capability is not None:
                rows.append(_blocked_theorem_row(layer, capability))
            else:  # pragma: no cover - try/except assigns one branch exactly.
                logger.error("layer_derivations missing theorem registry state")
                raise RuntimeError("missing-theorem-registry-state")
        elif layer.name in WITNESS_SOURCES:
            rows.append(_witness_row(layer))
        elif layer.name in SHADOW_LAYERS:
            rows.append(_nonproof_row(layer, "shadow"))
        elif layer.name in META_LAYERS:
            rows.append(_nonproof_row(layer, "meta"))
        else:
            logger.error("layer_derivations unreachable unclassified=%s", layer.name)
            raise ValueError(f"unclassified layer {layer.name}")
    result = tuple(rows)
    logger.debug("layer_derivations exit count=%d", len(result))
    return result


def layer_derivation_report() -> LayerDerivationReport:
    """Build the strict current-layer derivation report."""
    logger.debug("layer_derivation_report entry")
    result = LayerDerivationReport(layer_derivations())
    logger.debug("layer_derivation_report exit summary=%r", result.summary())
    return result
