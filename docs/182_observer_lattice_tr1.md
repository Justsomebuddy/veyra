# Observer Lattice — TR-1 Candidate Instrumentation

**Date:** 2026-08-27
**Status:** `INTERNAL_RESEARCH_CANDIDATE` instrumentation with executable
rows and a formally proved transfer spine. Not a theory yet: TR-2 (licensed
transfer laws with Ω calculi) is `OPEN`.
**Implementation:** `src/core/observer_lattice.py`
**Certificate:** `observer_lattice_tr1` in `src/core/certify.py`.
**Formal:** `proofs/lean/VeyraObserverLattice.lean` (`THM_TR1_001`–`004`).

## The arena

A **commutation doctrine** declares which unordered letter pairs may swap
when adjacent. Doctrines form a refinement lattice between the ordered word
observer (no pairs; classes are singletons) and the bag observer (all
pairs; classes are permutation sets). Classical mathematics owns individual
nodes — free monoids, trace monoids (Cartier–Foata, Mazurkiewicz),
commutative monoids — and that theory is credited, not claimed. What TR-1
registers is the **instrumentation of arithmetic truth as an object on the
lattice**: how a property moves along refinement edges and what witnesses
its breaks.

## What is executable now

- **Node identity** is the whole trace class — the swap-reachability echo
  object, enumerated exactly; exceeding the declared cap yields a typed
  `class-size-refusal`, never a silent truncation. A closure validator
  re-checks any claimed class independently. The Cartier–Foata layer form
  is computed as a display receipt (layer sets canonical; intra-layer print
  order is a docs/06 §3 shadow); no decision consults it.
- **Node primitivity**: a word is imprimitive at a node iff its class
  contains a literal power, detected through the cut-free `primitive_root`
  of members — decisions run over the class object, never a canonical cut.
- **Edge transfer rows**: refinement is checked with extra-pair witnesses;
  class containment is verified natively; a break carries the concrete
  **Ω exhibit** `v = u^k`, verified to live in the coarse class and outside
  the fine one.
- **Fragility spectrum**: per-node rows plus the exact first-break edge.
  Flagship cell: `aabbcc` along `∅ ⊂ {ab} ⊂ {ab,ac} ⊂ {ab,ac,bc}` stays
  primitive through three nodes and breaks exactly on the `bc` edge with
  exhibit `abcabc = (abc)²` — the first executable jump table of an
  arithmetic invariant across observer doctrines.

## The formal spine

`THM_TR1_001_reaches_monotone` proves by real induction that enlarging the
step relation preserves every reachability witness; `THM_TR1_002` transports
a power exhibit upward (imprimitivity moves to coarser nodes);
`THM_TR1_003` is the contrapositive — **coarse-primitive implies
fine-primitive** — the monotonicity every executable row exhibits;
`THM_TR1_004` is a concrete replay fixture. These are abstract shadow laws
over an inductive closure, deliberately free of any word encoding.

## Evidence levels (do not collapse)

| Item | Status |
|---|---|
| Lattice/echo/transfer instrumentation | `INTERNAL_RESEARCH_CANDIDATE` |
| Spectrum and transfer rows over exact bounded words/doctrines | `EXECUTABLE_EVIDENCE` |
| `THM_TR1_001`–`004` | `FORMALLY_PROVED` (abstract closure laws over host types) |
| TR-2: licensed transfer theorems, Ω calculus, Möbius-flow along the lattice | `OPEN` |

## Non-claims

1. Trace monoids and their combinatorics are classical; nothing about
   individual nodes is claimed as new.
2. No general transfer theorem is asserted: rows are exact bounded
   evidence; the Lean spine covers only the abstract monotone direction.
3. Class enumeration, caps, and counters are shadow bookkeeping; identity
   and membership run on the echo objects.
4. No promotion; statuses are `witnessed`/`blocked`/`refused`; a refusal is
   a resource boundary, not evidence of absence (silence-status map).

## Verification

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q tests/test_observer_lattice.py
python scripts/check_lean_sources.py --jobs 8
```
