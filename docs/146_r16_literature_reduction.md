# R16.6 — Literature reduction and no-promotion decision

**Status:** checked finite reduction; novelty promotion rejected  
**Date:** 2026-08-04  
**Executable API:** `src.core.observer_descent_reduction`

## Decision

The R16 promotion gate is resolved negatively. On the current finite carrier:

- descent is a best admitted lower approximation whenever its unique greatest
  candidate exists;
- residual is ordinary under-approximation precision loss;
- the field named `synergy` is a direct-versus-staged composition precision
  gap;
- the residual-chain balance is finite nested-set algebra;
- crest braid is a deterministic annotation of—and reconstructs—the full
  labelled path.

These facts support an implementation and explanatory vocabulary, but not a
novel calculus or new invariant claim.

## Executable audit

`z4_reduction_audit()` independently reconstructs the best admitted lower
approximation and compares it with every existing `Z/4` descent:

| Check | Result |
|---|---:|
| shift/target descents | `16/16` exact |
| composition rows | `64/64` balanced precision gaps |
| promotion status | `reduced-no-novelty-promotion` |

The existing R16 certificate requires those reduction counts, the negative
promotion status, and rejection of an exact-total target that is not a
canonical member of its declared target doctrine. Reduction calls supply that
doctrine explicitly through the required keyword-only `target_doctrine`
boundary.

## Totality correction

The earlier prose inferred total descent from finite bottom plus unique
internal admitted joins. That inference is false: an admitted internal join
can overshoot a raw pullback admitted by a separate valid target doctrine. A
checked five-state source diamond and two-element target doctrine leave two
incomparable maximal lower candidates and raise `descent-not-unique` while the
target still satisfies `q in O_Y`.

Current descent is therefore partial and fail-closed. Totality requires an
additional ambient-closure/right-adjoint hypothesis. The Lean partition spine
remains a conditional set theorem; it does not prove Python doctrine totality.

## CBC reduction

For a fixed doctrine, each crest is a deterministic function of one adjacent
state pair. Each stored tact contains that pair. Hence:

```text
full labelled path + doctrine  <->  current tact sequence with crests
```

Current CBC is sensitive to tree-like backtracking and sampling. This is not a
separation from full signatures on matched quotient data; it is a missing
invariance. Persistence and concurrency-quotiented trace comparisons remain
undefined until their required structures are supplied.

## Claim boundary

Established: finite reduction, exact bounded audit, partiality counterexample,
full-path reconstruction, and a no-promotion decision.

Not established: novelty, universal observer calculus, bisimulation algorithm,
path-signature non-reduction, persistence comparison, computational advantage,
or R8 theorem-derived promotion.
