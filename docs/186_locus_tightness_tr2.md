# Tightness of the Break-Locus Bound and Type Spectra — TR-2/4

**Date:** 2026-08-27
**Status:** classification slice on top of the Break-Locus Formula
(doc 185): the prime-count bound is proved tight by an explicit
constructive family; the small-shape type spectrum is complete; general
type-matrix realizability is `OPEN` (narrowed). A literature
due-diligence pass on the whole lane is in progress and will be recorded
separately; until it lands, no external-novelty wording is used beyond
"not found by us yet".
**Implementation:** `src/core/break_locus.py` (tightness/type extension).
**Certificate:** `locus_tightness_tr2d` in `src/core/certify.py`.

## Tightness Theorem (constructive; prose-derived + machine-verified)

> For every set of distinct primes `{q₁, …, q_r}` there is a word `w`
> with `|B(w)| = r`: the bound `|B(w)| ≤ #primes(gcd)` from doc 185 is
> tight.

**Star construction.** Alphabet `x₁, …, x_r` plus a hub `z`; every letter
has multiplicity `N = q₁⋯q_r`. Demand only the hub projections: for each
`i`, `proj(x_i, z) = (x_i^{N/q_i} z^{N/q_i})^{q_i}` — a `q_i`-th power of
a primitive word, hence not a `q_j`-power for `j ≠ i`. The `x_i`-blocks
are inserted into the shared `z`-stream at the gaps of their own
granularity (multiples of `N/q_i`); the constraint graph is a star, so no
position cycle (the doc-184 merge obstruction) can arise, and the word
exists explicitly. Then each floor `F_{q_i}` omits its own special pair
`(x_i, z)` and contains every other `(x_j, z)`, so the `r` prime floors
are pairwise incomparable and the formula gives `|B(w)| = r`. ∎

Machine verification (`verify_tightness`): `r = 1, 2, 3` (primes
`{2}`, `{2,3}`, `{2,3,5}`; word lengths 4, 18, 120) — locus sizes exactly
`1, 2, 3`, special-pair pattern and pairwise incomparability confirmed;
for `r = 2` the floors are exact (`F₂ = {ab, bz}`, `F₃ = {ab, az}` for
the witness `aaabbzzbbzaaazbbzz`) and the closed formula agrees with full
candidate enumeration.

## Type spectra

The formula reduces everything to the matrix of pair power-types. On the
exhaustive smallest three-pair shape `a²b²c²` at `q = 2`, **all 8
power/not-power vectors over the three pairs are realized** (90 words
scanned); on `a³b³` at `q = 3`, both vectors are realized. So on the
smallest shapes there is no hidden constraint among pair types. The
general realizability question — which pair-type matrices over several
primes are realizable by a word — is `OPEN`, now narrowed by: the star
case (hub-shared constraints) is always realizable (theorem above), and
full three-pair freedom holds at the smallest shape (exhaustive).

## Consequences for the classification

With doc 185: `B(w)` is computable in closed form; its size is exactly
the number of ⊆-minimal prime floors; the size bound `#primes(gcd)` is
attained for every `r`. What remains for a complete classification is
the exact realizability characterization of floor families (equivalently
type matrices) beyond the star case and the smallest shapes.

## Non-claims

1. The literature report has since landed (doc 187): the fixed-relation
   characterization used throughout is **classical (Duboc 1986,
   Prop. 1.7)** and the up-closedness spine is folklore; only the
   lattice-parametric layer — including this tightness theorem — carries
   a candidate-novelty status, with mandatory pre-submission checks still
   unperformed.
2. The spectrum completeness is exhaustive only for the stated shapes;
   nothing is claimed beyond them.
3. Statuses are `witnessed`/`blocked`/`refused`; `proved` appears only in
   Lean declaration names.

## Verification

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q tests/test_locus_tightness.py
```
