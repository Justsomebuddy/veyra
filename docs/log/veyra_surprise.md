# 68 — Veyra Surprise

**Status:** implemented seed.
**Layer:** observer-gap discovery.
**Goal:** define a computational object that can surprise the current lab by revealing hidden structure after an observer switch.

## Intuition

A Veyra surprise is not raw emotion. It is a measurable break in expectation:

```text
surface observer sees no useful structure,
hidden observer reveals a low-cost explanation.
```

The first implemented case compares:

- surface observer: exact cyclic compression;
- hidden observer: edit-lift resonance.

Example witness:

```text
mode = abababa
surface exact-cycle saving = 0
hidden edit-lift part = ab
expected rhythm = ababab
edit distance = 1
hidden saving > 0
```

The surprise is that the object is not an exact closed tiling, but a nearly
closed rhythm appears when one edit operation is allowed.

## API

- `VeyraSurpriseWitness` — JSON-ready observer-gap witness.
- `surface_exact_saving(mode, candidates)` — naive exact-cycle expectation.
- `best_surprise_for_mode(mode, alphabet, ...)` — best hidden-structure witness.
- `find_surprise_witnesses(...)` — finite search over mode space.
- `surprise_checklist()` — capability checklist.
- `ClassicalBlindSignature` — bounded classical baseline signature for separation tests.
- `SurpriseSeparationRow` — finite pair where named baselines are blind but Veyra surprise separates.
- `ExpandedClassicalSignature` — stronger finite baseline signature for counterexample pressure.
- `BaselineAuditRow` — records which stronger baselines catch a toy separation.
- `surprise_separation_rows()` — current observer-gap separation benchmark rows.
- `SurpriseSearchRow` — bounded exhaustive search row over baseline-collision groups.
- `expanded_baseline_search_row()` — S3 search for expanded-baseline-blind surprise splits.
- `HiddenCorrelationRow` — non-local XOR/parity row where pairwise baselines are blind.
- `xor_hidden_correlation_row()` — S4 hidden-correlation benchmark row.
- `KWiseHiddenCorrelationRow` — finite k-wise-blind/global-parity hidden-correlation row.
- `kwise_parity_hidden_correlation_row()` — S5 3-wise-blind / 4-wise parity row.
- `DeBruijnTrailRow` — finite local-window-blind de Bruijn trail row.
- `debruijn_trail_hidden_row()` — S6 order-3 cyclic-window / trail-adjacency row.
- `ObserverGrammar` / `ObserverTerm` — typed R5 finite search space.
- `fit_observer()` / `validate_observer()` — train-only fit with locked evaluator/config digest and payload-disjoint fixed-winner holdout validation.
- `parity_observer_synthesis()` — current even-4/odd-5 synthesis witness.
- `strict_observer_class_certificate()` — R6 proper-marginal-vs-parity class inclusion evidence.

## S1 separation program

The practical “нельзя” direction is not a claim of Turing-uncomputability.
It is a finite separation claim against a declared baseline family:

```text
baseline observers cannot distinguish two rows,
but a declared Veyra observer-gap witness separates them.
```

Current S1 benchmark:

| Structured word | Control word | Blind baselines | Veyra witness |
|---|---|---|---|
| `aabaabb` | `abbaaab` | symbol counts, lag-1/2 agreement, LZ78 phrase count | edit-lift part `aab`, gap `3` |

Expanded-baseline audit:

| Audit | Stronger baselines | Result |
|---|---|---|
| `S2-AUDIT-001` | block-frequency entropy proxy, higher-lag autocorrelation, cyclic spectral proxy | catches the toy pair |

S3 bounded search:

| Search | Corpus | Expanded collisions | Robust split pairs | Result |
|---|---:|---:|---:|---|
| `S3-SEARCH-001` | binary words length `4..8` (`496` words) | `32` | `0` | no expanded-baseline-blind surprise split found |

S4 hidden-correlation row:

| Row | Structured table | Control table | Blind baselines | Hidden observer |
|---|---|---|---|---|
| `S4-XOR-001` | duplicated even-parity cube | full `3`-bit cube | row count, single-bit marginals, pairwise joint marginals | triple parity gap `8` vs `0` |

S5 k-wise hidden-correlation row:

| Row | Structured table | Control table | Blind baselines | Hidden observer |
|---|---|---|---|---|
| `S5-KWISE-001` | duplicated even `4`-bit parity cube | full `4`-bit cube | all `1/2/3`-wise coordinate marginals | `4`-wise parity gap `16` vs `0` |

S6 de Bruijn trail row:

| Row | Structured cycle | Control cycle | Blind baselines | Hidden observer |
|---|---|---|---|---|
| `S6-DEBRUIJN-001` | `00010111` | `00011101` | cyclic window counts of width `1..3` | trail-adjacency / order-4 graph split, divergent transitions `8` |

This is deliberately weak but honest: it proves only one finite separation
against three named baseline observers. It does **not** prove that no
classical method can detect the structure. The expanded audit already shows
this toy pair is caught by stronger classical observers. The XOR/k-wise rows are
non-local hidden-correlation cases, but triple/global parity is itself a
classical high-order observer. The de Bruijn row is stronger in shape but still
finite: trail adjacency is a classical order-4 graph observer. The next work is
topological and Bell-style candidate families.

## Interpretation

This layer turns surprise into a research instrument:

1. declare the surface observer;
2. declare the hidden observer;
3. measure the gap;
4. record the witness;
5. decide whether the gap suggests a new definition, theorem, or counterexample.

It is a seed for broader discovery: the same pattern can later compare terminal
finite transition systems against residue, phase, side-information, or walk-trace observers.

## Verification

Executable checks:

- `tests/surprise/test_surprise.py` — hidden edit-lift witness, no-surprise negative case, checklist.
- `tests/surprise/test_surprise_separation.py` — first finite baseline-blind separation row and no-overclaim boundary.
- `tests/surprise/test_surprise_search.py` — bounded expanded-baseline search ledger and XOR/parity hidden-correlation row.
- `tests/surprise/test_surprise_kwise.py` — S5 k-wise/global-parity hidden-correlation row.
- `tests/surprise/test_surprise_debruijn.py` — S6 order-3-window-blind de Bruijn trail row.

Certificate status: `surprise_separation_s1` certifies the first finite
separation row, `surprise_search_s3` certifies the bounded negative search plus
S4 XOR row, `surprise_kwise_s5` certifies the S5 k-wise row, and
`surprise_debruijn_s6` certifies the S6 trail row; broader hidden-observer
families remain future work.

## R5/R6 promotion

The earlier S4/S5 parity rows are now a generic synthesis corpus rather than a
hand-named observer only. The engine builds `histogram(xor-rows(input))` from
typed primitives, scores it under positive costs, and validates the locked
winner on a different width and parity coset. Lean proves factor-class blindness
and separation after adding an extra response. The result is stronger only than
the declared proper-subset-marginal factor class; global parity is classical.
