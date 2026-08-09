"""R15 evidence ledger over the classical benchmark registry.

Every registered benchmark row (BM-F001..BM-F007 and BM-F009, including the R6 scoped
observer-synthesis row) gets explicit evidence fields: assumptions, carrier
strength, proof-length class, TCB/search/runtime cost class, and an observer
information-loss note. Rows are claim-tagged ledger/definition only; the sole
scoped ``stronger`` result is re-stated exactly as observer-class-scoped
(proper-marginal-vs-parity observer class) and never as superiority over
classical mathematics. Expected failures are explicit obstruction rows.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import logging

from .classical_benchmarks import ClassicalBenchmarkCard, classical_benchmark_cards
from ..observer.synthesis import strict_observer_class_certificate

logger = logging.getLogger(__name__)

CARRIER_STRENGTHS = ("finite-shadow", "witness", "theorem-derived")
PROOF_LENGTH_CLASSES = ("one-line", "finite-card", "bounded-derivation", "search-plus-lean-chain")
TCB_CLASSES = ("python", "python+lean")
SEARCH_CLASSES = ("closed-form", "bounded-enumeration", "grammar-search")
RUNTIME_CLASSES = ("constant", "linear-bounded", "exponential-bounded")
CLAIM_TAGS = ("ledger", "definition")
LOCAL_SCOPE_NOTE = "ledger row only; the paired verdict stays local to its declared comparison and is not a global claim"


@dataclass(frozen=True)
class BenchmarkEvidenceSpec:
    """Declared R15 evidence fields for one registered benchmark row."""

    benchmark_id: str
    assumptions: str
    carrier_strength: str
    proof_length_class: str
    tcb_class: str
    search_class: str
    runtime_class: str
    observer_loss: str


@dataclass(frozen=True)
class BenchmarkEvidenceRow:
    """One ready evidence-ledger row; the claim tag stays ledger/definition only."""

    benchmark_id: str
    verdict: str
    assumptions: str
    carrier_strength: str
    proof_length_class: str
    cost_class: str
    observer_loss: str
    scope_note: str
    claim_tag: str = "ledger"
    status: str = "ready"


@dataclass(frozen=True)
class BenchmarkEvidenceObstructionRow:
    """Explicit obstruction for a benchmark row with missing or invalid evidence."""

    benchmark_id: str
    reason: str
    missing_fields: tuple[str, ...]
    claim_tag: str = "ledger"
    status: str = "blocked"


EvidenceLedgerRow = BenchmarkEvidenceRow | BenchmarkEvidenceObstructionRow

_EVIDENCE_SPECS: tuple[BenchmarkEvidenceSpec, ...] = (
    BenchmarkEvidenceSpec(
        "BM-F001",
        "one declared observer and object; echo reflexivity scope equals one-line equality reflexivity; THM-F001 checks",
        "theorem-derived", "one-line", "python+lean", "closed-form", "constant",
        "echo observer discards all structure beyond same/different under the declared observer",
    ),
    BenchmarkEvidenceSpec(
        "BM-F002",
        "one finite stitch fixture of signed balances 3 and -2; net length observed once; no group law is assumed",
        "finite-shadow", "bounded-derivation", "python", "closed-form", "constant",
        "balance observer discards stitch path detail; only the net arising/fading length remains",
    ),
    BenchmarkEvidenceSpec(
        "BM-F003",
        "fixed 3-4-5 legs at a named apex; tremor-corridor card evidence binds hyp echo 25; no general triangle",
        "witness", "finite-card", "python", "closed-form", "constant",
        "corridor observer discards every triangle except the fixed 3-4-5 sample and keeps only hyp echo 25",
    ),
    BenchmarkEvidenceSpec(
        "BM-F004",
        "one closed breath wraps as a Mode and one open breath blocks; exactly four observer-derived shadows",
        "finite-shadow", "bounded-derivation", "python", "closed-form", "constant",
        "closure observer discards internal tact order; only open/closed status and the four shadows remain",
    ),
    BenchmarkEvidenceSpec(
        "BM-F005",
        "a supplied finite factor list; native stitch/weave/division reconstructs; escape from the product successor",
        "witness", "bounded-derivation", "python", "bounded-enumeration", "linear-bounded",
        "mode-length observer discards full prime structure; only the supplied-factor escape remains",
    ),
    BenchmarkEvidenceSpec(
        "BM-F006",
        "finite corridor/shell fixtures; invariant hits equal the invariant count; two obstruction cards stay blocked",
        "finite-shadow", "bounded-derivation", "python", "bounded-enumeration", "linear-bounded",
        "deformation observer discards embedding detail; only component, boundary, and cycle-rank invariants remain",
    ),
    BenchmarkEvidenceSpec(
        "BM-F007",
        "finite likelihood grid; exactly one fit domain and one blocked residual-family domain",
        "finite-shadow", "bounded-derivation", "python", "bounded-enumeration", "linear-bounded",
        "likelihood observer discards model parameters; only grid slopes and residual-family status remain",
    ),
    BenchmarkEvidenceSpec(
        "BM-F009",
        "locked width-4 train and untouched width-5 holdout parity corpora; baseline class and winner fixed before holdout",
        "theorem-derived", "search-plus-lean-chain", "python+lean", "grammar-search", "exponential-bounded",
        "baseline observers factor through proper-subset marginals and lose the global-parity bit; extended keeps it",
    ),
)


def benchmark_evidence_specs() -> tuple[BenchmarkEvidenceSpec, ...]:
    """Return the declared R15 evidence specs."""
    logger.debug("benchmark_evidence_specs entry")
    logger.debug("benchmark_evidence_specs exit count=%d", len(_EVIDENCE_SPECS))
    return _EVIDENCE_SPECS


def scoped_stronger_restatement(benchmark_id: str = "BM-F009") -> str:
    """Re-state the sole scoped stronger result exactly as observer-class-scoped."""
    logger.debug("scoped_stronger_restatement entry id=%s", benchmark_id)
    cert = strict_observer_class_certificate()
    result = (
        f"{benchmark_id} stronger is observer-class-scoped only: the extended observer class "
        f"({cert.extended_class}) strictly separates the locked train/holdout parity witness pair "
        f"that every observer in the baseline class ({cert.baseline_class}) is blind to; "
        "this proper-marginal-vs-parity observer-class result is never a claim of superiority "
        "over classical mathematics"
    )
    logger.debug("scoped_stronger_restatement exit length=%d", len(result))
    return result


def evidence_row_problems(row: BenchmarkEvidenceRow) -> tuple[str, ...]:
    """Return the names of missing or invalid evidence fields on one row."""
    logger.debug("evidence_row_problems entry id=%s", row.benchmark_id)
    problems: list[str] = []
    if not row.assumptions:
        problems.append("assumptions")
    if row.carrier_strength not in CARRIER_STRENGTHS:
        problems.append("carrier_strength")
    if row.proof_length_class not in PROOF_LENGTH_CLASSES:
        problems.append("proof_length_class")
    if not _cost_class_valid(row.cost_class):
        problems.append("cost_class")
    if not row.observer_loss or not any(token in row.observer_loss for token in ("discard", "lose", "blind")):
        problems.append("observer_loss")
    if not row.scope_note:
        problems.append("scope_note")
    elif row.verdict == "stronger":
        if row.scope_note != scoped_stronger_restatement(row.benchmark_id):
            problems.append("scope_note")
    elif "not a global claim" not in row.scope_note and "not global" not in row.scope_note:
        problems.append("scope_note")
    if row.claim_tag not in CLAIM_TAGS:
        problems.append("claim_tag")
    result = tuple(problems)
    logger.debug("evidence_row_problems exit problems=%r", result)
    return result


def benchmark_evidence_rows(cards: tuple[ClassicalBenchmarkCard, ...] | None = None) -> tuple[EvidenceLedgerRow, ...]:
    """Return one evidence or obstruction row per registered benchmark card."""
    logger.debug("benchmark_evidence_rows entry has_cards=%s", cards is not None)
    items = classical_benchmark_cards() if cards is None else cards
    specs = {spec.benchmark_id: spec for spec in _EVIDENCE_SPECS}
    rows: list[EvidenceLedgerRow] = []
    for card in items:
        spec = specs.get(card.benchmark_id)
        if spec is None:
            rows.append(BenchmarkEvidenceObstructionRow(card.benchmark_id, "missing-evidence-spec", ("evidence_spec",)))
            continue
        row = _build_row(card, spec)
        problems = evidence_row_problems(row)
        rows.append(row if not problems else BenchmarkEvidenceObstructionRow(card.benchmark_id, "invalid-evidence", problems))
    card_ids = {card.benchmark_id for card in items}
    for spec in _EVIDENCE_SPECS:
        if spec.benchmark_id not in card_ids:
            rows.append(BenchmarkEvidenceObstructionRow(f"orphan:{spec.benchmark_id}", "unregistered-evidence-spec", ("benchmark_registry",)))
    result = tuple(rows)
    logger.debug("benchmark_evidence_rows exit count=%d", len(result))
    return result


def validate_benchmark_evidence(rows: tuple[EvidenceLedgerRow, ...] | None = None) -> tuple[BenchmarkEvidenceObstructionRow, ...]:
    """Return obstruction rows for every registered benchmark with missing or invalid evidence."""
    logger.debug("validate_benchmark_evidence entry has_rows=%s", rows is not None)
    items = benchmark_evidence_rows() if rows is None else rows
    problems: list[BenchmarkEvidenceObstructionRow] = []
    for row in items:
        if isinstance(row, BenchmarkEvidenceObstructionRow):
            problems.append(row)
            continue
        bad = evidence_row_problems(row)
        if bad:
            problems.append(BenchmarkEvidenceObstructionRow(row.benchmark_id, "invalid-evidence", bad))
    result = tuple(problems)
    logger.debug("validate_benchmark_evidence exit count=%d", len(result))
    return result


def benchmark_evidence_summary(rows: tuple[EvidenceLedgerRow, ...] | None = None) -> dict[str, int | bool]:
    """Return the aggregate evidence-ledger summary row with exact counts."""
    logger.debug("benchmark_evidence_summary entry has_rows=%s", rows is not None)
    items = benchmark_evidence_rows() if rows is None else rows
    ready = tuple(row for row in items if isinstance(row, BenchmarkEvidenceRow))
    blocked = tuple(row for row in items if isinstance(row, BenchmarkEvidenceObstructionRow))
    carriers = Counter(row.carrier_strength for row in ready)
    result: dict[str, int | bool] = {
        "benchmarks": len(items) - sum(row.benchmark_id.startswith("orphan:") for row in blocked),
        "evidence_rows": len(ready),
        "obstructions": len(blocked),
        "complete": not blocked,
        "stronger_rows": sum(row.verdict == "stronger" for row in ready),
        "scoped_stronger": sum(row.verdict == "stronger" and row.scope_note == scoped_stronger_restatement(row.benchmark_id) for row in ready),
        "global_superiority_claims": sum(row.verdict == "stronger" and row.scope_note != scoped_stronger_restatement(row.benchmark_id) for row in ready),
    }
    for name in CARRIER_STRENGTHS:
        result[f"carrier_{name.replace('-', '_')}"] = carriers.get(name, 0)
    logger.debug("benchmark_evidence_summary exit result=%r", result)
    return result


def benchmark_evidence_checklist() -> tuple[str, ...]:
    """Return the R15 acceptance checklist entries."""
    logger.debug("benchmark_evidence_checklist entry")
    result = (
        "explicit assumptions", "carrier strength class", "proof-length class",
        "tcb/search/runtime cost class", "observer information-loss note",
        "ledger or definition claim tag", "observer-class-scoped stronger restatement",
        "no global superiority claim",
    )
    logger.debug("benchmark_evidence_checklist exit count=%d", len(result))
    return result


def _build_row(card: ClassicalBenchmarkCard, spec: BenchmarkEvidenceSpec) -> BenchmarkEvidenceRow:
    """Build one ready evidence row from a registered card and its declared spec."""
    logger.debug("_build_row entry id=%s", card.benchmark_id)
    scope = scoped_stronger_restatement(card.benchmark_id) if card.verdict == "stronger" else LOCAL_SCOPE_NOTE
    cost = f"tcb:{spec.tcb_class};search:{spec.search_class};runtime:{spec.runtime_class}"
    result = BenchmarkEvidenceRow(
        card.benchmark_id, card.verdict, spec.assumptions, spec.carrier_strength,
        spec.proof_length_class, cost, spec.observer_loss, scope,
    )
    logger.debug("_build_row exit result=%r", result)
    return result


def _cost_class_valid(cost_class: str) -> bool:
    """Check the compact ``tcb:<...>;search:<...>;runtime:<...>`` cost-class format."""
    parts = dict(part.split(":", 1) for part in cost_class.split(";") if ":" in part)
    result = (
        len(parts) == 3
        and parts.get("tcb") in TCB_CLASSES
        and parts.get("search") in SEARCH_CLASSES
        and parts.get("runtime") in RUNTIME_CLASSES
    )
    logger.debug("_cost_class_valid exit result=%s", result)
    return result
