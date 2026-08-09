# 50 — Veyra Sage Domain Notebooks

**Status:** implemented seed.
**Layer:** focused Sage/Jupyter lab generation by theorem domain.
**Goal:** split the global Veyra proof graph into inspectable domain notebooks.

## Why this layer exists

The global school/proof notebook shows the whole seed system.
Domain notebooks make each research lane smaller and more interactive:

- `algebra`;
- `analysis`;
- `combinatorics`;
- `geometry`;
- `probability`;
- `statistics`;
- `trig`.

Each notebook is generated from the current `VeyraProofGraph`, so it stays synchronized with theorem specs and dependencies.

## API

| Function/object | Meaning |
|---|---|
| `available_notebook_domains()` | sorted domains with theorem notebooks |
| `domain_notebook_spec(domain)` | descriptor with theorem IDs and cell count |
| `build_domain_theorem_notebook(domain)` | one focused domain notebook |
| `build_all_domain_notebooks()` | dictionary of all domain notebooks |
| `VeyraDomainNotebookSpec` | JSON-ready domain notebook descriptor |

## Current generated shape

Every domain notebook currently has:

- `8` cells;
- `4` markdown cells;
- `4` code cells;
- theorem catalogue cell;
- dependency ledger cell;
- executable code cells for object dictionaries and obstruction catalogs.

Global generated set:

```text
7 domains × 8 cells = 56 cells
```

## Example

```python
from veyra_sage.all import available_notebook_domains, build_domain_theorem_notebook

available_notebook_domains()
GEO = build_domain_theorem_notebook("geometry")
GEO.to_markdown()
GEO.to_ipynb_dict()
```

## Rule

Domain notebooks must remain generated artifacts over Veyra proof objects.
They may show dependencies and obstruction catalogs, but must not silently translate Veyra claims into classical theorem assertions.

## Verification

Executable checks:

- `tests/sage/test_veyra_sage_notebooks.py` — domains, specs, geometry shape, invalid-domain failure, all-domain generation.
- `tests/sage/test_veyra_sage.py` — certificate suite includes `sage_domain_notebooks_passed`.
- `scripts/sage_smoke.py` — prints `domain_notebooks=7`.
- `veyra_sage/examples.py` — doctest includes domain notebook builder.
