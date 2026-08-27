"""Explicit deduction-chain ledger for Veyra foundation honesty."""
from __future__ import annotations
from collections import Counter
from dataclasses import dataclass
import logging
from .benchmark_derivations import benchmark_derivation_summary
from .classical_benchmarks import classical_benchmark_summary
from .formal_bridge import echo_reflexive_certificate, check_lean_echo_export
from .native_geometry_derivations import native_geometry_derivation_summary
from .intrinsic_arithmetic import intrinsic_arithmetic_summary
from .native_formal_bridge import intrinsic_arithmetic_lean_status
from .native_runtime import native_runtime_report

logger = logging.getLogger(__name__)
STATUSES = ("derived", "observer-derived", "shadow-dependent", "blocked")

@dataclass(frozen=True)
class DeductionLink:
    """One declared link between a target layer and its sources."""
    link_id: str
    target: str
    sources: tuple[str, ...]
    anchors: tuple[str, ...]
    status: str
    boundary: str

    def as_dict(self) -> dict[str, object]:
        """Return JSON-ready deduction row."""
        logger.debug("DeductionLink.as_dict entry link=%s", self.link_id)
        result = self.__dict__.copy()
        logger.debug("DeductionLink.as_dict exit result=%r", result)
        return result

@dataclass(frozen=True)
class DeductionProofRow:
    """Executable check for one deduction-chain row."""
    link_id: str
    target: str
    status: str
    verified: bool
    evidence: str
    boundary: str

    def as_dict(self) -> dict[str, object]:
        """Return JSON-ready proof row."""
        logger.debug("DeductionProofRow.as_dict entry link=%s", self.link_id)
        result = self.__dict__.copy()
        logger.debug("DeductionProofRow.as_dict exit result=%r", result)
        return result

def deduction_links() -> tuple[DeductionLink, ...]:
    """Return current first-class deduction and non-deduction links."""
    logger.debug("deduction_links entry")
    result = (
        DeductionLink(
            "DC-001", "echo", ("AX-OBSERVER", "AX-ECHO"), ("THM-F001",), "derived",
            "observer-indexed echo reflexivity is checked internally and in Lean",
        ),
        DeductionLink(
            "DC-002", "native-runtime", ("AX-REZ", "AX-NOD", "AX-TACT", "AX-BREATH", "AX-MODE"),
            ("native_runtime_f4",), "derived", "runtime assembly is behavior-first before school shadows",
        ),
        DeductionLink(
            "DC-003", "intrinsic-arithmetic", ("native-runtime", "structural recurrence division", "VeyraNativeArithmetic"),
            ("THM-R3-001", "THM-R3-002"), "derived", "structural supplied-factor escape; still not prime infinitude",
        ),
        DeductionLink(
            "DC-004", "classical-benchmark", ("echo", "balance", "geometry-theorems", "native-runtime"),
            ("BM-F001", "BM-F002", "BM-F003", "BM-F004", "BM-F005", "BM-F006", "BM-F007", "BM-F009"), "derived",
            "benchmark verdicts derive by explicit rules; compared target layers are not derived here",
        ),
        DeductionLink(
            "DC-005", "geometry-theorems", ("native-runtime", "Breath length observer", "THM-G001"),
            ("THM-G001",), "derived", "finite native right-corner row; not full geometry theorem",
        ),
    )
    logger.debug("deduction_links exit count=%d", len(result))
    return result

def deduction_proof_rows(links: tuple[DeductionLink, ...] | None = None) -> tuple[DeductionProofRow, ...]:
    """Execute proof/evidence checks for every deduction-chain row."""
    logger.debug("deduction_proof_rows entry has_links=%s", links is not None)
    rows = tuple(links or deduction_links())
    checks = {
        "DC-001": _check_echo_derivation,
        "DC-002": _check_native_runtime_derivation,
        "DC-003": _check_native_number_derivation,
        "DC-004": _check_classical_benchmark_derivation,
        "DC-005": _check_native_geometry_derivation,
    }
    result = tuple(checks[row.link_id](row) for row in rows)
    logger.debug("deduction_proof_rows exit count=%d", len(result))
    return result

def deduction_chain_summary(links: tuple[DeductionLink, ...] | None = None) -> dict[str, int | bool]:
    """Return compact deduction-chain counters."""
    logger.debug("deduction_chain_summary entry has_links=%s", links is not None)
    rows = deduction_links() if links is None else links
    counts = Counter(row.status for row in rows)
    proofs = deduction_proof_rows(rows)
    result: dict[str, int | bool] = {
        "links": len(rows),
        "verified": sum(row.verified for row in proofs),
        "all_derived": all(row.status == "derived" for row in rows),
    }
    result.update({status: counts.get(status, 0) for status in STATUSES})
    logger.debug("deduction_chain_summary exit result=%r", result)
    return result

def deduction_chain_checklist() -> tuple[str, ...]:
    """Return acceptance checklist for deduction-chain honesty."""
    logger.debug("deduction_chain_checklist entry")
    result = (
        "derived links named", "executable proof row per link", "benchmark verdict rules named",
        "non-claim boundaries named",
        "all-derived means boundary-derived, not capability claim",
    )
    logger.debug("deduction_chain_checklist exit count=%d", len(result))
    return result

def _check_echo_derivation(link: DeductionLink) -> DeductionProofRow:
    logger.debug("_check_echo_derivation entry link=%s", link.link_id)
    internal = echo_reflexive_certificate()
    lean = check_lean_echo_export()
    verified = internal.status == "checked" and lean.status == "checked"
    evidence = f"{internal.theorem_id}:{internal.status};lean={lean.status}"
    result = DeductionProofRow(link.link_id, link.target, link.status, verified, evidence, link.boundary)
    logger.debug("_check_echo_derivation exit result=%r", result)
    return result

def _check_native_runtime_derivation(link: DeductionLink) -> DeductionProofRow:
    logger.debug("_check_native_runtime_derivation entry link=%s", link.link_id)
    report = native_runtime_report()
    verified = bool(report["mode_ready"] and report["shape_echo"] and report["shadows"] == 4)
    evidence = f"mode={report['mode_ready']};shape_echo={report['shape_echo']};shadows={report['shadows']}"
    result = DeductionProofRow(link.link_id, link.target, link.status, verified, evidence, link.boundary)
    logger.debug("_check_native_runtime_derivation exit result=%r", result)
    return result

def _check_native_number_derivation(link: DeductionLink) -> DeductionProofRow:
    logger.debug("_check_native_number_derivation entry link=%s", link.link_id)
    summary = intrinsic_arithmetic_summary()
    lean = intrinsic_arithmetic_lean_status()
    verified = bool(summary["status"] == "witnessed" and summary["division"] and summary["escape"] and lean == "checked")
    evidence = f"intrinsic={summary['status']};division={summary['division']};escape={summary['escape']};lean={lean}"
    result = DeductionProofRow(link.link_id, link.target, link.status, verified, evidence, link.boundary)
    logger.debug("_check_native_number_derivation exit result=%r", result)
    return result

def _check_classical_benchmark_derivation(link: DeductionLink) -> DeductionProofRow:
    logger.debug("_check_classical_benchmark_derivation entry link=%s", link.link_id)
    summary = classical_benchmark_summary()
    derived = benchmark_derivation_summary()
    verified = bool(summary["cards"] == derived["rows"] == derived["derived"] and summary["all_status"] and summary["unsupported_stronger"] == 0 and summary["overclaims"] == 0 and derived["stronger"] == 1 and derived["unsupported_stronger"] == 0 and derived["scoped_claims"])
    evidence = f"benchmarked={summary['benchmarked']}/{summary['cards']};verdicts={derived['derived']}/{derived['rows']};stronger={derived['stronger']};scoped={derived['scoped_claims']}"
    result = DeductionProofRow(link.link_id, link.target, link.status, verified, evidence, link.boundary)
    logger.debug("_check_classical_benchmark_derivation exit result=%r", result)
    return result

def _check_native_geometry_derivation(link: DeductionLink) -> DeductionProofRow:
    logger.debug("_check_native_geometry_derivation entry link=%s", link.link_id)
    summary = native_geometry_derivation_summary()
    verified = bool(summary["rows"] == 3 and summary["derived"] == 3 and summary["finite_only"])
    evidence = f"native_geometry={summary['derived']}/{summary['rows']};finite_only={summary['finite_only']}"
    result = DeductionProofRow(link.link_id, link.target, link.status, verified, evidence, link.boundary)
    logger.debug("_check_native_geometry_derivation exit result=%r", result)
    return result
