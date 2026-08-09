# Native Number-Theory X2

**Date:** 2026-07-07
**Status:** Sprint X2 closed as executable native number-theory expansion; N2 now extends theorem pressure with finite Fermat phase rows.
**Implementation:** `src/core/numbers/native_number.py`, `src/core/certificates/native_number.py`, `veyra_sage/number_theory.py`.
**Certificate:** `native_number_theory_x2`.

## Purpose

X2 extends the earlier cycle-echo number layer without turning school integers into primitives. Divisibility, prime-like behavior, and rank comparisons are represented as Veyra-native rows over finite modes and only then exposed as school shadows.

## New rows

| Row | Function | Meaning |
|---|---|---|
| Cycle divisibility | `cycle_divisibility_row(part, whole)` | repeat `part`, compare the lift with `whole` by cycle echo |
| Prime obstruction | `prime_obstruction_rows(modes)` | classify resonance-prime variants and record obstructions |
| Rank/factor comparison | `rank_factor_comparison(whole, candidates, max_defects)` | keep spectrum rank, compression rank, and factor-lift status separate |
| Fermat phase N2 | `native_fermat_phase_row(period)` | derive all unit residues from native Breath lengths and check finite prime-period Fermat phase return |

## Acceptance examples

- `ba` divides `abab` because the repeated lift `baba` is cycle-equivalent to `abab`.
- `aba` is blocked against `abab` by `length-obstruction`.
- `ab` is a native resonance-prime variant; `aa` is blocked by `cycle-power`; `a` is blocked by `unit-or-silent`.
- For whole `abab`, candidates `ab` and `ba` have factor-lift hits, while `aa` remains blocked.
- For prime period `5`, native unit lengths `(1,2,3,4)` all satisfy `u^4 mod 5 = 1`, and their phase orbits cover all nonzero residues.

## Sage notebook surface

`VeyraNumberTheoryLab` exposes:

- `divisibility_rows()`;
- `prime_rows()`;
- `rank_factor_rows()`;
- `fermat_rows()`;
- `summary()` and `build_number_theory_notebook()`.

The generated notebook is tracked as `notebooks/generated/global/number_theory.*` and participates in the global artifact manifest.

## Verification

```bash
PYTHONPATH=. python3 -m pytest -q tests/numbers/test_native_resonance_number.py tests/sage/test_veyra_sage_number_theory.py tests/shadows/test_certify.py tests/sage/test_veyra_sage.py
```

Expected X2 signals:

- `native_number_theory_x2` certificate passes;
- `native_fermat_phase_n2` certificate passes;
- `number_theory_lab_summary()` reports `factor_hits=2`, `blocked=1`, `fermat_derived=4`, `fermat_units=13`;
- generated notebook artifact count becomes 38.
