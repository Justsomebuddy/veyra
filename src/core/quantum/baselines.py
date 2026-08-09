"""Q3 baseline ledger for finite Q-Veyra rows."""
from __future__ import annotations
from collections import Counter
from dataclasses import dataclass
import logging
from .circuit_compression import circuit_compression_summary
from .error_obstructions import quantum_error_obstruction_summary
from .gate_identities import quantum_gate_identity_summary
from .qec_echo import quantum_qec_echo_summary
from .qft_period import quantum_qft_period_summary
from .stabilizer import quantum_stabilizer_summary
from .topology import quantum_topology_summary
from .veyra import quantum_veyra_summary

logger = logging.getLogger(__name__)

@dataclass(frozen=True)
class QuantumBaselineRow:
    """One current Q-Veyra result paired with a classical baseline."""
    result_id: str
    veyra_artifact: str
    baseline_family: str
    baseline_method: str
    verdict: str
    stronger_claim: bool
    status: str
    boundary: str


def _row(result_id: str, artifact: str, family: str, method: str) -> QuantumBaselineRow:
    logger.debug("_row entry result_id=%s family=%s", result_id, family)
    result = QuantumBaselineRow(
        result_id,
        artifact,
        family,
        method,
        "baseline-known",
        False,
        "benchmarked",
        "finite current-row comparison only; no quantum advantage or simulator claim",
    )
    logger.debug("_row exit result=%r", result)
    return result


def quantum_baseline_rows() -> tuple[QuantumBaselineRow, ...]:
    """Return Q3 baselines for every current finite Q-Veyra result family."""
    logger.debug("quantum_baseline_rows entry")
    q1 = quantum_veyra_summary()
    q2 = quantum_stabilizer_summary()
    q4 = quantum_topology_summary()
    q5 = quantum_qec_echo_summary()
    q6 = quantum_gate_identity_summary()
    q7 = quantum_error_obstruction_summary()
    q8 = quantum_qft_period_summary()
    q9 = circuit_compression_summary()
    if (
        q1["ready"] != 6
        or q2["single_error_corrected"] != 8
        or q4["deformation_echoes"] != 3
        or q5["ambiguity_rows"] != 6
        or q6["ready"] != 11
        or q7["ready"] != 6
        or q8["ready_period_rows"] != 3
        or q9["ready"] != 6
    ):
        logger.error("quantum_baseline_rows blocked q1=%r q2=%r q4=%r q5=%r q6=%r q7=%r q8=%r q9=%r", q1, q2, q4, q5, q6, q7, q8, q9)
        return ()
    result = (
        _row("Q-HH", "quantum_veyra.Q-HH", "classical-linear-algebra", "2x2 matrix multiplication proves H²=I"),
        _row("Q-XX", "quantum_veyra.Q-XX", "classical-linear-algebra", "2x2 permutation matrix proves X²=I"),
        _row("Q-CNOT-NORM", "quantum_veyra.Q-CNOT-NORM", "classical-linear-algebra", "4x4 permutation/unitary matrix preserves norm"),
        _row("Q-BELL-NONFACT", "quantum_veyra.Q-BELL-NONFACT", "tensor-product", "2x2 amplitude tensor rank/product test blocks factorization"),
        _row("Q-ZX-SHADOW", "quantum_veyra.Q-ZX-SHADOW", "classical-probability", "Born distribution in Z and X bases is computed directly"),
        _row("Q-NO-CLONE", "quantum_veyra.Q-NO-CLONE", "classical-linear-algebra", "linearity obstruction for |+> cloning is checked by distributions"),
        _row("Q2-SYNDROME", "quantum_stabilizer.syndrome_rows", "stabilizer-tableau", "Z0Z1/Z1Z2 parity rows match repetition-code syndrome table"),
        _row("Q2-ECHO-SPLIT", "quantum_stabilizer.stabilizer_echo_rows", "stabilizer-tableau", "same syndrome can still carry distinct logical observer rows"),
        _row("Q2-DOUBLE-ERROR", "quantum_stabilizer.logical_obstruction_rows", "classical-coding-theory", "distance-3 repetition code corrects one bit flip and miscorrects two"),
        _row("Q4-TOPO-ECHO", "quantum_topology.qtopo_echo_rows", "graph-topology", "finite component/boundary/cycle-rank invariants classify the toy topology echo"),
        _row("Q5-QEC-ECHO", "quantum_qec_echo.qec_split_echo_rows", "stabilizer-tableau", "observer-indexed syndrome/correction/logical rows are a repetition-code table"),
        _row("Q5-QEC-AMBIGUITY", "quantum_qec_echo.qec_ambiguity_rows", "classical-coding-theory", "distance-3 decoding ambiguity is the standard two-error obstruction"),
        _row("Q6-GATE-ID", "quantum_gate_identities.gate_identity_rows", "classical-matrix-algebra", "finite matrix multiplication and Clifford peephole rules verify each identity"),
        _row("Q7-ERROR-OBS", "quantum_error_obstructions.quantum_error_obstruction_rows", "classical-debugging", "finite matrix/norm/support/stabilizer diagnostics name each failure mode"),
        _row("Q8-QFT-PERIOD", "quantum_qft_period.qft_period_rows", "classical-fourier-analysis", "four-point DFT support arithmetic verifies the finite period shadows"),
        _row("Q9-CIRCUIT-COMPRESS", "quantum_circuit_compression.circuit_compression_rows", "classical-compiler-peephole", "finite matrix equality, global phase, and observer-projection checks verify each reduction"),
    )
    logger.debug("quantum_baseline_rows exit count=%d", len(result))
    return result


def quantum_baseline_summary(rows: tuple[QuantumBaselineRow, ...] | None = None) -> dict[str, int | bool]:
    """Return compact Q3 baseline counters."""
    logger.debug("quantum_baseline_summary entry has_rows=%s", rows is not None)
    data = quantum_baseline_rows() if rows is None else rows
    families = Counter(row.baseline_family for row in data)
    result: dict[str, int | bool] = {
        "rows": len(data),
        "benchmarked": sum(row.status == "benchmarked" for row in data),
        "families": len(families),
        "q1_rows": sum(row.result_id.startswith("Q-") for row in data),
        "q2_rows": sum(row.result_id.startswith("Q2-") for row in data),
        "q4_rows": sum(row.result_id.startswith("Q4-") for row in data),
        "q5_rows": sum(row.result_id.startswith("Q5-") for row in data),
        "q6_rows": sum(row.result_id.startswith("Q6-") for row in data),
        "q7_rows": sum(row.result_id.startswith("Q7-") for row in data),
        "q8_rows": sum(row.result_id.startswith("Q8-") for row in data),
        "q9_rows": sum(row.result_id.startswith("Q9-") for row in data),
        "stronger_claims": sum(row.stronger_claim for row in data),
        "overclaims": sum("finite" not in row.boundary for row in data),
        "all_status": all(row.status == "benchmarked" for row in data),
    }
    logger.debug("quantum_baseline_summary exit result=%r", result)
    return result


def quantum_baseline_checklist() -> tuple[str, ...]:
    """Return Q3 acceptance checklist."""
    logger.debug("quantum_baseline_checklist entry")
    result = (
        "each current finite Q-Veyra row has a baseline",
        "classical linear-algebra baselines included",
        "stabilizer-tableau/coding baselines included",
        "topology baseline included",
        "tensor-product baseline included",
        "Fourier and compiler peephole baselines included",
        "zero stronger or advantage claims",
    )
    logger.debug("quantum_baseline_checklist exit count=%d", len(result))
    return result
