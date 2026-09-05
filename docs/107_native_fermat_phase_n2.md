# Native Fermat Phase N2

**Date:** 2026-07-07
**Status:** finite prime-period Fermat phase theorem rows shipped.
**Implementation:** `src/core/native_number_theorems.py`, `src/core/certify_native_number_theorems.py`, `veyra_sage/number_theory.py`.
**Certificate:** `native_fermat_phase_n2`.

## Purpose

N2 strengthens native number theory beyond fixed divisibility fixtures. It does not claim full number theory, but it adds a reusable finite theorem schema:

1. build a native closed `Mode` whose length observer gives a period `p`;
2. build native unit `Breath` rows whose length observers give every unit `1..p-1`;
3. check the Fermat phase return `u^(p-1) mod p = 1` for every derived unit
   (host `pow(u, p-1, p)` on the observed lengths — see the boundary below);
4. for prime periods additionally require that every multiplicative orbit
   length divides `p-1` (a Lagrange instance) and that some orbit has length
   exactly `p-1` (a cyclicity instance) before the row is marked `derived`.

Correction 2026-09-03: the earlier fourth condition, "multiplicative-orbit
coverage of all nonzero residues", is automatically satisfied for every
prime period (each unit lies in its own orbit), so it exerted no pressure;
it is still reported in `coverage` but no longer counts as a check. Composite
periods used to be pre-filtered by `is_prime_int` before any arithmetic, so
the obstruction rows never exhibited a Fermat failure; they are now computed
and blocked on the first unit whose phase return fails (period 4: unit 2,
residue 0; period 6: unit 2, residue 2; period 561, a Carmichael number:
unit 3, residue 375).

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

- prime-ness is an integer-shadow observer on native Mode length, and the
  phase-return arithmetic is host `pow`-mod; `derived` means "checked by
  host modular arithmetic on natively observed lengths", never a native
  derivation — the native objects are built *from* the integer and observed
  back as the same integer;
- the theorem is finite over canonical periods, not an unbounded proof for
  all primes (the all-prime statement is `THM_NO_008` in
  `proofs/lean/VeyraNecklaceOrbit.lean`, proved by orbit counting);
- it does not implement quadratic reciprocity;

## Sage surface

`VeyraNumberTheoryLab.fermat_rows()` exposes four derived rows and three blocked rows. `number_theory_lab_summary()` now reports:

```python
{
    "fermat_rows": 7,
    "fermat_derived": 4,
    "fermat_units": 21,
}
```

The generated `notebooks/generated/global/number_theory.*` artifact includes the N2 checks while preserving the same 5-cell notebook shape.

## Verification

```bash
PYTHONPATH=. python3 -m pytest -q \
  tests/test_native_number_theorems.py \
  tests/test_veyra_sage_number_theory.py \
  tests/test_certify.py \
  tests/test_veyra_sage.py
```

Expected N2 signals:

- `native_fermat_phase_n2` certificate passes;
- `native_number_theorem_summary()` reports `fermat_derived=4`, `fermat_units=13`, and `fermat_blocked=3`;
- full suite reports `45/45` certificates after N2.
