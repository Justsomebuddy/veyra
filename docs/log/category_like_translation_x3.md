# Category-Like Translation X3

**Date:** 2026-07-07
**Status:** Sprint X3 closed as a bounded translation layer.
**Implementation:** `src/core/shadows/category_like.py`, `src/core/certificates/category.py`, `veyra_sage/category_like.py`.
**Certificate:** `category_like_translation_x3`.

## Purpose

X3 adds a category-like vocabulary without claiming full category theory. The layer names finite Veyra objects, morphisms, invariants, and universal shadows only as executable observer rows over current transformer schemas.

## Vocabulary

| Word | Executable row | Meaning |
|---|---|---|
| Object | `VeyraObject` | finite observer sample cloud, not a primitive set |
| Morphism | `VeyraMorphism` | transformer-backed arrow between declared object shadows |
| Invariant | `InvariantRow` | before/after observer property row |
| Universal shadow | `UniversalShadowRow` | bounded identity/associativity/mismatch witness |

## Finite diagram

The default X3 diagram uses four finite ratio-shadow objects:

- `A = {0,1,2}`;
- `B = {1,2,3}`;
- `C = {2,3,4}`;
- `D = {4,6,8}`.

The arrows are transformer-backed:

- `id_A : A → A`;
- `shift_AB : A → B`, the affine transformer `x ↦ x+1`;
- `shift_BC : B → C`, again `x ↦ x+1`;
- `double_CD : C → D`, the affine transformer `x ↦ 2x`.

## Counterexamples and discipline

- `sample-count` survives `shift_AB` as an invariant row.
- `sum-shadow` is deliberately marked `broken` under the same shift.
- `bad-composition` is blocked by `object-shadow-mismatch`.

This keeps the layer honest: it records transformer closure and bounded identity/associativity samples, but does not promote them to a full categorical universal property.

## Sage notebook surface

`VeyraCategoryLab` exposes:

- `object_rows()`;
- `morphism_rows()`;
- `invariant_rows()`;
- `universal_rows()`;
- `summary()` and `build_category_like_notebook()`.

The generated notebook is tracked as `notebooks/generated/global/category_like.*` and participates in the global artifact manifest.

## Verification

```bash
PYTHONPATH=. python3 -m pytest -q tests/shadows/test_category_like.py tests/sage/test_veyra_sage_category_like.py tests/shadows/test_certify.py tests/sage/test_veyra_sage.py
```

Expected X3 signals:

- `category_like_translation_x3` certificate passes;
- `category_like_lab_summary()` reports `objects=4`, `closed=4`, `blocked=1`;
- generated notebook artifact count becomes 39.
