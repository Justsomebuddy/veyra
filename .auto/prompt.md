# Autoresearch: Veyra open-problem proof campaign

## Objective
Prove, in the project's own pinned Lean 4.30.0-rc2 formalism, the GENERAL
versions of statements that the repository currently registers only as fixed
finite cards, and attack concrete open registry items. Every claim must be
Lean-checked with `-DwarningAsError=true`; no sorry/admit/axiom.

## Metrics
- **Primary**: `new_checked_proofs` (unitless, higher is better) — number of
  sorry-free `theorem`/`lemma` declarations that compile in
  `experimental/research_lean/`.
- **Secondary**: `research_theorems_total`, `base_build_s`,
  `research_compile_s`, main-tree gate (pass/fail via checks).

## How to Run
`./.auto/measure.sh` — compiles base modules once into
`data/tmp/research-olean/`, recompiles research files, emits METRIC lines.
`.auto/checks.sh` — recompiles the pinned 48-file tree (correctness gate).

## Files in Scope
- `experimental/research_lean/*.lean` — NEW research proofs (the only files
  we add/change).
- `scripts/check_research_lean.py`, `.auto/*` — campaign harness.

## Off Limits
- `proofs/lean/*.lean` — the pinned 48-file inventory; never modify.
- `src/`, `vam/`, `veyra_sage/`, `tests/` — production code is frozen for
  this campaign; do not weaken or bypass any validation to make a proof pass.
- Registry files (`THEOREMS.md`, `docs/reference/theorem-registry-*.md`) —
  status promotion is upstream ceremony, not this campaign.

## Constraints
- Lean 4.30.0-rc2 exact (elan at ~/.elan/bin).
- `-DwarningAsError=true`; `sorry`/`admit`/`axiom` forbidden in research files.
- Main-tree gate (`scripts/check_lean_sources.py --jobs 8`) must stay green.
- Do not overfit: a theorem that passes only by weakening the statement to a
  tautology or by hardcoding a finite case is a discard.

## Target list (from repository open items)
- T1 general binomial symmetry: choose n k = choose n (n-k) [fixed card B001 is 6,2]
- T2 binomial divisibility: p prime, 0<k<p -> p | choose p k
- T3 Fermat's little theorem: p prime -> a^p ≡ a (mod p) [generalizes F002-style rows]
- T4 prime-factor existence + Euclid: every n>1 has a prime divisor; for every
  finite prime list there is a prime outside it
- T5 general chord symmetry: chord law for arbitrary modulus/phase [fixed card C002 is 12,0,3,9]
- T6 general probability complement: P(complement) = total - P(event) [fixed cards P001..P003]
- T7 PΩ2 multiplicative inverse for unit first-digit families (field structure direction)
- T8 general cyclic period/reflection identities beyond C001

## What's Been Tried
- Batch 1 (11 proofs): general binomial symmetry (k<=n), general chord
  reflection, general complement/union/independence counting, reflected
  period + helper lemmas (VeyraResearchCards.lean).
- Batch 2-3 (+17): prime-divisor existence, Euclid infinitude via
  product+1, 2 prime (VeyraResearchPrimes.lean); shadow arithmetic —
  stitch shadows +, weave shadows *, injective shadow, comm/assoc/
  distributivity/units transport = registry THM-001/002/003
  (VeyraResearchShadow.lean).
- Batch 4 (+9): Euclid-algorithm gcd with termination, gcd divisibility,
  Bezout identity (Int coefficients), Euclid's lemma p|ab -> p|a or p|b
  (VeyraResearchGcd.lean).
- Batch 5 (+6): general Pythagorean triple law (Euclid's formula for all
  Int m n) + square expansion lemmas (VeyraResearchPythagorean.lean).
- Batch 6 (+5): binomial factor identity k*C(p,k)=p*C(p-1,k-1) for all
  1<=k<=p and prime divisibility of middle coefficients via Euclid's lemma
  (VeyraResearchFermat.lean).
- Batch 7 (+13): binomial theorem as a sum identity, freshmen's dream,
  and FERMAT'S LITTLE THEOREM (prime p, all a: a^p % p = a % p) — the
  named unbounded-Fermat repair-track item (VeyraResearchBinomSum.lean).
- Key techniques learned (see .auto/ideas.md for details): running
  invariant H(m) for list-index shifts; forward rw + conv lhs/rhs to
  avoid variable-pattern rewrite traps; prove Pascal via have+rw instead
  of unfolding recursive defs in the goal.
