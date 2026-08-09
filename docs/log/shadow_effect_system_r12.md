# R12 Shadow Effect System — Bridge Branding Slice

**Status:** R12.1 executable definitions and audit registry
**Version:** `veyra.shadow-effects.r12.1`
**Date:** 2026-07-28
**Claim boundary:** no new theorem, Lean artifact, certificate, layer promotion, or taxonomy change

## 1. Purpose

R9 proves an exact equivalence only between proof recurrence and its fixed-anchor unary intrinsic
image. R11 proves closed observer semantics and one-way equality-to-echo lifting, while its crest
observer deliberately collapses unequal pulses. Legacy VAM meanwhile stores raw `Shadow.value`
payloads and accepts `CERT` only after one finite echo execution.

R12 must stop these different statements from being described by the same untyped word
“bridge”. The first slice introduces closed carrier, capability, direction, evidence, scope, and
observation-brand records without modifying any trusted R9–R11 artifact or VAM wire format.

The remaining completion obligations are listed in this document.

## 2. Atomic capabilities and derived directions

A bridge never declares a direction directly. It supplies one exact canonical tuple of atomic
capabilities, and `bridge_direction()` derives the name:

| Direction | Exact capability tuple | Meaning in R12.1 |
|---|---|---|
| `preservation` | `preserves` | the declared source relation maps forward |
| `quotient` | `preserves, collapse-witness` | forward preservation plus an explicit unequal-source/equal-image witness |
| `reflection` | `reflects` | the target relation implies the source relation |
| `faithful` | `preserves, reflects` | both directions on the exact declared carrier |
| `equivalence` | `preserves, reflects, left-round-trip, right-round-trip` | faithful bridge with both checked round trips |

The names are not a total strength ordering. In particular, `quotient` is a many-to-one
classification here, not a synonym for equivalence or generic surjectivity. Unsupported,
duplicated, reordered, and type-confused capability rows fail closed.

## 3. Evidence classes

`EvidenceClass` is a closed disjoint vocabulary:

- `kernel-proof`;
- `formal-bridge`;
- `finite-obligation`;
- `executable-witness`;
- `vam-cert`;
- `shadow`.

Every reference also carries `general` or `finite` scope and a nonempty boundary. Finite
obligations, executable witnesses, and VAM certificates cannot be relabelled general.
A general bridge must include kernel-proof evidence. Even then, R12.1 reports
`promotion_ready=false`: only a separate exact R8 contract may promote a layer.

`formal-bridge` means the pinned formal transport surface, not proof by compilation.
`vam-cert` means the current finite VAM `CERT` acceptance, not a kernel proof.

## 4. Observer-bound response brands

`brand_observation(observer, observation, source)` accepts only an exact R11 `Ready` or
`Blocked` outcome from the R7 recurrence or R9 intrinsic-image carrier. The resulting
`BrandedObservation` binds:

1. schema `veyra.observed-response.r12.1`;
2. exact source carrier;
3. SHA-256 of the canonical closed observer;
4. SHA-256 of its inferred response kind;
5. the exact canonical R11 outcome and its SHA-256 payload digest;
6. one composite digest over the schema, source, observer, kind, and payload digests.

Branding also checks that a `Ready` value has the inferred response shape and that every `Blocked`
path names an actual `tail` site in the observer. This is path validity, not joint reachability of
multiple obstruction paths without the source recurrence. Verification requires the expected
source carrier. Payload/source mutation, kind mismatch, nonexistent obstruction sites, hostile
subclass, circular response kind, resource overflow, raw scalar, and mutable registries are rejected.

The brand is provenance organization over the existing R11 codec. It is not a new mathematical
proof and does not claim that every external value can be reconstructed from a shadow.

## 5. Fixed audited registry

The immutable default registry contains four rows:

| Bridge | Direction | Scope/evidence | Boundary |
|---|---|---|---|
| R7 recurrence → R9 intrinsic image | equivalence | general kernel + formal bridge | fixed-anchor unary image only |
| R7 equality → R11 ready echo | preservation | general kernel + formal bridge | echo does not imply equality |
| R11 crest response | quotient | general kernel + formal bridge | unequal pulses share the pulse crest |
| legacy Core → legacy VAM shadow | preservation | finite executable witness + VAM CERT | bounded compiled subset only |

The registry has deterministic canonical data and digest. Only the four exact audited claims and
their existing evidence identifiers enter that schema; caller-invented kernel IDs or modified rows
are rejected rather than serialized as audited evidence. R12.1 does not replay or replace the
R9/R11 formal bridges.

## 6. Why VAM IR is deferred

Current VAM `BREATH` requires at least one tact and has no anchor field, so it cannot represent
R9 anchored silence. Its `Shadow.value` is an unbranded generic payload. Changing that object or
the VAM0/VAMD report now would invalidate golden reports, optimizer witnesses, Python/Rust
parity, and possibly trusted binding inputs.

R12.2 therefore adds a separate immutable intrinsic sidecar IR for anchor, silence, pulse, mark,
obstruction, and response values before any append-only opcode extension.

## 7. Verification and remaining work

R12.1 acceptance is direct unit/mutation coverage, changed-file Ruff, canonical diff checks, and
execution under the real Sage 10.7 Python environment. No certificate is added yet because this
is not a completed layer: R12.6 will add the certificate and Sage facade only after intrinsic IR,
runtime parity, and the formal bridge exist.

The remaining steps are R12.2–R12.6, followed by a narrow new
`intrinsic-observer-echo` theorem nucleus in R13. Broad `echo` remains a shadow.
