# G4 finite observer-patch atlas

**Status:** bounded executable/formal slice

**Scope:** finite nod universes and finite patch partitions only

**Implementation:** `src/core/observer_patch_atlas.py`

**Classification:** `src/core/observer_patch_gluing_classification.py`

**Lean:** `proofs/lean/VeyraObserverPatchAtlas.lean`

## Purpose

G4 asks when local observer distinctions can be represented by one exact global
echo relation.  This card deliberately uses finite patches and partitions.  It
does **not** assert a manifold, sheaf, physical field, general topology result,
or R8 theorem promotion.

## Finite data

An `ObserverPatchAtlas` has a finite universe `U` and named patches covering
`U`.  A `LocalObserverSection` is a partition of one patch.  Two nods echo
locally exactly when they belong to the same block of that partition.

For local relations `E_i`, define

```text
E* = equivalence-closure(⋃ E_i).
```

The implementation computes `E*` by finite connected-component closure.  It
then reports a local contradiction whenever

```text
x,y ∈ patch i,  x E* y,  but not x E_i y.
```

## Exact gluing criterion

An exact global gluing is an equivalence relation `G` on `U` whose restriction
to every patch is exactly `E_i`, rather than merely containing it.

**Finite criterion.** Such a `G` exists if and only if the local contradiction
set is empty.

- Necessity: every `G` contains every local equality, so equivalence closure
  gives `E* ⊆ G`.  If `E*` equates two nods in a patch, exact restriction forces
  that patch to equate them too.
- Sufficiency: when there is no local contradiction, use `G = E*`.  Each local
  relation is contained in `E*` by construction, and the no-contradiction
  condition supplies the reverse inclusion on each patch.

`THM_G4_001_exact_gluing_exists_iff_no_local_contradiction` proves this
existence equivalence from the equivalence, containment, and least-closure
properties of `E*`.  The executable `exact_gluing_relation()` returns the
constructive `E*` witness or `None`.

## Why pairwise overlap checks are insufficient

The counterexample uses three patches:

| Patch | Nods | Local blocks |
|---|---|---|
| `AB` | `a,b` | `{a,b}` |
| `BC` | `b,c` | `{b,c}` |
| `CA` | `c,a` | `{c}`, `{a}` |

Every pairwise overlap is a singleton (`{b}`, `{c}`, or `{a}`), so the
restricted relations agree automatically.  Nevertheless `AB` and `BC`
generate `a E* c`, while `CA` distinguishes `a` from `c`.  Thus pairwise rows
all pass and exact global gluing fails.

- `THM_G4_002_triangle_singleton_overlaps_pass` proves the three pairwise
  compatibility statements.
- `THM_G4_003_triangle_exact_gluing_impossible` proves that no transitive global
  relation can have all three exact restrictions.

## EqRel bridge and uniqueness classification

On one declared finite cover, G4 exact-gluing existence is exactly the
matching-family amalgamation question for the set-valued presheaf
`V ↦ EqRel(V)`. This is an existence/effectivity reduction, not a general sheaf,
descent, topology, or stack implementation.

Conditional on existence, set `Q=U/E*` and join two quotient classes when one
patch meets both. Exact gluings are in bijection with conflict-independent
partitions of `Q`; uniqueness holds exactly when the conflict graph is complete.
The executable classifier also brute-forces every global partition within its
eight-node bound and rejects any disagreement with the constructed bijection.

Disjoint singleton patches show that existence does not imply uniqueness: both
identity and universal relations restrict exactly. The pair-coverage uniqueness
condition and this nonuniqueness witness are digest-bound Lean helpers, not new
registered `THM_G4_*` cards. See
[`162_comparative_bridge_separation_ledger.md`](162_comparative_bridge_separation_ledger.md).

## Verification boundary

Focused tests cover constructive gluing, exact restrictions, overlap mismatch,
invalid direct-constructor shapes, missing sections, and the three-patch
obstruction. Certificate `observer_patch_atlas_g4` binds the entire Lean file to
SHA-256 `6e0b011f…f07038c`, rejects mismatch before Lean, compiles only exact
captured bytes with the pinned `leanprover/lean4:v4.30.0-rc2` toolchain, and
rereads continuity afterward. It checks three registered theorems plus two
nonpromoted helpers. The historical 76/75 counts in this G4 release slice remain
historical; the current whole-project suite is documented separately.

## Related material

- [Observer-gap topology theorem](143_observer_gap_topology_theorem.md)
- [R16 observer descent residual calculus](141_observer_descent_residual_calculus_r16.md)
