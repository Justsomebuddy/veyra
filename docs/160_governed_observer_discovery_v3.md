# 160 — Governed Observer Discovery Phase III

## Status and separation

`src.core.observer_discovery_v3` is a separate experimental protocol package.
It does not replace or silently strengthen the Phase-I/II APIs described in
documents 157–159. The package root exports nothing; public names are exposed
through its narrow `schema`, `transport`, `dsl`, `ledger`, `service`, and
`replay` subpackages or the explicit `worker.runtime` module.

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

None of these states implies another unless the relevant linking validator
checks the exact roots. None promotes an empirical claim into causality,
semantic explanation, object formation, population generalization, a Veyra
theorem, or a registry certificate.

## Remaining production boundary

A stronger production-scientific system would still require, at minimum:

- real test-label custody outside the experiment operator's reach;
- a reviewed syscall/container/VM isolation boundary;
- anti-rollback or externally witnessed ledger state and trusted chronology;
- external key identity, authorization, rotation, revocation, and trust policy;
- a full disclosure/replay bundle containing the data, programs, policies,
  runtime identity, and deterministic reconstruction procedure;
- an external sampling and inference argument for any population claim.

Phase III is useful because it makes several missing controls explicit and
testable. It remains finite research infrastructure, not certification of a
scientific or ontological conclusion.
