# Necklace Congruences from Orbit Counting — N8

**Date:** 2026-08-27
**Status:** bounded executable lane plus exact formal instance cards.
**Implementation:** `src/core/necklace_congruence.py`
**Certificate:** `necklace_congruence_n8` in `src/core/certify.py`.
**Formal:** `proofs/lean/VeyraNecklaceCongruence.lean` (`THM_N8_001`–`007`).

## What this lane does

N8 is the first number-theory line whose divisibility facts are mechanized
natively: every congruence arises as an **exact partition of a finite mode set
into rotation orbits**, collected through `native_number.cycle_echo` (the
cut-free orbit object), never through a canonical representative and never as
a bare remainder check on opaque totals.

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
  (docs/06 §3 license); it decides nothing and only confirms that native
  counting reproduces the classical identity on the checked rows.
- **Composite-length counterpressure.** At length 4 the dichotomy fails —
  `abab` has orbit size 2 — recorded as a first-class blocked witness with
  obstruction `nonprime-length` and the exact counterexample.

## Evidence levels (do not collapse)

| Item | Status |
|---|---|
| Executable witnesses on exact bounded rows (`p ∈ {2,3,5,7}`, `k ∈ {2,3}`; `n ∈ 1..10`) | `EXECUTABLE_EVIDENCE` |
| `THM_N8_001`–`007` exact finite instance cards | `FORMALLY_PROVED` (Lean checks the literal fixtures only) |
| All-`p` / all-`n` general statements | not established by this lane; see non-claims |

## Non-claims

1. No general theorem is inferred from the bounded rows; passing certificates
   promotes nothing.
2. Fermat's little theorem and the Gauss congruence are classical results.
   N8 claims only a native orbit-counting **mechanization** of exact instances
   and bounded witness rows; the novelty claimed is the binding of the
   congruence to the orbit partition of Veyra modes, not the mathematics.
3. The Lean cards quantify over host `Nat`/`List` fixtures (host-carried
   computation; see README "How to read claims"); no completed-infinity,
   density, asymptotic, or analytic claim follows.
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
