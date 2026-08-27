# Toward Principality: the Forcing Structure — TR-2/2

**Date:** 2026-08-27
**Status:** partial proof of the Principality Conjecture (`THM-TR2-001`,
doc 183): the forcing floor and prime reduction are `FORMALLY_PROVED`; the
single-prime case is reduced to Achievability; the forced-locus law holds
on all 6285 exhaustively scanned words; the two-prime territory is probed,
not settled. The conjecture **remains `CONJECTURE`**.
**Implementation:** `src/core/break_locus.py` (forcing extension).
**Certificate:** `projection_forcing_tr2b` in `src/core/certify.py`.
**Formal:** `proofs/lean/VeyraProjectionPower.lean` (`THM_TR2_002`–`005`).

## Lemma A — the forcing floor (`FORMALLY_PROVED` core)

Projection onto a letter pair is a monoid homomorphism, so the projection
of a k-th power is the k-th power of the projection
(`THM_TR2_003_projection_of_power`, real induction over an
encoding-free `pick`/`powL` pair; the append-homomorphism is
`THM_TR2_002`). Consequently, for every exponent-k candidate `v`:

> `Δ(w,v) ⊇ F_k(w) := { p : proj_p(w) is not a k-th power }`.

The floor is executable (`forced_pairs`) and is counterpressured on every
candidate of every scanned word: **zero violations in 6285 words**.

## Lemma B — prime reduction (`FORMALLY_PROVED` core)

`powL u (b·a) = powL (powL u b) a` (`THM_TR2_005_pow_mul`, with
`THM_TR2_004_pow_add`): a k′-power is a k-power whenever k | k′, so
`F_k ⊆ F_{k′}` along divisibility and minimal deltas arise only at prime
exponents dividing `gcd` of the letter multiplicities.

## Single-prime reduction (prose-derived; native formalization OPEN)

If exactly one prime q divides the gcd — true of **all seven** scanned
shapes — then every delta contains `F_q(w)`, so:

> **Principality ⇔ Achievability:** `B(w) = {F_q(w)}` iff some candidate
> attains the floor; and any locus element whatsoever contains `F_q(w)`.

Derived from Lemmas A/B plus ⊆-minimality; recorded per the external-draft
precedent (registry-core W-001): prose-derived from `THM-TR2-002/003/005`,
Lean formalization of the reduction itself `OPEN`.

## The Forced-Locus Law (pinned after observation)

Exhaustive sweeps re-ran the seven shapes under the law
`B(w) == {F_q(w)}` for every non-degenerate single-prime word:

| shape | words | Lemma-A violations | law mismatches |
|---|---:|---:|---:|
| a³b³ / a⁴b² / a⁴b⁴ | 20 / 15 / 70 | 0 | 0 |
| a²b²c² / a²b²c⁴ / a⁴b⁴c² | 90 / 420 / 3150 | 0 | 0 |
| a²b²c²d² | 2520 | 0 | 0 |
| **total** | **6285** | **0** | **0** |

So on every scanned word the locus **is** the closed-form floor — no
candidate enumeration needed — and Achievability held universally in
range. `THM-TR2-001` (single-prime slice) is thereby equivalent, on
scanned territory and conjecturally beyond, to:

> **Achievability Conjecture.** For prime q, some exponent-q candidate
> attains `Δ = F_q(w)`.

## The two-prime frontier

Two incomparable floors exist in principle: `w = (aabbab)²` over `{a,b}`
has `F_2 = ∅` and `F_3 = {ab}` (executable fixture). A deliberate
counterexample attempt at shape a⁶b⁶c⁶ — ab-projection `(aabbab)²`
(square, not cube), ac-projection `(aacc)³` (cube, not square),
bc-projection `(bc)⁶` — **dies on realizability**: the three pairwise
orders force the position cycle `a₅ < b₄ < c₄ < a₅`, so no word has these
projections. This *merge obstruction* is the first structural hint of
*why* principality might survive multi-prime shapes.

Seeded deterministic probe (seed 20260827) of a⁶b⁶c⁶: **1200 sampled
words, all principal, `max_locus_size = 1`, floor respected** — `SAMPLED`
evidence only; the shape (17,153,136 words) is far beyond exhaustion and
nothing is claimed for it.

## Non-claims

1. `THM-TR2-001` is not proved; its status is unchanged (`CONJECTURE`).
2. The single-prime reduction is prose-derived; its Lean formalization,
   the Achievability Conjecture, and the two-prime case are `OPEN`.
3. Probe evidence is sampled, never exhaustive, and says nothing beyond
   its exact seed and sample count.
4. Statuses are `witnessed`/`blocked`/`refused`; `proved` appears only in
   the names of Lean-checked declarations.

## Verification

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q tests/test_projection_forcing.py
python scripts/check_lean_sources.py --jobs 8
```
