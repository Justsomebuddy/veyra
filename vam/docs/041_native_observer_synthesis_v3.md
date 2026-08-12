# Native observer synthesis v3: registry, transport programs, replay, and custody

**Status:** bounded Rust implementation and abstract Lean research slice.  
**Claim class:** finite executable calibration; no hidden-variable, optimality,
sandbox, implementation-proof, signer-identity, or general discovery claim.

## 1. Append-only grammar registry

The registry chains immutable profile descriptors rather than extending a
caller-matchable public primitive enum. Its first two rows are the already
published legacy and parity profiles. Each row binds its ordinal, parent,
introduction label, immutable lifecycle state, profile/catalog identities,
exact candidate and byte counts, and the preceding row digest. Prefix roots
allow a verifier to identify the exact catalog prefix it understood. Adding a
future grammar therefore requires a new profile key, schema/domain, catalog and
appended row; it must not renew old profile/catalog bytes. The v3 registry root
itself is new and intentionally includes this lifecycle metadata.

Current full registry root:

```text
f937c322be2fd20933a32993d5549009fbac6c23f80cae16964cdaaf653af8b5
```

The one-row legacy prefix remains separately pinned at
`6ea628f5924b82a2cb89b402beb08d762c4716ae2d4044ade3ceb21062bfdc0c`.
Registry inclusion establishes neither semantic completeness nor scientific
adequacy.

## 2. Typed finite transport DSL

The closed DSL represents identity, relabeling, bounded shift embedding,
projection, grouping, canonical finite encoding, and recursive composition.
Composition is precharged before compilation and is capped at depth 16, 32
total AST nodes, arity 32, and accumulated cost 32. Ordered child roots, exact
domain chaining, the final image, and accumulated cost are digest-bound.
Canonical table literals cost `1 + rows`, so they cannot masquerade as a
one-step semantic primitive. These costs are a declared program-size proxy,
not a universal semantic-distance measure. Compilation derives a complete
image table and mechanically classifies it:

- relabeling must be a whole-domain permutation;
- projection must be a monotone surjection onto a strictly smaller domain;
- grouping may be a non-monotone surjection, but also requires a strictly
  smaller target;
- shift embedding is the declared arithmetic injection; arbitrary remaining
  tables use the charged canonical-encoding form.

- **bijection:** exact inverse on the whole target;
- **injection:** a left inverse exists only on the image;
- **loss:** at least one collision, published with a collision witness.

Callers cannot assert the class. A second, separate task-transport receipt
checks the explicit finite commuting square. Even a bijection does not by
itself prove that task labels are preserved. Conversely, a lossy grouping may
commute for one task but cannot license representation equivalence. An adapter
reproduces all 120 published shift/permutation images without changing any v2
family bytes or roots.

## 3. Optimized/reference differential search

The v3 engine searches the direct product of only the caller-declared compiled
transport programs and the selected registered observer catalog. Candidates
are ordered by the unified `transport cost + observer cost`, then stable
ordinals. The optimized implementation builds stable cost buckets and memoizes
the four observations for each pair; the independent oracle uses direct echo
comparisons over the six obligations with a logical six-obligation precharge.
Their complete terminal results are compared.
An optimized `EXHAUSTED` result is admissible only when the reference engine
also exhausts the same closed product. Internal evaluation strategy may differ;
task, profile, catalog, declared transport set, status, cutoff frontier,
logical counter ledger and complete winner identity may not.

This first optimization is deliberately conservative. It is evidence about
semantic agreement on the declared finite cases, not a complexity theorem or
speed claim.

## 4. Observer-gap laboratory and typed pipeline

The laboratory records an integer vector rather than collapsing evidence into
one unexplained score: baseline/candidate obligation hits, response-class
savings, transform cost, observer cost, explanation cost, and information-loss
penalty. Positive and negative controls are generated deterministically. A
lossy transform cannot become a positive hidden-structure witness merely by
collapsing classes.

The atomic pipeline is:

```text
normalize -> transport -> observer -> explanation -> aggregate
```

Every stage binds its predecessor, output, logical limits and cost. The observer
stage directly selects from the declared transport set; it does not search a
legacy family and filter the winner afterwards. The selected transport's
mechanically derived collision count supplies the information-loss penalty;
caller-supplied nonzero penalties are rejected. A lossy selected transport can
complete as `READY/NO_GAP`, but cannot mint a positive gap, even when the
legacy policy's loss-acknowledgement flag is set. Only a complete
aggregate can be `READY`; a cutoff or obstruction exposes a failed stage and
audit root, never a partial positive witness. This remains a named finite
benchmark laboratory, not causal discovery, holdout evidence, or a general
hidden-variable theorem.

## 5. Replay bundle v2

VOR2 is a new bounded wire version; VORP v1 remains byte-for-byte unchanged.
V2 authenticates a payload-kind tag, exact request/result bytes, algorithm, key
identifier and authenticated label under distinct domains. It supports the
legacy worker-v1 payload and the canonical observer-pipeline-v3 payload, HMAC-
SHA256 for shared-key deployments, and Ed25519 for public verification.
Authentication is checked on bounded raw canonical bytes before semantic
parsing. Pipeline replay then decodes the bounded recursive DSL, performs a
fresh deterministic in-process pipeline rebuild, and compares the complete
canonical result bytes. This comparison is mandatory even when the legacy
worker policy disables its optional fresh-artifact check, because v3 has no
weaker result-decoding mode. That rebuild is not physical worker re-execution.

The verifier receives an external trust policy and key resolver. Key IDs and
labels are metadata, not identity; public keys and trust anchors are not
self-authorizing bundle content. A valid Ed25519 signature proves possession of
the corresponding private key for those bytes, not signer trust, chronology,
source truth, or theoremhood. HMAC remains shared-key integrity. Decoding from a
reader checks the declared bound before allocation and exact-file decoding
rejects trailing data.

The independent public-key verification path reads exactly one VOR2 frame from
standard input and accepts only the externally supplied Ed25519 key:

```bash
vam-observer-replay verify-ed25519 PUBLIC_KEY_HEX < bundle.vor2
```

It emits only `verified` on success or a static blocked reason on failure; it
does not read a private key or authorize the label embedded in the bundle.

## 6. Worker v2 controls and worker v3 custody

Worker v2 reports each physical control as `ENFORCED`, `AVAILABLE`,
`NOT_REQUESTED`, `UNAVAILABLE`, `UNSUPPORTED_PLATFORM`, or `FAILED`. A Linux
baseline child sets and reads back RLIMIT CPU/address-space/core,
no-new-privileges, an owned process group and the inherited-FD boundary.
Parent-owned wall/output custody remains merely `AVAILABLE` and the child ends
at `CUSTODY_PENDING`, never self-authorized `READY`. Strict mode requires
verified delegated-cgroup, namespace and pinned-seccomp controls; the current
implementation blocks because all three are not verified rather than silently
weakening isolation. Codec/authentication remains portable, while physical
execution on unsupported systems is truthfully blocked.

No worker receipt attests arbitrary executable provenance. An optional cgroup
path is trusted launch input outside the replay wire, but mere path existence
or process membership remains only `AVAILABLE`: limit ownership is not proved.
Optional cgroup, namespace or seccomp controls are never marked enforced from
configuration alone; setup/readback/cleanup must succeed before parent
promotion. This is a bounded local custody protocol, not a VM, remote
attestation, or universal sandbox.

Worker v3 connects those controls to the canonical v3 pipeline. Its fixed
name is checked, but its caller-supplied executable path remains trusted launch
input rather than binary attestation. Before `exec`, the Linux parent marks
every descriptor above standard error close-on-exec; the child then independently
audits the complete post-exec descriptor table. The child accepts only the
bounded canonical request, applies and reads back the baseline Linux controls,
executes the pipeline, and emits only
`CUSTODY_PENDING`. The parent drains concurrently under exact output and wall
limits, signals the owned process group, reaps its leader, checks child control
and digest bindings, freshly rebuilds the request/result, and only then returns
`READY`.
The final parent receipt digest also binds the wall and output ceilings. Strict
worker-v3 execution remains blocked until real cgroup-v2, seccomp and namespace
enforcement is implemented and verified.

## 7. Lean boundary

`VeyraObserverSynthesisV3.lean` proves four axiom-free abstract results:
canonical acceptance implies exact rebuild equality; an explicit bijection
commutes with a pulled-back task; and optimized acceptance/exhaustion transfer
to the reference engine only under an explicit whole-result equality witness.
It does not formalize the Rust implementation, hashes, signatures, system
calls, concrete catalogs, or benchmark results.

## Verification boundary

The development gate is limited to focused Rust unit/integration/property and
MSRV checks, the pinned Lean graph, focused Python inventory/docs tests,
portable CI, hygiene, public-content scanning and diff integrity. The multi-hour
`make verify` is intentionally excluded unless separately requested.
