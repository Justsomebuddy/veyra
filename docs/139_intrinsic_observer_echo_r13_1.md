# R13 — Intrinsic observer-echo theorem nucleus

**Status:** complete; guarded bridge, exact R8 promotion, certificate, and Sage facade checked
**Date:** 2026-07-29
**Narrow promoted layer:** `intrinsic-observer-echo`
**Broad `echo`:** remains witness-only
**Capability:** `preserves`

## Purpose

R13 must create a second substantive theorem nucleus without renaming an old
finite witness or reusing the R7 artifact merely to increase a counter.

The frozen candidate composes five already-separated boundaries:

```text
R7 checked unit-weave equality
  -> R9 exact intrinsic-mode image
  -> R10 source-replayed elaboration
  -> R11 equality + readiness implies echo
  -> R12 valid lowering-image echo transport
```

## Frozen source theorem

The Core proof source is:

```lisp
(veyra-proof 1
  (claim (forall item recurrence
    (equal (weave (var item) (pulse (silence))) (var item))))
  (proof (forall-intro item recurrence
    (native-law weave-unit-right (var item)))))
```

with proof closure:

```text
forall-intro
native-law weave-unit-right
```

Reconnaissance confirmed that this source parses and checks through the
current R10 surface. Reconnaissance digests are not trust roots; implementation
must replay, review, and pin the final captured source and artifact.

## General R13 statement

Let:

- `unit := pulse silence`;
- `o` be a closed typed R11 observer satisfying the 2,048-node/128-depth bound;
- `r` be an exact R7 recurrence satisfying the R11 128-tact bound;
- `ρ` be a response of the kind inferred for `o`.

The reviewed theorem is:

```text
observerBounded o
  and r11RecurrenceBounded r
  and echoOutcomeBounded (echo o r r)
  and observeIntrinsic o (intrinsicMode r) = ready ρ
  ->
echoIR o
  (lowerRecurrenceIR (weave r unit))
  (lowerRecurrenceIR r)
  = some (echo (lowerResponseIR ρ))
```

The claim is general over the explicitly bounded closed observer grammar and
recurrence carrier. It is conditional on readiness and the reviewed R12
resource predicates. It is not a finite enumeration or unbounded-domain result.

## Mandatory counter-boundaries

Two laws must ship in the same reviewed artifact.

### Readiness is necessary

For `r = silence` and the tail observer, unit-weave equality still holds, but
both observations are blocked by exactly:

```text
tailOfSilence@[applyTail]
```

The transported result is two-sided `domainBlocked`, never `echo`.

### Reflection is false

The crest observer can map unequal pulse recurrences to the same pulse mark.
Therefore the bridge does not reflect source equality and is not faithful or
an equivalence.

## Standalone theorem rows

The reviewed standalone Lean module now fixes five exact IDs:

| Candidate ID | Planned responsibility |
|---|---|
| THM-R13-001 | captured unit-weave source is accepted |
| THM-R13-002 | source semantics and exact R9 image |
| THM-R13-003 | general readiness-conditioned intrinsic echo |
| THM-R13-004 | tail/silence domain-blocked boundary |
| THM-R13-005 | crest nonreflection boundary |

These statements compile in a fresh pinned ten-stage parent chain. `THM-R13-001`
is consumed through R7 checker soundness before `THM-R13-002` derives the
unit-weave equality used by `THM-R13-003`; the Python surface/R10 artifact is
still an external phase-one origin until the guarded bridge binds both sides.

## Formal evidence boundary

- `src/core/intrinsic_observer_echo_source.py` replays the exact source through
  the R10 surface, R7 kernel, and checked R9 artifact path.
- Source/artifact pins are `1280f1c4...70f6` / `2ae21b67...cd1b`; the R10
  binding is `d7d5d9c0...67f4`.
- `proofs/lean/VeyraIntrinsicObserverEcho.lean` has exact source SHA-256
  `d9b86a1d...1df0` and no `sorry`, `admit`, `axiom`, or `unsafe`; the two
  fixed boundary rows discharge public `THM-R12-003/008` bounds directly.
- The named Lean declarations compile without `sorry`, `admit`, `axiom`, or
  `unsafe`, and the exact R7-soundness dependency is explicit.

This phase checkpoint is now consumed by the final guarded report described
below; it is not standalone authority for promotion.

## Carrier and bridge identities

Carrier:

```text
veyra.proof.r7-unit-weave.r9-image.r11-ready-echo.r12-lowering-image.r13.v1
```

Bridge:

```text
veyra.lean.r13.intrinsic-observer-echo-tcb.v1
```

The final bridge-plus-contract composition binds:

- the full R13 statement, not only a positive observer example;
- the captured R10 elaboration artifact;
- exact R11 and R12 parent report bindings;
- the separate R13 effect digest;
- source, object, snapshot, and pinned toolchain identities.

The theorem object itself is deliberately local-bound: it carries the exact
source proof, executable evidence, and effect. It does not claim to contain
the parent reports or formal bridge; those are checked separately by the
one-shot R8 bridge provider.

That provider/verifier handoff is synchronous and one-shot in the same
`ContextVar` context: provider entry clears stale state, every verification
attempt consumes the token, and `resolve_layer_theorem()` performs no
`await`/task split between the two calls.

## Promotion contract

R13 adds exactly one new trusted handler/contract to the R8 registry.

Requirements:

- preserve the existing `intrinsic-resonance` contract and digest byte-for-byte;
- use a distinct theorem object and artifact digest;
- normalize statement digests through an internal handler-specific trusted
  path, never caller-supplied dispatch;
- reject broad-`echo`, native-number, intrinsic-resonance, swapped-key,
  swapped-provider, and swapped-verifier transplants;
- resolve only the exact new layer metadata.

The post-promotion taxonomy is:

```text
36 layers
2 theorem-derived
4 witness-only
25 shadow
5 meta
proof_complete = false
```

Adding the narrow layer is preferable to relabeling broad `echo`, whose
semantics are wider than this theorem.

## Effect boundary

R13 uses a separate declaration; it must not mutate the four-row R12.1
registry or the R12.5 effect/manifest.

Evidence:

- source carriers: R7 recurrence, R9 intrinsic-mode image, R11 response;
- target: VAM intrinsic IR;
- capability: `preserves` only;
- evidence: `kernel-proof / general` plus `formal-bridge / general`;
- formal-effect promotion readiness: false;
- layer promotion: only through exact R8 contract resolution.

No `reflects`, faithful, equivalence, arbitrary raw-IR, VAMI-parser, receipt,
legacy-VAM, or all-observer-totality claim is allowed.

## Implementation groups

Keep every file at or below 300 lines:

- theorem/artifact/Lean-render/effect modules;
- one fail-closed R13 report/manifest/snapshot/compiler bridge family;
- `proofs/lean/VeyraIntrinsicObserverEcho.lean`;
- handler-specific R8 registry extension with old-digest preservation;
- one R13 certificate;
- direct theorem/artifact/effect/bridge/promotion/transplant tests.

## Acceptance

Final reviewed bindings:

- phase artifact: `2ae21b674aa54efd50630a6c764af47ed72ce973b9171fe8eea1a550f3c8cd1b`;
- executable evidence: `f30763425eda0f400f65447a96f8030df29dc99ff837cf8d04d49759e33d5902`;
- theorem artifact: `06531f09c4dddc7f04182a9ab5826623101351c3fa1066bf52717af1d2298e41`;
- guarded snapshot/report: `bc8dc77c8debbe5efe03f0d0f05959033971c1b3eb96c33e7993e551603a5953`
  / `e3a57712afd6b55f521b86b50b9543ab6317b135c23d3f4ecc9b41d89ee74957`;
- new R8 contract: `a2c8e00f8f5d35334a6a616121d2aee13e9bb2a547cedc121b2bb6482b140a4f`;
- direct executable-handler pin: `ee12d603d86b0a1387bcba3e9c6a76fbba983940908e5ec07a0b5d856a9d5673`;
- preserved old R7 contract: `484534000ee59a28d0d131b777dcc775d56d24b82c70797954ba82c8570a8eba`.

The bridge checks 25 exact sources through 11 stages and 10 reviewed objects.
Three executable rows retain ready echo, exact two-sided tail blockage, and
crest nonreflection. One level-3 core certificate and a presentation-only Sage
facade raised the R13-stage suite/API counts to 72/92; current integrated totals
are 74/93 without adding notebooks.

R13.1–R13.4 establish the bounded evidence stated above. K0 acceptance remains
a separate condition. The result is one narrow theorem-derived layer,
never a promotion of broad `echo`.
