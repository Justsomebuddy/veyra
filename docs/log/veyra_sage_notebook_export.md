# 49 — Veyra Sage Notebook Export

**Status:** implemented artifact bundle.
**Layer:** Sage-lab artifact generation.
**Goal:** turn the current school/proof facades into reproducible markdown and ipynb notebook artifacts.

## Why this layer exists

After `VeyraSchoolCore` and `VeyraProofGraph`, the lab needs a portable research surface:

- a summary of theorem/curriculum coverage;
- executable cells for loading Veyra facades;
- curriculum path probes;
- domain index probes;
- export-row inspection.

`build_school_proof_notebook()` produces that surface without depending on Jupyter or Sage internals.

## Objects

| Object | Meaning |
|---|---|
| `VeyraNotebookCell` | one markdown or code cell |
| `VeyraNotebook` | generated notebook artifact with markdown and ipynb renderers |
| `build_school_proof_notebook()` | builder from current school/proof registries |
| `VeyraNotebookArtifact` | named disk-ready notebook artifact |
| `current_notebook_artifacts()` | inventory of every current notebook builder |
| `write_current_notebook_artifacts()` | writes `.ipynb`, optional `.md`, and `manifest.json` |

## Current generated shape

The seed school/proof notebook contains:

- `8` cells;
- `4` markdown cells;
- `4` code cells;
- nbformat `4.5` dictionary output;
- markdown rendering with fenced Python code.

The disk bundle currently contains:

- `32` `.ipynb` artifacts;
- `32` markdown preview artifacts;
- `5` artifact families: global, domain theorems, executable cards, refutations, refutation search;
- `234` notebook cells total;
- compact manifest at `notebooks/generated/manifest.json`.

The notebook records the path:

```text
arithmetic-ratios → combinatorics → probability → statistics
```

## Example

```python
from veyra_sage.all import build_school_proof_notebook

N = build_school_proof_notebook()
N.summary()
N.to_markdown()
N.to_ipynb_dict()
N.write_markdown("veyra_lab.md")
N.write_ipynb("veyra_lab.ipynb")

from veyra_sage.all import write_current_notebook_artifacts
write_current_notebook_artifacts("notebooks/generated")
```

## Rule

Notebook export is a **lab surface**, not a proof by itself.
It must only expose declared Veyra proof/check objects and explicit classical shadows.

## Verification

Executable checks:

- `tests/sage/test_veyra_sage_notebooks.py` — summary, markdown, ipynb shape, artifact writes, invalid-cell failure.
- `tests/sage/test_veyra_sage_notebook_artifacts.py` — current notebook inventory and real disk bundle writes.
- `tests/sage/test_veyra_sage.py` — certificate suite includes `sage_notebook_passed`.
- `scripts/generate_notebooks.py` — writes and verifies the real `.ipynb` bundle with progress.
- `scripts/sage_smoke.py` — prints notebook summary, nbformat marker, and artifact inventory.
- `veyra_sage/examples.py` — doctest includes notebook builder.
