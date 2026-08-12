# Native observer synthesis v4: bounded representation search and replay custody

## Status

This document describes an append-only experimental layer over the frozen
observer-synthesis v1/v2/v3 contracts. It adds executable evidence and narrow
formal models; it does not promote a theorem, a complete observer language, or
a claim of hidden-variable discovery.

## Compatibility boundary

- Existing grammar rows, canonical bytes, profile roots, VORP/VOR2 packages,
  and worker-v3 receipts are unchanged.
- V4 types, roots, wire frames, packages, and binaries use new domain
  separators and versions.
- `FOUND`, `EXHAUSTED`, and `CUTOFF` are relative to the declared finite
  representation, transport, observer, explanation, and cost bounds.
- An optimized result is accepted only when its semantic terminal agrees with
  the independent exhaustive implementation. Engine tags and their enclosing
  receipt digests intentionally remain distinct.

## V3.1 stabilization

The preceding v3 contract now has fixed request, worker-ready, and HMAC replay
vectors plus hostile framing tests. Bounded property checks cover:

- the 24 canonical permutations and all 120 legacy representation images;
- inverse permutation composition;
- exact transport cost, node, and depth frontiers;
- optimized/reference terminals for tasks, profiles, and cutoffs; and
- the child `CUSTODY_PENDING` to parent `READY` transition, including strict
  fail-closed behavior.

These tests freeze the current contract. They do not establish completeness
outside the enumerated cases.

## Representation survey

The v4 survey enumerates a deterministic, finite registry of permutations,
cyclic-affine maps, grouping/quotient maps, and canonical encodings. Each row
has a typed transport term and a declared representation cost. The survey
classifies a row against one exact benchmark task by comparing the induced
equality partitions:

- `REPRESENTATION_STABLE`: the surface equality partition equals the task
  partition;
- `REPRESENTATION_HIDDEN`: the surface partition differs without merging
  distinct target classes; or
- `INFORMATION_DESTROYED`: at least one representation collision crosses a
  target-class boundary.

These labels are exact properties of the declared finite task and surface
observer. They are not causal, ontological, or representation-independent
claims.

## Joint synthesis

The search evaluates the typed chain

```text
representation -> transport -> observer -> explanation
```

under one deterministic total order. Representation and executable transport
costs are separate charged stages; the observer and explanation costs are then
added to form the admitted total. The optimized implementation memoizes
observations inside stable cost buckets, while a separately implemented
exhaustive reference path checks the same declared catalog and primitive
semantics.

`EXHAUSTED` means only that every pair admitted by the declared total-cost and
resource bounds was checked. `CUTOFF` retains the exact counters and does not
become negative evidence. The public benchmark covers a positive hidden case,
a negative control, a representation trap, a family containing
information-destroying quotients, exhaustion, and cutoff.

## Worker v4

The fixed observer-pipeline child exposes three Linux profiles:

| Profile | Required evidence |
|---|---|
| `baseline` | worker-v3 no-new-privileges, RLIMIT CPU/address-space/core, inherited-descriptor boundary, owned process group, bounded output/wall time, parent replay and process-group custody |
| `isolated` | baseline plus fresh user/mount/network/IPC/UTS namespace readback and an installed x86-64 seccomp-BPF allowlist |
| `strict` | isolated plus a caller-delegated cgroup-v2 leaf, exact `cpu.max`, `memory.max`, and `pids.max` readback, parent/child membership checks, empty-leaf check, and removal |

Promotion depends on successful parent and child readback. Merely finding a
kernel feature or writing a configuration never sets an enforced bit. Missing
delegation, unavailable user namespaces, unsupported architecture, mismatched
readback, or failed cleanup blocks the requested profile.

The mount namespace is fresh and made private, but the current profile does not
construct a sealed filesystem image: the host filesystem tree remains visible
subject to the worker's credentials and seccomp policy. The receipt therefore
must not be described as filesystem isolation, a container, executable
attestation, or protection from a hostile worker binary. The executable path
remains a local trust input.

## Autonomous signed replay

VOR4 is a bounded Ed25519-authenticated outer package containing:

- one independently Ed25519-authenticated VOR2 pipeline payload;
- the canonical request and result carried by that payload;
- the derived grammar-registry and transport-set roots;
- a bounded canonical source/toolchain manifest;
- an optional exact worker-v4 receipt digest and profile declaration; and
- a package digest and signature over every field above.

`vam-observer-replay-v4 verify-ed25519 PUBLIC_KEY_HEX` reads one package from
standard input, resolves no producer state, authenticates both layers with the
externally supplied key, and freshly rebuilds the pipeline semantics. Structural
bounds are checked before cryptography; no inner semantic decode is trusted as
valid evidence until outer authentication succeeds.

The public producer API can construct an executed worker-policy row only from
a completed profile-consistent worker-v4 receipt; its executed fields are not
caller-constructible. The portable package intentionally carries the receipt
digest rather than the full operating-system transcript, however, so a remote
verifier authenticates the signer's bounded declaration and digest binding—it
does not independently re-run or attest those Linux controls.

Manifest names and digests are signed declarations. Verification does not
retrieve source files, identify the signer, establish key trust, attest the
worker executable, supply trusted time, prove sandboxing, or convert executable
replay into theorem evidence.

## Lean boundary

`proofs/lean/VeyraObserverSynthesisV4.lean` provides small abstract results for
canonical encode/decode replay acceptance, explicit bijection preservation of a
declared task, and exhaustion of a supplied finite candidate list. The file is
checked under the pinned Lean toolchain and reports no axioms for its named
theorems.

The model does not parse Rust bytes, verify Ed25519, model Linux controls, prove
the concrete registry exhaustive, or verify the Rust implementation.

## Focused verification

Development evidence is intentionally bounded to focused Rust 1.83/current
tests, the pinned Lean source and inventory, Python metadata/documentation
checks, portable build checks, hygiene, LOC, safety scans, and diff integrity.
The multi-hour aggregate `make verify` is not part of this wave.
