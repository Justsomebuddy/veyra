"""Executable Essence/Core contract for Veyra."""

from __future__ import annotations

from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class VeyraEssenceAxiom:
    """One declared essence axiom with an executable witness hook."""

    name: str
    statement: str
    status: str
    witness: str

    def as_dict(self) -> dict[str, str]:
        """Return JSON-ready axiom row."""
        logger.debug("VeyraEssenceAxiom.as_dict entry name=%s", self.name)
        result = self.__dict__.copy()
        logger.debug("VeyraEssenceAxiom.as_dict exit result=%r", result)
        return result


@dataclass(frozen=True)
class VeyraCoreLayer:
    """One assembled core layer and its certificate anchor."""

    name: str
    role: str
    certificate: str
    status: str

    def as_dict(self) -> dict[str, str]:
        """Return JSON-ready layer row."""
        logger.debug("VeyraCoreLayer.as_dict entry name=%s", self.name)
        result = self.__dict__.copy()
        logger.debug("VeyraCoreLayer.as_dict exit result=%r", result)
        return result


@dataclass(frozen=True)
class VeyraEssenceReport:
    """Current executable readiness report for Veyra Essence/Core."""

    axioms: tuple[VeyraEssenceAxiom, ...]
    layers: tuple[VeyraCoreLayer, ...]
    checklist: tuple[str, ...]
    missing: tuple[str, ...]

    @property
    def executable_layers(self) -> int:
        """Count layers with ready executable status."""
        logger.debug("VeyraEssenceReport.executable_layers entry")
        result = sum(layer.status == "ready" for layer in self.layers)
        logger.debug("VeyraEssenceReport.executable_layers exit result=%d", result)
        return result

    @property
    def core_ready(self) -> bool:
        """Return operational assembly readiness, not proof completeness."""
        logger.debug("VeyraEssenceReport.core_ready entry")
        result = not self.missing and self.executable_layers == len(self.layers) and len(self.axioms) == 9
        logger.debug("VeyraEssenceReport.core_ready exit result=%s", result)
        return result

    @property
    def proof_complete(self) -> bool:
        """Return whether every mathematical layer is theorem-derived."""
        logger.debug("VeyraEssenceReport.proof_complete entry")
        from .layer_derivations import layer_derivation_report
        summary = layer_derivation_report().summary()
        result = summary["witness_backed"] == 0 and summary["shadow"] == 0
        logger.debug("VeyraEssenceReport.proof_complete exit result=%s", result)
        return result

    def summary(self) -> dict[str, object]:
        """Return compact readiness summary."""
        logger.debug("VeyraEssenceReport.summary entry")
        from .layer_derivations import layer_derivation_report
        derivations = layer_derivation_report().summary()
        result = {
            "axioms": len(self.axioms),
            "layers": len(self.layers),
            "executable_layers": self.executable_layers,
            "missing": len(self.missing),
            "checklist": len(self.checklist),
            "core_ready": self.core_ready,
            "execution_ready": self.core_ready,
            "proof_complete": self.proof_complete,
            "theorem_derived": derivations["theorem_derived"],
            "witness_only": derivations["witness_backed"],
            "shadow": derivations["shadow"],
            "meta": derivations["meta"],
        }
        logger.debug("VeyraEssenceReport.summary exit result=%r", result)
        return result


def essence_axioms() -> tuple[VeyraEssenceAxiom, ...]:
    """Return the nine current Essence axioms."""
    logger.debug("essence_axioms entry")
    rows = (
        ("no-primitive-equality", "Sameness is observer-indexed echo, never primitive equality.", "declared", "echo/core_language"),
        ("no-primitive-point", "Point is an event residue under observation, not location dust.", "declared", "geometry"),
        ("no-primitive-segment", "Segment is a tremor corridor, not a primitive distance stick.", "declared", "geometry_relations"),
        ("no-primitive-number", "Number is a mode/balance/ratio shadow, not count-first ontology.", "declared", "balance/ratio"),
        ("observer-dependence", "Truth status is declared relative to observers and domains.", "declared", "core_language"),
        ("obstruction-first-proof", "Blocked and unknown are first-class proof outcomes.", "declared", "language_proof"),
        ("shadow-discipline", "Human mathematics enters only as explicit semantic shadow.", "declared", "school_translation"),
        ("executable-pressure", "A claim must have a test, certificate, or counterexample lane.", "declared", "certify"),
        ("coverage-discipline", "Core readiness requires fuzz, coverage, and source diagnostics.", "declared", "language_coverage"),
    )
    result = tuple(VeyraEssenceAxiom(*row) for row in rows)
    logger.debug("essence_axioms exit count=%d", len(result))
    return result


def core_layers() -> tuple[VeyraCoreLayer, ...]:
    """Return assembled executable layers of the current Veyra core."""
    logger.debug("core_layers entry")
    rows = (
        ("echo", "observer-indexed sameness replacement", "echo", "ready"),
        ("resonance", "cyclic/phase relation beyond ordered equality", "cyclic_resonance", "ready"),
        ("intrinsic-resonance", "proof-carrying intrinsic recurrence weave witness", "proof_carrying_core_r7", "ready"),
        ("intrinsic-observer-echo", "proof-carrying explicitly bounded readiness-conditioned intrinsic observer echo", "intrinsic_observer_echo_r13", "ready"),
        ("native-number", "cycle-echo primitive counts and ranking comparisons", "native_resonance_number", "ready"),
        ("aura-weight", "derived tact defect costs", "aura_weighted", "ready"),
        ("balance", "signed arithmetic as arising/fading stitch", "balance", "ready"),
        ("ratio-order", "fraction/order/interval shadows", "ratio+order", "ready"),
        ("equation", "linear residual obstruction solving", "equation", "ready"),
        ("polynomial", "ratio-polynomial transformer schema", "polynomial", "ready"),
        ("calculus-depth", "local linearization, derivative rules, integral coherence", "calculus_depth", "ready"),
        ("trigonometry-identities", "rational unit phase and sum/double/inverse cards", "trigonometry_identities", "ready"),
        ("phase-equations", "rational phase equation rows and inverse obstruction cards", "phase_equation_normal_forms", "ready"),
        ("linear-algebra", "vector/matrix action, determinant and eigen shadows", "linear_algebra_seed", "ready"),
        ("statistics-inference", "distribution families, intervals, hypotheses, uncertainty seeds", "statistics_inference", "ready"),
        ("statistics-concentration", "finite concentration, likelihood, and decision-error rows", "statistics_concentration_likelihood", "ready"),
        ("transcendental-limit", "finite exp/log series and alternating tail envelopes", "transcendental_limit", "ready"),
        ("convergence-algebra", "Cauchy tails, majorants, nested intervals, and radius guards", "convergence_algebra", "ready"),
        ("real-analysis-structure", "finite modulus, refinement stability, and jump obstructions", "real_analysis_structure", "ready"),
        ("weighted-echo-measure", "finite weighted coverage, additivity, and tact pushforwards", "weighted_echo_measure", "ready"),
        ("science-domain-certificates", "finite conservation, flow, diffusion, and obstruction rows", "science_domain_certificates", "ready"),
        ("model-diagnostics", "finite residuals, fit reports, comparisons, and anomaly obstructions", "model_diagnostics", "ready"),
        ("scale-memory-log", "transition-depth recovery, residual logs, cyclic unwraps, and obstructions", "scale_memory_log", "ready"),
        ("compression-algebra", "edit drift, compression trees, factors, cost strategies", "compression_algebra", "ready"),
        ("category-like", "finite object/morphism/invariant/universal-shadow rows", "category_like_translation_x3", "ready"),
        ("topology-echo", "finite deformation-invariant echo rows", "topology_echo_x4", "ready"),
        ("likelihood-geometry", "finite likelihood geometry and residual-family certificates", "likelihood_geometry_x5", "ready"),
        ("language", "grammar/type/echo/normal/interpreter", "core_language", "ready"),
        ("proof-pressure", "source-spanned proof traces and negative cases", "core_language_proofs+coverage", "ready"),
        ("diagnostics", "source-span parser diagnostics and coverage", "core_language_spans+span_diagnostics", "ready"),
        ("proof-discipline", "rule/span/domain/model/export coverage", "proof_discipline", "ready"),
        ("foundational-kernel", "unified axioms, theorem objects, and formal proof bridge", "foundational_repair_f1_f3", "ready"),
        ("native-runtime", "behavior-first rez/nod/tact/breath/mode objects", "native_runtime_f4", "ready"),
        ("classical-benchmark", "paired classical proof versus Veyra artifact ledger", "classical_benchmark_f5", "ready"),
        ("native-number-theorem", "Euclid-style product-plus-one theorem shadow", "native_number_theorem_n1", "ready"),
        ("deduction-chain", "explicit derived observer shadow blocked ledger", "deduction_chain_f6", "ready"),
    )
    result = tuple(VeyraCoreLayer(*row) for row in rows)
    logger.debug("core_layers exit count=%d", len(result))
    return result


def essence_checklist() -> tuple[str, ...]:
    """Return the completion checklist for Essence/Core."""
    logger.debug("essence_checklist entry")
    result = (
        "native primitives are not school primitives",
        "equality/number/point/segment are reconstructed as shadows",
        "observer, obstruction, and shadow are explicit in every claim",
        "core layers are named by executable certificate anchors",
        "negative pressure is present through fuzz/refutation/coverage",
        "Sage facade can inspect the same report without changing ontology",
    )
    logger.debug("essence_checklist exit count=%d", len(result))
    return result


def essence_report() -> VeyraEssenceReport:
    """Build the current Essence/Core readiness report."""
    logger.debug("essence_report entry")
    axioms = essence_axioms()
    layers = core_layers()
    missing = tuple(layer.name for layer in layers if layer.status != "ready")
    result = VeyraEssenceReport(axioms, layers, essence_checklist(), missing)
    logger.debug(
        "essence_report exit axioms=%d layers=%d missing=%d",
        len(axioms),
        len(layers),
        len(missing),
    )
    return result
