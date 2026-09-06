# Resonance Arithmetic — the docs/02 Vocabulary Made Executable and Formal

**Date:** 2026-09-06
**Status:** native executable lane (`EXECUTABLE_EVIDENCE`) plus a stable Lean
source (`FORMALLY_PROVED`, not `PUBLICLY_VALIDATED`); closes the "open research
task" of docs/02 §6.
**Implementation:** `src/core/resonance_arithmetic.py`
**Certificate:** `resonance_arithmetic_ra` in `src/core/certify.py` (suite 111).
**Formal:** `proofs/lean/VeyraResonanceArithmetic.lean` (`THM_RA_001`–`014`).
**Guard:** `tests/test_resonance_decision_paths.py` (AST: no host arithmetic on
decision paths of any number-theory lane).
**Oracle:** lane `resonance-arithmetic` of `veyra_sage.number_theory_oracle`.

## Why this lane exists

The 2026-09-06 correspondence audit found that docs/02 promised a number
theory in the vocabulary of recurrence ("divisibility = resonance, primality =
indecomposable rhythm, modularity = phase obstruction, gcd = strongest shared
echo, lcm = smallest shared closure") while every executable decision ran on
host integers (`%`, `pow`, `is_prime_int`) and every general theorem was stated
over host `Nat`. This lane makes each item of that list a definition with an
executable native witness and a machine-checked theorem stated in the
vocabulary itself.

## The vocabulary, executable

All decisions run on `native_runtime.Mode` recurrences through
`structural_divide` (prefix removal), `stitch` and `weave`; the only observer
consulted is the length observer. Host integers enter through the declared
transport `unary` and leave through `length` (docs/06 §3), both listed in
`SHADOW_LICENSED`.

Before divisor enumeration, `resonance_prime_witness` admits the candidate by
native stitch with the zero recurrence on the supplied anchor. Foreign tacts
or an anchor mismatch return `blocked`, including at length two where there
are no proper candidate divisors. Lengths below two retain `length-too-short`;
valid witness rows and formal claim levels are unchanged.

| docs/02 phrase | Definition (native) | Function |
|---|---|---|
| `a ▹ b`, resonance | `structural_divide(b, a)` is exact | `resonates` |
| phase obstruction | residual of maximal extraction of the modulus | `phase_residual` |
| `x ≡_m y` | equal residuals after maximal `m`-extraction | `phase_congruent` |
| first-mode / indecomposable rhythm | every candidate divisor from `2` up to the rhythm leaves a residual | `resonance_prime_witness` |
| strongest shared echo | structural Euclid on residuals | `shared_echo` |
| smallest shared closure | `left` woven by `right / echo` | `shared_closure` |
| Fermat phase return | `phase_power(u, p−1, p)` returns to the unit phase; orbit lengths resonate inside `p−1`; some orbit has length `p−1` | `fermat_phase_witness` |
| Euclid escape | the successor of the weave of listed rhythms leaves the unit phase under each and carries a new resonance prime | `euclid_escape_witness` |

Consumers moved onto these decisions: the N2 Fermat rows
(`native_number_theorems.native_fermat_phase_row`: phase returns, orbits and
primality are native up to `NATIVE_PERIOD_LIMIT = 31`, with the host `pow`
route kept only as a declared shadow and above-limit fallback that says so in
its boundary text) and the N8 prime-length gate
(`necklace_congruence.orbit_dichotomy_witness`).

## The vocabulary, formal

`VeyraResonanceArithmetic.lean` works on the native `Recurrence` of
`VeyraNativeArithmetic.lean` (stitch, weave, `resonates` unchanged; the file is
imported, not edited, so the R9 trust chain is untouched).

| ID | Statement in the vocabulary | Proof |
|---|---|---|
| `THM_RA_001`–`003` | the one-tact length observer `toNat` is a bijection onto `Nat` carrying stitch to `+` and weave to `×` | structural inductions |
| `THM_RA_004` | weave is commutative, associative, distributes over stitch, has the single pulse as unit | transport through the observer |
| `THM_RA_005` | resonance is the divisibility preorder: reflexive, transitive, antisymmetric, `resonates f c ↔ toNat f ∣ toNat c` | transport |
| `THM_RA_006` | structural division reconstructs, bounds the residual, and is unique | `Nat.div_add_mod`, cancellation |
| `THM_RA_007` | `x ≡_m y` iff both equal `m`-weaves stitched with one common residual shorter than `m` — exactly docs/02 §6 | uniqueness of division |
| `THM_RA_008` | phase congruence is an equivalence compatible with stitch and weave | `Nat.add_mod`, `Nat.mul_mod` |
| `THM_RA_009` | resonance primes are exactly the primes of the length observer | definitional transport |
| `THM_RA_010` | **Fermat, natively:** for a resonance prime `p` and any `k`, `rpow k p ≡_p k` | `THM_NO_008` |
| `THM_RA_011` | the escape leaves the unit phase under every listed factor | mod arithmetic |
| `THM_RA_012` | **Euclid, natively:** no finite list of resonance primes exhausts them — the escape carries a resonance prime outside the list | constructive least-factor search |
| `THM_RA_013` | the shared echo resonates in both and every common resonator resonates in it (gcd universal property) | `Nat.dvd_gcd` |
| `THM_RA_014` | both resonate in the shared closure and it resonates in every common closure (lcm universal property) | `Nat.lcm_dvd` |

Axiom closures are `propext`/`Quot.sound` at most; no classical choice.

## Boundaries (do not collapse)

1. The proofs pass through the observer `toNat`; that is the declared
   consistency anchor of the shadow layer (README "Host-carried computation"),
   now a theorem (`THM_RA_001`–`003`) instead of a convention. The *statements*
   are native; the *metatheory* is Lean over `Nat`, as docs/149 §3 requires.
2. "For all resonance primes" is the host `Nat` quantifier through the
   bijection; no native Veyra quantifier or completed infinity is claimed.
3. Executable rows are bounded (`EXECUTABLE_EVIDENCE`); passing certificates
   promote nothing. W-001 / THM-001–003 for the native `Mode` of AX-007 keep
   their registry status; `THM_RA_001`–`003` concern the Lean `Recurrence`.
4. Multi-tact modes (words over several tacts) are the free monoid; this lane is
   the one-tact layer. Nothing here is new mathematics; it is the promised
   vocabulary honored by definitions, witnesses and proofs.

## Verification

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q tests/test_resonance_arithmetic.py tests/test_resonance_decision_paths.py
python scripts/check_lean_sources.py --jobs 8        # 59/59
sage -python scripts/sage_smoke.py --require-sage    # oracle lane resonance-arithmetic witnessed
```
