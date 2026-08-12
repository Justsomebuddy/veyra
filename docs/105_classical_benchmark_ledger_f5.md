# Classical Benchmark Ledger F5

**Date:** 2026-08-04
**Status:** eight-row paired ledger with one formally scoped observer-class result; not a proof of global superiority.
**Implements:** F5 plus R6 explicit comparison with classical mathematics.

## Scope boundary

This closes the narrow F5 blocker from `102_foundational_gap_audit.md`: promoted Veyra artifacts have a ledger that names a classical statement, a Veyra artifact, and an honest verdict.

It does **not** prove that Veyra is globally shorter, stronger, or more complete than classical mathematics. The ledger has eight cards; its sole `stronger` verdict is restricted to a declared observer class.

## Ledger rows

Implemented in `src/core/classical_benchmarks.py`.

| ID | Topic | Classical side | Veyra side | Verdict |
|---|---|---|---|---|
| `BM-F001` | echo reflexivity | `x = x` by equality reflexivity | `THM-F001` observer-indexed echo reflexivity | equivalent |
| `BM-F002` | signed addition | `3 + (-2) = 1` in integer arithmetic | arising/fading balance stitch has net length `1` | weaker |
| `BM-F003` | Pythagorean `3-4-5` | general right-triangle theorem | finite tremor-corridor theorem card for one exact sample | weaker |
| `BM-F004` | closed recurrence | finite closed walk endpoint check | closed breath wraps as `Mode`; open breath is an obstruction | clearer |
| `BM-F005` | Euclid product-plus-one | no finite prime list exhausts primes | intrinsic recurrence division and supplied-factor escape proof | weaker |
| `BM-F006` | deformation invariants | general topology invariant proof | finite corridor/shell invariant and obstruction rows | weaker |
| `BM-F007` | likelihood residuals | finite likelihood/residual diagnostics | finite slopes plus certified/blocked residual families | clearer |
| `BM-F009` | observer-class discrimination | every postprocessor of proper-subset marginals is blind | synthesized global-parity observer separates locked train and holdout | stronger, scoped |

## Verdict discipline

Allowed verdicts are `shorter`, `clearer`, `stronger`, `weaker`, and `equivalent`.

`stronger=1` is allowed only for `BM-F009`, dimension `declared-observer-class-discrimination`, scope “observers factoring through all proper-subset marginals.” Lean `THM-R6-001/002` plus executable coordinate-set inclusion, exact winner-AST membership, and locked train/holdout evidence show that adding global parity strictly extends this class. Global parity is classical; this is not Veyra-over-classical superiority.

## Certificate

`classical_benchmark_f5` checks:

1. all eight active benchmark IDs are present;
2. every row is marked `benchmarked`;
3. each row has a paired classical statement and Veyra artifact;
4. verdict counts are explicit: one equivalent, four weaker, two clearer, one scoped stronger;
5. any stronger row carries dimension, scope, evidence ID, Lean-backed strict certificate, derived class inclusion, exact winner membership, and non-global boundary;
6. unsupported stronger and overclaim counts are zero.

## Interpretation

The ledger is a truth-maintenance device. It is useful even when Veyra is weaker, because it marks exactly where current artifacts are only finite fixtures.

`BM-F004` and `BM-F007` remain clarity results. `BM-F009` is a genuine class-inclusion result, but its added observer is classical and its scope is deliberately narrow.

## Remaining work

- Expand the ledger for every stable theorem card promoted beyond a finite fixture.
- The current eighth row was added explicitly; there is no automated benchmark-row generator or proof-corpus discovery claim.
- Add size/complexity fields only after the proof language is stable enough to count proof steps honestly.
- Build nontrivial formal exports beyond `THM-F001` before claiming formal proof coverage.

## Structural comparisons stay separate

Issue #5's bridge/separation proposal is implemented in
[`162_comparative_bridge_separation_ledger.md`](162_comparative_bridge_separation_ledger.md).
It does not add `BM-F010`, change the eight F5 rows, or reuse F5 verdicts for
analogy, reduction, or predicate separation.
