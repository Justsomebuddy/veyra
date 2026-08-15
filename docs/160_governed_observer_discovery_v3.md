# 160 — Governed Observer Discovery Phase III

## Status and separation

`src.core.observer_discovery_v3` is a separate experimental protocol package.
It does not replace or silently strengthen the Phase-I/II APIs described in
documents 157–159. The package root exports nothing; public names are exposed
through its narrow `schema`, `transport`, `dsl`, `ledger`, `service`, `replay`,
`lineage`, and `ingestion` subpackages or the explicit `worker.runtime` module.

Phase III adds bounded engineering controls around canonical representations,
closed observers, local one-shot governance, and authenticated evidence roots.
It does **not** add a theorem, certificate-registry entry, proof artifact,
ontology promotion, release-version increment, or new conclusion for an
existing Phase-II discovery or confirmation receipt.

The v3 package does not implement a replacement search, reranking, or
statistical-confirmation engine. Its governed service evaluates a caller-
supplied frozen closed-term suite and records that evaluation under narrower
controls.

The strongest honest description is:

> A finite, canonical, locally governed observer experiment can bind declared
> data and program roots, burn one cooperating-process capability before
> evaluation, execute a closed observer in a bounded logical subprocess, check
> declared representation commuting squares on the supplied rows, and emit a
> root-only authenticated audit receipt.

Every phrase in that statement is scoped below.

## 1. Canonical representation schema

The strict schema accepts only frozen, slotted records with:

- one nonempty schema identifier;
- at most 32 explicitly ordered `binary` or `categorical` fields;
- finite typed categories (`str`, `int`, or `bool`), with binary domains exactly
  the integer pair `(0, 1)`;
- at most 8192 rows per presentation and 262144 retained feature cells;
- bounded UTF-8 text and bounded integers;
- explicit row, source, content, and group identities.

Canonicalization detaches caller values and binds separate schema and ordered
payload digests. A presentation requires unique row identities, one target per
group, at least two groups, equal group sizes, and source/content identities
that do not cross groups. A three-way presentation additionally requires one
schema and pairwise-disjoint row, source, content, and group identities across
train, validation, and declared test partitions.

These are structural checks over caller declarations. They do not prove source
fidelity, sampling validity, target exclusion, exchangeability, historical
label secrecy, observer admission, explanation, or object formation.

The strict schema has no Phase-II dependency. The optional
`schema.phase2_compat` module is deliberately quarantined: it can export
detached Phase-II row objects, but doing so establishes no locked-test custody,
isolation, E4 status, or claim promotion.

### 1.1 Explicit categorical byte ingestion

The separate non-root `ingestion` facade converts strict CSV or JSONL byte
payloads into the existing `ThreeWayPresentation`; it does not define another
schema, row, presentation, receipt, or digest contract. The caller supplies the
exact `RepresentationSchema` and separately names the `train`, `validation`,
and `test` byte payloads. Those three arguments are the complete split
declaration: no column, file name, randomizer, target, or row hash selects a
partition.

Every record has exactly these declared columns or JSON keys, in this order:

```text
row_id, source_id, content_id, group_id,
<one column per schema field in schema order>, target
```

All identities are caller values and record order is preserved within each
split. The adapter never generates IDs, trims or normalizes values, reorders
rows, deduplicates records, imputes missing cells, or skips malformed records.
Feature names that collide with the five reserved identity/target names are
rejected rather than aliased.

CSV uses fixed comma/quote rules and explicit scalar tags: `s:<text>`,
`i:<canonical-decimal>`, and `b:true`/`b:false`. Therefore the categorical
labels `"1"`, `1`, and `true` remain distinct. JSONL uses exact native JSON
string, integer, or boolean values and rejects duplicate keys, floats, `null`,
containers, non-finite constants, comments, and blank records. Neither format
infers a schema, type, category, delimiter, missing-value policy, ordinal
meaning, metric, arithmetic interpretation, or continuous variable.

Each split is an exact nonempty `bytes` object, strict UTF-8 without BOM or NUL,
at most 16 MiB, with physical and logical records capped at 32 KiB. Existing
field/category/row/cell/text/integer bounds still apply, and the existing
canonical presentation plus three-way lineage validators remain authoritative.
The adapter bounds are intentionally tighter than every theoretically possible
text rendering of the schema envelope.

The result binds only the existing typed schema, ordered canonical rows, and
three semantic payload roots. Raw CSV/JSONL bytes, quoting, line endings,
format, paths, filenames, inode/mtime, environment, and read chronology are not
present in that digest. This facade consequently proves no byte provenance,
source fidelity, label custody/secrecy, one-shot access, sampling validity,
leakage freedom beyond declared ID disjointness, statistical generalization,
observer admission, theorem, certificate, or promotion. Path/stream, missing-
data, continuous-data, inferred-schema, automatic-split, and provenance-receipt
policies require separate versioned designs.

### 1.2 Optional missing-data policy is a separate RFC

[Document 172](172_observer_v3_missing_data_policy_rfc.md) accepts a
documentation-only contract for a future non-root masked-missingness sibling.
It preserves this categorical ingestion API and every v1 byte, export, error
and rejection path. Native policy authority would require fresh replay of the
policy plus all three exact byte payloads; structural decode is external-only.
No missing-data runtime exists in the current package, and CSV `m:` plus JSON
`null` remain invalid here. Continuous interpretation and combined
missing×continuous preprocessing remain separate, unimplemented designs.

### 1.3 Optional continuous-data policy is a separate RFC

[Document 173](173_observer_v3_continuous_data_policy_rfc.md) accepts a
documentation-only contract for a future non-root exact fixed-bin sibling. It
binds caller-declared canonical decimal cut points and categorical output
labels without learning from any split. Native policy authority would require
fresh replay of the policy plus all three exact byte payloads; structural
decode is external-only. No continuous-data runtime exists in the current
package, and JSON floats plus CSV `d:` remain invalid here. Missing-data
composition remains a separate, unimplemented design.

## 2. Exact representation transport

`apply_representation_transport(...)` accepts an exact source-root-bound
transport specification containing:

- complete row and field permutations;
- unique destination field names;
- ordered, typed, bijective field-category maps;
- one typed target-category bijection.

An applied transport creates a new canonical presentation, preserves the
declared lineage tuple for every row, derives an inverse, and requires exact
round-trip equality with the source. Its receipt binds source and destination
schema/payload roots, the specification root, dimensions, lineage preservation,
and round-trip verification. Invalid, transplanted, partial, noninjective, or
noncanonical specifications terminate as `BLOCKED` without a destination or
receipt.

This proves only an exact finite encoding transport for the supplied data. It
does not by itself show that an observer response commutes with that transport.

## 3. Frozen-observer commuting square

`check_observer_representation_transport(...)` separately tests one
predeclared square:

```text
source row --representation transport--> destination row
    |                                      |
source closed observer              destination closed observer
    |                                      |
source response --declared bijection--> destination response
```

The implementation validates the applied representation receipt, evaluates
the two frozen scalar observers through the closed worker, joins outputs by
preserved row identity, and checks the declared response bijection. A completed
experiment is:

- `OBSERVER_TRANSPORT_VERIFIED` when all checked rows commute;
- `OBSERVER_TRANSPORT_REFUTED` when one or more checked rows mismatch;
- `BLOCKED` when inputs, mappings, transports, observers, or worker receipts
  cannot support a completed check.

The receipt binds both observer programs, the representation transport,
response map, both worker results, checked-row count, and mismatch count. Even
`OBSERVER_TRANSPORT_VERIFIED` means only that this finite square commuted on
these rows. It is not distributional or adversarial robustness, causality,
mechanism, explanation, observer equivalence, or a theorem.

## 4. Closed DSL and logical subprocess

The Phase-III observer language contains only versioned built-in operations:
`column`, `xor`, and `pair`. Its immutable AST contains no Python callback.
Grammar and term validation derive kinds and costs, enforce finite depth/cost/
arity limits, and serialize requests through strict canonical JSON.

`run_closed_observers_isolated(...)` uses a fresh `python -I` child on POSIX,
closes inherited file descriptors, supplies a minimal environment, enforces a
parent timeout, applies CPU/address-space/file-size/open-file limits, caps
request/response/output work, repeats evaluation for determinism, and verifies
the returned canonical receipt. A malformed request, timeout, failed child,
noncanonical response, resource breach, or receipt mismatch becomes `BLOCKED`
without retained partial outputs.

This profile is named `logical-subprocess`. It is **not** a syscall sandbox,
container, VM, seccomp policy, filesystem namespace, or network namespace. The
child still has the operating-system permissions of its user. The requested
`strict` profile deliberately fails with `strict-isolation-unavailable`; the
implementation does not pretend that the logical child is a strict sandbox.

## 5. Cooperating-process one-shot ledger

The local ledger records a hash-chained state machine:

```text
RESERVED -> CLAIMED -> CONSUMED
                    -> FAILED
```

It stores only a capability digest, not the raw capability. It requires an
existing same-user private directory, rejects symlink and unsafe ownership/mode
conditions, serializes access with one POSIX file lock, writes a canonical
bounded state file through atomic replacement, and rejects a second claim or
second finalization. A crash after `CLAIMED` leaves the attempt burned.

This is one-shot coordination only among cooperating processes using the same
local store. It provides no remote witness, monotonic hardware, anti-rollback
storage, trusted time, operator non-bypass, protection from a same-user process
that copies or resets state, or proof that labels were historically secret.
Within one intact store, reservation identifiers, capability digests, and test-
payload commitments are each unique, so renaming an attempt cannot reserve the
same capability or committed test twice.

## 6. Governed burn-before-evaluation service

`execute_one_shot_closed_evaluation(...)` claims the reserved capability before
validating the presented schema, test-payload root, feature-row evaluation
root, or observer-program root
and before invoking the worker. After a successful claim:

1. mismatched or malformed bound inputs finalize the attempt as `FAILED`;
2. a blocked worker finalizes it as `FAILED` with `WORKER_BLOCKED`;
3. a valid ready worker finalizes it as `CONSUMED` with
   `EVALUATION_COMPLETED`;
4. the governed result binds the claimed ledger receipt, terminal ledger
   receipt, worker root when present, program root, obstruction, and boundary.

`READY` means that the fixed closed evaluation completed under those roots. It
is not a discovery, replication, statistical confirmation, E4 judgment, or
truth verdict. The reservation also carries parent-result and confirmation-
policy roots, but this evaluation method does not independently replay those
upstream objects.

## 7. Authenticated root-only audit receipt

The replay package kind is currently only `AUDIT_RECEIPT`. It binds roots for
the parent result, confirmation result, test commitment and data, schema,
feature-row evaluation, observer program, confirmation policy, worker receipt, terminal ledger receipt,
and a nonempty bounded suite of transport receipts. It also binds a
caller-declared environment and serializes to bounded canonical JSON.

Two authentication profiles exist:

- `HMAC-SHA256-v1` is dependency-free shared-key integrity. Any holder of the
  shared key can create an indistinguishable tag, so it is not public
  verification or nonrepudiation.
- `Ed25519-v1` provides optional public-key signature verification when the
  `cryptography` dependency from the `signing` extra is installed. The package
  does not establish who controls a key, whether a key is trusted, its
  lifecycle, revocation status, or the truth of the signed roots.

Builders require a terminal linked ledger receipt. Validators can optionally
recheck that receipt link. Confirmation terminal outcomes bind the ledger
outcome root to `confirmation_result`; governed worker terminal outcomes bind
it to `worker_receipt_digest`. The other root remains an authenticated
declaration until a higher-layer validator receives and checks the corresponding
object. The package contains roots, not the underlying test
rows, observer programs, transport objects, worker runtime, or upstream
confirmation inputs. It is therefore **not independently executable full
replay**. The environment fields and `signer_id` are authenticated declarations,
not externally attested facts.

## Terminal evidence map

| Layer | Positive/completed state | Exact scope |
|---|---|---|
| representation transport | `APPLIED` | exact invertible encoding of one finite presentation |
| observer square | `OBSERVER_TRANSPORT_VERIFIED` | declared response commutation on checked rows |
| closed worker | `READY` | deterministic closed evaluation in a bounded logical child |
| ledger | `CONSUMED` | one cooperating local capability reached a completed outcome |
| governed service | `READY` | burned attempt produced a valid ready worker receipt |
| replay package | valid HMAC/Ed25519 | authenticated bound roots under supplied key material |
| research line | canonical bounded DAG | declared family history, relative only to disclosed nodes |
| lineage assessment | local/family/adaptive status tuple | no adaptive validity without a separate policy verifier |
| claim composition | licensed finite conjunction | exact governed or externally validated local contracts; every binding retained; no P2 promotion |

None of these states implies another unless the relevant linking validator
checks the exact roots. None promotes an empirical claim into causality,
semantic explanation, object formation, population generalization, a Veyra
theorem, or a registry certificate.

Document 165 adds a separate downstream composition boundary. It can combine
freshly validated `READY` governed results or explicitly validator-bound local
claim receipts only as an exact finite conjunction that retains every local
binding. It does not change the meaning of `READY`, trust an external validator,
or let receipt multiplicity alone license an aggregate claim.

## 8. Adaptive research-line boundary

The `lineage` subpackage addresses the representational half of `OD-A12`. It
binds finite experiment nodes, parents, design roots, data commitments, prior
outcomes visible before design, adaptation reasons, and local outcome roots
into a canonical DAG. `ISOLATED`, `PREDECLARED_CONTINUATION`, and
`ADAPTIVE_AFTER_OUTCOME` are disjoint shapes; adaptive nodes must name actual
ancestor outcome roots.

Assessment keeps local governed-result replay, family recording relative to
the declaration, and adaptive inference orthogonal. A named inferential policy
is deliberately `DECLARED_UNVERIFIED`; significance and population wording
remain disabled until a separate policy-specific verifier is implemented. The
exact independent-null adaptive-retry fixture demonstrates that twenty local
`alpha=0.05` attempts can have roughly `0.642` probability of at least one
nominal positive. See [document 163](163_adaptive_research_line_validity.md).

## Remaining production boundary

A stronger production-scientific system would still require, at minimum:

- real test-label custody outside the experiment operator's reach;
- a reviewed syscall/container/VM isolation boundary;
- anti-rollback or externally witnessed ledger state and trusted chronology;
- external key identity, authorization, rotation, revocation, and trust policy;
- a full disclosure/replay bundle containing the data, programs, policies,
  runtime identity, and deterministic reconstruction procedure;
- an external sampling and inference argument for any population claim.
- a proved/executable family-level inference policy for any adaptive sequence,
  plus trusted evidence that the declared research line is complete;

Phase III is useful because it makes several missing controls explicit and
testable. It remains finite research infrastructure, not certification of a
scientific or ontological conclusion.
