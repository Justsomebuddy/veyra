# VAM v1.6 — VAMD optimizer policy and generated parity corpus

**Status:** implemented bounded checkpoint.
**Scope:** policy for VAMD optimizer handling plus the generated parity corpus used as bounded regression evidence.

## Purpose

VAM v1.6 defines how the native optimizer surface treats VAMD inputs and how generated parity cases are interpreted.

The intended pipeline remains conservative:

```text
VAMD frame -> Rust decoder -> semantic optimizer report analysis -> Rust executor -> semantic report
```

The checkpoint is about semantic report parity and boundary clarity. It is not a performance milestone and does not introduce a proof-grade optimizer result.

## VAMD optimizer policy

VAMD optimizer support is policy-bounded:

- accepted VAMD inputs are decoded and executed for semantic report parity;
- optimizer-visible analysis reports semantic optimizer effects only when the implementation has enough information to do so safely;
- JSON reports expose `input_magic` plus `optimizer_boundary: decoded-ir-report-only`;
- unsupported, malformed, or ambiguous optimizer paths must reject or fall back to unoptimized semantic execution according to the existing input contract;
- Python oracle reports remain the comparison target for optimizer rows and canonical semantic reports;
- any optimizer row emitted for VAMD must preserve obstruction and diagnostic visibility.

The safe default is no rewrite. A VAMD case that cannot be modeled exactly must not be treated as optimized.

## No optimized VAMD frame yet

The v1.6 boundary is explicit:

- the optimizer report is semantic only;
- no optimized VAMD binary frame is claimed;
- no optimized VAMD payload bytes are part of this checkpoint;
- downstream code must not assume that a semantic optimizer report can be serialized back into an optimized VAMD frame.

Optimized VAMD frame emission requires a later, separately specified contract covering binary layout, CRC behavior, frame metadata, and parity fixtures for the emitted bytes.

## Generated parity corpus

`tests/vam/test_vam_native_optimizer_generated.py` is a bounded regression corpus for comparing native and Python behavior on selected shapes.

It may cover cases such as:

- VAMD frame decoding and semantic execution;
- duplicate observer or compression shapes;
- same-observer idempotent compression;
- dead-shadow-like local rows;
- obstruction-preserving cases;
- malformed or unsupported boundary fixtures.

Corpus expectations:

- Python and native semantic reports should match on accepted cases;
- optimizer rows should match the Python oracle where optimizer analysis is in scope;
- unsupported cases should fail or remain unoptimized in a documented way;
- generated cases should remain deterministic and reproducible enough for regression use;
- corpus metadata should identify the generator profile or fixture family when available.

## Evidence boundary

Generated parity is evidence for the bounded fixture families only.

It is not:

- a formal proof of optimizer correctness;
- a complete VAMD semantic equivalence theorem;
- evidence that all byte sequences or all generated programs are covered;
- a replacement for Python oracle comparison;
- a claim that optimized VAMD frames exist.

Passing generated parity cases means the tested native path agrees with the oracle on those cases. It does not prove equivalence outside the corpus.

## Non-claims

VAM v1.6 explicitly does **not** claim:

- proof-grade optimizer correctness;
- a full native VAMD optimizer;
- optimized VAMD frame emission;
- speedup or performance improvement;
- replacement of the Python oracle;
- coverage of every VAMD byte sequence or every lowering path.

Timing output from any harness remains operational metadata unless a later benchmark contract defines a performance claim.

## Acceptance checklist

Treat the v1.6 boundary as satisfied only when:

- VAMD semantic reports match Python on targeted accepted fixtures;
- optimizer rows, when emitted, match the Python oracle for the same fixture family;
- unsupported optimizer inputs are rejected or left unoptimized as specified;
- obstruction and diagnostic rows remain visible after any semantic optimizer analysis;
- generated parity results are described as bounded evidence, not proof;
- documentation and CLI text avoid speed, proof, and optimized-frame claims.
