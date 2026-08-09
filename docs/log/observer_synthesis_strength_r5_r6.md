# Observer synthesis and scoped strength R5–R6

**Status:** implemented and checked on 2026-07-14.
**Scope:** deterministic bounded synthesis plus one formally scoped observer-class separation; not global Veyra superiority.

## R5 — generic synthesis engine

`src/core/observer/synthesis.py` searches a typed finite grammar rather than recording a post-hoc observer name. Terms are built from `input`, unary `apply`, and binary `pair` nodes over registered primitives with positive semantic costs.

The engine provides:

- deterministic enumeration, canonical terms, and fingerprints;
- explicit depth/term/cost budgets and a complexity penalty;
- per-case response and obstruction evidence;
- rejection of noncanonical values and evaluator nondeterminism;
- unexpected obstructions that never count as successful separation;
- `fit_observer()` over training cases only;
- validation of the fixed winner on untouched holdout cases;
- a locked digest over grammar shape, mandatory trusted primitive semantic IDs, executable code/defaults/closures, reducible `itemgetter`/`partial` arguments, referenced local helpers, baselines, and scoring config;
- exact in-process evaluator identity between fit and validation, preventing post-fit callable replacement even when a replacement reuses the declared semantic ID;
- type-tagged canonical payload serialization plus split-ID/group-ID and pair-order-independent payload leakage rejection;
- mandatory trusted `payload_key` for opaque payloads: unkeyed opaque values block as `unbound-semantics`, while equal keys across train/holdout block as `split-leakage`;
- protocol-mismatch obstruction if holdout changes evaluator semantics, grammar, baselines, or config;
- the explicit conclusion “not found in this grammar/budget,” never “no observer exists.”

## Concrete synthesis witness

The parity section of `src/core/observer/synthesis.py` supplies a reusable corpus and primitives. The training split compares the duplicated even-parity 4-cube with the full 4-cube. The holdout uses the duplicated odd-parity 5-cube versus the full 5-cube with reversed columns.

The deterministic winner is:

```text
histogram(xor-rows(input))
```

It has train fit `1.0` and holdout fit `1.0`. Named baselines based on row count and proper-subset marginals are blind on both splits. The holdout is never used to rank candidates.

## R6 — one valid `stronger` result

The baseline observer class is exactly the functions factoring through all proper-subset marginal signatures. The extended class adds global parity. `proofs/lean/VeyraObserverSynthesis.lean` checks:

- `THM-R6-001`: post-processing a blind baseline cannot distinguish baseline-equal inputs;
- `THM-R6-002`: adding a response that differs on those inputs separates the product observer.

The executable certificate derives class inclusion from explicit coordinate sets, requires exact winner `histogram(xor-rows(input))`, checks that it belongs to the extended class but not the baseline class, then verifies baseline equality, named-baseline blindness, train/holdout separation, and Lean status. Mutation tests reject reversed inclusion and an unrepresented winner AST.

Benchmark `BM-F009` is therefore `stronger` only on the declared dimension `declared-observer-class-discrimination`. The full ledger is now:

```text
8 benchmarked = 1 equivalent + 4 weaker + 2 clearer + 1 stronger
unsupported stronger = 0; overclaims = 0
```

## Honest boundary

Global parity is classical mathematics. The result proves strict inclusion of one declared observer class, not that Veyra is globally stronger than classical mathematics, not a runtime speedup, and not a general algorithm that finds every useful observer. Synthesis is complete only for the supplied finite grammar and budgets. Semantic IDs and opaque-payload keys are trusted protocol declarations, not automatically proved meanings; unknown callable/payload structures are therefore rejected rather than hashed through unstable `repr` output.

## Verification surface

- `tests/observer/test_observer_synthesis.py`
- `tests/observer/test_observer_synthesis_parity.py`
- `tests/shadows/test_classical_benchmarks.py`
- `tests/shadows/test_benchmark_derivations.py`
- `tests/surprise/test_veyra_magic.py`
- `proofs/lean/VeyraObserverSynthesis.lean`
