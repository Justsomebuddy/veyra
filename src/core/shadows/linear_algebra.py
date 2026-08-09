"""Vector and matrix shadow seeds for Veyra linear algebra."""

from __future__ import annotations

from dataclasses import dataclass
import logging

from ..geometry.theorems import TheoremCard
from .ratio import RatioMode, add_ratios, multiply_ratios, ratio_from_ints, ratio_shadow, subtract_ratios

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class VectorMode:
    """Finite vector of ratio-mode coordinates."""

    values: tuple[RatioMode, ...]

    def __post_init__(self) -> None:
        """Validate nonempty vector."""
        logger.debug("VectorMode.__post_init__ entry dim=%d", len(self.values))
        if not self.values:
            logger.error("VectorMode empty")
            raise ValueError("vector must be nonempty")
        logger.debug("VectorMode.__post_init__ exit")

    @property
    def dimension(self) -> int:
        """Return vector dimension."""
        logger.debug("VectorMode.dimension entry")
        result = len(self.values)
        logger.debug("VectorMode.dimension exit result=%d", result)
        return result


@dataclass(frozen=True)
class MatrixTransformer:
    """Rectangular ratio matrix acting on vector shadows."""

    rows: tuple[tuple[RatioMode, ...], ...]

    def __post_init__(self) -> None:
        """Validate nonempty rectangular matrix."""
        logger.debug("MatrixTransformer.__post_init__ entry rows=%d", len(self.rows))
        if not self.rows or not self.rows[0]:
            logger.error("MatrixTransformer empty")
            raise ValueError("matrix must be nonempty")
        width = len(self.rows[0])
        if any(len(row) != width for row in self.rows):
            logger.error("MatrixTransformer ragged rows")
            raise ValueError("matrix rows must have equal width")
        logger.debug("MatrixTransformer.__post_init__ exit shape=%dx%d", len(self.rows), width)

    @property
    def shape(self) -> tuple[int, int]:
        """Return matrix shape."""
        logger.debug("MatrixTransformer.shape entry")
        result = (len(self.rows), len(self.rows[0]))
        logger.debug("MatrixTransformer.shape exit result=%r", result)
        return result


def vector_from_ints(values: list[int]) -> VectorMode:
    """Build vector from integer coordinates."""
    logger.debug("vector_from_ints entry values=%r", values)
    result = VectorMode(tuple(ratio_from_ints(value) for value in values))
    logger.debug("vector_from_ints exit dim=%d", result.dimension)
    return result


def matrix_from_ints(rows: list[list[int]]) -> MatrixTransformer:
    """Build matrix from integer rows."""
    logger.debug("matrix_from_ints entry rows=%r", rows)
    result = MatrixTransformer(tuple(tuple(ratio_from_ints(value) for value in row) for row in rows))
    logger.debug("matrix_from_ints exit shape=%r", result.shape)
    return result


def zero_vector(length: int) -> VectorMode:
    """Return a zero vector of requested length."""
    logger.debug("zero_vector entry length=%d", length)
    if length <= 0:
        logger.error("zero_vector invalid length=%d", length)
        raise ValueError("length must be positive")
    result = VectorMode(tuple(ratio_from_ints(0) for _ in range(length)))
    logger.debug("zero_vector exit dim=%d", result.dimension)
    return result


def dot_row(row: tuple[RatioMode, ...], vector: VectorMode) -> RatioMode:
    """Return exact dot product of one matrix row with a vector."""
    logger.debug("dot_row entry row_dim=%d vector_dim=%d", len(row), vector.dimension)
    if len(row) != vector.dimension:
        logger.error("dot_row dimension mismatch")
        raise ValueError("row and vector dimensions must agree")
    total = ratio_from_ints(0)
    for left, right in zip(row, vector.values, strict=True):
        total = add_ratios(total, multiply_ratios(left, right))
    logger.debug("dot_row exit result=%s", total.word)
    return total


def matrix_vector_apply(matrix: MatrixTransformer, vector: VectorMode) -> VectorMode:
    """Apply matrix transformer to a vector."""
    logger.debug("matrix_vector_apply entry shape=%r vector_dim=%d", matrix.shape, vector.dimension)
    if matrix.shape[1] != vector.dimension:
        logger.error("matrix_vector_apply dimension mismatch")
        raise ValueError("matrix columns and vector dimension must agree")
    result = VectorMode(tuple(dot_row(row, vector) for row in matrix.rows))
    logger.debug("matrix_vector_apply exit dim=%d", result.dimension)
    return result


def matrix_multiply(left: MatrixTransformer, right: MatrixTransformer) -> MatrixTransformer:
    """Return matrix product as transformer composition."""
    logger.debug("matrix_multiply entry left=%r right=%r", left.shape, right.shape)
    if left.shape[1] != right.shape[0]:
        logger.error("matrix_multiply dimension mismatch")
        raise ValueError("inner matrix dimensions must agree")
    rows = []
    for row in left.rows:
        out_row = []
        for col in range(right.shape[1]):
            out_row.append(dot_row(tuple(src[col] for src in right.rows), VectorMode(row)))
        rows.append(tuple(out_row))
    result = MatrixTransformer(tuple(rows))
    logger.debug("matrix_multiply exit shape=%r", result.shape)
    return result


def determinant_2x2(matrix: MatrixTransformer) -> RatioMode:
    """Return exact 2x2 determinant shadow."""
    logger.debug("determinant_2x2 entry shape=%r", matrix.shape)
    if matrix.shape != (2, 2):
        logger.error("determinant_2x2 invalid shape=%r", matrix.shape)
        raise ValueError("determinant seed only supports 2x2 matrices")
    a, b = matrix.rows[0]
    c, d = matrix.rows[1]
    result = subtract_ratios(multiply_ratios(a, d), multiply_ratios(b, c))
    logger.debug("determinant_2x2 exit result=%s", result.word)
    return result


def trace_2x2(matrix: MatrixTransformer) -> RatioMode:
    """Return exact 2x2 trace shadow."""
    logger.debug("trace_2x2 entry shape=%r", matrix.shape)
    if matrix.shape != (2, 2):
        logger.error("trace_2x2 invalid shape=%r", matrix.shape)
        raise ValueError("trace seed only supports 2x2 matrices")
    result = add_ratios(matrix.rows[0][0], matrix.rows[1][1])
    logger.debug("trace_2x2 exit result=%s", result.word)
    return result


def determinant_product_card(left: MatrixTransformer, right: MatrixTransformer) -> TheoremCard:
    """Certify det(AB)=det(A)det(B) for the 2x2 seed lane."""
    logger.debug("determinant_product_card entry")
    product = matrix_multiply(left, right)
    observed = determinant_2x2(product)
    expected = multiply_ratios(determinant_2x2(left), determinant_2x2(right))
    coherent = ratio_shadow(observed) == ratio_shadow(expected)
    result = TheoremCard("matrix-determinant-product", "exact", "coherent" if coherent else "broken", "none" if coherent else "det-product-gap", (("observed", str(ratio_shadow(observed))), ("expected", str(ratio_shadow(expected)))))
    logger.debug("determinant_product_card exit relation=%s", result.relation)
    return result


def eigen_candidate_card(matrix: MatrixTransformer, vector: VectorMode, eigenvalue: RatioMode) -> TheoremCard:
    """Check one exact eigenvector/eigenvalue shadow candidate."""
    logger.debug("eigen_candidate_card entry shape=%r vector_dim=%d", matrix.shape, vector.dimension)
    if all(ratio_shadow(value) == 0 for value in vector.values):
        logger.debug("eigen_candidate_card exit zero-vector")
        return TheoremCard("matrix-eigen-shadow", "exact", "blocked", "zero-vector", (("dimension", str(vector.dimension)),))
    observed = matrix_vector_apply(matrix, vector)
    expected = VectorMode(tuple(multiply_ratios(eigenvalue, value) for value in vector.values))
    coherent = tuple(map(ratio_shadow, observed.values)) == tuple(map(ratio_shadow, expected.values))
    result = TheoremCard("matrix-eigen-shadow", "exact", "eigen-shadow" if coherent else "blocked", "none" if coherent else "eigen-gap", (("lambda", str(ratio_shadow(eigenvalue))), ("dimension", str(vector.dimension))))
    logger.debug("eigen_candidate_card exit relation=%s", result.relation)
    return result


def linear_algebra_seed_checklist() -> tuple[str, ...]:
    """Return acceptance checklist for the vector/matrix seed."""
    logger.debug("linear_algebra_seed_checklist entry")
    result = ("vector-mode coordinates", "matrix-vector action", "2x2 determinant shadow", "eigen-candidate card")
    logger.debug("linear_algebra_seed_checklist exit count=%d", len(result))
    return result
