# Arithmetic as a variable object over the observer site

Status: 14 `FORMALLY_PROVED` Lean cards (`proofs/lean/VeyraVariableArithmetic.lean`,
Mathlib-free, axioms `propext`/`Quot.sound` only, no classical choice) with an
`EXECUTABLE_EVIDENCE` twin (`src/core/observer_arithmetic.py`, certificate
`observer_arithmetic_va`). Not `PUBLICLY_VALIDATED`. Step 2 of the program
opened in `docs/190`; nothing here concerns the AX-007 `Mode`, W-001, or
physical observers.

## 1. The claim

`docs/02` says that a number is the shadow of a mode, addition is stitching,
multiplication is weaving and divisibility is resonance. `docs/190` made
equality stage-relative. This document makes the *operations* stage-relative:
they live on the fibres of the presheaf of modes and exist at a stage exactly
when echo at that stage is a congruence for them. Four consequences follow,
each a theorem:

1. the natural numbers are literally the fibre of the presheaf at the length
   stage, with stitch as `+` and weave as `×`;
2. the laws of arithmetic (commutativity, left distributivity) are properties
   of stages, not of the operations;
3. closed modes have no native stitch (stitch does not respect cyclic echo)
   while they can be woven;
4. AX-005 (echo associativity, `docs/01`) is a theorem for open stitching and
   is false for stitching closed modes through their canonical cuts.

## 2. Definitions

- **DEF-765 — Fibre and restriction.** `Fibre T := Quot (Echo T)`, the
  presentations up to echo at stage `T`; for `T ⊆ T'` the restriction
  `Fibre T' → Fibre T` coarsens classes (well defined by `THM_OS_002`).
- **DEF-766 — Descent.** An operation *descends* to `T` when echo at `T` is a
  congruence for it, one argument at a time; it then acts on `Fibre T`.
- **DEF-767 — Stitch, weave, cyclic echo, canonical cut.** On words
  `stitch x y := x ++ y` (`docs/02` §2) and `weave x y := y^{|x|}` (every tact
  of `x` replaced by a copy of `y`, `docs/02` §3); `Cyc x y` iff `y` is a
  rotation of `x`; `minRot` is the lexicographically least rotation and
  `cutStitch x y := minRot x ++ minRot y`.
- **DEF-768 — Resonance at a stage.** `ResonatesAt T u x` iff `x` is echoed
  at `T` to some power `u^k` (`docs/02` §4 relativized).

## 3. Theorem cards

| Card | Statement |
|---|---|
| `THM_VA_001_restriction_homomorphism` | for `T ⊆ T'` and an operation descending to both, restriction commutes with the action. |
| `THM_VA_002_descends_length_word` | stitch and weave descend to `{length}` and to `{word}`. |
| `THM_VA_003_nat_is_length_fibre` | `toNat`/`ofNat` are inverse between the length fibre and `ℕ`; stitch is `+`, weave is `×`. |
| `THM_VA_004_descends_bag` | stitch and weave descend to the bag (Parikh) stage. |
| `THM_VA_005_stitch_breaks_cyclic` | `ab ~ ba` cyclically but `abab` and `baab` are not (finite countermodel). |
| `THM_VA_006_weave_respects_cyclic` | `Cyc y y'` implies `Cyc (y^k) (y'^k)`. |
| `THM_VA_007_stitch_comm_stage` | stitch commutes at the bag stage; not at the word stage. |
| `THM_VA_008_weave_comm_stage` | weave commutes at the length stage; not at the bag stage. |
| `THM_VA_009_distributivity_stage` | right distributivity is a literal identity; left distributivity holds at the bag stage and fails at the word stage. |
| `THM_VA_010_open_associativity` | open stitch and weave are literally associative. |
| `THM_VA_011_canonical_cut_not_associative` | `(a ⊙ b) ⊙ ab` and `a ⊙ (b ⊙ ab)` through canonical cuts are not cyclically echoed (finite countermodel). |
| `THM_VA_012_bag_prime_iff_coprime` | bag-stage primitivity is coprimality of the letter counts. |
| `THM_VA_013_resonance_retracts` | resonance at a finer stage implies resonance at a coarser one. |
| `THM_VA_014_length_resonance_is_divisibility` | at the length stage resonance is divisibility of lengths. |

Cards 005 and 011 are finite countermodels checked by `decide`; 007–009 pair
a general law with a `decide` countermodel.

## 4. Reading

**One addition, seen at many stages.** With 001 the fibres and their partial
operations form a presheaf of partial algebras over the stage lattice. There
is not a "true" addition of which the others are approximations: the class of
`ab ++ a` at the bag stage *is* the sum of the classes of `ab` and `a` there,
and coarsening it to the length stage gives `2 + 1`.

**The natural numbers are a stage.** 003 is the exact form of `docs/02` §1:
a natural number is a class of modes under the length observer, stitching
classes adds and weaving multiplies. The resonance arithmetic of `docs/189`
is the arithmetic of this fibre, and the Parikh vectors of the bag stage are
its commutative shadow one stage finer.

**Laws are stage properties.** Executable table on the four `docs/06` stages
(words up to length 3; the Lean cards give the general statements and
countermodels):

| Law | `{length}` | `{bag}` | `{cycle}` | `{word}` |
|---|---|---|---|---|
| stitch descends | yes | yes | no | yes |
| weave descends | yes | yes | yes | yes |
| stitch commutative | yes | yes | yes* | no |
| weave commutative | yes | no | no | no |
| weave left-distributes over stitch | yes | yes | no | no |
| right distributivity, associativity | literal identities at every stage | | | |

`*` `x ++ y` and `y ++ x` are conjugate words, hence cyclic rotations of
each other; the relation holds although the operation does not descend there.
Commutativity of addition is therefore a bag-stage law that the word stage
retracts; commutativity of multiplication survives only at the length stage.

**Closed modes have no native stitch.** 005 says cyclic echo is not a
congruence for concatenation: to stitch two closed modes one must cut them
open, and the result depends on the cuts. Weaving needs no cut (006). This is
the same phenomenon as the anchor-relative zero of `docs/02` §1: a closed
breath must be opened at a nod before it can be stitched.

**AX-005 demoted.** `docs/01` states echo associativity as a seed axiom. For
open breaths it is a literal identity (010), so it holds at every stage. For
closed modes stitched through a single-valued choice of cut it is false: the
lexicographically least cut gives `(a ⊙ b) ⊙ ab = abab` and
`a ⊙ (b ⊙ ab) = aabb`, which are not cyclically echoed (011). Associativity is
thus a property of open stitching, not of modes, and the 2026-08-27 audit
finding on the `min(rotations)` canonical cut now has a theorem behind it. The
multi-valued stitch (all cuts at once, compared as sets of cycles) is expected
to be associative and is left `OPEN`.

**An arithmetic invariant at an intermediate stage.** Primitivity at the bag
stage is coprimality of the letter counts (012): `baab` has counts `(2, 2)`
and is bag-composite, `aba` has `(2, 1)` and is bag-primitive. Along the
stages, primitivity reads: unit tact at `{length}` (`THM_OS_016`), coprime
counts at `{bag}`, primitive word at `{cycle}` and `{word}` (`THM_OS_015`).

**Resonance is contravariant.** Finer stages see fewer resonances (013); at
the length stage resonance is divisibility (014), which is `THM_RA_005` read
on the length fibre.

## 5. Executable counterpart

`src/core/observer_arithmetic.py`: `stitch`/`weave`; `descends` (congruence
check over all echo pairs of a family, with witnesses); `fibre_action` and
`restriction_commutes` (001); `nat_shadow` (003); `law_table` and
`literal_laws_hold` (007–010) with first witnesses; `cyclic_echo`,
`canonical_cut`, `cut_stitch`, `canonical_cut_associativity_failures` (011),
`weave_respects_cycle_violations` (006); `bag_vector`,
`parikh_shadow_primitive` (declared host-`gcd` shadow) and
`bag_primitivity_agreement` against the native `primitive_at((BAG,), …)`
(012); `resonates_at` and `length_divides` (013/014).
`observer_arithmetic_checklist()` maps the 14 cards to their replay.
Certificate `observer_arithmetic_va` (suite 113) pins the law table, the
cycle countermodel, four restriction squares, the length fibre `0..3`, the
Parikh agreement on 126 words, the AX-005 countermodel and the resonance rows.

## 6. Claims and non-claims

- Claimed: the 14 cards as stated on host lists (binary words for the bag
  and cyclic stages); the executable replay on bounded families.
- Not claimed: anything about the AX-007 `Mode`, W-001/THM-001–003, the
  native `Recurrence` of `docs/189` beyond the length-fibre reading, physical
  observers, or a topos-theoretic structure; not `PUBLICLY_VALIDATED`.
- Open: associativity of the multi-valued (all-cuts) stitch of closed modes;
  descent criteria for arbitrary observers (which observers make which
  operations descend); the fibres of the doctrine lattices of `docs/179`–`184`.

## 7. Verification

```bash
python scripts/check_lean_sources.py --jobs 8        # 59/59
python scripts/check_research_lean.py               # 68/68
python -m pytest -q tests/test_observer_arithmetic.py tests/test_certify.py
```
