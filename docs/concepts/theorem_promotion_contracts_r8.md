# Theorem Promotion Contracts R8

**Status:** implemented on 2026-07-14.
**Scope:** fail-closed authorization for moving an Essence/Core layer into `theorem-derived`.
**Certificate:** `theorem_promotion_contract_r8`.

## Why R8 was required

R7 made one proof artifact sound, but theorem-layer dispatch was still keyed only by a set of names. `_theorem_row(layer)` ignored the requested layer and always loaded `THM-R7-004`. The following maintenance mistake therefore produced a false promotion:

1. remove `native-number` from the shadow set;
2. add `native-number` to `THEOREM_LAYERS`;
3. request its derivation row;
4. receive `theorem-derived` carrying the intrinsic-resonance theorem and digest.

No proof of native number theory occurred. Because `proof_complete` consumes classification counts, this defect could also improve the headline readiness metric without adding mathematics.

R8 removes the name set and makes theorem promotion an exact contract lookup.

## Contract model

`LayerTheoremContract` binds every static field that affects the meaning of a promoted row:

| Field | Bound meaning |
|---|---|
| layer, role, certificate | exact `VeyraCoreLayer` identity |
| theorem ID | exact named theorem |
| statement digest | canonical proposition under a domain-separated hash |
| artifact digest | exact connected proof graph |
| proof rules/native laws | exact inferred closure |
| handler ID | approved theorem/provider/verifier family |
| semantic carrier | the object type for which the theorem is sound |
| bridge ID | the reviewed formal bridge family |
| boundary | exact non-claim text |

The production registry is a `MappingProxyType`. Contract digests include every static field. A trusted handler manifest anchors each `handler_id` to one reviewed contract digest and exact provider/verifier/bridge callable tuple. The digest is a hard-coded trust root, not a value accepted merely because a supplied contract can hash itself; changing layer/role/certificate in a singleton registry therefore blocks before dispatch.

## Resolution algorithm

For a requested layer, `resolve_layer_theorem()`:

1. rebuilds and validates the supplied registry values;
2. rejects mapping-key/contract-key mismatch;
3. rejects duplicate layer names, theorem IDs, proof artifacts, or contract digests;
4. requires exact layer name, role, certificate, and ready status;
5. calls only that contract's approved theorem provider and verifier;
6. recomputes statement, artifact, rule, law, and boundary evidence;
7. calls only the approved bridge provider, then independently rehashes the reviewed TCB, generated export, pinned toolchain identity, binding digest, diagnostics, and boundary rather than comparing a cache entry with itself;
8. returns a `VerifiedLayerTheorem` carrying statement, artifact, carrier, bridge, and contract digests.

There is no default theorem and no theorem-name membership fallback. `layer_derivations()` snapshots the immutable registry and passes the same mapping through classification and resolution.

## Exact contract at the R8 checkpoint

At the R8 checkpoint, before the R9 carrier bridge existed, the sole
production contract was:

```text
layer             = intrinsic-resonance
certificate       = proof_carrying_core_r7
theorem           = THM-R7-004
semantic carrier  = veyra.proof.recurrence.v1
formal bridge     = veyra.lean.r7.recurrence-tcb.v1
```

R8 hardened authorization for that one promotion; it did not add a theorem or
promote another layer.

## Current contract after the R10 renewal

R9 proved only the fixed-anchor unary intrinsic image carrier. R10 keeps that
carrier and renews the required formal bridge with exact source elaboration:

```text
layer             = intrinsic-resonance
certificate       = proof_carrying_core_r7
theorem           = THM-R7-004
semantic carrier  = veyra.proof.recurrence-equiv-strict-intrinsic-mode.v1
formal bridge     = veyra.lean.r10.proof-elaboration-tcb.v1
```

The promoted theorem and connected R7 proof artifact are unchanged. This is
not a second theorem-derived layer: taxonomy remains `1/4/25/5`. R9 transport
is in [doc 125](../concepts/intrinsic_mode_transport_r9.md); R10's closed recurrence
surface, generic image semantics, 37-source/ten-stage source/object/runtime trust boundary, and
Python-parser TCB are in [doc 126](../log/proof_grade_core_elaboration_r10.md).

## Three-carrier boundary

The repository still has three mathematically different carriers:

1. proof `Recurrence`: the unary inductive carrier in `VeyraNativeArithmetic.lean` and `proof_core_types.py`;
2. strict native `Mode`: anchored `Mode(Breath(Tact...))` with closure, contiguity, observer, and obstruction semantics;
3. external word `Mode`: labeled tact words used by cyclic/phase resonance shadows.

R8 did not identify these carriers. R9 now identifies proof `Recurrence` only
with the fixed-anchor unary `IntrinsicMode` image inside strict native `Mode`;
it does not identify arbitrary strict modes or the external word carrier. In
particular, `THM-R7-004` still cannot be attached to `native-number` or cyclic
`resonance` merely because those layers use recurrence language.

R9 completes the narrow positive bridge by proving fixed-anchor encode/decode,
intrinsic-image round trips, stitch/weave homomorphisms, and resonance transport.
Word erasure remains a separate obstruction: it forgets labels and phase, so
reflection into arbitrary cyclic resonance is false.

## Adversarial coverage

`tests/proof/test_layer_theorem_contracts.py` reproduces the old false-promotion edit and checks rejection of:

- unbound layers and renamed/swapped registry keys;
- singleton theorem transplantation to a different layer/readiness class;
- changed role, certificate, or status;
- changed theorem ID, statement/artifact digest, rule/law closure, or boundary;
- changed carrier, bridge, or handler ID;
- replaced providers and fail-open verifiers;
- a poisoned cached bridge report with forged TCB/toolchain/binding fields;
- malformed text/digest/closure/provider fields;
- duplicate layers, theorem IDs, proof artifacts, and contract digests.

The R8 certificate additionally requires that the readiness row expose the exact resolved statement, proof, carrier, bridge, and contract evidence.

## R8 checkpoint verification

- focused R8/R7/readiness tests: `67/67`;
- Rust VAM native tests: `12/12`;
- four Lean gates, including the captured R7 four-file bridge: checked with warnings as errors;
- full the complete verification suite: `64/64` certificates, Sage smoke, doctest `41/41`, hygiene;
- Ruff, `git diff --check`, and independent re-review: clean, with no blocker/high/medium.

## Next candidates after R10

Carrier transport and source elaboration are complete only for the closed R7
recurrence fragment and intrinsic image. The next candidates are:

1. R11 observer-indexed echo semantics and proof rules;
2. general Core/VAM elaboration only with a separately reviewed bridge;
3. only then, a second narrow theorem-derived nucleus to exercise
   multi-contract dispatch in practice.

The existing cyclic/phase, approximate, weighted, spectrum, compression, topology, and probability layers remain unchanged shadows or diagnostics.
