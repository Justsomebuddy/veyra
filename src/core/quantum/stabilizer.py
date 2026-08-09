"""Q2 finite stabilizer/QEC observer rows for Q-Veyra."""
from __future__ import annotations
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass(frozen=True)
class PauliRow:
    """Finite Pauli action row over computational-basis bitstrings."""
    name: str
    input_bits: str
    output_bits: str
    roundtrip_bits: str
    status: str
    boundary: str

@dataclass(frozen=True)
class SyndromeRow:
    """Syndrome and logical-observer row for 3-qubit repetition code."""
    logical: int
    error: str
    errored_bits: str
    syndrome: tuple[int, int]
    correction: str
    corrected_bits: str
    logical_after: int
    status: str
    boundary: str

@dataclass(frozen=True)
class StabilizerEchoRow:
    """Two states can echo under syndrome observer while differing logically."""
    error: str
    left_bits: str
    right_bits: str
    syndrome_echo: bool
    logical_echo: bool
    status: str
    boundary: str

@dataclass(frozen=True)
class LogicalObstructionRow:
    """Uncorrectable multi-error row where finite syndrome correction flips logic."""
    error: str
    errored_bits: str
    syndrome: tuple[int, int]
    correction: str
    corrected_bits: str
    logical_before: int
    logical_after: int
    status: str
    boundary: str

CODEWORDS = {0: "000", 1: "111"}
ERRORS = {"I": (), "X0": (0,), "X1": (1,), "X2": (2,)}
DOUBLE_ERRORS = {"X0X1": (0, 1), "X0X2": (0, 2), "X1X2": (1, 2)}
CORRECTIONS = {(1, 1): "I", (-1, 1): "X0", (-1, -1): "X1", (1, -1): "X2"}

def apply_x(bits: str, positions: tuple[int, ...]) -> str:
    """Apply finite Pauli-X flips to a computational bitstring."""
    logger.debug("apply_x entry bits=%s positions=%r", bits, positions)
    arr = list(bits)
    for pos in positions:
        arr[pos] = "1" if arr[pos] == "0" else "0"
    result = "".join(arr)
    logger.debug("apply_x exit result=%s", result)
    return result

def syndrome(bits: str) -> tuple[int, int]:
    """Return Z0Z1 and Z1Z2 repetition-code syndrome signs."""
    logger.debug("syndrome entry bits=%s", bits)
    result = (1 if bits[0] == bits[1] else -1, 1 if bits[1] == bits[2] else -1)
    logger.debug("syndrome exit result=%r", result)
    return result

def correction_for_syndrome(row: tuple[int, int]) -> str:
    """Return single-error correction name for a syndrome."""
    logger.debug("correction_for_syndrome entry row=%r", row)
    result = CORRECTIONS[row]
    logger.debug("correction_for_syndrome exit result=%s", result)
    return result

def logical_observer(bits: str) -> int:
    """Return majority-vote logical observer for three computational bits."""
    logger.debug("logical_observer entry bits=%s", bits)
    result = 1 if bits.count("1") >= 2 else 0
    logger.debug("logical_observer exit result=%d", result)
    return result

def pauli_x_rows() -> tuple[PauliRow, ...]:
    """Return finite Pauli-X involution rows for each physical qubit."""
    logger.debug("pauli_x_rows entry")
    rows = []
    for pos in range(3):
        out = apply_x("000", (pos,)); back = apply_x(out, (pos,))
        rows.append(PauliRow(f"X{pos}", "000", out, back, "ready" if back == "000" else "blocked", "finite Pauli-X involution row only"))
    result = tuple(rows)
    logger.debug("pauli_x_rows exit count=%d", len(result))
    return result

def syndrome_rows() -> tuple[SyndromeRow, ...]:
    """Return single-error syndrome/correction rows for logical 0 and 1."""
    logger.debug("syndrome_rows entry")
    rows = []
    for logical, codeword in CODEWORDS.items():
        for error, positions in ERRORS.items():
            errored = apply_x(codeword, positions); syn = syndrome(errored); corr = correction_for_syndrome(syn)
            corrected = apply_x(errored, ERRORS[corr]); after = logical_observer(corrected)
            ok = corrected == codeword and after == logical
            rows.append(SyndromeRow(logical, error, errored, syn, corr, corrected, after, "ready" if ok else "blocked", "finite 3-qubit repetition-code single-error row"))
    result = tuple(rows)
    logger.debug("syndrome_rows exit count=%d", len(result))
    return result

def stabilizer_echo_rows() -> tuple[StabilizerEchoRow, ...]:
    """Return syndrome-equal but logical-distinct observer split rows."""
    logger.debug("stabilizer_echo_rows entry")
    rows = []
    for error, positions in ERRORS.items():
        left = apply_x(CODEWORDS[0], positions); right = apply_x(CODEWORDS[1], positions)
        syn_echo = syndrome(left) == syndrome(right); log_echo = logical_observer(left) == logical_observer(right)
        rows.append(StabilizerEchoRow(error, left, right, syn_echo, log_echo, "ready" if syn_echo and not log_echo else "blocked", "finite syndrome observer echoes while logical observer distinguishes"))
    result = tuple(rows)
    logger.debug("stabilizer_echo_rows exit count=%d", len(result))
    return result

def logical_obstruction_rows() -> tuple[LogicalObstructionRow, ...]:
    """Return double-error rows where single-error correction becomes logical error."""
    logger.debug("logical_obstruction_rows entry")
    rows = []
    for error, positions in DOUBLE_ERRORS.items():
        errored = apply_x(CODEWORDS[0], positions); syn = syndrome(errored); corr = correction_for_syndrome(syn)
        corrected = apply_x(errored, ERRORS[corr]); after = logical_observer(corrected)
        rows.append(LogicalObstructionRow(error, errored, syn, corr, corrected, 0, after, "ready" if after == 1 else "blocked", "finite double-error obstruction for single-error code"))
    result = tuple(rows)
    logger.debug("logical_obstruction_rows exit count=%d", len(result))
    return result

def quantum_stabilizer_summary() -> dict[str, int]:
    """Return compact Q2 counters."""
    logger.debug("quantum_stabilizer_summary entry")
    p = pauli_x_rows(); s = syndrome_rows(); e = stabilizer_echo_rows(); o = logical_obstruction_rows()
    result = {"pauli_rows": len(p), "syndrome_rows": len(s), "single_error_corrected": sum(r.status == "ready" for r in s), "echo_split_rows": sum(r.status == "ready" for r in e), "logical_obstructions": sum(r.status == "ready" for r in o), "overclaims": sum("finite" not in r.boundary for r in (*p, *s, *e, *o))}
    logger.debug("quantum_stabilizer_summary exit result=%r", result)
    return result

def quantum_stabilizer_checklist() -> tuple[str, ...]:
    """Return Q2 stabilizer/QEC acceptance checklist."""
    logger.debug("quantum_stabilizer_checklist entry")
    result = ("Pauli-X involution rows", "syndrome-measurement observer rows", "logical-observer rows", "syndrome/logical observer split", "double-error obstruction rows", "finite-code boundary")
    logger.debug("quantum_stabilizer_checklist exit count=%d", len(result))
    return result
