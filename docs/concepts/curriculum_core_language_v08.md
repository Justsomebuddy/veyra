# Curriculum update after Core Language v0.8

**Date:** 2026-06-05
**Scope:** school-to-11 replacement map after Core Language coverage matrix, source-span diagnostics, Essence/Core, proof discipline, and Sage lab maturation.

## What changed

The old curriculum node map remains a compact certificate ledger: 11 nodes, 12 dependency edges, 0 missing nodes, and 19 Sage export rows.  After Core Language v0.8, the project also needs a more detailed topic ledger that records the full acceptance contract for each school topic:

```text
TopicRow = (
  topic-id,
  domain,
  native-definition,
  school-shadow,
  example,
  counterexample,
  test-path,
  sage-row,
  status,
  required-primitives
)
```

This row type is implemented in `src/core/registry/curriculum_topics.py` as `SchoolTopicCoverage`.

## Current topic matrix

| Topic | Domain | Status | Test / Sage row | Required primitives |
|---|---|---|---|---|
| `arithmetic-ratios` | arithmetic | covered | `tests/shadows/test_balance_ratio.py` / `facade:VeyraRatios` | balance, ratio, shadow |
| `linear-equations` | algebra | covered | `tests/shadows/test_equation.py` / `algebra.linear_solution` | ratio, linear-form, obstruction |
| `polynomials` | algebra | covered | `tests/shadows/test_polynomial.py` / `algebra.polynomial_identity` | polynomial, ratio, factor-hit |
| `combinatorics` | combinatorics | covered | `tests/registry/test_depth_packs.py` / `combinatorics.binomial_symmetry` | finite-choice, factorial-echo |
| `functions` | functions | covered | `tests/shadows/test_transformer.py` / `facade:VeyraLanguageLab` | mode, transformer, kind |
| `analysis-seeds` | analysis | covered | `tests/shadows/test_change.py` / `analysis.sampled_continuity` | completion, drift, area |
| `geometry-events` | geometry | covered | `tests/geometry/test_geometry_theorems.py` / `geometry.pythagorean` | event, corridor, shell, relabel |
| `proof-registry` | proof | covered | `tests/registry/test_theorem_registry.py` / `facade:VeyraProofGraph` | theorem-card, dependency-edge, proof-check |
| `trigonometry` | geometry | covered | `tests/numbers/test_cyclic_probability_stats.py` / `trig.cyclic_period` | cyclic-phase, shell, chord |
| `probability` | probability | covered | `tests/registry/test_depth_packs.py` / `probability.union` | finite-distribution, weighted-outcome, observer |
| `statistics` | statistics | covered | `tests/registry/test_depth_packs.py` / `statistics.variance_shift` | sample-echo, mean-balance, variance |
| `trigonometry-identities` | geometry | seeded | `tests/shadows/test_trigonometry_identities.py` / `trig.identity_seed` | angle-composition, inverse-phase, identity-normal-form |
| `calculus-depth` | analysis | seeded | `tests/shadows/test_calculus_depth.py` / `analysis.calculus_depth` | limit-algebra, local-linearization, integral-coherence |
| `statistics-inference` | statistics | seeded | `tests/shadows/test_statistics_inference.py` / `statistics.inference_seed` | distribution-family, sampling-law, uncertainty-certificate |
| `vectors-matrices` | linear-algebra | seeded | `tests/shadows/test_linear_algebra_seed.py` / `linear_algebra.matrix_seed` | vector-mode, matrix-transformer, determinant-shadow |

## Remaining school-to-11 gaps

`school_topic_gap_rows()` returns all rows whose status is not `covered`:

- `trigonometry-identities` — seeded; needs angle-composition normal form and identity theorem cards.
- `calculus-depth` — seeded; local linearization, product/chain cards, integral coherence, and Sage facade are executable; full transcendental calculus remains pending.
- `statistics-inference` — seeded; distribution family, interval, hypothesis, uncertainty, concentration, likelihood-grid geometry, and residual-family certificates are executable.
- `vectors-matrices` — seeded; vector/matrix action, determinant product, and eigen-candidate cards are executable; general linear algebra remains pending.

## Acceptance rule

A topic may move to `covered` only when the row has:

1. Veyra-native definition;
2. school-shadow translation;
3. executable example;
4. blocking counterexample/refutation;
5. pytest or doctest path;
6. Sage facade/export row;
7. required primitives listed explicitly.

The governing tests are in `tests/registry/test_curriculum_map.py`.
