# Doctrinal Induction — DI-1 Candidate Rule

**Date:** 2026-08-27
**Status:** `INTERNAL_RESEARCH_CANDIDATE` rule with executable license
machinery and formally proved shadow laws. Not an adopted axiom.
**Implementation:** `src/core/doctrinal_induction.py`
**Certificate:** `doctrinal_induction_di1` in `src/core/certify.py`.
**Formal:** `proofs/lean/VeyraDoctrinalInduction.lean` (`THM_DI1_001`–`005`).

## The rule (candidate)

DI-1 is Veyra's first native quantifier mechanism. From

1. a **base witness** — the property validated at the first subject;
2. a **step schema** — a transformer that rewrites the *previous derivation*
   into the next one (never a recomputation; for the demo family it shifts
   every `DivisionStep` by one block and appends the final removal);
3. an **adopted generator** — the declared production basis, exactly the
   AFIP totality-basis obligation of doc 151 carried to the proof side;

it licenses a **ledger-relative all-depth proof family**: every finite depth
replays in exactly that many step applications, each receipt digest-chained
to its predecessor. DI-1 is AFIP's proof-side companion: AFIP introduces one
value family from an accepted basis; DI-1 introduces one *derivation* family
from the same kind of basis, and nothing more.

## Uniformity, natively

The classical side condition "the step does not depend on n" becomes an
executable echo criterion: the whole derivation is replayed at two fresh
anchors and the receipt digests must agree after anchor renaming — the proof
must be about the **form** of the recurrence, not its name. A step that
smuggles the anchor name into its evidence is rejected as `nonuniform-step`
(adversarial control shipped in the certificate). Shift-uniformity across
depths (a second, translation-flavored criterion) is a recorded **OPEN**
refinement, not implemented.

## Demo family: the first natively licensed general arithmetic law

`P(n)`: *the block `b` divides `b·n` exactly* — subjects grow by
`stitch(previous, b)`, evidence is a `StructuralDivisionProof` transformed
locally at each step, and the validator re-checks every produced derivation
independently: chain integrity of the `DivisionStep`s plus the fully native
`weave`/`stitch` reconstruction. The certificate licenses depths 1..12 for
blocks 3 and 5, and both adversarial controls behave: the name-peeking step
fails uniformity; a depth bomb blocks at exactly its depth with a typed
obstruction.

## What this buys N8

The `repeat`/divide lift inside cycle-divisibility becomes family-licensable
instead of per-instance. Collapsing the N8 Fermat cards into one native
theorem additionally requires an **orbit-partition rule (DI-2)** — grouping
arguments, not successor induction — which is recorded `OPEN`.

## Evidence levels (do not collapse)

| Item | Status |
|---|---|
| The DI-1 rule itself | `INTERNAL_RESEARCH_CANDIDATE` — adoption into the F1 axiom registry would be a separate, explicit registry act |
| License outcomes over exact bounded probes | `EXECUTABLE_EVIDENCE` |
| `THM_DI1_001`–`005` shadow laws | `FORMALLY_PROVED` (general statements over host `Nat`, real `induction` proofs) |
| Shift-uniformity; DI-2 orbit-partition rule | `OPEN` |

## Non-claims

1. **DI-1 is not classical induction.** Its classical shadow is pinned
   deliberately and in the open: `THM_DI1_001` exposes the host recursor as
   what a license *shadows to*. The license itself asserts only replayable
   depths under the doctrine; no completed carrier, no unconditional
   universal, no index totality. The P1-D2 finite-to-universal countermodels
   remain binding: without the adopted generator there is no family.
2. Generator adoption is a doctrine act (gap-audit non-claim 8 applies to
   any object reading of a licensed family).
3. Passing the certificate promotes nothing; `licensed` is not `proved` and
   appears nowhere in the registry status vocabulary.
4. Receipt digests are integrity bookkeeping (docs/06 §3 shadow license for
   the tuple bookkeeping in chain validation); acceptance always passes
   through the native reconstruction check.

## Verification

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q tests/test_doctrinal_induction.py
python scripts/check_lean_sources.py --jobs 8
```
