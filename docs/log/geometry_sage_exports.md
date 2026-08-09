# Geometry Sage Exports and Visual Rows

**Date:** 2026-06-06
**Status:** executable Sage-lab export plus X6 visual regression; not package-stable Sage extension.
**Implementation:** `veyra_sage/geometry_cards.py`, `src/core/geometry/visual_regression.py`.
**Certificate surface:** `sage_geometry_theorem_cards_passed` in `sage_certificate_suite()`.

## Scope

This Sprint G seed adds a geometry-specific Sage lab for existing theorem cards:

- `VeyraGeometryTheoremLab.card_rows()` runs the five geometry theorem-card checks;
- `visual_rows()` exposes lightweight JSON sketches backed by canonical core scene rows;
- `stable_export_rows()` filters the stable formal-export gate to geometry hooks;
- `build_geometry_theorem_card_notebook()` adds a disk-generated notebook artifact.

The implementation uses the already stable theorem registry and proof-discipline export rows.  It does not add new geometry axioms or a package-stable Sage extension.

## Covered geometry cards

| Card | Ready relation |
|---|---|
| `pythagorean-separation` | `proven` |
| `sss-triangle` | `congruent` |
| `sas-triangle` | `congruent` |
| `line-shell-intersection` | `tangent` in the notebook example |
| `plane-relabel-composition` | `proven` |

All five are also visible as `stable-card-only` rows through the geometry export filter.

## Visual rows

The current visual rows are intentionally renderer-agnostic JSON sketches:

1. `pythagorean-right-triangle` — points `o=(0,0)`, `e=(3,0)`, `n=(0,4)` and triangle edges;
2. `line-shell-tangent` — center, radius squared, and tangent corridor;
3. `plane-relabel-composition` — sample point and relabel composition labels.

X6 adds deterministic renderer-independent text and digest snapshots for these rows: `1afff2f2c901296f`, `fe9658a7b70673e9`, and `4eeca8e45ca5ea21`. These are regression checks for scene drift, not theorem proofs.

## Artifact impact

The generated notebook bundle now includes:

- `notebooks/generated/global/geometry_theorem_cards.ipynb`;
- matching markdown preview;
- manifest summary `37` notebooks, `260` cells, `125` markdown cells, `135` code cells.

## Package boundary

`VeyraGeometryTheoremLab` is public through `veyra_sage.all` for current notebooks and tests, but remains under the research-lab boundary from `docs/concepts/package_boundary.md`.

Package-stable promotion is deferred until:

- renderer choice is tested;
- geometry rows stop changing;
- negative examples beyond current digest regression are added;
- theorem-card exports have formal-prover targets.

## Verification

```bash
PYTHONPATH=. python3 -m pytest -q tests/sage/test_veyra_sage_geometry_cards.py tests/sage/test_veyra_sage_notebook_artifacts.py tests/sage/test_veyra_sage.py tests/sage/test_veyra_sage_api_index.py
the complete verification suite
```

Expected after X6: `geometry_visual_regression_x6` passes; current suite after X7 reports `46/46`, Sage smoke ok, doctest `41/41`, and line hygiene stays clean.
