# Mathematical Discovery Report: Veyra Core-0

## Problem framing

Build a new mathematical system from minimal primitives: number, point, segment, but without taking human versions of these as primitive.

Objects under study:

- rez: distinction act,
- nod: point-like residue,
- breath: segment-like transition,
- mode: number-like recurrence.

Progress criterion for this stage:

- explicit definitions,
- minimal axioms,
- human-shadow model for consistency,
- first arithmetic operations,
- proof/refutation agenda.

## Historical lens

Closest historical strata:

1. Tally/counting — but replace counted things with closed recurrences.
2. Euclidean geometry — rebuild point/segment from postulates.
3. Number theory — reinterpret divisibility and primality as resonance.
4. Non-Euclidean move — deny that points, equality, and length are primitive.

## Assumption ledger

| Assumption | Type | Why believed | If removed | Test |
|---|---|---|---|---|
| Distinctions can leave stable residues | axiom | needed for point analogue | no addressable structure | model with graph vertices |
| Transitions can be stitched | axiom | needed for segment arithmetic | no composition | path concatenation model |
| Closed transitions form modes | definition | needed for number analogue | arithmetic has no objects | closed path model |
| Echo-equivalence can replace equality | heuristic/definition | avoids premature identity | proofs become harder | compare test families |
| One-tact seed recovers natural numbers | axiom for Core-0 | sanity anchor | no basic number theory | one-loop model |

## Operators applied

### Null object

`0_V` is not a count of nothing. It is the silent closed breath.

### Axiom variation

Primitive equality is removed and replaced by echo-equivalence.

### Change medium

Number theory is moved from counting objects to resonance of closed processes.

### Notation compression

`nod`, `breath`, `mode`, `echo`, `resonance` are intentionally short words that make the non-human framing cheap to use.

## Candidate conjectures

### Weak conjecture W-001

In the one-nod one-tact shadow, Veyra modes with `⊕` and `⊗` reproduce ordinary natural-number arithmetic.

Status: likely theorem via word-length model.

### Sharp conjecture S-001

For any finite one-tact mode, resonance decomposition matches ordinary prime factorization.

Status: plausible theorem after definitions of `⊗`, resonance, and echo are fixed.

### Risky conjecture R-001

In richer multi-tact Veyra layers, physically stable structures correspond to modes with low obstruction under resonance decomposition, not merely to low energy in a metric geometry.

Status: speculative scientific heuristic, not theorem.

## Proof track

1. Formalize Core-0 as a rewriting system of breaths and modes.
2. Prove stitch associativity up to echo.
3. Prove `0_V` and `1_V` behave as additive/multiplicative units in the one-tact shadow.
4. Prove weak conjecture W-001 by mapping `τ^n ↦ n`.
5. Define resonance precisely enough to prove S-001.

## Refutation track

1. Search for ambiguity in echo-equivalence: can two modes have same tests but different decompositions?
2. Try multi-tact examples where order matters: `αβ` vs `βα`.
3. Test whether `⊗` is well-defined if echo-equivalent representatives are substituted.
4. Look for a mode that has two incompatible resonance decompositions under a natural test family.

## Next experiments

- Build a tiny Python enumerator for one-tact and two-tact modes.
- Define at least two test families: coarse length-test and ordered word-test.
- Compare prime-like modes under both families.
- Decide whether echo-equivalence is global or always indexed by a test family.

## Caveat

This is a seed, not a claimed replacement for mathematics. The value will be measured by the quality of definitions, models, counterexamples, and problems it unlocks.
