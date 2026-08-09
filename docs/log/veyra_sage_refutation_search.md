# 53 — Veyra Sage Refutation Search

**Status:** implemented seed.
**Layer:** parameterized negative search for theorem-card labs.
**Goal:** discover blocked theorem-card candidates from small finite parameter spaces instead of only hand-written bad examples.

## Why this layer exists

Refutation notebooks define known bad cases.
Refutation search turns that into an experiment loop:

```text
candidate space → theorem-card builder → proof check → blocked hit report
```

The search is intentionally small and deterministic for now.
It is a seed for future larger mutation/refutation search over examples, parameters, and generators.

## API

| Function/object | Meaning |
|---|---|
| `VeyraSearchHit` | one blocked candidate found by search |
| `VeyraSearchReport` | per-domain tried/blocked report |
| `run_search_candidate(candidate_id)` | run one candidate by ID |
| `refutation_search(domain=None)` | run finite search and group by domain |
| `refutation_search_summary()` | compact search summary |
| `build_refutation_search_notebook(domain)` | notebook for one domain search |
| `build_all_refutation_search_notebooks()` | all search notebooks |

## Current finite search space

```text
7 domains
10 candidates tried
7 blocked hits
7 search notebooks
42 notebook cells total
```

Search includes both:

- known-valid candidates, e.g. `geo-right`, to prove the checker still accepts valid cases;
- known-bad candidates, e.g. `geo-non-right`, to prove the checker blocks failures.

## Example

```python
from veyra_sage.all import refutation_search, run_search_candidate

run_search_candidate("geo-right").status      # ready
run_search_candidate("geo-non-right").status  # blocked
refutation_search("geometry")[0].as_dict()
```

## Interpretation

This is not random fuzzing yet.
It is a deterministic micro-search layer that establishes the protocol and output format for future fuzzing, mutation, and property-based theorem pressure.

## Verification

Executable checks:

- `tests/sage/test_veyra_sage_refutation_search.py` — reports, positive/blocked candidates, filters, notebooks, unknown failures.
- `tests/sage/test_veyra_sage.py` — certificate suite includes `sage_refutation_search_passed`.
- `scripts/sage_smoke.py` — prints `refutation_search` summary.
- `veyra_sage/examples.py` — doctest includes `run_search_candidate`.
