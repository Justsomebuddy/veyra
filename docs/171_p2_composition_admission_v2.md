# P2 Licensed-Composition Presentation Admission V2

**Date:** 2026-08-15  
**Status:** accepted bounded implementation contract; runtime evidence pending  
**Issue:** [#51](https://github.com/Justsomebuddy/veyra/issues/51)  
**Version/schema:** `p2-r17-claim-admission-v2`,
`veyra.p2-claim-admission-judgment.v2`  
**Registry:** `p2-s-promotion-registry-v2`  
**Target package:** `src.core.p2_claim_admission_v2`

## 1. Purpose and compatibility boundary

Claim-composition v1 can freshly replay a licensed exact finite conjunction and
produce a nonpromoted P2 premise. P2-S registry v1 deliberately has no rule that
consumes it. A `PromotionSchemaAudit` checks only the syntax of a named request;
it is not authority for a conclusion and does not establish truth or ontology.

This contract closes only that bounded design seam. Its future non-root sibling
is limited to:

1. one named rule that admits an exact licensed-composition presentation;
2. one independently specified additive registry snapshot; and
3. one source-backed producer for a separate typed public judgment.

The existing P2-S and claim-composition v1 DTOs, digests, registry rows, literal
oracle, certificate, aliases, facade and root exports remain byte-exact. V2 is
not a generic promotion calculus and does not retroactively change the meaning
of any v1 artifact.

## 2. The sole new rule

The only new rule is:

```text
rule id       composition-licensed-presentation-v2
premise kind  claim-composition-presentation-v2
output        PRESENTED / ESTABLISHED / SUPPLIED_PRESENTATION
```

Its one premise exposes the exact evidence fields in this order:

1. `target-contract`;
2. `claim-set`;
3. `scope-set`;
4. `assumption-set`;
5. `doctrine-set`;
6. `source-validator-family`;
7. `source-family`;
8. `composition-license`;
9. `composition-assessment`; and
10. `nonpromotion`.

It exposes the exact visible indices, also in fixed order:

1. `contract`;
2. `claims`;
3. `scope`;
4. `assumptions`;
5. `doctrine`;
6. `source-validators`; and
7. `composition`.

No projection may hide any of these bindings. In particular, an empty P2
assumption-DAG closure does not imply that the conjunction has no assumptions.
The opaque target `assumption_roots` remain visible and explicitly undischarged.
Likewise, source-validator roots remain exact external identities; their
trustworthiness is never inferred. `source-validator-family` commits the
canonical ordered `(local receipt digest, validator root)` pairs, rather than
an unordered validator multiset that could detach a validator from its source.

## 3. Additive registry and independent oracle

The v2 registry is a complete additive snapshot, not an in-place edit of v1:

| Component | Exact count |
|---|---:|
| kind/status domains | 15 |
| named rules | 18 |
| premise projections | 41 |
| index projections | 1 |
| schema targets | 5 |

Its first 15 domains, 17 rules, 40 premise projections, one index projection
and five schema targets must equal the complete v1 registry byte-for-byte. The
only additions are the literal rule above and its one premise projection.

A separately written extension oracle must bind both the exact v1
registry/oracle and the literal new row. Re-serializing the implementation's own
generated registry and comparing it with itself is not independent evidence.
Registry order, cardinality, digests and oracle commitments are part of the
contract.

The inherited anchors are fixed literally:

- v1 registry digest:
  `375f1654807b462c3a9ebd9a112a75ee28fc96a4029cf767acae1fd591a60e9d`;
- v1 literal-oracle digest:
  `2cbe0f2f1f1025696b947c73e32196f230e7748c77c030543d2292a34585875a`.

The v2 extension oracle must bind both values rather than regenerating either
anchor from the implementation under test.

## 4. Authoritative producer

The public-judgment producer accepts only:

- the raw canonical composition source family;
- the exact target `ClaimContract`;
- the exact `CompositionLicense`;
- the exact `CompositionReceipt`; and
- a bounded judgment identifier.

It must first preflight shallow types and resource bounds. It then freshly
replays, in dependency order:

1. all original governed or external source bindings;
2. the exact target conjunction, including retained assumption and
   source-validator roots;
3. the target-specific license, all four independent composition-assessment
   predicates, and the receipt with `p2_promotion_established=false`;
4. the exact v2 premise and its visible evidence/indices;
5. the v2 registry and independent extension oracle;
6. the claim descriptor and audit request; and
7. the fixed five-target schema-only audit.

The derived P2 request has an exactly empty P2 assumption-DAG. Target
`assumption_roots` remain separately visible through the `assumptions` index;
the empty request closure cannot discharge or reinterpret those opaque roots.

Only after those checks may it construct the separate public judgment with the
fixed `PRESENTED / ESTABLISHED / SUPPLIED_PRESENTATION` triple. A caller cannot
supply an audit, descriptor, request, conclusion, status or provenance as
authority. `SCHEMA_CONFORMANT` remains a schema result only.

The verifier accepts the same raw authoritative inputs plus a candidate result,
reconstructs the complete result from scratch, and requires exact equality. A
strict canonical decoder does the same after decoding; digest-only evidence is
never sufficient.

The producer derives premise, descriptor, request and schema-audit values for
this one named rule. It does not expose a general caller-programmable P2
judgment constructor.

The planned truth-safe public result name is
`LicensedCompositionPresentation`. The targeted public API is:

- `promotion_registry_v2()`;
- `validate_registry_v2(...)`;
- `audit_registry_v2_against_literal_oracle(...)`;
- `build_composition_presentation_premise(...)`;
- `validate_composition_presentation_premise(...)`;
- `build_licensed_composition_presentation(...)`;
- `validate_licensed_composition_presentation(...)`; and
- strict canonical JSON encoder and source-backed decoder counterparts for the
  licensed-composition presentation.

The naming is deliberate: the object is a licensed presentation, not an
authoritative truth judgment.

## 5. Public-presentation meaning

When implemented, `PRESENTED / ESTABLISHED / SUPPLIED_PRESENTATION` will mean
only that one exact, licensed, freshly replayed finite conjunction conforms to
the new named presentation rule. It preserves and publicly binds:

- the exact target `ClaimContract` and complete claim, scope, assumption and
  doctrine sets;
- the source-validator and source-family identities;
- the exact `CompositionReceipt`, license and four-axis assessment;
- the full v2 premise, descriptor, request and schema-only audit, not only
  their digests;
- the exact registry/oracle bindings and every visible family root; and
- permanent false fields including `assumptions_discharged=false`, together
  with explicit nonclaim flags for truth, coherence, independence and ontology.

It will not reinterpret a composition receipt as truth or turn a schema audit
into a substantive conclusion. The result is a typed public presentation, not
a theorem, certificate or object constructor.

## 6. Codec and resource contract

V2 inherits every claim-composition limit:

- 2 through 64 canonical unique sources;
- at most 2,000,000 occurrence-expanded units;
- at most 256 roots in each contract dimension; and
- at most 1,024 total roots in one contract.

It adds the following sibling ceilings:

| Resource | Ceiling |
|---|---:|
| premise/rule cardinality | exactly one |
| identifier | 128 UTF-8 bytes |
| aggregate nonpayload UTF-8 text | 1 MiB |
| combined shallow and decoded structural nodes | 65,536 |
| canonical public-judgment JSON | 1 MiB |

The implementation must reject overlong character counts before UTF-8
encoding. It must then aggregate and precharge premise fields, assumption
dependencies, structural nodes and nonpayload text before deep validation,
equality, encoding or authoritative replay. The strict decoder rejects
subclasses, bool-as-int values, duplicate object keys, trailing or noncanonical
JSON, depth overflow, unknown enum members, stale roots, field/order drift and
every cross-object splice.

Errors use bounded reason codes and logs disclose no raw source, claim,
assumption, validator, license, assessment or payload body and no full digest.
Because legacy composition replay may log full roots through
`src.core.proof_core_codec`, every public replay must install a first-position,
context-local filter under a shared `RLock`, restore the exact prior filter and
record-factory state on success and exception, and allow unrelated threads to
pass. Acceptance tests must cover prefiltering, exception restoration and
concurrent unrelated-thread behavior.

## 7. Acceptance evidence

Implementation acceptance requires all of the following:

- exact claim-composition and P2-S v1 compatibility pins;
- exact v2 registry order, counts, digest and independent-oracle pressure;
- normal and hostile source-backed producer/verifier/decoder tests;
- two-source and 64-source cases;
- strict-JSON, splice, permutation and every resource-edge test;
- package discovery, wheel import and portable hosted coverage;
- public documentation, changelog and module memory; and
- two independent final reviews.

Passing those checks validates only this bounded executable contract. It does
not promote any mathematical or ontological claim.

Publication is dependency ordered:

1. this docs-only RFC freezes the public contract without runtime claims;
2. a registry/oracle wave may add only the v1-plus-one meta-validator snapshot,
   still without a public presentation producer; and
3. a later producer wave may add `LicensedCompositionPresentation` only after
   fresh source-backed replay and all acceptance evidence pass.

A later wave must update this status and evidence map from its exact merged
tree. Merely having worktree code or focused local tests is not a published
implementation claim.

## 8. Permanent nonclaims

No source truth, external-validator trust, logical consistency or coherence,
assumption discharge, unconditionalization, independence or corroboration,
adaptive/family/statistical/population validity, universal or existential
quantifier upgrade, objectivity, theorem, certificate, formal proof, ontology,
object, history, lifecycle, empirical or physical instantiation,
authentication, custody, chronology, or audit-as-truth follows.

## 9. Hard stops

Stop and redesign if the implementation:

- needs an output stronger than `PRESENTED`;
- mutates any P2-S or claim-composition v1 byte;
- hides assumptions or source validators behind an index projection;
- trusts a caller-supplied audit or conclusion;
- treats `SCHEMA_CONFORMANT` as truth;
- accepts digest-only evidence; or
- performs resource checks only after authoritative replay.

These are contract failures, not optional future hardening.

## 10. Related boundaries

- [P2 philosophical kernel](151_veyra_philosophical_kernel_p2.md)
- [Composition-licensed aggregate claims](165_composition_licensed_claims.md)
- [API reference](reference/api.md)
