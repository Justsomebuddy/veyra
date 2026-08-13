# Realization Transport Module

## Purpose

This additive module implements the first bounded answer to issue #33: an exact
same-P1-doctrine state reindexing between two independently replayed
`RealizationContext` endpoints.  A total graph `f : X_source -> X_target` must
preserve canonical recurrence inputs.  Realized R16 closure partitions then act
contravariantly by normalized pullback along `f`.

## Contract

- Both endpoint `ObserverRealizationWitness` values are authoritatively rebuilt
  through `verify_observer_realization_r16`; a digest match is never sufficient.
- Policies and the ordered source-cost vector must match exactly.
- Full structured `Ready`/`Blocked` payload bytes commute for every observer and
  mapped state.
- Every pulled-back target partition must be admitted by the source closure.
- Bottom and every pairwise join are reconstructed and checked.
- Source minimum cost may decrease after pullback but may never increase.
- Identity and composition rebuild fresh receipts; they are executable bounded
  evidence, not a formal category/functor theorem.

## Nonclaims

No cross-doctrine transport, P1-A response translation, covariant pushforward,
naturality, canonical quotient representatives, authentication, theorem, or
promotion is claimed.  Names, ordinals, generator IDs and representative indices
are endpoint-local and are not transported.

## Files

- `types.py`: immutable exact DTOs.
- `digest.py`: injective domain-separated receipt encodings.
- `validation.py`: exact-type/resource/integrity snapshots.
- `runtime.py`: endpoint replay, construction, verification and composition.
- `public.py`: narrow callable API and scope boundary.

## Version

Internal research contract v1 (`p1-r16-context-morphism-v1`).
