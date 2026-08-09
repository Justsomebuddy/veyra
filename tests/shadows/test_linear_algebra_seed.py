from src.core.linear_algebra import determinant_2x2, determinant_product_card, eigen_candidate_card, linear_algebra_seed_checklist, matrix_from_ints, matrix_multiply, matrix_vector_apply, trace_2x2, vector_from_ints, zero_vector
from src.core.ratio import ratio_from_ints, ratio_shadow


def test_matrix_vector_action_and_shape():
    matrix = matrix_from_ints([[2, 0], [0, 3]])
    vector = vector_from_ints([1, 2])
    image = matrix_vector_apply(matrix, vector)
    assert matrix.shape == (2, 2)
    assert image.dimension == 2
    assert tuple(map(ratio_shadow, image.values)) == (2, 6)


def test_determinant_trace_and_product_card():
    left = matrix_from_ints([[1, 2], [3, 4]])
    right = matrix_from_ints([[2, 0], [1, 2]])
    product = matrix_multiply(left, right)
    card = determinant_product_card(left, right)
    assert ratio_shadow(determinant_2x2(left)) == -2
    assert ratio_shadow(trace_2x2(product)) == 12
    assert card.relation == "coherent"
    assert card.obstruction == "none"


def test_eigen_candidate_card_blocks_zero_vector():
    matrix = matrix_from_ints([[2, 0], [0, 3]])
    good = eigen_candidate_card(matrix, vector_from_ints([1, 0]), ratio_from_ints(2))
    blocked = eigen_candidate_card(matrix, zero_vector(2), ratio_from_ints(2))
    assert good.relation == "eigen-shadow"
    assert blocked.obstruction == "zero-vector"
    assert len(linear_algebra_seed_checklist()) == 4
