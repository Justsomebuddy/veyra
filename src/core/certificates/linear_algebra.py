"""Linear algebra seed certificate helper for the main Veyra suite."""

from __future__ import annotations

import logging

from ..certify_types import Certificate
from ..shadows.linear_algebra import determinant_2x2, determinant_product_card, eigen_candidate_card, linear_algebra_seed_checklist, matrix_from_ints, matrix_vector_apply, trace_2x2, vector_from_ints
from ..shadows.ratio import ratio_from_ints, ratio_shadow

logger = logging.getLogger(__name__)


def certify_linear_algebra_seed() -> Certificate:
    """Certify vector/matrix seed shadows."""
    logger.debug("certify_linear_algebra_seed entry")
    matrix = matrix_from_ints([[2, 0], [0, 3]])
    vector = vector_from_ints([1, 0])
    image = matrix_vector_apply(matrix, vector)
    det = determinant_2x2(matrix)
    trace = trace_2x2(matrix)
    product = determinant_product_card(matrix_from_ints([[1, 2], [3, 4]]), matrix_from_ints([[2, 0], [1, 2]]))
    eigen = eigen_candidate_card(matrix, vector, ratio_from_ints(2))
    passed = tuple(map(ratio_shadow, image.values)) == (2, 0) and ratio_shadow(det) == 6 and ratio_shadow(trace) == 5 and product.relation == "coherent" and eigen.relation == "eigen-shadow" and len(linear_algebra_seed_checklist()) == 4
    result = Certificate("linear_algebra_seed", "vector/matrix action, determinant, eigen shadow", passed, f"det={ratio_shadow(det)} eigen={eigen.relation}", 1)
    logger.debug("certify_linear_algebra_seed exit result=%r", result)
    return result
