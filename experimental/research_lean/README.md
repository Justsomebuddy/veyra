# Research Lean candidate

Status: **`INTERNAL_RESEARCH_CANDIDATE`**. This directory is deliberately
outside the 53-source stable Lean inventory and is not part of `make verify`.

The canonical `manifest.json` binds ten research sources, their imports and
SHA-256 digests, 87 declarations (41 headline declarations and 46 helpers), the
41 literal headline signatures and claim boundaries, and the exact axiom
closure printed by Lean. Ordered domain-separated source and proof roots make
the aggregate review identity explicit. The reviewed toolchain is
`leanprover/lean4:v4.30.0-rc2`, Lean `4.30.0-rc2`, commit
`3dc1a088b6d2d8eafe25a7cd7ec7b58d731bd7cc`.

| Source | Declarations | Scope |
|---|---:|---|
| `VeyraResearchBinomSum.lean` | 13 | classical finite binomial-sum identities |
| `VeyraResearchCards.lean` | 11 | fixed arithmetic/counting cards |
| `VeyraResearchFermat.lean` | 5 | classical `Nat` Fermat support |
| `VeyraResearchFermatCorollary.lean` | 4 | classical `Nat` corollaries |
| `VeyraResearchGcd.lean` | 9 | classical `Nat` gcd support |
| `VeyraResearchPrimes.lean` | 6 | classical local `Veyra.Prime` results |
| `VeyraResearchPythagorean.lean` | 6 | classical integer identities |
| `VeyraResearchShadow.lean` | 11 | unary `Recurrence` pulse/silence image only |
| `VeyraResearchOneTactBridge.lean` | 21 | singleton-tact path-word / Nat / unary `Recurrence` / exact R9-image bridge |
| `VeyraResearchNativeNumberBridge.lean` | 1 | ready native Mode tact-count carrier into stable `THM-F002` product-plus-one law |

The source scanner rejects project-local `sorry`, `admit`, `axiom`,
`postulate`, `constant`, `opaque`, `unsafe`, `extern`, `implemented_by`, and
`sorryAx` code tokens. That is not an “axiom-free” claim: the frozen report has
26 empty closure rows and 61 rows depending on subsets of `propext`,
`Classical.choice`, and `Quot.sound`.

The candidate lane also rejects command-level declaration metaprogramming
(`run_tac`, custom syntax/elaborators/macros, and `Lean.addDecl`) so an unused
injected axiom cannot sit outside the exact 87-row audit.

Run `make research-lean` for a fresh isolated verification. The checker copies
the exact 53 stable and ten research sources into a temporary tree, compiles
a new `.olean` graph, generates all 87 `#check` and `#print axioms` commands,
and rehashes the originals after execution. It has no persistent cache.

## Evidence and trust boundary

`source_roots.base` and `source_roots.research` hash the ordered
`path + NUL + SHA-256` rows under separate length-delimited domains.
`proof_root` then binds those roots, the exact toolchain identity, all 41
literal claim/scope/registry rows, and all 87 ordered axiom closures. The root
does not hash itself or claim binary reproducibility.

The rebased candidate manifest binds the current 53-source stable inventory
and ten research sources at base root
`01cd6bff50b4bd86f2937e902ada183add2dcda496593ec62145384d7cc47ed2`,
research root
`28c8e91bc8b3158fa377624dfb8b19970289f7f59eba1f2dbfec0f0c71cb75ce`,
and proof root
`f4bfdd130b8abcc21e31a04e5eef0c994e2deabeb90f236303e207cda4e746ad`.
The complete manifest SHA-256 is
`5fc650436b788a6f46a37ff37fbfecf924d82559b38c84429dcb474c98f83f62`.

The trusted computing base remains the selected Lean compiler/kernel and its
reported primitive axioms, local Elan or hosted archive delivery, the Python
checker and host operating system, plus human review of the claim ledger. Exact compiler
version and commit checking is identity evidence, not a bit-for-bit runtime
attestation. Hosted CI verifies its exact clean checkout SHA before and after
replay (a synthetic merge SHA on `pull_request`, not necessarily the public PR
head); integration must separately match the public head. A repository
revision is deliberately not embedded in the same commit it names.

## Nonclaims

- The shadow file covers only the unary `Recurrence` pulse/silence image. It
  does not establish AX-007, LEM-001, a general Mode bridge, or THM-001–003.
- The one-tact bridge covers only the explicitly singleton-generated path-word
  realization. It does not prove that AX-007 excludes additional tacts, does not
  establish general LEM-001, does not identify arbitrary strict modes with `Nat`,
  and does not promote THM-001–003 or W-001.
- The native-number bridge is limited to ready-mode tact-count observation and the already-proved `THM-F002` congruence on that same count. It does not establish prime infinitude, Fermat, a third theorem-derived layer, or any R8 promotion.
- Prime, gcd, and Fermat declarations are classical local `Nat` results, not a
  Veyra resonance-prime theory, native repair, or factorization foundation.
- Counting identities are not event-theoretic or general probability results.
- Integer Pythagorean identities do not promote the stable fixed natural card.
- These declarations have no stable theorem IDs, certificates, package runtime
  surface, public validation, registry promotion, or mathlib equivalence claim.
