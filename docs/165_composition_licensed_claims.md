# 165 — Composition-licensed aggregate claims

## Status and layer boundary

Issue #18 is implemented as a bounded semantic-aggregation layer immediately
upstream of P2-S:

```text
validated local claim receipts
    -> exact ClaimContract bindings
    -> named bounded CompositionLicense replay
    -> CompositionReceipt / authenticated disclosure
    -> existing P2-S named-promotion firewall
```

The v1 implementation is `src.core.claim_composition`. It does **not** extend
P2-S into a generic promotion calculus and adds no P2 v1 rule. Every composition
receipt and disclosure permanently records `p2_promotion_established=false`.
The separate additive v2 admission contract is documented in
[document 171](171_p2_composition_admission_v2.md); it must freshly replay this
unchanged v1 boundary and would permit only a typed `PRESENTED` public
presentation after its producer wave is implemented.

## 1. Four predicates, not one summary bit

`CompositionAssessment` keeps four questions independent:

```text
local_receipts_valid
aggregate_claim_well_formed
composition_license_established
aggregate_claim_licensed
```

Locally valid receipts plus a well-formed target still produce
`composition_license_established=NOT_ESTABLISHED` and
`aggregate_claim_licensed=NOT_ESTABLISHED` when the named morphism is missing,
malformed, or inapplicable. `CompositionReceipt` exists only when all four
predicates freshly replay as `ESTABLISHED`.

`validate_composition_license_shape(...)` deliberately checks only closed
shape and digest. It is named as such so callers cannot mistake shape validity
for authority. Establishment is computed only by
`assess_claim_composition(...)` against the exact source family and target.

## 2. Local source contracts

Two explicit source adapters exist.

### 2.1 Assumption-bearing external local receipt

`build_local_claim_receipt(...)` binds a canonical `ClaimContract`, source
receipt root, source-validator root, and local validity. The composition layer
replays that binding exactly through `build_external_composition_source(...)`.
The validator root identifies the external contract under which validity was
established; composition does not silently replace that validator or claim its
trustworthiness.

This adapter supplies the issue's sharp fixture:

```text
R_A: A -> P(x)
R_B: B -> P(y)
```

The positive target retains both claim roots, both scope roots, and exactly
`{A,B}`. The unconditional target drops `{A,B}` and is rejected with
`assumptions-not-exact-union`. Receipt multiplicity cannot discharge an
assumption.

### 2.2 Governed Phase-III result

`build_governed_composition_source(...)` accepts only an exact
`GovernedEvaluationResult` that passes its original validator. It derives:

- the governed result root as the claim root;
- committed parent/test/schema/row/policy roots as scope;
- the observer-program root;
- claimed and terminal ledgers as **execution** lineage;
- worker/outcome, capability, attempt, and ledger roots as provenance;
- empty research-lineage and assumption vectors;
- `LOCAL`, `STRUCTURAL`, `SINGLE_LOCAL_RECEIPT`, `LOCAL_ONLY`, and
  `EVALUATION_COMPLETION`.

Capability and attempt digests are not semantic assumptions. Execution-ledger
lineage and research-line lineage are separate contract axes. `READY` means
evaluation completion only; it is not an empirical finding or truth verdict.

Directly constructing or mutating a DTO is never authority. Source replay
requires exact dataclass types, original governed validation or the external
receipt binding, canonical roots, and exact derived equality.

## 3. The only V1 morphism: exact conjunction

`EXACT_CONJUNCTION` accepts two to 64 distinct canonical
`INCLUDE_LOCAL_CLAIM` sources. The effect means “retain this local claim as one
conjunct”; it does not mean empirical support, independence, or confirmation.
The target is derived rather than caller-authored and carries:

- the exact union of claim, scope, and assumption roots;
- each component contract digest, preserving per-component relations;
- exact observer and doctrine bindings;
- separate exact execution- and research-lineage unions;
- exact provenance roots and claim classes;
- `FINITE_CONJUNCTION`, never `UNIVERSAL`;
- `MULTIPLE_LOCAL_RECEIPTS`, never agreement or independence;
- `LOCAL_ONLY`, never family/adaptive validity;
- `CONJUNCTIVE_SUMMARY`, never significance or population wording.

Sources are ordered by local receipt digest and duplicates are rejected.
Caller permutation therefore cannot change the N-ary artifact or manufacture
multiplicity. V1 accepts no capability roots: discharge, projection,
independence, transport, adaptive validity, and stronger wording need future
separately named verifiers.

## 4. Negative controls

Fresh replay blocks all of these upgrades:

| Attempt | Stable obstruction |
|---|---|
| replaced/widened scope | `scope-not-exact-union` |
| dropped assumptions | `assumptions-not-exact-union` |
| local/existential to universal | `quantifier-upgrade` |
| multiplicity to agreement/independence | `corroboration-upgrade` |
| local to family/adaptive validity | `adaptive-capability-upgrade` |
| structural/empirical to epistemic/objectivity | `claim-class-reinterpretation` |
| local wording to significance/family/population | `public-wording-upgrade` |
| execution-lineage rewrite | `execution-lineage-not-exact-union` |
| research-lineage rewrite | `research-lineage-not-exact-union` |
| diagnostic/counterevidence included as a conjunct | `source-effect-not-local-claim-inclusion` |

A license is target-specific. Component-contract drift, any changed semantic
axis, a missing license, a malformed digest, duplicates, subclasses, wrong
container types, or a noncanonical source order all fail closed.

## 5. Complete aggregate-envelope disclosure replay

`CompositionPublicExport` carries the **complete** target, license, assessment,
composition receipt, payload digest, and boundary. It intentionally omits the
potentially large original local artifacts. Therefore:

- `build_composition_public_export(...)` freshly replays original sources;
- `composition_public_export_json(...)` validates before canonical encoding;
- `composition_public_export_from_json(text, sources)` is a strict decoder and
  accepts only canonical bytes that replay against those exact sources;
- `composition_disclosure_json(...)` is the convenience build-and-render path.

This is a disclosure of a nonpromoted aggregate artifact, not a P2 judgment or
a self-contained proof of source validity. A recipient must possess the exact
governed results or externally validated local receipts named by the export.

`build_composition_p2_premise(...)` supplies the v1 seam: after fresh
source-backed receipt replay it creates one `PremiseArtifact` with no P2
indices and explicit target-contract, license, assessment, source-family, and
nonpromotion evidence. `validate_composition_p2_premise(...)` replays the exact
source family before accepting that artifact. No P2 v1 rule consumes its
`claim-composition-receipt` kind; the registry, literal oracle, certificate, and
historical entry 90 remain unchanged with `promotions=0`.

The v2 contract forbids casting this index-free v1 premise into a conclusion.
It requires the future sibling to derive a new
`claim-composition-presentation-v2` premise from the raw source family, target,
license and receipt, and to make contract, claims, scope, assumptions, doctrine,
source validators and composition visible as named indices. The target's opaque
assumption roots remain undischarged, and external validator roots remain
identities rather than trust claims.

For portable transfer, `CompositionReplayPackage` carries the public export
plus detached local receipt contracts/effects. Its strict canonical decoder
can replay composition without the original Python objects. This does not
revalidate an external validator or prove source truth. The bounded
`scripts/verify_composition.py` CLI reports replay and authentication as
separate outcomes and never treats omitted authentication as verified.

The decoder also rejects a source family that is complete but not in its
unique canonical order. Bounded mutation tests cover extra fields, digest and
receipt-root drift, source reordering, authentication-tag/export-root drift,
and both replay/authentication byte caps.

`proofs/lean/VeyraClaimComposition.lean` is a small abstract model, with no
project-declared axioms, of the same finite-conjunction shape. It proves
field-union preservation, permutation invariance, append decomposition, and
explicit false flags for P2 promotion, independence, assumption discharge,
and universalization. It is an internal research candidate: no theorem claims
that its abstract `Contract` is byte-equivalent to the Python DTO/codec, and it
has no `THM_*`, certificate, or P2 registry entry.

The JSON cap is 1 MiB. Each dimension accepts at most 256 sorted unique SHA-256
roots, each contract at most 1024 total roots, and a composition at most 64
sources. Before repeated governed replay, the implementation iteratively
precharges at most 2,000,000 occurrence-expanded worker-output units across the
family. Tests exercise the cap with a lowered bound rather than allocating a
hostile multi-million-value fixture.

## 6. Authentication is byte identity, not truth

`AuthenticatedCompositionExport` binds all four critical roots:

- export payload;
- composition receipt;
- license;
- assessment.

It supports the same bounded authentication profiles as replay packages:
HMAC-SHA256 and optional Ed25519. Canonical envelope JSON has a 32 KiB cap and
a strict decoder. Validation first replays the composition export against the
original sources, then verifies the exact root binding and authentication tag.

Authentication establishes only integrity/authenticity relative to supplied
key material. Signer identity and trust remain external. A valid MAC or
signature cannot make invalid sources valid, establish claim truth, discharge
assumptions, or flip the permanent P2 nonpromotion bit.

## 7. CI, package, and existing boundaries

The portable hosted lane runs external-receipt positive, adversarial,
disclosure, and authentication tests on every supported host. POSIX one-shot
adapter and worker-output precharge cases remain in the capability-gated full
lane. Wheel smoke imports `src.core.claim_composition` strictly from the
installed artifact.

- Document 166 implements issue #3 as a separate finite provenance diagnostic;
  composition still says only `MULTIPLE_LOCAL_RECEIPTS` and has no automatic
  independence upgrade.
- Document 162 governs Comparative Bridge / Structural Separation, not generic
  receipt aggregation.
- Document 163 governs declared adaptive research-line history; conjunction
  alone remains `LOCAL_ONLY`.
- P2-S v1 remains byte-exact. The additive v2 contract permits only the exact
  named licensed-composition presentation documented in 171; composition v1
  itself creates a possible premise, never its public presentation.

## 8. Exact nonclaims

This implementation does not establish:

- validity or trustworthiness of an arbitrary external validator;
- assumption discharge or implication theorems;
- finite coverage, universalization, or quantifier strengthening;
- observer/doctrine transport or provenance independence;
- adaptive/family statistical validity, significance, or population transfer;
- causal, explanatory, objectivity, ontology, novelty, theorem, certificate,
  or promoted-judgment status;
- trusted chronology, source fidelity, complete disclosure, key identity, or a
  self-contained executable replay of the original local computations. The
  replay package reproduces receipt-bound composition, not those computations.

Future composition rules must be closed, bounded, separately reviewed, and
must replay every contract axis they preserve or explicitly transform.
