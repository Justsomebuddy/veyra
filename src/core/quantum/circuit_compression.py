"""Q9 finite circuit-compression rows for Q-Veyra."""
from __future__ import annotations
from dataclasses import dataclass
import logging
from .gate_identities import AM1, gate_equal, gate_phase_equal, gate_word
from .veyra import QMode, q_basis_state, q_gate_h, observer_distribution

logger = logging.getLogger(__name__)

@dataclass(frozen=True)
class CircuitCompressionRow:
    """One finite circuit rewrite/compression row with explicit non-claim boundary."""
    row_id: str
    source_word: tuple[str, ...]
    reduced_word: tuple[str, ...]
    relation: str
    input_state: str
    observer: str
    source_cost: int
    reduced_cost: int
    saved_gates: int
    exact_equal: bool
    phase_equal: bool
    observer_echo: bool
    status: str
    witness: str
    boundary: str

    def as_dict(self) -> dict[str, object]:
        """Return a JSON-ready row."""
        logger.debug("CircuitCompressionRow.as_dict entry row_id=%s", self.row_id)
        result = self.__dict__.copy()
        logger.debug("CircuitCompressionRow.as_dict exit result=%r", result)
        return result

def _cost(word: tuple[str, ...]) -> int:
    """Return a tiny peephole cost where identity is free."""
    logger.debug("_cost entry word=%r", word)
    result = sum(name != "I" for name in word)
    logger.debug("_cost exit result=%d", result)
    return result

def _plus_state() -> QMode:
    """Return finite one-qubit |+> state."""
    logger.debug("_plus_state entry")
    result = q_gate_h().apply(q_basis_state("0"))
    logger.debug("_plus_state exit distribution=%r", result.distribution())
    return result

def _input_state(label: str) -> QMode:
    """Return the finite input mode used by a compression row."""
    logger.debug("_input_state entry label=%s", label)
    if label == "|0>":
        result = q_basis_state("0")
    elif label == "|+>":
        result = _plus_state()
    else:
        logger.error("_input_state invalid label=%s", label)
        raise ValueError("supported Q9 inputs are |0> and |+>")
    logger.debug("_input_state exit norm=%r", result.norm2())
    return result

def _observer_echo(source: tuple[str, ...], reduced: tuple[str, ...], state_label: str, observer: str) -> bool:
    """Return whether source/reduced circuits echo under one observer/input."""
    logger.debug("_observer_echo entry source=%r reduced=%r state=%s observer=%s", source, reduced, state_label, observer)
    mode = _input_state(state_label)
    left = gate_word(source).apply(mode)
    right = gate_word(reduced).apply(mode)
    result = observer_distribution(left, observer) == observer_distribution(right, observer)
    logger.debug("_observer_echo exit result=%s", result)
    return result

def _row(row_id: str, source: tuple[str, ...], reduced: tuple[str, ...], relation: str, state: str = "|0>", observer: str = "Z") -> CircuitCompressionRow:
    """Build one finite compression row."""
    logger.debug("_row entry row_id=%s relation=%s", row_id, relation)
    src_gate, red_gate = gate_word(source), gate_word(reduced)
    exact = gate_equal(src_gate, red_gate)
    phase = gate_phase_equal(src_gate, red_gate, AM1)
    echo = _observer_echo(source, reduced, state, observer)
    saved = _cost(source) - _cost(reduced)
    ready = (relation == "exact-reduction" and exact and saved > 0) or (relation == "global-phase-normalization" and phase) or (relation == "observer-preserving-reduction" and echo and saved > 0)
    witness = "exact matrix equality" if exact else "global phase -1" if phase else f"{observer} observer echo on {state}"
    result = CircuitCompressionRow(row_id, source, reduced, relation, state, observer, _cost(source), _cost(reduced), saved, exact, phase, echo, "ready" if ready else "blocked", witness, "finite peephole/observer row only; no general compiler optimality or quantum advantage claim")
    logger.debug("_row exit result=%r", result)
    return result

def circuit_compression_rows() -> tuple[CircuitCompressionRow, ...]:
    """Return finite Q9 circuit-compression rows."""
    logger.debug("circuit_compression_rows entry")
    result = (
        _row("Q9-REDUCE-HH", ("H", "H"), ("I",), "exact-reduction"),
        _row("Q9-REDUCE-XX", ("X", "X"), ("I",), "exact-reduction"),
        _row("Q9-REDUCE-SSSS", ("S", "S", "S", "S"), ("I",), "exact-reduction"),
        _row("Q9-PHASE-XZ-ZX", ("X", "Z"), ("Z", "X"), "global-phase-normalization"),
        _row("Q9-OBS-S-I-Z0", ("S",), ("I",), "observer-preserving-reduction"),
        _row("Q9-OBS-Z-I-ZPLUS", ("Z",), ("I",), "observer-preserving-reduction", "|+>", "Z"),
    )
    logger.debug("circuit_compression_rows exit count=%d", len(result))
    return result

def circuit_compression_summary() -> dict[str, int]:
    """Return compact Q9 counters."""
    logger.debug("circuit_compression_summary entry")
    rows = circuit_compression_rows()
    result = {
        "rows": len(rows),
        "ready": sum(row.status == "ready" for row in rows),
        "exact_reductions": sum(row.relation == "exact-reduction" and row.exact_equal for row in rows),
        "phase_normalizations": sum(row.relation == "global-phase-normalization" and row.phase_equal for row in rows),
        "observer_reductions": sum(row.relation == "observer-preserving-reduction" and row.observer_echo for row in rows),
        "saved_gates": sum(max(0, row.saved_gates) for row in rows),
        "overclaims": sum("finite" not in row.boundary for row in rows),
    }
    logger.debug("circuit_compression_summary exit result=%r", result)
    return result

def circuit_compression_checklist() -> tuple[str, ...]:
    """Return Q9 acceptance checklist."""
    logger.debug("circuit_compression_checklist entry")
    result = ("exact redundant-gate reductions", "global-phase subcircuit normalization", "observer-preserving reductions", "finite cost model", "classical compiler baseline", "no optimality claim")
    logger.debug("circuit_compression_checklist exit count=%d", len(result))
    return result
