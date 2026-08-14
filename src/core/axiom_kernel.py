"""Unified executable axiom kernel for Veyra F1."""
from __future__ import annotations
from dataclasses import dataclass
import logging
from collections.abc import Iterable
from .essence import VeyraCoreLayer
from .language import interpret_veyra
from .layer_derivations import layer_derivations
logger = logging.getLogger(__name__)

@dataclass(frozen=True)
class KernelAxiom:
    """One primitive axiom with an executable witness expression."""
    axiom_id: str
    primitive: str
    statement: str
    witness_source: str
    expected_status: str

@dataclass(frozen=True)
class AxiomWitness:
    """Execution result for a kernel-axiom witness."""
    axiom_id: str
    source: str
    status: str
    kind: str
    executable: bool
    obstruction: str = ""

@dataclass(frozen=True)
class LayerAxiomUse:
    """A dependency row derived from a checked witness graph or empty boundary."""
    layer: str
    certificate: str
    axioms: tuple[str, ...]
    derivation: str
    boundary: str
    status: str = "classified"

@dataclass(frozen=True)
class AxiomKernelReport:
    """Readiness report for F1: shared axioms plus layer dependency rows."""
    axioms: tuple[KernelAxiom, ...]
    witnesses: tuple[AxiomWitness, ...]
    layers: tuple[LayerAxiomUse, ...]
    missing_axioms: tuple[str, ...]
    unnamed_layers: tuple[str, ...]

    @property
    def ready(self) -> bool:
        """Return whether all axioms execute and every layer names dependencies."""
        logger.debug("AxiomKernelReport.ready entry")
        allowed_statuses = {
            "theorem-derived": "ready",
            "receipt-derived-witness": "ready",
            "shadow": "classified",
            "meta": "classified",
        }
        result = (
            not self.missing_axioms
            and not self.unnamed_layers
            and all(
                allowed_statuses.get(row.derivation) == row.status
                for row in self.layers
            )
        )
        logger.debug("AxiomKernelReport.ready exit result=%s", result)
        return result

    def summary(self) -> dict[str, int | bool]:
        """Return compact kernel counters."""
        logger.debug("AxiomKernelReport.summary entry")
        result: dict[str, int | bool] = {
            "axioms": len(self.axioms),
            "witnesses": len(self.witnesses),
            "layers": len(self.layers),
            "theorem_derived": sum(row.derivation == "theorem-derived" for row in self.layers),
            "theorem_blocked": sum(
                row.derivation == "theorem-derived" and row.status == "blocked"
                for row in self.layers
            ),
            "receipt_derived_witness": sum(row.derivation == "receipt-derived-witness" for row in self.layers),
            "shadow": sum(row.derivation == "shadow" for row in self.layers),
            "meta": sum(row.derivation == "meta" for row in self.layers),
            "missing_axioms": len(self.missing_axioms),
            "unnamed_layers": len(self.unnamed_layers),
            "ready": self.ready,
        }
        logger.debug("AxiomKernelReport.summary exit result=%r", result)
        return result

def unified_axiom_kernel() -> tuple[KernelAxiom, ...]:
    """Return the minimal F1 executable axiom list."""
    logger.debug("unified_axiom_kernel entry")
    rows = (
        ("AX-REZ", "rez", "distinction leaves a residue token", "rez:cut", "ready"),
        ("AX-NOD", "nod", "residue may be addressed as a nod", "nod:a", "ready"),
        ("AX-TACT", "tact", "two nods may form an ordered contact", "tact(nod:a,nod:b)", "ready"),
        ("AX-BREATH", "breath", "nonempty finite contacts assemble as breath", "breath(tact(nod:a,nod:b))", "ready"),
        ("AX-MODE", "mode", "a breath can be wrapped as a recurrent mode", "mode(breath(tact(nod:a,nod:a)))", "ready"),
        ("AX-OBSERVER", "observer", "observer labels choose visible responses", "observer:kind", "ready"),
        ("AX-ECHO", "echo", "echo is observer-indexed indistinguishability", "echo(nod:a,nod:b,observer:kind)", "ready"),
        ("AX-OBSTRUCTION", "obstruction", "blocked inference is retained as a first-class result", "echo(nod:a,nod:b,observer:trace)", "blocked"),
    )
    result = tuple(KernelAxiom(*row) for row in rows)
    logger.debug("unified_axiom_kernel exit count=%d", len(result))
    return result

def axiom_witness_rows(axioms: Iterable[KernelAxiom] | None = None) -> tuple[AxiomWitness, ...]:
    """Execute every kernel-axiom witness through the Core Language."""
    logger.debug("axiom_witness_rows entry")
    rows = []
    for axiom in tuple(axioms or unified_axiom_kernel()):
        interp = interpret_veyra(axiom.witness_source, "logic")
        kind = "none" if interp.check.kind is None else interp.check.kind.value
        executable = interp.check.status == axiom.expected_status
        rows.append(AxiomWitness(axiom.axiom_id, axiom.witness_source, interp.check.status, kind, executable, interp.check.obstruction))
    result = tuple(rows)
    logger.debug("axiom_witness_rows exit count=%d", len(result))
    return result

def layer_axiom_dependencies(layers: Iterable[VeyraCoreLayer] | None = None) -> tuple[LayerAxiomUse, ...]:
    """Derive axiom use from checked receipts; never fill dependency tuples."""
    logger.debug("layer_axiom_dependencies entry")
    derived = layer_derivations(tuple(layers) if layers is not None else None)
    result = tuple(
        LayerAxiomUse(
            row.layer,
            row.certificate,
            row.axioms,
            "receipt-derived-witness"
            if row.classification == "receipt-backed-witness"
            else row.classification,
            row.boundary,
            row.status,
        )
        for row in derived
    )
    logger.debug("layer_axiom_dependencies exit count=%d", len(result))
    return result

def axiom_kernel_report() -> AxiomKernelReport:
    """Build the F1 report: axioms, witnesses, and all layer dependencies."""
    logger.debug("axiom_kernel_report entry")
    axioms = unified_axiom_kernel()
    witnesses = axiom_witness_rows(axioms)
    layers = layer_axiom_dependencies()
    axiom_ids = {a.axiom_id for a in axioms}
    missing = tuple(row.axiom_id for row in witnesses if not row.executable)
    unnamed = tuple(row.layer for row in layers if any(ax not in axiom_ids for ax in row.axioms) or (row.derivation == "receipt-derived-witness" and not row.axioms))
    result = AxiomKernelReport(axioms, witnesses, layers, missing, unnamed)
    logger.debug("axiom_kernel_report exit summary=%r", result.summary())
    return result

def axiom_kernel_checklist() -> tuple[str, ...]:
    """Return F1 acceptance checklist entries."""
    logger.debug("axiom_kernel_checklist entry")
    result = ("eight primitive axioms", "executable witness per axiom", "receipt-derived witness closure", "no whole-layer dependency overclaim", "shadow layers claim no axioms", "theorem-derived and meta layers claim no primitive witness axioms")
    logger.debug("axiom_kernel_checklist exit count=%d", len(result))
    return result
