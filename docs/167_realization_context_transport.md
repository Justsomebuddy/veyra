# Restricted Realization-Context Transport

**Date:** 2026-08-13  
**Status:** bounded executable research contract; abstract Lean laws; no theorem promotion  
**Version/schema:** `p1-r16-context-morphism-v1`,
`veyra.p1-r16.realization-transport-receipt.v1`  
**Origin:** architecture question reported in issue #33

## 1. Decision and direction

The P1→R16 realization in [document 161](161_p1_r16_realization_contract.md)
remains relative to one exact `RealizationContext`.  This additive contract
does not invent transport from matching digests or retrofit a canonical map
into P1.  It admits only a restricted **same-doctrine state reindexing**

```text
f : source state index → target state index
```

whose graph is total on the finite source carrier.  The map must commute with
the exact canonical recurrence input at every source index.  Both endpoint
realization witnesses are independently and authoritatively replayed before
any transport row is accepted.

The induced action on extensional observation partitions has the opposite
direction:

```text
target R16 closure --f*--> source R16 closure
```

For a target partition `q`, `f*(q)` is its normalized inverse-image partition
along the state graph.  Thus the implemented operation is contravariant.  A
covariant pushforward would generally be absent or non-unique: a source
inclusion does not determine responses outside its image, while a state
collapse can identify states with incompatible responses.

## 2. Admitted arrows

`ContextMorphism` binds:

- a bounded human-readable morphism identifier;
- exact source and target context digests;
- exactly one target index for each source index;
- a version and domain-separated morphism digest.

Construction rejects partial and out-of-range graphs.  The endpoint contexts
must bind the same exact P1 doctrine fingerprint, ordered source-observer cost
vector, totalization policy, cost policy, and closure policy.  At each graph
row, the source and target recurrence inputs must have equal canonical bytes;
digest equality is not used as a substitute for this comparison.

Reordering, restriction to a source subcarrier, and duplication of target
states are representable when these conditions hold.  Arbitrary recurrence
conversion, policy conversion, or cross-doctrine observer translation is not.

## 3. Authoritative receipt reconstruction

`realization_context_morphism(...)` constructs one arrow receipt.
`verify_realization_transport(...)` does not trust supplied receipt rows.  It:

1. snapshots the doctrine and both contexts;
2. authoritatively replays both complete P1→R16 endpoint witnesses;
3. validates the total graph and exact endpoint bindings;
4. compares canonical recurrence bytes on every graph row;
5. reconstructs the full `Ready|Blocked` evaluation commuting table;
6. inverse-images every target closure partition and resolves it to one unique
   extensional source closure row;
7. checks bottom, binary join, and cost laws;
8. reconstructs every receipt field and requires exact equality.

Evaluation commutation compares the exact status and complete canonical
payload.  Equal status tags or equal digests alone are insufficient.  The
receipt retains bounded recurrence, evaluation, closure-action, and cost rows;
endpoint and receipt digests bind integrity but establish no authentication,
chronology, or trust.

The fixed scope string is intentionally narrower than a functor claim:

```text
finite-relative-replayed-single-arrow-no-category-or-functor-claim
```

## 4. Extensional closure and costs

The local ordered representatives, response-class ordinals, observer names,
and minimum-generator identifiers in a realization witness are not natural
data.  Transport therefore uses normalized extensional partitions and
recomputes the unique source closure index.  It does not copy local
representatives across contexts.

Inverse image preserves the indiscrete bottom and common refinement:

```text
f*(bottom) = bottom
f*(a join b) = f*(a) join f*(b)
```

Here `join` is R16's partition common refinement.  A target partition can
collapse onto a source partition that has a cheaper minimum generator set, so
the general admitted cost law is only

```text
source_cost(f*(q)) <= target_cost(q).
```

Each row is classified `NONINCREASING`; `EXACT` is recorded only when equality
was independently reconstructed.  Exact cost preservation is not a default
law and no cost-reflecting subcategory is claimed.

## 5. Identity and composition helpers

The API supplies deterministic identity and composition builders.  Composition
uses ordinary state-graph composition and then freshly reconstructs the
source-to-target receipt; it does not splice child receipt rows.  Focused tests
check graph identity/associativity and compare composed and direct closure rows
on finite examples of the contravariant action law

```text
(g ∘ f)* = f* ∘ g*.
```

These executable finite checks and the abstract Lean relation laws do not by
themselves define or certify a category-valued implementation, a functor, or a
natural transformation.  Such promotion would require a separately reviewed
interface-level theorem tying all admissible arrows, equality, composition,
receipts, and replay semantics together.

## 6. P1-A and cross-doctrine boundary

P1-A response translation is not used by this v1 contract.  It transforms
responses between observer identifiers only under one exact doctrine/source
binding; it does not supply a state graph, recurrence-input conversion,
cost/closure action, endpoint replay, or witness transport.  The separate v2
sibling now supplies only an all-status transformation preserving complete
structured `Ready|Blocked` payloads plus fresh finite identity/composition.

[RFC 169](169_p1a_all_status_transport_rfc.md) fixed that boundary and
[document 170](170_p1a_all_status_transport_v2.md) records its separate
implementation without changing v1: projection of `Blocked` retains exact obstruction
code/path/order/multiplicity, discarded-branch-only blockage is explicitly
undefined rather than fabricated as a coarse value, and a sibling v2 arrow is
admitted only when every finite row commutes against fresh coarse replay.

Cross-doctrine transport is likewise outside v1.  It would require an explicit
doctrine morphism, total and composable response transformation, recurrence
conversion, policy and cost laws, and an authoritative witness-transport rule.
No such data are inferred from a doctrine fingerprint, source binding, local
quotient section, or partial R16 descent.

## 7. Resource and trust boundary

All transport DTOs are exact immutable types.  Transport identifiers are exact
strings; invalid UTF-8 encodings are rejected and encoded byte length is
bounded.  Receipt row counts are bounded before row validation, and aggregate
receipt tuple nodes and text bytes are charged
before authoritative reconstruction.  Endpoint doctrine/context/witness values
remain subject to the separate realization validator's finite-value, depth,
byte, integer, evaluation, and closure limits.  Logging records control-flow
state plus bounded identifiers, indices, counts, costs, reason codes, and short
digest prefixes; it does not emit recurrence values, observation payloads, or
obstruction payloads.

The contract is deterministic local replay evidence.  It is not a portable
signed package, remote attestation, process sandbox, confidentiality boundary,
or proof that external input declarations describe reality.

## 8. Formal boundary

[`VeyraRealizationTransport.lean`](../proofs/lean/VeyraRealizationTransport.lean)
proves, without axioms, abstract relation-level laws for:

- inverse-image identity and composition;
- indiscrete-bottom preservation;
- common-refinement preservation;
- identity and composition of an explicitly hypothesized nonincreasing cost
  action.

The Lean source does not import or verify Python, canonical encodings, R11,
R16, endpoint replay, resource bounds, receipts, P1-A, or concrete contexts.
The executable/formal correspondence remains a documented review boundary, not
a theorem.

## 9. Nonclaims

This slice does not establish:

- cross-doctrine transport or general recurrence transformation;
- covariant pushforward, a category, functor, natural transformation, or
  canonical quotient section;
- transport of names, ordinals, chosen representatives, or generator IDs;
- exact cost preservation in general;
- total generic R16 descent or promotion of a partial descent;
- semantic embedding of R11 echo or P1 admission of derived closure observers;
- authentication, chronology, target independence, mathematical novelty,
  runtime optimality, theorem-card registration, or ontology promotion.

## 10. Implementation and evidence map

- package: [`src/core/realization_transport/`](../src/core/realization_transport/)
- API: [`public.py`](../src/core/realization_transport/public.py)
- DTOs: [`types.py`](../src/core/realization_transport/types.py)
- validation/digests: [`validation.py`](../src/core/realization_transport/validation.py),
  [`digest.py`](../src/core/realization_transport/digest.py)
- construction/replay/laws: [`runtime.py`](../src/core/realization_transport/runtime.py)
- focused tests: [`test_realization_transport.py`](../tests/test_realization_transport.py),
  [`test_realization_transport_adversarial.py`](../tests/test_realization_transport_adversarial.py)
- source realization: [document 161](161_p1_r16_realization_contract.md)
- P1-A sibling design and implementation:
  [RFC 169](169_p1a_all_status_transport_rfc.md),
  [document 170](170_p1a_all_status_transport_v2.md)
- abstract formal laws:
  [`VeyraRealizationTransport.lean`](../proofs/lean/VeyraRealizationTransport.lean)
