# Native observer benchmark family and representation transport

**Status:** four bounded Rust calibrations, two explicit transport rows, and one
atomic replayable suite receipt.  
**Implementation:**
`vam/native/src/observer_synthesis/{benchmark_suite,benchmark_marginals,benchmark_transport}.rs`.
Canonical receipt serialization/replay is isolated in
`vam/native/src/observer_synthesis/benchmark_suite_receipt.rs`.

## Question and fixed language

The suite asks a deliberately narrow question: how does the existing closed
1,565-row `Input`/`Tail`/`Crest`/ordered-`Pair` grammar behave on several exact
four-state binary partitions? It does not add primitives or change CEGIS.

Every benchmark binds four abstract states, an injective unary-recurrence
encoding, six unordered pair obligations, a target class for each abstract
state, the exact catalog, deterministic counter limits, and the terminal trace.
`FOUND` means the catalog produced the pinned first winner. `EXHAUSTED` means
all 1,565 rows were traversed without a winner. Neither status is a result about
observers outside this grammar.

## Exact results

| Benchmark | Encoding | Target classes | Exact outcome |
|---|---|---|---|
| mixture | `[0,1,2,3]` | `[0,1,1,1]` | `FOUND`: `Crest(Input)`, ordinal 1, cost/depth 1/1 |
| XOR/parity | `[0,1,2,3]` | `[0,1,1,0]` | `EXHAUSTED`: 1,565 candidates, no winner |
| shifted mixture | `[1,2,3,4]` | `[0,1,1,1]` | `FOUND`: `Crest(Tail(Input))`, ordinal 4, cost/depth 2/2 |
| permuted mixture | `[1,0,2,3]` | `[0,1,1,1]` | `EXHAUSTED`: 1,565 candidates, no winner |

On the identity mixture, `Input` separates all four encodings and therefore
satisfies only three of six quotient obligations. `Crest(Input)` satisfies all
six, reduces four response classes to two, and gives class saving 2.

The XOR row derives its two bits only from the canonical abstract ordinal. For
each bit value, both target classes occur exactly once, so both exact 2x2 tables
are `[[1,1],[1,1]]`. This is a finite balanced-marginal fact. It is not a
separation theorem for a formal marginal-observer class and is not BM-F009.

## Representation transport result

The three mixture rows bind the same abstract task digest. The suite evaluates
the identity winner `Crest(Input)` unchanged on each target representation
*before* performing a separate target re-synthesis:

```text
identity -> shifted:
  source-witness truth table = [false,false,false,true,true,true]
  relation hits              = 3 / 6
  unchanged transfer         = false
  target re-synthesis        = FOUND at cost 2 (delta +1)

identity -> permuted:
  source-witness truth table = [true,false,false,false,false,true]
  relation hits              = 2 / 6
  unchanged transfer         = false
  target re-synthesis        = EXHAUSTED
```

Thus the bounded result is representation sensitivity: a shift breaks direct
witness reuse but re-synthesis repairs it with a more expensive admitted
observer, while the chosen permutation is not expressed by the fixed catalog.
This is explicitly not general representation invariance/non-invariance,
physical transport, impossibility, hidden-variable recovery, or a theorem.

## Atomic receipt and replay

`NativeBenchmarkSuiteReceiptV1` binds the four benchmark/spec/task roots, exact
case order, CEGIS training/limits/trace roots, per-row ledgers, terminal status,
winner or exhaustion evidence, generic four-state score, the derived XOR
marginal table, and both transport truth tables. An `INCOMPLETE` or `INVALID`
row cannot mint a suite receipt; all four rows and both transports must replay
in their fixed order.

The default suite digest is
`5ff3518bf37060ac410c1a80765235da2d4758e6f2d2497ac5c38cfafbf96a17`.
Replay rebuilds every benchmark and the exact catalog, reruns CEGIS under the
receipt-bound counters, re-evaluates source-witness transport, and exact-compares
the complete reconstructed receipt. Child reorder, status/winner injection,
marginal mutation, transport-verdict mutation, and cutoff rebinding fail closed.

The implementation is an in-process dependency-free Rust calibration. Its
counter ledgers are protocol charges; they do not assert four physically
isolated catalog enumerations. Wall-clock/process-address-space custody,
holdout validity, signatures, performance, backend dispatch, theoremhood,
novelty, and P2 promotion remain absent.

## Focused verification

```bash
cargo fmt --manifest-path vam/native/Cargo.toml --all -- --check
cargo check --manifest-path vam/native/Cargo.toml --locked
cargo test --manifest-path vam/native/Cargo.toml --locked --test observer_benchmark_suite
```

The public integration tests pin the terminal matrix, winner identities/costs,
balanced marginal tables, transport truth tables, suite digest, exact replay,
tamper rejection, and cutoff-to-`INCOMPLETE` behavior.
