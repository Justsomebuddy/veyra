"""Q7 named quantum error-obstruction rows for finite Q-Veyra debugging."""
from __future__ import annotations
from dataclasses import dataclass
import logging
from .gate_identities import gate_equal, gate_word, q_gate_s, q_gate_z
from .qec_echo import qec_ambiguity_rows, qec_split_echo_rows
from .veyra import A0, A1, AH, QGate, QMode, R1, compose_gate, q_basis_state, q_gate_h

logger = logging.getLogger(__name__)

@dataclass(frozen=True)
class QuantumErrorObstructionRow:
    """One named finite quantum debugging obstruction row."""
    obstruction_id: str
    family: str
    observer: str
    expected_shadow: str
    observed_shadow: str
    witness: str
    status: str
    boundary: str

def _row(
    row_id: str,
    family: str,
    observer: str,
    expected: str,
    observed: str,
    witness: str,
    ready: bool,
) -> QuantumErrorObstructionRow:
    logger.debug("_row entry row_id=%s family=%s", row_id, family)
    result = QuantumErrorObstructionRow(
        row_id,
        family,
        observer,
        expected,
        observed,
        witness,
        "ready" if ready else "blocked",
        "finite named quantum debugging obstruction only",
    )
    logger.debug("_row exit result=%r", result)
    return result

def phase_break_row() -> QuantumErrorObstructionRow:
    """Return a phase-break row where one missing `S` breaks the expected `Z` phase."""
    logger.debug("phase_break_row entry")
    expected_ok = gate_equal(gate_word(("S", "S")), q_gate_z())
    observed_bad = not gate_equal(q_gate_s(), q_gate_z())
    result = _row(
        "Q7-PHASE-BREAK",
        "phase-break",
        "gate-phase",
        "S²=Z",
        "S≠Z",
        "one missing phase gate changes the exact phase shadow",
        expected_ok and observed_bad,
    )
    logger.debug("phase_break_row exit status=%s", result.status)
    return result

def interference_loss_row() -> QuantumErrorObstructionRow:
    """Return an interference-loss row for replacing `HH` by one `H`."""
    logger.debug("interference_loss_row entry")
    start = q_basis_state("0")
    target = start.distribution()
    restored = gate_word(("H", "H")).apply(start).distribution()
    half_path = q_gate_h().apply(start).distribution()
    result = _row(
        "Q7-INTERFERENCE-LOSS",
        "interference-loss",
        "Z-distribution",
        "HH|0> has |0> shadow",
        "H|0> has split shadow",
        "dropped recombination gate erases destructive/constructive interference return",
        restored == target and half_path != target,
    )
    logger.debug("interference_loss_row exit status=%s", result.status)
    return result

def leakage_row() -> QuantumErrorObstructionRow:
    """Return a leakage row with nonzero amplitude outside the computational subspace."""
    logger.debug("leakage_row entry")
    mode = QMode(("0", "1", "L"), (AH, A0, AH))
    leak = dict(mode.distribution())["L"]
    result = _row(
        "Q7-LEAKAGE",
        "leakage",
        "basis-support",
        "support⊆{0,1}",
        f"leak_mass={leak}",
        "nonzero `L` basis mass is outside the declared finite computational observer",
        not leak.is_zero() and mode.norm2() == R1,
    )
    logger.debug("leakage_row exit status=%s", result.status)
    return result

def nonunitarity_row() -> QuantumErrorObstructionRow:
    """Return a non-unitarity row where a bad gate drops `|1>` norm to zero."""
    logger.debug("nonunitarity_row entry")
    bad = QGate("DROP1", ((A1, A0), (A0, A0)))
    before = q_basis_state("1").norm2()
    after = bad.apply(q_basis_state("1")).norm2()
    result = _row(
        "Q7-NON-UNITARITY",
        "non-unitarity",
        "norm",
        f"norm={before}",
        f"norm={after}",
        "matrix with a zero image column fails finite norm preservation",
        before == R1 and after != before,
    )
    logger.debug("nonunitarity_row exit status=%s", result.status)
    return result

def syndrome_ambiguity_row() -> QuantumErrorObstructionRow:
    """Return an aggregate row for single-vs-double syndrome ambiguity."""
    logger.debug("syndrome_ambiguity_row entry")
    rows = qec_ambiguity_rows()
    ready = len(rows) == 6 and all(row.status == "ready" for row in rows)
    result = _row(
        "Q7-SYNDROME-AMBIGUITY",
        "syndrome-ambiguity",
        "syndrome+correction",
        "single errors correct",
        "double errors share syndrome but flip logical result",
        "six Q5 ambiguity rows name the non-binary failure surface",
        ready,
    )
    logger.debug("syndrome_ambiguity_row exit status=%s", result.status)
    return result

def branch_distinguishability_row() -> QuantumErrorObstructionRow:
    """Return an aggregate row for branches equal to recovery but distinct to logical observer."""
    logger.debug("branch_distinguishability_row entry")
    rows = qec_split_echo_rows()
    ready = len(rows) == 4 and all(row.status == "ready" for row in rows)
    result = _row(
        "Q7-BRANCH-DISTINGUISHABLE",
        "branch-distinguishability",
        "logical-after",
        "same syndrome/correction echo",
        "logical observer distinguishes branches",
        "four Q5 split rows show observer-indexed branch distinction",
        ready,
    )
    logger.debug("branch_distinguishability_row exit status=%s", result.status)
    return result

def quantum_error_obstruction_rows() -> tuple[QuantumErrorObstructionRow, ...]:
    """Return the finite Q7 named obstruction catalog."""
    logger.debug("quantum_error_obstruction_rows entry")
    result = (
        phase_break_row(),
        interference_loss_row(),
        leakage_row(),
        nonunitarity_row(),
        syndrome_ambiguity_row(),
        branch_distinguishability_row(),
    )
    logger.debug("quantum_error_obstruction_rows exit count=%d", len(result))
    return result

def quantum_error_obstruction_summary() -> dict[str, int]:
    """Return compact Q7 obstruction counters."""
    logger.debug("quantum_error_obstruction_summary entry")
    rows = quantum_error_obstruction_rows()
    result = {
        "rows": len(rows),
        "ready": sum(row.status == "ready" for row in rows),
        "families": len({row.family for row in rows}),
        "amplitude_rows": sum(row.family in {"phase-break", "interference-loss", "leakage", "non-unitarity"} for row in rows),
        "qec_rows": sum(row.family in {"syndrome-ambiguity", "branch-distinguishability"} for row in rows),
        "overclaims": sum("finite" not in row.boundary for row in rows),
    }
    logger.debug("quantum_error_obstruction_summary exit result=%r", result)
    return result

def quantum_error_obstruction_checklist() -> tuple[str, ...]:
    """Return Q7 obstruction-characterization acceptance checklist."""
    logger.debug("quantum_error_obstruction_checklist entry")
    result = (
        "phase-break row",
        "interference-loss row",
        "leakage row",
        "non-unitarity row",
        "syndrome ambiguity row",
        "branch distinguishability row",
    )
    logger.debug("quantum_error_obstruction_checklist exit count=%d", len(result))
    return result
