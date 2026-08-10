# 159 — Fixed Observer Confirmation on a Declared Test Set

## Status

This is an **experimental bounded replication protocol** over the observer
discovery MVP. It adds a caller-declared third split and evaluates only the
already frozen observer and the exact named baseline family. It is not a
theorem, certificate-registry entry, causal claim, authenticated chronology,
or process-isolated one-shot test.

This document and its APIs remain Phase II. The separate strict-v3 experiment
in [document 160](160_governed_observer_discovery_v3.md) does not change a
Phase-II receipt, upgrade its claim tuple, or retroactively supply custody,
authentication, isolation, or one-shot enforcement to this protocol.

The permitted positive conclusion is:

> The exact previously discovered observer, without replacement or reranking,
> retained positive categorical information and a positive observed gap over
> the exact named baselines on one disjoint declared test set, while its
> association passed the fixed-family global-independence calibration.

## Protocol

`confirm_observer_discovery(...)` accepts:

- an exact valid upstream `FOUND` report;
- the original grammar, train/holdout split, named baselines, and discovery
  configuration;
- a third tuple of categorical `DiscoveryRow` records;
- a bounded `DiscoveryConfirmationConfig`.

It proceeds in this order:

1. Snapshot and validate the supplied configuration, original inputs, and test
   rows under hard structural limits.
2. Reject row, source, content, or group identity overlap between the declared
   test set and either previous split. Equal ordinary feature values remain
   legal because equality of categories is not lineage identity.
3. Re-run the complete upstream discovery from the supplied original inputs
   and require exact report equality. A merely self-consistent forged report is
   not accepted as the parent. After equality, only the locally replayed parent
   is trusted; later mutation of the caller-owned report cannot retarget the
   winner or parent root used by the receipt.
4. Recompute the parent protocol, policy, grammar, train, holdout, and catalog
   roots and require equality with the upstream report.
5. Evaluate exactly the frozen winner plus the exact named baselines on the
   test rows. The test set cannot select another catalog member. After all
   evaluator callbacks, recompute the bound discovery inputs and callable
   identities; persistent evaluator-time protocol drift blocks the run.
6. Compute

   ```text
   fixed_gap = MI(frozen_winner; target)
               - max MI(named_baseline; target).
   ```

7. Perform deterministic group-label permutations. Every permutation
   recomputes the maximum mutual information over the fixed winner plus the
   exact named baselines. The observed statistic is the frozen winner's mutual
   information, and the add-one p-value cannot be zero. This tests global
   independence with fixed-family multiplicity control; it does not test a
   composite null of no advantage over an already informative baseline.
8. Bind the parent result, confirmation policy, test data, statistics,
   obstructions, boundary, and result under domain-separated SHA-256 roots.

The confirmation work estimate is precharged before test evaluation. The
configuration enforces finite thresholds and caps, including `alpha <= 0.05`,
at least 19 permutations with sufficient add-one resolution, at most 4095
permutations, bounded determinism checks, rows, retained output, and aggregate
work.

## Terminal states

- `REPLICATED_ON_DECLARED_TEST` — the fixed winner has positive test
  information, exceeds the configured positive named-baseline gap, and passes
  the fixed-family global-independence permutation threshold. The gap is a
  separately required descriptive threshold, not an inferential superiority
  claim.
- `NOT_REPLICATED_ON_DECLARED_TEST` — the complete valid test run fails at
  least one declared threshold. No alternate observer is supplied.
- `BLOCKED` — the parent, inputs, lineage, semantics, resource policy,
  evaluator, or runtime integrity failed before a positive or negative
  replication judgment could be issued.

The independent validator recomputes local arithmetic, null exceedances,
threshold failures, exact obstruction records, policy floors/caps, protocol
binding, nested record shapes, fixed boundary text, and result digest. Optional
digest pins can bind the expected parent-result and test-data identities. An
optional validated `parent_report` additionally requires an exact valid
upstream `FOUND` result and links both its committed winner fingerprint and its
ordered named-baseline identities (name, class, fingerprint, and boundary) to
every non-blocked confirmation. A parent-result string pin alone does not
establish those links, and none of these local checks replays test statistics.
They establish deterministic self-consistency, not authentication.

## Executable claim semantics

`observer_discovery_claim(...)` separately projects a valid discovery report
onto three orthogonal axes:

- execution evidence;
- interpretation evidence;
- ontology commitment.

For the current `FOUND` report the projection is
`(E3V locked-holdout-passed, I1 declared-baseline-gap, O0
presentation-only)`. The R5 callable remains a `research-shadow`. Causality,
semantic explanation, theoremhood, object formation, P0 admission, and
historical novelty are fixed to `not-claimed`.

`NOT_FOUND_WITHIN_BUDGET` supports only a finite-protocol nonfinding; `BLOCKED`
supports neither association nor absence. Claim envelopes bind the source
report roots and are validated by exact deterministic reconstruction.

Final-set replication strengthens the empirical evidence but does not by
itself reach `E4 robust-finite`; it is the separate `E3T
declared-test-replicated` milestone. Phase II reserves E4 for mandatory
adversarial, representation-transport, and refinement checks.

## Trust boundary

The implementation remains an in-process research protocol. In particular:

- schema correctness, target exclusion, group exchangeability, and lineage
  identities are caller assertions;
- Python evaluators can access ambient process capabilities, hang, allocate,
  or inspect state despite structural and determinism checks;
- post-evaluation identity recomputation detects persistent mutation of bound
  callable semantics, but in-process mutable indirection or mutate-and-restore
  attacks remain outside the claim;
- the caller already possesses the test labels, so the API cannot prove that
  they were historically untouched;
- repeated calls can reuse the same test set;
- unkeyed digests do not prove authorship, chronology, or external provenance;
- a positive finite result does not establish population validity.

The separate strict-v3 package now experiments with a canonical schema, a
closed observer DSL, a resource-bounded logical subprocess, a cooperating-
process local ledger, burn-before-evaluation orchestration, and authenticated
root-only audit receipts. Those controls are described in document 160 and do
not alter this Phase-II result. They also do not yet meet the stronger
production-scientific boundary: there is no syscall sandbox, physically
separated test-label capability, anti-rollback or externally witnessed state,
trusted time, operator non-bypass, externally established key trust, or
independently executable full replay bundle.

A local ledger remains audit governance, not protection from an operator who
can copy or reset its storage.

## Nonclaims

This protocol does not establish:

- causality, mechanism, semantic explanation, or hidden physical variables;
- optimality outside the declared finite grammar;
- superiority over any unnamed statistical, ML, or mathematical method;
- scientific novelty or invention of a new primitive;
- P0 observer admission, OEP observer emergence, or P1/SFP object formation;
- a proof, Lean theorem, registry certificate, or theorem promotion;
- within this Phase-II API, one-shot consumption, process isolation,
  authentication, or trusted time;
- generalization beyond the declared test set without an external sampling
  argument.

The honest result is a stronger finite replication receipt: a previously
locked observer survived one separately declared finite test corpus without
being replaced after its labels were evaluated.
