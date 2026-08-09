"""Executable audit for the current Veyra magic hypothesis."""
from __future__ import annotations
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)
VEYRA_MAGIC_THESIS = "observer synthesis: find the observer under which an object becomes simple, explanatory, or blocked"

@dataclass(frozen=True)
class MagicAuditRow:
    """One bounded claim about where Veyra may be nontrivially useful."""
    row_id: str
    name: str
    hypothesis: str
    evidence: tuple[str, ...]
    classical_status: str
    veyra_move: str
    verdict: str
    boundary: str

    def as_dict(self) -> dict[str, object]:
        """Return a JSON-ready magic audit row."""
        logger.debug("MagicAuditRow.as_dict entry row_id=%s", self.row_id)
        result = {
            "row_id": self.row_id,
            "name": self.name,
            "hypothesis": self.hypothesis,
            "evidence": self.evidence,
            "classical_status": self.classical_status,
            "veyra_move": self.veyra_move,
            "verdict": self.verdict,
            "boundary": self.boundary,
        }
        logger.debug("MagicAuditRow.as_dict exit result=%r", result)
        return result

def magic_audit_rows() -> tuple[MagicAuditRow, ...]:
    """Return the current finite audit of Veyra's possible magic nucleus."""
    logger.debug("magic_audit_rows entry")
    boundary = "not a superiority claim; every row names classical emulation or bounded evidence"
    result = (
        MagicAuditRow(
            "M1-OBSERVER-SYNTHESIS",
            "observer synthesis",
            "Veyra's primitive move is to search for the observer that makes a residue simple or explains why it stays blocked.",
            ("observer_synthesis_r5", "observer_class_strength_r6", "native_runtime_f4", "proof_discipline"),
            "classical methods can emulate each listed observer after it is named",
            "enumerate a locked typed grammar, fit before holdout, and retain obstruction evidence",
            "strongest-current-magic-candidate",
            boundary,
        ),
        MagicAuditRow(
            "M2-OBSTRUCTION-AS-DATA",
            "obstruction ledger",
            "Failures become structured objects rather than discarded negative cases.",
            ("quantum_error_obstruction_q7", "core_language_coverage"),
            "classical debugging also names failures, but not under one observer-indexed theorem/certificate ledger here",
            "store blocked/ambiguous/error states as named rows with witnesses",
            "active-magic-candidate",
            boundary,
        ),
        MagicAuditRow(
            "M3-HIDDEN-ORDER-PRESSURE",
            "hidden order pressure",
            "Rows S1..S6 show that a declared observer change can expose structure hidden from named lower-order baselines.",
            ("surprise_search_s3", "surprise_kwise_s5", "surprise_debruijn_s6"),
            "higher-order entropy, parity, and graph observers catch current examples once named",
            "turn missed structure into a search problem over observer families",
            "active-magic-candidate",
            boundary,
        ),
        MagicAuditRow(
            "M4-ANTI-MAGIC-GUARD",
            "anti-magic guard",
            "The system's truth-maintenance layer blocks fake magic by forcing baseline comparison and no-overclaim certificates.",
            ("classical_benchmark_f5", "quantum_baseline_q3", "foundational_repair_f1_f3"),
            "ordinary peer review can do this socially; Veyra makes it executable in the project loop",
            "attach every beautiful row to a baseline and boundary",
            "truth-maintenance",
            boundary,
        ),
        MagicAuditRow(
            "M5-NO-ADVANTAGE-YET",
            "blocked advantage claim",
            "No current row proves global superiority, speedup, or universal classical impossibility.",
            ("docs/concepts/foundational_gap_audit.md", "docs/log/veyra_surprise.md"),
            "classical baselines remain known for every current magic-looking row",
            "record the missing theorem before celebrating",
            "blocked-claim",
            boundary,
        ),
    )
    logger.debug("magic_audit_rows exit count=%d", len(result))
    return result

def magic_audit_summary() -> dict[str, int]:
    """Return compact counters for the Veyra magic audit."""
    logger.debug("magic_audit_summary entry")
    rows = magic_audit_rows()
    result = {
        "rows": len(rows),
        "strongest_candidates": sum(row.verdict == "strongest-current-magic-candidate" for row in rows),
        "active_candidates": sum(row.verdict == "active-magic-candidate" for row in rows),
        "truth_maintenance": sum(row.verdict == "truth-maintenance" for row in rows),
        "blocked_claims": sum(row.verdict == "blocked-claim" for row in rows),
        "overclaims": sum("not a superiority claim" not in row.boundary for row in rows),
    }
    logger.debug("magic_audit_summary exit result=%r", result)
    return result

def magic_audit_checklist() -> tuple[str, ...]:
    """Return the acceptance checklist for calling something Veyra magic."""
    logger.debug("magic_audit_checklist entry")
    result = ("name the observer switch", "show a bounded witness", "name the classical baseline", "record obstruction or ambiguity", "block global superiority claims", "turn the row into a certificate")
    logger.debug("magic_audit_checklist exit count=%d", len(result))
    return result
