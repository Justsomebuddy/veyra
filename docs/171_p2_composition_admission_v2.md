# P2 Licensed-Composition Presentation Admission V2

**Date:** 2026-08-15  
**Status:** registry/oracle and authoritative presentation producer implemented  
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

This contract closes only that bounded design seam. Its versioned non-root
sibling is limited to:

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
canonical ordered `(local receipt digest, validator root, authority class)`
triples, rather than an unordered validator multiset that could detach a
validator from its source or confuse a named validator with its execution.
The authority class is exactly one of `NATIVE_GOVERNED_REPLAY` and
`EXTERNAL_BINDING_ONLY`. A native class is derived only when the governed
result is present and its governed adapter is freshly replayed. A detached
receipt remains external-binding-only even if it names the same validator root
as the governed adapter.

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

The first implementation wave published only this meta-validation surface from
`src.core.p2_claim_admission_v2`:

- `promotion_registry_v2()`;
- `validate_registry_v2(...)`; and
- `audit_registry_v2_against_literal_oracle(...)`.

That dependency-first wave had no presentation DTO, premise producer,
schema-audit producer or decoder. The producer wave now adds those surfaces
without changing the exact v1 prefix; v1 still rejects the new rule and
complete v2 snapshot. Registry conformity alone therefore cannot issue a
public presentation.

## 4. Authoritative producer

The public-judgment producer accepts only:

- the raw canonical composition source family;
- the exact target `ClaimContract`;
- the exact `CompositionLicense`;
- the exact `CompositionReceipt`; and
- a bounded judgment identifier.

It must first preflight shallow types and resource bounds. It then freshly
replays, in dependency order:

1. all original governed or external source bindings, deriving the exact
   per-source authority class from the replay path rather than the validator
   name;
2. the exact target conjunction, including retained assumption and
   source-validator roots;
3. the target-specific license, all four independent composition-assessment
   predicates, and the receipt with `p2_promotion_established=false`;
4. the exact v2 premise and its visible evidence/indices;
5. the v2 registry and independent extension oracle;
6. the claim descriptor and audit request; and
7. the named-rule `PromotionSchemaAudit`; and
8. the separate fixed-five registry-v2 `SchemaAuditReport`.

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

The truth-safe public result is `LicensedCompositionPresentation`. Its public
producer surface is:

- `build_composition_presentation_premise(...)`;
- `validate_composition_presentation_premise(...)`;
- `build_licensed_composition_presentation(...)`;
- `validate_licensed_composition_presentation(...)`; and
- strict canonical JSON encoder and source-backed decoder counterparts for the
  licensed-composition presentation.

The DTO retains both audits under distinct `promotion_schema_audit` and
`schema_audit_report` fields. The former reconstructs the one named rule and
request under a v2-specific digest domain. The latter independently audits the
five exact registry-v2 DTO schemas in registry order under separate row/report
domains. Both bind `SCHEMA_CONFORMANT / NOT_CLAIMED`, explicit meta-only scopes
and the complete nonclaims; neither is conclusion authority. Callers can
supply neither audit nor an audit policy.

The naming is deliberate: the object is a licensed presentation, not an
authoritative truth judgment.

## 5. Public-presentation meaning

`PRESENTED / ESTABLISHED / SUPPLIED_PRESENTATION` means
only that one exact, licensed, freshly replayed finite conjunction conforms to
the new named presentation rule. It preserves and publicly binds:

- the exact target `ClaimContract` and complete claim, scope, assumption and
  doctrine sets;
- the source-validator and source-family identities plus the ordered authority
  class for every source;
- the exact `CompositionReceipt`, license and four-axis assessment;
- the full v2 premise, descriptor, request and schema-only audit, not only
  their digests;
- the exact registry/oracle bindings and every visible family root; and
- permanent false fields including `assumptions_discharged=false`, together
  with explicit nonclaim flags for truth, coherence, independence and ontology.

It does not reinterpret a composition receipt as truth or turn a schema audit
into a substantive conclusion. The result is a typed public presentation, not
a theorem, certificate or object constructor.

Native governed replay and detached binding replay may preserve the same v1
semantic `CompositionReceipt`. They must nevertheless produce distinct v2
source-validator-family and public-judgment digests whenever their authority
classes differ. Validator-root equality alone can never imply native execution.

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

The implementation rejects overlong character counts before UTF-8 encoding.
It then captures only exact allowlisted DTO and enum identities into a private
immutable snapshot while aggregating premise fields, assumption dependencies,
structural nodes and nonpayload text before deep validation, equality, encoding
or authoritative replay. Caller mutation after capture cannot alter the issued
judgment. The strict decoder rejects
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
- native-governed versus detached-binding replay demonstrating that equal v1
  composition identity does not collapse distinct current authority classes;
- package discovery, wheel import and portable hosted coverage;
- public documentation, changelog and module memory; and
- two independent final reviews.

Passing those checks validates only this bounded executable contract. It does
not promote any mathematical or ontological claim.

Publication was dependency ordered:

1. this docs-only RFC freezes the public contract without runtime claims;
2. the registry/oracle wave adds only the v1-plus-one meta-validator snapshot,
   still without a public presentation producer; and
3. the producer wave adds `LicensedCompositionPresentation` only after fresh
   source-backed replay and the bounded acceptance evidence passes.

The package, portable and hostile suites cover the producer and codec alongside
the unchanged registry-v2 and v1 compatibility pins. Exact commit, hosted CI,
reviewed tree and merge evidence remains recorded on the producer pull request;
focused tests alone are not comprehensive mathematical evidence.

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
