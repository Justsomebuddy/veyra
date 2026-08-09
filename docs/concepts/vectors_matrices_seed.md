# Vectors and matrices seed

**Status:** executable seed, not full linear algebra.
**Implemented:** `src/core/shadows/linear_algebra.py`, `src/core/certificates/linear_algebra.py`.

## Native intent

The `vectors-matrices` school row now has first-class Veyra objects instead of only pointing at the old linear-equation and transformer hooks.

A vector is a finite `VectorMode` of ratio coordinates.  A matrix is a rectangular `MatrixTransformer` whose rows act on vector shadows by exact dot rows.  This keeps the layer inside existing ratio/balance semantics and avoids treating matrices as primitive school objects.

## Executable objects

- `VectorMode(values)` — nonempty ratio-coordinate vector.
- `MatrixTransformer(rows)` — nonempty rectangular ratio matrix.
- `matrix_vector_apply(A, v)` — exact finite action.
- `matrix_multiply(A, B)` — transformer composition.
- `determinant_2x2(A)` and `trace_2x2(A)` — 2x2 seed shadows.
- `determinant_product_card(A, B)` — theorem card for `det(AB)=det(A)det(B)` in the 2x2 lane.
- `eigen_candidate_card(A, v, λ)` — exact candidate check with a `zero-vector` obstruction.

## Certificate

`linear_algebra_seed` checks:

1. matrix-vector action on a diagonal transformer;
2. determinant and trace shadows;
3. determinant product coherence;
4. one eigen-candidate shadow;
5. the four-item seed checklist.

## What is still not claimed

- no general `n×n` determinant algorithm;
- no row-reduction/system-solver layer beyond existing linear equations;
- no spectral theorem, diagonalization, norm, or inner-product space;
- no Sage facade yet for matrix parents.

## Tests

- `tests/shadows/test_linear_algebra_seed.py`
- `tests/shadows/test_certify.py`
- `tests/registry/test_curriculum_map.py`
