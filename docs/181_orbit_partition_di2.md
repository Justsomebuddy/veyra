# Orbit-Partition Rule — DI-2 Candidate

**Date:** 2026-08-27
**Status:** `INTERNAL_RESEARCH_CANDIDATE` rule with executable license
machinery and formally proved shadow laws. Not an adopted axiom.
**Implementation:** `src/core/orbit_partition.py`
**Certificate:** `orbit_partition_di2` in `src/core/certify.py`.
**Formal:** `proofs/lean/VeyraOrbitPartition.lean` (`THM_DI2_001`–`005`).
**Companion:** DI-1 (`docs/180_doctrinal_induction_di1.md`) supplies the
family dimension; DI-2 supplies the grouping inference.

## The rule (candidate)

DI-2 licenses a congruence from partition structure, with every load-bearing
step native:

1. **Primality is witnessed, not assumed:** for every candidate divisor
   length `d`, `structural_divide(p̄, d̄)` must leave a residual — an exact
   divisor blocks the witness with the offending row (`composite-length`).
2. **The period is decided structurally:** the cyclic period of a word is
   the least shift `d` whose unary length divides `p̄` exactly under
   `structural_divide` and whose rotation echoes the word; `period ∈ {1, p}`
   then follows from the divisor witness. (Until 2026-09-03 the period was
   read off `modes.primitive_root`, which uses host `%`/`//`; the sentence
   "`%` appears in no decision path" was false then and is true now.)
3. **The congruence is a reconstruction:** `weave(p̄, full_orbit_count)` must
   breath-equal the nonconstant tally. Declared boundary: the tally is the
   *enumerated* orbit total (every class's rotations counted through the
   cut-free `cycle_echo` orbit, host `len`), so the woven equality is a
   cross-check between the structural period classification and host
   enumeration — not a host-free derivation of `p | k^p − k`.

## N8 cells re-derived as licensed family statements

Composed with DI-1 over the alphabet depth — letters are minted from the
intrinsic index, and each step classifies only the rotation-closed delta of
words containing the new letter while the validator recomputes the whole
cell independently — the N8 Fermat cells at a witnessed-prime length become
**one licensed family statement** for that length: licensed for length 3 to
depth 4 and length 5 to depth 3 in the certificate, with the full-orbit and
tally counts echoing the N8 witnesses exactly (cross-tie test). Coverage is
stated exactly: DI-2 covers `(p=3, k≤4)` and `(p=5, k≤3)`; N8 covers
`p ∈ {2,3,5,7} × k ∈ {2,3}`; neither subsumes the other (an earlier
heading said "N8 subsumed", which overstated). The general all-`p`/all-`k`
statement is a formal theorem elsewhere (`THM_NO_007`/`008` in
`VeyraNecklaceOrbit.lean`); the license is executable evidence, not a
formal theorem.

## Adversarial controls (shipped in the certificate)

- composite length 4 blocks at the factory with the exact-divisor row;
- a tally bomb that drops one tact at depth 3 is caught by the independent
  validator at exactly `step-invalid-at-depth:3`;
- DI-1's anchor-renaming uniformity applies unchanged (letters depend on the
  intrinsic index, not the anchor name).

## Evidence levels (do not collapse)

| Item | Status |
|---|---|
| The DI-2 rule itself | `INTERNAL_RESEARCH_CANDIDATE` — F1 adoption would be a separate registry act |
| Family licenses over the exact bounded probes | `EXECUTABLE_EVIDENCE` |
| `THM_DI2_001`–`005` shadow laws | `FORMALLY_PROVED` — but definitional in content: `001` instantiates its own hypothesis (`hp per h`), `002`/`004` are `omega` arithmetic, `005` is a numeral `rfl`; only `003` is a (trivial) real induction. They pin the shadow semantics and prove nothing about orbits |
| General all-prime/all-depth Fermat as a formal theorem | established outside this lane by `THM_NO_007`/`008` (`VeyraNecklaceOrbit.lean`, orbit counting over host `List`/`Nat`); the DI-2 license itself remains depth-replayable evidence only and inherits nothing from that theorem |

## Non-claims

1. No completed carrier and no unconditional universal: the license asserts
   replayable depths under the doctrine; P1-D2 countermodels remain binding.
2. Fermat's little theorem is classical; DI-2 registers the native
   partition mechanization and the licensing composition, not the
   mathematics.
3. `THM_DI2_004` is conditional on its explicit ordering hypotheses and
   constructs nothing (house rule: conditional implication only).
4. Word enumeration and loop counters are docs/06 §3 shadow bookkeeping;
   every acceptance is a native breath equality or a division proof.
5. Passing the certificate promotes nothing; statuses never say `proved`.

## Verification

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q tests/test_orbit_partition.py
python scripts/check_lean_sources.py --jobs 8
```
