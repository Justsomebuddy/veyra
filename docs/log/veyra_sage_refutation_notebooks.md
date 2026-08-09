# 52 — Veyra Sage Refutation Notebooks

**Status:** implemented seed.
**Layer:** mutation/refutation notebooks for theorem-card labs.
**Goal:** test that Veyra proof objects reject bad or mutated cards, not only accept positive examples.

## Why this layer exists

A proof/check system needs negative pressure.
The executable card notebooks prove the happy path; refutation notebooks prove the guardrails:

```text
bad/mutated card → VeyraProofObject.check(card) → blocked VeyraProofCheck
```

This follows the Veyra research rule: every beautiful theorem-card must have a refutation track.

## API

| Function/object | Meaning |
|---|---|
| `VeyraRefutationExample` | descriptor for one intentional failing card |
| `run_refutation_example(refutation_id)` | run one bad/mutated card and return `VeyraProofCheck` |
| `refutation_examples(domain=None)` | list refutation descriptors |
| `refutation_summary()` | compact negative-coverage summary |
| `build_refutation_notebook(domain)` | domain notebook asserting blocked checks |
| `build_all_refutation_notebooks()` | all refutation notebooks |

## Current coverage

```text
7 refutation examples
7 blocked checks
7 domains
3 mutation cards
7 refutation notebooks
56 notebook cells total
```

Covered domains:

```text
algebra, analysis, combinatorics, geometry, probability, statistics, trig
```

## Counterexample vs mutation

- **Counterexample:** a genuine input where the theorem-card builder returns a failed relation/obstruction.
- **Mutation:** a deliberately corrupted card object used when the positive theorem is structurally tautological for valid inputs.

Both are useful, but they mean different things.
Counterexamples test the mathematics; mutations test the checker boundary.

## Example

```python
from veyra_sage.all import run_refutation_example, build_refutation_notebook

run_refutation_example("pythagorean-non-right").as_dict()
GEO_BAD = build_refutation_notebook("geometry")
GEO_BAD.to_markdown()
```

Expected signal:

```text
status == "blocked"
```

## Verification

Executable checks:

- `tests/sage/test_veyra_sage_refutations.py` — seven refutations, filters, notebooks, unknown failures.
- `tests/sage/test_veyra_sage.py` — certificate suite includes `sage_refutations_passed`.
- `scripts/sage_smoke.py` — prints refutation summary.
- `veyra_sage/examples.py` — doctest includes `run_refutation_example`.
