# 163 — Adaptive research-line validity

## Status

This document closes only the representational part of `OD-A12`. It records a
bounded experiment-family history and prevents the software from conflating a
valid local receipt with an established adaptive-inference guarantee. The
statistical policy itself remains `OPEN` until a separately reviewed verifier
establishes its assumptions and arithmetic for the chosen statistic and
filtration.

The implementation is the sibling package
`src.core.observer_discovery_v3.lineage`. It does not change Phase-I/II search,
the Phase-II fixed-winner confirmation rule, the v3 one-shot ledger, or any
registered theorem/certificate.

## 1. The distinction

Three predicates must not collapse:

```text
local_validity
family_recording
adaptive_validity
```

- `local_validity=ESTABLISHED` means the selected terminal node is linked to a
  freshly validated `GovernedEvaluationResult` whose exact result and outcome
  roots match the node. A caller declaration alone is insufficient.
- `family_recording=RECORDED_RELATIVE_TO_DECLARATION` means the supplied finite
  DAG is exact, bounded, canonical, acyclic, parent-closed, digest-bound, and
  internally honest about which ancestor outcome roots were visible before an
  adaptive design. It cannot prove that the operator disclosed every external
  experiment.
- `adaptive_validity` is independent. This implementation returns only
  `ISOLATED_LOCAL_ONLY`, `EXPLORATORY_NO_INFERENCE_CLAIMED`, or
  `NOT_ESTABLISHED`. It never licenses significance or population wording.

Consequently a locally valid terminal receipt can coexist with a recorded
adaptive family and `adaptive_validity=NOT_ESTABLISHED`.

The composition boundary in document 165 does not discharge this distinction.
Its only V1 rule fixes every aggregate to `LOCAL_ONLY`, so several locally
valid results still cannot become family/adaptive validity, significance, or
population wording through conjunction.

## 2. Canonical lineage node

`ExperimentLineageNode` binds:

```text
experiment_root
parent_nodes
doctrine_root
grammar_root
baseline_root
decision_policy_root
data_commitment_roots
prior_outcomes_visible_before_design
design_mode
adaptation_reason
terminal_local_status
terminal_outcome_root
node_digest
```

All roots are canonical lowercase SHA-256 shapes. Parent, data, and visible-
outcome tuples are bounded, unique, and sorted. Text is UTF-8 bounded. The
research line accepts at most 128 nodes, 16 direct parents per node, and eight
data commitments per experiment.

The design modes are disjoint:

- `ISOLATED` forbids parents, visible outcomes, and an adaptation reason;
- `PREDECLARED_CONTINUATION` requires parents but forbids outcome visibility
  and post-outcome adaptation text;
- `ADAPTIVE_AFTER_OUTCOME` requires parents, a nonempty reason, and at least
  one visible outcome root belonging to an actual ancestor.

The graph is deterministically topologically ordered by node digest and then
bound by one lineage digest. Unknown parents, cycles, duplicate experiment
roots, forged node/line roots, nonancestor visible outcomes, noncanonical
tuples, and oversized hostile inputs fail closed before unbounded traversal or
sorting. Assessment targets only a leaf of the declared graph, so an earlier
attempt with a declared continuation cannot be presented as the terminal one.

This mechanism makes declared adaptive history machine-visible. It cannot stop
an operator from falsely declaring a later attempt to be an isolated first
attempt; that requires external custody, witnessing, or trusted chronology.

## 3. Pluggable policy boundary

`AdaptiveInferencePolicy` names a caller-selected policy family and binds its
policy and optional evidence roots. Veyra does not hard-code alpha spending,
reusable holdout, e-process, or anytime-valid mathematics here.

An `EXPLORATORY_ONLY` policy must carry no inferential evidence root and yields
`EXPLORATORY_NO_INFERENCE_CLAIMED`. An inferential policy may be named and
root-bound, but without a policy-specific executable/formal verifier its status
is only `DECLARED_UNVERIFIED`; adaptive validity stays `NOT_ESTABLISHED` and
both significance and population wording remain forbidden.

This is intentional. A sequence of ordinary fixed-level p-values, the local
one-shot ledger, the Phase-II within-run max-stat calibration, and a provenance
DAG do not automatically become an anytime-valid or family-valid procedure.

## 4. Exact adaptive-retry witness

For `m` genuinely independent null experiments, each with exact nominal
positive probability `alpha`, stopping after the first nominal positive has
family-positive probability

```text
1 - (1 - alpha)^m.
```

For `m=20` and `alpha=1/20`, the exact value is computed as a rational and is
approximately `0.6415`. Every retained terminal run can still satisfy its local
fixed-alpha protocol. The witness therefore separates local protocol validity
from family-level inference validity under its explicit independence and exact-
alpha assumptions.

`veyra_sage.adaptive_research_line` independently computes the complement and,
under real Sage, checks it against the full binomial sum. Run:

```bash
sage -python scripts/verify_adaptive_retry.py \
  --attempts 20 --alpha-numerator 1 --alpha-denominator 20 --require-sage
```

This arithmetic is an adversarial illustration, not a model of every Veyra
workflow and not a proof that attempts, datasets, or p-values in a concrete
research line are independent.

## 5. Exact nonclaims

The lineage layer does **not** establish:

- completeness or truth of disclosed history;
- trusted time, append-only remote witnessing, operator non-bypass, or
  anti-rollback storage;
- statistical independence from graph shape or different commitments;
- family-wise error control, false-discovery control, optional-stopping safety,
  reusable-holdout validity, or an e-process;
- significance, a population claim, causality, explanation, objecthood,
  historical novelty, theoremhood, or ontology promotion;
- invalidity of current local R5/Phase-II/Phase-III receipts.

Exploratory reruns remain allowed when described as exploratory. Inferential
wording after continuation requires a named family policy and remains blocked
until that policy has separately established evidence for the exact protocol.
