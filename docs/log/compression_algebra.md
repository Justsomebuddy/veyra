# Compression Algebra

**Date:** 2026-06-03
**Status:** Sprint B executable layer.
**Implementation:** `src/core/numbers/compression_algebra.py`.
**Certificate:** `compression_algebra` in `src/core/certify.py`.

## Purpose

Sprint B turns resonance/compression into algebraic machinery:

1. edit-distance resonance with insert/delete drift;
2. recursive compression trees;
3. native polynomial root/factor hits;
4. comparison of uniform/manual/aura-derived mismatch costs.

## Edit drift resonance

`edit_resonance_profile(part, whole, max_edits)` compares a cyclic whole against repeated part candidates with Levenshtein insert/delete/substitution distance.

Example:

```python
edit_resonance_profile(mode("ab"), mode("abxab"), 1).distance == 1
```

Interpretation: a rhythm can survive one inserted tact.  This is different from bounded substitution-only resonance.

## Hierarchical compression tree

`hierarchical_compression_tree(mode, max_depth, max_defects)` recursively chooses positive-saving explanations.

For `ababab`, the first split is:

- whole: `ababab`;
- part: `ab`;
- repeats: `3`;
- saving: `4`.

This is the seed of multi-part/hierarchical explanation algebra.

## Polynomial root/factor search

`polynomial_factor_search(poly, candidates)` evaluates candidate roots as Veyra `RatioMode` values and returns exact factor hits.

For `x²-1`, roots `-1` and `1` produce linear factor hits:

- `x+1`;
- `x-1`.

The quotient is built by rational-shadow synthetic division, while the API returns Veyra polynomial/ratio objects.

## Cost strategy comparison

`compare_cost_strategies()` compares three weighted resonance strategies:

| Strategy | Meaning |
|---|---|
| uniform | every mismatch costs default `1` |
| manual | explicit user/research cost map |
| aura | cost map derived from `TactAuraEcho` context |

For `part=ab`, `whole=abac`, budget `0.5`:

- uniform rejects: cost `1.0`;
- manual accepts: cost `0.25`;
- aura accepts: cost `0.25`.

## Verification

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q tests/numbers/test_compression_algebra.py tests/shadows/test_certify.py
python3 scripts/certify_veyra.py
```

Verified on 2026-06-03: full tests `295/295`, doctest `41/41`, Sage smoke ok, certificates `19/19`, line hygiene `0` files over 300.

Expected signals:

- `compression_algebra` passes;
- certificate suite total increases to `19`;
- Essence/Core layer count increases to `12`.

## Next

Sprint B is closed at executable-contract level.  Next high-value work: Sage notebook/table maturation or proof-step coverage.
