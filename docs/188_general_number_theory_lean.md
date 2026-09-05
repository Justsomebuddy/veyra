# General Number-Theory Theorems in the Stable Lean Graph

**Date:** 2026-09-03
**Status:** three new stable Lean sources (54th–56th), `FORMALLY_PROVED`;
no public alias, certificate, or release-bundle entry (not
`PUBLICLY_VALIDATED`); no native Veyra quantifier is claimed.
**Formal:** `proofs/lean/VeyraNecklaceOrbit.lean` (`THM_NO_001`–`009`),
`proofs/lean/VeyraPrimitiveRoot.lean` (`THM_RT_001`–`004`),
`proofs/lean/VeyraPadicDomain.lean` (`THM_PD_001`–`003`).
**Origin:** the 2026-09-03 critical review of the number-theory layers found
that no general number-theoretic theorem existed in the stable Lean graph:
the N8 cards are `decide` fixtures, the DI shadow laws are definitional, the
only "Euclid" statement is `(n·k+1) % n = 1 % n`, and every PΩ2 declaration
holds for an arbitrary base `b ≥ 2` because none consumes the primality
witness. This document records what replaced that state.

## What is proved (all Mathlib-free, Lean core only)

| ID | Statement (host `Nat`/`List` quantifiers) | Proof shape |
|---|---|---|
| `THM_NO_001` | `rot a (rot b l) = rot (a + b) l` — rotations compose | cyclic-read extensionality |
| `THM_NO_002` | the shift stabilizer of a word is closed under `Nat.gcd` | `Nat.gcd.induction` (Euclid's algorithm on shifts) |
| `THM_NO_003` | prime length `p`, shift `0 < d < p` fixing the word ⇒ the word is constant | `gcd d p = 1` ⇒ shift 1 fixes ⇒ constant |
| `THM_NO_004` | nonconstant word of prime length: its `p` rotations are pairwise distinct | from `THM_NO_003` |
| `THM_NO_005` | duplicate-free list closed under an orbit assignment with orbits of exact size `p` has length divisible by `p` | strong induction, one orbit removed per step |
| `THM_NO_006` | `k^p = k + p·q` for every prime `p` and every `k` (constants + full orbits) | explicit enumeration `words k p`, `THM_NO_004`/`005` |
| `THM_NO_007` / `008` | `p ∣ k^p − k`; `k^p % p = k % p` | from `THM_NO_006` |
| `THM_NO_009` | `3 ∣ 2³−2`, `5 ∣ 2⁵−2`, `7 ∣ 2⁷−2`, `7 ∣ 3⁷−3`: the divisibility content of the N8 Fermat-count cards `THM_N8_004/005` plus `p = 7`; the dichotomy cards follow from `THM_NO_003/004`; the Gauss `n = 4` card and the composite counterexample are not covered | `THM_NO_007` + bounded `decide` primality |
| `THM_NO_010` | `n ∣ #{aperiodic words of length n over k letters}` for every `n > 0` and every `k` (Gauss divisibility, composite lengths included) | aperiodic words are rotation-closed with `n` distinct rotations; `THM_NO_005` |
| `THM_NO_011` | aperiodic (no shift `0 < d < n` fixes the word) ⇔ primitive (not a proper literal power), for nonempty words | gcd stabilizer ⇒ power of the first `gcd` letters; powers are fixed by the root length |
| `THM_RT_001` | powers of one word commute | power addition |
| `THM_RT_002` | `u ++ v = v ++ u ↔ ∃ z i j, u = z^i ∧ v = z^j` (Lyndon–Schützenberger) | strong induction on `|u| + |v|`, prefix cancellation |
| `THM_RT_003` | every nonempty word is a positive power of a primitive word | constructive bounded proper-period search (no `Classical.choice`) |
| `THM_RT_004` | the primitive root and its exponent are unique | `THM_RT_002` + prefix comparison |
| `THM_PD_001` | `ZpVeyra(p)`: families nonzero at depths `n`, `m` have a product nonzero at depth `n + m` | valuation split `X = pᵃ·u`, `p ∤ u`; Euclid's lemma from `no_proper_divisor` |
| `THM_PD_002` | constructive "nonzero somewhere" product law | `THM_PD_001` |
| `THM_PD_003` | `x·y = 0 → x = 0 ∨ y = 0` (no zero divisors) | classical corollary; `Classical.choice` in its printed closure |

## Why these three

- **Fermat by orbit counting** is exactly the argument the N8 lane mechanizes
  on fixtures; it is now a theorem for all primes and all bases, and the
  N8 cards are recovered from it (`THM_NO_009`). The Gauss divisibility at
  every positive length is now also a theorem (`THM_NO_010`), with the
  aperiodic ⇔ primitive bridge (`THM_NO_011`) tying it to the primitive-root
  theory; the Möbius count identity is not formalized.
- **Unique primitive root** is the precise content of "every mode is uniquely
  a power of a primitive rhythm" (docs/02 §4–5, docs/11 P2/P3); until now
  it was only executable (`primitive_root`, `is_ordered_primitive`).
- **Primality made load-bearing in PΩ2**: `THM_PD_001` is the first theorem
  in the family whose proof uses `VeyraPrimeWitness.no_proper_divisor`; with
  it, `ZpVeyra(p)` is distinguished from `lim← Z/bⁿ` for composite `b`.

## Evidence levels (do not collapse)

| Item | Status |
|---|---|
| `THM_NO_*`, `THM_RT_*`, `THM_PD_001/002` | `FORMALLY_PROVED`; axiom closures `propext`/`Quot.sound` only (`#print axioms` in `VeyraPadicDomain.lean`; the other two files use no classical reasoning) |
| `THM_PD_003` | `FORMALLY_PROVED` with `Classical.choice` (declared) |
| Public aliases / certificate / release bundle for any of them | absent — not `PUBLICLY_VALIDATED` |
| Native (non-host) quantification, completed infinity, the Möbius count identity, Z_p valuation/units/Hensel | not claimed / `OPEN` |

## Non-claims

1. "For all primes" is the host `Nat` quantifier (README "How to read
   claims"); nothing here is a native Veyra derivation of number theory.
2. Fermat's little theorem, Lyndon–Schützenberger, and the integral-domain
   property of Z_p are classical; the contribution is their Mathlib-free
   formalization inside this graph, replacing fixture cards and inert
   hypotheses, not new mathematics.
3. W-001 / THM-001–003 remain `CONJECTURE` for the native Mode; nothing here
   touches that status.

## Real-Sage cross-check (independent oracle)

`veyra_sage/number_theory_oracle.py` re-derives the same claims with SageMath
10.7 primitives that share no code with the production lanes and compares
exactly; without real Sage every entry point fails closed
(`real-sage-required-for-number-theory-oracle`) and the lab summary is a typed
`unavailable` record. Canonical bounds and results (2026-09-04, 0 mismatches,
about 3 s):

| Lane | Sage side | Checks |
|---|---|---|
| `fermat-lyndon` | `k^p − k = p · LyndonWords(k,p).cardinality()` for primes ≤ 13, alphabets 2..5; N8 full-orbit counts tied for `p ∈ {2,3,5,7}`, `k ∈ {2,3}` | 32 |
| `gauss-mobius` | `Σ_{d|n} μ(d) k^{n/d} = n · #Lyndon(k,n)` and `n ∣` count for `n ≤ 12`, `k ≤ 4`; N8 Gauss witnesses tied for `n ≤ 10` | 56 |
| `primitive-root` | `modes.primitive_root` vs `Word.primitive` / `primitive_length` on every word of length ≤ 7 over 3 letters | 3279 |
| `commutation` | `uv = vu` iff empty or equal Sage primitive roots, all ordered pairs of words of length ≤ 5 over 2 letters (Lyndon–Schützenberger, `THM_RT_002`) | 3969 |
| `padic-domain` | `THM_PD_001` coordinate law and `Zp` valuation additivity on seeded random cells for `p ∈ {2,3,5,7,11}`; base-6 counter-cell `2·3 ≡ 0 (mod 6)` | 879 |
| `fermat-phase` | N2 orbit lengths = Sage multiplicative orders, Lagrange, `primitive_root(p)` generator; composite periods 4, 6, 9, 561 fail exactly at the exhibited unit (`power_mod`) | 10 |
| `break-locus-gcd` | gcd-form locus from Sage projection exponents = `locus_formula` on 615 exhaustive words of five shapes plus the witness `w*` (`e_ab, e_ac, e_bc = 2, 3, 1`) | 616 |

The oracle is `EXECUTABLE_EVIDENCE`: agreement on finite bounds promotes
nothing; the general statements are the Lean theorems above. It runs in
`scripts/sage_smoke.py` (mandatory `witnessed` under `--require-sage`,
typed `unavailable` tolerated otherwise) and in
`tests/test_veyra_sage_number_theory_oracle.py` (real-Sage lanes skip without
Sage; the fail-closed path is portable).

## Verification

```bash
python scripts/check_lean_sources.py --jobs 8        # 56/56 pinned sources
python scripts/check_research_lean.py                # manifest binds the 56-source base
sage -python scripts/sage_smoke.py --require-sage    # real-Sage oracle: 7 lanes, 0 mismatches
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q tests/test_veyra_sage_number_theory_oracle.py
```
