# Necklace Congruences from Orbit Counting — N8

**Date:** 2026-08-27
**Status:** bounded executable lane plus exact formal instance cards.
**Implementation:** `src/core/necklace_congruence.py`
**Certificate:** `necklace_congruence_n8` in `src/core/certify.py`.
**Formal:** `proofs/lean/VeyraNecklaceCongruence.lean` (`THM_N8_001`–`007`,
exact fixtures) and, since 2026-09-03, `proofs/lean/VeyraNecklaceOrbit.lean`
(`THM_NO_001`–`009`, the general theorems: rotation group law, gcd
stabilizer, prime-length dichotomy for every prime and every alphabet, the
orbit-partition counting law, and Fermat `k^p ≡ k (mod p)` by orbit
counting for all primes `p` and all bases `k`).

## What this lane does

N8 mechanizes divisibility facts as **exact partitions of a finite mode set
into rotation orbits**, collected through `native_number.cycle_echo` (the
cut-free orbit object), never through a canonical representative and never as
a bare remainder check on opaque totals. Two host gates are declared rather
than hidden (README "Host-carried computation"): the prime-length
precondition of the dichotomy/Fermat witnesses is decided by the host-int
`primes.is_prime_int`, and orbit sizes are the host `len` of the rotation
set. Totals are sums of orbit sizes read off the partition.

- **Prime-length orbit dichotomy.** At prime length `p`, every rotation orbit
  has size `1` (constants) or exactly `p`. Witnessed orbit-by-orbit with an
  explicit counterexample slot.
- **Fermat partition count.** The `k^p − k` nonconstant words are exactly
  `(k^p − k)/p` full orbits of size `p`; divisibility is read off the
  partition itself (`partition_exact`), not computed by `%` on the total.
- **Gauss primitive-count divisibility.** Ordered-primitive words of length
  `n` fall into full orbits of size `n` (verified natively per word), so
  `n` divides the primitive count: `count == orbit_count · n`. The Möbius sum
  `Σ_{d|n} μ(d)·k^{n/d}` is a **declared school shadow** cross-check
  (docs/06 §3 license): it is reported in `shadow_match` and never decides
  the witness status (until 2026-09-03 a shadow mismatch did flip the
  status to `blocked`, contradicting this sentence; the certificate still
  requires `shadow_match` as a separately declared cross-check).
- **Composite-length counterpressure.** At length 4 the dichotomy fails —
  `abab` has orbit size 2 — recorded as a first-class blocked witness with
  obstruction `nonprime-length` and the exact counterexample.

## Evidence levels (do not collapse)

| Item | Status |
|---|---|
| Executable witnesses on exact bounded rows (`p ∈ {2,3,5,7}`, `k ∈ {2,3}`; `n ∈ 1..10`) | `EXECUTABLE_EVIDENCE` |
| `THM_N8_001`–`007` exact finite instance cards | `FORMALLY_PROVED` (Lean checks the literal fixtures only) |
| `THM_NO_003` prime-length dichotomy, `THM_NO_004` distinct rotations, `THM_NO_005` partition counting law, `THM_NO_006`–`008` Fermat decomposition/divisibility/congruence — all primes `p`, all bases `k`, any alphabet type | `FORMALLY_PROVED` (general statements over host `Nat`/`List`, real inductions, Mathlib-free; `THM_NO_009` recovers the divisibility content of the Fermat-count cards `THM_N8_004/005` plus `p = 7` from the general theorem; the dichotomy cards follow from `THM_NO_003/004`; `THM_N8_006/007` are not covered) |
| All-`n` Gauss divisibility `n ∣ #aperiodic words of length n` (every positive `n`, every `k`), with aperiodic ⇔ primitive (not a proper power) | `FORMALLY_PROVED` since 2026-09-05 (`THM_NO_010`/`011`, `VeyraNecklaceOrbit.lean`); the Möbius count identity `#primitive = Σ_{d|n} μ(d) k^{n/d}` itself remains `OPEN` as a formal theorem |

## Non-claims

1. No general theorem is inferred from the bounded rows; passing certificates
   promotes nothing. The general Fermat statement is a separate Lean
   theorem (`THM_NO_007`/`008`), proved by the orbit argument itself, not
   by the executable rows.
2. Fermat's little theorem and the Gauss congruence are classical results.
   N8 claims only a native orbit-counting **mechanization** of exact instances
   and bounded witness rows; the novelty claimed is the binding of the
   congruence to the orbit partition of Veyra modes, not the mathematics.
3. The Lean cards and theorems quantify over host `Nat`/`List` (host-carried
   computation; see README "How to read claims"); no completed-infinity,
   density, asymptotic, or analytic claim follows, and "for all primes" is
   the host `Nat` quantifier, not a native Veyra quantifier.
4. The Möbius column is shadow bookkeeping, not a native derivation of `μ`.
5. No new silence tokens are introduced; witness statuses are
   `witnessed`/`blocked` per CONTRIBUTING and the silence-status map.

## Verification

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q tests/test_necklace_congruence.py
python scripts/check_lean_sources.py --jobs 8
```

## Candidate continuations (not commitments)

A necklace-ring/Witt-vector bridge toward the PΩ2 carrier (ghost components
as phase observers; Verschiebung as weave) is a research candidate only; it
requires its own registry step and licenses nothing here.
