# R14 — Observer synthesis v2 design
**Status:** R14.1–R14.6 and the post-frozen-gate R14.3b dispatch/deep-snapshot repair are independently approved; focused repair `115/115` passes, while isolated Sage and continuation immutable-tree serial gates remain open
**Date:** 2026-07-29
**Scope:** bounded deterministic synthesis over the exact ordered R11 observer AST
**Capability effect:** none

## Purpose
R14 v2 is an isolated replacement for using the permissive R5
callable/string search surface as if it were the trusted observer calculus.
It searches only canonical, typed R11 observers and reports finite evidence
under explicit resource limits.

This document freezes the implementation contract. R14.1–R14.3 provide the
exact grammar, positive budgets, locked corpus, audited evaluation, real
worker, and train-only CEGIS. R14.4 and the in-process R14.5 core add locked
trials, equal-limit children, baselines, finite receipts, isolated receipt
execution, one atomic aggregate certificate, and a presentation-only Sage facade.

## Exact R11 calculus

The only admitted syntax is the existing closed R11 AST:

```text
Input
Apply(primitive, child)       primitive in {Tail, Crest}
Pair(left, right)
```

The generator must construct R11 objects directly. Strings, callables,
plugins, dynamic dispatch, and legacy R5 observer descriptions are not
members of the v2 grammar.

R11 response-kind rules remain authoritative:

- `Input` has recurrence response kind;
- `Tail` accepts recurrence and returns recurrence;
- `Crest` accepts recurrence and returns mark;
- `Apply` to a pair or mark response is rejected;
- `Pair` accepts any two typed child terms and preserves left/right order.

Constructor cost is frozen as:

```text
cost(Input) = 0
cost(Apply(p, x)) = 1 + cost(x)
cost(Pair(x, y)) = 1 + cost(x) + cost(y)
```

The dynamic program is two-dimensional in exact constructor cost and actual
tree depth. It seeds `Input` at `(cost=0, depth=0)`, applies `Tail` and `Crest`
only to recurrence-kind rows at cost `c-1`, and builds every ordered pair from
costs `i` and `c-1-i`. A row is retained only when its resulting depth is at
most four. This depth pruning is part of the count; an unbounded-depth scalar
recurrence is not an acceptable substitute. Ordered products include both
`Pair(x, y)` and `Pair(y, x)` when `x != y`; `Pair(x, x)` occurs once.

The default catalog includes costs `0..6` and has exact strata:

```text
cost       0   1   2    3     4     5      6
terms      1   3   8   27   104   358   1064
```

Its pinned totals are:

- `1,565` terms;
- `488,550` canonical bytes across all rows;
- `338` canonical bytes for the largest single row;
- catalog digest `23408184aba5d55d283e4a9440e1859beaefa9d73a909d283057d59b527437cf`.

Generation order is increasing:

```text
(constructor cost, tree depth, canonical_observer_bytes(term))
```

using the existing R11 canonical codec. Candidate ordinals, digests, and
transcripts derive from that order. Duplicate canonical bytes, a missing
catalog tail, a reversed-pair omission, or a noncanonical term makes the
input `INVALID`; it is never treated as exhaustion.

## Hard resource contract

Every search and candidate evaluation runs in a child process. The default
contract has five independent hard ceilings:

| Ledger | Ceiling |
|---|---:|
| generated/evaluated candidates | `2,048` |
| retained canonical grammar artifacts | `8 MiB` |
| observer-case evaluations | `100,000` |
| child wall time | `5 s` |
| child address space (`RLIMIT_AS`) | `512 MiB` |

The catalog contains 1,565 terms, so the candidate ceiling provides headroom
without weakening the exact grammar. R14.1 precharges construction; R14.2a
adds positive monotone ceilings. R14.3a binds each cache to one isolated run
nonce and exact ledger identity: every `HIT` first checkpoints, precharges
one evaluation, and replays exact R11 semantics before accepting cached data.
Thus hits are audit-consistency checks, not compute savings. The R14.2b parent
starts its deadline before spawn, applies and re-reads exact `RLIMIT_AS` plus
`RLIMIT_CORE=0` before sending GO, bounds combined stdout/stderr/result bytes,
and terminates/reaps the isolated process group on every partial/failure path.

The only terminal statuses are:

- `FOUND` — a candidate satisfies all accumulated training obligations within
  every budget; post-lock validation is reported separately;
- `EXHAUSTED` — all 1,565 terms were evaluated, no winner exists, and no
  cutoff, crash, missing tail, or partial traversal occurred;
- `INCOMPLETE` — any candidate, evaluation, retained-output, wall-time, or
  address-space cutoff, or any worker crash, signal, cancellation, or partial
  traversal;
- `INVALID` — malformed or noncanonical configuration, grammar, corpus,
  split, baseline, receipt, budget, binding, or overlap.

Every declared limit is an exact positive integer; zero, negative, Boolean,
subclassed, or above-maximum configurations are `INVALID`.

A blocked R11 observation is an ordinary typed outcome where the task permits
it, never silent evidence of separation. No cutoff or child failure may be
translated into `EXHAUSTED`.

## Deterministic CEGIS

Only the frozen training split may influence candidate choice.

1. Begin with `Input`.
2. Evaluate accumulated obligations in canonical row order.
3. Ask the deterministic oracle for the lexicographically first failing
   training row.
4. Append exactly that counterexample to the transcript.
5. Select the first catalog term satisfying all accumulated obligations.
6. Repeat until `FOUND`, true `EXHAUSTED`, or a hard failure status.

The calibration acceptance trace is exactly:

```text
Input -> first counterexample -> Crest(Input)
```

The implementation manifest must pin the concrete counterexample bytes and
digest rather than relying on the prose label above. Each append-only
transcript step binds the candidate ordinal/canonical digest, counterexample
row/digest, cumulative ledgers, and active budget contract.

Repeated runs over identical canonical inputs must be byte-identical. No
holdout, unseen-size, adversarial, baseline-result, or receipt information may
enter the CEGIS oracle.

## Locked evaluation splits

Before fitting, one manifest binds every split ID, bounded positive case/group
ID, ordered payload digest, unordered clone digest, task flag, and budget.
Cross-split identity, group, payload, or reverse-clone leakage is `INVALID`.

- **Train:** the sole search and counterexample source.
- **Holdout:** supported sizes also present in training, but disjoint
  identities, groups, and canonical payloads.
- **Unseen:** ordered pair-size signatures absent from training and fixed before
  fitting; individual component sizes may recur (silence size zero does).
- **Adversarial:** required reverse/equal probes plus explicit non-winner
  tail-of-silence diagnostics. Malformed canonical data and resource edges are
  negative protocol tests, not scored corpus rows.

Immediately after `FOUND`, the winner's canonical bytes, ordinal, and digest
are locked. The frozen `required_for_winner` flag separates validation from
diagnostics: `Crest(Input)` passes all eight required default cases, while
the two reverse Tail boundary rows remain diagnostics and do not reject it.
Later results cannot rerank/restart/tune; incomplete mandatory validation is
`INCOMPLETE`, while diagnostic mismatch remains an auditable false result.

## Fixed same-resource baselines

The baseline set is declared before search:

```text
Input
Tail(Input)
Crest(Input)
Pair(Input, Input)
```

Each is the exact R11 AST and uses the same canonical cases, observation
semantics, task scorer, candidate/evaluation accounting, wall clock, retained
bytes, and address-space limits as the synthesized candidate. A baseline gets
no privileged labels, hidden payload field, alternate parser, cached answer,
or larger budget.

Because `Crest(Input)` is an explicit control baseline, rediscovering it is a
determinism/calibration result, not novelty or superiority. Comparisons are
limited to the frozen finite task and these named same-information/resource
AST baselines; they imply nothing about classical mathematics or general
program synthesis.

## Equal-resource trial execution

R14.4b executes the locked winner plus four predeclared controls in five
separate fixed-entry `-E -s -S` children. All requests are built before any
result is consumed, and every child receives the same verified pre-GO
address-space/core contract plus its own wall/output limits, ledger, and cache.
The parent validates pinned full-subject payloads and performs only pure report
assembly; it does not re-evaluate, rerank, restart, or accept partial evidence.

Independent adversarial review passes `61/61`: legacy/new worker counts are
`24/24` and `23/23`; deleted request slots, cross-subject transplants, forged
entry kinds, hostile canonical depth, successful-leader descendants, and
SIGTERM-ignoring descendants fail closed. Hash seeds `0/1/777` produce the
same 2,278-byte report, SHA-256 `608df06c...35bf6`, whose internal report digest
remains `07dbfe...0f48`. This is equal-resource execution only, not proof of
global completeness, minimality, novelty, or superiority.

## Finite R12 receipts

Receipts are produced only after replaying the locked observer through the
existing exact R11 semantics and R12 lowering path. They are finite executable
audit witnesses, not search authority. Every R14 receipt must retain:

```text
capability = preserves
evidence_accepted = false
promotion_ready = false
taxonomy_changed = false
```

Receipts do not authenticate themselves, prove the synthesis result, supply
kernel/formal evidence, authorize R8 promotion, or alter the R13 taxonomy
`2/4/25/5` with `proof_complete=false`. Receipt failure or transplant is
`INVALID`; receipt success cannot upgrade a failed validation.

R14.5b binds the exact 19,980-byte full trial snapshot into one fixed child.
Before replay it charges one candidate, 47,837 canonical bytes, ten
evaluations, and 27,857 retained bytes. The parent performs no receipt
semantics and accepts only exact length, SHA-256 `0afbd9...4720`, and internal
bundle `740f55...0895`. Request/terminal snapshots and deadline-aware
GO/request transport fail closed under mutation and reduced pipes; focused
receipt-worker `22/22`, scoped `131/131`, and all R14 `295` pass; independent
review closes with blocker/high/medium/low `0/0/0/0`.

## Modular implementation inventory

Production remains split into cohesive files within the repository's 1000-line
target; the current implementation is still at or below 300 lines per file:

- grammar/types/validation and positive budgets:
  `observer_synthesis_v2_{types,grammar,validation,budget,budget_validation}.py`;
- locked protocol/corpus/evaluation: `observer_synthesis_v2_{protocol,corpus,evaluation}.py`;
- train-only synthesis and search isolation: `observer_synthesis_v2_cegis*.py`
  plus `observer_synthesis_v2_worker*.py`;
- baselines, reports, and equal-limit subjects:
  `observer_synthesis_v2_{baselines,trial*}.py`;
- finite receipts and their one-child isolation:
  `observer_synthesis_v2_{receipt*,receipts}.py`.

The final R14.5 wave adds `observer_synthesis_v2_pipeline.py`, one level-3
finite-audit certificate, and `VeyraObserverSynthesisV2Lab`. Sage presents the
already-run core certificate and performs no independent semantic replay.

## Test plan

- `test_observer_synthesis_v2_grammar.py`: exact strata, total/byte counts,
  ordering, both pair orders, and type rejection.
- `test_observer_synthesis_v2_budget*.py`: all five ceilings, child kills,
  every partial path as `INCOMPLETE`, malformed input as `INVALID`, and only
  full traversal as `EXHAUSTED`.
- `test_observer_synthesis_v2_cegis.py`: exact calibration trace,
  byte-deterministic append-only transcript, and no non-train access.
- R14.3a protocol/corpus/cache tests: bounded IDs, clone-disjoint splits,
  winner flags, charged replay hits, run/ledger binding, and poison rejection.
- `test_observer_synthesis_v2_trial*.py`: exact predeclared ASTs, identical
  information/resource ledgers, and five equal-limit children.
- `test_observer_synthesis_v2_receipts.py`: exact finite R12 replay and false
  evidence/promotion/taxonomy gates.
- `test_observer_synthesis_v2_receipt_worker.py`: one fixed receipt child,
  exact canonical pins, closed terminal states, and parent non-replay.
- Final R14.5: atomic 5+1 aggregate, exact level/name/boundary certificate,
  one-suite registration, Sage reuse, count, and hostile-shape tests.

Final review passes `26/26` plus API `2/2`, severity `0/0/0/0`; exact-slot,
numeric, boundary, and post-receipt TOCTOU drift is closed without claim drift.
Property and mutation coverage must include reversed pairs, duplicate or
renamed data, boolean/integer laundering, truncation, clock and memory
exhaustion, worker signals, transcript mutation, and baseline transplants.

## Claim boundary

`FOUND` supplies one finite witness. `EXHAUSTED` can justify completeness or
minimality only relative to the exact 1,565-term ordered grammar, exact frozen
corpus/task, and fully unspent hard-budget path. `INCOMPLETE` supports no
negative conclusion.

R14 does not claim unbounded or general observer synthesis, global
completeness, global minimality, optimality, observer-semantic correctness
beyond R11, advantage over R5 or classical methods, receipt authority, a new
theorem, a Lean proof, an R8 promotion, or a taxonomy change. The existing R5
callable/string grammar remains a separate legacy surface and is not a
trusted substitute for this design.

Consequently this design adds no notation or theorem registry entry. A future
implementation must update registries only if it introduces an actual public
definition or theorem rather than the local engineering names fixed here.
