"""Classical-vs-Veyra benchmark ledger for F5."""
from __future__ import annotations
from collections import Counter
from dataclasses import dataclass
import logging
from .balance import balance_from_int, stitch_balance
from .formal_bridge import echo_reflexive_certificate
from .geometry import event_from_ints
from .geometry_theorems import pythagorean_card
from .likelihood_geometry import likelihood_geometry_summary
from .intrinsic_arithmetic import intrinsic_arithmetic_summary
from .native_runtime import native_runtime_report
from .observer_synthesis_parity import BOUNDARY as OBSERVER_STRENGTH_BOUNDARY, strict_observer_class_certificate
from .topology_echo import topology_echo_summary

logger = logging.getLogger(__name__)
VERDICTS = ("shorter", "clearer", "stronger", "weaker", "equivalent")

@dataclass(frozen=True)
class ClassicalBenchmarkCard:
    """One paired classical proof versus Veyra artifact row."""
    benchmark_id: str
    topic: str
    classical_statement: str
    classical_method: str
    veyra_statement: str
    veyra_artifact: str
    verdict: str
    reason: str
    status: str
    verdict_dimension: str = "declared-artifact-comparison"
    comparison_scope: str = "the statements and artifacts named by this card"
    evidence_id: str = "card-artifact"
    boundary: str = "the verdict is local to the declared comparison, not global superiority"

    def as_dict(self) -> dict[str, str]:
        """Return JSON-ready benchmark row."""
        logger.debug("ClassicalBenchmarkCard.as_dict entry id=%s", self.benchmark_id)
        result = self.__dict__.copy()
        logger.debug("ClassicalBenchmarkCard.as_dict exit result=%r", result)
        return result

def _echo_card() -> ClassicalBenchmarkCard:
    logger.debug("_echo_card entry")
    cert = echo_reflexive_certificate()
    status = "benchmarked" if cert.status == "checked" else "blocked"
    result = ClassicalBenchmarkCard("BM-F001", "echo-reflexivity", "equality is reflexive: x = x", "one-line equality reflexivity", "for every observer o and object x, echo(o,x,x)", "THM-F001 / proofs/lean/VeyraEcho.lean", "equivalent", "same tiny reflexivity scope, with observer index made explicit", status)
    logger.debug("_echo_card exit result=%r", result)
    return result

def _balance_card() -> ClassicalBenchmarkCard:
    logger.debug("_balance_card entry")
    total = stitch_balance(balance_from_int(3), balance_from_int(-2))
    status = "benchmarked" if total.net_length == 1 else "blocked"
    result = ClassicalBenchmarkCard("BM-F002", "signed-addition", "3 + (-2) = 1", "integer group arithmetic", "arising/fading balance stitch has net length 1", "certify_balance / balance.py", "weaker", "current Veyra row is a finite executable fixture, not a general group theorem", status)
    logger.debug("_balance_card exit result=%r", result)
    return result

def _pythagorean_card() -> ClassicalBenchmarkCard:
    logger.debug("_pythagorean_card entry")
    apex = event_from_ints((0, 0), "O")
    leg_one = event_from_ints((3, 0), "A")
    leg_two = event_from_ints((0, 4), "B")
    card = pythagorean_card(apex, leg_one, leg_two)
    status = "benchmarked" if card.relation == "proven" and dict(card.evidence).get("hyp_echo") == "25" else "blocked"
    result = ClassicalBenchmarkCard("BM-F003", "pythagorean-3-4-5", "right triangles satisfy a²+b²=c²", "Euclidean proof or inner-product algebra", "finite tremor-corridor separation card proves 3-4-5 sample", "pythagorean_card / geometry_theorems.py", "weaker", "Veyra artifact is exact but finite; classical theorem is general", status)
    logger.debug("_pythagorean_card exit result=%r", result)
    return result

def _runtime_card() -> ClassicalBenchmarkCard:
    logger.debug("_runtime_card entry")
    report = native_runtime_report()
    status = "benchmarked" if report["mode_ready"] and report["shadows"] == 4 else "blocked"
    result = ClassicalBenchmarkCard("BM-F004", "closed-recurrence", "a finite closed walk returns to its boundary", "graph/path endpoint check", "a closed breath wraps as Mode and open breath remains obstruction", "native_runtime_f4 / native_runtime.py", "clearer", "Veyra records open failure as first-class obstruction while preserving derived shadows", status)
    logger.debug("_runtime_card exit result=%r", result)
    return result

def _native_number_card() -> ClassicalBenchmarkCard:
    logger.debug("_native_number_card entry")
    summary = intrinsic_arithmetic_summary()
    status = "benchmarked" if summary["status"] == "witnessed" and summary["division"] and summary["escape"] else "blocked"
    result = ClassicalBenchmarkCard("BM-F005", "euclid-product-plus-one", "Euclid proves no finite prime list exhausts primes", "product-plus-one divisibility contradiction", "native recurrence stitch/weave/division derives a product-successor escape proof", "intrinsic_arithmetic / VeyraNativeArithmetic.lean", "weaker", "finite structural supplied-factor escape is weaker than the general prime-infinitude theorem", status)
    logger.debug("_native_number_card exit result=%r", result)
    return result

def _topology_card() -> ClassicalBenchmarkCard:
    logger.debug("_topology_card entry")
    summary = topology_echo_summary()
    status = "benchmarked" if summary["invariant_hits"] == summary["invariants"] and summary["blocked"] == 2 else "blocked"
    result = ClassicalBenchmarkCard("BM-F006", "deformation-invariants", "homeomorphism-style deformation preserves topological invariants", "general topology invariant proof", "finite corridor/shell components, boundaries, cycle-rank, and obstruction cards", "topology_echo_x4 / topology_echo.py", "weaker", "finite deformation fixtures are weaker than general topology invariance", status)
    logger.debug("_topology_card exit result=%r", result)
    return result

def _likelihood_card() -> ClassicalBenchmarkCard:
    logger.debug("_likelihood_card entry")
    summary = likelihood_geometry_summary()
    status = "benchmarked" if summary["fit_domains"] == 1 and summary["blocked_domains"] == 1 else "blocked"
    result = ClassicalBenchmarkCard("BM-F007", "likelihood-residual-family", "finite likelihood grids and residual diagnostics classify model fit", "likelihood/residual arithmetic", "finite likelihood slopes plus certified and blocked residual-family rows", "likelihood_geometry_x5 / likelihood_geometry.py", "clearer", "explicit blocked residual-family obstruction makes the failure mode visible", status)
    logger.debug("_likelihood_card exit result=%r", result)
    return result

def _observer_class_card() -> ClassicalBenchmarkCard:
    logger.debug("_observer_class_card entry")
    cert = strict_observer_class_certificate()
    status = "benchmarked" if cert.strictly_stronger and cert.lean_status == "checked" else "blocked"
    result = ClassicalBenchmarkCard(
        "BM-F009", "observer-class-discrimination",
        "all postprocessors factoring through proper-subset marginals are blind on the paired parity corpora",
        "factorization through a fixed baseline signature",
        "a synthesized global-parity observer separates locked train and untouched holdout pairs",
        "observer_class_strength_r6 / THM-R6-001 / THM-R6-002", "stronger",
        "the extended observer class strictly separates a witness pair hidden from the declared baseline factor class",
        status, "declared-observer-class-discrimination", cert.baseline_class,
        "observer_class_strength_r6", OBSERVER_STRENGTH_BOUNDARY,
    )
    logger.debug("_observer_class_card exit result=%r", result)
    return result

def classical_benchmark_cards() -> tuple[ClassicalBenchmarkCard, ...]:
    """Return current F5 paired benchmark cards."""
    logger.debug("classical_benchmark_cards entry")
    result = (
        _echo_card(), _balance_card(), _pythagorean_card(), _runtime_card(),
        _native_number_card(), _topology_card(), _likelihood_card(), _observer_class_card(),
    )
    logger.debug("classical_benchmark_cards exit count=%d", len(result))
    return result

def classical_benchmark_summary(cards: tuple[ClassicalBenchmarkCard, ...] | None = None) -> dict[str, int | bool]:
    """Return compact benchmark counts and status."""
    logger.debug("classical_benchmark_summary entry has_cards=%s", cards is not None)
    rows = classical_benchmark_cards() if cards is None else cards
    counts = Counter(row.verdict for row in rows)
    supported_stronger = sum(row.verdict == "stronger" and row.evidence_id == "observer_class_strength_r6" and strict_observer_class_certificate().strictly_stronger for row in rows)
    result: dict[str, int | bool] = {"cards": len(rows), "benchmarked": sum(row.status == "benchmarked" for row in rows), "blocked": sum(row.status != "benchmarked" for row in rows), "all_status": all(row.status == "benchmarked" for row in rows), "scoped_claims": all(row.verdict_dimension and row.comparison_scope and row.boundary for row in rows), "unsupported_stronger": counts.get("stronger", 0) - supported_stronger, "overclaims": sum(row.verdict == "stronger" and "not global" not in row.boundary for row in rows)}
    result.update({name: counts.get(name, 0) for name in VERDICTS})
    logger.debug("classical_benchmark_summary exit result=%r", result)
    return result

def classical_benchmark_checklist() -> tuple[str, ...]:
    """Return F5 acceptance checklist entries."""
    logger.debug("classical_benchmark_checklist entry")
    result = ("paired classical statement", "paired Veyra artifact", "explicit verdict", "declared verdict dimension", "declared comparison scope", "strict certificate required for stronger", "non-global boundary")
    logger.debug("classical_benchmark_checklist exit count=%d", len(result))
    return result
