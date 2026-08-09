# R16 — Crest-Braid Derived Path Invariant
**Status:** finite full-path annotation; completion conjectural; novelty rejected
**Date:** 2026-08-04
**Primary API:** `src.core.observer.descent.chain`

## Role

Crest-Braid Calculus (CBC) is not a competing foundation. It is an ordered
full-path annotation derived from VODC. VODC can study any finite transformation;
CBC records which minimal admitted observers first distinguish consecutive
tacts of a path.

For doctrine \(O_X\) and states \(x,y\), define the minimal distinction crest:

\[
\operatorname{Cr}_{O_X}(x,y)=
\min_{\preceq}\{p\in O_X:(x,y)\in\Delta(p)\}.
\]

The minimum is an antichain and may contain several incomparable observers.
For a finite path \(\gamma=(x_0,\ldots,x_n)\):

\[
\boxed{
\operatorname{CB}_{O_X}(\gamma)=
\big(
\operatorname{Cr}_{O_X}(x_{i-1},x_i)
\big)_{i=1}^{n}.
}
\]

The endpoint receipt
\(\operatorname{Cr}_{O_X}(x_0,x_n)\) is stored separately. Hence CBC does not
collapse a closed path to its endpoint echo.

Because every stored tact includes its source and target, the tact sequence
reconstructs the original labelled path. Conversely the path and doctrine
deterministically produce every crest. Current finite CBC is therefore
information-equivalent to the full labelled sequential path, not a new path
invariant. Its sensitivity to tree-like insertion/sampling is currently a lack
of signature-style invariance, not positive non-reduction evidence.

## \(Z/4\) closed-breath witness

For the R16 diamond doctrine and path

\[
0\to1\to2\to3\to0,
\]

the ordered braid is

\[
(\{\mathrm{parity}\},
 \{\mathrm{parity},\mathrm{threshold}\},
 \{\mathrm{parity}\},
 \{\mathrm{parity},\mathrm{threshold}\}).
\]

The endpoint crest is empty because the endpoints echo exactly. The braid is
nonempty because path memory is not endpoint comparison.

This is an executable finite witness only. It does not yet define the
refinement/partition pro-limit proposed for continuous paths.

## Conjectures

### R16-C1 — Blocked-response chain

Receipted partial observers may admit an associative extension of descent and
the residual-chain balance. Status: **conjecture**. Ordered obstruction
propagation can break composition.

### R16-C2 — Cofinal completion

For separating nested finite doctrines and regulated paths, CBC atlases over
cofinal observer/partition schedules may have a schedule-independent
completion. Status: **conjecture**.

### R16-C3 — Common sensitivity exponent

A weighted crest-growth shadow may specialize to deterministic variation,
stochastic fluctuation, and program trace sensitivity. Status: **risky
conjecture**; observer weights may make the statement vacuous.

## Novelty-collision matrix

| VODC/CBC object | Closest known family | Required reduction test |
|---|---|---|
| greatest admitted descent | abstract interpretation / best correct approximation | exhibit a doctrine where VODC's residual-synergy law adds a nontrivial invariant or admit reduction |
| observer pullback | predicate transformers / Koopman pullback | distinguish observer-language closure from ordinary composition |
| distinction doctrine | partition lattice / bisimulation | compare exact quotient/minimization semantics |
| residual relation | approximation error / information loss | prove a theorem not obtained by relabeling set difference |
| synergy correction | nonfunctoriality defect / coreflection defect | locate categorical precedent or prove non-reduction |
| finite crest braid | trace semantics / symbolic dynamics | compare complete finite traces |
| refinement atlas | persistence / crossing trees | construct or refute schedule-independent completion |
| ordered path memory | signatures / rough paths / variation | find paths separated by one invariant but not the other under matched data |

No novelty claim survives merely because terminology is Veyra-native. At
least one new theorem, invariant, counterexample, or algorithmic advantage
must remain after these reductions.

## Falsification gates

Reject or sharply restrict the program if:

1. blocked observers make any reasonable composition nonassociative;
2. benign paths yield schedule-dependent completion;
3. equal complete CBC atlases fail a claimed prediction;
4. atlas size grows without compressible structure;
5. VODC is exactly an existing coreflection/interior construction and synergy
   is its standard defect;
6. CBC reduces completely to variation, persistence, bisimulation, trace
   semantics, or path signatures.

## Promotion decision and next research steps

The 2026-08-04 literature audit establishes reduction to full labelled trace
annotation and finds no matched-data non-reduction theorem. Novelty promotion
is rejected. Persistence comparison remains undefined without a filtration and
module; Mazurkiewicz comparison remains undefined without an independence
congruence. See [doc 146](../concepts/r16_literature_reduction.md).

1. Add a partial-response doctrine with explicit `ready/blocked` receipts.
2. State the categorical doctrine conditions for functorial descent.
3. Compare finite VODC against abstract-interpretation best correct
   approximation on the same examples.
4. Compare CBC against path signatures on finite words.
5. Attempt a non-reduction theorem before using the word “new”.

## Cross-links

- Primary calculus: [doc 141](../concepts/observer_descent_residual_calculus_r16.md)
- R11 typed observers: [doc 127](../concepts/native_observer_echo_core_r11.md)
- R14 observer synthesis: [doc 140](../concepts/observer_synthesis_v2_r14.md)
- Root theorem registry: [`../THEOREMS.md`](../../THEOREMS.md)
- Root notation catalog: [`../NOTATION.md`](../../NOTATION.md)
