# Certified observer discovery MVP

## Status

This is an **experimental bounded statistical protocol**, not a theorem and not
a general hidden-variable discovery claim.  It is the first data-facing layer
over the finite typed grammar in `src.core.observer_synthesis`.

The permitted conclusion is deliberately narrow:

> Within one declared finite grammar, locked split, calibration policy, and
> named baseline family, a train-selected observer remained informative on the
> supplied holdout and passed the configured finite checks.

No entry is added to `THEOREMS.md` or the theorem registry.

## Input contract

`DiscoveryRow` carries four independent provenance fields:

- `row_id` identifies the record;
- `source_id` identifies its originating entity;
- `content_id` identifies caller-declared content lineage;
- `group_id` is the exchangeability and resampling unit.

Features are immutable canonical categorical values.  Targets are finite
string, integer, or Boolean labels, and one group must have one target.  Train
and holdout record, source, content, and group identities must be disjoint.
Every source/content lineage belongs to exactly one group per split, and v1
requires equal-sized groups so bootstrap work and group weighting are explicit.
Ordinary repeated categorical values remain legal; `content_id`, rather than
feature equality, represents a claimed cross-split clone.

The split is supplied explicitly.  This layer does not choose a random split,
fit an encoder, impute values, or inspect files.

## Locked protocol

`discover_observer(...)` performs the following finite procedure:

1. Bounded-copy caller-owned records, then validate the detached data, grammar,
   named baselines, evaluator identities, budgets, and calibration
   configuration. Validation and evaluator callbacks never intentionally read
   the original mutable object graph after that snapshot. The copier enforces
   outer cardinality plus aggregate canonical/AST occurrence budgets before it
   recursively allocates detached structures; cycles and shared-DAG expansion
   fail closed.
2. Exhaust the declared R5 grammar through a streamed, construction-capped
   enumerator. A cutoff is `BLOCKED`, never evidence that no observer exists.
3. Evaluate every candidate deterministically on train.  Evaluator failure,
   noncanonical output, or nondeterminism blocks the complete run.
4. Rank candidates only on train by empirical mutual information minus the
   declared complexity cost.  The winner is then frozen.
5. Re-run selection on train-only group bootstrap samples and measure exact AST
   winner stability.
6. Evaluate the frozen winner and named baselines on holdout without reranking
   the winner.
7. Apply a conservative holdout max-T adjustment to the frozen winner: every
   group-label permutation recomputes the maximum raw mutual information over
   the complete candidate catalog, while the observed statistic remains the
   frozen winner's raw holdout mutual information.  This does not replay or
   claim calibration of the complete train-selection procedure.  The add-one
   p-value cannot be zero.
8. Require positive held-out information, a positive gap over the best named
   baseline, configured max-stat significance, and configured train stability.

This max-statistic rule is intentionally conservative.  It prevents a large
grammar from receiving the same evidential treatment as one preregistered
observer merely because both contain a favorable candidate.

## Terminal states

- `FOUND` — the complete bounded protocol passed.  The report carries the
  frozen train winner, holdout statistics, baselines, calibration, and
  stability.
- `NOT_FOUND_WITHIN_BUDGET` — a valid complete search finished, but no
  candidate passed all configured thresholds.  No partial winner is returned.
- `BLOCKED` — input, semantics, leakage, budget, calibration, determinism, or
  runtime integrity failed.  No partial winner is returned.

Failure within a finite grammar remains exactly
`NOT_FOUND_WITHIN_BUDGET`. It is not an impossibility result for other
observers.

Project-enforced floors cannot be weakened by configuration: alpha is at most
`0.05`, stability is at least `0.5`, permutations are at least `19`, and train
bootstraps are at least `16`. The implementation also caps rows per split,
feature shape, primitive count, grammar depth/cost, catalog size, determinism
checks, permutation/bootstrap counts, retained canonical output, and precharged
total statistical work. Input-controlled structural limits are checked before
evaluator work. Evaluator execution itself is trusted and in-process: v1 cannot
turn a hanging or memory-hostile user callable into a terminal report.

## Evidence identities

The report binds separate domain-separated SHA-256 identities for:

- grammar, primitive implementations, named baselines, and configuration;
- the published structural grammar (typed primitive signatures and costs);
- ordered train data;
- the train-best objective bound to the protocol, train-data, and catalog roots;
- ordered holdout data;
- the complete canonical catalog;
- the terminal result and all published statistics.

Every non-`BLOCKED` report also publishes a result-bound complete configuration
receipt:
the complexity cost, train and holdout thresholds, alpha, permutation and
bootstrap counts, stability threshold, determinism checks, catalog cap, and
random seed used for the decision. Its domain-separated digest is a named child
of the protocol root beside a grammar/baseline material digest, so changing the
receipt cannot validate against the old protocol root. The
report likewise publishes a protocol-bound structural grammar receipt, allowing
the independent validator to derive the winner's typed R5 complexity instead
of trusting the reported integer and to enforce grammar-relative depth, cost,
accepted output, and canonical pair order. It also checks the internally bound
train-best objective against the train threshold for early finite failure,
recomputes the winner
objective and observer gap, checks
calibration/stability counts and thresholds against that receipt, rejects
cyclic or oversized observer ASTs before calling recursive fingerprint helpers,
and then replays the terminal result digest.

Changing a primitive implementation, threshold, seed, split assignment,
provenance identity, catalog, baseline, or result therefore changes an evidence
root. `validate_discovery_report(...)` independently checks terminal and nested
statistical invariants, the published decision policy, AST fingerprints, hard
floors, and result binding
without rerunning caller evaluators. These digests provide deterministic
self-consistency identities, not signatures: a party able to replace every
root can construct a different self-consistent report. They do
not make caller-supplied provenance or evaluator purity truthful.

In particular, the train-evaluation digest binds a reported scalar to the
protocol/train/catalog identities; it does not recompute empirical optimality
without the original rows and evaluator execution. Default report validation
therefore checks result-local arithmetic and identity consistency. A caller
that obtained the train-evaluation root through a separately trusted channel
can pass it as `expected_train_evaluation=...` to pin that identity. This still
does not turn an unkeyed digest into authentication.

## Non-claims and current limitations

`FOUND` does **not** establish:

- causality or recovery of a physical latent variable;
- semantic or scientific explanation;
- population-wide generalization outside the supplied holdout;
- optimality outside the declared finite grammar;
- superiority over classical statistics, ML, or classical mathematics;
- validity of a weak, omitted, or adversarially selected baseline family;
- resistance to target leakage or a contaminated caller-provided split;
- process-level holdout isolation;
- stratified exchangeability: v1 assumes one homogeneous group pool;
- executable support for continuous/missing-data preprocessing; the separate
  [missing-data RFC](172_observer_v3_missing_data_policy_rfc.md) freezes only a
  future masked categorical boundary and adds no runtime here;
- a new Lean theorem.

The current API is in-process and programmatic. The separate Phase-II module
in `159_fixed_observer_confirmation.md` adds opt-in fixed-winner replication on
a third caller-declared test set, but it still cannot prove that those labels
were historically untouched. A later production slice must add a schema-bound
adapter, physically separate selection from test evaluation, and validate
target-leakage and preprocessing policies before this can be presented as an
end-user scientific discovery tool.

The in-process APIs are stateless and therefore cannot enforce one-shot holdout
or final-test consumption. Reusing either split for iterative research
decisions is an unsupported protocol violation that a later isolated receipt
ledger must prevent.

BM-F009 remains a calibration precedent only: it proves a strict inclusion of
one declared proper-marginal observer class after adding classical global
parity.  It is not evidence that Veyra is globally stronger than classical
methods.
