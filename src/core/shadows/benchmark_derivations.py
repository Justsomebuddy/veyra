"""Derived benchmark-verdict rules for F5 non-claim discipline."""
from __future__ import annotations
from collections import Counter
from dataclasses import dataclass
import logging
from .classical_benchmarks import ClassicalBenchmarkCard, classical_benchmark_cards
from ..native_runtime import Breath, NativeObstruction, breath, mode, nod, rez, tact

logger = logging.getLogger(__name__)
EXPECTED = {
    "BM-F001": ("equivalent", "same-tiny-reflexivity-scope"),
    "BM-F002": ("weaker", "finite-fixture-vs-general-theorem"),
    "BM-F003": ("weaker", "finite-right-corner-vs-general-theorem"),
    "BM-F004": ("clearer", "explicit-obstruction-row"),
    "BM-F005": ("weaker", "finite-mode-euclid-vs-general-theorem"),
    "BM-F006": ("weaker", "finite-deformation-vs-general-topology"),
    "BM-F007": ("clearer", "explicit-residual-obstruction-row"),
    "BM-F009": ("stronger", "strict-observer-class-separation"),
}

@dataclass(frozen=True)
class BenchmarkDerivationRow:
    """One benchmark verdict derived from explicit comparison rules."""
    benchmark_id: str
    verdict: str
    rule: str
    status: str
    evidence: str
    boundary: str

    def as_dict(self) -> dict[str, str]:
        """Return JSON-ready benchmark derivation row."""
        logger.debug("BenchmarkDerivationRow.as_dict entry id=%s", self.benchmark_id)
        result = self.__dict__.copy()
        logger.debug("BenchmarkDerivationRow.as_dict exit result=%r", result)
        return result

def derive_benchmark_verdict(card: ClassicalBenchmarkCard) -> BenchmarkDerivationRow:
    """Derive one benchmark verdict from explicit finite comparison rules."""
    logger.debug("derive_benchmark_verdict entry id=%s", card.benchmark_id)
    expected = EXPECTED.get(card.benchmark_id)
    if expected is None:
        result = BenchmarkDerivationRow(card.benchmark_id, card.verdict, "unknown", "blocked", "missing-rule", "no benchmark verdict without a named rule")
        logger.debug("derive_benchmark_verdict exit blocked=%r", result)
        return result
    verdict, rule = expected
    evidence_ok = _rule_evidence(card, rule)
    status = "derived" if card.status == "benchmarked" and card.verdict == verdict and evidence_ok else "blocked"
    boundary = card.boundary if verdict == "stronger" else "derives only the benchmark verdict; does not derive the compared mathematical target"
    evidence = f"card={card.status};verdict={card.verdict};rule={rule};evidence={evidence_ok}"
    result = BenchmarkDerivationRow(card.benchmark_id, verdict, rule, status, evidence, boundary)
    logger.debug("derive_benchmark_verdict exit result=%r", result)
    return result

def benchmark_derivation_rows(cards: tuple[ClassicalBenchmarkCard, ...] | None = None) -> tuple[BenchmarkDerivationRow, ...]:
    """Return derived benchmark-verdict rows for the current F5 ledger."""
    logger.debug("benchmark_derivation_rows entry has_cards=%s", cards is not None)
    rows = tuple(cards or classical_benchmark_cards())
    result = tuple(derive_benchmark_verdict(card) for card in rows)
    logger.debug("benchmark_derivation_rows exit count=%d", len(result))
    return result

def benchmark_derivation_summary(rows: tuple[BenchmarkDerivationRow, ...] | None = None) -> dict[str, int | bool]:
    """Return compact counters for derived benchmark verdicts."""
    logger.debug("benchmark_derivation_summary entry has_rows=%s", rows is not None)
    items = tuple(rows or benchmark_derivation_rows())
    counts = Counter(row.verdict for row in items)
    result: dict[str, int | bool] = {
        "rows": len(items),
        "derived": sum(row.status == "derived" for row in items),
        "blocked": sum(row.status != "derived" for row in items),
        "stronger": counts.get("stronger", 0),
        "unsupported_stronger": sum(row.verdict == "stronger" and row.status != "derived" for row in items),
        "scoped_claims": all(row.boundary for row in items),
    }
    logger.debug("benchmark_derivation_summary exit result=%r", result)
    return result

def benchmark_derivation_checklist() -> tuple[str, ...]:
    """Return acceptance checklist for derived benchmark verdicts."""
    logger.debug("benchmark_derivation_checklist entry")
    result = ("named verdict rule", "benchmarked source card", "declared verdict dimension", "declared comparison scope", "strict certificate required for stronger", "non-global boundary")
    logger.debug("benchmark_derivation_checklist exit count=%d", len(result))
    return result

def _rule_evidence(card: ClassicalBenchmarkCard, rule: str) -> bool:
    logger.debug("_rule_evidence entry id=%s rule=%s", card.benchmark_id, rule)
    if rule == "same-tiny-reflexivity-scope":
        result = "THM-F001" in card.veyra_artifact and "reflexivity" in card.reason
    elif rule in {"finite-fixture-vs-general-theorem", "finite-right-corner-vs-general-theorem", "finite-mode-euclid-vs-general-theorem", "finite-deformation-vs-general-topology"}:
        result = "finite" in card.reason and "general" in card.reason
    elif rule == "explicit-obstruction-row":
        result = _open_obstruction_ready() and "obstruction" in card.reason
    elif rule == "explicit-residual-obstruction-row":
        result = "residual" in card.veyra_statement and "obstruction" in card.reason
    elif rule == "strict-observer-class-separation":
        from ..observer.synthesis import strict_observer_class_certificate
        cert = strict_observer_class_certificate()
        result = card.evidence_id == "observer_class_strength_r6" and card.verdict_dimension == "declared-observer-class-discrimination" and card.comparison_scope == cert.baseline_class and cert.strictly_stronger and cert.lean_status == "checked" and "not global" in card.boundary
    else:
        result = False
    logger.debug("_rule_evidence exit result=%s", result)
    return result

def _open_obstruction_ready() -> bool:
    logger.debug("_open_obstruction_ready entry")
    a, b = nod(rez("bench:a")), nod(rez("bench:b"))
    run = breath(tact(a, b, "step"))
    blocked = mode(run) if isinstance(run, Breath) else run
    result = isinstance(blocked, NativeObstruction) and blocked.reason == "open-breath"
    logger.debug("_open_obstruction_ready exit result=%s", result)
    return result
