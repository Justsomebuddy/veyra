# The Break-Locus Formula and the Resolution of Principality — TR-2/3

**Date:** 2026-08-27
**Status:** resolution of `THM-TR2-001` (doc 183): the general conjecture
is **REFUTED** by an explicit witness; the single-prime slice is **derived
as a theorem**; both follow from the Break-Locus Formula
(`THM-TR2-008`), whose formal cores are Lean-checked and whose prose
assembly is recorded under the external-draft precedent (W-001).
**Implementation:** `src/core/break_locus.py` (firstSlice, achieved-floor
check, closed-form locus, agreement sweeps, refutation witness).
**Certificate:** `break_locus_formula_tr2c` in `src/core/certify.py`.
**Formal:** `proofs/lean/VeyraProjectionPower.lean`
(`THM_TR2_002`–`007`).

## Achievability — proved, constructively

Let `firstSlice_k(w)` keep, for every letter, its first `count/k`
occurrences. For every matched pair `p ∈ M_k` the projection of the slice
is exactly the first block of the power `proj_p(w) = r_p^k` — because the
first `m_x/k` occurrences of `x` in `r_p^k` all lie in the first block —
and **the first block of a power is its root**
(`THM_TR2_007_power_first_block`, from `THM_TR2_006_first_block`,
machine-checked). Hence `v₀ = firstSlice_k(w)^k` satisfies
`Δ(w, v₀) ⊆ F_k(w)`, and with the Lemma-A floor (`THM_TR2_003`):

> **Achievability Theorem.** For every valid exponent `k`, the floor is
> attained: `Δ(w, firstSlice_k(w)^k) = F_k(w)`.

The slice/projection commutation step is prose (plus the executable
`achieved_floor_check`, verified on **every valid exponent of every one of
the 6285 scanned words plus the witness — zero failures**); its native
formalization is `OPEN`.

## The Break-Locus Formula (`THM-TR2-008`)

Combining Achievability (upper bound) with Lemmas A/B (lower bound and
prime reduction):

> **B(w) = the ⊆-minimal antichain of { F_q(w) : q prime, q | gcd(m) }.**

The locus is a closed formula for every word — no candidate enumeration,
no reachability search. The realizability wall of doc 184 vanishes: the
floors are computed from an existing word. Executable agreement:
`locus_formula == break_locus` on all 6285 exhaustively scanned words
(zero mismatches) and on the witness.

## Consequences for `THM-TR2-001`

1. **Single-prime slice — PROVED (derived).** One prime ⇒ one floor ⇒
   `B(w) = {F_q(w)}`. This is exactly why all 6285 scanned words (whose
   shapes all had single-prime gcd) were principal: the conjecture was
   *true on the entire scanned territory for a structural reason*.
2. **General form — REFUTED.** Witness:
   > `w* = aaccabbbaccaaccbbb` (counts 6,6,6)
   with `proj_ab = aaabbbaaabbb` (a square, not a cube) and
   `proj_ac = (aacc)³` (a cube, not a square), so
   `F₂ = {ac, bc}` and `F₃ = {ab, bc}` are incomparable and
   **`B(w*) = { {ab,bc}, {ac,bc} }` — two minimal breaking doctrines.**
   The word was *constructed from the formula* (crossed floor types with
   the `bc` pair left free, so no position cycle can arise), machine
   verified: floors, minimal antichain, Lemma-A respect, and attainment
   at both exponents. Direct BFS confirmation at 18 letters exceeds the
   declared class caps and is honestly not performed: the refutation
   rests on the formula — every ingredient Lean-checked except the prose
   assembly and the classical projection lemma, which was cross-checked
   against BFS truth on six full small lattices with zero mismatches
   (doc 183).
3. **Why the earlier probe missed it:** crossed floor types are rare
   (squares among 12-letter pair words ≈ 2%), and the seeded 1200-sample
   probe simply never drew one; the deliberate doc-184 counterexample
   died because it over-constrained *exact* projections — the formula
   shows only the *types* matter.

## Non-claims

1. `THM-TR2-008` is prose-derived from Lean-checked cores; a native
   end-to-end formalization (including slice/projection commutation and
   the classical projection lemma) is `OPEN`.
1a. **Literature (doc 187):** the fixed-relation power characterization
   used here is classical — **Duboc 1986, Prop. 1.7** — and must be cited
   as the engine of the formula; the `firstSlice` root is very likely an
   easy corollary of the same machinery. Only the lattice-parametric
   assembly (`B(w)`, the prime-floor formula, tightness, the singleton
   criterion, the refutation witness) is a candidate contribution, with
   mandatory checks unperformed.
2. Bound corollary: `|B(w)| ≤` number of distinct primes dividing
   `gcd(m)` — derived, same status.
3. Nothing is claimed beyond the stated evidence classes; statuses are
   `witnessed`/`blocked`/`refused`; `proved` appears only in Lean
   declaration names and in the registry rung of those declarations.

## Verification

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q tests/test_break_locus_formula.py
python scripts/check_lean_sources.py --jobs 8
```
