# 044 — Discovery-v5 Slice-1 independent checking V1

**Date:** 2026-08-29  
**Status:** proposed documentation contract; no implementation is requested  
**Issue:** [#86](https://github.com/Justsomebuddy/veyra/issues/86)  
**Future utility:** out-of-tree `discovery-v5-slice1-reference` only

## Problem

Discovery-v5 already has canonical raw request/result codecs, an in-tree proof verifier, and separately versioned VOR5 threshold-authenticated replay. The narrow external boundary is an optional package that allows an independent checker to consume **exact canonical request and result bytes**, bind them to a frozen finite profile/catalog and declared coverage, and return a bounded verdict.

This contract is not a production-search change, a replacement for the native verifier, a VOR5 change, or a provenance/authentication design. It is a typed, versioned, fail-closed interface for a future out-of-tree reference utility.

## Normative V5 source pin

This proposed V1 contract is defined against source commit
[`c6287a513ac82092de61f23ac792d3c0e5177dd4`](https://github.com/Justsomebuddy/veyra/tree/c6287a513ac82092de61f23ac792d3c0e5177dd4).
Its normative production surfaces are
[`synthesis_v5.rs`](https://github.com/Justsomebuddy/veyra/blob/c6287a513ac82092de61f23ac792d3c0e5177dd4/vam/native/src/observer_synthesis/synthesis_v5.rs)
(schema, canonical six-field request codec, canonical twenty-three-field result
codec, result boundary, search, and proof-verifier entry),
[`grammar_v5.rs`](https://github.com/Justsomebuddy/veyra/blob/c6287a513ac82092de61f23ac792d3c0e5177dd4/vam/native/src/observer_synthesis/grammar_v5.rs)
(finite profile/catalog enumeration, cost, order, and pins), and
[`discovery_benchmark_v5.rs`](https://github.com/Justsomebuddy/veyra/blob/c6287a513ac82092de61f23ac792d3c0e5177dd4/vam/native/src/observer_synthesis/discovery_benchmark_v5.rs)
(benchmark/task reconstruction and splits). The pinned roots are
`profile_root = 787b4f3b9538f6861a0490ca5d3c89177f4579fc001c35de2d3c358fee1611ba`
and
`catalog_root = cb691d7892fa3235984538c3becd746109d112a597f1a6be52a364011543b7a7`.

This source pin makes the finite V1 interpretation reproducible; it does not
authenticate source provenance, toolchains, execution history, or a future
repository state.

## Compatibility boundary

The existing V5 request/result codecs, grammar/catalog, optimized search, exhaustive verifier, VOR5 framing and trust policy, CLI, public APIs, result roots, errors and limits remain unchanged. This document adds no request/result field and does not ask existing Rust code to emit the container below.

`request.bin` and `result.bin` must each end exactly at the last byte of their
canonical V5 encoding: NUL-separated fields with no terminator, six fields for
the request and twenty-three for the result. Any additional byte rejects even
when the record header, `request_len`/`result_len`, and SHA-256 are recomputed
to cover that byte.

The report linked from [issue #86](https://github.com/Justsomebuddy/veyra/issues/86)
records the original five-package external run as feasibility evidence only. It
is not published conformance evidence for this new container or for the future
public vector requirements/specification.

## Slice1ContainerV1

The wire object is one uncompressed byte sequence, not a directory, tar, zip, JSON envelope, or filesystem bundle. Its first four bytes are ASCII `VSL1`. It then contains exactly three length-prefixed records, in this exact order:

1. logical member name `slice1-contract.json`;
2. logical member name `request.bin`;
3. logical member name `result.bin`.

Each record is:

```text
u8(name_byte_length) || ASCII(name) || u32be(payload_byte_length) || payload
```

The names and name lengths must be exactly the three names above. The whole container must have byte length exactly

```text
4 + Σ(1 + name_byte_length + 4 + payload_byte_length)
```

for those three records. Compression, directory entries, headers other than `VSL1`, timestamps, permissions, duplicate names, renamed names, reordered records, padding, metadata records, and every byte after `result.bin` are forbidden. `slice1-contract.json` is at most 4,096 bytes; `request.bin` is at most 1,024 bytes; `result.bin` is at most 8,192 bytes.

This fixed binary layout exists so two checkers cannot disagree about paths, archive metadata, record order, unconsumed padding, or which bytes a SHA-256 actually names.

## Canonical `slice1-contract.json`

The first payload is UTF-8 JSON without BOM or whitespace outside strings.
Object keys are ASCII and appear in bytewise lexicographic order. Duplicate and
unknown keys reject. Every JSON string value and every object key is an exact
fixed identifier, an enum value from an explicit allowed-value table below, or
a digest matching exactly `[0-9a-f]{64}`. Escape sequences, every
non-ASCII/Unicode code point, floats, booleans, `null`, arrays, unknown fields,
and implicit defaults are forbidden. A numeric value is a JSON non-negative
integer `0` or `[1-9][0-9]*`, must fit `u64`, and has no sign, exponent,
fraction, or leading zero.

The top-level object has exactly these keys:

```text
catalog_root, coverage, format_id, nonclaims_id, profile_root,
request_len, request_sha256, result_len, result_sha256, semantic_model_id
```

`format_id` is exactly `veyra.discovery-v5.slice1-contract.v1`; `nonclaims_id` is exactly `veyra.discovery-v5.slice1-nonclaims.v1`; and `semantic_model_id` is exactly `veyra.discovery-v5.slice1-semantic-model.v1`. `request_sha256`, `result_sha256`, roots and every digest are exactly `[0-9a-f]{64}`. `request_len` and `result_len` must equal both their record headers and actual payload lengths; their SHA-256 fields must equal the actual raw payloads.

`profile_root` must equal the independently decoded result `grammar_profile_digest`; `catalog_root` must equal the independently decoded result `catalog_digest` and the checker’s own reconstruction of the frozen catalog. They identify only the declared finite profile/catalog; they do not authenticate source, toolchain, signer, custody, chronology, or historical event.

## Semantic model and declared coverage

`semantic_model_id` is exactly `veyra.discovery-v5.slice1-semantic-model.v1`. It normatively names this complete fixed model:

1. the strict canonical request/result parser, including UTF-8, NUL framing, integer, field-count and canonical-reencoding rules;
2. the discovery-v5 response equations over the fixed finite state domain;
3. the profile/catalog enumeration and root reconstruction;
4. the intrinsic cost rule and cost-admission predicate `candidate.cost <= maximum_total_cost`;
5. the `(intrinsic cost, catalog ordinal)` order and tie-break rule;
6. benchmark/task reconstruction: generator selection, represented-state and
   target construction (including the `misrepresentation-recovery-v5`
   `5*s+3 mod 16` state map), split assignment, and
   `benchmark_digest = SHA256(domain || 0x00 || task_body)` in its pinned
   domain;
7. the exact canonical-partition equality relation between represented
   candidate responses and generated targets; and
8. ledger, winner, same-cost-alternative, lower-bound, prune-proof, and
   domain-separated digest derivations that the checker validates.

An implementation may not silently add an evaluator, grammar, order, cost, parser, or normalization assumption to that identifier. The identifier makes shared semantic assumptions reviewable; it does not prove them true.

`coverage` is the sole nested object and has exactly these ASCII-ordered keys:

```text
admitted_domain, benchmark_digest, benchmark_id, benchmark_split,
candidate_limit, catalog_root, claim, coverage_format_id,
maximum_total_cost, order_and_tiebreak_rule, pair_disposition_limit,
profile_id, profile_root, terminal_status
```

`coverage_format_id` is exactly `veyra.discovery-v5.slice1-coverage.v1`; `admitted_domain` is exactly `cost-lte-maximum-total-cost.v1`; and `order_and_tiebreak_rule` is exactly `intrinsic-cost-then-catalog-ordinal.v1`. The duplicate profile/catalog roots must equal the top-level values. Benchmark values, profile ID, digests, limits and maximum cost must equal the independently decoded raw request/result and the independently reconstructed finite model.

The enum fields have no extension point in V1:

| Field | Exact allowed value(s) |
|---|---|
| `benchmark_id` | `hidden-affine-v5`, `reflection-symmetry-v5`, `misrepresentation-recovery-v5`, `diagonal-negative-control-v5`, `held-out-affine-v5` |
| `benchmark_split` | `CALIBRATION`, `SYNTHETIC_HELD_OUT` |
| `profile_id` | `affine-parity-reflection-v5` |
| `admitted_domain` | `cost-lte-maximum-total-cost.v1` |
| `order_and_tiebreak_rule` | `intrinsic-cost-then-catalog-ordinal.v1` |
| `terminal_status` | `FOUND`, `EXHAUSTED`; reserved raw V5 value `CUTOFF` is rejected as `REJECT_CUTOFF_NOT_ACCEPTED` |
| `claim` | `FOUND_MINIMUM_UNDER_DECLARED_BOUND`, `EXHAUSTED_COST_ADMITTED_CATALOG_UNDER_DECLARED_REQUEST` |

`benchmark_digest`, `profile_root`, and `catalog_root` are exactly `[0-9a-f]{64}`. `candidate_limit`, `maximum_total_cost`, and `pair_disposition_limit` are canonical `u64` JSON integers. Thus a coverage declaration has one parser-visible type for every field; it is not arbitrary producer metadata.

The only accepted terminal pairs are:

| `terminal_status` | `claim` |
|---|---|
| `FOUND` | `FOUND_MINIMUM_UNDER_DECLARED_BOUND` |
| `EXHAUSTED` | `EXHAUSTED_COST_ADMITTED_CATALOG_UNDER_DECLARED_REQUEST` |

`CUTOFF` is never an acceptance vector. `EXHAUSTED` does not mean that another profile, another cost bound, or the unrestricted catalog is exhausted.

## Reference-checker contract

The future checker must process the container before semantic work and return
only `ACCEPT_EXACT_SLICE1_V1` or one member of `RejectClassV1`. It must fail
closed for every malformed or unsupported container input. `ACCEPT` requires
`result.bin` to decode as the **optimized** (`optimized=true`) V5 result.
An exhaustive-reference result for the same request is a valid raw V5 value,
but is not a Slice-1 acceptance vector because its ledger is not the optimized
branch-and-bound ledger.

## RejectClassV1

`RejectClassV1` is the complete finite V1 set of stable **byte-level container verdicts**:

```text
REJECT_UNKNOWN_IDENTIFIER
REJECT_MISSING_REQUIRED
REJECT_DUPLICATE
REJECT_CONTAINER_LAYOUT
REJECT_MEMBER_NAME
REJECT_MEMBER_ORDER
REJECT_MEMBER_BINDING
REJECT_REQUEST_TRAILING_BYTES
REJECT_RESULT_TRAILING_BYTES
REJECT_RAW_CODEC
REJECT_ROOT_BINDING
REJECT_COVERAGE_BINDING
REJECT_CUTOFF_NOT_ACCEPTED
REJECT_EXHAUSTION_SCOPE
REJECT_CLAIM_BINDING
```

The checker applies the following normative first-failure-wins order. A vector
with several faults receives the earliest applicable class, not a later class
that might also describe it.

1. Parse the `VSL1` framing and records sequentially. A malformed magic,
   length prefix, or record framing is `REJECT_CONTAINER_LAYOUT`; EOF before a
   required record is `REJECT_MISSING_REQUIRED`; an unknown record name is
   `REJECT_MEMBER_NAME`; a repeated known record name is `REJECT_DUPLICATE`; a
   known, non-repeated name in the wrong position is `REJECT_MEMBER_ORDER`; and
   any fourth record or byte after record three is `REJECT_CONTAINER_LAYOUT`.
2. Parse `slice1-contract.json` strictly. A duplicate JSON key is
   `REJECT_DUPLICATE`; malformed/noncanonical JSON or an invalid JSON encoding
   is `REJECT_RAW_CODEC`; a missing required field is
   `REJECT_MISSING_REQUIRED`; an unknown JSON key, unknown fixed identifier, or
   unknown non-reserved enum value is `REJECT_UNKNOWN_IDENTIFIER`.
3. Compare record headers, declared lengths, and declared SHA-256 values with
   the three actual payloads. A mismatch is `REJECT_MEMBER_BINDING`.
4. Check raw canonical boundaries before ordinary raw decoding. Re-encode
   `request.bin` from the coverage-declared request fields; if `request.bin`
   has that exact canonical encoding as a strict prefix, return
   `REJECT_REQUEST_TRAILING_BYTES`. For `result.bin`, the fixed final V5
   boundary string delimits the canonical result; a canonical result prefix
   followed by any byte is `REJECT_RESULT_TRAILING_BYTES`.
5. Decode and canonical-reencode the remaining raw request/result values. Any
   failure of UTF-8, NUL field count, integer, field, canonicality, or raw V5
   binding rules is `REJECT_RAW_CODEC`.
6. Rebuild and compare profile/catalog roots. A mismatch is
   `REJECT_ROOT_BINDING`.
7. Bind coverage to the decoded request/result and finite model. A reserved
   raw V5 terminal status `CUTOFF` is
   `REJECT_CUTOFF_NOT_ACCEPTED`; all other undeclared or inconsistent coverage
   is `REJECT_COVERAGE_BINDING`.
8. Reconstruct the exact admitted domain and terminal claim. An `EXHAUSTED`
   result whose ledger does not cover that domain is
   `REJECT_EXHAUSTION_SCOPE`; any other false `FOUND`/`EXHAUSTED` minimum,
   fit, winner, or alternatives assertion is `REJECT_CLAIM_BINDING`.

No additional V1 `REJECT_*` class is available for checker implementation
review.

It must parse raw bytes itself and must not import the production decoder,
evaluator, optimized search, exhaustive/reference search, or native verifier
as an oracle. It must independently rebuild the declared profile/catalog,
response semantics, cost/admission domain and order/tie-break rule; bind the
request/task/limits and result ledger/winner/status to `coverage`; and then
establish the declared bounded claim. A full finite scan is permitted and is
the intentional honest cost of Slice-1.

Every `result.bin` byte is bound by `result_sha256`, but no semantic result
field is accepted by SHA-256 alone. The checker independently re-derives and
checks `optimized`, terminal status/detail, every ledger scalar and its
lower-bound/prune-proof digests, all winner fields (including ordinal, cost,
fit and same-cost alternatives), benchmark digest/split, profile/catalog
roots, maximum cost, and the fixed boundary. The SHA-256 values are only raw
member-integrity bindings for `request.bin` and `result.bin`; they do not
establish any of those semantic facts.

| Rule | What it prevents |
|---|---|
| Exact named record layout, order and terminal length | Archive, path, rename, reorder, metadata and padding ambiguity. |
| Canonical JSON, fixed keys and types | Parser-dependent duplicate/unknown/default, numeric and serialization ambiguity. |
| Header plus declared length/SHA-256 | Truncation, splice, substituted member and declared-versus-actual byte mismatch. |
| Exact request/result canonical re-encoding | A valid prefix followed by hidden trailing bytes. |
| Result-decoded plus independently reconstructed roots | Producer-declared profile/catalog root substitution. |
| Typed coverage and independently checked claim with an exact admitted domain | A bare result being silently promoted to a broader or false claim. |
| Normative `semantic_model_id` contents | Silent addition or replacement of parser/response/catalog/cost/order assumptions. |
| Independent reconstruction without production imports | Circular acceptance because the checker delegates its judgment to a production oracle. |

## Future public vector requirements/specification

This proposal specifies the required future public vector classes below; if it
is accepted, those V1 requirements become fixed. It does not publish a binary
fixture corpus or run a conforming checker. A future out-of-tree checker
milestone must publish a positive container plus its exact byte identity and
the required byte-level vectors. A historical five-package feasibility result is described in
[issue #86](https://github.com/Justsomebuddy/veyra/issues/86); it is not this
conformance evidence.

Each future published construction must be arranged so its required stable
result is the first applicable failure under the precedence above. A composite
malformed input may correctly receive an earlier class instead.

| ID | Mutation or positive construction | Required stable result | Source of truth | False acceptance excluded |
|---|---|---|---|---|
| S1-B-001 | One complete `VSL1` container whose three payloads and declared coverage independently agree | `ACCEPT_EXACT_SLICE1_V1` | Contract §§ Slice1ContainerV1–Reference-checker | Accepting a shape-only container without the declared byte/root/coverage bindings. |
| S1-B-002 | Unknown `format_id`, `nonclaims_id`, `semantic_model_id`, or `coverage_format_id` | `REJECT_UNKNOWN_IDENTIFIER` | Contract canonical JSON/semantic model | Silent semantic-version or nonclaim widening. |
| S1-B-003 | Absent required record or JSON field | `REJECT_MISSING_REQUIRED` | Contract layout and field set | Defaulted identity, root or coverage. |
| S1-B-004 | Duplicate record or duplicate JSON key | `REJECT_DUPLICATE` | Contract layout and JSON rules | Parser-dependent duplicate selection. |
| S1-B-005 | Extra record, directory/header/metadata record, padding or byte after final payload | `REJECT_CONTAINER_LAYOUT` | Contract container exact-length rule | Hidden metadata, archive ambiguity or uncommitted trailing data. |
| S1-B-006 | Rename any logical member | `REJECT_MEMBER_NAME` | Contract fixed names | Role substitution by path/name. |
| S1-B-007 | Reorder contract/request/result records while retaining otherwise valid payloads | `REJECT_MEMBER_ORDER` | Contract fixed order | Role substitution by record position. |
| S1-B-008 | Header length, contract `request_len`/`result_len`, or SHA-256 does not match payload | `REJECT_MEMBER_BINDING` | Contract member binding | Truncation, splice, substituted or padded payload. |
| S1-B-009 | Append a byte to `request.bin` after the coverage-declared canonical request encoding; recompute its record header, `request_len`, and `request_sha256` over the extended payload | `REJECT_REQUEST_TRAILING_BYTES` | Current request canonicality and contract | Prefix-only acceptance / hidden request suffix. |
| S1-B-010 | Append a byte to `result.bin` after its canonical encoding; recompute its record header, `result_len`, and `result_sha256` over the extended payload | `REJECT_RESULT_TRAILING_BYTES` | Current result canonicality and contract | Prefix-only acceptance / hidden result suffix. |
| S1-B-011 | Invalid UTF-8, wrong NUL field count, noncanonical integer or noncanonical re-encoding | `REJECT_RAW_CODEC` | Current V5 codecs | Cross-parser and framing disagreement. |
| S1-B-012 | Mutate declared or decoded profile/catalog root | `REJECT_ROOT_BINDING` | Current result root fields and independent model | Foreign profile/catalog substitution. |
| S1-B-013 | Change a present coverage field without corresponding raw/model evidence | `REJECT_COVERAGE_BINDING` | Contract coverage object | Bare result promoted to undeclared claim. |
| S1-B-014 | Container declares terminal `CUTOFF` | `REJECT_CUTOFF_NOT_ACCEPTED` | Current V5 boundary | Resource stop treated as negative/complete evidence. |
| S1-B-015 | For `diagonal-negative-control-v5`, construct a canonical, fully rebound `EXHAUSTED` result whose ledger omits one independently reconstructed cost-admitted candidate | `REJECT_EXHAUSTION_SCOPE` | Current V5 definition | An incomplete traversal promoted to cost-bounded exhaustion. |
| S1-B-016 | Construct a canonical, fully rebound `FOUND` result with a non-minimum/non-fitting winner or wrong same-cost alternatives count | `REJECT_CLAIM_BINDING` | Independent response/cost/order reconstruction | Hash-consistent but false minimum claim. |

## Reference-checker conformance and implementation audit

The checks in this section are **not properties of an input VSL1 container**. They are evaluated by source/import review and by independent checker-mutation tests. They do not have to return `RejectClassV1` for one parsed package, and they establish neither source authenticity nor universal semantic correctness.

At the out-of-tree checker milestone, S1-A-001 and S1-A-002 must each name a
published finite mutation list. Every listed mutation must identify its altered
rule and a published byte-level vector that exposes the changed checker
behavior. This is conformance evidence for a particular checker version, not a
new `RejectClassV1` reason and not a general semantic-correctness proof.

| ID | Audit subject | Required audit result | What failure would show |
|---|---|---|---|
| S1-A-001 | Mutate an independent parser, response equation or catalog-reconstruction rule covered by `semantic_model_id` | Mutation test or independent comparison must expose changed behavior; otherwise conformance audit fails | The checker can silently use a different semantic model. |
| S1-A-002 | Mutate intrinsic cost, cost-admission or order/tie-break rule | Mutation test or independent comparison must expose changed coverage/winner behavior; otherwise conformance audit fails | The checker can accept the same bytes under a different minimization relation. |
| S1-A-003 | Inspect imports/TCB and attempt a pre-parsed Rust-object handoff | Review must show no production decoder/evaluator/optimized search/reference search/native-verifier oracle and no pre-parsed object input; otherwise conformance audit fails | Circular producer/verifier agreement. |

## Positive-vector evidence requirements

`S1-B-001` is valid only when all of the following are public and exact:

1. the complete three-record container bytes and SHA-256;
2. source SHA, source paths and exact V5 codec/model references;
3. the expected `ACCEPT_EXACT_SLICE1_V1` verdict and bounded checker version/source digest;
4. exact request/result payload lengths and SHA-256 values;
5. profile/catalog roots and all declared coverage fields.

The requirements above become an actual public fixture corpus only at the next
separate out-of-tree checker milestone. The feasibility evidence described in
[issue #86](https://github.com/Justsomebuddy/veyra/issues/86) does not contain
`Slice1ContainerV1` and does not prove that every byte-level vector or
implementation audit above already exists or passes.

For avoidance of doubt, `maximum_total_cost = 1` is a valid request whose
cost-admitted domain is empty because the frozen catalog minimum cost is `2`.
Production returns `EXHAUSTED` for that request. A conforming checker accepts
that **vacuous** `EXHAUSTED` only when all other V1 bindings hold; it is not an
`REJECT_EXHAUSTION_SCOPE` vector. S1-B-015 instead uses a nonempty admitted
domain and an incomplete `EXHAUSTED` ledger, so its first failure is uniquely
`REJECT_EXHAUSTION_SCOPE` rather than `REJECT_COVERAGE_BINDING`.

## Non-claims and stops

Slice-1 establishes neither general Veyra correctness; catalog completeness outside its exact frozen profile and declared cost-admission domain; source/toolchain authenticity; signer identity, key rotation, epoch or threshold policy; provenance, custody, execution history or Linux attestation; VOR5 authentication; theoremhood; novelty; nor production readiness.

Stop and redesign if the contract requires a production-code change, a VOR5 policy change, a pre-parsed Rust object, a production semantic oracle, a nondeterministic/metadata-bearing container, unknown-field tolerance, acceptance of padding or trailing raw bytes, a `CUTOFF` acceptance result, or a broader claim than the declared finite coverage.

## Publication scope

This is a documentation-only contract. The first checker remains out of tree. Any runtime implementation, production integration, VOR5 certificate kind, authentication design, or source modification requires a separate proposal and review.
