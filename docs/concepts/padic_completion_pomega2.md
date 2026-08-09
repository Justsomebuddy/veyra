# PΩ2: exact ledger-relative prime-power completion

## Status

PΩ2 is released as one exact prime-power completion principle for a checked
prime `p`. It is not a generic inverse-limit theorem and not a metaphysical
claim about completed infinity.

Evidence consists of the 17 named Lean declarations in
`VeyraPadicCompletion.lean`, a concrete prime-instance application, and the
explicit `Quot.sound`/`propext` assumption ledger recorded in `THEOREMS.md`.
The evidence establishes only the relative object described here.

## Exact object

For `M_n = p^(n+1)` and `ZMod(M_n) = Fin M_n`, reduction is the canonical
remainder map

```text
ρ_m^n : ZMod(M_n) → ZMod(M_m),  m ≤ n.
```

The carrier is the literal dependent subtype

```text
ZpVeyra(p) = { a : (n : Nat) → ZMod(M_n) //
               ∀ m n, m ≤ n → ρ_m^n(a_n) = a_m }.
```

This is not a finite residue list, a productive procedure, or the former
custom-structure presentation. Equality is Lean equality after joint
coordinate separation; integer representatives are not substituted for
residue equality.

## Constructed algebra

`veyraCanonicalStageRingLaws` constructs zero, one, negation, addition, and
multiplication on every finite `Fin M_n` stage, proves reduction preserves all
five operations, and supplies the commutative-ring equations. Family
operations are coordinatewise and preserve compatibility.

`THM_POMEGA2_017_ppcp_introduction` takes only a prime witness. It no longer
takes an uninstantiated operations parameter: the returned bundle is indexed
by `veyraCanonicalStageRingLaws hp`.

The generated isolated instance defines `pomega2PrimeWitness`, then constructs

```text
pomega2ConcreteCompletion :=
  THM_POMEGA2_017_ppcp_introduction pomega2PrimeWitness.
```

Thus the positive runtime result is conditional neither on caller-supplied
ring laws nor on a hidden family adapter.

## Formal boundary

- Lean artifact: `proofs/lean/VeyraPadicCompletion.lean`.
- SHA-256: `28052d0260b1535e484ddd8e70f97fea945ca3ff9a23c358bb45d209a071a18f`.
- Toolchain: `leanprover/lean4:v4.30.0-rc2`, with exact elan/Lean binary pins.
- Generic rows: `THM_POMEGA2_001..017`, exact order, no `sorry` or `admit`.
- Canonical operations closure: `propext`.
- Final theorem and concrete instance closure: `Quot.sound`, `propext`.
- The generic source is compiled in an isolated directory to `VeyraPadicCompletion.olean`;
  the generated prime source imports that exact object and applies
  theorem 017.

Compilation shares one deadline and one live output cap across toolchain
attestation and both Lean phases. Captured generic bytes and regenerated prime
bytes are checked before execution and reread/regenerated afterward.

## Ledger

The 45-row ledger exposes the exact theorem/import dependency DAG. In
particular:

- theorem 005 directly depends on theorem 002;
- theorems 014 and 016 directly depend on theorem 009;
- proof irrelevance is a used foundation row for subtype proof-field erasure;
- `Std.Tactic` and `Init.GrindInstances.Ring.Fin` are explicit trusted imports;
- canonical operations and the p-specific theorem-017 application are named
  rows;
- the aggregate theorem closure is exactly `Quot.sound`, `propext`.

The package, run digest, and positive judgment bind the canonical-operations
and concrete-instance identifiers. Results are revalidated by fresh replay.

## Established, relative to the ledger

Prime lower bound, modulus divisibility, reduction congruence/identity/
composition, family compatibility, universal realization of every admitted
compatible family, coordinate agreement, joint separation, relative
uniqueness, zero/one formation, addition/negation/multiplication closure, the
full coordinatewise commutative ring, and the exact PPCP introduction are
established.

## Permanent nonclaims

PΩ2 establishes none of the following:

- a categorical inverse-limit universal property;
- equivalence with mathlib p-adic integers;
- a topological completion or p-adic field;
- generic completion or generic inverse-limit existence;
- construction of an all-depth family from a productive process;
- digit-stream equivalence;
- physical instantiation or foundation-independent actuality.

The completed-carrier status is therefore
`ESTABLISHED_RELATIVE_TO_LEDGER`, never absolute existence. Bounded shadows for
`p=2,3,5` are arithmetic QA only and do not construct the carrier.
