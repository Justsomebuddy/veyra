"""Exact finite tensor, Born-weight, and unitarity semantics.

The carrier reuses :mod:`quantum_veyra` amplitudes over ``Q(sqrt(2))[i]``.
It is an executable finite model, not a Hilbert-space or hardware claim.
"""
from __future__ import annotations

from dataclasses import dataclass
import logging

from .quantum_veyra import A0, A1, QGate, QMode, QAmp, R0, R1, Rad2

logger = logging.getLogger(__name__)

FINITE_BOUNDARY = (
    "finite exact Q(sqrt(2))[i] matrices and vectors only; "
    "no quantum advantage, simulator, or apparatus claim"
)


@dataclass(frozen=True, slots=True)
class UnitarityWitness:
    """Full finite matrix witness for both unitary identities."""

    gate: str
    dimension: int
    left_identity: bool
    right_identity: bool
    status: str
    boundary: str = FINITE_BOUNDARY


def conjugate(amplitude: QAmp) -> QAmp:
    """Return exact complex conjugation on the amplitude carrier."""
    logger.debug("conjugate entry amplitude=%r", amplitude)
    result = QAmp(amplitude.re, -amplitude.im)
    logger.debug("conjugate exit result=%r", result)
    return result


def _validate_mode(mode: QMode) -> None:
    logger.debug("_validate_mode entry basis_count=%d", len(mode.basis))
    if not mode.basis or len(mode.basis) != len(mode.amplitudes):
        logger.error(
            "_validate_mode invalid dimensions basis=%d amplitudes=%d",
            len(mode.basis),
            len(mode.amplitudes),
        )
        raise ValueError("a finite mode needs equally many nonempty labels and amplitudes")
    if len(set(mode.basis)) != len(mode.basis):
        logger.error("_validate_mode duplicate basis labels basis=%r", mode.basis)
        raise ValueError("basis labels must be unique")
    logger.debug("_validate_mode exit valid=True")


def _validate_gate(gate: QGate) -> int:
    logger.debug("_validate_gate entry gate=%s", gate.name)
    dimension = len(gate.matrix)
    if dimension == 0 or any(len(row) != dimension for row in gate.matrix):
        logger.error("_validate_gate nonsquare gate=%s rows=%d", gate.name, dimension)
        raise ValueError("a finite gate matrix must be nonempty and square")
    logger.debug("_validate_gate exit dimension=%d", dimension)
    return dimension


def inner_product(left: QMode, right: QMode) -> QAmp:
    """Return the exact sesquilinear inner product ``<left|right>``."""
    logger.debug("inner_product entry left_basis=%r right_basis=%r", left.basis, right.basis)
    _validate_mode(left)
    _validate_mode(right)
    if left.basis != right.basis:
        logger.error("inner_product incompatible bases left=%r right=%r", left.basis, right.basis)
        raise ValueError("inner-product modes must have the same ordered basis")
    total = A0
    for left_amp, right_amp in zip(left.amplitudes, right.amplitudes, strict=True):
        total = total + conjugate(left_amp) * right_amp
    logger.debug("inner_product exit result=%r", total)
    return total


def tensor_modes(factors: tuple[QMode, ...]) -> QMode:
    """Return the exact finite tensor product of any number of modes.

    The empty product is the one-dimensional scalar mode.
    """
    logger.debug("tensor_modes entry factors=%d", len(factors))
    basis = ("",)
    amplitudes = (A1,)
    for index, factor in enumerate(factors):
        _validate_mode(factor)
        invalid_labels = tuple(label for label in factor.basis if not label or "⊗" in label)
        if invalid_labels:
            logger.error(
                "tensor_modes ambiguous factor labels factor=%d labels=%r",
                index,
                invalid_labels,
            )
            raise ValueError("tensor factor basis labels must be nonempty and delimiter-free")
        basis = tuple(
            right if not left else f"{left}⊗{right}"
            for left in basis
            for right in factor.basis
        )
        if len(set(basis)) != len(basis):
            logger.error("tensor_modes nonunique product basis factor=%d basis=%r", index, basis)
            raise ValueError("tensor product basis labels must remain unique")
        amplitudes = tuple(left * right for left in amplitudes for right in factor.amplitudes)
        logger.debug("tensor_modes state_change factor=%d dimension=%d", index, len(basis))
    result = QMode(basis, amplitudes)
    logger.debug("tensor_modes exit dimension=%d norm=%r", len(result.basis), result.norm2())
    return result


def tensor_gates(factors: tuple[QGate, ...]) -> QGate:
    """Return the Kronecker product of any number of finite square gates."""
    logger.debug("tensor_gates entry factors=%d", len(factors))
    name = "1"
    matrix = ((A1,),)
    for index, factor in enumerate(factors):
        _validate_gate(factor)
        matrix = tuple(
            tuple(left * right for left in left_row for right in right_row)
            for left_row in matrix
            for right_row in factor.matrix
        )
        name = factor.name if name == "1" else f"{name}⊗{factor.name}"
        logger.debug("tensor_gates state_change factor=%d dimension=%d", index, len(matrix))
    result = QGate(name, matrix)
    logger.debug("tensor_gates exit gate=%s dimension=%d", result.name, len(result.matrix))
    return result


def born_distribution(mode: QMode) -> tuple[tuple[str, Rad2], ...]:
    """Return exact Born weights ``|amplitude|^2`` for every basis outcome."""
    logger.debug("born_distribution entry basis=%r", mode.basis)
    _validate_mode(mode)
    result = tuple(
        (label, amplitude.norm2())
        for label, amplitude in zip(mode.basis, mode.amplitudes, strict=True)
    )
    logger.debug("born_distribution exit outcomes=%d", len(result))
    return result


def born_total(mode: QMode) -> Rad2:
    """Return the exact total Born weight, equal to ``<mode|mode>``."""
    logger.debug("born_total entry basis=%r", mode.basis)
    total = R0
    for _, weight in born_distribution(mode):
        total = total + weight
    logger.debug("born_total exit result=%r", total)
    return total


def is_normalized(mode: QMode) -> bool:
    """Return whether exact Born weights sum to one."""
    logger.debug("is_normalized entry basis=%r", mode.basis)
    result = born_total(mode) == R1
    logger.debug("is_normalized exit result=%s", result)
    return result


def adjoint(gate: QGate) -> QGate:
    """Return the exact conjugate transpose of a finite square gate."""
    logger.debug("adjoint entry gate=%s", gate.name)
    _validate_gate(gate)
    result = QGate(
        f"{gate.name}†",
        tuple(tuple(conjugate(gate.matrix[column][row]) for column in range(len(gate.matrix)))
              for row in range(len(gate.matrix))),
    )
    logger.debug("adjoint exit gate=%s", result.name)
    return result


def _matrix_product(left: QGate, right: QGate) -> tuple[tuple[QAmp, ...], ...]:
    logger.debug("_matrix_product entry left=%s right=%s", left.name, right.name)
    left_dim, right_dim = _validate_gate(left), _validate_gate(right)
    if left_dim != right_dim:
        logger.error("_matrix_product dimension mismatch left=%d right=%d", left_dim, right_dim)
        raise ValueError("matrix-product gate dimensions must agree")
    columns = tuple(zip(*right.matrix, strict=True))
    result = tuple(
        tuple(
            _sum_amplitudes(tuple(a * b for a, b in zip(row, column, strict=True)))
            for column in columns
        )
        for row in left.matrix
    )
    logger.debug("_matrix_product exit dimension=%d", left_dim)
    return result


def _sum_amplitudes(items: tuple[QAmp, ...]) -> QAmp:
    logger.debug("_sum_amplitudes entry count=%d", len(items))
    total = A0
    for item in items:
        total = total + item
    logger.debug("_sum_amplitudes exit result=%r", total)
    return total


def unitarity_witness(gate: QGate) -> UnitarityWitness:
    """Check ``U†U = I`` and ``UU† = I`` over the full exact matrix."""
    logger.debug("unitarity_witness entry gate=%s", gate.name)
    dimension = _validate_gate(gate)
    dual = adjoint(gate)
    identity = tuple(
        tuple(A1 if row == column else A0 for column in range(dimension))
        for row in range(dimension)
    )
    left_ok = _matrix_product(dual, gate) == identity
    right_ok = _matrix_product(gate, dual) == identity
    result = UnitarityWitness(
        gate.name,
        dimension,
        left_ok,
        right_ok,
        "witnessed" if left_ok and right_ok else "refuted",
    )
    logger.debug("unitarity_witness exit result=%r", result)
    return result


def apply_unitary(gate: QGate, mode: QMode) -> QMode:
    """Apply a witnessed-unitary finite gate and verify exact norm preservation."""
    logger.debug("apply_unitary entry gate=%s basis=%r", gate.name, mode.basis)
    dimension = _validate_gate(gate)
    _validate_mode(mode)
    if dimension != len(mode.amplitudes):
        logger.error("apply_unitary dimension mismatch gate=%d mode=%d", dimension, len(mode.amplitudes))
        raise ValueError("gate and mode dimensions must agree")
    witness = unitarity_witness(gate)
    if witness.status != "witnessed":
        logger.error("apply_unitary nonunitary gate=%s", gate.name)
        raise ValueError("gate does not have a full exact unitarity witness")
    result = gate.apply(mode)
    if born_total(result) != born_total(mode):
        logger.error("apply_unitary internal norm mismatch gate=%s", gate.name)
        raise ArithmeticError("witnessed unitary failed exact norm preservation")
    logger.debug("apply_unitary exit gate=%s norm=%r", gate.name, result.norm2())
    return result
