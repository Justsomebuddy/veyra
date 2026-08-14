# RFC: Same-Doctrine All-Status P1-A Transport

**Date:** 2026-08-14  
**Status:** accepted design implemented by the separate bounded sibling v2; no theorem  
**Depends on:** P1-A in [document 150](150_constructive_observer_doctrine_p1.md),
P1→R16 in [document 161](161_p1_r16_realization_contract.md), and restricted
context transport v1 in [document 167](167_realization_context_transport.md)

## 1. Decision

The implemented P1-A-aware realization transport is a new sibling contract. It
must not widen or reinterpret `p1-r16-context-morphism-v1`, mutate its receipt
schema, or add exports to the existing facade. The only admitted first scope is
one exact P1 doctrine and source binding, one freshly reconstructed `STRONG`
P1-A judgment and structural projection, two independently replayed
realization contexts, and a finite caller-declared state graph already accepted
by an exact v1 context-transport receipt. `INFORMATION_ONLY` and `INCOMPARABLE`
judgments are not admitted merely because sampled rows happen to commute.

"All-status" means that every admitted observer/state row commutes as the exact
R11 sum

```text
Observation = Ready(ResponseValue) | Blocked(tuple[ObserverObstruction, ...])
```

It never means that every P1-A projection is transportable. A candidate arrow
is rejected when its observation action cannot be reconstructed for every row.
No status-only, digest-only, ready-only, or exception-to-blocked cast is
admissible.

## 2. Why current P1-A is insufficient

Current `translate_response(...)` accepts only a defined `ResponseValue` and
projects a typed pair response. R11 `Blocked` retains complete ordered
obstruction paths but not the successful values of unaffected pair branches.
Consequently a fine pair can be blocked solely in a branch discarded by the
projection while the selected coarse observer is ready. The coarse ready value
cannot be recovered from the fine `Blocked` payload.

This is a concrete information obstruction, not a missing `elif`. Relabeling
that fine row as coarse `Blocked`, deleting the row, copying only its status, or
using the independently replayed coarse value as if it had been derived from
the fine payload would all make a false commuting square. V1 therefore remains
correctly P1-A-free.

## 3. Proposed sibling objects

The implementation follows the reserved names and versions below; the runtime
and evidence map are documented in
[document 170](170_p1a_all_status_transport_v2.md):

```text
P1AObservationTransportV2
P1AObservationCommutingRowV2
P1ARealizationTransportReceiptV2
veyra.p1-r16.p1a-observation-transport.v2
veyra.p1-r16.p1a-realization-transport-receipt.v2
```

The arrow must bind one shared exact doctrine fingerprint, the
`ObserverSourceBinding.membership_digest`, the complete freshly reconstructed
`STRONG` judgment under a new canonical judgment root, the validated
`ResponseTranslation.translation_digest`, both context/witness roots, the
state-graph root, the exact v1 context-transport receipt root,
totalization/cost/closure policies, and a fixed scope string.
Fine and coarse observer IDs and kinds come from the P1-A translation; they are
not caller aliases.

Each commuting row must retain, in canonical bytes rather than only digests:

- source and target state indices plus recurrence commitments;
- the full fine and coarse source-context `Ready|Blocked` payloads;
- the full fine and coarse target-context `Ready|Blocked` payloads;
- the independently reconstructed transported-fine payload at each endpoint;
- exact digests for all six retained payloads; and
- a fixed outcome-law classification.

The receipt must be freshly reconstructed from authoritative endpoint replay.
It cannot accept caller-supplied rows as evidence or splice v1 child receipts.

## 4. Exact observation action

For `Ready(value)`, apply the existing validated P1-A structural response
projection and wrap the exact result as `Ready`.

For `Blocked(obstructions)`, walk the declared pair-projection path over every
obstruction path in its original order:

1. keep only obstructions whose next structural path step selects the declared
   branch;
2. remove exactly that structural prefix;
3. repeat for every projection step; and
4. retain the exact obstruction code, remaining path, order, and multiplicity.

For an empty structural projection, identity preserves `Blocked` and its full
payload exactly. For a nonempty structural projection, the projected
obstruction tuple must be nonempty and pass the existing exact validator. An
empty tuple after prefix filtering is `UNDEFINED`, not `Ready`, because the
source blockage contains no value for the selected branch. The entire arrow is
rejected if any finite context row is undefined.

The transported outcome must then equal the independently replayed coarse
outcome in tag and complete canonical payload bytes. For a blocked row this
requires exact obstruction code/path/order/multiplicity equality; a matching
`blocked` tag or payload digest is not enough. Original source and target
blocked bytes remain in the receipt, so neither side is overwritten by the
projected intermediate.

## 5. Commuting square and finite admission

For every source state `x`, mapped target state `f(x)`, and admitted P1-A
translation `tau`, a sibling v2 arrow must reconstruct the complete square:

```text
O_source(fine, x)   == O_target(fine, f(x))
       | tau                    | tau
       v                        v
O_source(coarse, x) == O_target(coarse, f(x))
```

Both horizontal equalities, including complete payload bytes, come from fresh
verification of the bound v1 context-transport receipt. Both vertical outcomes
are independently reconstructed by `tau_observation` and must equal the fresh
coarse replay at their own endpoint. The state edge separately satisfies v1's
exact canonical recurrence-byte equality. All four observations are fresh R11
evaluations under the same exact doctrine/source binding. A diagonal-only
fine-source/coarse-target equality is insufficient. Finite success licenses
only this captured square; it is not a universal observer naturality theorem.

Admission requires all rows. One undefined, missing, duplicated, malformed,
spliced, status-changing, payload-changing, or recurrence-mismatched row is a
terminal rejection with no partial receipt.

## 6. Closure and cost interaction

Let `Pi_fine_source`, `Pi_fine_target`, `Pi_coarse_source`, and
`Pi_coarse_target` be the four exact payload partitions. The bound v1 receipt
must establish the two independent horizontal laws:

```text
Pi_fine_source   = f*(Pi_fine_target)
Pi_coarse_source = f*(Pi_coarse_target).
```

At each endpoint, the transported-fine partition equals the corresponding
coarse partition. The raw fine partition generally only **refines** that
coarser partition; a lossy P1-A projection does not make them equal. The sibling
receipt reconstructs the vertical class map and refinement rather than
infer either from observer IDs or digests.

The first sibling-v2 contract adds no vertical closure or cost law. V1 bottom,
join, and nonincreasing/exact-cost checks remain independently scoped to its
horizontal state reindexing receipt. No P1-A cross-observer cost comparison
follows. Such a law requires a separate explicit cost premise, policy, DTO,
counterexample pressure, and review. Endpoint-local names, response-class
ordinals, representative indices, and generator IDs are not transported.

## 7. Identity and composition obligations

Identity must preserve every full `Ready` and `Blocked` payload byte-for-byte.
Composition must compose structural projection paths and state graphs, then
replay the direct endpoints and rebuild a fresh receipt. It must not compose by
trusting child payload rows.

Before any category, functor, or naturality wording, tests must establish on
the admitted finite scope:

```text
id_observation(outcome) = outcome
(sigma ∘ tau)_observation(outcome)
  = sigma_observation(tau_observation(outcome))
```

Both equalities include exact blocked obstruction payloads at both contexts.
The bound v1 receipt separately retains its existing state-graph composition
and `(g ∘ f)* = f* ∘ g*` law; that horizontal fact is not a vertical P1-A
closure or cost law. Executable finite laws still do not establish an
interface-level category or theorem.

## 8. Validation, resources, and logging

Each endpoint witness retains its current independent limits: at most 256
realization inputs, 8 source observers, 2,048 evaluation rows, 262,144 bytes per
canonical observation payload, and 8 MiB aggregate evaluation payload. The
bound v1 receipt separately retains its 131,072-node and 16 MiB precharge.

For one P1-A translation the sibling table has at most 256 rows. Its six
retained payload streams are charged separately and together before receipt
construction: every stream remains within the existing per-payload limit, the
two raw fine/coarse streams at each endpoint remain within that endpoint's
8 MiB aggregate, each endpoint's transported stream receives a separate 8 MiB
cap, and the six-stream sibling aggregate is capped at 32 MiB. Existing
128-byte P1-A
identifiers, projection length 128, 2,048-obstruction count, and 128-step
obstruction-path bounds remain authoritative. The implementation charges the
shallow sibling DTO graph and decoded payload graph together under one frozen
65,536-node ceiling, and charges every sibling UTF-8 scalar except separately
bounded canonical payload bytes under a 1 MiB nonpayload-text ceiling. Document
170 records the executable boundary and focused tests.

Decoders must reject subclasses, unknown enum members, noncanonical bytes,
duplicate keys/rows, overdeep values, stale roots, wrong endpoints, and trailing
data. Validation errors use fixed bounded reason codes. Logs may contain fixed
codes, counts, indices, and short digest prefixes, but never recurrence values,
response values, obstruction paths, complete payload bytes, or full digests.
Public sibling calls must transiently reduce reachable value-bearing
lower-layer records to fixed routing metadata for the duration of that
thread-local replay boundary. The redactor must precede pre-existing target
logger filters and restore their exact order at exit, without replacing the
process record factory.

## 9. Required implementation pressure

The implementation remains NO-GO unless its normal and hostile coverage retains:

- ready→ready identity, left/right and nested projections;
- blocked→blocked projection with exact path-prefix removal and stable order;
- discarded-branch-only blockage producing `UNDEFINED` and rejecting the arrow;
- mixed relevant/irrelevant obstructions without loss of relevant
  obstructions, duplication, or reorder;
- fine-ready/coarse-blocked and projected-blocked/coarse-ready mismatch;
- exact same-doctrine, source-binding, observer-kind, recurrence, endpoint and
  policy binding;
- translation, binding, context, witness, morphism and receipt-root
  anti-splicing plus fresh authoritative replay;
- identity/composition equality over full ready and blocked payloads;
- both horizontal v1 partition pullbacks, both vertical class maps, and raw-fine
  refinement of transported/coarse partitions without a vertical cost claim;
- row, projection, payload, aggregate, depth, text and integer limit edges; and
- unchanged v1 DTO bytes, digest pins, facade exports and behavior.

Stop and redesign if totality requires inventing a coarse ready value, if
blocked path projection is not compositional, if authoritative replay cannot
distinguish derivation from lookup, if v1 bytes would change, or if a claim
requires a vertical P1-A cost law without a new premise or cross-doctrine
conversion.

## 10. Explicit nonclaims

The RFC itself added no runtime. The later sibling implementation adds only its
separate DTO/runtime/package surface; it adds no root export, certificate,
theorem, status promotion, observer admission, R16 canonicality, category,
functor, natural transformation,
covariant pushforward, exact-cost theorem, chronology, authentication, custody,
confidentiality, or performance claim.

It also creates no cast or implication into P1-E1/P1-E4 observer role, Genesis,
Actualization, Consciousness, history, birth, token, efficacy, or promotion
status. A commuting observer square is not formation or lifecycle evidence.

Cross-doctrine transport remains NO-GO. It would require a separately specified
doctrine morphism, total recurrence and observation conversion, obstruction
semantics, policy/cost laws, composable trust roots, and authoritative witness
transport. Equality of fingerprints, source membership, finite commuting rows,
or P1-A projection paths cannot supply those objects.

## 11. Review outcome

The accepted order is:

1. retain realization-context transport v1 unchanged;
2. publish this same-doctrine all-status RFC;
3. implement the separate versioned sibling only after the obstruction action,
   total finite admission, resources, and hostile matrix are reviewed
   ([completed boundary](170_p1a_all_status_transport_v2.md)); and
4. keep cross-doctrine transport blocked unless a distinct RFC discharges its
   stronger obligations.
