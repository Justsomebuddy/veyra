# 51 — Veyra Sage Executable Card Notebooks

**Status:** implemented seed.
**Layer:** executable theorem-card examples inside Sage/Jupyter lab notebooks.
**Goal:** make each domain notebook run actual Veyra theorem-card checks, not only dependency ledgers.

## Why this layer exists

A theorem registry is useful only if claims can be pressure-tested.
This layer adds executable examples for every current theorem spec and wraps them into domain notebooks.

Each example path is:

```text
theorem_id → card builder → VeyraProofObject.check(card) → VeyraProofCheck
```

## API

| Function/object | Meaning |
|---|---|
| `VeyraCardExample` | descriptor for one executable theorem-card example |
| `run_card_example(theorem_id)` | build one card and return `VeyraProofCheck` |
| `card_examples(domain=None)` | list executable examples, optionally filtered by domain |
| `card_example_summary()` | compact coverage summary |
| `build_executable_card_notebook(domain)` | domain notebook that runs card checks |
| `build_all_executable_card_notebooks()` | all executable card notebooks |

## Current coverage

```text
19 executable examples
19 ready checks
7 domains
7 executable card notebooks
56 notebook cells total
```

Covered domains:

```text
algebra, analysis, combinatorics, geometry, probability, statistics, trig
```

## Example

```python
from veyra_sage.all import run_card_example, build_executable_card_notebook

run_card_example("pythagorean-separation").as_dict()
GEO = build_executable_card_notebook("geometry")
GEO.to_markdown()
GEO.to_ipynb_dict()
```

## Verification meaning

`ready` means the example card satisfies the Veyra theorem spec:

- required dependencies exist;
- relation is in the success relation set;
- obstruction is compatible with success.

It does **not** mean an unrestricted classical theorem has been proved.
It means the declared Veyra theorem-card instance is reproducibly certified.

## Verification

Executable checks:

- `tests/sage/test_veyra_sage_card_examples.py` — all 19 examples, filters, notebook builders, unknown failures.
- `tests/sage/test_veyra_sage.py` — certificate suite includes `sage_card_examples_passed`.
- `scripts/sage_smoke.py` — prints card example summary.
- `veyra_sage/examples.py` — doctest includes `run_card_example`.
