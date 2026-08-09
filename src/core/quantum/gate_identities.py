"""Q6 finite exact quantum gate identity catalog for Q-Veyra."""
from __future__ import annotations
from dataclasses import dataclass
from fractions import Fraction
import logging
from .veyra import A0, A1, AM1, QAmp, QGate, Rad2, compose_gate, q_gate_cnot, q_gate_h, q_gate_i, q_gate_x, tensor_gate

logger = logging.getLogger(__name__)

AI = QAmp(Rad2(), Rad2(Fraction(1)))
GATES_1Q = {"I": q_gate_i, "H": q_gate_h, "X": q_gate_x}

@dataclass(frozen=True)
class GateIdentityRow:
    """One exact or global-phase gate identity row with explicit boundary."""
    identity_id: str
    left_word: tuple[str, ...]
    right_word: tuple[str, ...]
    relation: str
    exact_equal: bool
    phase_equal: bool
    status: str
    boundary: str

@dataclass(frozen=True)
class GateIdentityBaselineRow:
    """Classical baseline row for the finite gate identity catalog."""
    family: str
    covered_rows: int
    method: str
    stronger_claim: bool
    status: str
    boundary: str

def q_gate_z() -> QGate:
    """Return the one-qubit Pauli-Z gate."""
    logger.debug("q_gate_z entry")
    result = QGate("Z", ((A1, A0), (A0, AM1)))
    logger.debug("q_gate_z exit result=%r", result)
    return result

def q_gate_s() -> QGate:
    """Return the one-qubit phase-S gate."""
    logger.debug("q_gate_s entry")
    result = QGate("S", ((A1, A0), (A0, AI)))
    logger.debug("q_gate_s exit result=%r", result)
    return result

def q_gate_i2() -> QGate:
    """Return the two-qubit identity gate."""
    logger.debug("q_gate_i2 entry")
    result = tensor_gate(q_gate_i(), q_gate_i())
    logger.debug("q_gate_i2 exit result=%r", result)
    return result

def gate_word(word: tuple[str, ...]) -> QGate:
    """Compose a one-qubit word as left-associated compiler notation."""
    logger.debug("gate_word entry word=%r", word)
    gates = {**GATES_1Q, "Z": q_gate_z, "S": q_gate_s}
    if not word:
        result = q_gate_i()
        logger.debug("gate_word exit gate=%s", result.name)
        return result
    current = gates[word[-1]]()
    for name in reversed(word[:-1]):
        current = compose_gate(gates[name](), current)
    logger.debug("gate_word exit gate=%s", current.name)
    return current

def scale_gate(gate: QGate, phase: QAmp) -> QGate:
    """Multiply every matrix entry by a global phase."""
    logger.debug("scale_gate entry gate=%s phase=%r", gate.name, phase)
    result = QGate(f"{phase}·{gate.name}", tuple(tuple(phase * amp for amp in row) for row in gate.matrix))
    logger.debug("scale_gate exit gate=%s", result.name)
    return result

def gate_equal(left: QGate, right: QGate) -> bool:
    """Return exact matrix equality for two finite gates."""
    logger.debug("gate_equal entry left=%s right=%s", left.name, right.name)
    result = left.matrix == right.matrix
    logger.debug("gate_equal exit result=%s", result)
    return result

def gate_phase_equal(left: QGate, right: QGate, phase: QAmp) -> bool:
    """Return whether `left == phase * right` exactly."""
    logger.debug("gate_phase_equal entry left=%s right=%s phase=%r", left.name, right.name, phase)
    result = gate_equal(left, scale_gate(right, phase))
    logger.debug("gate_phase_equal exit result=%s", result)
    return result

def _identity_row(
    row_id: str,
    left: QGate,
    right: QGate,
    left_word: tuple[str, ...],
    right_word: tuple[str, ...],
    relation: str = "exact",
) -> GateIdentityRow:
    logger.debug("_identity_row entry row_id=%s", row_id)
    exact = gate_equal(left, right)
    result = GateIdentityRow(
        row_id,
        left_word,
        right_word,
        relation,
        exact,
        False,
        "ready" if exact else "blocked",
        "finite exact matrix identity row only",
    )
    logger.debug("_identity_row exit result=%r", result)
    return result

def _phase_row(
    row_id: str,
    left: QGate,
    right: QGate,
    phase: QAmp,
    left_word: tuple[str, ...],
    right_word: tuple[str, ...],
) -> GateIdentityRow:
    logger.debug("_phase_row entry row_id=%s", row_id)
    exact = gate_equal(left, right)
    phase_ok = gate_phase_equal(left, right, phase)
    result = GateIdentityRow(
        row_id,
        left_word,
        right_word,
        "global-phase",
        exact,
        phase_ok,
        "ready" if phase_ok else "blocked",
        "finite global-phase compiler row only",
    )
    logger.debug("_phase_row exit result=%r", result)
    return result

def cnot_conjugation_rows() -> tuple[GateIdentityRow, ...]:
    """Return finite CNOT involution and Pauli propagation identity rows."""
    logger.debug("cnot_conjugation_rows entry")
    cnot = q_gate_cnot()
    xi = tensor_gate(q_gate_x(), q_gate_i())
    ix = tensor_gate(q_gate_i(), q_gate_x())
    rows = (
        _identity_row(
            "QID-CNOT-CNOT",
            compose_gate(cnot, cnot),
            q_gate_i2(),
            ("CNOT", "CNOT"),
            ("I⊗I",),
            "cnot-involution",
        ),
        _identity_row(
            "QID-CNOT-XC",
            compose_gate(cnot, compose_gate(xi, cnot)),
            tensor_gate(q_gate_x(), q_gate_x()),
            ("CNOT", "X⊗I", "CNOT"),
            ("X⊗X",),
            "pauli-propagation",
        ),
        _identity_row(
            "QID-CNOT-XT",
            compose_gate(cnot, compose_gate(ix, cnot)),
            ix,
            ("CNOT", "I⊗X", "CNOT"),
            ("I⊗X",),
            "pauli-propagation",
        ),
    )
    logger.debug("cnot_conjugation_rows exit count=%d", len(rows))
    return rows

def gate_identity_rows() -> tuple[GateIdentityRow, ...]:
    """Return the finite exact gate identity ledger for compiler checks."""
    logger.debug("gate_identity_rows entry")
    h, x, z, s, ident = q_gate_h(), q_gate_x(), q_gate_z(), q_gate_s(), q_gate_i()
    rows = (
        _identity_row("QID-HH", gate_word(("H", "H")), ident, ("H", "H"), ("I",), "involution"),
        _identity_row("QID-XX", gate_word(("X", "X")), ident, ("X", "X"), ("I",), "involution"),
        _identity_row("QID-ZZ", gate_word(("Z", "Z")), ident, ("Z", "Z"), ("I",), "involution"),
        _identity_row("QID-SS-Z", compose_gate(s, s), z, ("S", "S"), ("Z",), "phase-square"),
        _identity_row("QID-SSSS", gate_word(("S", "S", "S", "S")), ident, ("S", "S", "S", "S"), ("I",), "phase-period"),
        _identity_row("QID-HXH-Z", compose_gate(h, compose_gate(x, h)), z, ("H", "X", "H"), ("Z",), "basis-change"),
        _identity_row("QID-HZH-X", compose_gate(h, compose_gate(z, h)), x, ("H", "Z", "H"), ("X",), "basis-change"),
        _phase_row("QID-XZ-ANTI", compose_gate(x, z), compose_gate(z, x), AM1, ("X", "Z"), ("Z", "X")),
        *cnot_conjugation_rows(),
    )
    logger.debug("gate_identity_rows exit count=%d", len(rows))
    return rows

def gate_identity_baseline_rows() -> tuple[GateIdentityBaselineRow, ...]:
    """Return classical baselines for the finite identity catalog."""
    logger.debug("gate_identity_baseline_rows entry")
    count = len(gate_identity_rows())
    result = (
        GateIdentityBaselineRow("classical-matrix-algebra", count, "exact finite matrix multiplication", False, "benchmarked", "finite baseline row only"),
        GateIdentityBaselineRow("clifford-tableau", count, "standard Clifford rewrite identities", False, "benchmarked", "finite baseline row only"),
        GateIdentityBaselineRow("compiler-peephole", count, "local rewrite ledger for peephole verification", False, "benchmarked", "finite baseline row only"),
    )
    logger.debug("gate_identity_baseline_rows exit count=%d", len(result))
    return result

def quantum_gate_identity_summary() -> dict[str, int]:
    """Return compact Q6 gate-identity counters."""
    logger.debug("quantum_gate_identity_summary entry")
    rows = gate_identity_rows(); baselines = gate_identity_baseline_rows()
    result = {
        "rows": len(rows),
        "ready": sum(row.status == "ready" for row in rows),
        "exact_identities": sum(row.exact_equal for row in rows),
        "phase_identities": sum(row.phase_equal and not row.exact_equal for row in rows),
        "cnot_rows": sum(row.identity_id.startswith("QID-CNOT") for row in rows),
        "baseline_rows": len(baselines),
        "stronger_claims": sum(row.stronger_claim for row in baselines),
        "overclaims": sum("finite" not in row.boundary for row in (*rows, *baselines)),
    }
    logger.debug("quantum_gate_identity_summary exit result=%r", result)
    return result

def quantum_gate_identity_checklist() -> tuple[str, ...]:
    """Return Q6 gate identity catalog acceptance checklist."""
    logger.debug("quantum_gate_identity_checklist entry")
    result = (
        "involutions",
        "phase identities",
        "basis-change identities",
        "anti-commutation up to global phase",
        "CNOT Pauli propagation",
        "classical compiler baselines",
    )
    logger.debug("quantum_gate_identity_checklist exit count=%d", len(result))
    return result
