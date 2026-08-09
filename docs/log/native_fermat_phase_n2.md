# Native Fermat Phase N2

**Date:** 2026-07-07
**Status:** finite prime-period Fermat phase theorem rows shipped.
**Implementation:** `src/core/numbers/native_number_theorems.py`, `src/core/certificates/native_number_theorems.py`, `veyra_sage/number_theory.py`.
**Certificate:** `native_fermat_phase_n2`.

## Purpose

N2 strengthens native number theory beyond fixed divisibility fixtures. It does not claim full number theory, but it adds a reusable finite theorem schema:

1. build a native closed `Mode` whose length observer gives a prime period `p`;
2. build native unit `Breath` rows whose length observers give every unit `1..p-1`;
3. check the Fermat phase return `u^(p-1) mod p = 1` for every derived unit;
4. require multiplicative-orbit coverage of all nonzero residues before the row is marked `derived`.

## New row

`NativeFermatPhaseRow` records:

| Field | Meaning |
|---|---|
| `period` / `mode_length` | requested period and native observed Mode length |
| `unit_lengths` | native observed Breath lengths for all units |
| `residues` | `u^(p-1) mod p` for every unit |
| `orbit_lengths` | multiplicative phase orbit length for each unit |
| `coverage` | union of all phase orbits over the period |
| `status` | `derived` for prime periods, `blocked` for invalid/composite periods |

Canonical derived rows use periods `2, 3, 5, 7`; obstruction rows use `1, 4, 6`.

## Boundary

This is stronger than one-off finite tables because each prime-period row covers every unit residue for that period. It is still bounded:

- prime-ness is an integer-shadow observer on native Mode length;
- the theorem is finite over canonical periods, not an unbounded proof for all primes;
- it does not implement quadratic reciprocity;

## Sage surface

`VeyraNumberTheoryLab.fermat_rows()` exposes four derived rows and three blocked rows. `number_theory_lab_summary()` now reports:

```python
{
    "fermat_rows": 7,
    "fermat_derived": 4,
    "fermat_units": 13,
}
```

The generated `notebooks/generated/global/number_theory.*` artifact includes the N2 checks while preserving the same 5-cell notebook shape.

## Verification

```bash
PYTHONPATH=. python3 -m pytest -q \
  tests/numbers/test_native_number_theorems.py \
  tests/sage/test_veyra_sage_number_theory.py \
  tests/shadows/test_certify.py \
  tests/sage/test_veyra_sage.py
```

Expected N2 signals:

- `native_fermat_phase_n2` certificate passes;
- `native_number_theorem_summary()` reports `fermat_derived=4`, `fermat_units=13`, and `fermat_blocked=3`;
- full suite reports `45/45` certificates after N2.
