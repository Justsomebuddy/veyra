"""Q5 observer-indexed QEC echo rows for finite Q-Veyra."""
from __future__ import annotations
from dataclasses import dataclass
import logging
from .stabilizer import apply_x, correction_for_syndrome, logical_observer, syndrome

logger = logging.getLogger(__name__)

CODEWORDS = {0: "000", 1: "111"}
ERROR_POSITIONS: tuple[tuple[str, tuple[int, ...]], ...] = (
    ("I", ()),
    ("X0", (0,)),
    ("X1", (1,)),
    ("X2", (2,)),
    ("X0X1", (0, 1)),
    ("X0X2", (0, 2)),
    ("X1X2", (1, 2)),
)
SINGLE_ERRORS = frozenset({"I", "X0", "X1", "X2"})
DOUBLE_MATCHES = {"X0": "X1X2", "X1": "X0X2", "X2": "X0X1"}

@dataclass(frozen=True)
class QECBranchRow:
    """One finite QEC branch under physical, syndrome, correction, and logical observers."""
    logical: int
    error: str
    weight: int
    raw_bits: str
    syndrome: tuple[int, int]
    correction: str
    corrected_bits: str
    logical_after: int
    correctable: bool
    status: str
    boundary: str

@dataclass(frozen=True)
class QECObserverFamilyRow:
    """Named observer family used to form QEC echo classes."""
    name: str
    observers: tuple[str, ...]
    classes: int
    distinguishes_logical: bool
    distinguishes_correctability: bool
    status: str
    boundary: str

@dataclass(frozen=True)
class QECSplitEchoRow:
    """Syndrome/correction echo row that a logical observer can still distinguish."""
    error: str
    left_logical: int
    right_logical: int
    syndrome_correction_echo: bool
    logical_echo: bool
    status: str
    boundary: str

@dataclass(frozen=True)
class QECAmbiguityRow:
    """Single-vs-double error ambiguity with shared syndrome/correction shadow."""
    logical: int
    single_error: str
    double_error: str
    shared_syndrome: tuple[int, int]
    shared_correction: str
    single_correctable: bool
    double_correctable: bool
    logical_distinct_after: bool
    status: str
    boundary: str

def qec_branch(logical: int, error: str) -> QECBranchRow:
    """Return one deterministic finite repetition-code QEC branch."""
    logger.debug("qec_branch entry logical=%d error=%s", logical, error)
    positions = dict(ERROR_POSITIONS)[error]
    codeword = CODEWORDS[logical]
    raw = apply_x(codeword, positions)
    syn = syndrome(raw)
    correction = correction_for_syndrome(syn)
    corrected = apply_x(raw, dict(ERROR_POSITIONS)[correction])
    after = logical_observer(corrected)
    correctable = corrected == codeword and after == logical
    result = QECBranchRow(
        logical,
        error,
        len(positions),
        raw,
        syn,
        correction,
        corrected,
        after,
        correctable,
        "ready",
        "finite repetition-code observer branch only",
    )
    logger.debug("qec_branch exit result=%r", result)
    return result

def qec_branch_rows() -> tuple[QECBranchRow, ...]:
    """Return all finite QEC branches for logical 0/1 and weight 0/1/2 errors."""
    logger.debug("qec_branch_rows entry")
    result = tuple(qec_branch(logical, error) for logical in CODEWORDS for error, _ in ERROR_POSITIONS)
    logger.debug("qec_branch_rows exit count=%d", len(result))
    return result

def branch_shadow(row: QECBranchRow, observer: str) -> object:
    """Return a named observer shadow for one QEC branch."""
    logger.debug("branch_shadow entry observer=%s row=%r", observer, row)
    shadows = {
        "syndrome": row.syndrome,
        "correction": row.correction,
        "logical-before": row.logical,
        "logical-after": row.logical_after,
        "corrected-bits": row.corrected_bits,
        "correctable": row.correctable,
        "weight": row.weight,
        "error": row.error,
    }
    if observer not in shadows:
        logger.error("branch_shadow unknown observer=%s", observer)
        raise ValueError("unknown QEC observer")
    result = shadows[observer]
    logger.debug("branch_shadow exit result=%r", result)
    return result

def qec_echo(left: QECBranchRow, right: QECBranchRow, observers: tuple[str, ...]) -> bool:
    """Return whether two QEC branches echo under a declared observer family."""
    logger.debug("qec_echo entry left=%s right=%s observers=%r", left.error, right.error, observers)
    result = all(branch_shadow(left, obs) == branch_shadow(right, obs) for obs in observers)
    logger.debug("qec_echo exit result=%s", result)
    return result

def qec_observer_family_rows() -> tuple[QECObserverFamilyRow, ...]:
    """Return named observer families and their finite echo-class counts."""
    logger.debug("qec_observer_family_rows entry")
    rows = []
    branches = qec_branch_rows()
    families = (
        ("syndrome", ("syndrome",)),
        ("recovery", ("syndrome", "correction")),
        ("logical", ("logical-after",)),
        ("diagnostic", ("syndrome", "correction", "logical-after", "correctable")),
    )
    for name, observers in families:
        classes = len({tuple(branch_shadow(row, obs) for obs in observers) for row in branches})
        rows.append(
            QECObserverFamilyRow(
                name,
                observers,
                classes,
                "logical-after" in observers,
                "correctable" in observers,
                "ready",
                "finite observer-indexed QEC echo family only",
            )
        )
    result = tuple(rows)
    logger.debug("qec_observer_family_rows exit count=%d", len(result))
    return result

def qec_split_echo_rows() -> tuple[QECSplitEchoRow, ...]:
    """Return rows where syndrome/correction echo holds but logical echo fails."""
    logger.debug("qec_split_echo_rows entry")
    rows = []
    for error in ("I", "X0", "X1", "X2"):
        left = qec_branch(0, error)
        right = qec_branch(1, error)
        syndrome_echo = qec_echo(left, right, ("syndrome", "correction"))
        logical_echo = qec_echo(left, right, ("logical-after",))
        rows.append(
            QECSplitEchoRow(
                error,
                0,
                1,
                syndrome_echo,
                logical_echo,
                "ready" if syndrome_echo and not logical_echo else "blocked",
                "finite syndrome/correction echo with logical distinction only",
            )
        )
    result = tuple(rows)
    logger.debug("qec_split_echo_rows exit count=%d", len(result))
    return result

def qec_ambiguity_rows() -> tuple[QECAmbiguityRow, ...]:
    """Return single-vs-double ambiguity rows sharing syndrome and correction."""
    logger.debug("qec_ambiguity_rows entry")
    rows = []
    for logical in CODEWORDS:
        for single, double in DOUBLE_MATCHES.items():
            srow = qec_branch(logical, single)
            drow = qec_branch(logical, double)
            shared = qec_echo(srow, drow, ("syndrome", "correction"))
            distinct = srow.logical_after != drow.logical_after
            rows.append(
                QECAmbiguityRow(
                    logical,
                    single,
                    double,
                    srow.syndrome,
                    srow.correction,
                    srow.correctable,
                    drow.correctable,
                    distinct,
                    "ready" if shared and srow.correctable and not drow.correctable and distinct else "blocked",
                    "finite distance-3 ambiguity row only",
                )
            )
    result = tuple(rows)
    logger.debug("qec_ambiguity_rows exit count=%d", len(result))
    return result

def quantum_qec_echo_summary() -> dict[str, int]:
    """Return compact Q5 observer-indexed QEC counters."""
    logger.debug("quantum_qec_echo_summary entry")
    branches = qec_branch_rows()
    families = qec_observer_family_rows()
    splits = qec_split_echo_rows()
    ambiguities = qec_ambiguity_rows()
    all_rows = (*branches, *families, *splits, *ambiguities)
    result = {
        "branches": len(branches),
        "observer_families": len(families),
        "single_error_corrected": sum(r.error in SINGLE_ERRORS and r.correctable for r in branches),
        "double_error_obstructions": sum(r.error not in SINGLE_ERRORS and not r.correctable for r in branches),
        "split_echo_rows": sum(r.status == "ready" for r in splits),
        "ambiguity_rows": sum(r.status == "ready" for r in ambiguities),
        "overclaims": sum("finite" not in r.boundary for r in all_rows),
    }
    logger.debug("quantum_qec_echo_summary exit result=%r", result)
    return result

def quantum_qec_echo_checklist() -> tuple[str, ...]:
    """Return Q5 observer-indexed QEC acceptance checklist."""
    logger.debug("quantum_qec_echo_checklist entry")
    result = (
        "finite QEC branches for logical 0/1",
        "syndrome and correction observers form echo families",
        "logical observer splits syndrome/correction echoes",
        "single errors are corrected",
        "double errors become named ambiguity obstructions",
        "no fault-tolerance or advantage claim",
    )
    logger.debug("quantum_qec_echo_checklist exit count=%d", len(result))
    return result
