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
2. **The dichotomy is derived, never counted:** a word's orbit size is
   length/period; the period is read off the cut-free `primitive_root`, and
   `period ∈ {1, p}` follows from the divisor witness. No rotation
   enumeration decides anything.
3. **The congruence is a reconstruction:** `weave(p̄, full_orbit_count)` must
   breath-equal the nonconstant tally. Divisibility `p | k^p − k` is woven,
   not remainder-checked; `%` appears in no decision path.

## N8 subsumed as one licensed statement

Composed with DI-1 over the alphabet depth — letters are minted from the
intrinsic index, and each step classifies only the rotation-closed delta of
words containing the new letter while the validator recomputes the whole
cell independently — the N8 Fermat instances become **one licensed family
statement** per witnessed-prime length: licensed for length 3 to depth 4 and
length 5 to depth 3 in the certificate, with the full-orbit and tally counts
echoing the N8 witnesses exactly (cross-tie test). The N8 Lean instance
cards remain the formal anchors; the license is executable evidence, not a
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
| `THM_DI2_001`–`005` shadow laws | `FORMALLY_PROVED` (conditional statements and one real-induction monotonicity law over host `Nat`) |
| General all-prime/all-depth Fermat as a formal theorem | not established; the license is depth-replayable evidence only |

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
