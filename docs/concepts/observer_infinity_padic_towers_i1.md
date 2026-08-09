# I1 — Observer Infinity and p-adic Residue Towers

**Status:** bounded implementation reviewed; immutable full release gate passed
**Date:** 2026-08-06
**Capability effect:** none

## Purpose

I1 tests one precise reading of infinity inside Veyra:

> an infinite process is presented through a coherent observation at every
> finite depth, not through a Python loop that reaches a final infinity value.

This is a completion-motivated observer experiment using an inverse-system
pattern. It is deliberately separated into:

1. finite executable windows that can expose finite incompatibility;
2. an all-depth Lean family supplied as a theorem hypothesis;
3. classical bounded prime-power residue windows expressed in observer
   language.

I1 does **not** construct a p-adic inverse limit or p-adic carrier. It supplies
finite residue diagnostics, a one-link modular-addition law, and a separate
all-depth prefix theorem whose family is an explicit hypothesis.

## Finite prefix windows

A finite prefix window contains an alphabet and stages indexed `0..N`. Stage
`n` contains exactly `n` symbols. It is structurally valid even when adjacent
stages disagree, because the first disagreement is useful evidence rather than
a constructor error.

Adjacent coherence means

```text
stage[n + 1][:n] == stage[n].
```

The executable report returns the first failing link and symbol index, or a
coherent result with scope `finite-window`. A periodic constructor provides a
deterministic family of finite observations, but a checked depth `N` does not
prove that arbitrary finite data extend to an all-depth tower.

## All-depth prefix theorem

The Lean artifact uses a family

```text
Π(n) : Fin n → α
```

and assumes every larger view restricts to every smaller one. Its recovered
stream reads position `i` from view `i+1`.

- `THM-I1-001` proves that the recovered stream restricts to every declared
  finite view.
- `THM-I1-002` proves uniqueness among streams matching every finite view.
- `THM-I1-003` proves that one explicit restriction disagreement blocks any
  globally matching stream.

These are conventional extensional results over an already supplied
Nat-indexed family. They are not an existence theorem derived from a finite
Python window, compactness argument, choice principle, or new cardinal.

## Prime-power residue windows

For a checked prime `p`, stage `k` has modulus and canonical residue

```text
m_k = p^(k+1),       0 <= r_k < m_k.
```

Adjacent compatibility is

```text
r_(k+1) mod p^(k+1) = r_k.
```

For example, the integer `307` has the coherent `p=5` window

```text
2 mod 5, 7 mod 25, 57 mod 125, 307 mod 625.
```

The candidate `(2,8,57)` is structurally valid but obstructed immediately:
`8 mod 5 = 3`, not `2`.

Equal-prime/equal-depth coherent windows support componentwise canonical
addition and multiplication. Python checks only those declared finite
precisions. `THM-I1-004` mirrors that construction: it first canonicalizes the
upper sum modulo `p^(k+2)`, then projects it modulo `p^(k+1)`, and proves this
equals the canonical lower-stage sum. The divisibility calculation works for
any base, while the Python `p-adic` name additionally requires deterministic
primality.

## Executable API

- `prefix_alphabet`, `prefix_stage`, `prefix_tower_window`,
  `restrict_prefix`, `periodic_prefix_window`, `first_prefix_obstruction`, and
  `prefix_coherence_report` build and inspect only bounded prefix windows.
- `prime_base`, `padic_residue_stage`, `padic_residue_window`,
  `project_padic_stage`, `integer_padic_window`, `first_padic_obstruction`,
  `padic_coherence_report`, `add_padic_windows`, and
  `multiply_padic_windows` build and inspect only bounded residue windows.
- `certify_observer_infinity_i1` binds the full Lean bytes and exact four
  theorem symbols before reporting one level-1 certificate.

## Relation to the Veyra stack

### R11 observers

Prefixes and residues are finite observer shadows. Equality under the complete
declared prefix family gives stream extensionality only for that family.

### G4 gluing

A restriction mismatch is a gluing obstruction. G4's finite atlas result does
not prove arbitrary inverse-limit nonemptiness, so I1 states the all-depth
family as a Lean hypothesis.

### Number theory

The residue rows follow the standard inverse-system pattern behind p-adic
integers. I1 translates bounded stages into Veyra terms—observation,
restriction, echo, obstruction—rather than constructing the inverse limit or
claiming discovery of a new number system.

### R7/R8 evidence

The digest-bound Lean artifact supplies a level-1 theorem-card certificate.
It is not an R7 proof term, new theorem-derived Essence layer, R8 promotion
contract, or proof-completeness claim.

## Fail-closed boundary

The executable surface rejects:

- subclasses, Boolean integers, mutable/non-tuple containers, and bad stage
  numbering or lengths;
- empty/duplicate alphabet symbols, foreign prefix symbols, and declared
  resource-limit overflow;
- non-prime or oversized bases, wrong moduli, and noncanonical residues;
- arithmetic on different-prime, different-depth, or incoherent windows;
- Lean digest mismatch before compilation, missing/renamed/duplicate/out-of-order
  theorem declarations, and source changes after captured compilation.

Repeated symbols inside a prefix remain valid. An incoherent but structurally
valid candidate remains inspectable so its first obstruction can be reported.

## Evidence

I1 registers one certificate and no Sage symbol, notebook, ready layer,
taxonomy entry, or promotion. Initial review findings led to upper-stage
canonicalization in `THM-I1-004`, hostile-metaclass-safe pre-gate logging, a
cheap character bound before UTF-8 encoding, and exact ordered/unique theorem
declarations. Post-fix focused tests pass `19/19`; pinned Lean 4.30.0-rc2
warning-as-error checks full SHA-256
`7be8b425c0cefb243706d71d4774fa886df5ddb75c611cf6e2fb848930a75975`.
Scoped Ruff, pycompile, SHA continuity, diff, hygiene, and secret scan are green. The
continuation registers 77 certificates while Sage/layers/notebooks/taxonomy remain
`93 / 36 / 41 / 2-4-25-5`.

Independent re-review reports no blocker/high/medium after the repairs. The
immutable 77-certificate I1 snapshot passed serial the complete verification suite and source
continuity (`verify_rc=0`, `continuity_rc=0`, `17833s`); later P0/P1 changes are
outside that snapshot.

## Explicit non-claims

I1 proves no new infinity, cardinal hierarchy, transfinite recursion,
diagonal theorem, compactness, choice, general inverse-limit existence,
topological completion, p-adic field law, analytic convergence, manifold,
sheaf, physical field, mathematical novelty, or superiority over classical
number theory.

## Next experiments, not I1 claims

- profinite completion using all moduli ordered by divisibility;
- comparison with the existing finite Cauchy/refinement shadows;
- coinductive eventually periodic modes and bisimulation;
- only after those, a separately reviewed topology or transfinite programme.
